#!/usr/bin/env python3
"""Independent read-only138 evidence review; never import or execute a producer.
Only stdlib byte parsing, source ASTs and an independent numerical recomparison
are used. No target instance, checker, builder, Node, EXE or toolchain runs.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import ast,hashlib,json,math,os,re,sqlite3,stat,struct,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/combat0138-oracle-20261101T205616.629599Z'
PROFILE=ROOT/'evidence/wasm0138-profile-20261101T202038.814151Z'
MAPPING=ROOT/'evidence/combat0138-static-map-20261101T205516.792418Z'

def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    except PermissionError:return None
    return False

def leb(raw,p,signed=False):
    n=s=0
    while True:
        b=raw[p];p+=1;n|=(b&127)<<s;s+=7;assert s<=35
        if b<128:return(n-(1<<s)if signed and b&64 else n),p

def sections(raw):
    assert raw[:8]==b'\0asm\1\0\0\0';p=8;result=[]
    while p<len(raw):
        begin=p;kind=raw[p];size,start=leb(raw,p+1);p=start+size;assert p<=len(raw);result.append((kind,begin,start,p))
    assert p==len(raw);return result

def exports(raw):
    _,_,p,end=next(x for x in sections(raw)if x[0]==7);n,p=leb(raw,p);out=[]
    for _ in range(n):
        size,p=leb(raw,p);name=raw[p:p+size].decode();p+=size;kind=raw[p];index,p=leb(raw,p+1);out.append([name,kind,index])
    assert p==end;return out

def functions(raw,wanted):
    parts=sections(raw);_,_,p,end=next(x for x in parts if x[0]==2);imports,p=leb(raw,p)
    for _ in range(imports):
        for _ in range(2):n,p=leb(raw,p);p+=n
        assert raw[p]==0;_,p=leb(raw,p+1)
    assert p==end and imports==878
    _,_,p,end=next(x for x in parts if x[0]==1);n,p=leb(raw,p);types=[]
    for _ in range(n):
        assert raw[p]==0x60;a,p=leb(raw,p+1);params=raw[p:p+a].hex();p+=a;b,p=leb(raw,p);results=raw[p:p+b].hex();p+=b;types.append([params,results])
    assert p==end
    _,_,p,end=next(x for x in parts if x[0]==3);n,p=leb(raw,p);decl=[]
    for _ in range(n):t,p=leb(raw,p);decl.append(t)
    assert p==end
    _,_,p,end=next(x for x in parts if x[0]==10);count,p=leb(raw,p);assert count==n;out={}
    for index in range(imports,imports+n):
        size,start=leb(raw,p);p=start+size
        if index in wanted:out[index]=dict(index=index,signature=types[decl[index-imports]],body_start=start,body_end=p,body_sha256=hashlib.sha256(raw[start:p]).hexdigest())
    assert p==end and set(out)==set(wanted);return out

def static_reader(raw):
    parts=sections(raw);_,_,p,end=next(x for x in parts if x[0]==5);n,p=leb(raw,p);assert n==1;flags,p=leb(raw,p);assert flags in(0,1);pages,p=leb(raw,p)
    initial=pages*65536;_,_,p,end=next(x for x in parts if x[0]==11);n,p=leb(raw,p);segments=[]
    for index in range(n):
        flags,p=leb(raw,p);assert flags==0 and raw[p]==65;address,p=leb(raw,p+1,True);assert raw[p]==11;size,p=leb(raw,p+1)
        assert 0<=address<=address+size<=initial;segments.append((index,address,p,size));p+=size
    assert p==end;proofs=[]
    def read(address,size):
        assert 0<=address<=address+size<=initial and size<=1048576;result=bytearray(size);overlaps=[]
        for index,start,file,length in segments:
            a,b=max(start,address),min(start+length,address+size)
            if a<b:result[a-address:b-address]=raw[file+a-start:file+b-start];overlaps.append(dict(segment=index,memory_start=a,memory_end_exclusive=b,file_start=file+a-start))
        value=bytes(result);proofs.append(dict(address=address,bytes=size,active_overlays_in_original_order=overlaps,uncovered_bytes_use_WASM_initial_zero=True,hex=value.hex(),sha256=hashlib.sha256(value).hexdigest()));return value
    read.proofs=proofs;return read

def source_closure(names):
    """Resolve local Python imports from frozen ASTs, including package init.
    Node runner imports are separately restricted to explicit node: builtins.
    """
    edges=set();discovered=set();todo=list(names)
    def add(module,owner):
        if not module:return
        base=ROOT/'reconstruction'if module.split('.')[0]in('core_spec','resource_spec')else ROOT/'scripts'
        p=base.joinpath(*module.split('.')).with_suffix('.py')
        if not p.is_file():p=base.joinpath(*module.split('.'))/'__init__.py'
        if not p.is_file():return
        name=str(p.relative_to(ROOT));edges.add((owner,name));todo.append(name)
        if base==ROOT/'reconstruction'and'.'in module:todo.append('reconstruction/'+module.split('.')[0]+'/__init__.py')
    while todo:
        name=todo.pop()
        if name in discovered:continue
        discovered.add(name);p=RUN/'source-snapshot'/name;assert p.is_file(),('Unfrozen local import',name)
        if name.endswith('.mjs'):
            modules=re.findall(r"\bfrom\s*['\"]([^'\"]+)['\"]|\bimport\s*['\"]([^'\"]+)['\"]",p.read_text())
            assert all((a or b).startswith('node:')for a,b in modules);continue
        tree=ast.parse(p.read_text());package=name.removeprefix('reconstruction/').removesuffix('.py').replace('/','.')
        package=package.removesuffix('.__init__')if package.endswith('.__init__')else package.rsplit('.',1)[0]if'.'in package else''
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                for item in node.names:add(item.name,name)
            elif isinstance(node,ast.ImportFrom):
                assert node.level in(0,1)
                module=((package+'.')if package and node.module else package)+(node.module or'')if node.level else(node.module or'')
                add(module,name)
                for item in node.names:add(module+'.'+item.name if module else item.name,name)
    assert discovered==set(names),('Source closure mismatch',discovered^set(names));return sorted(edges)

def F(word):return struct.unpack('<f',struct.pack('<I',word))[0]
def bits(value):
    try:return struct.unpack('<I',struct.pack('<f',value))[0]
    except OverflowError:return 0x7f800000 if value>0 else 0xff800000

def numeric_operation(rows,now,phase,total,op,counters):
    """Independent scalar interpreter of reviewed913 windows, no model import.
    Finite f32 operands use binary64 exact product/significand intermediates,
    with an explicit f32 rounding after every original add/mul/sub instruction.
    """
    assert op['context']==0;target=int(op['target_id']);index=next((i for i,row in enumerate(rows)if struct.unpack_from('<Q',row,112)[0]==target),None);result=list(rows)
    if phase!=1:counters['phase_rejected']+=1;return result,total
    if index is None:counters['missing_target']+=1;return result,total
    row=rows[index];u=lambda o:struct.unpack_from('<I',row,o)[0];signed=lambda o:struct.unpack_from('<i',row,o)[0]
    assert signed(244)==-1 and signed(40)!=3
    add=lambda a,b:bits(F(a)+F(b));mul=lambda a,b:bits(F(a)*F(b));now=F(now);multiplier=0x3f800000
    if now<F(u(148)):multiplier=add(multiplier,u(144))
    multiplier=add(multiplier,u(152)if now<F(u(156))else u(160)if now<F(u(164))else 0)
    multiplier=add(add(multiplier,u(368)),0)
    school=0x3dcccccd if(op['school']&254)==2 and F(u(372))>now else 0;counters['school372_bonus_evaluations']+=bool(school)
    amount=mul(op['amount_bits'],add(multiplier,school));scale=0x3f800000
    if signed(64)!=-1:
        if F(u(420))>now:scale=0x3fc00000
        elif F(u(416))>now or any(struct.unpack_from('<I',x)[0]==0 and struct.unpack_from('<i',x,40)[0]==2 and struct.unpack_from('<Q',x,32)[0]==target for x in rows):scale=0x3e800000
    amount=mul(amount,scale)
    if u(0)==1:counters['dead_marker_rejected']+=1;return result,total
    damage=0x3f800000 if math.isnan(F(amount))or F(amount)<=1 else amount;new_hp=bits(F(u(288))-F(damage));assert math.isfinite(F(u(288)))and F(new_hp)>0
    accounted=min(max(0,F(u(288))),F(damage));old_total=struct.unpack('<d',struct.pack('<Q',total))[0];new_total=struct.unpack('<Q',struct.pack('<d',old_total+accounted))[0]
    counters['accepted_nonlethal']+=1;counters['f64_total_differs_from_f32_accumulation']+=float(F(bits(old_total+accounted)))!=old_total+accounted
    changed=bytearray(row);struct.pack_into('<I',changed,288,new_hp);result[index]=bytes(changed)
    for i,(a,b)in enumerate(zip(rows,result)):assert all(x==y or i==index and 288<=offset<292 for offset,(x,y)in enumerate(zip(a,b)))
    return result,new_total

def main():
    began=time.monotonic();out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('combat0138-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    report=json.loads((RUN/'comparison.json').read_text());manifest=json.loads((RUN/'manifest.json').read_text());profile=json.loads((PROFILE/'manifest.json').read_text());mapping=json.loads((MAPPING/'mapping.json').read_text())
    assert sha(RUN/'comparison.json')=='282e38ed4d2f14e87a12568cc9f0dbcca81c9641f63464936c9c08047278b7fa'
    assert report['version']=='0.138.0'and report['build']=='382771e6c'and report['complete']and report['mismatch_cases']==0 and report['source_before']==report['source_after']
    before={n:sha(ROOT/n)for n in report['source_before']};assert before==report['source_before'];assert len(before)==11
    for name,digest in before.items():assert sha(RUN/'source-snapshot'/name)==digest
    closure_edges=source_closure(before);production=[n for n in before if n.startswith('reconstruction/')]
    assert set(production)=={'reconstruction/core_spec/__init__.py','reconstruction/core_spec/binary32.py','reconstruction/core_spec/combat138.py','reconstruction/core_spec/upgrade_values.py'}
    direct_io=[]
    for name in production:
        for node in ast.walk(ast.parse((RUN/'source-snapshot'/name).read_text())):
            if isinstance(node,ast.Call):
                fn=node.func;label=fn.id if isinstance(fn,ast.Name)else fn.attr if isinstance(fn,ast.Attribute)else''
                if label in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__'):direct_io.append([name,label])
    assert not direct_io
    for name,digest in report['artifacts'].items():assert sha(RUN/name)==digest
    assert sha(RUN/'stdout.jsonl')==report['output_sha256']and sha(RUN/'stderr.log')==report['stderr_sha256']and not(RUN/'stderr.log').stat().st_size
    original=Path(profile['original_path']).read_bytes();module=(RUN/manifest['module_file']).read_bytes();assert hashlib.sha256(original).hexdigest()==profile['original_sha256']==manifest['original_sha256']and len(original)==90946299 and sha(RUN/manifest['module_file'])==manifest['module_sha256']
    a,b=sections(original),sections(module);assert[x[0]for x in a]==[x[0]for x in b]and not any(x[0]==8 for x in a)
    assert all(original[x:y]==module[u:v]for(k,x,_,y),(_,u,_,v)in zip(a,b)if k!=7)
    assert exports(module)==exports(original)+[['research138_damage913',0,913],['research138_stack0',3,0]]and['__wbindgen_malloc',0,92072]in exports(original)
    _,_,gs,ge=next(s for s in a if s[0]==6);assert original[gs:ge].hex()=='017f01418080c0000b'
    identities=functions(original,{913,914,68536});entry=identities[913];assert entry['signature']==['7f7e7d7f7f7f7f','']and identities[914]['signature']==['7f7f7f7f7f7f','']and identities[68536]['signature']==['7f7f7f7f','']
    for key,value in entry.items():assert manifest['entry'][key]==value
    assert stat.S_IMODE(Path(profile['database_path']).stat().st_mode)==0o444 and sha(Path(profile['database_path']))==profile['database_sha256']and sha(PROFILE/'manifest.json')==manifest['profile_manifest_sha256']
    queries=[];texts={}
    with sqlite3.connect(Path(profile['database_path']).resolve().as_uri()+'?mode=ro',uri=True)as c:
        c.row_factory=sqlite3.Row
        for idx in(913,68536):
            query='select * from functions where idx=?';row=dict(c.execute(query,(idx,)).fetchone());assert row['body_start']==identities[idx]['body_start']and row['body_end']==identities[idx]['body_end'];queries.append(dict(query=query,parameter=idx,result=row))
            with Path(profile['wat_path']).open('rb')as stream:stream.seek(row['wat_start']);wat=stream.read(row['wat_end']-row['wat_start'])
            assert len(wat)<524288;texts[idx]=wat;assert wat==(MAPPING/f'138-{idx}.wat').read_bytes()
        query='select callee,wat_offset,wat_line,instruction from calls where caller=? order by wat_offset';calls=[dict(x)for x in c.execute(query,(913,))];assert calls==sorted(manifest['direct_calls'],key=lambda x:x['wat_offset']);queries.append(dict(query=query,parameter=913,rows=len(calls),distinct_callees=len({x['callee']for x in calls})))
    assert texts[913]==(RUN/'913.wat').read_bytes()and hashlib.sha256(texts[913]).hexdigest()==manifest['entry']['wat_sha256']
    assert sha(MAPPING/'mapping.json')=='35c31aaa6d075c8823b166951a86598c072206ae79df3c13cbb9e756986ebf50'
    for name,value in mapping['artifacts'].items():assert sha(MAPPING/name)==value['sha256']and(MAPPING/name).stat().st_size==value['bytes']
    old=Path(ROOT/mapping['profiles']['137']['source']).read_bytes();assert hashlib.sha256(old).hexdigest()==mapping['profiles']['137']['source_sha256'];old_helper=functions(old,{68459})[68459];assert old_helper['signature']==['7f7f','']
    old_profile=ROOT/'evidence/wasm0137-profile-20261101T162221.947222Z'
    with sqlite3.connect((old_profile/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as c:
        c.row_factory=sqlite3.Row;row=dict(c.execute('select * from functions where idx=?',(68459,)).fetchone())
    assert(row['body_start'],row['body_end'])==(old_helper['body_start'],old_helper['body_end'])
    with(old_profile/'official-0.137.0-full.wat').open('rb')as stream:stream.seek(row['wat_start']);old_wat=stream.read(row['wat_end']-row['wat_start'])
    assert old_wat==(MAPPING/'137-68459.wat').read_bytes();save(out/'bounded-WAT-and-queries.json',dict(queries=queries,full_WAT_read=False,function_bytes_read=sum(map(len,texts.values()))+len(old_wat),old_helper=old_helper,new_helper=identities[68536],old_helper_text=old_wat.decode(),new_helper_text=texts[68536].decode()))
    lines=texts[913].decode().splitlines();proofs=[]
    for label,start,end in [('phase_and432_stride',1,79),('additives144152160',674,740),('additive368_and_empty_spell',887,913),('school_mask_U372',1110,1166),('phase420416_and_linked_kind2',1190,1295),('marker1_HP288_minimum1',1390,1460),('actual_f64_total984',1569,1580),('G1972_guarded_new_ABI',7199,7223),('new_ABI_second_invocation',7670,7679)]:proofs.append(dict(label=label,function=913,function_lines=[start,end],instructions=lines[start-1:end]))
    assert sum('f64.store offset=984'in l for l in lines)==1 and'call 68536'in texts[913].decode()
    rows=json.loads((RUN/'input.json').read_text());expected=json.loads((RUN/'expected.json').read_text());actual=[json.loads(x)for x in(RUN/'stdout.jsonl').read_text().splitlines()];observed_games=[json.loads(x)for x in(RUN/'raw-games.jsonl').read_text().splitlines()];labels=json.loads((RUN/'labels.json').read_text());counts=Counter();recordbytes=0;phase_cases=[];raw_index=0
    assert len(rows)==len(expected)==len(actual)==80 and expected==actual
    for case,want,answer in zip(rows,expected,actual):
        assert case['id']==want['id']==answer['id'];state=case['state'];records=[bytes.fromhex(x)for x in state['units432_hex']];total=int(state['accounted_total_bits']);assert all(len(x)==432 for x in records)and state['sources']==dict(items2028=[],spells2052=[],other_procs_absent=True)
        assert len({struct.unpack_from('<Q',x,112)[0]for x in records})==len(records)
        if any(struct.unpack_from('<I',x,64)[0]==0 and struct.unpack_from('<I',x,68)[0]==0 for x in records):phase_cases.append(case['id'])
        assert len(case['operations'])==len(answer['answers'])<=16
        for index,(op,seen)in enumerate(zip(case['operations'],answer['answers'])):
            counts['operations']+=1;records,total=numeric_operation(records,state['now_bits'],state['phase2587'],total,op,counts);prediction=dict(units432_hex=[x.hex()for x in records],accounted_total_bits=str(total),rng_words=state['rng_words']);assert prediction==seen,(case['id'],index)
            recordbytes+=sum(map(len,records));raw=observed_games[raw_index];raw_index+=1;assert(raw['case_id'],raw['operation'])==(case['id'],index);game=bytes.fromhex(raw['raw_game8192_hex']);assert len(game)==8192
            assert struct.unpack_from('<Q',game,984)[0]==total and list(struct.unpack_from('<4I',game,1720))==state['rng_words']
            assert struct.unpack_from('<III',game,1784)==(len(records),raw['unit_pointer'],len(records))and game[2587]==state['phase2587']and struct.unpack_from('<I',game,2352)[0]==state['now_bits']and struct.unpack_from('<I',game,1972)[0]==0
    assert counts['operations']==report['calls']==raw_index==len(observed_games)==125 and len(phase_cases)==7 and Counter(x['group']for x in labels)==report['groups']
    assert(RUN/'raw-games.jsonl').stat().st_size==report['raw_game_observations_bytes']and sha(RUN/'raw-games.jsonl')==report['raw_game_observations_sha256']
    runtime=report['runtime'];assert runtime==json.loads((RUN/'runtime.json').read_text())and runtime['cases']==runtime['fresh_instances']==80 and runtime['full_original913_calls']==125 and runtime['actual_host_calls']==0 and runtime['denied_imports']==878 and runtime['peak_memory_bytes']<=33554432
    assert Counter(x['role']for x in runtime['stack_checks'])=={'allocator92072':160,'damage913':125}
    assert len(runtime['stack_checks'])==285 and all(x['returned']and x['before']==x['after']==1048576 for x in runtime['stack_checks'])and runtime['stack_all_restored']
    assert all(runtime[k]is False for k in('application_start_called','windows_exe_executed','network_used','user_saves_accessed','shared52_roles_changed'))
    prepared=json.loads((RUN/'prepared.json').read_text());assert prepared['expected_before_original']and prepared['artifacts']==report['artifacts']and prepared['source_closure']==before and prepared['budgets']==dict(memory_mib=32,heap_mib=512,io_bytes=4194304,deadline_seconds=60,denied_imports=878)
    for name in('input.json','expected.json','stdout.jsonl','raw-games.jsonl'):assert(RUN/name).stat().st_size<4194304
    command=prepared['command'];assert'--max-old-space-size=512'in command and'--wasm-max-mem-pages=512'in command and sha(Path(command[0]))=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
    terminal=report['process'];assert terminal==json.loads((RUN/'process-terminal.json').read_text())and terminal['exit_code']==0 and terminal['launcher_error']is None and terminal['seconds']<60 and terminal['pid_missing']and terminal['pgid_missing']and missing(terminal['pid'])and missing(terminal['pgid'],True)
    assert json.loads((RUN/'owned-process.json').read_text())==dict(pid=terminal['pid'],pgid=terminal['pgid'],command=command)and json.loads((RUN/'differences.json').read_text())==[]
    validator=manifest['validator'];assert validator['exit_code']==0 and validator['pgid_missing']and validator['seconds']<45 and missing(validator['pid'])and missing(validator['pgid'],True)
    for item in validator['tools']['tools'].values():assert sha(Path(item['path']))==item['sha256']
    read=static_reader(original);npc=manifest['npc_definition'];decl=read(npc['pointer'],72);assert decl.hex()==npc['raw72_hex'];ptr,length=struct.unpack_from('<II',decl,16);assert read(ptr,length).decode()==npc['name']=='Kobold Vermin'
    native=manifest['windows_reference'];exe=Path(native['path']).read_bytes();assert hashlib.sha256(exe).hexdigest()==native['sha256']=='eb5fd1c1b96e6180fcf5f3d685d90a61471af28d22e5f060c02b7b7663fbf79e'and len(exe)==native['bytes']==147995648
    tail=decl[24:69];assert tail.hex()==native['scalar_tail45_hex'];matches=[];at=0
    while(at:=exe.find(tail,at))>=0:matches.append(at);at+=1
    assert matches==native['scalar_tail_file_matches']==[118538720]and len(tail)==45 and native['executed']is False
    profile_commands=json.loads((PROFILE/'commands.json').read_text());assert all(x['exit_code']==0 and x['owned_pgid_missing']and missing(x['process_group_id'],True)for x in profile_commands)
    profile_state=json.loads((PROFILE/'run-state.json').read_text());assert profile_state['status']=='complete'and missing(profile_state['pid']);handles=json.loads((PROFILE/'after-index-process-receipt.json').read_text());assert handles['observations']['handles']['exit_code']==0
    identity_path=ROOT/'evidence/branding0138-identity-20261101T202528.536773Z/identity.json';assert sha(identity_path)=='da6db208afd9669c8600205643ab6061d6c2d075c086c0759090838b053cef5d'
    identity=json.loads(identity_path.read_text());assert identity['web']['original_sha256']==manifest['original_sha256']and identity['actual_build_length']==9
    assert read(identity['web']['build_pointer'],9)==b'382771e6c'and read(identity['web']['version_pointer'],7)==b'0.138.0'
    native_identity=identity['native'];assert native_identity['exe_sha256']==native['sha256']and exe[native_identity['build_file_offset']:native_identity['build_file_offset']+16]==b'382771e6c0.138.0'
    guard=native_identity['instruction_guard'];at=guard['instruction_file_offset'];insn=bytes.fromhex(guard['exact_instruction_bytes_hex']);assert exe[at:at+len(insn)]==insn and guard['length']==9
    expected_line=None;original_line=None
    for node in ast.walk(ast.parse((RUN/'source-snapshot/scripts/check_combat138.py').read_text())):
        if not isinstance(node,ast.Call):continue
        if isinstance(node.func,ast.Name)and node.func.id=='save'and node.args and isinstance(node.args[0],ast.BinOp)and isinstance(node.args[0].right,ast.Constant)and node.args[0].right.value=='expected.json':expected_line=node.lineno
        if isinstance(node.func,ast.Attribute)and node.func.attr=='Popen':original_line=node.lineno
    assert expected_line is not None and original_line is not None and expected_line<original_line
    after={n:sha(ROOT/n)for n in before};assert before==after
    save(out/'original-instruction-windows.json',proofs);save(out/'static-image-reads.json',read.proofs)
    result=dict(status='passed_scoped_read_only_review',version='0.138.0',build='382771e6c',comparison=str(RUN/'comparison.json'),comparison_sha256=sha(RUN/'comparison.json'),reviewer_sha256=sha(Path(__file__)),source_before=before,source_after=after,source_files=11,production_files=4,local_import_edges=closure_edges,production_direct_IO_calls=direct_io,expected_and_actual_byte_values_equal=True,expected_first_static_source_lines=dict(expected_save=expected_line,original_Popen=original_line),independent_numeric_recomparison=dict(counts),strict_record_bytes_recompared=recordbytes,full_record_stride=432,all_known_input_physical_bytes=True,allowed_unit_write_bytes=[288,289,290,291],game984_exact_f64_and_all_RNG_verified_per_operation=True,rawGame8192_observation_records=raw_index,rawGame_full_equality_claimed=False,phase_kind64_zero_pointer_cases=phase_cases,phase_fixture_scope='U64=0/U68=0 explicit numeric fixtures; no timer/destructor consumption and no complete owner/constructor proof',private_export_section_only=True,original_callees_byte_identical=True,entry=entry,wrong_914=identities[914],new_helper68536=identities[68536],old_helper68459=old_helper,new_helper_scope='Static four-arg ABI only; all125 raw G1972=0. Nonempty producer behavior remains unverified.',bounded_queries_sha256=sha(out/'bounded-WAT-and-queries.json'),instruction_windows_sha256=sha(out/'original-instruction-windows.json'),profile_manifest_sha256=sha(PROFILE/'manifest.json'),index_sha256=profile['database_sha256'],full_WAT_read=False,profile_commands_and_parent_terminal=True,process_observation=handles['observations']['process'].get('status'),native=dict(exe_sha256=native['sha256'],scalar_tail45_exact_file_matches=matches,scope='One declaration scalar tail only; no Windows function/ABI/layout/runtime equivalence'),identity_sidecar_sha256=sha(identity_path),actual_version_and_9byte_build_original_data_rechecked=True,native_identity_instruction_bytes_rechecked=True,terminal=terminal,validator_terminal=validator,new_original_cases=0,new_fullgame_frames=0,original_model_checker_builder_executed_by_reviewer=False,pending=['death/XP/loot','nonempty item/spell/proc sources','nonzero inherited context','Boss/kind3 accepted continuation','nonempty G1972/new helper68536','statistics/packet/visual payloads','full Game constructor/880/natural frames','Windows gameplay ABI/runtime','exhaustive IEEE754 proof'],elapsed_seconds=time.monotonic()-began)
    save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],numeric_counts=dict(counts),seconds=result['elapsed_seconds'])))
if __name__=='__main__':main()
