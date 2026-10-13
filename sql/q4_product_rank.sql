WITH p AS(SELECT d.iso_week,c.category_code,b.brand_name,p.product_id,count(*) purchase_events,
sum(f.price) purchase_event_value FROM fact_event f JOIN dim_date d USING(date_key)
JOIN dim_product p USING(product_key) JOIN dim_category c USING(category_key) JOIN dim_brand b USING(brand_key)
WHERE f.event_date>=DATE '2019-10-21' AND f.event_date<DATE '2019-10-28' AND f.event_type_key=3 GROUP BY 1,2,3,4)
SELECT *,dense_rank() OVER(PARTITION BY iso_week,category_code ORDER BY purchase_events DESC) category_rank
FROM p QUALIFY category_rank<=5 ORDER BY 1,2,category_rank,product_id;
