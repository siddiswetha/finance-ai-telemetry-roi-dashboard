-- 01_cost_per_run.sql
-- Cost, tokens and latency for every individual run (tracing view).
-- One row per run_id so any single run can be audited end to end.
SELECT
    run_id,
    date,
    use_case,
    model,
    prompt_tokens,
    completion_tokens,
    prompt_tokens + completion_tokens AS total_tokens,
    cost_usd,
    ROUND(cost_usd / (prompt_tokens + completion_tokens), 6) AS cost_per_token_usd,
    latency_ms,
    user_feedback,
    team,
    user_id
FROM usage_logs
ORDER BY date, run_id;
