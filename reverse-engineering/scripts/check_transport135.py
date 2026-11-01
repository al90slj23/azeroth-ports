#!/usr/bin/env python3
"""Expected-first private6-leaf Web32 transport differential, valid typedcell."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from trace_transport135 import ROOT,SOURCE,SOURCE_SHA,build
from source_closure135 import core_sources

FILES=('scripts/check_transport135.py','scripts/run_transport135_oracle.mjs','scripts/trace_transport135.py',
 'scripts/source_closure135.py','scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py')+core_sources(ROOT,'transport135.py')
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'

def sha(p):
    with Path(p).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

IMPORTED={p:sha(ROOT/p)for p in FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.transport135 import(Transport135,TransportCell135,PayloadRing135,CommandVector135,TransportRow88,
 send_payload,replace_snapshot,poll_commands,replace_rows88,replace_rows12,false_method)


def blob(seed,n):return bytes((seed+j*37)&255 for j in range(n)).hex()

def command_blob(seed):
    # Original45626 constructs this payload-free variant with only i64tag2.
    # Its unused union tail is explicit nonzero backing, not a fabricated live
    # pointer or a guessed arbitrary command discriminant.
    return (b'\2'+bytes(7)+bytes.fromhex(blob(seed,224))).hex()

def row88(seed,mask):
    def text(n,k):return bytes(32+(seed+k+j)%95 for j in range(n)).hex()
    return dict(required=['',text(1+seed%7,1),('名字'+str(seed)).encode().hex()],
        optional=[text(0 if k%2==0 else 3+k,k)if mask>>k&1 else None for k in range(4)],word84=(seed*0x1234567)&0xffffffff)

def initial(cap=0,head=0,count=0,seed=1):
    active={(head+j)%cap for j in range(count)}
    storage=[blob(seed+j,j%11)if j in active or j%2==0 else None for j in range(cap)]
    return dict(strong=1,weak=1,borrow=0,ring=dict(storage=storage,head=head,count=count),
        commands=dict(storage=[],count=0),snapshot=None,rows88=None,rows12=None)

def corpus(full):
    cases=[]
    def add(label,state,ops):cases.append(dict(id=len(cases),label=label,input=dict(initial=state,operations=ops)))
    ops=[dict(kind='false'),dict(kind='poll'),dict(kind='send',hex=''),dict(kind='snapshot',hex=''),dict(kind='rows88',rows=[]),dict(kind='rows12',rows=[]),dict(kind='poll')]
    add('empty-constructor-typed-input',initial(),ops)
    for cap in((0,1,2,4,8)if full else(1,4)):
        for head in sorted({0,cap//2,cap-1})if cap else(0,):
            for count in sorted({0,max(0,cap-1),cap}):
                s=initial(cap,head,count,17+cap+head+count)
                add(f'ring-cap{cap}-head{head}-count{count}',s,[dict(kind='send',hex=blob(1,0)),dict(kind='send',hex=blob(2,17)),dict(kind='send',hex=blob(3,65)),dict(kind='false'),dict(kind='poll')])
    if full:
        for cap in(4,8):
            add(f'wrapped-short-prefix-relocation-cap{cap}',initial(cap,1,cap,63),
                [dict(kind='send',hex=blob(31,9)),dict(kind='send',hex=blob(41,33)),dict(kind='false')])
    for mask in(range(4)if full else range(1)):
        s=initial(4,3,2,51);s.update(snapshot=[None,'',blob(3,257),blob(5,1)][mask],
            rows88=None if mask==0 else[row88(1,15),row88(0,0)],rows12=None if mask==0 else[blob(7,12),blob(9,12)])
        replacement=[row88(10+j,j)for j in range(16)]
        add('owned-options-replace:'+str(mask),s,[dict(kind='snapshot',hex=blob(1,2049)),dict(kind='snapshot',hex=''),
            dict(kind='rows88',rows=replacement),dict(kind='rows88',rows=[row88(255,15)]),dict(kind='rows88',rows=[]),
            dict(kind='rows12',rows=[blob(11+j,12)for j in range(17)]),dict(kind='rows12',rows=[]),dict(kind='rows12',rows=[blob(255,12)]),dict(kind='false')])
    for cap in((0,1,4,8)if full else(4,)):
        for count in sorted({0,cap//2,cap}):
            s=initial(2,1,2,91);s['commands']=dict(storage=[command_blob(77+j)if j<count or j%2==0 else None for j in range(cap)],count=count)
            s['strong']=2
            add(f'command-move-cap{cap}-count{count}',s,[dict(kind='poll'),dict(kind='poll'),dict(kind='send',hex=b'{"type":"choices"}'.hex()),dict(kind='false')])
    return cases


def model(state):
    def record(row):return TransportRow88(tuple(bytes.fromhex(v)for v in row['required']),tuple(None if v is None else bytes.fromhex(v)for v in row['optional']),row['word84'])
    def vec(v):return None if v is None else bytes.fromhex(v)
    return Transport135(TransportCell135(state['strong'],state['weak'],state['borrow'],
        PayloadRing135(tuple(vec(v)for v in state['ring']['storage']),state['ring']['head'],state['ring']['count']),
        CommandVector135(tuple(None if v is None else tuple(bytes.fromhex(v))for v in state['commands']['storage']),state['commands']['count']),
        vec(state['snapshot']),None if state['rows88']is None else tuple(record(v)for v in state['rows88']),
        None if state['rows12']is None else tuple(bytes.fromhex(v)for v in state['rows12'])))


def vec_project(value):return None if value is None else dict(capacity=len(value),length=len(value),hex=value.hex())

def command_project(value):
    return dict(capacity=value.capacity,count=value.count,storage=[None if r is None else list(r)for r in value.storage])

def project(state):
    c=state.cell
    return dict(strong=c.strong,weak=c.weak,borrow=c.borrow,timer_absent=state.armed_at is None,
        ring=dict(capacity=c.ring.capacity,head=c.ring.head,count=c.ring.count,slots=[vec_project(v)for v in c.ring.storage]),
        commands=command_project(c.commands),snapshot=vec_project(c.snapshot),
        rows88=None if c.rows88 is None else dict(capacity=len(c.rows88),count=len(c.rows88),rows=[dict(required=[vec_project(v)for v in row.required],optional=[vec_project(v)for v in row.optional],word84=row.word84)for row in c.rows88]),
        rows12=None if c.rows12 is None else dict(capacity=len(c.rows12),count=len(c.rows12),hex=b''.join(c.rows12).hex()))


def expected(case):
    state=model(case['input']['initial']);stages=[]
    for op in case['input']['operations']:
        kind=op['kind'];moved=None;answer=None
        if kind=='send':state=send_payload(state,bytes.fromhex(op['hex']))
        elif kind=='snapshot':state=replace_snapshot(state,bytes.fromhex(op['hex']))
        elif kind=='poll':state,moved=poll_commands(state);moved=command_project(moved)
        elif kind=='rows88':state=replace_rows88(state,model(dict(initial(),rows88=op['rows'])).cell.rows88)
        elif kind=='rows12':state=replace_rows12(state,tuple(bytes.fromhex(v)for v in op['rows']))
        elif kind=='false':answer=false_method(state)
        else:raise ValueError(kind)
        stages.append(dict(kind=kind,state=project(state),moved=moved,answer=answer))
    return dict(id=case['id'],label=case['label'],stages=stages)


def compare(expected,actual):
    errors=[];counts=dict(known_ring_slots=0,unknown_ring_slots=0,known_command_bytes=0,unknown_command_bytes=0,stages=0)
    def command(e,a,label):
        if e is None or a is None:
            if e!=a:errors.append(dict(field=label+' absent'))
            return
        if(e['capacity'],e['count'])!=(a['capacity'],a['count']):errors.append(dict(field=label+' descriptor'));return
        raw=bytes.fromhex(a['backing_hex'])
        if len(raw)!=232*e['capacity']:errors.append(dict(field=label+' rawbacking'));return
        for j,row in enumerate(e['storage']):
            for k,word in enumerate(row if row is not None else[None]*232):
                counts['unknown_command_bytes'if word is None else'known_command_bytes']+=1
                if word is not None and raw[j*232+k]!=word:errors.append(dict(field=label+' byte',row=j,byte=k))
    if len(expected)!=len(actual):errors.append(dict(field='completed case count'))
    for e,a in zip(expected,actual):
        if e['id']!=a['id']or len(e['stages'])!=len(a['stages']):errors.append(dict(field='case/stage count'));continue
        for j,(x,y)in enumerate(zip(e['stages'],a['stages'])):
            counts['stages']+=1
            for k in('kind','answer'):
                if x[k]!=y[k]:errors.append(dict(id=e['id'],stage=j,field=k))
            p,q=x['state'],y['state']
            for k in('strong','weak','borrow','timer_absent','snapshot','rows88','rows12'):
                if p[k]!=q[k]:errors.append(dict(id=e['id'],stage=j,field=k,expected=p[k],actual=q[k]))
            for k in('capacity','head','count'):
                if p['ring'][k]!=q['ring'][k]:errors.append(dict(id=e['id'],stage=j,field='ring.'+k,expected=p['ring'][k],actual=q['ring'][k]))
            if len(p['ring']['slots'])!=len(q['ring']['slots']):errors.append(dict(field='ring slot count'));continue
            for k,(v,w)in enumerate(zip(p['ring']['slots'],q['ring']['slots'])):
                counts['unknown_ring_slots'if v is None else'known_ring_slots']+=1
                if v is not None and v!=w:errors.append(dict(id=e['id'],stage=j,field='ring slot',index=k,expected=v,actual=w))
            command(p['commands'],q['commands'],f'case{e["id"]}/stage{j}/cellcommands');command(x['moved'],y['moved'],f'case{e["id"]}/stage{j}/moved')
            if not y['source_preserved']or not y['deep_copy_distinct']or not y['unrelated_cell_bytes_preserved']:errors.append(dict(field='invariant'))
            if len(bytes.fromhex(y['raw_cell76_hex']))!=76 or len(bytes.fromhex(y['raw_transport24_hex']))!=24:errors.append(dict(field='rawstruct capture'))
    return errors,counts


def gone(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
    before={p:sha(ROOT/p)for p in FILES};assert before==IMPORTED and sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA
    cases=corpus(args.phase=='full');wanted=[expected(c)for c in cases]
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('transport0135-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    for n,h in before.items():q=out/'source-snapshot'/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/n).read_bytes());assert sha(q)==h
    inp=out/'inputs.json';inp.write_text(json.dumps([dict(id=c['id'],input=c['input'])for c in cases],separators=(',',':'))+'\n')
    exp=out/'expected.json';exp.write_text(json.dumps(wanted,separators=(',',':'))+'\n')
    frozen={p.name:sha(p)for p in(inp,exp,out/'manifest.json',out/manifest['module_file'])}
    assert before=={p:sha(ROOT/p)for p in FILES}
    output,stderr=out/'results.jsonl',out/'stderr.log';start=time.monotonic()
    cmd=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_transport135_oracle.mjs'),str(out),str(inp)]
    with output.open('wb')as so,stderr.open('wb')as se:
        child=subprocess.Popen(cmd,stdout=so,stderr=se,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=-9
    assert gone(child.pid)and gone(child.pid,True)
    after={p:sha(ROOT/p)for p in FILES};assert before==after and frozen=={p.name:sha(p)for p in(inp,exp,out/'manifest.json',out/manifest['module_file'])}
    actual=[json.loads(line)for line in output.read_text().splitlines()];errors,counts=compare(wanted,actual)
    mismatch=out/'mismatches.json';mismatch.write_text(json.dumps(errors,indent=2)+'\n');runtime=out/'transport135-runtime.json'
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,status='passed'if code==0 and not errors else'failed_preserved',cases=len(cases),completed_cases=len(actual),
        differences=len(errors),original_sha256=SOURCE_SHA,source_count=len(before),source_sha256_before=before,source_sha256_after=after,
        expected_before_original=True,expected_in_original_input=False,frozen_artifacts=frozen,comparison=counts,
        runtime=json.loads(runtime.read_text())if runtime.exists()else None,process=dict(command=cmd,pid=child.pid,exit_code=code,seconds=time.monotonic()-start,
        deadline_seconds=60,pid_and_pgid_missing=True),artifacts={p.name:sha(p)for p in(output,stderr,mismatch,runtime)if p.exists()},
        full_App_constructor=False,full880=False,snapshot_used=False,clock_or_logging_host_stubs=False,installed_apps_or_saves_modified=False,
        domain='Quiet original4253 flags20/21=0,timer-tag8=-1;explicit typedcell76/Rustallocowners;opaque232commands movedonly;complete6methods with unchangedcallees')
    target=out/'transport135-comparison.json';target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),status=receipt['status'],cases=len(cases),differences=len(errors),review_sha256=sha(target))))
    if code!=0 or errors:sys.exit(1)


if __name__=='__main__':main()
