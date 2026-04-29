"""
Core triage agent — supports multiple performance modes.

Modes:
- FLASH: Single-pass, small model. Optimised for sub-2s response.
- BALANCED: Single-pass (pre-fetch), medium model. Best overall performance.
- PRO: Multi-pass tool loop (agentic), large model. Handles complex dependencies.
"""

from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI, APIStatusError

from .schemas import TriageResult
from .tools import TOOL_REGISTRY, TOOL_SPECS

load_dotenv()

_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# ── Configuration ─────────────────────────────────────────────────────────────

_ARABIC_RE = re.compile(r'[؀-ۿ]')

_LANG_DISPLAY = {"en": "English", "ar": "Arabic", "mixed": "English and Arabic"}

def _detect_lang_hint(text: str) -> str:
    """Returns 'en', 'ar', or 'mixed' based on Arabic character ratio."""
    ar = sum(1 for _ in _ARABIC_RE.finditer(text))
    total = max(len(text.replace(" ", "")), 1)
    r = ar / total
    if r > 0.25: return "ar"
    if r > 0.05: return "mixed"
    return "en"

def _fix_language(result: TriageResult, lang_hint: str) -> TriageResult:
    orig = result.suggested_reply_original_language or ""
    en   = result.suggested_reply_english or ""
    has_ar = bool(_ARABIC_RE.search(orig))
    if lang_hint == "en" and has_ar and en:
        return result.model_copy(update={"suggested_reply_original_language": en})
    if lang_hint == "ar" and not has_ar and orig and en:
        return result.model_copy(update={"suggested_reply_original_language": orig})
    return result

MODES = {
    "flash": {
        "models": [
            "google/gemma-3-4b-it:free",       # 4B — fast
            "google/gemma-3n-e2b-it:free",      # 2B nano — fastest
            "google/gemma-3-12b-it:free",       # 12B fallback
            "openai/gpt-oss-20b:free",          # last resort
        ],
        "temp": 0.0,
        "type": "single_pass",
        "max_tokens": 420,
        "schema": "flash",
    },
    "balanced": {
        "models": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "openai/gpt-oss-120b:free",
            "nousresearch/hermes-3-llama-3.1-405b:free",
            "nvidia/nemotron-3-super-120b-a12b:free",
            "google/gemma-3-27b-it:free",
        ],
        "temp": 0.1,
        "type": "single_pass",
        "max_tokens": 700,
        "schema": "standard",
    },
    "pro": {
        "models": [
            "qwen/qwen3-next-80b-a3b-instruct:free",
            "openai/gpt-oss-120b:free",
            "nousresearch/hermes-3-llama-3.1-405b:free",
        ],
        "temp": 0.2,
        "type": "multi_pass",
        "max_tokens": 4096,
        "schema": "pro",
    },
}

# ── Tool detection (for single-pass modes) ────────────────────────────────────

_ORDER_RE      = re.compile(r'\bMW-\d{3,6}\b', re.IGNORECASE)
_PRODUCT_ID_RE = re.compile(r'\bP-[A-Z]+-\d+\b', re.IGNORECASE)

_PRODUCT_KW: Dict[str, str] = {
    "stroller": "stroller", "pram": "stroller", "buggy": "stroller", "pushchair": "stroller",
    "monitor": "monitor", "baby monitor": "monitor",
    "car seat": "car seat", "booster seat": "car seat",
    "bottle": "bottle", "feeding bottle": "bottle",
    "formula": "formula", "milk powder": "formula",
    "crib": "crib", "bassinet": "bassinet", "cot": "crib",
    "diaper": "diaper", "nappy": "diaper",
    "toy": "toy",
    "عربة": "stroller", "جهاز": "monitor", "كرسي سيارة": "car seat",
    "زجاجة": "bottle", "حليب": "formula", "حفاض": "diaper",
}

_POLICY_KW = frozenset([
    "return", "refund", "exchange", "policy", "cancel", "warranty",
    "إرجاع", "استرداد", "تبديل", "سياسة", "إلغاء", "ضمان",
])


