"""Check whether AUQ153 can refer to multiple devices in the primary domain."""
import argparse
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.stats import t

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("replication_root", type=Path)
args = parser.parse_args()
repo = args.replication_root.resolve()
sys.path.insert(0,str(repo))
from reproduce_nhanes_access_use import ear_pta, survey_logit

def read_survey(name):
    return pd.read_sas(repo / "nhanes_raw" / f"P_{name}.xpt", format="xport")

frame = read_survey("DEMO").merge(read_survey("AUQ"),on="SEQN",how="left",validate="one_to_one").merge(read_survey("AUX"),on="SEQN",how="left",validate="one_to_one")
frame = frame.loc[frame.RIDSTATR.eq(2) & frame.WTMECPRP.gt(0)].reset_index(drop=True)
pta = pd.concat([ear_pta(frame,side) for side in ("R","L")],axis=1).min(axis=1,skipna=False)
domain = (frame.RIDAGEYR.ge(70) & pta.notna() & frame.AUQ147.eq(1) & frame.AUQ149A.eq(1) &
          frame.AUQ153.isin(range(1,6)) & frame.AUQ144.isin(range(1,6)))
other = frame.AUQ149B.eq(2) | frame.AUQ149C.eq(3)
X = np.column_stack([np.ones(len(frame)),frame.AUQ144.eq(1),pta,frame.RIDAGEYR,frame.RIAGENDR.eq(2)])
Y = frame.AUQ153.isin([3,4]).to_numpy(float)
for label,selected in [('All aid reporters',domain),('Aid-only reporters',domain & ~other)]:
    coef,se,_,df,converged,_=survey_logit(frame,selected.to_numpy(),Y,X)
    assert converged
    q=t.ppf(.975,df)
    print(label, int(selected.sum()), "OR, 95% CI", np.exp([coef[1],coef[1]-q*se[1],coef[1]+q*se[1]]))
print('Co-report amplifiers',int((domain & frame.AUQ149B.eq(2)).sum()))
print('Co-report implants',int((domain & frame.AUQ149C.eq(3)).sum()))
