from pathlib import Path
import pandas as pd,numpy as np,json,zipfile,io,sys
from scipy import stats
R=Path(__file__).resolve().parent;raw=Path(sys.argv[1]) if len(sys.argv)>1 else R/'raw'
geo=pd.read_csv(raw/'cms_geo_2014_2024.csv',usecols=['BENE_GEO_LVL','BENE_GEO_CD','BENE_GEO_DESC']);geo=geo[geo.BENE_GEO_LVL=='State'].drop_duplicates('BENE_GEO_CD');geo['statefips']=pd.to_numeric(geo.BENE_GEO_CD,errors='coerce');mapping=geo.set_index('statefips').BENE_GEO_DESC.str.strip().to_dict()
frames=[]
for yr in range(2009,2019):
 with zipfile.ZipFile(raw/'sahie'/f'{yr}.zip') as z:
  s=z.read(next(n for n in z.namelist() if n.endswith('.csv'))).decode('utf-8-sig');lines=s.splitlines();start=next(i for i,l in enumerate(lines) if l.lower().startswith('year,'));f=pd.read_csv(io.StringIO('\n'.join(lines[start:])),skipinitialspace=True,low_memory=False)
 f.columns=f.columns.str.strip();f=f[(f.geocat==40)&(f.agecat==1)&(f.racecat==0)&(f.sexcat==0)&f.iprcat.isin([0,3])].copy()
 if 'version' in f.columns and yr==2013:
  print('2013 versions',f.version.unique());f=f[f.version.fillna('').str.strip().isin(['Updated',''])]
 f['PCTUI']=pd.to_numeric(f.PCTUI,errors='raise');f['state']=f.statefips.map(mapping);frames.append(f[['year','state','iprcat','PCTUI']])
a=pd.concat(frames);a.to_csv(R/'coverage_panel.csv',index=False)
p=pd.read_csv(R/'analysis_panel.csv');results={}
for inc in [0,3]:
 d=p[['state','YEAR','did']].merge(a[a.iprcat==inc],left_on=['state','YEAR'],right_on=['state','year'],validate='one_to_one');assert len(d)==250
 X=pd.concat([pd.Series(1.,index=d.index),pd.get_dummies(d.state,drop_first=True,dtype=float),pd.get_dummies(d.YEAR,drop_first=True,dtype=float),d[['did']]],axis=1).to_numpy(float);y=d.PCTUI.to_numpy();G=d.state.nunique();N,K=X.shape;I=np.linalg.inv(X.T@X);b=I@X.T@y;e=y-X@b;M=np.zeros((K,K))
 for st in d.state.unique():
  idx=d.state==st;u=X[idx].T@e[idx];M+=np.outer(u,u)
 V=I@M@I*(G/(G-1))*((N-1)/(N-K));se=np.sqrt(V[-1,-1]);q=stats.t.ppf(.975,G-1)
 results[str(inc)]={'uninsured_pp_change':float(b[-1]),'se':float(se),'lower':float(b[-1]-q*se),'upper':float(b[-1]+q*se),'p':float(2*stats.t.sf(abs(b[-1]/se),G-1))}
 # Supplemental event-study pretrend check for this coverage outcome.
 terms=[]
 for yr in range(2009,2019):
  if yr!=2013:d[f'e{yr}']=(d.state.isin(p[p.did==1].state.unique()) & (d.YEAR==yr)).astype(int);terms.append(f'e{yr}')
 Z=pd.concat([pd.Series(1.,index=d.index),pd.get_dummies(d.state,drop_first=True,dtype=float),pd.get_dummies(d.YEAR,drop_first=True,dtype=float),d[terms]],axis=1).to_numpy(float)
 J=np.linalg.inv(Z.T@Z);bb=J@Z.T@y;ee=y-Z@bb;MM=np.zeros((Z.shape[1],Z.shape[1]))
 for st in d.state.unique():
  ix=d.state==st;u=Z[ix].T@ee[ix];MM+=np.outer(u,u)
 VV=J@MM@J*(G/(G-1))*((N-1)/(N-Z.shape[1]));ii=[Z.shape[1]-len(terms)+terms.index(f'e{yr}') for yr in range(2009,2013)]
 qF=bb[ii]@np.linalg.inv(VV[np.ix_(ii,ii)])@bb[ii]/4
 results[str(inc)]['pretrend_p']=float(stats.f.sf(qF,4,G-1))
(R/'coverage_results.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
