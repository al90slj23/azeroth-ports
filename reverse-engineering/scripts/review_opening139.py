#!/usr/bin/env python3
"""Different-author complete1391108 review; no author or target execution."""
from collections import Counter
from pathlib import Path
import hashlib,json,math,sqlite3,struct,sys
from review_combat139 import parse_module,local_closure,sha,bits,fp,f32
from review_initial139 import reference as constructor_reference
from review_natural_npc139 import reference as natural_reference
from review_world_position139 import Reference as Position,load_world,trig,sin_kernel,cos_kernel,hypot_ref
from review_opening_actor139 import draw,uniform,object_packet

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'evidence/opening139-oracle-20261102T053454.622445Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
COMP='ad3ae6e0128cd109d1ac0f1e9b0cf3231b304cdbba6bba7ea5ff425c311386b6'
HAND='b128b1f5af03510c643782f300f46eb102ddde7dbc1ed202acbd109ec6245934'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
HELPERS={
 'scripts/review_combat139.py':'158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9',
 'scripts/review_initial139.py':'86d33e69c361eef223ad3ef271b6fb987d170f4d94847c0c068148c56ebe6fbc',
 'scripts/review_npc_spawn139.py':'aa1c8a9d5ca4fe0363f97cbdad71f13ce00ebccf238fe89b213f354627ef5074',
 'scripts/review_natural_npc139.py':'e14d0e0baa3f408380525a78c85ee068d5f5d4c52322e6dae20e76d8c1f4b665',
 'scripts/review_world_position139.py':'d842c619169a582ab8eb540cab2829233eb633bbd79d10ab674c50e71c92ab7e',
 'scripts/review_player_motion135.py':'8a339b74435adbc4abcf5aff7f3a25a24d5f8495653e42135f06aa94230de2b2',
 'scripts/review_opening_actor139.py':'85d620150923205eaaa286afe764ebb7db65be5d2854c3893a3d4208860c370f'}
load=lambda p:json.loads(p.read_text())
u=lambda b,o=0:struct.unpack_from('<I',b,o)[0]


def extended_trig(x):
    # Current11425/11499 medium range reduction, independently transcribed.
    magnitude=bits(x)&0x7fffffff
    if magnitude<=0x40c90fdb:return trig(x)
    if magnitude<1088565718:
        y=abs(x)-float.fromhex('0x1.921fb54442d18p2')
        return (-sin_kernel(y) if x<0 else sin_kernel(y)),cos_kernel(y)
    assert magnitude<=1305022426
    n=(x*float.fromhex('0x1.45f306dc9c883p-1')+float.fromhex('0x1.8p52'))+float.fromhex('-0x1.8p52')
    y=(x+n*float.fromhex('-0x1.921fb5p0'))+n*float.fromhex('-0x1.110b4611a6263p-26')
    s,c=sin_kernel(y),cos_kernel(y);q=int(n)&3
    return (s,c,-s,-c)[q],(c,-s,-c,s)[q]


def vector(rows,count=None):return dict(capacity=len(rows),count=len(rows)if count is None else count,storage=rows)


