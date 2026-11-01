#!/usr/bin/env python3
"""Bounded, read-only resource135->137 and Windows declaration mapping.

Queries the existing RO SQLite indices and seeks only named WAT functions.
Neither WebAssembly nor the Windows executable is executed or instantiated.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import mmap
import os
import re
import signal
import sqlite3
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('scripts/trace_resource_migration137.py',
           'scripts/trace_resource_spawn135.py',
           'reconstruction/core_spec/resource_spawn135.py')
PROFILES = {
    '135': ('wasm0135-profile-20261101T031028.877964Z', 'official-0.135.1-full.wat',
            'official-acquisition-20261101T030310.926207Z',
            'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'),
    '137': ('wasm0137-profile-20261101T162221.947222Z', 'official-0.137.0-full.wat',
            'official-acquisition-20261101T154517.001467Z',
            '20ec9a2b5182a72e13ca11668ff0aab17e9dc54a10b923b546708ab85e3fe1c8'),
}
NATIVE = ROOT / 'originals/official-acquisition-20261101T154517.001467Z/windows-0.137.0/AzerothSurvivors.exe'
NATIVE_SHA = 'aa6b254f905e2f7a4cbc7c2c8f11af822ec362e3d2b8e84cabd8c38893a10dc8'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def missing(pid, group=False):
    try:
        (os.killpg if group else os.kill)(pid, 0)
    except ProcessLookupError:
        return True
    return False


class Profile:
    def __init__(self, version, out):
        directory, wat, acquisition, expected = PROFILES[version]
        self.version, self.out = version, out
        self.directory = ROOT / 'evidence' / directory
        self.binary = ROOT / 'originals' / acquisition / 'latest-wenilla_bg.wasm'
        assert sha(self.binary) == expected
        self.source = self.binary.open('rb')
        self.wat = (self.directory / wat).open('rb')
        self.db = sqlite3.connect((self.directory / 'index.sqlite').as_uri() + '?mode=ro', uri=True)
        self.db.execute('pragma query_only=on')
        self.db.row_factory = sqlite3.Row
        self.identity = json.loads((self.directory / 'binary-identity.json').read_text())
        self.rows, self.queries, self.wat_bytes_read = {}, [], 0
        self.metadata = {n: sha(self.directory / n) for n in ('manifest.json', 'binary-identity.json')}
        self.index_stat = self.stat_index()

    def stat_index(self):
        s = (self.directory / 'index.sqlite').stat()
        return dict(bytes=s.st_size, mtime_ns=s.st_mtime_ns)

    def query(self, sql, arguments=()):
        rows = [dict(row) for row in self.db.execute(sql, arguments)]
        self.queries.append(dict(sql=sql, parameters=list(arguments), rows=rows))
        return rows

    def body(self, index):
        row = self.query('select * from functions where idx=?', (index,))[0]
        self.source.seek(row['body_start'])
        data = self.source.read(row['body_end'] - row['body_start'])
        return row, data

    def function(self, index):
        row, body = self.body(index)
        size = row['wat_end'] - row['wat_start']
        assert size <= 512 * 1024
        self.wat.seek(row['wat_start'])
        data = self.wat.read(size)
        assert len(data) == size
        self.wat_bytes_read += size
        (self.out / f'{self.version}-{index}.wat').write_bytes(data)
        calls = self.query('select callee,wat_line,instruction from calls where caller=? order by wat_offset', (index,))
        result = dict(row, body_sha256=hashlib.sha256(body).hexdigest(),
                      wat_sha256=hashlib.sha256(data).hexdigest(), calls=calls,
                      signature=data.splitlines()[0].decode())
        self.rows[index] = result
        return data.decode()

    def memory(self, address, size):
        assert 0 <= address and 0 <= size <= 4096
        # Defined static linear memory: implicit zeros plus every active segment
        # in source order. This does not fill unknown dynamic record cells.
        data = bytearray(size)
        for segment in self.identity['data_segments']:
            if segment['address'] is None:
                continue
            lo = max(address, segment['address'])
            hi = min(address + size, segment['address'] + segment['bytes'])
            if lo < hi:
                self.source.seek(segment['file_offset'] + lo - segment['address'])
                data[lo-address:hi-address] = self.source.read(hi-lo)
        return bytes(data)

    def finish(self):
        assert self.stat_index() == self.index_stat
        assert self.metadata == {n: sha(self.directory / n) for n in self.metadata}
        assert sha(self.binary) == PROFILES[self.version][3]
        self.source.close()
        self.wat.close()
        self.db.close()
        return dict(version=self.version, original_sha256=PROFILES[self.version][3],
                    profile=str(self.directory.relative_to(ROOT)), metadata_sha256=self.metadata,
                    index_open_mode='ro/query_only', index_stat_before_after=self.index_stat,
                    full_index_rehashed=False, complete_WAT_read=False,
                    target_WAT_bytes_read=self.wat_bytes_read, functions=list(self.rows.values()), queries=self.queries)


def resource_window(text):
    lines = text.splitlines()
    at = next(i for i, line in enumerate(lines) if 'f32.load offset=2444' in line)
    start = at - 5
    assert lines[start].strip().startswith('block')
    after = next(i for i in range(at + 1, len(lines)) if 'f32.load offset=2448' in lines[i])
    end = after - 3
    assert lines[end].strip().startswith('block')
    return '\n'.join(lines[start:end]) + '\n', start + 1, end


def compare_shape(old, new):
    """Keep every instruction; only label, call indices and named data move."""
    left, right = old.splitlines(), new.splitlines()
    assert len(left) == len(right)
    calls, relocations, unexpected = [], [], []
    for number, (a, b) in enumerate(zip(left, right), 1):
        if a == b:
            continue
        if number == 1 and a.lstrip().startswith('(func'):
            assert re.sub(r'\(;\d+;\)', '(;ENTRY;)', a) == re.sub(r'\(;\d+;\)', '(;ENTRY;)', b)
            continue
        ca, cb = re.fullmatch(r'(\s*)call (\d+)', a), re.fullmatch(r'(\s*)call (\d+)', b)
        if ca and cb and ca[1] == cb[1]:
            calls.append(dict(line=number, old=int(ca[2]), new=int(cb[2])))
            continue
        pattern = r'(\s*(?:i32.const |[if]\d+\.load(?:\d+_u)? offset=))(\d+)'
        aa, bb = re.fullmatch(pattern, a), re.fullmatch(pattern, b)
        if aa and bb and aa[1] == bb[1] and min(int(aa[2]), int(bb[2])) > 1000000:
            relocations.append(dict(line=number, operation=aa[1].strip(), old=int(aa[2]), new=int(bb[2])))
            continue
        unexpected.append(dict(line=number, old=a, new=b))
    return dict(lines=len(left), instruction_shape_equal_after_recorded_relocations=not unexpected,
                call_relocations=calls, data_relocations=relocations, other_instruction_changes=unexpected,
                dynamic_equivalence_claimed=False)


class PE:
    def __init__(self, data):
        self.data = data
        pe = struct.unpack_from('<I', data, 60)[0]
        assert data[pe:pe+4] == b'PE\0\0'
        count, size = struct.unpack_from('<H', data, pe+6)[0], struct.unpack_from('<H', data, pe+20)[0]
        optional = pe + 24
        assert struct.unpack_from('<H', data, optional)[0] == 0x20b
        self.base = struct.unpack_from('<Q', data, optional+24)[0]
        self.sections = []
        for index in range(count):
            at = optional + size + index * 40
            vs, rva, raw_size, file_offset = struct.unpack_from('<4I', data, at+8)
            self.sections.append(dict(name=data[at:at+8].split(b'\0')[0].decode(), virtual_size=vs,
                                      rva=rva, raw_size=raw_size, file_offset=file_offset))
        rva, size = struct.unpack_from('<II', data, optional+112+3*8)
        self.pdata_file, self.pdata_bytes = self.file(self.base+rva, size), size

    def file(self, va, size=1):
        rva = va - self.base
        section = next(s for s in self.sections if s['rva'] <= rva and rva+size <= s['rva']+s['raw_size'])
        return section['file_offset'] + rva - section['rva']

    def read(self, va, size):
        at = self.file(va, size)
        return self.data[at:at+size]

    def function_at(self, va):
        found = []
        for at in range(self.pdata_file, self.pdata_file+self.pdata_bytes, 12):
            a, b, unwind = struct.unpack_from('<III', self.data, at)
            if self.base+a <= va < self.base+b:
                found.append(dict(start=self.base+a, end=self.base+b, bytes=b-a,
                                  pdata_file_offset=at, unwind_rva=unwind))
        assert len(found) == 1
        return found[0]


def native_correspondence(out, geometry):
    assert NATIVE.stat().st_size == 147844608 and sha(NATIVE) == NATIVE_SHA
    with NATIVE.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        pe = PE(data)
        rows = []
        for kind, visual, display in ((3, 9006, 5931), (4, 9007, 5995), (5, 9008, 5991)):
            packed = struct.pack('<II', display, 0x3f800000)
            at = data.find(packed)
            assert at >= 0 and data.find(packed, at+1) == -1
            branch_file = at - 12
            expected = bytes.fromhex('c78590000000') + struct.pack('<I', visual) + bytes.fromhex('49bf') + packed
            assert data[branch_file:branch_file+20] == expected
            section = next(s for s in pe.sections if s['file_offset'] <= at < s['file_offset']+s['raw_size'])
            assert section['name'] == '.text'
            branch = pe.base + section['rva'] + branch_file-section['file_offset']
            rows.append(dict(kind=kind, visual=visual, display=display, scale_bits=0x3f800000,
                             branch_va=branch, file_offset=branch_file, bytes20_hex=expected.hex(),
                             section=section['name'], packed_display_scale_occurrences=1))
        bounds = pe.function_at(rows[0]['branch_va'])
        assert bounds['bytes'] <= 16384 and all(pe.function_at(row['branch_va']) == bounds for row in rows)
        body = pe.read(bounds['start'], bounds['bytes'])
        (out/'native-resource-producer.bin').write_bytes(body)
        sequence = bytes.fromhex('4489f8488d0d')
        at = body.index(sequence)
        assert body.find(sequence, at+1) == -1
        table = bounds['start'] + at + 10 + struct.unpack_from('<i', body, at+6)[0]
        entries = [table + struct.unpack('<i', pe.read(table+4*index, 4))[0] for index in range(7)]
        assert all(entries[row['kind']] == row['branch_va'] for row in rows)
        lea = body.index(bytes.fromhex('488d1d'), 0, 256)
        zone_base = bounds['start'] + lea + 7 + struct.unpack_from('<i', body, lea+3)[0]
        assert bytes.fromhex('4869f0f0000000') in body[:256]
        native_geometry = []
        for index in range(12):
            words = struct.unpack('<III', pe.read(zone_base+240*index+200, 8)+pe.read(zone_base+240*index+216, 4))
            assert list(words) == geometry[index]['137_words']
            native_geometry.append(dict(index=index, record_va=zone_base+240*index, words=list(words)))
        writes = {'kind32':'448974c820', 'amount36':'448964c824', 'guid40':'4c897cc828',
                  'visual48':'8954c830', 'xy52':'0f1374c834', 'z60':'f30f117cc83c', 'time64':'f3440f1144c840'}
        assert bytes.fromhex('488d0cf6') in body
        assert all(bytes.fromhex(value) in body for value in writes.values())
        assert bytes.fromhex('4189d7') in body[:128]  #edx -> r15d -> switch
        result = dict(exe_sha256=NATIVE_SHA, exe_bytes=len(data), image_base=pe.base,
            function=bounds, function_body_sha256=hashlib.sha256(body).hexdigest(),
            resource_declarations=rows, jump_table=dict(va=table, file_offset=pe.file(table, 28),
                raw28_hex=pe.read(table, 28).hex(), targets=entries),
            zone_geometry=dict(native_base_va=zone_base, stride=240, xy_offsets=[200,204], radius_offset=216,
                all12_match_Web137=True, rows=native_geometry),
            native_pickup_projection=dict(stride=72, stride_instruction='lea rcx,[rsi+8*rsi]; address[rax+8*rcx]',
                marker=24, kind=32, amount=36, guid=40, visual=48, xyz=[52,56,60], time=64,
                auxiliary_vector={'capacity':0,'pointer':8,'length':16},
                instruction_byte_anchors=writes, complete_record_layout_claimed=False),
            narrow_native_Game_reads=dict(world_pointer=3552,time=3720,pickup_capacity=1768,pickup_pointer=1776,pickup_length=1784),
            static_correspondence_only=True, complete_Game_ABI_claimed=False, native_executed=False)
    command = ['/usr/bin/objdump', '-d', '--x86-asm-syntax=intel',
               '--start-address='+hex(bounds['start']), '--stop-address='+hex(bounds['end']), str(NATIVE)]
    started = time.monotonic()
    with (out/'native-resource.objdump.txt').open('wb') as stdout, (out/'native-resource.objdump.stderr').open('wb') as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True,
                                 env=dict(os.environ, TMPDIR=str(out)))
        save(out/'objdump-owned.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=30))
        try:
            child.wait(timeout=30)
        finally:
            try:
                os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
    terminal = dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=missing(child.pid),
                    pgid_missing=missing(child.pid,True),seconds=time.monotonic()-started,deadline_seconds=30)
    assert terminal['exit_code']==0 and terminal['pid_missing'] and terminal['pgid_missing']
    assert (out/'native-resource.objdump.txt').stat().st_size < 256*1024
    save(out/'objdump-terminal.json',terminal)
    result['tool'] = dict(path='/usr/bin/objdump',sha256=sha('/usr/bin/objdump'),
                         disassembly_sha256=sha(out/'native-resource.objdump.txt'),owned_terminal=terminal)
    assert sha(NATIVE) == NATIVE_SHA
    return result


def worker(out):
    before = {name:sha(ROOT/name) for name in SOURCES}
    save(out/'source-before.json',before)
    for name in SOURCES:
        path=out/'source-snapshot'/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes((ROOT/name).read_bytes())
    profiles = {version:Profile(version,out) for version in PROFILES}
    latest=profiles['137']
    deadline=latest.query("select distinct function_idx from memops where field_offset=2444 and operation='f32.store'")
    assert deadline == [dict(function_idx=947)]
    candidates=latest.query('select function_idx,count(distinct value) as n from iconsts where value in (9006,9007,9008) and function_idx in (select callee from calls where caller=947) group by function_idx having n=3')
    assert candidates == [dict(function_idx=1420,n=3)]
    texts={('135',i):profiles['135'].function(i) for i in (947,1417,13516,1821)}
    for i in (947,1420,13502,1827):
        texts['137',i]=latest.function(i)
    window_old,a,b=resource_window(texts['135',947])
    window_new,c,d=resource_window(texts['137',947])
    assert 'call 13502' in window_new and 'call 1420' in window_new
    assert re.search(r'\(param i32 i32 i32 i32 i32\) \(result i64\)',texts['137',1827].splitlines()[0])
    comparisons=[]
    for old,new in ((1417,1420),(13516,13502),(1821,1827)):
        check=compare_shape(texts['135',old],texts['137',new])
        assert check['instruction_shape_equal_after_recorded_relocations']
        comparisons.append(dict(old=old,new=new,scope='complete function instruction shape only',**check))
    check=compare_shape(window_old,window_new)
    assert check['instruction_shape_equal_after_recorded_relocations'] and not check['data_relocations']
    comparisons.insert(0,dict(old=947,new=947,scope='G2444 resource window only, not full947',
        old_local_lines=[a,b],new_local_lines=[c,d],**check))
    (out/'135-947-resource-window.wat').write_text(window_old)
    (out/'137-947-resource-window.wat').write_text(window_new)
    helpers=[]
    for old,new in sorted({(row['old'],row['new']) for value in comparisons for row in value['call_relocations']}):
        _,left=profiles['135'].body(old)
        _,right=latest.body(new)
        helpers.append(dict(old=old,new=new,old_body_sha256=hashlib.sha256(left).hexdigest(),new_body_sha256=hashlib.sha256(right).hexdigest(),
                            raw_body_identical=left==right,execution_acceptance_claimed=False))
    geometry=[]
    for index in range(12):
        row=dict(index=index)
        for version,base in (('135',5456016),('137',1665968)):
            p=base+index*152
            row[version+'_words']=list(struct.unpack('<III',profiles[version].memory(p+104,8)+profiles[version].memory(p+120,4)))
        assert row['135_words']==row['137_words']
        geometry.append(row)
    declarations=[]
    declaration_lines=texts['137',1420].splitlines()
    for kind,visual,display in ((3,9006,5931),(4,9007,5995),(5,9008,5991)):
        packed=display|(0x3f800000<<32)
        matches=[i for i,line in enumerate(declaration_lines) if line.strip()=='i64.const '+str(packed)]
        assert len(matches)==1
        at=matches[0]
        assert [line.strip()for line in declaration_lines[at+1:at+4]]==['local.set 14','i32.const '+str(visual),'local.set 9']
        declarations.append(dict(kind=kind,visual=visual,display=display,scale_bits=0x3f800000,
            packed_display_scale=packed,local_line=at+1,
            absolute_WAT_line=latest.rows[1420]['wat_line']+at,
            instruction_window=declaration_lines[at:at+5],
            kind_switch_correspondence='Full1351417/1371420 control-flow instructions identical after recorded call/data relocations'))
    wrong=latest.query('select * from functions where idx=1821')[0]
    latest.wat.seek(wrong['wat_start'])
    header=latest.wat.read(128).decode().splitlines()[0]
    latest.wat_bytes_read+=128
    assert '(param i32 i32 i32)' in header and '(result i64)' not in header
    native=native_correspondence(out,geometry)
    after={name:sha(ROOT/name)for name in SOURCES}
    assert before==after
    result=dict(status='static_resource_migration_mapping_complete_dynamic_pending',
        version='0.137.0',build='d171b8f9f',source_before=before,source_after=after,
        profiles={v:p.finish()for v,p in profiles.items()},function_mapping=comparisons,
        resource_declaration_instruction_windows=declarations,
        direct_callee_raw_body_comparisons=helpers,zone_geometry12=geometry,
        rejected_same_index_assumption=dict(old135=1821,incorrect137=1821,actual137_signature=header,correct137=1827),
        Web137_layout=dict(Game=dict(now=2352,resource_deadline=2444,rng=[1720,1724,1728,1732],
            pickup_capacity=1868,pickup_pointer=1872,pickup_count=1876,world_pointer=2348,shared_counter=2408),
            pickup=dict(stride=56,marker=0,kind=8,amount=12,guid=16,auxiliary_vector=[24,28,32],visual=36,xyz=[40,44,48],time=52,unwritten_padding=[4,5,6,7]),
            resource_definitions=[{k:row[k]for k in ('kind','visual','display','scale_bits')}for row in declarations]),
        rules=['Due now>=G2444 writes now+45 before active kind3..5 cap2 count; marker is not read by this cap.',
            'xoshiro multiply3 rejects low product bits0xc0000000; postdraw state0 is amount, then random position advances shared RNG.',
            '13713502 samples15..40,1371420 clamps zone radius-2/max1, resolves height and calls1371827 with actor kind5/flags0.',
            'Full947 has other135->137 changes including432B Unit stride; only G2444 resource window is instruction-shape matched here.',
            'Call-index/data relocations and raw helper-body comparisons are static evidence, not dynamic semantic acceptance.'],
        native=native,original_program_executed=False,wasm_instantiated=False,new_original_cases=0,new_model_validation_cases=0,
        full880_frames=0,native_executed=False,complete_game=False,
        pending=['No137 resource model or original-function differential in this report.',
            'Referenced changed callee bodies require independent migration/validation; normalized shape alone is not execution proof.',
            'Resource collection effects,other due schedules and full947/880 remain outside scope.',
            'Windows resource producer fields are narrow static observations,not complete native Game/Unit ABI or cross-platform equivalence.'])
    save(out/'mapping.json',result)
    print(json.dumps(dict(directory=str(out),mapping_sha256=sha(out/'mapping.json'),status=result['status'],new_original_cases=0,native_function=hex(native['function']['start']))),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',type=Path)
    args=parser.parse_args()
    if args.worker:
        worker(args.worker.resolve())
        return
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('resource-migration0137-static-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    started=time.monotonic()
    error=None
    def stop(signum, frame):
        raise KeyboardInterrupt('Owned static trace stop '+str(signum))
    previous=signal.signal(signal.SIGTERM,stop)
    with(out/'stdout.log').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
        child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker',str(out)],stdout=stdout,stderr=stderr,
            start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'))
        save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,deadline_seconds=60))
        try:
            child.wait(timeout=60)
        except (subprocess.TimeoutExpired,KeyboardInterrupt,OSError) as exc:
            error=repr(exc)
        finally:
            try:
                os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
            # objdump has its own bounded session; reclaim it even if the
            # worker was interrupted before its normal tool cleanup.
            ledger=out/'objdump-owned.json'
            if ledger.exists():
                tool=json.loads(ledger.read_text())
                try:
                    os.killpg(tool['pgid'],signal.SIGKILL)
                except ProcessLookupError:
                    pass
            signal.signal(signal.SIGTERM,previous)
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=missing(child.pid),
                  pgid_missing=missing(child.pid,True),seconds=time.monotonic()-started,deadline_seconds=60,error=error)
    save(out/'process-terminal.json',terminal)
    print((out/'stdout.log').read_text(),end='')
    print(json.dumps(terminal))
    assert child.returncode==0 and not error and terminal['pid_missing']and terminal['pgid_missing']


if __name__=='__main__':
    main()
