#!/usr/bin/env python3
"""Read-only105-case physical live audit; never execute product or oracle.

The historical direct922 fixtures observe zero at a caller-stack union word.
That is not proof that effect8/9 writes definition+8: their branch skips that
assignment. This reviewer deliberately leaves that new write source unknown.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import argparse, ast, gzip, hashlib, json, math, os, struct, sys, time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'evidence/live-owner135-oracle-20261101T223912.866284Z'
ORIGINAL = ROOT / 'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
RECEIPT_SHA = 'd152eb693fe6ab39410d4977ec0e9e12e290dbe73a19920e111f1664e44c0541'


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def load(p): return json.loads(Path(p).read_text())
def save(p, x): Path(p).write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n')
def u(row, off=0):
    values = row[off:off + 4]
    assert len(values) == 4 and all(type(v) is int and 0 <= v < 256 for v in values)
    return struct.unpack('<I', bytes(values))[0]
def F(v): return struct.unpack('<f', struct.pack('<I', v))[0]
def B(v): return struct.unpack('<I', struct.pack('<f', v))[0]
def mul(a,b): return B(F(a)*F(b))
def add(a,b): return B(F(a)+F(b))
def put(row, off, value): row[off:off+4] = struct.pack('<I', value)


def missing(pid, group=False):
    try: (os.killpg if group else os.kill)(pid, 0)
    except ProcessLookupError: return True
    return False


def leb(raw, p):
    value = shift = 0
    while p < len(raw) and shift <= 28:
        b = raw[p]; p += 1; value |= (b & 127) << shift
        if b < 128: return value, p
        shift += 7
    raise AssertionError('LEB bound')


def sections(raw):
    assert raw[:8] == b'\0asm\1\0\0\0'
    p = 8; result = []
    while p < len(raw):
        start = p; kind = raw[p]; size, p = leb(raw,p+1); end = p+size
        assert end <= len(raw)
        result.append((kind,start,p,end)); p=end
    assert p == len(raw)
    return result


def exports(raw, sec):
    _,_,p,end=sec;count,p=leb(raw,p);result=[]
    for _ in range(count):
        n,p=leb(raw,p);name=raw[p:p+n].decode();p+=n;kind=raw[p];idx,p=leb(raw,p+1)
        result.append([name,kind,idx])
    assert p==end
    return result


def mechanical(w, a, path, counts):
    if w is None:
        if path==('success',): assert a is None; counts['structural_null_success']+=1; return
        assert len(path)>=4 and path[-4:-2]==('physical_live','storage')
        assert type(a)is int and 0<=a<256;counts['expected_unknown_bytes']+=1;return
    assert type(w)is type(a), (path,type(w),type(a))
    if isinstance(w,dict):
        assert set(w)==set(a), path
        for k in w:mechanical(w[k],a[k],path+(k,),counts)
    elif isinstance(w,list):
        assert len(w)==len(a),path
        for i,(x,y)in enumerate(zip(w,a)):mechanical(x,y,path+(i,),counts)
    else:
        assert w==a,(path,w,a);counts['mechanical_known_values']+=1


def reference(case, counts, *, materialize=False):
    #No production imports. Retain writes whole rows only into holes and does
    #not clear the inactive tail. Unknown stack write is a distinct provenance
    #from initial unknown allocation cells; neither is materialized as zero.
    original=case['physical_live'];rows=[list(row)for row in original['storage']]
    if materialize:
        rows=[[case['unknown_poison']if v is None else v for v in row]for row in rows]
    count=original['count'];assert count<=len(rows)<=128
    mode=case['mode'];append=True
    if mode=='cast':
        definition=struct.unpack('<22I',bytes.fromhex(case['cast_definition88_hex']))
        owned=struct.unpack('<20I',bytes.fromhex(case['cast_owned_hex']))
        assert definition[0]in(8,9) and definition[2]==0
        if not case['target_present']:return rows,count,None
        spell=definition[11]
        keep=lambda row:u(row,20)!=spell or u(row,0)!=0 or u(row,4)!=0
    else:
        assert mode in('resume','select');keep=lambda row:u(row,20)!=1020
    write=0
    for read in range(count):
        if keep(rows[read]):
            if write!=read:rows[write]=rows[read].copy();counts['whole32_moves']+=not materialize
            write+=1
        else:counts['removed_rows']+=not materialize
    count=write
    if count==len(rows):
        newcap=max(4,2*len(rows));assert newcap<=256
        rows.extend([[None]*32 for _ in range(newcap-len(rows))])
        counts['capacity_growths']+=not materialize
    target=rows[count]
    if mode=='cast':
        duration=mul(mul(mul(definition[17],0x3fb33333),owned[7]),owned[17])
        duration=duration if F(duration)>F(0x3dcccccd)else 0x3dcccccd
        writes=((0,0),(4,0),(8,definition[0]),(12,mul(owned[19],definition[1])),
            (20,spell),(24,add(case['level']['stats']['now_bits'],duration)),(28,0))
        for off,value in writes:put(target,off,value)
        #Actual i32.store from unassigned scratch48; initial target slot bytes
        #are overwritten, but source is absent in this historical capture.
        target[16:20]=[None]*4
        opaque=(count,16)
    else:
        writes=((0,0),(4,0),(8,12),(20,1020),
            (24,add(case['level']['stats']['now_bits'],0x3f800000)),(28,0))
        for off,value in writes:put(target,off,value)
        opaque=None
    return rows,count+1,opaque


def static_proof(manifest):
    by={x['idx']:x for x in manifest['functions']}
    for idx,item in by.items():
        assert sha(RUN/f'{idx}.wat')==item['WAT_sha256']
    lines=(RUN/'922.wat').read_text().splitlines()
    #Exact effect8/9 blocks end in br to the common append block, before the
    #default branch's assignment at5810. These windows are byte-hash bound.
    s8='\n'.join(lines[5747:5757]);s9='\n'.join(lines[5758:5768])
    assert 'i32.const 8\n' in s8 and 'i32.store offset=40' in s8 and 'f32.store offset=44' in s8 and 'br 4' in s8 and 'offset=48'not in s8
    assert 'i32.const 9\n' in s9 and 'i32.store offset=40' in s9 and 'f32.store offset=44' in s9 and 'br 3' in s9 and 'offset=48'not in s9
    default='\n'.join(lines[5809:5832]);assert 'i32.load offset=8' in default and 'i32.store offset=48' in default
    common='\n'.join(lines[5969:6008]);assert 'i32.load offset=48\n' in common and 'i32.store offset=16' in common
    resume=(RUN/'4600.wat').read_text().splitlines();tail='\n'.join(resume[668:691])
    assert 'i32.store offset=28' in tail and 'f32.store offset=24' in tail and 'i32.store offset=20' in tail and 'i32.store offset=8' in tail and 'i64.store\n'in tail
    assert 'offset=12'not in tail and 'offset=16'not in tail
    reserve=(RUN/'65320.wat').read_text();assert 'i32.const 1\n    i32.shl' in reserve and 'i32.const 4\n    i32.le_u\n    select' in reserve
    supplementary=ROOT/'evidence/self-buffs0135-oracle-20261101T221510.852622Z'
    supplementary_manifest=load(supplementary/'manifest.json')
    sup={item.get('index',item.get('idx')):item for item in supplementary_manifest['functions']}
    consumers={}
    for idx,lo,hi,summary in (
        (1512,1282,1523,'live dominance and kind8/9 stats use kind8/magnitude12/spell20/expiry24; no live16 read'),
        (1202,17,350,'positive aggregation uses kind8/9 magnitude12/spell20/expiry24; negative loop onlykind7'),
        (2088,23,181,'periodic budget28,expiry24,spell20,owner0; later retain copies complete32B'),
        (1073,55,96,'incoming protection scan uses expiry24 and kind12; later retain consumeskind7/sourceSpell20')):
        path=(RUN if idx==1073 else supplementary)/f'{idx}.wat'
        body=path.read_bytes();item=(next(x for x in manifest['functions']if x['idx']==idx)if idx==1073 else sup[idx])
        assert hashlib.sha256(body).hexdigest()==item.get('WAT_sha256',item.get('wat_sha256'))
        lines=body.decode().splitlines();window='\n'.join(lines[lo-1:hi])
        if idx in(1512,1202):
            assert 'i32.load offset=1708' in window and 'f32.load offset=12' in window and 'f32.load offset=24' in window
        elif idx==2088:assert 'i32.const 28\n' in window and 'i32.const 20\n' in window
        else:assert 'i32.const 12\n' in window and 'i32.const 24\n' in window
        consumers[str(idx)]={'path':str(path),'WAT_sha256':hashlib.sha256(body).hexdigest(),'bounded_lines':[lo,hi],'finding':summary}
    return {'922_effect8_lines':[5748,5757],'922_effect9_lines':[5759,5768],
        '922_default_only_assignment':[5810,5813],'922_common_source_write':[5982,5986],
        '4600_partial_append':[669,690],'effect8_9_definition_plus8_source_claim':'contradicted_by_control_flow',
        'actual_source':'922 scratch frame+48, unassigned by8/9 branch; historical output observes0 only',
        'stack_frame_bytes':240,'stack_word_absolute_for_direct_entry':1048576-240+48,
        'precall_stack_word_captured':False,'caller_producer_restoration':'pending',
        'bounded_consumer_inspection':consumers,
        'consumer_scope':'Admitted0/8/9/12,empty other sources,periodic budget0; no claim of whole-program non-observability'}


def parent_counterexample():
    #Only the previously audited evidence codec is imported. No production
    #model, original checker, original module or original process is executed.
    codec=ROOT/'scripts/opening_combat135_cas.py'
    assert sha(codec)=='728b3ae0576d372b9b7467c484022ae3487e772b9a09c0172bfbcdcf29c1479f'
    sys.path.insert(0,str(ROOT/'scripts'))
    from opening_combat135_cas import CaptureCAS135
    capture=ROOT/'evidence/opening-combat0135-oracle-20261101T223938.000541Z'
    decoder=CaptureCAS135(capture);envelopes=0;found=None
    with gzip.open(capture/'results.cas.jsonl.gz','rb')as stream:
        while line:=stream.readline(2*1024*1024+1):
            assert len(line)<=2*1024*1024 and line.endswith(b'\n')
            envelopes+=1;assert envelopes<=500
            raw=decoder.decode_line(line)
            if raw['record_kind']=='stage'and raw['stage_index']==70:
                assert raw['kind']=='player'
                live=raw['vectors']['live32'];assert live['count']==1
                row=bytes.fromhex(live['storage'][0]);assert len(row)==32
                assert u(row,8)==8 and u(row,20)==20600 and u(row,16)==0x4289add5
                game=bytes.fromhex(raw['raw_game2592_hex']);assert len(game)==2592
                assert struct.unpack_from('<3I',game,1704)==(live['capacity'],live['pointer'],live['count'])
                found={'stage':70,'kind':'player','effect_kind':8,'spell':20600,
                    'physical_plus16_word':u(row,16),'physical_plus16_hex':row[16:20].hex(),
                    'source_id':raw['projection']['source_id'],'envelopes_decoded':envelopes}
                break
    assert found is not None
    return {'capture':str(capture),'comparison_sha256':sha(capture/'comparison.json'),
        'result_file_sha256':sha(capture/'results.cas.jsonl.gz'),
        'evidence_decoder_sha256':sha(codec),'observation':found,
        'scope':'Bounded read-only prefix through stage70, per-line/blob verification; no completeCASfinish or all120-stage re-audit claimed.'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    out=args.output or ROOT/'evidence'/datetime.now(timezone.utc).strftime('live-owner135-independent-review-%Y%m%dT%H%M%S.%fZ')
    assert out.resolve().is_relative_to((ROOT/'evidence').resolve());out.mkdir(parents=True,exist_ok=False)
    began=time.monotonic();assert sha(RUN/'comparison.json')==RECEIPT_SHA
    primary=load(RUN/'comparison.json');manifest=load(RUN/'manifest.json');prepared=load(RUN/'prepared.json');runtime=load(RUN/'runtime.json');terminal=load(RUN/'process-terminal.json')
    assert primary['cases']==primary['full_calls']==105 and primary['comparison_complete']and primary['differences']==0
    sources=primary['source_before'];assert sources==primary['source_after']==prepared['source_before']and len(sources)==51
    frozen={n:sha(RUN/'source-snapshot'/n)for n in sources};assert frozen==sources
    current_before={n:sha(ROOT/n)for n in sources}
    for n in sources:
        if n.startswith('reconstruction/'):
            tree=ast.parse((RUN/'source-snapshot'/n).read_text())
            assert not any(isinstance(node,(ast.Import,ast.ImportFrom))and any(alias.name.split('.')[0]in('os','sys','subprocess','socket','urllib','pathlib')for alias in node.names)for node in ast.walk(tree))
    artifacts={n:sha(RUN/n)for n in primary['frozen_artifacts']};assert artifacts==primary['frozen_artifacts']==prepared['artifacts']
    extra={n:sha(RUN/n)for n in('comparison.json','stdout.jsonl','runtime.json','process-terminal.json','prepared.json','owned-process.json','differences.json')}
    original=ORIGINAL.read_bytes();assert hashlib.sha256(original).hexdigest()==primary['original_sha256']==manifest['original_sha256']
    changed=(RUN/manifest['module_file']).read_bytes();s1=sections(original);s2=sections(changed);assert [s[0]for s in s1]==[s[0]for s in s2]and all(s[0]!=8 for s in s1)
    for a,b in zip(s1,s2):
        if a[0]!=7:assert original[a[1]:a[3]]==changed[b[1]:b[3]]
    old=exports(original,next(s for s in s1 if s[0]==7));new=exports(changed,next(s for s in s2 if s[0]==7))
    allowed=[['research135_live_cast922',0,922],['research135_live_select1072',0,1072],['research135_live_resume4600',0,4600],['research135_live_stack0',3,0]]
    assert new==old+allowed and manifest['added_exports']==allowed
    for item in manifest['functions']:
        assert hashlib.sha256(original[item['body_start']:item['body_end']]).hexdigest()==item['body_sha256']
    static=static_proof(manifest);del original,changed
    assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and missing(terminal['pid'])and missing(terminal['pgid'],True)
    assert runtime['actual_host_calls']==0 and runtime['denied_imports']==878 and runtime['full_calls']==runtime['fresh_instances']==105 and runtime['error']is None
    assert runtime['peak_memory_bytes']<=runtime['memory_cap_bytes']==33554432 and runtime['heap_mib']==512
    assert runtime['entry_counts']=={'922':39,'1072':33,'4600':33}and runtime['stack_all_restored']
    assert all(x['returned']and x['before']==x['after']==1048576 for x in runtime['stack_checks'])
    cases=load(RUN/'input.json');expected=load(RUN/'expected.json');labels=load(RUN/'labels.json');actual=[json.loads(l)for l in(RUN/'stdout.jsonl').read_text().splitlines()]
    assert len(cases)==len(expected)==len(labels)==len(actual)==105
    counts=Counter();witnesses=[]
    for c,w,label,a in zip(cases,expected,labels,actual):
        assert c['id']==w['id']==label['id']==a['id'];mode=c['mode'];counts[mode+'_cases']+=1
        r=a['result'];r['physical_live']['storage']=[list(bytes.fromhex(x))for x in r['physical_live']['storage']]
        mechanical(w['result'],r,(),counts)
        raw_before=bytes.fromhex(a['raw_Game_before8192_hex']);raw_after=bytes.fromhex(a['raw_Game_after8192_hex']);assert len(raw_before)==len(raw_after)==8192
        R=lambda data,off:struct.unpack_from('<I',data,off)[0]
        assert(R(raw_before,1704),R(raw_before,1712))==(len(c['physical_live']['storage']),c['physical_live']['count'])
        assert(R(raw_after,1704),R(raw_after,1712),R(raw_after,1708))==(r['physical_live']['capacity'],r['physical_live']['count'],a['live_pointer'])
        assert r['derived_bits']=={str(o):R(raw_after,o)for o in range(1536,1628,4)}
        assert r['current_hp_bits']==R(raw_after,1440)and r['speed_bits']==R(raw_after,1648)
        assert r['rng_words']==list(struct.unpack_from('<4I',raw_after,1720))==c['level']['rng_words']
        assert r['action_sequence1644']==R(raw_after,1644)==9 and r['message_sequence2412']==R(raw_after,2412)==19
        assert r['basic_hex']==raw_after[1256:1336].hex()==c['basic_hex']and r['cast_owned_hex']==c['cast_owned_hex']
        for queue,off,stride in(('raw_packets',1880,16),('raw_notifications',1892,12)):
            q=a[queue];assert(q['capacity'],q['count'],q['pointer'])==(R(raw_after,off),R(raw_after,off+8),R(raw_after,off+4))
            md=bytes.fromhex(q['metadata_hex']);assert len(md)==q['count']*stride and len(q['active'])==q['count']
            for j,item in enumerate(q['active']):
                cap,ptr,length=struct.unpack_from('<3I',md,j*stride);assert(item['capacity'],item['pointer'],item['length'])==(cap,ptr,length)
                assert length<=cap<=1048576 and len(bytes.fromhex(item['payload_hex']))==length and ptr+length<=runtime['peak_memory_bytes']
                if queue=='raw_packets':assert item['opcode']==struct.unpack_from('<H',md,j*stride+12)[0]
        model,count,opaque=reference(c,counts);concrete,concrete_count,_=reference(c,Counter(),materialize=True)
        assert len(model)==len(concrete)==r['physical_live']['capacity']and count==concrete_count==r['physical_live']['count']
        for i,(row,truth,observed)in enumerate(zip(model,concrete,r['physical_live']['storage'])):
            assert len(row)==len(truth)==len(observed)==32
            for j,(v,t,real)in enumerate(zip(row,truth,observed)):
                if opaque==(i,16)and 16<=j<20:
                    counts['unresolved_written_scratch_bytes']+=1
                    continue
                if v is not None:assert v==real,(c['id'],i,j,v,real);counts['independent_known_physical_bytes']+=1
                elif t is not None:
                    assert real==t,(c['id'],i,j,t,real);counts['inherited_initial_None_poison_bytes']+=1
                else:counts['unwritten_new_allocation_bytes']+=1
        if opaque:
            word=u(r['physical_live']['storage'][opaque[0]],16);assert word==0
            counts['observed_zero_scratch_source_casts']+=1
            if len(witnesses)<8:witnesses.append({'case':c['id'],'caster':c['caster'],'physical_slot':opaque[0],'output_plus16_word':word,'precall_scratch_source_not_captured':True})
        if mode!='cast':
            counts['independent_selection_or_resume_partial_appends']+=1
            if any(v is None for v in model[count-1][12:20]):counts['selection_inherited_None_aux_words']+=1
        else:assert r['success']==int(c['target_present'])
    assert counts['mechanical_known_values']==primary['counts']['known_values']==16387
    assert counts['expected_unknown_bytes']==primary['counts']['explicit_unknown_bytes']==2388
    assert counts['structural_null_success']==66 and counts['unresolved_written_scratch_bytes']==4*counts['observed_zero_scratch_source_casts']
    assert sources=={n:sha(RUN/'source-snapshot'/n)for n in sources}and artifacts=={n:sha(RUN/n)for n in artifacts}and extra=={n:sha(RUN/n)for n in extra}
    current_after={n:sha(ROOT/n)for n in sources};assert current_before==current_after
    counterexample=parent_counterexample()
    result={'status':'partial_physical_review_passed_general_caster_plus16_source_claim_contradicted',
        'version':'0.135.1','actual_build':'90898d5e3','comparison':str(RUN/'comparison.json'),'comparison_sha256':RECEIPT_SHA,
        'source_files':51,'production_files':sum(n.startswith('reconstruction/')for n in sources),'frozen_sources_verified':True,
        'current_source_drift':{n:{'captured':sources[n],'current':current_after[n]}for n in sources if sources[n]!=current_after[n]},
        'artifacts':{**artifacts,**extra},'mechanical_expected_original_comparison_complete':True,'counts':dict(counts),'witnesses':witnesses,
        'static_proof':static,'parent_natural_prefix_counterexample':counterexample,
        'runtime_identity':{k:v for k,v in runtime.items()if k!='stack_checks'},'original_process':terminal,
        'source_failure':'Captured physical caster writes+16=definition[2]; effect8/9 skip that assignment and copy prior stack48. All direct fixtures happen to observe0, unlike natural parent composition.',
        'general_caster_source_restoration_validated':False,'selection_forward_retain_partial_append_validated':True,
        'new_original_executions':0,'production_model_executions':0,'checker_executions':0,'builder_executions':0,
        'numerical_scope':'Full frozen known numeric projection mechanically re-compared; this audit independently reconstructs physical storage, not all1512 arithmetic.',
        'limitations':['No precall scratch48 capture in105 fixtures; observed zero does not prove its source.','Caster8/9 general+16 source is an explicit unresolved write; selection1020+12/+16 inherited slot bytes are independently proved.','No headless/natural App/full880/Windows/fullgame acceptance.'],
        'reviewer_script_sha256':sha(Path(__file__)),'seconds':time.monotonic()-began}
    save(out/'review.json',result)
    print(json.dumps({'directory':str(out),'status':result['status'],'counts':result['counts'],'review_sha256':sha(out/'review.json')}),flush=True)


if __name__=='__main__':main()
