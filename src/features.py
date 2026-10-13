import duckdb,json,time,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run():
 os.chdir(ROOT);t=time.perf_counter();c=duckdb.connect('data/warehouse.duckdb');c.execute("SET threads=2;SET memory_limit='2GB'")
 c.execute('''CREATE OR REPLACE TABLE session_features AS
 WITH base AS(SELECT f.session_key,count(*) n_events,count(DISTINCT p.product_id) n_products,count(DISTINCT p.category_key) n_categories,
 count(*) FILTER(WHERE event_type_key=1) n_views,count(*) FILTER(WHERE event_type_key=2) carts,count(*) FILTER(WHERE event_type_key=3) purchases,
 avg(price)::DOUBLE mean_price,stddev_pop(price)::DOUBLE sd_price,avg(gap_seconds) mean_gap,stddev_pop(gap_seconds) sd_gap,
 sum(repeated_same_second)::DOUBLE/count(*) repeat_rate,avg(brand_missing::INT) missing_brand_rate,avg(category_missing::INT) missing_category_rate
 FROM fact_event f JOIN dim_product p USING(product_key) GROUP BY f.session_key),
 cats AS(SELECT session_key,category_key,count(*) n FROM fact_event JOIN dim_product USING(product_key) GROUP BY ALL),
 ent AS(SELECT session_key,-sum((n::DOUBLE/n_events)*ln(n::DOUBLE/n_events)) category_entropy FROM cats JOIN base USING(session_key) GROUP BY session_key)
 SELECT b.*,s.start_ts,s.end_ts,epoch(s.end_ts-s.start_ts) duration_seconds,
 greatest(n_events-1,0)*60.0/greatest(epoch(s.end_ts-s.start_ts),1) events_per_minute,
 carts::DOUBLE/n_events cart_rate,purchases::DOUBLE/n_events purchase_rate,e.category_entropy,
 CASE WHEN s.start_ts<'2019-10-22' AND s.end_ts<'2019-10-22' THEN 'train'
 WHEN s.start_ts>='2019-10-22' AND s.end_ts<'2019-10-25' THEN 'validation'
 WHEN s.start_ts>='2019-10-25' THEN 'test' ELSE 'boundary_excluded' END split
 FROM base b JOIN dim_session s USING(session_key) JOIN ent e USING(session_key)''')
 c.execute("COPY session_features TO 'data/session_features.parquet' (FORMAT PARQUET,COMPRESSION ZSTD)")
 stats=c.sql('select split,count(*) n,min(start_ts) earliest,max(end_ts) latest from session_features group by split order by split').df()
 stats.to_csv('results/session_splits.csv',index=False)
 c.sql('select e.event_type,count(*) n from fact_event f join dim_event_type e using(event_type_key) group by 1 order by n desc').df().to_csv('results/event_mix.csv',index=False)
 c.sql('select event_date,count(*) events,count(*) filter(where event_type_key=3) purchases from fact_event group by 1 order by 1').df().to_csv('results/daily_events.csv',index=False)
 c.sql('select p.relative_day,p.hour_in_day,count(*) transactions,sum(o.is_fraud) frauds from fact_card_transaction f join dim_elapsed_period p using(period_key) join card_outcome o using(transaction_key) group by 1,2 order by 1,2').df().to_csv('results/card_hourly.csv',index=False)
 c.execute('CHECKPOINT');c.close();(ROOT/'results/feature_run.json').write_text(json.dumps({'seconds':time.perf_counter()-t,'splits':stats.to_dict('records')},default=str,indent=2))
if __name__=='__main__':run()
