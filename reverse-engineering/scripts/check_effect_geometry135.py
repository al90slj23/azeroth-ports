#!/usr/bin/env python3
"""Expected-first genuine2785→910 raw9 producer→915 rectangle differential."""
from collections import Counter
from dataclasses import asdict,replace
import argparse,hashlib,json,os,random,signal,struct,subprocess,sys,time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
from source_closure135 import core_sources
FILES=('scripts/check_effect_geometry135.py','scripts/run_effect_geometry135_oracle.mjs','scripts/source_closure135.py',
 'scripts/build_full135_oracle.py','scripts/full135_host.mjs','scripts/build_upgrade134_oracle.py')+core_sources(ROOT,'effect_geometry135.py','spawn_boss135.py')
IMPORT_HASH={n:sha(ROOT/n)for n in FILES}
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node';RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.effect_geometry135 import (RECTANGLE_DECLARATIONS,Effect120135,EffectGeometryState135,
    PendingEffectGeometry135,produce_rectangle,tick_rectangles,get,put,cos_bits,sin_bits)
from core_spec.spawn_boss135 import BossInput,spawn_boss
from core_spec.spawn_boss135_data import BOSSES
from core_spec.spawn135_data import ZONES
from core_spec.spawn_position135_data import ZONE_GEOMETRY
from core_spec.incoming135 import IncomingState135
FIELDS=('armor_1392_bits','armor_cap_1572_bits','nearby_reduction_1444_bits','hp_1528_bits','shield_1532_bits','barrier_1536_bits',
 'shield_source_1344','shield_source_remaining_1348_bits','reserve_768_bits','absorbed_740_bits','maximum_shield_744_bits','last_hit_1648_bits')
INDEX={5433104:2,5453396:0,5454132:2}


def boss_input(decl,difficulty=0,flatheight=0,seed=(1,2,3,4),counter=0,fill=0,endless=0):
    _,z,p,_=decl
    return BossInput(z,INDEX[p],f.from_float(180),f.from_float(1),difficulty,0,1,0,endless,0,tuple(seed),counter,
        (*ZONE_GEOMETRY[z][:2],f.from_float(flatheight)),(0,0),f.from_float(flatheight),f.from_float(1),0,(bytes([fill])*424).hex())


def make_state(boss,*,fill=0xa5,effect_counter=17,movement_sequence=31,flat=True,armor=0,shield=0,phase=1):
    result=spawn_boss(boss);assert result.status=='boss_projection'
    incoming=IncomingState135(now_bits=boss.now_bits,hp_1528_bits=f.from_float(1000000),armor_1392_bits=f.from_float(armor),
        shield_1532_bits=f.from_float(shield),barrier_1536_bits=f.from_float(shield),map_id=ZONES[boss.zone][0].encode(),phase_2579=phase)
    state=EffectGeometryState135(tuple(Effect120135((bytes([fill])*120).hex())for _ in range(64)),0,(result.record_hex,),boss.now_bits,boss.zone,boss.player_xyz,incoming,
        effect_counter2356=effect_counter,movement_sequence2412=movement_sequence,rng_words=result.rng_words,spawn_counter2408=result.counter,
        difficulty387=boss.difficulty,endless2568=boss.endless_flag,flat_height_bits=boss.flat_height_bits,flat_height_enabled=flat,
        terrain_grid_absent=True,collision_grid_absent=True,navigation_absent=True,other_incoming_sources_absent=True)
    return state,result.timers_bits


