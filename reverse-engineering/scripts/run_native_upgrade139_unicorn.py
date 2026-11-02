#!/usr/bin/env python3
"""Execute only original513B x86_64 instructions with fail-closed Unicorn hooks."""
from pathlib import Path
import hashlib,json,struct,sys,time
sys.dont_write_bytecode=True
import unicorn
from unicorn import Uc,UcError,UC_ARCH_X86,UC_MODE_64,UC_PROT_READ,UC_PROT_WRITE,UC_PROT_EXEC,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_INVALID
from unicorn import x86_const as X

STATE_PAGE=0x100000000
STATE=STATE_PAGE+256
STATE_EXTENT=64  # Controlled fixture size, not a recovered native sizeof.
STACK=0x300000000
RSP=STACK+0x8008
SENTINEL=0x500000000
NATIVE_FIELDS=(36,20,24,28,32)


def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')


def run(case,manifest,pages,guard_probe=None):
    start=time.monotonic();kind,tier=case['kind'],case['tier'];definition=manifest['definitions'][case['definition_index']];mu=Uc(UC_ARCH_X86,UC_MODE_64);codebase=manifest['native_start'];codeend=manifest['native_end'];instructions={int(r['address'],16):r for r in manifest['native_instructions']}
    for page,blob,permissions in pages:
        mu.mem_map(page,4096,UC_PROT_READ|(UC_PROT_EXEC if permissions=='RX'else 0));mu.mem_write(page,blob)
    mu.mem_map(STATE_PAGE,4096,UC_PROT_READ);mu.mem_map(STACK,65536,UC_PROT_READ|UC_PROT_WRITE);mu.mem_map(SENTINEL,4096,UC_PROT_READ|UC_PROT_EXEC);mu.mem_write(SENTINEL,b'\x90');mu.mem_write(RSP,struct.pack('<Q',SENTINEL))
    before_canary=bytes((j*13+case['id']*7+3)&255 for j in range(64));after_canary=bytes((j*17+case['id']*11+9)&255 for j in range(64));mu.mem_write(STATE-64,before_canary);mu.mem_write(STATE+STATE_EXTENT,after_canary)
    owner=[None]*STATE_EXTENT;allowed=[]
    def initialized(offset,payload,label):
        mu.mem_write(STATE+offset,payload);owner[offset:offset+len(payload)]=payload;allowed.append((STATE+offset,STATE+offset+len(payload),label))
    if guard_probe!='uninitialized_owner':initialized(NATIVE_FIELDS[kind]if kind<5 else 36,struct.pack('<I',case['input_word']),'owned_consumed_field')
    if kind==2:
        initialized(0,struct.pack('<Q',definition['native_va']),'owned_definition_pointer');d=definition['native_va'];allowed.append((d+117,d+118,'actual_definition_exec117'))
        if definition['execution']==11:
            allowed.append((d,d+16,'actual_definition_name_fatptr'))
            if definition['name_bytes']in(9,11):allowed.append((definition['native_string_va'],definition['native_string_va']+definition['name_bytes'],'actual_definition_slug'))
    switch=manifest['switch_va'];allowed.append((switch,switch+20,'original_switch5'))
    if kind<5:allowed.append((manifest['native_tables'][kind]+4*tier,manifest['native_tables'][kind]+4*tier+4,'original_upgrade_table_element'))
    constants={0:[0x1464d5d10,0x1464d5b60],1:[0x147a1f88c,0x14653d154],2:[],3:[0x1464d5e04,0x1464e2df8],4:[0x1464d5ea0,0x1464d5e04]}
    for p in constants.get(kind,[]):allowed.append((p,p+4,'original_scalar'))
    allowed.append((RSP,RSP+8,'initialized_return_address'))
    snapshot=bytes(mu.mem_read(STATE_PAGE,4096));stack_before=bytes(mu.mem_read(STACK,65536));nonvolatile={getattr(X,'UC_X86_REG_'+name):0x1234000011110000+i*0x10001 for i,name in enumerate(['RBX','RBP','RSI','RDI','R12','R13','R14','R15'])}
    vector_nonvolatile={getattr(X,'UC_X86_REG_XMM'+str(i)):(0x112233445566778899aabbccddeeff00+i)for i in range(6,16)}
    for register,value in nonvolatile.items():mu.reg_write(register,value)
    for register,value in vector_nonvolatile.items():mu.reg_write(register,value)
    mu.reg_write(X.UC_X86_REG_RSP,RSP);mu.reg_write(X.UC_X86_REG_RCX,STATE);mu.reg_write(X.UC_X86_REG_RDX,kind);mu.reg_write(X.UC_X86_REG_R8,tier);mu.reg_write(X.UC_X86_REG_MXCSR,0x1f80)
    trace=[];reads=[];writes=[];violation=[]
    def stop(reason,**extra):
        if not violation:violation.append(dict(reason=reason,**extra))
        mu.emu_stop()
    def code_hook(uc,address,size,user):
        if address==SENTINEL:uc.emu_stop();return
        if not codebase<=address<codeend or address not in instructions:return stop('PC_outside_original_function_or_instruction_boundary',address=address,size=size)
        row=instructions[address];original=bytes.fromhex(row['bytes'])
        if len(original)!=size or bytes(uc.mem_read(address,size))!=original:return stop('Modified_or_misaligned_original_instruction',address=address,size=size)
        mnemonic=row['assembly'].split()[0].upper()
        if mnemonic in('CALL','SYSCALL','SYSENTER','INT','INT3','UD2','HLT'):return stop('Forbidden_call_syscall_or_trap',address=address,assembly=row['assembly'])
        trace.append(address)
    def read_hook(uc,access,address,size,value,user):
        selected=next((label for lo,hi,label in allowed if lo<=address and address+size<=hi),None)
        if selected is None:return stop('Uninitialized_or_out_of_whitelist_read',PC=uc.reg_read(X.UC_X86_REG_RIP),address=address,size=size)
        reads.append(dict(PC=uc.reg_read(X.UC_X86_REG_RIP),address=address,size=size,source=selected))
    def write_hook(uc,access,address,size,value,user):
        writes.append(dict(PC=uc.reg_read(X.UC_X86_REG_RIP),address=address,size=size,value=value));stop('All_guest_memory_writes_forbidden',address=address,size=size)
    def invalid_hook(uc,access,address,size,value,user):stop('Unmapped_or_protection_access',access=access,address=address,size=size);return False
    mu.hook_add(UC_HOOK_CODE,code_hook);mu.hook_add(UC_HOOK_MEM_READ,read_hook);mu.hook_add(UC_HOOK_MEM_WRITE,write_hook);mu.hook_add(UC_HOOK_MEM_INVALID,invalid_hook)
    error=None
    try:mu.emu_start(codebase,SENTINEL,timeout=1000000,count=2000)
    except UcError as e:error=str(e)
    rip=mu.reg_read(X.UC_X86_REG_RIP);rsp=mu.reg_read(X.UC_X86_REG_RSP);returned=not violation and error is None and rip==SENTINEL and rsp==RSP+8 and trace and instructions[trace[-1]]['assembly']=='RET'
    if not returned and not violation and error is None:violation.append(dict(reason='Budget_or_nonreturn',RIP=rip,RSP=rsp))
    assert bytes(mu.mem_read(STATE_PAGE,4096))==snapshot and bytes(mu.mem_read(STACK,65536))==stack_before
    for register,value in nonvolatile.items():assert mu.reg_read(register)==value
    for register,value in vector_nonvolatile.items():assert mu.reg_read(register)==value
    for page,blob,permissions in pages:assert bytes(mu.mem_read(page,4096))==blob
    return dict(id=case['id'],returned=bool(returned),result_bits=(mu.reg_read(X.UC_X86_REG_XMM0)&0xffffffff)if returned else None,instructions=len(trace),PC_trace=trace,reads=reads,guest_writes=writes,violations=violation,error=error,return_RIP=rip,entry_RSP=RSP,return_RSP=rsp,MXCSR=mu.reg_read(X.UC_X86_REG_MXCSR),owner64_known_or_None=owner,owner_page_unchanged=True,stack64KiB_unchanged=True,all_PE_pages_unchanged=True,Win64_nonvolatile_preserved=True,seconds=time.monotonic()-start)


