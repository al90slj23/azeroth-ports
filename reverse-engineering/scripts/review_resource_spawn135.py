#!/usr/bin/env python3
"""Read-only64-case resource producer review; no original/model/checker executes."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import ast,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
from review_opening_combat135 import sections,missing,allowed_unknown
from review_combat137 import exports
from review_battle_shout135 import F,B,add,sub,mul,literal
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/full0135-oracle-20261101T174727.123299Z'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
MASK=0xffffffff

def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def next_rng(s):
    a,b,c,d=s;rot=lambda x,k:((x<<k)|(x>>(32-k)))&MASK
    return(rot((a+d)&MASK,7)+a)&MASK,(a^b^d,b^a^c,(a^c^(b<<9))&MASK,rot(b^d,11))
def advance(s,n):
    assert 0<=n<=100000
    for _ in range(n):_,s=next_rng(s)
    return s

def uniform(s,hi):
    for draws in range(1,100001):
        value,s=next_rng(s);unit=sub((value>>9)|0x3f800000,0x3f800000);result=add(0,mul(unit,hi))
        if F(result)<F(hi):return result,s,draws
    raise AssertionError('Range watchdog')

def closure(source):
    base=source/'reconstruction';todo=['core_spec.resource_spawn135','core_spec.opening_handoff135','core_spec.spawn_frame_motion135','resource_spec.world_query135'];seen={}
    while todo:
        module=todo.pop()
        if module in seen:continue
        parts=module.split('.');path=base.joinpath(*parts).with_suffix('.py');package=module.rsplit('.',1)[0]
        if not path.exists():path=base.joinpath(*parts)/'__init__.py';package=module
        assert path.is_file();seen[module]=str(path.relative_to(source))
        if len(parts)>1:todo.append(parts[0])
        for n in ast.walk(ast.parse(path.read_text())):
            if isinstance(n,ast.Import):todo.extend(x.name for x in n.names if x.name.split('.')[0]in('core_spec','resource_spec'))
            elif isinstance(n,ast.ImportFrom):
                assert n.level in(0,1);prefix=package+('.'+n.module if n.module else'')if n.level else(n.module or'')
                if prefix.split('.')[0]not in('core_spec','resource_spec'):continue
                todo.append(prefix)
                for alias in n.names:
                    child=prefix+'.'+alias.name
                    if base.joinpath(*child.split('.')).with_suffix('.py').exists():todo.append(child)
    return sorted(set(seen.values()))

def decode169(encoded):
    raw=bytes.fromhex(encoded);assert struct.unpack_from('<I',raw)[0]==1 and raw[4]==0;p=5;variant=raw[p];p+=1;mask=raw[p];p+=1;guid=0
    for i in range(8):
        if mask>>i&1:guid|=raw[p]<<(8*i);p+=1
    object_type,flags=raw[p:p+2];p+=2
    if variant==3:assert(object_type,flags)==(3,112)and raw[p:p+8]==bytes(8);p+=8
    else:assert variant==2 and(object_type,flags)==(5,80)
    x,y,z,yaw=struct.unpack_from('<4I',raw,p);p+=16
    if variant==3:assert struct.unpack_from('<I',raw,p)[0]==0;p+=4+24
    assert struct.unpack_from('<I',raw,p)[0]==1;p+=4;n=raw[p];p+=1;masks=struct.unpack_from('<'+'I'*n,raw,p);p+=n*4;fields={}
    for i,w in enumerate(masks):
        for b in range(32):
            if w>>b&1:fields[i*32+b]=struct.unpack_from('<I',raw,p)[0];p+=4
    assert p==len(raw)and fields[0]==guid&MASK and fields[1]==guid>>32
    return dict(guid=guid,xyz=(x,y,z),yaw=yaw,fields=fields,variant=variant)

def clamp_xy(xyz,geometry):
    cx,cy,radius=geometry;dx,dy=sub(xyz[0],cx),sub(xyz[1],cy);distance=B(math.sqrt(F(B(F(dx)**2+F(dy)**2))));limit=add(radius,0xc0000000)
    limit=limit if F(limit)>1 else 0x3f800000
    if F(distance)<=F(limit):return tuple(xyz[:2]),False
    return(add(cx,mul(B(F(dx)/F(distance)),limit)),add(cy,mul(B(F(dy)/F(distance)),limit))),True

def review_case(c,w,a,label,geometry,counts,extra):
    assert c['id']==w['id']==a['id'];actual=a['result'];wanted=w['result'];inp=c['input'];old=inp['pickups'];packets=actual['packets'];decoded=[decode169(x['payload_hex'])for x in packets]
    assert all(x['opcode']==169 for x in packets)and actual['message_sequence']==c['message_sequence']==1 and actual['notifications_count']==0
    spawned=c['operation']=='produce'or label['status']=='resource2444_spawned';ordinary=[];words=tuple(inp['rng_words']);counter=inp['counter']
    if c['operation']=='tick':
        ordinary=label['ordinary_requests'];words=advance(words,label['ordinary_draws']);counter=(counter+len(ordinary))&MASK
        assert len(ordinary)==actual['units']['count']-c['units']['count']==3
        for request,packet in zip(ordinary,decoded):assert packet['guid']==request['guid']and packet['xyz']==tuple(request['position_bits'])and packet['variant']==3
        due=F(inp['now_bits'])>=F(inp['next_resource2444_bits']);kinds=[int.from_bytes(bytes(row[8:12]),'little')for row in old['storage'][:old['count']]];resource_count=sum(3<=k<=5 for k in kinds)
        assert actual['next_resource2444_bits']==(add(inp['now_bits'],B(45))if due else inp['next_resource2444_bits'])
        if not due:assert label['status']=='resource2444_future'and not spawned;extra['future_cases']+=1
        elif resource_count>=2:
            assert label['status']=='resource2444_cap'and label['counted_resources']==resource_count and not spawned;extra['cap_cases']+=1
            extra['cap_cases_with_nonzero_marker']+=any(3<=k<=5 and any(row[:4])for k,row in zip(kinds,old['storage'][:old['count']]))
        else:
            assert label['counted_resources']==resource_count
            for draws in range(1,100001):
                output,words=next_rng(words);product=output*3
                if(product&0xc0000000)!=0xc0000000:break
            kind,amount=3+(product>>32),words[0]
            assert kind==label['chosen_kind']and amount==label['amount']and draws==label['selection_draws'];extra['selection_rejection_cases']+=draws>1
            position=label['position'];words=advance(words,label['position_draws']);assert words==tuple(position['rng_words'])
            assert position['draws']==label['position_draws']
            if label['group']=='947-real-world-13th-unclamped':assert position['attempts']==position['fallback_attempts']==13 and position['draws']==26 and position['branch']=='unclamped_height';extra['fallback13_cases']+=1
        if not spawned:assert label['selection_draws']==label['position_draws']==label['actor_draws']==0
    else:kind,amount=inp['kind'],inp['amount']
    cap=len(old['storage']);newcount=old['count']+int(spawned);newcap=cap if newcount<=cap else max(4,2*cap)
    assert actual['pickups']['count']==newcount and actual['pickups']['capacity']==newcap
    if spawned:
        source_xyz=inp['position_bits']if c['operation']=='produce'else label['position']['position_bits'];xy,clamped=clamp_xy(source_xyz,geometry);extra['1417_clamp_cases']+=clamped
        resource=bytes.fromhex(actual['pickups']['storage'][old['count']]);value=lambda o:struct.unpack_from('<I',resource,o)[0];xyz=struct.unpack_from('<3I',resource,40)
        assert xyz[:2]==xy and xyz==tuple(label['final_position_bits'])and value(0)==0 and value(8)==kind and value(12)==amount and value(52)==inp['now_bits']
        assert struct.unpack_from('<3I',resource,24)==(0,8,0)
        visual=9006+kind-3;display={3:5931,4:5995,5:5991}[kind];counter=(counter+1)&MASK;guid=0xf110000000000000|(visual<<24)|(counter&0xffffff)
        assert struct.unpack_from('<Q',resource,16)[0]==guid and value(36)==visual
        yaw,words,draws=uniform(words,0x40c90fdb);assert draws==(label['draws']if c['operation']=='produce'else label['actor_draws'])
        packet=decoded[-1];assert packet['variant']==2 and packet['guid']==guid and packet['xyz']==xyz and packet['yaw']==add(yaw,0)
        fields=packet['fields'];assert all(fields[k]==v for k,v in {2:33,3:visual,4:0x3f800000,8:display,9:0,14:1,15:xyz[0],16:xyz[1],17:xyz[2],18:add(yaw,0),20:35,21:5}.items())
        extra['resource_packet_bindings']+=1
    assert tuple(actual['rng_words'])==words and actual['counter']==counter and len(packets)==len(ordinary)+int(spawned)
    for i,row in enumerate(old['storage']):
        observed=bytes.fromhex(actual['pickups']['storage'][i])
        for offset,value in enumerate(row):
            if spawned and i==old['count']and(offset<4 or offset>=8):continue
            assert observed[offset]==(c['unknown_poison']if value is None else value),'Prior physical pickup backing changed'
    if c['operation']=='tick':
        for i,row in enumerate(c['units']['storage'][:c['units']['count']]):assert bytes.fromhex(actual['units']['storage'][i])==bytes(c['unknown_poison']if v is None else v for v in row)
        for offset,value in actual['other_clocks'].items():assert value==dict(c['initial_scalars'])[int(offset)]
    converted=dict(actual)
    for name in('pickups','units'):
        if name in converted:converted[name]={**converted[name],'storage':[list(bytes.fromhex(x))for x in converted[name]['storage']]}
    def compare(want,got,path=()):
        if want is None:
            assert len(path)>=4 and path[-4]in('pickups','units')and path[-3]=='storage'and type(got)is int and 0<=got<=255
            name,index,offset=path[-4],path[-2],path[-1]
            if name=='pickups':
                if index<cap:assert old['storage'][index][offset]is None and not(spawned and index==old['count']and(offset<4 or offset>=8))
                elif index==old['count']and spawned:assert 4<=offset<8
            elif index<actual['units']['count']:allowed_unknown('units',wanted['units']['storage'][index],offset)
            counts['explicit_unknown_cells']+=1;extra['nonzero_unknown_original_cells']+=bool(got);return
        assert type(want)is type(got),(path,type(want),type(got))
        if isinstance(want,dict):
            assert set(want)==set(got)
            for key,value in want.items():compare(value,got[key],path+(key,))
        elif isinstance(want,list):
            assert len(want)==len(got)
            for i,(x,y)in enumerate(zip(want,got)):compare(x,y,path+(i,))
        else:assert want==got,(path,want,got);counts['equal_known_values']+=1
    compare(wanted,converted);counts['packets']+=len(packets);counts['packet_bytes']+=sum(len(bytes.fromhex(x['payload_hex']))for x in packets)

def main():
    began=time.monotonic();out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('resource-spawn135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir();report=json.loads((RUN/'resource-spawn135-comparison.json').read_text());source=RUN/'source-snapshot'
    assert sha(RUN/'resource-spawn135-comparison.json')=='85b5c088e80e33d059b880275e59aa6f2a3613344fc887f2886566130fdde005'and report['differences']==0 and report['source_sha256_before']==report['source_sha256_after']
    assert len(report['source_sha256_before'])==58
    for name,digest in report['source_sha256_before'].items():assert sha(source/name)==digest==sha(ROOT/name)
    assert sha(ROOT/'reconstruction/core_spec/resource_spawn135.py')=='f142c219f60abc3b69ba645ef2fd87adec7728a0e034069e524d06b15c0b2aa3'
    production=sorted(n for n in report['source_sha256_before']if n.startswith('reconstruction/'));assert production==closure(source)
    for name in production:
        for node in ast.walk(ast.parse((source/name).read_text())):
            if isinstance(node,ast.Call):
                f=node.func;fn=f.id if isinstance(f,ast.Name)else f.attr if isinstance(f,ast.Attribute)else''
                assert fn not in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__')
    for name,digest in(report['frozen_artifacts']|report['artifacts']).items():assert sha(RUN/name)==digest
    for name,digest in report['world_inputs'].items():assert sha(Path(name))==digest
    original=(ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm').read_bytes();manifest=json.loads((RUN/'manifest.json').read_text());changed=(RUN/manifest['module_file']).read_bytes();assert hashlib.sha256(original).hexdigest()==report['original_sha256']and hashlib.sha256(changed).hexdigest()==manifest['module_sha256']
    a,b=sections(original),sections(changed);assert[x[0]for x in a]==[x[0]for x in b]and 8 not in[x[0]for x in a]and all(original[x:y]==changed[u:v]for(k,x,_,y),(_,u,_,v)in zip(a,b)if k!=7)
    assert exports(changed)==exports(original)+[['research135_spawn_pickup',0,1417],['research135_spawn_tick',0,947],['research135_resource_stack0',3,0]]
    trace=json.loads((RUN/'resource-spawn135-static.json').read_text())
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as c,(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
        for row in trace['functions']:
            assert hashlib.sha256(original[row['body_start']:row['body_end']]).hexdigest()==row['body_sha256'];position=c.execute('select wat_start,wat_end from functions where idx=?',(row['index'],)).fetchone();assert position==(row['wat_start'],row['wat_end']);wat.seek(position[0]);raw=wat.read(position[1]-position[0]);assert raw==(RUN/f"resource-{row['index']}.wat").read_bytes()and hashlib.sha256(raw).hexdigest()==row['wat_sha256']
    inputs=json.loads((RUN/'resource-input.json').read_text());expected=json.loads((RUN/'resource-expected.json').read_text());actual=[json.loads(x)for x in(RUN/'resource-results.jsonl').read_text().splitlines()];labels=json.loads((RUN/'resource-labels.json').read_text());assert len(inputs)==len(expected)==len(actual)==len(labels)==64
    geometry=literal(source/'reconstruction/core_spec/spawn_position135_data.py','ZONE_GEOMETRY')[0];counts=Counter();extra=Counter();worlds=[]
    for c,w,a,label in zip(inputs,expected,actual,labels):
        assert c['world']['kind']=='independently_parsed451_asset_world_inputs'and c['world']['primary']is None and c['world']['flat_height_bits']is None
        assert c['world']['nav_width']==280 and c['world']['secondary_width']==560
        for entry in c['world']['artifacts'].values():assert report['world_inputs'][entry['path']]==entry['sha256']
        worlds.append(c['world']);review_case(c,w,a,label,geometry,counts,extra)
    assert all(x==worlds[0]for x in worlds)and dict(counts)==report['comparison']and counts['packets']==196 and counts['packet_bytes']==32043 and extra['selection_rejection_cases']==5 and extra['fallback13_cases']==2
    asset_receipt=Path(worlds[0]['directory'])/'receipt.json';asset=json.loads(asset_receipt.read_text());assert asset['version']=='0.135.1'and asset['original_program_executed']is False and asset['original_memory_read']is False
    terrain=Path(worlds[0]['artifacts']['terrain-query.bin']['path']).read_bytes();assert struct.unpack_from('<I',terrain)[0]==9
    provenance=json.loads((RUN/'resource-opening-input.json').read_text());assert len(provenance)==52 and all(x['natural_elapsed_frames']==0 and x['opening_units']==4 and x['opening_pickups']==2 for x in provenance)
    runtime=report['runtime'];assert runtime==json.loads((RUN/'resource-spawn135-runtime.json').read_text())and runtime['cases']==runtime['fresh_instances']==64 and runtime['functions']=={'947':52,'1417':12}
    assert all(x['returned']and x['before']==x['after']==1048576 for x in runtime['stack_checks'])and runtime['stack_all_restored']and runtime['actual_host_calls']==0 and runtime['denied_imports']==878 and runtime['max_memory_bytes']<=runtime['memory_cap_bytes']==33554432
    assert all(runtime[k]is False for k in('application_start_called','full_game_started','network_used','user_saves_accessed','original_memory_snapshot_read'))
    terminal=report['process'];assert terminal['exit_code']==0 and terminal['launcher_error']is None and terminal['seconds']<60 and missing(terminal['pid'])and missing(terminal['pgid'],True)and terminal==json.loads((RUN/'resource-process-terminal.json').read_text())
    assert(RUN/'resource-stderr.log').stat().st_size==0 and json.loads((RUN/'resource-differences.json').read_text())==[]
    prepared=json.loads((RUN/'resource-prepared.json').read_text());assert prepared['expected_before_original']and prepared['source_sha256']==report['source_sha256_before']and prepared['artifacts']==report['frozen_artifacts']and prepared['deadline_seconds']==60
    assert '--max-old-space-size=512'in prepared['command']and'--wasm-max-mem-pages=512'in prepared['command']
    assert report['full880_frames']==report['natural40_second_runs']==0
    for name,digest in report['source_sha256_before'].items():assert sha(source/name)==digest==sha(ROOT/name)
    result=dict(status='passed_scoped_read_only_review',comparison=str(RUN/'resource-spawn135-comparison.json'),comparison_sha256=sha(RUN/'resource-spawn135-comparison.json'),reviewer_script_sha256=sha(Path(__file__)),source_files=58,production_AST_closure_files=len(production),current_and_frozen_SHA_verified=True,only_private_exports_added=True,all_nonexport_sections_and_callees_unchanged=True,static_function_windows_verified=9,
        cases=64,original_entries=runtime['functions'],comparison_counts=dict(counts),independent_semantic_checks=dict(extra),all196_opcode169_payloads_strictly_compared_and_decoded=True,resource_amount_post_selection_state0_independently_verified=True,ordinary_prefix_RNG_draws_are_frozen_model_provenance=True,resource_rng_and_final_four_words_independently_replayed=True,
        world_input=dict(source='Independent451-asset query artifacts; manually packed query-equivalent Rc124/terrain/nav/secondary layout into fresh original with explicit unconsumed metadata zeros',primary_absent=True,terrain_tiles=9,nav_width=280,secondary_width=560,artifact_hashes=report['world_inputs'],asset_receipt_sha256=sha(asset_receipt),original_snapshot_read=False,original_World_constructor_claimed=False,asset_parser_or_query_model_rerun_by_reviewer=False),
        clamp_and_height_order='Original1417 clamp radius-2 and first height query precede resource common height query. FinalXY independently recomputed; finalZ and exact packet bytes strictly rechecked from frozen expected/original, without rerunning terrain query models.',fallback13_scope='Two realworld fixtures explicitly raise playerZ100; full13516 RNG confirms13 trials/26draws, final unconditional branch then1417 final clamp/height. Not a natural elapsed run.',cap_marker_scope='Count active-prefix kinds3..5 regardless of marker; cap/future stop resource work, while ordinary947 prefix still consumes its own RNG/world queries.',
        process=terminal,host_calls=0,stack_all_restored=True,model_or_original_or_checker_executed_by_reviewer=False,new_original_cases=0,new_full880_frames=0,natural40_second_runs=0,already_integrated_into400_chain=False,pending=report['pending'],elapsed_seconds=time.monotonic()-began)
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],counts=dict(counts),semantic=dict(extra))),flush=True)
if __name__=='__main__':main()
