"""Current139 full952 default ordinary schedule before other timers become due.

The genuine full1108 opening supplies fourNPCs, RNG, budget and all timers.
Independent canonical geometry supplies positions; no binary, snapshot, trace
or observed result is read. This first executable domain is stationary mode0,
no combat/deaths, before40s. Later pickup/elite/wave/Boss work is explicit Pending,
not replaced with an ordinary-only scheduler and not declared complete952.
"""
from dataclasses import dataclass,replace
import math,struct
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .rng import uniform_range_bits
from .npc_heading139 import atan2_bits
from .npc_spawn139 import NPC_WRITTEN_RANGES,BASE_SPEEDS,_packed_guid,_values
from .world_position139_v2 import WorldPositionInput139V2,sample_spawn_position
from .spawn_schedule139_data import ELWYNN152_HEX,NORMAL_BASE,NORMALS72_HEX

ONE=0x3f800000
ZONE=bytes.fromhex(ELWYNN152_HEX)
DEFS=tuple(bytes.fromhex(x)for x in NORMALS72_HEX)
def word(row,o):
    b=tuple(row[o:o+4])
    if len(b)!=4 or None in b:raise PendingSpawnSchedule139('Actually consumed unknown432 cell '+str(o))
    return struct.unpack('<I',bytes(b))[0]
def maximum(a,b):return a if f.to_float(a)>f.to_float(b)else b
def minimum(a,b):return a if f.to_float(a)<f.to_float(b)else b
class PendingSpawnSchedule139(NotImplementedError):pass

@dataclass(frozen=True)
class SpawnScheduleState139:
    records432:tuple
    count:int
    rng_words:tuple
    counter2408:int
    player_xyz:tuple
    previous_player_xyz:tuple
    velocity_xy:tuple
    budget2416_bits:int
    kill_cost2420_bits:int
    now_bits:int
    next_elite2424_bits:int
    next_wave2440_bits:int
    next_pickup2444_bits:int
    next_pickup2448_bits:int
    next_pickup2452:int
    boss_index2456:int
    packets:tuple

@dataclass(frozen=True)
class SpawnScheduleResult139:
    state:SpawnScheduleState139
    new_NPCs:tuple
    packets:tuple
    diagnostics:tuple
    pending:tuple=('40s pickup1446','60s ordinaryelite events','240s wave events','Boss2801 timers','farNPC replay','nondefault combat/mode/clock owners')

def from_opening139(opening):
    from .opening139 import opening_known_game139,opening_projection139
    g=opening_known_game139(opening);p=opening_projection139(opening)
    if p['units']['count']!=4 or p['phase2587']!=1:raise ValueError('Real default fullopening required')
    # Additional current1600 producers not in older frozen partial constructor
    # view: T+1824 i64zero -> G1736/1740; T+2504 i64(0x40400000)
    # -> G2416 budget3/G2420 killcost0; profile371<3 leaves local13=0,
    # stored T+2072 -> G1984. T+2456 i64zero also produces path2368None.
    return SpawnScheduleState139(tuple(tuple(r)for r in p['units']['storage']),4,tuple(opening.rng_words),opening.counter,tuple(opening.constructor.player_xyz),tuple(word(g,o)for o in(2428,2432,2436)),(0,0),word(g,2416),0,0,word(g,2424),word(g,2440),word(g,2444),word(g,2448),word(g,2452),word(g,2456),tuple(tuple(r)for r in p['packets']))

def choose_normal139(candidates,minutes,words):
    weights=[]
    for index in candidates:
        d=DEFS[index];age=maximum(f.sub(minutes,word(d,64)),0)
        weights.append(f.div(minimum(0x40800000,f.add(f.mul(age,0x3f000000),ONE)),word(d,60)))
    total=f.SIGN
    for weight in weights:total=f.add(total,weight)
    if not weights:raise PendingSpawnSchedule139('Empty normal candidate panic')
    draw=uniform_range_bits(words,0,maximum(0x3a83126f,total));left=draw.bits
    for index,weight in zip(candidates,weights):
        if f.to_float(left)<f.to_float(weight):return index,draw.state,draw.draws
        left=f.sub(left,weight)
    return candidates[0],draw.state,draw.draws

