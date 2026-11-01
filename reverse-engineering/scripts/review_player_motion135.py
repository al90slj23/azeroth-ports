#!/usr/bin/env python3
"""Read-only, independently computed review of the fixed1352328 snapshot batch.

No production, original, builder, checker or trace producer is executed.
The input Game/snapshot/world are explicitly supplied experimental state.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import argparse,ast,hashlib,json,math,os,re,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/player-motion135-oracle-20261101T231448.187735Z'
EXPECTED='840a034fc87e98a1b537924c1c1c99835a5b7bd424ad233089b8f9157afabd3e'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
ORIGINAL_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
SNAPSHOT=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_begin1089.memory'
SNAPSHOT_SHA='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf'
G,R=14554176,26204808

def sha(p):
    with Path(p).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def load(p):return json.loads(Path(p).read_text())
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def digest(x):return hashlib.sha256(x).hexdigest()
def F(x):return struct.unpack('<f',struct.pack('<I',x))[0]
def B(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def add(a,b):return B(F(a)+F(b))
def sub(a,b):return B(F(a)-F(b))
def mul(a,b):return B(F(a)*F(b))
def div(a,b):return B(F(a)/F(b))
def hypo(a,b):return B(math.sqrt(F(B(F(a)*F(a)+F(b)*F(b)))))
def u(raw,o=0):
    part=raw[o:o+4];assert len(part)==4
    if any(v is None for v in part):raise UnknownRead(o,4)
    return int.from_bytes(bytes(part),'little')
def put(raw,o,x):raw[o:o+4]=struct.pack('<I',x)
class UnknownRead(ValueError):
    def __init__(self,o,n):self.offset=o;self.size=n;super().__init__((o,n))
def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    except PermissionError:return None
    return False

def leb(b,p,signed=False):
    n=s=0
    while True:
        v=b[p];p+=1;n|=(v&127)<<s;s+=7;assert s<=35
        if v<128:return(n-(1<<s)if signed and v&64 else n),p
def sections(b):
    assert b[:8]==b'\0asm\1\0\0\0';p=8;rows=[]
    while p<len(b):
        start=p;kind=b[p];n,a=leb(b,p+1);p=a+n;assert p<=len(b);rows.append((kind,start,a,p))
    return rows
def exports(b,section):
    n,p=leb(b,section[2]);rows=[]
    for _ in range(n):
        size,p=leb(b,p);name=b[p:p+size].decode();p+=size;kind=b[p];idx,p=leb(b,p+1);rows.append((name,kind,idx))
    assert p==section[3];return rows
def static_reader(b):
    _,_,p,end=next(x for x in sections(b)if x[0]==11);n,p=leb(b,p);segments=[]
    for _ in range(n):
        flag,p=leb(b,p);assert flag==0 and b[p]==65
        addr,p=leb(b,p+1,True);assert b[p]==11;n,p=leb(b,p+1);segments.append((addr,b[p:p+n]));p+=n
    assert p==end
    def read(addr,n):
        out=bytearray(n)
        for a,v in segments:
            lo,hi=max(a,addr),min(a+len(v),addr+n)
            if lo<hi:out[lo-addr:hi-addr]=v[lo-a:hi-a]
        return bytes(out)
    return read

class World:
    """Independent snapshot input adapter and terrain/secondary height reader."""
    def __init__(self,memory,rc):
        self.ranges=[];self.queries=Counter();self.cache={}
        def take(p,n):
            assert 0<=p and 0<=n and p+n<=len(memory);self.ranges.append((p,n));return memory[p:p+n]
        header=take(rc,124);w=struct.unpack('<31I',header);self.header=header
        assert w[14]==0xffffffff and header[120]==0,'Only nonflat/no-primary Elwynn is admitted'
        rows=take(w[3],w[4]*36);bounds=take(w[6],w[7]*16);assert w[4]==w[7]==9
        self.tiles=[]
        for i in range(w[4]):
            cap,p,n=struct.unpack_from('<3I',rows,i*36);assert cap>=n==256
            chunks=take(p,n*264);tile=[]
            for j in range(n):
                cap,p,count=struct.unpack_from('<3I',chunks,j*264);assert cap>=count==145
                vertices=tuple(struct.iter_unpack('<3I',take(p,count*12)))
                tile.append((vertices,struct.unpack_from('<H',chunks,j*264+260)[0]))
            self.tiles.append((tuple(tile),struct.unpack_from('<4I',bounds,i*16)))
        self.secondary=None
        if w[23]!=0xffffffff:
            assert w[25]==w[28]**2
            self.secondary=(tuple(struct.unpack('<'+'I'*w[25],take(w[24],w[25]*4))),w[26],w[27],w[28])
        if w[8]!=0xffffffff:take(w[9],w[10])
        self.fallback=w[29]

    def triangle(self,a,b,c,x,y):
        ac=sub(a[0],c[0]);bc=sub(b[1],c[1]);cb=sub(c[0],b[0]);ay=sub(a[1],c[1])
        det=add(mul(ac,bc),mul(cb,ay))
        if F(det&0x7fffffff)<F(0x3089705f):return None
        px,py=sub(x,c[0]),sub(y,c[1])
        aa=div(add(mul(cb,py),mul(px,bc)),det)
        if F(aa)<0:return None
        bb=div(add(mul(ac,py),mul(px,sub(c[1],a[1]))),det)
        if F(bb)<0:return None
        cc=sub(sub(B(1),aa),bb)
        if F(cc)<0:return None
        return add(add(mul(aa,a[2]),mul(bb,b[2])),mul(cc,c[2]))

    def chunk(self,ch,x,y):
        v,holes=ch
        fx=mul(div(sub(v[0][0],x),0x44055555),B(16));fy=mul(div(sub(v[0][1],y),0x44055555),B(16))
        if not(0<=F(fx)<=1 and 0<=F(fy)<=1):return None
        row,col=min(7,int(F(mul(fx,B(8))))),min(7,int(F(mul(fy,B(8)))))
        if holes>>(((row<<1)&12)|(col>>1))&1:return None
        q=row*17+col;mid=q+9
        for a,b,c in ((mid,q,q+17),(mid,q+17,q+18),(mid,q+18,q+1),(mid,q+1,q)):
            sample=self.triangle(v[a],v[b],v[c],x,y)
            if sample is not None:return sample
        return None

    def terrain(self,x,y):
        for delta in (0,0x3d8f5c29,0xbd8f5c29):
            xx,yy=add(x,delta),add(y,delta)
            for chunks,bounds in self.tiles:
                if not(F(bounds[0])<=F(xx)<=F(bounds[2])and F(bounds[1])<=F(yy)<=F(bounds[3])):continue
                vx,vy=chunks[0][0][0][:2]
                row,col=div(sub(vx,xx),0x42055555),div(sub(vy,yy),0x42055555)
                if 0<=F(row)<16 and 0<=F(col)<16:
                    z=self.chunk(chunks[int(F(row))*16+int(F(col))],xx,yy)
                    if z is not None:return z
                else:
                    for ch in chunks:
                        z=self.chunk(ch,xx,yy)
                        if z is not None:return z
        return None

    def height(self,x,y):
        key=(x,y);self.queries['height_requests']+=1
        if key in self.cache:return self.cache[key]
        z=self.terrain(x,y)
        if z is not None and self.secondary is not None:
            values,ox,oy,width=self.secondary
            dx,dy=sub(x,ox),sub(y,oy);xx,yy=add(dx,dx),add(dy,dy)
            if 0<=F(xx)<width and 0<=F(yy)<width:
                v=values[int(F(xx))+width*int(F(yy))]
                if not math.isnan(F(v))and F(v)>F(z):z=v;self.queries['secondary_lift']+=1
        self.cache[key]=z;self.queries['height_unique_queries']+=1
        return z

def reference(game,xyz,facing,world,zone,counts):
    """2328 nonpolicy/circle/height-present domain, directly from its WAT."""
    raw=list(game);writes=[];packets=[]
    def get(o):return u(raw,o)
    def write(o,v):put(raw,o,v);writes.append((o,v))
    x,y,z=xyz;now=get(2352)
    if get(416):
        d2=add(mul(sub(get(420),x),sub(get(420),x)),mul(sub(get(424),y),sub(get(424),y)))
        if F(d2)>9 and F(sub(now,get(436)))<3:
            counts['pending_rejections']+=1
            return raw,0,packets,writes,'pending-correction-rejected'
        write(416,0);counts['cleared_pending']+=1
    #The clock is loaded even in the nonpolicy path; it does not affect the
    #admitted zero-condition timers. No inactive timestamp is invented.
    clock=get(444)if get(440)&1 else now
    assert get(464)==0 and zone[148]==0
    cx,cy,radius=struct.unpack_from('<2I',zone,104)+ (u(zone,120),)
    center=world.height(cx,cy)
    if center is None:center=world.fallback
    distance=hypo(sub(x,cx),sub(y,cy));outside=F(distance)>F(add(radius,B(10)))
    write(448,0);write(456,0);write(1744,0)
    h=world.height(x,y)
    assert h is not None,'Height-miss radius12/ring branches are outside this38-case audit'
    too_low=F(z)<F(add(h,B(-15)))
    corrected=outside or too_low
    if corrected:
        write(1744,0);write(456,0);write(448,0)
        px,py=x,y
        if outside:
            denom=distance if F(distance)>F(B(.01))else B(.01)
            extent=add(add(radius,B(10)),B(-4))
            px=add(cx,mul(div(sub(x,cx),denom),extent))
            py=add(cy,mul(div(sub(y,cy),denom),extent));counts['circle_clamps']+=1
        ground=world.height(px,py)
        assert ground is not None,'No synthetic fallback for unreviewed ring-rescue domain'
        pz=add(ground,B(.5));sequence=get(1644);write(1644,(sequence+1)&0xffffffff)
        guid=bytes(raw[1336:1344]);assert None not in raw[1336:1344]
        mask=sum(1<<i for i,v in enumerate(guid)if v);packed=bytes([mask])+bytes(v for v in guid if v)
        packets.append([199,(packed+struct.pack('<8I',sequence,0,0,px,py,pz,facing,0)).hex()])
        if outside:
            text=b'|cffff4040You cannot leave the battlefield.|r'
            packets.append([150,(struct.pack('<BIQI',10,0,0,len(text)+1)+text+b'\0\0').hex()])
        n=get(1888);assert n+len(packets)<=get(1880)
        for i in range(len(packets)):write(1888,n+i+1)
        for o,v in ((432,sequence),(428,pz),(424,py),(420,px),(416,1),(436,now)):write(o,v)
        counts['corrections']+=1;counts['action_wraps']+=int(sequence==0xffffffff);branch='corrected'
    else:px,py,pz=x,y,z;counts['unchanged_input']+=1;branch='unchanged-input'
    for o,v in ((2500,now),(1428,facing),(1424,pz),(1420,py),(1416,px)):write(o,v)
    assert raw[2587]==1,'Phase0 begin1089 continuation is not exercised'
    return raw,int(all(F(a)==F(b)for a,b in zip((px,py,pz),xyz))),packets,writes,branch

def source_edges(snapshot,names):
    edges=set()
    for name in names:
        path=snapshot/name
        if name.endswith('.mjs'):
            for relative in re.findall(r"from\s+['\"](\.[^'\"]+)['\"]",path.read_text()):
                target=str((ROOT/Path(name).parent/relative).resolve().relative_to(ROOT))
                assert target in names,(name,target);edges.add((name,target))
            continue
        if not name.endswith('.py'):continue
        tree=ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Call)and isinstance(node.func,ast.Name):assert node.func.id not in('exec','eval','__import__')
            modules=[]
            if isinstance(node,ast.ImportFrom):
                if node.level:
                    assert node.level==1 and name.startswith('reconstruction/')
                    prefix='.'.join(Path(name).parent.parts[1:])
                    if node.module:prefix+='.'+node.module
                else:prefix=node.module or ''
                modules=[prefix]+[prefix+'.'+a.name if prefix else a.name for a in node.names]
            elif isinstance(node,ast.Import):modules=[a.name for a in node.names]
            for module in modules:
                if not module:continue
                part=Path(*module.split('.'))
                for folder in('scripts','reconstruction'):
                    candidates=(ROOT/folder/part.with_suffix('.py'),ROOT/folder/part/'__init__.py')
                    found=next((p for p in candidates if p.is_file()),None)
                    if found is None:continue
                    target=str(found.relative_to(ROOT));assert target in names,(name,target);edges.add((name,target))
                    for parent in found.parents:
                        if parent==ROOT/folder:break
                        if (parent/'__init__.py').is_file():
                            target=str((parent/'__init__.py').relative_to(ROOT));assert target in names,(name,target);edges.add((name,target))
    return sorted(edges)

def static_proofs(original,out):
    funcs={};db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
    with (PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        for idx in(2328,968,1560,29631,18670,46295,5795,49503,29219,28964,38323):
            row=dict(db.execute('select * from functions where idx=?',(idx,)).fetchone());size=row['wat_end']-row['wat_start'];captured=min(size,65536)if idx==968 else size;assert captured<=524288
            stream.seek(row['wat_start']);wat=stream.read(captured);body=original[row['body_start']:row['body_end']]
            assert wat.splitlines()[0].startswith(f'  (func (;{idx};)'.encode())
            (out/f'{idx}.wat').write_bytes(wat);funcs[idx]=dict(body_start=row['body_start'],body_end=row['body_end'],body_sha256=digest(body),wat_start=row['wat_start'],wat_end=row['wat_end'],wat_capture_sha256=digest(wat),wat_bytes=captured,wat_full_bytes=size,complete_WAT_captured=captured==size)
    lines=(out/'2328.wat').read_text().splitlines();windows={}
    for name,a,b,tokens in(
        ('pending_reject',18,54,('offset=416','offset=420','offset=424','f32.gt','offset=2352','offset=436','f32.lt','br_if 2')),
        ('clock_override',55,68,('i32.const 444','i32.const 2352','offset=440','select','f32.load')),
        ('policy_gate',268,349,('offset=148','i32.eqz','br 1','call 23181','call 33324')),
        ('no_under_timer',436,445,('i32.eqz','offset=448')),
        ('no_nav_timer',518,528,('i32.store offset=456',)),
        ('nonpolicy_stuck_gate',556,584,('local.get 12','i32.eqz','br_if 0','i32.store offset=1744')),
        ('final_commit',2530,2614,('offset=432','offset=416','offset=436','offset=2500','offset=1428','offset=1424','offset=1420','offset=1416','call 1089','f32.eq'))):
        text='\n'.join(lines[a-1:b]);assert all(t in text for t in tokens),(name,tokens)
        windows[name]=dict(first_line=a,last_line=b,sha256=digest(text.encode()),text=text)
    return dict(functions=funcs,windows=windows,wat_bytes=sum(f['wat_bytes']for f in funcs.values()),full_WAT_scanned=False)

def controller_static_review(out,read):
    """A separate, static owner-boundary review; no controller is executed."""
    names=('headless_motion135.py','headless135.py','record_cells135.py','initial_state135_data.py')
    sources={};texts={}
    for name in names:
        path=ROOT/'reconstruction/core_spec'/name;sources[name]=sha(path);texts[name]=path.read_text()
        target=out/'controller-source'/name;target.parent.mkdir(exist_ok=True);target.write_text(texts[name])
    def constants(text):
        return{n.targets[0].id:ast.literal_eval(n.value)for n in ast.parse(text).body
            if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
    owner=constants(texts['headless_motion135.py']);entries=constants(texts['initial_state135_data.py'])['ZONE_ENTRIES']
    assert owner['ZERO_WORDS135']==(416,440,448,456,464,1744,1764,2496,2500)
    allowed=set(owner['MOTION_WORDS135']);assert not({1336,1340,1416,1420,1424,1644,1880,1884,1888,2352,2528,2583,2587}&allowed)
    assert len(entries)==12
    for i,entry in enumerate(entries):
        zone=read(5456016+152*i,152)
        assert(entry[1],entry[2],entry[3])==tuple(u(zone,o)for o in(104,108,116))
    owner_text=texts['headless_motion135.py'];headless=texts['headless135.py']
    assert 'raw=[None]*2592'in owner_text and 'ZONE_ENTRIES[zone][3]'in owner_text
    assert "u32(self.cells,416,'Motion pending correction')!=player_action_tag416"in owner_text
    assert 'for offset in MOTION_WORDS135:raw[offset:offset+4]=result[offset:offset+4]'in owner_text
    assert 'if state.world.primary is not None:'in headless and 'if state.collection.level.phase2587!=1:'in headless
    assert 'if state.special_mode2582 or state.collection.currency.mode or state.collection.currency.local_peer:'in headless
    assert 'if state.delayed_records56 or state.effect_records120 or state.player_action_tag416:'in headless
    assert "player_action_tag416=u32(result.game_bytes,416,'2328 correction state')"in headless
    lines=(out/'1560.wat').read_text().splitlines();windows={}
    for name,a,b,tokens in(
        ('zone_entry_pointer',205,220,('i32.const 152','i32.const 5456016','local.set 8')),
        ('entry_heading_load',530,532,('local.get 8','f32.load offset=116','local.set 33')),
        ('heading_store',707,709,('local.get 3','local.get 33','f32.store offset=1516')),
        ('constructor_zero_stores',1209,1235,('i64.store offset=2584','i32.store offset=544','i32.store offset=536','i32.store offset=528','i32.store offset=504','i32.store offset=1852','i32.store offset=1832','i32.store offset=552')),
        ('game_copy',2741,2753,('i32.const 88','i32.const 2592','memory.copy'))):
        value='\n'.join(lines[a-1:b]);assert all(x in value for x in tokens),(name,value)
        windows[name]=dict(first_line=a,last_line=b,text=value,sha256=digest(value.encode()))
    assert all(sha(ROOT/'reconstruction/core_spec'/n)==h for n,h in sources.items())
    return dict(kind='separate_read_only_static_controller_review_not_new_original_validation',source_sha256=sources,
        motion_persistent_words=owner['MOTION_WORDS135'],constructor_zero_words=owner['ZERO_WORDS135'],
        zone_heading_words=[x[3]for x in entries],constructor_proofs=windows,unknown_backing_preserved=True,
        canonical_binding_fields=[1336,1340,1416,1420,1424,1644,2352,2528,2583,2587],
        queue1880_1884_1888_not_manufactured=True,action416_owner_equality_enforced=True,
        effects_active416_guard_preserved=True,mode0_phase1_no_primary_only=True,
        full968_17726_broadcast_not_implemented=True,production_executions=0,new_original_cases=0)

def main():
    global RUN,EXPECTED
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--batch',type=Path);parser.add_argument('--comparison-sha256')
    args=parser.parse_args()
    if args.batch is not None:
        assert args.comparison_sha256;RUN=args.batch.resolve();EXPECTED=args.comparison_sha256
    else:assert args.comparison_sha256 is None
    out=args.output.resolve();assert out.is_relative_to((ROOT/'evidence').resolve());out.mkdir()
    before=sha(Path(__file__));(out/'reviewer-source.py').write_bytes(Path(__file__).read_bytes());start=time.monotonic()
    report=load(RUN/'comparison.json');assert sha(RUN/'comparison.json')==EXPECTED and report['cases']==report['actual_cases']==38 and report['differences']==0
    sources=report['source_sha256_before'];assert len(sources)>=17 and sources==report['source_sha256_after']
    for n,h in sources.items():assert sha(RUN/'source-snapshot'/n)==sha(ROOT/n)==h,n
    edges=source_edges(RUN/'source-snapshot',sources);assert not any('headless'in n for n in sources)
    assert edges==[tuple(x)for x in report['complete_static_local_import_edges']]
    assert report['expected_first']and not report['input_contains_expected']and report['closure_verified_before_expectations']
    for n,h in report['artifacts'].items():assert sha(RUN/n)==h
    artifacts={n:sha(RUN/n)for n in('comparison.json','fixtures.json','inputs.json','config.json','results.jsonl','manifest.json','terminal.json','runtime.json')}
    original=ORIGINAL.read_bytes();assert len(original)==90959080 and digest(original)==ORIGINAL_SHA
    manifest=load(RUN/'manifest.json');module=(RUN/manifest['module_file']).read_bytes();assert digest(module)==manifest['module_sha256']
    a,b=sections(original),sections(module);assert [x[0]for x in a]==[x[0]for x in b]and not any(x[0]==8 for x in a)
    for aa,bb in zip(a,b):
        if aa[0]!=7:assert original[aa[1]:aa[3]]==module[bb[1]:bb[3]]
    prior=exports(original,next(x for x in a if x[0]==7));changed=exports(module,next(x for x in b if x[0]==7));assert changed==prior+[
        ('research_player_motion135_move_player',0,2328),('research_player_motion135_motion_dispatch',0,968),('research_player_motion135_stack',3,0)]
    proofs=static_proofs(original,out);read=static_reader(original);zone=read(5456016,152);assert zone[148]==0
    assert struct.unpack_from('<2I',zone,104)==(3323121664,3290316800)and u(zone,120)==B(120)
    assert read(1585207,45)==b'|cffff4040You cannot leave the battlefield.|r'
    snapshot=SNAPSHOT.read_bytes();assert digest(snapshot)==SNAPSHOT_SHA and len(snapshot)==166395904
    world=World(snapshot,R);assert len(world.ranges)==2318
    fixtures,inputs,config=load(RUN/'fixtures.json'),load(RUN/'inputs.json'),load(RUN/'config.json')
    actual=[json.loads(line)for line in(RUN/'results.jsonl').read_text().splitlines()];assert len(fixtures)==len(inputs)==len(actual)==38
    assert config['snapshot_path']==str(SNAPSHOT)and config['snapshot_sha256']==SNAPSHOT_SHA
    assert(config['game_pointer'],config['world_pointer'])==(G,R)and config['input_sha256']==sha(RUN/'inputs.json')
    assert config['world_ranges']==[list(x)for x in world.ranges]
    geom=digest(b''.join(snapshot[p:p+n]for p,n in world.ranges));counts=Counter();groups=Counter();opcode=Counter();canonical=Counter();changed_offsets=Counter();all_writes=Counter()
    for case,inp,got in zip(fixtures,inputs,actual):
        assert case['id']==inp['id']==got['id'];assert set(inp)=={'id','xyz_bits','facing_bits','patch_words'}and inp==case['input']
        base=bytearray(snapshot[G:G+8192])
        for o,v in inp['patch_words']:put(base,o,v)
        assert base.hex()==got['game_before_hex']==case['expected']['game_before_hex']
        assert base[2587]==1 and u(base,464)==0 and u(base,2348)==R
        independent,ret,packets,writes,branch=reference(bytes(base),tuple(inp['xyz_bits']),inp['facing_bits'],world,zone,counts)
        after=bytes.fromhex(got['game_after_hex']);assert bytes(independent)==after==bytes.fromhex(case['expected']['game_after_hex'])
        assert ret==got['return_value']==case['expected']['return_value']and packets==got['packets']==case['expected']['packets']
        assert branch==case['expected']['branch']and [list(x)for x in writes]==case['diagnostic']['writes']
        changes=[i for i,(x,y)in enumerate(zip(base,after))if x!=y];assert got['changed_bytes']==changes
        assigned={i for o,v in writes for i in range(o,o+4)};assert all(base[i]==after[i]for i in range(8192)if i not in assigned)
        counts['all_game_bytes_strict']+=8192;counts['unchanged_game_bytes_outside_writes']+=8192-len(assigned)
        changed_offsets.update(changes);all_writes.update(o for o,v in writes);groups[case['group']]+=1;opcode.update(p[0]for p in packets)
        qb,qa=got['queue_before'],got['queue_after'];assert(qb['capacity'],qb['pointer'],qb['count'])==struct.unpack_from('<3I',base,1880)
        assert(qa['capacity'],qa['pointer'],qa['count'])==struct.unpack_from('<3I',after,1880)
        assert qb['capacity']==qa['capacity']and qb['pointer']==qa['pointer']and qa['count']-qb['count']==len(packets)
        assert got['world_before_hex']==got['world_after_hex']==world.header.hex()and got['geometry_ranges_unchanged']==2318
        assert got['stack_after']==1048576 and got['host_calls']==0 and got['full_original_function']==2328
        #Independently reproduce the canonical read-domain masks, not the
        #production canonical model or its selfcheck execution.
        spans=[(416,4),(440,4),(464,4),(2352,4),(1416,8),(2587,1)]
        if u(base,416):spans.extend(((420,8),(436,4)))
        if u(base,440)&1:spans.append((444,4))
        if packets:spans.extend(((1336,8),(1644,4),(1880,4),(1888,4)))
        cells=[None]*8192
        for o,n in spans:cells[o:o+n]=base[o:o+n]
        result,cr,cp,cw,cb=reference(cells,tuple(inp['xyz_bits']),inp['facing_bits'],world,zone,Counter())
        assert(cr,cp,cw,cb)==(ret,packets,writes,branch)
        for j,v in enumerate(result):
            if v is None:assert cells[j]is None;canonical['unknown_bytes_preserved']+=1
            else:assert v==after[j];canonical['known_bytes']+=1
        canonical['cases']+=1
    assert dict(groups)==report['groups']and canonical['unknown_bytes_preserved']==report['canonical_cells']['unknown_bytes_preserved']==309086
    first=fixtures[0];cells=list(bytes.fromhex(first['expected']['game_before_hex']));cells[464:468]=[None]*4
    try:reference(cells,tuple(first['input']['xyz_bits']),first['input']['facing_bits'],world,zone,Counter())
    except UnknownRead as e:assert(e.offset,e.size)==(464,4);canonical['unknown_read464_rejected']+=1
    else:raise AssertionError('Unknown scalar source was silently supplied')
    terminal=load(RUN/'terminal.json');rt=load(RUN/'runtime.json');assert terminal==report['process']
    assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<terminal['deadline_seconds']==60
    assert missing(terminal['pid'])is True and missing(terminal['pgid'],True)is True
    assert rt==report['runtime']and(rt['cases'],rt['original_calls'],rt['host_calls'],rt['denied_imports'])==(38,38,0,878)
    assert rt['max_memory_bytes']==len(snapshot)and not rt['freshGame']and not rt['worldRc_forged']and not rt['original_body_modified']
    assert geom==digest(b''.join(snapshot[p:p+n]for p,n in world.ranges))
    assert before==sha(Path(__file__))and all(sha(ROOT/n)==h for n,h in sources.items())
    assert artifacts=={n:sha(RUN/n)for n in artifacts}
    controller=controller_static_review(out,read)
    save(out/'controller-static-review.json',controller);save(out/'static-proofs.json',proofs)
    value=dict(status='scoped_player_motion135_read_only_independent_review_passed',version='0.135.1',actual_build='90898d5e3',comparison=str(RUN/'comparison.json'),comparison_sha256=EXPECTED,
        cases=38,full_original_calls=38,source_files=len(sources),production_files=sum(n.startswith('reconstruction/')for n in sources),source_sha256=sources,source_edges=edges,
        independent_counts=dict(counts),groups=dict(groups),new_packet_opcodes=dict(opcode),changed_byte_offsets=dict(changed_offsets),scalar_write_counts=dict(all_writes),
        independently_recomputed_canonical_masks=dict(canonical),world_input=dict(snapshot_sha256=SNAPSHOT_SHA,bytes=len(snapshot),range_count=2318,combined_ranges_sha256=geom,
            after_geometry_invariance='Frozen original runner asserted hashes for all2318 ranges; reviewer independently binds prestate ranges, not unavailable fullpostmemory'),
        static_proofs_sha256=sha(out/'static-proofs.json'),controller_static_review_sha256=sha(out/'controller-static-review.json'),artifacts_sha256=artifacts,original_process=terminal,runtime=rt,reviewer_sha256=before,elapsed_seconds=time.monotonic()-start,
        new_original_executions=0,production_model_executions=0,checker_executions=0,builder_executions=0,full880_frames=0,native_executions=0,complete_games=0,
        limitations=['Inputs include historicalsnapshotGame/world, with declared scalar patches; this is consumer validation, not independentconstructor/worldproduction.',
            'DefaultElwynn nonpolicycircle and all queried height-present branches only; no primary/aux/nav/polygon/timer/radius12/ring-rescue acceptance.',
            'Direct2328 only; exporting968 does not execute/validate its decoder,17726dispatch,broadcast orpeerstate handling.',
            'Phase1 only; phase0actual1089 continuation, inputproducer and completeApp/mainloop remainunverified.',
            'Existingqueueprefix unchanged is a frozenrunner assertion plus knownsnapshotprefix; fullpostqueuebacking is not exported for independentre-read.',
            'Canonicalmask recomputation is reviewer-only static-consumer replay and does not add38originalcases.'])
    save(out/'review.json',value);print(json.dumps(dict(directory=str(out),sha256=sha(out/'review.json'),counts=dict(counts),canonical=dict(canonical))),flush=True)

if __name__=='__main__':main()
