#!/usr/bin/env python3
"""Static1073 callback path plus narrow new-model guards,0 original calls."""
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict,replace
from collections import Counter
import hashlib,importlib.util,json,re,sqlite3,struct,sys,types
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
OBSERVER=ROOT/'evidence/incoming-callback-sources135-model-observer-20261102T002438.264636Z/sources.json'
OBSERVER_SHA='880fc4c769ee4da33a2261ea632bf021c873b32188d8dcbee70b92f31f77f59c'
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def model():
    #Isolate this new model plus its two pure leaf dependencies;do not import
    #core_spec.__init__ or execute any old scheduler/model/probe/checker.
    name='callback135_trace_core';pkg=types.ModuleType(name);pkg.__path__=[str(ROOT/'reconstruction/core_spec')];sys.modules[name]=pkg
    p=ROOT/'reconstruction/core_spec/incoming_callbacks135.py';spec=importlib.util.spec_from_file_location(name+'.incoming_callbacks135',p);mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod
def main():
    sys.dont_write_bytecode=True
    files=('reconstruction/core_spec/incoming_callbacks135.py','reconstruction/core_spec/binary32.py','reconstruction/core_spec/record_cells135.py','scripts/trace_incoming_callbacks135.py','reconstruction/core_spec/headless135.py','reconstruction/core_spec/level_cycle135.py','reconstruction/core_spec/selection_cycle135.py')
    before={n:sha(ROOT/n)for n in files};original=SOURCE.read_bytes();assert hashlib.sha256(original).hexdigest()==SOURCE_SHA
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('incoming-callbacks135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir();functions={};texts={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
        for index in(1073,984,914,921,1560):
            row=dict(db.execute('select *from functions where idx=?',(index,)).fetchone());stream.seek(row['wat_start']);data=stream.read(row['wat_end']-row['wat_start']);assert len(data)<2097152
            body=original[row['body_start']:row['body_end']];functions[index]=dict(body_start=row['body_start'],body_end=row['body_end'],body_bytes=len(body),body_sha256=hashlib.sha256(body).hexdigest(),wat_bytes=len(data),wat_sha256=hashlib.sha256(data).hexdigest());texts[index]=data.decode();(out/f'{index}.wat').write_bytes(data)
    windows={}
    for name,index,a,b,terms in(
        ('history_append_before_callbacks',1073,3350,3443,('i32.store offset=980','i32.store8 offset=45','f32.store offset=36','f32.store offset=28')),
        ('raw13_ordered_active_reduction',1073,3443,3566,('i32.load offset=1712','i32.load offset=1708','f32.const -0x0p+0','i32.const 13','f32.add','f32.gt')),
        ('GUID_contact_phase_shortcircuit',1073,3556,3590,('local.get 2','i64.eqz','local.get 3','i32.eqz','i32.load8_u offset=2587','br_if 2')),
        ('raw13_retaliation_and_phase_reread',1073,3580,3638,('i32.const 467','i32.const 13','call 914','i32.load8_u offset=2587')),
        ('item22_reduction',1073,3638,3775,('i32.load offset=2032','i32.load offset=2028','i32.const 22','f32.add','select')),
        ('item22_positive_gate_and_context774',1073,3774,3807,('local.get 1','f32.gt','local.get 27','i32.load8_u offset=774','i32.store8 offset=774','call 914')),
        ('two984_and_actual_HP_reread',1073,3807,3895,('i32.const 1024','i32.const 5','call 984','f32.load offset=1440','i32.load8_u offset=2578')),
        ('984_empty_source_earlyexit',984,8,25,('i32.load offset=2056','i32.const 36','i32.eqz','br_if 2')),
        ('984_dispatch_load_and_transient_context',984,173,225,('i32.load offset=32','i32.load offset=4','i32.store offset=476','i32.store offset=472')),
        ('984_tag_selector',984,250,265,('i32.const 12','i32.const 11','i32.le_u','i32.const 1','br_table')),
        ('ordinary921_contactflag1',921,7485,7492,('local.get 33','local.get 57','i32.const 1','i32.const 0','call 1073'))):
        text='\n'.join(texts[index].splitlines()[a-1:b]);assert all(t in text for t in terms),name
        if name=='two984_and_actual_HP_reread':assert text.count('call 984')==2
        windows[name]=dict(function=index,first_line=a,last_line=b,text=text,sha256=hashlib.sha256(text.encode()).hexdigest())
    lines=texts[984].splitlines();first_table=next(x for x in lines if 'br_table'in x);targets=re.findall(r'(\d+)\s+\(;@(\d+);\)',first_table);assert targets[41]==('31','6')
    tail='\n'.join(lines[-38:]);assert all(t in tail for t in('call 71889','i32.store offset=476','i32.store offset=472','local.get 41','call 1512'))
    windows['984_common_tail_restore_and_conditional1512']=dict(function=984,first_line=len(lines)-37,last_line=len(lines),text=tail,sha256=hashlib.sha256(tail.encode()).hexdigest())
    start=next(i for i,line in enumerate(lines)if 'block  ;; label = @6'in line);indent=len(lines[start])-len(lines[start].lstrip());end=next(i for i in range(start+1,len(lines))if lines[i].strip()=='end'and len(lines[i])-len(lines[i].lstrip())==indent)
    path='\n'.join(lines[end:end+21]);assert 'local.get 29'in path and'local.get 38'in path and'call 71889'in path and'local.get 41'in path
    windows['984_tag54_target_skips_all_event_branches']=dict(function=984,target_label=6,first_line=end+1,last_line=end+21,text=path,sha256=hashlib.sha256(path.encode()).hexdigest())
    #Readonly model source inspection demonstrates a gap,not producer proof.
    headless=(ROOT/'reconstruction/core_spec/headless135.py').read_text();assert 'buffs=buffs, modifiers=()'in headless and'incoming_item_effects=(),other_incoming_sources_absent=True'in headless
    assert sha(OBSERVER)==OBSERVER_SHA;observer=json.loads(OBSERVER.read_text());assert observer['original_calls']==0 and observer['source_unchanged']and len(observer['observations'])==921
    m=model();V=m.CallbackVector135;I=m.IncomingCallbacksInput135;B=lambda x:struct.unpack('<I',struct.pack('<f',x))[0]
    def live(kind,value=0,expiry=20):
        row=[None]*32;row[8:12]=struct.pack('<I',kind);row[24:28]=struct.pack('<I',B(expiry))
        if value is not None:row[12:16]=struct.pack('<I',B(value))
        return tuple(row)
    def item(kind,value):
        row=[None]*8;row[0]=kind
        if value is not None:row[4:8]=struct.pack('<I',B(value))
        return tuple(row)
    def definition(kind):return struct.pack('<I',kind)+bytes(32)
    base=I(B(10),B(-1),123,1,1,B(2),V(32,0,(),0),V(8,0,(),None),V(36,0,(),None));tests=[]
    def passed(label,values):
        proof=m.prove_post_history_callbacks135(values);assert proof.hp_before_minimum_one1440_bits==values.hp_after_history1440_bits;tests.append(dict(case=label,accepted=True,proof=asdict(proof)))
    def refused(label,fn):
        try:fn()
        except(m.UnknownIncomingCallbacks135,m.UnknownRecordRead135)as e:tests.append(dict(case=label,accepted=False,error=str(e)))
        else:raise AssertionError(label)
    passed('explicit_empty_sources_contact_nonzero',base)
    passed('zero_GUID_skips_item_and_984',replace(base,source_guid=0,items8=V(8,1,(item(22,3),)),modifiers36=V(36,1,(definition(0),))))
    passed('flag0_skips_item_and_984',replace(base,contact_flag3=0,items8=V(8,1,(item(22,3),)),modifiers36=V(36,1,(definition(0),))))
    passed('kind8_opaque_value_and_auxiliary_unused',replace(base,live32=V(32,1,(live(8,None),))))
    passed('expired13_payload_unknown_unused',replace(base,live32=V(32,1,(live(13,None,9),))))
    passed('raw13_ordered_cancellation',replace(base,live32=V(32,2,(live(13,2),live(13,-2)))))
    passed('item22_zero_base_amount',replace(base,item_retaliation_base_bits=0,items8=V(8,1,(item(22,2),))))
    passed('item7_unknown_value_unused',replace(base,items8=V(8,1,(item(7,None),))))
    passed('full36_tag54_noevent',replace(base,modifiers36=V(36,1,(definition(54),))))
    refused('raw13_active_positive',lambda:m.prove_post_history_callbacks135(replace(base,live32=V(32,1,(live(13,1),)))))
    refused('raw13_active_unknown_value',lambda:m.prove_post_history_callbacks135(replace(base,live32=V(32,1,(live(13,None),)))))
    refused('item22_positive',lambda:m.prove_post_history_callbacks135(replace(base,items8=V(8,1,(item(22,1),)))))
    refused('unknown_item_kind',lambda:m.prove_post_history_callbacks135(replace(base,items8=V(8,1,((None,)*8,)))))
    refused('unknown_modifier_kind',lambda:m.prove_post_history_callbacks135(replace(base,modifiers36=V(36,1,((None,)*36,)))))
    refused('unrestored984_kind',lambda:m.prove_post_history_callbacks135(replace(base,modifiers36=V(36,1,(definition(0),)))))
    bad54=list(definition(54));bad54[4]=None
    refused('copied54_payload_unknown',lambda:m.prove_post_history_callbacks135(replace(base,modifiers36=V(36,1,(tuple(bad54),)))))
    refused('unknown_physical_nonlive_owner',lambda:replace(base,items8=None))
    refused('phase2',lambda:m.prove_post_history_callbacks135(replace(base,phase2587=2)))
    kinds=Counter();reductions=Counter();unknowns=Counter();nonlive_shapes=Counter()
    for row in observer['observations']:
        owner=row['shape']['player_sources'];assert owner is not None
        vector=V(32,owner['live_count'],tuple(tuple(x)for x in owner['live_storage']),owner['live_capacity']);result=m.active_raw13_sum135(vector,row['stats']['now_bits']);assert not m.f.to_float(result)>0;reductions[str(result)]+=1
        for physical in vector.storage[:vector.count]:kinds[str(m.u32(physical,8))]+=1;unknowns['active_None_cells']+=sum(x is None for x in physical)
        assert all(row['unowned'][key]is None for key in('original_G2056_36B_vector','original_G2028_8B_item_vector'))
        nonlive_shapes[(len(row['shape']['sources']['item_modifiers']),len(row['shape']['sources']['definitions']))]+=1
    assert not kinds.get('13')and sum(reductions.values())==921
    after={n:sha(ROOT/n)for n in files};assert before==after
    result=dict(status='narrow_executable_callback_predicate_static_and_model_checks',original_sha256=SOURCE_SHA,original_calls=0,new_original_cases=0,production_scheduler_executions=0,source_before=before,source_after=after,functions=functions,windows=windows,selector54=dict(value=41,target_depth=31,target_label=6,rebuild1512_enabled=False),model_checks=tests,model_checks_kind='newmodule_selfcheck_not_original_differential',observer=dict(path=str(OBSERVER.relative_to(ROOT)),sha256=OBSERVER_SHA,observations=921,kind='pre_AI_model_source_observer_not_original_or_post_history_capture',raw13_reductions=dict(reductions),active_live_kinds=dict(kinds),unknown_cells=dict(unknowns),canonical_nonlive_semantic_tuple_sizes=[dict(items8=a,definitions36=b,observations=n)for(a,b),n in nonlive_shapes.items()],physical_nonlive_owners='unknown_null_all921;semantic empty tuples do not prove original source owners',last_frame=observer['observations'][-1]['frame'],last_level=observer['observations'][-1]['progression']['level']),api=dict(vector='CallbackVector135(stride,count,storage,capacity_word=None);complete active rows,unknown unusedcapacity remainsNone',partial='active_raw13_sum135(live32,now_bits) is not callbacks_complete',full='prove_post_history_callbacks135(IncomingCallbacksInput135(...)).callbacks_complete only afterallsourceproof',nonlive_unknown='None physical vector raisesUnknown;no tuple-empty promotion adapter'),limits=['No full1073 new differential;old163/40 cases neither rerun noradded.','Onlypost-history callbackblock;prefix/shield-break984/registry/history/HPminimumone/revival/death/keyedHP/Aura separate.','Current921 observer only proves no raw13 among its canonical preAI live sources;posthistory identity depends on earlierprefix source effects.','Original G2028/2032 andG2052/2056 current producer not established byobserver oroldheadless hardcodedempty.','All positive914 branches and984 kinds exceptfull54 rejected;negative modelguards not original acceptance.','Capacity/pointer not read by984 emptycount branch;unconsumed unknown headers/backing not filled.'])
    save(out/'trace.json',result);print(json.dumps(dict(output=str(out/'trace.json'),sha256=sha(out/'trace.json'),checks=len(tests),accepted=sum(x['accepted']for x in tests),observer_raw13_checks=921,source_sha256=before)))
if __name__=='__main__':main()
