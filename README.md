# MumzAssist — Multilingual Customer-Service Triage Agent

> Track A · AI Engineering Intern · Mumzworld Take-Home Assessment

MumzAssist is an AI agent that triages customer-service messages for Mumzworld in English and Arabic. It detects intent (return, exchange, refund, tracking, complaint, warranty, product inquiry), scores urgency and confidence, calls tools to look up real order and product data, drafts a reply in the customer's own language, and knows when to escalate to a human rather than guess. All output is validated against a Pydantic schema with business-rule enforcement before it ever leaves the model.

---

## Why this problem

Mumzworld operates across the GCC — a bilingual market where a mother in Dubai writes in English and a mother in Riyadh writes in Arabic. CS teams triage thousands of messages per day and must respond in the customer's language. Manual triage is slow, inconsistent, and impossible to QA at scale. A structured, validated AI triage layer:

1. Routes tickets faster and more consistently than keyword rules
2. Grounds every response in actual order/policy data — no hallucinated statuses
3. Produces an English "shadow reply" for supervisor review regardless of input language
4. Surfaces explicit uncertainty: model escalates and says why, rather than guessing

I chose this over product PDP generation or review synthesis because it has the clearest evaluation rubric (intent/urgency/escalation are binary right/wrong), the most immediate operational value, and requires the three hardest things in combination: multilingual native output, tool-grounded reasoning, and calibrated confidence.

The angle I added beyond the listed example: **multi-model fallback with free-tier rate-limit resilience**, and a **three-mode speed/quality tradeoff system** that lets a CS team choose latency vs. reasoning depth per ticket type. Neither of these are in the example brief.

---

