#!/usr/bin/env python3
"""Independent archived1371420 review; never import/run a game model/checker.

Rechecks complete records, exact unknown masks, retained input bytes, RNG,
GUID/169 schemas and Game guards, plus binary/source/ownership provenance.
"""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import argparse
import ast
import copy
import hashlib
import json
import math
import os
import re
import signal
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
FINAL=ROOT/'evidence/resource-pickup0137-oracle-20261101T182737.085717Z'
FINAL_SHA='1e9a748dd96d9c12b239c874067c943a344f96e9fb0eb94c8c3f42510690dba2'
OLD=ROOT/'evidence/resource-pickup0137-oracle-20261101T182323.787663Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T154517.001467Z/latest-wenilla_bg.wasm'
ORIGINAL_SHA='20ec9a2b5182a72e13ca11668ff0aab17e9dc54a10b923b546708ab85e3fe1c8'
MASK=(1<<32)-1


def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def load(path):return json.loads(path.read_text())
def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def word(data,offset):return struct.unpack_from('<I',data,offset)[0]
def fl(bits):return struct.unpack('<f',struct.pack('<I',bits))[0]
def bits(value):return struct.unpack('<I',struct.pack('<f',value))[0]
def f32(value):return fl(bits(value))
def rol(value,shift):return ((value<<shift)|(value>>(32-shift)))&MASK


def heading(words):
    a,b,c,d=words
    for draws in range(1,101):
        result=(rol((a+d)&MASK,7)+a)&MASK
        shift=(b<<9)&MASK
        c^=a;d^=b;b^=c;a^=d;c^=shift;d=rol(d,11)
        angle=f32(f32(fl((result>>9)|0x3f800000)-1)*fl(0x40c90fdb))
        if angle<fl(0x40c90fdb):return bits(angle),[a,b,c,d],draws
    raise AssertionError('Independent yaw watchdog')


def closure(start):
    bases=(ROOT/'scripts',ROOT/'reconstruction');pending=list(start);seen=set();edges=set()
    def resolve(name):
        for base in bases:
            p=base/Path(*name.split('.'))
            for candidate in (p.with_suffix('.py'),p/'__init__.py'):
                if candidate.is_file():return candidate
    while pending:
        path=pending.pop();key=str(path.relative_to(ROOT))
        if key in seen:continue
        seen.add(key)
        if path.suffix=='.mjs':
            names=[(path.parent/name).resolve()for name in re.findall(r"from\s+['\"](\.[^'\"]+)['\"]",path.read_text())]
        else:
            base=next(base for base in bases if path.is_relative_to(base))
            package=list(path.relative_to(base).with_suffix('').parts[:-1]);names=[]
            for node in ast.walk(ast.parse(path.read_text())):
                modules=[]
                if isinstance(node,ast.Import):modules=[row.name for row in node.names]
                elif isinstance(node,ast.ImportFrom):
                    prefix='.'.join(package[:len(package)-node.level+1])if node.level else''
                    module='.'.join(x for x in(prefix,node.module or'')if x)
                    modules=[module]+['.'.join(x for x in(module,row.name)if x)for row in node.names]
                names.extend(p for name in modules if name and(p:=resolve(name))is not None)
        for target in names:
            pending.append(target);edges.add((key,str(target.relative_to(ROOT))))
            base=next(base for base in bases if target.is_relative_to(base))
            parent=target.parent
            while parent!=base:
                if(parent/'__init__.py').is_file():
                    initializer=parent/'__init__.py';pending.append(initializer);edges.add((key,str(initializer.relative_to(ROOT))))
                parent=parent.parent
    return seen,edges


def literal(path,name):
    for node in ast.parse(path.read_text()).body:
        if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in node.targets):return ast.literal_eval(node.value)
    raise AssertionError(name)


class Reader:
    def __init__(self,data,start=0,end=None):self.data,self.at,self.end=data,start,len(data)if end is None else end
    def uint(self):
        value=shift=0
        while self.at<self.end and shift<=35:
            byte=self.data[self.at];self.at+=1;value|=(byte&127)<<shift
            if byte<128:return value
            shift+=7
        raise AssertionError('ULEB')
    def name(self):
        n=self.uint();a=self.at;self.at+=n;assert self.at<=self.end;return self.data[a:self.at].decode()


def sections(data):
    assert data[:8]==b'\0asm\x01\0\0\0';r=Reader(data,8);out=[]
    while r.at<r.end:
        start=r.at;kind=data[r.at];r.at+=1;size=r.uint();a=r.at;r.at+=size;assert r.at<=r.end
        out.append(dict(kind=kind,start=start,payload=a,end=r.at))
    return out


