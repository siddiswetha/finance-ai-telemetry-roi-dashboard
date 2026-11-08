-- 04_roi.sql
-- ROI summary for the whole period.
-- Estimated saving assumption (invented, stated in the README):
-- each run a user marked "helpful" saves an estimated 20 minutes of
-- analyst time, valued at $45 per hour = $15.00 per helpful run.
-- ROI = (estimated savings - total AI cost) / total AI cost.
-- The numbers below come from the log itself; only the $15.00 per
-- helpful run is an assumption, and it is labelled as one.
SELECT
    COUNT(*) AS total_runs,
    SUM(CASE WHEN user_feedback = 'helpful' THEN 1 ELSE 0 END) AS helpful_runs,
    ROUND(SUM(cost_usd), 4) AS total_cost_usd,
    ROUND(SUM(CASE WHEN user_feedback = 'helpful' THEN 1 ELSE 0 END) * 15.00, 2) AS estimated_savings_usd,
    ROUND(SUM(CASE WHEN user_feedback = 'helpful' THEN 1 ELSE 0 END) * 15.00 - SUM(cost_usd), 2) AS estimated_net_value_usd,
    ROUND((SUM(CASE WHEN user_feedback = 'helpful' THEN 1 ELSE 0 END) * 15.00 - SUM(cost_usd)) / SUM(cost_usd), 2) AS roi_ratio
FROM usage_logs;
