#!/usr/bin/env python3
"""Expected-first whole2376 with explicit initialized EN/zhCN name-map inputs."""
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict,replace
import argparse,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from check_special2376_135 import (ROOT,FILES as OLD_FILES,sha,save,missing,corpus as quiet_corpus,real_input)
from trace_special2376_135 import build_special2376_135
from source_closure135 import core_sources
from core_spec import binary32 as f
from core_spec.record_cells135 import cells135,encode_row,UnknownRecordRead135
from core_spec.special2376_135 import SpecialState2376_135,projection_special2376_135,UnknownSpecial2376_135
from core_spec.special2376_notify135 import (SpecialLocale2376_135,tick_special2376_notify135,
    ELWYNN_ENGLISH_NAMES,ELWYNN_CHINESE_NAMES)
FILES=tuple(dict.fromkeys(('scripts/check_special2376_notify135.py','scripts/run_special2376_notify135_oracle.mjs')+OLD_FILES+core_sources(ROOT,'special2376_notify135.py')))


def state_from(value):
    fields=dict(value);fields['storage']=tuple(bytes.fromhex(row)if isinstance(row,str)else tuple(row)for row in fields['storage']);fields['player_xy_bits']=tuple(fields['player_xy_bits'])
    return SpecialState2376_135(**fields)


def state_json(state):
    fields=asdict(state);fields['storage']=[encode_row(cells135(row,40))for row in state.storage];return fields


def expected(state,locale):
    result=projection_special2376_135(tick_special2376_notify135(state,0,locale));result.pop('status')
    before=bytearray([0xa5]*2592)
    for at,value in((392,state.selected392),(396,state.target396),(2392,state.announcement_time2392_bits),(1888,0)):struct.pack_into('<I',before,at,value)
    before[2565]=state.announced2565;after=bytearray(before)
    for at,key in((392,'selected392'),(396,'target396'),(2392,'announcement_time2392_bits')):struct.pack_into('<I',after,at,result[key])
    struct.pack_into('<I',after,1888,len(result['packets']));after[2565]=result['announced2565']
    result['game_changes']=[[i,v]for i,v in enumerate(after)if before[i]!=v]
    return result


