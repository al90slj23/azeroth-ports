"""Fixed135 G2448 timed kind2 supply and full1417 declared producer domain.

Clock scheduling is separate from ordinary947 work and G2444 resources345.
The caller supplies independently owned post-ordinary state and query world.
An iterator-address amount is represented by provenance, never a fake pointer.
"""
from dataclasses import dataclass
import struct

from . import binary32 as f
from .opening_entities135 import create_world_actor
from .opening_npc_pickups135 import OpeningVector135, _write_row
from .record_cells135 import u32, u64
from .spawn_geometry135 import hypot_bits
from .spawn_position135_data import ZONE_GEOMETRY
from .world_position135 import WorldPositionInput135, sample_random_position


class PendingSupplyKind2135(NotImplementedError):
    pass


def _word(value):
    if type(value)is not int or not 0<=value<=f.MASK:
        raise ValueError('Explicit unsigned32 supply word required')
    return value


def _finite(value):
    _word(value)
    if value&0x7fffffff>=f.INF:
        raise ValueError('Finite binary32 supply coordinate/time required')
    return value


def _common(value):
    if type(value.zone)is not int or not 0<=value.zone<len(ZONE_GEOMETRY):
        raise ValueError('Explicit fixed135 zone required')
    _finite(value.now_bits);_word(value.counter)
    if len(value.rng_words)!=4:
        raise ValueError('Four shared supply RNG words required')
    for word in value.rng_words:_word(word)
    if not isinstance(value.pickups,OpeningVector135)or value.pickups.stride!=56:
        raise ValueError('Complete physical56B supply vector required')
    if value.mode not in(0,1):
        raise PendingSupplyKind2135('Only actual local/cooperative mode0/1 supply restored')
    _word(value.party_count2140);_word(value.excluded2548)


def cooperative_supply_factor135(mode,party_count2140,excluded2548):
    """The actual wrapping/underflow guard, clamp-to-one and f32 sequence."""
    _word(party_count2140);_word(excluded2548)
    if mode==0:return 0x3f800000,None
    if mode!=1:raise PendingSupplyKind2135('Supply mode unsupported')
    total=(party_count2140+1)&f.MASK
    remaining=(total-excluded2548)&f.MASK
    guarded=remaining if remaining<=total else 0
    effective=max(1,guarded)
    factor=f.add(f.mul(f.sub(f.from_u32(effective),0x3f800000),0x3f000000),0x3f800000)
    return factor,guarded


def _round85719_u32(word):
    """Exact positive input slice of original85719, not generic ceil."""
    rounded=f.add(word,0x3effffff)
    exponent=(rounded>>23)&255
    if exponent<=149:
        mask=0x80000000 if exponent<127 else((-8388608)>>((exponent-127)&31))&f.MASK
        rounded&=mask
    value=f.to_float(rounded)
    return 0 if f.is_nan(rounded)or value<=0 else f.MASK if value>=f.MASK else int(value)


def supply_caps135(mode,party_count2140,excluded2548):
    factor,guarded=cooperative_supply_factor135(mode,party_count2140,excluded2548)
    return factor,_round85719_u32(f.mul(factor,0x40400000)),_round85719_u32(f.mul(factor,0x40a00000)),guarded