def projection(s,timers,label,events=()):
    result=dict(label=label,storage=[x.raw_hex for x in s.storage],length=s.length,units=list(s.units),timers_bits=list(timers),
        effect_counter2356=s.effect_counter2356,movement_sequence2412=s.movement_sequence2412,action_sequence1644=s.action_sequence1644,
        clock2364_bits=s.clock2364_bits,rng_words=list(s.rng_words),spawn_counter2408=s.spawn_counter2408,phase2587=s.incoming.phase_2579,
        entry_status='pending_original_spell_database'if s.entry_pending else'normal_rectangle_projection')
    result.update({k:getattr(s.incoming,k)for k in FIELDS});result['incoming_total_992_bits']=struct.pack('>d',s.incoming.incoming_total_992).hex()
    result['new_packet_opcodes']=[{'stop221':221,'spell_start305':305,'impact306':306}[x[0]]for x in events if x[0]in('stop221','spell_start305','impact306')]
    result['new_effect_json_events']=[dict(type='hz',id=x[1],kind='danger',shape='line')if x[0]=='preview_JSON'else dict(type='hzend',id=x[1])if x[0]=='remove_JSON'else dict(type='hzt')for x in events if x[0]in('preview_JSON','remove_JSON','hzt_JSON')]
    #915 serializes all previews first and performs reverse-index removals
    #afterwards. Logical events are grouped by those actual enqueue phases.
    result['new_effect_json_events'].sort(key=lambda x:('hz','hzend','hzt').index(x['type']))
    ends=[x for x in result['new_effect_json_events']if x['type']=='hzend'];others=[x for x in result['new_effect_json_events']if x['type']!='hzend']
    if ends:result['new_effect_json_events']=[x for x in others if x['type']=='hz']+list(reversed(ends))+[x for x in others if x['type']=='hzt']
    return result,[list(x.unspecified_bytes)for x in s.storage]


def apply_op(s,op):
    s=replace(s,now_bits=op['now_bits'],player_xyz_bits=tuple(op['player_xyz_bits']))
    if op.get('unit_patch'):
        raw=bytearray.fromhex(s.units[0])
        for o,v in op['unit_patch'].items():
            if int(o)==276:raw[276]=v
            else:put(raw,int(o),v)
        s=replace(s,units=(raw.hex(),))
    if 'incoming_phase'in op:s=replace(s,incoming=replace(s.incoming,phase_2579=op['incoming_phase']))
    return produce_rectangle(s,0,op['descriptor_pointer'],op['raw40_hex'])if op['kind']=='produce'else tick_rectangles(s,op['dt_bits'])


