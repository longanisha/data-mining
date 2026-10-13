import duckdb,time,json,statistics,hashlib,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run():
 os.chdir(ROOT);c=duckdb.connect('data/warehouse.duckdb');c.execute("SET threads=2; SET memory_limit='2GB'")
 for col in ['event_date','product_key','session_key']:c.execute(f'DROP INDEX IF EXISTS ix_{col}')
 queries={p.stem:p.read_text() for p in sorted((ROOT/'sql').glob('q*.sql'))};results=[];digests={}
 for mode in ['native','secondary_indexes','date_partitioned_parquet']:
  if mode=='secondary_indexes':
   t=time.perf_counter()
   for col in ['event_date','product_key','session_key']:c.execute(f'CREATE INDEX IF NOT EXISTS ix_{col} ON fact_event({col})')
   (ROOT/'results/index_build.json').write_text(json.dumps({'seconds':time.perf_counter()-t}))
  if mode=='date_partitioned_parquet':
   t=time.perf_counter();c.execute("COPY fact_event TO 'data/event_partitions' (FORMAT PARQUET, PARTITION_BY(event_date),COMPRESSION ZSTD,OVERWRITE_OR_IGNORE)")
   c.execute("CREATE OR REPLACE VIEW partitioned_event AS SELECT * FROM read_parquet('data/event_partitions/*/*.parquet',hive_partitioning=true)")
   (ROOT/'results/partition_build.json').write_text(json.dumps({'seconds':time.perf_counter()-t}))
  for name,original in queries.items():
   q=original.replace('fact_event','partitioned_event') if mode=='date_partitioned_parquet' else original
   warm=c.sql(q).df(); times=[]
   for _ in range(3):
    t=time.perf_counter();df=c.sql(q).df();times.append(time.perf_counter()-t)
   # Sorting serialized rows avoids tie-order sensitivity; floating aggregates rounded for parity.
   canonical=sorted(df.round(6).astype(str).apply(lambda r:'|'.join(r),axis=1).tolist())
   digest=hashlib.sha256('\n'.join(canonical).encode()).hexdigest()
   if mode=='native':digests[name]=digest;df.to_csv(f'results/{name}.csv',index=False)
   assert digests[name]==digest,(name,mode,'result mismatch')
   plan=c.execute('EXPLAIN ANALYZE '+q).fetchall()
   Path(f'results/{name}_{mode}_plan.txt').write_text('\n'.join(str(x) for x in plan))
   results.append({'query':name,'strategy':mode,'median_seconds':statistics.median(times),'min_seconds':min(times),'max_seconds':max(times),'runs':times,'rows':len(df),'result_sha256':digest})
   print(name,mode,times,flush=True)
 c.execute('CHECKPOINT');c.close();Path('results/benchmarks.json').write_text(json.dumps(results,indent=2))
if __name__=='__main__':run()
