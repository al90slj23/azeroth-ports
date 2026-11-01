#!/usr/bin/env python3
"""Read-only pinned135 WAT/body identity and kind3→periodic area chain."""
from datetime import datetime,timezone
import hashlib,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
WAT_SHA='15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'
EXPECTED={922:'32cdc4ec4ee9b320ae2052560c2a3f4682979df5638e57c3e7140ffc8b047d80',
3757:'e976ee48b3f0ad4117bfa98c81538fa88bf4607c4a9ca15c1a5a040c1c4477f5',
13151:'2ed3acb588007e712a00e5a3ff32998185066f7c4c457f397b0fe6928efa04ca',
2825:'aa886e283047dab55ccd6e51e180ced2e870e069e8e9e41feb2edcea1dc4d446',
85719:'3f9127d30eefb0c9bad49101460ed45df1f6069e63c42d87e351ffbb67151c36',
2244:'30192e9a1c26b5e718b31582831bb65699148fc38b48fd696b9bf6bb4dbaadfd'}


def digest(path):
 h=hashlib.sha256()
 with path.open('rb')as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()


def main():
 assert digest(SOURCE)==SOURCE_SHA
 wat=PROFILE/'official-0.135.1-full.wat';assert digest(wat)==WAT_SHA
 conn=sqlite3.connect('file:'+str(PROFILE/'index.sqlite')+'?mode=ro',uri=True)
 out=ROOT/'evidence'/('area-effects135-chain-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'));out.mkdir()
 identities=[];texts={}
 with SOURCE.open('rb')as binary,wat.open('rb')as fullwat:
  for index in(880,922,3757,13151,2825,85719,2244,914,915):
   a,b,line,bodya,bodyb=conn.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end FROM functions WHERE idx=?',(index,)).fetchone()
   binary.seek(bodya);body=binary.read(bodyb-bodya);bodysha=hashlib.sha256(body).hexdigest()
   if index in EXPECTED:assert bodysha==EXPECTED[index]
   fullwat.seek(a);text=fullwat.read(b-a);(out/f'{index}.wat').write_bytes(text);texts[index]=text.decode().splitlines()
   identities.append(dict(index=index,body_start=bodya,body_end=bodyb,body_bytes=len(body),body_sha256=bodysha,wat_line=line,
    wat_sha256=hashlib.sha256(text).hexdigest(),file=f'{index}.wat',signature=text.decode().splitlines()[0].strip()))
 calls={index:[dict(line=i,instruction=l.strip())for i,l in enumerate(texts[index])if l.strip().startswith('call ')]for index in texts}
 result=dict(original_sha256=SOURCE_SHA,full_wat_sha256=WAT_SHA,script_sha256=digest(Path(__file__)),functions=identities,
  chain=['880 player2088/owned1076→922 kind3','922 center13151 (or player-centred27562), flat height, visual2825, appendG1796/1800/1804 stride88',
   '880 delayed1754→3757 persistent areas→915→921→2862→947','3757 expiry/delete, optional modifier36-follow (pending), at most one due normal tick',
   '27562 sorted IDs→per-target critical RNG→full914→full2244','914 accepted-hit self-heal before ordinary death/loot→984; empty source domain'],
  calls=calls,layout=dict(stride=88,globals=[1796,1800,1804],fields={'0':'u64 normal_variant0','8..23':'retained unwritten append-slot bytes',
   '24':'u64 visualGUID=f100000000000000|full32counter','32/36/40':'effect tag/value/aux','44/48/52':'fixed centerXYZ','56':'radius','60':'spell',
   '64':'nextTick now+.25 then oldNext+interval','68':'duration/f32(actualTicks)','72':'remaining','76':'baseDamage/f32(baseTicks)',
   '80':'(duration+now)+.3','84':'school byte','85..87':'retained unwritten bytes'}),
  rules={'duration':'((def.duration*1.4)*owned.duration)*owned.additionalDuration',
   'actual_ticks':'max_u32(1,trunc_sat_u32(R85719((duration/maxnum(.01,def.duration))*f32(max_u32(1,baseTicks)))))',
   'damage':'((def.damage*1.4)*owned.damage*additionalDamage*.5 + maxHP*lifeDamage if def.damage>0)*G1540 / f32(max(1,baseTicks))',
   'center':'first24 sorted in-range candidate IDs; count ALL live XY within radius, including outside cast range; later score ties win',
   'expiration':'remove when now>=expiry before due tick; remove repeated expired entries in vector order',
   'tick':'remaining>0 && next<=now; decrement once and oldNext+=interval even if query empty',
   'slow1':'after914, if target marker!=1 and no override49: U120=value,U124=now+aux; no extra RNG'},
  pending=['915 unrelated large phase is not restored by this chain','Modifier36 area-follow and49 status override','effect2 frosttrap stun and alternate hostile area variants',
   'Terrain/grid/navigation height and physical visual/ECS/wire packets','Nonempty984 proc sources and full-game integration'],
  original_executed=False,application_start_called=False,network_used=False,user_saves_accessed=False)
 (out/'trace.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(directory=str(out),functions=len(identities),trace_sha256=digest(out/'trace.json'))))


if __name__=='__main__':main()