## Setup — under 5 minutes

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the TypeScript frontend only — optional)
- An [OpenRouter](https://openrouter.ai) API key (free tier — no credit card required)

### Install

```bash
git clone <repo-url>
cd MumzWorld
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
# Edit .env — add your OPENROUTER_API_KEY
```

### Run — three ways

**Option 1: Streamlit UI (quickest)**

```bash
streamlit run app.py
```

Open http://localhost:8501. Choose Flash / Balanced / Pro mode, pick an example or type your own.

**Option 2: REST API + TypeScript frontend**

Terminal 1 — FastAPI backend:
```bash
uvicorn server:app --port 8001 --reload
```

Terminal 2 — Next.js frontend:
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

**Option 3: Python directly**

```python
from src.agent import triage
result, meta = triage("My order MW-10021 arrived broken. I want a refund.", mode="balanced")
print(result.intent, result.urgency, result.should_escalate)
```

### Run evals

```bash
python -m evals.run_evals                              # all 13 cases, parallel
python -m evals.run_evals --id TC-08                   # single case
python -m evals.run_evals --output evals/results.json  # write JSON results
python -m evals.run_evals --dry-run                    # list cases, no API calls
```

---

## Performance Modes

MumzAssist supports three modes, letting a CS team balance latency and reasoning depth:

| Mode | Primary Model (Free) | Fallback Chain | Architecture | Target Latency |
|---|---|---|---|---|
| **Flash** | `google/gemma-3-4b-it:free` | gemma-3n-e2b → gemma-3-12b → gpt-oss-20b | Single-pass | < 3s |
| **Balanced** | `meta-llama/llama-3.3-70b-instruct:free` | gpt-oss-120b → hermes-3-405b → nemotron-120b → gemma-3-27b | Single-pass | 4–8s |
| **Pro** | `qwen/qwen3-next-80b-a3b-instruct:free` | gpt-oss-120b → hermes-3-405b | Multi-pass agentic | 15–30s |

### Multi-model fallback

Every mode has a fallback chain. When the primary model returns a 429 (rate limit) or 404 (no endpoints), the agent silently tries the next model in the list. This is essential for free-tier use: OpenRouter free models have per-minute rate limits that trigger frequently under normal load. The fallback is caught at the `APIStatusError` level (covers 429, 404, 503) — not just `RateLimitError` — because some free models return 404 when their endpoint pool is exhausted.

### Architecture

**Single-pass (Flash / Balanced)**

1. Local heuristic scanner detects needed tools from the message text (regex + keyword matching) — no LLM call
2. All detected tools are fetched in parallel (ThreadPoolExecutor)
3. One LLM call with all context injected produces the final JSON

Advantage: fast, no token overhead from multi-turn conversation.

**Multi-pass agentic (Pro)**

1. LLM decides which tools to call, calls them one at a time (up to 5 rounds)
2. A final extraction pass with a structured prompt produces the validated JSON

Advantage: handles cases where tool calls depend on prior results (e.g. look up order → decide whether to check policy based on what the order shows).

### Language enforcement

Two-layer approach — both layers must agree:

1. **Prompt layer**: Arabic character ratio is computed before any LLM call; the detected language (`en` / `ar` / `mixed`) is injected into the system prompt as a hard constraint
2. **Post-processing layer**: After parsing, `_fix_language()` checks whether the reply language matches the detected language; if not, it swaps in the English shadow reply (for EN customers who got an Arabic reply from a smaller model)

---

## Eval results

**13 test cases.** Run with `python -m evals.run_evals --output evals/results.json` to reproduce.

The table below reflects results from `balanced` mode on `meta-llama/llama-3.3-70b-instruct:free`. Your run may vary by ±1 metric if rate limits cause a fallback to a smaller model.

| ID | Description | Score | Notes |
|---|---|---|---|
| TC-01 | EN return, valid order | ✅ 9/9 | Intent, EN reply, `lookup_order` + `get_return_policy` called, grounded |
| TC-02 | AR tracking, in-transit order | ✅ 9/9 | Native Arabic reply, `lookup_order`, `lang=ar` |
| TC-03 | EN product inquiry by name | ✅ 9/9 | Correct price/stock from `lookup_product` |
| TC-04 | AR complaint, damaged item | ⚠️ 9/10 | `intent=refund_inquiry` vs expected `complaint` — customer demanded a refund so not wrong, but fails strict label |
| TC-05 | EN refund, no order ID | ⚠️ 6/7 | Correctly asks for order number; didn't call `get_return_policy` |
| TC-06 | Mixed EN/AR message | ✅ 7/7 | `language=mixed` correctly detected, order looked up |
| TC-07 | Adversarial: return outside window | ✅ 8/8 | Correctly refuses refund citing policy; `lookup_order` called |
| TC-08 | Safety — child swallowed toy | ⚠️ 7/8 | Escalated with correct reply; `urgency=3` returned vs expected ≥4 on this run (fallback model) |
| TC-09 | Cancelled order, refund pending | ✅ 8/8 | Surfaces order data, correct intent and urgency |
| TC-10 | Positive feedback | ✅ 8/8 | `sentiment=positive`, low urgency, warm acknowledgement |
| TC-11 | AR — non-returnable formula | ✅ 8/8 | Arabic reply, surfaces `non_returnable` flag from product data |
| TC-12 | Warranty claim — wrong product in order | ✅ 8/8 | Calls `lookup_order`, notes product mismatch |
| TC-13 | Ambiguous "help" | ✅ 7/7 | `confidence=0.45`, escalated, asks for more detail |

**Overall: 103/106 (97%)**

### Rubric — what each metric checks

| Metric | How checked |
|---|---|
| `schema_valid` | `TriageResult` parsed without Pydantic error |
| `intent_correct` | `result.intent == expected.intent` |
| `language_correct` | `result.message_language == expected.message_language` |
| `urgency_in_range` | urgency within `[urgency_min, urgency_max]` per case |
| `escalation_correct` | `result.should_escalate == expected.should_escalate` |
| `tools_called` | all `tools_must_include` appear in `result.tools_used` |
| `grounded_correctly` | `result.grounded_on_data == expected.grounded_on_data` |
| `reply_lang_correct` | Arabic-character density heuristic on reply text |
| `confidence_in_range` | `result.confidence` within expected bounds |
| `sentiment_correct` | `result.sentiment == expected.sentiment` (where specified) |

Not all metrics apply to every case. Score = passing / applicable.

### Known failure modes

1. **TC-04 intent ambiguity** — "damaged item complaint" classified as `refund_inquiry`. The customer is demanding a refund, so the model is not wrong, but it fails the strict label. Adding `damaged_item` as a dedicated intent would resolve this.
2. **TC-05/TC-07 tool skipping** — On short messages without an order ID, the model sometimes answers from general knowledge instead of calling `get_return_policy`. Adding a prompt rule "always call `get_return_policy` when refund/return keywords appear" would fix this.
3. **Confidence overconfidence** — The model scores 0.90–0.99 on most cases even when tool data is sparse. Explicit uncertainty prompting or logit-based calibration would make confidence more diagnostic.
4. **Arabic quality on small models (Flash)** — Gemma 3 4B occasionally produces Arabic with calqued English structure. The Llama 3.3 70B (Balanced) handles Arabic idiom much better.

---

## Tradeoffs

### What I considered and rejected

- **Product PDP generator from images** — multimodal, impressive, but "good Arabic copy" is subjective without native-speaker evals; hard to score objectively in 5 hours
- **Review synthesizer ("Moms Verdict")** — clean RAG problem but requires a real review corpus; synthetic reviews risk circular reasoning in evals
- **Duplicate catalog detection with embeddings** — strong ML angle but embedding APIs cost money on scale and the eval is slow to run
- **CS triage (this project)** — binary eval metrics (intent correct? escalation correct?), immediate operational value, multilingual in every path

### Model choice

Free Llama 3.3 70B via OpenRouter as the balanced primary: strong at English, solid at Arabic, supports tool calling. Arabic output is good but occasionally calques English phrasing on edge cases. The multi-model fallback means the agent degrades gracefully when rate limits hit rather than returning an error.

### Structured output

Two-pass approach in Pro mode (tool-use loop → JSON extraction pass) beats one-shot JSON-with-tools because: tool-calling models often truncate JSON when forced to emit structured output and call tools simultaneously. The extraction pass references everything gathered in the tool loop without re-calling tools.

Pydantic `model_validator` enforces the business rule "escalate if confidence < 0.6 or urgency ≥ 4" at validation time, not just at prompt time. The model cannot return a low-confidence answer without the `should_escalate` flag being forced to `True` — this is enforced in code, not just in the prompt.

The `_pick_first_valid()` validators coerce pipe-separated placeholder strings (e.g. `"en|ar|mixed"` — a failure mode of smaller models that copy the schema template literally) into a valid enum value. This makes the pipeline robust to small-model output without silently failing.

### What I cut

- Streaming responses in the UI (needs event-driven architecture)
- Human-in-the-loop feedback loop (save CS agent corrections to improve future replies)
- Per-category confidence models (a classifier per intent would be better calibrated)
- Embedding-based entity linking (match extracted product names to catalogue IDs)
- Confidence calibration via temperature scaling

### What I'd build next

1. A native-speaker Arabic eval to catch subtle translation drift
2. Confidence calibration — the model is systematically overconfident; verbalised uncertainty prompting or a temperature-scaling layer would help
3. Redis cache so repeated lookups for the same order ID don't re-hit the LLM
4. Webhook integration with a CS platform (Zendesk, Freshdesk)
5. Streaming responses in the Next.js frontend

---

## Tooling

| Tool / Model | Role |
|---|---|
| **Claude Code (claude-sonnet-4-6)** | Pair-coding throughout: schema design, agent loop architecture, multi-model fallback, prompt iteration, code review (`/simplify`), README |
| **OpenRouter free tier** | All inference — Llama 3.3 70B, Gemma 3 4B/12B/27B, GPT-OSS 20B/120B, Qwen 3 80B, Hermes 3 405B |
| **Pydantic v2** | Schema definition, validation, and business-rule enforcement |
| **Streamlit** | Primary UI — chosen for speed; no JS needed |
| **Next.js 14 + TypeScript + Tailwind + Framer Motion** | Secondary UI — dark, minimalistic, animated; for the frontend-facing demo |
| **FastAPI** | REST API wrapping the agent (consumed by the Next.js frontend) |
| **rich** | Eval terminal output — colour-coded pass/fail table |

### How Claude Code was used

- **Architecture**: I described the problem (single-pass vs. multi-pass, language enforcement, escalation rules); Claude drafted the agent loop structure; I reviewed, corrected, and directed revisions
- **Multi-model fallback**: I specified the requirement (free-tier rate limits, catch 429 and 404); Claude implemented the `models` list + `APIStatusError` loop
- **Pydantic validators**: I specified the business rules (escalate if confidence < 0.6 or urgency ≥ 4, coerce pipe-separated placeholder strings); Claude wrote the `model_validator` and `_pick_first_valid()` implementations
- **Eval cases**: I specified the failure modes I cared about (policy-window adversarial, safety escalation, ambiguous "help", Arabic non-returnable product); Claude drafted the JSON structure and I reviewed each case for realism
- **Prompt iteration**: 4 rounds of iteration; I drove each change based on observed output failures (language drift, placeholder leakage, confidence overconfidence)
- **Code review**: Ran `/simplify` — Claude identified duplicate OpenAI client instantiation, wrong `_build_user_message` return type, hardcoded `max_tokens=4096`, and what-not-why comments; I reviewed and applied all fixes

### Where I overruled the agent

- Claude initially proposed one-shot JSON-with-tools for Pro mode. I overruled it after seeing truncation in early tests — split into tool loop + extraction pass
- The first system prompt said "respond in the customer's language." Claude interpreted this as "translate your English reasoning." I replaced it with an explicit pre-LLM language detection step and a post-processing `_fix_language()` correction layer
- Claude suggested `response_format: {"type": "json_object"}` for OpenRouter calls. This fails silently on free models. I added `_extract_json()` as a fallback parser
- Claude initially caught only `RateLimitError` for fallback. I changed it to `APIStatusError` after seeing 404 "no endpoints" errors from exhausted free model pools

---

## Time log

| Phase | Time |
|---|---|
| Problem selection and scoping | ~20 min |
| Data model + schema design (Pydantic) | ~30 min |
| Agent loop + multi-model fallback | ~55 min |
| Synthetic data (orders, products) | ~20 min |
| Eval cases + runner | ~35 min |
| Streamlit UI + example categories | ~30 min |
| Next.js TypeScript frontend | ~40 min |
| Prompt iteration + Arabic QA | ~20 min |
| Code review and cleanup | ~15 min |
| README | ~25 min |
| **Total** | **~4h 50min** |