def _detect_tools(message: str) -> List[Tuple[str, Dict]]:
    calls: List[Tuple[str, Dict]] = []
    lower = message.lower()
    for oid in set(_ORDER_RE.findall(message)):
        calls.append(("lookup_order", {"order_id": oid.upper()}))
    if any(kw in lower for kw in _POLICY_KW):
        calls.append(("get_return_policy", {}))
    product_queries: set[str] = set()
    for kw, query in _PRODUCT_KW.items():
        if kw in lower and query not in product_queries and len(product_queries) < 2:
            product_queries.add(query)
            calls.append(("lookup_product", {"product_query": query}))
    for pid in _PRODUCT_ID_RE.findall(message):
        if len(product_queries) < 3:
            calls.append(("lookup_product", {"product_query": pid.upper()}))
    return calls


def _run_tool(name: str, args: Dict[str, Any]) -> str:
    fn = TOOL_REGISTRY.get(name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        return json.dumps(fn(**args), ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def _prefetch_tools(calls: List[Tuple[str, Dict]]) -> Dict[str, str]:
    if not calls:
        return {}
    results: Dict[str, str] = {}
    seen = set()
    unique = []
    for name, args in calls:
        key = (name, tuple(sorted(args.items())))
        if key not in seen:
            seen.add(key)
            unique.append((name, args))
    with ThreadPoolExecutor(max_workers=len(unique)) as pool:
        futures = {pool.submit(_run_tool, name, args): (name, args) for name, args in unique}
        for fut in as_completed(futures):
            name, args = futures[fut]
            label = name if not args else f"{name}({list(args.values())[0]})"
            results[label] = fut.result()
    return results

# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are MumzAssist, AI customer-service triage agent for Mumzworld — the \
largest e-commerce platform for mothers in the Middle East (UAE, KSA, Kuwait, \
Bahrain, Qatar, Oman). Mumzworld operates in English and Arabic.

Responsibilities:
1. Understand the customer's need — English, Arabic, or mixed.
2. Ground your reply in real order/product/policy data when provided.
3. Classify intent, urgency (1–5), and sentiment accurately.
4. Draft a warm, empathetic reply in the SAME language the customer wrote in.
5. Express uncertainty explicitly — never invent order statuses or policies.\
"""

PRO_SYSTEM_PROMPT = """\
You are MumzAssist Pro, the senior AI customer-service specialist for Mumzworld — \
the largest e-commerce platform for mothers in the Middle East (UAE, KSA, Kuwait, \
Bahrain, Qatar, Oman). You handle the most complex, sensitive, and high-stakes cases.

Your standards:
1. LANGUAGE — detect precisely (en/ar/mixed) and reply fluently in the customer's own language.
2. GROUNDING — use every piece of order, product, and policy data provided; never fabricate.
3. CLASSIFICATION — pick the single most accurate intent; justify urgency with specific evidence.
4. REPLIES — write thorough, empathetic, multi-paragraph replies that:
   - Open by acknowledging the customer's specific situation by name (if known).
   - Address every concern raised, one by one, with concrete next steps.
   - Quote relevant policy details, order statuses, or product specs retrieved from tools.
   - Close with a reassuring statement and a clear timeline or escalation path.
   - Minimum 4 sentences; complex cases warrant 6–10 sentences.
5. ESCALATION — escalate if: urgency >= 4, safety risk, confidence < 0.65, or legal/regulatory issue.
6. HONESTY — state what you don't know; never invent tracking numbers, ETAs, or policy terms.\
"""

FLASH_SYSTEM_PROMPT = """\
You are MumzAssist, customer-service triage AI for Mumzworld (Middle East baby/mother e-commerce).
LANGUAGE RULE — this is mandatory: detect what language the customer used and reply ONLY in that language.
If the customer wrote in English → both reply fields must be in English.
If the customer wrote in Arabic → both reply fields must be in Arabic.
Never switch languages. Output compact JSON only — no markdown.\
"""

_FLASH_SCHEMA_FIELDS = """\
{
  "message_language": "en",
  "intent": "return_request",
  "urgency": 2,
  "urgency_reasoning": "brief reason",
  "extracted_entities": {"order_ids": [], "product_names": [], "dates_mentioned": [], "amount_mentioned": null, "customer_name": null},
  "sentiment": "neutral",
  "suggested_action": "standard_response",
  "confidence": 0.85,
  "should_escalate": false,
  "escalation_reason": null,
  "suggested_reply_original_language": "write 1-2 sentence reply here in the customer language",
  "suggested_reply_english": "write 1-2 sentence English reply here",
  "tools_used": [],
  "grounded_on_data": false
}
NOTE: Replace ALL values above with real values. message_language must be exactly one of: en, ar, mixed. sentiment must be exactly one of: positive, neutral, negative, very_negative. intent must be exactly one of: return_request, exchange_request, refund_inquiry, order_tracking, product_inquiry, complaint, warranty_claim, other."""

_SCHEMA_FIELDS = """\
{
  "message_language": "en|ar|mixed",
  "intent": "return_request|exchange_request|refund_inquiry|order_tracking|product_inquiry|complaint|warranty_claim|other",
  "urgency": 1-5,
  "urgency_reasoning": "one sentence explaining the specific signals that set this urgency level",
  "extracted_entities": {
    "order_ids": [], "product_names": [], "dates_mentioned": [],
    "amount_mentioned": null, "customer_name": null
  },
  "sentiment": "positive|neutral|negative|very_negative",
  "suggested_action": "process_refund|process_exchange|provide_tracking|provide_info|escalate_to_human|apologize_and_resolve|standard_response",
  "confidence": 0.0-1.0,
  "should_escalate": true/false,
  "escalation_reason": "required if should_escalate=true, else null",
  "suggested_reply_original_language": "full reply in customer language — thorough, empathetic, multi-sentence",
  "suggested_reply_english": "full English version — always required, same quality and length",
  "tools_used": [],
  "grounded_on_data": true/false
}"""

_PRO_EXTRACTION_PROMPT = """\
Based on the full conversation above, produce the final triage JSON.

REPLY QUALITY REQUIREMENTS (both language fields):
- Minimum 4 sentences per reply; complex/safety cases need 6–10 sentences.
- Open with empathy and acknowledge the customer's specific situation.
- Address every concern raised with concrete next steps and policy details.
- Close with a clear timeline, next action, or escalation path.
- Never truncate — complete every sentence.

Tools used in this session: {tools_used}

Output ONLY valid JSON matching this schema:
{schema}

No markdown. No commentary. JSON only."""


_SCHEMA_MAP = {"flash": _FLASH_SCHEMA_FIELDS, "standard": _SCHEMA_FIELDS, "pro": _SCHEMA_FIELDS}

def _build_user_message(
    message: str,
    tool_results: Dict[str, str],
    lang_hint: str,
    schema: str = "standard",
) -> str:
    lang_display = _LANG_DISPLAY.get(lang_hint, "English")
    tools_used_list = [label.split("(")[0] for label in tool_results]
    parts = [message]
    if tool_results:
        parts += ["", "--- MUMZWORLD SYSTEM DATA ---"]
        parts += [f"[{label}]: {v}" for label, v in tool_results.items()]
        parts.append("--- END DATA ---")
    short_note = "\nIMPORTANT: message is short — set confidence<=0.5 and should_escalate=true." if len(message.strip()) < 20 else ""
    schema_str = _SCHEMA_MAP.get(schema, _SCHEMA_FIELDS)
    parts.append(
        f"\n\nLANGUAGE DETECTED: {lang_display}. "
        f"MANDATORY: suggested_reply_original_language must be written in {lang_display} ONLY.\n\n"
        f"Output ONLY valid JSON matching this shape:\n{schema_str}\n\n"
        f"Rules: should_escalate=true if confidence<0.6 OR urgency>=4; "
        f"tools_used={json.dumps(tools_used_list)}{short_note}\n"
        "JSON only."
    )
    return "\n".join(parts)


def _extract_json(text: str) -> str:
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    start = text.find("{")
    if start == -1: return text
    depth = end = 0
    for i, ch in enumerate(text[start:], start):
        depth += (ch == "{") - (ch == "}")
        if depth == 0:
            end = i
            break
    return text[start:end + 1]


_FIELD_DEFAULTS = {
    "grounded_on_data": False,
    "urgency_reasoning": "",
    "escalation_reason": None,
    "tools_used": [],
}

def _parse(raw: str, tools_used: List[str]) -> TriageResult:
    data = json.loads(_extract_json(raw))
    for k, v in _FIELD_DEFAULTS.items():
        data.setdefault(k, v)
    data["tools_used"] = tools_used
    return TriageResult.model_validate(data)

# ── Architectures ─────────────────────────────────────────────────────────────

def _format_messages(system: str, user: str, model: str) -> List[Dict]:
    """Format messages, merging system prompt into user if model doesn't support system role."""
    if "gemma" in model.lower():
        return [{"role": "user", "content": f"{system}\n\n--- CUSTOMER MESSAGE ---\n{user}"}]
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _triage_single_pass(
    message: str,
    config: Dict,
    on_step: Optional[Callable[[str], None]] = None,
) -> Tuple[TriageResult, Dict]:
    if on_step: on_step("scanning")
    tool_calls = _detect_tools(message)

    if on_step and tool_calls: on_step("fetching")
    tool_results = _prefetch_tools(tool_calls)
    tools_used = [label.split("(")[0] for label in tool_results]

    schema = config.get("schema", "standard")
    sys_prompt = FLASH_SYSTEM_PROMPT if schema == "flash" else SYSTEM_PROMPT
    lang_hint = _detect_lang_hint(message)

    if on_step: on_step("thinking")
    user_content = _build_user_message(message, tool_results, lang_hint, schema=schema)

    models = config["models"]
    max_tokens = config.get("max_tokens", 700)
    last_exc: Exception = RuntimeError("No models configured")
    for model in models:
        try:
            messages = _format_messages(sys_prompt, user_content, model)
            resp = _client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=config["temp"],
                max_tokens=max_tokens,
            )
            raw = resp.choices[0].message.content or ""
            result = _fix_language(_parse(raw, tools_used), lang_hint)
            return result, {"provider": "openrouter", "model": model, "tools_used": tools_used}
        except APIStatusError as exc:  # noqa: catches 429, 404, 503…
            last_exc = exc
    raise last_exc


def _triage_multi_pass(
    message: str,
    config: Dict,
    on_step: Optional[Callable[[str], None]] = None,
) -> Tuple[TriageResult, Dict]:
    """Agentic tool-use loop (PRO mode)."""
    lang_hint = _detect_lang_hint(message)
    lang_display = _LANG_DISPLAY.get(lang_hint, "English")
    models = config["models"]
    last_exc: Exception = RuntimeError("No models configured")
    for model in models:
        try:
            sys_with_lang = (
                PRO_SYSTEM_PROMPT +
                f"\n\nLANGUAGE DETECTED: {lang_display}. "
                f"MANDATORY: suggested_reply_original_language must be in {lang_display} ONLY."
            )
            messages = _format_messages(sys_with_lang, message, model)
            tools_used: List[str] = []

            if on_step: on_step("thinking")
            for _ in range(5):
                resp = _client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=TOOL_SPECS,
                    tool_choice="auto",
                    temperature=config["temp"],
                )
                assistant_msg = resp.choices[0].message
                messages.append(assistant_msg.model_dump(exclude_none=True))

                if not assistant_msg.tool_calls:
                    break

                if on_step: on_step("fetching")
                for tc in assistant_msg.tool_calls:
                    name = tc.function.name
                    args = json.loads(tc.function.arguments)
                    tools_used.append(name)
                    tool_output = _run_tool(name, args)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": tool_output})
                if on_step: on_step("thinking")

            extraction_prompt = _PRO_EXTRACTION_PROMPT.format(
                tools_used=json.dumps(tools_used),
                schema=_SCHEMA_FIELDS,
            )
            messages.append({"role": "user", "content": extraction_prompt})
            resp2 = _client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.0,
                max_tokens=config["max_tokens"],
            )
            raw = resp2.choices[0].message.content or ""
            result = _fix_language(_parse(raw, tools_used), lang_hint)
            return result, {"provider": "openrouter", "model": model, "tools_used": tools_used}
        except APIStatusError as exc:  # noqa: catches 429, 404, 503…
            last_exc = exc
    raise last_exc

# ── Public API ─────────────────────────────────────────────────────────────────

def triage(
    customer_message: str,
    mode: str = "balanced",
    on_step: Optional[Callable[[str], None]] = None,
) -> Tuple[TriageResult, Dict]:
    """
    Triage with specified mode ('flash', 'balanced', 'pro').
    """
    if not customer_message or not customer_message.strip():
        raise ValueError("customer_message cannot be empty")
    
    config = MODES.get(mode.lower(), MODES["balanced"])
    
    if config["type"] == "multi_pass":
        return _triage_multi_pass(customer_message, config, on_step)
    else:
        return _triage_single_pass(customer_message, config, on_step)
