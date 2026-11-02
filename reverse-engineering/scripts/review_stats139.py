#!/usr/bin/env python3
"""Read-only second-author audit of the frozen full1391542 evidence.

Only this auditor and the Python standard library execute. No production
module, checker, builder, WASM, native target, toolchain, or saved game executes.
Reference arithmetic uses semantic accumulators and current139 original static
data, with no imported production calculations or historical expected results.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import argparse, ast, hashlib, json, math, mmap, os, re, sqlite3, struct, sys, time
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT/'evidence/stats0139-oracle-20261102T020320.478498Z'
PROFILE = ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
ORIGINAL = ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
TRACE = ROOT/'evidence/stats139-static-20261102T015922.236942Z/trace.json'
SHA = '71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
COMPARISON_SHA = '9f667e74d304eed1b36dd56e06c1d17e941ab87e29e558e0dd6b3fec4c316de8'
MASK, ONE, ZERO = 0xffffffff, 0x3f800000, 0

def digest(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def load(path): return json.loads(Path(path).read_text())
def f(w): return struct.unpack('<f', struct.pack('<I', w))[0]
def b(v):
    try: return struct.unpack('<I', struct.pack('<f', v))[0]
    except OverflowError: return 0xff800000 if v < 0 else 0x7f800000
def plus(a, c): return b(f(a)+f(c))
def minus(a, c): return b(f(a)-f(c))
def times(a, c): return b(f(a)*f(c))
def divide(a, c):
    x,y=f(a),f(c)
    if y == 0:
        if x == 0 or math.isnan(x): return 0x7fc00000
        return ((a ^ c) & 0x80000000) | 0x7f800000
    return b(x/y)
def isnan(w): return (w & 0x7fffffff) > 0x7f800000
def low(a, c):
    x = c if isnan(a) else a
    y = x if isnan(c) else c
    return x if f(x)<f(y) else y
def high(a, c):
    x = c if isnan(a) else a
    y = x if isnan(c) else c
    return x if f(x)>f(y) else y
def trunc(w):
    x=f(w)
    return 0 if math.isnan(x) or x<=0 else MASK if x>=MASK else int(x)
def ceil_bits(w):
    x=f(w)
    if not math.isfinite(x) or x==0: return w
    rounded=math.ceil(x)
    return 0x80000000 if rounded==0 and w & 0x80000000 else b(rounded)
def word(raw, o): return struct.unpack_from('<I', raw, o)[0]

def leb(raw,p,signed=False):
    n=s=0
    while True:
        x=raw[p];p+=1;n|=(x&127)<<s;s+=7
        assert s<=35
        if x<128: return (n-(1<<s) if signed and x&64 else n),p
def sections(raw):
    assert raw[:8]==b'\0asm\1\0\0\0';out=[];p=8
    while p<len(raw):
        begin=p;k=raw[p];size,start=leb(raw,p+1);p=start+size
        assert p<=len(raw);out.append((k,begin,start,p))
    return out
def exports(raw):
    _,_,p,end=next(x for x in sections(raw) if x[0]==7);count,p=leb(raw,p);out=[]
    for _ in range(count):
        n,p=leb(raw,p);name=raw[p:p+n].decode();p+=n;kind=raw[p];index,p=leb(raw,p+1);out.append([name,kind,index])
    assert p==end;return out
def function_ids(raw,wanted,expected_imports=882):
    top=sections(raw);_,_,p,end=next(x for x in top if x[0]==2);imports,p=leb(raw,p)
    for _ in range(imports):
        for _ in range(2): n,p=leb(raw,p);p+=n
        assert raw[p]==0;_,p=leb(raw,p+1)
    assert p==end and imports==expected_imports
    _,_,p,end=next(x for x in top if x[0]==1);count,p=leb(raw,p);types=[]
    for _ in range(count):
        assert raw[p]==0x60;n,p=leb(raw,p+1);params=raw[p:p+n].hex();p+=n;n,p=leb(raw,p);results=raw[p:p+n].hex();p+=n;types.append([params,results])
    assert p==end;_,_,p,end=next(x for x in top if x[0]==3);count,p=leb(raw,p);decl=[]
    for _ in range(count): v,p=leb(raw,p);decl.append(v)
    assert p==end;_,_,p,end=next(x for x in top if x[0]==10);count2,p=leb(raw,p);assert count==count2;out={}
    for index in range(imports,imports+count):
        size,start=leb(raw,p);p=start+size
        if index in wanted: out[index]=dict(index=index,signature=types[decl[index-imports]],body_start=start,body_end=p,body_bytes=size,body_sha256=hashlib.sha256(raw[start:p]).hexdigest())
    assert p==end and set(out)==set(wanted);return out
def static_image_reader(raw):
    _,_,p,end=next(x for x in sections(raw) if x[0]==11);count,p=leb(raw,p);ranges=[]
    for _ in range(count):
        flags,p=leb(raw,p);assert flags==0 and raw[p]==65;address,p=leb(raw,p+1,True);assert raw[p]==11
        size,p=leb(raw,p+1);ranges.append((address,p,size));p+=size
    assert p==end;proofs={}
    def read(address,size):
        assert 0<=address and 0<size<=65536;out=bytearray(size);used=[]
        for start,file_start,n in ranges:
            lo,hi=max(address,start),min(address+size,start+n)
            if lo<hi:
                out[lo-address:hi-address]=raw[file_start+lo-start:file_start+hi-start];used.append([lo,hi,file_start+lo-start,file_start+hi-start])
        value=bytes(out);proofs[str(address)+':'+str(size)]=dict(hex=value.hex(),sha256=hashlib.sha256(value).hexdigest(),file_intervals=used)
        return value
    read.proofs=proofs;return read
def literal(path,name):
    tree=ast.parse(path.read_text())
    return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))

def local_edges(source,files):
    declared=set(files);edges=set()
    for name in declared:
        path=source/name
        if path.suffix=='.mjs':
            for rel in re.findall(r"(?:from\s+|import\s*\()['\"](\.[^'\"]+)['\"]",path.read_text()):
                child=str((ROOT/Path(name).parent/rel).resolve().relative_to(ROOT));assert child in declared,(name,child);edges.add((name,child))
            continue
        if path.suffix!='.py': continue
        parts=Path(name).with_suffix('').parts
        for node in ast.walk(ast.parse(path.read_text())):
            modules=[]
            if isinstance(node,ast.Import): modules=[x.name for x in node.names]
            elif isinstance(node,ast.ImportFrom):
                base='.'.join(list(parts[1:-node.level])+([node.module] if node.module else [])) if node.level else node.module or ''
                modules=[base]+[base+'.'+x.name if base else x.name for x in node.names]
            for module in modules:
                if not module: continue
                for folder in ('scripts','reconstruction'):
                    rel=Path(*module.split('.'));p=ROOT/folder/rel.with_suffix('.py');q=ROOT/folder/rel/'__init__.py';child=p if p.is_file() else q if q.is_file() else None
                    if child is None: continue
                    key=str(child.relative_to(ROOT));assert key in declared,(name,key);assert (source/key).is_file();edges.add((name,key))
                    for parent in child.parents:
                        if parent==ROOT/folder: break
                        init=parent/'__init__.py'
                        if init.is_file(): key=str(init.relative_to(ROOT));assert key in declared,(name,key);edges.add((name,key))
    return [list(x) for x in sorted(edges)]

def reference(s,classes,races,semantic):
    """Direct semantic interpretation of1542's ordered numeric source passes;semantic accumulator reference reused,no old results."""
    c=s['class_byte']&255;r=s['race_byte']&255
    hp,armor=classes[c];race=races[r];level_delta=plus(b(s['level']),0xbf800000)
    a=dict.fromkeys(('damage','cooldown','health_extra','crit','crit_power','speed','armor','regen','gold','area','channel1612','v1596','v1620','v1624','health','radius','xp','v1584','v1600','live_scale','regen_hp','damage_armor','damage_excess','cap'),0)
    a.update(damage=plus(times(level_delta,0x3cf5c28f),ONE),crit=0x3d4ccccd,crit_power=0x40000000,speed=ONE,armor=armor,regen=plus(times(level_delta,0x3da3d70a),0x3f4ccccd),gold=ONE,area=ONE,health=ONE,radius=0x41100000,xp=ONE)
    integer=0
    def accum(key,value): a[key]=plus(a[key],value)
    for tag,value in race:
        if tag==7: a['radius']=times(a['radius'],plus(value,ONE))
        else: accum({1:'damage',2:'cooldown',3:'speed',4:'crit',5:'armor',6:'regen',8:'xp',9:'gold',10:'v1584',11:'v1600'}.get(tag,'health'),value)
    passive={1:'cooldown',2:'health_extra',3:'crit',4:'crit_power',5:'speed',6:'armor',7:'regen',9:'gold',10:'area',12:'v1596',13:'v1620',14:'v1624'}
    for e in s['passives']:
        tag,value=e['tag'],e['value_bits']
        if tag==8: a['radius']=times(a['radius'],plus(value,ONE))
        elif tag==11: integer=(integer+value)&MASK
        else: accum(passive.get(tag,'damage'),value)
    adjustment={1:'cooldown',2:'health',3:'crit',4:'crit_power',7:'regen',8:'area',9:'v1596',10:'speed',12:'xp',13:'gold',14:'v1584',15:'v1600',17:'live_scale',19:'channel1612'}
    for e in s['adjustments']:
        tag,value=e['tag']&255,e['value_bits']
        if tag in (16,18): continue
        if tag==5:
            accum('armor',low(value,times(e['definition32_bits'],0x40400000)));accum('health',times(value,0x40800000))
        elif tag==6:
            accum('armor',low(times(value,0x3e23d70a),0x3df5c28f));accum('health',value)
        elif tag==11: a['radius']=times(a['radius'],plus(value,ONE))
        else: accum(adjustment.get(tag,'damage'),value)
    channel=low(a['channel1612'],ONE) if s['adjustments'] else 0
    a['cap']=0x3f19999a
    item=[(e['tag']&255,e['value_bits']) for e in s['item_modifiers']]
    reduction=0x80000000
    for tag,value in item:
        if tag==32: reduction=plus(reduction,value)
    if f(reduction)>0:
        for identifier,rank in s['owned_skills']:
            if identifier=='soul_link':
                if rank&255: item.append((5,times(b(rank&255),0x3c23d70a)));semantic['soul_link_append']+=1
                break
    for e in s['timed_records']:
        if f(e['expires_bits'])<=f(s['now_bits']): semantic['timed_expired']+=1;continue
        i=e['definition_index']
        if i>=len(s['timed_definitions']): semantic['timed_bad_index']+=1;continue
        definition=s['timed_definitions'][i]
        if definition['kind']==27: item.append((definition['modifier_tag']&255,times(definition['value20_bits'],b(e['stack_count']))));semantic['timed_append']+=1
    item_targets={1:'cooldown',2:'health',3:'crit',4:'crit_power',5:'armor',6:'regen',7:'speed',8:'area',10:'xp',11:'gold',12:'v1584',13:'v1596',15:'v1600',23:'live_scale',24:'regen_hp',25:'damage_armor',26:'damage_excess',27:'cap'}
    for tag,value in item:
        if tag in (14,16,17,18,19,20,21,22,28,29,30,31,32): continue
        if tag==9: a['radius']=times(a['radius'],plus(value,ONE))
        else: accum(item_targets.get(tag,'damage'),value)
    scale=plus(a['live_scale'],ONE);accepted=[]
    for i,e in enumerate(s['live_effects']):
        if f(e['expires_bits'])<=f(s['now_bits']): continue
        current=e['value_bits'] if e['kind'] in (8,9) else ZERO;dominated=False
        for j,other in enumerate(s['live_effects']):
            if i==j or e['spell_id']!=other['spell_id'] or other['spell_id']==774 or not f(other['expires_bits'])>f(s['now_bits']): continue
            competing=other['value_bits'] if other['kind'] in (8,9) else ZERO
            if f(competing)>f(current) or j<i and f(competing)==f(current): dominated=True;break
        if dominated: semantic['live_dominated']+=1;continue
        accepted.append(i)
        if e['kind'] in (8,9): accum('damage' if e['kind']==8 else 'cooldown',times(scale,e['value_bits']))
        if e['spell_id']==23451: accum('speed',0x3f19999a)
        elif e['spell_id']==23505: accum('damage',0x3f000000)
    base_hp=plus(hp,times(level_delta,0x41100000));max_hp=times(plus(base_hp,a['health_extra']),a['health']);excess_crit=f(a['crit'])>1
    speed_multiplier=low(a['speed'],0x400ccccd);armor=low(a['armor'],a['cap'])
    derived={1536:max_hp,1540:plus(plus(divide(times(a['damage_armor'],armor),0x41200000),times(a['damage_excess'],high(minus(a['armor'],a['cap']),ZERO))),a['damage']),1544:divide(ONE,plus(a['cooldown'],ONE)),1548:ONE if excess_crit else a['crit'],1552:plus(a['crit_power'],plus(a['crit'],0xbf800000)) if excess_crit else a['crit_power'],1556:speed_multiplier,1560:a['radius'],1564:a['xp'],1568:armor,1572:a['cap'],1576:plus(times(a['regen_hp'],max_hp),a['regen']),1580:a['area'],1584:plus(a['v1584'],s['conditional268_bits']) if s['flag2574']&255 else a['v1584'],1588:a['gold'],1592:integer,1596:a['v1596'],1600:a['v1600'],1604:a['live_scale'],1608:min(((trunc(level_delta)+1)&MASK)//15,3),1612:channel,1616:plus(divide(max_hp,high(base_hp,ONE)),0xbf800000),1620:a['v1620'],1624:a['v1624']}
    hp_delta=minus(max_hp,s['old_max_hp_bits']);current=low(plus(hp_delta,s['current_hp_bits']) if f(hp_delta)>0 else s['current_hp_bits'],max_hp)
    pool=high(low(s['pool1536_bits'],s['pool1532_bits']),ZERO);excess=high(minus(pool,max_hp),ZERO)
    aux={'1444':s['pool1532_bits'],'1448':minus(pool,excess),'1348':s['conditional1348_bits'],'764':s['pool768_bits']}
    if f(excess)>0:
        semantic['pool_excess_branch']+=1;aux['1444']=high(minus(s['pool1532_bits'],excess),ZERO)
        if s['conditional1344_id']==11426: aux['1348']=low(s['conditional1348_bits'],aux['1448']);semantic['conditional_pool_clamps']+=1
        aux['764']=low(s['pool768_bits'],aux['1444'])
    speed=times(speed_multiplier,0x40e00000);changed=f(minus(speed,s['previous_speed_bits'])&0x7fffffff)>f(0x3c23d70a)
    return dict(derived_bits={str(k):v for k,v in sorted(derived.items())},current_hp_bits=current,auxiliary_bits=aux,object_fields={'22':trunc(ceil_bits(high(current,ZERO))),'28':trunc(ceil_bits(max_hp)),'1109':times(derived[1548],0x42c80000)},speed_bits=speed if changed else s['previous_speed_bits'],speed_changed=changed,accepted_live_indices=accepted)

def scalar_equal(want,got,integer,path,counters):
    assert type(want)is int and type(got)is int and 0<=want<=MASK and 0<=got<=MASK,(path,want,got)
    if not integer:
        counters['nan_category_comparisons']+=isnan(want) or isnan(got)
        counters['signed_negative_zero_values']+=want==0x80000000
    if want!=got:
        assert not integer and isnan(want) and isnan(got),(path,want,got)
        counters['nan_payload_differences']+=1
    counters['strict_integer_values' if integer else 'float_values']+=1
    counters['compared_values']+=1

def process_missing(pid,group=False):
    try: (os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError: return True
    except PermissionError: return None
    return False

def static_bounds(raw):
    _,_,p,end=next(x for x in sections(raw)if x[0]==11);n,p=leb(raw,p);ranges=[]
    for _ in range(n):
        flag,p=leb(raw,p);assert flag==0 and raw[p]==65;address,p=leb(raw,p+1,True);assert raw[p]==11
        size,p=leb(raw,p+1);ranges.append((address,address+size));p+=size
    assert p==end;return min(a for a,b in ranges),max(b for a,b in ranges)

def numeric_prefix(text,bounds):
    """Independent alpha/data-relocation normal form,not runtime acceptance.

    Only the instructions before the first BTree lookup are compared. They
    include all seven numeric sources, derived/current/pool/speed writes and
    the HP-key expression. BTree tail code-generation is checked separately.
    """
    lines=[x.strip()for x in text.splitlines()][2:]
    lines=lines[:lines.index('i32.load offset=2476')]
    frame=int(lines[3].split()[-1]);assert frame in(4,5)
    aliases={frame:'frame',9-frame:'temporary'}
    normalized=[];callee={}
    for line in lines:
        m=re.fullmatch(r'local\.(get|set|tee) ([45])',line)
        if m:line='local.'+m[1]+' '+aliases[int(m[2])]
        m=re.fullmatch(r'call (\d+)',line)
        if m:
            index=int(m[1]);callee.setdefault(index,len(callee));line='call ordered_callee'+str(callee[index])
        m=re.fullmatch(r'(i32.const |i32.load offset=)(\d+)',line)
        if m and bounds[0]<=int(m[2])<bounds[1]:line=m[1]+'relocated_static_address'
        normalized.append(line)
    at=normalized.index('i32.load offset=1700');count=normalized[at+1].split()[-1]
    assert normalized[at+1].startswith('local.tee ')and normalized[at+2]=='i32.eqz'
    end=next(j for j in range(at+3,at+30)if normalized[j:j+3]==['i32.const 3','i32.shl','local.set 2'])
    normalized[at+1]='local.tee passive_count'
    assert normalized[end-1]=='local.get '+count;normalized[end-1]='local.get passive_count'
    at=normalized.index('i32.const 23451');spell=normalized[at-1].split()[-1]
    assert normalized[at-1].startswith('local.tee ')and normalized[at+3]=='local.get '+spell and normalized[at+4]=='i32.const 23505'
    normalized[at-1]='local.tee special_spell';normalized[at+3]='local.get special_spell'
    return normalized,dict(frame_local=frame,passive_count_local=count,special_spell_local=spell,ordered_callees=callee)

def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def imports_of(raw):
    _,_,p,end=next(x for x in sections(raw)if x[0]==2);n,p=leb(raw,p);result=[]
    for _ in range(n):
        values=[]
        for _ in range(2):size,p=leb(raw,p);values.append(raw[p:p+size].decode('utf8'));p+=size
        assert raw[p]==0;index,p=leb(raw,p+1);result.append(dict(module=values[0],name=values[1],type_index=index))
    assert p==end and len(result)==882;return result
def bind_wat(profile,filename,identities,out):
    values={};proof={}
    with sqlite3.connect((profile/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(profile/filename).open('rb')as stream:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
        for index,identity in identities.items():
            row=dict(db.execute('select * from functions where idx=?',(index,)).fetchone())
            assert all(row[k]==identity[k]for k in('body_start','body_end','body_bytes'))
            stream.seek(row['wat_start']);wat=stream.read(row['wat_end']-row['wat_start']);assert len(wat)<=2*1024*1024
            (out/'static').mkdir(exist_ok=True);(out/'static'/f'{index}.wat').write_bytes(wat)
            values[index]=wat.decode();proof[index]=dict(**identity,wat_bytes=len(wat),wat_sha256=hashlib.sha256(wat).hexdigest(),wat_start=row['wat_start'],wat_end=row['wat_end'])
    return values,proof

def current_static_contract(original,manifest,out):
    trace=load(TRACE);assert digest(TRACE)=='557b4841cd3043f229b7c7f0f7f10315c210d5935476c4b8f8b9701e5e6c6125'and trace['source_sha256']==SHA
    indices={x['index']for x in trace['functions']}|{93344};ids=function_ids(original,indices)
    wat,proof=bind_wat(PROFILE,'official-0.139.0-full.wat',ids,out)
    for record in trace['functions']:
        f=proof[record['index']]
        assert f['signature']==[record['params_hex'],record['results_hex']]and f['body_sha256']==record['body_sha256']and f['wat_sha256']==record['wat_sha256']
    assert ids[1542]['signature']==['7f','']and ids[1542]['body_sha256']=='43d5e3cd844d1cf156dd0cb058dc05c0a33ce41280649000a7a2b2d3a8f0a72c'and ids[1542]['body_bytes']==4745
    assert ids[93344]['signature']==['7f7f','7f']
    assert wat[1542].encode()==(RUN/'1542.wat').read_bytes();text=wat[1542];lines=[x.strip()for x in text.splitlines()]
    actual_calls=Counter(int(x.split()[1])for x in lines if re.fullmatch(r'call \d+',x));assert actual_calls==Counter({x['callee']:x['sites']for x in manifest['full_direct_callees']})
    assert len(actual_calls)==8 and actual_calls==Counter({48967:1,52397:3,66546:1,66553:2,73034:1,81897:1,108362:1,109316:1})
    for guard in trace['guards']:
        locations=[i+1 for i in range(len(lines)-len(guard['instructions'])+1)if lines[i:i+len(guard['instructions'])]==guard['instructions']]
        assert locations==guard['sites']
    expected_headers=dict(passives=[1692,1696,1700,8],adjustments=[1668,1672,1676,16],items=[2024,2028,2032,8],owned=[168,172,176,8],timed_definitions=[2048,2052,2056,36],timed_records=[592,596,600,12],live=[1704,1708,1712,32])
    assert manifest['source_headers']==trace['seven_source_headers']==expected_headers
    for cap,ptr,n,stride in expected_headers.values():assert f'i32.load offset={ptr}'in lines and f'i32.load offset={n}'in lines
    assert all(t in text for t in('f32.load offset=764','f32.store offset=764','f32.store offset=1572','f32.store offset=1648','call 48967'))
    assert all(t not in text for t in('f32.load offset=768','f32.store offset=768','i32.load offset=604'))
    # Static reuse is distinct from transferring historical test acceptance.
    old=ROOT/'originals/official-release-20261101T201508.341687Z/latest-wenilla_bg.wasm';oldraw=old.read_bytes()
    assert hashlib.sha256(oldraw).hexdigest()=='c60161d991ce97a9a4a9d3866b5e629d9e38f0fab8364c051faae8d01945b11b'
    oldids=function_ids(oldraw,{1512},878);oldwat,oldproof=bind_wat(ROOT/'evidence/wasm0138-profile-20261101T202038.814151Z','official-0.138.0-full.wat',oldids,out)
    left,lp=numeric_prefix(oldwat[1512],static_bounds(oldraw));right,rp=numeric_prefix(text,static_bounds(original));assert left==right and len(right)==1959
    prefix=dict(current_instructions=len(right),normalized_sha256=hashlib.sha256('\n'.join(right).encode()).hexdigest(),old_alpha=lp,current_alpha=rp,historical_static_body=oldproof[1512],historical_runtime_results_read=False)
    # Current139 BTree temporary writes low0/highlocal2 as two little-endian
    # words. Freeze the three exact sites; no full-node heap model is implied.
    pattern=['local.get 4','local.get 2','i32.store offset=24','local.get 4','i32.const 0','i32.store offset=20']
    pairs=[i+1 for i in range(len(lines)-len(pattern)+1)if lines[i:i+len(pattern)]==pattern];assert len(pairs)==3
    assert all(f'i32.const {k}'in lines for k in(22,28,1109))and 'f32.ceil'in lines and 'i32.trunc_sat_f32_u'in lines
    read=static_image_reader(original);classes={};races={};declarations=[]
    for selector in range(256):
        delta=(selector-2)&255;cp=word(read(1601376+delta*4,4),0)if delta<=9 else 5877920
        classes[selector]=struct.unpack('<2I',read(cp+72,8))
        rp0=word(read(1601216+delta*4,4),0)if delta<=6 else 5874636
        ptr,n=struct.unpack('<2I',read(rp0+16,8));assert n<=16
        races[selector]=list(struct.iter_unpack('<2I',read(ptr,n*8)))if n else[]
        if selector in(1,2,3,4,5,7,8,9,11):declarations.append(dict(domain='class',selector=selector,pointer=cp,hp_bits=classes[selector][0],armor_bits=classes[selector][1],scalar8_hex=read(cp+72,8).hex()))
        if 1<=selector<=8:declarations.append(dict(domain='race',selector=selector,pointer=rp0,modifier_pointer=ptr,modifier_count=n,raw_modifiers8_hex=read(ptr,n*8).hex()if n else'',modifiers=[list(x)for x in races[selector]]))
    assert sorted(declarations,key=lambda r:(r['domain'],r['selector']))==sorted(trace['declarations'],key=lambda r:(r['domain'],r['selector']))
    constants=literal(RUN/'source-snapshot/reconstruction/core_spec/derived_stats139.py','CLASS_HP_ARMOR');racial=literal(RUN/'source-snapshot/reconstruction/core_spec/derived_stats139.py','RACE_MODIFIERS')
    assert constants=={k:classes[k]for k in constants}and racial=={k:tuple(races[k])for k in racial}
    assert sum(len(races[k])for k in range(1,9))==14
    artifact=dict(functions=proof,current_source_headers=expected_headers,current_data=declarations,current_data_read_proofs=read.proofs,numeric_prefix=prefix,current_BTree_two_word_sites=pairs,native_execution=False)
    save(out/'static-proof.json',artifact);return classes,races,artifact

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();out=args.output.resolve();assert out.is_relative_to((ROOT/'evidence').resolve())and not out.is_relative_to(RUN);out.mkdir();began=time.monotonic()
    auditor=digest(Path(__file__));(out/'auditor.py').write_bytes(Path(__file__).read_bytes())
    c=load(RUN/'comparison.json');m=load(RUN/'manifest.json');p=load(RUN/'prepared.json');runtime=load(RUN/'runtime.json');terminal=load(RUN/'process-terminal.json');handoff=load(RUN/'task-handoff.json')
    assert digest(RUN/'comparison.json')==COMPARISON_SHA and digest(RUN/'task-handoff.json')=='d4875aaed1f2b90f887c8a1a8470028e56ba9add77021a06a34ca766ec1d1ecf'
    files=c['source_sha256_before'];source=RUN/'source-snapshot';assert files==c['source_sha256_after']==p['source_sha256']and len(files)==13
    for n,h in files.items():assert digest(source/n)==digest(ROOT/n)==h,n
    edges=local_edges(source,files);assert edges==c['source_import_edges']==p['source_import_edges']and len(edges)==19
    production={n for n in files if n.startswith('reconstruction/')};seen=set();todo=['reconstruction/core_spec/derived_stats139.py']
    while todo:
        name=todo.pop()
        if name in seen:continue
        seen.add(name);todo.extend(b for a,b in edges if a==name)
    assert seen==production and len(production)==5
    for name in production:
        for node in ast.walk(ast.parse((source/name).read_text())):
            if isinstance(node,ast.Call):
                fn=node.func;label=fn.id if isinstance(fn,ast.Name)else fn.attr if isinstance(fn,ast.Attribute)else''
                assert label not in('open','read_text','read_bytes','write_text','write_bytes','Popen','eval','exec','__import__','import_module'),(name,label)
    for row in handoff['files']:assert digest(ROOT/row['path'])==row['sha256']and(ROOT/row['path']).stat().st_size==row['bytes']
    assert len(handoff['files'])==7
    assert c['frozen_artifacts']==p['artifacts']
    for name,h in c['frozen_artifacts'].items():assert digest(RUN/name)==h
    artifacts={n:digest(RUN/n)for n in('comparison.json','manifest.json','prepared.json','runtime.json','process-terminal.json','owned-process.json','validator-terminal.json','validation.stdout','validation.stderr','stdout.jsonl','stderr.log','expected.json','fixtures.jsonl','1542.wat','stats139-original-exports.wasm','task-handoff.json','differences.json')}
    assert artifacts['stdout.jsonl']==c['output_sha256']and artifacts['stderr.log']==c['stderr_sha256']and artifacts['runtime.json']==c['runtime_sha256']
    original=ORIGINAL.read_bytes();changed=(RUN/m['module_file']).read_bytes();assert len(original)==92511151 and hashlib.sha256(original).hexdigest()==m['original_sha256']==SHA and digest(RUN/m['module_file'])==m['module_sha256']
    old,new=sections(original),sections(changed);assert[x[0]for x in old]==[x[0]for x in new]and not any(x[0]==8 for x in old)
    assert all(original[a:b]==changed[u:v]for(k,a,_,b),(_,u,_,v)in zip(old,new)if k!=7)
    assert exports(original)==m['original_exports']and exports(changed)==exports(original)+[['research139_stats1542',0,1542],['research139_stats_stack0',3,0]]and ['__wbindgen_malloc',0,93344]in exports(original)
    imported=imports_of(original);assert imported==m['original_imports'];surface=[dict(module=x['module'],name=x['name'],kind='function')for x in imported]
    assert surface==runtime['denied_import_surface']and hashlib.sha256(json.dumps(surface,separators=(',',':')).encode()).hexdigest()==runtime['denied_import_surface_sha256']
    classes,races,static=current_static_contract(original,m,out);del original,changed
    checker=(source/'scripts/check_stats139.py').read_text();runner=(source/'scripts/run_stats139_oracle.mjs').read_text()
    assert checker.index("save(out/'expected.json',expected)")<checker.index('subprocess.Popen(')and c['expected_before_original']and not c['historical_outputs_used']and not c['old_results_transferred']
    assert p['historical_expected_or_actual_read']is False and p['template_controlled_input_sha256']==c['controlled_template_sha256']==artifacts['fixtures.jsonl']=='362dd58da9b1b201535c9e0334b212ddc0bc03f84887cac2a039c9188ccb2c09'
    assert 'call(1542,e.research139_stats1542,G)'in runner and 'calls%32===0'in runner and 'bytes().fill(0,p,p+n)'in runner
    assert runtime==c['runtime']and terminal==c['process']and terminal['exit_code']==0 and terminal['error']is None and terminal['pid_missing']and terminal['pgid_missing']and process_missing(terminal['pid'])and process_missing(terminal['pgid'],True)
    facts=dict(version='0.139.0',actual_build='f79c5e2b4',cases=10569,completed_cases=10569,full1542_calls=10569,fresh_instances=331,actual_host_calls=0,denied_imports=882,memory_cap_bytes=33554432,heap_cap_mib=512,stack_guards=101736,stack_all_restored=True,original_function_bodies_unchanged=True,network_used=False,user_saves_accessed=False,original_snapshot_loaded=False,error=None)
    for key,value in facts.items():assert runtime[key]==value,(key,runtime[key],value)
    assert runtime['peak_memory_bytes']==15007744 and runtime['output_bytes']==(RUN/'stdout.jsonl').stat().st_size and(RUN/'stderr.log').stat().st_size==0
    assert runtime['stats_stack_returns']==[dict(case=i,before=1048576,after=1048576,returned=True)for i in range(10569)]
    expected=load(RUN/'expected.json');assert len(expected)==10569;counts=Counter();semantic=Counter();groups=Counter();stack_guards=0;headers=Counter()
    with(RUN/'fixtures.jsonl').open('rb')as fixtures,(RUN/'stdout.jsonl').open('rb')as actuals:
        for index,(left,right)in enumerate(zip(fixtures,actuals,strict=True)):
            assert len(left)<=32768 and len(right)<=16384 and left.endswith(b'\n')and right.endswith(b'\n')and time.monotonic()-began<180
            fixture=json.loads(left);actual=json.loads(right);want=expected[index];assert fixture['id']==actual['id']==want['id']==index;groups[fixture['group']]+=1;s=fixture['input']
            prediction=reference(s,classes,races,semantic);model=want['result'];assert set(prediction)==set(model)
            temp=Counter()
            for name in('derived_bits','auxiliary_bits','object_fields'):
                assert set(prediction[name])==set(model[name])==set(actual[name])
                for key,value in prediction[name].items():
                    integer=name=='object_fields'and key in('22','28')or name=='derived_bits'and key in('1592','1608')
                    scalar_equal(value,model[name][key],integer,(index,'expected',name,key),temp);scalar_equal(value,actual[name][key],integer,(index,'original',name,key),counts)
            for key in('current_hp_bits','speed_bits'):
                scalar_equal(prediction[key],model[key],False,(index,'expected',key),temp);scalar_equal(prediction[key],actual[key],False,(index,'original',key),counts)
            assert prediction['speed_changed']==model['speed_changed']and prediction['accepted_live_indices']==model['accepted_live_indices']
            changed=int(prediction['speed_changed']);assert actual['speed_sequence']==actual['movement_queue_count']==changed
            counts['compared_values']+=2;counts['strict_integer_values']+=2;counts['movement_queue_entries']+=changed;counts['cases']+=1
            game=bytes.fromhex(actual['raw_game2592_hex']);assert len(game)==2592;counts['raw_Game_bytes_field_bound']+=len(game)
            for name in('derived_bits','auxiliary_bits'):
                for offset,value in actual[name].items():assert word(game,int(offset))==value
            for key,offset in(('current_hp_bits',1440),('speed_bits',1648),('speed_sequence',1644),('movement_queue_count',1888)):assert word(game,offset)==actual[key]
            assert game[360]==s['class_byte']&255 and game[361]==s['race_byte']&255 and game[2582]==s['flag2574']&255
            for key,offset in(('level',1432),('now_bits',2352),('conditional268_bits',268),('conditional1344_id',1344)):assert word(game,offset)==s[key]
            assert int.from_bytes(game[1336:1344],'little')==1 and word(game,2476)>0 and word(game,2480)==0
            for key,offset in(('passives',1692),('adjustments',1668),('item_modifiers',2024),('owned_skills',168),('timed_definitions',2048),('timed_records',592),('live_effects',1704)):
                cap,ptr,n=struct.unpack_from('<3I',game,offset);assert cap==n==len(s[key])and ptr>0;counts['source_vector_headers']+=1
            capacity,pointer,n=struct.unpack_from('<3I',game,1880);assert n==changed and n<=capacity and pointer>0
            if not changed:assert(capacity,pointer,n)==(0,4,0)
            headers[str(capacity)]+=1
            stack_guards+=9+len(s['adjustments'])+2*len(s['owned_skills'])
    assert dict(groups)==c['groups']and counts['cases']==c['cases']==c['original1542_calls']==10569
    assert counts['compared_values']==c['counts']['compared_values']==359346 and counts['movement_queue_entries']==c['counts']['actual_movement_packets']==1537
    assert counts['source_vector_headers']==73983 and counts['raw_Game_bytes_field_bound']==27394848 and stack_guards==runtime['stack_guards']==101736
    assert counts['nan_category_comparisons']>0 and counts['signed_negative_zero_values']>0 and c['differences']==0
    for n,h in files.items():assert digest(ROOT/n)==digest(source/n)==h
    for row in handoff['files']:assert digest(ROOT/row['path'])==row['sha256']
    for n,h in artifacts.items():assert digest(RUN/n)==h
    assert digest(Path(__file__))==auditor
    result=dict(status='scoped_fresh139_full1542_independent_read_only_review_passed',version='0.139.0',actual_build='f79c5e2b4',original_sha256=SHA,comparison=str((RUN/'comparison.json').relative_to(ROOT)),comparison_sha256=COMPARISON_SHA,cases=10569,full1542_calls_in_frozen_batch=10569,new_original_calls=0,production_imports=0,production_executions=0,checker_builder_tracer_executions=0,differences=0,source_count=13,production_sources=5,local_import_edges=19,sources=files,handoff_files=7,handoff_sha256=artifacts['task-handoff.json'],auditor_source='scripts/review_stats139.py',auditor_sha256=auditor,counts=dict(counts),semantic_counts=dict(semantic),groups=dict(groups),movement_queue_capacity_observations=dict(headers),stack_guards_independently_counted=stack_guards,static_function_proof=static['functions'],numeric_prefix_proof=static['numeric_prefix'],static_proof_sha256=digest(out/'static-proof.json'),current139_class_race_data_reextracted=True,current_class_records=9,current_race_records=8,current_race_modifier_entries=14,seven_explicit_source_headers=static['current_source_headers'],only_export7_changed=True,all_eight_actual_callees_preserved=True,allocator=93344,entry=1542,physical_timed_pointer_count=[596,600],reserve_offset=764,armor_cap1572_single_ordered_accumulator=True,old_runtime_acceptance_transferred=False,pilot12_added=False,runtime={k:v for k,v in runtime.items()if k not in('stats_stack_returns','denied_import_surface')},process=terminal,artifacts=artifacts,seconds=time.monotonic()-began,full880_frames=0,native_executions=0,complete_games=0,limitations=['All10569 current139 original calls were already recorded; this review replays immutable evidence without executing original/production/checker/builder/tracer.','Semantic accumulator reference code is reused,not historical expected/actual/pass status. Current139 full1959-instruction numeric prefix is independently re-normalized and every139 class/race lookup is newly extracted before recalculation.','NaN float outputs match by classification only; finite/infinite values,signed zeros and integer fields match exact words.','Raw Game2592 is bound fieldwise,including73983 seven-source headers; no whole image or source backing/heap/BTree layout equality claim.','1537 counts actual movement queue entries only; payload bytes,physical backing and network delivery were not captured or independently recovered.','Explicit seven source snapshots are synthetic controlled inputs; natural profile/equipment/talent/live producers and constructor139/full flow remain separate work.','The12-case pilot is not added; fixed135/138 acceptance and native Windows execution/layout receive no transferred runtime credit.'])
    save(out/'review.json',result);print(json.dumps(dict(output=str(out/'review.json'),sha256=digest(out/'review.json'),cases=10569,counts=dict(counts),seconds=result['seconds'])),flush=True)

if __name__=='__main__':main()
