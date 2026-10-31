#!/usr/bin/env python3
"""Acquire pinned official Ghidra/JDK privately and run REA provider diagnostics.

Does not register MCP, change global Java, or execute the target game.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / '.toolchain'
DOWNLOADS = TOOLS / 'downloads'
SOURCES = {
    'ghidra': {
        'version': '12.1.4',
        'url': 'https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.1.4_build/ghidra_12.1.4_PUBLIC_20260921.zip',
        'sha256': 'ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db',
        'bytes': 569649598,
        'metadata_source': 'https://api.github.com/repos/NationalSecurityAgency/ghidra/releases/tags/Ghidra_12.1.4_build',
    },
    'jdk': {
        'version': '21.0.13+9',
        'url': 'https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.13%2B9/OpenJDK21U-jdk_aarch64_mac_hotspot_21.0.13_9.tar.gz',
        'sha256': 'bf036b35b071bfb2f54f2c0af8ee8d88afa95ee6eb3dce02c0f94cfc2524d04a',
        'bytes': 199754598,
        'metadata_source': 'https://api.adoptium.net/v3/assets/latest/21/hotspot?architecture=aarch64&image_type=jdk&os=mac&vendor=eclipse',
    },
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def download(item):
    name, info = item
    destination = DOWNLOADS / info['url'].rsplit('/', 1)[-1]
    if not destination.exists():
        partial = destination.with_name(destination.name + '.partial')
        print(f'Downloading official {name} {info["version"]} ({info["bytes"]} bytes)', flush=True)
        subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                        '--retry', '3', '--connect-timeout', '20', '--max-time', '1200',
                        info['url'], '-o', str(partial)], check=True)
        if partial.stat().st_size != info['bytes'] or digest(partial) != info['sha256']:
            raise RuntimeError('Official archive size/digest mismatch: ' + name)
        partial.rename(destination)
    if destination.stat().st_size != info['bytes'] or digest(destination) != info['sha256']:
        raise RuntimeError('Cached official archive size/digest mismatch: ' + name)
    print(f'Verified official {name} SHA-256', flush=True)
    return name, destination


def extract_ghidra(archive):
    parent = TOOLS / 'ghidra'
    home = parent / 'ghidra_12.1.4_PUBLIC'
    if home.exists():
        return home
    parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as source:
        for member in source.infolist():
            path = Path(member.filename)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != home.name:
                raise RuntimeError('Unexpected Ghidra archive member')
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise RuntimeError('Unexpected symlink in Ghidra ZIP')
        source.extractall(parent)
        # zipfile preserves contents, but executable bits require explicit restoration.
        for member in source.infolist():
            mode = (member.external_attr >> 16) & 0o777
            if mode:
                (parent / member.filename).chmod(mode)
    return home


def extract_jdk(archive):
    parent = TOOLS / 'jdk'
    home = parent / 'jdk-21.0.13+9/Contents/Home'
    if home.exists():
        return home
    parent.mkdir(exist_ok=True)
    with tarfile.open(archive) as source:
        source.extractall(parent, filter='data')
    if not home.is_dir():
        raise RuntimeError('Unexpected JDK archive layout')
    return home


def build_mac_decompiler(ghidra):
    destination = ghidra / 'Ghidra/Features/Decompiler/os/mac_arm_64/decompile'
    if destination.is_file():
        return
    source = ghidra / 'Ghidra/Features/Decompiler/src/decompile/cpp'
    output = ROOT / 'evidence/native-setup'
    output.mkdir(parents=True, exist_ok=True)
    command = ['make', '-j4', 'ghidra_opt', 'CXX=clang++ -std=c++11',
               'ARCH_TYPE=-arch arm64', 'OSDIR=mac_arm_64',
               'ADDITIONAL_FLAGS=-mmacosx-version-min=11.0 -w']
    print('Building missing macOS ARM64 decompiler from the verified official archive sources', flush=True)
    with (output / 'decompiler-build.log').open('w') as log:
        subprocess.run(command, cwd=source, stdout=log, stderr=subprocess.STDOUT, check=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / 'ghidra_opt', destination)
    destination.chmod(0o755)
    info = {'source_archive_sha256': SOURCES['ghidra']['sha256'],
            'source_relative_path': 'Ghidra/Features/Decompiler/src/decompile/cpp',
            'source_edited': False, 'make_arguments': command,
            'compiler': subprocess.check_output(['clang++', '--version'], text=True),
            'artifact_sha256': digest(destination),
            'artifact_file_type': subprocess.check_output(['file', str(destination)], text=True).strip()}
    (TOOLS / 'native-build.json').write_text(json.dumps(info, indent=2) + '\n')


def main():
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise SystemExit('This pinned setup profile is for macOS ARM64 only')
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        archives = dict(pool.map(download, SOURCES.items()))
    ghidra = extract_ghidra(archives['ghidra'])
    java = extract_jdk(archives['jdk'])
    build_mac_decompiler(ghidra)
    properties = (ghidra / 'Ghidra/application.properties').read_text()
    if 'application.version=12.1.4' not in properties:
        raise RuntimeError('Extracted Ghidra version differs from pinned release')
    for required in [ghidra / 'support/analyzeHeadless',
                     ghidra / 'Ghidra/Features/Decompiler/os/mac_arm_64/decompile',
                     java / 'bin/java', java / 'bin/javac']:
        if not required.is_file() or not os.access(required, os.X_OK):
            raise RuntimeError('Required native executable is missing: ' + str(required))
    env = dict(os.environ, GHIDRA_INSTALL_DIR=str(ghidra), JAVA_HOME=str(java))
    env['PATH'] = str(java / 'bin') + os.pathsep + env.get('PATH', '')
    output = ROOT / 'evidence/native-setup'
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'doctor.json').open('w') as out, (output / 'doctor.stderr.log').open('w') as err:
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/rea.py'),
                                 'doctor', '--provider', 'ghidra', '--json'],
                                env=env, stdout=out, stderr=err)
    install = {'sources': SOURCES, 'GHIDRA_INSTALL_DIR': str(ghidra), 'JAVA_HOME': str(java),
               'doctor_exit_code': result.returncode, 'target_executed': False,
               'mcp_registration_changed': False}
    (TOOLS / 'native-install.json').write_text(json.dumps(install, indent=2) + '\n')
    print(json.dumps({k: v for k, v in install.items() if k != 'sources'}), flush=True)
    if result.returncode:
        raise SystemExit('Provider diagnostics failed; inspect evidence/native-setup/doctor.json')


if __name__ == '__main__':
    main()
