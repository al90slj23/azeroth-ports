#!/usr/bin/env python3
"""Read-only physical-player composition audit; no model/original execution.

Player live/Aura transitions and opaque-source copy identities are rebuilt
here from fixed instructions, input clocks and observed cast event metadata.
No original auxiliary source word is inserted into the production model.
"""
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
from functools import lru_cache
import argparse,ast,gzip,hashlib,importlib.util,json,struct,sys,time,zlib

sys.dont_write_bytecode=True
import review_opening_combat135_750 as old

ROOT=Path(__file__).resolve().parents[1]
BASE=old.base
S=old.S
F,B,add,sub,mul,word=old.F,old.B,old.add,old.sub,old.mul,old.word
ORIGINAL_SHA=old.ORIGINAL_SHA


def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def u(row,o=0):
    v=row[o:o+4];assert len(v)==4 and None not in v
    return int.from_bytes(bytes(v),'little')
def put(row,o,v):row[o:o+4]=struct.pack('<I',v)


class PhysicalPlayerAudit:
    def __init__(self,read):
        self.read=read;self.rows=[];self.count=0;self.origins=[];self.aura=[];self.initialized=0
        self.words={};self.counts=Counter();self.births=[];self.aura_fields={};self.last=None

    def retain(self,predicate):
        write=0;original=[row.copy()for row in self.rows];origins=self.origins.copy()
        for i,row in enumerate(original[:self.count]):
            if predicate(row):
                if write!=i:self.rows[write]=row.copy();self.counts['whole32_moves']+=1
                self.origins[write]=origins[i];write+=1
            else:self.counts['removed_live_rows']+=1
        self.count=write

    def append(self,writes,origin=None):
        if self.count==len(self.rows):
            cap=max(4,len(self.rows)*2);self.rows.extend([[None]*32 for _ in range(cap-len(self.rows))]);self.origins.extend([None]*(cap-len(self.origins)));self.counts['capacity_growths']+=1
        row=self.rows[self.count]
        for o,v in writes:put(row,o,v)
        if origin is not None:
            row[16:20]=[None]*4;self.origins[self.count]=origin
        self.count+=1

    def rebuild_aura(self,now):
        ordered={}
        for row in self.rows[:self.count]:
            if not F(u(row,24))>F(now):continue
            kind,spell=u(row,8),u(row,20);assert kind in(0,8,12)
            if kind==8:assert F(u(row,12))>=0
            elif kind==12:assert spell==1020
            if spell in ordered:
                assert kind==0,'Duplicate positive self source outside this trajectory'
                continue
            ordered[spell]=(u(row,24),1)
        rows=[[None]*16 for _ in range(48)]
        for row in rows:put(row,0,0)
        for row,(spell,(expiry,n))in zip(rows,ordered.items()):
            for o,v in((0,1),(4,spell),(8,expiry),(12,n)):put(row,o,v)
        self.aura=rows;self.initialized=1
        for i,row in enumerate(rows):self.aura_fields[str(47+i)]=u(row,4)if u(row)==1 else 0
        for group in range(6):self.aura_fields[str(95+group)]=sum((9 if i<32 else 8)<<(4*(i&7))for i in range(group*8,group*8+8)if u(rows[i])==1)
        for group in range(12):self.aura_fields[str(113+group)]=sum((min(u(rows[i],12),255)-1)<<(8*(i&3))for i in range(group*4,group*4+4)if u(rows[i])==1 and u(rows[i],12))
        self.counts['Aura_rebuild_events']+=1

    def cast_events(self,before,raw,want,frame,now):
        #The observed append event is bound to an actual persistent basic or
        #learned80 owner and a due timer. Target-query/card generation rules
        #are separate independently reviewed components, not re-inferred from
        #a phase-end target marker here.
        entries=[bytes.fromhex(x)for x in before['projection']['owned_records_hex']]
        entries.append(bytes.fromhex(before['projection']['racial_record_hex']))
        after=[bytes.fromhex(x)for x in raw['projection']['owned_records_hex']]
        after.append(bytes.fromhex(raw['projection']['racial_record_hex']))
        assert len(entries)==len(after)
        active=[bytes.fromhex(x)for x in raw['vectors']['live32']['storage'][:raw['vectors']['live32']['count']]]
        declarations=want.get('unresolved_live_auxiliary_origins',[])
        new={tuple(item['source'])for item in declarations if tuple(item['source'])not in self.words}
        consumed=set()
        for record,current in zip(entries,after):
            pointer=word(record,0);definition=self.read(pointer,88);tag,spell=word(definition,0),word(definition,44)
            if tag not in(8,9)or definition[84]!=9:continue
            assert tag==8,'This fixed human-warrior trajectory has only positive8 self casters'
            duration=mul(mul(mul(word(definition,68),0x3fb33333),word(record,28)),word(record,68))
            duration=duration if F(duration)>.1 else B(.1);deadline=add(now,duration)
            written=[row for row in active if word(row,8)==tag and word(row,20)==spell and word(row,24)==deadline and row[:8]==bytes(8)]
            if not written:continue
            assert len(written)==1
            assert F(sub(word(record,8),raw['_dt_bits']))<=0 and F(word(current,8))>0
            matches=[token for token in new if token[0]=='922.effect8or9.caller_frame+48'and token[1]==frame+1 and token[2]==spell and token[3]==now]
            assert len(matches)==1,(frame,spell,new);token=matches[0]
            assert len(token)==5 and type(token[4])is int and token[4]>0
            #attempt-count is an unverified controller annotation: the raw
            #capture lacks all three complete ledgers. It is not value proof.
            consumed.add(token)
            self.retain(lambda row:u(row,20)!=spell or u(row,0)!=0 or u(row,4)!=0)
            index=self.count
            self.append(((0,0),(4,0),(8,tag),(12,mul(word(record,76),word(definition,4))),
                (20,spell),(24,deadline),(28,0)),origin=token)
            self.rebuild_aura(now)
            observed=word(written[0],16);self.words[token]=observed
            self.births.append(dict(frame=frame,completed_frame=frame+1,stage=raw['stage_index'],slot=index,source=list(token),
                static_pointer=pointer,spell=spell,observed_word=observed,caller_value_predicted=False,attempt_count_independently_verified=False))
            self.counts['self_cast_write_events']+=1
        assert new==consumed,('Invented or unbound new scratch origin',new,consumed)

    def observe(self,before,raw,want,frame,now):
        kind=raw['record_kind'];phase=raw.get('kind')
        if kind=='opening':assert not self.rows and not self.aura
        elif kind=='stage'and phase=='player':
            expired=any(F(now)>=F(u(row,24))for row in self.rows[:self.count])
            if expired:
                self.retain(lambda row:F(now)<F(u(row,24)));self.rebuild_aura(now);self.counts['dirty_prefix_stages']+=1
            self.cast_events(before,raw,want,frame,now)
        elif kind=='stage'and phase=='select'and raw['projection']['phase2587']==1:
            self.retain(lambda row:u(row,20)!=1020)
            self.append(((0,0),(4,0),(8,12),(20,1020),(24,add(now,B(1))),(28,0)))
            self.rebuild_aura(now);self.counts['selection1020_partial_appends']+=1
        elif kind=='stage'and phase=='collect':
            #This stationary750 path has no natural nearby rune consumer.
            #Do not claim the independently verified component is thereby
            #covered by this continuous trajectory.
            assert not raw['projection']['rune_notifications']
            self.counts['collect_stages_without_rune_consumption']+=1
        if want is None:return
        expected=want['vectors'];live=expected['live32'];aura=expected['aura48']
        assert live==dict(capacity=len(self.rows),count=self.count,storage=self.rows)
        assert aura==dict(capacity=len(self.aura),count=len(self.aura),storage=self.aura)
        assert want['projection']['aura_initialized2569']==self.initialized
        for key,value in self.aura_fields.items():assert want['projection']['player_fields'][key]==raw['projection']['player_fields'][key]==value
        declarations=[dict(slot=i,source=list(origin))for i,origin in enumerate(self.origins)if origin is not None]
        assert want.get('unresolved_live_auxiliary_origins',[])==declarations
        for i,origin in enumerate(self.origins):
            if origin is None:continue
            assert self.rows[i][16:20]==[None]*4
            observed=word(bytes.fromhex(raw['vectors']['live32']['storage'][i]),16)
            assert origin in self.words and observed==self.words[origin],(frame,phase,i,origin,observed,self.words.get(origin))
            self.counts['opaque_word_copy_observations']+=1
        assert want['projection']['notification_next_id14340336']==raw['projection']['notification_next_id14340336']==1
        self.counts['physical_owner_snapshots']+=1


