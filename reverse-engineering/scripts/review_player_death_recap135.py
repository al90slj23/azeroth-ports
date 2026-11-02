#!/usr/bin/env python3
"""Independent read-only1367 audit; no production/original execution/imports."""
from pathlib import Path
from collections import Counter
import argparse,ast,hashlib,json,math,os,re,sqlite3,struct,time

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/player-death-recap135-oracle-20261101T234514.840259Z'
RECEIPT_SHA='05c30dcb209a287d5a722f80fa5e10207c8b173fcb8f0866210677157da8d090'
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
SIGN=0x80000000


def digest(value):return hashlib.sha256(value).hexdigest()
def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def load(path):return json.loads(Path(path).read_text())
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def U(raw,offset=0):return struct.unpack_from('<I',raw,offset)[0]
def F(word):return struct.unpack('<f',struct.pack('<I',word))[0]
def B(value):
    try:return struct.unpack('<I',struct.pack('<f',value))[0]
    except OverflowError:return 0xff800000 if value<0 else 0x7f800000
def add(a,b):return B(F(a)+F(b))
def sub(a,b):return add(a,b^SIGN)
def div(a,b):
    x,y=F(a),F(b)
    if math.isnan(x)or math.isnan(y):return 0x7fc00000
    if y==0:
        if x==0:return 0x7fc00000
        return((a^b)&SIGN)|0x7f800000
    return B(x/y)


def rounded_integer_word(word):
    """Direct85719 instruction restoration, not Python round-to-even."""
    value=add(word,(word&SIGN)|0x3effffff);exponent=(value>>23)&255
    if exponent<127:return value&SIGN
    if exponent<=149:return value&((-8388608>>(exponent-127))&0xffffffff)
    return value


def scalar_number(value):
    """52241: nonfinite0,small integral decimal,otherwise exactly3 digits."""
    if not math.isfinite(value):return b'0'
    if value==math.trunc(value)and abs(value)<1000000000000000:return str(int(value)).encode()
    return format(value,'.3f').encode()


def quoted(text):
    #11735 decodes UTF8 scalars, preserves nonASCII, and special-cases only
    #LF/quote/backslash. Other controls use lower-case four-digit unicode.
    chunks=[b'"']
    for character in text:
        code=ord(character)
        if code==10:chunks.append(b'\\n')
        elif code==34:chunks.append(b'\\"')
        elif code==92:chunks.append(b'\\\\')
        elif code<32:chunks.append(('\\u%04x'%code).encode())
        else:chunks.append(character.encode('utf8'))
    chunks.append(b'"');return b''.join(chunks)


class Writer:
    """Atom-by-atom Vec<u8> growth, derived54802 minimum8/2x/needed."""
    def __init__(self,opening):self.chunks=[opening];self.length=len(opening);self.capacity=len(opening);self.entries=0
    def write(self,value):
        needed=self.length+len(value)
        if needed>self.capacity:self.capacity=max(needed,self.capacity*2,8)
        self.chunks.append(value);self.length=needed
    def pair(self,key,value):
        if self.entries:self.write(b',')
        self.entries+=1;self.write(quoted(key));self.write(b':');self.write(value)
    def n(self,key,word):self.pair(key,scalar_number(F(word)))
    def element(self,value):
        if self.entries:self.write(b',')
        self.entries+=1;self.write(value)
    def bytes(self):return b''.join(self.chunks)


