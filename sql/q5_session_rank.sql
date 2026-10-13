WITH visits AS(SELECT s.session_key,u.user_key,count(*) events,epoch(max(f.event_ts)-min(f.event_ts)) duration_seconds,
count(*) FILTER(WHERE f.event_type_key=3) purchases FROM fact_event f
JOIN dim_session s USING(session_key) JOIN dim_user u USING(user_key)
WHERE f.event_date>=DATE '2019-10-31' AND f.event_date<DATE '2019-11-01' GROUP BY 1,2)
SELECT *,greatest(events-1,0)*60.0/greatest(duration_seconds,1) events_per_minute,
row_number() OVER(ORDER BY events DESC,session_key) activity_rank
FROM visits ORDER BY activity_rank LIMIT 100;
