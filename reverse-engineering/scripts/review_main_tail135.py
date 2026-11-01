#!/usr/bin/env python3
"""Independent frozen frame/terminal replay and raw bytes review; no WASM run."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from decimal import Decimal,localcontext,ROUND_HALF_EVEN
import hashlib,json,math,struct
from review_gameplay_phase135 import ROOT,ORIGINAL,ORIGINAL_SHA,sha,strict,norm,uint,sections,bodies,core_closure,load_checker
from extract_catalogue134 import parse_binary

FRAME=ROOT/'evidence/full0135-oracle-20261101T075536.007629Z'
TERMINAL=ROOT/'evidence/full0135-oracle-20261101T081314.600878Z'
LABELS=ROOT/'evidence/terminal-transition0135-static-20261101T075941.450411Z/label-evidence.json'

def word(raw,o):return struct.unpack_from('<I',raw,o)[0]
def guid(raw,o=0):return struct.unpack_from('<Q',raw,o)[0]
def number(w):return struct.unpack('<f',struct.pack('<I',w))[0]
def packed(n):
    parts=[(n>>(8*i))&255 for i in range(8)]
    return bytes([sum((v!=0)<<i for i,v in enumerate(parts))]+[v for v in parts if v])
def decoded(raw):
    mask=raw[0];n=0;at=1
    for i in range(8):
        if mask>>i&1:assert raw[at]!=0;n|=raw[at]<<(8*i);at+=1
    return n,at

def signatures(raw,sec):
    _,_,at,end=next(x for x in sec if x[0]==1);n,at=uint(raw,at);types=[]
    for _ in range(n):
        assert raw[at]==0x60;at+=1;p,at=uint(raw,at);params=raw[at:at+p];at+=p;r,at=uint(raw,at);results=raw[at:at+r];at+=r
        types.append((params.hex(),results.hex()))
    assert at==end
    _,_,at,end=next(x for x in sec if x[0]==3);n,at=uint(raw,at);result={}
    for i in range(n):idx,at=uint(raw,at);result[i+878]=types[idx]
    assert at==end;return result

def exports(raw,sec):
    _,_,at,end=next(x for x in sec if x[0]==7);n,at=uint(raw,at);result=[]
    for _ in range(n):
        size,at=uint(raw,at);name=raw[at:at+size].decode();at+=size;kind=raw[at];at+=1;index,at=uint(raw,at);result.append((name,kind,index))
    assert at==end;return result

def freeze(batch,prefix,entries,original,original_sections,code):
    path=batch/(prefix+'-comparison.json');r=json.loads(path.read_text());frozen=r['source_sha256_before'];snap=batch/'source-snapshot'
    assert frozen==r['source_sha256_after']
    for n,h in frozen.items():assert sha(snap/n)==h
    closure=core_closure(snap,entries);assert set(closure)<=frozen.keys()
    for n,h in r['artifacts'].items():assert sha(batch/n)==h
    assert sha(batch/'manifest.json')==r['manifest_sha256']
    changed=(batch/'research135-exports.wasm').read_bytes();assert hashlib.sha256(changed).hexdigest()==r['module_sha256']
    assert [(k,x)for k,x,_,_ in original_sections if k!=7]==[(k,x)for k,x,_,_ in sections(changed)if k!=7]
    manifest=json.loads((batch/'manifest.json').read_text());guards=r['body_guards']+manifest['roles']
    old_exports=exports(original,original_sections);new_exports=exports(changed,sections(changed))
    assert new_exports[:len(old_exports)]==old_exports
    assert new_exports[len(old_exports):]==[('research135_'+x['role'],0,x['index'])for x in manifest['roles']]
    sigs=signatures(original,original_sections);signature_checks=0
    for item in guards:
        a,b=code[item['index']-878];assert(a,b)==(item['body_start'],item['body_end'])
        assert hashlib.sha256(original[a:b]).hexdigest()==item['body_sha256']
        if 'parameters_hex'in item:
            assert sigs[item['index']]==(item['parameters_hex'],item['results_hex']);signature_checks+=1
    assert manifest['denied_function_import_count']==878 and r['runtime']['host_calls']==0 and r['process']['exit_code']==0
    assert not r['runtime']['application_start_called']and not r['runtime']['network_used']and not r['runtime']['user_saves_accessed']
    drift={n:dict(frozen=h,current=sha(ROOT/n))for n,h in frozen.items()if sha(ROOT/n)!=h}
    coordinated=[]
    if 'scripts/full135_host.mjs'in drift:
        old=(snap/'scripts/full135_host.mjs').read_text();current=(ROOT/'scripts/full135_host.mjs').read_text()
        assert current==old.replace('size>1048576','size>4194304')
        coordinated.append('Only allocate per-block limit1MiB→4MiB;512page/32MiB total andall878deny unchanged. Frozen receipt still binds oldhost.')
    return r,snap,dict(receipt=str(path.relative_to(ROOT)),receipt_sha256=sha(path),source_files=len(frozen),core_package_init_closure=closure,
        frozen_source_sha256=frozen,current_source_drift=drift,body_guards_recomputed=len(guards),signature_guards_recomputed=signature_checks,
        coordinated_host_difference_verified=coordinated,original_exports_preserved=True,approved_added_export_bindings_verified=True,all_nonexport_sections_identical=True)

def independent_frame(c,out,counts):
    rows=[bytes.fromhex(x)for x in c['storage']];n=c['count'];packet_count=0;stages=[]
    for op,actual in zip(c['ops'],out['stages']):
        old=n;packets=[];trap=False;i=0;now=number(op['now_bits'])
        if c['kind']=='owned':
            for item in c['owned']:
                p=word(bytes.fromhex(item),0);assert bytes.fromhex(c['definitions'][str(p)])[84]!=11
                counts['owned80_bytes']+=80
        elif c['kind']in('deadline','secondary'):
            stride=32 if c['kind']=='deadline'else 112
            while i<n:
                row=rows[i];due=number(word(row,8 if stride==32 else 100))
                remove=due<=now if stride==32 else now>=due
                if not remove:
                    if stride==112:assert not number(word(row,104))<=now,'Unrestored active due leaked into acceptedfixtures'
                    i+=1;continue
                if i+1<n:counts['nontrivial_stable_compactions']+=1
                for j in range(i,n-1):rows[j]=rows[j+1]
                n-=1;counts['removed_records']+=1
                if stride==112:
                    if word(row,0)==0:trap=True;counts['post_pop_null_traps']+=1;break
                    actor=guid(row,80)
                    if actor:packets.append([170,32,actor.to_bytes(8,'little').hex()])
                else:
                    actor=guid(row);g=packed(actor);wire=g+g+row[12:16]+bytes.fromhex('000100004000')+row[16:28]
                    first,at=decoded(wire);second,b=decoded(wire[at:]);assert first==second==actor and at+b+22==len(wire)
                    packets.append([306,32 if len(wire)<=32 else 64,wire.hex()])
                    counts['GUIDs_above_2pow53']+=actor>1<<53
        elif c['kind']=='claim':assert c['phase']!=1 or n==0
        elif c['kind']=='terminal':assert not(c['field400']and c['phase']==1 and not(c['endless']&1))
        else:raise AssertionError(c['kind'])
        changes=[]
        if old!=n:changes.append([1840 if c['kind']=='deadline'else 1864 if c['kind']=='secondary'else 2116,n])
        if packets:packet_count+=len(packets);changes.append([1888,packet_count])
        prediction=dict(count=n,storage=[x.hex()for x in rows],owned=c['owned'],packets=packets,game_changes=sorted(changes),entry_trap=trap)
        assert strict(prediction,actual)
        stages.append(prediction);counts['stages']+=1;counts['complete_backing_bytes']+=sum(map(len,rows));counts['packets']+=len(packets)
        counts['packet_payload_bytes']+=sum(len(bytes.fromhex(p[2]))for p in packets)
        counts['all2592_game_words_scanned_by_frozen_runner']+=648
        if trap:break
    assert strict(stages,c['expected'])

def quote_bytes(value):
    out=bytearray(b'"')
    for x in value.encode('utf8'):
        if x in(34,92):out.extend((92,x))
        elif x==10:out.extend(b'\\n')
        elif x<32:out.extend(('\\u%04x'%x).encode())
        else:out.append(x)
    out.extend(b'"');return bytes(out)

def decimal_text(value):
    if not math.isfinite(value):return b'0'
    if value==int(value)and abs(value)<10**15:return str(int(value)).encode()
    with localcontext()as ctx:
        ctx.prec=400
        return format(Decimal.from_float(value).quantize(Decimal('.001'),rounding=ROUND_HALF_EVEN),'f').encode()

def notification(input_,labels):
    counters=dict(input_['counters']);f64=lambda k:struct.unpack('<d',struct.pack('<Q',int(input_[k])))[0]
    values=[('type',quote_bytes('victory')),('time',decimal_text(number(input_['now_bits'])))]
    for offset,key in((1432,'level'),(1084,'kills'),(1088,'elites'),(1092,'guardians'),(1096,'bosses')):values.append((key,str(counters[offset]).encode()))
    values.extend((('damage',decimal_text(f64('damage984_f64_bits'))),('taken',decimal_text(f64('taken992_f64_bits'))),('gold',str(counters[1100]).encode()),('chests',str(counters[1104]).encode())))
    for key,value in(('class',labels['class'][input_['class_byte']]),('hero',input_['hero']),('race',labels['race_fallback'][input_['race_byte']]),('bg',labels['zone_fallback'][input_['region_index']])):values.append((key,quote_bytes(value)))
    values.extend((('left',b'true'if input_['left2567']else b'false'),('recap',b'{}')))
    cap=1;data=bytearray(b'{')
    def append(bs):
        nonlocal cap
        if len(data)+len(bs)>cap:cap=max(cap*2,len(data)+len(bs),8)
        data.extend(bs)
    for j,(key,value)in enumerate(values):
        if j:append(b',')
        append(quote_bytes(key));append(b':');append(value)
    append(b'}')
    return dict(capacity=cap,payload_hex=data.hex())

def raw_game_changes(old,new):
    changes=[];skip=set()
    for off in(1884,1896):
        if old[off:off+4]!=new[off:off+4]:changes.append([off,'heap_pointer'])
        skip.update(range(off,off+4))
    changes.extend([i,b]for i,b in enumerate(new)if i not in skip and b!=old[i])
    return sorted(changes)

def independent_terminal(c,out,initial,f,labels,counts):
    s=c['model_input'];source=int(s['source_id']);constructor=bytes.fromhex(out['constructor_raw_g2592_hex'])
    assert len(constructor)==2592 and guid(constructor,1336)==source
    speed=initial.level.stats.previous_speed_bits;assert word(constructor,1648)==speed
    prefix=[]
    if number(f.sub(speed,0x40e00000)&0x7fffffff)>number(0x3c23d70a):
        prefix=[dict(opcode=226,capacity=32,payload_hex=(packed(source)+struct.pack('<II',1,speed)).hex())]
        assert c['input']['race_byte']==4;counts['actual_constructor226_preserved']+=1
        counts['constructor226_payload_bytes']+=len(bytes.fromhex(prefix[0]['payload_hex']))
    assert strict(prefix,c['constructor_expected']['packets'])and strict(prefix,out['before']['packets'])
    assert word(constructor,1880)==(4 if prefix else 0)and word(constructor,1888)==len(prefix)
    assert word(constructor,1644)==1+len(prefix)
    for base in(1784,656,2108):assert word(constructor,base)==word(constructor,base+8)==0
    assert word(constructor,1900)==0 and word(constructor,2408)==initial.spawn_counter
    assert [word(constructor,1720+4*j)for j in range(4)]==list(initial.level.rng_words)
    for k,v in c['words'].items():assert word(bytes.fromhex(out['before']['raw_g2592_hex']),int(k))==v
    for k,v in c['bytes'].items():assert bytes.fromhex(out['before']['raw_g2592_hex'])[int(k)]==v
    for k,v in c['doubles'].items():assert guid(bytes.fromhex(out['before']['raw_g2592_hex']),int(k))==int(v)
    rows={k:[bytearray.fromhex(x)for x in s[k+'_storage']]for k in('units','auxiliary','claims')}
    seq=s['movement_sequence2412'];action=s['action_sequence1644'];phase=s['phase2587'];packets=prefix[:];notices=[];oldgame=bytes.fromhex(out['before']['raw_g2592_hex'])
    for stage in out['stages']:
        before_packets=len(packets)
        if s['field400']and phase==1 and not(s['endless2568']&1):
            phase=5;counts['true_terminal_entries']+=1
            for kind,ao,bo,so,do,go,to in(('units',316,328,340,344,112,None),('auxiliary',32,44,56,60,16,68),('claims',44,56,68,72,24,76)):
                for row in rows[kind][:s[kind+'_count']]:
                    now=number(s['now_bits']);duration=word(row,do);start=word(row,so)
                    move=not now>=number(f.add(start,duration))if kind=='claims'else number(duration)>0 and now<number(f.add(duration,start))and(kind!='units'or word(row,0)==0)
                    if not move:continue
                    if kind=='claims'and number(duration)<=0:xyz=[word(row,bo+4*j)for j in range(3)]
                    else:
                        ratio=f.div(f.sub(s['now_bits'],start),duration)
                        if number(ratio)<0:ratio=0
                        if number(ratio)>1:ratio=0x3f800000
                        xyz=[f.add(word(row,ao+4*j),f.mul(f.sub(word(row,bo+4*j),word(row,ao+4*j)),ratio))for j in range(3)]
                    if s['flat_height_enabled']:xyz[2]=s['flat_height_bits']
                    for off in(ao,bo):struct.pack_into('<3I',row,off,*xyz)
                    struct.pack_into('<II',row,so,s['now_bits'],0)
                    if to is not None:struct.pack_into('<I',row,to,s['now_bits'])
                    actor=guid(row,go);seq=(seq+1)&0xffffffff
                    wire=packed(actor)+struct.pack('<4I',*xyz,seq)+b'\x01';decoded_actor,at=decoded(wire)
                    assert decoded_actor==actor and len(wire)==at+17
                    packets.append(dict(opcode=221,capacity=32,payload_hex=wire.hex()));counts['stopped_'+kind]+=1;counts['movement_GUIDs_above_2pow53']+=actor>1<<53
            packets.append(dict(opcode=232,capacity=32,payload_hex=(packed(source)+struct.pack('<I',action)).hex()));action=(action+1)&0xffffffff
            note=notification(s,labels);notices.append(note);counts['new_notifications']+=1
            counts['notification_payload_bytes']+=len(bytes.fromhex(note['payload_hex']))
            counts['hero_with_nonASCII']+=any(ord(x)>127 for x in s['hero'])
            counts['hero_with_control']+=any(ord(x)<32 for x in s['hero'])
        else:counts['false_terminal_entries']+=1
        assert stage['phase']==phase and stage['movement_sequence']==seq and stage['action_sequence']==action
        for kind in rows:
            assert stage['vectors'][kind]['count']==s[kind+'_count']
            assert stage['vectors'][kind]['storage']==[r.hex()for r in rows[kind]]
            counts['full_'+kind+'_backing_bytes']+=sum(map(len,rows[kind]))
        assert strict(stage['packets'],packets)and strict(stage['notifications'],notices)
        for packet in packets[before_packets:]:counts['new_packet_opcode'+str(packet['opcode'])]+=1;counts['new_packet_payload_bytes']+=len(bytes.fromhex(packet['payload_hex']))
        game=bytes.fromhex(stage['raw_g2592_hex']);assert len(game)==2592
        assert strict(raw_game_changes(oldgame,game),stage['game_changed_bytes'])
        counts['raw_game_bytes_recomputed']+=2592;counts['normalized_heap_word_events']+=sum(v=='heap_pointer'for o,v in stage['game_changed_bytes']);oldgame=game
        counts['terminal_stages']+=1
    counts['constructor_raw_bytes_checked']+=2592

def main():
    raw=ORIGINAL.read_bytes();assert hashlib.sha256(raw).hexdigest()==ORIGINAL_SHA
    sec=sections(raw);code=bodies(raw,sec);frame,fsnap,fr=freeze(FRAME,'frame-systems135',('frame_systems135.py',),raw,sec,code)
    terminal,tsnap,tr=freeze(TERMINAL,'terminal-transition135',('terminal_transition135.py','initial_state135.py'),raw,sec,code)
    profile=parse_binary(raw);memory=bytearray(max(x['memory_start']+x['file_end']-x['file_start']for x in profile['segments']))
    for x in profile['segments']:memory[x['memory_start']:x['memory_start']+x['file_end']-x['file_start']]=raw[x['file_start']:x['file_end']]
    labels={}
    for x in json.loads(LABELS.read_text())['labels']:
        assert bytes(memory[x['string_pointer']:x['string_pointer']+x['bytes']]).decode()==x['value']
        labels.setdefault(x['kind'],{})[x['id']]=x['value']
    assert sum(map(len,labels.values()))==29
    del raw,sec,code,memory,profile
    author=load_checker(fsnap,'check_frame_systems135.py','review_frozen_frame135');cases=json.loads((FRAME/'frame-systems135-fixtures.json').read_text());outputs=[json.loads(x)for x in(FRAME/'frame-systems135-results.jsonl').read_text().splitlines()]
    assert strict(cases,norm(author.corpus(False)))
    guards=norm(author.negatives());assert strict(guards,json.loads((FRAME/'frame-systems135-rejections.json').read_text()))and len(guards)==12
    assert[o['id']for o in outputs]==list(range(573));fc=Counter()
    for c,o in zip(cases,outputs):assert strict(c['expected'],o['stages']);independent_frame(c,o,fc)
    assert(fc['stages'],fc['post_pop_null_traps'],fc['packets'])==(944,23,463)
    fr.update(status='passed within complete38007/2602expiryidle and three declared gate domains',cases=573,stages=944,rejections=12,counts=dict(fc),
        regenerated_from_frozen_production=True,independent_queue_and_packet_replay=True,definition_pointer_normalization='Controlled88B definition allocation maps to input explicit ID; all other80B bytes strict',
        game_state_evidence='Frozen runner scans all648 words per2592B entry. This batch retains only exact change lists, not a full rawG sidecar.',
        masks=[],nan_relaxation=False,limitations=frame['limitations'])
    author=load_checker(tsnap,'check_terminal_transition135.py','review_frozen_terminal135');cases=json.loads((TERMINAL/'terminal-transition135-fixtures.json').read_text());outputs=[json.loads(x)for x in(TERMINAL/'terminal-transition135-results.jsonl').read_text().splitlines()]
    assert strict(cases,norm(author.corpus(False)))
    guards=norm(author.negatives());assert strict(guards,json.loads((TERMINAL/'terminal-transition135-rejections.json').read_text()))and len(guards)==5
    assert[o['id']for o in outputs]==list(range(416));tc=Counter()
    for c,o in zip(cases,outputs):
        reduced=[{k:v for k,v in s.items()if k!='raw_g2592_hex'}for s in o['stages']]
        assert strict(c['expected'],reduced)
        initial=author.initialize_empty_profile(author.ConstructorInput135(**{k:int(v)if k in('seed_u64','object_id_u64')else v for k,v in c['input'].items()}))
        independent_terminal(c,o,initial,author.f,labels,tc)
    assert(tc['terminal_stages'],tc['true_terminal_entries'],tc['new_packet_opcode221'],tc['new_packet_opcode232'],tc['actual_constructor226_preserved'])==(832,315,355,315,19)
    tr.update(status='passed true49037 in declared absentterrain/collision Englishfallback domain',cases=416,terminal_stages=832,constructor_calls=416,total_original_calls=1248,
        rejections=5,counts=dict(tc),regenerated_from_frozen_production=True,independent_three_source_stop_wire_notification_replay=True,static_data_labels_independently_read=29,
        labels_evidence=str(LABELS.relative_to(ROOT)),labels_evidence_sha256=sha(LABELS),normalized_heap_word_offsets=[1884,1896],
        other_game_bytes_masked=[],nan_relaxation=False,limitations=terminal['limitations']+['Only observed fixture allocator behavior is retained; no physical heap-address identity is independently reconstructed.'])
    for r,snap in((fr,fsnap),(tr,tsnap)):
        for n,h in r['frozen_source_sha256'].items():assert sha(snap/n)==h
    deps=(Path(__file__),ROOT/'scripts/review_gameplay_phase135.py',ROOT/'scripts/extract_catalogue134.py')
    for prefix,result in(('frame-systems0135',fr),('terminal-transition0135',tr)):
        out=ROOT/'evidence'/datetime.now(timezone.utc).strftime(prefix+'-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
        for p in deps:
            q=out/'reviewer-source'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
        result.update(version='0.135.1',build='0898d5e3',reviewer_source_sha256={str(p.relative_to(ROOT)):sha(p)for p in deps},original_executed_by_reviewer=False,author_sources_modified_by_reviewer=False)
        (out/'review.json').write_text(json.dumps(result,indent=2)+'\n');wrapper=dict(result,evidence_directory=str(out.relative_to(ROOT)),review_sha256=sha(out/'review.json'))
        (ROOT/'reports'/('2026-11-01-'+prefix+'-independent-review.json')).write_text(json.dumps(wrapper,indent=2)+'\n')
        if prefix.startswith('frame'):
            summary='573组/944阶段，550正常case与23个预期null-definition移除后trap分列；完整队列backing与463份消息wire/capacity通过独立字节重放，12个未知guard保持。10源与packageinit闭包、非export节与5入口身份均通过。975只验证无execution11，2602活跃due只partial；2573只早退，49037只false guard。真正终态由后续416组独立覆盖，未追溯扩大本批范围。G2592保存全word变化列表，缺少完整rawG侧录，复核未宣称能从独立raw重新生成这部分列表。'
        else:
            summary='416组/832终态阶段+416真实构造，315次true转移，355份221、315份232及19份原构造226完整保留。独立复算三source停止顺序/所有424、112、88B backing、全部UTF8/control/fixed3通知bytes/capacity及raw2592变化。20源/packageinit闭包与19helper身份通过；29项fallback文字直接由固定原件data字节读回。仅1884/1896两heap地址词归一化，其余原始G字节无mask。Englishfallback与显式terrain/collision缺席是输入域；未恢复真实世界、中文本地化标签、完整1089或880。'
        (ROOT/'reports'/('2026-11-01-'+prefix+'-independent-review.md')).write_text('# 0.135.1 '+prefix+' 独立只读复核\n\n'+summary+'\n\n未重跑原件或修改作者源码。快照模型重生fixture、原保留结果严格类型/形状/值比较、原件非export节逐字节验证均通过。当前协调过的共享host扩容漂移在JSON逐项列出，不混入旧源码。\n\n证据：`'+str((out/'review.json').relative_to(ROOT))+'`。\n')
        print(json.dumps(dict(kind=prefix,path=str(out/'review.json'),sha256=sha(out/'review.json'),counts=result['counts'],drift=list(result['current_source_drift']))))

if __name__=='__main__':main()
