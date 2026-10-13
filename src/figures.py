from pathlib import Path
import textwrap
import json,numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'report';plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.bbox':'tight','font.family':'DejaVu Sans'})
def diagram():
 fig,ax=plt.subplots(figsize=(7.2,4.9));ax.set(xlim=(-.5,12.6),ylim=(0,10));ax.axis('off')
 nodes={
 'source':(4.4,9,3.2,.8,'DIM_SOURCE','PK source_key; name, grain, labels'),
 'date':(0,7.8,3.1,1.0,'DIM_DATE','PK date_key; calendar_date\nyear/month/day; week, weekday'),
 'time':(0,6.6,3.1,.85,'DIM_TIME','PK time_key; hour, minute'),
 'type':(0,5.4,3.1,.85,'DIM_EVENT_TYPE','PK event_type_key; event_type'),
 'event':(4.4,5.7,3.2,2.6,'FACT_EVENT','PK source_event_id (degenerate)\nFK source/date/time/type\nFK product/session\nevent_ts, event_date, price\nmissing flags, gap, repetition flag'),
 'product':(8.8,7.2,3.2,1.7,'DIM_PRODUCT (SCD2)','PK product_key\nFK source/category/brand\nproduct_id, version\neffective/expiry pairs\nis_current'),
 'category':(8.8,5.8,3.2,1.2,'DIM_CATEGORY','PK category_key; FK group_key\nsource_category_id, category_code'),
 'group':(8.8,4.4,3.2,.9,'DIM_CATEGORY_GROUP','PK group_key; group_name'),
 'brand':(8.8,3.1,3.2,.9,'DIM_BRAND','PK brand_key; brand_name'),
 'session':(4.4,3.4,3.2,1.4,'DIM_SESSION','PK session_key; FK user_key\nsource_session_id, visit_no\nstart_ts, end_ts'),
 'user':(0,3.4,3.1,1.1,'DIM_USER','PK user_key; FK source_key\nuser_id (pseudonymous)'),
 'card':(4.4,.6,3.2,1.9,'FACT_CARD_TRANSACTION','PK transaction_key (degenerate)\nFK source_key, period_key\nelapsed_seconds, amount\npca_features (28 values)'),
 'period':(0,1,3.1,1.0,'DIM_ELAPSED_PERIOD','PK period_key; relative_day\nhour_in_day'),
 'outcome':(8.8,1,3.2,1,'CARD_OUTCOME','PK/FK transaction_key\nis_fraud (benchmark target only)')}
 for key,(x,y,w,h,title,body) in nodes.items():
  ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.035',facecolor='#edf4f8' if 'FACT' not in title else '#d4e9e4',edgecolor='#385569',linewidth=.75))
  ax.text(x+.1,y+h-.13,title,fontsize=6.0,weight='bold',va='top');ax.text(x+.1,y+h-.38,'\n'.join('\n'.join(textwrap.wrap(line,32,break_long_words=False)) for line in body.split('\n')),fontsize=5.5,va='top',linespacing=1.2)
 def path(points):
  ax.plot(*zip(*points),color='#526775',linewidth=.7,zorder=1)
  ax.annotate('',xy=points[-1],xytext=points[-2],arrowprops={'arrowstyle':'->','lw':.7,'color':'#526775'},zorder=2)
 for pts in [
  [(4.4,7.8),(3.1,8.25)],[(4.4,7.0),(3.1,7.0)],[(4.4,6.2),(3.1,5.8)],
  [(6,8.3),(6,9)],[(7.6,7.8),(8.8,7.8)],[(6,5.7),(6,4.8)],[(4.4,4.1),(3.1,4.1)],
  [(8.8,8.6),(7.6,9.3)],[(10.4,7.2),(10.4,6.9)],[(10.4,5.8),(10.4,5.3)],
  [(12,8.0),(12.35,8.0),(12.35,3.55),(12,3.55)],
  [(0,4.0),(-.3,4.0),(-.3,9.4),(4.4,9.4)],
  [(7.6,2.0),(8.1,2.0),(8.1,9.5),(7.6,9.5)],
  [(4.4,1.5),(3.1,1.5)],[(8.8,1.5),(7.6,1.5)]
 ]:path(pts)
 ax.text(0,.08,'Arrow: child FK → parent PK (many-to-one); CARD_OUTCOME → card is one-to-one. Nullable attributes are permitted.',fontsize=6.8)
 fig.savefig(OUT/'erd.pdf');fig.savefig(OUT/'erd.png',dpi=180);plt.close(fig)
def plots():
 d=pd.read_csv(ROOT/'results/daily_events.csv');mix=pd.read_csv(ROOT/'results/event_mix.csv');cards=pd.read_csv(ROOT/'results/card_hourly.csv')
 fig,axs=plt.subplots(2,1,figsize=(3.5,3.4));axs[0].plot(pd.to_datetime(d.event_date).dt.day,d.events/1000,color='#216b82');axs[0].set(xlabel='October day (2019)',ylabel='Events (thousands)');axs[1].bar(mix.event_type,mix.n,color=['#216b82','#e29549','#4d9078']);axs[1].set_yscale('log');axs[1].set(ylabel='Event count (log scale)');fig.tight_layout();fig.savefig(OUT/'eda.pdf');plt.close(fig)
 b=pd.DataFrame(json.loads((ROOT/'results/benchmarks.json').read_text()));b['query']=b['query'].str[:2].str.upper();pivot=b.pivot(index='query',columns='strategy',values='median_seconds')*1000
 ax=pivot.plot.bar(figsize=(3.5,2.5),color=['#e29549','#216b82','#4d9078'],rot=0);ax.set(ylabel='Median elapsed time (ms)',xlabel='Query');ax.legend(['Date partitions','Native','Secondary indexes'],fontsize=6,frameon=False);plt.tight_layout();plt.savefig(OUT/'benchmarks.pdf');plt.close()
 cm=json.loads((ROOT/'results/card_mining.json').read_text());fig,ax=plt.subplots(figsize=(3.5,2.65))
 for name,label in [('isolation_forest','Isolation Forest'),('logistic_regression','Logistic regression'),('random_forest','Random Forest')]:
  p=pd.read_csv(ROOT/f'results/pr_{name}.csv');ax.plot(p.recall,p.precision,label=label,linewidth=1)
 prevalence=cm['splits']['test']['frauds']/cm['splits']['test']['n'];ax.axhline(prevalence,color='gray',ls='--',label='Test prevalence');ax.set(xlabel='Recall',ylabel='Precision',xlim=(0,1),ylim=(0,1.02));ax.legend(fontsize=6,frameon=False);fig.tight_layout();fig.savefig(OUT/'pr.pdf');plt.close(fig)
if __name__=='__main__':diagram();plots()
