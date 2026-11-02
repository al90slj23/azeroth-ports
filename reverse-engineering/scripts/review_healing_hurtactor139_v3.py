#!/usr/bin/env python3
"""Different-author readonly Regen/Leech shared-ledger v3 review.

Only prior independently reviewed reference functions are imported. No author
production module,checker,builder,runner or original target is executed.
"""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import ast,copy,hashlib,json,math,os,re,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_thunder_clap139 as T
import review_player_update139 as U
import review_cast139 as C
import review_growth139 as G
import review_growth_world139 as W
import review_opening139 as O
import review_death139 as D
from review_initial139 import record as initial_record
from review_world_position139 import load_world
from review_combat139 import sha,parse_module,local_closure,fp,bits
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
HURT=ROOT/'evidence/hurtactor139-v3-oracle-20261102T121344.276555Z'
HAND='89dc742f740d5d8dde81618322b2e89c80bd7fe7e0d99ed77305076161119239'
BATCHES=[('healing139-v3-oracle-20261102T121237.785322Z','5d773c21620cb1334a816776d129b1cf8859e5d0c2ca0b9605e9585446733e20',5,62,217),('hurtactor139-v3-oracle-20261102T121344.276555Z','7925e334e6a9328ff3bf57c28afa0cea54325b34cda893a538e93a66f4a142bf',4,62,217)]
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,x:Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
u=lambda b,p=0:struct.unpack_from('<I',b,p)[0]
def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False

def ledger():return dict(event_counter960='0',accepted_count1016='0',reason_totals64={})
def account(state,reason,amount,now,events,*,damage=False):
    # Current36520 damage counter precedes2077; finite positive domain here.
    value=C.rational(amount)
    if not damage and value<=0:return
    assert value>0
    state['event_counter960']=str((int(state['event_counter960'])+1)&((1<<64)-1));state['accepted_count1016']=str((int(state['accepted_count1016'])+1)&((1<<64)-1))
    old=C.f64(int(state['reason_totals64'].get(reason,'0')))
    state['reason_totals64'][reason]=str(C.bits64(old+float(value)))
    if not damage:events.append(dict(reason_id=reason,amount_bits=amount,now_bits=now,event_id=int(state['event_counter960']),resolved_spell_id_or_zero=0,arg3_descriptor_head=-1 if reason=='regen'else-2,arg4_descriptor_head=0 if reason=='regen'else-1))
def heal_number(hp,maximum,request):
    candidate=C.add(hp,request);result=maximum if C.rational(candidate)>C.rational(maximum)else candidate
    return result,C.sub(result,hp)
def regen(state,L,now,dt):
    g=state['g'];old=g['current_hp_bits'];maximum=g['derived_bits']['1536'];extra=C.mul(maximum,g['derived_bits']['1620'])if C.rational(C.sub(now,state['scalar']['1652']))>=3 else 0
    request=C.mul(C.ONE,C.mul(dt,C.add(g['derived_bits']['1576'],extra)))
    hp=old
    if C.rational(old)<C.rational(maximum):
        #2123 actual candidate is (old+request)+live0, preserving that f32 add.
        candidate=C.add(C.add(old,request),0);hp=maximum if C.rational(candidate)>C.rational(maximum)else candidate
        g['player_fields'].update({'22':max(0,math.ceil(C.rational(hp))),'28':max(0,math.ceil(C.rational(maximum)))})
    delta=C.sub(hp,old);positive=delta if C.rational(delta)>0 else 0;amount=request if C.rational(request)<C.rational(positive)else positive
    g['current_hp_bits']=hp;events=[];account(L,'regen',amount,now,events)
    return request,amount,events
