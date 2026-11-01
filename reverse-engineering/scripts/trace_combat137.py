#!/usr/bin/env python3
"""RO indexed135/136→137 damage mapping; static identity is not dynamic proof."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sqlite3
from build_combat137_oracle import ROOT,PROFILE,SOURCE,SOURCE_SHA,sha,save

PROFILES={
 '135':(ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z',ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm',914),
 '136':(ROOT/'evidence/wasm0136-profile-20261101T143713.272522Z',ROOT/'originals/official-acquisition-20261101T142725.754244Z/latest-wenilla_bg.wasm',914),
 '137':(PROFILE,SOURCE,913),
}
def main():
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('combat0137-static-map-%Y%m%dT%H%M%S.%fZ');out.mkdir();summary={};bodies={}
 for version,(directory,source,entry)in PROFILES.items():
  binary=source.read_bytes();con=sqlite3.connect((directory/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
  callees=sorted({r[0]for r in con.execute('select callee from calls where caller=?',(entry,))});items=[]
  for idx in (entry,*[x for x in callees if x!=entry]):
   row=dict(con.execute('select * from functions where idx=?',(idx,)).fetchone());a,b=row['body_start'],row['body_end'];items.append(dict(index=idx,body_sha256=hashlib.sha256(binary[a:b]).hexdigest(),body_bytes=b-a))
  row=dict(con.execute('select * from functions where idx=?',(entry,)).fetchone())
  with(directory/f'official-0.{version}.0-full.wat').open('rb')if version in('136','137')else(directory/'official-0.135.1-full.wat').open('rb')as stream:
   stream.seek(row['wat_start']);text=stream.read(row['wat_end']-row['wat_start'])
  (out/f'{version}-{entry}.wat').write_bytes(text);bodies[version]=items
  summary[version]=dict(entry=entry,source=str(source.relative_to(ROOT)),source_sha256=hashlib.sha256(binary).hexdigest(),signature=text.splitlines()[0].decode(),wat_bytes=len(text),wat_sha256=hashlib.sha256(text).hexdigest(),callees=items,source_read_only=True)
  con.close()
 mappings=[]
 for version in ('135','136'):
  exact=[]
  for old in bodies[version][1:]:
   matched=[v['index']for v in bodies['137'][1:]if v['body_sha256']==old['body_sha256']]
   if matched:exact.append(dict(old_index=old['index'],new_indices=matched,body_sha256=old['body_sha256'],scope='Exact raw body identity only,not execution acceptance'))
  mappings.append(dict(source=version,target='137',semantic_damage_entry=[PROFILES[version][2],913],exact_body_direct_helpers=exact))
 lines=(out/'137-913.wat').read_text().splitlines();windows=[]
 for a,b,label in ((8,79,'phase/G/vector/432stride and controls'),(690,753,'ordered additive144/152/160 clocks'),(873,913,'U368 and empty spell sources'),(1091,1162,'school372 bonus and multiplication'),(1198,1258,'moved phase420/416 and linked protection'),(1400,1468,'unique live GUID and HP288 minimum1 write'),(1568,1581,'f64 G984 accounting')):
  windows.append(dict(label=label,start=a,end=b,lines=[dict(line=n,text=lines[n-1])for n in range(a,b+1)]))
 result=dict(version='0.137.0',build='d171b8f9f',scope='Static source/call/field mapping only;0 new original calls',profiles=summary,mappings=mappings,
   fields=dict(Game=dict(now=2352,phase=2587,unit_capacity=1784,unit_pointer=1788,unit_count=1792,total_f64=984,item_ptr=2028,item_count=2032,spell_ptr=2052,spell_count=2056),
    Unit=dict(stride=432,guid=112,hp=288,maxhp=292,control124=124,old_control380=388,old_control388=396,old_phase408=416,old_phase412=420,old_elite416=424,additive368=368,new_school_bonus_clock=372),
    unknown_new_unit_words=[380,384]),windows=windows,normalized_correspondence_is_dynamic_acceptance=False,Windows_gameplay_ABI_confirmed=False,
   producer_sha256=sha(Path(__file__)))
 save(out/'mapping.json',result);print(json.dumps(dict(directory=str(out),mapping_sha256=sha(out/'mapping.json'),exact_direct_helpers={x['source']:len(x['exact_body_direct_helpers'])for x in mappings},target_executed=False)))

if __name__=='__main__':main()
