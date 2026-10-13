"""Manual, deterministic batch pipeline. No automatic remote submission."""
from datetime import datetime,timedelta
from pathlib import Path
import os,subprocess
from airflow import DAG
from airflow.operators.python import PythonOperator
ROOT=Path(__file__).resolve().parents[1]
def step(script):
 env=os.environ.copy();env.update({'PYSPARK_PYTHON':str(ROOT/'.venv/bin/python'),'SPARK_LOCAL_IP':'127.0.0.1','OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','MKL_NUM_THREADS':'2'})
 subprocess.run([str(ROOT/'.venv/bin/python'),'-u',str(ROOT/'src'/script)],cwd=ROOT,env=env,check=True)
with DAG('itcs544_phase2',start_date=datetime(2026,10,1),schedule=None,catchup=False,max_active_runs=1,default_args={'retries':1,'retry_delay':timedelta(seconds=5)},tags=['phase2']) as dag:
 tasks=[PythonOperator(task_id=name,python_callable=step,op_args=[script]) for name,script in [('extract','extract.py'),('spark_staging','stage.py'),('warehouse_validate','warehouse.py'),('feature_mart','features.py'),('olap_benchmarks','benchmark.py'),('mining','mine.py')]]
 for a,b in zip(tasks,tasks[1:]):a>>b
if __name__=='__main__':dag.test()
