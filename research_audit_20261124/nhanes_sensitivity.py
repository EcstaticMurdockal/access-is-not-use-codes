#!/usr/bin/env python3
"""Deterministic NHANES specification audit, not causal identification.
CDC codebook AUQ144: 1=<1 year, 2=1--4 years, 3=5--9 years,
4=10+ years, 5=never. AUQ153: 3=4--7h/day; 4=8+h/day.
All specifications below are reported, without selecting on significance.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
from scipy.stats import t
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reproduce_nhanes_access_use import ear_pta,survey_logit,weighted_prevalence
OUT=Path(__file__).resolve().parent

def main():
    raw={k:pd.read_sas(ROOT/'nhanes_raw'/f'P_{k}.xpt',format='xport') for k in ['DEMO','AUQ','AUX']}
    d=raw['DEMO'].merge(raw['AUQ'],on='SEQN',how='left',validate='one_to_one').merge(raw['AUX'],on='SEQN',how='left',validate='one_to_one')
    d['pta_r']=ear_pta(d,'R');d['pta_l']=ear_pta(d,'L');d['pta']=d[['pta_r','pta_l']].min(axis=1,skipna=False)
    f=d.loc[d.RIDSTATR.eq(2)&d.WTMECPRP.gt(0)].copy().reset_index(drop=True)
    primary=(f.RIDAGEYR.ge(70)&f.pta.notna()&f.AUQ147.eq(1)&f.AUQ149A.eq(1)&f.AUQ153.isin([1,2,3,4,5])&f.AUQ144.isin([1,2,3,4,5])).to_numpy()
    y=f.AUQ153.isin([3,4]).to_numpy(float);y8=f.AUQ153.eq(4).to_numpy(float)
    e1=f.AUQ144.eq(1).to_numpy(float);e5=f.AUQ144.isin([1,2]).to_numpy(float)
    age=f.RIDAGEYR.to_numpy(float);pta=f.pta.to_numpy(float);sex=f.RIAGENDR.eq(2).to_numpy(float);ones=np.ones(len(f))
    educ=f.DMDEDUC2.where(f.DMDEDUC2.isin([1,2,3,4,5])).to_numpy(float)
    edu_mid=np.where(np.isfinite(educ),np.isin(educ,[3,4]).astype(float),np.nan)
    edu_hi=np.where(np.isfinite(educ),(educ==5).astype(float),np.nan)
    pir=f.INDFMPIR.to_numpy(float)
    base=lambda e:np.column_stack([ones,e,pta,age,sex])
    specs=[
       ('baseline_code_corrected_label','<1 year; primary adjustment',e1,y,base(e1),primary),
       ('five_year_exposure','<5 years; primary adjustment',e5,y,base(e5),primary),
       ('unadjusted','<1 year; unadjusted',e1,y,np.column_stack([ones,e1]),primary),
       ('age_sex_only','<1 year; age and sex only',e1,y,np.column_stack([ones,e1,age,sex]),primary),
       ('eight_hour_outcome','<1 year; outcome >=8h/day',e1,y8,base(e1),primary),
       ('age_categories','<1 year; age categories 70–74/75–79/80+',e1,y,np.column_stack([ones,e1,pta,sex,((age>=75)&(age<80)).astype(float),(age>=80).astype(float)]),primary),
       ('quadratic_pta','<1 year; add centered PTA squared',e1,y,np.column_stack([base(e1),(pta-40)**2/100]),primary),
       ('education_income','<1 year; add education and income',e1,y,np.column_stack([base(e1),edu_mid,edu_hi,pir]),primary),
       ('five_year_education_income','<5 years; add education and income',e5,y,np.column_stack([base(e5),edu_mid,edu_hi,pir]),primary),
       ('same_complete_cases','<1 year; primary model on education/income complete cases',e1,y,base(e1),primary&np.isfinite(educ)&np.isfinite(pir)),
       ('exclude_never','<1 year vs >=1 year among ever-tested',e1,y,base(e1),primary&f.AUQ144.ne(5).to_numpy()),
       ('age_70_79','<1 year; restrict age 70–79',e1,y,base(e1),primary&(age<80)),
    ]
    rows=[]
    for key,label,e,yy,X,dom in specs:
       dom=dom&np.isfinite(X).all(axis=1)
       try:
        beta,se,ddf,rdf,conv,it=survey_logit(f,dom,yy,X)
        crit=t.ppf(.975,rdf);lo,hi=np.exp(beta[1]+np.array([-1,1])*crit*se[1])
        row=dict(specification=key,label=label,n=int(dom.sum()),exposed_n=int((dom&(e==1)).sum()),outcome_events=int(yy[dom].sum()),outcome_nonevents=int(dom.sum()-yy[dom].sum()),odds_ratio=float(np.exp(beta[1])),ci95_low=float(lo),ci95_high=float(hi),p_value=float(2*t.sf(abs(beta[1]/se[1]),rdf)),coefficient=float(beta[1]),se=float(se[1]),domain_df=int(ddf),residual_df=int(rdf),converged=bool(conv),iterations=it)
        rows.append(row)
       except (ValueError,np.linalg.LinAlgError) as ex: rows.append(dict(specification=key,label=label,n=int(dom.sum()),error=str(ex)))
    baseline=rows[0]
    full_df=f[['SDMVSTRA','SDMVPSU']].drop_duplicates().shape[0]-f.SDMVSTRA.nunique()
    rdf=int(full_df-(5-1));crit=t.ppf(.975,rdf)
    rows.append(dict(specification='full_frame_df',label='<1 year; full-design residual df',n=baseline['n'],odds_ratio=baseline['odds_ratio'],ci95_low=float(np.exp(baseline['coefficient']-crit*baseline['se'])),ci95_high=float(np.exp(baseline['coefficient']+crit*baseline['se'])),p_value=float(2*t.sf(abs(baseline['coefficient']/baseline['se']),rdf)),residual_df=rdf,converged=True))
    assert abs(rows[0]['odds_ratio']-2.816264656159935)<1e-10
    prevalence={}
    for label,e in [('less_than_one_year',e1),('less_than_five_years',e5)]:
       prevalence[label]={}
       for group,test in [('exposed',e==1),('comparison',e==0)]:
        dom=primary&test;prevalence[label][group]=dict(n=int(dom.sum()),regular_prevalence=weighted_prevalence(f,dom,y),eight_hour_prevalence=weighted_prevalence(f,dom,y8))
    out=dict(codebook_correction='AUQ144=1 denotes less than one year, not less than five years. Codes 1 and 2 jointly denote less than five years.',prevalence=prevalence,primary_n=int(primary.sum()),missing_education=int((primary&~np.isfinite(educ)).sum()),missing_pir=int((primary&~np.isfinite(pir)).sum()),topcoded_age80=int((primary&(age==80)).sum()),full_frame_design_df=int(full_df),specifications=rows,sources=['https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_AUQ.htm','https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.htm'],raw_sha256={k:hashlib.sha256((ROOT/'nhanes_raw'/f'P_{k}.xpt').read_bytes()).hexdigest() for k in raw},limitations=['Current-user selection remains.','Test recency is neither rehabilitation intensity nor capacity.','No causal congestion or service-treatment effect is identified.','Sensitivity specifications were defined after seeing the original headline result; this is an audit, not preregistered confirmatory analysis.','Design-based SE algorithm retained from existing reproduction; full-design degrees-of-freedom sensitivity also shown.'])
    (OUT/'nhanes_sensitivity_results.json').write_text(json.dumps(out,indent=2)+'\n')
    pd.DataFrame(rows).to_csv(OUT/'nhanes_sensitivity_results.csv',index=False)
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
