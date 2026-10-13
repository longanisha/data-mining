"""Read-only demonstration against the delivered database snapshot."""
from pathlib import Path
import argparse,json,duckdb,os
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--query',type=int,choices=range(1,6));a=p.parse_args();os.chdir(ROOT)
c=duckdb.connect('data/warehouse.duckdb',read_only=True)
print('WAREHOUSE GRAINS:');print(c.sql('select * from dim_source').df().to_string(index=False))
print('\nVALIDATION:');print((ROOT/'results/warehouse_checks.json').read_text())
if a.query:
 q=next((ROOT/'sql').glob(f'q{a.query}_*.sql'));print('\n'+q.name);print(c.sql(q.read_text()).df().head(20).to_string(index=False))
else:
 print('\nSCD HISTORY EXAMPLE:');print(c.sql('select product_id,product_version,effective_ts,expiry_ts,is_current from dim_product where product_id=(select product_id from dim_product group by 1 having count(*)>1 order by 1 limit 1) order by product_version').df().to_string(index=False))
 print('\nCARD BASELINES:');print(json.dumps(json.loads((ROOT/'results/card_mining.json').read_text())['metrics'],indent=2))
c.close()
