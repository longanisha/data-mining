"""Conditional uncertainty on fixed chronological test set; no test-set tuning."""
from pathlib import Path
import duckdb,pandas as pd,numpy as np,joblib,json
from sklearn.metrics import average_precision_score
ROOT=Path(__file__).resolve().parents[1]
def run():
 c=duckdb.connect(str(ROOT/'data/warehouse.duckdb'),read_only=True);df=c.sql('select f.*,o.is_fraud from fact_card_transaction f join card_outcome o using(transaction_key) where elapsed_seconds>=145248 order by elapsed_seconds,transaction_key').df();c.close()
 bundle=joblib.load(ROOT/'models/card_models.joblib');X=bundle['scaler'].transform(np.column_stack([np.stack(df.pca_features),np.log1p(df.amount)]));y=df.is_fraud.to_numpy();pos=np.where(y==1)[0];neg=np.where(y==0)[0];out=[];pred=df[['transaction_key','elapsed_seconds','is_fraud']].copy()
 for name,m in bundle['models'].items():
  score=-m.score_samples(X) if name=='isolation_forest' else m.predict_proba(X)[:,1];pred[name]=score;rng=np.random.default_rng(544);aps=[]
  for _ in range(100):
   ix=np.concatenate([rng.choice(pos,len(pos),replace=True),rng.choice(neg,len(neg),replace=True)]);aps.append(average_precision_score(y[ix],score[ix]))
  lo,hi=np.quantile(aps,[.025,.975]);out.append({'model':name,'ap':average_precision_score(y,score),'low_95':lo,'high_95':hi,'replicates':100})
 pred.to_parquet(ROOT/'results/card_test_predictions.parquet',index=False);(ROOT/'results/bootstrap.json').write_text(json.dumps(out,indent=2))
if __name__=='__main__':run()
