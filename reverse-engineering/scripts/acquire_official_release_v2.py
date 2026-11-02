#!/usr/bin/env python3
"""Freeze official Windows/Web bytes with bounded owned HTTPS transfers.

HTTP content compression is negotiated independently of the Windows gzip
update container. No target is executed and no prior fixed input is changed.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse, gzip, hashlib, json, os, re, signal, subprocess, time
from acquire_official_snapshot import ROOT, ORIGIN, official_url


def sha(p):
    with p.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def missing(pid, group=False):
    try:
        (os.killpg if group else os.kill)(pid, 0)
    except ProcessLookupError:
        return True
    return False


def download(directory, filename, url, *, expected_bytes=None, max_bytes=120_000_000):
    official_url(url)
    target = directory / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists() and not target.with_name(target.name + '.attempt.json').exists()
    partial = target.with_name(target.name + '.part')
    headers = target.with_name(target.name + '.headers.txt')
    command = ['curl', '--compressed', '--fail', '--silent', '--show-error', '--location',
               '--proto', '=https', '--proto-redir', '=https', '--connect-timeout', '15',
               '--max-time', '55', '--max-filesize', str(max_bytes), '--dump-header', str(headers),
               '--output', str(partial), '--write-out', '%{http_code}\n%{url_effective}\n%{size_download}\n', url]
    started = time.monotonic()
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, start_new_session=True)
    save(target.with_name(target.name + '.owned-start.json'),
         dict(pid=p.pid, pgid=p.pid, command=command, timeout_seconds=60))
    try:
        stdout, stderr = p.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        stdout, stderr = p.communicate()
    terminal = dict(pid=p.pid, pgid=p.pid, exit_code=p.returncode,
                    seconds=time.monotonic() - started, pid_missing=missing(p.pid),
                    pgid_missing=missing(p.pid, True))
    attempt = dict(at_utc=datetime.now(timezone.utc).isoformat(), url=url,
                   stdout=stdout, stderr=stderr, process=terminal,
                   partial_bytes=partial.stat().st_size if partial.exists() else 0)
    save(target.with_name(target.name + '.attempt.json'), attempt)
    if p.returncode:
        raise RuntimeError('Bounded HTTPS transfer failed: ' + filename + ': ' + stderr[:400])
    status, effective, transfer_bytes = stdout.strip().splitlines()
    official_url(effective)
    size = partial.stat().st_size
    assert status == '200' and 0 < size <= max_bytes
    assert expected_bytes is None or size == expected_bytes
    assert terminal['pid_missing'] and terminal['pgid_missing']
    partial.rename(target)
    record = dict(url=url, effective_url=effective, status=200, bytes=size,
                  sha256=sha(target), filename=filename, headers_sha256=sha(headers),
                  transfer_bytes=int(transfer_bytes), decoded_by='curl --compressed',
                  attempt_sha256=sha(target.with_name(target.name + '.attempt.json')))
    save(target.with_name(target.name + '.http.json'), record)
    print(json.dumps(dict(downloaded=filename, decoded_bytes=size)), flush=True)
    return record


def page_stamp(path):
    m = re.search(r'''(?:src|href)=["']([^"']*rogue\.js\?v=([^"'&]+))''', path.read_text())
    assert m and re.fullmatch('[0-9a-zA-Z_-]{1,80}', m[2])
    return m[2]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--expected-version', required=True)
    ap.add_argument('--expected-native-sha256', required=True)
    args = ap.parse_args()
    assert re.fullmatch(r'\d+\.\d+\.\d+', args.expected_version)
    assert re.fullmatch('[0-9a-f]{64}', args.expected_native_sha256)
    base = (ROOT / 'originals').resolve()
    assert str(base).startswith('/Volumes/RuiRui4TB/')
    out = base / datetime.now(timezone.utc).strftime('official-release-v2-%Y%m%dT%H%M%S.%fZ')
    out.mkdir(exist_ok=False)
    sources = [Path(__file__).resolve(), ROOT / 'scripts/acquire_official_snapshot.py']
    before = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    (out / 'source-snapshot').mkdir()
    for p in sources:
        (out / 'source-snapshot' / p.name).write_bytes(p.read_bytes())
    result = dict(expected_version=args.expected_version, expected_native_sha256=args.expected_native_sha256,
                  started_at_utc=datetime.now(timezone.utc).isoformat(), source_sha256_before=before,
                  status='started', consumed_build=None, target_executed=False, wasm_instantiated=False,
                  user_saves_accessed=False, installed_packages_replaced=False, fixed_inputs_replaced=False)
    print(json.dumps(dict(directory=str(out))), flush=True)
    try:
        meta = download(out, 'windows-latest.json', ORIGIN + 'exe/latest.json', max_bytes=100_000)
        manifest = json.loads((out / 'windows-latest.json').read_text())
        assert manifest['version'] == args.expected_version and manifest['sha256'] == args.expected_native_sha256
        assert type(manifest['size']) is int and 0 < manifest['size'] <= 250_000_000
        assert 0 < len(manifest['parts']) <= 16
        parts = []
        for i, part in enumerate(manifest['parts']):
            assert type(part['size']) is int and 0 < part['size'] <= 25_000_000
            parts.append(download(out, f'windows-update-parts/part-{i:03}.bin',
                                  official_url(part['url'], ORIGIN + 'exe/'),
                                  expected_bytes=part['size'], max_bytes=25_000_000))
        compressed = out / ('AzerothSurvivors-' + args.expected_version + '.exe.gz')
        with compressed.open('wb') as stream:
            for part in parts:
                stream.write((out / part['filename']).read_bytes())
        native_dir = out / ('windows-' + args.expected_version)
        native_dir.mkdir()
        exe = native_dir / 'AzerothSurvivors.exe'
        count = 0
        with gzip.open(compressed, 'rb') as source, exe.with_suffix('.exe.part').open('wb') as target:
            while block := source.read(1024 * 1024):
                count += len(block)
                assert count <= manifest['size']
                target.write(block)
        assert count == manifest['size'] and sha(exe.with_suffix('.exe.part')) == manifest['sha256']
        exe.with_suffix('.exe.part').rename(exe)
        native = dict(version=args.expected_version, manifest=meta, parts=parts,
                      notes=manifest.get('notes'), compressed_bytes=compressed.stat().st_size,
                      compressed_sha256=sha(compressed), gzip_crc_isize_passed=True,
                      exe_relative_path=str(exe.relative_to(out)), exe_bytes=count,
                      exe_sha256=sha(exe), official_identity_matched=True, target_executed=False)
        save(out / 'windows-acquisition.json', native)
        result['native'] = native
        index = download(out, 'official-index.html', ORIGIN, max_bytes=5_000_000)
        stamp = page_stamp(out / 'official-index.html')
        scripts = {n: download(out, 'official-' + n, official_url(n + '?v=' + stamp), max_bytes=10_000_000)
                   for n in ('rogue.js', 'boot.js', 'wenilla.js')}
        wasm = download(out, 'latest-wenilla_bg.wasm', official_url('wenilla_bg.wasm?v=' + stamp))
        raw = (out / 'latest-wenilla_bg.wasm').read_bytes()
        assert raw.startswith(b'\0asm\1\0\0\0')
        anchor = raw.find(b'Made by Aethus')
        assert anchor >= 0 and raw.find(b'Made by Aethus', anchor + 1) == -1
        assert args.expected_version.encode() in raw[anchor:anchor + 240]
        after_index = download(out, 'official-index-after.html', ORIGIN, max_bytes=5_000_000)
        after_manifest = download(out, 'windows-latest-after.json', ORIGIN + 'exe/latest.json', max_bytes=100_000)
        coherent = (json.loads((out / 'windows-latest-after.json').read_text()) == manifest
                    and page_stamp(out / 'official-index-after.html') == stamp
                    and index['sha256'] == after_index['sha256'])
        web = dict(stamp=stamp, stamp_after=page_stamp(out / 'official-index-after.html'),
                   index=index, scripts=scripts, wasm=wasm, index_after=after_index,
                   page_stamp_stable_during_acquisition=coherent,
                   branding_discovery=dict(file_offset=anchor, context_hex=raw[anchor:anchor + 240].hex(),
                                           expected_version_present=True, consumed_build_identity_proved=False),
                   official_independent_wasm_digest_published=False,
                   sha256_origin='Computed locally from complete HTTPS decoded bytes',
                   application_start_called=False, module_instantiated=False)
        save(out / 'web-acquisition.json', web)
        result.update(web=web, ending_manifest=after_manifest,
                      native_manifest_equal_before_after=coherent, raw_html_equal_before_after=coherent)
        assert coherent, 'Deployment changed; retain all bytes without coherent-release claim'
        result['status'] = 'coherent_bytes_acquired_build_identity_pending'
    except BaseException as error:
        result.update(status='failed_preserved', error=repr(error))
        raise
    finally:
        result.update(finished_at_utc=datetime.now(timezone.utc).isoformat(),
                      source_sha256_after={str(p.relative_to(ROOT)): sha(p) for p in sources})
        result['sources_unchanged'] = before == result['source_sha256_after']
        save(out / 'release-acquisition.json', result)
        print(json.dumps(dict(directory=str(out), status=result['status'],
                              receipt_sha256=sha(out / 'release-acquisition.json'))), flush=True)
    assert result['sources_unchanged']


if __name__ == '__main__':
    main()
