#!/usr/bin/env python3
"""139 full5719/1586/source declarations, bounded static proof, no target."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,sqlite3,struct
from wasm139_profile import ROOT,SOURCE,SOURCE_SHA,binary_identity
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
FUNCTIONS=(5719,1586,21552,97427,6440,66565,43076,51773,10804,24602,35202)
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 before=sha(Path(__file__));raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA;identity,ranges=binary_identity(raw)
 segs=[s for s in identity['data_segments']if s['address']is not None];mem=bytearray(max(s['address']+s['bytes']for s in segs))
 for s in segs:mem[s['address']:s['address']+s['bytes']]=raw[s['file_offset']:s['file_offset']+s['bytes']]
 u=lambda p:struct.unpack_from('<I',mem,p)[0];zone=5871348;pointer=u(zone+64);assert pointer==5830904 and u(zone+68)==12
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('npc-spawn139-static-%Y%m%dT%H%M%S.%fZ');out.mkdir();funcs={};total=0
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as f:
  db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
  for index in FUNCTIONS:
   row=dict(db.execute('select *from functions where idx=?',(index,)).fetchone());a,b,_=ranges[index];assert(a,b)==(row['body_start'],row['body_end']);n=row['wat_end']-row['wat_start'];assert n<=1048576 and total+n<=4194304;total+=n;f.seek(row['wat_start']);wat=f.read(n);(out/f'{index}.wat').write_bytes(wat)
   funcs[str(index)]=dict(**row,body_sha256=hashlib.sha256(raw[a:b]).hexdigest(),wat_sha256=hashlib.sha256(wat).hexdigest(),signature=wat.decode().splitlines()[0].strip(),direct_calls=[dict(x)for x in db.execute('select *from calls where caller=?order by wat_offset',(index,))])
 text=(out/'5719.wat').read_text();assert funcs['5719']['body_sha256']=='8035b0969dab682144a748cb3b535602f50600763e83dadfcb4e62d45d3e3ed5'
 assert 'i32.const 432'in text and 'i64.store offset=416'in text and 'i32.store8 offset=424'in text and 'i32.store16 offset=425'in text
 assert not re.search(r'local\.(?:set|tee) 0(?:\s|$)',text)
 assert text.count('local.get 0')==2 # outputcursor retainedunderouterblock plusGUIDstore8
 proof=dict(version='0.139.0',build='f79c5e2b4',source_wasm_sha256=SOURCE_SHA,script_sha256=before,functions=funcs,read_WAT_bytes=total,
  declaration=dict(zone_pointer=zone,raw_zone152_hex=bytes(mem[zone:zone+152]).hex(),normal_pointer=pointer,normal_count=u(zone+68),zone136_scaling_bits=u(zone+136),zone140_late_bits=u(zone+140),first72_hex=bytes(mem[pointer:pointer+72]).hex(),name=bytes(mem[u(pointer+16):u(pointer+16)+u(pointer+20)]).decode(),entry=u(pointer+24),display=u(pointer+28),classification68=mem[pointer+68]),
  admitted_domain=dict(zone='elwynn',definition_index=0,time2352=0,mode2582=0,difficulty387=0,members2540=1,victory400=0,endless2568=0,player_GUID=0,level1432=1,position='SomeXYZ/finiteXY; no8740sampling',existing_states='0..3 records eachmarker0'),
  heading_tables={str(p):[hex(x)for x in struct.unpack_from('<4I',mem,p)]for p in(14426512,14426528,14426544,14426560)},
  NPC_record432_written_ranges=[[0,4],[8,4],[16,4],[40,4],[64,4],[112,136],[280,147]],unwritten_bytes_per_fresh_row=129,
  minimum_result_bytes16='5719 writesi64resulttagat0 andGUIDat8; param0neverrebound andnotforwardedtoopaqueproducer. FullWAT retained.',
  target_executions=0,production_executions=0,old_acceptance_transferred=False,old_snapshot_loaded=False,
  limitations=['Only fixed initial numeric/defaultNPC andSomeXYZ finiteXY runtime domain is admitted.','Nonzero time/scaling/difficulty/mode/endless andnonzero existingmarkers are notdynamicacceptance.','This is notnaturalposition/full1108/worldRc production.'])
 p=out/'proof.json';p.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');assert before==sha(Path(__file__));print(json.dumps(dict(directory=str(out),proof_sha256=sha(p),functions=len(funcs),read_WAT_bytes=total)),flush=True)
if __name__=='__main__':main()
