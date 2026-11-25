"""Retrieve and verify the 35 NHS and CDC archive inputs, or check a local copy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import urllib.request


def sha256(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def obtain(entry, root, offline):
    destination = root / entry['path']
    if destination.exists():
        if sha256(destination) != entry['sha256']:
            raise RuntimeError(f'Existing file has a different digest: {destination}')
        return
    if offline:
        raise FileNotFoundError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(entry['url'], headers={'User-Agent': 'AcademicReplication/1.0'})
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as tmp:
        partial = Path(tmp.name)
    try:
        with urllib.request.urlopen(request, timeout=90) as response, partial.open('wb') as out:
            shutil.copyfileobj(response, out)
        if sha256(partial) != entry['sha256']:
            raise RuntimeError(f'Upstream digest changed: {destination}')
        os.replace(partial, destination)
    finally:
        partial.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, type=Path, help='Root for the base replication files')
    parser.add_argument('--offline', action='store_true', help='Require all files to exist already')
    args = parser.parse_args()
    manifest = Path(__file__).with_name('base_source_downloads.json')
    entries = json.loads(manifest.read_text(encoding='utf-8'))
    for entry in entries:
        obtain(entry, args.base, args.offline)
    print(f'{len(entries)} source files match their archived hashes.')


if __name__ == '__main__':
    main()
