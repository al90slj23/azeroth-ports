#!/usr/bin/env python3
"""Read-only review of schema3 JSONL and schema4 gzip opening/combat evidence.

Only artifact bytes and source ASTs are read. Neither target, producer nor checker
executes. Historical sources require an explicit mode; schema4 defaults to exact
current+frozen source identity. Complete streams retain their original scope.
"""
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import argparse,ast,copy,hashlib,heapq,json,os,struct,sys,time,zlib
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'evidence/opening-combat0135-oracle-20261101T154826.676203Z'
STAGES=('player','extra','owned_effects','hits','area','effects','deadline','secondary','ai','collect','claims','spawn','special','terminal')
ENTRIES=(2088,916,975,1754,3757,915,38007,2602,921,2862,2573,947,2376,49037)
NPC_WRITTEN=((0,4),(8,4),(16,4),(40,4),(64,4),(112,136),(280,139))
LAYOUTS={'companions':(2108,88),'units':(1784,424),'areas':(1796,88),'effects120':(1808,120),
 'delayed56':(1820,56),'deadline32':(1832,32),'hits112':(1844,112),'secondary112':(1856,112),
 'pickups':(1868,56),'candidates80':(1904,80),'special':(1916,40),'windows':(1964,8),
 'boundaries':(2120,8),'owned80':(1656,80),'live32':(1704,32),'timed12':(596,12),'active84':(644,84),
 'xp_queue8':(2144,8),'currency_queue8':(2156,8)}
GUARDIAN_KEYS={'unit_index','guid','capacity','timers_bits','ability_pointer','header_pointer','ability_records44_hex','header28_hex'}
DECLARATIONS={5484048:5477460,5484076:5477592,5484104:5477724}
EMPTY_DOMAINS=('effects120','delayed56','hits112','active84','timed12','deadline32','secondary112','xp_queue8','currency_queue8')

def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    except PermissionError:return None
    return False

def leb(raw,p,signed=False):
    n=s=0
    while True:
        b=raw[p];p+=1;n|=(b&127)<<s;s+=7;assert s<=35
        if b<128:return(n-(1<<s)if signed and b&64 else n),p

def sections(raw):
    assert raw[:8]==b'\0asm\1\0\0\0';p=8;result=[]
    while p<len(raw):
        begin=p;kind=raw[p];size,start=leb(raw,p+1);p=start+size;assert p<=len(raw);result.append((kind,begin,start,p))
    return result

def static_reader(raw):
    parts=sections(raw);_,_,p,_=next(s for s in parts if s[0]==5)
    memories,p=leb(raw,p);assert memories==1;flags,p=leb(raw,p);assert flags in(0,1)
    pages,p=leb(raw,p);initial_bytes=pages*65536
    _,_,p,end=next(s for s in parts if s[0]==11);n,p=leb(raw,p);ranges=[]
    for index in range(n):
        flags,p=leb(raw,p);assert flags==0 and raw[p]==65;address,p=leb(raw,p+1,True);assert raw[p]==11
        size,p=leb(raw,p+1);assert address+size<=initial_bytes
        ranges.append((index,address,p,raw[p:p+size]));p+=size
    assert p==end
    cache={};proofs={}
    def read(address,size):
        assert 0<=address and 0<=size<=1048576 and address+size<=initial_bytes
        key=(address,size)
        if key in cache:return cache[key]
        # WASM memory starts zeroed. Active segments overlay in module order;
        # sparse zero holes between segments are part of this static image.
        # This reconstructs original static bytes, never independent None cells.
        result=bytearray(size);covered=bytearray(size);overlap=[]
        for index,start,file_start,payload in ranges:
            lo,hi=max(address,start),min(address+size,start+len(payload))
            if lo>=hi:continue
            result[lo-address:hi-address]=payload[lo-start:hi-start];covered[lo-address:hi-address]=b'\1'*(hi-lo)
            overlap.append(dict(segment=index,memory_start=lo,memory_end_exclusive=hi,original_file_start=file_start+lo-start,original_file_end_exclusive=file_start+hi-start))
        holes=[];i=0
        while i<size:
            if covered[i]:i+=1;continue
            end=i+1
            while end<size and not covered[end]:end+=1
            holes.append([address+i,address+end]);i=end
        value=bytes(result);cache[key]=value
        proofs[f'{address}:{size}']=dict(memory_address=address,bytes=size,initial_memory_bytes=initial_bytes,active_segment_overlaps_in_module_order=overlap,implicit_initial_zero_intervals=holes,reconstructed_hex=value.hex(),reconstructed_sha256=hashlib.sha256(value).hexdigest())
        return value
    read.proofs=proofs
    return read

