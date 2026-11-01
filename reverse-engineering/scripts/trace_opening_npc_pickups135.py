#!/usr/bin/env python3
"""Fixed135 NPC/kind2 declaration/complete-function evidence; no target execution."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,re,sqlite3,struct
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source
from build_upgrade134_oracle import sha

PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
INDICES=(5736,1525,1417,1821,21454,23469,10823,50798,65342,65337)


def main():
    script=Path(__file__);script_sha=sha(script);raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    _,_,_,bodies,segments=parse_source(raw)
    image=bytearray(max(s['address']+s['length']for s in segments if s['address']is not None))
    for s in segments:
        if s['address']is not None:image[s['address']:s['address']+s['length']]=raw[s['file_offset']:s['file_offset']+s['length']]
    speeds=list(struct.unpack_from('<6I',image,1587548));speeds[1]=1088421888
    assert speeds==[1075838976,1088421888,1083179008,1083645041,1075838976,1078530011]
    con=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('opening-npc-pickups0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir();rows=[];texts={}
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        for i in INDICES:
            row=dict(con.execute('select *from functions where idx=?',(i,)).fetchone());assert(row['body_start'],row['body_end'])==bodies[i]
            stream.seek(row['wat_start']);wat=stream.read(row['wat_end']-row['wat_start']);assert wat.splitlines()[0].startswith(f'  (func (;{i};)'.encode())
            (out/f'{i}.wat').write_bytes(wat);texts[i]='\n'.join(line.strip()for line in wat.decode().splitlines())
            rows.append(dict(index=i,**row,body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest(),wat_sha256=hashlib.sha256(wat).hexdigest(),
                direct_callees=[dict(x)for x in con.execute('select callee,count(*)sites from calls where caller=?group by callee',(i,))]))
    field_branches=[]
    for m in re.finditer(r'local.get 9\ni32.const (\d+)\ni32.store offset=88\n.*?call 3735',texts[1525],re.S):
        field_branches.append(dict(key=int(m[1]),instructions=m[0].splitlines()))
    assert sorted(x['key']for x in field_branches)==[2,3,4,22,28,34,35,36,46,126,127,129,130,131,132,134,135,145]
    assert 'local.get 14\ni32.const 16\nlocal.get 0\ni64.load offset=1336\ncall 23469'in texts[1525]
    assert 'local.get 0\nf32.load offset=1420\nlocal.get 7\nf32.load offset=4\nf32.sub\nlocal.get 0\nf32.load offset=1416\nlocal.get 7\nf32.load\nf32.sub\ncall 42475'in texts[1525]
    assert 'i64.const 4575657221408424195'in texts[1417]and'i64.const 34359738368'in texts[1417]
    report=dict(version='0.135.1',build='0898d5e3',original_sha256=SOURCE_SHA,script_sha256=script_sha,
        model_sha256=sha(ROOT/'reconstruction/core_spec/opening_npc_pickups135.py'),functions=rows,npc1525_field_branches=field_branches,
        npc_complete_fields=dict(guid_keys=[0,1],target_player_guid_keys=[16,17],fields={2:9,3:'entry',4:'scale_bits',22:'ceil(hp) sat_u32',28:'ceil(hp) sat_u32',
            34:'min((level1432+3*bool(elite))&u32,63)',35:14,36:256,46:0,126:2000,127:2000,129:'scale*.5',130:'scale*1.5',131:'display',132:'display',
            134:1084227584,135:1092616192,145:1065353216},speeds=speeds,facing='atan2(playerY-positionY,playerX-positionX),notrecord396RNGyaw',
            packet='Complete10823(kind3,self0,flags0x70)->50798;logicalfieldsallincluded,includingzero targetGUID words.'),
        npc424_written_ranges=[[0,4],[8,4],[16,4],[40,4],[64,4],[112,136],[280,139]],npc424_written_bytes=295,npc424_unwritten_bytes=129,
        kind2=dict(descriptor=dict(visual=9005,display=259,scale_bits=1065353216),actor1821=dict(kind21=3,flags9=0),
            amount_order=[2,1],random_position13516_radii=[18,50],pickup1417_clamp='radius=max(1,zoneRadius-2);center+(delta/distance)*limit;finalworldheightorprimary/fallbackZ',
            empty_aux_vec_words=[0,8,0],record56_unwritten_offsets=[4,5,6,7],mode0_count_cap=5,initial_count=0),
        boundaries=['Mode0 emptyNPC/pickup start only;explicit preallocatedpriorbacking accepted without clearing unknown/padding.',
            'World is alreadyresolved pureconsumer input; no worldproducer,profileproducer orBTreephysicalallocation implementation.',
            'Historical snapshot developerreplay isnotneworiginaldifferential;whole1089 receiptmustgenerateindependentexpectedbeforefutureoriginalexecution.'],
        original_executed=False,existing_sources_modified=False)
    target=out/'trace.json';target.write_text(json.dumps(report,indent=2)+'\n');assert sha(script)==script_sha and sha(SOURCE)==SOURCE_SHA
    print(json.dumps(dict(directory=str(out),trace_sha256=sha(target),functions=len(rows),original_executed=False)))


if __name__=='__main__':main()
