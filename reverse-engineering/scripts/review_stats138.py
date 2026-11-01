#!/usr/bin/env python3
"""Read-only second-author audit of the frozen full1381512 evidence.

Only this auditor and the Python standard library execute. No production
module, checker, builder, WASM, native target, toolchain, or saved game executes.
Reference arithmetic uses semantic accumulators and current138 original static
data, with no imported production calculations or historical expected results.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import ast, hashlib, json, math, mmap, os, re, sqlite3, struct, sys, time
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT/'evidence/stats0138-oracle-20261101T231303.006206Z'
PROFILE = ROOT/'evidence/wasm0138-profile-20261101T202038.814151Z'
ORIGINAL = ROOT/'originals/official-release-20261101T201508.341687Z/latest-wenilla_bg.wasm'
CORE = ROOT/'evidence/flow135-to138-core-static-20261101T230745.455530Z'
SHA = 'c60161d991ce97a9a4a9d3866b5e629d9e38f0fab8364c051faae8d01945b11b'
COMPARISON_SHA = 'eda066a0d8b059c1f9526a6c31119ee775512c2c1dc448317aadf060efd61e19'
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
def function_ids(raw,wanted):
    top=sections(raw);_,_,p,end=next(x for x in top if x[0]==2);imports,p=leb(raw,p)
    for _ in range(imports):
        for _ in range(2): n,p=leb(raw,p);p+=n
        assert raw[p]==0;_,p=leb(raw,p+1)
    assert p==end and imports==878
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
    """Direct semantic interpretation of1512's ordered numeric source passes."""
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

