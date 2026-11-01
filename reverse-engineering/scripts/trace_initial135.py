#!/usr/bin/env python3
"""Read pinned initial data/function evidence; never execute the game."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sqlite3,struct
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source


def extract():
 binary=SOURCE.read_bytes();assert hashlib.sha256(binary).hexdigest()==SOURCE_SHA
 segments=parse_source(binary)[4];memory=bytearray(max(s['address']+s['length']for s in segments if s['address']is not None))
 for s in segments:
  if s['address']is not None:memory[s['address']:s['address']+s['length']]=binary[s['file_offset']:s['file_offset']+s['length']]
 u=lambda p:struct.unpack_from('<I',memory,p)[0]
 ident=lambda p,n:bytes(memory[p:p+n]).decode('ascii')
 definitions={ident(u(5467428+j*88+12),u(5467428+j*88+16)):5467428+j*88 for j in range(114)}
 classes=[];races=[];zones=[]
 for cls in (1,2,3,4,5,7,8,9,11):
  p=u(1595888+4*(cls-2))if cls>=2 else 5462608;aid=ident(u(p+40),u(p+44))
  classes.append(dict(class_byte=cls,table_pointer=p,starter_id=aid,starter_definition=definitions[aid],hp_bits=u(p+72),raw88_hex=bytes(memory[p:p+88]).hex()))
 for race in range(1,9):
  p=u(1595728+4*(race-2))if race>=2 else 5459304;aid=ident(u(p+24),u(p+28));dp=definitions[aid]
  races.append(dict(race_byte=race,table_pointer=p,racial_id=aid,racial_definition=dp,execution_kind=memory[dp+84],effect_tag=u(dp),raw44_hex=bytes(memory[p:p+44]).hex()))
 for j in range(12):
  p=5456016+j*152;zones.append(dict(index=j,identifier=ident(u(p+8),u(p+12)),x_bits=u(p+104),y_bits=u(p+108),field116_bits=u(p+116),raw152_hex=bytes(memory[p:p+152]).hex()))
 return dict(version='0.135.1',build='0898d5e3',wasm_sha256=SOURCE_SHA,classes=classes,races=races,zones=zones)


def main():
 result=extract();out=ROOT/'evidence'/('initial135-data-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'));out.mkdir()
 (out/'initial-data.json').write_text(json.dumps(result,indent=2)+'\n')
 profile=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z';db=sqlite3.connect('file:'+str(profile/'index.sqlite')+'?mode=ro',uri=True);functions=[]
 with(profile/'official-0.135.1-full.wat').open('rb')as f,SOURCE.open('rb')as wasm:
  for index in (1560,25765,10319,9480,18669,6730,2080,1089):
   wa,wz,a,z,line=db.execute('select wat_start,wat_end,body_start,body_end,wat_line from functions where idx=?',(index,)).fetchone();f.seek(wa);wat=f.read(wz-wa);wasm.seek(a);body=wasm.read(z-a)
   (out/(str(index)+'.wat')).write_bytes(wat);functions.append(dict(index=index,wat_start=wa,wat_end=wz,wat_line=line,wat_sha256=hashlib.sha256(wat).hexdigest(),body_sha256=hashlib.sha256(body).hexdigest(),callees=[x[0]for x in db.execute('select distinct callee from calls where caller=?',(index,))]))
 (out/'functions.json').write_text(json.dumps(functions,indent=2)+'\n');print(json.dumps(dict(directory=str(out),classes=len(result['classes']),races=len(result['races']),zones=len(result['zones']),target_executed=False)))
if __name__=='__main__':main()
