#!/usr/bin/env python3
"""Different-author read-only current49961 review; executes no author/original."""
from pathlib import Path
from collections import Counter
import ast,copy,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
AUDIT=Counter()
def audit(event,args):
    if event in('subprocess.Popen','os.system','os.exec','ctypes.dlopen')or event=='import'and str(args[0]).startswith('core_spec'):
        AUDIT['forbidden_execution_or_author_import']+=1;raise RuntimeError('Read-only reviewer refuses '+event)
sys.addaudithook(audit)
import review_cast139 as C
import review_opening139 as O
import review_enemy_ai139 as E
from review_initial139 import reference as constructor_reference
from review_world_position139 import load_world
from review_combat139 import parse_module,local_closure,sha,fp,bits

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'evidence/terminal139-oracle-20261102T131953.320492Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
HAND='9feaec0233ca1948a5899c09baee7c1edb06e8a9970365b25255c7d1727f32f3'
COMP='ac44ab48fd44f86435bc813363cb628a921a016d199b0cf48570ac864b66181e'
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=lambda b,o=0:struct.unpack_from('<I',b,o)[0]
q=lambda b,o=0:struct.unpack_from('<Q',b,o)[0]


def read(row,offset,width=4):
    part=row[offset:offset+width];assert len(part)==width and None not in part
    return int.from_bytes(bytes(part),'little')


def quoted(value):
    #11741 operates on originalUTF8 bytes and handlesLF separately from the
    #other ASCIIcontrols. It is deliberately not json.dumps' \t/\r dialect.
    output=bytearray(b'"')
    for byte in value.encode('utf8'):
        if byte in(34,92):output.extend((92,byte))
        elif byte==10:output.extend(b'\\n')
        elif byte<32:output.extend(('\\u%04x'%byte).encode())
        else:output.append(byte)
    output.append(34);return bytes(output)


def notification(hero,labels):
    #1965 supplies these17fields in exactly this order. This batch has
    #time1.25 and initialzero counters/damage;53225 emits1.250,not1.25.
    fields=[('type',quoted('victory')),('time',b'1.250'),('level',b'1'),('kills',b'0'),('elites',b'0'),('guardians',b'0'),('bosses',b'0'),('damage',b'0'),('taken',b'0'),('gold',b'0'),('chests',b'0'),('class',quoted(labels['class_label'])),('hero',quoted(hero)),('race',quoted(labels['race_label'])),('bg',quoted(labels['zone_label'])),('left',b'false'),('recap',b'{}')]
    buffer=bytearray(b'{');capacity=1;reserves=[]
    def append(fragment):
        nonlocal capacity
        needed=len(buffer)+len(fragment)
        if needed>capacity:capacity=max(needed,2*capacity,8);reserves.append(capacity)
        buffer.extend(fragment)
    for index,(key,value)in enumerate(fields):
        if index:append(b',')
        append(quoted(key));append(b':');append(value)
    append(b'}');return[capacity,buffer.hex()],reserves


def transition(case,state,world,labels,counts):
    result=copy.deepcopy(state);packets=[];stops=[];notes=[]
    if not case['field400']or result['phase2587']!=1 or case['endless2568']&1:return result,packets,notes,stops
    now=case['now_bits'];result['phase2587']=5
    for name,source,destination,start,duration,ident,timer in[('units',316,328,340,344,112,None),('auxiliary',32,44,56,60,16,68),('claims',44,56,68,72,24,76)]:
        vector=result['vectors'][name]
        for row in vector['storage'][:vector['count']]:
            d,t=read(row,duration),read(row,start)
            if name=='units':active=read(row,0)==0 and C.rational(d)>0 and C.rational(now)<C.rational(C.add(d,t))
            elif name=='auxiliary':active=C.rational(d)>0 and C.rational(now)<C.rational(C.add(d,t))
            else:active=C.rational(now)<C.rational(C.add(d,t))
            if not active:continue
            endpoint=tuple(read(row,destination+4*i)for i in range(3))
            if name=='claims'and C.rational(d)<=0:xyz=endpoint
            else:
                ratio=C.div(C.sub(now,t),d);ratio=0 if C.rational(ratio)<0 else C.ONE if C.rational(ratio)>1 else ratio
                xyz=tuple(C.add(read(row,source+4*i),C.mul(C.sub(endpoint[i],read(row,source+4*i)),ratio))for i in range(3))
            height=world.height(*xyz[:2]);assert height is not None,'Fallback/nearestprimary not dynamically admitted'
            xyz=(*xyz[:2],height);counts['processed_height_hits']+=1
            for base in(source,destination):
                for i,value in enumerate(xyz):row[base+4*i:base+4*i+4]=struct.pack('<I',value)
            row[start:start+4]=struct.pack('<I',now);row[duration:duration+4]=bytes(4)
            if timer is not None:row[timer:timer+4]=struct.pack('<I',now)
            target=read(row,ident,8);result['movement2412']=(result['movement2412']+1)&0xffffffff;packets.append([221,32,(C.packguid(target)+struct.pack('<4I',*xyz,result['movement2412'])+b'\1').hex()]);stops.append(str(target));counts['stop_'+name]+=1
    packets.append([232,32,(C.packguid(0)+struct.pack('<I',result['action1644'])).hex()]);result['action1644']=(result['action1644']+1)&0xffffffff
    for packet in packets:
        if result['packet_count']==result['packet_capacity']:result['packet_capacity']=max(4,2*result['packet_capacity'])
        result['packet_count']+=1
    note,reserves=notification(case['hero'],labels);notes.append(note);counts['JSON_reserve_events']+=len(reserves)
    if result['notification_count']==result['notification_capacity']:result['notification_capacity']=max(4,2*result['notification_capacity'])
    result['notification_count']+=1;counts['controlled_terminal_transitions']+=1
    return result,packets,notes,stops


