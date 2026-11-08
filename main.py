#!/usr/bin/env python3
"""Finance AI Telemetry & ROI Dashboard.

Reads synthetic AI usage logs (data/usage-logs.csv), loads them into
SQLite (Python standard library only), runs the SQL queries in sql/,
and writes a simple HTML dashboard to output/dashboard.html.

Usage:
    python3 main.py            # build the dashboard
    python3 main.py --eval     # run the eval suite (evals/eval.py)

No external dependencies. No API keys. All data is synthetic.
"""

import csv
import html
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "usage-logs.csv"
SQL_DIR = BASE_DIR / "sql"
OUTPUT_FILE = BASE_DIR / "output" / "dashboard.html"

# Invented per-token prices used when the log was created.
# They are only used to re-check that each row's cost matches its tokens.
TOKEN_RATES = {
    "finance-assistant-standard": 0.00005,
    "finance-assistant-large": 0.00012,
}

# Stated ROI assumption (invented, see README): each run a user marked
# "helpful" saves an estimated 20 minutes of analyst time at $45/hour.
SAVING_PER_HELPFUL_RUN_USD = 15.00

SQL_FILES = [
    ("01_cost_per_run.sql", "Cost per run (tracing view)"),
    ("02_usage_by_use_case.sql", "Usage by use case"),
    ("03_engagement.sql", "Engagement by use case"),
    ("04_roi.sql", "ROI summary"),
    ("05_daily_trend.sql", "Daily trend"),
]


def load_logs(conn):
    """Load the CSV into a SQLite table and return the row count."""
    conn.execute(
        """CREATE TABLE usage_logs (
            run_id TEXT,
            date TEXT,
            use_case TEXT,
            model TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            cost_usd REAL,
            latency_ms INTEGER,
            user_feedback TEXT,
            team TEXT,
            user_id TEXT
        )"""
    )
    with open(DATA_FILE, newline="") as f:
        rows = list(csv.DictReader(f))
    conn.executemany(
        "INSERT INTO usage_logs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                r["run_id"],
                r["date"],
                r["use_case"],
                r["model"],
                int(r["prompt_tokens"]),
                int(r["completion_tokens"]),
                float(r["cost_usd"]),
                int(r["latency_ms"]),
                r["user_feedback"],
                r["team"],
                r["user_id"],
            )
            for r in rows
        ],
    )
    return len(rows)


def run_query(conn, sql_path):
    """Run one .sql file and return (column names, rows)."""
    sql = sql_path.read_text()
    cur = conn.execute(sql)
    columns = [d[0] for d in cur.description]
    return columns, cur.fetchall()


def render_table(title, columns, rows):
    parts = [f"<h2>{html.escape(title)}</h2>", "<table><thead><tr>"]
    parts += [f"<th>{html.escape(c)}</th>" for c in columns]
    parts.append("</tr></thead><tbody>")
    for row in rows:
        parts.append("<tr>")
        parts += [f"<td>{html.escape(str(v))}</td>" for v in row]
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "\n".join(parts)


