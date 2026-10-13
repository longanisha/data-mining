import duckdb,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
c=duckdb.connect(str(ROOT/'data/warehouse.duckdb'),read_only=True);c.execute("SET threads=2;SET memory_limit='2GB'")
sql={
 'exact_observed_repeat_rows':'''select coalesce(sum(n-1),0) from (select event_ts,event_type,product_id,category_id,category_code,brand,price,user_id,user_session,count(*) n from read_parquet('data/staging/events/*.parquet') group by all having count(*)>1)''',
 'zero_price_events':'select count(*) from fact_event where price=0',
 'source_sessions':'select count(*) from(select distinct user_key,source_session_id from dim_session)',
 'scd_changed_products':'select count(*) from(select product_id from dim_product group by 1 having count(*)>1)',
 'card_null_cells':'select count(*) from fact_card_transaction where elapsed_seconds is null or amount is null or len(pca_features)<>28 or list_count(pca_features)<>28',
 'card_negative_amount':'select count(*) from fact_card_transaction where amount<0',
 'card_zero_amount':'select count(*) from fact_card_transaction where amount=0',
 'card_feature_duplicate_rows':'select sum(n-1) from(select elapsed_seconds,amount,pca_features,count(*) n from fact_card_transaction group by all having count(*)>1)',
 'mining_nonfinite':'select count(*) from session_features where not isfinite(events_per_minute) or not isfinite(category_entropy)'
}
import os;os.chdir(ROOT)
out={k:c.sql(v).fetchone()[0] for k,v in sql.items()};c.close();(ROOT/'results/extra_quality.json').write_text(json.dumps(out,indent=2));print(out)