class JsonlReader:
    """Bounded decompression; rejects concatenated/truncated gzip members."""
    def __init__(self,path,compressed,raw_cap):
        self.path=path;self.compressed=compressed;self.raw_cap=raw_cap;self.bytes=0;self.maximum=0;self.records=0
        self.digest=hashlib.sha256();self.file_digest=hashlib.sha256();self.file_bytes=0;self.complete=False
    def __iter__(self):
        inflater=zlib.decompressobj(31)if self.compressed else None;pending=b''
        with self.path.open('rb')as stream:
            while chunk:=stream.read(65536):
                self.file_bytes+=len(chunk);self.file_digest.update(chunk)
                assert self.file_bytes<=268435456
                while chunk:
                    raw=inflater.decompress(chunk,2097153)if inflater else chunk
                    chunk=inflater.unconsumed_tail if inflater else b''
                    self.bytes+=len(raw);assert self.bytes<=self.raw_cap;self.digest.update(raw);pending+=raw
                    while(break_at:=pending.find(b'\n'))>=0:
                        line,pending=pending[:break_at+1],pending[break_at+1:];assert len(line)<=2097152
                        self.maximum=max(self.maximum,len(line));self.records+=1;yield json.loads(line)
                    assert len(pending)<=2097152
                    if inflater and inflater.eof:
                        assert not inflater.unused_data and not chunk and not stream.read(1),'Extra gzip member/trailing bytes'
                        self.complete=True;break
                if self.complete:break
        assert not pending and(not inflater or inflater.eof),'Truncated gzip/JSONL';self.complete=True
    def receipt(self):
        assert self.complete
        return dict(file_bytes=self.file_bytes,file_sha256=self.file_digest.hexdigest(),uncompressed_bytes=self.bytes,
            uncompressed_sha256=self.digest.hexdigest(),maximum_record_bytes=self.maximum,records=self.records,gzip=self.compressed,single_member=self.compressed)

def frozen_closure(source):
    todo=['core_spec.headless135','core_spec.opening_handoff135'];seen={};base=source/'reconstruction'
    while todo:
        module=todo.pop()
        if module in seen:continue
        parts=module.split('.');path=base.joinpath(*parts).with_suffix('.py');package=module.rsplit('.',1)[0]
        if not path.exists():path=base.joinpath(*parts)/'__init__.py';package=module
        assert path.is_file();seen[module]=str(path.relative_to(source))
        if len(parts)>1:todo.append(parts[0])
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.Import):todo.extend(x.name for x in node.names if x.name.split('.')[0]in('core_spec','resource_spec'))
            elif isinstance(node,ast.ImportFrom):
                assert node.level in(0,1)
                prefix=(package+('.'+node.module if node.module else''))if node.level else(node.module or'')
                if prefix.split('.')[0]not in('core_spec','resource_spec'):continue
                todo.append(prefix)
                for name in node.names:
                    child=prefix+'.'+name.name
                    if base.joinpath(*child.split('.')).with_suffix('.py').exists():todo.append(child)
    return sorted(set(seen.values()))

def check_value(want,actual,path,counts):
    if want is None and len(path)>=3 and path[-3]=='pickup_words'and path[-1]==1:
        assert type(actual)is int and 0<=actual<=0xffffffff;counts['unwritten_pickup_arrival_words']+=1;return
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
        if int.from_bytes(bytes(row[64:68]),'little')==3:assert not 72<=offset<109,'Guardian writes known fields72..108'
        if 4<=offset<8:assert row[:4]==[0,0,0,0]
    elif name=='pickups':assert 4<=offset<8 and row[:4]==[0,0,0,0]
    elif name=='special':assert 8<=offset<16 or 36<=offset<40
    elif name=='live32':
        kind=int.from_bytes(bytes(row[8:12]),'little');spell=int.from_bytes(bytes(row[20:24]),'little')
        assert 16<=offset<20 and kind in(7,8,9,12)or 12<=offset<16 and spell==1020
    else:raise AssertionError(('Unknown active byte outside recovered write masks',name,offset))

