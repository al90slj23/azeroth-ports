#!/usr/bin/env python3
"""RO bounded137→138913/direct-helper mapping; never instantiate a target."""
from pathlib import Path
from datetime import datetime,timezone
import difflib,hashlib,json,re,sqlite3
from wasm137_profile import binary_identity as identity137
from build_combat138_oracle import ROOT,PROFILE,SOURCE,SOURCE_SHA,Reader,binary_identity,sha,save
OLD_PROFILE=ROOT/'evidence/wasm0137-profile-20261101T162221.947222Z'
OLD_SOURCE=ROOT/'originals/official-acquisition-20261101T154517.001467Z/latest-wenilla_bg.wasm'

def inspect(profile,source,version,out):
 raw=source.read_bytes();identity,ranges=(identity137 if version=='137' else binary_identity)(raw)
 sec=next(x for x in identity['sections']if x['kind']==1);r=Reader(raw,sec['payload_start'],sec['end']);types=[]
 for _ in range(r.uint()):
  assert r.byte()==0x60
  types.append((r.raw(r.uint()).hex(),r.raw(r.uint()).hex()))
 sec=next(x for x in identity['sections']if x['kind']==3);r=Reader(raw,sec['payload_start'],sec['end']);decl=[r.uint()for _ in range(r.uint())]
 con=sqlite3.connect((profile/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
 rows=[dict(x)for x in con.execute('select callee,wat_offset,wat_line,instruction from calls where caller=913 order by wat_offset')]
 entry=dict(con.execute('select * from functions where idx=913').fetchone());items=[]
 for idx in sorted({913}|{x['callee']for x in rows}):
  row=dict(con.execute('select * from functions where idx=?',(idx,)).fetchone());a,b=row['body_start'],row['body_end'];assert ranges[idx][:2]==(a,b)
  items.append(dict(index=idx,body_sha256=hashlib.sha256(raw[a:b]).hexdigest(),body_bytes=b-a,signature=list(types[decl[idx-878]])))
 texts={}
 for idx in (913,68459 if version=='137' else 68536):
  row=dict(con.execute('select * from functions where idx=?',(idx,)).fetchone())
  with(profile/f'official-0.{version}.0-full.wat').open('rb')as f:f.seek(row['wat_start']);text=f.read(row['wat_end']-row['wat_start'])
  assert len(text)<524288
  name=f'{version}-{idx}.wat';(out/name).write_bytes(text);texts[idx]=text.decode()
 con.close()
 return dict(source=str(source.relative_to(ROOT)),source_sha256=hashlib.sha256(raw).hexdigest(),source_bytes=len(raw),profile_manifest_sha256=sha(profile/'manifest.json'),entry=entry,direct_calls=rows,bodies=items),texts

def main():
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('combat0138-static-map-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 old,ot=inspect(OLD_PROFILE,OLD_SOURCE,'137',out);new,nt=inspect(PROFILE,SOURCE,'138',out);assert new['source_sha256']==SOURCE_SHA
 exact=[]
 for prior in old['bodies']:
  candidates=[x['index']for x in new['bodies']if(x['body_sha256'],x['signature'])==(prior['body_sha256'],prior['signature'])]
  if candidates:exact.append(dict(old_index=prior['index'],new_candidates=candidates,body_sha256=prior['body_sha256'],signature=prior['signature']))
 assert len(old['direct_calls'])==len(new['direct_calls'])
 ordinal={}
 for a,b in zip(old['direct_calls'],new['direct_calls']):ordinal.setdefault(a['callee'],set()).add(b['callee'])
 norm=lambda s:re.sub(r'call \d+','call INDEX',re.sub(r'\(type \d+\)','(type TYPE)',re.sub(r'\(func \(;\d+;\)','(func (;INDEX;)',s))).splitlines(True)
 diff=''.join(difflib.unified_diff(norm(ot[913]),norm(nt[913]),fromfile='137-913-type-call-index-normalized',tofile='138-913-type-call-index-normalized'))
 (out/'913-call-normalized.diff').write_text(diff)
 lines=nt[913].splitlines();windows=[]
 for a,b,label in ((8,79,'G phase/unit Vec432/clock'),(690,753,'ordered additive144/152/160'),(873,913,'U368 and empty spell source'),(1091,1162,'school bitmask/U372'),(1198,1258,'U420/416 and linked guard'),(1400,1468,'HP288 nonlethal write'),(1568,1581,'G984 f64 accounting'),(7188,7223,'new helper ABI behind G1972 count'),(7657,7679,'new helper ABI second invocation')):
  windows.append(dict(label=label,start=a,end=b,lines=[dict(line=n,text=lines[n-1])for n in range(a,b+1)]))
 result=dict(version='0.138.0',build='382771e6c',scope='Static bounded source mapping;0 target executions;not whole-function behavioral equivalence',profiles={'137':old,'138':new},exact_body_and_signature_direct_helpers=exact,ordinal_call_correspondence={str(k):sorted(v)for k,v in ordinal.items()},ordinal_correspondence_is_semantic_proof=False,
  actual_abi_change=dict(old_index=68459,old_signature=['7f7f',''],new_index=68536,new_signature=['7f7f7f7f',''],description='Vec remove-first specialized two-arg helper becomes indexed four-arg helper;913 passes explicit index0 and panic location1590040. Nonempty G1972 domain remains pending.'),
  fields=dict(Game=dict(now=2352,phase=2587,unit_capacity=1784,unit_pointer=1788,unit_count=1792,total_f64=984,item_ptr=2028,item_count=2032,spell_ptr=2052,spell_count=2056,new_helper_source_count=1972),Unit=dict(stride=432,guid=112,hp=288,maxhp=292,school_bonus_clock=372,additive=368,phase416=416,phase420=420)),windows=windows,
  artifacts={p.name:dict(bytes=p.stat().st_size,sha256=sha(p))for p in out.iterdir()if p.is_file()},producer_sha256=sha(Path(__file__)),Windows_gameplay_ABI_confirmed=False)
 save(out/'mapping.json',result);print(json.dumps(dict(directory=str(out),mapping_sha256=sha(out/'mapping.json'),exact_helpers=len(exact),calls=len(new['direct_calls']),target_executed=False)))
if __name__=='__main__':main()
