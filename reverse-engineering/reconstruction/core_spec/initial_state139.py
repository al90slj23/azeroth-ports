"""Independent fixed1391600 empty-profile numeric/record constructor domain.

Arithmetic expressions are derived from earlier independent constructor work,
then rebound to actual1391600 stores and fresh139 data. No old acceptance is
transferred and no original, snapshot or capture is read by this model.

The selectedProfile376 and explicit flat-world query view are component
inputs. This does not construct App, JS/externref, a cached world Rc owner or
phase1. Unknown pointers/backing and inactive payloads are not synthesized.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f
from .derived_stats139 import StatsInput,recalculate
from .initial_state139_data import CLASS_STARTERS,RACIAL_ABILITIES,ZONE_ENTRIES

MASK64=(1<<64)-1


@dataclass(frozen=True)
class ConstructorInput139:
    class_byte:int
    race_byte:int
    region_index:int
    seed_u64:int
    object_id_u64:int
    flat_height_bits:int

    def __post_init__(self):
        for value,width in((self.class_byte,8),(self.race_byte,8),(self.seed_u64,64),(self.object_id_u64,64),(self.flat_height_bits,32)):
            if type(value)is not int or not 0<=value<1<<width:raise ValueError('Explicit constructor unsigned input required')
        if self.class_byte not in CLASS_STARTERS or self.race_byte not in RACIAL_ABILITIES:raise ValueError('Declared nineclass/eightrace empty-profile domain')
        if type(self.region_index)is not int or not 0<=self.region_index<len(ZONE_ENTRIES):raise ValueError('Fixed139 region')
        if f.is_nan(self.flat_height_bits)or f.is_inf(self.flat_height_bits):raise ValueError('Finite flat query height required')


def seed_rng_words139(seed):
    """1600 inlined PCG four-word seed transformation, before game draws."""
    if type(seed)is not int or not 0<=seed<=MASK64:raise ValueError('u64 seed')
    def draw(multiplier,increment):
        n=(seed*multiplier+increment)&MASK64;value=((n>>45)^(n>>27))&f.MASK;rotate=(n>>59)&31
        return((value>>rotate)|(value<<((-rotate)&31)))&f.MASK
    a=draw(7520897724310334953,-2259998930035483990);b=draw(793875393913628917,5507651024068337109)
    c=draw(-338549647893938671,-3398641427998916252);d=draw(6364136223846793005,-6812164046247290893)
    ab=a|b;abd=ab|d
    check=(ab>>24)|(c&0xffffff)|(d>>24)|((ab|(abd>>8)|(abd>>16)|d)&255)
    if check or c>=0x1000000:return(d,a,b,c)
    low=(-2152535657050944081)&MASK64;high=7960286522194355700
    return(low&f.MASK,low>>32,high&f.MASK,high>>32)


def default_ability_record139(pointer):
    """1600 full80B starter/racial store sequence; every field explicit."""
    one=0x3f800000
    words=(pointer,1,0x3f000000,one,one,0,one,one,0,0,0,0,0,one,one,0,one,one,0,one)
    return struct.pack('<20I',*words).hex()


@dataclass(frozen=True)
class InitialState139:
    input:ConstructorInput139
    stats_result:dict
    owned_records_hex:tuple
    racial_record_hex:str
    player_xyz:tuple
    rng_words:tuple
    initial_scalar_words:tuple
    initial_byte_flags:tuple
    constructor_tags:tuple
    pending:tuple


def initialize_empty_profile139(value):
    if not isinstance(value,ConstructorInput139):raise TypeError('ConstructorInput139 required')
    _,ability,hp=CLASS_STARTERS[value.class_byte];_,racial,_,_=RACIAL_ABILITIES[value.race_byte]
    result=recalculate(StatsInput(class_byte=value.class_byte,race_byte=value.race_byte,level=1,
        old_max_hp_bits=hp,current_hp_bits=hp,now_bits=0,previous_speed_bits=0x40e00000,
        conditional268_bits=0,flag2574=0,pool1532_bits=0,pool1536_bits=0,
        conditional1344_id=0,conditional1348_bits=0,pool768_bits=0))
    zone=ZONE_ENTRIES[value.region_index]
    words=((488,0),(736,0),(740,0),(1652,0xc1200000),
        (2416,0x40400000),(2424,0x42700000),(2428,0),(2432,0),(2436,0),
        (2440,0x43700000),(2444,0x42200000),(2448,0x42700000),(2452,20),
        (2456,0),(2460,0),(2464,0),(2468,0),(2472,0),(2516,0x3f800000))
    flags=tuple((offset,0)for offset in(768,2568,2572,2573,2576,2578,2581,2583))
    # Real1600 writes only option tags; theirinactive payloads remainunknown.
    tags=tuple((o,0)for o in(416,440,448,456,464,1744,1764))
    return InitialState139(value,result,(default_ability_record139(ability),),default_ability_record139(racial),
        (zone[1],zone[2],value.flat_height_bits),seed_rng_words139(value.seed_u64),words,flags,tags,
        ('Account/selected-profile producer is an explicit input boundary,not natural App construction',
         'Default equipment/heapvectors/BTree backing and world Rc lifetime are not independently produced',
         'Cachedworld6786 and opening1108/phase1 remain separate latest139 work'))


def projection139(state):
    result=state.stats_result;value=state.input
    aux=dict(result['auxiliary_bits']);aux['752']=0
    return dict(progression=dict(level=1,xp=0,pending_upgrades=0),derived_bits=result['derived_bits'],
        current_hp_bits=result['derived_bits']['1536'],auxiliary_bits=aux,speed_bits=result['speed_bits'],player_fields=result['object_fields'],
        rng_words=list(state.rng_words),candidates=[],phase2587=0,selection_kind2585=255,generation_counter2400=0,
        owned_records_hex=list(state.owned_records_hex),racial_record_hex=state.racial_record_hex,player_xyz=list(state.player_xyz),
        source_id=str(value.object_id_u64),timer1628_bits=0,spawn_counter=10,message_sequence=1,kill_cost_bits=0,
        action_sequence1644=1+int(result['speed_changed']),movement_packets=constructor_packets139(state),
        game_tag='0',member_count=1,initial_scalar_words=dict(state.initial_scalar_words),initial_byte_flags=dict(state.initial_byte_flags),
        constructor_tags=dict(state.constructor_tags),now_bits=0,mode2582=0,owned_capacity=1,owned_count=1,
        source_counts=dict(passives=0,adjustments=0,item_modifiers=0,owned_skills=0,timed_records=0,definitions=0,live_effects=0,ability_modifiers=0,active84=0),
        unit_count=0,pickup_count=0,gold=0,earned=0,flags768=0,context908=0,extra_cast1596_bits=result['derived_bits']['1596'])


def constructor_packets139(state):
    """1542→48967: new speed after a>.01 change, using old sequence1."""
    if not state.stats_result['speed_changed']:return()
    raw=state.input.object_id_u64.to_bytes(8,'little');mask=sum(1<<j for j,v in enumerate(raw)if v)
    packed=bytes((mask,))+bytes(v for v in raw if v)
    return((226,(packed+struct.pack('<II',1,state.stats_result['speed_bits'])).hex()),)


def canonical_game_cells139(state):
    """Known constructor bytes only; live pointers/inactive payloads stayNone.

    This view is validated bytewise by new1391600 calls. It is deliberately
    partial: neither untouchedstack words nor noncompared physical producers
    become known merely because a fresh WASM memory often contains zeros.
    """
    cells=[None]*2592;p=projection139(state);value=state.input
    def put(offset,data):cells[offset:offset+len(data)]=data
    def word(offset,bits):put(offset,struct.pack('<I',bits))
    put(0,bytes(8));put(1336,struct.pack('<Q',value.object_id_u64));put(1256,bytes.fromhex(state.racial_record_hex))
    cells[360]=value.class_byte;cells[361]=value.race_byte
    for j,v in enumerate(state.player_xyz):word(1416+4*j,v)
    word(1428,ZONE_ENTRIES[value.region_index][3])
    for key,v in p['derived_bits'].items():word(int(key),v)
    for key,v in p['auxiliary_bits'].items():word(int(key),v)
    for o,v in state.initial_scalar_words+state.constructor_tags:word(o,v)
    for o,v in state.initial_byte_flags:cells[o]=v
    for o,v in((1432,1),(1436,0),(1440,p['current_hp_bits']),(1456,0),(1100,0),(1644,p['action_sequence1644']),
            (1648,p['speed_bits']),(1628,0),(2352,0),(2376,0),(2400,0),(2408,10),(2412,1),(2540,1)):
        word(o,v)
    for j,v in enumerate(state.rng_words):word(1720+4*j,v)
    # New physical timed596/600, active84 header640/644/648. No heap pointer
    # is synthesized for the one active owned80 record.
    for cap,ptr,count,sentinel in((592,596,600,4),(640,644,648,4),(1668,1672,1676,4),(1704,1708,1712,8)):
        word(cap,0);word(ptr,sentinel);word(count,0)
    for count in(1700,2032,176,2056,2044):word(count,0)
    word(1656,1);word(1664,1);word(1792,0);word(1876,0)
    word(1888,len(p['movement_packets']))
    cells[2582]=0;cells[2585]=255;cells[2587]=0;cells[908]=0
    return tuple(cells)
