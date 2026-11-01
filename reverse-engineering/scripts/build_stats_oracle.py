#!/usr/bin/env python3
"""Build a host-free original1573-body oracle with explicitly replaced allocators.

All original function indices/types are retained. Only1573 is copied; allocator
106495, temporary-8B-vector reserve65045 and free71577 use bounded WASM shims.
Every other function is a trap, including message emission and BTree insertion.
Fixtures must prepopulate fields22/28/1109 and match speed1456 to avoid those.
This is original-body numeric acceptance under substituted allocation, not full
original closure, network, game-entry, save or production-runtime acceptance.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import tarfile

from build_progression_oracle import unsigned, section, read_leb
from trace_coop import module_data
from wasm_index import ORIGINAL_SHA, body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
BODY_SHA = 'e05c38868e23157be89c2ac8030ef941ce24f583758c2e3c5f9d29cda8d5db07'
INDEX = ROOT/'evidence/wasm-index-20261031T213003.825753Z/index.sqlite'


def parse_sections(binary):
    if binary[:8] != b'\0asm\1\0\0\0': raise ValueError('Invalid WASM')
    p = 8; result = {}
    while p < len(binary):
        kind = binary[p]; length, begin = read_leb(binary,p+1); end = begin+length
        if end > len(binary): raise ValueError('Section out of range')
        if kind and kind in result: raise ValueError('Duplicate section')
        result[kind] = binary[begin:end]; p = end
    return result


def vector_uint(raw):
    count,p=read_leb(raw,0); result=[]
    for _ in range(count):
        value,p=read_leb(raw,p);result.append(value)
    if p!=len(raw):raise ValueError('Vector boundary differs')
    return result


def imported_types(raw):
    count,p=read_leb(raw,0); result=[]
    for _ in range(count):
        for _ in range(2):
            length,p=read_leb(raw,p);p+=length
        if raw[p]!=0:raise ValueError('Expected all function imports')
        value,p=read_leb(raw,p+1);result.append(value)
    if p!=len(raw):raise ValueError('Import boundary differs')
    return result


def signed(value):
    result=bytearray()
    while True:
        byte=value&127;value>>=7
        stop=(value==0 and byte&64==0) or (value==-1 and byte&64!=0)
        result.append(byte if stop else byte|128)
        if stop:return bytes(result)


SHIMS = r'''(module
  (memory 512 512)
  (global (mut i32) (i32.const 32505856))
  (global (mut i32) (i32.const 25165824))
  (global (mut i32) (i32.const 0))
  (global (mut i32) (i32.const 0))
  (global (mut i32) (i32.const 0))
  ;; 106495(size,alignment)->ptr. Inputs here are 8B-vector lengths, alignment4.
  (func (param i32 i32) (result i32) (local i32 i32)
    local.get 1 i32.const 4 i32.ne if unreachable end
    global.get 1 local.tee 2 local.get 0 i32.add local.tee 3
    local.get 2 i32.lt_u if unreachable end
    local.get 3 i32.const 29360128 i32.gt_u if unreachable end
    local.get 3 global.set 1
    global.get 2 i32.const 1 i32.add global.set 2
    local.get 2)
  ;; 65045(&Vec8). Layout cap+0,ptr+4,len+8; copy exactly len*8 bytes.
  (func (param i32) (local i32 i32 i32 i32 i32)
    local.get 0 i32.load local.set 1
    local.get 0 i32.load offset=8 local.set 2
    local.get 2 local.get 1 i32.ne if unreachable end
    local.get 1 i32.const 2 i32.mul local.tee 3
    i32.const 4 i32.lt_u if i32.const 4 local.set 3 end
    local.get 3 i32.const 524288 i32.gt_u if unreachable end
    global.get 1 local.tee 4 local.get 3 i32.const 3 i32.shl i32.add
    local.tee 5 i32.const 29360128 i32.gt_u if unreachable end
    local.get 5 global.set 1
    local.get 4 local.get 0 i32.load offset=4 local.get 2 i32.const 3 i32.shl memory.copy
    local.get 0 local.get 3 i32.store
    local.get 0 local.get 4 i32.store offset=4
    global.get 3 i32.const 1 i32.add global.set 3)
  ;;71577(ptr,size): fixture arena is reset between calls; no memory reuse.
  (func (param i32 i32)
    global.get 4 i32.const 1 i32.add global.set 4)
)'''


def build():
    original=ROOT.parent/'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(original)!=ORIGINAL_SHA:raise ValueError('Original identity differs')
    binary=original.read_bytes();sections=parse_sections(binary);ranges=body_ranges(binary)
    begin,end,length=ranges[1573];body=binary[begin:end]
    if hashlib.sha256(body).hexdigest()!=BODY_SHA:raise ValueError('1573 body identity differs')
    index_sha=sha(INDEX)
    with sqlite3.connect(INDEX.resolve().as_uri()+'?mode=ro',uri=True) as con:
        meta={k:json.loads(v) for k,v in con.execute('select key,value from meta')}
        if meta['original_sha256']!=ORIGINAL_SHA or meta['wat_sha256']!=WAT_SHA:raise ValueError('Index identity differs')
        wat=Path(meta['wat_path'])
        if sha(wat)!=WAT_SHA:raise ValueError('WAT identity differs')
        row=con.execute('select body_start,body_end,body_bytes from functions where idx=1573').fetchone()
        if tuple(row)!=ranges[1573]:raise ValueError('Indexed code boundary differs')
    output=ROOT/'evidence'/datetime.now(timezone.utc).strftime('stats-oracle-%Y%m%dT%H%M%S.%fZ')
    output.mkdir(parents=True,exist_ok=False)
    tools=ROOT/'.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin'
    provenance=json.loads((ROOT/'.toolchain/rea-wasm-profile/installed-provenance.json').read_text())
    if sha(tools/'wasm-validate')!=provenance['tools']['wasm-validate']['sha256']:raise ValueError('Validator identity differs')
    archive=ROOT/'.toolchain/rea-wasm-profile/wabt-1.0.42-macos-arm64.tar.gz'
    if sha(archive)!=provenance['archive_sha256']:raise ValueError('WABT archive identity differs')
    with tarfile.open(archive) as tar:
        candidates=[m for m in tar.getmembers() if m.name.endswith('/bin/wat2wasm')]
        if len(candidates)!=1 or tar.extractfile(candidates[0]).read()!=(tools/'wat2wasm').read_bytes():
            raise ValueError('wat2wasm differs from pinned archive')
    shimwat=output/'allocation-shims.wat';shimwat.write_text(SHIMS)
    shimwasm=output/'allocation-shims.wasm'
    subprocess.run([str(tools/'wat2wasm'),str(shimwat),'-o',str(shimwasm)],check=True,timeout=30)
    shimsections=parse_sections(shimwasm.read_bytes());count,p=read_leb(shimsections[10],0);shimbodies=[]
    if count!=3:raise ValueError('Unexpected shim functions')
    for _ in range(count):
        size,p=read_leb(shimsections[10],p);shimbodies.append(shimsections[10][p:p+size]);p+=size
    function_types=imported_types(sections[2])+vector_uint(sections[3])
    if [function_types[i] for i in (1573,106495,65045,71577)]!=[3,6,3,0]:raise ValueError('Callee signatures differ')
    # All indices, including original imports, become defined functions. A trap
    # validates for any result signature and prevents accidental external work.
    bodies=[b'\x00\x00\x0b']*len(function_types)
    bodies[1573]=body
    for i,shim in zip((106495,65045,71577),shimbodies):bodies[i]=shim
    funcs=unsigned(len(function_types))+b''.join(unsigned(i) for i in function_types)
    code=unsigned(len(bodies))+b''.join(unsigned(len(b))+b for b in bodies)
    exports=[('recalculate',0,1573),('memory',2,0),('stack',3,0),('heap',3,1),
             ('allocations',3,2),('reserves',3,3),('frees',3,4)]
    exportbytes=unsigned(len(exports))+b''.join(unsigned(len(n))+n.encode()+bytes([k])+unsigned(i) for n,k,i in exports)
    # Retain only exact static spans reached by1573's class/race reads.
    source=json.loads((ROOT/'reports/2026-11-01-derived-stats.json').read_text())
    spans=[source['class_lookup_source'],source['race_lookup_source']]
    spans += [entry['source'] for entry in source['classes']]
    spans += [entry[key] for entry in source['races'] for key in ('source','modifier_source')]
    segments,*_=module_data(binary)
    memory=bytearray(max(s['address']+s['size'] for s in segments))
    for segment in segments:
        memory[segment['address']:segment['address']+segment['size']]=binary[segment['file_start']:segment['file_end']]
    static=[];data=bytearray(unsigned(len(spans)))
    for span in spans:
        address=span['memory_address'];raw=bytes.fromhex(span['hex'])
        origins=[]
        for segment in segments:
            lo=max(address,segment['address']);hi=min(address+len(raw),segment['address']+segment['size'])
            if lo<hi:origins.append({'address':lo,'bytes':hi-lo,'file_offset':segment['file_start']+lo-segment['address']})
        if memory[address:address+len(raw)]!=raw or hashlib.sha256(raw).hexdigest()!=span['sha256']:raise ValueError('Static data identity differs')
        data+=b'\x00\x41'+signed(address)+b'\x0b'+unsigned(len(raw))+raw
        static.append({'address':address,'bytes':len(raw),'sha256':span['sha256'],'original_data_ranges':origins,
                       'implicit_zero_bytes':len(raw)-sum(x['bytes'] for x in origins)})
    module=b'\0asm\1\0\0\0'+section(1,sections[1])+section(3,funcs)+section(5,shimsections[5])+section(6,shimsections[6])+section(7,exportbytes)+section(10,code)+section(11,bytes(data))
    target=output/'isolated-stats.wasm';target.write_bytes(module)
    subprocess.run([str(tools/'wasm-validate'),str(target)],check=True,timeout=60)
    checksections=parse_sections(module)
    if set(checksections)!={1,3,5,6,7,10,11}:raise ValueError('Unexpected module sections')
    # Independently re-extract from the generated code section (no imports).
    code_count,q=read_leb(checksections[10],0);copied=None
    if code_count!=len(function_types):raise ValueError('Function count differs')
    for i in range(code_count):
        size,q=read_leb(checksections[10],q)
        if i==1573:copied=checksections[10][q:q+size]
        q+=size
    if q!=len(checksections[10]) or copied!=body:raise ValueError('Copied body is not byte-identical')
    manifest={'version':'0.126.0','build':'3e72472a','original_wasm_sha256':ORIGINAL_SHA,
              'complete_wat_sha256':WAT_SHA,'index_sha256':index_sha,
              'original_function_index':1573,'original_body_sha256':BODY_SHA,
              'original_body_bytes':length,'original_body_byte_identical':True,
              'module_file':target.name,'module_bytes':len(module),'module_sha256':sha(target),
              'imports':[],'start':None,'table':None,'memory_fixed_pages':512,
              'defined_functions':len(bodies),'original_bodies_retained':[1573],
              'replacement_functions':{'106495':'bounded bump allocator, alignment4',
                  '65045':'bounded8B vector reserve/copy','71577':'arena free counter; reset per fixture'},
              'all_other_functions':'unreachable trap',
              'static_spans':static,'shim_wat_sha256':sha(shimwat),
              'oracle_scope':'original1573 byte-identical body with substituted allocation; existing BTree fields and fixed speed required',
              'network_used':False,'user_saves_read':False,'game_entry_executed':False}
    if sha(original)!=ORIGINAL_SHA or sha(wat)!=WAT_SHA or sha(INDEX)!=index_sha:raise ValueError('Original inputs changed')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return output,manifest


if __name__=='__main__':
    directory,manifest=build()
    print(json.dumps({'run_directory':str(directory),'module_sha256':manifest['module_sha256'],
                      'original_body_byte_identical':True,'replacement_callees':[106495,65045,71577]}))
