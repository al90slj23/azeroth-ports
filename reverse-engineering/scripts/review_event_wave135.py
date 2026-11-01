#!/usr/bin/env python3
"""Read-only wave25 audit: no production, original, builder or checker runs.

Own struct-f32 arithmetic, RNG, world queries, geometry and wire decoders
reconstruct the event reference. Ordinary prefix draw/position records remain
an explicit dependency; exact frozen output re-comparison is a separate layer.
"""
from collections import Counter,deque
from datetime import datetime,timezone
from functools import lru_cache
from pathlib import Path
import argparse,ast,hashlib,json,math,os,re,struct,sys,time
sys.dont_write_bytecode=True
from review_opening_combat135 import sections,static_reader,missing,allowed_unknown
from review_combat137 import exports
from review_resource_spawn135 import decode169

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/full0135-oracle-20261101T190041.544885Z'
RECEIPT_SHA='b02fcbe303c2058fee848c00b47f3389832690138cb6b99ab6386f38adeab555'
CORE_SHA='9c7c9bec1757df7717a9cbcf5b1be3b452fd1e1663978f22480b6f683314d0b6'
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
SNAPSHOT=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_begin1089.memory'
SNAPSHOT_SHA='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf'
MASK=0xffffffff;TAU=0x40c90fdb

def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def F(x):return struct.unpack('<f',struct.pack('<I',x))[0]
def B(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def A(a,b):return B(F(a)+F(b))
def S(a,b):return B(F(a)-F(b))
def M(a,b):return B(F(a)*F(b))
def D(a,b):return B(F(a)/F(b))
def SQ(a):return B(math.sqrt(F(a)))
def H(a,b):return SQ(B(F(a)**2+F(b)**2))
def U(row,o):return int.from_bytes(bytes(row[o:o+4]),'little')
def Q(row,o):return int.from_bytes(bytes(row[o:o+8]),'little')
def literal(p,name):
    tree=ast.parse(p.read_text());return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id==name for x in n.targets)))
def rng(s):
    a,b,c,d=s;rot=lambda x,k:((x<<k)|(x>>(32-k)))&MASK
    return(rot((a+d)&MASK,7)+a)&MASK,(a^b^d,b^a^c,(a^c^(b<<9))&MASK,rot(b^d,11))
def advance(s,n):
    for _ in range(n):_,s=rng(s)
    return s
def pick(s,count):
    threshold=((count<<(32-count.bit_length()))-1)&MASK
    for n in range(1,100001):
        x,s=rng(s);p=x*count
        if(p&MASK)<=threshold:return p>>32,s,n
    raise AssertionError('Review index watchdog')
def uniform(s,lo=0,hi=TAU):
    for n in range(1,100001):
        x,s=rng(s);value=A(lo,M(A((x>>9)|0x3f800000,0xbf800000),S(hi,lo)))
        if F(value)<F(hi):return A(value,0),s,n
    raise AssertionError('Review float-range watchdog')

# Independent scalar kernels follow the source's ordered binary64 polynomial
# constants; no game module/function is imported or called by this auditor.
h=float.fromhex
PI2=h('0x1.921fb54442d18p0');PI=h('0x1.921fb54442d18p1');PI3=h('0x1.2d97c7f3321d2p2');TWO_PI=h('0x1.921fb54442d18p2')
def sk(x):
    z=x*x;v=z*x
    return B((v*(z*z))*(z*h('0x1.6cd878c3b46a7p-19')+h('-0x1.a00f9e2cae774p-13'))+(v*(z*h('0x1.11110896efbb2p-7')+h('-0x1.5555554cbac77p-3'))+x))
def ck(x):
    z=x*x;w=z*z
    return B((z*h('-0x1.ffffffd0c5e81p-2')+1)+w*h('0x1.55553e1053a42p-5')+(z*w)*(z*h('0x1.99342e0ee5069p-16')+h('-0x1.6c087e80f1e27p-10')))
def trig(bits,cosine=False):
    a=bits&0x7fffffff;x=abs(F(bits))
    if a<=0x40c90fdb:
        if cosine:
            if a<=1061752794:return ck(x)
            if a<=1075235811:return sk(PI2-x)
            if a<=1081824209:return ck(x-PI)^0x80000000
            if a<=1085271519:return sk(x-PI3)
            return ck(x-TWO_PI)
        if a<1061752795:r=sk(x)
        elif a<1075235812:r=ck(x-PI2)
        elif a<1081824210:r=sk(x-PI)^0x80000000
        elif a<1085271520:r=ck(x-PI3)^0x80000000
        else:r=sk(x-TWO_PI)
        return r^(bits&0x80000000)
    if a<1088565718:return ck(x-TWO_PI)if cosine else sk(x-TWO_PI)^(bits&0x80000000)
    assert a<=1305022426
    value=F(bits);n=((value*h('0x1.45f306dc9c883p-1'))+h('0x1.8p52'))+h('-0x1.8p52');y=(value+n*h('-0x1.921fb5p0'))+n*h('-0x1.110b4611a6263p-26');q=int(n)&3
    return(ck(y),sk(y)^0x80000000,ck(y)^0x80000000,sk(y))[q]if cosine else(sk(y),ck(y),sk(y)^0x80000000,ck(y)^0x80000000)[q]
