#!/usr/bin/env python3
"""Read-only semantic projection of ONE caller-frozen 0.135.1 memory image.

No WASM, original function, browser, network, save or producer is invoked.
Observed allocator/inactive bytes remain raw observations, never predictions.
Offsets inherit existing validated opening/headless/query observation layouts.
"""
from dataclasses import dataclass,asdict
import hashlib,json,struct

VERSION='0.135.1'
BUILD='0898d5e3'
ORIGINAL_SHA256='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PLAYER_MODELED_KEYS=(22,28,34,716,717,1109,1176)


@dataclass(frozen=True)
class Vector135:
    name:str
    capacity_offset:int|None
    pointer_offset:int
    count_offset:int
    stride:int
    evidence:str


VECTORS=(
    Vector135('owned_skill_sources8',None,172,176,8,'stats/level/racial oracle'),
    Vector135('timed12',596,600,604,12,'proc/level/racial oracle'),
    Vector135('active84',644,648,652,84,'headless/frame oracle'),
    Vector135('auxiliary_motion112',None,660,664,112,'movement pause count/pointer; capacity unresolved'),
    Vector135('owned80',1656,1660,1664,80,'initial/headless oracle'),
    Vector135('adjustments16',None,1672,1676,16,'stats/level oracle; capacity unresolved'),
    Vector135('passives8',None,1696,1700,8,'stats/level oracle; capacity unresolved'),
    Vector135('live32',1704,1708,1712,32,'initial/headless oracle'),
    Vector135('units424',1784,1788,1792,424,'opening/headless oracle'),
    Vector135('areas88',1796,1800,1804,88,'headless oracle'),
    Vector135('effects120',1808,1812,1816,120,'headless/effect oracle'),
    Vector135('delayed56',1820,1824,1828,56,'headless/effect oracle'),
    Vector135('deadline32',1832,1836,1840,32,'headless/frame oracle'),
    Vector135('hits112',1844,1848,1852,112,'headless oracle'),
    Vector135('secondary112',1856,1860,1864,112,'headless/frame oracle'),
    Vector135('pickups56',1868,1872,1876,56,'opening/headless oracle'),
    Vector135('packets16',1880,1884,1888,16,'opening oracle; payload Vec0/4/8,opcode u16+12'),
    Vector135('notifications12',1892,1896,1900,12,'opening oracle; byte Vec0/4/8'),
    Vector135('candidates80',1904,1908,1912,80,'candidate/headless oracle'),
    Vector135('special40',1916,1920,1924,40,'opening/headless oracle'),
    Vector135('windows8',1964,1968,1972,8,'opening oracle'),
    Vector135('item_modifiers8',2024,2028,2032,8,'stats/candidate/level oracle'),
    Vector135('ability_modifiers20',2036,2040,2044,20,'new ability/selection cycle oracle'),
    Vector135('definitions36',2048,2052,2056,36,'stats/proc/level oracle'),
    Vector135('blocked_ids8',2084,2088,2092,8,'candidate oracle; pointer/length pairs'),
    Vector135('banished_keys12',2096,2100,2104,12,'candidate oracle; String cap/ptr/len'),
    Vector135('companions_claims88',2108,2112,2116,88,'opening companion; headless claim alias, not two vectors'),
    Vector135('boundaries8',2120,2124,2128,8,'opening oracle'),
    Vector135('xp_queue8',2144,2148,2152,8,'headless/selection cycle oracle'),
    Vector135('currency_queue8',2156,2160,2164,8,'headless/selection cycle oracle'),
)

