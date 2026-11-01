#!/usr/bin/env python3
"""Read-only independent review of frozen120-frame opening/combat evidence.

No original/producer/checker executes. This separately validates streamed
ordering, raw captures, declared projection comparisons, bounded unknown masks,
source closure and terminal state. A separate Dijkstra traversal checks the
distance-map digest against the independent navigation artifact.
"""
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import ast
import hashlib
import heapq
import json
import os
import struct
import sys
import time

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'evidence/opening-combat0135-oracle-20261101T154826.676203Z'
STAGES=('player','extra','owned_effects','hits','area','effects','deadline','secondary','ai','collect','claims','spawn','special','terminal')
NPC_WRITTEN=((0,4),(8,4),(16,4),(40,4),(64,4),(112,136),(280,139))
LAYOUTS={'companions':(2108,88),'units':(1784,424),'areas':(1796,88),'effects120':(1808,120),
 'delayed56':(1820,56),'deadline32':(1832,32),'hits112':(1844,112),'secondary112':(1856,112),
 'pickups':(1868,56),'candidates80':(1904,80),'special':(1916,40),'windows':(1964,8),
 'boundaries':(2120,8),'owned80':(1656,80),'live32':(1704,32),'timed12':(596,12),'active84':(644,84),
 'xp_queue8':(2144,8),'currency_queue8':(2156,8)}


def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    except PermissionError:return None
    return False


def sections(raw):
    def leb(p):
        n=s=0
        while True:
            b=raw[p];p+=1;n|=(b&127)<<s
            if b<128:return n,p
            s+=7;assert s<=28
    assert raw[:8]==b'\0asm\1\0\0\0';p=8;result=[]
    while p<len(raw):
        begin=p;kind=raw[p];size,start=leb(p+1);p=start+size;assert p<=len(raw);result.append((kind,begin,p))
    return result


def check_value(want,actual,path,counts):
    if want is None and path[-3:-1]==('pickup_words',path[-2])and path[-1]==1:
        assert type(actual)is int;counts['unwritten_pickup_arrival_words']+=1;return
    assert type(want)is type(actual),(path,type(want),type(actual))
    if isinstance(want,dict):
        for k,v in want.items():assert k in actual;check_value(v,actual[k],path+(k,),counts)
    elif isinstance(want,list):
        assert len(want)==len(actual),(path,len(want),len(actual))
        for i,(a,b)in enumerate(zip(want,actual)):check_value(a,b,path+(i,),counts)
    else:assert want==actual,(path,want,actual);counts['projection_leaves']+=1


def allowed_unknown(name,row,offset):
    if name=='units':
        assert not any(a<=offset<a+n for a,n in NPC_WRITTEN)
        if 4<=offset<8:assert row[:4]==[0,0,0,0]
    elif name=='pickups':assert 4<=offset<8 and row[:4]==[0,0,0,0]
    elif name=='special':assert 8<=offset<16 or 36<=offset<40
    elif name=='live32':
        kind=int.from_bytes(bytes(row[8:12]),'little');spell=int.from_bytes(bytes(row[20:24]),'little')
        assert 16<=offset<20 and kind in(7,8,9,12)or 12<=offset<16 and spell==1020
    else:raise AssertionError(('Unknown active byte outside recovered write masks',name,offset))


def check_snapshot(raw,want,counts,maximum):
    game=bytes.fromhex(raw['raw_game2592_hex']);assert len(game)==2592 and raw['stack']==1048576
    u=lambda o:struct.unpack_from('<I',game,o)[0]
    projection=raw['projection'];assert projection['phase2587']==game[2587]and projection['now_bits']==u(2352)
    for key,offset in(('spawn_counter',2408),('message_sequence',2412),('kill_cost_bits',2420),('generation_counter2400',2400)):
        assert projection[key]==u(offset)
    assert projection['rng_words']==list(struct.unpack_from('<4I',game,1720))
    assert projection['selection_kind2585']==game[2585]
    assert projection['distance_map_updated_at_bits']==u(2372)
    assert raw['ownership']['game_world_pointer']==u(2348)==raw['ownership']['app_cache_pointer']==26204808
    app=bytes.fromhex(raw['ownership']['raw_app5168_hex']);assert len(app)==5168 and app[5165]==0
    for name,(offset,stride)in LAYOUTS.items():
        vector=raw['vectors'][name];cap,ptr,count=struct.unpack_from('<3I',game,offset)
        assert (vector['capacity'],vector['pointer'],vector['count'],vector['stride'])==(cap,ptr,count,stride)
        rows=[bytes.fromhex(v)for v in vector['storage']];assert len(rows)==cap and all(len(v)==stride for v in rows)
        assert hashlib.sha256(b''.join(rows)).hexdigest()==vector['storage_sha256'];maximum[name]=max(maximum[name],count)
    if want is None:return
    check_value(want['projection'],projection,('projection',),counts)
    for name,expected in want['vectors'].items():
        actual=raw['vectors'][name]
        for field in('capacity','count'):
            if field in expected:assert expected[field]==actual[field];counts['vector_shape_fields']+=1
        for field in('storage','records'):
            if field not in expected:continue
            rows=expected[field];observed=actual['storage']if field=='storage'else actual['storage'][:actual['count']]
            assert len(rows)==len(observed)
            for i,(row,encoded)in enumerate(zip(rows,observed)):
                payload=bytes.fromhex(encoded);assert len(row)==len(payload)
                for offset,(known,value)in enumerate(zip(row,payload)):
                    if known is None:
                        if i<actual['count']:allowed_unknown(name,row,offset)
                        counts['unknown_cells']+=1;counts['unknown_cells_nonzero_original']+=bool(value)
                    else:assert type(known)is int and known==value,(name,i,offset,known,value);counts['strict_record_bytes']+=1