def reference(c,world,nav,scalars,tables,definition,speeds,classes,races,zones,eligible,minutes):
    seed=(int(c['app_seed_u64'])*6364136223846793005+1442695040888963407)&((1<<64)-1)
    center=scalars['center_xy_bits'];z=world.height(*center);assert z is not None
    ctor,known=constructor_reference(dict(class_byte=1,race_byte=1,region_index=0,seed_u64=str(seed),object_id_u64='0',flat_height_bits=z),classes,races,zones)
    inp=dict(id=c['id'],rng_words=ctor['rng_words'],counter=10,initial_backing=[],player_xyz=ctor['player_xyz'],velocity_xy=[0,0],distance_map=None)
    stages,diagnostics=natural_reference(inp,world,nav,scalars,tables,definition,speeds);units=stages[-1]
    words=units['rng_words'];counter=units['counter'];packets=list(units['packets']);pickups=[[None]*56 for _ in range(4)]
    def height(x,y):
        found=world.height(bits(x),bits(y));return scalars['fallback_height_bits']if found is None else found
    def actor(entry,display,scale,xyz,kind,flags):
        nonlocal counter,words
        counter=(counter+1)&0xffffffff;guid=0xf110000000000000|((entry&0xffffff)<<24)|(counter&0xffffff)
        yaw,words=uniform(words,0.,fp(0x40c90fdb));yaw=f32(yaw+0.)
        packets.append([169,object_packet(guid,entry,display,scale,xyz,yaw,kind,flags)])
        return guid
    for i,amount in enumerate((2,1)):
        state=dict(zone=0,player_xyz=ctor['player_xyz'],velocity_xy=[0,0],low_radius_bits=bits(18.),high_radius_bits=bits(50.),bias_probability_bits=bits(.5),rng_words=list(words),distance_map=None)
        loc=Position(state,world,nav,scalars,tables);xyz=loc.random();words=loc.words
        x,y=map(fp,xyz[:2]);cx,cy=map(fp,center);dx,dy=f32(x-cx),f32(y-cy);distance=hypot_ref(dx,dy)
        if distance>118.:x=f32(cx+f32(f32(dx/distance)*118.));y=f32(cy+f32(f32(dy/distance)*118.))
        placed=[bits(x),bits(y),height(x,y)];guid=actor(9005,259,0x3f800000,placed,3,0)
        pickups[i][0:4]=bytes(4);pickups[i][8:56]=struct.pack('<IIQ4I4I',2,amount,guid,0,8,0,9005,*placed,0)
    count_draws=0
    while True:
        output,words=draw(words);product=output*2;count_draws+=1
        if(product&0xffffffff)<=0x7fffffff:count=2+(product>>32);break
        assert count_draws<100
    windows=[[None]*8 for _ in range(4)];width=f32(f32(fp(minutes)*60.)/f32(count))
    for i in range(count):
        value,words=uniform(words,fp(0x3f19999a),1.);start=f32(width*f32(i));end=f32(start+f32(width*value));windows[i]=list(struct.pack('<2f',start,end))
    cx,cy=map(fp,center);centerz=fp(z);special=[];special_trace=[]
    for i in range(4):
        angle=f32(f32(f32(f32(i)*fp(0x40c90fdb))*.25)+f32(fp(scalars['heading_bits'])+fp(0x3f490fdb)))
        sine,cosine=extended_trig(angle);xyz=None;trials=0
        for coefficient in (0x3f333333,0x3f1eb852,0x3f0a3d71,0x3eeb851f,0x3ec28f5c):
            trials+=1;distance=f32(fp(scalars['radius_bits'])*fp(coefficient));x=f32(cx+f32(cosine*distance));y=f32(cy+f32(sine*distance));blocked=False
            for dx in range(-2,3):
                for dy in range(-2,3):
                    probe,_=loc.probe(f32(x+f32(dx)),f32(y+f32(dy)))
                    if probe:blocked=True;break
                if blocked:break
            if blocked:continue
            found=world.height(bits(x),bits(y))
            if found is not None and abs(f32(fp(found)-centerz))<30.:xyz=[bits(x),bits(y),found];break
        if xyz is None:
            distance=f32(fp(scalars['radius_bits'])*.5);x=f32(cx+f32(distance*cosine));y=f32(cy+f32(distance*sine));xyz=[bits(x),bits(y),height(x,y)]
        row=[None]*40;row[:8]=bytes(8);row[16:36]=struct.pack('<3III',*xyz,eligible[i%len(eligible)],bits(20.));special.append(row)
        special_trace.append(dict(angle_bits=bits(angle),trials=trials))
    radius=f32(fp(scalars['radius_bits'])+10.);n=math.ceil(f32(f32(radius*fp(0x40c90fdb))/12.));assert n==69
    boundary=[[None]*8 for _ in range(128)]
    for i in range(n):
        angle=f32(f32(f32(i)*fp(0x40c90fdb))/f32(n));sine,cosine=trig(angle);x=f32(cx+f32(radius*cosine));y=f32(cy+f32(radius*sine))
        guid=actor(9013,4831,0x3f800000,[bits(x),bits(y),height(x,y)],5,16);boundary[i]=list(struct.pack('<Q',guid))
    title=b'Elwynn Forest';subtitle='The Defias Uprising — survive the onslaught!'.encode()
    banner=bytes.fromhex('5a00000000')+struct.pack('<I',len(title)+1)+title+b'\0'+bytes(8)+struct.pack('<I',len(subtitle)+1)+subtitle+b'\0\0'
    projection=dict(phase2587=1,counter=counter,rng_words=list(words),player_xyz=ctor['player_xyz'],companions=vector([]),units=vector(units['records432_cells']),pickups=vector(pickups,2),windows=vector(windows,count),special=vector(special),boundaries=vector(boundary,n),packets=[[150,banner.hex()]]+packets,packet_capacity=128,notification_capacity=4,notifications=[b'{"type":"start"}'.hex()])
    after=list(known);after[2587]=1
    def word(o,v):after[o:o+4]=struct.pack('<I',v)
    for i,w in enumerate(words):word(1720+4*i,w)
    word(2408,counter)
    for k,cap,num in [('units',1784,1792),('pickups',1868,1876),('special',1916,1924),('windows',1964,1972),('companions',2108,2116),('boundaries',2120,2128)]:word(cap,projection[k]['capacity']);word(num,projection[k]['count'])
    for o,v in [(1880,128),(1888,76),(1892,4),(1900,1)]:word(o,v)
    after[244]=after[252]=255
    selected=bytearray([0xa5]*40);selected[0:4]=bytes(4);selected[8:12]=bytes(4);selected[16:36]=bytes(20);selected[4]=selected[12]=255
    return dict(projection=projection,known_Game2592=after,constructor_cells=known,constructor_seed_u64=str(seed),selected40_cells=list(selected),diagnostic=dict(window_count_draws=count_draws,window_uniform_draws=count,boundary_actor_draws=n)),dict(special=special_trace,natural=diagnostics)


