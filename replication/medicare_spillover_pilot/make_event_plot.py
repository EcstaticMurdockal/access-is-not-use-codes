"""Exact SVG event-study graphic; Arial text remains editable."""
import csv
from pathlib import Path
R=Path(__file__).resolve().parent;rows=list(csv.DictReader((R/'event_study.csv').open()))
W,H=920,420;left,right,top,bottom=85,880,65,320
lo=min(float(x['lower']) for x in rows);hi=max(float(x['upper']) for x in rows);limit=max(abs(lo),abs(hi),.05)*1.1
x=lambda year:left+(int(year)-2009)*(right-left)/9
y=lambda v:bottom-(v+limit)/(2*limit)*(bottom-top)
a=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', '<rect width="100%" height="100%" fill="white"/>','<g font-family="Arial, sans-serif" fill="black">','<text x="85" y="27" font-size="19" font-weight="bold">Medicare hospital-outpatient utilization: exploratory event study</text>',f'<rect x="{x(2014)-35}" y="{top}" width="{right-x(2014)+35}" height="{bottom-top}" fill="#FFF2DF"/>']
for v in [-.2,-.1,0,.1,.2]:
 if abs(v)>limit:continue
 yy=y(v);a +=[f'<line x1="{left}" y1="{yy}" x2="{right}" y2="{yy}" stroke="'+('#111' if v==0 else '#D7E7F3')+'"/>',f'<text x="{left-12}" y="{yy+5}" text-anchor="end" font-size="13">{v*100:.0f}</text>']
for r in rows:
 xx=x(r['year']);yy=y(float(r['beta']));up=y(float(r['upper']));dn=y(float(r['lower']));a +=[f'<line x1="{xx}" y1="{up}" x2="{xx}" y2="{dn}" stroke="#3974A2" stroke-width="2"/>',f'<line x1="{xx-5}" y1="{up}" x2="{xx+5}" y2="{up}" stroke="#3974A2"/>',f'<line x1="{xx-5}" y1="{dn}" x2="{xx+5}" y2="{dn}" stroke="#3974A2"/>',f'<circle cx="{xx}" cy="{yy}" r="4.5" fill="#3974A2"/>',f'<text x="{xx}" y="345" text-anchor="middle" font-size="13">{r["year"]}</text>']
a +=['<text x="17" y="230" transform="rotate(-90 17 230)" font-size="13">Log points × 100 relative to 2013</text>','<text x="85" y="380" font-size="13">25 states; 2009–2018. Pointwise 95% intervals; state-clustered CR1, t(24).</text>','<text x="85" y="402" font-size="13">2013 is the reference year. Shading marks 2014 onward; aggregate populations, not a fixed cohort.</text>','</g></svg>'];(R/'event_study.svg').write_text('\n'.join(a))
