#!/usr/bin/env python3
"""Independent readonly G656 owner source trace and historical460 CAS audit."""
from pathlib import Path
from collections import Counter
import argparse,ast,hashlib,importlib.util,json,re,sqlite3,struct,sys,time,zlib
sys.dont_write_bytecode=True
import review_player_motion135 as M
import review_stats138 as H  # Binary function/static-data parser only.
from review_opening_combat135 import JsonlReader
import review_opening_combat135 as J
ROOT=M.ROOT;RUN=ROOT/'evidence/motion-aux-owner135-20261102T005437.610338Z'
SHA='572c0a668e89bd03b966be6a8b8aff970a76812a640b0f882e16c08220879c9a'
CAPTURE=ROOT/'evidence/opening-combat0135-oracle-20261101T232156.684647Z'
CAPTURE_SHA='521db52b9d97637212460083a7ea88b9038d63871536d6635edc21645e0bd622'
GUARDS=(604,652,2032,2056,1804,1852,1816,1828,1840,1864,2116)
NAMES={604:'timed12',652:'active84',1804:'areas',1852:'hits112',1816:'effects120',1828:'delayed56',2116:'companions'}
FATAL=('collect','claims','spawn','special','terminal')
sha=M.sha;load=M.load
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to((ROOT/'evidence').resolve());out.mkdir();start=time.monotonic()
    reviewers={str(p.relative_to(ROOT)):sha(p)for p in(Path(__file__),Path(M.__file__),Path(H.__file__),Path(J.__file__))}
    for n,h in reviewers.items():p=out/'reviewer-source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    assert sha(RUN/'comparison.json')==SHA;report=load(RUN/'comparison.json');prepared=load(RUN/'prepared.json');handoff=load(RUN/'task-handoff.json');static=load(RUN/'static-proof.json')
    assert report['status']=='scoped_auxiliary_owner_historical_match'and(report['new_original_calls'],report['historical_stage_records'],report['differences'])==(0,6488,0)
    files=report['source_sha256_before'];assert len(files)==20 and files==report['source_sha256_after']
    for n,h in files.items():assert sha(ROOT/n)==sha(RUN/'source-snapshot'/n)==h,n
    edges=M.source_edges(RUN/'source-snapshot',files);assert edges==[tuple(x)for x in report['source_import_edges']]and len(edges)==48
    prod={n for n in files if n.startswith('reconstruction/')};todo=['reconstruction/core_spec/motion_aux_owner135.py'];seen=set()
    while todo:
        n=todo.pop()
        if n in seen:continue
        seen.add(n);todo.extend(b for a,b in edges if a==n)
    assert seen==prod and len(prod)==15
    for n,h in report['artifact_sha256'].items():assert sha(RUN/n)==h
    for n,h in handoff['new_files'].items():assert sha(ROOT/n)==h
    assert sha(RUN/'static-proof.json')==report['static_proof_sha256']==handoff['static_proof_sha256']
    source=(RUN/'source-snapshot/reconstruction/core_spec/motion_aux_owner135.py').read_text();tree=ast.parse(source)
    literal=lambda name:next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets))
    definitions=literal('ADMITTED_DEFINITIONS135');assert literal('EMPTY_SOURCE_COUNTS135')==GUARDS and literal('FATAL_TAIL_EVENTS135')==FATAL
    assert 'return owner'in source and'Nonempty or reallocated auxiliary owner'in source and'owner.pointer660!=8'in source
    original=M.ORIGINAL.read_bytes();assert hashlib.sha256(original).hexdigest()==M.ORIGINAL_SHA==report['original_sha256'];read=H.static_image_reader(original)
    ids=tuple(int(x)for x in static['functions']);assert len(ids)==36;identities=H.function_ids(original,ids);texts={};functions={}
    with sqlite3.connect((M.PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(M.PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
        for idx in ids:
            row=dict(db.execute('select *from functions where idx=?',(idx,)).fetchone());i=identities[idx];assert(row['body_start'],row['body_end'])==(i['body_start'],i['body_end']);stream.seek(row['wat_start']);raw=stream.read(row['wat_end']-row['wat_start']);assert len(raw)<16777216
            assert raw==(RUN/'static'/f'{idx}.wat').read_bytes()and hashlib.sha256(raw).hexdigest()==static['functions'][str(idx)]['wat_sha256']and i['body_sha256']==static['functions'][str(idx)]['body_sha256'];texts[idx]=raw.decode();functions[idx]=dict(i,wat_sha256=hashlib.sha256(raw).hexdigest(),wat_bytes=len(raw))
        callers={str(i):[r[0]for r in db.execute('select distinct caller from calls where callee=? order by caller',(i,))]for i in(1680,5745,10146)}
    assert callers=={'1680':[984,5745,10146],'5745':[916,984,1089,10146],'10146':[1089]}==static['summon_direct_callers']
    for pointer,(name,execution,effect,h)in definitions.items():
        raw=read(pointer,88);assert hashlib.sha256(raw).hexdigest()==h and raw[84]==execution and int.from_bytes(raw[:4],'little')==effect
        string,n=struct.unpack_from('<2I',raw,12);assert read(string,n).decode()==name
    #Constructor interpretation independent of model/observed zero headers.
    words=bytearray(16);struct.pack_into('<Q',words,0,0);struct.pack_into('<Q',words,8,8);header=list(struct.unpack_from('<3I',words,4));assert header==[0,8,0]
    windows={}
    for name,index,a,b,terms in(
        ('1560_real_aux_constructor',1560,1358,1369,('i64.const 8','i64.store offset=748','i64.const 0','i64.store offset=740')),
        ('1560_copy_base88',1560,2740,2753,('i32.const 88','i32.const 2592','memory.copy')),
        ('1680_real_append',1680,1974,2069,('i32.load offset=664','i32.load offset=656','call 65336','i32.load offset=660','i32.store offset=664')),
        ('984_empty_event_definition',984,8,25,('i32.load offset=2056','i32.eqz','br_if 2')),
        ('10146_first_item_guard',10146,8,16,('i32.load offset=2032','if (result i32)')),
        ('10146_second_item_guard',10146,441,449,('i32.load offset=2032','br_if')),
        ('916_empty_timed',916,8,25,('i32.load offset=604','i32.eqz')),
        ('916_empty_active84',916,212,224,('i32.load offset=652','if')),
        ('1089_direct_summon_guard',1089,1885,1897,('i32.load8_u offset=2576','br_if')),
        ('2573_phase1',2573,8,18,('i32.load8_u offset=2587','i32.const 1','br_if')),
        ('49037_phase1',49037,8,22,('i32.load8_u offset=2587','i32.const 1','br_if'))):
        text='\n'.join(texts[index].splitlines()[a-1:b]);assert all(t in text for t in terms),name;windows[name]=dict(function=index,first_line=a,last_line=b,text=text,sha256=hashlib.sha256(text.encode()).hexdigest())
    assert not re.search(r'\bload\S* offset=416(?:\s|$)',texts[915])
    for idx in(1072,4600):assert not re.search(r'offset=(656|660|664)(?:\s|$)',texts[idx])
    assert sha(CAPTURE/'comparison.json')==CAPTURE_SHA;capture=load(CAPTURE/'comparison.json');fixture=load(CAPTURE/'fixtures.json');assert sha(CAPTURE/'fixtures.json')==capture['fixtures_sha256']
    assert fixture['input']['class_byte']==fixture['input']['race_byte']==1 and fixture['input']['region_index']==0 and fixture['input']['app_lcg_seed_u64']=='0'
    assert 'reconstruction/core_spec/motion_aux_owner135.py'not in capture['source_sha256_before']
    reader=JsonlReader(CAPTURE/'stage-expectations.jsonl.gz',True,1073741824);predictions=[dict(record_kind='constructor',kind='constructor',header=header,source_counts={str(o):0 for o in GUARDS})];previous=None;events=Counter();phases=Counter();skills=set()
    def context(e):
        p=e['projection'];assert p['mode2582']==0 and p['tail_flags']['protection2576']==0
        pointers=[int.from_bytes(bytes.fromhex(x)[:4],'little')for x in p['owned_records_hex']]+[int.from_bytes(bytes.fromhex(p['racial_record_hex'])[:4],'little')]
        assert 5476580 in pointers and all(x in definitions for x in pointers)
        skills.update(definitions[x][0]for x in pointers)
        guards={str(o):e['vectors'][NAMES[o]]['count']if o in NAMES else 0 for o in GUARDS};assert not any(guards.values())
        return p,guards
    for row in reader:
        e=row['expected'];p,guards=context(e)
        if row['record_kind']=='opening':
            assert previous is None and p['phase2587']==1;predictions.append(dict(record_kind='opening',kind='opening',header=header,source_counts=guards));events['opening1089']+=1
        else:
            assert row['record_kind']=='stage'and row['stage_index']==len(predictions)-2;kind=row['kind'];event='selection1072'if kind=='select'else'motion2328'if kind=='motion'else kind
            pre=previous['projection'];assert pre['phase2587']in(1,2)and p['phase2587']in(1,2)
            if kind=='select':assert pre['phase2587']==2 and pre['selection_kind2585']==0
            predictions.append(dict(record_kind='stage',stage_index=row['stage_index'],action_index=row['action_index'],kind=kind,header=header,event=event,source_counts=guards,phase2587=p['phase2587']));events[event]+=1;phases[p['phase2587']]+=1
        previous=e
    assert reader.receipt()==report['expected_reader']and len(predictions)==6490 and predictions==load(RUN/'new-expectations.json')
    #Freeze this review's independently generated predictions before opening
    #original capture transport. Never use captured zero as the producer.
    save(out/'independent-expectations.json',predictions);expected_sha=sha(out/'independent-expectations.json')
    assert prepared['new_model_expectations_before_historical_CAS_read']and not prepared['author_blinded']and prepared['original_calls']==0
    codec=CAPTURE/'source-snapshot/scripts/opening_combat135_cas.py';assert sha(codec)==capture['source_sha256_before']['scripts/opening_combat135_cas.py']==sha(RUN/'frozen_capture_transport.py')
    target=out/'frozen_capture_transport.py';target.write_bytes(codec.read_bytes());spec=importlib.util.spec_from_file_location('independent_aux_capture_transport',target);transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport);decoder=transport.CaptureCAS135(CAPTURE)
    compressed=(CAPTURE/'results.cas.jsonl.gz').read_bytes();inflate=zlib.decompressobj(31);raw_index=inflate.decompress(compressed,33554433);assert inflate.eof and not inflate.unused_data and not inflate.unconsumed_tail and len(raw_index)<=33554432
    it=iter(predictions);counts=Counter();rows=[]
    for index,line in enumerate(raw_index.splitlines(keepends=True)):
        entry=decoder.decode_line(line);kind=entry['record_kind']
        if kind not in('constructor','opening','stage'):continue
        predicted=next(it);assert kind==predicted['record_kind']
        if kind=='stage':assert(entry['stage_index'],entry['kind'],entry['action_index'])==(predicted['stage_index'],predicted['kind'],predicted['action_index'])
        raw=bytes.fromhex(entry['raw_game2592_hex']);assert list(struct.unpack_from('<3I',raw,656))==header
        for offset,value in predicted['source_counts'].items():assert struct.unpack_from('<I',raw,int(offset))[0]==value;counts['sourceguard_words']+=1
        counts['header_snapshots']+=1;counts['header_words']+=3;counts['header_bytes']+=12
        rows.append(dict(record_kind=kind,stage_index=entry.get('stage_index'),kind=entry.get('kind',kind),expected=header,actual=header))
        if index%1000==0:print(json.dumps(dict(progress_record=index,headers=counts['header_snapshots'])),flush=True)
    assert next(it,None)is None and counts['header_snapshots']==6490 and counts['sourceguard_words']==71390
    assert rows==[json.loads(x)for x in(RUN/'header-comparisons.jsonl').read_text().splitlines()]
    cas=decoder.finish(capture['runtime']['capture_cas']);assert cas==report['capture_CAS_full_finish']and cas['records']==6952 and cas['logical_bytes']==2139516743
    assert dict(events)==report['events']and{str(k):v for k,v in phases.items()}==report['phase_counts']and sorted(skills)==report['observed_admitted_skills']and' demo_shout'.strip()not in skills
    terminal=load(RUN/'owned-terminal.json');assert terminal==handoff['owned_process']and terminal['exit_code']==0 and terminal['seconds']<terminal['deadline_seconds']==180 and terminal['pid_missing']and terminal['pgid_missing']and M.missing(terminal['pid'])and M.missing(terminal['pgid'],True)
    for n,h in files.items():assert sha(ROOT/n)==sha(RUN/'source-snapshot'/n)==h
    for n,h in reviewers.items():assert sha(ROOT/n)==h
    assert sha(out/'independent-expectations.json')==expected_sha and sha(RUN/'comparison.json')==SHA
    result=dict(status='passed-within-admitted-empty-auxiliary-domain',author_receipt_sha256=SHA,source_count=20,production_sources=15,local_import_edges=48,sources_verified=files,reviewer_sources=reviewers,static_functions=functions,static_windows=windows,summon_direct_callers=callers,definition_sha256={str(k):v[3]for k,v in definitions.items()},counts=dict(counts),events=dict(events),phases=dict(phases),observed_skills=sorted(skills),new_original_calls=0,new_original_frames=0,reviewer_production_imports=0,reviewer_production_executions=0,expected_reader=reader.receipt(),full_CAS_finish=cas,expected_sha256=expected_sha,author_process=terminal,artifact_sha256={n:sha(RUN/n)for n in(*report['artifact_sha256'],'comparison.json','task-handoff.json','owned-terminal.json')},seconds=time.monotonic()-start,limits=['Newowner/historical6490header match,not new original calls/frames orfreshworld/App/fatal acceptance.','Static constructor0/8/0 andbounded admitted-source exclusion establish expectations;original zero is read only afterward.','Four omitted oldprojection guards2032/2056/1840/1864 derive constructor/no-admitted-producer obligations;not a generic alias/wholeprogram writeproof.','G656 auxiliary112 isdistinct fromG1856 secondary112.915 hasno direct416load;do not treatheadless416guard asoriginal auxpredicate.','Demo declaration isstaticonly;historicalskills4,phases1/2only.Phase4 five-tail inheritance static+author modelchecks,not new original acceptance.','19 authornegativechecks/5phase4checks notexecuted byreviewer.','All unsupported/nonempty summon/item/proc/timed/active84/network source paths remain unknown andmust notclearowner.'])
    save(out/'review.json',result);print(json.dumps(dict(output=str(out/'review.json'),sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])))
if __name__=='__main__':main()
