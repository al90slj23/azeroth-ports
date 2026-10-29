#!/usr/bin/env python3
"""Build a signed, sideloadable Android APK using official Android build-tools and JDK 17."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import zipfile
from prepare_assets import prepare, DEFAULT_WEB, DEFAULT_CORE, ANDROID_REVISION

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'io.github.al90slj23.azerothsurvivors'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', type=Path, default=ROOT / '.toolchain/android-sdk')
    parser.add_argument('--java-home', type=Path, default=Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home'))
    parser.add_argument('--web', type=Path, default=DEFAULT_WEB)
    parser.add_argument('--core', type=Path, default=DEFAULT_CORE)
    args = parser.parse_args()
    tools = args.sdk / 'build-tools/35.0.0'
    platform = args.sdk / 'platforms/android-35/android.jar'
    env = dict(os.environ, JAVA_HOME=str(args.java_home))
    env['PATH'] = str(args.java_home / 'bin') + os.pathsep + env.get('PATH', '')
    for name in ('aapt2', 'd8', 'zipalign', 'apksigner'):
        if not (tools / name).is_file():
            raise SystemExit(f'Missing Android build-tool: {tools / name}')
    if not platform.is_file():
        raise SystemExit('Android API 35 platform not installed')

    def run(command):
        subprocess.run([str(v) for v in command], env=env, cwd=ROOT, check=True)

    build = ROOT / 'build'
    build.mkdir(exist_ok=True)
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    files = prepare(args.web, build / 'assets', args.core)
    core = json.loads((build / 'assets/game-provenance.json').read_text())
    version = core['game_version'] + f'-android.{ANDROID_REVISION}'
    numbers = [int(n) for n in core['game_version'].split('.')]
    version_code = str(numbers[0] * 100000000 + numbers[1] * 10000 + numbers[2] * 10 + ANDROID_REVISION)
    build_info = ROOT / 'app/src/main/java/io/github/al90slj23/azerothsurvivors/BuildInfo.java'
    build_info.write_text('package ' + PACKAGE + ';\npublic final class BuildInfo {\n'
                          + ' public static final String GAME_VERSION = ' + json.dumps(core['game_version']) + ';\n'
                          + ' public static final String GAME_BUILD = ' + json.dumps(core['game_build']) + ';\n'
                          + ' public static final String ASSET_REVISION = ' + json.dumps(core['asset_revision']) + ';\n'
                          + ' private BuildInfo() {}\n}\n')
    classes = build / 'classes'
    dex = build / 'dex'
    for directory in (classes, dex):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir()
    sources = sorted((ROOT / 'app/src/main/java').rglob('*.java'))
    run([args.java_home / 'bin/javac', '-encoding', 'UTF-8', '-source', '8', '-target', '8',
         '-classpath', platform, '-d', classes, *sources])
    classes_jar = build / 'classes.jar'
    run([args.java_home / 'bin/jar', 'cf', classes_jar, '-C', classes, '.'])
    run([tools / 'd8', '--lib', platform, '--min-api', '31', '--output', dex, classes_jar])
    resources = build / 'resources.zip'
    run([tools / 'aapt2', 'compile', '--dir', ROOT / 'app/src/main/res', '-o', resources])
    base_apk = build / 'base.apk'
    run([tools / 'aapt2', 'link', '-o', base_apk, '--manifest', ROOT / 'app/src/main/AndroidManifest.xml',
         '-I', platform, '--min-sdk-version', '31', '--target-sdk-version', '35',
         '--version-code', version_code, '--version-name', version, resources])
    unaligned = build / 'game-unaligned.apk'
    shutil.copy2(base_apk, unaligned)
    print('Packing original game assets…', flush=True)
    with zipfile.ZipFile(unaligned, 'a', compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=False) as apk:
        apk.write(dex / 'classes.dex', 'classes.dex')
        for name in ('android-asset-index.json', 'game-provenance.json'):
            apk.write(build / 'assets' / name, 'assets/' + name)
        license_file = ROOT.parent / 'macos/assets/font-source/OFL.txt'
        apk.write(license_file, 'assets/licenses/Noto-CJK-OFL.txt')
        for index, (name, source) in enumerate(files.items(), 1):
            apk.write(source, 'assets/www/' + name)
            if index % 5000 == 0:
                print(f'  {index}/{len(files)} files', flush=True)
    aligned = build / 'game-aligned.apk'
    run([tools / 'zipalign', '-f', '-p', '4', unaligned, aligned])
    private = ROOT / '.private'
    private.mkdir(mode=0o700, exist_ok=True)
    secret = private / 'signing-password.txt'
    key = private / 'android-release.keystore'
    if not secret.exists():
        secret.write_text(secrets.token_urlsafe(36) + '\n')
        secret.chmod(0o600)
    if not key.exists():
        run([args.java_home / 'bin/keytool', '-genkeypair', '-keystore', key, '-alias', 'azeroth-android',
             '-storepass:file', secret, '-keypass:file', secret, '-keyalg', 'RSA', '-keysize', '3072',
             '-validity', '10000', '-dname', 'CN=Azeroth Survivors Android Community Build'])
        key.chmod(0o600)
    final = output / f'AzerothSurvivors-{version}-universal.apk'
    run([tools / 'apksigner', 'sign', '--ks', key, '--ks-key-alias', 'azeroth-android',
         '--ks-pass', 'file:' + str(secret),
         '--v1-signing-enabled', 'false', '--v2-signing-enabled', 'true', '--v3-signing-enabled', 'true',
         '--v4-signing-enabled', 'false',
         '--out', final, aligned])
    run([tools / 'zipalign', '-c', '-p', '4', final])
    run([tools / 'apksigner', 'verify', '--verbose', '--print-certs', final])
    metadata = {'apk': str(final), 'package': PACKAGE, 'version': version, 'version_code': int(version_code),
                'min_android_api': 31, 'target_android_api': 35, 'bytes': final.stat().st_size,
                'sha256': sha(final), 'signature_verified': True, 'zip_alignment_verified': True,
                'source_files_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sources},
                'game': json.loads((build / 'assets/game-provenance.json').read_text())}
    (output / 'build-manifest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    (output / 'SHA256SUMS.txt').write_text(f'{metadata["sha256"]}  {final.name}\n')
    print(json.dumps({'apk': str(final), 'bytes': final.stat().st_size, 'sha256': metadata['sha256']}), flush=True)


if __name__ == '__main__':
    main()
