"""Fixed135 full17119 movement stop with explicit real world-query inputs.

NPC424 -> auxiliary112 -> claim88 order shares wrapping movement sequence2412.
Only active branches consume motion/GUID/height. Unknown padding and inactive
payload remain None. WorldQueries135 is parsed input, not a world producer.
Paired None packet metadata requests a semantic projection: no physical queue
header, allocation, successful original return, or complete entry is inferred.
"""
from dataclasses import dataclass,replace
import struct
from . import binary32 as f
from .record_cells135 import cells135,u32,u64,put_u32,encode_row
from resource_spec.world_query135 import WorldQueries135

class UnknownWorldMotionStop135(NotImplementedError):pass

def _uint(value,bits=32):
    if type(value)is not int or not 0<=value<1<<bits:raise ValueError('Explicit unsigned word required')
    return value
def _finite(word):
    _uint(word)
    if f.is_nan(word)or f.is_inf(word):raise UnknownWorldMotionStop135('Processed motion needs finite consumed coordinates/time')
    return word
def _packed(guid):
    words=guid.to_bytes(8,'little');return bytes([sum(1<<j for j,value in enumerate(words)if value)])+bytes(value for value in words if value)

@dataclass(frozen=True)
class WorldMotionStopInput135:
    now_bits:int
    movement_sequence2412:int
    units_storage:tuple
    units_count:int
    auxiliary_storage:tuple
    auxiliary_count:int
    claims_storage:tuple
    claims_count:int
    packet_capacity:int|None
    packet_count:int|None

    def __post_init__(self):
        for value in(self.now_bits,self.movement_sequence2412):_uint(value)
        if (self.packet_capacity is None)!=(self.packet_count is None):raise ValueError('Packet capacity/count must both be explicit or both be None')
        if self.packet_capacity is not None:
            _uint(self.packet_capacity);_uint(self.packet_count)
            if self.packet_count>self.packet_capacity:raise ValueError('Packet count must not exceed explicit capacity')
        for name,stride in(('units',424),('auxiliary',112),('claims',88)):
            rows=getattr(self,name+'_storage');count=getattr(self,name+'_count')
            if type(rows)is not tuple or len(rows)>512 or type(count)is not int or not 0<=count<=len(rows):raise ValueError('Explicit physical source backing and active count required')
            for row in rows:cells135(row,stride)

@dataclass(frozen=True)
class MotionStopHeight135:
    domain:str
    record_index:int
    xy_bits:tuple
    interpolated_z_bits:int
    result_z_bits:int
    source:str

@dataclass(frozen=True)
class WorldMotionStopResult135:
    state:WorldMotionStopInput135
    packets:tuple
    stopped_guids:tuple
    heights:tuple
    packet_header_known:bool
    complete:bool
    pending:tuple