def independent_distance_sha(directory,fixtures,report):
    receipt=Path(report['world_input']['receipt']);world=json.loads(receipt.read_text());base=receipt.parent
    nav=(base/world['world_artifacts']['navigation']['file']).read_bytes();meta=world['world_artifacts']['navigation'];width=meta['width']
    float32=lambda w:struct.unpack('<f',struct.pack('<I',w))[0]
    rounded=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
    xy=fixtures['opening']['projection']['player_xyz'];origin=meta['origin_xy_bits']
    x,y=(int(rounded(float32(a)-float32(b)))for a,b in zip(xy[:2],origin));assert 0<=x<width and 0<=y<width
    seed=x+y*width;cost=[65535]*len(nav);cost[seed]=0;heap=[(0,seed)]
    while heap:
        old,index=heapq.heappop(heap)
        if old!=cost[index]:continue
        cy,cx=divmod(index,width)
        for yy in range(max(0,cy-1),min(width,cy+2)):
            for xx in range(max(0,cx-1),min(width,cx+2)):
                target=xx+width*yy
                if target==index or nav[target]or xx!=cx and yy!=cy and(nav[xx+width*cy]or nav[cx+width*yy]):continue
                if old+1<cost[target]:cost[target]=old+1;heapq.heappush(heap,(old+1,target))
    payload=b''.join(struct.pack('<H',v)for v in cost)
    return dict(count=len(cost),start_index=seed,field24=sum(v!=65535 for v in cost),values_sha256=hashlib.sha256(payload).hexdigest())


