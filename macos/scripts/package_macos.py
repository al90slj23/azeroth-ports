#!/usr/bin/env python3
"""Package the reviewed wrapper and verified official web core in the pinned Mac runtime."""
import argparse
import hashlib
import json
import pathlib
import plistlib
import shutil
import subprocess
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARCHIVE_SHA256 = "f948d53b6a5dd201e91bdbdd2ac20178a42181954756ce63ff0596251d17886d"
ORIGINAL_WRAPPER_SHA256 = "498fa7257bd8897eaab46b0e4e993c8ef6cfaad36dc6a27b56d04718b11631b8"
WRAPPER_FILES = ("main.js", "static-server.js", "coop-proxy.js", "profile-migration.js", "package.json")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verified_web_core(directory):
    """Verify the complete download manifest before extracting or changing an App."""
    directory = directory.resolve(strict=True)
    manifest = json.loads((directory / "core-manifest.json").read_text())
    for field in ("game_version", "game_build", "stamp", "source"):
        if not isinstance(manifest.get(field), str) or not manifest[field]:
            raise SystemExit(f"Missing web core metadata: {field}")
    files = manifest.get("files")
    required = {"index.html", "rogue.js", "wenilla.js", "wenilla_bg.wasm",
                "boot.js", "boot-manifest.json", "world-manifest.json", "data/__index"}
    if not isinstance(files, dict) or not required.issubset(files):
        raise SystemExit("The official web core manifest is incomplete")
    verified = []
    for name, info in files.items():
        relative = pathlib.PurePosixPath(name)
        if (not name or relative.is_absolute() or ".." in relative.parts
                or "\\" in name or str(relative) != name):
            raise SystemExit(f"Unsafe web core member: {name}")
        source = directory.joinpath(*relative.parts).resolve(strict=True)
        if not source.is_relative_to(directory) or not source.is_file():
            raise SystemExit(f"Web core member leaves its directory: {name}")
        if (not isinstance(info, dict) or source.stat().st_size != info.get("bytes")
                or digest(source) != info.get("sha256")):
            raise SystemExit(f"Web core hash or size mismatch: {name}")
        verified.append((relative, source))
    return manifest, verified


def overlay_web_core(web_root, files):
    web_root = web_root.resolve(strict=True)
    for relative, source in files:
        destination = web_root.joinpath(*relative.parts)
        if not destination.resolve().is_relative_to(web_root):
            raise SystemExit(f"Web core destination leaves the App: {relative}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path,
                        help="New directory; must not exist")
    parser.add_argument("--font-patches", type=pathlib.Path, default=ROOT / "assets/official-fonts")
    parser.add_argument("--web-core", type=pathlib.Path, default=ROOT / "assets/latest-web-core",
                        help="Official web core directory with a verified core-manifest.json")
    args = parser.parse_args()
    archive = args.archive.resolve(strict=True)
    for name in WRAPPER_FILES:
        if not (ROOT / "mac" / name).is_file():
            raise SystemExit(f"Missing required wrapper source: {name}")
    core_manifest, core_files = verified_web_core(args.web_core)
    font_manifest = json.loads((args.font_patches / "font-patch.json").read_text())
    for name, info in font_manifest["fonts"].items():
        if pathlib.Path(name).name != name or digest(args.font_patches / name) != info["sha256"]:
            raise SystemExit("Font patch hash mismatch")
    if digest(archive) != ARCHIVE_SHA256:
        raise SystemExit("Archive SHA-256 does not match the pinned upstream release")
    if args.output.exists():
        raise SystemExit("Output already exists; choose a new directory")
    # ditto preserves the relative framework symlinks in the macOS bundle.
    with zipfile.ZipFile(archive) as bundle:
        for item in bundle.infolist():
            path = pathlib.PurePosixPath(item.filename)
            if path.is_absolute() or ".." in path.parts:
                raise SystemExit("Unsafe ZIP member")
    args.output.mkdir(parents=True)
    subprocess.run(["ditto", "-x", "-k", str(archive), str(args.output)], check=True)
    app = args.output / "Azeroth Survivors.app"
    resources = app / "Contents/Resources"
    wrapper = resources / "app"
    if not (wrapper / "main.js").is_file() or not (resources / "www/index.html").is_file():
        raise SystemExit("Unexpected upstream bundle layout")
    original = wrapper / "main.js"
    if digest(original) != ORIGINAL_WRAPPER_SHA256:
        raise SystemExit("Unexpected upstream wrapper content")
    # Keep the original wrapper for local provenance outside the resulting app.
    shutil.copy2(original, args.output / "upstream-main.js")
    for name in WRAPPER_FILES:
        source = ROOT / "mac" / name
        if source.exists():
            shutil.copy2(source, wrapper / name)
    # Update the official JS, WASM, indexes and changed/new data as one verified snapshot.
    # Apply CJK fonts afterwards: the official asset index omits their standalone names.
    overlay_web_core(resources / "www", core_files)
    info_path = app / "Contents/Info.plist"
    info = plistlib.loads(info_path.read_bytes())
    info["CFBundleShortVersionString"] = core_manifest["game_version"]
    # Keep this app opted out of macOS Game Mode across future rebuilds.
    info["LSSupportsGameMode"] = False
    info_path.write_bytes(plistlib.dumps(info))
    for name in font_manifest["fonts"]:
        shutil.copy2(args.font_patches / name, resources / "www/data/fonts" / name)
    index_path = resources / "www/data/__index"
    asset_names = json.loads(index_path.read_text())
    known_names = {name.lower() for name in asset_names}
    for name in font_manifest.get("index_names", []):
        if name.lower() not in known_names:
            asset_names.append(name)
    index_path.write_text(json.dumps(asset_names, ensure_ascii=False, separators=(",", ":")))
    shutil.copy2(args.font_patches / "font-patch.json", resources / "font-patch.json")
    shutil.copy2(args.web_core / "core-manifest.json", resources / "web-core-manifest.json")
    shutil.copy2(ROOT / "assets/font-source/OFL.txt", resources / "NotoSansSC-OFL.txt")
    subprocess.run(["node", "--check", str(wrapper / "main.js")], check=True)
    # The runtime keeps its upstream ad-hoc signature; renew the outer resource seal.
    subprocess.run(["codesign", "--force", "--sign", "-",
                    "--preserve-metadata=entitlements,requirements,flags,runtime", str(app)], check=True)
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app)], check=True)
    manifest = {
        "game_version": core_manifest["game_version"], "game_build": core_manifest["game_build"],
        "web_stamp": core_manifest["stamp"],
        "web_core": core_manifest,
        "base_game_version": "0.120.5", "base_game_build": "e0e2410c",
        "windows_archive_sha256": "6cf1108db4e8bd7f55e214e24e976a6f24ab657a3eed86c16743ff76e6b85671",
        "windows_embedded_version_string": "0.102.3", "windows_embedded_build_string": "f78e6fab",
        "upstream": "https://github.com/myslithell/azeroth-survivors/releases/tag/v0.120.5",
        "upstream_archive_sha256": ARCHIVE_SHA256,
        "original_wrapper_sha256": digest(args.output / "upstream-main.js"),
        "local_wrapper_files": {name: digest(wrapper / name) for name in
                                WRAPPER_FILES},
        "app": str(app.resolve()),
        "font_patch": font_manifest,
    }
    (args.output / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(app.resolve())


if __name__ == "__main__":
    main()