@lru_cache(maxsize=32768)
def mask(name,row,active):
    gaps=tuple(i for i,v in enumerate(row)if v is None);spans=[];start=0
    for i in gaps+(len(row),):
        if start<i:spans.append((start,i,bytes(row[start:i])))
        start=i+1
    if active and name not in('live32','aura48'):
        for i in gaps:BASE.allowed_unknown650(name,list(row),i)
    return tuple(spans),gaps


def snapshot(raw,want,counts,maximum,read):
    guardians=S.check_snapshot(raw,None,counts,maximum,read)
    game=bytes.fromhex(raw['raw_game2592_hex']);v=raw['vectors']['aura48'];cap,ptr,n=struct.unpack_from('<3I',game,2000)
    assert(v['capacity'],v['pointer'],v['count'],v['stride'])==(cap,ptr,n,16)and n<=cap<=48
    assert len(v['storage'])==cap and all(len(bytes.fromhex(row))==16 for row in v['storage'])
    assert v['storage_sha256']==hashlib.sha256(b''.join(bytes.fromhex(row)for row in v['storage'])).hexdigest()
    assert raw['projection']['aura_initialized2569']==game[2569]
    if want is None:return
    BASE.BINDER.observe(raw,want)
    raw['projection']['resource_create_packets169']=BASE.resource_packets(raw)
    raw['projection']['explicit_actor_creates169']=BASE.actor_packets(raw,{int(x['guid'])for x in want['projection']['explicit_actor_creates169']})
    raw['projection']['banner150_packets']=[x['payload_hex']for x in raw['packets']['active']if x['opcode']==150]
    raw['projection']['npc_aura_updates169']=old.projection_aura(raw)
    raw['projection']['player_speed226_packets']=[x['payload_hex']for x in raw['packets']['active']if x['opcode']==226]
    runes=[]
    for item in raw['notifications']['active']:
        try:d=json.loads(bytes.fromhex(item['payload_hex']))
        except(ValueError,UnicodeDecodeError):continue
        if isinstance(d,dict)and d.get('type')=='banner'and d.get('kind')=='rune':runes.append(item['payload_hex'])
    raw['projection']['rune_notifications']=runes
    BASE.check_value650(want['projection'],raw['projection'],('projection',),counts)
    for name,expected in want['vectors'].items():
        actual=raw['vectors'][name]
        for key in('capacity','count'):
            if key in expected:assert expected[key]==actual[key];counts['vector_shape_fields']+=1
        for field in('storage','records'):
            if field not in expected:continue
            data=actual['storage']if field=='storage'else actual['storage'][:actual['count']]
            assert len(data)==len(expected[field])
            for i,(row,encoded)in enumerate(zip(expected[field],data)):
                observed=bytes.fromhex(encoded);assert len(row)==len(observed)
                spans,gaps=mask(name,tuple(row),i<actual['count'])
                for a,b,value in spans:assert observed[a:b]==value,(name,i,a,b)
                counts['strict_record_bytes']+=len(observed)-len(gaps);counts['unknown_cells']+=len(gaps)
                counts['unknown_cells_nonzero_original']+=sum(observed[i]!=0 for i in gaps)
    return guardians


