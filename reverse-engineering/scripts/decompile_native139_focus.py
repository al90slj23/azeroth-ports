#!/usr/bin/env python3
"""Fresh139 Windows upgrade-table consumers, no target execution.

Reuse only the PE/LEA scanner and bounded Ghidra script, never old native
addresses or acceptance. Inputs, JVM state, process receipts and output stay
on the external disk. Scan first; --prepared-run resumes that exact scan.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import signal
import struct
import subprocess
import sys
import time

from decompile_latest_native_focus import PE, scan, TABLES
from incoming139_tools import ROOT, original, static_reader, SOURCE_SHA

NATIVE=ROOT/'originals/official-release-20261102T011227.335145Z/windows-0.139.0/AzerothSurvivors.exe'
NATIVE_SHA='0e8e314df4d78ab211b1bef5c48d78d713ed64260894af342f998d298d74d274'
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
save=lambda p,d:Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
load=lambda p:json.loads(Path(p).read_text())


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def owned(run,label,command,timeout,env=None):
    started=time.monotonic()
    with(run/(label+'.stdout')).open('w')as so,(run/(label+'.stderr')).open('w')as se:
        child=subprocess.Popen(command,env=env,stdout=so,stderr=se,start_new_session=True)
        save(run/(label+'-start.json'),dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=timeout,target_executed=False))
        expired=False
        try:code=child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            expired=True;os.killpg(child.pid,signal.SIGTERM)
            try:code=child.wait(timeout=10)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);code=child.wait()
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,timed_out=expired,seconds=time.monotonic()-started,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True))
    save(run/(label+'-terminal.json'),terminal)
    return terminal


def prepare():
    assert NATIVE.stat().st_size==150595584 and sha(NATIVE)==NATIVE_SHA
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('native139-upgrade-focus-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    sources={str(Path(__file__).relative_to(ROOT)):sha(__file__)}
    for n in ['scripts/decompile_latest_native_focus.py','scripts/AzerothLatestFocusedDecompile.java','scripts/incoming139_tools.py','scripts/wasm139_profile.py']:
        sources[n]=sha(ROOT/n)
    raw,identity,_=original();read=static_reader(raw,identity);tables=[]
    for (name,(fmt,values)),address in zip(TABLES.items(),[5405004,5405040,5405076,5405112,5405148],strict=True):
        encoded=struct.pack('<'+fmt*5,*values)
        assert read(address,20)==encoded,(name,address)
        tables.append(dict(research_label=name,current_WASM_address=address,bytes_hex=encoded.hex(),sha256=hashlib.sha256(encoded).hexdigest()))
    del raw
    pe=PE(NATIVE.read_bytes());constants,hits,selection=scan(pe)
    save(out/'current-wasm-tables.json',tables);save(out/'constants.json',constants);save(out/'lea-candidates.json',hits);save(out/'selection.json',selection)
    save(out/'pe-map.json',dict(image_base=hex(pe.base),sections=pe.sections,pdata_ranges=len(pe.ranges)))
    assert {v['name']for v in constants}==set(TABLES)
    assert len(selection)>=2,'Too few fresh multi-table consumers; no old addresses used'
    for i,selected in enumerate(selection):
        t=owned(out,'llvm-'+str(i),['objdump','-d','--x86-asm-syntax=intel','--start-address='+selected['start'],'--stop-address='+selected['end_exclusive'],str(NATIVE)],30)
        assert t['exit_code']==0 and not t['timed_out'] and t['pid_missing'] and t['pgid_missing']
    frozen={n:sha(out/n)for n in ['current-wasm-tables.json','constants.json','lea-candidates.json','selection.json','pe-map.json']}
    install=ROOT/'.toolchain/native-install.json'
    save(out/'prepared.json',dict(version='0.139.0',build='f79c5e2b4',native_file=str(NATIVE),native_sha256=NATIVE_SHA,wasm_sha256=SOURCE_SHA,sources=sources,frozen=frozen,install_manifest_sha256=sha(install),new_native_addresses_derived_from_this_PE=True,old_native_addresses_read=False,old_acceptance_transferred=False,target_executed=False,selected_functions=len(selection),candidate_instruction_boundaries_verified=False))
    print(json.dumps(dict(directory=str(out),prepared_sha256=sha(out/'prepared.json'),selected_functions=len(selection),fresh_LEA_candidates=len(hits),target_executed=False)),flush=True)
    return out


def decompile(out):
    assert out.is_dir() and ROOT/'evidence' in out.parents
    p=load(out/'prepared.json');assert p['native_sha256']==NATIVE_SHA and sha(NATIVE)==NATIVE_SHA
    assert p['wasm_sha256']==SOURCE_SHA and p['new_native_addresses_derived_from_this_PE']
    for n,h in p['sources'].items():assert sha(ROOT/n)==h,n
    for n,h in p['frozen'].items():assert sha(out/n)==h,n
    assert not (out/'ghidra-start.json').exists(),'Existing owned analysis must be polled, not restarted'
    install=load(ROOT/'.toolchain/native-install.json');assert sha(ROOT/'.toolchain/native-install.json')==p['install_manifest_sha256']
    for n in ['project','tmp','settings','cache']:(out/n).mkdir()
    env=dict(os.environ)
    env.update({k:install[k]for k in ['JAVA_HOME','GHIDRA_INSTALL_DIR']})
    env.update(GHIDRA_HEADLESS_MAXMEM='3G',GHIDRA_JAVA_OPTIONS='',TMPDIR=str(out/'tmp'))
    env['GHIDRA_HEADLESS_JAVA_OPTIONS']=' '.join(['-Djava.io.tmpdir='+str(out/'tmp'),'-Dapplication.settingsdir='+str(out/'settings'),'-Dapplication.cachedir='+str(out/'cache'),'-Djava.util.prefs.userRoot='+str(out/'cache/prefs')])
    command=[str(Path(install['GHIDRA_INSTALL_DIR'])/'support/analyzeHeadless'),str(out/'project'),'fixed139-upgrade-consumers','-import',str(NATIVE),'-readOnly','-deleteProject','-noanalysis','-scriptPath',str(ROOT/'scripts'),'-log',str(out/'ghidra.log'),'-scriptlog',str(out/'script.log'),'-postScript','AzerothLatestFocusedDecompile.java',str(out/'functions.json'),str(out/'selection.json')]
    terminal=owned(out,'ghidra',command,300,env)
    f=out/'functions.json';d=load(f)if f.exists()else dict(functions=[])
    pattern=re.compile(r'bad instruction|overlaps instruction|Could not find normalized switch variable|truncation of jumptable|unrecovered jumptable|Too many branches',re.I)
    for fn in d['functions']:
        fn['flow_warning_pattern']=bool(pattern.search(fn.get('pseudocode','')+fn.get('diagnostic','')))
        fn['accepted_for_bounded_semantic_inspection']=fn.get('completed')is True and fn.get('undecoded_bytes')==0 and not fn['flow_warning_pattern']and not fn.get('instructions_crossing_selected_end')and not fn.get('unresolved_computed_jump_sites')and not fn.get('error')
    if f.exists():save(f,d)
    same=all(sha(ROOT/n)==h for n,h in p['sources'].items());unchanged=sha(NATIVE)==NATIVE_SHA
    result=dict(version='0.139.0',build='f79c5e2b4',kind='fresh_native139_bounded_static_decompilation_not_execution',native_sha256=NATIVE_SHA,wasm_sha256=SOURCE_SHA,terminal=terminal,prepared_sha256=sha(out/'prepared.json'),functions_sha256=sha(f)if f.exists()else None,selected_functions=p['selected_functions'],pseudocode_completed=sum(x.get('completed')is True for x in d['functions']),accepted_for_bounded_semantic_inspection=sum(x['accepted_for_bounded_semantic_inspection']for x in d['functions']),source_before_after_same=same,original_native_unchanged=unchanged,target_executed=False,full_program_semantics_verified=False,native_Game_Unit_ABI_restored=False,new_runtime_cases=0,complete_games=0,old_native_addresses_used=False,old_runtime_acceptance_transferred=False,limits=['Freshtable/xref/.pdata/Ghidrafunctioninspectiononly;reusedscannerlabelsdonotprovefunctionpurpose.','LLVM/Ghidraregisterprototypesareanalystannotations,notrecoveredRustsourceorABIguarantees.','Selectedshortfunctionsarenottheactualdamage/AI/mainloop/networkengine;semanticassociationrequiresseparateinspection.','NoWindows/Wine/VMgameexecutionandnoWASM/nativebehavioralequivalenceclaimed.'])
    save(out/'run-summary.json',result)
    print(json.dumps(dict(directory=str(out),summary_sha256=sha(out/'run-summary.json'),**result)),flush=True)
    if terminal['exit_code']or terminal['timed_out']or not terminal['pid_missing']or not terminal['pgid_missing']or not same or not unchanged:raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepared-run',type=Path);args=parser.parse_args()
    if args.prepared_run:decompile(args.prepared_run.resolve())
    else:prepare()
