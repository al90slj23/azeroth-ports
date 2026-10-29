#!/usr/bin/env python3
"""Create a verified APK asset plan without copying the 1.7 GB original resource tree."""
import argparse
import hashlib
import json
from pathlib import Path
from sync_official import module_dependencies

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WEB = Path('/Volumes/RuiRui4TB/MacStorage/Codex/Projects/AzerothSurvivorsMac/build/Azeroth Survivors.app/Contents/Resources/www')
DEFAULT_CORE = ROOT / 'assets/latest-web-core'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare(base, output, core=DEFAULT_CORE):
    base = base.resolve(strict=True)
    core = core.resolve(strict=True)
    core_manifest = json.loads((core / 'core-manifest.json').read_text())
    core_files = core_manifest['files']
    for field in ('game_version', 'game_build', 'stamp'):
        if not isinstance(core_manifest.get(field), str) or not core_manifest[field]:
            raise SystemExit(f'Missing core metadata: {field}')
    verified = {}
    for name, info in core_files.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts or '\\' in name or relative.as_posix() != name:
            raise SystemExit(f'Unsafe core path: {name}')
        source = (core / relative).resolve(strict=True)
        if not source.is_relative_to(core) or not source.is_file():
            raise SystemExit(f'Core file leaves snapshot: {name}')
        if source.stat().st_size != info['bytes'] or digest(source) != info['sha256']:
            raise SystemExit(f'Incomplete or changed official file: {name}')
        verified[name] = source
    required = ('wenilla_bg.wasm', 'wenilla.js', 'index.html', 'rogue.js', 'boot.js', 'boot-manifest.json', 'world-manifest.json', 'data/__index')
    if any(name not in verified for name in required):
        raise SystemExit('The official core snapshot is incomplete')
    for name, source in verified.items():
        if name.endswith('.js'):
            for dependency in module_dependencies(source.read_text()):
                target = (Path(name).parent / dependency).as_posix()
                if target not in verified:
                    raise SystemExit(f'Missing current-build module dependency: {target}')
    wasm_sha = core_files['wenilla_bg.wasm']['sha256']
    font_manifest = {'fonts': {}}
    for name in ('azs_sc.ttf', 'azs_jp.ttf', 'azs_kr.ttf'):
        relative = 'data/fonts/' + name
        source = verified.get(relative, base / relative)
        if not source.is_file():
            raise SystemExit(f'Missing official CJK font: {name}')
        font_manifest['fonts'][name] = {'sha256': digest(source), 'bytes': source.stat().st_size,
                                      'source': 'https://wow.aethus.pl/' + relative}
    output.mkdir(parents=True, exist_ok=True)
    overlay = output / 'overlay'
    overlay.mkdir(exist_ok=True)
    original = verified['index.html'].read_text()
    if '<head>' not in original or 'android-bridge.js' in original:
        raise SystemExit('Unexpected original HTML layout')
    (overlay / 'index.html').write_text(original.replace('<head>', '<head>\n<script src="./android-bridge.js?v=android-1"></script>', 1))
    files = {}
    for source in sorted(base.rglob('*')):
        if not source.is_file():
            continue
        resolved = source.resolve(strict=True)
        if not resolved.is_relative_to(base):
            raise SystemExit('An original resource leaves the web directory')
        name = source.relative_to(base).as_posix()
        files[name] = source
    files.update(verified)
    files['index.html'] = overlay / 'index.html'
    files['android-bridge.js'] = ROOT / 'web/android-bridge.js'
    files['android-probe.html'] = ROOT / 'web/android-probe.html'
    names = json.loads(verified['data/__index'].read_text())
    known = {name.lower() for name in names}
    for name in ('Fonts\\AZS_SC.TTF', 'Fonts\\AZS_JP.TTF', 'Fonts\\AZS_KR.TTF'):
        if name.lower() not in known:
            names.append(name)
    (overlay / '__index').write_text(json.dumps(names, ensure_ascii=False, separators=(',', ':')))
    files['data/__index'] = overlay / '__index'
    lengths = {name: source.stat().st_size for name, source in files.items()}
    (output / 'android-asset-index.json').write_text(json.dumps(lengths, ensure_ascii=False, separators=(',', ':')))
    provenance = {
        'game_version': core_manifest['game_version'], 'game_build': core_manifest['game_build'],
        'asset_revision': core_manifest['game_build'] + '-android.1',
        'original_wasm_sha256': wasm_sha, 'original_wasm_modified': False,
        'source': 'https://wow.aethus.pl/', 'original_mac_base': str(base),
        'original_core_manifest': core_manifest,
        'font_patch': font_manifest,
        'asset_files': len(files), 'asset_bytes': sum(lengths.values()),
        'android_adapter_files': {n: digest(files[n]) for n in ('index.html', 'android-bridge.js', 'android-probe.html')},
    }
    (output / 'game-provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n')
    plan = {'base': str(base), 'files': {name: str(source.resolve()) for name, source in files.items()}}
    (output / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, separators=(',', ':')))
    print(json.dumps({'files': len(files), 'bytes': sum(lengths.values()), 'wasm_sha256': wasm_sha}))
    return files


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--web', type=Path, default=DEFAULT_WEB)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/assets')
    parser.add_argument('--core', type=Path, default=DEFAULT_CORE)
    args = parser.parse_args()
    prepare(args.web, args.output, args.core)