def main():
    out=Path(sys.argv[1]).resolve();out.mkdir()
    assert sha(CASE/'comparison.json')==COMP and sha(CASE/'task-handoff.json')==HAND and sha(SOURCE)==WASM
    for name,h in HELPERS.items():assert sha(ROOT/name)==h,(name,sha(ROOT/name))
    c=load(CASE/'comparison.json');hand=load(CASE/'task-handoff.json');prep=load(CASE/'prepared.json');m=load(CASE/'manifest.json');runtime=load(CASE/'runtime.json')
    for name,h in hand['files'].items():assert sha(ROOT/name)==h
    sources=c['source_sha256_before'];assert sources==c['source_sha256_after']==prep['sources'] and len(sources)==39
    for name,h in sources.items():assert sha(ROOT/name)==sha(CASE/'source-snapshot'/name)==h
    edges=local_closure(sources);assert edges==sorted(c['source_import_edges'])==sorted(prep['source_import_edges']) and len(edges)==100
    for table in [c['frozen_artifacts'],c['artifacts'],prep['artifacts']]:
        for name,h in table.items():assert sha(CASE/name)==h
    assert prep['expected_before_original'] and not prep['original_input_contains_expected'] and c['expected_before_original'] and not c['original_input_contains_expected']
    cfg=load(CASE/'config.json');assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']==c['resource_context_snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'
    assert sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')==c['resource_context_gate_sha256']=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
    ranges=load(Path(cfg['range_file']));assert sha(Path(cfg['range_file']))==cfg['range_sha256'] and len(ranges)==2318 and cfg['world_rc']==20544696
    wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';wr=load(wp);assert sha(wp)==c['independent_world_receipt_sha256']=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
    world,nav,scalars=load_world(dict(receipt=str(wp),receipt_sha256=sha(wp),world_artifacts=wr['world_artifacts']));assert not scalars['flat_present'] and not scalars['primary_present']
    raw=SOURCE.read_bytes();original=parse_module(raw);modified_raw=(CASE/m['module_file']).read_bytes();modified=parse_module(modified_raw)
    assert len(original['sections'])==len(modified['sections'])
    for a,b in zip(original['sections'],modified['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==modified_raw[b['start']:b['end']]
    additions=[('research139_open_actor1886',0,1886),('research139_open_pickup1446',0,1446),('research139_open_random13563',0,13563),('research139_open_initial1600',0,1600),('research139_open_companion2945',0,2945),('research139_open_begin1108',0,1108),('research139_open_stack0',3,0)]
    assert modified['exports']==original['exports']+additions and len(original['imports'])==882
    assert [(v['module'],v['name'])for v in original['imports']]==[(v['module'],v['name'])for v in m['original_imports']]
    def data(address,size):
        result=bytearray(size)
        for at,offset,n in original['data_segments']:
            if at is None:continue
            lo,hi=max(at,address),min(at+n,address+size)
            if lo<hi:result[lo-address:hi-address]=raw[offset+lo-at:offset+hi-at]
        return bytes(result)
    def word(p):return u(data(p,4))
    abilities={}
    for i in range(114):
        p=5882740+88*i;abilities[data(word(p+12),word(p+16))]=p
    classes={1:dict(hp_armor=[word(5877920+72),word(5877920+76)],ability_pointer=5882740)}
    mp,count=word(5874636+16),word(5874636+20)
    races={1:dict(ability_pointer=abilities[data(word(5874636+24),word(5874636+28))],modifiers=[(data(mp+8*i,1)[0],word(mp+8*i+4))for i in range(count)])}
    zone=data(5871348,152);scalars['heading_bits']=u(zone,116);assert [u(zone,o)for o in [64,68,104,108,116,120,136,140,148]]==[5830904,12,*scalars['center_xy_bits'],scalars['heading_bits'],scalars['radius_bits'],1062333317,0,0]
    zones=[dict(xyz=[*scalars['center_xy_bits'],u(zone,116)])]
    definition=data(5830904,72);tables=[list(struct.unpack('<4f',data(p,16)))for p in [14426512,14426528,14426544,14426560]];speeds=list(struct.unpack('<6I',data(1593032,24)));speeds[1]=1088421888
    eligible=[i for i in range(12)if word(5830904+72*i+68)==1 and math.isfinite(fp(word(5830904+72*i+64)))];assert eligible==[9,10,11]
    assert [word(1593828),word(1593832)]==[2,3];minutes=word(u(zone,72)+336);assert minutes==1098907648
    whole=load(CASE/'whole-opening-static/trace.json');claims=m['functions']|m['extra_static_functions']|whole['functions'];bindings={};texts={}
    db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
    with(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        for key,row in claims.items():
            idx=int(key);r=db.execute('select *from functions where idx=?',(idx,)).fetchone();a,z=original['bodies'][idx];assert(a,z)==(r['body_start'],r['body_end']) and hashlib.sha256(raw[a:z]).hexdigest()==row['body_sha256']
            stream.seek(r['wat_start']);value=stream.read(r['wat_end']-r['wat_start']);h=hashlib.sha256(value).hexdigest();assert h==row['WAT_sha256'];texts[idx]=value.decode();bindings[key]=dict(body_sha256=row['body_sha256'],WAT_sha256=h)
    for idx in [11425,11499]:
        for token in ['i32.const 1088565718','i32.const 1305022426','f64.const 0x1.45f306dc9c883p-1','f64.const 0x1.8p+52','f64.const -0x1.8p+52','f64.const -0x1.921fb5p+0','f64.const -0x1.110b4611a6263p-26']:assert token in texts[idx]
    assert texts[1108].count('call 5719')==4 and 'call 13563'in texts[1108] and 'call 1446'in texts[1108] and 'call 1886'in texts[1108]
    for key in ['selector_source_window','append_source_window']:
        w=whole[key];value='\n'.join(texts[1108].splitlines()[w['first_line']-1:w['last_line']]);assert hashlib.sha256(value.encode()).hexdigest()==w['sha256']
    cases=load(CASE/'inputs.json');expected=load(CASE/'expected.json');actual=[json.loads(x)for x in(CASE/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==16
    counts=Counter();traces=[];window_counts=Counter();window_draws=Counter()
    def check_cells(label,cells,observed):
        assert len(cells)==len(observed)
        for i,(v,b)in enumerate(zip(cells,observed)):
            if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
            else:assert v==b,(label,i,v,b);counts[label+'_known']+=1
    for case,e,a in zip(cases,expected,actual,strict=True):
        assert case['id']==e['id']==a['id'];answer,trace=reference(case,world,nav,scalars,tables,definition,speeds,classes,races,zones,eligible,minutes);claim=e['expected']
        for k,v in answer.items():assert v==claim[k],(case['id'],k)
        traces.append(dict(id=case['id'],details=trace));p=answer['projection'];g=a['after'];window_counts[p['windows']['count']]+=1;window_draws[answer['diagnostic']['window_count_draws']]+=1
        assert answer['constructor_seed_u64']==a['constructor_seed_u64'] and a['new_game_pointer']!=a['old_snapshot_Game_pointer_not_target']==14685248
        assert a['account_unchanged'] and a['profile_unchanged'] and a['selection_canaries']==['c3'*16,'d7'*16]
        check_cells('selected',answer['selected40_cells'],bytes.fromhex(a['selected40_hex']));check_cells('constructor',answer['constructor_cells'],bytes.fromhex(a['constructor']['raw_Game2592_hex']));check_cells('afterGame',answer['known_Game2592'],bytes.fromhex(g['raw_Game2592_hex']))
        for k in ['phase2587','counter','rng_words','player_xyz']:assert p[k]==g[k]
        for k in ['companions','units','pickups','special','windows','boundaries']:
            assert p[k]['capacity']==g[k]['capacity'] and p[k]['count']==g[k]['count']
            for row,hx in zip(p[k]['storage'],g[k]['storage'],strict=True):check_cells(k,row,bytes.fromhex(hx))
        assert g['packets']['capacity']==p['packet_capacity'] and g['packets']['count']==len(p['packets']) and p['packets']==[[v['opcode'],v['payload_hex']]for v in g['packets']['active']]
        assert g['notifications']['capacity']==4 and g['notifications']['count']==1 and p['notifications']==[v['payload_hex']for v in g['notifications']['active']]
        counts['complete_packets']+=len(p['packets']);counts['complete_packet_bytes']+=sum(len(bytes.fromhex(h))for _,h in p['packets']);counts['notifications']+=1
        before=bytearray.fromhex(a['before']['raw_Game2592_hex']);after=bytes.fromhex(g['raw_Game2592_hex'])
        constructor=bytearray.fromhex(a['constructor']['raw_Game2592_hex'])
        for offset in [1736,1740,2368]:constructor[offset:offset+4]=bytes(4)
        assert before==constructor
        assert before[360:362]==bytes([1,1]) and before[244]==before[252]==255
        assert all(before[o]==0 for o in [387,2576,2577,2582,2587])
        assert all(u(before,o)==0 for o in [400,2032,2056,2140]) and u(before,1432)==1
        assert u(before,2348)==20544696 and u(before,2540)==1
        assert [u(before,o)for o in [1736,1740,2368]]==[0,0,0] and a['constructor']['phase2587']==0 and a['constructor']['counter']==10
        for i,v in enumerate(answer['known_Game2592']):
            if v is not None:before[i]=v
        for key,offset in [('units',1788),('pickups',1872),('special',1920),('windows',1968),('boundaries',2124),('packets',1884),('notifications',1896)]:
            assert g[key]['capacity']!=a['before'][key]['capacity'];before[offset:offset+4]=after[offset:offset+4];counts['new_pointer_words_observed']+=1
        assert before==after;counts['relativeGame_bytes']+=2592
    assert counts['complete_packets']==1216 and counts['new_pointer_words_observed']==112 and counts['relativeGame_bytes']==41472
    assert sum(counts[k+'_known']for k in ['units','pickups','special','windows','boundaries'])==31984
    assert sum(counts[k+'_None']for k in ['units','pickups','special','windows','boundaries'])==18704
    assert window_counts=={2:10,3:6} and counts['afterGame_known']==16*556
    assert runtime==c['runtime'] and runtime['full_calls']=={'1108':16,'1600':16,'2945':16} and runtime['fresh_instances']==16 and runtime['host_calls']==0 and runtime['denied_imports']==882
    assert runtime['allocator_calls']==80 and runtime['stack_guards']==128 and runtime['peak_memory_bytes']==177078272 and runtime['error']is None
    assert len(runtime['target_and_setup_returns'])==48 and all(v['returned']and v['before']==v['after']==1048576 for v in runtime['target_and_setup_returns'])
    assert len(runtime['world_source_checks'])==48 and all(v['unchanged']and v['ranges']==2318 for v in runtime['world_source_checks'])
    assert not any(runtime[k]for k in ['old_snapshot_Game_reused_as_target','flags_or_Once_readiness_injected','App_or_WorldRc_producer_executed','externref_state_restored','full_mainloop_frames','native_executions','complete_games','network_used','user_saves_accessed'])
    terminal=load(CASE/'owned-terminal.json');assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<120
    audit=load(CASE/'expectation-read-audit.json');assert not audit['original_WASM_or_memory_read'] and audit['layer']=='Pythonopenaudit;notOSaudit' and all(not str(v).endswith(('.wasm','.memory'))and'/originals/'not in str(v)for v in audit['opened'])
    for name,h in hand['files'].items():assert sha(ROOT/name)==h
    for name,h in HELPERS.items():assert sha(ROOT/name)==h
    result=dict(status='pass_complete139_default_controlled_opening_only',comparison_sha256=COMP,handoff_sha256=HAND,reviewer_script_sha256=sha(Path(__file__)),helper_sha256=HELPERS,author_files=hand['files'],counts=dict(counts),cases=16,full1108_calls=16,setup2945_calls=16,setup1600_calls=16,window_counts=dict(window_counts),window_count_draws=dict(window_draws),source_files=39,source_edges=100,full_current139_function_bindings=bindings,all_nonexport_sections_byte_identical=True,reviewer_original_executions=0,reviewer_author_model_builder_checker_executions=0,author_process=terminal,limitations=['Resource-only legal v2post1108 snapshot on original side;new2945/1600Game,not naturalApp/Rc/externref/host bootstrap.','Independent expectations reconstructed from current static data and raw-derived canonical world;no author production or target execution by reviewer.','Known556Game bytes only;112newpointer words observations and other unknown/payload allocation cells remain unknown.','48world range checks and account/profile conservation booleans are frozen runner observations;full account/profile before-and-after bytes not serialized.','AppLCG is controlled arithmetic/current6786static binding;full6786 not executed. Explicit velocity0/pathNone required.','TwoRune/special40/windows/circle/defaultElwynn HumanWarrior only;other companions/events/debug domains remain unknown.','No mainloop/nativeWindows/fullgame/network/save acceptance implied.'])
    (out/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(out/'reference-traces.json').write_text(json.dumps(traces,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(out=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts))))


if __name__=='__main__':main()
