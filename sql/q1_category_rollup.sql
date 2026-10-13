SELECT d.iso_week,g.group_name,count(*) event_count,
 count(*) FILTER(WHERE t.event_type='purchase') purchase_events
FROM fact_event f JOIN dim_date d USING(date_key) JOIN dim_product p USING(product_key)
JOIN dim_category c USING(category_key) JOIN dim_category_group g USING(group_key)
JOIN dim_event_type t USING(event_type_key)
WHERE f.event_date >= DATE '2019-10-01' AND f.event_date < DATE '2019-11-01'
GROUP BY ROLLUP(d.iso_week,g.group_name) ORDER BY 1 NULLS LAST,2 NULLS LAST;
