#!/usr/bin/env python3
"""Pin139 world-query ABI/layout and compare complete mathematical WAT bodies.

No target is instantiated. Only function/type/callee identities and three
explicit panic-location pointers may differ in the successful-query reuse
proof. Diagnostic panic text is not claimed equivalent.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,sqlite3,struct,sys
from wasm139_profile import ROOT,SOURCE,SOURCE_SHA,binary_identity
from wasm135_profile import binary_identity as binary_identity135

OLD=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
OLD_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILES={135:ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z',
          139:ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'}
WATS={135:'official-0.135.1-full.wat',139:'official-0.139.0-full.wat'}
PAIRS=((29631,29912),(18670,18742),(46295,47025),(5795,5787),(23181,23333))
CALLS=dict(PAIRS)|{80663:81897}
PANICS={(29631,81):(5512528,5762524),(29631,193):(5508976,5762404),
        (23181,203):(5512672,5762668)}


def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def main():
    before=sha(Path(__file__));assert sha(OLD)==OLD_SHA and sha(SOURCE)==SOURCE_SHA
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world139-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    sources={135:OLD.read_bytes(),139:SOURCE.read_bytes()};identities={};ranges={};functions={};texts={}
    for version in(135,139):
        identities[version],ranges[version]=(binary_identity135 if version==135 else binary_identity)(sources[version])
        indices=[pair[version==139]for pair in PAIRS]
        with sqlite3.connect((PROFILES[version]/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILES[version]/WATS[version]).open('rb')as stream:
            db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
            for index in indices:
                row=dict(db.execute('select *from functions where idx=?',(index,)).fetchone())
                assert(row['body_start'],row['body_end'])==ranges[version][index][:2]
                stream.seek(row['wat_start']);wat=stream.read(row['wat_end']-row['wat_start']);(out/f'{version}-{index}.wat').write_bytes(wat)
                functions[version,index]=dict(index=index,body_start=row['body_start'],body_end=row['body_end'],body_sha256=hashlib.sha256(sources[version][row['body_start']:row['body_end']]).hexdigest(),wat_sha256=hashlib.sha256(wat).hexdigest(),direct_callees=[tuple(z)for z in db.execute('select callee,count(*) from calls where caller=? group by callee',(index,))])
                texts[version,index]=wat.decode().splitlines()
    proofs=[]
    for old,new in PAIRS:
        a=texts[135,old];b=texts[139,new];assert len(a)==len(b),(old,new)
        substitutions=[]
        for line,(x,y)in enumerate(zip(a,b),1):
            if x==y:continue
            if line==1:
                nx=re.sub(r'\(;\d+;\) \(type \d+\)','(;FUNCTION;) (type TYPE)',x)
                ny=re.sub(r'\(;\d+;\) \(type \d+\)','(;FUNCTION;) (type TYPE)',y)
                assert nx==ny;reason='function_and_type_identity_same_full_signature'
            elif re.fullmatch(r'\s*call \d+',x):
                p,q=int(x.split()[-1]),int(y.split()[-1]);assert CALLS[p]==q;reason='exact_bound_callee'
            elif(old,line)in PANICS:
                p,q=PANICS[old,line];assert x.strip()==f'i32.const {p}'and y.strip()==f'i32.const {q}'
                assert a[line].strip()=='call 80663'and b[line].strip()=='call 81897';reason='explicit_panic_location_pointer_before_same_bounds_panic'
            else:raise AssertionError((old,new,line,x,y))
            substitutions.append(dict(line=line,old=x.strip(),new=y.strip(),reason=reason))
        proofs.append(dict(old=old,new=new,lines=len(a),all_other_lines_exact=True,substitutions=substitutions))
    raw=sources[139];identity=identities[139]
    def data(address,n):
        value=bytearray(n);coverage=bytearray(n)
        # Active data segments may split one static row around zero runs.
        # WASM initial memory is genuinely zero-initialized; these are not
        # allocator-unwritten runtime bytes or values learned from a snapshot.
        assert address+n<=max(s['address']+s['bytes']for s in identity['data_segments']if s['address']is not None)
        for segment in identity['data_segments']:
            start=segment['address']
            if start is None:continue
            lo,hi=max(address,start),min(address+n,start+segment['bytes'])
            if lo<hi:
                off=segment['file_offset']+lo-start;value[lo-address:hi-address]=raw[off:off+hi-lo];coverage[lo-address:hi-address]=b'\x01'*(hi-lo)
        return bytes(value),bytes(coverage)
    zone,zone_coverage=data(5871348,152);config=dict(map_id=struct.unpack_from('<I',zone,96)[0],center_xy_bits=list(struct.unpack_from('<2I',zone,104)),fallback_height_bits=struct.unpack_from('<I',zone,112)[0],radius_bits=struct.unpack_from('<I',zone,120)[0])
    assert config==dict(map_id=0,center_xy_bits=[3323121664,3290316800],fallback_height_bits=0x42880000,radius_bits=0x42f00000)
    result=dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,old_static_reference_sha256=OLD_SHA,original_executions=0,
        functions={str(v)+':'+str(i):x for(v,i),x in functions.items()},whole_WAT_proofs=proofs,source_zone152=dict(address=5871348,raw_hex=zone.hex(),sha256=hashlib.sha256(zone).hexdigest(),config=config,active_segment_mask_hex=zone_coverage.hex(),WASM_zero_initialized_bytes=zone_coverage.count(0)),
        Rc_contract=['29912/18742 receive realWorldRc+8; Rc124 active tiles cap/ptr/count at8/12/16 and bounds at20/24/28.',
            'Terrain tiles36 use active chunks264 with vertex cap/ptr/count at0/4/8,145 XYZ12 vertices,holes u16 at260.',
            'Primary tag/pointer/count/originXY/width atRc56/72/76/80/84/88;secondary at92/96/100/104/108/112.',
            'Fallback f32 atRc116 andflat flagbyte120; nearest23333 receives the primary-style36B descriptor.'],
        limits=['Successful-query mathematical identity only;panic file/line diagnostic contents not proved equivalent.','135 dynamic acceptance not transferred;139world producer buffers and query behavior still need new139 validation.','Inline nav consumer and all other world/model/render/cache behaviors are outside these five functions.'],script_sha256=before)
    save(out/'trace.json',result);assert sha(Path(__file__))==before
    print(json.dumps(dict(directory=str(out),trace_sha256=sha(out/'trace.json'),functions=10,whole_function_pairs=5,original_executions=0)),flush=True)


if __name__=='__main__':main()
