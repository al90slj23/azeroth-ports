"""Read-only, bounded, lossless decoder for original capture CAS v1.

Float tokens keep their exact JavaScript JSON spelling until the logical line
SHA is checked. Production models never import this evidence-only module.
"""
from collections import Counter, OrderedDict
from pathlib import Path
import hashlib
import json
import re

MARKER = '$cas135_blob_v1'
PROTOCOL = 'opening-combat135-cas-v1'
SHA = re.compile(r'[0-9a-f]{64}\Z')
SURROGATE = re.compile(r'[\ud800-\udfff]')
# The admitted one-case controller emits four boundary records, fourteen
# stages per frame, and one record per action (clock or selection). With at
# most750 frames/800 actions this is11304 records, indices0..11303. This does
# not relax the independent byte/blob/depth/occurrence budgets.
CAPTURE_RECORD_LIMIT = 4 + 14 * 750 + 800
FRAGMENT_CACHE_WEIGHT_LIMIT = 16 * 1024 * 1024
FRAGMENT_CACHE_ITEM_LIMIT = 1024 * 1024


class CaptureCAS135Error(ValueError):
    pass


class _FloatToken(str):
    """JSON numeric lexeme, not a string in the reconstructed document."""


def _require(value, label):
    if not value:
        raise CaptureCAS135Error(label)


def _uint(value, maximum, label):
    _require(type(value) is int and 0 <= value <= maximum, label)
    return value


def _loads(raw):
    def no_constant(value):
        raise CaptureCAS135Error('Nonfinite JSON literal: ' + value)
    def pairs(rows):
        result={}
        for key,value in rows:
            _require(key not in result,'Duplicate CAS JSON key')
            result[key]=value
        return result
    return json.loads(raw, parse_float=_FloatToken, parse_constant=no_constant,object_pairs_hook=pairs)


def _string(value):
    _require(SURROGATE.search(value) is None, 'Unpaired UTF16 in CAS string')
    return json.encoder.encode_basestring(value)


def _json(value):
    if isinstance(value, _FloatToken):
        return str(value)
    if value is None:
        return 'null'
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    if type(value) is int:
        return str(value)
    if type(value) is str:
        return _string(value)
    if type(value) is list:
        return '[' + ','.join(_json(v) for v in value) + ']'
    if type(value) is dict:
        return '{' + ','.join(_string(k) + ':' + _json(v) for k, v in value.items()) + '}'
    raise CaptureCAS135Error('Unsupported decoded CAS value')