def corpus(pilot=False):
    rows=[];b=f.from_float
    def add(decl,group='producer-hit-expiry',*,relative=(5,0),aim=(10,0),difficulty=0,flat=True,height=0,armor=0,shield=0,phase=1,
            fill=0xa5,counter=0,seq=31,effect_counter=17,moving=False,weakness=0,buff276=0,count=1,seed=(1,2,3,4),interval=.2,first_tick_due=False,endless=0):
        bs=boss_input(decl,difficulty,height,seed,counter,endless=endless);s,timers=make_state(bs,fill=fill,effect_counter=effect_counter,movement_sequence=seq,flat=flat,armor=armor,shield=shield,phase=phase)
        first,mask=projection(s,timers,'boss2785');expected=[first];masks=[mask];ops=[];events=[];raw=bytes.fromhex(s.units[0]);xyz=tuple(get(raw,o)for o in(328,332,336));now=b(180)
        player=(f.add(xyz[0],b(aim[0])),f.add(xyz[1],b(aim[1])),b(height+3))
        def do(op):
            nonlocal s
            result=apply_op(s,op);s=result.state;op['expected_status']=result.status;output,mask=projection(s,timers,op['kind'],result.events);expected.append(output);masks.append(mask);ops.append(op);events.append(result.events)
        for k in range(count):
            patch={}
            if k==0:
                if moving:
                    for j,x in enumerate(xyz):patch[str(316+4*j)]=f.sub(x,b((j+1)*2))
                    patch.update({'340':b(179),'344':b(2)})
                if weakness:patch.update({'128':b(weakness),'132':b(200),'136':b(.7),'140':b(200)})
                if buff276:patch['276']=buff276
            do(dict(kind='produce',now_bits=f.add(now,b(k*interval)),player_xyz_bits=list(player),descriptor_pointer=decl[2],raw40_hex=decl[3],unit_patch=patch))
        # All expected coordinates come from the independent producer before
        # invoking the original; the runner never reads original output as input.
        er=bytes.fromhex(s.records[0].raw_hex);angle=get(er,68);cs=cos_bits(angle);sn=sin_bits(angle)
        impact=(f.add(get(er,56),f.sub(f.mul(b(relative[0]),cs),f.mul(b(relative[1]),sn))),
                f.add(get(er,60),f.add(f.mul(b(relative[0]),sn),f.mul(b(relative[1]),cs))),b(height+3))
        due=get(er,76)
        times=(due,f.add(due,b(.1)),f.add(due,b(1)))if first_tick_due else(now,due-1,due,f.add(due,b(.1)),f.add(due,b(1)),f.add(due,b(5)))
        for t in times:
            do(dict(kind='tick',now_bits=t,dt_bits=b(.1),player_xyz_bits=list(impact)))
            if s.entry_pending:break
        inc=asdict(make_state(bs,fill=fill,effect_counter=effect_counter,movement_sequence=seq,flat=flat,armor=armor,shield=shield,phase=phase)[0].incoming);inc['map_id']=inc['map_id'].decode()
        rows.append(dict(id=len(rows),group=group,declaration=decl[0],boss=asdict(bs),definition_pointer=BOSSES[bs.zone][bs.definition_index][0],zone_id=ZONES[bs.zone][0],
            incoming=inc,flat_height_enabled=flat,max_hp_bits=b(1000000),storage=[(bytes([fill])*120).hex()]*64,effect_counter2356=effect_counter,movement_sequence2412=seq,
            action_sequence1644=1,ops=ops,expected=expected,unspecified_storage_bytes=masks,predicted_events=events))
    for decl in RECTANGLE_DECLARATIONS:
        add(decl);add(decl,'outside-rectangle-miss-expire',relative=(5,20));add(decl,'multiple-real-producers',count=3,phase=0)
    if pilot:return json.loads(json.dumps(rows,allow_nan=False))
    for decl in RECTANGLE_DECLARATIONS:
        d=bytes.fromhex(decl[3]);length=f.to_float(get(d,4));width=f.to_float(get(d,8))
        for forward in(-.01,0,.01,length-.01,length,length+.01):
            for side in(0,width/2-.01,width/2,width/2+.01,-width/2,-width/2-.01):
                add(decl,'rectangle-inclusive-boundaries',relative=(forward,side),phase=0)
        for aim in((10,0),(-10,0),(0,10),(0,-10),(3,4),(-4,3),(-3,-4),(4,-3)):
            for relative in((5,0),(5,3)):
                add(decl,'all-heading-quadrants',aim=aim,relative=relative,phase=0)
        for difficulty in(0,1,3,4,5,255):
            for phase in(0,1,2):add(decl,'difficulty-windup-and-incoming-phase',difficulty=difficulty,phase=phase)
        for flat in(False,True):
            for height in(-7,13):add(decl,'moving-deathless-caster-stop-and-flatheight',moving=True,flat=flat,height=height,phase=0)
        for armor in(0,.3,1):
            for shield in(0,1,1000):add(decl,'incoming-armor-shield-scalar',armor=armor,shield=shield)
        for weakness in(.2,1):
            for flag in(0,1):add(decl,'source-weakness-priority-and-boss276',weakness=weakness,buff276=flag)
        for fill in(0,0x5a,0xff):add(decl,'unwritten-slot-and-shared-counter-wrap',fill=fill,counter=0xffffffff,seq=0xffffffff,effect_counter=0xffffffff,count=3,phase=0)
        for phase in(0,1):
            for count in(1,3):add(decl,'first-preview-and-expiry-same-entry-aggregate',count=count,interval=0,first_tick_due=True,phase=phase)
        for endless in(1,2,255):
            for difficulty in(0,3,4):add(decl,'incoming-difficulty-endless-multiplier',difficulty=difficulty,endless=endless)
    rng=random.Random(0x135910915)
    for k in range(72):
        add(rng.choice(RECTANGLE_DECLARATIONS),'seeded-real-boss-producer-and-overlap',relative=(rng.uniform(-2,35),rng.uniform(-5,5)),
            aim=(rng.uniform(-20,20),rng.uniform(-20,20)),difficulty=rng.choice((0,1,4)),moving=bool(k%2),count=rng.choice((1,2,4)),
            seed=tuple(rng.randrange(0x100000000)for _ in range(4)),fill=rng.randrange(256),effect_counter=rng.randrange(0x100000000))
    return json.loads(json.dumps(rows,allow_nan=False))


