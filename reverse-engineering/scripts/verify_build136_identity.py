#!/usr/bin/env python3
"""Prove actual branding pointer/length in136 Web/native, plus135 Web alias.

No adjacent-byte or fixed-eight-hex regex inference is used. WAT stores and
native RIP-relative LEA/stack stores bind the consumed string and its length.
Neither target is executed. Existing acquisition/135 receipts remain untouched.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import sqlite3
import struct
import subprocess
from wasm135_profile import Reader

ROOT=Path(__file__).resolve().parents[1]
NEW_DIR=ROOT/'originals/official-acquisition-20261101T142725.754244Z'
NEW_PROFILE=ROOT/'evidence/wasm0136-profile-20261101T143713.272522Z'
OLD_DIR=ROOT/'originals/official-acquisition-20261101T030310.926207Z'
OLD_PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
NEW_SHA='48c3bce7d690b3be02973bde89903c385e21ef16deca23539dcef60a1eb2eef3'
OLD_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
EXE_SHA='eb744751b4e17ec1397b0cdc85a22af63b6af63c1da1d9c2861762c3c4d8947c'


def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def web(directory,profile,expected,version,out):
    raw=(directory/'latest-wenilla_bg.wasm').read_bytes();assert hashlib.sha256(raw).hexdigest()==expected
    top=Reader(raw,8);sections={}
    while top.pos<top.end:
        kind,size=top.byte(),top.uint();sections[kind]=(top.pos,top.pos+size);top.raw(size)
    version_file=raw.find(version.encode(),raw.find(b'Made by Aethus'),raw.find(b'Made by Aethus')+200)
    assert version_file>=0
    segment=None;t=Reader(raw,*sections[11])
    for index in range(t.uint()):
        flags=t.uint();assert flags in(0,1,2);address=None
        if flags!=1:
            if flags==2:t.uint()
            assert t.byte()==0x41;address=t.sint()&0xffffffff;assert t.byte()==0x0b
        length=t.uint();begin=t.pos;data=t.raw(length)
        if begin<=version_file<begin+length:
            segment=dict(index=index,address=address,file_offset=begin,bytes=length,payload=data)
    t.finish();assert segment
    version_pointer=segment['address']+version_file-segment['file_offset']
    con=sqlite3.connect((profile/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    refs=con.execute('select function_idx,value,wat_line from iconsts where operation="i32.const"and value>=?and value<?',
        (version_pointer-16,version_pointer)).fetchall();matches=[]
    wat=Path(json.loads((profile/'manifest.json').read_text())['wat_path'])
    with wat.open('rb')as stream:
        for function,pointer,wat_line in refs:
            begin,end=con.execute('select wat_start,wat_end from functions where idx=?',(function,)).fetchone()
            stream.seek(begin);source=stream.read(end-begin).decode();text='\n'.join(line.strip()for line in source.splitlines())
            pattern=(r'local.get (\d+)\ni32.const (\d+)\ni32.store offset=(\d+)\n'
                r'local.get \1\ni32.const '+str(pointer)+r'\ni32.store offset=(\d+)')
            for match in re.finditer(pattern,text):
                length=int(match[2]);length_field=int(match[3]);pointer_field=int(match[4])
                if length_field!=pointer_field+4 or pointer+length!=version_pointer:continue
                start=pointer-segment['address'];build=segment['payload'][start:start+length]
                assert re.fullmatch(rb'[0-9a-f]+',build)
                assert segment['payload'][version_pointer-segment['address']:version_pointer-segment['address']+len(version)]==version.encode()
                # Version's actual ptr/len7 pair is present in the same static
                # branding data; it is not part of the build's9B slice.
                descriptor=struct.pack('<II',version_pointer,len(version))
                assert descriptor in segment['payload']
                target=out/f'web-{version}-{function}.wat';target.write_text(source)
                matches.append(dict(version=version,build=build.decode(),build_length=length,
                    function=function,build_pointer=pointer,version_pointer=version_pointer,
                    length_store_offset=length_field,pointer_store_offset=pointer_field,
                    full_wat_line_of_build_pointer=wat_line,guard_instructions=match[0].splitlines(),
                    guard_first_function_line=text[:match.start()].count('\n')+1,
                    function_wat_file=target.name,function_wat_sha256=sha(target),
                    data_segment={k:v for k,v in segment.items()if k!='payload'},
                    build_file_offset=segment['file_offset']+start,
                    version_descriptor_hex=descriptor.hex(),original_sha256=expected))
    con.close();assert len(matches)==1
    return matches[0]


def native(directory,web_identity,out):
    path=directory/'windows-0.136.0/AzerothSurvivors.exe';raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==EXE_SHA
    pe=struct.unpack_from('<I',raw,0x3c)[0];assert raw[pe:pe+4]==b'PE\0\0'
    count=struct.unpack_from('<H',raw,pe+6)[0];optional_size=struct.unpack_from('<H',raw,pe+20)[0]
    optional=pe+24;assert struct.unpack_from('<H',raw,optional)[0]==0x20b
    image_base=struct.unpack_from('<Q',raw,optional+24)[0];sections=[]
    for index in range(count):
        p=optional+optional_size+index*40;name=raw[p:p+8].split(b'\0')[0].decode()
        virtual_size,rva,file_size,file_offset=struct.unpack_from('<4I',raw,p+8)
        sections.append(dict(name=name,rva=rva,virtual_size=virtual_size,file_size=file_size,file_offset=file_offset))
    needle=(web_identity['build']+web_identity['version']).encode();build_file=raw.find(needle)
    assert build_file>=0 and raw.find(needle,build_file+1)<0
    section=next(s for s in sections if s['file_offset']<=build_file<s['file_offset']+s['file_size'])
    pointer=image_base+section['rva']+build_file-section['file_offset']
    version_pointer=pointer+web_identity['build_length']
    descriptor=struct.pack('<QQ',version_pointer,len(web_identity['version']))
    assert raw[build_file+len(needle):build_file+len(needle)+16]==descriptor
    text=next(s for s in sections if s['name']=='.text');code=raw[text['file_offset']:text['file_offset']+text['file_size']]
    # lea rax,[rip+disp32]; mov[rbp+disp32],rax;
    # mov qword[rbp+disp32+8],imm32. Bind both destination and the explicit9.
    pattern=rb'\x48\x8d\x05(.{4})\x48\x89\x85(.{4})\x48\xc7\x85(.{4})(.{4})'
    matches=[]
    for match in re.finditer(pattern,code,re.S):
        instruction=image_base+text['rva']+match.start()
        target=instruction+7+struct.unpack('<i',match[1])[0]
        if target!=pointer:continue
        pfield=struct.unpack('<i',match[2])[0];lfield=struct.unpack('<i',match[3])[0];length=struct.unpack('<I',match[4])[0]
        assert lfield==pfield+8 and length==web_identity['build_length']==9
        matches.append(dict(instruction_va=hex(instruction),instruction_file_offset=text['file_offset']+match.start(),
            pointer=hex(pointer),pointer_stack_offset=pfield,length_stack_offset=lfield,length=length,
            exact_instruction_bytes_hex=match[0].hex()))
    assert len(matches)==1
    start=int(matches[0]['instruction_va'],16);command=['/usr/bin/objdump','--disassemble',
        '--start-address='+hex(start),'--stop-address='+hex(start+50),str(path)]
    result=subprocess.run(command,capture_output=True,timeout=20);assert result.returncode==0
    target=out/'native-build-consumer.disassembly.txt';target.write_bytes(result.stdout+result.stderr)
    return dict(version=web_identity['version'],build=web_identity['build'],build_length=9,
        exe_sha256=EXE_SHA,exe_bytes=len(raw),image_base=hex(image_base),build_file_offset=build_file,
        build_pointer=hex(pointer),version_pointer=hex(version_pointer),version_descriptor_hex=descriptor.hex(),
        instruction_guard=matches[0],disassembly_command=command,disassembly_exit_code=result.returncode,
        disassembly_file=target.name,disassembly_sha256=sha(target),target_executed=False)


def main():
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('branding0136-identity-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    current=web(NEW_DIR,NEW_PROFILE,NEW_SHA,'0.136.0',out)
    previous=web(OLD_DIR,OLD_PROFILE,OLD_SHA,'0.135.1',out)
    windows=native(NEW_DIR,current,out)
    report=dict(kind='actual_consumed_build_string_identity',new_web=current,new_native=windows,old_web=previous,
        new_native_web_same_version_build_and_length=True,new_build='fe24fb74c',new_build_length=9,
        legacy135_historical_alias='0898d5e3',legacy135_actual_consumed_web_build=previous['build'],
        legacy135_actual_consumed_web_build_length=previous['build_length'],
        old_receipts_or_acquisition_overwritten=False,script_sha256=sha(Path(__file__)),
        old_acceptance_relabelled=False,new_acceptance_transferred=False,targets_executed=False)
    target=out/'identity.json';target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),identity_sha256=sha(target),new_build=current['build'],
        new_length=current['build_length'],old_consumed_web_build=previous['build'],targets_executed=False)))


if __name__=='__main__':main()
