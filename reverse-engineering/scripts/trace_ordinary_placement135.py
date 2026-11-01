#!/usr/bin/env python3
"""Static byte-backed source trace for914→1417→1821 pickup placement."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,sqlite3
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'


def main():
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
 db=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);out=ROOT/'evidence'/('ordinary-placement135-trace-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'));out.mkdir()
 rows=[]
 with(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
  for idx in(914,1417,1821,49503,29631,23181):
   start,end,body_start,body_end=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(idx,)).fetchone();wat.seek(start);text=wat.read(end-start);(out/f'{idx}.wat').write_bytes(text)
   rows.append(dict(function=idx,wat_start=start,wat_end=end,body_start=body_start,body_end=body_end,body_bytes=body_end-body_start,
    body_sha256=hashlib.sha256(raw[body_start:body_end]).hexdigest(),wat_sha256=hashlib.sha256(text).hexdigest(),header=text.splitlines()[0].decode()))
 proof=dict(original_wasm_sha256=SOURCE_SHA,original_executed=False,functions=rows,
  ordered_chain=['914 reads pre-hit U316/320/324,U328/332/336,U340,U344 and current G2352; ratio clamp0..1 with exact per-op f32.',
   '914 freezes both endpoints to interpolatedXYZ, writes U340=now,U344=0; reward requests use that pre-hit point.',
   'XP1417 receives deathXYZ; ordinary coin1417 receives(deathX+.8,deathY+.8,deathZ), with offsets rounded before clamp.',
   '1417 reads zone+104/+108 center and zone+120radius; limit=maxNumeric(1,radius-2), exact hypot49503.',
   'If distance>limit, axis=center+(((axis-center)/distance)*limit); resulting XY queried through29631 then optional23181.',
   'Final XP/coin record height is world query/default V116, not deathZ. With flat enabled and absent terrain/nav, it is exactly V116.',
   '1821 generates kind1 entity counter/GUID/angle; it receives already-resolvedXYZ and does not apply another zone clamp.'],
  pending=['Actual terrain height grids/navigation result and producer initialization','Nonordinary/flagged death routes and merge/cap behavior beyond reused pure codec scope'])
 (out/'trace.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'directory':str(out),'source_sha256':SOURCE_SHA,'functions':len(rows)}))


if __name__=='__main__':main()
