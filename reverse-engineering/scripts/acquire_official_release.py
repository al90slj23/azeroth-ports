#!/usr/bin/env python3
"""Freeze a release's official native/Web bytes without executing either.

The historical acquisition script's eight-character branding regex is not
used. Branding context is a discovery observation, never a consumed-build
identity proof. A separate instruction/pointer/length analysis must supply it.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import re

from acquire_official_snapshot import ORIGIN, acquire_windows, download, official_url

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def page_stamp(path):
    match = re.search(r'''(?:src|href)=["']([^"']*rogue\.js\?v=([^"'&]+))''', path.read_text())
    if not match or not re.fullmatch(r'[0-9a-zA-Z_-]{1,80}', match[2]):
        raise ValueError('Official page has no valid stamped rogue.js')
    return match[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-version', required=True)
    parser.add_argument('--directory', type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r'\d+\.\d+\.\d+', args.expected_version):
        parser.error('Expected version must be numeric semver')
    originals = (ROOT / 'originals').resolve()
    if not originals.is_relative_to(Path('/Volumes/RuiRui4TB').resolve()):
        raise ValueError('Research downloads must stay on the4T volume')
    directory = (args.directory or originals / datetime.now(timezone.utc).strftime(
        'official-release-%Y%m%dT%H%M%S.%fZ')).resolve()
    if not directory.is_relative_to(originals):
        raise ValueError('Output must stay inside ignored originals/')
    directory.mkdir(parents=True, exist_ok=False)
    sources = (Path(__file__).resolve(), ROOT / 'scripts/acquire_official_snapshot.py')
    frozen = {}
    for source in sources:
        target = directory / 'source-snapshot' / source.name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(source.read_bytes())
        frozen[str(source.relative_to(ROOT))] = sha(target)
    result = dict(kind='frozen_official_native_and_web_release_acquisition',
        expected_version=args.expected_version, consumed_build=None,
        started_at_utc=datetime.now(timezone.utc).isoformat(),
        target_executed=False, wasm_instantiated=False, user_saves_accessed=False,
        installed_packages_replaced=False, source_sha256_before=frozen)
    print(json.dumps(dict(directory=str(directory))), flush=True)
    try:
        download(directory, 'windows-latest.json', ORIGIN + 'exe/latest.json', max_bytes=100_000)
        manifest = json.loads((directory / 'windows-latest.json').read_text())
        if manifest['version'] != args.expected_version:
            raise ValueError('Official latest changed before acquisition; frozen metadata retained')
        native = acquire_windows(directory)
        index = download(directory, 'official-index.html', ORIGIN, max_bytes=5_000_000)
        stamp = page_stamp(directory / 'official-index.html')
        scripts = {name: download(directory, 'official-' + name,
            official_url(name + '?v=' + stamp), max_bytes=10_000_000)
            for name in ('rogue.js', 'boot.js', 'wenilla.js')}
        wasm = download(directory, 'latest-wenilla_bg.wasm',
            official_url('wenilla_bg.wasm?v=' + stamp), max_bytes=120_000_000)
        raw = (directory / 'latest-wenilla_bg.wasm').read_bytes()
        if not raw.startswith(b'\x00asm\x01\x00\x00\x00'):
            raise ValueError('Not a version1 WASM module')
        anchor = raw.find(b'Made by Aethus')
        if anchor < 0 or raw.find(b'Made by Aethus', anchor + 1) >= 0:
            raise ValueError('Branding discovery anchor is not unique')
        context = raw[anchor:anchor + 240]
        if args.expected_version.encode() not in context:
            raise ValueError('Web branding version differs from frozen native version')
        ending = download(directory, 'official-index-after.html', ORIGIN, max_bytes=5_000_000)
        after_stamp = page_stamp(directory / 'official-index-after.html')
        ending_manifest = download(directory, 'windows-latest-after.json',
            ORIGIN + 'exe/latest.json', max_bytes=100_000)
        after_manifest = json.loads((directory / 'windows-latest-after.json').read_text())
        web = dict(stamp=stamp, stamp_after=after_stamp,
            page_stamp_stable_during_acquisition=stamp == after_stamp,
            index=index, index_after=ending, scripts=scripts, wasm=wasm,
            branding_discovery=dict(file_offset=anchor, context_hex=context.hex(),
                expected_version_present=True, consumed_build_identity_proved=False),
            official_independent_wasm_digest_published=False,
            sha256_origin='Computed locally from saved HTTPS bytes',
            application_start_called=False, module_instantiated=False)
        save(directory / 'web-acquisition.json', web)
        result.update(native=native, web=web, ending_manifest=ending_manifest,
            native_manifest_equal_before_after=manifest == after_manifest,
            raw_html_equal_before_after=index['sha256'] == ending['sha256'])
        if stamp != after_stamp or manifest != after_manifest:
            raise ValueError('Official deployment changed during acquisition; not a coherent release')
        result['status'] = 'coherent_bytes_acquired_build_identity_pending'
    except BaseException as error:
        result.update(status='failed_preserved', error=repr(error))
        raise
    finally:
        result.update(finished_at_utc=datetime.now(timezone.utc).isoformat(),
            source_sha256_after={str(p.relative_to(ROOT)): sha(p) for p in sources})
        result['sources_unchanged'] = result['source_sha256_before'] == result['source_sha256_after']
        save(directory / 'release-acquisition.json', result)
        print(json.dumps(dict(directory=str(directory), status=result['status'],
            receipt_sha256=sha(directory / 'release-acquisition.json'))), flush=True)
    if not result['sources_unchanged']:
        raise RuntimeError('Acquisition producer changed while running')


if __name__ == '__main__':
    main()