def guards():
    s,_=make_state(boss_input(RECTANGLE_DECLARATIONS[0]));decl=RECTANGLE_DECLARATIONS[0];out=[]
    for name,x in(('terrain',replace(s,terrain_grid_absent=False)),('collision',replace(s,collision_grid_absent=False)),('navigation',replace(s,navigation_absent=False)),
        ('movement',replace(s,player_flags2496=1)),('remote-owner',replace(s,mode2582=1)),('delayed56',replace(s,delayed_records56=(bytes(56).hex(),))),
        ('incoming-absence',replace(s,other_incoming_sources_absent=False)),('clock',replace(s,clock2364_bits=f.from_float(1)))):
        try:produce_rectangle(x,0,decl[2],decl[3])
        except PendingEffectGeometry135 as e:assert e.state==x;out.append(dict(name=name,rejected=True,original_state_preserved=True))
        else:raise AssertionError(name)
    bad=Effect120135(bytes(120).hex());x=replace(s,storage=(bad,)+s.storage[1:],length=1)
    try:tick_rectangles(x,0)
    except PendingEffectGeometry135 as e:assert e.state==x;out.append(dict(name='unknown120',rejected=True,original_state_preserved=True))
    else:raise AssertionError('Unknown120 accepted')
    try:produce_rectangle(s,0,decl[2],bytes(40).hex())
    except PendingEffectGeometry135 as e:assert e.state==s;out.append(dict(name='unknown-declaration40',rejected=True,original_state_preserved=True))
    else:raise AssertionError('Unknown40 accepted')
    x=produce_rectangle(s,0,decl[2],decl[3]).state;r=bytes.fromhex(x.records[0].raw_hex)
    x=replace(x,now_bits=get(r,76),player_xyz_bits=(f.add(get(r,56),f.mul(f.from_float(5),cos_bits(get(r,68)))),f.add(get(r,60),f.mul(f.from_float(5),sin_bits(get(r,68)))),0))
    prefix=tick_rectangles(x,0);assert prefix.status=='pending_original_spell_database'and prefix.state.entry_pending
    try:tick_rectangles(prefix.state,0)
    except PendingEffectGeometry135 as e:assert e.state==prefix.state;out.append(dict(name='interrupted-prefix-not-resumable',rejected=True,original_state_preserved=True))
    else:raise AssertionError('Pending state resumed')
    return out