def tick_hurt(state,L,now,dt,classes,races,definitions):
    state=copy.deepcopy(state);g=state['g'];g['now_bits']=now;state['scalar']['2352']=now
    retained=[i for i in range(state['count'])if C.rational(now)<C.rational(U.read(state['live'][i],24))];expired=[U.read(state['live'][i],20)for i in range(state['count'])if i not in retained]
    for row in state['live'][:state['count']]:assert U.read(row,28)==0
    if expired:
        prior=copy.deepcopy(state['live'])
        for j,i in enumerate(retained):state['live'][j]=prior[i]
        state['count']=len(retained);U.recalculate(state,classes,races);U.sync_aura(state)
    request,amount,events=regen(state,L,now,dt)
    # Independent quiet1238 scheduler: racial remains on real42s cooldown.
    alive=[r for r in state['NPC']if U.read(r,0)==0];remaining=C.sub(state['scalar']['1628'],dt)
    if C.rational(remaining)<=0:
        assert all(C.rational(U.distance(r,state['player']))>36 for r in alive);remaining=0x3e19999a
    state['scalar']['1628']=remaining
    for index,hx in enumerate(g['owned_records80_hex']):
        row=bytearray.fromhex(hx);definition=next(v[1]for v in definitions.values()if v[0]==u(row));remaining=C.sub(u(row,8),dt)
        if C.rational(remaining)<=0:
            spell=u(definition,44);U.attempt(state,spell)
            radius=u(definition,56)if definition[84]==5 else C.mul(C.mul(C.mul(g['derived_bits']['1580'],u(definition,60)),u(row,24)),u(row,64))
            assert all(C.rational(U.distance(r,state['player']))>C.rational(C.mul(radius,radius))for r in alive);remaining=0x3e4ccccd
        U.put(row,8,remaining);g['owned_records80_hex'][index]=row.hex()
    remaining=C.sub(U.read(state['racial'],8),dt);assert C.rational(remaining)>0,'No second racial due in admittedmatrix';U.put(state['racial'],8,remaining)
    return state,dict(regen_request_bits=request,regen_accounted_bits=amount,heal_events=events,expired_spells=expired,retained_source_indices=retained,expiry_recalculate1542_called=bool(expired),expiry_sync1173_called=bool(expired),known_packets=[])

