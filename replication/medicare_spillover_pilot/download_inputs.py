"""Fetch the exact public inputs; fail on any source hash change."""
from pathlib import Path
import urllib.request,json,hashlib,zipfile
R=Path(__file__).resolve().parent;raw=R/'raw';raw.mkdir(exist_ok=True)
for item in json.loads((R/'source_manifest.json').read_text()):
 p=raw/item['filename'];p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():urllib.request.urlretrieve(item['url'],p)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'], 'Source changed: '+item['filename']
 if p.name=='historical_2007_2013.zip':
  with zipfile.ZipFile(p) as z:z.extractall(raw/'historical')
print('All 13 public inputs downloaded and hash-verified.')