def exports(data,section):
    r=Reader(data,section['payload'],section['end']);result=[]
    for _ in range(r.uint()):
        name=r.name();kind=data[r.at];r.at+=1;result.append((name,kind,r.uint()))
    assert r.at==r.end;return result


def binary_proof(manifest):
    assert sha(ORIGINAL)==ORIGINAL_SHA
    original=ORIGINAL.read_bytes();changed=(FINAL/manifest['module_file']).read_bytes()
    assert hashlib.sha256(changed).hexdigest()==manifest['module_sha256']
    a,b=sections(original),sections(changed)
    assert [s['kind']for s in a]==[s['kind']for s in b]and all(s['kind']!=8 for s in a)
    for left,right in zip(a,b):
        if left['kind']!=7:assert original[left['start']:left['end']]==changed[right['start']:right['end']]
    prior=exports(original,next(s for s in a if s['kind']==7));new=exports(changed,next(s for s in b if s['kind']==7))
    assert new==prior+[('research137_resource_pickup1420',0,1420),('research137_resource_pickup_stack0',3,0)]
    global_section=next(s for s in a if s['kind']==6)
    assert original[global_section['payload']:global_section['end']].hex()=='017f01418080c0000b'
    code=next(s for s in a if s['kind']==10);reader=Reader(original,code['payload'],code['end']);count=reader.uint();found={}
    for index in range(878,878+count):
        n=reader.uint();lo=reader.at;reader.at+=n
        if index in(1420,1827):found[index]=dict(start=lo,end=lo+n,sha256=hashlib.sha256(original[lo:lo+n]).hexdigest())
    assert found[1420]==dict(start=manifest['entry']['body_start'],end=manifest['entry']['body_end'],sha256=manifest['entry']['body_sha256'])
    assert found[1827]['sha256']=='28d0c7e50a34d9ddb8c5012c981757ac89a5edcf2d9674902c372dd460ca5c6d'
    imp=next(s for s in a if s['kind']==2);reader=Reader(original,imp['payload'],imp['end']);n=reader.uint();assert n==878
    for _ in range(n):reader.name();reader.name();assert original[reader.at]==0;reader.at+=1;reader.uint()
    return dict(nonexport_sections_byte_identical=True,private_two_exports_only=True,no_start_section=True,
                all_original_callees_preserved=True,original_imported_functions=n,functions=found)


def packet(data):
    at=0
    def take(n):
        nonlocal at
        value=data[at:at+n];assert len(value)==n;at+=n;return value
    assert take(6)==bytes.fromhex('010000000002')
    mask=take(1)[0];raw=bytearray(8)
    for i in range(8):
        if mask>>i&1:raw[i]=take(1)[0];assert raw[i]!=0
    guid=int.from_bytes(raw,'little');assert take(2)==b'\x05\x50'
    xyz_heading=struct.unpack('<4I',take(16));assert struct.unpack('<I',take(4))[0]==1
    length=take(1)[0];assert length==1;mask=struct.unpack('<I',take(4))[0];values={}
    for key in range(32):
        if mask>>key&1:values[key]=struct.unpack('<I',take(4))[0]
    assert at==len(data)
    return guid,xyz_heading,values


def deep_compare(want,got,counts):
    pending=[(want,got)]
    while pending:
        expected,actual=pending.pop()
        if expected is None:assert type(actual)is int and 0<=actual<=255;counts['explicit_unknown_cells']+=1
        elif type(expected)is dict:
            assert type(actual)is dict and set(expected)==set(actual);pending.extend((value,actual[key])for key,value in expected.items())
        elif type(expected)is list:
            assert type(actual)is list and len(expected)==len(actual);pending.extend(zip(expected,actual))
        else:
            assert type(expected)is type(actual)and expected==actual;counts['compared_known_values']+=1


