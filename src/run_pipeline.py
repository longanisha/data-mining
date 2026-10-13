"""A lightweight, equivalent sequential runner without Airflow's metadata service."""
from pathlib import Path
import os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
env=os.environ.copy();env.update(PYSPARK_PYTHON=sys.executable,SPARK_LOCAL_IP='127.0.0.1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
for name in ['extract','stage','warehouse','features','benchmark','mine']:
 subprocess.run([sys.executable,str(ROOT/'src'/f'{name}.py')],cwd=ROOT,env=env,check=True)
