#!/usr/bin/env python3
"""Unchanged current884 local declaration + contiguous original clock prefix.

This builds a micro-module, NOT an original full884 entry. Only a return of
local156 and outer end are appended. The prefix stack subtraction remains and
is observed by the runner; no stack restoration is inserted into the prefix.
"""
import hashlib,sqlite3,struct
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,PROFILE,Reader,original,signatures,unsigned,sha,save

def section(k,payload):return bytes([k])+unsigned(len(payload))+payload
def name(v):b=v.encode();return unsigned(len(b))+b
def signed(value):
    data=bytearray()
    while True:
        b=value&127;value>>=7;done=(value==0 and not b&64)or(value==-1 and b&64)
        data.append(b if done else b|128)
        if done:return bytes(data)
def build(out):
    raw,identity,ranges=original();a,b,n=ranges[884];assert signatures(raw,identity)[884]==('7f7c','')and n==139350
    r=Reader(raw,a,b);groups=[]
    for _ in range(r.uint()):groups.append((r.uint(),r.byte()))
    locals_end=r.pos;assert groups==[(137,0x7f),(11,0x7e),(11,0x7d),(2,0x7c)]
    ending=bytes.fromhex('2000200139030820004201370300')
    end=raw.index(ending,locals_end,locals_end+256)+len(ending)
    assert raw[end:end+8]==bytes.fromhex('20002802d026211a')
    decl=raw[a:locals_end];prefix=raw[locals_end:end];tail=b'\x20'+unsigned(156)+b'\x0b'
    body=decl+prefix+tail
    # local156 is the seventh f32 local with original indices, unchanged.
    flat=[0x7f,0x7c]+[t for c,t in groups for _ in range(c)];assert flat[156]==0x7d
    micro=(b'\0asm\x01\0\0\0'+section(1,b'\x01\x60\x02\x7f\x7c\x01\x7d')+
        section(3,b'\x01\x00')+section(5,b'\x01\x01\x20\x20')+
        section(6,b'\x01\x7f\x01\x41'+signed(1048576)+b'\x0b')+
        section(7,b'\x03'+name('sample')+b'\x00\x00'+name('memory')+b'\x02\x00'+name('stack')+b'\x03\x00')+
        section(10,b'\x01'+unsigned(len(body))+body))
    p=out/'frame-clock139-original-prefix-micro.wasm';p.write_bytes(micro)
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
        ws,we=db.execute('select wat_start,wat_end from functions where idx=884').fetchone()
    assert we-ws==4012471
    with(PROFILE/'official-0.139.0-full.wat').open('rb')as f:f.seek(ws);wat=f.read(we-ws)
    lines=wat.decode().splitlines(keepends=True);first=''.join(lines[:45]);assert'local.set 156'in first and'i64.store'in first
    (out/'884-first45.wat').write_text(first)
    for label,x,y in [('firstPhase1Clock',34962,34978),('secondPhase1Clock',47936,47955)]:
        (out/(label+'.wat')).write_text(''.join(lines[x-1:y]))
    (out/'original-local-declaration.bin').write_bytes(decl);(out/'original-clock-prefix.bin').write_bytes(prefix);(out/'instrumentation-tail.bin').write_bytes(tail)
    result=dict(kind='original_contiguous_instruction_prefix_micro_module_not_full884',version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,original_function=884,original_signature=['i32','f64'],original_result=[],original_body_start=a,original_body_end=b,original_body_bytes=n,original_body_sha256=hashlib.sha256(raw[a:b]).hexdigest(),indexed_WAT_bytes=len(wat),indexed_WAT_sha256=hashlib.sha256(wat).hexdigest(),local_groups=groups,original_local_bytes=len(decl),prefix_start=locals_end,prefix_end=end,prefix_bytes=len(prefix),prefix_sha256=hashlib.sha256(prefix).hexdigest(),local_declaration_sha256=hashlib.sha256(decl).hexdigest(),instrumentation_tail_hex=tail.hex(),tail_only_get156_and_end=True,module_file=p.name,module_sha256=sha(p),imports=0,memory_pages=32,stack_initial=1048576,original_prefix_stack_subtraction=10704,full884_calls=0,original_function_entry_calls=0,builder_original_executions=0)
    save(out/'manifest.json',result);return result
