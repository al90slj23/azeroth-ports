#!/usr/bin/env python3
"""Read-only moving460 CAS, full968 and natural Restoration Rune review.

Only frozen evidence and reviewer routines execute. The frozen CAS transport
is an explicit dependency; production models/checkers and original WASM do not.
"""
from pathlib import Path
from collections import Counter,defaultdict
import argparse,ast,hashlib,importlib.util,json,math,re,struct,sys,time,zlib
sys.dont_write_bytecode=True
import review_opening_player_sources135 as P
import review_player_motion135 as M
import review_resource_consumer135 as R
ROOT=M.ROOT;S=P.S;BASE=P.BASE;OLD=P.old
RUN=ROOT/'evidence/opening-combat0135-oracle-20261101T232156.684647Z'
COMPARISON='521db52b9d97637212460083a7ea88b9038d63871536d6635edc21645e0bd622'
TARGET=17370383913897164969
ZERO=(416,440,448,456,464,1744,1764,2496,2500)
WORDS=(416,420,424,428,432,436,440,444,448,452,456,460,464,1428,1744,1748,1752,1756,1760,1764,1768,1772,1776,1780,2496,2500)

def frozen_reviewers(out):
    todo=[Path(__file__).resolve()];seen={}
    while todo:
        path=todo.pop();name=str(path.relative_to(ROOT))
        if name in seen:continue
        seen[name]=M.sha(path);source=path.read_text()
        for node in ast.walk(ast.parse(source)):
            modules=[a.name for a in node.names]if isinstance(node,ast.Import)else[node.module]if isinstance(node,ast.ImportFrom)and node.module else[]
            for module in modules:
                child=ROOT/'scripts'/(module.replace('.','/')+'.py')
                if child.is_file():assert module.startswith('review_'),module;todo.append(child)
        target=out/'reviewer-source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
    return seen

