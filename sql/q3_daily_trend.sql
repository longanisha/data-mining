WITH daily AS(SELECT f.event_date,g.group_name,count(*) events,
sum(CASE WHEN t.event_type='purchase' THEN f.price ELSE 0 END) purchase_event_value
FROM fact_event f JOIN dim_product p USING(product_key) JOIN dim_category c USING(category_key)
JOIN dim_category_group g USING(group_key) JOIN dim_event_type t USING(event_type_key)
WHERE f.event_date>=DATE '2019-10-01' AND f.event_date<DATE '2019-11-01' GROUP BY 1,2)
SELECT *,lag(events) OVER w previous_observed_day_events,
avg(events) OVER(PARTITION BY group_name ORDER BY event_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) moving_observation_mean
FROM daily WINDOW w AS(PARTITION BY group_name ORDER BY event_date) ORDER BY 1,2;