def _npc139(index,now,position,player,words,counter,backing):
    """5719/1586 ordinary finite default1player/level1 nonendless branch."""
    d=DEFS[index]
    if d[68]:raise PendingSpawnSchedule139('Elite5719 record')
    t=f.div(now,0x42700000);scale=word(ZONE,136)
    growth=f.mul(scale,f.add(f.add(f.add(f.mul(t,0x3dcccccd),ONE),f.mul(t,f.mul(t,0x3d1374bc))),f.mul(t,f.mul(t,f.mul(t,0x3be6afcd)))))
    hp=f.mul(f.mul(0x409e6666,word(d,40)),growth)
    q=minimum(ONE,maximum(f.div(t,0x41a00000),0))
    hp=f.mul(hp,f.add(f.mul(q,f.mul(q,word(ZONE,140))),ONE))
    poly=f.add(f.mul(t,0x3d8f5c29),ONE)
    poly=f.add(poly,f.mul(t,f.mul(t,0x3c75c28f)))
    poly=f.add(poly,f.mul(t,f.mul(t,f.mul(t,0x3951b717))))
    attack=f.mul(f.mul(0x3fa00000,word(d,44)),f.mul(poly,sqrt_bits(scale)))
    counter=(counter+1)&f.MASK;entry=word(d,24);guid=0xf130000000000000|((entry&0xffffff)<<24)|(counter&0xffffff)
    yaw=uniform_range_bits(words,0,0x40c90fdb);jitter=uniform_range_bits(yaw.state,0,0x3e99999a)
    raw=bytearray(432)
    def put(o,v):struct.pack_into('<I',raw,o,v)
    for o in(40,64,244):put(o,f.MASK)
    struct.pack_into('<Q',raw,112,guid);struct.pack_into('<Q',raw,236,4)
    scale_npc=word(d,32);speed=word(d,48)
    for o,v in((280,0),(284,NORMAL_BASE+72*index),(288,hp),(292,hp),(296,attack),(300,f.mul(word(d,52),0x3f866666)),(304,speed),(308,f.add(f.mul(scale_npc,0x3f99999a),0x400ccccd)),(312,scale_npc),(340,now),(348,f.add(now,f.add(jitter.bits,0))),(352,f.mul(speed,0x3f000000)),(404,f.add(yaw.bits,0))):put(o,v)
    for o in(316,328):struct.pack_into('<3I',raw,o,*position)
    cells=list(backing)
    for o,n in NPC_WRITTEN_RANGES:cells[o:o+n]=raw[o:o+n]
    hpceil=math.ceil(f.to_float(hp));display=word(d,28)
    fields={0:guid&f.MASK,1:guid>>32,2:9,3:entry,4:scale_npc,16:0,17:0,22:hpceil,28:hpceil,34:1,35:14,36:256,46:0,126:2000,127:2000,129:f.mul(scale_npc,0x3f000000),130:f.mul(scale_npc,0x3fc00000),131:display,132:display,134:0x40a00000,135:0x41200000,145:ONE}
    heading=atan2_bits(f.sub(player[1],position[1]),f.sub(player[0],position[0]))
    payload=struct.pack('<IB',1,0)+bytes([3])+_packed_guid(guid)+bytes([3,112])+struct.pack('<2I',0,0)+struct.pack('<4I',*position,heading)+struct.pack('<I',0)+struct.pack('<6I',*BASE_SPEEDS)+struct.pack('<I',1)+_values(fields)
    return tuple(cells),jitter.state,counter,(169,payload.hex()),yaw.draws+jitter.draws

