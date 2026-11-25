"""Check the exact numerical files reproduced by the documented Linux build."""
import argparse
import hashlib
import json
from pathlib import Path


def verify(directory, expected):
    failures = []
    for name, digest in expected.items():
        path = directory / name
        if not path.is_file():
            failures.append(f"missing: {path}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            failures.append(f"changed: {path}")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, type=Path, help='Root of the tagged code or extracted current supplement')
    parser.add_argument('--cms', required=True, type=Path, help='Directory containing the Medicare extension')
    parser.add_argument('--current-supplement', action='store_true',
                        help='Use the supplied corrected model output for the open-ended age class')
    args = parser.parse_args()
    record = json.loads(Path(__file__).with_name('validation.json').read_text(encoding='utf-8'))
    expectations = record['expected_outputs_sha256']
    base_hashes = dict(expectations['base'])
    if args.current_supplement:
        manifest = json.loads((args.base / 'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
        base_hashes['verification_results.json'] = manifest['verification_results.json']
    failures = verify(args.base, base_hashes) + verify(args.cms, expectations['cms'])
    if failures:
        raise SystemExit('\n'.join(failures))
    print(f"Matched {len(expectations['base'])} base and {len(expectations['cms'])} extension outputs.")


if __name__ == '__main__':
    main()
