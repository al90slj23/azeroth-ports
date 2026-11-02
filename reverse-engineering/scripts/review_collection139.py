#!/usr/bin/env python3
"""Independent139 collector reference; no author or target execution."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import hashlib,json,math,sqlite3,struct,sys
import review_cast139 as C
import review_death139 as D
from review_combat139 import parse_module,local_closure,sha,fp,bits,f32
from review_initial139 import default_stats,record,rng
from review_natural_npc139 import reference as natural_reference
from review_world_position139 import load_world

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
SOURCE_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
load=lambda p:json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def read(row,o,n=4):
    value=row[o:o+n];assert len(value)==n and None not in value,('unknown_input_read',o,n)
    return int.from_bytes(bytes(value),'little')
def put(row,o,v):row[o:o+4]=struct.pack('<I',v)
def add(a,b):return bits(f32(fp(a)+fp(b)))
def mul(a,b):return bits(f32(fp(a)*fp(b)))
def div(a,b):return bits(f32(fp(a)/fp(b)))
def sqrt_exact(word):
    # Binary32 approximation locates neighbors; exact rational midpoint decides.
    s=C.rational(word);assert s>=0
    if not s:return word
    low=bits(f32(math.sqrt(float(s))))
    while C.rational(low)**2>s:low-=1
    while C.rational(low+1)**2<=s:low+=1
    midpoint=(C.rational(low)+C.rational(low+1))/2
    return low if s<midpoint**2 or s==midpoint**2 and not low&1 else low+1
def distance(row,player):
    dx=C.sub(read(row,40),player[0]);dy=C.sub(read(row,44),player[1])
    return sqrt_exact(C.add(C.mul(dx,dx),C.mul(dy,dy)))
def rounded86979(word):
    word=add(word,0x3effffff|(word&0x80000000));exponent=(word>>23)&255
    if exponent<=149:word&=0x80000000 if exponent<127 else((-0x800000)>>((exponent-127)&31))&0xffffffff
    return word
def truncsat(word):
    x=fp(word)
    return 0 if math.isnan(x)or x<=0 else min(int(x),0xffffffff)
def append_queue(queue,peer,amount):
    if len(queue['entries'])==queue['capacity']:queue['capacity']=max(4,2*queue['capacity'])
    queue['entries'].append([peer,amount])


def project(s):
    return dict(pickup_capacity=len(s['rows']),pickup_count=s['count'],pickups56_cells=[list(r)for r in s['rows']],movement_sequence2412=s['sequence'],gold1456=s['gold'],earned1100=s['earned'],level1432=1,xp1436=s['xp'],pending2376=0,phase2587=1,selection_kind2585=255,generation2400=0,rng_words=list(s['words']),hp1440_bits=s['hp'],derived_bits={str(k):v for k,v in s['derived'].items()},known_player_fields={str(k):v for k,v in s['fields'].items()},xp_queue2144=dict(capacity=s['xpq']['capacity'],entries=[list(r)for r in s['xpq']['entries']]),coin_queue2156=dict(capacity=s['coinq']['capacity'],entries=[list(r)for r in s['coinq']['entries']]))


def collect(s,now):
    rows=s['rows'];n=s['count'];claimed=set();player=s['player'];packets=[];attracted=[]
    for row in rows[:n]:
        guid=read(row,16,8)
        for claim in s['claims'][:s['claim_count']]:
            if read(claim,0)==1 and read(claim,8,8)==guid:claimed.add(guid);break
    for i in range(n):
        old=rows[i]
        if read(old,8)!=0 or read(old,0)!=0:continue
        dist=distance(old,player);age=fp(C.sub(now,read(old,52)))>6 and read(old,16,8)not in claimed
        if not age and not fp(dist)<=fp(s['derived'][1560]):continue
        delay=div(dist,0x42000000 if age else 0x41c00000)
        if not fp(delay)>fp(0x3df5c28f):delay=0x3df5c28f
        row=list(old);put(row,0,1);put(row,4,add(now,delay));rows[i]=row;s['sequence']=(s['sequence']+1)&0xffffffff
        xyz=[read(old,o)for o in [40,44,48]];guid=read(old,16,8)
        payload=C.packguid(guid)+struct.pack('<4I',*xyz,s['sequence'])+b'\0'+struct.pack('<3I',256,max(1,truncsat(mul(delay,bits(1000.)))),1)+struct.pack('<3I',*player)
        packets.append([221,payload.hex()]);attracted.append(dict(index=i,delay=delay,age=age))
    eligible=[]
    for i,row in enumerate(rows[:n]):
        kind=read(row,8);marker=read(row,0)
        if kind==0:accept=marker!=0 and fp(read(row,4))<=fp(now)
        elif kind==1:
            accept=fp(distance(row,player))<=fp(s['derived'][1560])
            if not accept:accept=marker==1 and fp(read(row,4))<=fp(now)
        else:
            assert fp(distance(row,player))>3,'Nearbyresource remainsunknown'
            accept=False
        if accept:eligible.append(i)
    before_shift=[list(r)for r in rows];events=[]
    for i in reversed(eligible):
        old=rows[i];kind=read(old,8);amount=read(old,12);guid=read(old,16,8);assert read(old,0)!=2,'32070 marker2 is a real trap,not skip170'
        assert read(old,32)==0,'AuxiliaryGUID owner not restored'
        for j in range(i,n-1):rows[j]=list(rows[j+1])
        n-=1;packets.append([170,struct.pack('<Q',guid).hex()]);factor=bits(1.)
        if s['mode']==1:
            denominator=add(mul(mul(0x3f333333,bits(f32(float((s['members']-1)&0xffffffff)))),0x3e9fbe77),bits(1.));factor=div(bits(1.),denominator)
        multiplier=s['derived'][1564 if kind==0 else 1588];result=rounded86979(mul(factor,mul(multiplier,bits(f32(float(amount))))))
        if kind==0:
            if not fp(result)>1:result=bits(1.)
            award=truncsat(result);s['xp']=(s['xp']+award)&0xffffffff;assert s['xp']<5,'Crosslevel notaccepted bythiscollectorbatch'
            s['fields'][716]=s['xp'];s['fields'][717]=5
            if s['mode']:append_queue(s['xpq'],s['peer'],amount)
        else:
            award=truncsat(result);s['gold']=(s['gold']+award)&0xffffffff;s['earned']=(s['earned']+award)&0xffffffff;s['fields'][1176]=(s['gold']*10000)&0xffffffff
            if s['mode']:append_queue(s['coinq'],s['peer'],amount)
        events.append(dict(index=i,kind=kind,guid=str(guid),amount=amount,award=award))
    s['count']=n;answer=project(s);answer.update(now_bits=now,new_packets=packets)
    return answer,dict(attractions=attracted,events=events,precompaction=before_shift)


def predecessor(case,world,nav,scalars,tables,npc_def,speeds,definition,derived,fields):
    center=scalars['center_xy_bits'];height=world.height(*center);words=rng(1442695040888963407);owned=bytes.fromhex(record(5882740))
    inp=dict(id=case['id'],rng_words=words if case['rng_words']is None else case['rng_words'],counter=case['counter'],player_xyz=[*center,height],velocity_xy=[0,0],initial_backing=case['initial_backing'],distance_map=None)
    spawn_speeds=list(speeds);spawn_speeds[1]=1088421888
    born,diags=natural_reference(inp,world,nav,scalars,tables,npc_def,spawn_speeds);rows=[list(r)for r in born[-1]['records432_cells']];first=rows[0 if case['action']=='near_first'else 1];player=[read(first,o)for o in [316,320,324]]
    death=dict(rows=rows,words=tuple(born[-1]['rng_words']),counter=born[-1]['counter'],total=0,spelltotals={},kills=0,elites=0,cost=0,sets=[[],[],[]],pickups=[],pickup_count=0);casts=[]
    assert case['repeats']==2 and not case['gentle_owned_multiplier']
    for _ in range(2):
        p,hits=D.cast_reference(death,player,derived,definition,owned,world,scalars,speeds,npc_def);casts.append(p)
    s=dict(rows=[list(r)for r in death['pickups']],count=death['pickup_count'],words=death['words'],hp=derived[1536],derived=dict(derived),fields={int(k):v for k,v in fields.items()},player=player,claims=[],claim_count=0,sequence=1,gold=0,earned=0,xp=0,mode=0,members=1,peer=0,xpq=dict(capacity=0,entries=[]),coinq=dict(capacity=0,entries=[]))
    explicit=case['component']
    if explicit is not None:
        s.update(rows=[list(bytes.fromhex(h))for h in explicit['pickups56']],count=explicit['pickup_count'],claims=[list(bytes.fromhex(h))for h in explicit['claims88']],claim_count=explicit['claims_count'],player=explicit['player_xyz'],sequence=explicit['sequence'],gold=explicit['gold'],earned=explicit['earned'],mode=explicit['mode'],members=explicit['member_count'],peer=explicit['peer'])
        for key,name in [(1560,'radius'),(1564,'xp_multiplier'),(1588,'coin_multiplier')]:s['derived'][key]=explicit[name]
    return s,born,casts,diags


def main():
    batch=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir()
    expected_comparison,expected_handoff=sys.argv[3:5]
    assert sha(batch/'comparison.json')==expected_comparison and sha(batch/'task-handoff.json')==expected_handoff
    comp=load(batch/'comparison.json');hand=load(batch/'task-handoff.json');prep=load(batch/'prepared.json');manifest=load(batch/'manifest.json');runtime=load(batch/'runtime.json');terminal=load(batch/'process-terminal.json')
    assert comp['phase']=='full' and comp['cases']==comp['completed']==18 and comp['differences']==0
    prior_review=ROOT/'reports/2026-11-02-death0139-independent-review.json'
    assert sha(prior_review)=='c51bae1196a54df1ec75ed7e74ddab09701b7bd340882f32d08cc269e8ea0f04'
    dependency=load(prior_review);helpers=dict(dependency['helpers']);helpers['review_death139.py']='fe7790f0adcb3e3d5010d53c44f375bec5bbee6d3fe780873a6e1613afe11e6a'
    for name,h in helpers.items():assert sha(ROOT/'scripts'/name)==h
    assert sha(ROOT/dependency['review_file'])==dependency['review_sha256']=='8a2b71be6089ddd93a200ef5f182e14a4a36c7ff405c85128f99dc4d74e92a02'
    author=hand.get('files',hand.get('frozen_author_files',hand.get('owned_files')));assert author
    for name,h in author.items():assert sha(ROOT/name)==h
    sources=comp['source_before'];assert sources==comp['source_after']==prep['source_before']
    for name,h in sources.items():assert sha(ROOT/name)==h==sha(batch/'source-snapshot'/name)
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])
    for name,h in comp['artifacts'].items():assert sha(batch/name)==h
    for name,h in prep['frozen'].items():assert sha(batch/name)==h
    assert prep['expected_before_original'] and not prep['original_inputs_contain_expected'] and comp['expectation_reads_forbidden']==[]
    cfg=load(batch/'config.json');gate=ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json'
    assert sha(gate)=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
    assert cfg['snapshot_sha256']=='ed3a755752ddf9907712b408f7ef042f5a9407d684d0aa6afd3f0a394bbd7ce2' and cfg['game_pointer']==14685248 and cfg['app_pointer']==14680072
    assert sha(Path(cfg['snapshot_path']))==cfg['snapshot_sha256'] and cfg['input_sha256']==sha(batch/'inputs.json')
    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA;original=parse_module(raw);private=(batch/manifest['module_file']).read_bytes();assert hashlib.sha256(private).hexdigest()==manifest['module_sha256'];modified=parse_module(private)
    additions=[('research139_spawn5719',0,5719),('research139_npc_cast922',0,922),('research139_collect2890',0,2890),('research139_spawn_stack0',3,0)]
    assert modified['exports']==original['exports']+additions and len(original['imports'])==882
    assert [(v['module'],v['name'])for v in original['imports']]==[(v['module'],v['name'])for v in manifest['original_imports']]
    for a,b in zip(original['sections'],modified['sections'],strict=True):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==private[b['start']:b['end']]
    bindings={};texts={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        for key,row in manifest['functions'].items():
            idx=int(key);a,z=original['bodies'][idx];assert hashlib.sha256(raw[a:z]).hexdigest()==row['body_sha256'];start,end=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();stream.seek(start);wat=stream.read(end-start);assert wat==(batch/'static'/(key+'.wat')).read_bytes() and hashlib.sha256(wat).hexdigest()==row['WAT_sha256'];bindings[key]=row;texts[idx]=wat.decode()
    assert original['types'][original['decl'][2890-882]]==('7f','') and original['types'][original['decl'][4677-882]]==('7f7f','')
    assert all(t in texts[2890]for t in ['f32.sqrt','f32.const 0x1.8p+2','f32.const 0x1.8p+4','f32.const 0x1p+5','call 27650','call 32070','call 4677','call 29338'])
    panic=texts[32070];assert 'i32.const 56'in panic and 'memory.copy'in panic and 'i32.const 2\n          i32.eq\n          br_if 0 (;@3;)'in panic and 'call 81894\n        unreachable'in panic
    assert 'i32.store offset=1456'in texts[29338] and 'i32.store offset=1100'in texts[29338]
    def data(address,size):
        result=bytearray(size)
        for base,pos,n in original['data_segments']:
            if base is None:continue
            lo,hi=max(base,address),min(base+n,address+size)
            if lo<hi:result[lo-address:hi-address]=raw[pos+lo-base:pos+hi-base]
        return bytes(result)
    definition=data(5882740,88);npc_def=data(5830904,72);assert definition.hex()==manifest['definition']['raw88_hex']
    classdata=data(5877920,108);racedata=data(5874636,44);ptr,n=struct.unpack_from('<II',racedata,16);derived,_,_,fields=default_stats(struct.unpack_from('<II',classdata,72),list(struct.iter_unpack('<II',data(ptr,n*8))))
    tables=[list(struct.unpack('<4f',data(p,16)))for p in [14426512,14426528,14426544,14426560]];speeds=list(struct.unpack('<6I',data(1593032,24)));world,nav,scalars=load_world(comp['world_provenance'])
    cases=load(batch/'inputs.json');expected=load(batch/'expected.json');actual=[json.loads(x)for x in(batch/'stdout.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==18
    counts=Counter();diagnostics=[];groups=Counter()
    def check_rows(label,want,got):
        assert len(want)==len(got)
        for row,hx in zip(want,got,strict=True):
            raw=bytes.fromhex(hx);assert len(row)==len(raw)
            for i,(v,b)in enumerate(zip(row,raw,strict=True)):
                if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
                else:assert v==b,(label,i,v,b);counts[label+'_known']+=1
    for case,e,a in zip(cases,expected,actual,strict=True):
        assert case['id']==e['id']==a['id'] and case==e['input'];groups[e['group']]+=1
        s,born,casts,position_diags=predecessor(case,world,nav,scalars,tables,npc_def,speeds,definition,derived,fields)
        assert project(s)==e['precollection'],('precollection',case['id'])
        for p,g in zip(born,a['answers'],strict=True):
            check_rows('producer',p['records432_cells'],g['records432_hex']);assert{k:v for k,v in p.items()if k!='records432_cells'}=={k:v for k,v in g.items()if k!='records432_hex'}
        for p,g in zip(casts,a['cast_stages'],strict=True):
            check_rows('NPC',p['records432_cells'],g['records432_hex']);check_rows('cast_pickup',p['pickups56_cells'],g['pickups56_hex'])
            excluded=['records432_cells','records432_hex','pickups56_cells','pickups56_hex','known_packets','new_packets']
            assert{k:v for k,v in p.items()if k not in excluded}=={k:v for k,v in g.items()if k not in excluded}
            cursor=0
            for packet in p['known_packets']:
                cursor=next(i+1 for i in range(cursor,len(g['new_packets']))if g['new_packets'][i]==packet)
            counts['full922_checked']+=1
        assert len(a['collection_stages'])==len(case['collect_times'])==len(e['expected']);previous=None
        for now,want,got in zip(case['collect_times'],e['expected'],a['collection_stages'],strict=True):
            before_rows=[list(r)for r in s['rows']];answer,trace=collect(s,now);assert answer==want,('stored_expectation',case['id'],now)
            check_rows('collect_pickup',answer['pickups56_cells'],got['pickups56_hex']);check_rows('precollect_pickup',before_rows,got['before_pickups56_hex'])
            # Actual unknown input bytes remain observations. Reproduce only
            # the proven writes and whole56B shifts; never fill a model None.
            relative=[bytearray.fromhex(h)for h in got['before_pickups56_hex']]
            oldcount=C.u(bytes.fromhex(got['raw_game_before_hex']),1876)
            for attraction in trace['attractions']:
                row=relative[attraction['index']];put(row,0,1);put(row,4,add(now,attraction['delay']))
            for event in trace['events']:
                index=event['index']
                for j in range(index,oldcount-1):relative[j]=bytearray(relative[j+1])
                oldcount-=1
            assert oldcount==answer['pickup_count'] and [r.hex()for r in relative]==got['pickups56_hex']
            counts['relative_pickup_bytes_including_None']+=sum(len(r)for r in relative)
            for k,v in answer.items():
                if k=='pickups56_cells':continue
                if k=='known_player_fields':
                    seen=dict(got['player_fields'])
                    for key,value in v.items():assert seen[int(key)]==value;counts['known_player_fields']+=1
                else:assert v==got[k],('actual',case['id'],now,k,v,got[k])
            pre=bytes.fromhex(got['raw_game_before_hex']);post=bytes.fromhex(got['raw_game_after_hex']);assert len(pre)==len(post)==2592
            assert [C.u(pre,1720+4*i)for i in range(4)]==[C.u(post,1720+4*i)for i in range(4)]==answer['rng_words']
            assert pre[2587]==post[2587]==1 and C.u(pre,1432)==C.u(post,1432)==1 and C.u(pre,1788)==C.u(post,1788) and C.u(pre,1792)==C.u(post,1792)==4
            assert got['units_before_hex']==got['units_after_hex']==''.join(a['cast_stages'][-1]['records432_hex']) and got['claims_before_hex']==got['claims_after_hex']==''.join(bytes(r).hex()for r in s['claims'])
            for cap,ptr,num in [(2108,2112,2116),(2144,2148,2152),(2156,2160,2164)]:assert C.u(pre,cap)<=512 and C.u(post,num)<=C.u(post,cap)
            if case['component']is None and previous is None:
                inherited=bytearray.fromhex(a['cast_raw_games'][-1]['after_hex']);put(inherited,2352,now);assert inherited==pre;counts['cast_to_collect_inherited_Game_bytes']+=2592
            elif previous is not None:
                inherited=bytearray(previous);put(inherited,2352,now);assert inherited==pre;counts['collect_to_collect_inherited_Game_bytes']+=2592
            if previous is not None:
                assert got['before_pickups56_hex']==previous_pickups
            previous=post;previous_pickups=got['pickups56_hex'];counts['full2890_checked']+=1;counts['collector_packets']+=len(answer['new_packets']);counts['collector_packet_bytes']+=sum(len(h)//2 for _,h in answer['new_packets']);counts['attractions']+=len(trace['attractions']);counts['consumptions']+=len(trace['events']);counts['NPC_conserved_bytes']+=len(bytes.fromhex(got['units_before_hex']));counts['claims_conserved_bytes']+=len(bytes.fromhex(got['claims_before_hex']))
            for event in trace['events']:counts['XP_awards'if event['kind']==0 else'coin_awards']+=1
            diagnostics.append(dict(id=case['id'],now=now,trace=trace))
        assert a['world124_before_hex']==a['world124_after_hex'] and a['world_data_digest_before']==a['world_data_digest_after'] and a['stack_after']==1048576
    assert runtime==comp['runtime'] and terminal==comp['process'] and terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<60
    assert runtime['full5719_calls']==72 and runtime['full922_calls']==36 and runtime['full2890_calls']==counts['full2890_checked'] and runtime['snapshot_restores']==18 and runtime['denied_imports']==882 and runtime['actual_host_calls']==0
    assert comp['comparison']['known56bytes']==counts['collect_pickup_known'] and comp['comparison']['unknown56bytes']==counts['collect_pickup_None'] and comp['comparison']['complete_collector_packets']==counts['collector_packets']
    for name,h in author.items():assert sha(ROOT/name)==h
    assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    save(out/'reference-diagnostics.json',diagnostics)
    result=dict(status='pass_current139_sameGame_death_to_belowthreshold_collection',reviewer='/root',author='/root/collection139_finish',comparison_sha256=expected_comparison,handoff_sha256=expected_handoff,reviewer_source_sha256=sha(Path(__file__)),helper_sha256=helpers,author_files=author,cases=18,groups=dict(groups),counts=dict(counts),source_files=len(sources),source_edges=len(edges),current_function_bindings=bindings,all_nonexport_sections_byte_identical=True,author_process=terminal,reviewer_original_executions=0,reviewer_author_model_checker_builder_executions=0,limitations=['Original-side18healthyv2phase0snapshots;notfreshApp/full1108;rootcompleteopeningisasetseparatebatch.','Sevennaturaldeathchainsplus11explicitcomponentoverrides;NPC4keptinallcases,emptyoractual88claims.Counters/phase/playeractionsarecontrolledinputs.','Experienceonlybelowfirstthreshold5;gain4677realpath,nolevelup2181orselect1093acceptanceinthisbatch.','Fullcollector221/170checked;priorcast592andHP169andgrowthUIpacketsnotfullyreconstructed.','Selectedmarker2isarealoriginal32070trapaftermove/count--;nowmodelrejects,failedprebatchpreservednotregisteredpassing.','KnownNonepickupcellsretained;completeactualNPC/claimsbytesconservedbutphysicalallocator/BTree/queueaddressesremainobservations.','NaNXPmultiplierandnegativecoinmodifierareexplicitcomponentfixtures,notnormalproducerclaims.','Reusedindependentreferencesarecurrent139body/data-bound;nooldversionpassedcasetransfer.NoWindowsnative/mainloop/fullgame.'])
    save(out/'review.json',result);print(json.dumps(dict(out=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts))))


if __name__=='__main__':main()
