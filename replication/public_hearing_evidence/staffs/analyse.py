"""Reconstruct aggregate pathway checks and local administrative fitting totals."""
from pathlib import Path
from collections import Counter, defaultdict
import csv, hashlib
import xlrd
from datetime import datetime

BASE=Path(__file__).resolve().parent
TARGET='05G'
NEIGHBOURS=['04Y','05D','05Q','05V','05W']
NAMES={'05G':'North Staffordshire','04Y':'Cannock Chase','05D':'East Staffordshire','05Q':'South East Staffordshire and Seisdon Peninsula','05V':'Stafford and Surrounds','05W':'Stoke-on-Trent'}

def write(name,rows):
    with (BASE/name).open('w',newline='') as f:
        out=csv.DictWriter(f,fieldnames=list(rows[0]));out.writeheader();out.writerows(rows)

def load():
    rows=[]
    for f in csv.DictReader((BASE/'workbooks.csv').open()):
        m=f['month'];p=BASE/'raw'/f'{m}.xls'
        assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256']
        b=xlrd.open_workbook(p);s=b.sheet_by_name('CCG')
        assert datetime.strptime(s.cell_value(4,2),'%B %Y').strftime('%Y-%m')==m
        head=next(i for i in range(30) if '>0-1' in s.row_values(i))
        cols=s.row_values(head)
        found=set()
        for i in range(head+1,s.nrows):
            v=s.row_values(i);code=v[cols.index('Commissioner Code' if 'Commissioner Code' in cols else 'Code')]
            if code not in NAMES:continue
            row=dict(zip(cols,v));tot=row['Total (all)'];known=row['Total (known clock start)']
            assert isinstance(tot,float) and isinstance(known,float),(m,code,tot,known)
            lag=sum(row[f'>{k}-{k+1}'] for k in range(6,52))+row['52 plus']
            assert sum(row[f'>{k}-{k+1}'] for k in range(52))+row['52 plus']==known
            assert known+row['Patients with unknown clock start date']==tot
            rows.append(dict(month=m,code=code,commissioner=NAMES[code],completed=int(tot),known_start=int(known),wait_over_six_weeks=int(lag)))
            found.add(code)
        assert found==set(NAMES),(m,found)
    assert len(rows)==216
    return rows

def summary(rows):
    results=[]
    # Include the actual audit window, same-month prior-year placebo and 12-month sensitivity.
    specs=[('prepolicy_placebo_6m','2013-10','2014-03','2014-10','2015-03'),('policy_6m','2014-10','2015-03','2015-10','2016-03'),('prepolicy_placebo_12m','2013-10','2014-09','2014-10','2015-09'),('policy_12m','2014-10','2015-09','2015-10','2016-09')]
    for label,p0,p1,t0,t1 in specs:
        for name,group in [('North Staffordshire',[TARGET]),('pooled five comparison CCGs',NEIGHBOURS)]+[(NAMES[k],[k]) for k in NEIGHBOURS]:
            def agg(a,b):return {key:sum(r[key] for r in rows if r['code'] in group and a<=r['month']<=b) for key in ['known_start','completed','wait_over_six_weeks']}
            pre,post=agg(p0,p1),agg(t0,t1)
            rate=lambda r:r['wait_over_six_weeks']/r['known_start']
            results.append(dict(window=label,group=name,pre_start=p0,pre_end=p1,post_start=t0,post_end=t1,
                       pre_completed=pre['completed'],post_completed=post['completed'],pct_change=(post['completed']/pre['completed']-1)*100,
                       pre_over_6w_pct=rate(pre)*100,post_over_6w_pct=rate(post)*100))
    return results

def local():
    vals=list(csv.DictReader((BASE/'committee_counts.csv').open()))
    pre,post=vals
    a,b=int(pre['assessed']),int(post['assessed']); e,f=int(pre['fitted']),int(post['fitted'])
    assert e==1226 and f==1223
    return [dict(measure=m,before=before,after=after,change=after-before) for m,before,after in [('assessments',a,b),('patients fitted',e,f),('fitted count per 100 assessed',100*e/a,100*f/b)]]
def main():
    rows=load();write('six_ccg_months.csv',rows);r=summary(rows);write('geographic_checks.csv',r)
    write('local_results.csv',local())
    contrasts=[]
    for label in dict.fromkeys(x['window'] for x in r):
        a,c=[q for q in r if q['window']==label][:2]
        contrasts.append(dict(window=label,relative_change_percent=100*((a['post_completed']/a['pre_completed'])/(c['post_completed']/c['pre_completed'])-1),
            wait_sixweeks_did_pp=(a['post_over_6w_pct']-a['pre_over_6w_pct'])-(c['post_over_6w_pct']-c['pre_over_6w_pct'])))
    write('pooled_checks.csv',contrasts)
if __name__=='__main__':main()
