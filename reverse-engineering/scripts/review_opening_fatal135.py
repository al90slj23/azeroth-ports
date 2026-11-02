#!/usr/bin/env python3
"""Independent, read-only continuous-fatal135 evidence review.

No production model/checker, builder, target WASM or native client is executed.
The explicitly frozen CAS transport is the only non-reviewer executable input.
Reference combat is limited to the actual ordinary, no-shield, empty-item lane.
"""
from pathlib import Path
from collections import Counter, defaultdict
import argparse, ast, hashlib, importlib.util, json, math, os, sqlite3, struct, sys, time
sys.dont_write_bytecode=True
import review_opening_motion_rune135 as V
import review_player_death135 as D
import review_player_death_recap135 as C
from review_stats138 import function_ids

M=V.M; P=V.P; S=V.S; BASE=V.BASE; ROOT=M.ROOT
F=M.F; B=M.B; U=M.u; add=M.add; sub=M.sub; mul=M.mul; div=M.div
COUNTERS=(1432,1084,1088,1092,1096,1100,1104)
CODEC_SHA='0b038e68360219ef9886465446fe5d7d375dc0284bbf28f951eec089c9abbacb'
RECAP_SHA='b0c92d1116587a58022028844e2bf24d4fc259d6faec092708f9c5d6f2a7b088'

def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def frozen_reviewers(out):
    pending=[Path(__file__).resolve()];seen={}
    while pending:
        path=pending.pop();name=str(path.relative_to(ROOT))
        if name in seen:continue
        seen[name]=M.sha(path)
        for node in ast.walk(ast.parse(path.read_text())):
            modules=[a.name for a in node.names]if isinstance(node,ast.Import)else[node.module]if isinstance(node,ast.ImportFrom)and node.module else[]
            for module in modules:
                child=ROOT/'scripts'/(module.replace('.','/')+'.py')
                if child.is_file():assert module.startswith('review_'),('Reviewer may not import production/checker',module);pending.append(child)
        target=out/'reviewer-source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
    return seen
def rows(raw,name):
    v=raw['vectors'][name];return[bytes.fromhex(x)for x in v['storage'][:v['count']]]
def guid(row):return int.from_bytes(row[112:120],'little')
def position(row,now):
    duration=U(row,344)
    if F(duration)<=0:return[U(row,o)for o in(328,332,336)]
    ratio=div(sub(now,U(row,340)),duration);ratio=0 if F(ratio)<0 else B(1)if F(ratio)>1 else ratio
    return[add(U(row,a),mul(sub(U(row,b),U(row,a)),ratio))for a,b in((316,328),(320,332),(324,336))]
def distance(x,y):
    dx,dy=sub(x[0],y[0]),sub(x[1],y[1]);return B(math.sqrt(F(add(mul(dx,dx),mul(dy,dy)))))
def known_value(want,actual,path,counts):
    if want is None and len(path)>=5 and path[:3]==('projection','run_ledger','incoming_history')and path[3]=='storage':
        assert type(actual)is int and 0<=actual<=255;counts['unknown_history_pointer_or_unwritten_cells']+=1;return
    if want is None and path in(('projection','paused408'),('projection','paused412_bits')):
        assert type(actual)is int and 0<=actual<=0xffffffff;counts['unwritten_pause_words']+=1;return
    if want is None and len(path)>=3 and path[-3]=='pickup_words':
        assert type(actual)is int and 0<=actual<=0xffffffff
        if path[-1]==1:counts['unwritten_pickup_arrival_words']+=1;return
        assert path[-1]==3 and path[-2]in BASE.BINDER.indices;counts['verified_opaque_pickup_amount_words']+=1;return
    assert type(want)is type(actual),(path,type(want),type(actual))
    if isinstance(want,dict):
        assert set(want)<=set(actual),(path,set(want)-set(actual))
        for k,v in want.items():known_value(v,actual[k],path+(k,),counts)
    elif isinstance(want,list):
        assert len(want)==len(actual),(path,len(want),len(actual))
        for i,(a,b)in enumerate(zip(want,actual)):known_value(a,b,path+(i,),counts)
    else:assert want==actual,(path,want,actual);counts['projection_leaves']+=1

