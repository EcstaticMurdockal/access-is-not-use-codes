"""Fetch the 36 monthly DAA completed-pathway source workbooks around the 2015 rule."""
from pathlib import Path
import csv, re, hashlib, time
from urllib.request import urlopen
from urllib.parse import urljoin
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from lxml import html

BASE = Path(__file__).resolve().parent
PAGE = 'https://www.england.nhs.uk/statistics/statistical-work-areas/direct-access-audiology/daa-data/'
FIRST,LAST = '2013-10','2016-09'
def fetch(url, path):
    if path.exists(): return
    for attempt in range(3):
        try:
            with urlopen(url,timeout=35) as r: data=r.read()
            path.write_bytes(data)
            return
        except OSError:
            if attempt == 2: raise
            time.sleep(1+attempt)
def main():
    raw=BASE/'raw';raw.mkdir(exist_ok=True)
    fetch(PAGE,raw/'archive.html')
    links={}
    for tag in html.parse(str(raw/'archive.html')).xpath('//a[@href]'):
        title=' '.join(tag.text_content().split())
        if 'Completed Pathways' not in title or 'Commissioner & Provider' not in title: continue
        token=re.search(r'\b([A-Z][a-z]{2}[0-9]{2})\b',title)
        if not token:continue
        key=datetime.strptime(token[1],'%b%y').strftime('%Y-%m')
        if FIRST<=key<=LAST and (key not in links or 'revised' in title.lower()):
            links[key]=urljoin(PAGE,tag.get('href'))
    assert len(links)==36,len(links)
    def worker(item):
        month,url=item
        path=raw/f'{month}.xls'
        fetch(url,path)
        assert path.read_bytes().startswith(b'\xd0\xcf\x11\xe0'),(month,path.stat().st_size)
        return [month,url,hashlib.sha256(path.read_bytes()).hexdigest()]
    with ThreadPoolExecutor(6) as pool: rows=list(pool.map(worker,sorted(links.items())))
    with open(BASE/'workbooks.csv','w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['month','source_url','sha256']);writer.writerows(rows)
if __name__=='__main__': main()
