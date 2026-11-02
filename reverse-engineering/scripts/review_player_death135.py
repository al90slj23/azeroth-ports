#!/usr/bin/env python3
"""Second-author, read-only fixed135 fatal40 audit. No production execution.

The1367 dependency is computed by its *other author's* frozen independent
reviewer; this reviewer authored the production1367 and claims no independent
restoration credit for it. Only stdlib and that audited reviewer execute.
"""
from pathlib import Path
from collections import Counter
import argparse,ast,hashlib,json,math,os,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_player_death_recap135 as R
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/player-death135-oracle-20261101T235258.508019Z'
RECEIPT='f4c71af5b092d629812c8084a7cf9daab96292151739059b1fb80393013e9c08'
DEPENDENCY=ROOT/'evidence/player-death-recap135-review-owned-20261102T000113.244785Z/review/review.json'
DEPENDENCY_SHA='9a0b879daa2d18d2b87d3d56786134f4497c0348d32acc338ae353310b7a6dcf'
REFERENCE_SHA='b0c92d1116587a58022028844e2bf24d4fc259d6faec092708f9c5d6f2a7b088'
DEPENDENCY_REPORT=ROOT/'reports/2026-11-02-player-death-recap0135-independent-review.json'
DEPENDENCY_REPORT_SHA='1625cc4628bbb215121e6a5f770bed12f090896c7fcace6b17d9a38b29af6b88'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
STATIC=ROOT/'evidence/player-death135-static-20261101T234954.522203Z'
MASK=(1<<32)-1
def sha(p):return R.sha(p)
def load(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def U(b,o=0):
    if isinstance(b,list):
        assert all(type(v)is int and 0<=v<256 for v in b[o:o+4]),('unknown consumed',o)
        return struct.unpack('<I',bytes(b[o:o+4]))[0]
    return struct.unpack_from('<I',b,o)[0]
def put(b,o,v):b[o:o+4]=struct.pack('<I',v)
def F(w):return struct.unpack('<f',struct.pack('<I',w))[0]
def B(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def add(a,b):return B(F(a)+F(b))
def sub(a,b):return B(F(a)-F(b))
def mul(a,b):return B(F(a)*F(b))
def div(a,b):return B(F(a)/F(b))
def f64(w):return struct.unpack('<d',struct.pack('<Q',int(w)))[0]
def f64bits(x):return struct.unpack('<Q',struct.pack('<d',x))[0]
def packed(guid):
    octets=guid.to_bytes(8,'little');return bytes([sum((1<<i)for i,v in enumerate(octets)if v)])+bytes(v for v in octets if v)
def quote(s):
    out=bytearray(b'"')
    for c in s:
        n=ord(c)
        if n==10:out.extend(b'\\n')
        elif n in(34,92):out.extend(bytes([92,n]))
        elif n<32:out.extend(('\\u%04x'%n).encode())
        else:out.extend(c.encode('utf8'))
    return bytes(out)+b'"'
def number(x):
    if not math.isfinite(x):return b'0'
    if x==math.trunc(x)and abs(x)<10**15:return str(int(x)).encode()
    return format(x,'.3f').encode()
def notification(s,taken,recap,labels):
    counters=dict(s['counters']);fields=[('type',quote('defeat')),('time',number(F(s['now_bits'])))]
    for k,o in(('level',1432),('kills',1084),('elites',1088),('guardians',1092),('bosses',1096)):fields.append((k,number(counters[o])))
    fields.extend([('damage',number(f64(s['damage984_f64_bits']))),('taken',number(f64(taken))),('gold',number(counters[1100])),('chests',number(counters[1104]))])
    for k,v in(('class',labels['class'][s['class_byte']]),('hero',s['hero']),('race',labels['race_fallback'][s['race_byte']]),('bg',labels['zone_fallback'][s['region_index']])):fields.append((k,quote(v)))
    fields.extend([('left',b'true'if s['left2567']else b'false'),('recap',recap)])
    out=bytearray(b'{');capacity=1
    def append(raw):
        nonlocal capacity
        if len(out)+len(raw)>capacity:capacity=max(capacity*2,len(out)+len(raw),8)
        out.extend(raw)
    for i,(k,v)in enumerate(fields):
        if i:append(b',')
        append(quote(k));append(b':');append(v)
    append(b'}');return dict(capacity=capacity,payload_hex=out.hex())

def motion(s,counts):
    result={};packets=[];sequence=s['movement_sequence2412']
    for name,stride,origin,dest,start,duration,guid,timer in(('units',424,316,328,340,344,112,None),('auxiliary',112,32,44,56,60,16,68),('claims',88,44,56,68,72,24,76)):
        rows=[list(x)if isinstance(x,list)else bytearray.fromhex(x)for x in s[name+'_storage']];n=s[name+'_count'];assert n<=len(rows)<=512 and all(len(x)==stride for x in rows)
        for row in rows[:n]:
            if name=='claims':due=not F(s['now_bits'])>=F(add(U(row,start),U(row,duration)))
            elif name=='units':due=U(row)==0 and F(U(row,duration))>0 and F(s['now_bits'])<F(add(U(row,duration),U(row,start)))
            else:due=F(U(row,duration))>0 and F(s['now_bits'])<F(add(U(row,duration),U(row,start)))
            if not due:counts['inactive_records_preserved']+=1;continue
            if name=='claims'and F(U(row,duration))<=0:xyz=[U(row,dest+4*i)for i in range(3)]
            else:
                t=div(sub(s['now_bits'],U(row,start)),U(row,duration));t=0 if F(t)<0 else B(1)if F(t)>1 else t
                xyz=[add(U(row,origin+4*i),mul(sub(U(row,dest+4*i),U(row,origin+4*i)),t))for i in range(3)]
            if s['flat_height_enabled']:xyz[2]=s['flat_height_bits']
            assert s['terrain_grid_absent']and s['collision_grid_absent']and all(math.isfinite(F(x))for x in xyz)
            for o in(origin,dest):
                for i,v in enumerate(xyz):put(row,o+4*i,v)
            put(row,start,s['now_bits']);put(row,duration,0)
            if timer is not None:put(row,timer,s['now_bits'])
            sequence=(sequence+1)&MASK;g=U(row,guid)|(U(row,guid+4)<<32)
            packets.append(dict(opcode=221,capacity=32,payload_hex=(packed(g)+struct.pack('<4I',*xyz,sequence)+b'\1').hex()));counts['stopped_'+name]+=1
        result[name]=dict(count=n,storage=[list(x)if any(v is None for v in x)else bytes(x).hex()for x in rows]);counts['complete_motion_backing_bytes']+=sum(map(len,rows))
    return result,packets,sequence

def semantic(inp,actual,labels,counts):
    s=inp['model_state'];assert s['phase2587']==1 and s['class_byte']==8 and s['race_byte']==1 and s['region_index']==0
    assert s['left2567']==inp['left']and s['hero']==inp['hero']and int(inp['source_guid'])==0 and s['localization_profile']=='english_fallback'
    for name,guid_offset in(('units',112),('auxiliary',16),('claims',24)):
        assert all(struct.unpack_from('<Q',bytes.fromhex(x),guid_offset)[0]!=0 for x in s[name+'_storage'])
    vectors,packets,sequence=motion(s,counts);taken=int(inp['taken_before_bits']);history=dict(capacity=0,head=0,count=0,storage=[],strings=[])
    if inp['kind']=='incoming':
        hp=sub(inp['starting_hp_bits'],inp['amount_bits']);assert F(hp)<=0
        taken=f64bits(f64(taken)+F(inp['amount_bits']));cells=[None]*48
        for o,v in((4,0),(12,5),(20,12),(24,s['now_bits']),(28,inp['amount_bits']),(32,0),(36,hp),(40,B(215))):cells[o:o+4]=struct.pack('<I',v)
        cells[44:46]=[4,0];history=dict(capacity=4,head=0,count=1,storage=[cells]+[[None]*48 for _ in range(3)],strings=[['','Melee','INV_Sword_04']]+[None]*3)
        observed=actual['after']['history'];assert(observed['capacity'],observed['head'],observed['count'])==(4,0,1)and len(observed['active'])==1
        row=observed['active'][0];assert row['strings']==history['strings'][0];raw=bytes.fromhex(row['raw_hex']);assert len(raw)==48
        for o,v in enumerate(cells):
            if v is not None:assert raw[o]==v;counts['history_known_bytes']+=1
        for o in(0,8,16):assert U(raw,o)>0
        counts['history_records']+=1
    else:assert inp['kind']=='helper'and inp['starting_hp_bits']==0 and actual['after']['history']==dict(capacity=0,head=0,count=0,active=[])
    recap=b'{}'
    if not inp['left']:
        # No production1367 is imported. Other-author reader independently
        # proved this pure reference against103 original full1367 calls.
        # Single active row logical projection is equivalent for1367's ordered
        # ring iterator. Use its exported bytes (including unconsumed pointer
        # and padding observations), never fill canonical None with zero.
        # The3 unexported unused slots remain None in expected state above.
        active=actual['after']['history']['active']
        h=dict(capacity=len(active),head=0,count=len(active),rows48_hex=[x['raw_hex']for x in active],strings=[x['strings']for x in active])
        _,recap,_=R.reference(dict(id=inp['id'],history=h,reference_time_bits=s['now_bits']),['mob','elite','boss','object','none'],Counter())
        counts['left0_other_author_recap_consumers']+=1
    note=notification(s,taken,recap,labels)
    cap=s['packet_capacity'];count=s['packet_count']
    for _ in packets:
        if count==cap:cap=max(4,cap*2)
        count+=1
    ncap=s['notification_vector_capacity']
    if s['notification_count']==ncap:ncap=max(4,ncap*2)
    expected=dict(phase=4,hp_bits=0,paused=1,paused_time_bits=s['now_bits'],action_sequence=s['action_sequence1644'],movement_sequence=sequence,packets=packets,notifications=[note],packet_capacity=cap,packet_count=count,notification_capacity=ncap,notification_count=s['notification_count']+1,vectors=vectors,taken_f64_bits=str(taken),maximum_hp_bits=B(215),history=history)
    after=actual['after'];before=actual['before'];raw=bytes.fromhex(after['raw_game2592_hex']);old=bytes.fromhex(before['raw_game2592_hex']);assert len(raw)==len(old)==2592
    predict=bytearray(old)
    for o,v in((408,1),(412,s['now_bits']),(2412,sequence),(1880,cap),(1888,count),(1892,ncap),(1900,s['notification_count']+1)):put(predict,o,v)
    predict[2587]=4
    pointer_observations=[]
    for o,changed in((1884,cap!=before['packet_capacity']),(1896,ncap!=before['notification_capacity'])):
        if changed:
            assert 0<U(raw,o)<33554432;predict[o:o+4]=raw[o:o+4];pointer_observations.append(o)
    if inp['kind']=='incoming':
        for o,v in((968,4),(976,0),(980,1),(1440,0),(1652,s['now_bits'])):put(predict,o,v)
        predict[992:1000]=struct.pack('<Q',taken)
        assert 0<U(raw,972)<33554432;predict[972:976]=raw[972:976]
        # The damage-source registry allocation/layout is deliberately unknown.
        # Its five changing bytes are observational only, never invented.
        for o in(1112,1120):predict[o:o+4]=raw[o:o+4]
        counts['incoming_registry_observation_bytes']+=8;counts['incoming_history_allocator_observation_bytes']+=4
    else:counts['helper_allocator_pointer_words']+=len(pointer_observations)
    assert raw==predict,(inp['id'],'raw Game delta',[o for o,(a,b)in enumerate(zip(raw,predict))if a!=b])
    assert actual['changed_bytes']==[[o,raw[o]]for o in range(2592)if raw[o]!=old[o]]
    counts['helper_complete_Game_bytes'if inp['kind']=='helper'else'incoming_Game_bytes_scanned']+=2592
    counts['Game_allocator_pointer_observation_bytes']+=len(pointer_observations)*4
    for k in('packets','notifications','packet_capacity','packet_count','notification_capacity','notification_count','vectors'):assert after[k]==expected[k],(inp['id'],k)
    assert after['keyed_fields']=={'22':0 if inp['kind']=='incoming'else 215,'28':215,'1109':B(5)}
    assert U(raw,1644)==s['action_sequence1644']and U(raw,1440)==0 and raw[2582]==0 and raw[2587]==4
    counts['notifications']+=1;counts['notification_JSON_bytes']+=len(bytes.fromhex(note['payload_hex']));counts['stop221']+=len(packets);counts['stop_payload_bytes']+=sum(len(bytes.fromhex(x['payload_hex']))for x in packets)
    return expected

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();out=args.output.resolve();assert out.is_relative_to((ROOT/'evidence').resolve());out.mkdir();start=time.monotonic()
    reviewers={str(x.relative_to(ROOT)):sha(x)for x in(Path(__file__),Path(R.__file__))};assert sha(Path(R.__file__))==REFERENCE_SHA and sha(DEPENDENCY)==DEPENDENCY_SHA
    dependency=load(DEPENDENCY);assert dependency['status']=='passed-within-declared-domain'and dependency['cases']==103 and dependency['production_imports']==0 and dependency['new_original_calls']==0 and sha(DEPENDENCY_REPORT)==DEPENDENCY_REPORT_SHA
    for n,h in reviewers.items():dest=out/'reviewer-source'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/n).read_bytes());assert sha(dest)==h
    assert sha(RUN/'comparison.json')==RECEIPT;report=load(RUN/'comparison.json');prepared=load(RUN/'prepared.json');manifest=load(RUN/'manifest.json');runtime=load(RUN/'runtime.json');handoff=load(RUN/'task-handoff.json')
    assert report['status']=='scoped_original_differential_passed'and report['cases']==40 and report['differences']==0
    files=report['source_sha256_before'];assert len(files)==27 and files==report['source_sha256_after']==prepared['source_sha256']
    for n,h in files.items():assert sha(ROOT/n)==sha(RUN/'source-snapshot'/n)==h,n
    edges=R.source_edges(RUN/'source-snapshot',files);assert edges==[tuple(x)for x in report['source_import_edges']]==[tuple(x)for x in prepared['source_import_edges']]and len(edges)==73
    production={n for n in files if n.startswith('reconstruction/')};todo=['reconstruction/core_spec/player_death135.py','reconstruction/core_spec/initial_state135.py','reconstruction/core_spec/incoming135.py'];seen=set()
    while todo:
        n=todo.pop()
        if n in seen:continue
        seen.add(n);todo.extend(b for a,b in edges if a==n)
    assert seen==production and len(production)==20
    for table in('frozen_artifacts','artifacts'):
        for n,h in report[table].items():assert sha(RUN/n)==h,(table,n)
    assert report['expected_before_original']and prepared['expected_before_original']
    checker=(RUN/'source-snapshot/scripts/check_player_death135.py').read_text();assert checker.index("save(out/'expected.json'")<checker.index('subprocess.Popen(')
    for n,h in handoff['new_files'].items():assert sha(ROOT/n)==h,n
    assert len(handoff['new_files'])==7 and handoff['comparison_sha256']==RECEIPT and not handoff['shared_core_modified']
    original=R.SOURCE.read_bytes();assert len(original)==90959080 and hashlib.sha256(original).hexdigest()==R.SOURCE_SHA==report['original_sha256']
    private=(RUN/manifest['module_file']).read_bytes();assert hashlib.sha256(private).hexdigest()==manifest['module_sha256']==report['module_sha256']
    old,new=R.sections(original),R.sections(private);assert[k for k,*_ in old]==[k for k,*_ in new]and not any(k==8 for k,*_ in old)
    assert all(original[a:z]==private[b:y]for(k,a,_,z),(_,b,_,y)in zip(old,new)if k!=7)
    ex=lambda raw,sects:R.exports(raw,next(x for x in sects if x[0]==7))
    assert ex(private,new)==ex(original,old)+[(x['export'],0,x['index'])for x in manifest['roles']]+[('research_death135_stack0',3,0)]
    r=R.Reader(original,next(x for x in old if x[0]==1)[2]);types=[]
    for _ in range(r.uint()):
        assert r.byte()==0x60;n=r.uint();a=bytes(r.byte()for _ in range(n));n=r.uint();b=bytes(r.byte()for _ in range(n));types.append((a.hex(),b.hex()))
    r=R.Reader(original,next(x for x in old if x[0]==3)[2]);decl=[r.uint()for _ in range(r.uint())]
    r=R.Reader(original,next(x for x in old if x[0]==10)[2]);body=[]
    for _ in range(r.uint()):n=r.uint();body.append((r.pos,r.pos+n));r.pos+=n
    assert sha(STATIC/'proof.json')==handoff['static_proof_sha256'];proof=load(STATIC/'proof.json');functions={};wat={}
    indices={1560,1073,5620,17119,17217,16340,45845,1938,1367,984,58162,11735,52241,54802}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
        for index in sorted(indices):
            row=dict(db.execute('select *from functions where idx=?',(index,)).fetchone());a,b=body[index-878];assert(a,b)==(row['body_start'],row['body_end']);stream.seek(row['wat_start']);text=stream.read(row['wat_end']-row['wat_start']);assert len(text)<1048576
            functions[index]=dict(body_start=a,body_end=b,body_sha256=hashlib.sha256(original[a:b]).hexdigest(),signature=list(types[decl[index-878]]),wat_sha256=hashlib.sha256(text).hexdigest(),wat_bytes=len(text));wat[index]=text.decode();(out/f'{index}.wat').write_bytes(text)
            if(STATIC/f'{index}.wat').exists():assert text==(STATIC/f'{index}.wat').read_bytes()
    for role in manifest['roles']:assert functions[role['index']]['signature']==[role['params_hex'],role['results_hex']]and functions[role['index']]['body_sha256']==role['body_sha256']
    windows={}
    for name,index,a,b,terms in(
        ('1073_HP_taken_prefix',1073,1594,1615,('f32.store offset=1652','f32.store offset=1440','f64.store offset=992')),
        ('1073_minimum_and_intrinsic_gate',1073,3877,3927,('i32.load8_u offset=2578','f32.le','i32.const 12','f32.load offset=1264')),
        ('1073_modifier31_separate_gate',1073,3990,4025,('i32.load offset=2056','i32.const 31')),
        ('1073_zero_lives_real_death',1073,4596,4628,('i32.load offset=1632','i32.store offset=1440','call 5620','f32.const 0x1p-1')),
        ('5620_mode0_complete',5620,8,64,('i32.store8 offset=2587','i32.store offset=408','f32.store offset=412','i32.load8_u offset=2582','call 17119','call 1938','i32.store offset=1900')),
        ('984_empty_modifiers_skip_callbacks',984,8,25,('i32.load offset=2056','i32.const 36','br_if 2')),
        ('17119_NPC_predicate',17119,33,63,('i32.load','i32.const 344','i32.const 340','f32.gt','f32.lt')),
        ('17217_aux_predicate',17217,30,58,('i32.const 60','i32.const 56','f32.gt','f32.lt')),
        ('16340_claim_predicate',16340,28,57,('i32.const 68','i32.const 72','f32.ge','i32.eqz')),
        ('1938_left0_actual_recap',1938,1519,1544,('i32.const 968','i32.const 412','i32.const 2352','i32.load offset=408','call 1367'))):
        text='\n'.join(wat[index].splitlines()[a-1:b]);assert all(t in text for t in terms),name
        windows[name]=dict(function=index,first_line=a,last_line=b,sha256=hashlib.sha256(text.encode()).hexdigest(),text=text)
    for index,terms in{1073:('f32.store offset=1440','f64.store offset=992','i32.load8_u offset=2578','i32.const 12','i32.const 31','i32.load offset=1632','call 5620'),5620:('i32.store8 offset=2587','i32.store offset=408','f32.store offset=412','call 17119','call 1938'),17119:('i32.const 344','i32.const 340','call 45845','call 17217','call 16340'),17217:('i32.const 60','i32.const 56','call 45845'),16340:('i32.const 72','i32.const 68','call 45845'),45845:('i32.const 221','i32.store16'),1938:('i32.load8_u offset=2567','i32.load offset=408','call 1367')}.items():assert all(t in wat[index]for t in terms),index
    read=R.static_reader(original,old);labels={}
    label_path=ROOT/'evidence/terminal-transition0135-static-20261101T075941.450411Z/label-evidence.json'
    for row in load(label_path)['labels']:assert read(row['string_pointer'],row['bytes']).decode()==row['value'];labels.setdefault(row['kind'],{})[row['id']]=row['value']
    assert read(5414827,5)==b'Melee'and read(5414832,12)==b'INV_Sword_04'and read(1583464,6)==b'defeat'
    assert U(read(5463136+72,4))==B(215)
    p,n=struct.unpack('<2I',read(5459304+16,8));assert list(struct.iter_unpack('<2I',read(p,n*8)))==[(8,B(.2)),(9,B(.2))]
    fixtures=load(RUN/'fixtures.json');inputs=load(RUN/'inputs.json');expected=load(RUN/'expected.json');actual=[json.loads(l)for l in(RUN/'stdout.jsonl').read_text().splitlines()];assert len(fixtures)==len(inputs)==len(expected)==len(actual)==40
    counts=Counter();groups=Counter();cases=[]
    for c,i,e,a in zip(fixtures,inputs,expected,actual):
        assert c['id']==i['id']==e['id']==a['id']and c['input']==i and c['expected']==e['expected']and set(i)=={'id','kind','left','hero','model_state','starting_hp_bits','amount_bits','source_guid','taken_before_bits'}
        constructor=bytes.fromhex(a['constructor_raw_game2592_hex']);before=bytes.fromhex(a['before']['raw_game2592_hex']);s=i['model_state'];assert len(constructor)==2592 and a['constructor_innate_kind']==8
        assert all(U(constructor,o)==0 for o in(1712,2056,2032,1632,1792,664,2116))and before[2578]==0 and U(before,1568)==0
        # Source constructor snapshot stays an observation. All fixture writes
        # are rebound independently; allocator pointer values are observed.
        patched=bytearray(constructor);put(patched,220,U(before,220));put(patched,224,len(i['hero'].encode('utf8')))
        for o,v in s['counters']:put(patched,o,v)
        for o,v in((2352,s['now_bits']),(1644,s['action_sequence1644']),(2412,s['movement_sequence2412']),(1440,i['starting_hp_bits']),(1568,0)):put(patched,o,v)
        patched[984:992]=struct.pack('<Q',int(s['damage984_f64_bits']));patched[992:1000]=struct.pack('<Q',int(i['taken_before_bits']));patched[2587]=1;patched[2567]=i['left'];patched[2582]=0;patched[2578]=0
        for name,base in(('units',1784),('auxiliary',656),('claims',2108)):
            if s[name+'_storage']:put(patched,base,len(s[name+'_storage']));put(patched,base+4,U(before,base+4));put(patched,base+8,s[name+'_count'])
        assert before==patched and a['before']['packets']==a['before']['notifications']==[]and a['before']['history']==dict(capacity=0,head=0,count=0,active=[])
        p=semantic(i,a,labels,counts);assert p==c['expected'],(i['id'],'independent expectation');assert(a['stack_after'],a['host_calls'])==(1048576,0)
        counts[i['kind']+'_calls']+=1;groups[c['group']]+=1;cases.append(dict(id=i['id'],kind=i['kind'],group=c['group'],left=i['left'],stop_count=len(p['packets']),notification_capacity=p['notifications'][0]['capacity'],notification_bytes=len(bytes.fromhex(p['notifications'][0]['payload_hex']))))
    projection=load(RUN/'unknown-cell-projection.json');assert projection['case_id']==1 and projection['preserved_unknown_cells']==1096
    # Reconstruct the sparse input from the original predicates, then apply
    # this reviewer's lazy interpreter. Do not merely accept author's mask.
    sparse=dict(inputs[1]['model_state'])
    for name in('units','auxiliary','claims'):
        sparse[name+'_storage']=[]
        for j,h in enumerate(inputs[1]['model_state'][name+'_storage']):
            raw=bytes.fromhex(h)
            ranges=(((0,4),(112,120),(316,348))if j==0 else((0,4),(344,348)))if name=='units'else(((16,24),(32,64))if j==0 else((60,64),))if name=='auxiliary'else(((24,32),(44,76))if j==0 else((68,76),))
            sparse[name+'_storage'].append([v if any(a<=o<b for a,b in ranges)else None for o,v in enumerate(raw)])
    sparse_result,sparse_packets,_=motion(sparse,Counter());assert sparse_packets==fixtures[1]['expected']['packets']
    assert {k:v['storage']for k,v in sparse_result.items()}==projection['vectors']
    known=unknown=0
    for name,rows in projection['vectors'].items():
        observed=actual[1]['after']['vectors'][name]['storage'];assert len(rows)==len(observed)
        for cells,h in zip(rows,observed):
            raw=bytes.fromhex(h)
            for o,v in enumerate(cells):
                if v is None:unknown+=1
                else:assert raw[o]==v;known+=1
    assert(known,unknown)==(152,1096);counts['model_only_unknown_preservation_cells']=unknown;counts['known_cell_original_projection_bytes']=known
    terminal=load(RUN/'owned-terminal.json');assert terminal==report['process']and terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<terminal['deadline_seconds']==60
    assert R.missing(terminal['pid'])and R.missing(terminal['pgid'],True)
    assert runtime==report['runtime']and(runtime['full1560_calls'],runtime['full5620_direct_calls'],runtime['full1073_calls'],runtime['fresh_instances'])==(40,18,22,40)and runtime['actual_host_calls']==0 and runtime['denied_imports']==878 and runtime['max_memory_bytes']<=33554432 and runtime['stack_guards']==337
    assert not any(runtime[k]for k in('nested_callee_count_instrumented','app_start_called','network_used','user_saves_accessed'))
    assert dict(groups)==report['groups']and counts['stop221']==27 and counts['notifications']==40
    for n,h in files.items():assert sha(ROOT/n)==sha(RUN/'source-snapshot'/n)==h
    for n,h in reviewers.items():assert sha(ROOT/n)==h
    assert sha(DEPENDENCY)==DEPENDENCY_SHA and sha(RUN/'comparison.json')==RECEIPT
    result=dict(status='passed-within-declared-domain',author_receipt_sha256=RECEIPT,new_original_calls=0,production_imports=0,production_executions=0,reviewer_sources=reviewers,source_count=len(files),production_sources=len(production),local_import_edges=len(edges),sources_verified=files,static_functions=functions,counts=dict(counts),groups=dict(groups),cases=cases,original_runtime=runtime,original_process=terminal,dependency=dict(receipt=str(DEPENDENCY.relative_to(ROOT)),sha256=DEPENDENCY_SHA,reference_sha256=REFERENCE_SHA,cases=103,independent_reviewer='self_buffs119_review',current_reviewer_authored_production1367=True,new_independent1367_credit=0),unknown_projection_kind='152 known bytes original-compared;1096 None preservation model-only,0 new original cases',static_proof_sha256=sha(STATIC/'proof.json'),task_handoff_sha256=sha(RUN/'task-handoff.json'),artifact_sha256={n:sha(RUN/n)for n in set(report['artifacts'])|set(report['frozen_artifacts'])|{'comparison.json','task-handoff.json'}},seconds=time.monotonic()-start,limitations=['Bounded fresh1560/typed fixture setup,not natural full App or completed game.40 setup1560 separate from40 targets.','18 complete5620 rawGame2592 compared with explicit allocator pointer observations;22 complete1073 Game deltas additionally preserve8 observed registry bytes and4 observed history pointer bytes per case rather than invent registry semantics.','All declared scalar,motion full backing,complete27 stop221 payloads/capacities,40 complete defeatJSON/capacities and22 active48 history known cells independently recomputed.','History unused capacity backing not exported;active pointerwords/padding unresolved in canonical expected.','12 left0 recap consumers use other-author independently validated pure1367 reviewer;current reviewer authored production1367,no own-helper independent restoration credit.','16 negative guards and1096 None preservation are author model selfcheck only;this review does not execute them or add original cases.','Actual sourceGUID0 unmatched,empty callback/item/modifier/live domains,innatekind8,lives0,minone0,phase1/mode0,Englishfallback only.','No intrinsic12 resurrection,modifier31,lives>0,mode1,nonflat height or naturalcallback/source registry producer acceptance.'])
    result['static_windows']=windows
    result['dependency']['tracked_report']=str(DEPENDENCY_REPORT.relative_to(ROOT));result['dependency']['tracked_report_sha256']=DEPENDENCY_REPORT_SHA
    result['dependency']['single_active_history_adapter']='1367 reference sees logical active0/1-row projection from exported actual48;all consumed scalar/string cells independently validated first.Canonical4-slot history keeps None,unused backing unexported;no None filled.'
    result['innate_gate_equivalence']='Actual constructor kind8;author expected fixture boundary kind9.Both satisfy original kind!=12 before any cooldown read.Exact actual8 verified in all40,not claimed same numeric boundary.'
    result['negative_guard_receipt']=dict(count=16,kind='author model selfcheck only,not executed by this reviewer',sha256=sha(RUN/'rejections.json'))
    save(out/'review.json',result);print(json.dumps(dict(output=str(out/'review.json'),sha256=sha(out/'review.json'),cases=40,counts=dict(counts),seconds=result['seconds'])))

if __name__=='__main__':main()