def main():
    out=Path(sys.argv[1]).resolve();config=json.loads(Path(sys.argv[2]).read_text());manifest=json.loads((out/'manifest.json').read_text());raw=Path(config['input_file']).read_bytes();assert sha(raw)==config['input_sha256']and unicorn.__version__=='2.1.4';cases=json.loads(raw);assert 1<=len(cases)<=4096;guards=config.get('guard_mode',False);assert type(guards)is bool
    from unicorn.unicorn_py3.unicorn import uclib
    library=Path(uclib._name).resolve();assert library==Path(config['unicorn_library']).resolve()and sha(library.read_bytes())==config['unicorn_library_sha256']and Path(unicorn.__file__).resolve().parent==library.parent.parent
    pages=[]
    for row in manifest['native_pages']:
        blob=(out/row['file']).read_bytes();assert len(blob)==4096 and sha(blob)==row['sha256'];pages.append((row['va'],blob,row['permissions']))
    calls=0;instructions=0;error=None;completed=0
    try:
        for c in cases:
            assert set(c)=={'id','kind','tier','definition_index','input_word','label'}|({'guard_probe'}if guards else set())and all(type(c[k])is int for k in['id','kind','tier','definition_index','input_word'])and c['id']==completed and 0<=c['kind']<(6 if guards else 5)and 0<=c['tier']<(6 if guards else 5)and 0<=c['definition_index']<114 and 0<=c['input_word']<1<<32
            if guards:assert(c['guard_probe'],c['kind'],c['tier'])in[('uninitialized_owner',0,2),('invalid_variant',5,2),('out_of_range_tier',0,5)]
            answer=run(c,manifest,pages,c.get('guard_probe'));calls+=1;instructions+=answer['instructions'];print(json.dumps(answer),flush=True);completed+=1
            if not guards and not answer['returned']:raise RuntimeError('Original native function did not return: '+json.dumps(answer['violations']))
            if guards and answer['returned']:raise RuntimeError('Harness accepted a forbidden guard probe')
    except BaseException as e:error=repr(e);raise
    finally:save(out/('native-guards-runtime.json'if guards else'native-runtime.json'),dict(kind='Unicorn2.1.4_actual_original_x86_64_instruction_emulation',native_function_calls_completed=0 if guards else completed,native_function_attempts=calls,harness_negative_guard_probes=completed if guards else 0,native_instructions=instructions,Unicorn_version=unicorn.__version__,core_version=unicorn.uc_version(),Unicorn_library=str(library),Unicorn_library_sha256=sha(library.read_bytes()),function_bytes=513,original_code_patched=False,Windows_application_executions=0,Windows_syscalls=0,guest_host_calls=0,guest_network_calls=0,guest_saves=0,PC_restricted_to_original_function_or_ret_sentinel=True,all_guest_writes_forbidden=True,all_reads_initialized_or_original_PE_bytes=True,error=error))


if __name__=='__main__':main()