def guardian_binding(raw,read_static):
    rows=[bytes.fromhex(x)for x in raw['vectors']['units']['storage'][:raw['vectors']['units']['count']]]
    owners=raw.get('unit_cooldowns');projection=raw['projection'].get('guardian_cooldowns')
    if owners is None:assert projection is None;return[]
    assert len(owners)==len(rows);guardians=[];ranges=[];guids=set();special=raw['vectors']['special']
    for index,(unit,owner)in enumerate(zip(rows,owners)):
        u=lambda o:struct.unpack_from('<I',unit,o)[0]
        guid=str(struct.unpack_from('<Q',unit,112)[0]);assert guid not in guids;guids.add(guid)
        assert owner['unit_index']==index and owner['guid']==guid and owner['tag64']==u(64)
        assert bytes.fromhex(owner['raw_unit_header64_100_hex'])==unit[64:100]
        if u(64)==0xffffffff:assert owner['variant']=='none'and owner['pointer_dereferenced']is False;continue
        assert owner['variant']=='timers'and owner['pointer_dereferenced']is True
        assert owner['capacity']==u(64)==owner['count']==u(72)==3
        ptr=u(68);assert owner['pointer']==ptr and ptr>0 and ptr%4==0 and ptr+12<=raw['memory_bytes']
        assert all(ptr+12<=a or ptr>=b for a,b in ranges),'Aliased guardian cooldown ownership';ranges.append((ptr,ptr+12))
        units=raw['vectors']['units'];assert ptr+12<=units['pointer']or ptr>=units['pointer']+units['capacity']*424
        assert bytes.fromhex(owner['raw_timer_vec12_hex'])==unit[64:76]
        backing=bytes.fromhex(owner['backing_hex']);assert len(backing)==12 and hashlib.sha256(backing).hexdigest()==owner['backing_sha256']
        assert owner['timers_bits']==list(struct.unpack('<3I',backing))
        assert owner['ability_pointer']==u(76)==owner['ability_slice_pointer']==u(84)
        assert owner['ability_count']==u(80)==owner['ability_slice_count']==u(88)==3
        assert owner['header_pointer']==u(96)and DECLARATIONS[u(96)]==u(76)
        abilities=owner['ability_records44_hex'];assert len(abilities)==3 and all(len(bytes.fromhex(x))==44 for x in abilities)
        assert owner['ability_slice_records44_hex']==abilities
        assert bytes.fromhex(''.join(abilities))==read_static(u(76),132)
        for k,row in enumerate(abilities):assert bytes.fromhex(row)==read_static(u(76)+k*44,44)
        assert bytes.fromhex(owner['header28_hex'])==read_static(u(96),28)
        if u(0)==0:
            slot=u(92);assert slot<special['count'];state=bytes.fromhex(special['storage'][slot])
            assert struct.unpack_from('<Q',state)[0]==1 and str(struct.unpack_from('<Q',state,8)[0])==guid
        guardians.append({k:owner[k]for k in GUARDIAN_KEYS})
    assert projection==guardians,'Guardian projection must bind each concrete owner, no omission/reorder'
    assert all(set(g)==GUARDIAN_KEYS for g in projection)
    return guardians

def candidate_binding(raw,read_static):
    p=raw['projection']['candidates'];v=raw['vectors']['candidates80'];assert len(p)==v['count']<=4
    owned=raw['vectors']['owned80']
    for value,encoded in zip(p,v['storage']):
        row=bytes.fromhex(encoded);u=lambda o:struct.unpack_from('<I',row,o)[0];tag=u(60)
        assert value['tier']==u(76)
        if tag==0x80000000:assert value['variant']=='new'and value['ability_id']==read_static(u(64),u(68)).decode('ascii')
        elif tag<0x80000000 or tag==0x80000001:
            assert value['variant']=='upgrade'and value['owned_index']==u(72)<owned['count']
            definition=struct.unpack_from('<I',bytes.fromhex(owned['storage'][u(72)]))[0]
            pointer,length=struct.unpack('<2I',read_static(definition+12,8));assert value['ability_id']==read_static(pointer,length).decode('ascii')
            assert len(value['kinds'])==u(68)<=5 and all(type(k)is int and 0<=k<=255 for k in value['kinds'])
        else:assert tag==0x80000004 and value['variant']=='gold'and value['gold']==u(64)

