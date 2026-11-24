"""Local subsidy-linked supply paths; scenarios, not estimated supply elasticities."""
from pathlib import Path
import sys,json,csv
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from verify_models import group
OUT=Path(__file__).resolve().parent

def main():
    z=group();n=z['n'];h=z['h'];D=z['D'];w=np.array([.2,1.]);m=np.array([.5,.5]);p=np.array([.5,.5])
    q=z['q'];t=p/q;qp=np.array([.2,1.])*w*np.exp(-w*h)
    A=m/q;B=A*t*qp;L=D+h*(w@B)
    threshold=h*w[0]*A[0]
    rows=[];err=0.;right_err=0.
    for fraction in [-.5,0,.5,1,1.5]:
        gamma=fraction*threshold
        dh=(gamma-threshold)/L
        dn=np.array([A[0],0.])+B*dh
        eps=1e-6
        plus=group(s=[eps,0],K=.3+gamma*eps)
        minus=group(s=[-eps,0],K=.3-gamma*eps)
        err=max(err,abs((plus['h']-minus['h'])/(2*eps)-dh),float(np.max(abs((plus['n']-minus['n'])/(2*eps)-dn))))
        right_err=max(right_err,abs((plus['h']-h)/eps-dh),float(np.max(abs((plus['n']-n)/eps-dn))))
        rows.append(dict(supply_fraction=fraction,dK_dsL=float(gamma),dh_dsL=float(dh),dnL_dsL=float(dn[0]),dnH_dsL=float(dn[1])))
    assert err<1e-7 and right_err<1e-5
    assert rows[1]['dh_dsL']<0 and abs(rows[3]['dh_dsL'])<1e-12 and rows[4]['dh_dsL']>0
    result=dict(passed=True,reference=dict(K=.3,w=[.2,1.],n=n.tolist(),h=h),neutralizing_capacity_response=float(threshold),max_centered_difference_error=err,max_right_difference_error=right_err,rows=rows,interpretation='Alternative local K(s_L) paths through the same equilibrium; not a provider optimization model or welfare ranking. Supply financing and operating-cost responses are not identified.')
    (OUT/'supply_response_results.json').write_text(json.dumps(result,indent=2)+'\n')
    with (OUT/'supply_response_results.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    lines=[r'\begin{tabular}{rrrr}',r'\toprule',r'$K_{s_L}/(hw_LA_L)$ & $K_{s_L}$ & $h_{s_L}$ & $\partial n_H/\partial s_L$\\',r'\midrule']
    for row in rows:lines.append(f"{row['supply_fraction']:.1f} & {row['dK_dsL']:.6f} & {row['dh_dsL']:.6f} & {row['dnH_dsL']:.6f}"+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}']
    (OUT/'supply_response_table.tex').write_text('\n'.join(lines)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
