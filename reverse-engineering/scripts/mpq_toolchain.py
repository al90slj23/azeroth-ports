#!/usr/bin/env python3
"""Build/verify project-local official StormLib as a read-only reference tool."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '6bb1882bd00ddbc3729cac5dac0fda81a61e5514'
ARCHIVE_SHA = 'f584f35edf9cb7f5e6adc65ee467ddfcf5f5b2d06445a0b6a3f274755d9e8484'
URL = f'https://codeload.github.com/ladislav-zezula/StormLib/tar.gz/{COMMIT}'
TOOL = ROOT / '.toolchain/mpq-stormlib9.40'
ARCHIVE = TOOL / f'StormLib-{COMMIT}.tar.gz'
SOURCE = TOOL / f'StormLib-{COMMIT}'
LIBRARY = TOOL / 'build/storm.framework/storm'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def source_identity():
    if sha(ARCHIVE) != ARCHIVE_SHA:
        raise ValueError('Official source archive identity differs')
    files = {}
    with tarfile.open(ARCHIVE) as archive:
        for member in archive.getmembers():
            if member.issym() or member.islnk() or not (TOOL / member.name).resolve().is_relative_to(TOOL.resolve()):
                raise ValueError('Unsafe source member')
            if member.isfile():
                expected = hashlib.sha256(archive.extractfile(member).read()).hexdigest()
                if sha(TOOL / member.name) != expected:
                    raise ValueError('Extracted source differs: ' + member.name)
                files[member.name] = expected
    return files


def verify():
    receipt = json.loads((TOOL / 'toolchain.json').read_text())
    if receipt['archive_sha256'] != ARCHIVE_SHA or receipt['source_files'] != source_identity():
        raise ValueError('Toolchain source identity differs')
    if not LIBRARY.resolve().is_relative_to(TOOL.resolve()) or sha(LIBRARY) != receipt['library_sha256']:
        raise ValueError('Built StormLib identity differs')
    return receipt


def bootstrap():
    TOOL.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE.exists():
        subprocess.run(['curl', '--fail', '--silent', '--show-error', '--location',
                        '--proto', '=https', '--proto-redir', '=https', '--max-time', '60',
                        '--max-filesize', '20000000', '--output', str(ARCHIVE), URL], check=True, timeout=65)
    if sha(ARCHIVE) != ARCHIVE_SHA:
        raise ValueError('Downloaded official source digest differs')
    if not SOURCE.exists():
        with tarfile.open(ARCHIVE) as archive:
            for member in archive.getmembers():
                if member.issym() or member.islnk() or not (TOOL / member.name).resolve().is_relative_to(TOOL.resolve()):
                    raise ValueError('Unsafe source member')
            archive.extractall(TOOL, filter='data')
    files = source_identity()
    cmake = shutil.which('cmake')
    if not cmake:
        raise ValueError('CMake is required to build the reference tool')
    commands = [[cmake, '-S', str(SOURCE), '-B', str(TOOL / 'build'),
                 '-DBUILD_SHARED_LIBS=ON', '-DSTORM_BUILD_TESTS=OFF', '-DSTORM_SKIP_INSTALL=ON',
                 '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_OSX_ARCHITECTURES=arm64'],
                [cmake, '--build', str(TOOL / 'build'), '--parallel', '4']]
    for number, command in enumerate(commands):
        with (TOOL / f'build-{number}.stdout.txt').open('wb') as stdout, (TOOL / f'build-{number}.stderr.txt').open('wb') as stderr:
            subprocess.run(command, check=True, timeout=60, stdout=stdout, stderr=stderr)
    receipt = {'at_utc': datetime.now(timezone.utc).isoformat(),
               'project': 'Official ladislav-zezula/StormLib', 'release_tag': 'v9.40',
               'commit': COMMIT, 'source_url': URL, 'archive_sha256': ARCHIVE_SHA,
               'source_files': files, 'commands': commands, 'library': str(LIBRARY.resolve()),
               'library_sha256': sha(LIBRARY), 'cmake_sha256': sha(cmake),
               'source_script_sha256': sha(__file__), 'global_installation': False,
               'target_game_executed': False}
    save(TOOL / 'toolchain.json', receipt)
    return verify()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bootstrap', action='store_true')
    args = parser.parse_args()
    receipt = bootstrap() if args.bootstrap else verify()
    print(json.dumps({'library': receipt['library'], 'library_sha256': receipt['library_sha256'],
                      'verified': True, 'target_game_executed': False}))
