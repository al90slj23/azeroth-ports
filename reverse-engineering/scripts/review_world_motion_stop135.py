#!/usr/bin/env python3
"""Independent readonly nonflat17119 audit. Only reviewer code executes."""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_player_motion135 as M  # Previously independent raw-world reader.
ROOT=M.ROOT;RUN=ROOT/'evidence/world-motion-stop135-oracle-20261102T000919.144127Z'
RECEIPT='8a49cd52bcaaf2b8fbd803ab0476f1dce459e7c837a57ac6b4c16bb83a983e99'
STRIDES={'units':424,'auxiliary':112,'claims':88}
F=M.F;B=M.B;add=M.add;sub=M.sub;mul=M.mul;div=M.div;U=M.u;put=M.put;sha=M.sha;load=M.load
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def packed(n):
    b=n.to_bytes(8,'little');return bytes([sum(1<<i for i,v in enumerate(b)if v)])+bytes(v for v in b if v)
def reference(inp,world,counts):
    now=inp['now_bits'];sequence=inp['sequence'];packets=list(inp['prefix']);capacity=inp['packet_capacity'];count=len(packets);heights=[];stopped=[];vectors={}
    for name,stride,origin,dest,start,duration,guid,timer in(('units',424,316,328,340,344,112,None),('auxiliary',112,32,44,56,60,16,68),('claims',88,44,56,68,72,24,76)):
        rows=[list(v)if isinstance(v,list)else list(bytes.fromhex(v))for v in inp['storage'][name]];n=inp['counts'][name];assert 0<=n<=len(rows)<=512 and all(len(row)==stride for row in rows)
        for index,row in enumerate(rows[:n]):
            if name=='units':due=U(row)==0 and F(U(row,duration))>0 and F(now)<F(add(U(row,duration),U(row,start)))
            elif name=='auxiliary':due=F(U(row,duration))>0 and F(now)<F(add(U(row,duration),U(row,start)))
            else:due=not F(now)>=F(add(U(row,start),U(row,duration)))
            if not due:counts['inactive_active_records']+=1;continue
            if name=='claims'and F(U(row,duration))<=0:
                xyz=[U(row,dest+4*j)for j in range(3)];counts['claim_destination_only']+=1
            else:
                ratio=div(sub(now,U(row,start)),U(row,duration))
                if F(ratio)<0:ratio=0;counts['negative_ratio_clamps']+=1
                if F(ratio)>1:ratio=B(1);counts['above_one_ratio_clamps']+=1
                xyz=[add(U(row,origin+4*j),mul(sub(U(row,dest+4*j),U(row,origin+4*j)),ratio))for j in range(3)]
            z=world.height(xyz[0],xyz[1]);source='world29631'if z is not None else'interpolated';result_z=xyz[2]if z is None else z
            heights.append(dict(domain=name,record_index=index,xy_bits=xyz[:2],interpolated_z_bits=xyz[2],result_z_bits=result_z,source=source));counts[source]+=1
            xyz[2]=result_z
            for offset in(origin,dest):
                for j,value in enumerate(xyz):put(row,offset+4*j,value)
            put(row,start,now);put(row,duration,0)
            if timer is not None:put(row,timer,now)
            actor=U(row,guid)|(U(row,guid+4)<<32);stopped.append(str(actor));sequence=(sequence+1)&0xffffffff
            if count==capacity:capacity=max(4,capacity*2)
            count+=1;packets.append(dict(opcode=221,capacity=32,payload_hex=(packed(actor)+struct.pack('<4I',*xyz,sequence)+b'\1').hex()));counts['stopped_'+name]+=1
        vectors[name]=dict(count=n,storage=[row if any(v is None for v in row)else bytes(row).hex()for row in rows]);counts['full_source_backing_bytes']+=stride*len(rows)
    return dict(sequence=sequence,packet_capacity=capacity,packet_count=count,packets=packets,vectors=vectors,heights=heights,stopped_guids=stopped)

