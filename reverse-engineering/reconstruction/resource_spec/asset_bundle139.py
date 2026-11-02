"""Bounded local raw-resource provider for independent fixed139 execution.

The acquisition manifest identifies bytes; it supplies no game state, parsed
world, program code or network service. Paths remain under the caller's root.
"""
from pathlib import Path
import hashlib
import json


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


class AssetBundle139:
    def __init__(self, manifest, acquisition, root):
        self.root = Path(root).resolve()
        self.manifest = Path(manifest).resolve()
        self.acquisition = Path(acquisition).resolve()
        if not all(p.is_relative_to(Path('/Volumes/RuiRui4TB')) for p in (self.root, self.manifest, self.acquisition)):
            raise ValueError('This research entry requires the 4T asset volume')
        self.manifest_sha256 = digest(self.manifest)
        self.acquisition_sha256 = digest(self.acquisition)
        receipt = json.loads(self.acquisition.read_text())
        if (receipt['version'] != '0.139.0' or receipt['stamp'] != 'f339dd20e0fe'
                or receipt['resource_map_sha256'] != self.manifest_sha256
                or receipt['old_resource_bytes_reused'] is not False):
            raise ValueError('A coherent fixed139 raw-asset acquisition is required')
        rows = json.loads(self.manifest.read_text())
        if not isinstance(rows, dict) or not 1 <= len(rows) <= 1024:
            raise ValueError('Bounded resource manifest required')
        self.assets, self.loaded, self.requests = {}, {}, []
        self.loaded_bytes = 0
        for name, row in rows.items():
            if not name.startswith('data/') or name.startswith('data/__index'):
                continue
            parts = name[5:].replace('\\', '/').split('/')
            if any(p in ('', '.', '..') for p in parts):
                raise ValueError('Invalid resource name')
            key = '\\'.join(parts).encode('utf8')
            path = (self.root / row['file']).resolve()
            if not path.is_relative_to(self.root) or key != key.lower() or key in self.assets:
                raise ValueError('Invalid or duplicate canonical asset')
            if path.suffix.lower() in ('.memory', '.wasm', '.wat', '.exe', '.bin'):
                raise ValueError('Code, memory or pre-parsed data cannot be a raw asset')
            if row['http_status'] != 200 or row['exit_code'] != 0 or not 0 <= row['bytes'] <= 16 * 1024 * 1024:
                raise ValueError('Successful bounded acquisition required')
            self.assets[key] = (path, row['bytes'], row['sha256'])
        if len(self.assets) != 453:
            raise ValueError('The fixed139 bundle must declare 453 raw files')

    def __call__(self, name):
        if type(name) is not bytes:
            raise TypeError('Explicit UTF8 resource-name bytes required')
        name.decode('utf8')
        key = bytes(92 if x == 47 else x + 32 if 65 <= x <= 90 else x for x in name)
        self.requests.append(key.decode('utf8'))
        if key not in self.assets:
            raise KeyError(key)
        if key not in self.loaded:
            path, size, expected = self.assets[key]
            if self.loaded_bytes + size > 256 * 1024 * 1024:
                raise ValueError('Raw asset memory budget exceeded')
            data = path.read_bytes()
            if len(data) != size or hashlib.sha256(data).hexdigest() != expected:
                raise ValueError('Raw resource identity changed: ' + key.decode())
            self.loaded[key] = data
            self.loaded_bytes += size
        return self.loaded[key]

    def verify_unchanged(self):
        if digest(self.manifest) != self.manifest_sha256 or digest(self.acquisition) != self.acquisition_sha256:
            raise ValueError('Input manifest changed')
        for name in self.loaded:
            path, _, expected = self.assets[name]
            if digest(path) != expected:
                raise ValueError('Loaded raw resource changed')