def main():
    directory=Path(sys.argv[1]).resolve()if len(sys.argv)>1 else DEFAULT
    began=time.monotonic();out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('opening-combat0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    report=json.loads((directory/'comparison.json').read_text());fixtures=json.loads((directory/'fixtures.json').read_text());inputs=json.loads((directory/'inputs.json').read_text())
    assert report['differences']==0 and report['status']=='matched_requested_budget'and report['source_sha256_before']==report['source_sha256_after']
    for name,digest in report['source_sha256_before'].items():
        assert sha(directory/'source-snapshot'/name)==digest and sha(ROOT/name)==digest,name
    assert len(report['source_sha256_before'])==90
    for name,key in(('fixtures.json','expectations_sha256'),('inputs.json','inputs_sha256'),('results.jsonl','original_results_sha256')):assert sha(directory/name)==report[key]
    assert inputs==[{k:fixtures[k]for k in('id','input','actions')}]
    production=[p for p in report['source_sha256_before']if p.startswith('reconstruction/')];assert len(production)==80
    io=[]
    for name in production:
        tree=ast.parse((directory/'source-snapshot'/name).read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Call):
                f=node.func;fn=f.id if isinstance(f,ast.Name)else f.attr if isinstance(f,ast.Attribute)else''
                if fn in('open','read_bytes','read_text','write_bytes','write_text','Popen','system','eval','exec','__import__'):io.append((name,fn))
    assert not io,io
    original=(ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm').read_bytes();manifest=json.loads((directory/'manifest.json').read_text());module=(directory/manifest['module_file']).read_bytes()
    assert hashlib.sha256(original).hexdigest()==report['original_sha256']and hashlib.sha256(module).hexdigest()==manifest['module_sha256']
    a,b=sections(original),sections(module);assert[k for k,_,_ in a]==[k for k,_,_ in b]and 8 not in[k for k,_,_ in a]
    assert all(original[x:y]==module[u:v]for(k,x,y),(_,u,v)in zip(a,b)if k!=7)
    del original,module
    expected_order=[('case_start',None,None),('constructor',None,None),('opening',None,None)];frame=0
    for index,action in enumerate(fixtures['actions']):
        if action['kind']=='select':expected_order.append(('stage',index,'select'))
        else:expected_order.append(('clock_control',index,None));expected_order.extend(('stage',index,kind)for kind in STAGES);frame+=1
    expected_order.append(('case_end',None,None));assert frame==120
    distance=independent_distance_sha(directory,fixtures,report);counts=Counter();maximum=defaultdict(int);stage_index=0;clock=0;previous=None;selection=None;last=None;records=Counter();packet_max=0;locale=None
    with(directory/'results.jsonl').open()as stream:
        for line_index,line in enumerate(stream):
            assert time.monotonic()-began<120
            raw=json.loads(line);records[raw['record_kind']]+=1;kind,action_index,stage_kind=expected_order[line_index]
            assert raw['record_kind']==kind and raw['id']==0
            if action_index is not None:assert raw['action_index']==action_index
            if stage_kind is not None:assert raw['kind']==stage_kind
            if kind=='case_start':locale=raw['locale_prestate'];assert locale['effective_index']==0 and locale['once_flag']==3
            if kind=='clock_control':
                action=fixtures['actions'][action_index];assert raw['old_bits']==clock and raw['dt_bits']==action['dt_bits']
                f=lambda w:struct.unpack('<f',struct.pack('<I',w))[0]
                clock=struct.unpack('<I',struct.pack('<f',f(clock)+f(action['dt_bits'])))[0]
                assert raw['new_bits']==clock and raw['original880_called']is False and raw['only_external_game_write_offset']==2352
            if kind in('constructor','opening','stage'):
                want=fixtures['opening']if kind=='opening'else fixtures['stages'][stage_index]['expected']if kind=='stage'else None
                check_snapshot(raw,want,counts,maximum);packet_max=max(packet_max,raw['packets']['count'])
                if kind=='stage':
                    assert raw['stage_index']==stage_index and raw['projection']['now_bits']==clock;stage_index+=1
                    if raw['kind']=='select':
                        assert previous['projection']['phase2587']==2 and raw['input_index']==0
                        cards=[c['ability_id']for c in previous['projection']['candidates']];assert cards==['thunder_clap','battle_shout','bloodthirst']
                        assert raw['projection']['phase2587']==1 and len(raw['projection']['owned_records_hex'])==2
                        selection=dict(action_index=action_index,clock_bits=clock,candidates=cards,selected_index=0,selected_id=cards[0],phase_after=1)
                    if raw['projection']['distance_map']is not None:
                        for k,v in distance.items():assert raw['projection']['distance_map'][k]==v
                previous=raw;last=raw
            if kind=='case_end':
                assert raw['boundary']is None and raw['host_calls']==[] and raw['stage_count']==1681 and raw['locale_writes']==0
                assert raw['locale_after']==locale
                for call in raw['calls']:assert call['stack_after']==1048576
                calls=[c for c in raw['calls']if c['role']!='original_allocator'];assert len(calls)==1683 and all(c['returned']for c in calls)
    assert line_index+1==len(expected_order)and stage_index==1681 and selection
    # No omitted nonempty timed/queued/secondary payload was accepted as empty.
    empty_domains=('effects120','delayed56','hits112','active84','timed12','deadline32','secondary112','xp_queue8','currency_queue8')
    assert all(maximum[k]==0 for k in empty_domains),dict(maximum)
    assert report['runtime']['output_bytes']==(directory/'results.jsonl').stat().st_size<268435456
    assert report['process']['exit_code']==0 and report['process']['seconds']<60 and(directory/'stderr.log').stat().st_size==0
    terminal=dict(pid_missing=missing(report['process']['pid']),pgid_missing=missing(report['process']['pgid'],True));assert all(terminal.values())
    assert json.loads((directory/'differences.json').read_text())==[]
    assert all(sha(ROOT/name)==digest for name,digest in report['source_sha256_before'].items())
    result=dict(status='passed_scoped_read_only_review',comparison=str(directory/'comparison.json'),comparison_sha256=sha(directory/'comparison.json'),
        reviewer_script_sha256=sha(Path(__file__)),source_files=90,production_files=80,all_current_and_frozen_sources_verified=True,
        production_direct_IO_calls=io,nonexport_sections_unchanged=True,strict_stream_order=True,stream_record_counts=dict(records),
        declared_projection_recompared=True,comparison_counts=dict(counts),active_unknown_masks_restricted_to_recovered_write_sets=True,
        omitted_payload_max_counts={k:maximum[k]for k in empty_domains},observed_vector_max_counts=dict(maximum),
        independent_dijkstra_distance_map=distance,first_selection=selection,frames_after_first_selection=120-87,
        final_progression=last['projection']['progression'],final_gold=last['projection']['gold'],observed_packet_count_max=packet_max,
        packet_payloads_claimed_compared=False,all_packet_payloads_preserved_as_observations=True,
        terminal=terminal,original_program_executed_by_reviewer=False,model_producer_executed_by_reviewer=False,
        new_original_cases=0,new_full880_frames=0,elapsed_seconds=time.monotonic()-began,
        limitations=['One seed/class/race/navigationFalse/stationary12s context; no broader input or full-game acceptance.',
          'Preparsed independent world/original snapshot/external clock remain separate declared inputs.',
          'Raw packet queues are nonempty and retained, but their unmodeled payload semantics are explicitly not claimed compared.',
          'Original full raw heap/vector captures remain concrete; unknown independent bytes are bounded masks, not predicted zero.',
          'This review checks existing frozen outputs/source/protocol; it does not rerun any original or add a differential case.'])
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],seconds=result['elapsed_seconds'])))


if __name__=='__main__':main()
