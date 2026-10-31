#!/usr/bin/env python3
"""REA static PE imports/Rust metadata for the identified Windows reference."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, help='Original reference EXE; otherwise use local.sources.json')
    args = parser.parse_args()
    config = json.loads((ROOT / 'targets.json').read_text())['windows_native_reference']
    if args.exe is None:
        local = ROOT / 'local.sources.json'
        if not local.is_file():
            raise SystemExit('Supply --exe /path/to/original.exe or create local.sources.json')
        args.exe = Path(json.loads(local.read_text())[config['local_source_key']])
    source = args.exe.resolve(strict=True)
    with source.open('rb') as stream:
        original_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    if source.stat().st_size != config['bytes'] or original_sha != config['sha256']:
        raise SystemExit('Native target identity differs; review and add a separate baseline first')
    run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ-native')
    run.mkdir(parents=True, exist_ok=False)
    operations = {
        'pe-imports': ['inspect-pe-imports', str(source), '--max-file-bytes', '167772160', '--json'],
        'rust': ['inspect-rust-binary', str(source), '--json'],
    }
    for name, operation in operations.items():
        with (run / (name + '.json')).open('w') as out, (run / (name + '.stderr.log')).open('w') as err:
            subprocess.run([sys.executable, str(ROOT / 'scripts/rea.py'), *operation],
                           stdout=out, stderr=err, check=True)
    with source.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != original_sha:
            raise SystemExit('Original native file changed while analyzing')
    print(json.dumps({'run_directory': str(run), 'original_preserved': True,
                      'target_executed': False, 'native_decompilation': False}))


if __name__ == '__main__':
    main()