class History:
    def __init__(self):self.data=[];self.strings=[];self.head=0;self.count=0;self.counts=Counter()
    def append(self,now,damage,hp,maximum,metadata,rank):
        cap=len(self.data);cutoff=add(now,B(-10))
        while self.count and(self.count>399 or F(U(self.data[self.head],24))<F(cutoff)):
            self.head=(self.head+1)%cap;self.count-=1;self.counts['pruned']+=1
        if self.count==cap:
            old=cap;cap=max(4,cap*2);self.data.extend([[None]*48 for _ in range(cap-old)]);self.strings.extend([None]*(cap-old))
            if self.head>old-self.count:
                prefix=old-self.head;suffix=self.count-prefix
                if prefix>suffix and cap-old>=suffix:
                    self.data[old:old+suffix]=[r[:]for r in self.data[:suffix]];self.strings[old:old+suffix]=self.strings[:suffix]
                else:
                    dest=cap-prefix;self.data[dest:cap]=[r[:]for r in self.data[self.head:old]];self.strings[dest:cap]=self.strings[self.head:old];self.head=dest
            self.counts['growths']+=1
        slot=(self.head+self.count)%cap;row=self.data[slot][:]
        for off,text in zip((0,8,16),metadata):row[off:off+4]=[None]*4;row[off+4:off+8]=struct.pack('<I',len(text.encode('utf8')))
        row[24:44]=struct.pack('<5I',now,damage,0,hp,maximum);row[44:46]=[rank,0]
        self.data[slot]=row;self.strings[slot]=list(metadata);self.count+=1;self.counts['appends']+=1
    def check(self,raw):
        h=raw['projection']['run_ledger']['incoming_history'];cap=len(self.data)
        assert h['header']==dict(capacity=cap,head=self.head,count=self.count)
        assert len(h['storage'])==cap
        for i,(want,actual)in enumerate(zip(self.data,h['storage'])):
            assert len(actual)==48
            for j,v in enumerate(want):
                if v is not None:assert v==actual[j],('independent ring',raw.get('frame'),i,j,v,actual[j]);self.counts['known_backing_bytes']+=1
                else:self.counts['unknown_backing_bytes_retained']+=1
        assert h['active']==[dict(slot=(self.head+j)%cap,strings=self.strings[(self.head+j)%cap])for j in range(self.count)]

def physical_ledger(raw,counts):
    game=bytes.fromhex(raw['raw_game2592_hex']);p=raw['projection'];a=raw['run_ledger135'];h=a['incoming_history'];cap,ptr,head,n=struct.unpack_from('<4I',game,968)
    assert h['header']==dict(capacity968=cap,pointer972=ptr,head976=head,count980=n,raw_header16_hex=game[968:984].hex())
    assert 0<=n<=cap<=4096 and(head==0 if cap==0 else 0<=head<cap)and ptr+cap*48<=raw['memory_bytes']
    storage=[bytes.fromhex(x)for x in h['storage48_hex']];assert len(storage)==cap and all(len(x)==48 for x in storage)
    assert b''.join(storage).hex()==h['backing_hex']and h['stride']==48
    assert p['run_ledger']['incoming_history']['header']==dict(capacity=cap,head=head,count=n)
    assert p['run_ledger']['incoming_history']['storage']==[list(x)for x in storage]
    assert len(h['active'])==n
    for logical,item in enumerate(h['active']):
        slot=(head+logical)%cap;row=storage[slot];assert item['slot']==slot and item['raw48_hex']==row.hex()and len(item['strings'])==3
        text=[]
        for j,s in enumerate(item['strings']):
            q,length=struct.unpack_from('<2I',row,j*8);data=bytes.fromhex(s['utf8_hex'])
            assert(q,length)==(s['pointer'],s['length'])and len(data)==length and q+length<=raw['memory_bytes']and data.decode('utf8')==s['text'];text.append(s['text'])
        assert p['run_ledger']['incoming_history']['active'][logical]==dict(slot=slot,strings=text)
    hero=a['hero'];capacity,pointer,length=struct.unpack_from('<3I',game,216)
    assert hero['raw_header12_hex']==game[216:228].hex()and(capacity,pointer,length)==(hero['capacity216'],hero['pointer220'],hero['length224'])
    assert capacity==length==0 and pointer==1 and hero['utf8_hex']==''and hero['text']==p['run_ledger']['hero']==''
    assert p['run_ledger']['counters']=={str(o):U(game,o)for o in COUNTERS}
    assert a['scalar_words']=={str(o):U(game,o)for o in(*COUNTERS,1632,408,412)}
    assert p['run_ledger']['lives1632']==U(game,1632)==0 and p['run_ledger']['left2567']==a['left2567']==game[2567]==0
    assert(p['paused408'],p['paused412_bits'])==(U(game,408),U(game,412))
    counts['physical_history_backing_bytes_bound']+=cap*48;counts['physical_active_strings_bound']+=n*3

