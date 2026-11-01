#!/usr/bin/env python3
"""Archive an official release without executing it or replacing fixed inputs.

Every HTTP request is bounded to 60 seconds. Re-running with --directory uses
the archived release manifest; only already complete, recorded downloads are
reused. Original binaries and request receipts stay in ignored originals/.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://wow.aethus.pl/"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def official_url(relative: str, base: str = ORIGIN) -> str:
    url = urljoin(base, relative)
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "wow.aethus.pl":
        raise ValueError(f"Non-official HTTPS URL refused: {url}")
    return url


def download(directory: Path, filename: str, url: str, *,
             expected_bytes: int | None = None, max_bytes: int = 150_000_000) -> dict:
    official_url(url)
    target = directory / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    receipt = target.with_name(target.name + ".http.json")
    if target.exists() and receipt.exists():
        previous = json.loads(receipt.read_text())
        if (previous["url"] == url and previous["bytes"] == target.stat().st_size
                and previous["sha256"] == digest(target)
                and (expected_bytes is None or expected_bytes == target.stat().st_size)):
            return previous
        raise ValueError(f"Existing download failed recorded identity: {target}")
    if target.exists():
        raise ValueError(f"Unrecorded existing output refused: {target}")
    partial = target.with_name(target.name + ".part")
    headers = target.with_name(target.name + ".headers.txt")
    command = ["curl", "--fail", "--silent", "--show-error", "--location",
               "--proto", "=https", "--proto-redir", "=https", "--connect-timeout", "15",
               "--max-time", "60", "--max-filesize", str(max_bytes),
               "--dump-header", str(headers), "--output", str(partial),
               "--write-out", "%{http_code}\n%{url_effective}\n", url]
    result = subprocess.run(command, capture_output=True, text=True, timeout=65)
    write_json(target.with_name(target.name + ".attempt.json"), {
        "at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "url": url,
        "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
    })
    if result.returncode:
        raise RuntimeError(f"curl failed for {filename}: {result.stderr.strip()}")
    status, effective = result.stdout.strip().splitlines()[-2:]
    official_url(effective)
    if status != "200":
        raise ValueError(f"Expected full HTTP200 response, got {status}")
    size = partial.stat().st_size
    if size > max_bytes or (expected_bytes is not None and size != expected_bytes):
        raise ValueError(f"Unexpected size for {filename}: {size}")
    partial.rename(target)
    record = {"url": url, "effective_url": effective, "status": 200,
              "bytes": size, "sha256": digest(target), "filename": filename,
              "headers_sha256": digest(headers)}
    write_json(receipt, record)
    print(json.dumps({"downloaded": filename, "bytes": size}, ensure_ascii=False), flush=True)
    return record


def acquire_windows(directory: Path) -> dict:
    manifest_record = download(directory, "windows-latest.json", ORIGIN + "exe/latest.json",
                               max_bytes=100_000)
    manifest = json.loads((directory / "windows-latest.json").read_text())
    version = manifest["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Invalid version")
    if not re.fullmatch(r"[0-9a-f]{64}", manifest["sha256"]):
        raise ValueError("Invalid publisher SHA256")
    expected_size = manifest["size"]
    if not isinstance(expected_size, int) or not 0 < expected_size <= 250_000_000:
        raise ValueError("Unreasonable EXE size")
    parts = []
    if not 1 <= len(manifest["parts"]) <= 16:
        raise ValueError("Unreasonable part count")
    for i, part in enumerate(manifest["parts"]):
        if not isinstance(part["size"], int) or not 0 < part["size"] <= 25_000_000:
            raise ValueError("Unreasonable part size")
        parts.append(download(directory, f"windows-update-parts/part-{i:03}.bin",
                              official_url(part["url"], ORIGIN + "exe/"),
                              expected_bytes=part["size"], max_bytes=25_000_000))
    compressed = directory / f"AzerothSurvivors-{version}.exe.gz"
    with compressed.open("wb") as output:
        for part in parts:
            with (directory / part["filename"]).open("rb") as source:
                shutil.copyfileobj(source, output)
    output_directory = directory / f"windows-{version}"
    output_directory.mkdir(exist_ok=True)
    target = output_directory / "AzerothSurvivors.exe"
    partial = target.with_suffix(".exe.part")
    # Read to gzip EOF, which verifies CRC and ISIZE, and enforce advertised size.
    count = 0
    with gzip.open(compressed, "rb") as source, partial.open("wb") as output:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            count += len(block)
            if count > expected_size:
                raise ValueError("EXE exceeds official size")
            output.write(block)
    actual_sha = digest(partial)
    if count != expected_size or actual_sha != manifest["sha256"]:
        raise ValueError("EXE fails official size/SHA256")
    partial.replace(target)
    result = {"version": version, "notes": manifest.get("notes"),
              "manifest": manifest_record, "parts": parts,
              "compressed_bytes": compressed.stat().st_size,
              "compressed_sha256": digest(compressed), "gzip_crc_isize_passed": True,
              "exe_relative_path": str(target.relative_to(directory)),
              "exe_bytes": count, "exe_sha256": actual_sha,
              "official_identity_matched": True, "target_executed": False}
    write_json(directory / "windows-acquisition.json", result)
    return result


def acquire_web(directory: Path) -> dict:
    index = download(directory, "official-index.html", ORIGIN, max_bytes=5_000_000)
    html = (directory / "official-index.html").read_text()
    match = re.search(r'''(?:src|href)=["']([^"']*rogue\.js\?v=([^"'&]+))''', html)
    if not match:
        raise ValueError("Could not identify stamped rogue.js in official HTML")
    stamp = match.group(2)
    if not re.fullmatch(r"[0-9a-zA-Z_-]{1,80}", stamp):
        raise ValueError("Invalid cache stamp")
    scripts = {}
    for name in ("rogue.js", "boot.js", "wenilla.js"):
        scripts[name] = download(directory, "official-" + name,
                                 official_url(name + "?v=" + stamp), max_bytes=10_000_000)
    wasm = download(directory, "latest-wenilla_bg.wasm",
                    official_url("wenilla_bg.wasm?v=" + stamp), max_bytes=120_000_000)
    binary = (directory / "latest-wenilla_bg.wasm").read_bytes()
    if not binary.startswith(b"\x00asm\x01\x00\x00\x00"):
        raise ValueError("Downloaded file is not WASM version1")
    # Static printable context only; it is not an instantiated/executed module.
    branding = []
    for found in re.finditer(rb"0\.\d+\.\d+", binary):
        start = max(0, found.start() - 100)
        end = min(len(binary), found.end() + 160)
        branding.append({"offset": found.start(), "version": found.group().decode(),
                         "context_latin1": binary[start:end].decode("latin1")})
    menu_signatures = []
    for found in re.finditer(rb"Made by Aethus.{0,140}?([0-9a-f]{8})(0\.\d+\.\d+)",
                             binary, re.DOTALL):
        menu_signatures.append({"offset": found.start(), "build": found.group(1).decode(),
                                "version": found.group(2).decode()})
    if len(menu_signatures) != 1:
        raise ValueError(f"Expected one Aethus menu branding signature, got {len(menu_signatures)}")
    # Recheck index after the large WASM download to detect a deployment race.
    ending_index = download(directory, "official-index-after.html", ORIGIN, max_bytes=5_000_000)
    ending_html = (directory / "official-index-after.html").read_text()
    ending_match = re.search(r'''(?:src|href)=["']([^"']*rogue\.js\?v=([^"'&]+))''', ending_html)
    ending_stamp = ending_match.group(2) if ending_match else None
    result = {"stamp": stamp, "stamp_after": ending_stamp,
              "page_stamp_stable_during_acquisition": stamp == ending_stamp,
              "index": index, "index_after": ending_index, "scripts": scripts,
              "wasm": wasm, "branding_candidates": branding,
              "menu_branding": menu_signatures[0],
              "official_independent_wasm_digest_published": False,
              "sha256_origin": "Computed locally from saved HTTPS bytes",
              "application_start_called": False, "module_instantiated": False}
    write_json(directory / "web-acquisition.json", result)
    if stamp != ending_stamp:
        raise ValueError("Official deployment changed during acquisition; keep snapshot but do not identify it as coherent")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--stage", choices=("windows", "web", "all"), default="all")
    options = parser.parse_args()
    directory = options.directory or (ROOT / "originals" / (
        "official-acquisition-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")))
    directory = directory.resolve()
    if not directory.is_relative_to((ROOT / "originals").resolve()):
        raise ValueError("Outputs must remain inside this project's ignored originals directory")
    directory.mkdir(parents=True, exist_ok=True)
    print(json.dumps({"directory": str(directory), "stage": options.stage}), flush=True)
    if options.stage in ("windows", "all"):
        acquire_windows(directory)
    if options.stage in ("web", "all"):
        acquire_web(directory)


if __name__ == "__main__":
    main()