def compare(cases,rows):
    failures=[];masked=0;strict_bytes=0
    assert[r['id']for r in rows]==list(range(len(cases)))
    for c,row in zip(cases,rows):
        if len(c['expected'])!=len(row['stages']):raise AssertionError('Stage length')
        for si,(e,a,masks)in enumerate(zip(c['expected'],row['stages'],c['unspecified_storage_bytes'])):
            assert e.keys()==a.keys()
            for key in e:
                if key=='storage':
                    for j,(x,y,mask)in enumerate(zip(e[key],a[key],masks)):
                        xb,yb=bytes.fromhex(x),bytes.fromhex(y);assert len(xb)==len(yb)==120
                        for offset,(u,v)in enumerate(zip(xb,yb)):
                            if offset in mask:masked+=1
                            else:
                                strict_bytes+=1
                                if u!=v:failures.append(dict(id=c['id'],stage=si,field=f'storage[{j}]+{offset}',expected=u,actual=v))
                elif e[key]!=a[key]:failures.append(dict(id=c['id'],stage=si,field=key,expected=e[key],actual=a[key]))
    return failures,strict_bytes,masked


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
    before={n:sha(ROOT/n)for n in FILES};assert before==IMPORT_HASH
    cases=corpus(args.phase=='pilot');negative=guards();out,manifest=build(['spawn_boss','npc_action','effect_tick']);snapshot=out/'source-snapshot';snapshot.mkdir()
    for n,h in before.items():
        target=snapshot/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes());assert sha(target)==h
    fixture=out/'effect-geometry135-fixtures.json';fixture.write_text(json.dumps(cases,allow_nan=False)+'\n');assert json.loads(fixture.read_text())==cases
    guardfile=out/'effect-geometry135-guards.json';guardfile.write_text(json.dumps(negative,indent=2)+'\n')
    frozen={p.name:sha(p)for p in(fixture,guardfile,out/'manifest.json',out/manifest['module_file'])};assert sha(RUNTIME)==RUNTIME_SHA
    result=out/'effect-geometry135-results.jsonl';stderr=out/'effect-geometry135-stderr.log';command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_effect_geometry135_oracle.mjs'),str(out),str(fixture)];start=time.monotonic()
    with result.open('w')as stream,stderr.open('w')as err:
        child=subprocess.Popen(command,stdout=stream,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned geometry deadline')
    if code:raise RuntimeError(f'Original geometry failed:{out}')
    rows=[json.loads(x)for x in result.read_text().splitlines()];failures,strict_bytes,masked=compare(cases,rows)
    mismatch=out/'effect-geometry135-mismatches.json';mismatch.write_text(json.dumps(failures,indent=2)+'\n')
    after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA
    assert frozen=={p.name:sha(p)for p in(fixture,guardfile,out/'manifest.json',out/manifest['module_file'])}
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),stages=sum(len(c['expected'])for c in cases),mismatch_fields=len(failures),
        strict120_storage_bytes=strict_bytes,unspecified_scratch_bytes=masked,groups=dict(Counter(c['group']for c in cases)),guards=len(negative),
        normal_completed_cases=sum(c['expected'][-1]['entry_status']=='normal_rectangle_projection'for c in cases),
        expected_host_denial_prefix_cases=sum(c['expected'][-1]['entry_status']=='pending_original_spell_database'for c in cases),
        stage_status_counts=dict(Counter(s['entry_status']for c in cases for s in c['expected'])),
        source_sha256_before=before,source_sha256_after=after,original_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),
        artifacts={p.name:sha(p)for p in(fixture,guardfile,result,stderr,mismatch,out/'effect-geometry135-runtime.json')},expected_before_original=True,source_snapshots=True,only_changed_section=7,
        runtime=json.loads((out/'effect-geometry135-runtime.json').read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,deadline_seconds=60),
        limitations=['Only three genuine raw9 Boss declarations/normal0,type0,shape2; actual2785 initializes Boss then actual910 creates every active120 record, never injected synthetic120.',
        'Full120 storage strict except exact4 copied unspecified scratch bytes+20..23 per produced physical slot; actual bytes preserved separately, never read to generate expected. Slot+4..7/+119 strict.',
        'Unit248 allocator pointer canonicalized; all424 other bytes and full ability timers strict. Finite flat world and stationary player flags0; remote ownership, terrain/collision/navigation unresolved.',
        'Normal miss/phaseguard completion is distinct from phase1 accepted incoming: real1073 writes scalar HP/shield/G992 then4546 tries real Spell.dbc through SELF, denied by host. Expected host-denial prefixes stop immediately and never count as complete915 success or resumable game state.',
        'Nonfatal1073 scalar/shield/phase only, empty buffs/modifiers/item effects/other incoming producers; registry/history/aura and wire serialization remain pending.221/305/306 delta opcode and hz/hzend/hzt type/id/kind/shape order compared; full actual payload retained separately.',
        'No app start/full880/gameflow/network/saves; no claim of full915 family coverage or ordinary NPC910 consumer closure.'])
    (out/'effect-geometry135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),cases=len(cases),stages=receipt['stages'],mismatch_fields=len(failures),first_failures=failures[:8])))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