def atan(bits):
    a=bits&0x7fffffff;v=bits;index=-1
    if a>=1054867456:
        if a<1066926080:
            if a>=1060110336:v=D(A(a,0xbf800000),A(a,0x3f800000));index=1
            else:v=D(A(A(a,a),0xbf800000),A(a,0x40000000));index=0
        elif a<1075576832:v=D(A(a,0xbfc00000),A(M(a,0x3fc00000),0x3f800000));index=2
        else:v=D(0xbf800000,a);index=3
    elif a<964689920:return bits
    z=M(v,v);w=M(z,z);p=M(v,A(M(w,A(M(w,0xbdda1247),0xbe4cca98)),M(z,A(M(w,A(M(w,0x3d7cac25),0x3e11f50d)),0x3eaaaaa9))))
    if index<0:return S(v,p)
    high=(0x3eed6338,0x3f490fda,0x3f7b985e,0x3fc90fda);low=(0x31ac3769,0x33222168,0x33140fb4,0x33a22168)
    return S(high[index],S(S(p,low[index]),v))^(bits&0x80000000)
def atan2(y,x):
    if x==0x3f800000:return atan(y)
    q=((x>>30)&2)|(y>>31);ay,ax=y&0x7fffffff,x&0x7fffffff
    if not ay:return(0,0,0x40490fdb,0xc0490fdb)[q]if q&2 else y
    if not ax:return 0x3fc90fdb|(y&0x80000000)
    angle=atan(D(y,x)&0x7fffffff)
    return(angle,angle^0x80000000,S(0x40490fdb,A(angle,0x33bbbd2e)),A(A(angle,0x33bbbd2e),0xc0490fdb))[q]

