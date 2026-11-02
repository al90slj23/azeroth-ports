#!/usr/bin/env python3
"""Expected-first fresh full1367 differential; borrowed history input only."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,ast,hashlib,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_player_death_recap135_oracle import ROOT,build
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.incoming_history135 import IncomingHistory135
from core_spec.player_death_recap135 import recap135

def sha(p):
    with Path(p).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def B(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def state(h):
    rows=[];origins=[]
    for i,encoded in enumerate(h['rows48_hex']):
        row=list(bytes.fromhex(encoded));why=['fixture']*48
        if h['strings'][i]is not None:
            for o in(0,8,16):row[o:o+4]=[None]*4;why[o:o+4]=['resource_pointer']*4
        rows.append(tuple(row));origins.append(tuple(why))
    texts=tuple(None if x is None else tuple(x)for x in h['strings'])
    return IncomingHistory135(h['capacity'],h['head'],h['count'],tuple(rows),texts,tuple(origins))

def sources():
    pending=[ROOT/'scripts'/n for n in('check_player_death_recap135.py','build_player_death_recap135_oracle.py','run_player_death_recap135_oracle.mjs')];seen=set();edges=set()
    def resolve(module):
        parts=Path(*module.split('.'));result=[]
        for folder in('scripts','reconstruction'):
            for p in(ROOT/folder/parts.with_suffix('.py'),ROOT/folder/parts/'__init__.py'):
                if p.is_file():result.append(p);break
        return result
    while pending:
        path=pending.pop()
        if path in seen:continue
        seen.add(path);name=str(path.relative_to(ROOT))
        if path.suffix!='.py':continue
        parts=Path(name).with_suffix('').parts
        for node in ast.walk(ast.parse(path.read_text())):
            modules=[]
            if isinstance(node,ast.Import):modules=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom):
                prefix='.'.join(list(parts[1:-node.level])+([node.module]if node.module else[]))if node.level else node.module or''
                modules=[prefix]+[prefix+'.'+a.name if prefix else a.name for a in node.names]
            for module in modules:
                if not module:continue
                for target in resolve(module):
                    pending.append(target);edges.add((name,str(target.relative_to(ROOT))))
                    for parent in target.parents:
                        if parent in(ROOT/'scripts',ROOT/'reconstruction'):break
                        initializer=parent/'__init__.py'
                        if initializer.is_file():pending.append(initializer);edges.add((name,str(initializer.relative_to(ROOT))))
    return sorted(str(p.relative_to(ROOT))for p in seen),sorted(edges)

def corpus(pilot):
    rows=[]
    def row(stamp=20,damage=1,absorbed=0,hp=50,maxhp=100,source='Kobold',name='Melee',icon='INV_Sword_04',rank=0,mechanic=0):
        return dict(words=[B(x)for x in(stamp,damage,absorbed,hp,maxhp)],texts=[source,name,icon],rank=rank,mechanic=mechanic)
    def add(group,items,now=20,capacity=None,head=0,poison=0xa5):
        cap=len(items)if capacity is None else capacity;assert cap>=len(items)and(cap==0 and head==0 or head<cap)
        back=[bytearray([poison]*48)for _ in range(cap)];texts=[None]*cap
        for logical,item in enumerate(items):
            slot=(head+logical)%cap;record=back[slot];texts[slot]=item['texts']
            for j,text in enumerate(item['texts']):struct.pack_into('<II',record,8*j,0,len(text.encode('utf8')))
            struct.pack_into('<5I',record,24,*item['words']);record[44]=item['rank'];record[45]=item['mechanic']
        h=dict(capacity=cap,head=head,count=len(items),rows48_hex=[bytes(x).hex()for x in back],strings=texts)
        original=dict(id=len(rows),history=h,reference_time_bits=B(now));result=recap135(state(h),B(now))
        rows.append(dict(id=len(rows),group=group,input=original,expected=dict(capacity=result.capacity,raw_hex=result.raw_hex),diagnostic=dict(selected_slots=result.selected_slots,hit_groups=result.hit_groups,source_groups=result.source_groups,total_bits=result.total_bits,absorbed_bits=result.absorbed_bits,avoidable_bits=result.avoidable_bits)))
    add('empty-zero',[]);add('single',[row()]);add('cutoff-inclusive',[row(9.999),row(10),row(20)],capacity=5,head=4)
    if pilot:return rows
    add('empty-capacity',[],capacity=8,head=5);add('expired',[row(0),row(9.999)]);add('future',[row(22),row(25)],now=20)
    add('adjacent-one-second',[row(10),row(11),row(12.0001),row(12.5)],now=20)
    add('reverse-time-adjacent',[row(18),row(11),row(15)],now=20)
    add('same-pair-changing-metadata',[row(19,2,1,source='A',name='B',icon='first',rank=0,mechanic=0),row(20,3,4,source='A',name='B',icon='last',rank=2,mechanic=1)])
    add('interleaved-global-groups',[row(18,5,source='A'),row(18.1,7,source='B'),row(18.2,11,source='A')])
    for n in(7,8,9,20,21,22,25,33):
        add('top8-top6-sort-'+str(n),[row(10+i*9/(n-1),damage=(i*17)%13+.5,source='source'+str(i),name='hit'+str(i))for i in range(n)],capacity=n+3,head=n)
        add('stable-equal-sort-'+str(n),[row(10+i*9/(n-1),damage=5,source='tie'+str(i),name='same')for i in range(n)])
    for v in(-5,-1.5,-.5,-.49999,-0.0,0,.49999,.5,1.5,2.5,1000000.5):
        add('rounding',[row(20,damage=v,absorbed=v,mechanic=1,hp=-v)])
    for v in(-100,0,.1,33.3333,100,200):add('hp-ratio',[row(hp=v,maxhp=100)])
    add('maxhp-lower-bound',[row(maxhp=-5,hp=.5)])
    add('ordered-f32-cancellation',[row(18,16777216,source='a'),row(18.1,1,source='b'),row(18.2,-16777216,source='c')])
    add('mechanic-two-is-true-not-avoidable',[row(19,3,mechanic=2),row(20,5,mechanic=1,source='B')])
    add('unicode-control',[row(source='中文\r\n\t"\\\0',name='烈焰🔥',icon='路径\\图标')])
    add('all-ranks',[row(16+i*.5,rank=i,source='r'+str(i))for i in range(5)])
    add('wrapped400',[row(10+i/40,damage=(i%9)+.25,source='s'+str(i%27),name='n'+str(i%3))for i in range(400)],capacity=512,head=400)
    for position,bits in(('stamp',0x7fc00000),('stamp',0x7f800000),('damage',0x7fc00000),('absorbed',0x7f800000),('hp',0x7fc00000),('maxhp',0x7fc00000)):
        value=row();value['words'][{'stamp':0,'damage':1,'absorbed':2,'hp':3,'maxhp':4}[position]]=bits;add('nonfinite-'+position,[value])
    seed=0x1234abcd
    for case in range(48):
        count=case%24+1;items=[]
        for i in range(count):
            seed=(seed*1664525+1013904223)&0xffffffff
            items.append(row(9+(seed%12000)/1000,damage=((seed>>3)%10000)/32,absorbed=((seed>>8)%100)/16,hp=((seed>>12)%300)-50,maxhp=50+(seed%200),source='s'+str(seed%7),name='n'+str(seed%4),rank=seed%5,mechanic=(seed>>7)%3))
        add('deterministic-mixed',items,capacity=count+3,head=count)
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args();files,edges=sources();before={n:sha(ROOT/n)for n in files}
    rows=corpus(args.phase=='pilot');assert len(rows)<=256
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('player-death-recap135-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    for n,h in before.items():target=out/'source-snapshot'/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes());assert sha(target)==h
    save(out/'fixtures.json',rows);save(out/'inputs.json',[x['input']for x in rows]);save(out/'config.json',dict(input_path=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json')))
    frozen={n:sha(out/n)for n in('fixtures.json','inputs.json','config.json','manifest.json',manifest['module_file'])};assert before=={n:sha(ROOT/n)for n in files}
    node=ROOT/'.toolchain/runtime/node_modules/node/bin/node';assert sha(node)=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
    command=[str(node),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_player_death_recap135_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
    with(out/'results.jsonl').open('w')as stdout,(out/'stderr.log').open('w')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True);save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=60))
        try:child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
    def missing(group=False):
        try:(os.killpg if group else os.kill)(child.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,seconds=time.monotonic()-start,deadline_seconds=60,pid_missing=missing(),pgid_missing=missing(True));save(out/'terminal.json',terminal)
    actual=[json.loads(x)for x in(out/'results.jsonl').read_text().splitlines()];differences=[]
    for c,a in zip(rows,actual):
        assert c['id']==a['id']
        for key,want in c['expected'].items():
            if a[key]!=want:differences.append(dict(id=c['id'],group=c['group'],field=key,expected=want,actual=a[key]))
    assert before=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen}
    save(out/'differences.json',differences);runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    report=dict(version='0.135.1',actual_build='90898d5e3',phase=args.phase,cases=len(rows),actual_cases=len(actual),differences=len(differences),status='passed'if child.returncode==0 and len(actual)==len(rows)and not differences else'failed_preserved',
        full_original_function=1367,expected_before_original=True,input_contains_expected=False,source_sha256_before=before,source_sha256_after=before,local_source_import_edges=edges,
        frozen_artifacts=frozen,original_body_sha256=manifest['entry']['body_sha256'],process=terminal,runtime=runtime,
        artifacts={n:sha(out/n)for n in('results.jsonl','runtime.json','stderr.log','terminal.json','owned-process.json','differences.json')if(out/n).exists()},
        limitations=['Explicit borrowed incoming48 ring and resolvedUTF8 metadata,not independent1073 producer or complete5620/1938 integration.',
            'History resource-pointer words are semanticNone with separately bound bytes; no pointer/heap allocation prediction.',
            'Only five original source-rank labels; larger classification payloads remainunknown.',
            'No Game/App,phase transition,network/native/complete game acceptance.'])
    save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),actual_cases=len(actual),differences=len(differences),first_differences=differences[:2],terminal=terminal)))
    if report['status']!='passed':raise SystemExit(1)

if __name__=='__main__':main()
