#!/usr/bin/env python3
"""Bounded fixed138 default constructor data/layout extraction; no execution."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,sqlite3,struct
from wasm138_profile import ROOT,SOURCE,SOURCE_SHA,binary_identity
from wasm135_profile import binary_identity as identity135

PROFILE=ROOT/'evidence/wasm0138-profile-20261101T202038.814151Z'
OLD_SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
OLD_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
NATIVE=SOURCE.parent/'windows-0.138.0/AzerothSurvivors.exe'
NATIVE_SHA='eb5fd1c1b96e6180fcf5f3d685d90a61471af28d22e5f060c02b7b7663fbf79e'


def sha(path):
    with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()


def extract(raw,identity,version):
    memory=bytearray(max(s['address']+s['bytes']for s in identity['data_segments']if s['address']is not None))
    for s in identity['data_segments']:
        if s['address']is not None:memory[s['address']:s['address']+s['bytes']]=raw[s['file_offset']:s['file_offset']+s['bytes']]
    def read(p,n):
        assert 0<=p<=p+n<=len(memory)
        return bytes(memory[p:p+n])
    u=lambda p:struct.unpack('<I',read(p,4))[0]
    text=lambda p,n:read(p,n).decode('ascii')
    default,table,rdefault,rtable,definitions,zones=(1673176,1597616,1669892,1597456,1677996,1666604)if version==138 else(5462608,1595888,5459304,1595728,5467428,5456016)
    abilities={text(u(definitions+j*88+12),u(definitions+j*88+16)):definitions+j*88 for j in range(114)}
    classes=[];races=[];regions=[]
    for cls in(1,2,3,4,5,7,8,9,11):
        p=u(table+4*(cls-2))if cls>=2 else default;name=text(u(p+40),u(p+44));definition=abilities[name]
        numeric=read(p+72,8)
        classes.append(dict(class_byte=cls,pointer=p,starter_id=name,definition_pointer=definition,hp_bits=u(p+72),armor_bits=u(p+76),
            raw88_hex=read(p,88).hex(),raw88_sha256=hashlib.sha256(read(p,88)).hexdigest(),scalar8_hex=numeric.hex(),scalar8_sha256=hashlib.sha256(numeric).hexdigest(),
            definition88_hex=read(definition,88).hex(),definition88_sha256=hashlib.sha256(read(definition,88)).hexdigest()))
    for race in range(1,9):
        p=u(rtable+4*(race-2))if race>=2 else rdefault;name=text(u(p+24),u(p+28));definition=abilities[name]
        races.append(dict(race_byte=race,pointer=p,racial_id=name,definition_pointer=definition,effect_tag=u(definition),execution_kind=read(definition+84,1)[0],
            raw44_hex=read(p,44).hex(),raw44_sha256=hashlib.sha256(read(p,44)).hexdigest(),definition88_hex=read(definition,88).hex(),definition88_sha256=hashlib.sha256(read(definition,88)).hexdigest()))
    for index in range(12):
        p=zones+index*152;name=text(u(p+8),u(p+12));scalar=read(p+104,16)
        regions.append(dict(index=index,pointer=p,identifier=name,x_bits=u(p+104),y_bits=u(p+108),field116_bits=u(p+116),
            raw152_hex=read(p,152).hex(),raw152_sha256=hashlib.sha256(read(p,152)).hexdigest(),position16_hex=scalar.hex(),position16_sha256=hashlib.sha256(scalar).hexdigest()))
    return dict(version=version,classes=classes,races=races,zones=regions)


def main():
    source_before=sha(Path(__file__));assert sha(SOURCE)==SOURCE_SHA and sha(OLD_SOURCE)==OLD_SHA and sha(NATIVE)==NATIVE_SHA
    raw=SOURCE.read_bytes();identity,ranges=binary_identity(raw);oldraw=OLD_SOURCE.read_bytes();oldidentity,_=identity135(oldraw)
    fresh=extract(raw,identity,138);old=extract(oldraw,oldidentity,135)
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('initial138-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    native=NATIVE.read_bytes()
    def matches(pattern):
        result=[];at=0
        while True:
            at=native.find(pattern,at)
            if at<0:break
            result.append(at);at+=1
            if len(result)>32:break
        return result
    equal=[];references=[]
    for label,fields in(('classes',('starter_id','hp_bits','armor_bits')),('races',('racial_id','effect_tag','execution_kind')),('zones',('identifier','x_bits','y_bits','field116_bits'))):
        for i,(a,b)in enumerate(zip(old[label],fresh[label])):
            selected_old={k:a[k]for k in fields};selected_new={k:b[k]for k in fields}
            oldbytes=json.dumps(selected_old,sort_keys=True,separators=(',',':')).encode();newbytes=json.dumps(selected_new,sort_keys=True,separators=(',',':')).encode()
            record_key={'classes':'raw88_hex','races':'raw44_hex','zones':'raw152_hex'}[label]
            equal.append(dict(domain=label,index=i,fields=list(fields),old=selected_old,new=selected_new,equal=selected_old==selected_new,
                old_semantic_sha256=hashlib.sha256(oldbytes).hexdigest(),new_semantic_sha256=hashlib.sha256(newbytes).hexdigest(),
                full_record_bytes_equal=a[record_key]==b[record_key]))
    for item in fresh['classes']:
        references.append(dict(domain='classHPArmor',class_byte=item['class_byte'],pattern_hex=item['scalar8_hex'],matches=matches(bytes.fromhex(item['scalar8_hex']))))
    for item in fresh['zones']:
        pattern=struct.pack('<II',item['x_bits'],item['y_bits'])
        references.append(dict(domain='zoneXY8',zone=item['identifier'],pattern_hex=pattern.hex(),matches=matches(pattern)))
    functions=[]
    with sqlite3.connect(PROFILE.resolve().as_uri()+'/index.sqlite?mode=ro',uri=True)as con,(PROFILE/'official-0.138.0-full.wat').open('rb')as stream:
        con.row_factory=sqlite3.Row;con.execute('pragma query_only=on')
        for index in(1571,25794,10287,9440,29649,23171):
            row=dict(con.execute('select *from functions where idx=?',(index,)).fetchone());assert ranges[index][:2]==(row['body_start'],row['body_end'])
            stream.seek(row['wat_start']);wat=stream.read(row['wat_end']-row['wat_start']);assert wat.startswith(f'  (func (;{index};)'.encode())
            (out/f'{index}.wat').write_bytes(wat);(out/f'{index}.compact.txt').write_text('\n'.join(f'{j+1}: {line.strip()}'for j,line in enumerate(wat.decode().splitlines()))+'\n')
            functions.append(dict(index=index,**row,body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest(),wat_sha256=hashlib.sha256(wat).hexdigest(),
                callees=[dict(x)for x in con.execute('select callee,count(*) sites from calls where caller=?group by callee',(index,))]))
    report=dict(version='0.138.0',actual_build='382771e6c',original_wasm_sha256=SOURCE_SHA,old_wasm_sha256=OLD_SHA,script_sha256=source_before,
        fresh=fresh,old=old,semantic_field_equality=equal,windows_reference=dict(exe_sha256=NATIVE_SHA,patterns=references,executed=False,scope='Static numeric bytes only,not native ABI or Windows gameplay'),
        functions=functions,original_executed=False,old_acceptance_transferred=False,full_WAT_scanned=False)
    path=out/'initial-data.json';path.write_text(json.dumps(report,indent=2)+'\n');assert sha(Path(__file__))==source_before
    print(json.dumps(dict(directory=str(out),sha256=sha(path),semantic_equal=sum(x['equal']for x in equal),semantic_rows=len(equal),functions=len(functions),original_executed=False)))


if __name__=='__main__':main()
