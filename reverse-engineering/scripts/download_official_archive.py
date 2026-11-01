#!/usr/bin/env python3
"""Resume the official Windows RAR using authenticated HTTP range receipts.

Only HTTPS at the supplied official origin is used. No executable is run.
The output directory must be on the external 4T volume. Completed range files
and their receipts let a later invocation continue without fetching them again.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
import subprocess
import threading
import time
from urllib.parse import urlsplit


URL = "https://wow.aethus.pl/download/AzerothSurvivorsWindowsNew.rar"
ETAG = '"6ad660ef-2cff2e88"'
SIZE = 754921096
CHUNK = 4 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def parse_headers(path: Path) -> tuple[int, dict[str, str]]:
    blocks = re.split(r"\r?\n\r?\n", path.read_text(errors="replace"))
    blocks = [block for block in blocks if block.startswith("HTTP/")]
    if not blocks:
        raise ValueError("Missing HTTP response headers")
    lines = blocks[-1].splitlines()
    return int(lines[0].split()[1]), {
        key.strip().lower(): value.strip()
        for line in lines[1:] if ":" in line
        for key, value in [line.split(":", 1)]
    }


class Downloader:
    def __init__(self, directory: Path, workers: int):
        self.directory = directory
        self.parts = directory / "rar-ranges"
        self.parts.mkdir(exist_ok=True)
        self.lock = threading.Lock()
        self.serial = threading.Lock()
        self.rate_limited = threading.Event()
        self.stopped = threading.Event()
        self.backoff_until = 0.0
        self.workers = workers
        self.started = time.time()

    def path(self, index: int, suffix: str) -> Path:
        return self.parts / f"{index:04d}{suffix}"

    def log(self, **event: object) -> None:
        event["at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with self.lock:
            with (self.directory / "rar-range-events.jsonl").open("a") as stream:
                stream.write(json.dumps(event) + "\n")
            print(json.dumps(event), flush=True)

    def valid_part(self, index: int) -> bool:
        path = self.path(index, ".bin")
        receipt = self.path(index, ".json")
        if not path.exists() or not receipt.exists():
            return False
        data = json.loads(receipt.read_text())
        start = index * CHUNK
        length = min(CHUNK, SIZE - start)
        return (
            data.get("url") == URL and data.get("etag") == ETAG
            and data.get("start") == start and data.get("length") == length
            and path.stat().st_size == length and data.get("sha256") == sha256(path)
        )

    def seed(self, prefix: Path | None) -> None:
        if prefix is None:
            return
        probe = self.directory / "rar-range-probe.bin"
        probe_status, probe_headers = parse_headers(self.directory / "rar-range-probe.headers.txt")
        if (
            probe_status != 206 or probe_headers.get("etag") != ETAG
            or probe_headers.get("content-range") != f"bytes 0-1023/{SIZE}"
            or int(probe_headers.get("content-length", "-1")) != 1024
            or probe.stat().st_size != 1024
        ):
            raise ValueError("Independent prefix probe does not match pinned archive")
        original_headers = self.directory / "windows-download.headers.txt"
        status, headers = parse_headers(original_headers)
        if status != 200 or headers.get("etag") != ETAG or int(headers["content-length"]) != SIZE:
            raise ValueError("Original prefix headers do not match pinned archive")
        with prefix.open("rb") as source:
            if source.read(1024) != probe.read_bytes():
                raise ValueError("Existing prefix differs from the independent range probe")
        prefix_length = prefix.stat().st_size
        with prefix.open("rb") as source:
            for index in range((prefix_length + CHUNK - 1) // CHUNK):
                block = source.read(CHUNK)
                if self.valid_part(index):
                    continue
                partial = self.path(index, ".partial")
                if partial.exists():
                    continue
                partial.write_bytes(block)
                seed = {
                    "url": URL, "etag": ETAG, "start": index * CHUNK,
                    "length": len(block), "sha256": hashlib.sha256(block).hexdigest(),
                    "source": str(prefix), "source_headers": str(original_headers),
                    "prefix_probe_match_bytes": 1024,
                    "provenance": "Bytes inherited from interrupted official HTTP 200 response",
                }
                write_json(self.path(index, ".partial.json"), seed)
                if len(block) == min(CHUNK, SIZE - index * CHUNK):
                    partial.replace(self.path(index, ".bin"))
                    write_json(self.path(index, ".json"), seed)

    def fetch(self, index: int) -> dict[str, object]:
        if self.stopped.is_set():
            raise RuntimeError("Download stopped after a failed range")
        if self.valid_part(index):
            return {"index": index, "cached": True}
        start = index * CHUNK
        end = min(start + CHUNK, SIZE) - 1
        partial = self.path(index, ".partial")
        segments: list[dict[str, object]] = []
        if partial.exists():
            seed = json.loads(self.path(index, ".partial.json").read_text())
            if (
                seed.get("url") != URL or seed.get("etag") != ETAG
                or seed["start"] != start or seed["length"] != partial.stat().st_size
                or seed["sha256"] != sha256(partial)
            ):
                raise ValueError(f"Untrusted partial range {index}")
            segments.append(seed)
        offset = partial.stat().st_size if partial.exists() else 0
        for attempt in range(1, 13):
            if self.stopped.is_set():
                raise RuntimeError("Download stopped after a failed range")
            requested_start = start + offset
            expected_length = end - requested_start + 1
            if expected_length == 0:
                break
            # A 429 permanently lowers subsequent requests to one at a time.
            gate = self.serial if self.rate_limited.is_set() else None
            if gate:
                gate.acquire()
            try:
                delay = self.backoff_until - time.time()
                if delay > 0:
                    time.sleep(delay)
                body = self.path(index, f".attempt-{attempt}.incoming")
                header = self.path(index, f".attempt-{attempt}.headers")
                error = self.path(index, f".attempt-{attempt}.stderr")
                command = [
                    "curl", "--http1.1", "--proto", "=https", "--tlsv1.2",
                    "--silent", "--show-error", "--connect-timeout", "20",
                    "--max-time", "480", "--speed-limit", "256", "--speed-time", "90",
                    "--header", f"If-Match: {ETAG}",
                    "--header", "Accept-Encoding: identity",
                    "--range", f"{requested_start}-{end}",
                    "--dump-header", str(header), "--output", str(body), URL,
                ]
                self.log(event="range_started", index=index, attempt=attempt,
                         start=requested_start, end=end)
                with error.open("wb") as stderr:
                    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=stderr)
                try:
                    status, headers = parse_headers(header)
                except ValueError:
                    status, headers = 0, {}
                received = body.stat().st_size if body.exists() else 0
                if status == 429:
                    self.rate_limited.set()
                    retry = headers.get("retry-after", "60")
                    seconds = max(60, int(retry) if retry.isdigit() else 60)
                    with self.lock:
                        self.backoff_until = max(self.backoff_until, time.time() + seconds)
                    self.log(event="rate_limited", index=index, retry_seconds=seconds)
                    continue
                expected_range = f"bytes {requested_start}-{end}/{SIZE}"
                valid = (
                    result.returncode == 0 and status == 206
                    and headers.get("etag") == ETAG
                    and headers.get("content-range") == expected_range
                    and int(headers.get("content-length", "-1")) == expected_length
                    and received == expected_length
                )
                if not valid:
                    self.log(event="range_rejected", index=index, attempt=attempt,
                             curl_exit=result.returncode, status=status, received=received,
                             headers=headers, stderr=error.read_text(errors="replace")[-1000:])
                    if status in (200, 412) or headers.get("etag", ETAG) != ETAG:
                        raise ValueError("Pinned archive changed or server ignored Range")
                    time.sleep(min(2 ** attempt, 30))
                    continue
                with partial.open("ab") as destination, body.open("rb") as source:
                    for block in iter(lambda: source.read(1024 * 1024), b""):
                        destination.write(block)
                segments.append({
                    "start": requested_start, "length": received,
                    "sha256": sha256(body), "headers": str(header),
                    "status": status, "curl_exit": result.returncode,
                })
                body.unlink()
                offset += received
                break
            finally:
                if gate:
                    gate.release()
        if offset != end - start + 1:
            raise RuntimeError(f"Range {index} exhausted retries")
        completed = self.path(index, ".bin")
        partial.replace(completed)
        receipt = {
            "url": URL, "etag": ETAG, "start": start, "length": offset,
            "sha256": sha256(completed), "segments": segments,
        }
        write_json(self.path(index, ".json"), receipt)
        self.log(event="range_complete", index=index, bytes=offset)
        return {"index": index, "cached": False}

    def run(self, prefix: Path | None) -> None:
        self.seed(prefix)
        count = (SIZE + CHUNK - 1) // CHUNK
        futures = []
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.workers)
        try:
            for index in range(count):
                futures.append(pool.submit(self.fetch, index))
            for future in concurrent.futures.as_completed(futures):
                future.result()
        except BaseException:
            self.stopped.set()
            for future in futures:
                future.cancel()
            raise
        finally:
            pool.shutdown(wait=True, cancel_futures=True)
        target = self.directory / "AzerothSurvivorsWindowsNew.rar"
        temporary = target.with_suffix(".rar.assembling")
        with temporary.open("wb") as destination:
            for index in range(count):
                if not self.valid_part(index):
                    raise ValueError(f"Range {index} failed assembly revalidation")
                with self.path(index, ".bin").open("rb") as source:
                    for block in iter(lambda: source.read(1024 * 1024), b""):
                        destination.write(block)
        if temporary.stat().st_size != SIZE:
            raise ValueError("Assembled size differs from pinned official Content-Length")
        temporary.replace(target)
        receipt = {
            "url": URL, "etag": ETAG, "bytes": SIZE, "sha256": sha256(target),
            "last_modified": "Mon, 19 Oct 2026 18:26:55 GMT",
            "range_bytes": CHUNK, "range_count": count, "archive": str(target),
            "elapsed_seconds": round(time.time() - self.started, 3),
            "complete": True,
            "sha256_origin": "Locally computed; no official full-RAR SHA was advertised",
        }
        write_json(self.directory / "rar-download-receipt.json", receipt)
        self.log(event="archive_complete", **receipt)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--prefix", type=Path)
    parser.add_argument("--workers", type=int, default=4, choices=range(1, 5))
    args = parser.parse_args()
    directory = args.output_dir.resolve()
    if not str(directory).startswith("/Volumes/RuiRui4TB/"):
        parser.error("All download output must remain on /Volumes/RuiRui4TB")
    directory.mkdir(parents=True, exist_ok=True)
    if urlsplit(URL).hostname != "wow.aethus.pl":
        raise ValueError("Unexpected origin")
    Downloader(directory, args.workers).run(args.prefix.resolve() if args.prefix else None)


if __name__ == "__main__":
    main()
