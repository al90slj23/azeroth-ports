"""Independent current139 default humanWarrior complete opening composition.

The pure current139 world provider,explicit empty-account sources and App LCG
input are supplied. No original program,snapshot,capture,resource file,save or
host is read. Natural App/resource/Rc ownership is not manufactured here.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f
from .initial_state139 import(ConstructorInput139,initialize_empty_profile139,canonical_game_cells139,constructor_packets139)
from .natural_npc139 import NaturalNPCInput139,create_four_natural_normals139
from .opening_profile139 import EmptyAccountSources139,absent_companion_selection139,advance_app_seed139,start_banner139
from .opening_actor139 import OpeningVector139,create_initial_kind2_139
from .opening_aux139 import create_opening_windows139,create_special_records139,create_boundaries139
from .opening_aux139_data import CENTER_XY_BITS,TITLE_UTF8,SUBTITLE_UTF8

class UnknownOpening139(NotImplementedError):pass
@dataclass(frozen=True)
class DefaultOpeningInput139:
    app_seed_u64:int
    companion_sources:EmptyAccountSources139
    selected_prior40:tuple|None=None

@dataclass(frozen=True)
class DefaultOpening139:
    constructor:object
    constructor_seed_u64:int
    selected40_cells:tuple
    units:dict
    pickups:object
    windows:object
    special:OpeningVector139
    boundaries:object
    counter:int
    rng_words:tuple
    packets:tuple
    packet_capacity:int
    notifications:tuple
    pending:tuple

def initialize_default_opening139(value,world):
    if not isinstance(value,DefaultOpeningInput139):raise TypeError('Typed current139 default opening input required')
    if not isinstance(value.companion_sources,EmptyAccountSources139):raise UnknownOpening139('Explicit producer-bound companion sources required')
    if world.primary is not None or world.flat_height_bits is not None:raise UnknownOpening139('Default real no-primary nonflat world required')
    selected=absent_companion_selection139(value.companion_sources,value.selected_prior40)
    if selected[4]!=255 or selected[12]!=255:raise UnknownOpening139('Only independently absent companion variants')
    height=world.height(*CENTER_XY_BITS)
    if not height.found:raise UnknownOpening139('Constructor centre miss/nearest fallback remains separate')
    seed=advance_app_seed139(value.app_seed_u64);initial=initialize_empty_profile139(ConstructorInput139(1,1,0,seed,0,height.value_bits))
    prefix=tuple(constructor_packets139(initial))
    if prefix:raise UnknownOpening139('Current default expects no constructor speed-change packet')
    units=create_four_natural_normals139(NaturalNPCInput139(tuple(initial.rng_words),10,initial.player_xyz,(0,0),(),None),world);last=units['answers'][-1]
    pickups=create_initial_kind2_139(initial.player_xyz,world,tuple(last['rng_words']),last['counter'],now_bits=0,velocity_xy=(0,0),distance_map=None)
    windows=create_opening_windows139(pickups.rng_words);special=create_special_records139(world);boundaries=create_boundaries139(world,pickups.counter,windows.rng_words)
    banner=start_banner139(TITLE_UTF8,SUBTITLE_UTF8);packets=((150,banner.payload.hex()),)+tuple(tuple(row)for row in last['packets'])+tuple((169,a.payload169.hex())for a in pickups.creates)+tuple((169,a.payload169.hex())for a in boundaries.creates)
    cap=0
    for i,_ in enumerate(packets):
        if i==cap:cap=max(4,2*cap)
    return DefaultOpening139(initial,seed,selected,units,pickups,windows,special,boundaries,boundaries.counter,boundaries.rng_words,packets,cap,(b'{"type":"start"}',),
        ('Only currentElwynn/class1/race1/playerGUID0/mode0/level1/emptyaccount/defaultcontrols.',
         'World provider is independently resolved data;App/profile/WorldRc/JSresource bootstrap remains explicit.',
         'No subsequent mainloop/combat/growth/death/game completion is implied.'))

def opening_projection139(state):
    def vector(v):return dict(capacity=v.capacity,count=v.count,storage=[list(row)for row in v.storage])
    last=state.units['answers'][-1]
    return dict(phase2587=1,counter=state.counter,rng_words=list(state.rng_words),player_xyz=list(state.constructor.player_xyz),companions=dict(capacity=0,count=0,storage=[]),
        units=dict(capacity=last['capacity'],count=last['count'],storage=last['records432_cells']),pickups=vector(state.pickups.vector),windows=vector(state.windows.vector),special=vector(state.special),boundaries=vector(state.boundaries.vector),
        packets=[list(p)for p in state.packets],packet_capacity=state.packet_capacity,notification_capacity=4,notifications=[n.hex()for n in state.notifications])

def opening_known_game139(state):
    cells=list(canonical_game_cells139(state.constructor));p=opening_projection139(state)
    def word(offset,value):cells[offset:offset+4]=struct.pack('<I',value)
    cells[2587]=1
    for j,w in enumerate(state.rng_words):word(1720+4*j,w)
    word(2408,state.counter)
    for key,cap,count in(('units',1784,1792),('pickups',1868,1876),('special',1916,1924),('windows',1964,1972),('companions',2108,2116),('boundaries',2120,2128)):
        word(cap,p[key]['capacity']);word(count,p[key]['count'])
    word(1880,state.packet_capacity);word(1888,len(state.packets));word(1892,4);word(1900,len(state.notifications))
    # Actual1600 selectedP+224/+232 toGame+240/+248 is an input handoff.
    # Unknown producer padding staysNone;the control tags are independently255.
    cells[244]=cells[252]=255
    return tuple(cells)