def reference(inp,ranks,counters):
    h=inp['history'];cap,head,count=h['capacity'],h['head'],h['count'];rows=[bytes.fromhex(x)for x in h['rows48_hex']]
    assert cap==len(rows)==len(h['strings'])and all(len(x)==48 for x in rows)and count<=cap<=512
    assert 0<=count and(head==0 if cap==0 else 0<=head<cap)
    now=inp['reference_time_bits'];cutoff=add(now,B(-10));chosen=[]
    for logical in range(count):
        slot=(head+logical)%cap
        if F(U(rows[slot],24))>=F(cutoff):chosen.append(slot)
    counters['active_input_rows']+=count;counters['selected_rows']+=len(chosen)
    counters['future_selected_rows']+=sum(F(U(rows[s],24))>F(now)for s in chosen)
    if not chosen:
        out=Writer(b'{');out.write(b'}')
        return out.capacity,out.bytes(),dict(selected_slots=[],hit_groups=[],source_groups=[],total_bits=SIGN,absorbed_bits=SIGN,avoidable_bits=SIGN)
    def metadata(slot):
        row=rows[slot];who,what,icon=h['strings'][slot];assert 0<=row[44]<len(ranks)
        for i,string in enumerate((who,what,icon)):assert len(string.encode('utf8'))==U(row,8*i+4)
        out=Writer(b'{')
        for key,value in(('who',who),('rank',ranks[row[44]]),('what',what),('icon',icon)):out.pair(key,quoted(value))
        out.pair('mechanic',b'true'if row[45]else b'false');return out
    # Keep the three reductions independent, as the original unrolled loops.
    totals=[]
    for offset in(28,32):
        acc=SIGN
        for slot in chosen:acc=add(acc,U(rows[slot],offset))
        totals.append(acc)
    avoid=SIGN
    for slot in chosen:
        if rows[slot][45]==1:avoid=add(avoid,U(rows[slot],28))
    recent=[]
    for slot in chosen:
        damage,absorbed=U(rows[slot],28),U(rows[slot],32)
        if recent and h['strings'][recent[-1][0]][:2]==h['strings'][slot][:2]and F(sub(U(rows[slot],24),U(rows[recent[-1][0]],24)))<=1:
            old=recent[-1];recent[-1]=[slot,add(damage,old[1]),add(absorbed,old[2]),(old[3]+1)&0xffffffff];counters['adjacent_merges']+=1
            counters['reverse_time_merges']+=F(sub(U(rows[slot],24),U(rows[old[0]],24)))<0
        else:recent.append([slot,damage,absorbed,1])
    by=[];positions={}
    for slot in chosen:
        pair=tuple(h['strings'][slot][:2]);damage=U(rows[slot],28)
        if pair in positions:
            group=by[positions[pair]];group[1]=add(damage,group[1]);group[2]=(group[2]+1)&0xffffffff
        else:positions[pair]=len(by);by.append([slot,damage,1])
    def order(word):
        transformed=word^(0x7fffffff if word&SIGN else 0)
        return transformed-(1<<32)if transformed&SIGN else transformed
    by=sorted(by,key=lambda group:(-order(group[1]),chosen.index(group[0])))
    counters['hit_groups_before_limit']+=len(recent);counters['source_groups_before_limit']+=len(by)
    counters['long_sort_cases']+=len(by)>=21;counters['small_sort_cases']+=2<=len(by)<21
    hits=Writer(b'[')
    for slot,damage,absorbed,n in recent[max(0,len(recent)-8):]:
        out=metadata(slot);ago=sub(now,U(rows[slot],24));ago=ago if F(ago)>0 else 0
        out.n('ago',ago);out.n('n',rounded_integer_word(damage));out.n('abs',rounded_integer_word(absorbed));out.pair('count',scalar_number(n))
        maximum=U(rows[slot],40)
        if not F(maximum)>1:maximum=B(1)
        ratio=div(U(rows[slot],36),maximum)
        if F(ratio)<0:ratio=0
        if F(ratio)>1:ratio=B(1)
        out.n('hp',ratio);out.write(b'}');hits.element(out.bytes())
    hits.write(b']');sources=Writer(b'[')
    for slot,damage,n in by[:6]:
        out=metadata(slot);out.n('n',rounded_integer_word(damage));out.pair('count',scalar_number(n));out.write(b'}');sources.element(out.bytes())
    sources.write(b']');last=chosen[-1];killer=metadata(last);killer.n('n',rounded_integer_word(U(rows[last],28)))
    over=U(rows[last],36)^SIGN;over=over if F(over)>0 else 0;killer.n('overkill',rounded_integer_word(over));killer.write(b'}')
    age=sub(now,U(rows[chosen[0]],24))
    if F(age)<0:age=0
    if F(age)>10:age=B(10)
    out=Writer(b'{');out.n('secs',age);out.n('total',rounded_integer_word(totals[0]));out.n('absorbed',rounded_integer_word(totals[1]));out.n('avoidable',rounded_integer_word(avoid));out.n('maxhp',rounded_integer_word(U(rows[last],40)))
    out.pair('killer',killer.bytes());out.pair('hits',hits.bytes());out.pair('by',sources.bytes());out.write(b'}')
    return out.capacity,out.bytes(),dict(selected_slots=chosen,hit_groups=recent,source_groups=by,total_bits=totals[0],absorbed_bits=totals[1],avoidable_bits=avoid)