def update_spawn_schedule139(state,now,dt,world):
    if not isinstance(state,SpawnScheduleState139):raise TypeError('SpawnScheduleState139 required')
    for x in(now,dt):
        if type(x)is not int or f.is_nan(x)or f.is_inf(x):raise ValueError('Finite explicit binary32 clock required')
    if not 0<f.to_float(dt)<=.125 or f.to_float(now)<f.to_float(state.now_bits):raise ValueError('Positive explicit component dt<=.125 and monotonic clock')
    if f.to_float(now)>=min(map(f.to_float,(state.next_pickup2444_bits,state.next_pickup2448_bits,state.next_elite2424_bits,state.next_wave2440_bits))):raise PendingSpawnSchedule139('A real nonordinary timer is due; not replaced by empty/simplified scheduler')
    if state.kill_cost2420_bits!=0 or state.velocity_xy!=(0,0):raise PendingSpawnSchedule139('Nonzero killcatchup/velocity')
    if state.previous_player_xyz not in((0,0,0),state.player_xyz):raise PendingSpawnSchedule139('Player motion producer')
    units=list(state.records432);count=state.count
    for row in units[:count]:
        if word(row,0)!=0 or word(row,244)!=f.MASK:raise PendingSpawnSchedule139('Death/Boss slowdown or nondefault actor')
        if word(row,344)!=0:raise PendingSpawnSchedule139('Moving NPC replay')
        distance=f.add(f.mul(f.sub(word(row,328),state.player_xyz[0]),f.sub(word(row,328),state.player_xyz[0])),f.mul(f.sub(word(row,332),state.player_xyz[1]),f.sub(word(row,332),state.player_xyz[1])))
        if f.to_float(distance)>3025:raise PendingSpawnSchedule139('FarNPC full8740/221 replay')
    minute=f.div(now,0x42700000)
    rate=f.mul(f.add(f.add(f.mul(minute,0x3ea3d70a),0x3f666666),f.mul(minute,f.mul(minute,0x3ccccccd))),0x3f19999a)
    budget=f.add(state.budget2416_bits,f.mul(dt,rate));words=state.rng_words;counter=state.counter2408;packets=[];new=[];diagnostics=[]
    candidates=tuple(i for i,d in enumerate(DEFS)if d[68]==0 and f.to_float(word(d,64))<=f.to_float(minute))
    def attempt(index,origin,choice_draws):
        nonlocal words,counter,count,units
        if count>=50:return False
        location=sample_spawn_position(WorldPositionInput139V2(0,state.player_xyz,(0,0),0x41d00000,0x42100000,0x3f000000,words,None),world)
        if count==len(units):units.extend([(None,)*432]*(max(4,2*len(units))-len(units)))
        row,words,counter,packet,draws=_npc139(index,now,location.position_bits,state.player_xyz,location.rng_words,counter,units[count]);units[count]=row
        new.append((count,index,str(struct.unpack('<Q',bytes(row[112:120]))[0]),origin));count+=1;packets.append(packet)
        diagnostics.append(dict(origin=origin,index=index,choice_draws=choice_draws,position_draws=location.draws,position_attempts=location.attempts,position_shrinks=location.radius_shrinks,position_branch=location.branch,NPC_draws=draws))
        return True
    if f.to_float(budget)>=1:
        for _ in range(8):
            index,words,n=choose_normal139(candidates,minute,words);cost=word(DEFS[index],60)
            if f.to_float(cost)>f.to_float(budget):break
            if not attempt(index,'budget',n):budget=minimum(cost,budget);break
            budget=f.sub(budget,cost)
            if f.to_float(budget)<1:break
    target=int(f.to_float(minimum(0x42100000,f.add(f.mul(minute,0x3fcccccd),0x40800000))))
    alive=sum(word(row,0)==0 and word(row,284)!=0 and DEFS[(word(row,284)-NORMAL_BASE)//72][68]==0 for row in units[:count])
    for _ in range(min(3,max(0,target-alive))):
        index,words,n=choose_normal139(candidates,minute,words)
        if not attempt(index,'density',n):break
    result=replace(state,records432=tuple(units),count=count,rng_words=tuple(words),counter2408=counter,previous_player_xyz=state.player_xyz,budget2416_bits=budget,now_bits=now,packets=state.packets+tuple(packets))
    return SpawnScheduleResult139(result,tuple(new),tuple(packets),tuple(diagnostics))

def projection139(state):
    return dict(count=state.count,capacity=len(state.records432),records432_cells=[list(r)for r in state.records432],rng_words=list(state.rng_words),counter2408=state.counter2408,now_bits=state.now_bits,budget2416_bits=state.budget2416_bits,kill_cost2420_bits=state.kill_cost2420_bits,previous_player_xyz=list(state.previous_player_xyz),velocity_xy=list(state.velocity_xy),timer_fields={str(k):v for k,v in ((2424,state.next_elite2424_bits),(2440,state.next_wave2440_bits),(2444,state.next_pickup2444_bits),(2448,state.next_pickup2448_bits),(2452,state.next_pickup2452),(2456,state.boss_index2456))},packets=[list(p)for p in state.packets])