U32_FIELDS={
    'victory_field400':400,'action_tag416':416,
    'action_payload420_raw':420,'action_payload424_raw':424,'action_payload428_raw':428,
    'action_payload432_raw':432,'action_payload436_raw':436,'movement_gate440':440,'movement_time444_bits':444,'busy488':488,
    'absorbed740_bits':740,'maximum_shield744_bits':744,'aux756_bits':756,'reserve768_bits':768,
    'earned1100':1100,'source_aux1348_bits':1348,
    'player_x_bits':1416,'player_y_bits':1420,'player_z_bits':1424,'heading1428_bits':1428,
    'level1432':1432,'xp1436':1436,'hp1440_bits':1440,'aux1444_bits':1444,'aux1448_bits':1448,'gold1456':1456,
    'extra_cast1596_bits':1596,'timer1628_bits':1628,'action_sequence1644':1644,'speed1648_bits':1648,'last_hit1652_bits':1652,
    'velocity_x_bits':1736,'velocity_y_bits':1740,'world_rc2348':2348,'clock2352_bits':2352,
    'effect_counter2356':2356,'effect_clock2364_bits':2364,'distance_map2368':2368,'pending_upgrades2376':2376,
    'generation_counter2400':2400,'spawn_counter2408':2408,'message_sequence2412':2412,'spawn_budget2416_bits':2416,
    'kill_cost2420_bits':2420,'due2424_bits':2424,'previous_x_bits':2428,'previous_y_bits':2432,'previous_z_bits':2436,
    'due2440_bits':2440,'due2444_bits':2444,'due2448_bits':2448,
    'initial2452_bits':2452,'initial2456_bits':2456,'initial2460_bits':2460,'initial2464_bits':2464,
    'initial2468_bits':2468,'initial2472_bits':2472,'player_tree_root2476':2476,'player_tree_depth2480':2480,
    'zone_multiplier2516_bits':2516,'startblock_localpeer2528':2528,'members2540':2540,
}
BYTE_FIELDS={
    'rank273':273,'flag275':275,'class360':360,'race361':361,'heal_gate387':387,
    'flags772':772,'context908':908,'flag2568':2568,'flag2572':2572,'flag2573':2573,'mode_flag2574':2574,
    'start_bit2575':2575,'protection2576':2576,'flag2578':2578,'gate2579':2579,'flag2581':2581,
    'mode2582':2582,'deny2583':2583,'selection_kind2585':2585,'phase2587':2587,'global_phase2588':2588,
}
NPC_OPENING_WRITES=((0,4),(8,4),(16,4),(40,4),(64,4),(112,136),(280,139))


@dataclass(frozen=True)
class CaptureLimits135:
    vector_capacity:int=16384
    vector_bytes:int=16*1024*1024
    total_bytes:int=32*1024*1024
    payload_bytes:int=1024*1024
    tree_nodes:int=512
    tree_depth:int=8
    terrain_tiles:int=512
    chunks_per_tile:int=1024


def capture_schema135():
    return dict(version=VERSION,build=BUILD,original_sha256=ORIGINAL_SHA256,app_bytes=5168,
        game_app_offset=16,game_bytes=2592,supported_present_game_tag=0,menu_game_absent_tag=2,
        u32_fields=U32_FIELDS,byte_fields=BYTE_FIELDS,derived23_offsets=list(range(1536,1628,4)),
        rng_offsets=[1720,1724,1728,1732],racial_offset=1256,racial_stride=80,source_guid_offset=1336,
        outgoing_f64_offset=984,incoming_f64_offset=992,vectors=[asdict(v)for v in VECTORS],
        unresolved_header1952=dict(capacity_word=1952,pointer_word=1956,count_word=1960,stride=None),
        unit424=dict(guid_u64=112,definition_pointer=284,hp_bits=288,max_hp_bits=292,marker_u32=0,
            death_time_bits_conditional=4,kind_i32_offsets=[40,64,244],elite_byte=416,
            from_xyz_bits=[316,320,324],to_xyz_bits=[328,332,336],movement_time_bits=340,duration_bits=344,priority_until_bits=372),
        pickup56=dict(marker=0,arrival_bits_initially_unwritten=4,kind=8,amount=12,guid_u64=16,
            aux_header=[24,28,32],visual_id=36,xyz_bits=[40,44,48],spawn_time_bits=52),
        transport=dict(app_holder_pointer=4768,app_vtable=4772,supported_vtable=1495776,
            holder_bytes=24,holder_cell_pointer=16,cell_bytes=76,ring_cap_ptr_head_count=[12,16,20,24],
            commands_cap_ptr_count=[28,32,36],command_stride=232),
        player_tree=dict(root_offset=2476,depth_offset=2480,node_count_u16=50,keys_u16=52,values_u32=4,children_u32=76,max_keys=11),
        world=dict(game_pointer_offset=2348,app_cache_pointer_offset=5116,raw_rc_bytes=124,
            tiles=(8,12,16,36),tile_bounds=(20,24,28,16),nav=(32,36,40,1),
            nav_origin_width=(44,48,52),primary_tag=56,primary_values_ptr_len=(72,76),
            primary_origin_width=(80,84,88),secondary=(92,96,100,4),secondary_origin_width=(104,108,112),
            fallback_bits=116,flat_byte=120,tile_chunks=(0,4,8,264),chunk_vertices=(0,4,8,12),holes_u16=260),
        capture_contract='One synchronous immutable linear-memory copy at a genuine original return boundary; no G/phase/Once/cache writes.',
        snapshot_input_contract='bytes, or a contiguous readonly byte memoryview whose actual owner is immutable bytes; no implicit freeze/copy in this reader.',
        bytes_contract='Active bytes and inactive capacity backing are observed separately; neither zero nor initialization is inferred.',
        opening_npc_constructor_written_ranges=NPC_OPENING_WRITES,
        original_execution=False,independent_model=False)