class Reader:
    def __init__(self,raw,pos=0):self.raw=raw;self.pos=pos
    def byte(self):v=self.raw[self.pos];self.pos+=1;return v
    def uint(self):
        value=shift=0
        while True:
            x=self.byte();value|=(x&127)<<shift
            if x<128:return value
            shift+=7;assert shift<=35
    def integer(self):
        value=shift=0
        while True:
            x=self.byte();value|=(x&127)<<shift;shift+=7
            if x<128:return value-(1<<shift)if x&64 else value
    def name(self):n=self.uint();v=self.raw[self.pos:self.pos+n];self.pos+=n;return v.decode()


def sections(raw):
    assert raw[:8]==bytes.fromhex('0061736d01000000');r=Reader(raw,8);out=[]
    while r.pos<len(raw):
        start=r.pos;kind=r.byte();size=r.uint();a=r.pos;r.pos+=size;assert r.pos<=len(raw);out.append((kind,start,a,r.pos))
    return out


def exports(raw,section):
    r=Reader(raw,section[2]);out=[]
    for _ in range(r.uint()):out.append((r.name(),r.byte(),r.uint()))
    assert r.pos==section[3];return out


def static_reader(raw,sects):
    section=next(x for x in sects if x[0]==11);r=Reader(raw,section[2]);parts=[]
    for _ in range(r.uint()):
        flag=r.uint();assert flag in(0,1,2)
        if flag==2:assert r.uint()==0
        address=None
        if flag!=1:assert r.byte()==0x41;address=r.integer();assert r.byte()==0x0b
        n=r.uint();parts.append((address,r.pos,n));r.pos+=n
    assert r.pos==section[3]
    def read(address,n):
        found=[raw[p+address-a:p+address-a+n]for a,p,count in parts if a is not None and a<=address and address+n<=a+count]
        assert len(found)==1,(address,n);return found[0]
    return read


