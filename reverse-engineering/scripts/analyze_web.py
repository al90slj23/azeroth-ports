#!/usr/bin/env python3
"""Verify and statically analyze the seven original web JS files through REA."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    target = json.loads((ROOT / 'targets.json').read_text())['web_core']
    source = REPOSITORY / target['repository_path']
    manifest = json.loads((source / target['manifest']).read_text())
    if (manifest['game_version'], manifest['game_build']) != (target['version'], target['build']):
        raise SystemExit('Official core identity changed; review targets.json first')
    wasm = source / target['wasm_filename']
    with wasm.open('rb') as stream:
        wasm_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    if wasm.stat().st_size != target['wasm_bytes'] or wasm_sha != target['wasm_sha256']:
        raise SystemExit('Original WASM changed; never analyze an unidentified packaging copy')
    inputs = {}
    for name in target['javascript_sources']:
        data = (source / name).read_bytes()
        expected = manifest['files'][name]
        if len(data) != expected['bytes'] or sha(data) != expected['sha256']:
            raise SystemExit('Original JavaScript differs from official manifest: ' + name)
        inputs[name] = data
    # A fresh immutable selection avoids traversing large resource packs or private files.
    # This is a declared partial source selection, not a complete reconstructed app.
    run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ-web')
    stage = run / 'input'
    stage.mkdir(parents=True, exist_ok=False)
    for name, data in inputs.items():
        (stage / name).write_bytes(data)
    (run / 'inputs.json').write_text(json.dumps({
        'scope': 'seven exact original JS files; excludes WASM, assets and Android adaptations',
        'game_version': target['version'], 'game_build': target['build'],
        'original_wasm_sha256': wasm_sha,
        'sources': {name: {'bytes': len(data), 'sha256': sha(data)} for name, data in inputs.items()}
    }, indent=2) + '\n')
    command = [sys.executable, str(ROOT / 'scripts/rea.py'),
               'analyze-javascript-application', str(stage), '--json']
    with (run / 'application.json').open('w') as out, (run / 'analysis.stderr.log').open('w') as err:
        result = subprocess.run(command, stdout=out, stderr=err)
    if result.returncode:
        raise SystemExit(f'REA returned {result.returncode}; inspect {run}')
    # Preserve the complete Evidence; project a bounded view instead of rerunning it.
    request = {'source': {'kind': 'evidence-file', 'path': str(run / 'application.json')},
               'view': {'kind': 'summary'}}
    view = run / 'summary-request.json'
    view.write_text(json.dumps(request) + '\n')
    with (run / 'summary.json').open('w') as out, (run / 'view.stderr.log').open('w') as err:
        subprocess.run([sys.executable, str(ROOT / 'scripts/rea.py'),
                        'inspect-analysis-view', str(view), '--json'], stdout=out, stderr=err, check=True)
    for name, data in inputs.items():
        if (source / name).read_bytes() != data:
            raise SystemExit('Original source changed while analyzing: ' + name)
    print(json.dumps({'run_directory': str(run), 'source_files': len(inputs),
                      'originals_preserved': True, 'target_executed': False}))


if __name__ == '__main__':
    main()
