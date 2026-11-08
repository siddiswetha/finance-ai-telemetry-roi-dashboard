# Finance AI Telemetry & ROI Dashboard

A small, from-scratch telemetry and ROI reporting tool for AI assistants used
in Finance work. It takes synthetic AI usage logs, loads them into SQLite,
runs plain SQL queries, and produces a simple HTML dashboard that leadership
could actually read: how much the AI costs, which finance use cases drive
usage, whether users find it helpful, and what the return looks like under a
clearly stated assumption.

**All data is synthetic.** Every log row, cost, token count and user is
invented example data for demonstrating the method. Nothing here is real
company data, real spend, or a real business result.

## What it is, in plain words

Imagine a Finance team using an AI assistant to help with reconciliation,
forecasting, reporting, month-end close checklists, vendor invoices and
budget checks. Every time someone uses the assistant, the system writes one
log line: who used it, for what, how many tokens it used, what it cost, how
long it took, and whether the user marked it helpful.

This project collects those log lines and answers four questions a Finance
leader would ask:

1. **What does each run cost?** One row per run, so any single run can be
   traced and audited.
2. **Where does usage and cost concentrate?** Broken down by use case, model
   and team.
3. **Do people find it helpful?** The share of runs marked helpful, per use
   case — the engagement signal.
4. **Is it worth it?** An ROI figure built from a stated assumption (see
   below), shown next to the assumption so nobody mistakes it for a fact.

## How this fits Swetha's actual background

Author: Venkata Swetha Siddi. Actual resume: 4+ years in ML and analytics, enterprise networking, and cloud automation, now focused on AI/ML engineering and applied AI. Certified by Anthropic in Claude and the AI Fluency Framework (Claude 101 and AI Fluency Framework & Foundations, June 2026). Skills on that resume include ML evaluation, EDA, feature engineering, model benchmarking with scikit-learn, SQL, Python, FastAPI, GitHub Actions, Docker, and Kubernetes. Experience on that resume includes Data Scientist, Cognizant, Dec 2019–Apr 2022, with end-to-end ML, scikit-learn, evaluation, dashboards, and stakeholder narratives; and Network Engineer, Relic Solutions, Elmont, NY, Oct 2025–Feb 2026.

## Role skill mapping

This project is built as a Finance AI Engineer portfolio project. It demonstrates:

| AI Engineer requirement | Where this project shows it |
|---|---|
| Build AI telemetry — usage, cost, engagement, ROI reporting | `main.py` + `sql/` + `output/dashboard.html` |
| Dashboards leadership relies on | The HTML dashboard: summary cards, per-use-case and daily tables |
| Validate outputs so they are explainable and auditable | Every run has a `run_id` with tokens, cost, latency and feedback; the cost-tracing eval (E09) re-checks every row's cost from its tokens |
| Working Python for automation / prototyping | `main.py` and `evals/eval.py`, Python standard library only |
| Basic SQL with Finance-grade rigor | Five `.sql` files with grouped, rounded, auditable aggregates |
| Evaluation, tracing, observability | `evals/eval-set.csv` (12 tests) and `evals/eval.py`; tracing fields on every run |
| Finance processes (close, reconciliation, forecasting, reporting) | Use cases in the log: reconciliation, forecasting, reporting, close-checklist, vendor-invoice-review, budget-variance |

## How it works

```
data/usage-logs.csv  --(csv)-->  SQLite table `usage_logs`  --(sql/*.sql)-->
summary numbers + tables  --(HTML)-->  output/dashboard.html
```

1. `main.py` reads `data/usage-logs.csv` (24 synthetic runs, 2026-10-01 to
   2026-10-12, 8 invented users across 4 teams).
2. It loads the rows into an in-memory SQLite database — no server, no
   setup, no external service.
3. It runs the five queries in `sql/` and renders the results into
   `output/dashboard.html`.
4. `evals/eval.py` independently recomputes 12 expected values and compares
   them to the hand-computed figures in `evals/eval-set.csv`.

Tracing fields on every run: `run_id`, `date`, `use_case`, `model`,
`prompt_tokens`, `completion_tokens`, `cost_usd`, `latency_ms`,
`user_feedback` (helpful / not helpful), `team`, `user_id`.

## How to run

Requirements: Python 3.8 or newer. **No external dependencies, no API key.**

```bash
cd finance-ai-telemetry-roi-dashboard
python3 main.py            # builds output/dashboard.html
python3 main.py --eval     # runs the eval suite (same as python3 evals/eval.py)
```

Then open `output/dashboard.html` in any browser. No server needed.

## The SQL queries

| File | What it answers |
|---|---|
| `sql/01_cost_per_run.sql` | Cost, tokens and latency for every run (tracing view) |
| `sql/02_usage_by_use_case.sql` | Usage and cost by finance use case |
| `sql/03_engagement.sql` | Helpful rate by use case |
| `sql/04_roi.sql` | ROI summary for the whole period |
| `sql/05_daily_trend.sql` | Runs, cost and helpful rate per day |