def source_edges(base,names):
    declared=set(names);edges=set()
    for name in declared:
        path=base/name
        if path.suffix=='.mjs':
            for rel in re.findall(r"from\s+['\"](\.[^'\"]+)['\"]",path.read_text()):
                dep=str((path.parent/rel).resolve().relative_to(base));assert dep in declared;edges.add((name,dep))
            continue
        if path.suffix!='.py':continue
        parts=Path(name).with_suffix('').parts
        for node in ast.walk(ast.parse(path.read_text())):
            modules=[]
            if isinstance(node,ast.Import):modules=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom):
                prefix='.'.join(list(parts[1:-node.level])+([node.module]if node.module else[]))if node.level else node.module or''
                modules=[prefix]+[prefix+'.'+a.name if prefix else a.name for a in node.names]
            for module in modules:
                if not module:continue
                rel=Path(*module.split('.'))
                for folder in('scripts','reconstruction'):
                    candidates=[base/folder/rel.with_suffix('.py'),base/folder/rel/'__init__.py'];dep=next((x for x in candidates if x.is_file()),None)
                    if dep is None:continue
                    key=str(dep.relative_to(base));assert key in declared,(name,key);edges.add((name,key))
                    for parent in dep.parents:
                        if parent==base/folder:break
                        init=parent/'__init__.py'
                        if init.is_file():key=str(init.relative_to(base));assert key in declared;edges.add((name,key))
    return sorted(edges)


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);a=parser.parse_args();out=a.output.resolve()
    assert out.is_relative_to((ROOT/'evidence').resolve());out.mkdir();start=time.monotonic();own=Path(__file__);own_sha=sha(own)
    (out/'reviewer.py').write_bytes(own.read_bytes())
    assert sha(RUN/'comparison.json')==RECEIPT_SHA;report=load(RUN/'comparison.json')
    assert report['cases']==report['actual_cases']==103 and report['differences']==0 and report['status']=='passed'
    sources=report['source_sha256_before'];assert len(sources)==12 and sources==report['source_sha256_after']
    for name,h in sources.items():assert sha(ROOT/name)==sha(RUN/'source-snapshot'/name)==h,name
    edges=source_edges(RUN/'source-snapshot',sources);assert edges==[tuple(x)for x in report['local_source_import_edges']]
    for table in('frozen_artifacts','artifacts'):
        for name,h in report[table].items():assert sha(RUN/name)==h,(table,name)
    assert report['expected_before_original']and not report['input_contains_expected']
    original=SOURCE.read_bytes();assert len(original)==90959080 and digest(original)==SOURCE_SHA
    manifest=load(RUN/'manifest.json');changed=(RUN/manifest['module_file']).read_bytes();assert digest(changed)==manifest['module_sha256']
    before,after=sections(original),sections(changed);assert [x[0]for x in before]==[x[0]for x in after]and not any(x[0]==8 for x in before)
    for x,y in zip(before,after):
        if x[0]!=7:assert original[x[1]:x[3]]==changed[y[1]:y[3]]
    old=exports(original,next(x for x in before if x[0]==7));new=exports(changed,next(x for x in after if x[0]==7))
    assert new==old+[('research135_death_recap1367',0,1367),('research135_death_recap_stack0',3,0)]and('__wbindgen_malloc',0,91941)in old
    global_sec=next(x for x in before if x[0]==6);assert original[global_sec[2]:global_sec[3]].hex()=='017f01418080c0000b'
    import_sec=next(x for x in before if x[0]==2);r=Reader(original,import_sec[2]);assert r.uint()==878
    for _ in range(878):r.name();r.name();assert r.byte()==0;r.uint()
    assert r.pos==import_sec[3]
    r=Reader(original,next(x for x in before if x[0]==1)[2]);types=[]
    for _ in range(r.uint()):assert r.byte()==0x60;n=r.uint();p=bytes(r.byte()for _ in range(n));n=r.uint();v=bytes(r.byte()for _ in range(n));types.append((p.hex(),v.hex()))
    r=Reader(original,next(x for x in before if x[0]==3)[2]);decl=[r.uint()for _ in range(r.uint())];assert types[decl[1367-878]]==('7f7f7d','')
    read=static_reader(original,before);ranks=[]
    for rank in range(5):ranks.append(read(U(read(5414964+rank*4,4)),U(read(5414944+rank*4,4))).decode('utf8'))
    assert ranks==['mob','elite','boss','object','none']
    functions={};texts={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as con,(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        con.row_factory=sqlite3.Row;con.execute('pragma query_only=on')
        for index in(1367,13106,6332,85719,44448,51418,11735,52241,54802):
            row=dict(con.execute('select *from functions where idx=?',(index,)).fetchone());stream.seek(row['wat_start']);wat=stream.read(row['wat_end']-row['wat_start']);assert len(wat)<150000
            assert wat.startswith(f'  (func (;{index};)'.encode());texts[index]=[x.strip()for x in wat.decode().splitlines()]
            functions[index]=dict(body_start=row['body_start'],body_end=row['body_end'],body_sha256=digest(original[row['body_start']:row['body_end']]),wat_sha256=digest(wat),wat_bytes=len(wat))
            (out/f'{index}.wat').write_bytes(wat)
    for f in manifest['functions']:
        for key in('body_start','body_end','body_sha256','wat_sha256'):assert functions[f['index']][key]==f[key]
    assert functions[1367]['body_sha256']==report['original_body_sha256']=='f5b307b9d13c9e9c899ddca880349c2ba03815cf12508b3669dc02c37db502d7'
    windows={}
    for name,index,a,b,terms in(
        ('cutoff_future',1367,118,128,('f32.const -0x1.4p+3','f32.ge')),
        ('ordered_total',1367,425,449,('f32.load offset=28','f32.add')),
        ('mechanic_exact_one',1367,605,617,('i32.load8_u offset=45','i32.const 1','i32.eq')),
        ('adjacent_merge',1367,701,773,('call 82066','f32.load offset=24','f32.sub','f32.le','i32.store','f32.add')),
        ('last8_groups',1367,871,899,('i32.const 8','i32.sub','i32.shl')),
        ('descending_total_order',1367,1690,1777,('i32.shr_s','i32.shr_u','i32.xor','i32.gt_s','i32.lt_s')),
        ('stable_merge_equal_takes_left',6332,531,590,('i32.lt_s','select','i32.ge_s','i32.const 12')),
        ('top6_sources',1367,2064,2087,('i32.const 60','i32.eq','i32.const 12')),
        ('round_halfaway',85719,3,34,('f32.copysign','f32.add','i32.const 149','i32.and')),
        ('UTF8_control_escaping',11735,172,207,('i32.const 10','i32.const 34','i32.const 92','i32.const 32')),
        ('formatter_nonfinite_integer',52241,14,40,('i64.const 9218868437227405312','f64.trunc','f64.const 0x1.c6bf52634p+49')),
        ('Vec_growth',54802,28,65,('i32.shl','i32.const 8','i32.const 4','call 56192'))):
        text='\n'.join(texts[index][a-1:b]);assert all(term in text for term in terms),name
        windows[name]=dict(function=index,first_line=a,last_line=b,text=text,sha256=digest(text.encode()))
    fixture=load(RUN/'fixtures.json');inputs=load(RUN/'inputs.json');actual=[json.loads(x)for x in(RUN/'results.jsonl').read_text().splitlines()]
    assert len(fixture)==len(inputs)==len(actual)==103
    config=load(RUN/'config.json');assert config==dict(input_path=str(RUN/'inputs.json'),input_sha256=sha(RUN/'inputs.json'))
    counts=Counter();groups=Counter();capacities=Counter();decoded=[]
    for c,inp,got in zip(fixture,inputs,actual):
        assert c['id']==inp['id']==got['id']and c['input']==inp and set(inp)=={'id','history','reference_time_bits'}
        capacity,raw,diag=reference(inp,ranks,counts)
        assert(capacity,raw.hex())==(got['capacity'],got['raw_hex'])==(c['expected']['capacity'],c['expected']['raw_hex']),(c['id'],c['group'])
        assert diag==c['diagnostic'],(c['id'],'groupdiagnostic')
        assert len(raw)==got['length']<=capacity and len(bytes.fromhex(got['output_backing_hex']))==capacity and bytes.fromhex(got['output_backing_hex'])[:len(raw)]==raw
        document=json.loads(raw);decoded.append(dict(id=c['id'],group=c['group'],capacity=capacity,length=len(raw),selected=len(diag['selected_slots']),hits=len(document.get('hits',[])),by=len(document.get('by',[])),sha256=digest(raw)))
        h=inp['history'];hb=bytes.fromhex(got['history_header_before_hex']);assert hb.hex()==got['history_header_after_hex']and len(hb)==16
        assert(U(hb),U(hb,8),U(hb,12))==(h['capacity'],h['head'],h['count'])and U(hb,4)!=0
        rb=bytes.fromhex(got['history_storage_before_hex']);assert rb.hex()==got['history_storage_after_hex']and len(rb)==48*h['capacity']
        pointer_bytes=set()
        for j,encoded in enumerate(h['rows48_hex']):
            before_row=bytes.fromhex(encoded);real=rb[48*j:48*(j+1)]
            text=h['strings'][j]
            if text is not None:
                assert len(text)==3
                for k,string in enumerate(text):
                    assert len(string.encode('utf8'))==U(before_row,8*k+4)==U(real,8*k+4)and U(real,8*k)>0
                    pointer_bytes.update(range(j*48+k*8,j*48+k*8+4));counts['resolved_UTF8_bytes']+=len(string.encode('utf8'))
            for offset in range(48):
                if j*48+offset not in pointer_bytes:assert real[offset]==before_row[offset]
        assert got['strings_unchanged']==sum(x is not None for x in h['strings'])*3
        assert(got['stack_after'],got['host_calls'],got['full_original_function'])==(1048576,0,1367)and got['memory_bytes']<=33554432
        counts['strict_input_backing_bytes']+=len(rb);counts['strict_input_header_bytes']+=16;counts['unrelocated_input_bytes']+=len(rb)-len(pointer_bytes);counts['JSON_bytes']+=len(raw)
        counts['inactive_padding_bytes']+=2*h['capacity'];groups[c['group']]+=1;capacities[capacity]+=1
    assert dict(groups)==report.get('groups',dict(groups))
    process=load(RUN/'terminal.json');assert process==report['process']and process['exit_code']==0 and process['pid_missing']and process['pgid_missing']and process['seconds']<process['deadline_seconds']==60
    assert missing(process['pid'])and missing(process['pgid'],True)
    owned=load(RUN/'owned-process.json');assert(owned['pid'],owned['pgid'],owned['deadline_seconds'])==(process['pid'],process['pgid'],60)
    assert '--wasm-max-mem-pages=512'in owned['command']and '--max-old-space-size=512'in owned['command']and owned['command'][-2:]==[str(RUN),str(RUN/'config.json')]
    rt=load(RUN/'runtime.json');assert rt==report['runtime']and(rt['cases'],rt['completed_cases'],rt['full1367_calls'],rt['fresh_instances'])==(103,103,103,103)
    assert(rt['host_calls'],rt['denied_imports'],rt['max_memory_bytes'],rt['memory_cap_bytes'],rt['stack_checks'])==(0,878,14614528,33554432,4447)
    assert not any(rt[x]for x in('old_snapshot_loaded','App_or_Game_constructed','history_producer_executed','original_bodies_modified','user_saves_accessed','network_used','error'))
    assert sha(own)==own_sha and sha(RUN/'comparison.json')==RECEIPT_SHA
    for name,h in sources.items():assert sha(ROOT/name)==sha(RUN/'source-snapshot'/name)==h
    for table in('frozen_artifacts','artifacts'):
        for name,h in report[table].items():assert sha(RUN/name)==h
    result=dict(status='passed-within-declared-domain',reviewer_source_sha256=own_sha,author_receipt_sha256=RECEIPT_SHA,
        original_wasm_sha256=SOURCE_SHA,original_body_sha256=functions[1367]['body_sha256'],cases=103,new_original_calls=0,production_imports=0,production_executions=0,
        source_count=len(sources),local_source_edges=len(edges),sources_verified=sources,static_functions=functions,static_windows=windows,
        counts=dict(counts),capacity_histogram=dict(sorted(capacities.items())),groups=dict(groups),cases_recomputed=decoded,original_process=process,
        original_runtime=rt,seconds=time.monotonic()-start,
        limits=['Explicit borrowedhistory1367 only,not full1073/5620/1938 ornaturalplayerdeath chain.',
            'All JSON activebytes/capacity andfullhistory header/storageinvariance are independently checked.',
            'Input stringcontents consumed byJSON andsource-boundruntime assertsallallocatedstrings unchanged;rawstringsbackings not persisted inresults.',
            'Unused outputcapacity bytes are preserved observations,not independently predicted.',
            'Five-labelclassification andregistered103corpus; arbitraryNaNpayload multi-groupordering andmalformedrings remainunaccepted.',
            'No fullGame/App/UI/nativeWindows/network orcompletegame acceptance.'])
    save(out/'review.json',result);print(json.dumps(dict(output=str(out/'review.json'),sha256=sha(out/'review.json'),cases=103,source_count=len(sources),counts=dict(counts))))


if __name__=='__main__':main()