def build_dashboard():
    conn = sqlite3.connect(":memory:")
    row_count = load_logs(conn)

    summary = conn.execute(
        """SELECT COUNT(*),
                  ROUND(SUM(cost_usd), 4),
                  SUM(prompt_tokens + completion_tokens),
                  ROUND(AVG(cost_usd), 4),
                  ROUND(AVG(latency_ms), 1),
                  ROUND(100.0 * SUM(CASE WHEN user_feedback = 'helpful'
                      THEN 1 ELSE 0 END) / COUNT(*), 2),
                  COUNT(DISTINCT user_id),
                  COUNT(DISTINCT date)
           FROM usage_logs"""
    ).fetchone()
    (total_runs, total_cost, total_tokens, avg_cost, avg_latency,
     helpful_rate, distinct_users, distinct_days) = summary

    roi = conn.execute(
        """SELECT ROUND(SUM(CASE WHEN user_feedback = 'helpful'
                      THEN 1 ELSE 0 END) * ?, 2),
                  ROUND((SUM(CASE WHEN user_feedback = 'helpful'
                      THEN 1 ELSE 0 END) * ? - SUM(cost_usd)) / SUM(cost_usd), 2)
           FROM usage_logs""",
        (SAVING_PER_HELPFUL_RUN_USD, SAVING_PER_HELPFUL_RUN_USD),
    ).fetchone()
    estimated_savings, roi_ratio = roi

    sections = []
    for filename, title in SQL_FILES:
        columns, rows = run_query(conn, SQL_DIR / filename)
        sections.append(render_table(title, columns, rows))
    conn.close()

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Finance AI Telemetry &amp; ROI Dashboard</title>
<style>
body {{ font-family: sans-serif; margin: 2em; color: #222; }}
table {{ border-collapse: collapse; margin-bottom: 2em; }}
th, td {{ border: 1px solid #999; padding: 4px 8px; text-align: left; }}
th {{ background: #eee; }}
.card {{ display: inline-block; border: 1px solid #999; padding: 0.5em 1em;
        margin: 0.3em; }}
.card b {{ font-size: 1.4em; }}
.note {{ background: #fff8e1; border: 1px solid #e0c36a; padding: 0.8em; }}
</style>
</head>
<body>
<h1>Finance AI Telemetry &amp; ROI Dashboard</h1>
<p class="note"><b>Synthetic data.</b> Every number on this page comes from
invented example logs in <code>data/usage-logs.csv</code> (24 runs,
2026-10-01 to 2026-10-12). Nothing here is real company data, real spend,
or a real result. The dashboard shows the method, not a business outcome.</p>

<h2>Summary</h2>
<div class="card">Total runs<br><b>{total_runs}</b></div>
<div class="card">Total AI cost<br><b>${total_cost:.4f}</b></div>
<div class="card">Total tokens<br><b>{total_tokens:,}</b></div>
<div class="card">Avg cost / run<br><b>${avg_cost:.4f}</b></div>
<div class="card">Avg latency<br><b>{avg_latency:.1f} ms</b></div>
<div class="card">Helpful rate<br><b>{helpful_rate:.2f}%</b></div>
<div class="card">Active users<br><b>{distinct_users}</b></div>
<div class="card">Days covered<br><b>{distinct_days}</b></div>

<h2>ROI (stated assumption)</h2>
<p>Each run marked "helpful" is assumed to save an estimated 20 minutes of
analyst time at $45/hour = ${SAVING_PER_HELPFUL_RUN_USD:.2f} per helpful run.
That assumption is invented for this demo and must be replaced with measured
time savings before anyone relies on the ROI figure.</p>
<div class="card">Estimated savings<br><b>${estimated_savings:.2f}</b></div>
<div class="card">ROI ratio<br><b>{roi_ratio:.2f}x</b></div>

{''.join(sections)}

<h2>How to read this</h2>
<ul>
<li><b>Cost per run</b> is the tracing view: every run has an id, tokens,
cost, latency, feedback, use case, team and user, so any single run can be
audited.</li>
<li><b>Usage by use case</b> shows where volume and cost concentrate.
Forecasting costs the most per run here because it uses the larger model.</li>
<li><b>Engagement</b> is the share of runs users marked helpful. Low rates
(e.g. reporting at 60%) are the signal to investigate, not to hide.</li>
<li><b>ROI</b> is only as good as the time-saving assumption behind it.
Treat it as a method demo, not a claim.</li>
</ul>
<p>Queries: <code>sql/01_cost_per_run.sql</code> through
<code>sql/05_daily_trend.sql</code>. Eval suite: <code>python3 main.py --eval</code>.</p>
</body>
</html>
"""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(page)
    print(f"Loaded {row_count} synthetic log rows from {DATA_FILE.name}.")
    print(f"Total runs: {total_runs} | Total cost: ${total_cost:.4f} | "
          f"Total tokens: {total_tokens:,} | Avg cost/run: ${avg_cost:.4f}")
    print(f"Avg latency: {avg_latency:.1f} ms | Helpful rate: {helpful_rate:.2f}% | "
          f"Users: {distinct_users} | Days: {distinct_days}")
    print(f"Estimated savings: ${estimated_savings:.2f} | ROI ratio: {roi_ratio:.2f}x")
    print(f"Dashboard written to {OUTPUT_FILE}")
    return 0


def main(argv):
    if "--eval" in argv:
        sys.path.insert(0, str(BASE_DIR / "evals"))
        import eval as eval_module

        return eval_module.main()
    return build_dashboard()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
