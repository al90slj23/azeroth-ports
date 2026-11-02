#!/usr/bin/env python3
"""1398740/13563/rng/trig/staticzone bindings; bounded reads, no target."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sqlite3,struct
from wasm139_profile import ROOT,SOURCE,SOURCE_SHA,binary_identity
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
FUNCTIONS=(8740,13563,11425,11499,33028,50441,43076,35202)
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 before=sha(Path(__file__));raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA;identity,ranges=binary_identity(raw);segments=[s for s in identity['data_segments']if s['address']is not None];mem=bytearray(max(s['address']+s['bytes']for s in segments))
 for s in segments:mem[s['address']:s['address']+s['bytes']]=raw[s['file_offset']:s['file_offset']+s['bytes']]
 zones=[]
 for j in range(12):
  p=5871348+j*152;row=bytes(mem[p:p+152]);u=lambda o:struct.unpack_from('<I',row,o)[0];name=bytes(mem[u(8):u(8)+u(12)]).decode();zones.append(dict(index=j,pointer=p,identifier=name,x_bits=u(104),y_bits=u(108),radius_bits=u(120),fallback_bits=u(112),raw152_hex=row.hex()))
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-position139-static-%Y%m%dT%H%M%S.%fZ');out.mkdir();functions={};total=0;texts={}
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as w:
  db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
  for index in FUNCTIONS:
   row=dict(db.execute('select *from functions where idx=?',(index,)).fetchone());a,b,_=ranges[index];assert(a,b)==(row['body_start'],row['body_end']);n=row['wat_end']-row['wat_start'];assert n<=1048576 and total+n<=4194304;total+=n;w.seek(row['wat_start']);wat=w.read(n);(out/f'{index}.wat').write_bytes(wat);texts[index]=wat.decode()
   functions[str(index)]=dict(**row,body_sha256=hashlib.sha256(raw[a:b]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest(),signature=texts[index].splitlines()[0].strip(),direct_calls=[dict(x)for x in db.execute('select *from calls where caller=?order by wat_offset',(index,))])
 assert all(x in texts[8740]for x in('f32.load offset=1736','f32.load offset=1740','i32.load offset=2368','call 13563','i32.const 16','f32.load offset=5871468','call 43076','call 11425','call 11499','call 29912'))
 content='"""Fresh1398740 zone literal consumers; runtime hasnooriginal IO."""\nSOURCE_WASM_SHA256='+repr(SOURCE_SHA)+'\nZONE_GEOMETRY139='+repr(tuple((x['x_bits'],x['y_bits'],x['radius_bits'])for x in zones))+'\n'
 data=ROOT/'reconstruction/core_spec/world_position139_data.py'
 if data.exists():assert data.read_text()==content
 else:data.write_text(content)
 proof=dict(version='0.139.0',build='f79c5e2b4',source_wasm_sha256=SOURCE_SHA,script_sha256=before,functions=functions,zones=zones,read_WAT_bytes=total,
  scalar_contract=dict(playerXYZ=[1416,1420,1424],smoothVelocityXY=[1736,1740],rng=[1720,1724,1728,1732],worldRc=2348,distance_view=2368,worldInnerDelta=8,NPCtrials=16,radiusShrink_bits=0xc0000000,minRadius_bits=0x41400000,randomFallbackTrials=13),
  production_data_module=str(data.relative_to(ROOT)),production_data_sha256=sha(data),target_executions=0,old_acceptance_transferred=False,old_snapshot_loaded=False,
  boundaries=['Only matching139Elwynn realworld is dynamicallyadmitted;12zone declarations arestatic data.','World is anexplicit independentcanonical input; production model cannotreadoriginalmemory.','Original snapshot belongs only to target runner; only healthyv2 is admitted.'])
 p=out/'proof.json';p.write_text(json.dumps(proof,indent=2)+'\n');assert before==sha(Path(__file__));print(json.dumps(dict(directory=str(out),proof_sha256=sha(p),functions=len(functions),read_WAT_bytes=total,entries={k:functions[k]['body_sha256']for k in('8740','13563')})),flush=True)
if __name__=='__main__':main()