def check_queue(raw,game,base,stride,name):
    queue=raw[name];cap,ptr,n=struct.unpack_from('<3I',game,base)
    assert(queue['capacity'],queue['pointer'],queue['count'])==(cap,ptr,n)and n<=cap<=4096
    metadata=bytes.fromhex(queue['metadata_backing_hex']);assert len(metadata)==cap*stride and len(queue['active'])==n
    for i,item in enumerate(queue['active']):
        row=metadata[i*stride:(i+1)*stride];assert bytes.fromhex(item['metadata_hex'])==row
        capacity,pointer,length=struct.unpack_from('<3I',row);assert(item['capacity'],item['pointer'],item['length'])==(capacity,pointer,length)
        backing=bytes.fromhex(item['backing_hex']);payload=bytes.fromhex(item['payload_hex'])
        assert length<=capacity<=1048576 and len(backing)==capacity and len(payload)==length and backing[:length]==payload
        assert pointer+capacity<=raw['memory_bytes']
        if name=='packets':assert item['opcode']==struct.unpack_from('<H',row,12)[0]

def check_snapshot(raw,want,counts,maximum,read_static):
    game=bytes.fromhex(raw['raw_game2592_hex']);assert len(game)==2592 and raw['stack']==1048576
    u=lambda o:struct.unpack_from('<I',game,o)[0];p=raw['projection']
    words={'now_bits':2352,'spawn_counter':2408,'message_sequence':2412,'kill_cost_bits':2420,'generation_counter2400':2400,
        'current_hp_bits':1440,'timer1628_bits':1628,'budget_bits':2416,'gold':1456,'earned':1100,'last_hit_bits':1652,
        'absorbed740_bits':740,'maximum_shield744_bits':744,'distance_map_updated_at_bits':2372,'field1092':1092}
    for key,offset in words.items():
        if key in p:assert p[key]==u(offset),(key,p[key],u(offset))
    assert p['phase2587']==game[2587]and p['selection_kind2585']==game[2585]
    if'mode2582'in p:assert p['mode2582']==game[2582]
    assert p['rng_words']==list(struct.unpack_from('<4I',game,1720))and p['source_id']==str(struct.unpack_from('<Q',game,1336)[0])
    for key,start,n in(('player_xyz',1416,3),('velocity_xy',1736,2),('previous_player_xyz',2428,3)):
        assert p[key]==list(struct.unpack_from('<'+'I'*n,game,start))
    assert p['progression']==dict(level=u(1432),xp=u(1436),pending_upgrades=u(2376))
    assert p['derived_bits']=={str(1536+i*4):u(1536+i*4)for i in range(23)}
    assert p['racial_record_hex']==game[1256:1336].hex()
    for key,offset in(('outgoing_total_hex',984),('incoming_total_hex',992)):assert p[key]==game[offset:offset+8][::-1].hex()
    assert p['special']==dict(selected392=u(392),target396=u(396),navigation2564=game[2564],announced2565=game[2565],announcement_time2392_bits=u(2392))
    assert p['effect']==dict(clock2364_bits=u(2364),effect_counter2356=u(2356),action_sequence1644=u(1644),player_action_tag416=u(416))
    assert p['tail_flags']==dict(field400=u(400),protection2576=game[2576],flag2568=game[2568],gate2579=game[2579])
    assert raw['ownership']['game_world_pointer']==u(2348)==raw['ownership']['app_cache_pointer']==26204808
    app=bytes.fromhex(raw['ownership']['raw_app5168_hex']);assert len(app)==5168 and app[5165]==0
    assert len(bytes.fromhex(raw['ownership']['raw_world_rc124_hex']))==124
    for name,(offset,stride)in LAYOUTS.items():
        vector=raw['vectors'][name];cap,ptr,count=struct.unpack_from('<3I',game,offset)
        assert(vector['capacity'],vector['pointer'],vector['count'],vector['stride'])==(cap,ptr,count,stride)and count<=cap<=4096
        rows=[bytes.fromhex(v)for v in vector['storage']];assert len(rows)==cap and all(len(v)==stride for v in rows)
        assert ptr+cap*stride<=raw['memory_bytes']and hashlib.sha256(b''.join(rows)).hexdigest()==vector['storage_sha256'];maximum[name]=max(maximum[name],count)
    for field,name,all_storage in(('owned_records_hex','owned80',False),('records','units',False),('area_records','areas',False),('unit_storage','units',True),('area_storage','areas',True),('pickup_storage','pickups',True)):
        v=raw['vectors'][name];assert p[field]==(v['storage']if all_storage else v['storage'][:v['count']])
    assert p['pickup_words']==[list(struct.unpack('<14I',bytes.fromhex(row)))for row in raw['vectors']['pickups']['storage'][:raw['vectors']['pickups']['count']]]
    assert p['player_fields']==raw['player_keyed_tree']['fields']
    candidate_binding(raw,read_static);guardians=guardian_binding(raw,read_static)
    for base,stride,name in((1880,16,'packets'),(1892,12,'notifications')):check_queue(raw,game,base,stride,name)
    path=p['distance_map']
    if path is not None:
        header=bytes.fromhex(path['raw_header28_hex']);assert len(header)==28
        assert list(struct.unpack('<7I',header))==[path[k]for k in('strong_count','weak_count','capacity','values_pointer','count','start_index','field24')]
        assert path['rc_pointer']==u(2368)and path['updated2372_bits']==u(2372)and path['values_sha256']==path['values_u16le_sha256']
    if want is None:return guardians
    if guardians:
        assert len(want['projection']['guardian_cooldowns'])==len(guardians),'Pointer masks require all owner payloads'
        for guardian in guardians:
            row=want['vectors']['units']['storage'][guardian['unit_index']]
            assert row[68:72]==[None]*4 and str(int.from_bytes(bytes(row[112:120]),'little'))==guardian['guid']
    check_value(want['projection'],p,('projection',),counts)
    for name,expected in want['vectors'].items():
        actual=raw['vectors'][name]
        for field in('capacity','count'):
            if field in expected:assert expected[field]==actual[field];counts['vector_shape_fields']+=1
        for field in('storage','records'):
            if field not in expected:continue
            rows=expected[field];observed=actual['storage']if field=='storage'else actual['storage'][:actual['count']];assert len(rows)==len(observed)
            for i,(row,encoded)in enumerate(zip(rows,observed)):
                payload=bytes.fromhex(encoded);assert len(row)==len(payload)
                for offset,(known,value)in enumerate(zip(row,payload)):
                    if known is None:
                        if i<actual['count']:allowed_unknown(name,row,offset)
                        counts['unknown_cells']+=1;counts['unknown_cells_nonzero_original']+=bool(value)
                        if name=='units'and i<actual['count']and 68<=offset<72 and int.from_bytes(payload[64:68],'little')==3:counts['guardian_physical_pointer_unknown_bytes']+=1
                    else:assert type(known)is int and known==value,(name,i,offset,known,value);counts['strict_record_bytes']+=1
    return guardians

