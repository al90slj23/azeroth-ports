#!/usr/bin/env python3
"""PinnedWAT/binary body evidence for pause/resume moving snapshots; no execution."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sqlite3
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
WAT_SHA='15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'
INDICES=(1371,35514,25472,26200,45845,27457,15916,45628)

def main():
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA;types,imports,decl,bodies,_=parse_source(raw)
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('movement-pause0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 db=sqlite3.connect(f'file:{PROFILE/"index.sqlite"}?mode=ro',uri=True);functions=[];texts={}
 with(PROFILE/'official-0.135.1-full.wat').open('rb')as f:
  assert hashlib.file_digest(f,'sha256').hexdigest()==WAT_SHA
  for i in INDICES:
   a,b=db.execute('select wat_start,wat_end from functions where idx=?',(i,)).fetchone();f.seek(a);wat=f.read(b-a);texts[i]=wat.decode();assert f'(func (;{i};)'in texts[i].splitlines()[0]
   (out/f'{i}.wat').write_bytes(wat);x,y=bodies[i];params,results=types[decl[i-len(imports)]]
   functions.append(dict(index=i,body_start=x,body_end=y,body_bytes=y-x,body_sha256=hashlib.sha256(raw[x:y]).hexdigest(),parameters_hex=params.hex(),results_hex=results.hex(),wat_start=a,wat_end=b,wat_sha256=hashlib.sha256(wat).hexdigest(),direct_callees=[r[0]for r in db.execute('select distinct callee from calls where caller=? order by callee',(i,))]))
 for i in(35514,25472):
  assert 'call 26200'in texts[i]and'offset=2412'in texts[i]and'offset=1888'in texts[i]
  assert 'offset=1720'not in texts[i]and'offset=1788'not in texts[i]
 assert texts[26200].index('offset=1788')<texts[26200].index('offset=660')<texts[26200].index('offset=2112')
 report=dict(original_sha256=SOURCE_SHA,wat_sha256=WAT_SHA,functions=functions,collector=dict(npc_source=[1788,1792,424],predicate='load_u32(marker0)==0 && duration344>0 && f32(duration344+start340)>now2352',order='NPC vector order; noGUID deduplication. Auxiliary112B records then88B claims are concatenated after NPC snapshots.',other_sources=[dict(pointer=660,length=664,stride=112),dict(pointer=2112,length=2116,stride=88)]),consumers={'35514':'Each40B snapshot increments wrappingG2412 once and appends221 stop packet; flatheight fallback uses snapshot interpolatedorigin.', '25472':'Sameordered snapshot collector, each incrementsG2412 once and appends221 resumepacket withtarget/remaining duration.'},entry='1371 rawcommandtag7+payloadbyte4; pause1→3 calls35514, resume3→1 calls25472, game_tag2 andmode lowbit1 guard.',pending=['Nonempty auxiliary motions/claims selection producers andtheir ownpredicate details.','Nonflat terrain height correction andcomplete221 geometry serialization.','Application pause scheduler androotnaturalchoice composition remain separate tests.'],source_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 (out/'movement-pause135-static.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(directory=str(out),functions=len(functions))))

if __name__=='__main__':main()
