#!/usr/bin/env python3
"""Static137 Windows/WASM NPC declaration scalar/name correspondence only."""
from datetime import datetime,timezone
import struct,json
from build_combat137_oracle import ROOT,SOURCE,SOURCE_SHA,sha,save,PROFILE

def main():
    identity=json.loads((PROFILE/'binary-identity.json').read_text());raw=SOURCE.read_bytes();assert sha(SOURCE)==SOURCE_SHA
    native=SOURCE.parent/'windows-0.137.0/AzerothSurvivors.exe';exe=native.read_bytes();assert sha(native)=='aa6b254f905e2f7a4cbc7c2c8f11af822ec362e3d2b8e84cabd8c38893a10dc8'
    #Initial WASM memory holes are defined zero; this is static data overlay,
    #not materialization of unknown dynamically allocated record cells.
    initial=bytearray(max(s['address']+s['bytes']for s in identity['data_segments']if s['address']is not None))
    for s in identity['data_segments']:
        if s['address']is not None:initial[s['address']:s['address']+s['bytes']]=raw[s['file_offset']:s['file_offset']+s['bytes']]
    def memory(at,n):
        if not 0<=at<=at+n<=len(initial):raise ValueError('Static memory bounds')
        return bytes(initial[at:at+n])
    pe=struct.unpack_from('<I',exe,60)[0];assert exe[pe:pe+4]==b'PE\0\0';count=struct.unpack_from('<H',exe,pe+6)[0];size=struct.unpack_from('<H',exe,pe+20)[0]
    optional=pe+24;assert struct.unpack_from('<H',exe,optional)[0]==0x20b;image_base=struct.unpack_from('<Q',exe,optional+24)[0];sections=[]
    for i in range(count):
        p=optional+size+40*i;name=exe[p:p+8].split(b'\0')[0].decode();vs,rva,rs,fo=struct.unpack_from('<4I',exe,p+8);sections.append(dict(name=name,rva=rva,virtual_size=vs,file_offset=fo,raw_size=rs))
    def at_va(va,n):
        rva=va-image_base
        for s in sections:
            if s['rva']<=rva and rva+n<=s['rva']+s['raw_size']:return s['file_offset']+rva-s['rva']
        raise ValueError('PE virtual address outside mapped file')
    rows=[]
    for i in range(12):
        p=1625524+i*72;row=memory(p,72);name_ptr,length=struct.unpack_from('<II',row,16);name=memory(name_ptr,length)
        scalar=row[24:69];found=[];start=0
        while True:
            at=exe.find(scalar,start)
            if at<0:break
            found.append(at);start=at+1
        assert len(found)==1;at=found[0];ptr,n=struct.unpack_from('<QQ',exe,at-16);name_file=at_va(ptr,n);assert n==length and exe[name_file:name_file+n]==name
        section=next(s['name']for s in sections if s['file_offset']<=at and at+45<=s['file_offset']+s['raw_size'])
        rows.append(dict(index=i,wasm_pointer=p,wasm_stride=72,entry=struct.unpack_from('<I',row,24)[0],name=name.decode(),name_UTF8_hex=name.hex(),
            scalar_tail45_hex=scalar.hex(),native_scalar_file_offset=at,native_name_pointer=ptr,native_name_length=n,native_name_file_offset=name_file,section=section))
    strides=[b['native_scalar_file_offset']-a['native_scalar_file_offset']for a,b in zip(rows,rows[1:])]
    native_stride=strides[0]if len(set(strides))==1 else None
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('native0137-declaration-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    result=dict(version='0.137.0',build='d171b8f9f',wasm_sha256=SOURCE_SHA,native_sha256=sha(native),native_bytes=len(exe),
        native_executed=False,wasm_instantiated=False,rows=rows,adjacent_native_declaration_stride=native_stride,measured_adjacent_distances=strides,
        confirmed='12 exact45B scalar tails and borrowed UTF8 names; measured array spacing and32/64-bit name pointers only',
        not_confirmed=['Windows damage-function address/ABI','Windows gameplay Unit/Game size/field offsets','native damage/runtime equivalence'],
        producer_sha256=sha(ROOT/'scripts/trace_native137_declaration.py'))
    save(out/'correspondence.json',result);print(json.dumps(dict(directory=str(out),sha256=sha(out/'correspondence.json'),rows=len(rows),native_stride=native_stride,measured_adjacent_distances=strides,target_executed=False)))

if __name__=='__main__':main()
