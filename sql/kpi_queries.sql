
-- Example KPI query: monthly paid totals by region and network
SELECT
  date_trunc('month', c.service_date) AS month,
  m.region,
  p.in_network,
  COUNT(*) AS claims,
  SUM(c.paid_amount) AS paid_total,
  AVG(c.paid_amount) AS paid_avg
FROM insurance.claim c
JOIN insurance.member m ON m.member_id = c.member_id
JOIN insurance.provider p ON p.provider_id = c.provider_id
GROUP BY 1,2,3
ORDER BY 1,2,3;
