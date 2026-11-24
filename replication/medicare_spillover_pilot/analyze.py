from pathlib import Path
import pandas as pd,numpy as np,json,hashlib,sys
from scipy import stats
ROOT=Path(__file__).resolve().parent
RAW=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'raw'
T='AR KY MD NV NM ND OR RI WV'.split();C='AL FL GA ID KS MS MO NE NC OK SC SD TN TX UT WY'.split()
old=pd.read_excel(RAW/'historical/2007-2013 Medicare FFS Geographic Variation Public Use File.xlsx')
new=pd.read_csv(RAW/'cms_geo_2014_2024.csv',low_memory=False)
print('Age values',old.BENE_AGE_LVL.unique(),new.BENE_AGE_LVL.unique(),flush=True)
old=old.rename(columns={'BENES_FFS_CNT':'BENES_OM_CNT','EVER_MA_PRTCPTN_RATE':'MA_PRTCPTN_RATE'})
d=pd.concat([old,new],ignore_index=True)
d=d[(d.BENE_GEO_LVL=='State') & (d.BENE_AGE_LVL.isin(['>65','>=65'])) & d.YEAR.between(2009,2018)].copy()
d['state']=d.BENE_GEO_DESC.str.strip();d=d[d.state.isin(T+C)].copy();d['treated']=d.state.isin(T).astype(int);d['did']=d.treated*(d.YEAR>=2014)
outs=['OP_VISITS_PER_1000_BENES','IP_CVRD_STAYS_PER_1000_BENES','ER_VISITS_PER_1000_BENES','HH_VISITS_PER_1000_BENES']
checks=['BENES_OM_CNT','BENE_AVG_AGE','BENE_FEML_PCT','BENE_DUAL_PCT','MA_PRTCPTN_RATE']
for c in outs+checks:d[c]=pd.to_numeric(d[c].astype(str).str.replace(',',''),errors='coerce')
d=d.sort_values(['state','YEAR']);assert len(d)==250,(len(d),d.state.unique());assert not d.duplicated(['state','YEAR']).any();assert d[outs].notna().all().all();assert (d[outs]>0).all().all()
d[['state','YEAR','treated','did']+outs+checks].to_csv(ROOT/'analysis_panel.csv',index=False)
base=d[d.YEAR==2013].set_index('state').BENES_OM_CNT

def fit(f,y,terms=['did'],weighted=False):
 X=pd.concat([pd.Series(1.,index=f.index,name='const'),pd.get_dummies(f.state,prefix='s',drop_first=True,dtype=float),pd.get_dummies(f.YEAR,prefix='t',drop_first=True,dtype=float),f[terms].astype(float)],axis=1)
 names=X.columns.tolist();x=X.to_numpy(float);v=y.to_numpy(float);w=f.state.map(base).to_numpy() if weighted else np.ones(len(f));w=w/w.mean();xw=x*np.sqrt(w[:,None]);yw=v*np.sqrt(w)
 inv=np.linalg.inv(xw.T@xw);b=inv@xw.T@yw;e=yw-xw@b;g=f.state.to_numpy();G=len(np.unique(g));N,K=x.shape;meat=np.zeros((K,K))
 for st in np.unique(g):
  u=xw[g==st].T@e[g==st];meat+=np.outer(u,u)
 cov=inv@meat@inv*(G/(G-1))*((N-1)/(N-K));return b,cov,names,G

def result(f,col,weighted=False):
 b,V,n,G=fit(f,np.log(f[col]),weighted=weighted);k=n.index('did');se=np.sqrt(V[k,k]);q=stats.t.ppf(.975,G-1)
 return dict(beta=float(b[k]),se=float(se),percent=float(np.expm1(b[k])*100),lower_percent=float(np.expm1(b[k]-q*se)*100),upper_percent=float(np.expm1(b[k]+q*se)*100),p=float(2*stats.t.sf(abs(b[k]/se),G-1)),states=G,n=len(f))
res={'main':{c:result(d,c) for c in outs},'sensitivity':{},'composition':{}}
p=outs[0]
res['sensitivity']['window2011_2018']=result(d[d.YEAR>=2011],p)
res['sensitivity']['baseline_population_weighted']=result(d,p,True)
f=d[d.YEAR<=2013].copy();f['did']=f.treated*(f.YEAR>=2012);res['sensitivity']['placebo2012']=result(f,p)
loo=[]
for st in T+C:loo.append({'excluded':st,**result(d[d.state!=st],p)})
pd.DataFrame(loo).to_csv(ROOT/'leave_one_state_out.csv',index=False)
res['sensitivity']['leave_one_state_out_percent_range']=[min(r['percent'] for r in loo),max(r['percent'] for r in loo)]
terms=[]
for yr in range(2009,2019):
 if yr!=2013:d[f'e{yr}']=d.treated*(d.YEAR==yr);terms.append(f'e{yr}')
b,V,n,G=fit(d,np.log(d[p]),terms);rows=[]
for yr in range(2009,2019):
 if yr==2013:rows.append({'year':yr,'beta':0,'se':0,'lower':0,'upper':0});continue
 k=n.index(f'e{yr}');se=np.sqrt(V[k,k]);q=stats.t.ppf(.975,G-1);rows.append({'year':yr,'beta':b[k],'se':se,'lower':b[k]-q*se,'upper':b[k]+q*se})
pd.DataFrame(rows).to_csv(ROOT/'event_study.csv',index=False)
ks=[n.index(f'e{y}') for y in range(2009,2013)];B=b[ks];VV=V[np.ix_(ks,ks)];F=B@np.linalg.inv(VV)@B/len(ks)
res['pretrend']={'joint_F':float(F),'df_num':len(ks),'df_den':G-1,'p':float(stats.f.sf(F,len(ks),G-1))}
for c in checks:
 if d[c].notna().all():
  b,V,n,G=fit(d,d[c]);k=n.index('did');res['composition'][c]={'difference':float(b[k]),'se':float(np.sqrt(V[k,k]))}
# Independent balanced-panel DID identity checks the FE coefficient.
diff=d.groupby(['state',d.YEAR>=2014])[p].apply(lambda x:np.log(x).mean()).unstack();delta=diff[True]-diff[False]
manual=delta.loc[T].mean()-delta.loc[C].mean();assert abs(manual-res['main'][p]['beta'])<1e-10
res['validation']={'balanced_panel':True,'manual_did_agrees':True,'source_rows_old':len(old),'source_rows_new':len(new),'primary_outcome':p}
(ROOT/'results.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
