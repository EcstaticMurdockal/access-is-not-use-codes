"""Matched-baseline pooled versus reserved capacity. Illustrative, not calibrated.

The reservation shares are fixed at the pooled reference equilibrium before
policy changes. They are NOT recalculated after a subsidy perturbation.
"""
from pathlib import Path
import sys,json,csv
import numpy as np
from scipy.optimize import root
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from verify_models import group
OUT=Path(__file__).resolve().parent
MASS=np.array([.5,.5]);PRICE=np.array([.5,.5]);WEIGHT=np.array([.2,1.])
BASE=np.array([.8,.2]);GAIN=np.array([.2,1.]);NEED=np.ones(2)
K=.3;ETA=.5;LAM=.1
reference=group(K=K,wL=.2)
N0=reference['n'];D0=WEIGHT@N0
SHARE=WEIGHT*N0/D0

def allocation(n,alpha):
    D=WEIGHT@n
    return alpha*K*SHARE/n+(1-alpha)*K*WEIGHT/D

def at(n,alpha,s):
    y=allocation(n,alpha)
    q=BASE+GAIN*(-np.expm1(-y/NEED))
    t=(PRICE-s)/q
    return y,q,t

def solve(alpha,s):
    s=np.asarray(s)
    def residual(n):
        if np.any(n<=0):return np.full(2,1e6)
        _,q,t=at(n,alpha,s)
        return n-MASS*(1-t)
    sol=root(residual,N0,tol=1e-11)
    n=sol.x
    assert np.max(np.abs(residual(n)))<1e-10
    assert np.all((n>0)&(n<MASS))
    y,q,t=at(n,alpha,s)
    assert abs(n@y-K)<1e-11
    val=MASS*(1-t*t)/2
    W=(1+ETA)*(val@q)-PRICE@n-LAM*(s@n)
    return n,y,W

def derivatives(alpha):
    n=N0;D=WEIGHT@n;y,q,t=at(n,alpha,np.zeros(2))
    qp=GAIN*np.exp(-y/NEED)/NEED
    A=MASS/q;T=A*t*qp
    d=1+alpha*K*SHARE*T/(n*n)
    u=(1-alpha)*K*T*WEIGHT/(D*D)
    den=1+np.sum(WEIGHT*u/d)
    response=np.diag(A/d)-np.outer(u/d,WEIGHT*A/d)/den
    # Allocation Jacobian (per-person support with respect to adopter masses).
    L=-np.diag(alpha*K*SHARE/(n*n))-(1-alpha)*K*np.outer(WEIGHT,WEIGHT)/(D*D)
    val=MASS*(1-t*t)/2
    C=-(val*qp)@L
    J=(1+ETA)*(t*q-C)-PRICE
    Ws=J@response-LAM*n
    return response,Ws,C

def main():
    rows=[];maxerr=0.;matcherr=0.
    for alpha in np.linspace(0,1,5):
        n,y,_=solve(alpha,[0,0]);matcherr=max(matcherr,float(np.max(abs(n-N0))))
        response,Ws,C=derivatives(alpha)
        for j in range(2):
            eps=1e-6;shift=np.zeros(2);shift[j]=eps
            plus=solve(alpha,shift);minus=solve(alpha,-shift)
            maxerr=max(maxerr,float(np.max(abs((plus[0]-minus[0])/(2*eps)-response[:,j]))),abs((plus[2]-minus[2])/(2*eps)-Ws[j]))
        rows.append(dict(reserved_fraction=float(alpha),n_L=float(n[0]),n_H=float(n[1]),support_L=float(y[0]),support_H=float(y[1]),dnL_dsL=float(response[0,0]),dnH_dsL=float(response[1,0]),dnL_dsH=float(response[0,1]),dnH_dsH=float(response[1,1]),W_sL=float(Ws[0]),W_sH=float(Ws[1])))
    assert maxerr<1e-7 and matcherr<1e-10
    assert np.max(abs(derivatives(0)[0]-reference['dns']))<1e-10
    assert np.max(abs(derivatives(0)[1]-reference['Ws']))<1e-10
    assert derivatives(1)[0][0,1]==0 and derivatives(1)[0][1,0]==0
    result=dict(passed=True,parameters=dict(mass=MASS.tolist(),price=PRICE.tolist(),weight=WEIGHT.tolist(),baseline_benefit=BASE.tolist(),gain=GAIN.tolist(),need=NEED.tolist(),K=K,eta=ETA,lam=LAM),fixed_reservation_shares=SHARE.tolist(),max_finite_difference_error=maxerr,max_reference_equilibrium_difference=matcherr,rows=rows,interpretation='Matched baseline; reserve shares fixed before perturbation. Local interior comparative statics, not causal estimates or a global welfare ranking.')
    (OUT/'reserved_capacity_results.json').write_text(json.dumps(result,indent=2)+'\n')
    with (OUT/'reserved_capacity_results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    lines=[r'\begin{tabular}{rrrrr}',r'\toprule',r'Reserved share $\alpha$ & $\partial n_H/\partial s_L$ & $\partial n_L/\partial s_H$ & $W_{s_L}$ & $W_{s_H}$\\',r'\midrule']
    for z in rows:lines.append(f"{z['reserved_fraction']:.2f} & {z['dnH_dsL']:.6f} & {z['dnL_dsH']:.6f} & {z['W_sL']:.6f} & {z['W_sH']:.6f}"+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}']
    (OUT/'reserved_capacity_table.tex').write_text('\n'.join(lines)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
