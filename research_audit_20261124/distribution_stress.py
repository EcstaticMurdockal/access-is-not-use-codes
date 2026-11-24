"""Independent generalized equilibrium stress audit. Numerical, not empirical.
Seeded shifted beta valuation distributions, 2--5 groups, three concave benefit
families, zero-response/zero-weight limits, stable corner active sets and fiscal
accounting. All parameters are artificial test inputs, never calibration.
"""
from pathlib import Path
import json
import numpy as np
from scipy.special import betainc,beta as beta_fn
from scipy.optimize import brentq
OUT=Path(__file__).resolve().parent

def evaluate(P,s=None,K=None):
    s=P['s'] if s is None else np.asarray(s);K=P['K'] if K is None else K
    m,w,a,b,r,p,lo,hi,al,be=[P[k] for k in ['m','w','a','b','r','p','lo','hi','al','be']]
    def response(h):
        v=w*h/r
        if P['family']=='exponential':
            g=-np.expm1(-v)/(-np.expm1(-1.));gp=np.exp(-v)/(-np.expm1(-1.))
        elif P['family']=='logarithmic':g=np.log1p(v)/np.log(2.);gp=1/(1+v)/np.log(2.)
        else:
            z=P['power'];g=(1+v)**z-1;g/=2**z-1;gp=z*(1+v)**(z-1)/(2**z-1)
        return a+b*g,b*w/r*gp
    def at(h):
        q,qp=response(h);t=(p-s)/q;z=np.clip((t-lo)/(hi-lo),0,1)
        n=m*(1-betainc(al,be,z));M=m*(lo*(1-betainc(al,be,z))+(hi-lo)*al/(al+be)*(1-betainc(al+1,be,z)))
        return q,qp,t,z,n,M
    upper=max(1.,K)
    for _ in range(80):
        if upper*(w@at(upper)[4])>K:break
        upper*=2
    else:raise ValueError('no finite positive-load root bracket')
    h=brentq(lambda h:h*(w@at(h)[4])-K,0,upper,xtol=1e-12)
    q,qp,t,z,n,M=at(h);D=w@n
    active=(t>lo)&(t<hi)
    f=np.zeros(len(m));za=z[active]
    f[active]=(za**(al[active]-1)*(1-za)**(be[active]-1)/beta_fn(al[active],be[active])/(hi[active]-lo[active]))
    A=m*f/q;B=A*t*qp;L=D+h*(w@B)
    hs=-h*w*A/L;dns=np.diag(A)+np.outer(B,hs);dnK=B/L
    S=M@qp;C=h*w*S/D
    # Full/zero groups have locally fixed n, so their cutoff does not enter dn.
    J=(1+P['eta'])*(t*q-C)-p-P['lam']*s
    Ws=J@dns-P['lam']*n
    WK=(1+P['eta'])*S/D+J@dnK-(1+P['lam'])*P['cx']
    Es=n+s@dns;EK=P['cx']+s@dnK
    E=s@n+P['cx']*K
    W=(1+P['eta'])*(M@q)-p@n-P['cx']*K-P['lam']*E
    return dict(h=h,n=n,q=q,t=t,D=D,active=active,dns=dns,dnK=dnK,hs=hs,hK=1/L,Ws=Ws,WK=WK,Es=Es,EK=EK,W=W,E=E,residual=h*D-K)

