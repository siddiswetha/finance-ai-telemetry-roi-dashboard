-- 02_usage_by_use_case.sql
-- Usage and cost broken down by finance use case.
-- Shows which use cases drive volume and which drive cost.
SELECT
    use_case,
    COUNT(*) AS run_count,
    COUNT(DISTINCT user_id) AS distinct_users,
    SUM(prompt_tokens) AS total_prompt_tokens,
    SUM(completion_tokens) AS total_completion_tokens,
    SUM(prompt_tokens + completion_tokens) AS total_tokens,
    ROUND(SUM(cost_usd), 4) AS total_cost_usd,
    ROUND(AVG(cost_usd), 4) AS avg_cost_per_run_usd,
    ROUND(AVG(latency_ms), 1) AS avg_latency_ms
FROM usage_logs
GROUP BY use_case
ORDER BY total_cost_usd DESC;
