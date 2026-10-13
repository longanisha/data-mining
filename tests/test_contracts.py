import unittest,duckdb,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
class BoundaryContracts(unittest.TestCase):
 def test_exact_inactivity_boundary(self):
  c=duckdb.connect();r=c.sql('''with e(t) as(values (0),(1800),(3601)),g as(select t,t-lag(t) over(order by t) gap from e) select sum(case when gap is null or gap>1800 then 1 else 0 end) over(order by t) from g''').fetchall();self.assertEqual(r,[(1,),(1,),(2,)])
 def test_scd_same_timestamp_tiebreak(self):
  c=duckdb.connect();r=c.sql("select (timestamp '2019-10-01',10)<(timestamp '2019-10-01',11),(timestamp '2019-10-01',11)>=(timestamp '2019-10-01',11)").fetchone();self.assertEqual(r,(True,True))
 def test_warehouse_and_model_contracts(self):
  w=json.loads((ROOT/'results/warehouse_checks.json').read_text());self.assertGreaterEqual(w['event_count'],5000000)
  for key in ['orphan_product','orphan_session','duplicate_event_ids','invalid_scd_assignment','current_version_errors']:self.assertEqual(w[key],0,key)
  s=json.loads((ROOT/'results/card_mining.json').read_text())['splits'];self.assertLess(s['train']['max_elapsed'],s['validation']['min_elapsed']);self.assertLess(s['validation']['max_elapsed'],s['test']['min_elapsed']);self.assertEqual(sum(x['frauds'] for x in s.values()),492)
 def test_query_result_parity(self):
  b=json.loads((ROOT/'results/benchmarks.json').read_text());self.assertEqual(len(b),15)
  for q in {x['query'] for x in b}:self.assertEqual(len({x['result_sha256'] for x in b if x['query']==q}),1,q)
if __name__=='__main__':unittest.main()
