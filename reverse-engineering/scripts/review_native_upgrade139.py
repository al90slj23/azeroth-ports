#!/usr/bin/env python3
"""Different-author readonly2150 review; no Unicorn/author/original execution.

The instruction addresses below describe a pure reconstructed branch plan used
to audit saved PC/read traces. They are not fed to an emulator or target engine.
"""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import ast,hashlib,json,os,re,sqlite3,struct,sys,time,zipfile
sys.dont_write_bytecode=True
from review_frame_clock139 import classify,fraction,rounded
from review_combat139 import parse_module,local_closure
ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'evidence/native-upgrade139-full-20261102T124511.825553Z'
HAND='57d6668d23a5b79ced19f62154db55babcae46050a5b684a73fe1fb53f1f12f7'
COMP='cc2da65bc3266331971c5adee19c3576073982e12020b5016c7336052d9a3e2a'
FOCUS=ROOT/'evidence/native139-upgrade-focus-20261102T115527.969158Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PEFILE=ROOT/'originals/official-release-20261102T011227.335145Z/windows-0.139.0/AzerothSurvivors.exe'
SIGN=0x80000000;INF=0x7f800000;NAN=0x7fc00000
STATE=0x100000100;RSP=0x300008008;SENTINEL=0x500000000
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,x:Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
u=lambda b,o=0:struct.unpack_from('<I',b,o)[0]
q=lambda b,o=0:struct.unpack_from('<Q',b,o)[0]
def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0);return False
    except ProcessLookupError:return True
def kind(v):return classify(v,8,23)
def number(v):return fraction(v,8,23)
def round32(v,negative_zero=False):return rounded(v,8,23,negative_zero)
def plus(a,b):
    ca,cb=kind(a),kind(b)
    if'nan'in(ca,cb):return NAN
    if ca==cb=='infinity':return NAN if(a^b)&SIGN else a
    if ca=='infinity':return a
    if cb=='infinity':return b
    return round32(number(a)+number(b),a==b==SIGN)
def minus(a,b):return plus(a,b^SIGN)
def times(a,b):
    ca,cb=kind(a),kind(b);sign=(a^b)&SIGN
    if'nan'in(ca,cb)or(ca=='infinity'and cb=='zero')or(cb=='infinity'and ca=='zero'):return NAN
    if'infinity'in(ca,cb):return sign|INF
    return round32(number(a)*number(b),bool(sign))
def divide(a,b):
    ca,cb=kind(a),kind(b);sign=(a^b)&SIGN
    if'nan'in(ca,cb)or ca==cb=='infinity'or ca==cb=='zero':return NAN
    if ca=='infinity'or cb=='zero':return sign|INF
    if cb=='infinity':return sign
    return round32(number(a)/number(b),bool(sign))
def positive_or_zero(a):
    if kind(a)=='nan':return 0
    if kind(a)=='infinity':return 0 if a&SIGN else a
    return a if number(a)>0 else 0
def scalar(c,definition,tables):
    k,t,x=c['kind'],c['tier'],c['input_word']
    if k==0:return divide(tables[0][t],plus(times(round32(Fraction(x)),0x3f000000),0x3f800000))
    if k==1:factor=divide(plus(x,0xbe4ccccd),0x3f4ccccd)
    elif k==2:
        cap=12
        if definition['execution']==11:cap=2 if definition['slug']in{'seal_fate','soul_fire','lightwell','faerie_fire'}else 0
        return round32(Fraction(min(cap-x if x<=cap else 0,tables[2][t])))
    elif k==3:factor=times(minus(0x40a00000,x),0x3e800000)
    else:factor=divide(minus(0x40c00000,x),0x40a00000)
    return times(positive_or_zero(factor),tables[k][t])

class PE:
    def __init__(self,data):
        self.data=data;nt=u(data,60);assert data[:2]==b'MZ'and data[nt:nt+4]==b'PE\0\0'
        machine,ns=struct.unpack_from('<HH',data,nt+4);opt=nt+24;osz=struct.unpack_from('<H',data,nt+20)[0]
        assert machine==0x8664 and struct.unpack_from('<H',data,opt)[0]==0x20b
        self.base=q(data,opt+24);self.sections=[]
        for j in range(ns):
            p=opt+osz+j*40;name=data[p:p+8].split(b'\0')[0].decode();vs,rva,n,off=struct.unpack_from('<4I',data,p+8);self.sections.append((name,vs,rva,n,off))
        rva,n=struct.unpack_from('<II',data,opt+112+3*8);assert n%12==0
        raw=self.read(self.base+rva,n);self.ranges=[struct.unpack_from('<3I',raw,j)for j in range(0,n,12)]
    def read(self,va,n):
        candidates=[off+va-self.base-rva for _,vs,rva,size,off in self.sections if self.base+rva<=va and va+n<=self.base+rva+size]
        assert len(candidates)==1,(hex(va),n)
        p=candidates[0];return self.data[p:p+n]

