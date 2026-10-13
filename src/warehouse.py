"""Transactional snapshot rebuild; preserves previous good database on failure."""
import json,os,time,shutil
from pathlib import Path
import duckdb
ROOT=Path(__file__).resolve().parents[1]

def validate(c):
    checks={
      'event_count':c.sql('select count(*) from fact_event').fetchone()[0],
      'card_count':c.sql('select count(*) from fact_card_transaction').fetchone()[0],
      'fraud_count':c.sql('select sum(is_fraud) from card_outcome').fetchone()[0],
      'session_count':c.sql('select count(*) from dim_session').fetchone()[0],
      'product_versions':c.sql('select count(*) from dim_product').fetchone()[0],
      'products':c.sql('select count(distinct product_id) from dim_product').fetchone()[0],
      'orphan_product':c.sql('select count(*) from fact_event f left join dim_product p using(product_key) where p.product_key is null').fetchone()[0],
      'orphan_session':c.sql('select count(*) from fact_event f left join dim_session s using(session_key) where s.session_key is null').fetchone()[0],
      'duplicate_event_ids':c.sql('select count(*)-count(distinct source_event_id) from fact_event').fetchone()[0],
      'invalid_scd_assignment':c.sql('select count(*) from fact_event f join dim_product p using(product_key) where (f.event_ts,f.source_event_id)<(p.effective_ts,p.effective_event_id) or (p.expiry_ts is not null and (f.event_ts,f.source_event_id)>=(p.expiry_ts,p.expiry_event_id))').fetchone()[0],
      'current_version_errors':c.sql('select count(*) from(select product_id from dim_product group by product_id having count(*) filter(where is_current)<>1)').fetchone()[0],
      'repeated_same_second':c.sql('select sum(repeated_same_second) from fact_event').fetchone()[0],
    }
    profile=json.loads((ROOT/'results/staging_quality.json').read_text())
    assert checks['event_count']==profile['valid_rows']
    assert checks['card_count']==284807 and checks['fraud_count']==492
    assert all(checks[x]==0 for x in ['orphan_product','orphan_session','duplicate_event_ids','invalid_scd_assignment','current_version_errors'])
    return checks

def run():
    os.chdir(ROOT);t=time.perf_counter();tmp=ROOT/'data/warehouse.build.duckdb';tmp.unlink(missing_ok=True)
    c=duckdb.connect(str(tmp));c.execute("SET threads=2; SET memory_limit='3GB'; SET temp_directory='data/ducktmp';")
    c.execute((ROOT/'sql/warehouse.sql').read_text());metrics=validate(c)
    metrics['database_build_seconds']=time.perf_counter()-t
    c.execute('CHECKPOINT');c.close()
    (ROOT/'data/warehouse.duckdb.wal').unlink(missing_ok=True)
    tmp.replace(ROOT/'data/warehouse.duckdb')
    (ROOT/'results/warehouse_checks.json').write_text(json.dumps(metrics,indent=2))
    print(metrics,flush=True)

if __name__=='__main__':run()