def static_bindings(original,identities,out):
    profile=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z';proof={};texts={}
    with sqlite3.connect((profile/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(profile/'official-0.135.1-full.wat').open('rb')as stream:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
        for index in(921,1073,5620,17119,17217,16340,1938,1367,984,1560,69798,27375,914,2862,20660,27457,45845,13814):
            row=dict(db.execute('select * from functions where idx=?',(index,)).fetchone());identity=identities[index]
            assert(row['body_start'],row['body_end'])==(identity['body_start'],identity['body_end'])
            stream.seek(row['wat_start']);wat=stream.read(row['wat_end']-row['wat_start']);assert len(wat)<=16*1024*1024
            (out/'static').mkdir(exist_ok=True);(out/'static'/f'{index}.wat').write_bytes(wat)
            proof[index]=dict(original_identity=identity,WAT_bytes=len(wat),WAT_sha256=M.digest(wat));texts[index]=wat.decode()
    terms={921:('f32.load offset=400','f32.load offset=352','f32.store offset=352','f32.load offset=308','f32.load offset=404','call 69798','call 1073'),69798:('f32.load offset=132','f32.load offset=128','f32.load offset=140','f32.load offset=136','f32.load offset=296','f32.mul'),1073:('f32.store offset=1440','f64.store offset=992','i32.load8_u offset=2578','i32.load offset=1632','call 5620'),5620:('i32.store8 offset=2587','i32.store offset=408','f32.store offset=412','call 17119','call 1938'),17119:('call 17217','call 16340','call 29631'),1938:('i32.load8_u offset=2567','i32.load offset=408','call 1367'),984:('i32.load offset=2056','i32.const 36'),914:('i32.store offset=1084','i32.store offset=1088'),20660:('i32.store offset=1104',)}
    for index,values in terms.items():
        if not values:continue
        assert all(value in texts[index]for value in values),('static instructions',index)
    # Freeze exact ordered-drain argument evidence: nonzero source, contact1,
    # category0. This is not the earlier sourceGUID0/flag0 fatal40 domain.
    lines=texts[921].splitlines();at=next(j for j,x in enumerate(lines)if x.strip()=='call 1073')
    window='\n'.join(x.strip()for x in lines[at-8:at+7]);assert 'i32.const 1\ni32.const 0\nlocal.get 2\ncall 1073'in window
    proof['ordinary_contact1073_window']=dict(first_line=at-7,last_line=at+7,text=window,sha256=M.digest(window.encode()))
    at_move=next(j for j,x in enumerate(lines)if x.strip()=='call 27457');assert at_move<at
    window='\n'.join(x.strip()for x in lines[at_move-15:at_move+2]);assert 'f32.const 0x1.f4p+9 (;=1000;)'in window and 'i32.trunc_sat_f32_u'in window
    proof['ordinary_move_before_incoming_window']=dict(first_line=at_move-14,last_line=at_move+2,text=window,sha256=M.digest(window.encode()))
    window='\n'.join(x.strip()for x in lines[3685:3775]);assert all(x in window for x in('i32.load8_u offset=108','f32.load offset=288','f32.load offset=292','f32.const 0x1.8p+1 (;=3;)','f32.const 0x1.4p+4 (;=20;)'))
    proof['guardian_idle_no_engagement_window']=dict(first_line=3686,last_line=3775,text=window,sha256=M.digest(window.encode()))
    assert all(term in texts[27457]for term in('i32.const 221','call 15916','call 45628','i32.const 256','i32.const 0','i32.const 1','local.get 5','i32.le_u'))
    assert all(term in texts[45845]for term in('i32.const 221','call 15916','call 45628','i32.const 1','i32.store8'))
    lines330=[x.strip()for x in texts[13814].splitlines()];assert any(a=='i32.const 330'and b.startswith('i32.store16')for a,b in zip(lines330,lines330[1:]))
    return proof

class Combat:
    def __init__(self,read,world):
        self.read=read;self.world=world;self.history=History();self.counts=Counter();self.events=[];self.fatal=None;self.tail=[]
        self.kills=0;self.elites=0;self.earned=0;self.last_counters=None;self.recap_counts=Counter()
    def observe(self,before,raw,dt):
        game=bytes.fromhex(raw['raw_game2592_hex']);p=raw['projection'];stage=raw.get('kind');now=U(game,2352)
        physical_ledger(raw,self.counts)
        assert game[2571]==0,'Autocollect chest branch requires its explicit producer guard'
        if before is not None:
            oldgame=bytes.fromhex(before['raw_game2592_hex']);oldrows={guid(r):r for r in rows(before,'units')}
            for row in rows(raw,'units'):
                prior=oldrows.get(guid(row))
                if prior is not None and U(prior)==0 and U(row)==1:
                    assert all(U(prior,o)==0xffffffff for o in(40,64,244))
                    self.kills+=1;self.elites+=prior[416]&1;self.counts['raw_new_ordinary_deaths']+=1
            gold_delta=U(game,1456)-U(oldgame,1456)
            assert gold_delta>=0,('unadmitted spend',raw.get('frame'),stage,gold_delta)
            self.earned+=gold_delta
            if stage=='ai':self.incoming(before,raw,dt)
        assert(U(game,1084),U(game,1088),U(game,1092),U(game,1096),U(game,1100),U(game,1104))==(self.kills,self.elites,0,0,self.earned,0),('independent counters',raw.get('frame'),stage)
        assert U(game,1432)==p['progression']['level'];self.history.check(raw)
        if self.fatal is not None and raw['stage_index']>self.fatal['stage_index']:
            assert game[2587]==4 and U(game,408)==1 and U(game,412)==self.fatal['now_bits']
            assert p['terminal_notifications']==self.fatal['notifications']and p['fatal_stop_packets']==self.fatal['canonical_stop_packets']
            self.tail.append(dict(frame=raw['frame'],stage=stage,stage_index=raw['stage_index'],phase=4,hp_bits=U(game,1440)))
    def incoming(self,before,raw,dt):
        a=bytes.fromhex(before['raw_game2592_hex']);z=bytes.fromhex(raw['raw_game2592_hex']);now=U(a,2352);p=raw['projection']
        assert a[2587]==1 and a[2582]==0 and a[2576]&1==0 and a[2578]==0
        assert U(a,2032)==U(a,2056)==0 and U(a,1444)==0 and U(a,1624)==0
        live=rows(before,'live32');active12=any(U(r,8)==12 and F(U(r,24))>F(now)for r in live)
        raw13=B(-0.)
        for r in live:
            if U(r,8)==13 and F(U(r,24))>F(now):raw13=add(raw13,U(r,12))
        assert F(raw13)<=0
        attacks=[];contact=set();pre=rows(before,'units');xyz=[U(a,o)for o in(1416,1420,1424)]
        guardian_owners={int(owner['guid']):owner for owner in before['projection']['guardian_cooldowns']}
        for row in pre:
            if U(row)!=0:continue
            if U(row,64)!=0xffffffff:
                assert guid(row)in guardian_owners and U(row,64)==U(row,72)==3 and U(row,40)==U(row,244)==0xffffffff
                assert not any(U(row,o)for o in(8,16,232,240,360,372,380,388))
                if F(U(row,400))>F(now):self.counts['guardian_locked_no_contact']+=1;continue
                pos=position(row,now);d=distance(pos,xyz)
                assert F(d)>F(U(row,308))and row[108]==0 and U(row,288)==U(row,292)and F(U(row,292))>0
                specials=rows(before,'special');index=U(row,92);home=[U(specials[index],o)for o in(16,20,24)]if index<len(specials)else pos
                assert F(distance(pos,home))>3 or F(d)>20,'Guardian engagement is outside the proven idle input domain'
                post=next(owner for owner in raw['projection']['guardian_cooldowns']if int(owner['guid'])==guid(row))
                assert post['timers_bits']==guardian_owners[guid(row)]['timers_bits']
                self.counts['guardian_idle_no_contact']+=1;continue
            assert all(U(row,o)==0xffffffff for o in(40,64,244))
            if F(U(row,400))>F(now):continue
            pos=position(row,now)
            if F(distance(pos,xyz))>F(U(row,308)):continue
            contact.add(guid(row))
            if F(sub(U(row,352),dt))<=0 and F(U(row,404))<=F(now):
                assert U(self.read(U(row,284),4))&1==0,'Only ordinary melee queue producer is admitted'
                weakness=U(row,128)if F(U(row,132))>F(now)else U(row,136)if F(U(row,140))>F(now)else 0
                attacks.append((row,mul(U(row,296),sub(B(1),weakness))))
        hp=U(a,1440);taken=struct.unpack_from('<d',a,992)[0];last=U(a,1652);phase=1;events=[]
        for row,amount in attacks:
            if phase!=1:self.counts['post_fatal_phase_guard_attacks']+=1;continue
            if active12:self.counts['active12_guard_attacks']+=1;continue
            damage=mul(amount,sub(B(1),U(a,1568)));hp=sub(hp,damage);taken+=F(damage);last=now
            nameptr,namelen=struct.unpack('<2I',self.read(U(row,284)+16,8));label=self.read(nameptr,namelen).decode('utf8')
            self.history.append(now,damage,hp,U(a,1536),(label,'Melee','INV_Sword_04'),row[416])
            events.append(dict(guid=str(guid(row)),amount_bits=amount,damage_bits=damage,hp_after_prefix_bits=hp,source=label))
            if F(hp)<=0:phase=4;hp=0
        assert hp==U(z,1440)and struct.pack('<d',taken)==z[992:1000]and last==U(z,1652)and phase==z[2587],('independent incoming',raw['frame'],hp,U(z,1440),phase,z[2587])
        self.counts['queued_contact_attacks']+=len(attacks);self.counts['accepted_incoming_history']+=len(events)
        if events:self.events.append(dict(frame=raw['frame'],now_bits=now,events=events))
        if phase==4:
            assert self.fatal is None;assert U(z,408)==1 and U(z,412)==now and U(z,1632)==0 and z[2567]==0
            innate_kind=U(self.read(U(a,1256),4));assert innate_kind!=12 or F(U(a,1264))>0,'Available intrinsic12 resurrection is outside this admitted fatal branch'
            appended=raw['packets']['active'][before['packets']['count']:]
            invocation221=[[221,x['capacity'],x['payload_hex']]for x in appended if x['opcode']==221]
            stops=[];canonical=[];normal=[];other=[]
            for packet in appended:
                if packet['opcode']!=221:continue
                data=bytes.fromhex(packet['payload_hex']);mask=data[0];at=1;g=0
                for j in range(8):
                    if mask>>j&1:assert data[at]!=0;g|=data[at]<<(8*j);at+=1
                if len(data)!=at+17 or data[-1]!=1:
                    assert len(data)==at+41 and packet['capacity']==64 and data[at+16]==0 and U(data,at+17)==256 and U(data,at+25)==1,'Only the statically bound27457 ordinary movement alternative is admitted'
                    start=list(struct.unpack_from('<3I',data,at));end=list(struct.unpack_from('<3I',data,at+29));seq=U(data,at+12);duration_ms=U(data,at+21)
                    source=next(r for r in pre if guid(r)==g);logical=position(source,now);height=self.world.height(logical[0],logical[1]);logical[2]=logical[2]if height is None else height
                    assert start==logical and duration_ms>=1 and all(math.isfinite(F(w))for w in end)
                    height=self.world.height(end[0],end[1]);assert height is None or height==end[2]
                    normal.append(dict(guid=str(g),sequence=seq,start_xyz_bits=start,end_xyz_bits=end,duration_ms=duration_ms,source_function=27457,capacity64=True,payload_hex=data.hex()))
                    other.append([221,packet['capacity'],packet['payload_hex']]);continue
                source=next(r for r in pre if guid(r)==g);assert g not in contact and U(source)==0
                assert packet['capacity']==32
                assert(F(U(source,344))>0 and F(now)<F(add(U(source,340),U(source,344))))or(F(U(source,348))<=F(now)and F(U(source,400))<=F(now))
                point=position(source,now);height=self.world.height(point[0],point[1]);point[2]=point[2]if height is None else height
                x,y,zword,seq=struct.unpack_from('<4I',data,at);assert[x,y,zword]==point
                final=next(r for r in rows(raw,'units')if guid(r)==g)
                assert[U(final,o)for o in(316,320,324,328,332,336,340,344)]==point+point+[now,0]
                stops.append(dict(guid=str(g),sequence=seq,xyz_bits=point,original_payload_hex=data.hex()))
                canonical.append([221,packet['capacity'],packet['payload_hex']])
            assert stops and [x['sequence']for x in stops]==list(range(stops[0]['sequence'],stops[0]['sequence']+len(stops)))and stops[-1]['sequence']==U(bytes.fromhex(raw['raw_game2592_hex']),2412)
            assert p['fatal_stop_packets']==canonical and len(normal)==1 and normal[0]['sequence']+1==stops[0]['sequence']
            first_stop=next(i for i,x in enumerate(appended)if x['opcode']==221 and [221,x['capacity'],x['payload_hex']]in canonical)
            assert any(x['opcode']==330 for x in appended[:first_stop])and all(x['opcode']!=330 for x in appended[:next(i for i,x in enumerate(appended)if x['opcode']==221)])
            transitions=raw['run_ledger135']['fatal_transitions'];assert len(transitions)==1
            assert transitions[0]==dict(from_phase=1,to_phase=4,call_role='update_units',entry_index=921,call_returned=True,previous_packet_count=before['packets']['count'],current_packet_count=raw['packets']['count'],new221_count=len(canonical),appended221_count=len(invocation221),other221_packets=other,stop221_classifier='packedGUID_then_XYZ12_sequence4_flag1_exact_length')
            h=raw['run_ledger135']['incoming_history'];strings=[None]*len(self.history.data)
            for j in range(self.history.count):slot=(self.history.head+j)%len(strings);strings[slot]=self.history.strings[slot]
            self.history.check(raw)
            cap,recap,diagnostic=C.reference(dict(id=0,reference_time_bits=now,history=dict(capacity=len(strings),head=self.history.head,count=self.history.count,rows48_hex=h['storage48_hex'],strings=strings)),['mob','elite','boss','object','none'],self.recap_counts)
            state=dict(counters={o:U(bytes.fromhex(raw['raw_game2592_hex']),o)for o in COUNTERS},now_bits=now,damage984_f64_bits=struct.unpack_from('<Q',a,984)[0],class_byte=1,hero='',race_byte=1,region_index=0,left2567=0)
            note=D.notification(state,struct.unpack('<Q',struct.pack('<d',taken))[0],recap,self.labels)
            assert p['terminal_notifications']==[[note['capacity'],note['payload_hex']]]
            self.fatal=dict(frame=raw['frame'],completed_frame=raw['frame']+1,stage_index=raw['stage_index'],now_bits=now,notifications=p['terminal_notifications'],invocation221=invocation221,canonical_stop_packets=canonical,canonical_stop221=stops,other_invocation221=len(invocation221)-len(stops),normal27457_packets=normal,appended_opcode_order=[x['opcode']for x in appended],first_stop_tail_index=first_stop,queued_hits=len(attacks),accepted_hits=len(events),recap_capacity=cap,recap_hex=recap.hex(),recap_diagnostics=diagnostic,summary=p['run_ledger']['counters'],hp_final=0)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);parser.add_argument('--receipt-sha256',required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    run=args.run.resolve();out=args.output.resolve();assert run.parent==(ROOT/'evidence').resolve()and out.is_relative_to((ROOT/'evidence').resolve())and run!=out and not out.is_relative_to(run);out.mkdir();began=time.monotonic()
    reviewers=frozen_reviewers(out);assert M.sha(ROOT/'scripts/review_player_death_recap135.py')==RECAP_SHA
    dependencies={
        'reports/2026-11-02-player-death-recap0135-independent-review.json':'1625cc4628bbb215121e6a5f770bed12f090896c7fcace6b17d9a38b29af6b88',
        'reports/2026-11-02-incoming-callbacks0135-independent-review.json':'6c2274f327c59fa80c122f671b257948caabc15539ab5ea68618b5bd4ce8040b'}
    for n,h in dependencies.items():assert M.sha(ROOT/n)==h
    report=M.load(run/'comparison.json');assert M.sha(run/'comparison.json')==args.receipt_sha256 and report['differences']==0
    sources=report['source_sha256_before'];assert sources==report['source_sha256_after'];source=run/'source-snapshot'
    for n,h in sources.items():assert M.sha(source/n)==h,n
    edges,reachable,inactive=V.active_source_edges(source,sources);production=sorted(n for n in sources if n.startswith('reconstruction/'));assert production==S.frozen_closure(source)
    fixture=M.load(run/'fixtures.json');config=M.load(run/'config.json');runtime=M.load(run/'opening-combat135-cas-runtime.json');manifest=M.load(run/'manifest.json')
    assert config['run_ledger135']and config['app_game_domain']=='typed_partial_inline_fixture_not_naturalApp'and config['clock_scheduler']=='explicit_external_f32_add_G2352_not_original880'
    assert fixture['final_phase2587']==4 and fixture['boundary']=='not_running'and fixture['defeat_notifications']==1 and fixture['physical_player_sources']
    assert M.load(run/'inputs.json')==[{k:fixture[k]for k in('id','input','actions')}]
    for n,k in(('fixtures.json','fixtures_sha256'),('inputs.json','inputs_sha256'),('stage-expectations.jsonl.gz','expectations_sha256'),('results.cas.jsonl.gz','original_results_sha256')):assert M.sha(run/n)==report[k]
    original=M.ORIGINAL.read_bytes();assert M.digest(original)==M.ORIGINAL_SHA;changed=(run/manifest['module_file']).read_bytes();assert M.digest(changed)==manifest['module_sha256']
    a,b=M.sections(original),M.sections(changed);assert[x[0]for x in a]==[x[0]for x in b]and not any(x[0]==8 for x in a)
    assert all(original[x:y]==changed[u:v]for(k,x,_,y),(_,u,_,v)in zip(a,b)if k!=7)
    assert V.OLD.exports(changed)==V.OLD.exports(original)+[['research_opening_combat135_'+r['role'],0,r['index']]for r in manifest['roles']]+[['research_opening_combat135_stack',3,0]]
    identities=function_ids(original,{r['index']for r in manifest['roles']}|{1073,5620,17119,17217,16340,1938,1367,984,1560,69798,27375,914,2862,20660,27457,45845,13814})
    for role in manifest['roles']:assert role['body_sha256']==identities[role['index']]['body_sha256']
    static=static_bindings(original,identities,out);read=S.static_reader(original)
    snapshot=M.SNAPSHOT.read_bytes();assert M.digest(snapshot)==M.SNAPSHOT_SHA==config['snapshot_sha256'];world=M.World(snapshot,M.R)
    codec=source/'scripts/opening_combat135_cas.py';assert M.sha(codec)==CODEC_SHA
    spec=importlib.util.spec_from_file_location('frozen_fatal135_capture_transport',codec);transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport);decoder=transport.CaptureCAS135(run)
    S.check_queue=BASE.check_queue500;S.check_value=known_value;BASE.check_value650=known_value;BASE.BINDER=BASE.IndependentAddressBindings()
    combat=Combat(read,world);combat.labels={}
    for item in M.load(ROOT/'evidence/terminal-transition0135-static-20261101T075941.450411Z/label-evidence.json')['labels']:
        assert read(item['string_pointer'],item['bytes']).decode()==item['value'];combat.labels.setdefault(item['kind'],{})[item['id']]=item['value']
    rune=V.RuneAudit(read);motion=V.MotionAudit(world,read(5456016,152))
    expected_reader=S.JsonlReader(run/'stage-expectations.jsonl.gz',True,1073741824);expected=iter(expected_reader);encoded=V.RawIndexReader(run/'results.cas.jsonl.gz')
    order=[('case_start',None,None,0),('constructor',None,None,0),('opening',None,None,0)];frames=0
    for i,action in enumerate(fixture['actions']):
        if action['kind']in('select','motion'):order.append(('stage',i,action['kind'],frames))
        else:
            assert action['kind']=='controlled_tail_frame';order.append(('clock_control',i,None,frames));order.extend(('stage',i,k,frames)for k in S.STAGES);frames+=1
    order.append(('case_end',None,None,frames));assert frames==report['independent_frames']==921
    counts=Counter();maximum=defaultdict(int);kinds=Counter();stages=0;clock=0;dt=0;previous=None;packets=[];notices=[];last=None;calls=None;locale=None
    artifacts={n:M.sha(run/n)for n in('comparison.json','fixtures.json','inputs.json','config.json','manifest.json',manifest['module_file'],'stage-expectations.jsonl.gz','results.cas.jsonl.gz','opening-combat135-cas-runtime.json','process-terminal.json','owned-process.json','differences.json','stderr.log','blob-index.jsonl','blob-references.jsonl')}
    for line_index,line in enumerate(encoded):
        assert time.monotonic()-began<840,'finite840s evidence audit budget';raw=decoder.decode_line(line);kind,action_index,stage,frame=order[line_index];assert raw['record_kind']==kind and raw['id']==0;kinds[kind]+=1
        action=fixture['actions'][action_index]if action_index is not None else None
        if action_index is not None:assert raw['action_index']==action_index and raw['frame']==frame
        if stage is not None:assert raw['kind']==stage
        if kind=='case_start':
            locale=raw['locale_prestate'];assert locale['effective_index']==0 and locale['once_flag']==3
            guard=raw['empty_research_profile_guard'];P0=config['app_pointer']+3376
            assert guard['pointer']==P0 and guard['ranked_effect_count160']==guard['ranked_effect_flag164']==guard['name_length208']==0 and guard['equipment_ids260']==[0]*19
            for key,off,n in(('ranked_effect_header12_hex',152,12),('name_header12_hex',200,12),('equipment76_hex',260,76)):assert guard[key]==snapshot[P0+off:P0+off+n].hex()
            domain=raw['typed_partial_inline_App_fixture'];assert domain['kind']==config['app_game_domain']and not domain['natural1371_install_executed']and domain['Game']==14549016
            assert domain['before_hex']==snapshot[14549000:14549000+5168].hex()and domain['declared_tag_writes']==[dict(offset=16,bits64='2'),dict(offset=2608,bits64='2')]
            declared=bytearray.fromhex(domain['before_hex'])
            for offset in(16,2608):struct.pack_into('<Q',declared,offset,2)
            assert declared.hex()==raw['app_before_declared_hex'];inp=fixture['input']
            struct.pack_into('<Q',declared,4928,int(inp['app_lcg_seed_u64']));struct.pack_into('<Q',declared,3552,int(inp['object_id_u64']))
            for offset,value in((3720,inp['class_byte']),(3721,inp['race_byte']),(3604,255),(3612,255)):declared[offset]=value
            assert declared.hex()==raw['app_after_declared_hex']
        if kind=='clock_control':
            dt=action['dt_bits'];assert raw['old_bits']==clock and raw['dt_bits']==dt;clock=add(clock,dt);assert raw['new_bits']==clock and not raw['original880_called']and raw['only_external_game_write_offset']==2352
        if kind in('constructor','opening','stage'):
            ownership=raw['ownership'];app=bytes.fromhex(ownership['raw_app5168_hex'])
            assert ownership['App']==14549000 and ownership['G']==14549016 and app[16:2608].hex()==raw['raw_game2592_hex']and int.from_bytes(app[2608:2616],'little')==2
            want=None
            if kind in('opening','stage'):
                item=next(expected);assert item['record_kind']==kind;want=item['expected']
                if kind=='stage':assert item['stage_index']==raw['stage_index']==stages and item['action_index']==action_index and item['kind']==stage
                game=bytes.fromhex(raw['raw_game2592_hex']);raw['projection']['auxiliary_motion']=dict(capacity656=U(game,656),pointer660=U(game,660),count664=U(game,664),storage112=[])
                assert U(game,656)==U(game,664)==0
                raw['projection']['auxiliary_source_counts']={k:U(game,int(k))for k in want['projection']['auxiliary_source_counts']}
            P.snapshot(raw,want,counts,maximum,read)
            for queue,field,prior in(('packets','new_packets',packets),('notifications','new_notifications',notices)):
                current=V.packet_values(raw)if queue=='packets'else V.notifications(raw);delta=raw[field]
                assert current[:len(prior)]==prior and delta['prefix_preserved']and delta['previous_count']==len(prior)and delta['current_count']==len(current)and delta['appended']==current[len(prior):]
                if queue=='packets':packets=current
                else:notices=current
            if kind=='stage':
                assert raw['entry_index']==(968 if stage=='motion'else 1072 if stage=='select'else S.ENTRIES[S.STAGES.index(stage)])and raw['projection']['now_bits']==clock
                combat.observe(previous,raw,dt);rune.observe(previous,raw);stages+=1
            else:combat.observe(previous,raw,dt)
            motion.observe(previous,raw,want,action);previous=raw;last=raw
        if kind=='case_end':
            calls=[x for x in raw['calls']if x['role']!='original_allocator'];assert raw['boundary']is None and raw['stage_count']==stages and raw['host_calls']==[]and all(x['returned']and x['stack_after']==1048576 for x in calls)
            assert raw['locale_writes']==0 and raw['locale_after']==locale and len(calls)==stages+2
        if(line_index+1)%500==0:
            save(out/'progress.json',dict(records=line_index+1,stages=stages,seconds=time.monotonic()-began));print(json.dumps(dict(records=line_index+1,stages=stages)),flush=True)
    assert next(expected,None)is None and stages==report['compared_stages']and len(order)==decoder.record_index
    cas=decoder.finish(runtime['capture_cas']);assert cas==report['capture_cas_verification']and encoded.bytes==runtime['uncompressed_output_bytes']and encoded.digest.hexdigest()==runtime['uncompressed_sha256']
    assert expected_reader.bytes==fixture['expected_uncompressed_bytes']==report['expected_uncompressed_bytes']and expected_reader.file_digest.hexdigest()==report['expectations_sha256']
    assert combat.fatal is not None and [x['stage']for x in combat.tail]==['collect','claims','spawn','special','terminal']and all(x['frame']==920 for x in combat.tail)
    assert len(rune.events)==1 and len(motion.events)==44 and combat.counts['accepted_incoming_history']==combat.history.counts['appends']
    known_value(fixture['final_summary'],last['projection']['run_ledger'],('projection','run_ledger'),counts)
    assert fixture['fatal_stop_packets']==len(combat.fatal['canonical_stop_packets'])
    terminal=M.load(run/'process-terminal.json');assert terminal['exit_code']==0 and not terminal['deadline_exceeded']and M.missing(terminal['pid'])and M.missing(terminal['pgid'],True)
    for n,h in sources.items():assert M.sha(source/n)==h
    for n,h in artifacts.items():assert M.sha(run/n)==h
    for n,h in reviewers.items():assert M.sha(ROOT/n)==h
    result=dict(status='passed-within-declared-domain',author_receipt_sha256=args.receipt_sha256,run=str(run.relative_to(ROOT)),new_original_calls=0,production_imports=0,production_executions=0,original_function_identities=identities,static_bindings=static,source_count=len(sources),production_source_count=len(production),source_sha256=sources,source_edges=edges,reachable=reachable,inactive_edges=inactive,reviewer_source_sha256=reviewers,artifacts=artifacts,records=dict(kinds),completed_frames=frames,compared_stages=stages,comparison_counts=dict(counts),combat_counts=dict(combat.counts),history_counts=dict(combat.history.counts),recap_counts=dict(combat.recap_counts),fatal=combat.fatal,phase4_tail=combat.tail,incoming_events=combat.events,rune_events=rune.events,motion_events=motion.events,expected_stream=expected_reader.receipt(),encoded_stream=encoded.receipt(),CAS_finish=cas,process=terminal,seconds=time.monotonic()-began,limitations=['Fixed135 ordinary humanwarrior empty research selected profile only; typed partial App snapshot and externally scheduled14 stages,not natural1371/full880/native client or latest138.','World queries independently read from pinned original snapshot; no freshworld/cache/Rc producer or primary-nearest runtime credit.','Full declared projection and storage bytes are compared; None remains explicit unknown,including physical queue allocation/header proof pending in the model.','Ordered incoming/history/counters are rebuilt from original pre-AI states; ordinary AI movement/pathfinding and full skills are checked by independently expected-first differential,not independently reimplemented here.','Recap1367 uses the different-author reviewed pure reference after independent validation of all consumed ring cells/metadata; raw pointer/padding/backing observations are not fed into production.','Canonical221 stop coordinates/payload grammar/sequence and real appended-tail origin are checked; total stop eligibility for newly planned routes is not a new independent whole921 implementation.','No complete game flow/victory/all-module reconstruction claim; one fatal firstRune route and its actual five phase4 tail calls.'])
    result['different_author_dependencies']=dependencies
    result['dependency_original_cases_added_to_this_review']=0
    save(out/'review.json',result);print(json.dumps(dict(path=str(out/'review.json'),sha256=M.sha(out/'review.json'),frames=frames,stages=stages,seconds=result['seconds'])),flush=True)

if __name__=='__main__':main()