def corpus():
    old,_,_,provenance=quiet_corpus();cases=[];answers=[];labels=[]
    en=SpecialLocale2376_135(ELWYNN_ENGLISH_NAMES);zh=SpecialLocale2376_135(ELWYNN_CHINESE_NAMES)
    def add(group,state,locale,label,original=None):
        identifier=len(cases)
        physical=original if original is not None else [bytes(cells135(row,40)).hex()for row in state.storage]
        cases.append(dict(id=identifier,input=dict(state=state_json(state),zone=0,locale=dict(label=label,names=locale.names),original_storage=physical)))
        answers.append(dict(id=identifier,answer=expected(state,locale)));labels.append(dict(id=identifier,group=group,locale=label))
    for item in old:add('replay_previous71_quiet_domain',state_from(item['input']),en,'en_initialized')
    actual,_=real_input();first=replace(actual,now_bits=f.from_float(.025),navigation2564=1,announced2565=0,selected392=0,target396=0,announcement_time2392_bits=0)
    for locale,label in((en,'en_initialized'),(zh,'zhCN_initialized')):
        add('first_opening_scalar_state_four_special',first,locale,label)
        for marker in(0,1):
            for index in range(12):
                row=bytearray(actual.storage[0]);struct.pack_into('<Q',row,0,marker);struct.pack_into('<I',row,28,index)
                add('every_Elwynn_name_and_both_literal_suffixes',replace(first,storage=(bytes(row),),count=1),locale,label)
        logical=[];physical=[]
        for i,row in enumerate(first.storage):
            concrete=bytearray(row)
            for j in (*range(8,16),*range(36,40)):concrete[j]=(31+17*i+13*j)&255
            cells=list(concrete)
            for j in (*range(8,16),*range(36,40)):cells[j]=None
            logical.append(tuple(cells));physical.append(concrete.hex())
        add('opening_unknown_GUID_and_padding_never_read_or_materialized',replace(first,storage=tuple(logical)),locale,label,physical)
        rows=[]
        for row in first.storage:
            raw=bytearray(row);struct.pack_into('<Q',raw,0,1);rows.append(bytes(raw))
        for now in(300,300.0001):
            # One active object makes the chosen index explicit without a spawn.
            add('same_target_strict_300s_announcement_boundary',replace(first,storage=(rows[0],),count=1,now_bits=f.from_float(now),selected392=1,announced2565=1),locale,label)
    for marker in(0,1):
        row=bytearray(first.storage[0]);struct.pack_into('<Q',row,0,marker)
        for name in('A','A'*33,'A'*34,'守卫甲'*20):
            locale=SpecialLocale2376_135((('enemy.609',name),));add('explicit_name_UTF8_and_Vec_capacity_growth',replace(first,storage=(bytes(row),),count=1),locale,'controlled_initialized_name')
    missing_name=SpecialLocale2376_135(tuple(row for row in ELWYNN_CHINESE_NAMES if row[0]!='enemy.609'))
    add('explicit_locale_missing_key_uses_original_definition_name',first,missing_name,'zhCN_without_selected_name')
    negatives=[]
    for group,state in(('due20_NPC_pending',replace(first,now_bits=f.from_float(20))),
                        ('unknown_marker_read',replace(first,storage=(tuple([None]*8+list(first.storage[0][8:])),),count=1)),
                        ('unknown_required_notification_X',replace(first,storage=(tuple(list(first.storage[0][:16])+[None]*4+list(first.storage[0][20:])),),count=1))):
        try:tick_special2376_notify135(state,0,en)
        except(UnknownSpecial2376_135,UnknownRecordRead135)as error:negatives.append(dict(group=group,rejected=True,reason=str(error)))
        else:raise AssertionError(group)
    return cases,answers,labels,negatives,provenance


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--directory',type=Path);args=parser.parse_args()
    sources={file:sha(ROOT/file)for file in FILES}
    if args.directory:
        out=args.directory.resolve();config=json.loads((out/'config.json').read_text());assert config['source_sha256']==sources and not(out/'owned-process.json').exists()
    else:
        out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('special2376-notify0135-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir()
        inputs,answers,labels,negative,provenance=corpus()
        save(out/'input.json',inputs);save(out/'expected.json',answers);save(out/'case-labels.json',labels);save(out/'pending-boundaries.json',negative);save(out/'fixture-source.json',provenance)
        assert max((out/'input.json').stat().st_size,(out/'expected.json').stat().st_size)<=4194304
        manifest=build_special2376_135(out)
        config=dict(source_sha256=sources,cases=len(inputs),previous71_replayed_not_added=71,module_sha256=manifest['module_sha256'],
            original_body_sha256=manifest['entry']['body_sha256'],locale_input_scope='Explicit initialized Vec14<HashMap<UTF8,UTF8>> with real bucket/ctrl/SipHash13; no cold locale producer claim',
            memory_page_cap=512,denied_imports=878,io_cap_bytes=4194304,node_heap_mib=512,timeout_seconds=60)
        save(out/'config.json',config)
        for name in FILES:
            target=out/'source-snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
    frozen={str(out/name):sha(out/name)for name in('input.json','expected.json','manifest.json','config.json','special2376_135.wasm')}
    if args.prepare_only:print(json.dumps(dict(directory=str(out),prepared_only=True,cases=config['cases'],source_files=len(sources),frozen=frozen)));return
    node=ROOT/'.toolchain/runtime/node_modules/node/bin/node';assert sha(node)=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
    command=[str(node),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_special2376_notify135_oracle.mjs'),str(out),str(out/'input.json')]
    began=time.monotonic();launcher_error=None
    def interrupted(sig,frame):raise KeyboardInterrupt('Owned2376 notify launcher signal '+str(sig))
    previous=signal.signal(signal.SIGTERM,interrupted)
    with(out/'stdout.jsonl').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'))
        save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command,timeout_seconds=60))
        try:child.wait(timeout=60)
        except(subprocess.TimeoutExpired,KeyboardInterrupt,OSError)as error:launcher_error=str(error)
        finally:
            if child.poll()is None:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=2)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            signal.signal(signal.SIGTERM,previous)
    terminal=dict(pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True));after={file:sha(ROOT/file)for file in FILES}
    differences=[];runtime=None;unknown=0
    if child.returncode==0:
        inputs=json.loads((out/'input.json').read_text());wanted=json.loads((out/'expected.json').read_text());observed=[json.loads(v)for v in(out/'stdout.jsonl').read_text().splitlines()]
        assert len(wanted)==len(observed)==config['cases']
        for inp,expect,actual in zip(inputs,wanted,observed):
            assert expect['id']==actual['id'] and actual['stack_before']==actual['stack_after']
            logical=expect['answer'];physical=actual['answer'];normalized=dict(physical);normalized['storage']=[]
            for row,hexvalue,original in zip(logical['storage'],physical['storage'],inp['input']['original_storage']):
                cells=cells135(row,40);raw=bytes.fromhex(hexvalue);source=bytes.fromhex(original)
                assert len(raw)==40
                for offset,(known,value)in enumerate(zip(cells,raw)):
                    if known is None:
                        assert value==source[offset];unknown+=1
                    else:assert known==value,(actual['id'],offset,known,value)
                normalized['storage'].append(row)
            if logical!=normalized:differences.append(dict(id=actual['id'],expected=logical,actual=physical))
        runtime=json.loads((out/'special2376_notify135-runtime.json').read_text());assert runtime['actual_host_calls']==0 and runtime['unknown_input_cells_preserved']==unknown
    inputs_unchanged=all(sha(file)==value for file,value in frozen.items())
    comparison=dict(status='matched_scoped_full2376_notifications'if child.returncode==0 and not differences else'boundary_or_differences_preserved',
        directory=str(out),source_sha256_before=sources,source_sha256_after=after,source_files=len(sources),source_unchanged=sources==after,
        frozen_inputs_before=frozen,frozen_inputs_unchanged=inputs_unchanged,cases=config['cases'],previous71_replayed_not_added=71,differences=differences,
        unknown_cells_preserved_not_predicted=unknown,runtime=runtime,launcher_error=launcher_error,
        process=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,seconds=time.monotonic()-began,terminal=terminal),
        locale_producer_recovered=False,full2376_due_NPC_production_complete=False,shared52_roles_changed=False,new_independent_mainloop_frames=0,complete_game=False)
    save(out/'comparison.json',comparison)
    print(json.dumps(dict(directory=str(out),status=comparison['status'],cases=config['cases'],differences=len(differences),exit_code=child.returncode,terminal=terminal,comparison_sha256=sha(out/'comparison.json'))))
    assert child.returncode==0 and not differences and sources==after and inputs_unchanged and all(terminal.values()) and launcher_error is None


if __name__=='__main__':main()
