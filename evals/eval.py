#!/usr/bin/env python3
"""Eval suite for the Finance AI Telemetry & ROI Dashboard.

Rebuilds the SQLite table from data/usage-logs.csv, recomputes each
expected value in evals/eval-set.csv independently, and compares.
Writes evals/eval-results.csv and updates the `result` column of
evals/eval-set.csv with the true outcome of this run only.

Usage:
    python3 evals/eval.py
    python3 main.py --eval

Pass bar: all 12 tests must pass. A failure is recorded as failed,
never hidden or rounded away.
"""

import csv
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "usage-logs.csv"
EVAL_SET = BASE_DIR / "evals" / "eval-set.csv"
EVAL_RESULTS = BASE_DIR / "evals" / "eval-results.csv"

TOKEN_RATES = {
    "finance-assistant-standard": 0.00005,
    "finance-assistant-large": 0.00012,
}
SAVING_PER_HELPFUL_RUN_USD = 15.00


def build_db():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """CREATE TABLE usage_logs (
            run_id TEXT, date TEXT, use_case TEXT, model TEXT,
            prompt_tokens INTEGER, completion_tokens INTEGER,
            cost_usd REAL, latency_ms INTEGER, user_feedback TEXT,
            team TEXT, user_id TEXT
        )"""
    )
    with open(DATA_FILE, newline="") as f:
        rows = list(csv.DictReader(f))
    conn.executemany(
        "INSERT INTO usage_logs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            (r["run_id"], r["date"], r["use_case"], r["model"],
             int(r["prompt_tokens"]), int(r["completion_tokens"]),
             float(r["cost_usd"]), int(r["latency_ms"]),
             r["user_feedback"], r["team"], r["user_id"])
            for r in rows
        ],
    )
    return conn


def compute_actuals(conn):
    """Return {test_id: actual value as a string} for every test."""
    one = lambda sql, *a: conn.execute(sql, a).fetchone()[0]
    actuals = {}
    actuals["E01"] = str(one("SELECT COUNT(*) FROM usage_logs"))
    actuals["E02"] = f"{one('SELECT ROUND(SUM(cost_usd), 4) FROM usage_logs'):.4f}"
    actuals["E03"] = str(one("SELECT SUM(prompt_tokens) FROM usage_logs"))
    actuals["E04"] = str(one("SELECT SUM(completion_tokens) FROM usage_logs"))
    actuals["E05"] = f"{one('SELECT ROUND(AVG(cost_usd), 4) FROM usage_logs'):.4f}"
    helpful_sql = ("SELECT ROUND(100.0 * SUM(CASE WHEN user_feedback = ? "
                   "THEN 1 ELSE 0 END) / COUNT(*), 2) FROM usage_logs")
    actuals["E06"] = f"{one(helpful_sql, 'helpful'):.2f}"
    runs, cost = conn.execute(
        "SELECT COUNT(*), ROUND(SUM(cost_usd), 4) FROM usage_logs "
        "WHERE use_case = 'reconciliation'"
    ).fetchone()
    actuals["E07"] = f"{runs} runs, {cost:.4f} USD"
    forecast_sql = ("SELECT ROUND(SUM(cost_usd), 4) FROM usage_logs "
                    "WHERE use_case = 'forecasting'")
    actuals["E08"] = f"{one(forecast_sql):.4f}"
    mismatches = 0
    for model, pt, ct, cost in conn.execute(
        "SELECT model, prompt_tokens, completion_tokens, cost_usd FROM usage_logs"
    ):
        if round((pt + ct) * TOKEN_RATES[model], 4) != round(cost, 4):
            mismatches += 1
    actuals["E09"] = f"{mismatches} mismatches"
    helpful = one(
        "SELECT COUNT(*) FROM usage_logs WHERE user_feedback = 'helpful'"
    )
    total_cost = one("SELECT SUM(cost_usd) FROM usage_logs")
    roi = (helpful * SAVING_PER_HELPFUL_RUN_USD - total_cost) / total_cost
    actuals["E10"] = f"{roi:.2f}"
    actuals["E11"] = str(one("SELECT COUNT(DISTINCT user_id) FROM usage_logs"))
    max_lat, run_id = conn.execute(
        "SELECT latency_ms, run_id FROM usage_logs "
        "ORDER BY latency_ms DESC LIMIT 1"
    ).fetchone()
    actuals["E12"] = f"{max_lat} ms ({run_id})"
    return actuals


def main():
    conn = build_db()
    actuals = compute_actuals(conn)
    conn.close()

    with open(EVAL_SET, newline="") as f:
        tests = list(csv.DictReader(f))

    # Guard: a malformed row (e.g. an unquoted comma) would silently
    # shift columns and drop tests. Fail loudly instead.
    if any(None in t for t in tests):
        bad = [t.get("test_id") for t in tests if None in t]
        raise SystemExit(f"eval-set.csv is malformed (extra columns) in rows: {bad}")
    if len(tests) != 12:
        raise SystemExit(f"eval-set.csv should have 12 tests, found {len(tests)}")

    results = []
    passed = 0
    for t in tests:
        test_id = t["test_id"]
        expected = t["expected_outcome"]
        actual = actuals.get(test_id, "NO CHECK DEFINED")
        ok = actual == expected
        passed += 1 if ok else 0
        status = "PASS" if ok else "FAIL"
        results.append({
            "test_id": test_id,
            "expected_outcome": expected,
            "actual_outcome": actual,
            "result": status,
        })
        print(f"{test_id}: {status} (expected {expected!r}, got {actual!r})")
        t["result"] = status

    with open(EVAL_RESULTS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["test_id", "expected_outcome",
                                          "actual_outcome", "result"])
        w.writeheader()
        w.writerows(results)

    with open(EVAL_SET, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["test_id", "case_description",
                                          "expected_outcome", "rubric",
                                          "pass_bar", "result"])
        w.writeheader()
        w.writerows(tests)

    total = len(tests)
    print(f"\nEval result: {passed}/{total} passed.")
    print(f"Pass bar: all {total} tests must pass. "
          f"{'MET' if passed == total else 'NOT MET'}")
    print(f"Results written to {EVAL_RESULTS}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
