#!/usr/bin/env python3
"""Project-local pinned REA launcher. Never registers clients or changes game files."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'toolchain.json').read_text())
TOOLS = ROOT / '.toolchain'
NODE = TOOLS / 'runtime/node_modules/node/bin/node'
PACKAGE = TOOLS / 'rea/node_modules/rea-agents'
ENTRY = PACKAGE / 'scripts/rea.mjs'


def runtime():
    if not NODE.is_file() or not ENTRY.is_file():
        raise SystemExit('Run: python3 reverse-engineering/scripts/rea.py bootstrap')
    version = subprocess.check_output([str(NODE), '--version'], text=True).strip()
    if version != 'v' + CONFIG['node_version']:
        raise SystemExit('Local Node version differs from toolchain.json')
    package = json.loads((PACKAGE / 'package.json').read_text())
    if package['version'] != CONFIG['rea_version']:
        raise SystemExit('Local REA version differs from toolchain.json')
    lock = json.loads((TOOLS / 'rea/package-lock.json').read_text())
    if lock['packages']['node_modules/rea-agents']['integrity'] != CONFIG['rea_tarball_integrity']:
        raise SystemExit('Local REA package lock differs from the pinned registry integrity')
    env = dict(os.environ)
    env['PATH'] = str(NODE.parent) + os.pathsep + env.get('PATH', '')
    return env


def bootstrap():
    npm = shutil.which('npm')
    if npm is None:
        raise SystemExit('An existing npm is required to acquire the private runtime')
    TOOLS.mkdir(exist_ok=True)
    subprocess.run([npm, 'install', '--prefix', str(TOOLS / 'runtime'), '--no-audit',
                    '--no-fund', '--package-lock=false', '--no-save',
                    'node@' + CONFIG['node_version']], check=True)
    env = dict(os.environ)
    env['PATH'] = str(NODE.parent) + os.pathsep + env.get('PATH', '')
    subprocess.run([npm, 'install', '--prefix', str(TOOLS / 'rea'), '--omit=optional',
                    '--ignore-scripts', '--no-audit', '--no-fund', '--save-exact',
                    CONFIG['rea_package'] + '@' + CONFIG['rea_version']], env=env, check=True)
    runtime()
    print('Project-local REA is ready; no MCP client registration was changed.')


def main():
    args = sys.argv[1:]
    if args == ['bootstrap']:
        bootstrap()
        return
    if not args:
        raise SystemExit('Usage: rea.py bootstrap | <REA CLI arguments>')
    env = runtime()
    # Invoke argv directly. No shell evaluation and no implicit target selection.
    raise SystemExit(subprocess.run([str(NODE), str(ENTRY), *args], env=env).returncode)


if __name__ == '__main__':
    main()
