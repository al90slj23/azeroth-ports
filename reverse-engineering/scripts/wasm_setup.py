#!/usr/bin/env python3
"""Acquire the exact official WABT macOS ARM64 release into the local research area."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = 'wabt-1.0.42-macos-arm64.tar.gz'
URL = 'https://github.com/WebAssembly/wabt/releases/download/1.0.42/' + ARCHIVE
EXPECTED = '3f654779b436c628db3ca4323c51538815f5fbc887a6d5f3bb1c18d36281e240'
TOOLS = ('wasm-validate', 'wasm-objdump', 'wasm2wat')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    if (platform.system(), platform.machine()) != ('Darwin', 'arm64'):
        raise SystemExit('This pinned WABT producer profile is verified for macOS ARM64 only')
    root = ROOT / '.toolchain/rea-wasm-profile'
    root.mkdir(parents=True, exist_ok=True)
    archive = root / ARCHIVE
    if not archive.exists():
        with tempfile.TemporaryDirectory(prefix='wabt-download-', dir=root) as temporary:
            partial = Path(temporary) / ARCHIVE
            subprocess.run(['curl', '--fail', '--location', '--retry', '2', '--connect-timeout', '20',
                            '--max-time', '180', URL, '-o', str(partial)], check=True)
            if sha(partial) != EXPECTED:
                raise SystemExit('Downloaded WABT archive SHA-256 differs from the fixed official release')
            partial.replace(archive)
    if archive.is_symlink() or sha(archive) != EXPECTED:
        raise SystemExit('Existing WABT archive identity differs; inspect it before replacing')
    destination = root / 'wabt'
    expected_tools = {}
    with tarfile.open(archive) as source:
        members = source.getmembers()
        total = 0
        seen = set()
        for member in members:
            relative = PurePosixPath(member.name)
            if (relative.is_absolute() or '..' in relative.parts or
                    not relative.parts or relative.parts[0] != 'wabt-1.0.42' or
                    str(relative) in seen or not (member.isfile() or member.isdir())):
                raise SystemExit('Unsafe or unexpected WABT archive member')
            seen.add(str(relative)); total += member.size
            if total > 128 * 1024 * 1024:
                raise SystemExit('WABT archive unpacked size exceeds this local profile')
            if member.isfile() and str(relative) in {f'wabt-1.0.42/bin/{t}' for t in TOOLS}:
                with source.extractfile(member) as data:
                    expected_tools[relative.name] = hashlib.sha256(data.read()).hexdigest()
        if set(expected_tools) != set(TOOLS):
            raise SystemExit('Official archive is missing required WABT tools')
        if destination.exists():
            if destination.is_symlink():
                raise SystemExit('WABT destination must be a project-local directory')
        else:
            with tempfile.TemporaryDirectory(prefix='wabt-unpack-', dir=root) as temporary:
                stage = Path(temporary) / 'wabt'; stage.mkdir()
                # Only regular files/directories are admitted; no links or special files.
                for member in members:
                    target = stage.joinpath(*PurePosixPath(member.name).parts)
                    if member.isdir():
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with source.extractfile(member) as data, target.open('xb') as out:
                            shutil.copyfileobj(data, out)
                        target.chmod(0o755 if member.mode & 0o111 else 0o644)
                stage.replace(destination)
    identities = {}
    for name in TOOLS:
        tool = destination / 'wabt-1.0.42/bin' / name
        if tool.is_symlink() or sha(tool) != expected_tools[name]:
            raise SystemExit('Installed WABT differs from verified archive: ' + name)
        banner = subprocess.check_output([str(tool), '--version'], text=True, timeout=10).strip()
        if banner != '1.0.42':
            raise SystemExit('Installed WABT reported an unexpected version: ' + name)
        identities[name] = {'version': banner, 'sha256': expected_tools[name]}
    (root / 'installed-provenance.json').write_text(json.dumps({
        'source': URL, 'archive_sha256': EXPECTED, 'tools': identities,
        'global_installation': False
    }, indent=2) + '\n')
    print(json.dumps({'status': 'ready', 'archive_sha256': EXPECTED,
                      'tool_count': len(identities), 'global_installation': False}))


if __name__ == '__main__':
    main()
