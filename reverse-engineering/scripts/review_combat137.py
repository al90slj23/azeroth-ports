#!/usr/bin/env python3
"""Read-only independent137 numeric/profile/export/native-data evidence review.
No original, production module, builder, checker or toolchain command executes.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import ast,hashlib,json,math,sqlite3,stat,struct,sys,time
sys.dont_write_bytecode=True
from review_opening_combat135 import leb,sections,static_reader,missing
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/combat0137-oracle-20261101T163523.434970Z'
PROFILE=ROOT/'evidence/wasm0137-profile-20261101T162221.947222Z'
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def exports(raw):
    _,_,p,end=next(x for x in sections(raw)if x[0]==7);n,p=leb(raw,p);out=[]
    for _ in range(n):
        size,p=leb(raw,p);name=raw[p:p+size].decode();p+=size;kind=raw[p];index,p=leb(raw,p+1);out.append([name,kind,index])
    assert p==end;return out

def function_identity(raw,index):
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
    signature=types[decl[index-imports]]
    _,_,p,end=next(x for x in parts if x[0]==10);count,p=leb(raw,p);assert count==n;wanted=None
    for i in range(imports,imports+n):
        size,start=leb(raw,p);p=start+size
        if i==index:wanted=dict(index=i,signature=signature,body_start=start,body_end=p,body_sha256=hashlib.sha256(raw[start:p]).hexdigest())
    assert p==end;return wanted

def F(word):return struct.unpack('<f',struct.pack('<I',word))[0]
def bits(value):
    try:return struct.unpack('<I',struct.pack('<f',value))[0]
    except OverflowError:return 0x7f800000 if value>0 else 0xff800000

def numeric_operation(rows,now,phase,total,op,counters):
    target=int(op['target_id']);index=next((i for i,row in enumerate(rows)if struct.unpack_from('<Q',row,112)[0]==target),None)
    result=list(rows)
    if phase!=1:counters['phase_rejected']+=1;return result,total
    if index is None:counters['missing_target']+=1;return result,total
    row=rows[index];u=lambda o:struct.unpack_from('<I',row,o)[0];signed=lambda o:struct.unpack_from('<i',row,o)[0]
    assert signed(244)==-1 and signed(40)!=3
    add=lambda a,b:bits(F(a)+F(b));mul=lambda a,b:bits(F(a)*F(b));now=F(now)
    multiplier=0x3f800000
    if now<F(u(148)):multiplier=add(multiplier,u(144))
    multiplier=add(multiplier,u(152)if now<F(u(156))else u(160)if now<F(u(164))else 0)
    multiplier=add(add(multiplier,u(368)),0)
    school=0x3dcccccd if(op['school']&254)==2 and F(u(372))>now else 0
    counters['new_school372_bonus_evaluations']+=bool(school)
    amount=mul(op['amount_bits'],add(multiplier,school));phase_scale=0x3f800000
    if signed(64)!=-1:
        if F(u(420))>now:phase_scale=0x3fc00000
        elif F(u(416))>now or any(struct.unpack_from('<I',x)[0]==0 and struct.unpack_from('<i',x,40)[0]==2 and struct.unpack_from('<Q',x,32)[0]==target for x in rows):phase_scale=0x3e800000
    amount=mul(amount,phase_scale)
    if u(0)==1:counters['dead_marker_rejected']+=1;return result,total
    damage=0x3f800000 if math.isnan(F(amount))or F(amount)<=1 else amount
    new_hp=bits(F(u(288))-F(damage));assert F(new_hp)>0,'Outside nonlethal proof domain'
    accounted=min(max(0,F(u(288))),F(damage));old_total=struct.unpack('<d',struct.pack('<Q',total))[0]
    new_total=struct.unpack('<Q',struct.pack('<d',old_total+accounted))[0]
    counters['accepted_nonlethal']+=1;counters['f64_total_differs_from_f32_accumulation']+=float(F(bits(old_total+accounted)))!=old_total+accounted
    changed=bytearray(row);struct.pack_into('<I',changed,288,new_hp);result[index]=bytes(changed)
    for i,(a,b)in enumerate(zip(rows,result)):
        assert all(x==y or i==index and 288<=offset<292 for offset,(x,y)in enumerate(zip(a,b)))
    return result,new_total

def main():
    began=time.monotonic();out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('combat0137-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    report=json.loads((RUN/'comparison.json').read_text());manifest=json.loads((RUN/'manifest.json').read_text());profile=json.loads((PROFILE/'manifest.json').read_text())
    assert sha(RUN/'comparison.json')=='d6a8a3e4ea448f933f8e01b871193e597ca42f52549df1471d4dcb68cdb1c72c'
    assert report['complete']and report['mismatch_cases']==0 and report['source_before']==report['source_after']
    for name,digest in report['source_before'].items():assert sha(ROOT/name)==digest==sha(RUN/'source-snapshot'/name)
    assert len(report['source_before'])==11
    io=[];production=[p for p in report['source_before']if p.startswith('reconstruction/')]
    assert set(production)=={'reconstruction/core_spec/__init__.py','reconstruction/core_spec/binary32.py','reconstruction/core_spec/combat137.py','reconstruction/core_spec/upgrade_values.py'}
    for name in production:
        for node in ast.walk(ast.parse((RUN/'source-snapshot'/name).read_text())):
            if isinstance(node,ast.Call):
                fn=node.func;label=fn.id if isinstance(fn,ast.Name)else fn.attr if isinstance(fn,ast.Attribute)else''
                if label in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__'):io.append([name,label])
    assert not io
    for name,digest in report['artifacts'].items():assert sha(RUN/name)==digest
    assert sha(RUN/'stdout.jsonl')==report['output_sha256']and sha(RUN/'stderr.log')==report['stderr_sha256']and not(RUN/'stderr.log').stat().st_size
    original=Path(profile['original_path']).read_bytes();module=(RUN/manifest['module_file']).read_bytes();assert hashlib.sha256(original).hexdigest()==profile['original_sha256']==manifest['original_sha256']
    a,b=sections(original),sections(module);assert[x[0]for x in a]==[x[0]for x in b]and not any(x[0]==8 for x in a)
    assert all(original[x:y]==module[u:v]for(k,x,_,y),(_,u,_,v)in zip(a,b)if k!=7)
    prior=exports(original);assert exports(module)==prior+[['research137_damage913',0,913],['research137_stack0',3,0]]and['__wbindgen_malloc',0,91933]in prior
    entry=function_identity(original,913);wrong=function_identity(original,914)
    assert entry['signature']==['7f7e7d7f7f7f7f','']and wrong['signature']==['7f7f7f7f7f7f','']
    for key,value in entry.items():assert manifest['entry'][key]==value
    read_static=static_reader(original)
    assert len(module)==90941154 and len(original)==90941108
    with sqlite3.connect(Path(profile['database_path']).resolve().as_uri()+'?mode=ro',uri=True)as c:
        c.row_factory=sqlite3.Row;function=dict(c.execute('select * from functions where idx=913').fetchone())
        for key in('body_start','body_end'):assert function[key]==entry[key]
        index_counts={table:c.execute('select count(*) from '+table).fetchone()[0]for table in('functions','calls','iconsts','memops')}
        assert index_counts==profile['counts']
    assert stat.S_IMODE(Path(profile['database_path']).stat().st_mode)==0o444
    assert sha(Path(profile['database_path']))==profile['database_sha256']and sha(Path(profile['wat_path']))==profile['wat_sha256']
    with Path(profile['wat_path']).open('rb')as f:f.seek(function['wat_start']);wat=f.read(function['wat_end']-function['wat_start'])
    assert wat==(RUN/'913.wat').read_bytes()and hashlib.sha256(wat).hexdigest()==manifest['entry']['wat_sha256']
    lines=wat.decode().splitlines();proofs=[]
    for label,start,end in [('phase_and432_stride',1,49),('school_mask_and_U372_target',1111,1162),('HP288_only_numeric_write',1426,1454),('actual_f64_total984',1569,1580)]:
        proofs.append(dict(label=label,function=913,function_lines=[start,end],instructions=lines[start-1:end]))
    assert sum('f64.store offset=984'in l for l in lines)==1
    rows=json.loads((RUN/'input.json').read_text());expected=json.loads((RUN/'expected.json').read_text());actual=[json.loads(x)for x in(RUN/'stdout.jsonl').read_text().splitlines()];labels=json.loads((RUN/'labels.json').read_text());counts=Counter();known_bytes=0;phase_owned_empty_pointer_cases=[]
    assert len(rows)==len(expected)==len(actual)==80 and expected==actual
    for c,w,a in zip(rows,expected,actual):
        assert c['id']==w['id']==a['id'];s=c['state'];records=[bytes.fromhex(x)for x in s['units432_hex']];total=int(s['accounted_total_bits'])
        assert all(len(x)==432 for x in records)and s['sources']==dict(items2028=[],spells2052=[],other_procs_absent=True)
        assert len({struct.unpack_from('<Q',x,112)[0]for x in records})==len(records)
        if any(struct.unpack_from('<I',x,64)[0]==0 and struct.unpack_from('<I',x,68)[0]==0 for x in records):phase_owned_empty_pointer_cases.append(c['id'])
        assert len(c['operations'])==len(a['answers'])<=16
        for op,observed in zip(c['operations'],a['answers']):
            assert op['context']==0;counts['operations']+=1
            records,total=numeric_operation(records,s['now_bits'],s['phase2587'],total,op,counts)
            prediction=dict(units432_hex=[x.hex()for x in records],accounted_total_bits=str(total),rng_words=s['rng_words'])
            assert prediction==observed,(c['id'],op,prediction,observed);known_bytes+=sum(map(len,records))
    assert counts['operations']==report['calls']==125 and Counter(x['group']for x in labels)==report['groups']
    runtime=report['runtime'];assert runtime==json.loads((RUN/'runtime.json').read_text())
    assert runtime['cases']==runtime['fresh_instances']==80 and runtime['full_original913_calls']==125 and runtime['actual_host_calls']==0 and runtime['denied_imports']==878 and runtime['peak_memory_bytes']<=33554432
    assert len(runtime['stack_checks'])==80*2+125 and all(x['returned']and x['before']==x['after']==1048576 for x in runtime['stack_checks'])
    assert all(runtime[k]is False for k in('application_start_called','windows_exe_executed','network_used','user_saves_accessed','shared52_roles_changed'))
    prepared=json.loads((RUN/'prepared.json').read_text());assert prepared['expected_before_original']and prepared['artifacts']==report['artifacts']
    assert prepared['budgets']==dict(memory_mib=32,heap_mib=512,io_bytes=4194304,deadline_seconds=60,denied_imports=878)
    for x in('input.json','expected.json','stdout.jsonl'):assert(RUN/x).stat().st_size<4194304
    command=prepared['command'];assert'--max-old-space-size=512'in command and'--wasm-max-mem-pages=512'in command
    terminal=report['process'];assert terminal['exit_code']==0 and terminal['launcher_error']is None and terminal['seconds']<60 and missing(terminal['pid'])and missing(terminal['pgid'],True)
    assert terminal==json.loads((RUN/'process-terminal.json').read_text())and json.loads((RUN/'differences.json').read_text())==[]
    native_report=ROOT/'evidence/native0137-declaration-20261101T164138.951728Z/correspondence.json';native=json.loads(native_report.read_text());exe=Path(manifest['windows_reference']['path']).read_bytes();assert hashlib.sha256(exe).hexdigest()==native['native_sha256']==manifest['windows_reference']['sha256']and len(exe)==147844608
    pe=struct.unpack_from('<I',exe,0x3c)[0];assert exe[pe:pe+4]==b'PE\0\0';count=struct.unpack_from('<H',exe,pe+6)[0];optional=pe+24;size=struct.unpack_from('<H',exe,pe+20)[0];assert struct.unpack_from('<H',exe,optional)[0]==0x20b;image_base=struct.unpack_from('<Q',exe,optional+24)[0]
    native_sections=[]
    for i in range(count):
        pos=optional+size+i*40;vsize,rva,rawsize,file=struct.unpack_from('<4I',exe,pos+8);native_sections.append((rva,max(vsize,rawsize),file))
    def native_offset(pointer):
        address=pointer-image_base
        for start,length,file in native_sections:
            if start<=address<start+length:return file+address-start
        raise AssertionError('Native pointer outside sections')
    for value in native['rows']:
        pointer=value['wasm_pointer'];tail=read_static(pointer+24,45);at=value['native_scalar_file_offset'];assert tail==bytes.fromhex(value['scalar_tail45_hex'])==exe[at:at+45]
        nameptr,n=struct.unpack('<2I',read_static(pointer+16,8));name=read_static(nameptr,n);assert name.decode()==value['name']
        nativeptr,native_len=struct.unpack_from('<2Q',exe,at-16);file=native_offset(nativeptr)
        assert nativeptr==value['native_name_pointer']and native_len==n==value['native_name_length']and file==value['native_name_file_offset']and exe[file:file+n]==name
    assert len(native['rows'])==12 and all(b['native_scalar_file_offset']-a['native_scalar_file_offset']==80 and b['wasm_pointer']-a['wasm_pointer']==72 for a,b in zip(native['rows'],native['rows'][1:]))
    assert native['native_executed']is False and native['wasm_instantiated']is False
    profile_commands=json.loads((PROFILE/'commands.json').read_text());assert all(x['exit_code']==0 and x['owned_pgid_missing']and missing(x['process_group_id'],True)for x in profile_commands)
    profile_state=json.loads((PROFILE/'run-state.json').read_text());assert profile_state['status']=='complete'and missing(profile_state['pid'])
    handles=json.loads((PROFILE/'after-index-process-receipt.json').read_text());assert handles['observations']['handles']['exit_code']==0
    pending=json.loads((RUN/'pending-checks.json').read_text());assert pending['new_original_calls']==0 and len(pending['checks'])==4 and all(x['pending']for x in pending['checks'])
    for name,digest in report['source_before'].items():assert sha(ROOT/name)==digest==sha(RUN/'source-snapshot'/name)
    result=dict(status='passed_scoped_read_only_review',comparison=str(RUN/'comparison.json'),comparison_sha256=sha(RUN/'comparison.json'),reviewer_sources={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),'scripts/review_opening_combat135.py':sha(ROOT/'scripts/review_opening_combat135.py')},version='0.137.0',build='d171b8f9f',source_files=11,production_files=4,current_and_frozen_SHA_match=True,production_direct_IO_calls=io,nonexport_sections_byte_identical=True,only_private_exports_added=True,real_entry=entry,wrong137_index914=wrong,original_WAT_proofs=proofs,
        cases=80,full_original913_calls=125,all_output_equals_frozen_expected=True,independent_numeric_recomparison=dict(counts),strict_record_bytes_recompared=known_bytes,write_mask='Only target U288..291 changes in admitted operations; G984 f64 and RNG checked for each operation',source_contract='Explicit complete controlled432B input records; empty items/spells/procs,context0,nonlethal,noBoss/kind3 accepted continuation',
        phase_kind64_zero_pointer_cases=phase_owned_empty_pointer_cases,phase_fixture_scope='U64=0 phase fixtures retain explicit U68=0 input; timers/destructor are not consumed here. This verifies numeric branches only, not complete special-NPC owner/constructor validity.',profile=dict(manifest_sha256=sha(PROFILE/'manifest.json'),full_WAT_sha_verified=True,index_sha_verified=True,index_mode='0444/mode=ro',counts=index_counts,commands_exit0_and_missing=True,parent_complete_and_missing=True,handles_lsof_exit0=True,ps_observation=handles['observations']['process'].get('status')),native=dict(receipt_sha256=sha(native_report),declarations=12,scalar_bytes_each=45,wasm_stride=72,native_stride=80,names_and_actual64bit_pointers_verified=True,scope='Data only; Windows damage address/ABI/Game/Unit layout/runtime remain unverified'),terminal=terminal,pure_pending_checks_observed=4,pending_checks_rerun=False,original_or_producer_executed_by_reviewer=False,new_original_cases=0,new_fullgame_frames=0,elapsed_seconds=time.monotonic()-began)
    (out/'static-image-reads.json').write_text(json.dumps(read_static.proofs,indent=2)+'\n');result['static_image_reads_sha256']=sha(out/'static-image-reads.json')
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],seconds=result['elapsed_seconds'],numeric_counts=dict(counts))))
if __name__=='__main__':main()