def stop_world_motion135(state,world):
    """Unchanged17119 plus17217/16340 consumer in the declared domain.

   29631(worldRc+8,XY) wins when found. Otherwise23181(primary) may replace
    only Z; both misses preserve interpolatedZ. The fallback-world height field
    is never substituted here. Unknown world is permitted only if no selected
    active record consumes a query. No packet232/action1644/phase write occurs.
    Paired None packet headers preserve None and return complete=False. Records,
    sequence and newly encoded221 packets then describe the semantic projection
    conditional on successful original execution, without predicting physical
    queue metadata or allocation/copy/panic behavior. Explicit headers retain
    the existing declared projection; their old 4096 limit was a fixture budget,
    not a game rule. Allocation pointers are outside both returned projections.
    """
    if not isinstance(state,WorldMotionStopInput135):raise TypeError('Explicit movement-stop state required')
    storage={name:[cells135(row,stride)for row in getattr(state,name+'_storage')]for name,stride in(('units',424),('auxiliary',112),('claims',88))}
    now=f.to_float(state.now_bits);sequence=state.movement_sequence2412;packets=[];stopped=[];heights=[];capacity=state.packet_capacity;count=state.packet_count;header_known=capacity is not None
    def word(row,offset):return u32(row,offset,consumer='world_motion_stop135')
    def position(row,origin,end,start,duration,claim,domain,index):
        duration_bits=_finite(word(row,duration));start_bits=_finite(word(row,start));_finite(state.now_bits)
        destination=tuple(_finite(word(row,end+j*4))for j in range(3))
        if claim and f.to_float(duration_bits)<=0:xyz=destination
        else:
            source=tuple(_finite(word(row,origin+j*4))for j in range(3));ratio=f.div(f.sub(state.now_bits,start_bits),duration_bits)
            if f.to_float(ratio)<0:ratio=0
            if f.to_float(ratio)>1:ratio=0x3f800000
            xyz=tuple(f.add(a,f.mul(f.sub(b,a),ratio))for a,b in zip(source,destination))
        if not isinstance(world,WorldQueries135):raise UnknownWorldMotionStop135('Selected motion requires explicit resolved WorldQueries135 input')
        height=world.height(xyz[0],xyz[1]);z=xyz[2];kind='interpolated'
        if height.found:z=height.value_bits;kind='world29631'
        elif world.primary is not None:
            nearest=world.nearest_primary(xyz[0],xyz[1])
            if nearest.found:z=nearest.xyz_bits[2];kind='nearest23181_Z_only'
        heights.append(MotionStopHeight135(domain,index,xyz[:2],xyz[2],z,kind));return(*xyz[:2],z)
    def stop(row,origin,end,start,duration,guid_offset,domain,index,timer=None,claim=False):
        nonlocal sequence,capacity,count
        xyz=position(row,origin,end,start,duration,claim,domain,index)
        for offset in(origin,end):
            for j,value in enumerate(xyz):put_u32(row,offset+j*4,value)
        put_u32(row,start,state.now_bits);put_u32(row,duration,0)
        if timer is not None:put_u32(row,timer,state.now_bits)
        guid=u64(row,guid_offset,consumer='world_motion_stop135.GUID');sequence=(sequence+1)&f.MASK
        if header_known:
            if count==capacity:
                grown=max(4,capacity*2)
                if grown>f.MASK:raise UnknownWorldMotionStop135('Packet capacity growth exceeds the declared unsigned metadata projection')
                capacity=grown
            if count==f.MASK:raise UnknownWorldMotionStop135('Packet count growth exceeds the declared unsigned metadata projection')
            count+=1
        packets.append((221,32,(_packed(guid)+struct.pack('<3II',*xyz,sequence)+b'\1').hex()));stopped.append(guid)
    for index,row in enumerate(storage['units'][:state.units_count]):
        if word(row,0)==0 and f.to_float(word(row,344))>0 and now<f.to_float(f.add(word(row,344),word(row,340))):stop(row,316,328,340,344,112,'units',index)
    for index,row in enumerate(storage['auxiliary'][:state.auxiliary_count]):
        if f.to_float(word(row,60))>0 and now<f.to_float(f.add(word(row,60),word(row,56))):stop(row,32,44,56,60,16,'auxiliary',index,68)
    for index,row in enumerate(storage['claims'][:state.claims_count]):
        if not now>=f.to_float(f.add(word(row,68),word(row,72))):stop(row,44,56,68,72,24,'claims',index,76,True)
    result=replace(state,movement_sequence2412=sequence,units_storage=tuple(encode_row(row)for row in storage['units']),auxiliary_storage=tuple(encode_row(row)for row in storage['auxiliary']),claims_storage=tuple(encode_row(row)for row in storage['claims']),packet_capacity=capacity,packet_count=count)
    pending=()if header_known else('packet_capacity_and_count','packet_vector_allocation_copy_and_panic','complete_physical17119_return')
    return WorldMotionStopResult135(result,tuple(packets),tuple(stopped),tuple(heights),header_known,header_known,pending)