def main():
    p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--comparison-sha',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    capture=args.capture.resolve();out=args.output.resolve();assert capture.is_relative_to((ROOT/'evidence').resolve())and out.is_relative_to((ROOT/'evidence').resolve());out.mkdir()
    reviewer_sources=old.reviewer_sources(out)
    own_name=str(Path(__file__).resolve().relative_to(ROOT));reviewer_sources[own_name]=sha(Path(__file__))
    target=out/'reviewer-source-snapshot'/own_name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(Path(__file__).read_bytes())
    start=time.monotonic();report=load(capture/'comparison.json');assert sha(capture/'comparison.json')==args.comparison_sha
    assert report['physical_player_sources']and report['status']=='matched_requested_budget'and report['differences']==0
    fixture=load(capture/'fixtures.json');runtime=load(capture/'opening-combat135-cas-runtime.json');manifest=load(capture/'manifest.json')
    assert fixture['physical_player_sources']and fixture['explicit_App_notification_counter']==1
    frames=fixture['independent_frames'];assert frames in(120,750)and report['compared_stages']==fixture['stage_count']
    source=report['source_sha256_before'];assert source==report['source_sha256_after']
    assert source=={n:sha(capture/'source-snapshot'/n)for n in source}=={n:sha(ROOT/n)for n in source}
    for name in source:
        if name.startswith('reconstruction/'):
            for node in ast.walk(ast.parse((capture/'source-snapshot'/name).read_text())):
                if isinstance(node,ast.Call):
                    func=node.func;called=func.id if isinstance(func,ast.Name)else func.attr if isinstance(func,ast.Attribute)else''
                    assert called not in('open','read_text','read_bytes','write_text','write_bytes','Popen','eval','exec','__import__')
    original=(ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm').read_bytes();assert hashlib.sha256(original).hexdigest()==ORIGINAL_SHA
    modified=(capture/manifest['module_file']).read_bytes();a,b=S.sections(original),S.sections(modified)
    assert[x[0]for x in a]==[x[0]for x in b]and all(x[0]!=8 for x in a)
    assert all(original[x:y]==modified[u:v]for(k,x,_,y),(_,u,_,v)in zip(a,b)if k!=7)
    assert old.exports(modified)==old.exports(original)+[['research_opening_combat135_'+x['role'],0,x['index']]for x in manifest['roles']]+[['research_opening_combat135_stack',3,0]]
    read=S.static_reader(original);del original,modified
    decoder_path=capture/'source-snapshot/scripts/opening_combat135_cas.py';assert sha(decoder_path)=='728b3ae0576d372b9b7467c484022ae3487e772b9a09c0172bfbcdcf29c1479f'
    spec=importlib.util.spec_from_file_location('frozen_player_CAS_evidence_codec',decoder_path);transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport);decoder=transport.CaptureCAS135(capture)
    artifacts={name:sha(capture/name)for name in('comparison.json','fixtures.json','inputs.json','config.json','manifest.json',manifest['module_file'],'stage-expectations.jsonl.gz','results.cas.jsonl.gz','opening-combat135-cas-runtime.json','process-terminal.json','owned-process.json')}
    original_process=load(capture/'process-terminal.json');owned=load(capture/'owned-process.json');assert original_process['exit_code']==0 and not original_process['deadline_exceeded']and S.missing(owned['pid'])and S.missing(owned['pgid'],True)
    assert runtime['denied_imports']==878 and runtime['host_imports_throw']and runtime['boundaries']==0 and runtime['completed_controlled_tail_frames']==frames
    check=(capture/'source-snapshot/scripts/check_opening_combat135.py').read_text();assert check.index('row=corpus(')<check.index('child=subprocess.Popen(')
    expected_reader=S.JsonlReader(capture/'stage-expectations.jsonl.gz',True,1073741824);expected=iter(expected_reader)
    tracker=PhysicalPlayerAudit(read);counts=Counter();maximum=defaultdict(int);records=Counter();stages=0;clock=0;previous=None;self_stack=[];stream_hash=hashlib.sha256();stream_bytes=0
    with gzip.open(capture/'results.cas.jsonl.gz','rb')as stream:
        while line:=stream.readline(2097153):
            assert time.monotonic()-start<420 and len(line)<=2097152 and line.endswith(b'\n')
            stream_hash.update(line);stream_bytes+=len(line);raw=decoder.decode_line(line);kind=raw['record_kind'];records[kind]+=1
            assert raw['id']==0
            if kind=='clock_control':
                action=fixture['actions'][raw['action_index']];assert raw['old_bits']==clock and raw['dt_bits']==action['dt_bits']
                clock=add(clock,action['dt_bits']);assert raw['new_bits']==clock and not raw['original880_called'];continue
            if kind in('constructor','opening','stage'):
                want=None
                if kind in('opening','stage'):
                    entry=next(expected);assert entry['record_kind']==kind;want=entry['expected']
                if kind=='stage':
                    assert entry['stage_index']==raw['stage_index']==stages and entry['kind']==raw['kind']and entry['action_index']==raw['action_index']
                    action=fixture['actions'][raw['action_index']];raw['_dt_bits']=action.get('dt_bits',0);assert raw['projection']['now_bits']==clock
                    assert raw['entry_index']==(1072 if raw['kind']=='select'else S.ENTRIES[BASE.STAGES.index(raw['kind'])]);counts['stage_identity_leaves']+=2
                    scratch=raw.get('caller_scratch48_observation');assert scratch['address']==1048080 and scratch['root_stack']==1048576 and scratch['kind']=='read_only_SP_minus496_not_model_input'
                    self_stack.append(dict(stage=stages,kind=raw['kind'],before=scratch['before'],after=scratch['after']))
                snapshot(raw,want,counts,maximum,read)
                tracker.observe(previous,raw,want,raw.get('frame',0),clock)
                previous=raw
                if kind=='stage':stages+=1
            if kind=='case_end':
                assert raw['boundary']is None and raw['host_calls']==[]and raw['stage_count']==stages
                calls=[x for x in raw['calls']if x['role']!='original_allocator'];assert len(calls)==runtime['original_entry_calls']and all(x['returned']and x['stack_after']==1048576 for x in calls)
            if sum(records.values())%500==0:
                progress=dict(records=sum(records.values()),stages=stages,seconds=time.monotonic()-start);save(out/'progress.json',progress);print(json.dumps(progress),flush=True)
    assert stages==fixture['stage_count']==report['compared_stages']and next(expected,None)is None
    cas=decoder.finish(runtime['capture_cas']);assert cas==report['capture_cas_verification']
    assert stream_bytes==runtime['uncompressed_output_bytes']and stream_hash.hexdigest()==runtime['uncompressed_sha256']
    expected_receipt=expected_reader.receipt();assert expected_reader.bytes==fixture['expected_uncompressed_bytes']and expected_receipt['file_sha256']==report['expectations_sha256']
    known=sum(counts[k]for k in('strict_record_bytes','projection_leaves','vector_shape_fields','stage_identity_leaves'))
    assert known==report['comparison']['compared_leaves']and counts['unknown_cells']==report['comparison']['declared_unknown_cells']
    assert counts['unwritten_pickup_arrival_words']==report['comparison']['unwritten_pickup_arrivals']and counts['verified_opaque_pickup_amount_words']==report['comparison']['verified_opaque_pickup_amounts']
    assert BASE.BINDER.report()==report['pickup_address_proof']
    assert tracker.counts['opaque_word_copy_observations']==report['live_auxiliary_source_observations']['observations']
    assert len(tracker.words)==report['live_auxiliary_source_observations']['distinct_sources']
    assert source=={n:sha(capture/'source-snapshot'/n)for n in source}=={n:sha(ROOT/n)for n in source}and artifacts=={n:sha(capture/n)for n in artifacts}
    assert reviewer_sources=={n:sha(ROOT/n)for n in reviewer_sources}
    result=dict(status='scoped_physical_player_composition_read_only_review_passed',version='0.135.1',actual_build='90898d5e3',capture=str(capture),comparison_sha256=args.comparison_sha,
        frames=frames,stages=stages,selections=fixture['independent_selections'],source_files=len(source),production_files=sum(n.startswith('reconstruction/')for n in source),source_hashes=source,artifacts=artifacts,
        reviewer_sources=reviewer_sources,
        comparison_counts=dict(counts),reconciled_known_leaves=known,stream_records=dict(records),capture_cas_verification=cas,expected_stream=expected_receipt,
        independent_player_counts=dict(tracker.counts),independent_source_births=tracker.births,opaque_source_values_predicted=False,opaque_original_values_fed_to_model=False,
        attempt_counter_token_annotation_independently_verified=False,caller_scratch_entry_observations_are_inner_read_value_proof=False,
        natural_rune_consumption_events=0,pickup_address_proof=BASE.BINDER.report(),original_process=original_process,
        new_original_executions=0,production_model_executions=0,checker_executions=0,builder_executions=0,seconds=time.monotonic()-start,
        limitations=['Controlled14-tail after actual6730/1089, historical originalsnapshot, independent preparsedworld/externalclock, not full880/native/fullgame/latest138 acceptance.',
            'Cast write events bind due80B basic/owned timers and static declarations; target query/fullauto scheduler is separately reviewed, not independently replayed here.',
            'Named922 auxiliary source values remain observations plus copy/inheritance binding. EntrySP-496 before/after does not recover the inner read source value.',
            'No natural nearby rune consumption in this stationary trajectory; mixed/resource components remain separate.'])
    save(out/'review.json',result);save(out/'caller-scratch-entry-observations.json',self_stack)
    print(json.dumps(dict(directory=str(out),status=result['status'],review_sha256=sha(out/'review.json'),counts=tracker.counts)),flush=True)


if __name__=='__main__':main()
