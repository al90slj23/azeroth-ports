#!/usr/bin/env python3
"""Current139 Windows/WASM ability declarations; static bytes only.

Discover the native cleave row through PE-mapped string fat pointers, validate
the120B schema against all114 rows, and normalize addresses/field ordering.
This does not identify native gameplay functions, Game/Unit layout or behavior.
"""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,struct
from inspect_official_windows import PE
from review_combat139 import parse_module

ROOT=Path(__file__).resolve().parents[1]
ORIGINALS=ROOT/'originals/official-release-20261102T011227.335145Z'
NATIVE=ORIGINALS/'windows-0.139.0/AzerothSurvivors.exe'
WASM=ORIGINALS/'latest-wenilla_bg.wasm'
NATIVE_SHA='0e8e314df4d78ab211b1bef5c48d78d713ed64260894af342f998d298d74d274'
WASM_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(x).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()


def main():
    source_files=['scripts/trace_native139_ability_layout.py','scripts/inspect_official_windows.py','scripts/review_combat139.py'];before={n:sha(ROOT/n)for n in source_files}
    native=NATIVE.read_bytes();wasm=WASM.read_bytes();assert digest(native)==NATIVE_SHA and digest(wasm)==WASM_SHA and len(native)==150595584 and len(wasm)==92511151
    pe=PE(native);assert pe.bits==64 and pe.identity['machine_name']=='x86-64';module=parse_module(wasm)
    def memory(p,n):
        assert 0<=n<=65536 and 0<=p<=p+n<=module['minimum_memory_pages']*65536
        result=bytearray(n)
        for base,offset,size in module['data_segments']:
            if base is None:continue
            lo,hi=max(base,p),min(base+size,p+n)
            if lo<hi:result[lo-p:hi-p]=wasm[offset+lo-base:offset+hi-base]
        return bytes(result)
    def nslice(p,n):
        assert 0<=n<=65536
        if not n:return b''
        offset=pe.offset(p-pe.image_base,n);return native[offset:offset+n]
    def payload(row,is_native):
        pairs=[struct.unpack_from('<QQ'if is_native else'<II',row,o)for o in([0,16,32,48]if is_native else[12,20,28,36])]
        values=[(nslice if is_native else memory)(p,n)for p,n in pairs]
        return dict(identifier=values[0].decode(),default_display_name=values[1].decode(),icon_identifier=values[2].decode(),upgrade_kinds=list(values[3]),effect12_hex=(row[104:116]if is_native else row[:12]).hex(),numeric40_hex=(row[64:104]if is_native else row[44:84]).hex(),execution=row[117 if is_native else 84],school=row[116 if is_native else 85])
    wasm_rows=[memory(5882740+88*i,88)for i in range(114)];expected=[payload(r,False)for r in wasm_rows];assert expected[0]['identifier']=='cleave'and expected[0]['execution']==5
    strings=[];start=0;candidates=[]
    while True:
        at=native.find(b'cleave',start)
        if at<0:break
        start=at+1;assert len(strings)<512;strings.append(at)
        section=next((s for s in pe.sections if s['file_offset']<=at< s['file_offset']+s['raw_bytes']),None)
        if section is None:continue
        va=pe.image_base+section['rva']+at-section['file_offset'];needle=struct.pack('<QQ',va,6);cursor=0
        while True:
            q=native.find(needle,cursor)
            if q<0:break
            cursor=q+1
            if q+120>len(native):continue
            row=native[q:q+120]
            if row[117]!=5 or row[64:104]!=wasm_rows[0][44:84]:continue
            try:match=payload(row,True)==expected[0]
            except(AssertionError,ValueError,UnicodeDecodeError):match=False
            if match:candidates.append(dict(file_offset=q,string_file_offset=at,string_va=hex(va)))
    assert len(candidates)==1,candidates;base=candidates[0]['file_offset'];schema_trials=[];accepted=[]
    for stride in [112,120,128,136,144]:
        ok=0;reason=None
        for i in range(114):
            q=base+stride*i
            try:row=native[q:q+120];got=payload(row,True)
            except(AssertionError,ValueError,struct.error,UnicodeDecodeError)as error:reason=type(error).__name__;break
            if got!=expected[i]:reason='declaration_mismatch';break
            ok+=1
        schema_trials.append(dict(stride=stride,matching_prefix_rows=ok,stopped_because=reason))
        if ok==114:accepted.append(stride)
    assert accepted==[120],schema_trials
    actual=[];rows=[]
    for i,want in enumerate(expected):
        offset=base+120*i;row=native[offset:offset+120];got=payload(row,True);assert got==want;actual.append(got)
        section=next(s for s in pe.sections if s['file_offset']<=offset and offset+120<=s['file_offset']+s['raw_bytes']);va=pe.image_base+section['rva']+offset-section['file_offset']
        rows.append(dict(index=i,identifier=got['identifier'],wasm_memory_address=5882740+88*i,native_file_offset=offset,native_virtual_address=hex(va),section=section['name'],native120_sha256=digest(row),wasm88_sha256=digest(wasm_rows[i]),native_static_padding118_119=row[118:120].hex(),wasm_static_padding86_87=wasm_rows[i][86:88].hex(),normalized_sha256=digest(canonical(got)),normalized=got))
    normalized=digest(canonical(expected));assert normalized==digest(canonical(actual))and before=={n:sha(ROOT/n)for n in source_files}and sha(NATIVE)==NATIVE_SHA and sha(WASM)==WASM_SHA
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('native139-ability-layout-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    result=dict(status='static_declaration_correspondence_only',version='0.139.0',build='f79c5e2b4',native_sha256=NATIVE_SHA,wasm_sha256=WASM_SHA,native_bytes=len(native),wasm_bytes=len(wasm),PE=pe.identity,source_sha256_before=before,source_sha256_after=before,native_executed=False,wasm_instantiated=False,new_runtime_cases=0,rows=114,matched=114,normalized_sha256=normalized,literal_cleave_occurrences=len(strings),native_row_candidates=candidates,schema_trials=schema_trials,native_stride=120,wasm_stride=88,field_mapping=dict(id_fatptr=[0,12],display_fatptr=[16,20],icon_fatptr=[32,28],upgrade_kinds_fatptr=[48,36],numeric40=[64,44],effect12=[104,0],execution_byte=[117,84],school_byte=[116,85]),row_evidence=rows,limitations=['120Bnative/88BWASMlayoutisobservedstaticabilitydeclarationonly,notRustABIguaranteeforothertypes/builds.','Nativepointerwidth/orderandexec/schoolbyteorderaredifferent;addressesarenotcomparedasgameplayvalues.','ExactdatacorrespondencedoesnotidentifyWindowsdamage/castfunctions,nativeGame/Unit/ownedrecordlayoutorcallingconvention.','NoWindows/Wine/VMgameexecution,nodynamicbehavioralequivalence,norendering/UI/network/fullgameacceptance.','Typedstaticrowsarefresh139evidence,notoldversionacceptancetransfer.'])
    save(out/'correspondence.json',result);print(json.dumps(dict(out=str(out),receipt_sha256=sha(out/'correspondence.json'),matched=114,native_stride=120,normalized_sha256=normalized,new_runtime_cases=0)))


if __name__=='__main__':main()
