#!/usr/bin/env python3
"""Exploratory deletion diagnostics; not a jackknife variance or causal test."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from reproduce_nhanes_access_use import ear_pta,survey_logit
OUT=Path(__file__).resolve().parent

def main():
 d=pd.read_sas(ROOT/'nhanes_raw/P_DEMO.xpt',format='xport')
 for k in ['AUQ','AUX']:d=d.merge(pd.read_sas(ROOT/f'nhanes_raw/P_{k}.xpt',format='xport'),on='SEQN',how='left',validate='one_to_one')
 d['pta']=pd.concat([ear_pta(d,'R'),ear_pta(d,'L')],axis=1).min(axis=1,skipna=False)
 f=d.loc[d.RIDSTATR.eq(2)&d.WTMECPRP.gt(0)].copy().reset_index(drop=True)
 dom=(f.RIDAGEYR.ge(70)&f.pta.notna()&f.AUQ147.eq(1)&f.AUQ149A.eq(1)&f.AUQ153.isin([1,2,3,4,5])&f.AUQ144.isin([1,2,3,4,5])).to_numpy()
 y=f.AUQ153.isin([3,4]).to_numpy(float);e=f.AUQ144.eq(1).to_numpy(float)
 X=np.column_stack([np.ones(len(f)),e,f.pta,f.RIDAGEYR,f.RIAGENDR.eq(2)])
 b=survey_logit(f,dom,y,X);assert b[4] and abs(np.exp(b[0][1])-2.816264656159935)<1e-8
 rows=[]
 masks=[('person',str(int(f.loc[i,'SEQN'])),np.arange(len(f))==i) for i in np.flatnonzero(dom)]
 for st,ps in f.loc[dom,['SDMVSTRA','SDMVPSU']].drop_duplicates().itertuples(index=False,name=None):
  masks.append(('masked_psu',f'{int(st)}:{int(ps)}',(f.SDMVSTRA.eq(st)&f.SDMVPSU.eq(ps)).to_numpy()))
 for kind,key,remove in masks:
  beta,se,ddf,rdf,conv,it=survey_logit(f,dom&~remove,y,X)
  assert conv and np.isfinite(beta).all()
  rows.append(dict(deletion=kind,key=key,removed_n=int((dom&remove).sum()),odds_ratio=float(np.exp(beta[1])),coefficient_change=float(beta[1]-b[0][1])))
 w=f.loc[dom,'WTMECPRP'].to_numpy();w=w/w.sum()
 summary={}
 for kind in ['person','masked_psu']:
  rr=[x for x in rows if x['deletion']==kind]
  summary[kind]=dict(refits=len(rr),min_OR=min(x['odds_ratio'] for x in rr),max_OR=max(x['odds_ratio'] for x in rr),max_abs_logOR_change=max(abs(x['coefficient_change']) for x in rr))
 out=dict(passed=True,n=int(dom.sum()),baseline_OR=float(np.exp(b[0][1])),weight_only_effective_n=float(1/(w@w)),max_weight_share=float(w.max()),top_five_weight_share=float(np.sort(w)[-5:].sum()),summary=summary,limitations=['Exploratory influence diagnostics selected after inspecting the main result.','Deletion ranges are not confidence intervals or jackknife variance estimates.','Weights are not recalibrated after deletion; these are perturbations of the fitted sample.','Weight-only effective n excludes clustering and is not regression effective sample size.','No correction for unmeasured confounding, reverse causation or current-user selection.'])
 (OUT/'nhanes_influence_results.json').write_text(json.dumps(out,indent=2)+'\n');pd.DataFrame(rows).to_csv(OUT/'nhanes_influence_results.csv',index=False)
 print(json.dumps(out,indent=2))
if __name__=='__main__':main()
