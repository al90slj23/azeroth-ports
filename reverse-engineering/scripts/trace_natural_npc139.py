#!/usr/bin/env python3
"""Static natural1395719(None) call order/seed witness; no original execution."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/natural-npc139-oracle-20261102T044325.586298Z'
NPC=ROOT/'evidence/npc-spawn139-static-20261102T031838.749854Z'
OPENING=ROOT/'evidence/opening-aux139-static-20261102T043651.314712Z/1108.wat'
SEED=ROOT/'evidence/opening139-context-static-20261102T022955.014560Z/6786.wat'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def excerpt(lines,start,end):return dict(first_line_1based=start+1,last_line_1based=end,text='\n'.join(lines[start:end]))
d=json.loads((NPC/'proof.json').read_text());p=NPC/'5719.wat';assert sha(p)==d['functions']['5719']['wat_sha256'];lines=p.read_text().splitlines();at=next(i for i,x in enumerate(lines)if x.strip()=='call 8740');assert all(x in '\n'.join(lines[at-8:at+1])for x in('f32.const 0x1.ap+4','f32.const 0x1.2p+5','f32.const 0x1p-1'))
assert at<next(i for i,x in enumerate(lines)if 'i32.load offset=1720'in x)
opening=OPENING.read_text().splitlines();calls=[i for i,x in enumerate(opening)if x.strip()=='call 5719'];assert len(calls)==4 and calls[-1]<next(i for i,x in enumerate(opening)if x.strip()=='call 13563')
window='\n'.join(opening[calls[0]-17:calls[-1]+1]);assert window.count('i32.store offset=248')==4 and window.count('call 5719')==4
seed=SEED.read_text().splitlines();lcg=next(i for i,x in enumerate(seed)if 'i64.const 6364136223846793005'in x);store=next(i for i,x in enumerate(seed)if 'i64.store offset=3128'in x)
assert 'i64.load offset=4928'in seed[lcg-1] and 'i64.const 1442695040888963407'in seed[lcg+2] and any('local.get 74'in x for x in seed[store-2:store])
r=dict(kind='static_component_input_witness',script_sha256=sha(Path(__file__)),original_executions=0,model_executions=0,NPC5719_proof_sha256=sha(NPC/'proof.json'),NPC5719_body_sha256=d['functions']['5719']['body_sha256'],NPC5719_wat_sha256=sha(p),None_argument_path=excerpt(lines,at-23,at+2),heading_jitter_source_occurs_after8740=True,opening1108_wat_sha256=sha(OPENING),opening_four_None_calls=excerpt(opening,calls[0]-17,calls[-1]+1),seed6786_wat_sha256=sha(SEED),LCG=excerpt(seed,lcg-2,lcg+8),selectedP_seed184_scratch3128=excerpt(seed,store-3,store+2),controlledAppseed0_LCG_u64=str(1442695040888963407),naturalApp_account_profile_production_claimed=False,complete1108_executed=False)
(OUT/'static-input-proof.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(path=str(OUT/'static-input-proof.json'),sha256=sha(OUT/'static-input-proof.json'))))