def independent_distance_sha(opening,report):
    receipt=Path(report['world_input']['receipt']);assert sha(receipt)==report['world_input']['receipt_sha256'];world=json.loads(receipt.read_text());base=receipt.parent
    for name,digest in report['world_input']['artifacts'].items():assert sha(Path(name))==digest
    nav=(base/world['world_artifacts']['navigation']['file']).read_bytes();meta=world['world_artifacts']['navigation'];width=meta['width']
    f=lambda w:struct.unpack('<f',struct.pack('<I',w))[0];rounded=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
    xy=opening['projection']['player_xyz'];origin=meta['origin_xy_bits'];x,y=(int(rounded(f(a)-f(b)))for a,b in zip(xy[:2],origin));assert 0<=x<width and 0<=y<width
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

def owner_negative_checks(raw,want,read_static):
    results=[];index=next(i for i,x in enumerate(raw['unit_cooldowns'])if x['variant']=='timers')
    def reject(label,change,check):
        candidate=copy.deepcopy(raw);change(candidate)
        try:check(candidate)
        except(AssertionError,KeyError):results.append(label);return
        raise AssertionError(('Owner corruption accepted',label))
    reject('cross_unit_guid_rejected',lambda x:x['unit_cooldowns'][index].update(guid=x['unit_cooldowns'][0]['guid']),lambda x:guardian_binding(x,read_static))
    reject('projection_owner_omission_rejected',lambda x:x['projection'].update(guardian_cooldowns=[]),lambda x:guardian_binding(x,read_static))
    reject('timer_payload_backing_mismatch_rejected',lambda x:x['unit_cooldowns'][index]['timers_bits'].__setitem__(0,0),lambda x:guardian_binding(x,read_static))
    altered=copy.deepcopy(want);altered['projection']['guardian_cooldowns'][0]['timers_bits'][0]^=1
    try:check_value(altered['projection'],raw['projection'],('projection',),Counter())
    except AssertionError:results.append('expected_timer_bit_mismatch_rejected')
    else:raise AssertionError('Timer semantic difference accepted')
    row=want['vectors']['units']['storage'][index]
    try:allowed_unknown('units',row,72)
    except AssertionError:results.append('guardian_nonpointer_written_byte_mask_rejected')
    else:raise AssertionError('Unrecovered guardian mask accepted')
    return results

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',nargs='?',type=Path,default=DEFAULT)
    parser.add_argument('--historical-frozen-sources',action='store_true',help='Only schema3: verify historical frozen sources while explicitly reporting current drift')
    args=parser.parse_args();directory=args.directory.resolve();began=time.monotonic()
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('opening-combat0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    report=json.loads((directory/'comparison.json').read_text());fixtures=json.loads((directory/'fixtures.json').read_text());inputs=json.loads((directory/'inputs.json').read_text());runtime=report['runtime'];schema=runtime['schema_version']
    assert schema in(3,4)and(not args.historical_frozen_sources or schema==3)
    assert report['differences']==0 and report['status']=='matched_requested_budget'and report['source_sha256_before']==report['source_sha256_after']
    source=directory/'source-snapshot';drift=[]
    for name,digest in report['source_sha256_before'].items():
        assert sha(source/name)==digest,name
        if sha(ROOT/name)!=digest:drift.append(name)
    assert not drift or args.historical_frozen_sources,('Current source drift',drift)
    assert len(report['source_sha256_before'])==report['source_files']
    for name,key in(('inputs.json','inputs_sha256'),('fixtures.json','fixtures_sha256'if schema==4 else'expectations_sha256'),('results.jsonl.gz'if schema==4 else'results.jsonl','original_results_sha256')):assert sha(directory/name)==report[key]
    assert inputs==[{k:fixtures[k]for k in('id','input','actions')}]and len(inputs)==1
    assert len(fixtures['actions'])<=600
    production=sorted(p for p in report['source_sha256_before']if p.startswith('reconstruction/'));assert production==frozen_closure(source)
    io=[]
    for name in production:
        for node in ast.walk(ast.parse((source/name).read_text())):
            if isinstance(node,ast.Call):
                f=node.func;fn=f.id if isinstance(f,ast.Name)else f.attr if isinstance(f,ast.Attribute)else''
                if fn in('open','read_bytes','read_text','write_bytes','write_text','Popen','system','eval','exec','__import__'):io.append((name,fn))
    assert not io,io
    original=(ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm').read_bytes();manifest=json.loads((directory/'manifest.json').read_text());module=(directory/manifest['module_file']).read_bytes()
    assert hashlib.sha256(original).hexdigest()==report['original_sha256']and hashlib.sha256(module).hexdigest()==manifest['module_sha256']
    a,b=sections(original),sections(module);assert[k for k,_,_,_ in a]==[k for k,_,_,_ in b]and 8 not in[k for k,_,_,_ in a]
    assert all(original[x:y]==module[u:v]for(k,x,_,y),(_,u,_,v)in zip(a,b)if k!=7)
    read_static=static_reader(original);del original,module
    if schema==4:read_static(5426156,40)
    expected_reader=None
    if schema==4:
        expected_path=directory/'stage-expectations.jsonl.gz';assert sha(expected_path)==report['expectations_sha256'];expected_reader=JsonlReader(expected_path,True,1073741824);expected=iter(expected_reader)
        first=next(expected);assert first['record_kind']=='opening';opening=first['expected']
    else:opening=fixtures['opening'];expected=iter(fixtures['stages'])
    order=[('case_start',None,None,0),('constructor',None,None,0),('opening',None,None,0)];frame=0;selections=0
    for index,action in enumerate(fixtures['actions']):
        if action['kind']=='select':order.append(('stage',index,'select',frame));selections+=1
        else:
            assert action['kind']=='controlled_tail_frame';order.append(('clock_control',index,None,frame));order.extend(('stage',index,kind,frame)for kind in STAGES);frame+=1
    order.append(('case_end',None,None,frame));assert frame==report['independent_frames']<=500 and selections==report['independent_selections']
    distance=independent_distance_sha(opening,report);counts=Counter();maximum=defaultdict(int);stage_index=0;clock=0;previous=None;last=None;records=Counter();packet_max=0;locale=None;selected=[];owners={};first_guardian=None;guardian_captures=0;guardian_payloads=0;negative=[]
    reader=JsonlReader(directory/('results.jsonl.gz'if schema==4 else'results.jsonl'),schema==4,1073741824 if schema==4 else 268435456)
    previous_packets=[];previous_notifications=[]
    for line_index,raw in enumerate(reader):
        assert time.monotonic()-began<120 and line_index<len(order)
        records[raw['record_kind']]+=1;kind,action_index,stage_kind,frame_index=order[line_index];assert raw['record_kind']==kind and raw['id']==0
        if action_index is not None:assert raw['action_index']==action_index and raw['frame']==frame_index
        if stage_kind is not None:assert raw['kind']==stage_kind
        if kind=='case_start':locale=raw['locale_prestate'];assert locale['effective_index']==0 and locale['once_flag']==3
        if kind=='clock_control':
            action=fixtures['actions'][action_index];assert raw['old_bits']==clock and raw['dt_bits']==action['dt_bits'];f=lambda w:struct.unpack('<f',struct.pack('<I',w))[0]
            clock=struct.unpack('<I',struct.pack('<f',f(clock)+f(action['dt_bits'])))[0]
            assert raw['new_bits']==clock and raw['original880_called']is False and raw['only_external_game_write_offset']==2352
        if kind in('constructor','opening','stage'):
            want=opening if kind=='opening'else None
            if kind=='stage':
                item=next(expected)
                if schema==4:assert item['record_kind']=='stage'and item['stage_index']==stage_index
                assert item['action_index']==action_index and item['kind']==stage_kind;want=item['expected'];counts['stage_identity_leaves']+=2
            guardians=check_snapshot(raw,want,counts,maximum,read_static);packet_max=max(packet_max,raw['packets']['count'])
            for queue,field,old in(('packets','new_packets',previous_packets),('notifications','new_notifications',previous_notifications)):
                current=[{'opcode':x['opcode'],'payload_hex':x['payload_hex']}for x in raw[queue]['active']]if queue=='packets'else[x['payload_hex']for x in raw[queue]['active']]
                prefix=len(old)<=len(current)and current[:len(old)]==old;delta=raw[field]
                assert delta['prefix_preserved']==prefix and delta['previous_count']==len(old)and delta['current_count']==len(current)
                assert delta['appended']==(current[len(old):]if prefix else[])
                if not prefix:assert delta['full_current']==current
                if queue=='packets':previous_packets=current
                else:previous_notifications=current
            if guardians:
                guardian_captures+=1;guardian_payloads+=len(guardians)
                if first_guardian is None:first_guardian=dict(frame=raw['frame'],action_index=action_index,kind=stage_kind,stage_index=stage_index,count=len(guardians),clock_bits=clock);negative=owner_negative_checks(raw,want,read_static)
                for owner in guardians:
                    identity=(owner['ability_pointer'],owner['header_pointer']);assert owners.get(owner['guid'],identity)==identity;owners[owner['guid']]=identity
            if kind=='stage':
                assert raw['stage_index']==stage_index and raw['projection']['now_bits']==clock
                role_index=1072 if stage_kind=='select'else ENTRIES[STAGES.index(stage_kind)];assert raw['entry_index']==role_index
                if stage_kind=='select':
                    index=fixtures['actions'][action_index]['index'];assert previous['projection']['phase2587']==2 and raw['input_index']==index
                    cards=previous['projection']['candidates'];assert 0<=index<len(cards)
                    selected.append(dict(action_index=action_index,frame=frame_index,clock_bits=clock,candidates=cards,selected_index=index,selected_id=cards[index]['ability_id'],phase_after=raw['projection']['phase2587']))
                    if len(selected)==1:assert[c['ability_id']for c in cards]==['thunder_clap','battle_shout','bloodthirst']and index==0
                path=raw['projection']['distance_map']
                if path is not None:
                    for k,v in distance.items():assert path[k]==v
                stage_index+=1
            previous=raw;last=raw
        if kind=='case_end':
            assert raw['boundary']is None and raw['host_calls']==[] and raw['stage_count']==report['compared_stages']and raw['locale_writes']==0 and raw['locale_after']==locale
            for call in raw['calls']:assert call['stack_after']==1048576
            calls=[c for c in raw['calls']if c['role']!='original_allocator'];assert len(calls)==report['compared_stages']+2==runtime['original_entry_calls']and all(c['returned']for c in calls)
    assert reader.records==len(order)and stage_index==report['compared_stages']and len(selected)==selections and next(expected,None)is None
    assert all(maximum[k]==0 for k in EMPTY_DOMAINS),dict(maximum)
    if schema==4:
        assert runtime['output_protocol']=='bounded_stage_jsonl_gzip'and runtime['js_heap_cap_mib']==512
        assert runtime['budgets']==dict(cases=1,actions_per_case=600,controlled_frames_per_case=500,record_uncompressed_bytes=2097152,uncompressed_output_bytes=1073741824,compressed_output_bytes=268435456)
        assert runtime['uncompressed_output_bytes']==reader.bytes==runtime['output_bytes']==report['original_uncompressed_bytes']
        assert runtime['compressed_output_bytes']==reader.file_bytes and runtime['output_sha256']==reader.file_digest.hexdigest()and runtime['uncompressed_sha256']==reader.digest.hexdigest()
        assert runtime['max_record_uncompressed_bytes']==reader.maximum==report['maximum_original_record_bytes']and runtime['output_records']==reader.records
        assert expected_reader.bytes==fixtures['expected_uncompressed_bytes']==report['expected_uncompressed_bytes']
    else:assert runtime['output_bytes']==reader.bytes<268435456
    assert runtime['memory_page_cap']==4096 and runtime['peak_memory_bytes']<=268435456 and runtime['denied_imports']==878 and runtime['host_imports_throw']is True
    reconciled=sum(counts[k]for k in('strict_record_bytes','projection_leaves','vector_shape_fields','stage_identity_leaves'))
    assert reconciled==report['comparison']['compared_leaves']and counts['unknown_cells']==report['comparison']['declared_unknown_cells']and counts['unwritten_pickup_arrival_words']==report['comparison']['unwritten_pickup_arrivals']
    assert report['process']['exit_code']==0 and report['process']['seconds']<60 and(directory/'stderr.log').stat().st_size==0
    terminal=dict(pid_missing=missing(report['process']['pid']),pgid_missing=missing(report['process']['pgid'],True));assert all(terminal.values())
    assert json.loads((directory/'differences.json').read_text())==[]
    assert all(sha(source/name)==digest for name,digest in report['source_sha256_before'].items())
    if not args.historical_frozen_sources:assert all(sha(ROOT/name)==digest for name,digest in report['source_sha256_before'].items())
    result=dict(status='passed_scoped_historical_sources_review'if args.historical_frozen_sources else'passed_scoped_read_only_review',comparison=str(directory/'comparison.json'),comparison_sha256=sha(directory/'comparison.json'),reviewer_script_sha256=sha(Path(__file__)),schema_version=schema,
        source_files=len(report['source_sha256_before']),production_files=len(production),frozen_AST_import_closure_exact=True,all_frozen_sources_verified=True,all_current_and_frozen_sources_verified=not drift,current_source_drift=drift,historical_frozen_source_mode=args.historical_frozen_sources,
        production_direct_IO_calls=io,nonexport_sections_unchanged=True,strict_stream_order=True,stream_record_counts=dict(records),original_stream=reader.receipt(),expected_stream=expected_reader.receipt()if expected_reader else None,
        declared_projection_recompared=True,comparison_counts=dict(counts),declared_comparison_leaf_total_reconciled=reconciled,active_unknown_masks_restricted_to_recovered_write_sets=True,
        omitted_payload_max_counts={k:maximum[k]for k in EMPTY_DOMAINS},observed_vector_max_counts=dict(maximum),independent_dijkstra_distance_map=distance,selections=selected,first_selection=selected[0]if selected else None,
        first_guardian=first_guardian,distinct_guardian_GUIDs=sorted(owners),guardian_owner_captures=guardian_captures,guardian_payload_comparisons=guardian_payloads,guardian_owner_corruption_checks=negative,
        guardian_static_declaration_source='Original WASM initial zero memory plus all active data segments overlaid in module order; no snapshot or model literal fallback.',
        final_progression=last['projection']['progression'],final_gold=last['projection']['gold'],observed_packet_count_max=packet_max,packet_payloads_claimed_compared=False,all_packet_payloads_preserved_as_observations=True,
        terminal=terminal,original_program_executed_by_reviewer=False,model_producer_executed_by_reviewer=False,new_original_cases=0,new_full880_frames=0,elapsed_seconds=time.monotonic()-began,
        limitations=[f'One seed/class/race/navigationFalse/stationary{frame} controlled frames; no broader input or full-game acceptance.','Preparsed independent world/original snapshot/external clock remain declared inputs.','Raw nonempty packet payloads remain observations; their unmodeled semantics are not claimed compared.','Guardian timers/static records strictly match expected owners; only their four physical pointer bytes remain unknown.','No original, model producer or checker was rerun.'])
    static_proof=out/'static-memory-proofs.json'
    static_proof.write_text(json.dumps(dict(kind='WASM_initial_zero_memory_plus_ordered_active_data_segments',original_sha256=report['original_sha256'],independent_None_bytes_zero_filled=False,reads=read_static.proofs),indent=2)+'\n')
    result.update(static_memory_proofs=str(static_proof),static_memory_proofs_sha256=sha(static_proof))
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],seconds=result['elapsed_seconds'],reconciled_leaves=reconciled)))
if __name__=='__main__':main()
