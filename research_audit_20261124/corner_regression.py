"""Local corner derivative checks for the companion code, not new economics."""
from pathlib import Path
import json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from verify_models import group,stock_flow
out=[];eps=1e-6
# Positive net prices with a group that has zero adoption; negative subsidy
# case is a code-domain stress only, not a recommended admissible policy.
for s,K,label in [([0.,0.],.001,'zero-adoption group; admissible nonnegative subsidies'),([.6,.6],.3,'full-adoption numerical stress; subsidy above price')]:
 z=group(s=s,K=K,wL=.2);maxerr=0.
 for j in range(2):
  sp=np.array(s);sm=sp.copy();sp[j]+=eps;sm[j]-=eps
  zp=group(s=sp,K=K,wL=.2);zm=group(s=sm,K=K,wL=.2)
  maxerr=max(maxerr,float(np.max(abs((zp['n']-zm['n'])/(2*eps)-z['dns'][:,j]))),abs((zp['W']-zm['W'])/(2*eps)-z['Ws'][j]))
 out.append(dict(case=label,n=z['n'].tolist(),max_absolute_derivative_error=maxerr));assert maxerr<1e-7
for s in [.6,-.6]:
 z=stock_flow(s=s);zp=stock_flow(s=s+eps);zm=stock_flow(s=s-eps)
 err=max(abs((zp['A']-zm['A'])/(2*eps)-z['dAds']),abs((zp['h']-zm['h'])/(2*eps)-z['dhds']))
 out.append(dict(case=f'stock-flow code-domain corner s={s}',adoption=z['A'],max_absolute_derivative_error=err));assert err<1e-7
Path(__file__).with_name('corner_regression_results.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
