-- 03_engagement.sql
-- Engagement: how often users found each use case helpful.
-- "helpful" means the user marked the run helpful in the log.
SELECT
    use_case,
    COUNT(*) AS run_count,
    SUM(CASE WHEN user_feedback = 'helpful' THEN 1 ELSE 0 END) AS helpful_runs,
    SUM(CASE WHEN user_feedback = 'not helpful' THEN 1 ELSE 0 END) AS not_helpful_runs,
    ROUND(100.0 * SUM(CASE WHEN user_feedback = 'helpful' THEN 1 ELSE 0 END) / COUNT(*), 2) AS helpful_rate_pct
FROM usage_logs
GROUP BY use_case
ORDER BY helpful_rate_pct ASC, run_count DESC;