@dataclass(frozen=True)
class OpaqueSupplyAmount135:
    owner_symbol:str
    active_count:int
    byte_delta:int

    def __post_init__(self):
        if self.owner_symbol!='pickup56_owner_before2448' or not 1<=self.active_count<=4096:
            raise ValueError('Exact pre2448 vector owner provenance required')
        expected=(176+224*(self.active_count//4)if self.active_count%4==0 else 8+56*self.active_count)
        if self.byte_delta!=expected:
            raise ValueError('Incorrect actual947 counting iterator delta')


@dataclass(frozen=True)
class Kind2PickupInput135:
    zone:int
    amount:int|None
    position_bits:tuple
    now_bits:int
    rng_words:tuple
    counter:int
    pickups:OpeningVector135
    mode:int=0
    party_count2140:int=0
    excluded2548:int=0
    opaque_amount:OpaqueSupplyAmount135|None=None


@dataclass(frozen=True)
class Kind2PickupResult135:
    pickups:OpeningVector135
    rng_words:tuple
    counter:int
    position_bits:tuple
    creates:tuple
    packets:tuple
    removed_guids:tuple
    opaque_word_provenance:tuple
    actor_draws:int


def _position(value,world):
    if world is None or not hasattr(world,'primary'):
        raise PendingSupplyKind2135('Explicit query-world provider required')
    if len(value.position_bits)!=3:raise ValueError('Explicit supply XYZ required')
    x,y,_=tuple(_finite(word)for word in value.position_bits)
    cx,cy,radius=ZONE_GEOMETRY[value.zone]
    dx,dy=f.sub(x,cx),f.sub(y,cy);distance=hypot_bits(dx,dy)
    limit=f.add(radius,0xc0000000)
    limit=limit if not f.is_nan(limit)and f.to_float(limit)>1 else 0x3f800000
    if not f.to_float(distance)<=f.to_float(limit):
        x=f.add(cx,f.mul(f.div(dx,distance),limit));y=f.add(cy,f.mul(f.div(dy,distance),limit))
        first=world.height(x,y)
        if not first.found and world.primary is not None:world.nearest_primary(x,y)
    sampled=world.height(x,y)
    if sampled.found:return x,y,sampled.value_bits
    if world.primary is None:return x,y,world.fallback_height_bits
    nearest=world.nearest_primary(x,y)
    if nearest.found:return x,y,nearest.xyz_bits[2]
    raise PendingSupplyKind2135('1417 primary-present nearest-miss low-address read unresolved')


def _total_key(word):
    transformed=word^(0x7fffffff if word&0x80000000 else 0)
    return transformed-(1<<32)if transformed&0x80000000 else transformed


def produce_kind2_pickup135(value:Kind2PickupInput135,world):
    """1417 kind2; oldest replacement has actual default-empty aux owner."""
    _common(value)
    if value.amount is None:
        if not isinstance(value.opaque_amount,OpaqueSupplyAmount135):
            raise ValueError('Unknown amount requires exact iterator owner provenance')
    else:
        _word(value.amount)
        if value.opaque_amount is not None:raise ValueError('Known amount must not carry opaque provenance')
    xyz=_position(value,world)
    _,_,cap,_=supply_caps135(value.mode,value.party_count2140,value.excluded2548)
    storage=list(value.pickups.storage);count=value.pickups.count
    matching=[i for i,row in enumerate(storage[:count])if u32(row,8,'1417 kind2 count')==2]
    packets=[];removed=[]
    if matching and len(matching)>=cap:
        index=min(matching,key=lambda i:_total_key(u32(storage[i],52,'1417 kind2 oldest arrival')))
        row=storage[index];marker=u32(row,0,'31732 removal marker')
        if marker==2:
            raise PendingSupplyKind2135('Original31732 marker2 enters panic after compaction; partial trap projection pending')
        if marker!=2:
            if u32(row,24,'31732 auxiliary capacity')or u32(row,32,'31732 auxiliary length'):
                raise PendingSupplyKind2135('Nonempty kind2 auxiliary GUID ownership/drop unresolved')
            guid=u64(row,16,'31732 removed GUID');packets.append((170,struct.pack('<Q',guid).hex()));removed.append(guid)
        storage[index:count-1]=storage[index+1:count]
        count-=1
    vector=OpeningVector135(56,tuple(storage),count)
    actor=create_world_actor(9005,259,0x3f800000,xyz,3,0,value.counter,value.rng_words)
    amount=struct.pack('<I',value.amount)if value.amount is not None else(None,)*4
    vector=_write_row(vector,((0,struct.pack('<I',0)),(8,struct.pack('<I',2)),(12,amount),
        (16,struct.pack('<Q',actor.create.guid)),(24,struct.pack('<III',0,8,0)),
        (36,struct.pack('<I',9005)),(40,struct.pack('<4I',*xyz,value.now_bits))))
    packets.append((169,actor.create.payload169_hex))
    opaque=()if value.opaque_amount is None else(dict(guid=str(actor.create.guid),offset=12,bytes=4,
        owner_symbol=value.opaque_amount.owner_symbol,active_count=value.opaque_amount.active_count,
        byte_delta=value.opaque_amount.byte_delta,expression='pre_owner_base+byte_delta modulo2^32'),)
    return Kind2PickupResult135(vector,actor.rng_words,actor.counter,xyz,(actor.create,),tuple(packets),tuple(removed),opaque,actor.draws)


@dataclass(frozen=True)
class SupplyTickInput135:
    zone:int
    now_bits:int
    next_supply2448_bits:int
    player_xyz_bits:tuple
    velocity_xy:tuple
    rng_words:tuple
    counter:int
    pickups:OpeningVector135
    mode:int=0
    party_count2140:int=0
    excluded2548:int=0


@dataclass(frozen=True)
class SupplyTickResult135:
    status:str
    next_supply2448_bits:int
    pickups:OpeningVector135
    rng_words:tuple
    counter:int
    packets:tuple=()
    creates:tuple=()
    opaque_word_provenance:tuple=()
    position:object|None=None
    final_position_bits:tuple|None=None
    counted_kind2:int|None=None
    factor_bits:int|None=None
    cap:int|None=None
    position_draws:int=0
    actor_draws:int=0


def step_supply_kind2_135(value:SupplyTickInput135,world):
    _common(value);_word(value.next_supply2448_bits)
    if not f.to_float(value.now_bits)>=f.to_float(value.next_supply2448_bits):
        return SupplyTickResult135('supply2448_future',value.next_supply2448_bits,value.pickups,value.rng_words,value.counter)
    factor,cap,_,guarded=supply_caps135(value.mode,value.party_count2140,value.excluded2548)
    deadline=f.add(value.now_bits,f.div(0x428c0000,factor))
    counted=sum(u32(row,8,'G2448 active kind count')==2 for row in value.pickups.storage[:value.pickups.count])
    if counted>=cap:
        return SupplyTickResult135('supply2448_cap',deadline,value.pickups,value.rng_words,value.counter,
            counted_kind2=counted,factor_bits=factor,cap=cap)
    count=value.pickups.count;opaque=None
    if count:
        opaque=OpaqueSupplyAmount135('pickup56_owner_before2448',count,
            176+224*(count//4)if count%4==0 else 8+56*count)
        amount=None
    elif value.mode==1:
        amount=guarded
    else:
        raise PendingSupplyKind2135('Mode0 empty-vector amount depends on earlier947 local2 provenance')
    location=sample_random_position(WorldPositionInput135(value.zone,value.player_xyz_bits,value.velocity_xy,
        0x41900000,0x42480000,0,value.rng_words),world)
    created=produce_kind2_pickup135(Kind2PickupInput135(value.zone,amount,location.position_bits,value.now_bits,
        location.rng_words,value.counter,value.pickups,value.mode,value.party_count2140,value.excluded2548,opaque),world)
    return SupplyTickResult135('supply2448_spawned',deadline,created.pickups,created.rng_words,created.counter,
        created.packets,created.creates,created.opaque_word_provenance,location,created.position_bits,counted,
        factor,cap,location.draws,created.actor_draws)