def main():
    rng=np.random.default_rng(20261124);rows=[];skipped=0;family_counts={};maxerr={k:0. for k in ['adoption','welfare','fiscal','capacity','constraint']};signfails=0;negativeE=0;cornercases=0;rankwins={'subsidy':0,'capacity':0};counterexamples={};eps=2e-6
    for trial in range(1500):
        n=int(rng.integers(2,6));lo=rng.uniform(.05,.4,n)
        P=dict(m=rng.dirichlet(np.ones(n)),w=rng.uniform(.05,2.5,n),a=rng.uniform(.1,1.0,n),b=rng.uniform(0,1.8,n),r=rng.uniform(.25,3,n),p=rng.uniform(.25,1.5,n),lo=lo,hi=lo+rng.uniform(.5,2,n),al=rng.uniform(.65,4,n),be=rng.uniform(.65,4,n),K=float(rng.uniform(.03,1.5)),eta=float(rng.uniform(0,1.5)),lam=float(rng.uniform(0,.4)),cx=float(rng.uniform(.05,1.0)),family=['exponential','logarithmic','shifted_power'][trial%3],power=float(rng.uniform(.2,.9)))
        P['s']=P['p']*rng.uniform(0,.9,n)
        if trial%7==0:P['w'][0]=0
        if trial%11==0:P['b'][-1]=0
        try:z=evaluate(P)
        except ValueError:skipped+=1;continue
        # Exclude non-smooth near-cutoff transitions from two-sided derivatives.
        if np.min(np.minimum(abs(z['t']-P['lo']),abs(z['t']-P['hi'])))<2e-4:skipped+=1;continue
        cornercases+=int(not np.all(z['active']));family_counts[P['family']]=family_counts.get(P['family'],0)+1
        err={k:0. for k in maxerr};err['constraint']=abs(z['residual']);negativeE+=int(np.any(z['Es']<0))
        for j in range(n):
            sp=P['s'].copy();sm=sp.copy();sp[j]+=eps;sm[j]-=eps
            zp,zm=evaluate(P,s=sp),evaluate(P,s=sm)
            err['adoption']=max(err['adoption'],float(np.max(abs((zp['n']-zm['n'])/(2*eps)-z['dns'][:,j]))))
            err['welfare']=max(err['welfare'],abs((zp['W']-zm['W'])/(2*eps)-z['Ws'][j]))
            err['fiscal']=max(err['fiscal'],abs((zp['E']-zm['E'])/(2*eps)-z['Es'][j]))
            signfails+=int(z['dns'][j,j]<-1e-10 or np.any(np.delete(z['dns'][:,j],j)>1e-10))
            if z['dns'][:,j].sum()<-1e-5 and 'negative_total_adoption' not in counterexamples:counterexamples['negative_total_adoption']={'trial':trial,'group':j,'total_derivative':float(z['dns'][:,j].sum()),'own_derivative':float(z['dns'][j,j])}
            if z['Es'][j]<-1e-5 and 'negative_marginal_fiscal_cost' not in counterexamples:counterexamples['negative_marginal_fiscal_cost']={'trial':trial,'group':j,'E_s':float(z['Es'][j])}
        zp,zm=evaluate(P,K=P['K']+eps),evaluate(P,K=P['K']-eps)
        err['capacity']=float(np.max(abs((zp['n']-zm['n'])/(2*eps)-z['dnK'])))
        err['welfare']=max(err['welfare'],abs((zp['W']-zm['W'])/(2*eps)-z['WK']))
        err['fiscal']=max(err['fiscal'],abs((zp['E']-zm['E'])/(2*eps)-z['EK']))
        signfails+=int(np.any(z['dnK']<-1e-10) or z['hK']<=0)
        for k in err:maxerr[k]=max(maxerr[k],err[k])
        good=z['Es']>1e-7
        if np.any(good):
            bestsub=float(np.max(z['Ws'][good]/z['Es'][good]));cap=float(z['WK']/z['EK']);rankwins['subsidy' if bestsub>cap else 'capacity']+=1
        rows.append({'trial':trial,'family':P['family'],'groups':n,'corner':bool(not np.all(z['active'])),'errors':err})
    result={'seed':20261124,'attempts':1500,'tested':len(rows),'skipped_no_root_or_near_cutoff':skipped,'stable_corner_cases':cornercases,'families':family_counts,'max_absolute_errors':maxerr,'sign_failures':signfails,'cases_with_negative_marginal_fiscal_cost':negativeE,'ranking_counts_artificial_design_not_probabilities':rankwins,'counterexamples':counterexamples,'pass':signfails==0 and max(maxerr.values())<5e-5,'scope':'Finite numerical stress grid; neither proof of global policy optimality nor empirical calibration. Positive-weight limiting demand is required for a positive-load equilibrium.'}
    (OUT/'distribution_stress_results.json').write_text(json.dumps(result,indent=2,default=lambda v:v.item()));(OUT/'distribution_stress_cases.json').write_text(json.dumps(rows,indent=2,default=lambda v:v.item()));print(json.dumps(result,indent=2,default=lambda v:v.item()));assert result['pass']
if __name__=='__main__':main()
