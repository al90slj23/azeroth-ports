"""Static-only helpers for private fixed139 incoming research."""
from pathlib import Path
import hashlib,json,sqlite3,struct
from wasm139_profile import ROOT,SOURCE,SOURCE_SHA,Reader,binary_identity
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
def sha(path):
    with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def original():
    raw=SOURCE.read_bytes();assert len(raw)==92511151 and hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    identity,ranges=binary_identity(raw);assert not identity['implicit_start_section']and len(identity['imports'])==882
    return raw,identity,ranges
def signatures(raw,identity):
    sections={s['kind']:s for s in identity['sections']};s=sections[1];r=Reader(raw,s['payload_start'],s['end']);types=[]
    for _ in range(r.uint()):assert r.byte()==0x60;types.append((r.raw(r.uint()).hex(),r.raw(r.uint()).hex()))
    r.finish();s=sections[3];r=Reader(raw,s['payload_start'],s['end']);decl=[r.uint()for _ in range(r.uint())];r.finish()
    return {i+882:types[t]for i,t in enumerate(decl)}
def static_reader(raw,identity):
    ranges=[s for s in identity['data_segments']if s['address']is not None];proof={}
    def read(address,size):
        assert type(address)is int and 0<=address and 0<=size<=2*1024*1024;out=bytearray(size);used=[]
        for seg in ranges:
            p,n,start=seg['address'],seg['bytes'],seg['file_offset'];lo,hi=max(address,p),min(address+size,p+n)
            if lo<hi:out[lo-address:hi-address]=raw[start+lo-p:start+hi-p];used.append([lo,hi,start+lo-p,start+hi-p])
        value=bytes(out);proof[str(address)+':'+str(size)]=dict(bytes=size,sha256=hashlib.sha256(value).hexdigest(),file_intervals=used)
        return value
    read.proof=proof;return read
def function_proof(raw,identity,ranges,indices,out=None):
    sig=signatures(raw,identity);result={};texts={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
        for i in sorted(indices):
            row=dict(db.execute('select *from functions where idx=?',(i,)).fetchone());a,b,n=ranges[i];assert(a,b,n)==(row['body_start'],row['body_end'],row['body_bytes']);size=row['wat_end']-row['wat_start'];assert size<=16*1024*1024;stream.seek(row['wat_start']);text=stream.read(size);assert text.startswith(f'  (func (;{i};)'.encode())
            if out is not None:(Path(out)/f'{i}.wat').write_bytes(text)
            result[i]=dict(index=i,signature=sig[i],body_start=a,body_end=b,body_bytes=n,body_sha256=hashlib.sha256(raw[a:b]).hexdigest(),WAT_bytes=size,WAT_sha256=hashlib.sha256(text).hexdigest());texts[i]=text.decode()
    return result,texts
def unsigned(value):
    data=bytearray()
    while True:
        b=value&127;value>>=7;data.append(b|(128 if value else 0))
        if not value:return bytes(data)
def private_exports(raw,identity,additions):
    s=next(x for x in identity['sections']if x['kind']==7);r=Reader(raw,s['payload_start'],s['end']);count=r.uint();p=r.pos
    extra=[]
    for name,kind,index in additions:
        key=name.encode();extra.append(unsigned(len(key))+key+bytes([kind])+unsigned(index))
    payload=unsigned(count+len(extra))+raw[p:s['end']]+b''.join(extra)
    module=raw[:s['start']]+b'\x07'+unsigned(len(payload))+payload+raw[s['end']:];after,_=binary_identity(module)
    for a,b in zip(identity['sections'],after['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==module[b['start']:b['end']]
    expected=[(x['name'],x['kind'],x['index'])for x in identity['exports']]+additions
    assert[(x['name'],x['kind'],x['index'])for x in after['exports']]==expected
    return module