class CaptureCAS135:
    """One completed experiment's DAG, with bounded encoded-node LRU cache."""

    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.blob_directory=self.directory/'cas-blobs'
        _require(self.directory.is_dir()and not self.blob_directory.is_symlink()
                 and self.blob_directory.is_dir()
                 and self.blob_directory.resolve().is_relative_to(self.directory),'CAS blob directory escaped experiment')
        self.entries = {}
        self.entry_order = {}
        self.declared_refs = {}
        self.cache = OrderedDict()
        self.cache_bytes = 0
        self.fragments = OrderedDict()
        self.fragment_cache_weight = 0
        self.record_index = 0
        self.logical_bytes = 0
        self.logical_hash = hashlib.sha256()
        self.actual_refs = Counter()
        self.first_seen = {}
        self.last_seen = {}
        self.max_record = 0
        self.stream_hash=hashlib.sha256()
        self.stream_bytes=0
        self.max_stream_record=0
        self.max_blob_index_record=0
        self.unique_bytes = 0
        self.index_hash = hashlib.sha256()
        self.index_bytes = 0
        self.refs_hash = hashlib.sha256()
        self.refs_bytes = 0
        path = self.directory / 'blob-index.jsonl'
        _require(not path.is_symlink()and path.resolve().parent==self.directory,'CAS blob index escaped experiment')
        _require(path.stat().st_size <= 256 * 1024 * 1024, 'CAS blob index256MiB budget')
        with path.open('rb') as stream:
            for raw in stream:
                _require(len(raw) <= 2 * 1024 * 1024 and raw.endswith(b'\n'), 'CAS index record budget')
                self.index_hash.update(raw)
                self.index_bytes += len(raw)
                self.max_blob_index_record=max(self.max_blob_index_record,len(raw))
                row = json.loads(raw)
                _require(set(row) == {'sha256', 'bytes', 'file', 'first_record_index', 'child_refs'}, 'CAS blob index shape')
                h = row['sha256']
                _require(type(h) is str and SHA.fullmatch(h) and h not in self.entries, 'CAS duplicate/invalid blob SHA')
                n = _uint(row['bytes'], 16 * 1024 * 1024, 'CAS blob16MiB budget')
                _require(n > 0 and row['file'] == 'cas-blobs/' + h + '.json', 'CAS blob path')
                _uint(row['first_record_index'], CAPTURE_RECORD_LIMIT - 1, 'CAS first record index')
                _require(type(row['child_refs']) is list, 'CAS child-reference list')
                seen = set()
                for child in row['child_refs']:
                    _require(set(child) == {'sha256', 'bytes', 'count'}, 'CAS child-reference shape')
                    ch = child['sha256']
                    _require(ch in self.entries and ch not in seen, 'CAS child must precede parent, once')
                    _require(child['bytes'] == self.entries[ch]['bytes'], 'CAS child byte identity')
                    _uint(child['count'], 1048576, 'CAS child occurrence budget')
                    _require(child['count'] > 0, 'CAS positive child count')
                    seen.add(ch)
                self.entry_order[h] = len(self.entries)
                self.entries[h] = row
                self.unique_bytes += n
                _require(len(self.entries) <= 65536 and self.unique_bytes <= 512 * 1024 * 1024, 'CAS unique blob budget')
        path = self.directory / 'blob-references.jsonl'
        _require(not path.is_symlink()and path.resolve().parent==self.directory,'CAS reference metadata escaped experiment')
        _require(path.stat().st_size <= 32 * 1024 * 1024, 'CAS reference metadata32MiB budget')
        with path.open('rb') as stream:
            for raw in stream:
                _require(len(raw) <= 2 * 1024 * 1024 and raw.endswith(b'\n'), 'CAS reference metadata record')
                self.refs_hash.update(raw)
                self.refs_bytes += len(raw)
                row = json.loads(raw)
                _require(set(row) == {'sha256', 'bytes', 'first_record_index', 'last_record_index', 'total_logical_references'}, 'CAS reference metadata shape')
                h = row['sha256']
                _require(h in self.entries and h not in self.declared_refs, 'CAS reference metadata identity')
                _require(row['bytes'] == self.entries[h]['bytes'] and row['first_record_index'] == self.entries[h]['first_record_index'], 'CAS reference metadata mismatch')
                _uint(row['last_record_index'], CAPTURE_RECORD_LIMIT - 1, 'CAS last record index')
                _uint(row['total_logical_references'], 1 << 40, 'CAS logical ref count')
                _require(row['total_logical_references'] > 0, 'CAS positive logical refs')
                self.declared_refs[h] = row
        _require(set(self.entries) == set(self.declared_refs), 'CAS missing reference metadata')
        actual=set()
        for p in self.blob_directory.iterdir():
            _require(p.is_file()and not p.is_symlink(),'CAS nonregular or symlink blob')
            actual.add(p.name)
        _require(actual == {h + '.json' for h in self.entries}, 'CAS missing/unindexed blob files')

    def _encoded(self, h):
        if h in self.cache:
            value, n = self.cache.pop(h)
            self.cache[h] = (value, n)
            return value
        row = self.entries[h]
        path = self.directory / row['file']
        _require(not path.is_symlink()and path.resolve().parent==self.blob_directory.resolve(), 'CAS path escaped blob directory')
        _require(path.stat().st_size == row['bytes'], 'CAS blob size mismatch')
        raw = path.read_bytes()
        _require(hashlib.sha256(raw).hexdigest() == h, 'CAS blob SHA mismatch')
        value = _loads(raw)
        refs = Counter()
        def walk(v, depth=0):
            _require(depth <= 128, 'CAS encoded depth budget')
            if type(v) is dict and MARKER in v:
                _require(set(v) == {MARKER, 'bytes'}, 'CAS reserved reference shape')
                ch = v[MARKER]
                _require(type(ch) is str and ch in self.entries and v['bytes'] == self.entries[ch]['bytes'], 'CAS child identity')
                refs[ch] += 1
            elif type(v) in (dict, list):
                for x in (v.values() if type(v) is dict else v):
                    walk(x, depth + 1)
        walk(value)
        expected = Counter({x['sha256']: x['count'] for x in row['child_refs']})
        _require(refs == expected, 'CAS actual child edges differ from index')
        if len(raw) <= 8 * 1024 * 1024:
            while self.cache and self.cache_bytes + len(raw) > 8 * 1024 * 1024:
                _, (_, n) = self.cache.popitem(last=False)
                self.cache_bytes -= n
            self.cache[h] = (value, len(raw))
            self.cache_bytes += len(raw)
        return value

    def _expand(self, value, active, depth, work):
        work[0] += 1
        #Each logical node can add one transport-reference hop. Such a hop
        #does not increase the original document's nesting depth.
        _require(depth <= 128 and work[0] <= 2097152, 'CAS expanded tree budget')
        if type(value) is dict:
            if MARKER in value:
                _require(set(value) == {MARKER, 'bytes'}, 'CAS reference shape')
                h = value[MARKER]
                _require(type(h) is str and h in self.entries and h not in active, 'CAS unknown/cyclic reference')
                row = self.entries[h]
                _require(type(value['bytes']) is int and value['bytes'] == row['bytes'], 'CAS reference byte mismatch')
                _require(row['first_record_index'] <= self.record_index, 'CAS reference precedes declaration')
                self.actual_refs[h] += 1
                self.first_seen.setdefault(h, self.record_index)
                self.last_seen[h] = self.record_index
                return self._expand(self._encoded(h), active | {h}, depth, work)
            return {k: self._expand(v, active, depth + 1, work) for k, v in value.items()}
        if type(value) is list:
            return [self._expand(v, active, depth + 1, work) for v in value]
        return value

    def _fragment_value(self, value, active):
        """Canonical bytes plus exact transitive references/depth/work.

        Cached bytes preserve every original field and numeric lexeme. The
        reference footprint replaces repeated traversal, not its verification:
        occurrence counts and first/last record bounds are still checked.
        """
        if type(value) is dict and MARKER in value:
            _require(set(value) == {MARKER, 'bytes'}, 'CAS reference shape')
            h = value[MARKER]
            _require(type(h) is str and h in self.entries and h not in active, 'CAS unknown/cyclic reference')
            row = self.entries[h]
            _require(type(value['bytes']) is int and value['bytes'] == row['bytes'], 'CAS reference byte mismatch')
            data, footprint, depth, work = self._fragment_hash(h, active)
            refs = footprint.copy()
            refs[h] += 1
            _require(work + 1 <= 2097152, 'CAS expanded tree budget')
            return data, refs, depth, work + 1
        if type(value) not in (dict, list):
            data = _json(value).encode('utf8')
            _require(len(data) <= 2 * 1024 * 1024, 'CAS logical record budget')
            return data, Counter(), 0, 1
        parts, refs, depth, work, size = [], Counter(), 0, 1, 2
        entries = value.items() if type(value) is dict else ((None, v) for v in value)
        for key, item in entries:
            data, child_refs, child_depth, child_work = self._fragment_value(item, active)
            prefix = (_string(key).encode('utf8') + b':') if key is not None else b''
            size += len(prefix) + len(data) + bool(parts)
            depth = max(depth, child_depth + 1)
            work += child_work
            _require(depth <= 128 and work <= 2097152, 'CAS expanded tree budget')
            _require(size <= 2 * 1024 * 1024, 'CAS logical record budget')
            refs.update(child_refs)
            parts.append(prefix + data)
        if type(value) is dict:
            data = b'{' + b','.join(parts) + b'}'
        else:
            data = b'[' + b','.join(parts) + b']'
        return data, refs, depth, work

    def _fragment_hash(self, h, active):
        if h in self.fragments:
            fragment, weight = self.fragments.pop(h)
            self.fragments[h] = (fragment, weight)
            return fragment
        # _encoded checks file size/SHA, reserved shapes, exact direct edges
        # and encoded depth, even if a logical fragment is not cacheable.
        fragment = self._fragment_value(self._encoded(h), active | {h})
        data, refs, _, _ = fragment
        # Avoid filling the cache with unique whole-record roots. Weight also
        # accounts conservatively for the reference-map entries; this is a
        # cache accounting bound, not a claim about total Python RSS.
        weight = len(data) + 160 * len(refs) + 512
        if len(data) <= FRAGMENT_CACHE_ITEM_LIMIT and weight <= FRAGMENT_CACHE_WEIGHT_LIMIT:
            while self.fragments and self.fragment_cache_weight + weight > FRAGMENT_CACHE_WEIGHT_LIMIT:
                _, (_, old_weight) = self.fragments.popitem(last=False)
                self.fragment_cache_weight -= old_weight
            self.fragments[h] = (fragment, weight)
            self.fragment_cache_weight += weight
        return fragment

    def decode_line(self, raw):
        _require(self.record_index < CAPTURE_RECORD_LIMIT, 'CAS capture record count budget')
        _require(len(raw) <= 2 * 1024 * 1024 and raw.endswith(b'\n'), 'CAS stream record budget')
        row = _loads(raw)
        _require(set(row) == {'cas_protocol', 'record_index', 'record_kind', 'id', 'logical_bytes', 'logical_sha256', 'capture'}, 'CAS envelope shape')
        _require(row['cas_protocol'] == PROTOCOL and type(row['record_index']) is int and row['record_index'] == self.record_index, 'CAS envelope order/protocol')
        _require(type(row['record_kind'])is str,'CAS record_kind must be a string')
        _uint(row['id'],(1<<53)-1,'CAS id must be a nonnegative safe integer, never bool')
        _uint(row['logical_bytes'], 2 * 1024 * 1024, 'CAS logical record budget')
        _require(type(row['logical_sha256']) is str and SHA.fullmatch(row['logical_sha256']), 'CAS logical SHA shape')
        data, refs, depth, work = self._fragment_value(row['capture'], set())
        _require(depth <= 128 and work <= 2097152, 'CAS expanded tree budget')
        for h in refs:
            _require(self.entries[h]['first_record_index'] <= self.record_index, 'CAS reference precedes declaration')
        logical = data + b'\n'
        _require(len(logical) == row['logical_bytes'] and hashlib.sha256(logical).hexdigest() == row['logical_sha256'], 'CAS reconstructed logical line mismatch')
        value = json.loads(logical)
        _require(type(value)is dict and type(value['record_kind'])is str and type(value['id'])is int
                 and value['record_kind']==row['record_kind']and value['id']==row['id'],'CAS logical identity')
        self.actual_refs.update(refs)
        for h in refs:
            self.first_seen.setdefault(h, self.record_index)
            self.last_seen[h] = self.record_index
        self.logical_bytes += len(logical)
        self.max_record = max(self.max_record, len(logical))
        _require(self.logical_bytes <= 8 * 1024 * 1024 * 1024, 'CAS logical8GiB budget')
        self.logical_hash.update(logical)
        self.stream_hash.update(raw)
        self.stream_bytes+=len(raw)
        self.max_stream_record=max(self.max_stream_record,len(raw))
        _require(self.stream_bytes<=1024*1024*1024,'CAS envelope stream1GiB budget')
        self.record_index += 1
        return value

    def finish(self, receipt):
        _require(receipt['protocol'] == PROTOCOL and receipt['marker'] == MARKER, 'CAS runtime protocol')
        checks = {'records': self.record_index, 'logical_bytes': self.logical_bytes,
                  'logical_sha256': self.logical_hash.hexdigest(), 'maximum_logical_record_bytes': self.max_record,
                  'unique_blobs': len(self.entries), 'unique_blob_bytes': self.unique_bytes,
                  'maximum_blob_bytes':max((x['bytes']for x in self.entries.values()),default=0),
                  'index_uncompressed_bytes':self.stream_bytes,'index_uncompressed_sha256':self.stream_hash.hexdigest(),
                  'maximum_index_record_bytes':self.max_stream_record,
                  'maximum_blob_index_record_bytes':self.max_blob_index_record,
                  'total_logical_blob_references': sum(self.actual_refs.values()),
                  'blob_index_bytes': self.index_bytes, 'blob_index_sha256': self.index_hash.hexdigest(),
                  'blob_references_bytes': self.refs_bytes, 'blob_references_sha256': self.refs_hash.hexdigest()}
        for k, value in checks.items():
            _require(receipt[k] == value, 'CAS runtime differs: ' + k)
        _require(set(self.actual_refs) == set(self.entries), 'CAS unreferenced/missing blob')
        for h, row in self.declared_refs.items():
            _require(row['total_logical_references'] == self.actual_refs[h]
                     and row['first_record_index'] == self.first_seen[h]
                     and row['last_record_index'] == self.last_seen[h], 'CAS occurrence metadata mismatch')
        return dict(checks, all_blobs_and_occurrences_verified=True, decoder_cache_bytes=self.cache_bytes,
                    logical_fragment_cache_weight_bytes=self.fragment_cache_weight,
                    logical_fragment_cache_weight_limit=FRAGMENT_CACHE_WEIGHT_LIMIT,
                    logical_fragment_cache_item_limit=FRAGMENT_CACHE_ITEM_LIMIT)