def sparse_input(inp):
    result={**inp,'storage':{}}
    for name,stride,origin,dest,start,duration,guid in(('units',424,316,328,340,344,112),('auxiliary',112,32,44,56,60,16),('claims',88,44,56,68,72,24)):
        result['storage'][name]=[]
        for index,h in enumerate(inp['storage'][name]):
            raw=bytes.fromhex(h);ranges=[]
            if index<inp['counts'][name]:
                if name=='units':
                    ranges=[(0,4)]
                    if U(raw)==0:
                        ranges.append((duration,duration+4))
                        if F(U(raw,duration))>0:
                            ranges.append((start,start+4))
                            if F(inp['now_bits'])<F(add(U(raw,duration),U(raw,start))):ranges.extend(((guid,guid+8),(origin,dest+12)))
                elif name=='auxiliary':
                    ranges=[(duration,duration+4)]
                    if F(U(raw,duration))>0:
                        ranges.append((start,start+4))
                        if F(inp['now_bits'])<F(add(U(raw,duration),U(raw,start))):ranges.extend(((guid,guid+8),(origin,dest+12)))
                else:
                    ranges=[(start,duration+4)]
                    if not F(inp['now_bits'])>=F(add(U(raw,start),U(raw,duration))):
                        ranges.extend(((guid,guid+8),(dest,dest+12)))
                        if not F(U(raw,duration))<=0:ranges.append((origin,origin+12))
            result['storage'][name].append([v if any(a<=j<b for a,b in ranges)else None for j,v in enumerate(raw)])
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();out=args.output.resolve();assert out.is_relative_to((ROOT/'evidence').resolve());out.mkdir();started=time.monotonic()
    reviewers={str(x.relative_to(ROOT)):sha(x)for x in(Path(__file__),Path(M.__file__))}
    for n,h in reviewers.items():dest=out/'reviewer-source'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/n).read_bytes());assert sha(dest)==h
    assert sha(RUN/'comparison.json')==RECEIPT;report=load(RUN/'comparison.json');prepared=load(RUN/'prepared.json');manifest=load(RUN/'manifest.json');handoff=load(RUN/'task-handoff.json')
    assert(report['cases'],report['full_original17119_calls'],report['differences'])==(56,56,0)and report['status']=='scoped_original_differential_passed'
    files=report['source_sha256_before'];assert len(files)==17 and files==report['source_sha256_after']==prepared['source_sha256']
    for n,h in files.items():assert sha(ROOT/n)==sha(RUN/'source-snapshot'/n)==h,n
    edges=M.source_edges(RUN/'source-snapshot',files);assert edges==[tuple(x)for x in report['source_import_edges']]==[tuple(x)for x in prepared['source_import_edges']]and len(edges)==34
    prod={n for n in files if n.startswith('reconstruction/')};todo=['reconstruction/core_spec/world_motion_stop135.py'];seen=set()
    while todo:
        n=todo.pop()
        if n in seen:continue
        seen.add(n);todo.extend(b for a,b in edges if a==n)
    assert seen==prod and len(prod)==10
    for table in('frozen_artifacts','artifacts'):
        for n,h in report[table].items():assert sha(RUN/n)==h,(table,n)
    for n,h in handoff['new_files'].items():assert sha(ROOT/n)==h
    assert len(handoff['new_files'])==6 and handoff['comparison_sha256']==RECEIPT and not handoff['shared_sources_modified']
    assert report['expected_before_original']and prepared['expected_before_original']and not report['input_contains_expected']
    checker=(RUN/'source-snapshot/scripts/check_world_motion_stop135.py').read_text();assert checker.index("save(out/'expected.json'")<checker.index('subprocess.Popen(')
    original=M.ORIGINAL.read_bytes();assert hashlib.sha256(original).hexdigest()==M.ORIGINAL_SHA==report['original_sha256']
    module=(RUN/manifest['module_file']).read_bytes();assert hashlib.sha256(module).hexdigest()==manifest['module_sha256']==report['module_sha256']
    old,new=M.sections(original),M.sections(module);assert[k for k,*_ in old]==[k for k,*_ in new]and not any(k==8 for k,*_ in old)
    assert all(original[a:z]==module[b:y]for(k,a,_,z),(_,b,_,y)in zip(old,new)if k!=7)
    ex=lambda raw,sects:M.exports(raw,next(x for x in sects if x[0]==7))
    assert ex(module,new)==ex(original,old)+[('research_world_motion_stop135_stop',0,17119),('research_world_motion_stop135_stack0',3,0)]
    r=next(x for x in old if x[0]==1)[2];n,r=M.leb(original,r);types=[]
    for _ in range(n):
        assert original[r]==0x60;a,r=M.leb(original,r+1);params=original[r:r+a].hex();r+=a;b,r=M.leb(original,r);results=original[r:r+b].hex();r+=b;types.append([params,results])
    r=next(x for x in old if x[0]==3)[2];n,r=M.leb(original,r);decl=[]
    for _ in range(n):a,r=M.leb(original,r);decl.append(a)
    r=next(x for x in old if x[0]==10)[2];n,r=M.leb(original,r);bodies=[]
    for _ in range(n):size,a=M.leb(original,r);r=a+size;bodies.append((a,r))
    functions={};texts={}
    with sqlite3.connect((M.PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(M.PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
        for idx in(17119,17217,16340,29631,23181,45845,18670,46295):
            row=dict(db.execute('select *from functions where idx=?',(idx,)).fetchone());a,b=bodies[idx-878];assert(a,b)==(row['body_start'],row['body_end']);stream.seek(row['wat_start']);text=stream.read(row['wat_end']-row['wat_start']);assert len(text)<1048576
            functions[idx]=dict(body_start=a,body_end=b,body_sha256=hashlib.sha256(original[a:b]).hexdigest(),signature=types[decl[idx-878]],wat_bytes=len(text),wat_sha256=hashlib.sha256(text).hexdigest());texts[idx]=text.decode();(out/f'{idx}.wat').write_bytes(text)
    for k,guard in manifest['body_guards'].items():
        f=functions[int(k)];assert f['signature']==[guard['params_hex'],guard['results_hex']]and all(f[n]==guard[n]for n in('body_start','body_end','body_sha256'))
    assert 'call 29631'in texts[17119]and'call 23181'in texts[17119]and'call 17217'in texts[17119]and'call 16340'in texts[17119]
    assert 'f32.load offset=12'in texts[17119]and'i32.const 56'in texts[17119]and'call 29631'in texts[17217]and'call 29631'in texts[16340]
    assert all(x in texts[29631]for x in('i32.load8_u offset=112','i32.load offset=48','call 18670','i32.load offset=84','f32.gt','f32.load offset=108'))
    assert all(x in texts[18670]for x in('f32.const 0x1.1eb852p-4','f32.const -0x1.1eb852p-4','call 46295'))
    inputs=load(RUN/'inputs.json');snapshot=Path(inputs['snapshot_path']);assert snapshot==M.SNAPSHOT and sha(snapshot)==M.SNAPSHOT_SHA==inputs['snapshot_sha256'];memory=snapshot.read_bytes();world=M.World(memory,inputs['world_rc']);assert inputs['world_rc']==M.R
    ranges=sorted(set(world.ranges));assert ranges==[tuple(x)for x in inputs['world_ranges']]and len(ranges)==2318 and sum(n for _,n in ranges)==5950608
    h=hashlib.sha256()
    for address,n in ranges:h.update(struct.pack('<2I',address,n));h.update(memory[address:address+n])
    digest=h.hexdigest();assert digest==inputs['expected_world_digest']==report['world']['expected_world_digest'];del memory
    assert U(world.header,56)==0xffffffff and world.header[120]==0 and len(world.tiles)==9 and world.secondary[3]==560
    fixtures=load(RUN/'fixtures.json');expected=load(RUN/'expected.json');actual=[json.loads(x)for x in(RUN/'stdout.jsonl').read_text().splitlines()];assert len(fixtures)==len(expected)==len(actual)==len(inputs['cases'])==56
    counts=Counter();groups=Counter();cases=[];world_digest=dict(sha256=digest,bytes=5950608)
    for c,i,e,a in zip(fixtures,inputs['cases'],expected,actual):
        assert c['id']==i['id']==e['id']==a['id']and c['input']==i and c['expected']==e['expected']and set(i)=={'id','now_bits','sequence','storage','counts','packet_capacity','prefix'}
        p=reference(i,world,counts);assert p==c['expected'],(i['id'],'independent state/height/packets')
        before=a['before'];after=a['after'];q=after['queue'];oldraw=bytes.fromhex(before['raw_game2592_hex']);raw=bytes.fromhex(after['raw_game2592_hex']);assert len(raw)==len(oldraw)==2592
        assert before['vectors']=={name:dict(count=i['counts'][name],storage=i['storage'][name])for name in STRIDES}and after['vectors']==p['vectors']
        assert before['queue']['packets']==i['prefix']and q['packets']==p['packets']and(q['capacity'],q['count'])==(p['packet_capacity'],p['packet_count'])
        physical=bytearray([0xa5]*2592)
        for offset,value in((2348,M.R),(2352,i['now_bits']),(2412,i['sequence']),(1880,i['packet_capacity']),(1884,before['queue']['pointer']),(1888,len(i['prefix']))):put(physical,offset,value)
        for name,base in(('units',1784),('auxiliary',656),('claims',2108)):
            put(physical,base,len(i['storage'][name]));put(physical,base+4,U(oldraw,base+4));put(physical,base+8,i['counts'][name]);assert 0<U(oldraw,base+4)<268435456
        assert oldraw==physical,(i['id'],'exact fixture bind')
        desired=bytearray(oldraw)
        for offset,value in((2412,p['sequence']),(1880,p['packet_capacity']),(1888,p['packet_count'])):put(desired,offset,value)
        if q['capacity']!=before['queue']['capacity']:assert 0<q['pointer']<268435456;put(desired,1884,q['pointer']);counts['observed_packet_vector_pointer_words']+=1
        assert raw==desired and U(raw,2348)==M.R
        n=len(i['prefix']);prefix=bytes.fromhex(before['queue']['active_metadata_hex']);assert len(prefix)==n*16 and q['active_metadata_hex'][:n*32]==prefix.hex()
        for j,entry in enumerate(i['prefix']):
            metadata=prefix[j*16:(j+1)*16];assert(U(metadata),U(metadata,8),struct.unpack_from('<H',metadata,12)[0])==(entry['capacity'],len(bytes.fromhex(entry['payload_hex'])),entry['opcode'])and metadata[14:]==b'\xa5\xa5'and 0<U(metadata,4)<268435456
        assert before['world']==after['world']==world_digest and a['full17119']and(a['stack_after'],a['host_calls'],a['world_rc'],a['snapshot_bytes'])==(1048576,0,M.R,166395904)
        counts['all_Game_bytes']+=2592;counts['prefix_metadata_bytes']+=len(prefix);counts['new221_packets']+=len(p['packets'])-n;counts['new_payload_bytes']+=sum(len(bytes.fromhex(x['payload_hex']))for x in p['packets'][n:]);groups[c['group']]+=1;cases.append(dict(id=i['id'],group=c['group'],stops=len(p['heights']),heights=p['heights'],sequence=p['sequence']))
    partials=load(RUN/'partial-projections.json');known=unknown=0
    for part in partials:
        i=part['case_id'];sparse=sparse_input(inputs['cases'][i]);p=reference(sparse,world,Counter());assert{n:v['storage']for n,v in p['vectors'].items()}==part['vectors']
        assert p['packets']==fixtures[i]['expected']['packets']and p['heights']==fixtures[i]['expected']['heights']
        k=u=0
        for name,rows in part['vectors'].items():
            for j,cells in enumerate(rows):
                observed=bytes.fromhex(actual[i]['after']['vectors'][name]['storage'][j])
                for o,v in enumerate(cells):
                    if v is None:assert sparse['storage'][name][j][o]is None;u+=1
                    else:assert observed[o]==v;k+=1
        assert(k,u)==(part['known_bytes'],part['unknown_cells_preserved']);known+=k;unknown+=u
    assert(known,unknown)==(216,3080)
    runtime=load(RUN/'runtime.json');terminal=load(RUN/'owned-terminal.json');assert runtime==report['runtime']and terminal==report['process']and terminal['exit_code']==0 and terminal['seconds']<terminal['deadline_seconds']==60 and terminal['pid_missing']and terminal['pgid_missing']and M.missing(terminal['pid'])and M.missing(terminal['pgid'],True)
    assert(runtime['cases'],runtime['full17119_calls'],runtime['fresh_instances'],runtime['stack_guards'],runtime['actual_host_calls'],runtime['denied_imports'],runtime['max_memory_bytes'])==(56,56,56,277,0,878,166395904)
    assert runtime['world_bytes_hashed_per_side_total']==5950608*56 and not any(runtime[k]for k in('fresh_world_constructed','externref_table_restored','app_start_called','network_used','user_saves_accessed'))
    assert counts['all_Game_bytes']==145152 and counts['full_source_backing_bytes']==82544 and counts['new221_packets']==165 and counts['prefix_metadata_bytes']==48 and counts['world29631']==150 and counts['interpolated']==15 and dict(groups)==report['groups']
    for n,h in files.items():assert sha(ROOT/n)==sha(RUN/'source-snapshot'/n)==h
    for n,h in reviewers.items():assert sha(ROOT/n)==h
    assert sha(RUN/'comparison.json')==RECEIPT
    result=dict(status='passed-within-declared-domain',author_receipt_sha256=RECEIPT,new_original_calls=0,production_imports=0,production_executions=0,source_count=17,production_sources=10,local_import_edges=34,sources_verified=files,reviewer_sources=reviewers,static_functions=functions,counts=dict(counts),world_queries=dict(world.queries),world_input=dict(snapshot_sha256=M.SNAPSHOT_SHA,world_rc=M.R,range_count=2318,range_bytes=5950608,digest=digest,primary_present=False,secondary_width=560,fresh_producer=False),cases=cases,groups=dict(groups),partial_projection=dict(known_bytes_original_compared=known,None_preservation_model_only=unknown,cases=[x['case_id']for x in partials],new_original_calls=0),runtime=runtime,process=terminal,task_handoff_sha256=sha(RUN/'task-handoff.json'),artifact_sha256={n:sha(RUN/n)for n in set(report['artifacts'])|set(report['frozen_artifacts'])|{'comparison.json','task-handoff.json'}},seconds=time.monotonic()-started,limitations=['56 full17119 calls consume restored observed world input,not freshworld/actualdeath/fullApp/880.17217/16340 counts inferred statically,not instrumented.','Primary absent;nearest23181 Z-only branch static/interface only,no runtime credit.','150 original-packet-matching world heights and15 interpolated misses independently recomputed;source categories are reference diagnostics,not original instrumentation.','All fullGame deltas/backing/payloads/capacities/prefix metadata match;new packet-vector heap pointerwords are explicit allocator observations.','2318 independent raw query input ranges hash stable before/after each original call;not all world allocations/geometries or Rc lifecycle.','216 known sparse bytes matched existing original cases;3080 None preservation and negative unknown-world/marker guards remain model properties,not extra original cases.'])
    save(out/'review.json',result);print(json.dumps(dict(output=str(out/'review.json'),sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])))
if __name__=='__main__':main()
