-- Cohort is visits starting in the chosen day. A stage means observed, not ordered completion.
SELECT hour(s.start_ts) start_hour,g.group_name,
count(DISTINCT f.session_key) observed_visits,
count(DISTINCT f.session_key) FILTER(WHERE t.event_type='cart') cart_visits,
count(DISTINCT f.session_key) FILTER(WHERE t.event_type='purchase') purchase_visits
FROM fact_event f JOIN dim_session s USING(session_key) JOIN dim_product p USING(product_key)
JOIN dim_category c USING(category_key) JOIN dim_category_group g USING(group_key)
JOIN dim_event_type t USING(event_type_key)
WHERE f.event_date >= DATE '2019-10-25' AND f.event_date < DATE '2019-10-27'
AND s.start_ts >= TIMESTAMP '2019-10-25' AND s.start_ts < TIMESTAMP '2019-10-26'
GROUP BY 1,2 ORDER BY 1,2;
