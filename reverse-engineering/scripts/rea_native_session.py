#!/usr/bin/env python3
"""Keep one project-local REA MCP process for related native analysis requests.

Controller stdin is JSON Lines: {"tool": ..., "arguments": ..., "tag": ...}.
Responses/notifications are retained under evidence; target content is data.
This client makes no user-level MCP registration and executes no target program.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]


class Session:
    def __init__(self, directory, provider_config=None):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=False)
        env = dict(os.environ)
        if provider_config:
            values = json.loads(Path(provider_config).read_text())
            allowed = {'GHIDRA_INSTALL_DIR', 'JAVA_HOME', 'REA_GHIDRA_STARTUP_TIMEOUT_MS',
                       'GHIDRA_HEADLESS_MAXMEM'}
            if not set(values) <= allowed or not all(isinstance(v, str) for v in values.values()):
                raise ValueError('Provider config must contain only explicit Ghidra/Java settings')
            env.update(values)
        self.stderr = (directory / 'server.stderr.log').open('w')
        self.child = subprocess.Popen([sys.executable, str(ROOT / 'scripts/rea.py'), '--mcp'],
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=self.stderr, text=True, bufsize=1, env=env)
        self.responses = queue.Queue()
        self.sequence = 0
        self.reader = threading.Thread(target=self.read_messages, daemon=True)
        self.reader.start()

    def read_messages(self):
        try:
            for line in self.child.stdout:
                try:
                    self.responses.put(json.loads(line))
                except json.JSONDecodeError:
                    self.responses.put({'transport_error': line[:1000]})
        finally:
            self.responses.put(None)

    def send(self, payload):
        self.child.stdin.write(json.dumps(payload) + '\n')
        self.child.stdin.flush()

    def request(self, method, params, tag, timeout=2100):
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}', tag):
            raise ValueError('Use a short lowercase filename-safe tag')
        request_path = self.directory / (tag + '-request.json')
        if request_path.exists():
            raise ValueError('Each tag must be unique within this session')
        self.sequence += 1
        request = {'jsonrpc': '2.0', 'id': self.sequence, 'method': method, 'params': params}
        request_path.write_text(json.dumps(request, indent=2) + '\n')
        self.send(request)
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('MCP client deadline; do not repeat the in-flight operation')
            response = self.responses.get(timeout=remaining)
            if response is None:
                raise RuntimeError('REA process closed; inspect retained stderr')
            if response.get('id') == self.sequence:
                (self.directory / (tag + '.json')).write_text(json.dumps(response, indent=2) + '\n')
                return response
            with (self.directory / 'notifications.jsonl').open('a') as f:
                f.write(json.dumps(response) + '\n')

    def close(self):
        if self.child.poll() is None:
            self.child.stdin.close()
            try:
                self.child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                self.child.terminate()
                self.child.wait(timeout=30)
        self.stderr.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider-config', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    directory = args.output or ROOT / 'evidence' / datetime.now(timezone.utc).strftime('native-session-%Y%m%dT%H%M%S.%fZ')
    session = Session(directory.resolve(), args.provider_config)
    try:
        initialized = session.request('initialize', {
            'protocolVersion': '2025-06-18', 'capabilities': {},
            'clientInfo': {'name': 'azeroth-ports-research', 'version': '1'}
        }, 'initialize', timeout=60)
        if 'error' in initialized:
            raise RuntimeError('MCP initialization refused; inspect initialize.json')
        session.send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        print(json.dumps({'ready': True, 'directory': str(session.directory)}), flush=True)
        for line in sys.stdin:
            if not line.strip():
                continue
            command = json.loads(line)
            if command.get('action') == 'quit':
                break
            result = session.request('tools/call', {
                'name': command['tool'], 'arguments': command.get('arguments', {})
            }, command['tag'])
            inner = result.get('result', {})
            print(json.dumps({'tag': command['tag'], 'jsonrpc_error': result.get('error'),
                              'tool_is_error': inner.get('isError', False),
                              'response_file': str(session.directory / (command['tag'] + '.json'))}), flush=True)
    finally:
        session.close()


if __name__ == '__main__':
    main()