def active_source_edges(source,names):
    """All production imports; module/top-level and called script functions.

    Optional main functions in imported checker helpers are not executed.
    Their absent static edges are reported, never retroactively hashed.
    """
    names=set(names);production={n for n in names if n.startswith('reconstruction/')}
    edges=set(M.source_edges(source,production));loaded={};pending=[('scripts/check_opening_combat135.py',None),('scripts/check_opening_combat135.py','main')];seen=set();inactive=[]
    def resolve(module):
        parts=Path(*module.split('.'));found=[]
        for folder in('scripts','reconstruction'):
            for p in(ROOT/folder/parts.with_suffix('.py'),ROOT/folder/parts/'__init__.py'):
                if p.is_file():found.append(str(p.relative_to(ROOT)));break
        return found
    def imports(node):
        if isinstance(node,ast.Import):return[(a.asname or a.name.split('.')[0],a.name,None)for a in node.names]
        if isinstance(node,ast.ImportFrom):
            assert node.level==0
            return[(a.asname or a.name,node.module,a.name)for a in node.names]
        return[]
    def walk(statements):
        for node in statements:
            yield node
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):continue
            yield from walk(list(ast.iter_child_nodes(node)))
    while pending:
        name,fn=pending.pop()
        if(name,fn)in seen:continue
        seen.add((name,fn));assert name in names,(name,fn)
        if not name.startswith('scripts/'):continue
        if name not in loaded:
            tree=ast.parse((source/name).read_text());defs={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
            aliases={}
            for node in walk(tree.body):
                for alias,module,member in imports(node):aliases[alias]=(module,member)
            loaded[name]=(tree,defs,aliases)
        tree,defs,aliases=loaded[name]
        body=tree.body if fn is None else defs[fn].body if fn in defs else[]
        if fn is None:
            body=[n for n in body if not isinstance(n,ast.If)or not(isinstance(n.test,ast.Compare)and isinstance(n.test.left,ast.Name)and n.test.left.id=='__name__')]
        nodes=list(walk(body))
        for node in nodes:
            for alias,module,member in imports(node):
                for target in resolve(module):
                    assert target in names,(name,target,node.lineno);edges.add((name,target));pending.append((target,None))
                if member:
                    for target in resolve(module+'.'+member):
                        assert target in names,(name,target,node.lineno);edges.add((name,target));pending.append((target,None))
            if isinstance(node,ast.Call):
                if isinstance(node.func,ast.Name):
                    call=node.func.id
                    if call in defs:pending.append((name,call))
                    elif call in aliases:
                        module,member=aliases[call]
                        for target in resolve(module):pending.append((target,member))
                elif isinstance(node.func,ast.Attribute)and isinstance(node.func.value,ast.Name)and node.func.value.id in aliases:
                    module,member=aliases[node.func.value.id]
                    if member is None:
                        for target in resolve(module):pending.append((target,node.func.attr))
    # The runtime reader/Node runner are selected by explicit names in main,
    # not a Python import. Their files are already frozen by the checker.
    for name in names:
        if name.endswith('.mjs'):
            for relative in re.findall(r"from\s+['\"](\.[^'\"]+)['\"]",(source/name).read_text()):
                target=str((ROOT/Path(name).parent/relative).resolve().relative_to(ROOT))
                assert target in names,(name,target);edges.add((name,target))
        if not name.startswith('scripts/')or not name.endswith('.py'):continue
        tree=ast.parse((source/name).read_text())
        for node in ast.walk(tree):
            for alias,module,member in imports(node):
                for target in resolve(module):
                    if target not in names:inactive.append(dict(source=name,line=node.lineno,target=target,active_import_verified_absent=True))
    assert('scripts/check_opening_handoff135.py','main')not in seen
    inactive=[dict(zip(('source','line','target'),row),active_import_verified_absent=True)
        for row in sorted({(r['source'],r['line'],r['target'])for r in inactive})]
    assert inactive==[dict(source='scripts/check_opening_handoff135.py',line=243,target='scripts/check_opening135.py',active_import_verified_absent=True)]
    return sorted(edges),sorted(seen,key=lambda row:(row[0],row[1]or'')),inactive

def packet_values(raw):return[dict(opcode=p['opcode'],payload_hex=p['payload_hex'])for p in raw['packets']['active']]
def notifications(raw):return[p['payload_hex']for p in raw['notifications']['active']]
class RawIndexReader:
    def __init__(self,path):self.path=path;self.bytes=0;self.digest=hashlib.sha256();self.records=0;self.maximum=0
    def __iter__(self):
        encoded=self.path.read_bytes();assert len(encoded)<=268435456;self.file_sha256=M.digest(encoded);self.file_bytes=len(encoded)
        inflater=zlib.decompressobj(31);raw=inflater.decompress(encoded,33554433)
        assert len(raw)<=33554432 and inflater.eof and not inflater.unused_data and not inflater.unconsumed_tail
        self.bytes=len(raw);self.digest.update(raw);assert raw.endswith(b'\n')
        for line in raw.splitlines(keepends=True):
            assert len(line)<=2097152 and line.endswith(b'\n');self.maximum=max(self.maximum,len(line));self.records+=1;yield line
    def receipt(self):return dict(file_bytes=self.file_bytes,file_sha256=self.file_sha256,uncompressed_bytes=self.bytes,uncompressed_sha256=self.digest.hexdigest(),records=self.records,maximum_record_bytes=self.maximum,single_member=True)
def pickup_guid(row):return int.from_bytes(row[16:24],'little')
def distance(row,xyz):
    dx,dy=M.sub(M.u(row,40),xyz[0]),M.sub(M.u(row,44),xyz[1])
    return M.B(math.sqrt(M.F(M.add(M.mul(dx,dx),M.mul(dy,dy)))))

class RuneAudit:
    def __init__(self,read):
        self.events=[];self.counts=Counter();self.next_id=1;self.read=read;self.birth=None
        ptr=M.u(read(5505544+4*4,4));length=M.u(read(5505504+4*4,4));self.name=read(ptr,length).decode()
        assert self.name=='Restoration Rune'and read(14340336,4)==b'\x01\0\0\0'
    def observe(self,before,raw):
        if raw['record_kind']!='stage':return
        p,old=raw['projection'],before['projection'];stage=raw['kind']
        prior=before['vectors']['pickups'];current=raw['vectors']['pickups']
        if stage=='spawn'and self.birth is None:
            newcomers=[bytes.fromhex(x)for x in current['storage'][prior['count']:current['count']]]
            values=[row for row in newcomers if M.u(row,8)in(3,4,5)]
            if values:
                assert len(values)==1 and M.u(values[0],8)==5 and pickup_guid(values[0])==TARGET
                self.birth=dict(frame=raw['frame'],stage_index=raw['stage_index'],row56_hex=values[0].hex(),guid=str(TARGET),kind=5)
        if stage!='collect':return
        self.counts['collect_stages']+=1
        back=[bytearray.fromhex(x)for x in prior['storage']];count=prior['count'];now=p['now_bits'];xyz=old['player_xyz'];radius=old['derived_bits']['1560'];attracted=[]
        for index,row in enumerate(back[:count]):
            if M.u(row,8)or M.u(row):continue
            d=distance(row,xyz);aged=M.F(M.sub(now,M.u(row,52)))>6
            if not aged and M.F(d)>M.F(radius):continue
            delay=M.div(d,M.B(32 if aged else 24));delay=delay if M.F(delay)>M.F(0x3df5c28f)else 0x3df5c28f
            M.put(row,0,1);M.put(row,4,M.add(now,delay));attracted.append(index)
        selected=[]
        for index,row in enumerate(back[:count]):
            kind,marker=M.u(row,8),M.u(row);d=distance(row,xyz)
            eligible=bool(marker and M.F(M.u(row,4))<=M.F(now))if kind==0 else(M.F(d)<=M.F(radius)or marker==1 and M.F(M.u(row,4))<=M.F(now))if kind==1 else M.F(d)<=3 if kind in(3,4,5)else False
            if eligible:selected.append(index)
        consumed=[]
        for index in reversed(selected):
            row=back[index][:];kind=M.u(row,8);owner=pickup_guid(row);consumed.append((index,kind,owner,row))
            for j in range(index,count-1):back[j]=back[j+1][:]
            count-=1;self.counts['consumed_kind'+str(kind)]+=1
        assert prior['capacity']==current['capacity']and current['count']==count
        assert current['storage']==[bytes(x).hex()for x in back],('Physical56 attraction/reverse-memmove',raw['frame'])
        delta=raw['new_packets']['appended'];destroy=[x['payload_hex']for x in delta if x['opcode']==170]
        assert destroy==[struct.pack('<Q',x[2]).hex()for x in consumed]
        self.counts['full56_backing_bytes_recomputed']+=len(back)*56;self.counts['attracted_rows']+=len(attracted)
        runes=[x for x in consumed if x[1]in(3,4,5)]
        for index,kind,owner,row in runes:
            assert kind==5 and owner==TARGET and self.birth is not None
            assert old['progression']['level']==p['progression']['level']and old['derived_bits']==p['derived_bits']
            before_game=bytes.fromhex(before['raw_game2592_hex']);after_game=bytes.fromhex(raw['raw_game2592_hex'])
            maximum=old['derived_bits']['1536'];request=M.mul(maximum,M.B(.5));gate=before_game[387]
            request=M.mul(request,M.B(.5)if gate>4 else M.B(1));summed=M.add(old['current_hp_bits'],request)
            hp=summed if M.F(summed)<M.F(maximum)else maximum
            assert p['current_hp_bits']==M.u(after_game,1440)==hp
            assert p['player_fields']['22']==math.ceil(M.F(hp))and p['player_fields']['28']==math.ceil(M.F(maximum))
            assert before['vectors']['live32']==raw['vectors']['live32']and before['vectors']['aura48']==raw['vectors']['aura48']
            source=int(p['source_id']);spell=R.spellgo(source,23493)
            notice=dict(type='banner',id=self.next_id,kind='rune',text=self.name+'!',name=self.name,boss=False)
            notice_hex=json.dumps(notice,ensure_ascii=False,separators=(',',':')).encode().hex()
            text=('AZSBANNER\tid='+str(self.next_id)+';kind=rune;boss=0;name='+self.name+';text='+self.name+'!').encode()
            banner=(struct.pack('<BIQI',6,0xffffffff,source,len(text)+1)+text+b'\0\0').hex()
            first=next(i for i,x in enumerate(delta)if x==dict(opcode=170,payload_hex=struct.pack('<Q',owner).hex()))
            assert delta[first+1:first+3]==[dict(opcode=306,payload_hex=spell),dict(opcode=150,payload_hex=banner)]
            assert raw['new_notifications']['appended']==[notice_hex]
            self.events.append(dict(frame=raw['frame'],completed_frame=raw['frame']+1,stage_index=raw['stage_index'],guid=str(owner),kind=kind,index=index,
                eligibility_distance_bits=distance(row,xyz),player_xyz=xyz,row56_hex=row.hex(),reverse_consumption_order=[[i,k,str(g)]for i,k,g,r in consumed],
                hp_before=old['current_hp_bits'],maximum_hp_bits=maximum,heal_gate387=gate,request_bits=request,hp_after=hp,
                spell306_hex=spell,banner150_hex=banner,JSON_hex=notice_hex,notification_id=self.next_id,live_and_Aura_unchanged=True))
            self.next_id=(self.next_id+1)&0xffffffff
        if not runes:assert not raw['new_notifications']['appended']or all(json.loads(bytes.fromhex(x)).get('kind')!='rune'for x in raw['new_notifications']['appended'])

class PlayerAudit(P.PhysicalPlayerAudit):
    """Reuse independently reviewed owner operations; add real kind5 path."""
    def __init__(self,read,rune):super().__init__(read);self.rune=rune
    def observe(self,before,raw,want,frame,now):
        kind,phase=raw['record_kind'],raw.get('kind')
        if kind=='opening':assert not self.rows and not self.aura
        elif kind=='stage'and phase=='player':
            if any(M.F(now)>=M.F(P.u(row,24))for row in self.rows[:self.count]):
                self.retain(lambda row:M.F(now)<M.F(P.u(row,24)));self.rebuild_aura(now);self.counts['dirty_prefix_stages']+=1
            self.cast_events(before,raw,want,frame,now)
        elif kind=='stage'and phase=='select'and raw['projection']['phase2587']==1:
            self.retain(lambda row:P.u(row,20)!=1020)
            self.append(((0,0),(4,0),(8,12),(20,1020),(24,M.add(now,M.B(1))),(28,0)))
            self.rebuild_aura(now);self.counts['selection1020_partial_appends']+=1
        if want is None:return
        assert want['vectors']['live32']==dict(capacity=len(self.rows),count=self.count,storage=self.rows)
        assert want['vectors']['aura48']==dict(capacity=len(self.aura),count=len(self.aura),storage=self.aura)
        assert want['projection']['aura_initialized2569']==self.initialized
        for key,value in self.aura_fields.items():assert want['projection']['player_fields'][key]==raw['projection']['player_fields'][key]==value
        declarations=[dict(slot=i,source=list(origin))for i,origin in enumerate(self.origins)if origin is not None]
        assert want.get('unresolved_live_auxiliary_origins',[])==declarations
        for i,origin in enumerate(self.origins):
            if origin is None:continue
            assert self.rows[i][16:20]==[None]*4 and origin in self.words
            assert P.word(bytes.fromhex(raw['vectors']['live32']['storage'][i]),16)==self.words[origin]
            self.counts['opaque_word_copy_observations']+=1
        assert want['projection']['notification_next_id14340336']==raw['projection']['notification_next_id14340336']==self.rune.next_id
        self.counts['physical_owner_snapshots']+=1

class MotionAudit:
    def __init__(self,world,zone):
        self.world,self.zone=world,zone;self.owner=[None]*2592;self.events=[];self.counts=Counter();self.target=None;self.stopped=False
        for o in ZERO:M.put(self.owner,o,0)
        M.put(self.owner,1428,M.u(zone,116))
    def known(self):return{str(o):M.u(self.owner,o)for o in WORDS if all(x is not None for x in self.owner[o:o+4])}
    def observe(self,before,raw,want,action):
        if raw.get('kind')=='motion':
            assert raw['opcode']==action['opcode']and raw['input_payload24_hex']==action['payload24_hex']and raw['entry_index']==968
            original=bytes.fromhex(before['raw_game2592_hex']);actual=bytes.fromhex(raw['raw_game2592_hex'])
            flags,ms,x,y,z,facing=struct.unpack('<6I',bytes.fromhex(action['payload24_hex']))
            assert all((v&0x7fffffff)<=0x7f7fffff for v in(x,y,z,facing))and facing==0
            oldxyz=before['projection']['player_xyz'];now=before['projection']['now_bits'];assert ms==int(M.F(now)*1000)
            picks=[bytes.fromhex(x)for x in before['vectors']['pickups']['storage'][:before['vectors']['pickups']['count']]]
            if self.target is None:
                row=next(r for r in picks if M.u(r,8)in(3,4,5));assert pickup_guid(row)==TARGET and raw['frame']==401
                self.target=row;assert action['opcode']==181
            present=any(pickup_guid(row)==TARGET for row in picks)
            if present:
                dx,dy=M.sub(M.u(self.target,40),oldxyz[0]),M.sub(M.u(self.target,44),oldxyz[1])
                length=M.B(math.sqrt(M.F(M.add(M.mul(dx,dx),M.mul(dy,dy)))))
                travel=M.mul(M.u(original,1648),M.B(.1));ratio=M.div(travel,length)if M.F(length)>M.F(travel)else M.B(1)
                wanted_xy=(M.add(oldxyz[0],M.mul(dx,ratio)),M.add(oldxyz[1],M.mul(dy,ratio)))
                assert(x,y)==wanted_xy and z==self.world.height(x,y)and flags==1
                assert action['opcode']==(181 if not self.events else 238)
            else:
                assert not self.stopped and action['opcode']==183 and flags==0 and(x,y,z)==tuple(oldxyz)
                assert raw['frame']==444;self.stopped=True
            seed=bytearray(original);clock=M.div(M.B(float(ms)),M.B(1000))
            for o,v in((2496,flags),(440,1),(444,clock)):M.put(seed,o,v)
            cells,ret,packets,writes,branch=M.reference(seed,(x,y,z),facing,self.world,self.zone,self.counts)
            M.put(cells,440,0);assert bytes(cells)==actual and ret==1 and not packets and branch=='unchanged-input'
            own=self.owner[:]
            for o,v in((2352,now),(1644,M.u(original,1644)),(2528,M.u(original,2528)),(2496,flags),(440,1),(444,clock)):
                M.put(own,o,v)
            own[1336:1344]=original[1336:1344]
            for o in(1416,1420,1424):M.put(own,o,M.u(original,o))
            own[2583]=original[2583];own[2587]=original[2587]
            reduced,rr,rp,rw,rb=M.reference(own,(x,y,z),facing,self.world,self.zone,Counter());M.put(reduced,440,0)
            assert(rr,rp,rw,rb)==(ret,packets,writes,branch)
            self.owner=[None]*2592
            for o in WORDS:self.owner[o:o+4]=reduced[o:o+4]
            app=bytearray.fromhex(before['ownership']['raw_app5168_hex']);app[16:2608]=actual
            assert app.hex()==raw['ownership']['raw_app5168_hex']
            assert before['vectors']==raw['vectors']and before['packets']==raw['packets']and before['notifications']==raw['notifications']
            assert before['ownership']['raw_world_rc124_hex']==raw['ownership']['raw_world_rc124_hex']
            self.events.append(dict(frame=raw['frame'],stage_index=raw['stage_index'],opcode=action['opcode'],flags=flags,milliseconds=ms,clock444_bits=clock,xyz_bits=[x,y,z],normal_terrain=True,fullGame2592_equal=True,fullApp5168_equal=True))
            self.counts['strict_motion_Game_bytes']+=2592;self.counts['strict_motion_App_bytes']+=5168
        if want is not None:
            assert want['projection']['motion_scalar_words']==self.known()
            game=bytes.fromhex(raw['raw_game2592_hex'])
            for key,value in self.known().items():assert M.u(game,int(key))==value
            self.counts['canonical_owner_snapshots']+=1

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();out=args.output.resolve();assert out.is_relative_to((ROOT/'evidence').resolve());out.mkdir();began=time.monotonic()
    reviewers=frozen_reviewers(out);report=M.load(RUN/'comparison.json');assert M.sha(RUN/'comparison.json')==COMPARISON
    assert(report['status'],report['differences'],report['independent_frames'],report['independent_selections'],report['compared_stages'])==('matched_requested_budget',0,460,4,6488)
    source=RUN/'source-snapshot';sources=report['source_sha256_before'];assert len(sources)==117 and sources==report['source_sha256_after']
    for n,h in sources.items():assert M.sha(source/n)==M.sha(ROOT/n)==h,n
    edges,reachable,inactive=active_source_edges(source,sources);production=sorted(n for n in sources if n.startswith('reconstruction/'));assert len(production)==100 and production==S.frozen_closure(source)
    for name in production:
        for node in ast.walk(ast.parse((source/name).read_text())):
            if isinstance(node,ast.Call):
                f=node.func;called=f.id if isinstance(f,ast.Name)else f.attr if isinstance(f,ast.Attribute)else''
                assert called not in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__'),(name,called)
    fixture=M.load(RUN/'fixtures.json');config=M.load(RUN/'config.json');runtime=M.load(RUN/'opening-combat135-cas-runtime.json');manifest=M.load(RUN/'manifest.json')
    assert fixture['physical_player_sources']and fixture['motion_actions']==44 and fixture['explicit_App_notification_counter']==1
    assert len(fixture['actions'])==508 and M.load(RUN/'inputs.json')==[{k:fixture[k]for k in('id','input','actions')}]
    assert config['app_game_domain']=='typed_partial_inline_fixture_not_naturalApp'and config['clock_scheduler']=='explicit_external_f32_add_G2352_not_original880'
    assert config['snapshot_sha256']==M.SNAPSHOT_SHA and config['app_pointer']==14549000 and config['world_pointer']==M.R
    for name,key in(('fixtures.json','fixtures_sha256'),('inputs.json','inputs_sha256'),('stage-expectations.jsonl.gz','expectations_sha256'),('results.cas.jsonl.gz','original_results_sha256')):assert M.sha(RUN/name)==report[key]
    original=M.ORIGINAL.read_bytes();assert M.digest(original)==M.ORIGINAL_SHA
    changed=(RUN/manifest['module_file']).read_bytes();assert M.digest(changed)==manifest['module_sha256']
    a,b=M.sections(original),M.sections(changed);assert[x[0]for x in a]==[x[0]for x in b]and not any(x[0]==8 for x in a)
    assert all(original[x:y]==changed[u:v]for(k,x,_,y),(_,u,_,v)in zip(a,b)if k!=7)
    assert len(manifest['roles'])==18
    assert OLD.exports(changed)==OLD.exports(original)+[['research_opening_combat135_'+r['role'],0,r['index']]for r in manifest['roles']]+[['research_opening_combat135_stack',3,0]]
    read=S.static_reader(original);zone=read(5456016,152);del original,changed
    snapshot=M.SNAPSHOT.read_bytes();assert M.digest(snapshot)==M.SNAPSHOT_SHA;world=M.World(snapshot,M.R)
    decoder_path=source/'scripts/opening_combat135_cas.py';assert M.sha(decoder_path)=='728b3ae0576d372b9b7467c484022ae3487e772b9a09c0172bfbcdcf29c1479f'
    spec=importlib.util.spec_from_file_location('declared_frozen_moving_CAS_transport',decoder_path);transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport);decoder=transport.CaptureCAS135(RUN)
    S.check_queue=BASE.check_queue500;S.check_value=BASE.check_value650
    BASE.BINDER=BASE.IndependentAddressBindings()
    rune=RuneAudit(read);player=PlayerAudit(read,rune);motion=MotionAudit(world,zone)
    artifact_names=('comparison.json','fixtures.json','inputs.json','config.json','manifest.json',manifest['module_file'],'stage-expectations.jsonl.gz','results.cas.jsonl.gz','opening-combat135-cas-runtime.json','process-terminal.json','owned-process.json','differences.json','stderr.log','blob-index.jsonl','blob-references.jsonl')
    artifacts={n:M.sha(RUN/n)for n in artifact_names};assert report['model_expected_before_original']and report['original_input_contains_no_expectations']
    checker=(source/'scripts/check_opening_combat135.py').read_text();assert checker.index('row=corpus(')<checker.index('child=subprocess.Popen(')
    expected_reader=S.JsonlReader(RUN/'stage-expectations.jsonl.gz',True,1073741824);expected=iter(expected_reader)
    encoded_reader=RawIndexReader(RUN/'results.cas.jsonl.gz')
    order=[('case_start',None,None,0),('constructor',None,None,0),('opening',None,None,0)];frames=0
    for index,action in enumerate(fixture['actions']):
        if action['kind']in('select','motion'):order.append(('stage',index,action['kind'],frames))
        else:
            assert action['kind']=='controlled_tail_frame';order.append(('clock_control',index,None,frames));order.extend(('stage',index,k,frames)for k in S.STAGES);frames+=1
    order.append(('case_end',None,None,frames));assert frames==460 and len(order)==6952
    # Preserve exact index bytes as well as each reconstructed logical SHA.
    counts=Counter();maximum=defaultdict(int);records=Counter();previous=None;clock=0;stages=0;selections=[];terminal_frames=[];locale=None;last=None;known_shapes=Counter()
    previous_packets=[];previous_notices=[]
    for line_index,line in enumerate(encoded_reader):
        assert time.monotonic()-began<240,'Independent moving review240s budget'
        raw=decoder.decode_line(line)
        kind,action_index,stage,frame=order[line_index];records[kind]+=1;assert raw['record_kind']==kind and raw['id']==0
        if action_index is not None:assert raw['action_index']==action_index and raw['frame']==frame
        if stage is not None:assert raw['kind']==stage
        action=fixture['actions'][action_index]if action_index is not None else None
        if kind=='case_start':
            locale=raw['locale_prestate'];assert locale['effective_index']==0 and locale['once_flag']==3
            domain=raw['typed_partial_inline_App_fixture'];assert domain['kind']==config['app_game_domain']and not domain['natural1371_install_executed']and domain['Game']==14549016
            assert domain['before_hex']==snapshot[14549000:14549000+5168].hex()
            assert domain['declared_tag_writes']==[dict(offset=16,bits64='2'),dict(offset=2608,bits64='2')]
            pre=bytearray.fromhex(domain['before_hex'])
            for offset in(16,2608):struct.pack_into('<Q',pre,offset,2)
            assert pre.hex()==raw['app_before_declared_hex']
            inp=fixture['input'];struct.pack_into('<Q',pre,4928,int(inp['app_lcg_seed_u64']));struct.pack_into('<Q',pre,3552,int(inp['object_id_u64']))
            for offset,value in((3720,inp['class_byte']),(3721,inp['race_byte']),(3604,255),(3612,255)):pre[offset]=value
            assert pre.hex()==raw['app_after_declared_hex']
        if kind=='clock_control':
            assert raw['old_bits']==clock and raw['dt_bits']==action['dt_bits'];clock=M.add(clock,action['dt_bits'])
            assert raw['new_bits']==clock and not raw['original880_called']and raw['only_external_game_write_offset']==2352
        if kind in('constructor','opening','stage'):
            own=raw['ownership'];assert own['App']==14549000 and own['G']==14549016 and own['raw_app5168_hex'][32:32+5184]==raw['raw_game2592_hex']
            appbytes=bytes.fromhex(own['raw_app5168_hex']);assert int.from_bytes(appbytes[2608:2616],'little')==2
            want=None
            if kind in('opening','stage'):
                item=next(expected);assert item['record_kind']==kind;want=item['expected']
            if kind=='stage':
                assert item['stage_index']==raw['stage_index']==stages and item['action_index']==action_index and item['kind']==stage
                assert raw['projection']['now_bits']==clock;raw['_dt_bits']=action.get('dt_bits',0)
                assert raw['entry_index']==(968 if stage=='motion'else 1072 if stage=='select'else S.ENTRIES[S.STAGES.index(stage)])
                counts['stage_identity_leaves']+=2
                scratch=raw['caller_scratch48_observation'];assert scratch['kind']=='read_only_SP_minus496_not_model_input'and scratch['address']==1048080 and scratch['root_stack']==1048576
            P.snapshot(raw,want,counts,maximum,read)
            for queue,field,prior in(('packets','new_packets',previous_packets),('notifications','new_notifications',previous_notices)):
                current=packet_values(raw)if queue=='packets'else notifications(raw);delta=raw[field]
                assert current[:len(prior)]==prior and delta['prefix_preserved']and delta['previous_count']==len(prior)and delta['current_count']==len(current)and delta['appended']==current[len(prior):]
                if queue=='packets':previous_packets=current
                else:previous_notices=current
            if kind=='stage':rune.observe(previous,raw)
            player.observe(previous,raw,want,frame,clock);motion.observe(previous,raw,want,action)
            if stage=='select':
                selected=action['index'];assert previous['projection']['phase2587']==2 and raw['input_index']==selected
                selections.append(dict(frame=frame,stage_index=stages,index=selected,card=previous['projection']['candidates'][selected],phase_after=raw['projection']['phase2587']))
            if stage=='terminal':terminal_frames.append(dict(frame=frame,hp_bits=raw['projection']['current_hp_bits'],xyz_bits=raw['projection']['player_xyz'],notification_next_id=raw['projection']['notification_next_id14340336'],target_still_present=any(pickup_guid(bytes.fromhex(x))==TARGET for x in raw['vectors']['pickups']['storage'][:raw['vectors']['pickups']['count']])))
            if kind=='stage':stages+=1
            previous=raw;last=raw
        if kind=='case_end':
            assert raw['boundary']is None and raw['host_calls']==[]and raw['stage_count']==6488 and raw['locale_writes']==0 and raw['locale_after']==locale
            calls=[x for x in raw['calls']if x['role']!='original_allocator'];assert len(calls)==6490 and all(x['returned']and x['stack_after']==1048576 for x in calls)
            known_shapes.update(x['role']for x in calls)
        if(line_index+1)%250==0:
            progress=dict(records=line_index+1,stages=stages,seconds=time.monotonic()-began);M.save(out/'progress.json',progress);print(json.dumps(progress),flush=True)
    assert stages==6488 and len(selections)==4 and next(expected,None)is None and decoder.record_index==6952
    cas=decoder.finish(runtime['capture_cas']);assert cas==report['capture_cas_verification']
    assert encoded_reader.bytes==runtime['uncompressed_output_bytes']and encoded_reader.digest.hexdigest()==runtime['uncompressed_sha256']
    assert expected_reader.bytes==fixture['expected_uncompressed_bytes']==report['expected_uncompressed_bytes']and expected_reader.file_digest.hexdigest()==report['expectations_sha256']
    assert len(motion.events)==44 and Counter(x['opcode']for x in motion.events)==Counter({181:1,238:42,183:1})and motion.stopped
    assert len(rune.events)==1 and rune.events[0]['frame']==443 and rune.birth['frame']==400
    later=[x for x in terminal_frames if x['frame']>rune.events[0]['frame']];assert len(later)==16 and all(not x['target_still_present']and x['notification_next_id']==2 for x in later)
    known=sum(counts[k]for k in('strict_record_bytes','projection_leaves','vector_shape_fields','stage_identity_leaves'))
    assert known==report['comparison']['compared_leaves']and counts['unknown_cells']==report['comparison']['declared_unknown_cells']and counts['unwritten_pickup_arrival_words']==report['comparison']['unwritten_pickup_arrivals']
    assert BASE.BINDER.report()==report['pickup_address_proof']
    assert player.counts['opaque_word_copy_observations']==report['live_auxiliary_source_observations']['observations']and len(player.words)==report['live_auxiliary_source_observations']['distinct_sources']
    assert runtime==report['runtime']and runtime['original_entry_calls']==6490 and runtime['completed_stages']==6488 and runtime['completed_controlled_tail_frames']==460
    assert runtime['denied_imports']==878 and runtime['host_imports_throw']and runtime['peak_memory_bytes']==166395904 and runtime['memory_page_cap']==4096 and runtime['js_heap_cap_mib']==512
    assert not any(runtime[k]for k in('full880_called','network_used','user_saves_accessed','world_rc_forged','constructor_phase_overwritten','preallocated_zero128_storage','locale_once_injected'))
    original_process=M.load(RUN/'process-terminal.json');owned=M.load(RUN/'owned-process.json')
    assert original_process['exit_code']==0 and not original_process['deadline_exceeded']and original_process['seconds']<original_process['deadline_seconds']==owned['deadline_seconds']==180
    assert M.missing(original_process['pid'])is True and M.missing(original_process['pgid'],True)is True
    assert M.load(RUN/'differences.json')==[]and(RUN/'stderr.log').stat().st_size==0
    assert all(M.sha(ROOT/n)==M.sha(source/n)==h for n,h in sources.items())and all(M.sha(ROOT/n)==h for n,h in reviewers.items())and all(M.sha(RUN/n)==h for n,h in artifacts.items())
    result=dict(status='passed_scoped_read_only_moving460_rune_review',version='0.135.1',actual_build='90898d5e3',comparison=str(RUN/'comparison.json'),comparison_sha256=COMPARISON,
        frames=460,selections=selections,motion_actions=44,stages=6488,original_entry_calls=6490,roles=dict(known_shapes),source_files=117,production_files=100,source_hashes=sources,source_import_edges=edges,reachable_script_scopes=reachable,inactive_optional_source_edges=inactive,
        reviewer_sources=reviewers,artifacts_sha256=artifacts,stream_records=dict(records),capture_cas_verification=cas,encoded_stream=encoded_reader.receipt(),expected_stream=expected_reader.receipt(),
        comparison_counts=dict(counts),reconciled_known_leaves=known,observed_vector_max=dict(maximum),motion_counts=dict(motion.counts),motion_events=motion.events,
        rune_birth=rune.birth,rune_events=rune.events,rune_counts=dict(rune.counts),continued_sameGame_terminal_frames=later,
        physical_player_counts=dict(player.counts),opaque_source_births=player.births,pickup_address_proof=BASE.BINDER.report(),
        no_unknown_cells_filled=True,App_input_domain='typedpartial fixture inlineG=App+16;declared16tag2/network2608tag2;notnatural1371 App',
        original_process=original_process,new_original_executions=0,production_model_executions=0,checker_executions=0,builder_executions=0,full880_frames=0,native_executions=0,complete_games=0,
        original_values_fed_to_production_model=False,reviewer_transition_checks_use_observed_prestate=True,
        reused_review_dependencies='750/CAS snapshot and physical live/Aura readers; previously independently restored2328 geometry and306 encoder; no second helper restoration claimed',
        limitations=['One controlled humanwarrior/Elwynn/seed0/navFalse trajectory with external clock and predetermined firstRune route, not recovered UI/joystick motion physics.',
            'App is typedpartial component input; no natural4253/1371 App producer,externrefVM restoration,freshboot or whole880.',
            'All declared known projections/physicalbytes are recompared; allocator addresses/unwritten bytes remain observations or None,not reconstructed values.',
            'Resource kind5 only in this natural-nearby witness; prior3/4 mixed components and othermaps/remote modes remain separate.',
            'Full968 mode0 route0 only; no network send,broadcast,199ACK or multiplayerplayability acceptance.',
            'Named live auxiliary source words remain observed values with GUID/copy binding; inner source and controller attempt annotation are not independently recovered.'],seconds=time.monotonic()-began)
    M.save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=M.sha(out/'review.json'),counts=dict(counts),rune_events=rune.events,motion_counts=dict(motion.counts))),flush=True)

if __name__=='__main__':main()