class World:
    def __init__(self,description):
        self.desc=description;files=description['artifacts'];raw=Path(files['terrain-query.bin']['path']).read_bytes();p=0
        def take(fmt):
            nonlocal p
            values=struct.unpack_from(fmt,raw,p);p+=struct.calcsize(fmt);return values
        n,=take('<I');assert n==9;self.tiles=[]
        for _ in range(n):
            a,b,c,d,nchunks=take('<5I');assert nchunks==256;chunks=[]
            for _ in range(nchunks):
                holes,vertices=take('<HI');assert vertices==145
                chunks.append((holes,tuple(take('<3I')for _ in range(vertices))))
            self.tiles.append(((a,b,c,d),chunks))
        assert p==len(raw)
        self.nav=Path(files['navigation.bin']['path']).read_bytes();data=Path(files['secondary-height.u32le']['path']).read_bytes();self.secondary=struct.unpack('<'+'I'*(len(data)//4),data)
        self.origin=description['origin_xy_bits'];self.width=description['nav_width'];self.secondary_width=description['secondary_width'];self.probes=Counter()
    def nav_at(self,x,y):
        dx,dy=S(x,self.origin[0]),S(y,self.origin[1]);xx,yy=int(F(dx)),int(F(dy))
        if F(dx)<0 or F(dy)<0 or xx>=self.width or yy>=self.width:return False,None,None
        i=xx+self.width*yy;assert i<len(self.nav);return True,self.nav[i],i
    @staticmethod
    def triangle(a,b,c,x,y):
        ac=S(a[0],c[0]);bc=S(b[1],c[1]);cb=S(c[0],b[0]);ay=S(a[1],c[1]);det=A(M(ac,bc),M(cb,ay))
        if abs(F(det))<F(0x3089705f):return None
        py,px=S(y,c[1]),S(x,c[0]);alpha=D(A(M(cb,py),M(px,bc)),det)
        if F(alpha)<0:return None
        beta=D(A(M(ac,py),M(px,S(c[1],a[1]))),det)
        if F(beta)<0:return None
        gamma=S(S(0x3f800000,alpha),beta)
        if F(gamma)<0:return None
        return A(A(M(alpha,a[2]),M(beta,b[2])),M(gamma,c[2]))
    def chunk(self,item,x,y):
        holes,v=item;fx=M(D(S(v[0][0],x),0x44055555),0x41800000);fy=M(D(S(v[0][1],y),0x44055555),0x41800000)
        if not(0<=F(fx)<=1 and 0<=F(fy)<=1):return None
        row=min(7,int(F(M(fx,0x41000000))));col=min(7,int(F(M(fy,0x41000000))))
        if holes>>(((row<<1)&12)|(col>>1))&1:return None
        base=row*17+col;center=base+9
        for ia,ib,ic in((center,base,base+17),(center,base+17,base+18),(center,base+18,base+1),(center,base+1,base)):
            result=self.triangle(v[ia],v[ib],v[ic],x,y)
            if result is not None:return result
        return None
    def tile(self,chunks,x,y):
        v=chunks[0][1][0];fx=D(S(v[0],x),0x42055555);fy=D(S(v[1],y),0x42055555)
        if 0<=F(fx)<16 and 0<=F(fy)<16:return self.chunk(chunks[int(F(fx))*16+int(F(fy))],x,y)
        for chunk in chunks:
            result=self.chunk(chunk,x,y)
            if result is not None:return result
        return None
    @lru_cache(maxsize=8192)
    def height(self,x,y):
        value=None
        for delta in(0,0x3d8f5c29,0xbd8f5c29):
            xx,yy=A(x,delta),A(y,delta)
            for bounds,chunks in self.tiles:
                a,b,c,d=map(F,bounds)
                if a<=F(xx)<=c and b<=F(yy)<=d:
                    value=self.tile(chunks,xx,yy)
                    if value is not None:break
            if value is not None:break
        if value is None:return None
        dx=A(S(x,self.origin[0]),S(x,self.origin[0]));dy=A(S(y,self.origin[1]),S(y,self.origin[1]))
        if 0<=F(dx)<self.secondary_width and 0<=F(dy)<self.secondary_width:
            extra=self.secondary[int(F(dx))+self.secondary_width*int(F(dy))]
            if extra&0x7fffffff<=0x7f800000 and F(extra)>F(value):value=extra
        return value

def strict_compare(want,got,path,counts,initial,charged):
    if want is None:
        assert len(path)>=4 and path[-4]in('units','pickups')and path[-3]=='storage'and type(got)is int and 0<=got<=255
        owner,index,offset=path[-4],path[-2],path[-1];input_vector=initial['units']if owner=='units'else initial['input']['pickups']
        if index<len(input_vector['storage'])and input_vector['storage'][index][offset]is None:
            pass
        elif owner=='units'and index>=input_vector['count']:
            if index<charged['active_units_count']:allowed_unknown('units',charged['expected_units'][index],offset)
        else:raise AssertionError(('Unjustified physical unknown',path))
        if owner=='units'and index in charged['indices']:assert offset not in range(16,32)and offset not in range(348,352)
        counts['explicit_unknown_cells']+=1;counts['unknown_nonzero_observed']+=bool(got);return
    assert type(want)is type(got),(path,type(want),type(got))
    if isinstance(want,dict):
        assert set(want)==set(got),(path,set(want),set(got))
        for k,v in want.items():strict_compare(v,got[k],path+(k,),counts,initial,charged)
    elif isinstance(want,list):
        assert len(want)==len(got),(path,len(want),len(got))
        for i,(a,b)in enumerate(zip(want,got)):strict_compare(a,b,path+(i,),counts,initial,charged)
    else:assert want==got,(path,want,got);counts['equal_known_values']+=1

def npc_fields(guid,d,row,player,level):
    hp=math.ceil(max(F(U(row,288)),0));scale=d['scale_bits']
    return{0:guid&MASK,1:guid>>32,2:9,3:d['entry'],4:scale,16:player&MASK,17:player>>32,22:hp,28:hp,34:min((level+3*d['elite'])&MASK,63),35:14,36:256,46:0,126:2000,127:2000,129:M(scale,0x3f000000),130:M(scale,0x3fc00000),131:d['display'],132:d['display'],134:0x40a00000,135:0x41200000,145:0x3f800000}

def frozen_closure(frozen,files):
    declared=set(files);edges=set();production=0
    for name in files:
        p=frozen/name
        if p.suffix=='.mjs':
            for relative in re.findall(r"from\s+['\"](\.[^'\"]+)['\"]",p.read_text()):
                target=str((p.parent/relative).resolve().relative_to(frozen.resolve()));assert target in declared;edges.add((name,target))
            continue
        if p.suffix!='.py':continue
        parts=Path(name).with_suffix('').parts;tree=ast.parse(p.read_text());production+=name.startswith('reconstruction/')
        for node in ast.walk(tree):
            if name.startswith('reconstruction/')and isinstance(node,ast.Call):
                fn=node.func;key=fn.id if isinstance(fn,ast.Name)else fn.attr if isinstance(fn,ast.Attribute)else''
                assert key not in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__'),(name,key)
            modules=[]
            if isinstance(node,ast.Import):modules=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom):
                prefix='.'.join(list(parts[1:-node.level])+([node.module]if node.module else[]))if node.level else(node.module or'')
                modules=[prefix]+[prefix+'.'+a.name if prefix else a.name for a in node.names]
            for module in modules:
                if not module:continue
                rel=Path(*module.split('.'))
                for folder in('scripts','reconstruction'):
                    source=frozen/folder/rel.with_suffix('.py');package=frozen/folder/rel/'__init__.py'
                    path=source if source.is_file()or(ROOT/folder/rel.with_suffix('.py')).is_file()else package if package.is_file()or(ROOT/folder/rel/'__init__.py').is_file()else None
                    if path:target=str(path.relative_to(frozen));assert target in declared;edges.add((name,target))
    return production,[list(x)for x in sorted(edges)]

def event_reference(c,label,actual,defs,geometry,world,stats):
    inp=c['input'];now=inp['now_bits'];minute=D(now,0x42700000);words=advance(tuple(inp['rng_words']),label['ordinary_draws']);draws=0
    eligible=[i for i,d in enumerate(defs)if not d['elite']and F(d['unlock_bits'])<=F(minute)]
    cheap=[i for i in eligible if F(defs[i]['cost_bits'])<=F(0x3f99999a)]or eligible
    choices=[i for i in range(4)if i!=inp['last_event2586']];index,words,n=pick(words,len(choices));draws+=n;style=choices[index];index,words,n=pick(words,len(cheap));draws+=n;index=cheap[index]
    stats['selection_rejection_draws']+=draws-2
    assert style==label['event']==actual['last_event2586']
    delay=A(M(minute,0xbfc00000),0x42700000);deadline=A(now,delay if F(delay)>35 else B(35));assert actual['next_event2424_bits']==deadline
    origin=inp['player_xyz_bits'];cx,cy,radius=geometry;path=c['distance_map'];positions=[];charges=[];new_records=[]
    begin=c['units']['count']+len(label['ordinary_requests']);raw_units=[bytes.fromhex(x)for x in actual['units']['storage']]
    def probe(x,y,inline=False):
        stats['geometry_probes']+=1;distance=H(S(x,cx),S(y,cy))
        if F(distance)>F(A(radius,B(18))):stats['rejected_zone_radius']+=1;return None
        height=world.height(x,y)
        if height is None:stats['rejected_height_miss']+=1;return None
        threshold=8 if F(distance)>F(radius)else 25
        if abs(F(S(height,origin[2])))>threshold:stats['rejected_height_difference']+=1;return None
        inside,nav,at=world.nav_at(x,y)
        if path is None:
            if inside and(nav==1 if inline else bool(nav)):stats['rejected_nav']+=1;return None
        else:
            if inside and nav:stats['rejected_nav']+=1;return None
            if path['field24']>=401:
                if not inside:stats['rejected_path_outside']+=1;return None
                cost=path['values_u16'][at];limit=A(M(H(S(x,origin[0]),S(y,origin[1])),B(1.5)),B(12))
                if cost==65535 or F(B(cost))>F(limit):stats['rejected_path_cost']+=1;return None
        return x,y,height
    def radial(angle,values,inline=False):
        sine,cosine=trig(angle),trig(angle,True)
        for radius in values:
            xyz=probe(A(origin[0],M(cosine,B(radius))),A(origin[1],M(sine,B(radius))),inline)
            if xyz is not None:return xyz
        return None
    def ur(lo=0,hi=TAU):
        nonlocal words,draws
        x,words,n=uniform(words,lo,hi);draws+=n;return x
    def append(xyz,charge=None):
        nonlocal words,draws
        row=raw_units[begin+len(positions)];angle=ur();jitter=ur(0,0x3e99999a)
        assert U(row,284)==defs[index]['pointer']and tuple(struct.unpack_from('<3I',row,316))==xyz==tuple(struct.unpack_from('<3I',row,328))
        assert U(row,396)==angle and U(row,340)==now
        if charge is None:assert U(row,348)==A(now,A(jitter,0))
        else:
            x,y,until=charge;assert(U(row,16),U(row,20),U(row,24),U(row,28),U(row,348))==(1,x,y,until,now);charges.append(Q(row,112))
        positions.append(xyz);new_records.append(row)
    moving=F(A(M(inp['velocity_xy'][0],inp['velocity_xy'][0]),M(inp['velocity_xy'][1],inp['velocity_xy'][1])))>4
    if style==0:
        count=max(1,int(F(M(A(M(minute,B(2.5)),B(12)),B(.6)))))
        for i in range(count):
            xyz=radial(M(D(B(i),B(count)),TAU),range(26,7,-2),True)
            if xyz is not None:append(xyz)
    elif style==3:
        weights=[D(min(B(4),A(M(max(S(minute,d['unlock_bits']),0,key=F),B(.5)),B(1)),key=F),d['cost_bits'])for d in(defs[i]for i in eligible)]
        total=0x80000000
        for w in weights:total=A(total,w)
        residual=ur(0,max(B(.001),total,key=F));index=eligible[0]
        for candidate,w in zip(eligible,weights):
            if F(residual)<F(w):index=candidate;break
            residual=S(residual,w)
        anchor=radial(ur(),range(32,13,-2));count=max(2,int(F(M(A(M(minute,B(.8)),B(5)),B(.6)))))
        if anchor is not None:
            for i in range(count):
                angle=M(B(i),B(2.4));r=A(M(SQ(B(i)),B(1.6)),B(1));xyz=probe(A(anchor[0],M(trig(angle,True),r)),A(anchor[1],M(trig(angle),r)))
                if xyz is None:stats['pack_anchor_fallback']+=1
                append(anchor if xyz is None else xyz)
    else:
        count=max(1,int(F(M(A(A(minute,minute),B(10)),B(.6)))))
        if style==1:
            index=max(cheap,key=lambda i:(F(defs[i]['field52_bits']),i))
            if moving:
                output,words=rng(words);draws+=1;theta=A(A(atan2(inp['velocity_xy'][1],inp['velocity_xy'][0]),0x3fc8f5c3 if output&0x80000000 else 0xbfc8f5c3),ur(0xbecccccd,0x3ecccccd))
            else:theta=ur()
            anchor=radial(A(theta,0x40490fdb),range(34,13,-2))
            if anchor is not None:
                sine,cosine=trig(theta),trig(theta,True);distance=H(S(anchor[0],origin[0]),S(anchor[1],origin[1]));travel_distance=A(A(distance,distance),B(12));speed=max(M(M(defs[index]['field52_bits'],0x3f866666),0x3fb33333),B(1),key=F);duration=D(travel_distance,speed);columns=(count+1)//2;middle=M(S(B(columns),B(1)),B(.5))
                for i in range(count):
                    rr,cc=divmod(i,columns);lateral=M(S(B(cc),middle),B(2.6));x=S(S(anchor[0],M(sine,lateral)),M(M(cosine,B(rr)),B(3)));y=S(A(anchor[1],M(cosine,lateral)),M(M(sine,B(rr)),B(3)));xyz=probe(x,y)
                    if xyz is not None:append(xyz,(A(xyz[0],M(cosine,travel_distance)),A(xyz[1],M(sine,travel_distance)),A(A(duration,now),B(3))))
        else:
            theta=atan2(inp['velocity_xy'][1],inp['velocity_xy'][0])if moving else ur();start=S(theta,B(1.2))
            for i in range(count):
                angle=A(start,D(M(A(B(i),B(.5)),B(2.4)),B(count)));xyz=radial(angle,range(30,11,-2),True)
                if xyz is not None:append(xyz)
    assert count==label['requested']and index==label['definition_index']and len(positions)==label['successful']
    assert draws==label['wave_draws']and tuple(actual['rng_words'])==words and charges==label['charged_guids']
    assert actual['units']['count']==begin+len(positions)
    stats['independent_geometry_created']+=len(positions);stats['independent_charge_bindings']+=len(charges);stats['wave_draws']+=draws;stats['style'+str(style)]+=1
    return index,begin,new_records

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();out=args.output;out.mkdir(exist_ok=True);began=time.monotonic();counts=Counter();semantic=Counter()
    r=json.loads((RUN/'event-wave135-comparison.json').read_text());assert sha(RUN/'event-wave135-comparison.json')==RECEIPT_SHA and r['differences']==0 and r['source_sha256_before']==r['source_sha256_after']and r['source_files']==97
    frozen=RUN/'source-snapshot';drift=[]
    for n,d in r['source_sha256_before'].items():
        assert sha(frozen/n)==d,n
        if sha(ROOT/n)!=d:drift.append(n)
    assert drift==['reconstruction/core_spec/headless135.py']
    assert sha(ROOT/'reconstruction/core_spec/event_wave135.py')==CORE_SHA
    production,import_edges=frozen_closure(frozen,r['source_sha256_before'])
    assert r['expected_before_original']and r['all_artifacts_and_world_inputs_unchanged']
    for n,d in r['frozen_artifacts'].items():assert sha(RUN/n)==d,n
    for n,d in r['world_inputs'].items():assert sha(Path(n))==d,n
    audit_files=('event-input.json','event-expected.json','event-labels.json','event-results.jsonl','event-prepared.json','event-process-terminal.json','event-owned-process.json','event-wave135-runtime.json','event-stderr.log','event-wave135-comparison.json','manifest.json','event-wave135-static.json')
    audit_sha={n:sha(RUN/n)for n in audit_files}
    prepared=json.loads((RUN/'event-prepared.json').read_text());assert prepared['source_sha256']==r['source_sha256_before']and prepared['artifacts']==r['frozen_artifacts']and prepared['expected_before_original']and prepared['deadline_seconds']==60
    assert sha(SOURCE)==SOURCE_SHA and sha(SNAPSHOT)==SNAPSHOT_SHA
    original=SOURCE.read_bytes();changed=(RUN/'research135-exports.wasm').read_bytes();manifest=json.loads((RUN/'manifest.json').read_text());assert hashlib.sha256(changed).hexdigest()==manifest['module_sha256'];a,b=sections(original),sections(changed)
    assert[k for k,*_ in a]==[k for k,*_ in b]and 8 not in[k for k,*_ in a]
    assert all(original[x:y]==changed[u:v]for(k,x,_,y),(_,u,_,v)in zip(a,b)if k!=7)
    assert exports(changed)==exports(original)+[['research135_spawn_tick',0,947],['research135_event_stack0',3,0]]
    read_static=static_reader(original)
    trace=json.loads((RUN/'event-wave135-static.json').read_text())
    for fn in trace['functions']:
        path=RUN/f"event-{fn['index']}.wat";assert sha(path)==fn['wat_sha256'];assert hashlib.sha256(original[fn['body_start']:fn['body_end']]).hexdigest()==fn['body_sha256']
    constructor=(RUN/'event-1560.wat').read_text();assert'i32.const 255\n                  i32.store8 offset=2674'in constructor and'i32.const 2592\n                  memory.copy'in constructor
    wave=(RUN/'event-947.wat').read_text();assert wave.index('i32.store8 offset=2586')<wave.index('f32.store offset=2424')<wave.index('i32.load offset=2456',wave.index('f32.store offset=2424'))
    cases=json.loads((RUN/'event-input.json').read_text());expected=json.loads((RUN/'event-expected.json').read_text());actual=[json.loads(x)for x in(RUN/'event-results.jsonl').read_text().splitlines()];labels=json.loads((RUN/'event-labels.json').read_text());assert len(cases)==len(expected)==len(actual)==len(labels)==25
    fieldnames=literal(frozen/'reconstruction/core_spec/spawn135_data.py','NORMAL_FIELDS');defs=[dict(zip(fieldnames,row))for row in literal(frozen/'reconstruction/core_spec/spawn135_data.py','NORMALS')[0]];geometry=literal(frozen/'reconstruction/core_spec/spawn_position135_data.py','ZONE_GEOMETRY')[0]
    assert tuple(struct.unpack('<II',read_static(5456016+104,8)))+(U(read_static(5456016+120,4),0),)==geometry
    for d in defs:
        raw=read_static(d['pointer'],72);nameptr,namelen=struct.unpack_from('<2I',raw,16);assert read_static(nameptr,namelen).decode()==d['name']
        assert list(struct.unpack_from('<11I',raw,24))==[d[k]for k in('entry','display','scale_bits','classification','hp_bits','attack_bits','field48_bits','field52_bits','xp','cost_bits','unlock_bits')]and raw[68]==d['elite']
    world=World(cases[0]['world']);messages=literal(frozen/'reconstruction/core_spec/event_wave135.py','MESSAGES135');base_speeds=literal(frozen/'reconstruction/core_spec/opening_entities135.py','BASE_SPEEDS')
    with SNAPSHOT.open('rb')as f:f.seek(14384320);snapshot_locale=f.read(25)
    for c,w,raw,label in zip(cases,expected,actual,labels):
        assert time.monotonic()-began<110,'Read-only audit budget';assert c['id']==w['id']==raw['id']==label['id'];counts['equal_known_values']+=1;result=raw['result'];inp=c['input']
        assert c['world']==cases[0]['world']and inp['last_event2586']==255 and inp['zone']==0 and inp['mode']==0
        assert raw['locale_prestate']==raw['locale_poststate']and bytes.fromhex(raw['locale_prestate']['header'])==snapshot_locale and raw['locale_prestate']['once']==3 and raw['locale_prestate']['effective']==0
        assert result['notifications_count']==0 and result['message_sequence']==c['message_sequence']
        for k,value in result['other_clocks'].items():assert value==dict(c['initial_scalars'])[int(k)]
        before,after=bytes.fromhex(raw['game_before2592_hex']),bytes.fromhex(raw['game_after2592_hex']);assert len(before)==len(after)==2592
        allowed=set(range(1720,1744))|set(range(1784,1796))|set(range(1880,1892))|set(range(2408,2412))|set(range(2416,2428))|set(range(2428,2440))|{2586}
        assert all(x==y or i in allowed for i,(x,y)in enumerate(zip(before,after)));semantic['unchanged_game_bytes_outside_declared_mask']+=2592-len(allowed)
        for o,key in((2352,'now_bits'),(2424,'next_event2424_bits')):assert U(before,o)==inp[key]
        assert before[2586]==255 and after[2586]==result['last_event2586']and U(after,2424)==result['next_event2424_bits']
        index,begin,wave_rows=event_reference(c,label,result,defs,geometry,world,semantic)
        packets=result['packets'];assert len(packets)==len(label['ordinary_requests'])+len(wave_rows)+1 and packets[-1]['opcode']==150
        npc_packets=packets[:-1];all_rows=[bytes.fromhex(x)for x in result['units']['storage']];counter=inp['counter']
        for j,packet in enumerate(npc_packets):
            assert packet['opcode']==169;p=decode169(packet['payload_hex']);counter=(counter+1)&MASK;row=all_rows[c['units']['count']+j];d=next(d for d in defs if d['pointer']==U(row,284));guid=0xf130000000000000|(d['entry']<<24)|(counter&0xffffff)
            assert Q(row,112)==p['guid']==guid and p['variant']==3 and p['xyz']==tuple(struct.unpack_from('<3I',row,316))and p['fields']==npc_fields(guid,d,row,int(c['player_guid']),c['level'])
            yaw=atan2(S(inp['player_xyz_bits'][1],p['xyz'][1]),S(inp['player_xyz_bits'][0],p['xyz'][0]));assert p['yaw']==yaw
            encoded=bytes.fromhex(packet['payload_hex']);at=7+encoded[6].bit_count()+2+8+16+4;assert list(struct.unpack_from('<6I',encoded,at))==list(base_speeds)
            if j<len(label['ordinary_requests']):assert p['guid']==label['ordinary_requests'][j]['guid']and p['xyz']==tuple(label['ordinary_requests'][j]['position_bits'])
            semantic['full169_packet_bindings']+=1
        assert counter==result['counter']and result['counter']==(inp['counter']+len(npc_packets))&MASK
        name=dict(c['locale']['enemy_names']).get('enemy.'+str(defs[index]['entry']),defs[index]['name']).encode();message=dict(c['locale']['messages']).get(messages[label['event']].decode(),messages[label['event']].decode()).encode()
        announcement=bytes((90,))+struct.pack('<II',0,len(name)+1)+name+b'\0'+bytes(8)+struct.pack('<I',len(message)+1)+message+b'\0\0';assert packets[-1]['payload_hex']==announcement.hex();semantic['full150_packet_bindings']+=1
        charged={i for i,row in enumerate(all_rows[:result['units']['count']])if Q(row,112)in label['charged_guids']}
        converted=json.loads(json.dumps(result));converted['units']['storage']=[list(bytes.fromhex(x))for x in result['units']['storage']];converted['pickups']['storage']=[list(bytes.fromhex(x))for x in result['pickups']['storage']]
        strict_compare(w['result'],converted,(),counts,c,{'indices':charged,'expected_units':w['result']['units']['storage'],'active_units_count':result['units']['count']})
        assert result['pickups']['count']==inp['pickups']['count']and result['pickups']['capacity']==len(inp['pickups']['storage'])
        for old,encoded in zip(inp['pickups']['storage'],result['pickups']['storage']):assert bytes.fromhex(encoded)==bytes(c['unknown_poison']if v is None else v for v in old)
        oldc=c['units']['count'];guardians={g['unit_index']:g for g in c['guardians']};timers=[]
        assert len(result['guardian_cooldowns'])==len(c['guardians'])
        for i,old in enumerate(c['units']['storage'][:oldc]):
            row=all_rows[i]
            for o,v in enumerate(old):
                if i in guardians and 68<=o<72:continue
                assert row[o]==(c['unknown_poison']if v is None else v),(c['id'],i,o)
        for owner,observed in zip(c['guardians'],result['guardian_cooldowns']):
            assert owner==observed;row=all_rows[owner['unit_index']];pointer=U(row,68);assert Q(row,112)==int(owner['guid'])and U(row,64)==U(row,72)==owner['capacity']==3 and pointer%4==0 and 0<pointer<r['runtime']['max_memory_bytes']-12
            unit_base,unit_capacity=U(after,1788),U(after,1784);assert pointer+12<=unit_base or pointer>=unit_base+unit_capacity*424
            assert all(pointer+12<=a or pointer>=b for a,b in timers);timers.append((pointer,pointer+12));assert len(owner['timers_bits'])==3
            assert bytes.fromhex(''.join(owner['ability_records44_hex']))==read_static(owner['ability_pointer'],132)and bytes.fromhex(owner['header28_hex'])==read_static(owner['header_pointer'],28)
            assert U(row,76)==owner['ability_pointer']and U(row,80)==3 and U(row,84)==owner['ability_pointer']and U(row,88)==3 and U(row,96)==owner['header_pointer'];semantic['guardian_full_payload_bindings']+=1
        if c['id']==24:
            assert label['natural_elapsed_frames']==600 and label['original_elapsed_frames']==0 and label['full601_original_validated']is False and label['ordinary_draws']==0 and len(c['guardians'])==4
            assert label['original_next2448_bits']==B(60)and label['isolated_next2448_bits']==B(1000)==dict(c['initial_scalars'])[2448]
            assert c['units']['count']==16 and result['units']['count']==24 and result['units']['capacity']==32 and label['wave_draws']==19 and label['event']==0
        counts['packets']+=len(packets);counts['packet_bytes']+=sum(len(bytes.fromhex(p['payload_hex']))for p in packets)
    assert counts['equal_known_values']==r['comparison']['equal_known_values']and counts['explicit_unknown_cells']==r['comparison']['explicit_unknown_cells']and counts['packets']==194 and counts['packet_bytes']==31639,(dict(counts),r['comparison'])
    terminal=json.loads((RUN/'event-process-terminal.json').read_text());rt=json.loads((RUN/'event-wave135-runtime.json').read_text());assert terminal==r['process']and rt==r['runtime'];assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<60 and not terminal['launcher_error']
    assert rt['cases']==rt['fresh_instances']==25 and rt['functions']=={'947':25}and rt['actual_host_calls']==0 and rt['denied_imports']==878 and rt['max_memory_bytes']<=rt['memory_cap_bytes']==268435456 and rt['stack_all_restored']and not rt['locale_once_injected']
    assert all(x['before']==x['after']==1048576 and x['returned']for x in rt['stack_checks'])
    assert audit_sha=={n:sha(RUN/n)for n in audit_files}
    helpers=('scripts/review_event_wave135.py','scripts/review_opening_combat135.py','scripts/review_combat137.py','scripts/review_resource_spawn135.py','scripts/review_battle_shout135.py')
    summary=dict(status='passed_read_only_frozen_wave25_review',version='0.135.1',actual_build='90898d5e3',comparison_sha256=RECEIPT_SHA,cases=25,full947_calls=25,original_executed_by_review=False,production_model_executed_by_review=False,checker_executed_by_review=False,
        frozen_sources_verified=97,frozen_production_sources=production,local_source_import_edges=import_edges,current_source_drift=drift,current_wave_core_sha256=CORE_SHA,all_nonexport_bytes_equal=True,counts=dict(counts),semantic=dict(semantic),static_byte_proofs=read_static.proofs,audited_artifact_sha256=audit_sha,
        snapshot_sha256=SNAPSHOT_SHA,world_inputs=r['world_inputs'],original_process=terminal,current_pid_missing_probe=missing(terminal['pid']),current_pgid_missing_probe=missing(terminal['pgid'],True),
        reviewer_source_sha256={n:sha(ROOT/n)for n in helpers},seconds=time.monotonic()-began,
        limitations=['Ordinary prefix draw/position metadata and independently produced600-frame context are explicit dependencies, not re-executed or newly validated full601',
            'All25 inputs zone0,last2586=255,mode0; repeat-event exclusion, otherzones, noeligible/cheapfallback, noncanonicalnav and cap saturation not new dynamic acceptance',
            'Original snapshot supplies initialized locale/allocator context; query-world124 manually packed independent451 assets; no independent fullWorld/App constructor',
            'Defaultcase2448 intentionally future1000;0full880/0native/0fullgames; historical counters not added'])
    save(out/'review.json',summary);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=summary['status'],counts=dict(counts),semantic=dict(semantic))),flush=True)

if __name__=='__main__':main()
