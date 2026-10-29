#!/usr/bin/env python3
"""Create a verified APK asset plan without copying the 1.7 GB original resource tree."""
import argparse
import hashlib
import json
from pathlib import Path
from sync_official import module_dependencies
from patch_mobile_reroll import patch as patch_reroll

ROOT = Path(__file__).resolve().parents[1]
ANDROID_REVISION = 4
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
    adapters = ('android-bridge.js', 'android-performance.js', 'android-touch.js', 'android-localization.js')
    tags = '\n'.join(f'<script src="./{name}?v=android-{ANDROID_REVISION}"></script>' for name in adapters)
    (overlay / 'index.html').write_text(original.replace('<head>', '<head>\n' + tags, 1))
    # One explicit hook after upstream mobile defaults, before WASM starts. Keep the original snapshot intact.
    rogue = verified['rogue.js'].read_text()
    hook = "  if (lite !== null) window.__wenilla_env.pbr_lite = lite;"
    if rogue.count(hook) != 1:
        raise SystemExit('Official boot defaults changed; review Android performance hook')
    (overlay / 'rogue.js').write_text(rogue.replace(hook, hook +
        "\n  window.__azerothAndroidPerformance?.applyBootOptions();", 1))
    # Upstream keeps a fixed canvas backing size on some mobile views. Normalize
    # only its input getters to that canvas, preserving native pointer identity,
    # trusted events and the game's multitouch controls at arbitrary Android DPR.
    glue = verified['wenilla.js'].read_text()
    for field, axis in (('offsetX', 'x'), ('offsetY', 'y'), ('movementX', 'x'), ('movementY', 'y')):
        getter = f'const ret = arg0.{field};'
        if glue.count(getter) != 1:
            raise SystemExit(f'Official input glue changed: {field}')
        replacement = (f'const ret = window.AzerothAndroidTouch?.canvasCoordinate(arg0, "{axis}", arg0.{field})'
                       f' ?? arg0.{field};')
        glue = glue.replace(getter, replacement, 1)
    # Pause only this WASM client's frames and monotonic game clock while its
    # Android quick panel is open. DOM animation/timers and wall-clock saves are
    # left intact; no Escape toggle can accidentally resume an already paused run.
    frame_hooks = {
        'arg0.cancelAnimationFrame(arg1);':
            'if (window.AzerothAndroidPause) window.AzerothAndroidPause.cancelFrame(arg0, arg1); else arg0.cancelAnimationFrame(arg1);',
        'const ret = arg0.requestAnimationFrame(arg1);':
            'const ret = window.AzerothAndroidPause ? window.AzerothAndroidPause.requestFrame(arg0, arg1) : arg0.requestAnimationFrame(arg1);',
    }
    for original_call, replacement in frame_hooks.items():
        if glue.count(original_call) != 1:
            raise SystemExit('Official frame scheduling changed; review Android pause adapter')
        glue = glue.replace(original_call, replacement, 1)
    now_call = 'const ret = arg0.now();'
    if glue.count(now_call) != 2:
        raise SystemExit('Official monotonic clock imports changed; review Android pause adapter')
    glue = glue.replace(now_call, 'const ret = window.AzerothAndroidPause ? window.AzerothAndroidPause.monotonicNow(arg0) : arg0.now();')
    (overlay / 'wenilla.js').write_text(glue)
    # Mobile UI-only constants in the original Reroll button. Exact source,
    # function and instruction hashes are checked; original snapshots stay intact.
    mobile_wasm, reroll_edits = patch_reroll(verified['wenilla_bg.wasm'].read_bytes())
    patched_wasm = overlay / 'wenilla_bg.wasm'
    patched_wasm.write_bytes(mobile_wasm)
    mobile_wasm_sha = digest(patched_wasm)
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
    files['rogue.js'] = overlay / 'rogue.js'
    files['wenilla.js'] = overlay / 'wenilla.js'
    files['wenilla_bg.wasm'] = patched_wasm
    for name in adapters:
        source = ROOT / 'web' / name
        if not source.is_file():
            raise SystemExit(f'Missing Android adapter: {name}')
        files[name] = source
    files['android-probe.html'] = ROOT / 'web/android-probe.html'
    # Separate, verified Simplified Chinese variants. The locale adapter selects
    # these per browser preference; the originals remain available for other languages.
    localized = ROOT / 'android-overrides/zh-CN'
    localization = json.loads((localized / 'localization-manifest.json').read_text())
    for name, info in localization['files'].items():
        rel = Path(name)
        if rel.is_absolute() or '..' in rel.parts or rel.as_posix() != name or '\\' in name:
            raise SystemExit(f'Unsafe localized path: {name}')
        source = (localized / rel).resolve(strict=True)
        if not source.is_relative_to(localized.resolve()) or digest(source) != info['sha256']:
            raise SystemExit(f'Changed localized file: {name}')
        if name not in files or digest(files[name]) != info['original_sha256']:
            raise SystemExit(f'Original localization source changed: {name}')
        files['android-zh-CN/' + name] = source
    files['android-zh-CN/manifest.json'] = localized / 'localization-manifest.json'
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
        'asset_revision': core_manifest['game_build'] + f'-android.{ANDROID_REVISION}',
        'original_wasm_sha256': wasm_sha, 'original_wasm_modified': True,
        'packaged_wasm_sha256': mobile_wasm_sha, 'gameplay_rules_modified': False,
        'wasm_ui_patch': {'name': 'native-reroll-button-2x', 'source_snapshot_preserved': True, 'instruction_edits': reroll_edits},
        'source': 'https://wow.aethus.pl/', 'original_mac_base': str(base),
        'original_core_manifest': core_manifest,
        'font_patch': font_manifest, 'localization_patch': localization,
        'asset_files': len(files), 'asset_bytes': sum(lengths.values()),
        'android_adapter_files': {n: digest(files[n]) for n in ('index.html', 'rogue.js', 'wenilla.js', 'android-probe.html', *adapters)},
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