def review_case(case,expected,record,label,geometry,counts):
    i=case['id'];assert expected['id']==record['id']==label['id']==i
    s=case['input'];want=expected['result'];actual=copy.deepcopy(record['result'])
    actual['pickups']['storage']=[list(bytes.fromhex(row))for row in actual['pickups']['storage']]
    deep_compare(want,actual,counts)
    incoming=s['pickups'];count=incoming['count'];capacity=len(incoming['storage'])
    new_capacity=capacity if count<capacity else max(4,2*capacity)
    assert actual['pickups']['capacity']==new_capacity and actual['pickups']['count']==count+1
    counter=(s['counter']+1)&MASK;visual=9003+s['kind'];display={3:5931,4:5995,5:5991}[s['kind']]
    guid=0xf110000000000000|(visual<<24)|(counter&0xffffff)
    yaw,rng,draws=heading(s['rng_words']);assert want['rng_words']==rng==actual['rng_words']and want['counter']==counter==actual['counter']
    assert label['draws']==draws and actual['message_sequence']==case['message_sequence']and actual['notifications_count']==0
    assert len(actual['packets'])==1 and actual['packets'][0]['opcode']==169
    data=bytes.fromhex(actual['packets'][0]['payload_hex']);pguid,(x,y,z,angle),fields=packet(data)
    assert pguid==guid and angle==yaw
    expected_fields={0:guid&MASK,1:guid>>32,2:33,3:visual,4:0x3f800000,8:display,9:0,14:1,15:x,16:y,17:z,18:yaw,20:35,21:5}
    assert set(fields)==set(expected_fields)|{12,13}
    assert all(fields[key]==value for key,value in expected_fields.items())
    half=f32(fl(yaw)*.5)
    assert abs(fl(fields[12])-math.sin(half))<=2**-21 and abs(fl(fields[13])-math.cos(half))<=2**-21
    cx,cy,radius=map(fl,geometry[s['zone']]);sx,sy=map(fl,s['position_bits'][:2])
    dx,dy=f32(sx-cx),f32(sy-cy);distance=f32(math.hypot(dx,dy));limit=max(f32(radius-2),1.)
    clamped=distance>limit
    px=f32(cx+f32(f32(dx/distance)*limit))if clamped else sx
    py=f32(cy+f32(f32(dy/distance)*limit))if clamped else sy
    assert (x,y)==(bits(px),bits(py))and label['clamped']==clamped
    if case['world']['kind']=='controlled_query_world':
        world=case['world']
        if world['flat_height_bits']is not None:height=world['flat_height_bits']
        else:
            finite={v for v in world['primary']['values_bits']if math.isfinite(fl(v))}
            assert len(finite)==1;height=finite.pop()
        assert z==height;counts['height_independent_controlled_cases']+=1
    else:counts['height_explicit135_artifact_cases']+=1
    rows=copy.deepcopy(incoming['storage'])+[[None]*56 for _ in range(new_capacity-capacity)]
    writes={0:struct.pack('<I',0),8:struct.pack('<IIQ',s['kind'],s['amount'],guid),24:struct.pack('<III',0,8,0),36:struct.pack('<I',visual),40:struct.pack('<4I',x,y,z,s['now_bits'])}
    for offset,content in writes.items():rows[count][offset:offset+len(content)]=content
    assert want['pickups']['storage']==rows
    for ri,row in enumerate(incoming['storage']):
        for offset,value in enumerate(row):
            if ri!=count or 4<=offset<8:
                assert actual['pickups']['storage'][ri][offset]==(case['unknown_poison']if value is None else value)
                counts['retained_input_physical_bytes']+=1
    before=bytes.fromhex(record['game_before8192_hex']);after=bytes.fromhex(record['game_after8192_hex']);assert len(before)==len(after)==8192
    allowed=set(range(1720,1736))|set(range(1868,1892))|set(range(2408,2412))
    assert all(a==b for j,(a,b)in enumerate(zip(before,after))if j not in allowed)
    for offset,value in [(2352,s['now_bits']),(2408,s['counter']),(2412,case['message_sequence']),(1868,capacity),(1876,count)]:assert word(before,offset)==value
    assert [word(before,1720+j*4)for j in range(4)]==s['rng_words']
    assert [word(after,1720+j*4)for j in range(4)]==rng
    assert word(after,2408)==counter and word(after,1876)==count+1 and word(after,1868)==new_capacity
    assert word(after,1888)==1 and word(after,1900)==0
    counts['unchanged_game_bytes_outside_admitted_ranges']+=8192-len(allowed)
    counts['observed_changed_game_bytes']+=sum(a!=b for a,b in zip(before,after))
    counts['packets']+=1;counts['packet_bytes']+=len(data);counts['semantic_actor_fields']+=len(fields)
    counts['exact_yaw_RNG_GUID_cases']+=1