def main():
    start=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir()
    assert sha(BATCH/'task-handoff.json')==HAND and sha(BATCH/'comparison.json')==COMP
    h=load(BATCH/'task-handoff.json');comp=load(BATCH/'comparison.json');prepared=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');report=load(ROOT/'reports/2026-11-02-native-upgrade0139.json')
    assert len(h['frozen_author_files'])==7
    for n,v in h['frozen_author_files'].items():assert sha(ROOT/n)==v
    assert comp['sources_before']==comp['sources_after']==prepared['sources']and len(prepared['sources'])==14
    assert local_closure(prepared['sources'])==sorted(prepared['source_import_edges'])==sorted(comp['source_import_edges'])and len(comp['source_import_edges'])==14
    for n,v in prepared['sources'].items():assert sha(ROOT/n)==sha(BATCH/'source-snapshot'/n)==v
    for table in(comp['frozen'],comp['artifacts'],prepared['frozen']):
        for n,v in table.items():assert sha(BATCH/n)==v
    assert sha(BATCH/'prepared.json')==h['prepared_sha256']
    assert comp['expected_before_both_originals']and prepared['expected_before_both_original_engines']and prepared['original_inputs_contain_expected']is False
    assert load(BATCH/'expectation-read-audit.json')==dict(opened=[],forbidden=[],static_manifest_data_supplied=True,no_runtime_output_supplied=True)
    pe=PE(PEFILE.read_bytes());assert hashlib.sha256(pe.data).hexdigest()==m['native_sha256']=='0e8e314df4d78ab211b1bef5c48d78d713ed64260894af342f998d298d74d274'
    a,z=m['native_start'],m['native_end'];assert z-a==513 and(a-pe.base,z-pe.base,m['native_pdata_match'][1][2])in pe.ranges
    assert pe.ranges[m['native_pdata_match'][0]]==tuple(m['native_pdata_match'][1])
    assert pe.read(a,513)==(BATCH/'native513.bin').read_bytes()and hashlib.sha256(pe.read(a,513)).hexdigest()==m['native513_sha256']
    instructions={int(x['address'],16):x for x in m['native_instructions']};assert len(instructions)==108
    prior=load(FOCUS/'functions.json')['functions'][0];assert m['native_instructions']==prior['instructions']
    llvm={}
    for line in(FOCUS/'llvm-0.stdout').read_text().splitlines():
        match=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\t',line)
        if match:llvm[int(match[1],16)]=bytes.fromhex(match[2])
    cursor=a
    for pc,row in sorted(instructions.items()):
        b=bytes.fromhex(row['bytes']);assert pc==cursor and pe.read(pc,len(b))==b==llvm[pc];cursor+=len(b)
    assert cursor==z
    for page in m['native_pages']:
        raw=(BATCH/page['file']).read_bytes();assert len(raw)==4096 and hashlib.sha256(raw).hexdigest()==page['sha256']and raw==pe.read(page['va'],4096)
        assert page['permissions']==('RX'if page['va']==a&~4095 else'R')
    assert len(m['native_pages'])==15
    targets=[m['switch_va']+i for i in struct.unpack('<5i',pe.read(m['switch_va'],20))];assert targets==m['switch_targets']and all(p in instructions for p in targets)
    tables=[list(struct.unpack('<5I',pe.read(p,20)))for p in m['native_tables']];assert tables==m['tables']
    for p,v in m['native_scalars'].items():assert u(pe.read(int(p),4))==v
    original_raw=SOURCE.read_bytes();assert hashlib.sha256(original_raw).hexdigest()==m['wasm_sha256']=='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
    original=parse_module(original_raw);private_raw=(BATCH/m['wasm_module_file']).read_bytes();private=parse_module(private_raw)
    assert sha(BATCH/m['wasm_module_file'])==m['wasm_module_sha256']and len(private['sections'])==len(original['sections'])
    for old,new in zip(original['sections'],private['sections']):
        assert old['kind']==new['kind']
        if old['kind']!=7:assert original_raw[old['start']:old['end']]==private_raw[new['start']:new['end']]
    assert private['exports']==original['exports']+[tuple(row)for row in m['wasm_added_exports']]and len(original['imports'])==882
    def data(address,n):
        ans=bytearray(n)
        for at,p,size in original['data_segments']:
            if at is None:continue
            lo,hi=max(address,at),min(address+n,at+size)
            if lo<hi:ans[lo-address:hi-address]=original_raw[p+lo-at:p+hi-at]
        return bytes(ans)
    for address,table in zip(m['wasm_tables'],tables):assert list(struct.unpack('<5I',data(address,20)))==table
    defs_wasm={}
    for i in range(114):
        address=5882740+88*i;b=data(address,88);slug=data(u(b,12),u(b,16)).decode();assert slug not in defs_wasm;defs_wasm[slug]=(address,b)
    definitions=[]
    for i in range(114):
        va=0x147323958+120*i;b=pe.read(va,120);ptr,length=q(b),q(b,8);slug=pe.read(ptr,length).decode();wva,w=defs_wasm[slug]
        d=dict(index=i,slug=slug,native_va=va,native_string_va=ptr,name_bytes=length,wasm_va=wva,execution=b[117],native120_hex=b.hex(),wasm88_hex=w.hex());assert d==m['definitions'][i]and b[117]==w[84];definitions.append(d)
    assert len({v['slug']for v in definitions})==114
    proof=m['wasm_functions']['25511'];lo,hi=original['bodies'][25511];assert hashlib.sha256(original_raw[lo:hi]).hexdigest()==proof['body_sha256']
    db=sqlite3.connect((ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z/index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);lo,hi=db.execute('select wat_start,wat_end from functions where idx=25511').fetchone()
    with(ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z/official-0.139.0-full.wat').open('rb')as stream:stream.seek(lo);wat=stream.read(hi-lo)
    assert hashlib.sha256(wat).hexdigest()==proof['WAT_sha256']and wat==(BATCH/'static/25511.wat').read_bytes()
    (out/'25511.wat').write_bytes(wat)
    assert proof['signature']==['7f7f7f','7d']and all('offset='+str(v)in wat.decode()for v in m['wasm_tables'])
    # Independent reconstructed legal branch plan. No instructions are executed.
    def pc(v):return 0x145f64000+int(v,16)
    def span(l,r):return[p for p in sorted(instructions)if pc(l)<=p<=pc(r)]
    common=span('cc0','cd5');tail=span('e52','e78');shared=span('e1e','e2f')
    def plan(k,d):
        if k==0:return common+span('cd8','d10')
        if k==1:return common+span('df8','e16')+shared
        if k==3:return common+span('dd0','df6')+shared
        if k==4:return common+span('d11','d37')+shared
        result=common+span('d3c','d49')
        if d['execution']!=11:return result+tail
        result+=span('d4f','d5a')
        if d['name_bytes']==11:
            result+=span('e30','e4e')
            return result+(span('e79','e82')+span('e58','e78')if d['slug']=='faerie_fire'else span('e50','e78'))
        result+=span('d60','d64')
        if d['name_bytes']!=9:return result+span('e50','e78')
        result+=span('d6a','d88')
        if d['slug']=='seal_fate':return result+tail
        result+=span('d8e','da7')
        if d['slug']=='soul_fire':return result+tail
        return result+(span('dad','dcb')+tail if d['slug']=='lightwell'else span('dad','dc5')+span('e50','e78'))
    def read_plan(c,d,trace):
        k,t=c['kind'],c['tier'];p=d['native_string_va'];v=d['native_va']
        rows={pc('cce'):(m['switch_va']+4*k,4,'original_switch5'),pc('ce2'):(STATE+36,4,'owned_consumed_field'),pc('cf2'):(0x1464d5d10,4,'original_scalar'),pc('cfa'):(m['native_tables'][0]+4*t,4,'original_upgrade_table_element'),pc('d00'):(0x1464d5b60,4,'original_scalar'),pc('d10'):(RSP,8,'initialized_return_address'),pc('e09'):(STATE+20,4,'owned_consumed_field'),pc('e0e'):(0x147a1f88c,4,'original_scalar'),pc('e16'):(0x14653d154,4,'original_scalar'),pc('e25'):(m['native_tables'][k]+4*t,4,'original_upgrade_table_element'),pc('e2f'):(RSP,8,'initialized_return_address'),pc('de1'):(0x1464d5e04,4,'original_scalar'),pc('de9'):(STATE+28,4,'owned_consumed_field'),pc('dee'):(0x1464e2df8,4,'original_scalar'),pc('d22'):(0x1464d5ea0,4,'original_scalar'),pc('d2a'):(STATE+32,4,'owned_consumed_field'),pc('d2f'):(0x1464d5e04,4,'original_scalar'),pc('d3c'):(STATE,8,'owned_definition_pointer'),pc('d44'):(v+117,1,'actual_definition_exec117'),pc('d4f'):(v,8,'actual_definition_name_fatptr'),pc('d52'):(v+8,8,'actual_definition_name_fatptr'),pc('e3a'):(p,8,'actual_definition_slug'),pc('e47'):(p+3,8,'actual_definition_slug'),pc('d74'):(p,8,'actual_definition_slug'),pc('d77'):(p+8,1,'actual_definition_slug'),pc('d98'):(p,8,'actual_definition_slug'),pc('d9b'):(p+8,1,'actual_definition_slug'),pc('db7'):(p,8,'actual_definition_slug'),pc('dba'):(p+8,1,'actual_definition_slug'),pc('e5a'):(STATE+24,4,'owned_consumed_field'),pc('e67'):(m['native_tables'][2]+4*t,4,'original_upgrade_table_element'),pc('e78'):(RSP,8,'initialized_return_address')}
        return[dict(PC=p,address=rows[p][0],size=rows[p][1],source=rows[p][2])for p in trace if p in rows]
    cases=load(BATCH/'inputs.json');expected=load(BATCH/'expected.json');native=[json.loads(v)for v in(BATCH/'native-actual.jsonl').read_text().splitlines()];wasm=[json.loads(v)for v in(BATCH/'wasm-actual.jsonl').read_text().splitlines()]
    assert len(cases)==len(expected)==len(native)==len(wasm)==2150 and len({(v['kind'],v['tier'],v['definition_index'],v['input_word'])for v in cases})==2150
    counts=Counter();classes=Counter();readcounts=Counter();pcs=set();reference=[]
    for i,(c,e,n,w)in enumerate(zip(cases,expected,native,wasm,strict=True)):
        assert i==c['id']==e['id']==n['id']==w['id'];d=definitions[c['definition_index']];pred=scalar(c,d,tables);category=kind(pred);classes[category]+=1
        assert e==dict(id=i,result_bits=pred,result_class=category)
        nan_input=c['kind']in(1,3,4)and kind(c['input_word'])=='nan'
        if nan_input:
            assert pred==n['result_bits']==w['result_bits']==0
            counts['NaN_input_cases']+=1 # Author gate is class-only. Independent observation here is +0.
        else:assert pred==n['result_bits']==w['result_bits'];counts['strict_nonNaN_result_bits']+=1
        trace=plan(c['kind'],d);assert trace==n['PC_trace']and len(trace)==n['instructions'];pcs.update(trace)
        reads=read_plan(c,d,trace);assert reads==n['reads'];readcounts.update(v['source']for v in reads)
        owner=[None]*64;field=(36,20,24,28,32)[c['kind']];owner[field:field+4]=struct.pack('<I',c['input_word'])
        if c['kind']==2:owner[:8]=struct.pack('<Q',d['native_va'])
        assert owner==n['owner64_known_or_None']
        for rd in reads:
            if STATE<=rd['address']<STATE+64:assert None not in owner[rd['address']-STATE:rd['address']-STATE+rd['size']]
        assert n['returned']and n['violations']==n['guest_writes']==[]and n['error']is None
        assert n['return_RIP']==SENTINEL and n['entry_RSP']==RSP and n['return_RSP']==RSP+8 and n['MXCSR']&~63==0x1f80
        for flag in('owner_page_unchanged','stack64KiB_unchanged','all_PE_pages_unchanged','Win64_nonvolatile_preserved'):assert n[flag]is True
        assert w['owner_page_unchanged']and w['stack_before']==w['stack_after']==1048576
        counts['fixtures']+=1;counts['kind'+str(c['kind'])]+=1;counts['instructions']+=len(trace);counts['data_reads']+=len(reads);counts['read_bytes']+=sum(v['size']for v in reads);counts['owner_None_cells']+=sum(v is None for v in owner)
        reference.append(dict(id=i,result_bits=pred,result_class=category,NaN_input=nan_input,trace_instructions=len(trace),data_reads=len(reads)))
    assert classes==Counter(finite=1840,zero=290,infinity=20)and counts['NaN_input_cases']==60 and counts['strict_nonNaN_result_bits']==2090
    assert counts['instructions']==48335 and counts['data_reads']==13750 and counts['read_bytes']==67090 and counts['owner_None_cells']==114840 and len(pcs)==94
    for d in definitions:
        for tier in range(5):
            for count in(0,1,2):assert any(c['kind']==2 and c['tier']==tier and c['input_word']==count and c['definition_index']==d['index']for c in cases)
    # Negative attempts stop before inadmissible read or external CALL. They are
    # not three accepted original semantic fixtures or panic behavior tests.
    guards=load(BATCH/'guard-inputs.json');guard_actual=[json.loads(s)for s in(BATCH/'native-guards-actual.jsonl').read_text().splitlines()];assert len(guards)==len(guard_actual)==3
    guard_reasons=['Uninitialized_or_out_of_whitelist_read','Uninitialized_or_out_of_whitelist_read','Forbidden_call_syscall_or_trap'];guardtraces=[common+span('cd8','ce2'),span('cc0','cce'),common+span('cd8','cdc')+span('e9f','ea6')+span('eaf','eb7')]
    for i,(g,v,reason,trace)in enumerate(zip(guards,guard_actual,guard_reasons,guardtraces,strict=True)):
        assert g['id']==v['id']==i and v['returned']is False and v['result_bits']is None and v['guest_writes']==[]and v['error']is None
        assert [a['reason']for a in v['violations']]==[reason]and v['PC_trace']==trace and v['instructions']==len(trace)
    cfg=load(BATCH/'config.json');assert sha(Path(cfg['input_file']))==cfg['input_sha256']==comp['frozen']['inputs.json']
    # Verify installed engine bytes, without importing Unicorn or loading dylib.
    wheel=Path(prepared['Unicorn_wheel']);assert sha(wheel)==prepared['Unicorn_wheel_sha256']==cfg['wheel_sha256']=='d6c93e0f60328d8f4a1792af3f834137a28050fcc2305f2ec01efe8558a9844e'
    library=Path(cfg['unicorn_library']);site=library.parent.parent;wheel_files=0
    with zipfile.ZipFile(wheel)as zf:
        for name in zf.namelist():
            if name.startswith('unicorn/')and Path(name).suffix in('.py','.dylib'):assert hashlib.sha256(zf.read(name)).hexdigest()==sha(site/name[len('unicorn/'):]);wheel_files+=1
    assert sha(library)==cfg['unicorn_library_sha256']==prepared['Unicorn_library_sha256']
    # Read frozen instrumentation source rather than executing it. Memory
    # conservation rawbefore/after pairs are not stored, only true flags.
    native_source=(ROOT/'scripts/run_native_upgrade139_unicorn.py').read_text();wasm_source=(ROOT/'scripts/run_native_upgrade139_wasm.mjs').read_text()
    for token in ['UC_PROT_READ|(UC_PROT_EXEC if permissions',"mu.mem_map(STATE_PAGE,4096,UC_PROT_READ)","mu.mem_map(STACK,65536,UC_PROT_READ|UC_PROT_WRITE)","if mnemonic in('CALL','SYSCALL','SYSENTER','INT','INT3','UD2','HLT')",'all_guest_writes_forbidden=True','Uninitialized_or_out_of_whitelist_read','original=bytes.fromhex(row[\'bytes\'])',"timeout=1000000,count=2000",'UC_HOOK_MEM_INVALID','mu.reg_write(X.UC_X86_REG_MXCSR,0x1f80)']:assert token in native_source
    assert 'cases=JSON.parse(input)'in wasm_source and 'research139_upgrade25511(STATE,c.kind,c.tier)'in wasm_source
    assert "if(before!==hex(PAGE,4096)||SP.value!==1048576)"in wasm_source and 'outsideHash===hash('in wasm_source
    runtime={label:load(BATCH/(label+'-runtime.json'))for label in['native','wasm','native-guards']}
    assert runtime['native']==comp['runtimes']['native']and runtime['wasm']==comp['runtimes']['wasm']
    assert runtime['native']['native_function_calls_completed']==runtime['native']['native_function_attempts']==2150 and runtime['native']['native_instructions']==48335
    assert runtime['native-guards']['native_function_calls_completed']==0 and runtime['native-guards']['native_function_attempts']==runtime['native-guards']['harness_negative_guard_probes']==3
    assert runtime['wasm']['full25511_calls']==2150 and runtime['wasm']['fresh_instances']==1 and runtime['wasm']['imports_denied']==882 and runtime['wasm']['actual_host_calls']==0 and runtime['wasm']['outside_owner_page_batch_hash_unchanged']
    for label,rt in runtime.items():
        assert rt['error']is None and rt['Windows_application_executions']==0
        if label.startswith('native'):assert rt['guest_host_calls']==rt['Windows_syscalls']==rt['guest_network_calls']==0
        terminal=load(BATCH/(label+'-owned-terminal.json'));assert terminal==h['owned_processes'][label]and terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing'];assert missing(terminal['pid'])and missing(terminal['pgid'],True)
        owned=load(BATCH/(label+'-owned-start.json'));assert owned['pid']==owned['pgid']==terminal['pid']and owned['deadline_seconds']==120
    failed=h['failed_first_pilot_preserved'];d=ROOT/failed['directory'];assert sha(d/'comparison.json')==failed['comparison_sha256']and load(d/'native-owned-terminal.json')['exit_code']==-4
    assert(d/'native-actual.jsonl').read_bytes()==b''and not(d/'native-runtime.json').exists()
    oldE=load(d/'expected.json');oldW=[json.loads(s)for s in(d/'wasm-actual.jsonl').read_text().splitlines()];assert len(oldE)==len(oldW)==13 and all(a['result_bits']==b['result_bits']for a,b in zip(oldE,oldW))
    capabilities=[]
    for item in report['capability_probes']:
        d=ROOT/item['directory']
        for n,v in item['artifacts'].items():assert sha(d/n)==v
        assert load(d/'owned-terminal.json')==item['terminal']and item['terminal']['Windows_application_executions']==item['terminal']['original_function_calls']==0
        capabilities.append(dict(path=item['directory'],exit_code=item['terminal']['exit_code'],stdout=(d/'stdout.log').read_text(),original_function_calls=0))
    assert [v['exit_code']for v in capabilities]==[-4,0]
    for prior in h['prior_success_pilots_excluded']:assert sha(ROOT/prior['directory']/'comparison.json')==prior['comparison_sha256']
    assert not any(n.startswith(('core_spec','resource_spec','unicorn'))for n in sys.modules)
    for n,v in h['frozen_author_files'].items():assert sha(ROOT/n)==v
    helper_sha={n:sha(ROOT/'scripts'/n)for n in ['review_frame_clock139.py','review_combat139.py']}
    save(out/'independent-reference.json',reference)
    result=dict(status='pass_current139_native513_and_WASM25511_scoped2150_readonly_independent_review',author='/root/collection139_finish',reviewer='/root/growth139_world',author_handoff_sha256=HAND,comparison_sha256=COMP,reviewer_source_sha256=sha(__file__),independent_helpers=helper_sha,frozen_author7=h['frozen_author_files'],source_files=14,import_edges=14,counts=dict(counts),result_classes=dict(classes),unique_native_PC_boundaries=len(pcs),native_static_boundaries=108,native_read_source_counts=dict(readcounts),native_original_PE_pages=15,actual_definitions=114,negative_guard_probes=3,capability_probes=capabilities,Unicorn_wheel_installed_files_matched=wheel_files,original_executions=0,author_production_checker_builder_runner_executions=0,original_engine_imports=0,Windows_application_executions=0,independent_reference_sha256=sha(out/'independent-reference.json'),seconds=time.monotonic()-start,limits=['2150unique fixtures supplied both saved engines; not4300unique fixtures. Nativeinstructionemulations2150 and fullWASM25511entries2150 are distinct layers.','Only513B scalar and matching25511; noWindowsApp/exe/Wine/VM/bootstrap/fullABI/damageAI/mainloop/network/save behavior is accepted.','60classification-only author cases are NaNinput-related; independent saved outputs are all+zero, actualoutputNaNcount0; NaNpayload/sign equivalence unclaimed.','Native64B andWASM80B controlledpartial fixtures are notsizeof/naturalAppowner proofs; original114defs onlyexercise countscalar kind2, not114fullskill behaviors.','AllPC/read traces independently recomputed; unchangedPE/owner/stack flags are runtime instrumentation+source checks, not reread rawbeforeafterbytepairs.','WASM outside32MiB ownerpage hash preserved only asbatchbool, nointermediate or rawhashpair stored.','Negative3 probes are refused harnessattempts; noforeignCALL/panic behavior execution.','FirstSIGILL Nativepilot0rows/unknown result andsandbox2NOP capability failure are retained; successfulunsandboxed2NOP is capabilityevidence, notNativegameexecution.'])
    save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),result_classes=dict(classes),seconds=result['seconds'])),flush=True)
if __name__=='__main__':main()
