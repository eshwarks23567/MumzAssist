"""
Eval runner for MumzAssist.

Usage:
    python -m evals.run_evals              # run all cases
    python -m evals.run_evals --id TC-01  # run single case
    python -m evals.run_evals --dry-run   # print cases without calling API

Scoring rubric (each metric 0 or 1, score = passing / applicable):
  - schema_valid        : TriageResult parsed without error
  - intent_correct      : classified intent matches expected
  - language_correct    : detected message_language matches expected
  - urgency_in_range    : urgency within [urgency_min, urgency_max] bounds
  - escalation_correct  : should_escalate matches expected (if specified)
  - tools_called        : all tools_must_include were actually called
  - grounded_correctly  : grounded_on_data matches expected (if specified)
  - reply_lang_correct  : reply is in the expected language (heuristic check)
  - confidence_in_range : confidence within [confidence_min, confidence_max] bounds
  - sentiment_correct   : sentiment matches expected (if specified)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.table import Table

# Force UTF-8 on Windows so rich symbols don't crash cp1252
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Allow running as `python -m evals.run_evals` from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import triage
from src.schemas import TriageResult

console = Console()

CASES_PATH = Path(__file__).parent / "test_cases.json"


def load_cases(filter_id: Optional[str] = None) -> List[Dict]:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if filter_id:
        cases = [c for c in cases if c["id"] == filter_id]
    return cases


# ── Heuristic reply-language check ────────────────────────────────────────────

_AR_CHARS = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")


def _is_arabic(text: str) -> bool:
    ar = sum(1 for ch in text if ch in _AR_CHARS)
    return ar / max(len(text), 1) > 0.15


def _reply_language(reply: str) -> str:
    return "ar" if _is_arabic(reply) else "en"


# ── Metric checks ─────────────────────────────────────────────────────────────

def evaluate(result: TriageResult, expected: Dict[str, Any]) -> Dict[str, Optional[bool]]:
    metrics: Dict[str, Optional[bool]] = {}

    # intent
    if "intent" in expected:
        metrics["intent_correct"] = result.intent == expected["intent"]

    # language
    if "message_language" in expected:
        metrics["language_correct"] = result.message_language == expected["message_language"]

    # urgency
    lo = expected.get("urgency_min", 1)
    hi = expected.get("urgency_max", 5)
    metrics["urgency_in_range"] = lo <= result.urgency <= hi

    # escalation
    if "should_escalate" in expected:
        metrics["escalation_correct"] = result.should_escalate == expected["should_escalate"]

    # tools
    if "tools_must_include" in expected:
        required = set(expected["tools_must_include"])
        called = set(result.tools_used)
        metrics["tools_called"] = required.issubset(called)

    # grounding
    if "grounded_on_data" in expected:
        metrics["grounded_correctly"] = result.grounded_on_data == expected["grounded_on_data"]

    # reply language
    if "reply_language" in expected:
        actual_lang = _reply_language(result.suggested_reply_original_language)
        metrics["reply_lang_correct"] = actual_lang == expected["reply_language"]

    # confidence
    c_min = expected.get("confidence_min", 0.0)
    c_max = expected.get("confidence_max", 1.0)
    metrics["confidence_in_range"] = c_min <= result.confidence <= c_max

    # sentiment
    if "sentiment" in expected:
        metrics["sentiment_correct"] = result.sentiment == expected["sentiment"]

    return metrics


def score(metrics: Dict[str, Optional[bool]]) -> Tuple[int, int]:
    applicable = {k: v for k, v in metrics.items() if v is not None}
    passing = sum(1 for v in applicable.values() if v)
    return passing, len(applicable)


# ── Runner ────────────────────────────────────────────────────────────────────

def run_case(case: Dict, dry_run: bool = False) -> Dict:
    case_id = case["id"]
    description = case["description"]
    message = case["input"]
    expected = case["expected"]

    console.print(f"\n[bold cyan]>> {case_id}[/bold cyan] - {description}")
    console.print(f"  Input: [italic]{message[:120]}{'…' if len(message) > 120 else ''}[/italic]")

    if dry_run:
        return {"id": case_id, "status": "skipped"}

    schema_valid = True
    result: Optional[TriageResult] = None
    error_msg = ""

    try:
        start = time.time()
        result, meta = triage(message)
        elapsed = time.time() - start
        console.print(f"  [green]✓ Parsed OK[/green] ({elapsed:.1f}s) | intent={result.intent} | lang={result.message_language} | urgency={result.urgency} | conf={result.confidence:.2f}")
    except Exception as exc:
        schema_valid = False
        error_msg = str(exc)
        elapsed = 0.0
        console.print(f"  [red]✗ ERROR: {error_msg[:200]}[/red]")

    if not schema_valid or result is None:
        return {
            "id": case_id,
            "description": description,
            "status": "error",
            "error": error_msg,
            "metrics": {"schema_valid": False},
            "score": (0, 1),
        }

    metrics = evaluate(result, expected)
    metrics["schema_valid"] = True
    p, total = score(metrics)

    for metric, passed in metrics.items():
        icon = "[green]✓[/green]" if passed else "[red]✗[/red]"
        console.print(f"    {icon} {metric}")

    console.print(f"  [bold]Score: {p}/{total}[/bold]")

    return {
        "id": case_id,
        "description": description,
        "status": "ok",
        "input": message,
        "result": result.model_dump(),
        "metrics": metrics,
        "score": (p, total),
        "elapsed_s": round(elapsed, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="MumzAssist eval runner")
    parser.add_argument("--id", help="Run a single test case by ID")
    parser.add_argument("--dry-run", action="store_true", help="List cases without calling API")
    parser.add_argument("--output", help="Write JSON results to file")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers (default 4)")
    args = parser.parse_args()

    cases = load_cases(filter_id=args.id)
    if not cases:
        console.print("[red]No cases matched.[/red]")
        sys.exit(1)

    console.print(f"\n[bold]MumzAssist Eval Suite — {len(cases)} case(s)[/bold]")
    if not args.dry_run and len(cases) > 1:
        console.print(f"[dim]Running {min(args.workers, len(cases))} cases in parallel[/dim]")
    console.print("=" * 60)

    if args.dry_run or len(cases) == 1:
        results = [run_case(c, dry_run=args.dry_run) for c in cases]
    else:
        # Parallel execution — results may arrive out of order, print as they complete
        id_order = {c["id"]: i for i, c in enumerate(cases)}
        results_map: Dict[str, Dict] = {}
        with ThreadPoolExecutor(max_workers=min(args.workers, len(cases))) as pool:
            futures = {pool.submit(run_case, c): c["id"] for c in cases}
            for fut in as_completed(futures):
                r = fut.result()
                results_map[r["id"]] = r
        results = [results_map[c["id"]] for c in cases]  # restore original order

    # Summary table
    if not args.dry_run:
        console.print("\n" + "=" * 60)
        console.print("[bold]Summary[/bold]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", width=8)
        table.add_column("Description", width=40)
        table.add_column("Score", justify="right")
        table.add_column("Status")

        total_p, total_t = 0, 0
        for r in results:
            p, t = r.get("score", (0, 0))
            total_p += p
            total_t += t
            pct = f"{p}/{t} ({100*p//t if t else 0}%)" if t else "N/A"
            status_icon = "✓" if r["status"] == "ok" and p == t else ("✗" if r["status"] == "error" else "~")
            color = "green" if p == t and t > 0 else ("red" if r["status"] == "error" else "yellow")
            table.add_row(r["id"], r["description"][:38], pct, f"[{color}]{status_icon}[/{color}]")

        console.print(table)

        overall_pct = 100 * total_p // total_t if total_t else 0
        console.print(f"\n[bold]Overall: {total_p}/{total_t} ({overall_pct}%)[/bold]")

        if args.output:
            Path(args.output).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            console.print(f"Results written to [cyan]{args.output}[/cyan]")


if __name__ == "__main__":
    main()