def run_review(out):
    began=time.monotonic();reviewer_before=Path(__file__).read_bytes()
    (out/'reviewer-source.py').write_bytes(reviewer_before)
    assert sha(FINAL/'comparison.json')==FINAL_SHA
    receipt=load(FINAL/'comparison.json');prepared=load(FINAL/'prepared.json');manifest=load(FINAL/'manifest.json')
    assert receipt['cases']==90 and receipt['differences']==0 and load(FINAL/'differences.json')==[]
    frozen=receipt['source_sha256_before'];assert len(frozen)==36 and frozen==receipt['source_sha256_after']==prepared['source_sha256']
    for name,h in frozen.items():assert sha(ROOT/name)==sha(FINAL/'source-snapshot'/name)==h,name
    names,edges=closure([ROOT/'scripts/check_resource_pickup137.py',ROOT/'scripts/run_resource_pickup137_oracle.mjs'])
    assert names==set(frozen)and edges=={tuple(row)for row in receipt['local_source_import_edges']}and len(edges)==91
    for name,h in(receipt['frozen_artifacts']|receipt['artifacts']).items():assert sha(FINAL/name)==h,name
    assert prepared['artifacts']==receipt['frozen_artifacts']and prepared['world_inputs']==receipt['world_inputs']
    for name,h in prepared['world_inputs'].items():assert sha(Path(name))==h
    world_receipt=load(Path(next(name for name in prepared['world_inputs']if name.endswith('/receipt.json'))))
    assert world_receipt['version']=='0.135.1'and world_receipt['original_program_executed']is False and world_receipt['original_memory_read']is False
    assert(FINAL/'expected.json').stat().st_mtime_ns<=(FINAL/'prepared.json').stat().st_mtime_ns<(FINAL/'owned-process.json').stat().st_mtime_ns
    runner=(FINAL/'source-snapshot/scripts/run_resource_pickup137_oracle.mjs').read_text()
    assert 'expected'not in runner and 'world.verify()'in runner and 'WebAssembly.instantiate'in runner
    binary=binary_proof(manifest)
    geometry=literal(FINAL/'source-snapshot/reconstruction/core_spec/spawn_position135_data.py','ZONE_GEOMETRY')
    zone_names=literal(FINAL/'source-snapshot/reconstruction/core_spec/initial_state135_data.py','ZONE_ENTRIES')
    assert manifest['zone_geometry137']==[list(row)for row in geometry]
    cases,expected,labels=load(FINAL/'input.json'),load(FINAL/'expected.json'),load(FINAL/'labels.json')
    actual=[json.loads(row)for row in(FINAL/'stdout.jsonl').read_text().splitlines()]
    assert len(cases)==len(expected)==len(labels)==len(actual)==90
    counts=Counter()
    for index,args in enumerate(zip(cases,expected,actual,labels)):
        assert args[0]['id']==index and args[0]['map_id_utf8']==zone_names[args[0]['input']['zone']][0]
        review_case(*args,geometry,counts)
    for key,value in receipt['comparison'].items():assert counts[key]==value,(key,counts[key],value)
    groups=dict(Counter(row['group']for row in labels));assert groups==receipt['groups']
    matrix=Counter((c['input']['zone'],c['input']['kind'],label['clamped'])for c,label in zip(cases[:72],labels[:72]))
    assert matrix==Counter({(zone,kind,outside):1 for zone in range(12)for kind in(3,4,5)for outside in(False,True)})
    controls=[]
    for label,index,edit in [('mask_known_kind_byte',0,lambda w,g:w['result']['pickups']['storage'][0].__setitem__(8,None)),
        ('RNG_word_corruption',2,lambda w,g:g['result']['rng_words'].__setitem__(0,g['result']['rng_words'][0]^1)),
        ('Game_unallowed_byte',2,lambda w,g:g.__setitem__('game_after8192_hex','01'+g['game_after8192_hex'][2:])),
        ('physical_unknown_input_not_preserved',1,lambda w,g:g['result']['pickups']['storage'].__setitem__(0,g['result']['pickups']['storage'][0][:8]+'00'+g['result']['pickups']['storage'][0][10:]))]:
        w,g=copy.deepcopy(expected[index]),copy.deepcopy(actual[index]);edit(w,g)
        try:review_case(cases[index],w,g,labels[index],geometry,Counter())
        except AssertionError:controls.append(dict(name=label,rejected=True))
        else:raise AssertionError('Independent control accepted '+label)
    runtime=load(FINAL/'resource-pickup137-runtime.json');assert runtime==receipt['runtime']
    assert runtime['fresh_instances']==90 and runtime['functions']=={'1420':90}and runtime['actual_host_calls']==0 and runtime['denied_imports']==878
    assert runtime['max_memory_bytes']<=33554432 and runtime['stack_all_restored']
    assert all(x['before']==x['after']==1048576 and x['returned']for x in runtime['stack_checks'])
    assert sum(x['index']==1420 for x in runtime['stack_checks'])==90
    assert all(x['index']in(1420,91933)for x in runtime['stack_checks'])
    assert all(runtime[key]is False for key in('application_start_called','full_game_started','network_used','user_saves_accessed','original_memory_snapshot_read'))
    terminal=load(FINAL/'process-terminal.json');owned=load(FINAL/'owned-process.json')
    assert terminal==receipt['process']and terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and not terminal['error']
    assert terminal['pid']==terminal['pgid']==owned['pid']==owned['pgid']and owned['deadline_seconds']==60
    assert sha(Path(prepared['command'][0]))=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
    old=load(OLD/'comparison.json');same={n:receipt['frozen_artifacts'][n]==old['frozen_artifacts'][n]for n in('input.json','expected.json','labels.json','refusals.json','resource-pickup137-original-exports.wasm','1420.wat')};assert all(same.values())
    assert 'reconstruction/core_spec/initial_state135_data.py'not in old['source_sha256_before']
    assert reviewer_before==Path(__file__).read_bytes()
    assert all(sha(ROOT/name)==sha(FINAL/'source-snapshot'/name)==digest for name,digest in frozen.items())
    assert all(sha(FINAL/name)==digest for name,digest in(receipt['frozen_artifacts']|receipt['artifacts']).items())
    assert all(sha(Path(name))==digest for name,digest in prepared['world_inputs'].items())
    result=dict(status='passed_scoped_read_only_review',version='0.137.0',build='d171b8f9f',comparison=str((FINAL/'comparison.json').relative_to(ROOT)),comparison_sha256=FINAL_SHA,
        reviewer_sha256=sha(Path(__file__)),source_count=36,local_import_edges=91,source_before_after_snapshot_current_verified=True,
        source_inputs_and_reviewer_hashes_unchanged_across_review=True,
        binary=binary,independent_comparison_counts=dict(counts),groups=groups,negative_control_rejections=controls,
        expected_frozen_before_original=True,original_runner_never_reads_expected=True,all_world4_inputs_frozen=True,
        world_provenance='135 independently produced query artifacts passed as controlled137 inputs, or explicit synthetic World124; not137 world bootstrap',
        unknown_mask_scope='Exactly old producer cells plus uninitialized growth; no known byte masked; retained input None poison explicitly checked.',
        old35_source_batch=dict(receipt=str((OLD/'comparison.json').relative_to(ROOT)),sha256=sha(OLD/'comparison.json'),missing='reconstruction/core_spec/initial_state135_data.py',same_input_expected_module_WAT=same,not_added_to_case_count=True),
        original_owned_terminal=terminal,all_stack_returns_restored=True,actual_host_calls=0,
        archived_model_refusals=load(FINAL/'refusals.json'),refusals_rerun_by_reviewer=False,
        cases=90,original1420_calls=90,full947_calls=0,new_original_cases=0,new_model_validation_cases=0,new_full880_frames=0,
        model_checker_or_original_executed_by_reviewer=False,Windows_executed=False,complete_games=0,
        limits=['8192-byte Game and World124 are explicit controlled fixtures, not complete constructors or ownership.',
            '78 controlled heights checked independently;12 real artifact terrain heights are expected/original comparison with explicit135 provenance, not a reimplementation of terrain queries.',
            'Exact yaw/RNG/GUID/packet bytes and schemas checked; quaternion sin/cos additionally checked with finite f32 tolerance, not a new exact trig model.',
            'Resource scheduler947, collection, other kinds,primary nearest miss,full137world/game/UI/network/native execution remain outside scope.'],
        seconds=time.monotonic()-began)
    save(out/'review.json',result)
    print(json.dumps(dict(directory=str(out),status=result['status'],review_sha256=sha(out/'review.json'),cases=90,new_original_cases=0)),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--worker',type=Path);args=parser.parse_args()
    if args.worker:run_review(args.worker.resolve());return
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('resource-pickup0137-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    started=time.monotonic();error=None
    def stop(sig,frame):raise KeyboardInterrupt('Owned review stop '+str(sig))
    previous=signal.signal(signal.SIGTERM,stop)
    with(out/'stdout.log').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
        child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker',str(out)],stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'))
        save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,deadline_seconds=60))
        try:child.wait(timeout=60)
        except(subprocess.TimeoutExpired,KeyboardInterrupt,OSError)as exc:error=repr(exc)
        finally:
            try:os.killpg(child.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            signal.signal(signal.SIGTERM,previous)
    def missing(group=False):
        try:(os.killpg if group else os.kill)(child.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=missing(),pgid_missing=missing(True),seconds=time.monotonic()-started,deadline_seconds=60,error=error)
    save(out/'process-terminal.json',terminal);print((out/'stdout.log').read_text(),end='');print(json.dumps(terminal))
    assert child.returncode==0 and not error and terminal['pid_missing']and terminal['pgid_missing']


if __name__=='__main__':main()