def capture_game_entry135(memory_bytes,app_pointer,*,include_world=True,limits=CaptureLimits135()):
    """Project only caller-frozen bytes; bounds/unsupported regions remain errors.

    This is a snapshot input adapter. It does not manufacture independent state
    or legal pointers. The caller must bind snapshotSHA and original identity.
    A readonly view is accepted only when its actual buffer owner is bytes.
    The caller owns the explicit freeze time; this reader never freezes a view.
    """
    if not isinstance(memory_bytes,(bytes,memoryview)):raise TypeError('Immutable caller-frozen bytes required')
    memory=memoryview(memory_bytes)
    if not memory.readonly:raise TypeError('Writable/live memory is forbidden')
    if not isinstance(memory.obj,bytes):raise TypeError('Immutable bytes owner required; readonly mutable-owner views are forbidden')
    if not memory.c_contiguous:raise TypeError('Contiguous frozen bytes required')
    if memory.itemsize!=1 or memory.format not in('B','b','c'):raise TypeError('A byte view over immutable bytes is required')
    memory=memory.cast('B')
    if type(app_pointer)is not int or app_pointer<16:raise ValueError('Explicit actual App pointer required')
    ranges=[];boundaries=[];total=0
    def take(p,n,label):
        nonlocal total
        if type(p)is not int or type(n)is not int or p<0 or n<0 or p+n>len(memory):raise ValueError(label+': snapshot bounds')
        if n>limits.vector_bytes or total+n>limits.total_bytes:raise ValueError(label+': declared capture byte budget')
        total+=n;ranges.append(dict(label=label,pointer=p,bytes=n));return bytes(memory[p:p+n])
    def u(p):
        if not 0<=p<=len(memory)-4:raise ValueError('word outside snapshot')
        return struct.unpack_from('<I',memory,p)[0]
    def attempt(label,fn):
        try:return fn()
        except(ValueError,struct.error)as exc:
            boundaries.append(dict(region=label,error=str(exc)));return dict(status='unresolved_or_capture_boundary',error=str(exc))
    def span(p,n,label):
        raw=take(p,n,label);return dict(pointer=p,bytes=n,sha256=hashlib.sha256(raw).hexdigest(),raw_hex=raw.hex())
    def vector(base,v,maximum_capacity=None):
        pointer,count=u(base+v.pointer_offset),u(base+v.count_offset)
        capacity=None if v.capacity_offset is None else u(base+v.capacity_offset)
        maximum=limits.vector_capacity if maximum_capacity is None else maximum_capacity
        if count>maximum or capacity is not None and(count>capacity or capacity>maximum):raise ValueError(v.name+': capacity/count budget or shape')
        n=count if capacity is None else capacity
        raw=take(pointer,n*v.stride,v.name+'.backing')
        return dict(pointer=pointer,count=count,capacity=capacity,stride=v.stride,
            capacity_semantics='unrestored; active rows only'if capacity is None else'observed full capacity',
            raw_backing_hex=raw.hex(),active_records_hex=[raw[i*v.stride:(i+1)*v.stride].hex()for i in range(count)],
            inactive_backing_hex=raw[count*v.stride:].hex(),sha256=hashlib.sha256(raw).hexdigest())
    app=take(app_pointer,5168,'rawApp5168');G=app_pointer+16;tag=struct.unpack_from('<Q',app,16)[0]
    result=dict(version=VERSION,build=BUILD,original_sha256=ORIGINAL_SHA256,App=app_pointer,G=G,memory_bytes=len(memory),
        raw_app5168_hex=app.hex(),game_tag_u64=str(tag),boundaries=boundaries,
        app_context=dict(marker_u64=str(struct.unpack_from('<Q',app,0)[0]),previous_f64_raw_u64=str(struct.unpack_from('<Q',app,8)[0]),
            lcg_seed_u64=str(struct.unpack_from('<Q',app,4928)[0]),world_cache_pointer=struct.unpack_from('<I',app,5116)[0],
            selected_profile_tag_u32=struct.unpack_from('<I',app,3376)[0],transport_pointer=struct.unpack_from('<I',app,4768)[0],
            transport_vtable=struct.unpack_from('<I',app,4772)[0]),
        snapshot_is_explicit_input=True,independent_state_producer=False,original_functions_called=0,
        table_or_globals_or_externref_restored=False,physical_pointer_ownership_validated=False)
    if tag!=0:
        result.update(status='menu_or_unsupported_game_variant',supported_present_game_observed=False,source_ranges=ranges)
        return result
    raw=take(G,2592,'rawGame2592')
    result.update(status='captured_declared_present_game_fields',supported_present_game_observed=True,raw_game2592_hex=raw.hex(),
        scalar_words={name:struct.unpack_from('<I',raw,offset)[0]for name,offset in U32_FIELDS.items()},
        flags={name:raw[offset]for name,offset in BYTE_FIELDS.items()},
        derived23_bits={str(o):struct.unpack_from('<I',raw,o)[0]for o in range(1536,1628,4)},
        rng_words=list(struct.unpack_from('<4I',raw,1720)),source_guid_u64=str(struct.unpack_from('<Q',raw,1336)[0]),
        outgoing_f64_raw_u64=str(struct.unpack_from('<Q',raw,984)[0]),incoming_f64_raw_u64=str(struct.unpack_from('<Q',raw,992)[0]),
        racial80_hex=raw[1256:1336].hex(),vectors={v.name:attempt(v.name,lambda v=v:vector(G,v))for v in VECTORS})
    mode,phase,global_phase=raw[2582],raw[2587],raw[2588]
    result['running_gate']=dict(mode=mode,individual_phase=phase,global_phase=global_phase,
        phase_gate_allows_running=(phase==1 if mode==0 else global_phase==1),clock2352_bits=u(G+2352),
        actual_clock_advancement_not_proved_by_single_snapshot=True)
    def ability(record_hex,label):
        record=bytes.fromhex(record_hex);pointer=struct.unpack_from('<I',record)[0]
        if not pointer:raise ValueError(label+': null definition remains unresolved')
        definition=take(pointer,88,label+'.definition88');p,n=struct.unpack_from('<2I',definition,12)
        if n>limits.payload_bytes:raise ValueError(label+': ability ID budget')
        return dict(definition_pointer=pointer,definition88_hex=definition.hex(),ability_id_hex=take(p,n,label+'.id').hex(),execution_kind=definition[84])
    owned=result['vectors']['owned80'].get('active_records_hex',[])
    result['ability_definitions']=[attempt('racial_definition',lambda:ability(result['racial80_hex'],'racial'))]+[
        attempt('owned_definition'+str(i),lambda r=r,i=i:ability(r,'owned'+str(i)))for i,r in enumerate(owned)]
    for name in('packets16','notifications12'):
        value=result['vectors'][name]
        def payloads():
            rows=[]
            for i,h in enumerate(value.get('active_records_hex',[])):
                record=bytes.fromhex(h);capacity,pointer,count=struct.unpack_from('<3I',record)
                if count>capacity or capacity>limits.payload_bytes:raise ValueError(name+': payload shape/budget')
                data=take(pointer,capacity,name+str(i)+'.payload_backing')
                row=dict(capacity=capacity,pointer=pointer,length=count,payload_hex=data[:count].hex(),backing_hex=data.hex(),raw_metadata_hex=h)
                if name=='packets16':row['opcode_u16']=struct.unpack_from('<H',record,12)[0]
                rows.append(row)
            return rows
        value['payloads']=attempt(name+'.payloads',payloads)
    def candidates():
        rows=[]
        for h in result['vectors']['candidates80'].get('active_records_hex',[]):
            row=bytes.fromhex(h);tag,p,n,index,tier=struct.unpack_from('<5I',row,60)
            item=dict(tag60=tag,tier=tier,owned_index=index,raw80_hex=h)
            if tag==0x80000000 or tag<0x80000000 or tag==0x80000001:
                if n>limits.payload_bytes:raise ValueError('candidate payload budget')
                item.update(payload_kind='new_id'if tag==0x80000000 else'upgrade_kinds',payload_hex=take(p,n,'candidate.payload').hex())
            elif tag==0x80000004:item.update(payload_kind='gold',gold=p)
            else:item.update(payload_kind='unrestored_variant')
            rows.append(item)
        return rows
    result['candidate_payloads']=attempt('candidates.payloads',candidates)
    def tree():
        root,depth=u(G+2476),u(G+2480);nodes=[];items=[];seen=set()
        if root and depth>limits.tree_depth:raise ValueError('tree depth budget')
        def walk(p,level):
            if not p or p in seen or len(seen)>=limits.tree_nodes:raise ValueError('tree pointer/cycle/node budget')
            seen.add(p);node=take(p,124 if level else 76,'playerTree.node');n=struct.unpack_from('<H',node,50)[0]
            if n>11:raise ValueError('tree node exceeds11 keys')
            nodes.append(dict(pointer=p,level=level,raw_hex=node.hex(),count=n))
            for j in range(n):
                if level:walk(struct.unpack_from('<I',node,76+j*4)[0],level-1)
                items.append((struct.unpack_from('<H',node,52+j*2)[0],struct.unpack_from('<I',node,4+j*4)[0]))
            if level:walk(struct.unpack_from('<I',node,76+n*4)[0],level-1)
        if root:walk(root,depth)
        return dict(root=root,depth=depth,nodes=nodes,ordered_items=items,
            modeled_keys={str(k):v for k,v in items if k in PLAYER_MODELED_KEYS},
            unmodeled_keys={str(k):v for k,v in items if k not in PLAYER_MODELED_KEYS},
            values_are_raw_u32_not_all_semantic_types=True)
    result['player_keyed_tree']=attempt('playerTree',tree)
    result['unresolved_vector_header1952']=dict(capacity_word=u(G+1952),pointer_word=u(G+1956),count_word=u(G+1960),
        stride_unrestored=True,payload_not_read=True,raw_header12_hex=raw[1952:1964].hex())
    result['spell_ledger_views']=[attempt('ledger'+str(o),lambda o=o:dict(pointer=u(G+o),count=u(G+o+4),
        active_u32_hex=take(u(G+o),u(G+o+4)*4,'spellLedger'+str(o)).hex()))for o in(672,684,732)]
    def distance_map():
        p=u(G+2368)
        if not p:return dict(present=False)
        header=take(p,28,'distanceMap.header');cap,ptr,n=struct.unpack_from('<3I',header,8)
        if n>cap or cap>limits.vector_capacity*1024:raise ValueError('distance map shape/budget')
        return dict(present=True,pointer=p,raw_header28_hex=header.hex(),capacity=cap,count=n,field24=struct.unpack_from('<I',header,24)[0],
            raw_u16_backing_hex=take(ptr,cap*2,'distanceMap.u16').hex())
    result['distance_map']=attempt('distanceMap',distance_map)
    def transport():
        holder,vt=u(app_pointer+4768),u(app_pointer+4772)
        if vt!=1495776 or not holder:raise ValueError('Only validated1495776 transport holder may be followed')
        holder_raw=take(holder,24,'transport24');cell=struct.unpack_from('<I',holder_raw,16)[0]
        if not cell:raise ValueError('Null actual transport cell remains unresolved')
        cell_raw=take(cell,76,'transportCell76');cap,ptr,head,count=struct.unpack_from('<4I',cell_raw,12)
        if count>cap or cap>limits.vector_capacity or cap and head>=cap or not cap and(head or count):raise ValueError('Transport ring shape/budget')
        backing=take(ptr,cap*12,'transportRing.backing');payloads=[]
        for j in range(count):
            index=(head+j)%cap;p=ptr+index*12;pc,pp,pn=struct.unpack_from('<3I',backing,index*12)
            if pn>pc or pc>limits.payload_bytes:raise ValueError('Transport ring payload budget')
            data=take(pp,pc,'transportRing.payload')
            payloads.append(dict(logical_index=j,physical_index=index,metadata_pointer=p,capacity=pc,pointer=pp,count=pn,
                payload_hex=data[:pn].hex(),raw_payload_backing_hex=data.hex()))
        commands=vector(cell,Vector135('transport_commands232',28,32,36,232,'transport six-method differential'))
        return dict(holder_pointer=holder,vtable=vt,raw_holder24_hex=holder_raw.hex(),cell_pointer=cell,raw_cell76_hex=cell_raw.hex(),
            ring=dict(capacity=cap,pointer=ptr,head=head,count=count,raw_backing_hex=backing.hex(),logical_payloads=payloads),
            commands232=commands,optional_snapshot_and_rows_metadata_only=True,
            unknown_cell_bytes_not_assumed_zero=True,original_owner_lifecycle_not_validated=True)
    result['transport']=attempt('transport',transport)
    if include_world:
        world_partial={}
        def world():
            R=u(G+2348)
            if not R:raise ValueError('ActiveGame has null worldRc; no world manufactured')
            header=take(R,124,'worldRc124');w=struct.unpack('<31I',header)
            value=world_partial
            value.update(pointer=R,app_cache_pointer=u(app_pointer+5116),raw_rc124_hex=header.hex(),strong_observed=w[0],weak_observed=w[1],
                fallback_bits=w[29],flat_byte=header[120],ownership_not_proved=True)
            tiles=vector(R,Vector135('world_tiles36',8,12,16,36,'world_query135 decoder'))
            value['tiles36']=tiles;value['bounds16']=vector(R,Vector135('world_bounds16',20,24,28,16,'world_query135 decoder'))
            value['terrain_chunks']=[]
            if tiles['count']>limits.terrain_tiles:raise ValueError('terrain tile budget')
            for i,h in enumerate(tiles['active_records_hex']):
                row=bytes.fromhex(h);cap,p,n=struct.unpack_from('<3I',row)
                if n>cap or cap>limits.chunks_per_tile:raise ValueError('terrain chunk shape/budget')
                chunks=take(p,cap*264,'terrain.chunks264');entries=[]
                for j in range(n):
                    chunk=chunks[j*264:(j+1)*264];vc,vp,vn=struct.unpack_from('<3I',chunk)
                    if vn>vc or vc>4096:raise ValueError('terrain vertices shape/budget')
                    entries.append(dict(raw264_hex=chunk.hex(),vertex_capacity=vc,vertex_count=vn,
                        vertices_xyz_bits_hex=take(vp,vc*12,'terrain.vertices12').hex(),holes_u16=struct.unpack_from('<H',chunk,260)[0]))
                value['terrain_chunks'].append(dict(tile_index=i,capacity=cap,count=n,pointer=p,raw_backing264_hex=chunks.hex(),active=entries))
            if w[8]!=0xffffffff:
                value['nav']=vector(R,Vector135('nav_bytes',32,36,40,1,'world_query135 decoder'),limits.vector_bytes)
                value['nav']['origin_xy_bits_width']=list(w[11:14])
            else:value['nav']=dict(present=False,sentinel=0xffffffff)
            if w[14]!=0xffffffff:
                n=w[19];value['primary']=dict(present=True,tag56=w[14],pointer=w[18],count=n,capacity_unrestored=True,
                    origin_xy_bits_width=list(w[20:23]),raw_f32_values_hex=take(w[18],n*4,'primary.height_values').hex())
            else:value['primary']=dict(present=False,sentinel=0xffffffff)
            if w[23]!=0xffffffff:
                value['secondary']=vector(R,Vector135('secondary_height',92,96,100,4,'world_query135 decoder'),limits.vector_bytes//4)
                value['secondary']['origin_xy_bits_width']=list(w[26:29])
            else:value['secondary']=dict(present=False,sentinel=0xffffffff)
            return value
        observed_world=attempt('world',world)
        if observed_world.get('status')=='unresolved_or_capture_boundary':observed_world['partial_observations']=world_partial
        result['world']=observed_world
    result.update(source_ranges=ranges,source_bytes_copied_with_duplicates=total,capture_complete_for_declared_schema=not boundaries,
        unknown_contracts=['Raw observed bytes are not a full independent Game/App producer.',
            'OpeningNPC unwritten ranges are constructor provenance only; later systems can write some of them.',
            'Vector capacity tails, player action inactive words, padding and unknown keyed values remain observed/opaque.',
            'Pointer-length source arrays with unknown capacity capture active bytes only; arbitrary pointed owners are not recursively invented.',
            'Snapshot/table/global/externref/GPU/owner lifetimes are not restored.'])
    return result


if __name__=='__main__':
    import argparse
    from pathlib import Path
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--schema',action='store_true')
    p.add_argument('--snapshot',type=Path);p.add_argument('--app',type=int);p.add_argument('--output',type=Path);args=p.parse_args()
    if args.schema:value=capture_schema135()
    elif args.snapshot is not None and args.app is not None:
        raw=args.snapshot.read_bytes();value=capture_game_entry135(raw,args.app)
        value['input_snapshot_sha256']=hashlib.sha256(raw).hexdigest();value['input_snapshot_path']=str(args.snapshot)
    else:p.error('Provide --schema or explicit --snapshot/--app; this script never acquires or runs an original')
    text=json.dumps(value,indent=2)+'\n'
    if args.output is not None:args.output.write_text(text)
    else:print(text,end='')