def main():
    start=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir();assert sha(SOURCE)==WASM and sha(BATCH/'comparison.json')==COMP and sha(BATCH/'task-handoff.json')==HAND
    comp=load(BATCH/'comparison.json');hand=load(BATCH/'task-handoff.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json');runtime=load(BATCH/'runtime.json')
    assert len(hand['author_files'])==6
    for name,digest in hand['author_files'].items():assert sha(ROOT/name)==digest
    sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==75 and sum(n.startswith('reconstruction/')for n in sources)==63
    for name,digest in sources.items():assert sha(ROOT/name)==sha(BATCH/'source-snapshot'/name)==digest
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(edges)==250
    for table in[comp['artifacts'],comp['frozen'],prep['frozen']]:
        for name,digest in table.items():assert sha(BATCH/name)==digest
    assert comp['differences']==0 and comp['cases']==comp['completed_cases']==5 and comp['expected_before_original']and prep['expected_before_original']and not comp['original_input_contains_expected']and not prep['original_input_contains_expected']and not comp['forbidden_model_reads']
    helpers={**O.HELPERS,**E.HELPERS,'scripts/review_cast139.py':'bc0fc0e1a107a504893168d713b3ca73bce77e03a9aade0d9961c2761aa06c5b','scripts/review_opening139.py':'29de9cb7dbeb7595ce2baced0a0de9d5c5e967ce73cecd8cff5868d4feafc5c9'}
    oldhand=ROOT/'evidence/enemy-ai139-independent-review-owned-20261102T110424.508946Z/task-handoff.json';assert sha(oldhand)=='5eb378c134e04a316075a5b479819800f72d29a49f7cc3e1a6c5e5ec170a1092'
    record=load(oldhand);mapping=record['frozen_reviewer_files'];assert mapping
    for name,digest in mapping.items():
        if name.endswith('review_enemy_ai139.py'):helpers[name]=digest
    assert 'scripts/review_enemy_ai139.py'in helpers
    for name,digest in helpers.items():assert sha(ROOT/name)==digest
    assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'and sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(Path(cfg['range_file'])))==2318 and cfg['world_rc']==20544696
    wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';wr=load(wp);assert sha(wp)=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48';world,nav,scalars=load_world(dict(receipt=str(wp),receipt_sha256=sha(wp),world_artifacts=wr['world_artifacts']));assert not scalars['primary_present']and not scalars['flat_present']
    raw=SOURCE.read_bytes();original=parse_module(raw);private=(BATCH/m['module_file']).read_bytes();modified=parse_module(private)
    for a,b in zip(original['sections'],modified['sections'],strict=True):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==private[b['start']:b['end']]
    exports=[('research139_gw_companion',0,2945),('research139_gw_initial',0,1600),('research139_gw_opening',0,1108),('research139_gw_stack',3,0),('research139_auto_ai925',0,925),('research139_terminal49961',0,49961)]
    assert modified['exports']==original['exports']+exports and len(original['imports'])==882 and original['types'][original['decl'][49961-882]]==('7f','')
    texts={};bindings={};extra={55846,30179,29237,50441,81682,11425,11499,35202,35232,1711,108362,6786}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as s:
        for idx in sorted(set(map(int,m['functions']))|extra):
            a,z=original['bodies'][idx];lo,hi=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();s.seek(lo);wat=s.read(hi-lo);record=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest());texts[idx]=wat.decode();bindings[str(idx)]=record
            if str(idx)in m['functions']:
                claim=m['functions'][str(idx)];assert record['body_sha256']==claim['body_sha256']and record['WAT_sha256']==claim['WAT_sha256']and wat==(BATCH/'static'/f'{idx}.wat').read_bytes()
            (out/f'{idx}.wat').write_bytes(wat)
    terminal=texts[49961];assert terminal.index('i32.store8 offset=2587')<terminal.index('call 17209')<terminal.index('call 55851')<terminal.index('call 1965')
    assert 'i32.load offset=400'in terminal and'i32.load8_u offset=2568'in terminal and'i32.const 5'in terminal
    assert texts[17209].index('call 17319')<texts[17209].index('call 16380')and'i32.const 432'in texts[17209]
    assert 'f64.const 0x1.c6bf52634p+49'in texts[53225]and'i32.const 1609998'in texts[53225]
    def data(address,size):
        result=bytearray(size)
        for base,pos,n in original['data_segments']:
            if base is None:continue
            lo,hi=max(base,address),min(base+n,address+size)
            if lo<hi:result[lo-address:hi-address]=raw[pos+lo-base:pos+hi-base]
        return bytes(result)
    word=lambda p:u(data(p,4));string=lambda p,n:data(p,n).decode();abilities={}
    for i in range(114):
        p=5882740+88*i;r=data(p,88);abilities[string(u(r,12),u(r,16))]=(p,r)
    cls=data(5877920,108);race=data(5874636,44);zone=data(5871348,152);classes={1:dict(hp_armor=[u(cls,72),u(cls,76)],ability_pointer=5882740)};races={1:dict(ability_pointer=abilities[string(u(race,24),u(race,28))][0],modifiers=list(struct.iter_unpack('<II',data(u(race,16),8*u(race,20)))))}
    labels=dict(class_id=string(u(cls,16),u(cls,20)),class_label=string(u(cls,24),u(cls,28)),race_label=string(u(race,0),u(race,4)),zone_label=string(u(zone,16),u(zone,20)));assert labels==m['current_labels']
    assert data(1588650,7)==b'victory'and data(1588657,4)==b'type';scalars['heading_bits']=u(zone,116);zones=[dict(xyz=[u(zone,104),u(zone,108),u(zone,116)])];normal=data(5830904,72);eligible=[i for i in range(12)if word(5830904+72*i+68)==1 and math.isfinite(fp(word(5830904+72*i+64)))];minutes=word(u(zone,72)+336)
    tables=[list(struct.unpack('<4f',data(p,16)))for p in[14426512,14426528,14426544,14426560]];speeds=list(struct.unpack('<6I',data(1593032,24)));speeds[1]=1088421888;neighbors=list(struct.iter_unpack('<ii',data(5408444,64)));english=json.loads(data(*struct.unpack('<II',data(5401532,8))));names={5830904:'Kobold Vermin'}
    cases=load(BATCH/'inputs.json');actual=[json.loads(x)for x in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(actual)==5
    assert[(c['app_seed_u64'],c['field400'],c['phase2587'],c['endless2568'])for c in cases]==[('0',1,1,0),('0',1,1,0),('0',0,1,0),('11',1,1,1),('69',1,2,0)]
    counts=Counter();traces=[]
    def cells(label,want,hx):
        seen=bytes.fromhex(hx);assert len(want)==len(seen)
        for i,(v,b)in enumerate(zip(want,seen)):
            if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
            else:assert v==b,(label,i,v,b);counts[label+'_known']+=1
    for case,a in zip(cases,actual,strict=True):
        assert case['id']==a['id']and case['repeat']==2 and case['now_bits']==0x3fa00000
        opening,_=O.reference(case,world,nav,scalars,tables,normal,speeds,classes,races,zones,eligible,minutes);op=opening['projection'];ctor,_=constructor_reference(dict(class_byte=1,race_byte=1,region_index=0,seed_u64=opening['constructor_seed_u64'],object_id_u64='0',flat_height_bits=world.height(*scalars['center_xy_bits'])),classes,races,zones)
        assert a['opening']['packets']==op['packets'];cells('openingGame',opening['known_Game2592'],a['opening']['raw_game2592_hex'])
        initial=dict(rows=copy.deepcopy(op['units']['storage']),now=C.sub(bits(1.),0x3dcccccd),frame=0,player=op['player_xyz'],path=None,path_values=None,path_clock=0,sequence=1,hp=ctor['current_hp_bits'],last=0xc1200000,incoming=0.,category=0.,has_category=False,derived=ctor['derived_bits'],guards={k:0 for k in[736,740,764,1344,1348,1444,1448,1624]},fields=copy.deepcopy(ctor['player_fields']),history=dict(head=0,count=0,rows=[],strings=[],origin=[]),packets=copy.deepcopy(op['packets']))
        ai,answer=E.tick(initial,0x3dcccccd,world,nav,neighbors,names,english,counts);assert ai['now']==bits(1.)and not answer['attacks']and len(answer['records'])==4
        assert a['moving']['packets']==answer['packets']and a['moving']['background']['movement_sequence2412']==answer['movement_sequence2412']
        for row,hx in zip(answer['records'],a['moving']['background']['units']['storage'],strict=True):cells('movingNPC',row,hx)
        assert a['new_Game_pointer']!=14685248 and a['account368_before_hex']==a['account368_after_hex']and a['profile376_before_hex']==a['profile376_after_hex']and a['stack_after']==1048576
        moving=bytes.fromhex(a['moving']['raw_game2592_hex']);before=a['before'];rawbefore=bytes.fromhex(before['raw_Game2592_hex']);wanted=bytearray(moving)
        assert before['vectors']['units']==a['moving']['background']['units']
        for key in['pickups','special','windows','boundaries','counter2408']:assert a['moving']['background'][key]==a['opening']['background'][key]==before['background'][key]
        for off,value in[(2352,case['now_bits']),(400,case['field400'])]:struct.pack_into('<I',wanted,off,value)
        wanted[2587]=case['phase2587'];wanted[2568]=case['endless2568'];hero=case['hero'].encode()
        if hero:
            assert u(rawbefore,216)==u(rawbefore,224)==len(hero)and u(rawbefore,220)>0;struct.pack_into('<III',wanted,216,len(hero),u(rawbefore,220),len(hero))
        for name,off,stride in[('auxiliary',652,112),('claims',2108,88)]:
            rows=case['fixture_vectors'][name];assert rows==before['vectors'][name]['storage']
            if rows:assert len(rows)==2 and before['vectors'][name]['count']==1 and u(moving,off)==u(moving,off+8)==0;struct.pack_into('<III',wanted,off,2,u(rawbefore,off+4),1)
        assert bytes(wanted)==rawbefore,'Controlled inputs must match actual49961 arguments exactly'
        assert u(rawbefore,408)==0 and rawbefore[2567]==0 and q(rawbefore,984)==q(rawbefore,992)==0 and all(u(rawbefore,o)==0 for o in[1084,1088,1092,1096,1100,1104])and u(rawbefore,1432)==1
        state=dict(phase2587=case['phase2587'],action1644=1,movement2412=answer['movement_sequence2412'],packet_capacity=128,packet_count=len(answer['packets']),notification_capacity=4,notification_count=1,vectors=dict(units=dict(count=4,storage=copy.deepcopy(answer['records'])),auxiliary=dict(count=int(bool(case['fixture_vectors']['auxiliary'])),storage=[list(bytes.fromhex(s))for s in case['fixture_vectors']['auxiliary']]),claims=dict(count=int(bool(case['fixture_vectors']['claims'])),storage=[list(bytes.fromhex(s))for s in case['fixture_vectors']['claims']])))
        for key,value in state.items():
            if key!='vectors':assert before[key]==value
        previous=before;stages=[]
        for index,observed in enumerate(a['stages']):
            state,packets,notes,stopped=transition(case,state,world,labels,counts);assert observed['new_packets']==packets and observed['new_notifications']==notes
            physical_before=bytes.fromhex(previous['raw_Game2592_hex']);physical_after=bytearray(physical_before)
            for key,off in[('action1644',1644),('movement2412',2412),('packet_capacity',1880),('packet_count',1888),('notification_capacity',1892),('notification_count',1900)]:struct.pack_into('<I',physical_after,off,state[key]);assert observed[key]==state[key]
            physical_after[2587]=state['phase2587'];assert observed['phase2587']==state['phase2587']and physical_after.hex()==observed['raw_Game2592_hex'];counts['whole_Game2592_bytes']+=2592
            changes=[[i,b]for i,(old,b)in enumerate(zip(physical_before,physical_after))if old!=b];assert changes==observed['changed_Game_bytes']
            for name,stride in[('units',432),('auxiliary',112),('claims',88)]:
                expected=state['vectors'][name];got=observed['vectors'][name];assert got['count']==expected['count']and got['capacity']==len(expected['storage'])and got['pointer']==previous['vectors'][name]['pointer']
                for row,oldhx,hx in zip(expected['storage'],previous['vectors'][name]['storage'],got['storage'],strict=True):
                    cells('terminal_'+name,row,hx);replay=bytearray.fromhex(oldhx)
                    for off,value in enumerate(row):
                        if value is not None:replay[off]=value
                        else:counts['physical_None_inheritance']+=1
                    assert replay.hex()==hx;counts['full_physical_vector_bytes']+=stride
            for key in['pickups','special','windows','boundaries','counter2408']:assert observed['background'][key]==before['background'][key];counts['other_background_groups_conserved']+=1
            assert observed['rng_words']==before['rng_words']and observed['packets']==previous['packets']+packets and observed['notifications']==previous['notifications']+notes
            counts['full49961_targets']+=1;counts['new_stop221_or232_packets']+=len(packets);counts['packet_payload_bytes']+=sum(len(z[2])//2 for z in packets);counts['complete_victory_notifications']+=len(notes);counts['notification_UTF8_payload_bytes']+=sum(len(z[1])//2 for z in notes)
            stages.append(dict(phase=state['phase2587'],stopped_guids=stopped,packets=packets,notifications=notes,Game_changes=changes));previous=observed
        traces.append(dict(input=case,stages=stages))
    assert counts['full49961_targets']==10 and counts['controlled_terminal_transitions']==2 and counts['processed_height_hits']==10 and counts['packet_payload_bytes']==236 and counts['notification_UTF8_payload_bytes']==466 and counts['physical_None_inheritance']==5160
    assert runtime==comp['runtime']and runtime['fresh_instances']==5 and runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['error']is None and runtime['memory_cap_bytes']==268435456 and runtime['peak_memory_bytes']==177078272
    assert runtime['full_calls']=={'2945':5,'1600':5,'1108':5,'925':5,'49961':10,'4677':0,'1093':0,'922':0,'1775':0,'3755':0,'2123':0,'1076':0,'1238':0}and runtime['stack_checks']==58 and runtime['allocator_calls']==28
    assert len(runtime['target_and_setup_returns'])==30 and all(x['returned']and x['before']==x['after']==1048576 for x in runtime['target_and_setup_returns'])and len(runtime['world_source_checks'])==25 and all(x['ranges']==2318 and x['unchanged']for x in runtime['world_source_checks'])
    terminal=load(BATCH/'owned-terminal.json');assert terminal==comp['process']==hand['process']and terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']
    for name,digest in hand['author_files'].items():assert sha(ROOT/name)==digest
    for name,digest in sources.items():assert sha(ROOT/name)==digest
    assert not AUDIT
    result=dict(status='pass_current49961_controlled_terminal_transition_and_three_guards_only',author_handoff_sha256=HAND,comparison_sha256=COMP,author6_unchanged=hand['author_files'],reviewer_script_sha256=sha(Path(__file__)),pure_helpers=helpers,source_files=75,production_files=63,source_edges=250,current_bindings=bindings,original22body_claims_rebound=True,only_export_section_changed=True,formal_counts=dict(fixtures=5,target49961=10,setup2945_1600_1108_925_each=5,all_direct_entries=30,controlled_transitions=2,natural_victories=0,complete_games=0,reviewer_original_executions=0,reviewer_author_program_executions=0,differences=0),counts=dict(counts),author_process=terminal,reviewer_audit=dict(AUDIT),independent_expected_outputs_read=False,limits=['Controlledfield400=1 transition with real1108/925 NPCs and separatecontrolledaux112/companion88 case;field400 naturalBoss/endproducer not restored.','Field400zero/endlessbit1/phase2 and repeatedphase5 guards actualfixtures;not allterminalstates/classes/locale/recap or wholegame.','Fullphysical2592Game no additionalchanges andallvectorNone inheritance checked;heap/resource ownerpointer meaning remainsunknown.','Full12newpackets/236B and2completevictoryUTF8 strings/466B/cap272 checked;17fieldorder/quotecontrolformat current1965/11741/45182/53225/reserve55846 bound.','Fresh925 setup onlynow1/dt.1,quietcenter/noincoming;independentpureAI geometry matched4moves perfixture. BFS rawarrays not serialized,not claimed newlyverified here.','Canonicalnonflat10height hits;worldmiss/nearestprimary/detachedrecap/nonEnglish/generalnumberformatting outsidefixtures remainPending.','Sourcecontextlegalresource-onlyv2/newGame notApp/WorldRc/externref bootstrap.0native/full884/naturalvictory/completegame/network/save acceptance.'],seconds=time.monotonic()-start)
    save(out/'review.json',result);save(out/'reference-traces.json',traces);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
