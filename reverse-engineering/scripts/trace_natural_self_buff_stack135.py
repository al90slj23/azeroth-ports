#!/usr/bin/env python3
"""Bounded read-only provenance investigation of922's physical auxiliary word.

No original/model execution. This records proven frame/branch facts and an
unresolved last writer; raw evidence is used to falsify constant hypotheses,
never fed into an independent model. Partial CAS reading is not a full audit.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,gzip,hashlib,json,re,sqlite3,struct,sys
sys.dont_write_bytecode=True
from opening_combat135_cas import CaptureCAS135
ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
CAPTURE=ROOT/'evidence/opening-combat0135-oracle-20261101T223938.000541Z'
SNAPSHOT=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_begin1089.memory'
INDICES=(2088,1076,922,947,8751,5736,2376,49037,26366,41561,27562,1453,921,13516,29631,49503,11428,11503,18670,46295,5795)

def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
 out=args.output.resolve()if args.output else ROOT/'evidence'/datetime.now(timezone.utc).strftime('natural-self-buff-stack135-static-%Y%m%dT%H%M%S.%fZ');assert out.is_relative_to((ROOT/'evidence').resolve());out.mkdir()
 static=[];texts={}
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
  db.execute('pragma query_only=on')
  for idx in INDICES:
   lo,hi,bs,be=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(idx,)).fetchone();assert hi-lo<1000000;wat.seek(lo);b=wat.read(hi-lo);(out/(str(idx)+'.wat')).write_bytes(b);texts[idx]=b.decode();static.append(dict(index=idx,wat_start=lo,wat_end=hi,wat_bytes=hi-lo,wat_sha256=hashlib.sha256(b).hexdigest(),body_start=bs,body_end=be))
 frames={2088:96,1076:208,922:240,947:336,8751:16,921:592,1453:1840}
 for idx,n in frames.items():
  assert re.search(r'global.get 0\s+i32.const '+str(n)+r'\s+i32.sub',texts[idx])
 assert 'local.get 0\n      local.get 1\n      call 1076'in texts[2088]
 assert texts[1076].count('call 922')>=1
 lines=texts[922].splitlines();assert 'i32.load offset=48' in lines[5983]
 start=next(i for i,line in enumerate(lines)if line.strip()=='i32.const 8'and i>5735)
 branch8='\n'.join(lines[start-1:start+10]);assert 'i32.store offset=40'in branch8 and'f32.store offset=44'in branch8 and'offset=48'not in branch8
 start9=next(i for i,line in enumerate(lines)if line.strip()=='i32.const 9'and i>start)
 branch9='\n'.join(lines[start9-1:start9+10]);assert 'i32.store offset=40'in branch9 and'f32.store offset=44'in branch9 and'offset=48'not in branch9
 default='\n'.join(lines[5809:5818]);assert'i32.load offset=8'in default and'i32.store offset=48'in default
 #This branch statement is local, not proof that an arbitrary callee never
 #writes memory: write coverage outside the admitted path remains unresolved.
 decoder=CaptureCAS135(CAPTURE);selected=[]
 with gzip.open(CAPTURE/'results.cas.jsonl.gz','rb')as stream:
  for line in stream:
   raw=decoder.decode_line(line)
   if raw['record_kind']=='stage'and raw['stage_index']in(69,70):selected.append(raw)
   if raw['record_kind']=='stage'and raw['stage_index']>=70:break
 assert len(selected)==2 and all(x['stack']==1048576 for x in selected)
 before,after=selected;assert before['kind']=='terminal'and after['kind']=='player'
 assert before['vectors']['live32']['count']==0 and after['vectors']['live32']['count']==1
 live=bytes.fromhex(after['vectors']['live32']['storage'][0]);assert len(live)==32
 kind,aux,spell=struct.unpack_from('<I',live,8)[0],struct.unpack_from('<I',live,16)[0],struct.unpack_from('<I',live,20)[0]
 assert(kind,spell,aux)==(8,20600,0x4289add5)
 address=1048576-frames[2088]-frames[1076]-frames[922]+48
 with SNAPSHOT.open('rb')as f:f.seek(address);snapshot_word=int.from_bytes(f.read(4),'little')
 assert snapshot_word==0x4280a5d6 and snapshot_word!=aux
 value=struct.pack('<I',aux);occurrences=[]
 for name,q in before['vectors'].items():
  for slot,row in enumerate(q.get('storage',[])):
   if not isinstance(row,str):continue
   data=bytes.fromhex(row)
   for off in range(len(data)-3):
    if data[off:off+4]==value:occurrences.append(dict(vector=name,slot=slot,offset=off))
 assert not occurrences and before['projection']['player_xyz'][2]!=aux
 save(out/'local-branch-proofs.json',dict(effect8_lines=branch8,effect9_lines=branch9,default_lines=default,append_lines='\n'.join(lines[5976:5987])))
 observations=[dict(stage_index=x['stage_index'],kind=x['kind'],stack=x['stack'],now_bits=x['projection']['now_bits'],live=x['vectors']['live32'],player_xyz=x['projection']['player_xyz'])for x in selected]
 save(out/'early-original-observations.json',observations)
 result=dict(status='partial_provenance_last_writer_unresolved',version='0.135.1',actual_build='90898d5e3',static_functions=static,wat_bytes_read=sum(v['wat_bytes']for v in static),
 frame_bytes=frames,proven_live16_expression='load_u32(rootSP-96-208-240+48)',rootSP=1048576,absolute_address=address,
 branch_fact='effect8/9 writes scratch40/44 but not48; default definition+8 write is a different branch. live+16 is nevertheless written from scratch48.',
 raw_observation=dict(capture=str(CAPTURE),comparison_sha256=sha(CAPTURE/'comparison.json'),comparison_has_gameplay_differences=load(CAPTURE/'comparison.json')['differences'],stage_before=69,stage_after=70,spell_id=spell,live_kind=kind,observed_auxiliary_word=aux,observed_auxiliary_float=struct.unpack('<f',value)[0],
 prior_vector_backing_contains_observed_word=False,player_z_is_observed_word=False,partial_CAS_read_only=True,complete_CAS_finish_claimed=False),
 snapshot_counterexample=dict(path=str(SNAPSHOT),known_expected_sha256='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf',read_offset=address,word=snapshot_word,observed_word_different=True,whole_snapshot_hash_rechecked_in_this_script=False),
 next_observation='Add readonly4B read of rootSP-496 before/after constructor/opening and each unchanged original stage. First establish actual writing phase, then trace its exact called branch; do not assume a last writer from address overlap alone.',
 hypotheses_not_proved=['Prior921 frame592 aliases this address at+96, but no actual writer identified.','Prior947/worldheight callchain can reach this stack address; terrain/vertex value resemblance is insufficient evidence.'],
 production_expression_independently_available=False,new_original_executions=0,model_executed=False,source_sha256=sha(Path(__file__)),evidence_decoder_sha256=sha(ROOT/'scripts/opening_combat135_cas.py'),full_game_acceptance=False)
 save(out/'trace.json',result);print(json.dumps(dict(directory=str(out),sha256=sha(out/'trace.json'),status=result['status'],address=address,wat_bytes_read=result['wat_bytes_read'])))
def load(p):return json.loads(p.read_text())
if __name__=='__main__':main()
