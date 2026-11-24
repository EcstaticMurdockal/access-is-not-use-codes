"""Generate the manuscript event-study figure from the audited CSV; requires Arial."""
from pathlib import Path
import argparse
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
p=argparse.ArgumentParser();p.add_argument('--arial-dir',type=Path);a=p.parse_args()
if a.arial_dir:
 for f in a.arial_dir.glob('*'):
  if f.suffix.lower()=='.ttf':fm.fontManager.addfont(str(f))
fm.findfont('Arial',fallback_to_default=False)
plt.rcParams.update({'font.family':'Arial','font.size':10,'axes.labelcolor':'black','text.color':'black','xtick.color':'black','ytick.color':'black','pdf.fonttype':42,'ps.fonttype':42})
r=Path(__file__).resolve().parent;d=pd.read_csv(r/'event_study.csv')
f,ax=plt.subplots(figsize=(7.5,3.6));f.subplots_adjust(left=.12,right=.985,bottom=.19,top=.92)
ax.axvspan(2013.5,2018.5,color='#FFF0D9',zorder=0);ax.axhline(0,color='black',lw=.8)
e=d[d.year!=2013];ax.errorbar(e.year,e.beta*100,yerr=[(e.beta-e.lower)*100,(e.upper-e.beta)*100],fmt='o',color='#3679A7',ecolor='#3679A7',elinewidth=1.3,capsize=3,markersize=4.5)
ax.scatter([2013],[0],s=28,facecolors='white',edgecolors='black',zorder=5)
ax.set_xticks(d.year);ax.set_xlim(2008.6,2018.4);ax.set_xlabel('Calendar year');ax.set_ylabel('Difference relative to 2013\n(log points × 100)')
ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',color='#DCE7EC',linewidth=.55);ax.set_axisbelow(True)
ax.set_title('Hospital outpatient visits, age 65+',loc='left',pad=9,fontweight='bold',fontsize=11)
ax.text(.98,.98,'2014 onward',transform=ax.transAxes,va='top',ha='right',fontsize=9)
f.savefig(r/'event_study.pdf');f.savefig(r/'event_study.png',dpi=180);plt.close(f)
