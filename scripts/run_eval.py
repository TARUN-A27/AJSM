"""
Runs the golden-answer eval set (reference/eval/golden_answers.json — gitignored, contains
real business figures) against the live app pipeline: generate_sql -> validate -> execute.
Server-only (Oracle/Ollama access), same as check_schema_access.py — see CLAUDE.md §8.

Usage: ./venv/bin/python scripts/run_eval.py
"""

import json
import sys
import time
from pathlib import Path

from app.oracle_client import OracleExecutionError, run_safe_select
from app.sql_generator import SQLGenerationError, generate_sql
from app.sql_safety import SQLSafetyError, validate_select_only

GOLDEN_PATH = Path(__file__).resolve().parent.parent / "reference" / "eval" / "golden_answers.json"


def _matches(actual, expected) -> bool:
    if actual is None:
        return False
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(float(actual) - float(expected)) < 0.01
    return str(actual).strip().upper() == str(expected).strip().upper()


def run_one(entry: dict) -> dict:
    question = entry["question"]
    result = {"id": entry["id"], "family": entry["family"], "question": question}
    sql = None

    try:
        sql = generate_sql(question)
        validate_select_only(sql)
        exec_result = run_safe_select(sql)
    except (SQLGenerationError, SQLSafetyError, OracleExecutionError) as exc:
        result.update(status="ERROR", detail=f"{type(exc).__name__}: {exc}", sql=sql, actual=None)
        return result

    rows = exec_result["rows"]
    actual = rows[0][0] if len(rows) == 1 and len(rows[0]) == 1 else None
    status = "PASS" if _matches(actual, entry["golden_answer"]) else "FAIL"

    result.update(
        status=status,
        sql=sql,
        actual=actual,
        row_shape=f"{len(rows)}x{len(exec_result['columns'])}",
        golden_answer=entry["golden_answer"],
    )
    return result


def main():
    with open(GOLDEN_PATH) as f:
        golden = json.load(f)

    results = []
    for entry in golden["questions"]:
        started = time.time()
        r = run_one(entry)
        r["elapsed_s"] = round(time.time() - started, 1)
        results.append(r)
        print(f"[{r['status']:5s}] #{r['id']} ({r['family']}) {r['question']!r} ({r['elapsed_s']}s)")
        if r["status"] != "PASS":
            print(f"        expected={entry['golden_answer']!r} actual={r.get('actual')!r}")
            print(f"        sql={r.get('sql')!r}")
            if r.get("detail"):
                print(f"        error={r['detail']}")

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    print(f"\n{passed}/{total} passed")

    by_family: dict[str, list[dict]] = {}
    for r in results:
        by_family.setdefault(r["family"], []).append(r)
    for family, items in sorted(by_family.items()):
        fam_passed = sum(1 for r in items if r["status"] == "PASS")
        print(f"  {family}: {fam_passed}/{len(items)}")

    out_path = Path(__file__).resolve().parent.parent / "reference" / "eval" / "last_run_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nFull results: {out_path}")

    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