def main():
    began=time.monotonic();out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('stats138-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    comparison=load(RUN/'comparison.json');manifest=load(RUN/'manifest.json');prepared=load(RUN/'prepared.json');runtime=load(RUN/'runtime.json');terminal=load(RUN/'process-terminal.json');handoff=load(RUN/'task-handoff.json')
    assert digest(RUN/'comparison.json')==COMPARISON_SHA and digest(RUN/'task-handoff.json')=='bbfbce79a70025f69ecfd37d39729db95a54894c1037bccdb7c4cc7efc1c1415'
    assert comparison['source_sha256_before']==comparison['source_sha256_after']==prepared['source_sha256']
    source=RUN/'source-snapshot';files=comparison['source_sha256_before'];assert len(files)==22
    for name,value in files.items(): assert digest(ROOT/name)==value==digest(source/name),name
    assert local_edges(source,files)==comparison['source_import_edges']==prepared['source_import_edges'];assert len(comparison['source_import_edges'])==35
    production=[n for n in files if n.startswith('reconstruction/')];assert len(production)==8
    reachable=set();todo=['reconstruction/core_spec/derived_stats138.py','reconstruction/core_spec/flow138_contract.py']
    while todo:
        name=todo.pop()
        if name in reachable: continue
        reachable.add(name);todo.extend(b for a,b in comparison['source_import_edges'] if a==name)
    assert reachable==set(production),('production transitive import closure',reachable,production)
    forbidden=[]
    for name in production:
        for node in ast.walk(ast.parse((source/name).read_text())):
            if isinstance(node,ast.Call):
                fn=node.func;label=fn.id if isinstance(fn,ast.Name) else fn.attr if isinstance(fn,ast.Attribute) else ''
                if label in ('open','read_text','read_bytes','write_text','write_bytes','Popen','eval','exec','__import__','import_module'): forbidden.append([name,label])
    assert not forbidden
    assert comparison['frozen_artifacts']==prepared['artifacts']
    for name,value in comparison['frozen_artifacts'].items(): assert digest(RUN/name)==value,name
    for name,value in handoff['new_files'].items(): assert digest(ROOT/name)==value,name
    assert len(handoff['new_files'])==13
    original=ORIGINAL.read_bytes();module=(RUN/manifest['module_file']).read_bytes()
    assert len(original)==90946299 and hashlib.sha256(original).hexdigest()==manifest['original_sha256']==SHA
    assert original.count(b'382771e6c')==4
    top,new=sections(original),sections(module);assert [x[0] for x in top]==[x[0] for x in new] and not any(x[0]==8 for x in top)
    assert all(original[a:e]==module[b:z] for (k,a,_,e),(_,b,_,z) in zip(top,new) if k!=7)
    assert exports(original)==manifest['original_exports'] and exports(module)==exports(original)+[['research138_stats1512',0,1512],['research138_stats_stack0',3,0]]
    assert ['__wbindgen_malloc',0,92072] in exports(original) and manifest['allocator_index']==92072
    roles=literal(ROOT/'reconstruction/core_spec/flow138_contract.py','ROLES')|literal(ROOT/'reconstruction/core_spec/flow138_consumers_contract.py','ROLES');assert len(roles)==13
    for name in ('flow138_contract.py','flow138_consumers_contract.py'):
        assert literal(ROOT/'reconstruction/core_spec'/name,'STATIC_GUARDS_ARE_RUNTIME_ACCEPTANCE') is False
    identities=function_ids(original,{v[0] for v in roles.values()}|{92072})
    for role,(index,params,results,h) in roles.items(): assert identities[index]['signature']==[params,results] and identities[index]['body_sha256']==h,role
    assert identities[1512]['body_sha256']==manifest['entry']['body_sha256'] and identities[1512]['body_bytes']==4756
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as c:
        c.row_factory=sqlite3.Row;indexed={i:dict(c.execute('select * from functions where idx=?',(i,)).fetchone()) for i in identities}
    wat_path=PROFILE/'official-0.138.0-full.wat'
    with wat_path.open('rb') as stream:
        slices={}
        for i,item in indexed.items():
            for k in ('body_start','body_end','body_bytes'): assert item[k]==identities[i][k]
            stream.seek(item['wat_start']);slices[i]=stream.read(item['wat_end']-item['wat_start'])
    assert slices[1512]==(RUN/'1512.wat').read_bytes()
    wat=slices[1512].decode();assert 'i32.load offset=596' in wat and 'i32.load offset=600' in wat and 'f32.load offset=764' in wat and 'f32.store offset=764' in wat
    assert all(x not in wat for x in ('i32.load offset=604','f32.load offset=768','f32.store offset=768'))
    runner=(source/'scripts/run_stats138_oracle.mjs').read_text();checker=(source/'scripts/check_stats138.py').read_text();builder=(source/'scripts/build_stats138_oracle.py').read_text()
    assert 'await WebAssembly.instantiate(module,bindings)' in runner and 'research138_stats1512' in runner and '92072' in runner
    # Source ordering is provenance evidence, not a cryptographically signed timeline.
    assert checker.index("save(out/'expected.json',expected)")<checker.index('subprocess.Popen(')
    assert comparison['expected_before_original'] and not comparison['old_results_transferred']
    read=static_image_reader(original);classes={};races={};class_records=[];race_records=[]
    for selector in range(256):
        cp=word(read(1597616+((selector-2)&255)*4,4),0) if ((selector-2)&255)<=9 else 1673176
        classes[selector]=struct.unpack('<2I',read(cp+72,8))
        rp=word(read(1597456+((selector-2)&255)*4,4),0) if ((selector-2)&255)<=6 else 1669892
        ptr,count=struct.unpack('<2I',read(rp+16,8));assert count<=16;races[selector]=list(struct.iter_unpack('<2I',read(ptr,count*8))) if count else []
        if 1<=selector<=11: class_records.append(dict(class_byte=selector,pointer=cp,HP72_bits=classes[selector][0],armor76_bits=classes[selector][1]))
        if 1<=selector<=8: race_records.append(dict(race_byte=selector,pointer=rp,modifiers_pointer=ptr,count=count,modifier8_hex=read(ptr,count*8).hex() if count else ''))
    mapping=load(CORE/'mapping.json');assert digest(CORE/'mapping.json')=='038eea903cd28433582e7c6d92f5dd686828aa62fedfd13930175f842ac535b9'
    extracted=next(x for x in mapping['stats_static_data']['versions'] if x['version']=='138');assert class_records==extracted['classes'] and race_records==extracted['races']
    (out/'static-data-provenance.json').write_text(json.dumps(dict(classes=class_records,races=race_records,reads=read.proofs),indent=2)+'\n')
    native=load(CORE/'native-class-scalar-correspondence.json');assert digest(CORE/'native-class-scalar-correspondence.json')==mapping['native_scalar_sha256']
    native_path=ROOT/'originals/official-release-20261101T201508.341687Z/windows-0.138.0/AzerothSurvivors.exe';assert digest(native_path)==native['exe_sha256']
    with native_path.open('rb') as stream, mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as exe:
        for entry in native['classes']:
            raw=struct.pack('<2I',*classes[entry['class_byte']]);assert raw.hex()==entry['scalar8_hex'];first=exe.find(raw);assert [first]==entry['file_matches'] and exe.find(raw,first+1)==-1
    assert runtime==comparison['runtime'] and terminal==comparison['process'] and terminal['exit_code']==0 and terminal['error'] is None
    assert terminal['pid_missing'] and terminal['pgid_missing'] and process_missing(terminal['pid']) and process_missing(terminal['pgid'],True)
    for k,v in dict(version='0.138.0',actual_build='382771e6c',cases=10569,completed_cases=10569,full1512_calls=10569,fresh_instances=331,actual_host_calls=0,denied_imports=878,memory_cap_bytes=33554432,heap_cap_mib=512,stack_guards=101736,stack_all_restored=True,original_function_bodies_unchanged=True,network_used=False,user_saves_accessed=False,original_snapshot_loaded=False,error=None).items(): assert runtime[k]==v,(k,runtime[k],v)
    assert runtime['peak_memory_bytes']<=runtime['memory_cap_bytes'] and runtime['output_bytes']==(RUN/'stdout.jsonl').stat().st_size
    assert len(runtime['stats_stack_returns'])==10569
    assert all(row==dict(case=i,before=1048576,after=1048576,returned=True) for i,row in enumerate(runtime['stats_stack_returns']))
    assert (RUN/'stderr.log').stat().st_size==0
    counters=Counter();semantic=Counter();groups=Counter();expected=load(RUN/'expected.json');assert len(expected)==10569
    with (RUN/'fixtures.jsonl').open() as fixtures,(RUN/'stdout.jsonl').open() as actuals:
        for i,(case_line,actual_line) in enumerate(zip(fixtures,actuals,strict=True)):
            c=json.loads(case_line);actual=json.loads(actual_line);wanted=expected[i];assert c['id']==actual['id']==wanted['id']==i;groups[c['group']]+=1
            prediction=reference(c['input'],classes,races,semantic);model=wanted['result'];assert set(prediction)==set(model)
            # First bind every independently calculated value to the frozen fresh expected.
            temp=Counter()
            for domain in ('derived_bits','auxiliary_bits','object_fields'):
                assert set(prediction[domain])==set(model[domain])==set(actual[domain])
                for key,value in prediction[domain].items():
                    integer=domain=='object_fields' and key in ('22','28') or domain=='derived_bits' and key in ('1592','1608')
                    scalar_equal(value,model[domain][key],integer,(i,'expected',domain,key),temp)
                    scalar_equal(value,actual[domain][key],integer,(i,'original',domain,key),counters)
            for key in ('current_hp_bits','speed_bits'):
                scalar_equal(prediction[key],model[key],False,(i,'expected',key),temp);scalar_equal(prediction[key],actual[key],False,(i,'original',key),counters)
            assert prediction['speed_changed']==model['speed_changed'] and prediction['accepted_live_indices']==model['accepted_live_indices']
            changed=int(prediction['speed_changed']);assert actual['speed_sequence']==actual['movement_queue_count']==changed
            counters['compared_values']+=2;counters['strict_integer_values']+=2;counters['movement_queue_entries']+=actual['movement_queue_count'];counters['cases']+=1
            raw=bytes.fromhex(actual['raw_game2592_hex']);assert len(raw)==2592;counters['raw_game_bytes']+=len(raw)
            for domain in ('derived_bits','auxiliary_bits'):
                for offset,value in actual[domain].items(): assert word(raw,int(offset))==value
            for key,offset in (('current_hp_bits',1440),('speed_bits',1648),('speed_sequence',1644),('movement_queue_count',1888)): assert word(raw,offset)==actual[key]
            state=c['input'];assert raw[360]==state['class_byte']&255 and raw[361]==state['race_byte']&255 and raw[2582]==state['flag2574']&255
            assert word(raw,1432)==state['level'] and word(raw,2352)==state['now_bits'] and word(raw,268)==state['conditional268_bits'] and word(raw,1344)==state['conditional1344_id']
            for key,offset in (('passives',1692),('adjustments',1668),('item_modifiers',2024),('owned_skills',168),('timed_definitions',2048),('timed_records',592),('live_effects',1704)):
                cap,ptr,count=struct.unpack_from('<3I',raw,offset);assert cap==count==len(state[key]) and ptr>0
                counters['raw_source_vector_triples']+=1
    assert dict(groups)==comparison['groups'] and counters['cases']==comparison['cases']==comparison['original1512_calls']==10569
    assert counters['compared_values']==comparison['counts']['compared_values']==359346 and counters['movement_queue_entries']==comparison['counts']['actual_movement_packets']==1537
    assert counters['raw_game_bytes']==27394848 and comparison['differences']==0
    assert counters['nan_category_comparisons']>0 and counters['signed_negative_zero_values']>0
    for name,value in files.items(): assert digest(ROOT/name)==value==digest(source/name),name
    observation={name:digest(RUN/name) for name in ('comparison.json','prepared.json','runtime.json','process-terminal.json','fixtures.jsonl','expected.json','stdout.jsonl','stderr.log','manifest.json','1512.wat','task-handoff.json')}
    observation['stats138-original-exports.wasm']=manifest['module_sha256'];observation['auditor.py']=digest(Path(__file__))
    summary=dict(status='scoped_frozen138_full1512_independent_read_only_audit_passed',version='0.138.0',actual_build='382771e6c',original_sha256=SHA,comparison=str((RUN/'comparison.json').relative_to(ROOT)),comparison_sha256=COMPARISON_SHA,cases=10569,full_original1512_calls_in_frozen_capture=10569,new_original_executions=0,new_production_executions=0,differences=0,counts=dict(counters),semantic_counts=dict(semantic),groups=dict(groups),source_files=22,production_files=8,source_import_edges=35,source_snapshot_and_current_equal=True,new_handoff_files_verified=13,entry_identity=identities[1512],only_export_section_changed=True,complete_original_callees_preserved=True,added_exports=manifest['added_exports'],allocator_index=92072,physical_layout=dict(timed_pointer=596,timed_count=600,reserve=764),static13_entry_guards_identity_verified=True,static13_entry_guards_dynamic_acceptance=False,current138_static_class_race_data_reextracted=True,native_scalar8_unique_byte_correspondence_verified=True,native_executions=0,full880_frames=0,complete_games=0,old135_cases_transferred=0,old135_results_transferred=False,pilot12_added=False,runtime_summary={k:v for k,v in runtime.items() if k!='stats_stack_returns'},captured_terminal=terminal,artifacts_sha256=observation,static_provenance_sha256=digest(out/'static-data-provenance.json'),auditor_source=str(Path(__file__).relative_to(ROOT)),auditor_sha256=digest(Path(__file__)),elapsed_seconds=round(time.monotonic()-began,3),pending=['Natural constructor/profile/talent/equipment producers','Full BTree node physical layout beyond the three observed keyed values','Movement packet payload bytes and network delivery','Full Game/880/continuous frame flow','NativeWindows execution and ABI'],limitations=['Original capture is replayed as immutable evidence, not re-executed by this audit.','Expected-first ordering supported by frozen source control flow and prepared capture; not an externally signed timestamp.','NaN floating outputs compared by category only; finite, infinities, signed zeros and integer fields exact.','Raw Game is bound fieldwise including all seven source vector headers, not whole-image equality.','1537 is an observed queue-entry count; packet payload bytes were not captured.','Static13 admission guards and native8B scalar correspondence do not establish runtime support.'])
    (out/'review.json').write_text(json.dumps(summary,indent=2)+'\n')
    report=ROOT/'reports/2026-11-02-stats0138-independent-review.json';report.write_text(json.dumps(summary|dict(evidence=str(out.relative_to(ROOT)),review_sha256=digest(out/'review.json')),indent=2)+'\n')
    md=ROOT/'reports/2026-11-02-stats0138-independent-review.md'
    md.write_text('# Fixed138 full1512 independent review\n\nRead-only second-author audit passed for the fixed `0.138.0 / 382771e6c` capture. The auditor executed neither originals nor production/model/checker/builder code.\n\n- Recomputed10569 fixtures independently against current138 static class/race data, all359346 observed values matched; NaN float payloads compare by category, all other words exact.\n-1537 actual movement queue entries and sequence decisions matched; packet payload bytes are still unknown.\n-22 current/frozen source hashes,8 production files,35 exact local import edges,13 new handoff file hashes verified.\n- OriginalSHA `'+SHA+'`; full1512 and all callees preserved byte-for-byte outside export section7; only1512 and stackglobal0 exported, malloc92072 retained.\n- Verified physical timed596/600 and reserve764 through originalWAT, fixture-runner source and persisted rawGame. Bound27394848 rawGame bytes fieldwise including73983 original source vector headers.\n-331 fresh instances,32MiB WASM cap,512MiB heap,878 denied imports,0 actual host calls;10569 returned stack guards and successful exited/missing PID/PGID captured.\n- All13 static entry bindings matched current138 bodies/signatures; this provides no new dynamic acceptance for those other entry points. Native class8B values have unique byte matches only; no native execution or native layout is established.\n- Historical135 generator is only an input source; no historical runtime result was added. The separate12-case pilot is not added.\n\nPending: natural constructor/profile/talent/equipment producers; fullBTree physical layout; movement packet bytes/network; fullGame/880 flow; nativeWindows behavior. Complete games remain0.\n\nEvidence: `'+str(out.relative_to(ROOT))+'`; `review.json` SHA256 `'+digest(out/'review.json')+'`.\n')
    print(json.dumps(dict(status=summary['status'],evidence=str(out.relative_to(ROOT)),evidence_sha256=digest(out/'review.json'),report_json_sha256=digest(report),report_md_sha256=digest(md),auditor_sha256=digest(Path(__file__)),counts=dict(counters),seconds=summary['elapsed_seconds'])))

if __name__=='__main__': main()