Example — usage by use case:

```sql
SELECT
    use_case,
    COUNT(*) AS run_count,
    ROUND(SUM(cost_usd), 4) AS total_cost_usd,
    ROUND(AVG(cost_usd), 4) AS avg_cost_per_run_usd,
    ROUND(AVG(latency_ms), 1) AS avg_latency_ms
FROM usage_logs
GROUP BY use_case
ORDER BY total_cost_usd DESC;
```

## Results on the synthetic data

These numbers come from the invented log only — they demonstrate the
reporting, they are not real results:

- **24 runs**, **48,240 tokens** (35,150 prompt + 13,090 completion)
- **Total AI cost: $3.8946**, average **$0.1623 per run**
- **Average latency: 2,129.2 ms**; slowest run R012 at 3,540 ms
- **Helpful rate: 83.33%** (20 of 24 runs marked helpful)
- Costliest use case: **forecasting, $1.3726** across 5 runs (it uses the
  larger model most); cheapest per run: **close-checklist, $0.0518**
- Lowest helpful rate: **reporting, 60%** (3 of 5) — the first place to
  investigate, not to hide

### ROI — read the assumption first

The ROI figure rests on one invented assumption: each run a user marked
"helpful" saves an estimated **20 minutes of analyst time at $45/hour =
$15.00 per helpful run**. That is a placeholder, not a measurement.

- Estimated savings: 20 helpful runs x $15.00 = **$300.00**
- Total AI cost: **$3.8946**
- ROI ratio: **(300.00 − 3.8946) / 3.8946 = 76.03x**

A real deployment must replace the $15.00 with measured time savings
before anyone relies on the ROI number. The dashboard states the
assumption next to the figure for exactly that reason.

## Eval pass bar

**Pass bar: all 12 tests in `evals/eval-set.csv` must pass.** The eval
script recomputes each expected value from the CSV and compares it to the
hand-computed figure; results are recorded in `evals/eval-results.csv`
and in the `result` column of `evals/eval-set.csv`.

Run on 2026-11-07: **12/12 passed** — total cost, token totals, average
cost, helpful rate, reconciliation and forecasting figures, the per-row
cost re-check (0 mismatches), the ROI formula, distinct users, and the
slowest-run trace all matched. See `evals/eval-results.csv` for the
per-test actual vs. expected values.

## Risks and guardrails

- **Synthetic data only.** Never point this at real logs containing real
  names, real spend or real prompts without a privacy review. The demo
  users (`U101`–`U108`) are invented IDs, not people.
- **The ROI assumption is invented.** The $15.00-per-helpful-run figure
  is a placeholder. Presenting it without the assumption would be
  misleading; the dashboard always shows them together.
- **Feedback is self-reported.** "Helpful" is a single click from the
  user, not a quality grade. A high helpful rate does not prove the
  output was correct — Finance outputs need a separate accuracy check
  before they reach a report or a close.
- **Cost is token-based only.** Real AI cost also includes hosting,
  retries, evaluation and human review time. This tool tracks the
  token bill, not the full cost of ownership.
- **No real data leaves the machine.** The tool runs locally, uses only
  the Python standard library, and makes no network calls.

## Staged release note

If this were taken from demo to real use, the safe order would be:

1. **Stage 1 — shadow mode.** Log runs and build the dashboard, but change
   nothing. Check that costs reconcile to the vendor bill and that every
   run traces to a `run_id`.
2. **Stage 2 — one team, one use case.** Roll the dashboard out to a single
   team (e.g. Finance Ops on reconciliation) and replace the invented
   $15.00 saving with measured time saved.
3. **Stage 3 — wider rollout.** Add use cases one at a time, keep the
   helpful-rate and accuracy checks per use case, and only then use the
   ROI figure in leadership reporting.

## Project layout

```
finance-ai-telemetry-roi-dashboard/
├── README.md
├── main.py                  # stdlib-only pipeline: CSV -> SQLite -> HTML dashboard
├── .gitignore
├── data/
│   └── usage-logs.csv       # 24 synthetic log rows (SYNTHETIC)
├── sql/
│   ├── 01_cost_per_run.sql
│   ├── 02_usage_by_use_case.sql
│   ├── 03_engagement.sql
│   ├── 04_roi.sql
│   └── 05_daily_trend.sql
├── evals/
│   ├── eval-set.csv         # 12 test cases with hand-computed expectations
│   ├── eval.py              # runs the tests, writes eval-results.csv
│   └── eval-results.csv     # filled in by the eval run
└── output/
    └── dashboard.html       # generated by `python3 main.py` (git-ignored)
```

## Author note

Built from scratch as a portfolio project. Original synthetic data, original
code, original SQL and original eval cases — nothing copied from any other
project.
