import os,json,time,joblib
from pathlib import Path
import numpy as np,pandas as pd,duckdb
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest,RandomForestClassifier
from sklearn.cluster import MiniBatchKMeans
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score,roc_auc_score,precision_score,recall_score,f1_score,confusion_matrix,silhouette_score,precision_recall_curve
ROOT=Path(__file__).resolve().parents[1];SEED=544
LOG=['n_events','n_products','n_categories','n_views','carts','purchases','mean_price','sd_price','mean_gap','sd_gap','duration_seconds','events_per_minute']
RATE=['repeat_rate','missing_brand_rate','missing_category_rate','cart_rate','purchase_rate','category_entropy']
def run():
 os.chdir(ROOT);t=time.perf_counter();rng=np.random.default_rng(SEED)
 df=pd.read_parquet('data/session_features.parquet');raw=df[LOG+RATE].fillna(0).astype(float);raw[LOG]=np.log1p(raw[LOG]);tr=df.split.eq('train');va=df.split.eq('validation');te=df.split.eq('test')
 scaler=StandardScaler().fit(raw.loc[tr]);X=scaler.transform(raw).astype('float32')
 iso=IsolationForest(n_estimators=100,max_samples=256,random_state=SEED,n_jobs=2).fit(X[tr]);score=-iso.score_samples(X);threshold=float(np.quantile(score[tr],.995))
 candidates=[];models={}
 vi=rng.choice(np.where(va)[0],min(2000,va.sum()),replace=False)
 for k in [3,4,5,6]:
  m=MiniBatchKMeans(n_clusters=k,batch_size=4096,n_init=3,random_state=SEED).fit(X[tr]);labels=m.predict(X[vi]);sil=float(silhouette_score(X[vi],labels)) if len(np.unique(labels))>1 else -1
  candidates.append({'k':k,'validation_silhouette':sil});models[k]=m
 best=max(candidates,key=lambda x:x['validation_silhouette']);km=models[best['k']];clusters=km.predict(X);ti=rng.choice(np.where(te)[0],min(2000,te.sum()),replace=False)
 test_sil=float(silhouette_score(X[ti],clusters[ti]));pd.DataFrame(candidates).to_csv('results/cluster_selection.csv',index=False)
 out=df[['session_key','split','n_events','n_products','duration_seconds','events_per_minute','purchases']].copy();out['cluster']=clusters;out['anomaly_score']=score;out['flagged']=score>=threshold
 out.to_parquet('data/session_scores.parquet',index=False)
 df['cluster']=clusters;df['anomaly_score']=score;df['flagged']=score>=threshold
 profiles=df.loc[te].groupby('cluster').agg(sessions=('session_key','size'),events=('n_events','mean'),products=('n_products','mean'),duration=('duration_seconds','mean'),purchase_rate=('purchase_rate','mean'),flag_rate=('flagged','mean'))
 profiles.to_csv('results/cluster_profiles.csv');top=out.loc[te].nlargest(100,'anomaly_score').copy();top['review_label']='';top['review_notes']='';top.to_csv('results/review_queue.csv',index=False)
 baseline_threshold=float(np.quantile(df.loc[tr,'events_per_minute'],.995));metrics={'features':LOG+RATE,'train_sessions':int(tr.sum()),'validation_sessions':int(va.sum()),'test_sessions':int(te.sum()),'if_threshold_train_q995':threshold,'test_flagged':int((score[te]>=threshold).sum()),'velocity_threshold_train_q995':baseline_threshold,'velocity_test_flagged':int((df.loc[te,'events_per_minute']>baseline_threshold).sum()),'selected_k':best['k'],'validation_silhouette':best['validation_silhouette'],'test_silhouette':test_sil,'silhouette_sample':len(ti),'no_fraud_labels':True}
 joblib.dump({'scaler':scaler,'isolation_forest':iso,'kmeans':km,'features':LOG+RATE,'log_features':LOG,'threshold':threshold},'models/session_models.joblib')
 Path('results/session_mining.json').write_text(json.dumps(metrics,indent=2));print(metrics,flush=True)
 del X,raw,df
 c=duckdb.connect('data/warehouse.duckdb',read_only=True);cards=c.sql('select f.*,o.is_fraud from fact_card_transaction f join card_outcome o using(transaction_key) order by elapsed_seconds,transaction_key').df();c.close()
 a=np.stack(cards.pca_features.to_numpy());a=np.column_stack([a,np.log1p(cards.amount.to_numpy())]);y=cards.is_fraud.to_numpy();times=cards.elapsed_seconds.to_numpy();cut1,cut2=np.quantile(times,[.6,.8]);tr=times<cut1;va=(times>=cut1)&(times<cut2);te=times>=cut2
 cs=StandardScaler().fit(a[tr]);a=cs.transform(a);models={'isolation_forest':IsolationForest(n_estimators=100,max_samples=256,random_state=SEED,n_jobs=2),'logistic_regression':LogisticRegression(class_weight='balanced',max_iter=1000,random_state=SEED),'random_forest':RandomForestClassifier(n_estimators=100,max_depth=12,min_samples_leaf=2,class_weight='balanced_subsample',n_jobs=2,random_state=SEED)}
 results=[];curves={};saved={}
 for name,m in models.items():
  m.fit(a[tr]) if name=='isolation_forest' else m.fit(a[tr],y[tr])
  sv=-m.score_samples(a[va]) if name=='isolation_forest' else m.predict_proba(a[va])[:,1];st=-m.score_samples(a[te]) if name=='isolation_forest' else m.predict_proba(a[te])[:,1]
  p,r,thresholds=precision_recall_curve(y[va],sv);f=2*p[:-1]*r[:-1]/np.maximum(p[:-1]+r[:-1],1e-15);th=float(thresholds[np.argmax(f)]);pred=st>=th
  row={'model':name,'threshold_validation_max_f1':th,'test_average_precision':average_precision_score(y[te],st),'test_roc_auc':roc_auc_score(y[te],st),'test_precision':precision_score(y[te],pred,zero_division=0),'test_recall':recall_score(y[te],pred),'test_f1':f1_score(y[te],pred),'confusion_tn_fp_fn_tp':confusion_matrix(y[te],pred).ravel().tolist()};results.append(row)
  p,r,_=precision_recall_curve(y[te],st);pd.DataFrame({'precision':p,'recall':r}).to_csv(f'results/pr_{name}.csv',index=False);saved[name]=m;print(row,flush=True)
 # Naive amount baseline uses the same validation-only threshold selection protocol.
 sv=cards.loc[va,'amount'].to_numpy();st=cards.loc[te,'amount'].to_numpy();p,r,ths=precision_recall_curve(y[va],sv);f=2*p[:-1]*r[:-1]/np.maximum(p[:-1]+r[:-1],1e-15);th=float(ths[np.argmax(f)]);pred=st>=th
 results.append({'model':'amount_baseline','threshold_validation_max_f1':th,'test_average_precision':average_precision_score(y[te],st),'test_roc_auc':roc_auc_score(y[te],st),'test_precision':precision_score(y[te],pred,zero_division=0),'test_recall':recall_score(y[te],pred),'test_f1':f1_score(y[te],pred),'confusion_tn_fp_fn_tp':confusion_matrix(y[te],pred).ravel().tolist()})
 splits={name:{'n':int(mask.sum()),'frauds':int(y[mask].sum()),'min_elapsed':float(times[mask].min()),'max_elapsed':float(times[mask].max())} for name,mask in [('train',tr),('validation',va),('test',te)]}
 Path('results/card_mining.json').write_text(json.dumps({'splits':splits,'cutoffs':[cut1,cut2],'features':'V1..V28 plus log1p(Amount); Time only for temporal split; Class excluded from X','metrics':results,'seconds_total_mining':time.perf_counter()-t},indent=2));joblib.dump({'scaler':cs,'models':saved,'features':'V1..V28,log1p(Amount)'},'models/card_models.joblib')
if __name__=='__main__':run()
