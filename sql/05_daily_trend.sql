-- 05_daily_trend.sql
-- Daily trend: runs, cost and helpful rate per day.
-- Lets a reader spot spikes (for example a costly day) at a glance.
SELECT
    date,
    COUNT(*) AS run_count,
    ROUND(SUM(cost_usd), 4) AS total_cost_usd,
    ROUND(AVG(latency_ms), 1) AS avg_latency_ms,
    ROUND(100.0 * SUM(CASE WHEN user_feedback = 'helpful' THEN 1 ELSE 0 END) / COUNT(*), 2) AS helpful_rate_pct
FROM usage_logs
GROUP BY date
ORDER BY date;
