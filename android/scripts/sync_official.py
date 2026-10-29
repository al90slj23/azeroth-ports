#!/usr/bin/env python3
"""Fetch a coherent official web-core overlay without changing the installed Mac game."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
HOME = 'https://wow.aethus.pl/'
BASE = Path('/Volumes/RuiRui4TB/MacStorage/Codex/Projects/AzerothSurvivorsMac/build/Azeroth Survivors.app/Contents/Resources/www')
CORE = ['rogue.js', 'rogue.css', 'addons.js', 'saves.js', 'boot.js', 'wasi_stubs.js',
        'wenilla.js', 'wenilla_bg.wasm', 'boot-manifest.json', 'world-manifest.json', 'data/__index']


def module_dependencies(text):
    # Includes template-literal imports such as `./ime.js${STAMP}`. Optional imports
    # can be added by the author without changing the WASM import symbol table.
    prefix = r"(?:\b(?:import|fetch|prefetchManifest)\s*\(\s*|\bfrom\s+|\bnew\s+URL\s*\(\s*)"
    return set(re.findall(prefix + r"['\"`]\./([A-Za-z0-9_./-]+\.(?:json|m?js|wasm|css))(?![A-Za-z0-9_.])", text))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical(name):
    normalized = name.replace('\\', '/').lower()
    relative = PurePosixPath(normalized)
    if relative.is_absolute() or '..' in relative.parts or str(relative) != normalized:
        raise ValueError(f'Unsafe official asset name: {name}')
    return normalized


def download(url, target, timeout=180):
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + '.partial')
    subprocess.run(['curl', '-sS', '--fail', '--location', '--compressed',
                    '--connect-timeout', '20', '--max-time', str(timeout),
                    '--retry', '3', '--retry-all-errors', '--retry-delay', '2',
                    url, '-o', str(partial)], check=True)
    partial.replace(target)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--output', type=Path, default=ROOT / 'assets/latest-web-core')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / 'core-manifest.json'
    if manifest_path.exists():
        raise SystemExit('A completed snapshot exists; select a new output directory')
    sources = {}
    download(HOME, output / 'index.html')
    index = (output / 'index.html').read_text()
    stamps = set(re.findall(r'[?&]v=([a-f0-9]{8,64})', index))
    if len(stamps) != 1:
        raise SystemExit('The official entry page does not identify one coherent build')
    stamp = stamps.pop()
    print(f'Official stamp: {stamp}', flush=True)
    sources['index.html'] = HOME

    def fetch(name):
        encoded = urllib.parse.quote(name, safe='/')
        url = HOME + encoded + '?v=' + stamp
        path = download(url, output / name, 600 if name.endswith('.wasm') else 240)
        return name, url, path

    # The large WASM runs in parallel with small modules and static mutable data.
    with ThreadPoolExecutor(max_workers=8) as pool:
        initial = {pool.submit(fetch, name): name for name in CORE}
        for future in as_completed(initial):
            name, url, path = future.result()
            sources[name] = url
            print(f'Core fetched: {name} ({path.stat().st_size} bytes)', flush=True)

        checked_modules = set()
        while True:
            dependencies = set()
            for name in list(sources):
                if name.endswith('.js') and name not in checked_modules:
                    checked_modules.add(name)
                    for dependency in module_dependencies((output / name).read_text()):
                        resolved = (PurePosixPath(name).parent / dependency).as_posix()
                        if '..' in PurePosixPath(resolved).parts:
                            raise SystemExit('Unexpected parent-relative JS dependency')
                        dependencies.add(resolved)
            needed = dependencies - sources.keys()
            if not needed:
                break
            for name, url, path in pool.map(fetch, sorted(needed)):
                sources[name] = url

        names = json.loads((output / 'data/__index').read_text())
        if not isinstance(names, list) or not names:
            raise SystemExit('Invalid official asset index')
        canonical_names = {canonical(name) for name in names}
        new_assets = {name for name in canonical_names if not (args.base / 'data' / name).is_file()}
        mutable = {name for name in canonical_names if name.startswith(('dbfilesclient/', 'fonts/'))
                   or (name.startswith('interface/') and name.endswith(('.lua', '.xml')))
                   or name in ('wow.ini', 'wtf/defaultbindings.wtf')}
        mutable.update(['fonts/azs_sc.ttf', 'fonts/azs_jp.ttf', 'fonts/azs_kr.ttf'])
        assets = sorted({'data/' + name for name in new_assets | mutable})
        print(f'Data index: {len(names)} names; new assets {len(new_assets)}; refresh {len(assets)} files', flush=True)
        futures = {pool.submit(fetch, name): name for name in assets}
        for number, future in enumerate(as_completed(futures), 1):
            name, url, path = future.result()
            sources[name] = url
            if number % 50 == 0 or number == len(assets):
                print(f'Data fetched: {number}/{len(assets)}', flush=True)

    wasm = (output / 'wenilla_bg.wasm').read_bytes()
    # The main-menu branding places the build hash immediately before the semantic version.
    candidates = re.findall(rb'([a-f0-9]{8})(0\.\d{1,4}\.\d{1,4})(?![\d.])', wasm)
    candidates = [(a.decode(), b.decode()) for a, b in candidates]
    if not candidates:
        raise SystemExit('Could not identify embedded game build and version')
    build, version = candidates[-1]
    print(f'Embedded original game: {version} / {build}', flush=True)
    download(HOME + 'exe/latest.json', output / 'windows-latest.json')
    windows = json.loads((output / 'windows-latest.json').read_text())
    if windows.get('version') != version:
        raise SystemExit('Official Windows and downloaded web client version changed during sync')

    # Compile the untouched bytes, and check every imported WASM symbol has matching glue.
    validator = r'''
const fs = require('fs');
const wasm = fs.readFileSync(process.argv[1]);
const glue = fs.readFileSync(process.argv[2], 'utf8');
WebAssembly.compile(wasm).then(module => {
  const imports = WebAssembly.Module.imports(module);
  const missing = imports.filter(i => !glue.includes(i.name));
  if (missing.length) throw new Error('WASM/glue import mismatch: '+JSON.stringify(missing));
  console.log(JSON.stringify({compiled:true, imports:imports.length, imports_all_present:true}));
}).catch(e => {console.error(e);process.exit(1)});
'''
    result = subprocess.run(['node', '-e', validator, str(output / 'wenilla_bg.wasm'), str(output / 'wenilla.js')],
                            check=True, text=True, capture_output=True)
    validation = json.loads(result.stdout)
    missing = []
    for filename in ('boot-manifest.json', 'world-manifest.json'):
        listed = json.loads((output / filename).read_text())['names']
        for name in listed:
            relative = 'data/' + canonical(name)
            if not (output / relative).is_file() and not (args.base / relative).is_file():
                missing.append(relative)
        validation[filename + '_entries'] = len(listed)
    if missing:
        raise SystemExit('Missing boot/world assets: ' + repr(missing[:20]))
    download(HOME, output / 'index-recheck.html')
    if (output / 'index-recheck.html').read_bytes() != (output / 'index.html').read_bytes():
        raise SystemExit('The official build changed during sync; do not package this snapshot')
    validation.update(index_unchanged_after_download=True, boot_world_assets_present=True,
                      relative_module_dependencies_present=True,
                      new_data_files=len(new_assets), mutable_data_files=len(mutable))
    manifest = {'game_version': version, 'game_build': build, 'stamp': stamp, 'source': HOME,
                'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'files': {name: {'sha256': sha(output / name), 'bytes': (output / name).stat().st_size,
                                 'source': url} for name, url in sorted(sources.items())},
                'validation': validation}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'manifest': str(manifest_path), 'game_version': version, 'game_build': build,
                      'stamp': stamp, 'files': len(manifest['files']),
                      'bytes': sum(f['bytes'] for f in manifest['files'].values())}), flush=True)


if __name__ == '__main__':
    main()