def main():
    start=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir();assert sha(SOURCE)==WASM and sha(HURT/'task-handoff.json')==HAND
    hand=load(HURT/'task-handoff.json');authors=hand['frozen_author_files'];assert len(authors)==8
    for n,h in authors.items():assert sha(ROOT/n)==h
    for n,h in hand['frozen_shared_core_unchanged'].items():assert sha(ROOT/n)==h
    prior=ROOT/'evidence/hurtactor139-oracle-20261102T114019.166570Z/task-handoff.json';assert sha(prior)==hand['v2_handoff_sha256']=='853c2ecc932ac946586f6166f083295fb9b4eb522d07f87609f2082f70d385b5'
    v2=load(prior);assert len(v2['frozen_author_files'])==11
    for n,h in v2['frozen_author_files'].items():assert sha(ROOT/n)==h
    v2review=ROOT/'evidence/healing-hurtactor139-v2-fidelity-20261102T120709.762548Z/task-handoff.json';assert sha(v2review)=='fbc171f9445f5fc20bd81ca7ae8bc156628aacf65727610d1d42c16df8506f37'
    assert 'not_accepted' in json.dumps(load(v2review))
    for row in v2['prior_studies_excluded']:assert sha(ROOT/row['path']/'comparison.json')==row['comparison_sha256']
    revision=v2['metadata_revision2'];prior_archive=ROOT/revision['prior_handoff_path'];assert sha(prior_archive)==revision['prior_handoff_sha256']
    archive=ROOT/revision['prior_exact11_archive'];receipt=archive.parent/'author-revision1-receipt.json';assert sha(receipt)==revision['prior_archive_receipt_sha256'];old=load(receipt);assert len(old['files'])==11
    for n,h in old['files'].items():assert sha(archive/n)==h
    # Read-only AST/text proof that one explicit input object supplies both sides.
    parameter_source_proof={}
    for name in ('healing','hurtactor'):
        checker=ROOT/f'scripts/check_{name}139_v3.py';driver=ROOT/f'scripts/run_{name}139_v3_oracle.mjs';text=checker.read_text();tree=ast.parse(text)
        incoming_calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='resolve_prefix139'];assert len(incoming_calls)==1
        kw={k.arg:k.value for k in incoming_calls[0].keywords};assert ast.dump(kw['contact_flag'])==ast.dump(ast.parse("incoming_control['contact_flag']",mode='eval').body)
        assert "assert incoming_control['category']==incoming_control['spell_id']==0" in text
        assert 'incoming_control=incoming_control' in text
        js=driver.read_text();assert "const ic=c.incoming_control;" in js
        assert "ic.contact_flag!==1||ic.category!==0||ic.spell_id!==0" in js
        call=re.search(r"call\('1076',e\.research139_heal_incoming1076,G,fv\(c\.hurt_amount_bits\),(source|incomingSource),ic\.contact_flag,ic\.category,ic\.spell_id\)",js);assert call
        assert "getBigUint64(u(G+1788)+112,true)" in js
        assert 'incoming_control_observed:incomingControlObserved' in js
        parameter_source_proof[name]=dict(checker_sha256=sha(checker),driver_sha256=sha(driver),actual_call=call[0],expected_contact_argument=ast.unparse(kw['contact_flag']),actual_guid='first actual full1108 NPC432 at +112',category_and_param5_controlled=0)
    helpers={**T.HELPERS,'scripts/review_thunder_clap139.py':sha(ROOT/'scripts/review_thunder_clap139.py')}
    for n,h in helpers.items():assert sha(ROOT/n)==h
    raw=SOURCE.read_bytes();original=parse_module(raw)
    def data(address,size):
        result=bytearray(size)
        for at,pos,n in original['data_segments']:
            if at is None:continue
            lo,hi=max(address,at),min(address+size,at+n)
            if lo<hi:result[lo-address:hi-address]=raw[pos+lo-at:pos+hi-at]
        return bytes(result)
    text=lambda p,n:data(p,n).decode();word=lambda p:u(data(p,4));abilities={}
    for i in range(114):
        p=5882740+88*i;b=data(p,88);abilities[text(u(b,12),u(b,16))]=(p,b,tuple(data(u(b,36),u(b,40))))
    cls=data(5877920,108);assert u(cls,80)==0x3c75c28f
    classes={1:dict(hp_armor=[u(cls,72),u(cls,76)],ability_pointer=5882740)};kit=[text(p,n)for p,n in struct.iter_unpack('<II',data(u(cls,32),8*u(cls,36)))];defs={k:abilities[k]for k in kit}
    race=data(5874636,44);racial_name=text(u(race,24),u(race,28));races={1:dict(ability_pointer=abilities[racial_name][0],modifiers=list(struct.iter_unpack('<II',data(u(race,16),8*u(race,20)))))}
    zone=data(5871348,152);zones=[dict(xyz=[u(zone,104),u(zone,108),u(zone,116)])];heading=[list(struct.unpack('<4f',data(p,16)))for p in[14426512,14426528,14426544,14426560]];speeds=list(struct.unpack('<6I',data(1593032,24)));spawn_speeds=list(speeds);spawn_speeds[1]=1088421888;normal=data(5830904,72);eligible=[j for j in range(12)if word(5830904+72*j+68)==1 and math.isfinite(fp(word(5830904+72*j+64)))];minutes=word(u(zone,72)+336);cooldown=struct.unpack('<5I',data(5912332,20));damage=struct.unpack('<5I',data(5912384,20));definition=data(5882916,88);perception=data(5891892,88)
    wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';wr=load(wp);assert sha(wp)=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48';world,nav,scalars=load_world(dict(receipt=str(wp),receipt_sha256=sha(wp),world_artifacts=wr['world_artifacts']));scalars['heading_bits']=u(zone,116)
    literal={}
    for p in(1592624,1591852):
        b=data(p,44);literal['regen'if p==1592624 else'leech']={str(k):text(u(b,k),u(b,k+4))for k in(0,8,16,24,32)}
    assert literal['regen']['0']=='regen'and literal['leech']['0']=='leech'
    counts=Counter();bindings={};batchrows=[];reference=[];parameter_receipts=[];breakdown_seen={};db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.execute('pragma query_only=on')
    def cells(label,want,hx):
        seen=bytes.fromhex(hx);assert len(want)==len(seen)
        for v,w in zip(want,seen):
            if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(w)
            else:assert v==w,(label,v,w);counts[label+'_known']+=1
    def player(obs,state,label):
        want=U.project(state);cap=obs['capture'];assert cap['projection']==want['growth'],(label,'growth');assert G.tree_fields(cap,bytes.fromhex(cap['raw_game2592_hex']))==want['growth']['player_fields']
        for k in('racial80_hex','scalar','source_flags','spell_sets'):assert obs[k]==want[k],(label,k)
        for k,width in(('live',32),('aura',16)):
            for field in('capacity','count')+(('flag2569',)if k=='aura'else()):assert want[k][field]==obs[k][field],(label,k,field)
            for row,hx in zip(want[k]['storage'],obs[k]['storage'],strict=True):assert len(row)==width;cells(k,row,hx)
        game=bytes.fromhex(cap['raw_game2592_hex']);assert u(game,1440)==state['g']['current_hp_bits']and u(game,1652)==state['scalar']['1652'];assert game[387]==0
        assert all(u(game,p)==0 for p in(1676,1700,2032,176,600,2056,2044,648,660,2116)),'Actualdefaultsourceownersnotempty'
        counts['logical_player_maps']+=1
    def accounting(obs,L,label,player_obs=None):
        for k,v in L.items():assert obs[k]==v,(label,k,v,obs[k])
        aggregate=bytes.fromhex(obs['accounting_struct68_hex']);assert len(aggregate)==68 and struct.unpack_from('<Q',aggregate,16)[0]==int(L['accepted_count1016'])
        if player_obs is not None:
            game=bytes.fromhex(player_obs['capture']['raw_game2592_hex']);assert struct.unpack_from('<Q',game,960)[0]==int(L['event_counter960'])and game[1000:1068]==aggregate
        decoded={}
        for row in obs['stats_keys']:
            raw96=bytes.fromhex(row['raw96']);assert len(raw96)==96 and row['raw96']==obs['stats']['storage'][row['index']]
            assert struct.unpack_from('<Q',raw96,8)[0]==int(row['total64']);reason=row['reason'];decoded[reason]=C.bits64(C.f64(decoded.get(reason,0))+C.f64(int(row['total64'])))
        assert {k:str(v)for k,v in decoded.items()}==L['reason_totals64']
        expected=[dict(name=literal[k]['24'],icon=literal[k]['32'],total64=v,owns=0,nested_count=0)for k,v in L['reason_totals64'].items()if k in literal]
        assert [{k:r[k]for k in expected[0]}for r in obs['breakdown']]==expected if expected else obs['breakdown']==[]
        for row in obs['breakdown']:
            raw48=bytes.fromhex(row['raw48']);assert len(raw48)==48 and struct.unpack_from('<Q',raw48,8)[0]==int(row['total64'])and u(raw48,4)==len(row['icon'].encode())and u(raw48,36)==len(row['name'].encode())and u(raw48,24)==0 and raw48[40]==0 and u(raw48,28)==0xffffffff
            if row['name']in breakdown_seen:
                old=breakdown_seen[row['name']];assert old[:8]+old[16:]==raw48[:8]+raw48[16:];counts['inherited_Vec48_nonvalue_bytes']+=40
            breakdown_seen[row['name']]=raw48
        for name in('source_registry','saved_history'):assert[obs[name][k]for k in('capacity','pointer','count')]==[0,8,0]
        counts['semantic_ledger_snapshots']+=1;counts['Vec48_rows']+=len(expected)
    for batchname,compSHA,ncases,nsources,nedges in BATCHES:
        batch=ROOT/'evidence'/batchname;assert sha(batch/'comparison.json')==compSHA
        comp=load(batch/'comparison.json');prep=load(batch/'prepared.json');m=load(batch/'manifest.json');assert len(m['functions'])==(31 if ncases==5 else 35);assert m['functions']['1076']['signature']==['7f7d7e7f7f7f',''];cfg=load(batch/'config.json');sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==nsources and len([n for n in sources if n.startswith('reconstruction/')])==47
        for n,h in sources.items():assert sha(ROOT/n)==sha(batch/'source-snapshot'/n)==h
        assert local_closure(sources)==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(comp['source_import_edges'])==nedges
        for table in(comp['artifacts'],comp['frozen'],prep['frozen']):
            for n,h in table.items():assert sha(batch/n)==h,(batchname,n)
        assert comp['differences']==0 and comp['cases']==comp['completed_cases']==ncases and prep['expected_before_original']and not prep['original_input_contains_expected']and comp['forbidden_model_reads']==[]
        for n in sources:
            if n.startswith('reconstruction/'):
                for node in ast.walk(ast.parse((ROOT/n).read_text())):
                    if isinstance(node,ast.Call):
                        fn=node.func;tag=fn.id if isinstance(fn,ast.Name)else fn.attr if isinstance(fn,ast.Attribute)else'';assert tag not in('open','read_bytes','read_text','Popen','system','eval','exec','__import__')
        private_raw=(batch/m['module_file']).read_bytes();private=parse_module(private_raw);assert len(original['sections'])==len(private['sections'])
        for a,b in zip(original['sections'],private['sections']):
            assert a['kind']==b['kind']
            if a['kind']!=7:assert raw[a['start']:a['end']]==private_raw[b['start']:b['end']]
        assert private['exports']==original['exports']+[tuple(x)for x in m['added_exports']]and len(original['imports'])==882
        with(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
            for idx in sorted(set(map(int,m['functions']))|{1466,2123,913,18421,2077,28155,19598,36520,26202,30861,1600,925,1076}):
                a,z=original['bodies'][idx];ws,we=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();stream.seek(ws);wat=stream.read(we-ws);proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest());bindings[str(idx)]=proof;(out/f'{idx}.wat').write_bytes(wat)
                if str(idx)in m['functions']:assert all(proof[k]==m['functions'][str(idx)][k]for k in proof)
        assert'offset=1440'not in(out/'1466.wat').read_text()
        # Bound current1076 signature and actual925 incoming call. Parameter5 is
        # controlled0 for category0, not claimed to duplicate925 dynamicqueueindex.
        t1076=(out/'1076.wat').read_text();t925=(out/'925.wat').read_text()
        assert '(param i32 f32 i64 i32 i32 i32)' in t1076.splitlines()[0]
        assert 'local.get 57\n          i32.const 1\n          i32.const 0\n          local.get 2\n          call 1076' in t925
        assert 'local.get 4\n            i32.eqz\n            br_if 0' in t1076
        n1076=[' '.join(v.split())for v in t1076.splitlines()]
        refs5=[(j,v)for j,v in enumerate(n1076)if v in('local.get 5','local.set 5','local.tee 5')]
        assert refs5[:3]==[(3397,'local.get 5'),(3400,'local.get 5'),(3424,'local.set 5')]
        assert n1076[3394:3402]==['local.get 4','i32.eqz','br_if 0 (;@4;)','local.get 5','i32.eqz','br_if 0 (;@4;)','local.get 5','call 4562']
        assert n1076[3443:3448]==['local.get 4','i32.const 1','i32.sub','br_table 1 (;@5;) 2 (;@4;) 0 (;@6;)','end']
        assert n1076[3448:3457]==['local.get 11','i32.const 8','i32.add','i32.const 5909746','i32.const 5','call 20060','local.get 11','i32.load offset=12','local.set 5']
        # Category0 skips both entry-param5 reads, follows br_table default,
        # and overwrites local5 before any subsequent metadata use. This does
        # not validate history/callback/category semantics outside this domain.
        # Healing caller descriptor metadata remains static-only (not sampled).
        t2123=(out/'2123.wat').read_text();t28155=(out/'28155.wat').read_text();t913=(out/'913.wat').read_text();assert'i32.const 1592624'in t2123 and'call 28155'in t2123 and'i64.const -4294967296'in t28155
        leech='\n'.join(t913.splitlines()[5602:5666]);assert'i32.const -2'in leech and'i32.const -1'in leech and'call 1466'in leech
        assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'and sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(cfg['range_file']))==2318
        cases=load(batch/'inputs.json');authorE=load(batch/'expected.json');actual=[json.loads(x)for x in(batch/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(authorE)==len(actual)==ncases
        for case,E,A in zip(cases,authorE,actual,strict=True):
            breakdown_seen.clear()
            assert case==E['input']and case['id']==E['id']==A['id'];op,_=O.reference(dict(id=case['id'],app_seed_u64=case['app_seed_u64']),world,nav,scalars,heading,normal,spawn_speeds,classes,races,zones,eligible,minutes);opening=op['projection'];initial,_=G.reference(dict(id=case['id'],seed_u64=op['constructor_seed_u64'],amount=0,select_index=None),classes,races,zones,kit,defs,cooldown,damage);before=initial['before'];before['rng_words']=opening['rng_words'];gain,index,selected,_=W.grow(before,case,classes,races,kit,defs,cooldown,damage,W.inactive(opening['units']['storage']));assert index==0 and gain['candidates'][0]['ability_id']=='thunder_clap'
            assert A['opening']['packets']==opening['packets']and A['new_Game_pointer']!=A['old_snapshot_Game_not_target']==14685248
            ic=case['incoming_control'];assert ic==dict(contact_flag=1,category=0,spell_id=0)
            npc_source=str(D.read(opening['units']['storage'][0],112,8));control=dict(ic,source_guid=npc_source)
            assert control==E['incoming_control_expected']==A['incoming_control_observed']
            assert control['source_guid']==str(struct.unpack_from('<Q',bytes.fromhex(A['warmup']['capture']['background']['units']['storage'][0]),112)[0])
            parameter_receipts.append(dict(batch=batchname,id=case['id'],independent_control=control,expected_equal=True,actual_equal=True))
            counts['input_parameter_fidelity_cases']+=1
            state=dict(g=copy.deepcopy(selected['projection']),live=copy.deepcopy(selected['live32_cells'])+[[None]*32 for _ in range(3)],count=1,aura=[],aura_count=0,aura_flag=None,racial=list(bytes.fromhex(initial_record(5891892))),scalar={str(k):v for k,v in[(2352,0),(1628,0),(1444,0),(1448,0),(1344,0),(1348,0),(764,0),(1648,0x40e00000),(1652,0xc1200000)]},sets=[[],[],[]],NPC=copy.deepcopy(opening['units']['storage']),player=opening['player_xyz']);state['g']['now_bits']=0;U.sync_aura(state);player(A['player_before'],state,'initial')
            state,_=U.tick(state,0x3f800000,0x3f800000,classes,races,defs,perception);L=ledger();player(A['warmup'],state,'warmup');accounting(A['warmup_healing'],L,'warmup',A['warmup'])
            g=state['g'];incoming=C.mul(case['hurt_amount_bits'],C.sub(C.ONE,g['derived_bits']['1568']));g['current_hp_bits']=C.sub(g['current_hp_bits'],incoming);assert C.rational(g['current_hp_bits'])>0;state['scalar']['1652']=0x3f800000;g['player_fields'].update({'22':math.ceil(C.rational(g['current_hp_bits'])),'28':math.ceil(C.rational(g['derived_bits']['1536']))});player(A['hurt'],state,'actual1076');accounting(A['hurt_healing'],L,'actual1076',A['hurt']);assert struct.unpack_from('<d',bytes.fromhex(A['hurt']['capture']['raw_game2592_hex']),992)[0]==float(C.rational(incoming));counts['full1076']+=1
            if 'updates'in case:
                assert U.project(state)==E['hurt'];previous=A['hurt']
                for j,(control,obs)in enumerate(zip(case['updates'],A['player_stages'],strict=True)):
                    inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);U.put(inherited,2352,control['now_bits']);assert inherited.hex()==obs['before']['capture']['raw_game2592_hex'];counts['inherited_Game2592_bytes']+=2592
                    state,d=tick_hurt(state,L,control['now_bits'],control['dt_bits'],classes,races,defs);want=U.project(state);assert want==E['stages'][j];assert L==E['healing'][j];player(obs['after'],state,('regen',j));accounting(obs['healing'],L,('regen',j),obs['after'])
                    for k in('regen_request_bits','regen_accounted_bits','heal_events','expired_spells','retained_source_indices','expiry_recalculate1542_called','expiry_sync1173_called','known_packets'):assert d[k]==E['diagnostics'][j][k],('regen',j,k)
                    assert obs['after']['capture']['background']==A['player_before']['capture']['background'];counts['positive_regen_events']+=len(d['heal_events']);counts['zero_regen_steps']+=not d['heal_events'];counts['full2123']+=1;previous=obs['after']
                reference.append(dict(batch=batchname,id=case['id'],player=U.project(state),ledger=copy.deepcopy(L)))
            else:
                g=state['g'];owned=bytes.fromhex(g['owned_records80_hex'][1]);assert u(owned,4)==1;derived={int(k):v for k,v in g['derived_bits'].items()};i,k=case['action']['first'],case['action']['second'];pa=T.position(state['NPC'][i],0x3f800000);pb=T.position(state['NPC'][k],0x3f800000);playerXYZ=[C.mul(C.add(pa[0],pb[0]),0x3f000000),C.mul(C.add(pa[1],pb[1]),0x3f000000),0];height=world.height(*playerXYZ[:2]);playerXYZ[2]=height if height is not None else pa[2];assert playerXYZ[2]==case['action']['height_bits'];state['player']=playerXYZ
                s=dict(rows=copy.deepcopy(state['NPC']),words=list(g['rng_words']),sets=copy.deepcopy(state['sets']),total=0,spelltotals={},kills=0,elites=0,counter=opening['counter'],sequence=1,cost=0,pickups=copy.deepcopy(opening['pickups']['storage']),pickup_count=opening['pickups']['count']);previous=A['controlled_before']
                for j,(now,obs)in enumerate(zip(case['casts'],A['cast_stages'],strict=True)):
                    inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);U.put(inherited,2352,now);assert inherited.hex()==obs['before']['capture']['raw_game2592_hex'];counts['inherited_Game2592_bytes']+=2592;oldrows=copy.deepcopy(s['rows'])
                    result,diag=T.cast(s,playerXYZ,now,derived,definition,owned,world,scalars,speeds,normal,counts);heal_events=[]
                    for hit in diag['hits']:
                        row=next(r for r in oldrows if str(D.read(r,112,8))==hit['target']);mult=C.ONE
                        if C.rational(now)<C.rational(D.read(row,148)):mult=C.add(mult,D.read(row,144))
                        term=D.read(row,152)if C.rational(now)<C.rational(D.read(row,156))else D.read(row,160)if C.rational(now)<C.rational(D.read(row,164))else 0;mult=C.add(C.add(C.add(mult,term),D.read(row,368)),0);school=0x3dcccccd if definition[85]&254==2 and C.rational(now)<C.rational(D.read(row,372))else 0;effective=C.mul(C.mul(hit['amount_bits'],C.add(mult,school)),C.ONE);effective=effective if C.rational(effective)>1 else C.ONE
                        actual=min(max(C.rational(D.read(row,288)),0),C.rational(effective));account(L,'ability:thunder_clap:r1',C.rounded(actual),now,[],damage=True)
                        request=C.mul(C.mul(effective,0x3c75c28f),C.ONE);hp,delta=heal_number(g['current_hp_bits'],derived[1536],request);g['current_hp_bits']=hp;g['player_fields'].update({'22':math.ceil(C.rational(hp)),'28':math.ceil(C.rational(derived[1536]))});account(L,'leech',delta,now,heal_events)
                    result['player_hp1440_bits']=g['current_hp_bits'];g['rng_words']=list(s['words']);g['now_bits']=now;state['scalar']['2352']=now;state['NPC']=copy.deepcopy(s['rows']);state['sets']=copy.deepcopy(s['sets']);result['xp1436']=g['xp'];assert result==E['stages'][j],('hurt independentcast',case['id'],j);assert U.project(state)['growth']==E['growth_stages'][j];player(obs['after'],state,('hurt',j));accounting(obs['healing'],L,('hurt',j),obs['after']);assert L==E['healing'][j]
                    for p,(want,hx,beforehx)in enumerate(zip(result['records432_cells'],obs['combat']['records432_hex'],obs['before_combat']['records432_hex'],strict=True)):
                        cells('NPC',want,hx);a,b=bytes.fromhex(hx),bytes.fromhex(beforehx)
                        for off,v in enumerate(want):
                            if v is None:assert a[off]==b[off];counts['NPC_unknown_conserved']+=1
                    for want,hx in zip(result['pickups56_cells'],obs['combat']['pickups56_hex'],strict=True):cells('pickup',want,hx)
                    for k,v in result.items():
                        if k not in('records432_cells','pickups56_cells'):assert v==obs['combat'][k],('hurtcombat',j,k)
                    for k in('windows','special','boundaries','auxiliary','claims'):
                        assert obs['after']['capture']['background'][k]==A['controlled_before']['capture']['background'][k];counts['background_vectors_conserved']+=1
                    game=bytes.fromhex(obs['after']['capture']['raw_game2592_hex'])
                    for k,p in(('kills1084',1084),('elites1088',1088),('counter2408',2408),('movement_sequence2412',2412),('killcost2420_bits',2420)):assert u(game,p)==result[k]
                    for k in('selected_ids','base_damage_bits','radius_bits','effect_writes','hits','known_packets','enqueued_hits','enqueued_areas'):assert diag[k]==E['diagnostics'][j][k],('castdiag',j,k)
                    assert [{k:e[k]for k in('reason_id','amount_bits','event_id')}for e in heal_events]==E['diagnostics'][j]['heal_events'];counts['positive_Leech_events']+=len(heal_events)
                    cursor=0
                    for packet in diag['known_packets']:
                        at=next(k for k in range(cursor,len(obs['new_packets']))if obs['new_packets'][k]==packet);cursor=at+1;counts['known_packets']+=1;counts['known_packet_bytes']+=len(packet[1])//2
                    assert obs['pending_after']['hits']['count']==obs['pending_after']['areas']['count']==0 and obs['empty_consumers_Game2592_unchanged'];previous=obs['after']
                now=C.add(case['casts'][-1],0x3e000000);state,d=tick_hurt(state,L,now,0x3e000000,classes,races,defs);assert U.project(state)==E['post_regen'];assert L==E['post_regen_healing'];player(A['post_regen'],state,'postregen');accounting(A['post_regen_healing'],L,'postregen',A['post_regen']);counts['positive_regen_events']+=len(d['heal_events']);counts['full2123']+=1
                reference.append(dict(batch=batchname,id=case['id'],player=U.project(state),ledger=copy.deepcopy(L)))
            assert A['account368_before_hex']==A['account368_after_hex']and A['profile376_before_hex']==A['profile376_after_hex']and A['selection_canaries']==['c3'*16,'d7'*16]
            counts['full2123']+=1 #actual warmup percase
        rt=load(batch/'runtime.json');term=load(batch/'owned-terminal.json');assert rt==comp['runtime']and term==comp['process'];assert rt['incoming_params_from_frozen_input']and rt['controlled_incoming_values']==[1,0,0];assert rt['actual_host_calls']==0 and rt['denied_imports']==882 and rt['error']is None and rt['fresh_instances']==ncases
        assert all(x['returned']and x['before']==x['after']==1048576 for x in rt['target_and_setup_returns']);assert all(x['unchanged']and x['ranges']==2318 for x in rt['world_source_checks']);assert term['exit_code']==0 and term['pid_missing']and term['pgid_missing'];assert missing(term['pid'])and missing(term['pgid'],True)
        expected_calls={'1076':5,'1093':5,'1108':5,'1600':5,'2123':34,'2945':5,'4677':5}if ncases==5 else{'922':32,'1076':4,'1093':4,'1108':4,'1600':4,'1775':32,'2123':8,'2945':4,'3755':32,'4677':4}
        assert rt['full_calls']==expected_calls and len(rt['target_and_setup_returns'])==sum(expected_calls.values())and len(rt['world_source_checks'])==(54 if ncases==5 else 56)
        assert rt['stack_checks']==(89 if ncases==5 else 148)and rt['allocator_calls']==ncases*5 and rt['peak_memory_bytes']==177078272
        assert not any(rt[k]for k in('old_Game_used_as_target','readiness_flags_injected','explicit_dead_marker_fixtures','App_or_world_Rc_producer_executed','externref_restored','native_executions','full_mainloop_frames','complete_games','HP_or_source_headers_written_by_harness'))and rt['input_dead_mask_all_zero']
        audit=load(batch/'expectation-read-audit.json');assert audit['forbidden']==[];assert all(not Path(p).suffix.lower()in('.wasm','.wat','.memory','.exe')and'/originals/'not in p for p in audit['opened'])
        batchrows.append(dict(path=str(batch),comparison_sha256=compSHA,source_files=nsources,production_files=47,edges=nedges,current_function_bodies=len(m['functions']),runtime=rt,author_terminal=term))
    assert counts['input_parameter_fidelity_cases']==9
    assert counts['full2123']==42 and counts['full1076']==9 and counts['full922']==32 and counts['damage_calls']==42 and counts['positive_Leech_events']==28 and counts['positive_regen_events']==27
    assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    for n,h in authors.items():assert sha(ROOT/n)==h
    for n,h in hand['frozen_shared_core_unchanged'].items():assert sha(ROOT/n)==h
    for n,h in v2['frozen_author_files'].items():assert sha(ROOT/n)==h
    for n,h in helpers.items():assert sha(ROOT/n)==h
    save(out/'independent-reference.json',reference)
    result=dict(status='pass_current139_hurtactor_regeneration_v3_scoped_projection_and_input_fidelity',reviewer='/root/growth139_world',author='/root/growth139_review',reviewer_script_sha256=sha(Path(__file__)),author_handoff_sha256=HAND,author_files=authors,helper_sha256=helpers,batches=batchrows,counts=dict(counts),current_body_bindings=bindings,incoming_parameter_source_proof=parameter_source_proof,incoming_parameter_receipts=parameter_receipts,v2_status_preserved='not_accepted_source_parameter_mismatch',source_metadata_param3_param4_static_only=True,metadata=dict(regen=[0,-1,0,1592624],Leech=[0,-2,-1]),original_executions=0,author_production_checker_runner_builder_executions=0,original_target_calls=0,independent_reference_sha256=sha(out/'independent-reference.json'),seconds=time.monotonic()-start,limits=['OnlydefaultWarrior empty-source finite nonfatalhurt/positiveRegen/rank1ThunderLeech domain; incoming controls1/0/0and actualNPC GUID match both sides.','Category0 param5controlled0 is unconsumed spelllookup payload, not actual925 dynamic330queueindex.','Incominghistory/category/callback remainsPending; no full1076 projection or complete2077 claim.','Metadataarg3/4headsareboundtostaticcallersandliterals,notcapturedfunctionarguments.','SharedledgersemanticG960/G1016/reasonf64totalsandVec48name/iconprojectiononly;full2077physical96key/catalog/buckets/historynotaccepted.','Controlleddt/clockanddirectcasts;notreal884framecap/AI/full1238success/naturalApp/native/game.','Knownpacketsorderedsubsequence;complete592/HP169/presentation/physicalBTreepointersunknown.','Reviewerpreviouslyprovidedstatic1466/2077notes;thisreviewindependentlyrecomputesnumbersusingpriorreferencehelpersandnewheal/ledgerlogic,doesnotexecuteauthorscode.'])
    save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])),flush=True)
if __name__=='__main__':main()
