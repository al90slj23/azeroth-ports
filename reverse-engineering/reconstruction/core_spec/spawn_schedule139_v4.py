"""WIP current139 complete952 scheduler threaded with real combat owners.

The genuine full1108 opening supplies four NPCs, two Runes, windows, RNG,
ordinary budget and all timers. All four wave shapes use current rebound
432B constructors and geometry. Canonical world/pathNone/zero velocity are
explicit genuine constructor inputs. Boss/elite/window-due and combat remain
Pending; this module is neither full884 nor an independent App/bootstrap.
"""
from dataclasses import dataclass,replace
import math,struct
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .spawn_math135 import exp_bits
from .position_math139 import hypot_bits
from .world_position139_v2 import DistanceMap139V2
from .rng import uniform_range_bits,next_u32_words
from .npc_heading139 import atan2_bits
from .npc_spawn139 import NPC_WRITTEN_RANGES,BASE_SPEEDS,_packed_guid,_values
from .world_position139_v2 import WorldPositionInput139V2,sample_spawn_position,sample_random_position
from .opening_actor139 import OpeningVector139,_append,create_world_actor139,_kind2_xyz
from .spawn_wave139_v4 import step_event_wave139,EventWaveInput139,EventWaveLocale139,WaveVector139
from .opening_aux139_data import KIND2_DESCRIPTOR
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
class SpawnScheduleState139V4:
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
    next_wave2424_bits:int
    next_elite2440_bits:int
    next_pickup2444_bits:int
    next_pickup2448_bits:int
    next_pickup2452:int
    boss_index2456:int
    packets:tuple
    pickups:OpeningVector139
    last_wave2586:int
    windows:OpeningVector139
    player_level1432:int=1
    distance_map:DistanceMap139V2|None=None

@dataclass(frozen=True)
class SpawnScheduleResult139V4:
    state:SpawnScheduleState139V4
    new_NPCs:tuple
    packets:tuple
    diagnostics:tuple
    pending:tuple=('240s ordinaryelite2440','Boss2801 first3minutes','farNPC replay','nondefault combat/mode/clock owners','window due')

def from_opening139(opening):
    from .opening139 import opening_known_game139,opening_projection139
    g=opening_known_game139(opening);p=opening_projection139(opening)
    if p['units']['count']!=4 or p['phase2587']!=1:raise ValueError('Real default fullopening required')
    # Additional current1600 producers not in older frozen partial constructor
    # view: T+1824 i64zero -> G1736/1740; T+2504 i64(0x40400000)
    # -> G2416 budget3/G2420 killcost0; profile371<3 leaves local13=0,
    # stored T+2072 -> G1984. T+2456 i64zero also produces path2368None.
    return SpawnScheduleState139V4(tuple(tuple(r)for r in p['units']['storage']),4,tuple(opening.rng_words),opening.counter,tuple(opening.constructor.player_xyz),tuple(word(g,o)for o in(2428,2432,2436)),(0,0),word(g,2416),0,0,word(g,2424),word(g,2440),word(g,2444),word(g,2448),word(g,2452),word(g,2456),tuple(tuple(r)for r in p['packets']),OpeningVector139(56,tuple(tuple(r)for r in p['pickups']['storage']),p['pickups']['count']),255,opening.windows.vector)

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

def _npc139(index,now,position,player,words,counter,backing,player_level1432=1):
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
    fields={0:guid&f.MASK,1:guid>>32,2:9,3:entry,4:scale_npc,16:0,17:0,22:hpceil,28:hpceil,34:player_level1432,35:14,36:256,46:0,126:2000,127:2000,129:f.mul(scale_npc,0x3f000000),130:f.mul(scale_npc,0x3fc00000),131:display,132:display,134:0x40a00000,135:0x41200000,145:ONE}
    heading=atan2_bits(f.sub(player[1],position[1]),f.sub(player[0],position[0]))
    payload=struct.pack('<IB',1,0)+bytes([3])+_packed_guid(guid)+bytes([3,112])+struct.pack('<2I',0,0)+struct.pack('<4I',*position,heading)+struct.pack('<I',0)+struct.pack('<6I',*BASE_SPEEDS)+struct.pack('<I',1)+_values(fields)
    return tuple(cells),jitter.state,counter,(169,payload.hex()),yaw.draws+jitter.draws

def update_spawn_schedule139(state,now,dt,world):
    if not isinstance(state,SpawnScheduleState139V4):raise TypeError('SpawnScheduleState139V4 required')
    for x in(now,dt):
        if type(x)is not int or f.is_nan(x)or f.is_inf(x):raise ValueError('Finite explicit binary32 clock required')
    if not 0<f.to_float(dt)<=.125 or f.to_float(now)<f.to_float(state.now_bits):raise ValueError('Positive explicit component dt<=.125 and monotonic clock')
    if f.to_float(now)>=min(180.,f.to_float(state.next_elite2440_bits)):raise PendingSpawnSchedule139('Real Boss/elite timer due')
    if state.windows.count and f.to_float(now)>=f.to_float(word(state.windows.storage[0],4)):raise PendingSpawnSchedule139('Actual resource window due; not cleared')
    if not 1<=state.player_level1432<=62:raise PendingSpawnSchedule139('Level beyond currentdefault1586 finite field34 branch')
    velocity=state.velocity_xy
    dx=f.div(f.sub(state.player_xyz[0],state.previous_player_xyz[0]),dt);dy=f.div(f.sub(state.player_xyz[1],state.previous_player_xyz[1]),dt)
    if f.to_float(hypot_bits(dx,dy))<40:
        smoothing=f.sub(ONE,exp_bits(dt^f.SIGN));velocity=(f.add(velocity[0],f.mul(smoothing,f.sub(dx,velocity[0]))),f.add(velocity[1],f.mul(smoothing,f.sub(dy,velocity[1]))))
    units=list(state.records432);count=state.count
    for row in units[:count]:
        marker=word(row,0)
        if marker not in(0,1):raise PendingSpawnSchedule139('Unknown NPC marker')
        if marker==1:continue
        if word(row,244)!=f.MASK:raise PendingSpawnSchedule139('Live Boss slowdown producer remains Pending')
        if word(row,284)==0 or word(row,64)!=f.MASK or word(row,16):continue
        duration=word(row,344)
        if f.to_float(duration)<=0:xy=tuple(word(row,k)for k in(328,332))
        else:
            ratio=minimum(ONE,maximum(0,f.div(f.sub(now,word(row,340)),duration)))
            xy=tuple(f.add(word(row,a),f.mul(f.sub(word(row,b),word(row,a)),ratio))for a,b in((316,328),(320,332)))
        distance=f.add(f.mul(f.sub(xy[0],state.player_xyz[0]),f.sub(xy[0],state.player_xyz[0])),f.mul(f.sub(xy[1],state.player_xyz[1]),f.sub(xy[1],state.player_xyz[1])))
        if f.to_float(distance)>3025:raise PendingSpawnSchedule139('Actual farNPC replay8750/221; not ignored')
    minute=f.div(now,0x42700000)
    rate=f.mul(f.add(f.add(f.mul(minute,0x3ea3d70a),0x3f666666),f.mul(minute,f.mul(minute,0x3ccccccd))),0x3f19999a)
    killed=f.mul(state.kill_cost2420_bits,exp_bits(f.div(dt,0xc1400000)))
    catchup=minimum(0x40400000,maximum(ONE,f.div(f.mul(f.div(killed,0x41400000),0x3fa00000),maximum(0x3a83126f,rate))))
    rate=f.mul(rate,catchup)
    budget=f.add(state.budget2416_bits,f.mul(dt,rate));words=state.rng_words;counter=state.counter2408;packets=[];new=[];diagnostics=[dict(origin='killcost_decay_catchup',old_bits=state.kill_cost2420_bits,new_bits=killed,catchup_bits=catchup,rate_bits=rate)]
    candidates=tuple(i for i,d in enumerate(DEFS)if d[68]==0 and f.to_float(word(d,64))<=f.to_float(minute))
    def attempt(index,origin,choice_draws):
        nonlocal words,counter,count,units
        if sum(word(r,0)^1 for r in units[:count])>=50:return False
        location=sample_spawn_position(WorldPositionInput139V2(0,state.player_xyz,velocity,0x41d00000,0x42100000,0x3f000000,words,state.distance_map),world)
        if count==len(units):units.extend([(None,)*432]*(max(4,2*len(units))-len(units)))
        row,words,counter,packet,draws=_npc139(index,now,location.position_bits,state.player_xyz,location.rng_words,counter,units[count],state.player_level1432);units[count]=row
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
    # Complete current2424 call order: ordinary -> elite(future) -> wave -> Boss(future).
    wave=step_event_wave139(EventWaveInput139(0,now,state.next_wave2424_bits,state.last_wave2586,state.player_xyz,velocity,tuple(words),counter,1,WaveVector139(432,tuple(units),count),0,state.player_level1432,word(ZONE,136),distance_map=state.distance_map),world,locale=EventWaveLocale139(0))
    words=wave.rng_words;counter=wave.counter;units=list(wave.units.storage);count=wave.units.count;packets.extend(wave.packets)
    new.extend((slot,index,guid,'wave2424')for slot,index,guid in wave.creates)
    if wave.event is not None:diagnostics.append(dict(origin='wave2424',event=wave.event,index=wave.definition_index,requested=wave.requested,draws=wave.draws,charged=list(map(str,wave.charged_guids))))
    # Real95240s scheduler: periodic45s, cappedtwo kind3/4/5 pickups.
    pickups=state.pickups;deadline=state.next_pickup2444_bits
    if f.to_float(now)>=f.to_float(deadline):
        deadline=f.add(now,0x42340000)
        if sum(3<=word(row,8)<=5 for row in pickups.storage[:pickups.count])<2:
            for draw_count in range(1,100001):
                output,words=next_u32_words(words);product=output*3
                if product&f.MASK<=0xbfffffff:break
            else:raise PendingSpawnSchedule139('Bounded kind3 RNG watchdog')
            kind=3+(product>>32);argument2=words[0]
            location=sample_random_position(WorldPositionInput139V2(0,state.player_xyz,velocity,0x41700000,0x42200000,0,words,state.distance_map),world)
            descriptor={3:(9006,5931,ONE),4:(9007,5995,ONE),5:(9008,5991,ONE)}[kind]
            xyz=_kind2_xyz(location.position_bits,world)
            actor=create_world_actor139(*descriptor,xyz,5,0,counter,location.rng_words)
            pickups=_append(pickups,((0,struct.pack('<I',0)),(8,struct.pack('<IIQ',kind,argument2,actor.create.guid)),(24,struct.pack('<4I',0,8,0,descriptor[0])),(40,struct.pack('<4I',*xyz,now))))
            counter=actor.counter;words=actor.rng_words;packets.append((169,actor.create.payload169.hex()))
            diagnostics.append(dict(origin='pickup40',kind=kind,argument2=argument2,kind_draws=draw_count,position_draws=location.draws,actor_draws=actor.draws))
    # Genuine first Rune2448, cap3. The opaque argument2 is an actual heap
    # pointer expression left in caller local2, not a modeled numeric amount.
    rune_deadline=state.next_pickup2448_bits
    if f.to_float(now)>=f.to_float(rune_deadline):
        rune_deadline=f.add(now,0x428c0000)
        if sum(word(row,8)==2 for row in pickups.storage[:pickups.count])<3:
            if pickups.count!=3:raise PendingSpawnSchedule139('FirstRune opaque argument2 source outside count3')
            location=sample_random_position(WorldPositionInput139V2(0,state.player_xyz,velocity,0x41900000,0x42480000,0,words,state.distance_map),world)
            xyz=_kind2_xyz(location.position_bits,world);actor=create_world_actor139(*KIND2_DESCRIPTOR,xyz,3,0,counter,location.rng_words)
            pickups=_append(pickups,((0,struct.pack('<I',0)),(8,struct.pack('<I',2)),(12,(None,)*4),(16,struct.pack('<Q',actor.create.guid)),(24,struct.pack('<4I',0,8,0,KIND2_DESCRIPTOR[0])),(40,struct.pack('<4I',*xyz,now))))
            words=actor.rng_words;counter=actor.counter;packets.append((169,actor.create.payload169.hex()));diagnostics.append(dict(origin='Rune2448',argument2_known=False,argument2_expression='preRunePickupBase+176',position_draws=location.draws,actor_draws=actor.draws))
    result=replace(state,records432=tuple(units),count=count,rng_words=tuple(words),counter2408=counter,previous_player_xyz=state.player_xyz,velocity_xy=velocity,budget2416_bits=budget,kill_cost2420_bits=killed,now_bits=now,packets=state.packets+tuple(packets),pickups=pickups,next_pickup2444_bits=deadline,next_pickup2448_bits=rune_deadline,next_wave2424_bits=wave.next_event2424_bits,last_wave2586=wave.last_event2586)
    return SpawnScheduleResult139V4(result,tuple(new),tuple(packets),tuple(diagnostics))

def from_combat139(opening,actor,physical,*,previous=None,distance_map=None):
    """Thread genuine player/combat/physical owners into the scheduler.

    Persistent scheduler fields come from the previous952 result, or genuine
    constructor/opening if952 has not run. Player/AI/collection packet streams
    belong to their caller; state.packets is this scheduler's emission history.
    """
    state=from_opening139(opening)if previous is None else previous
    if not isinstance(state,SpawnScheduleState139V4):raise TypeError('Current v4 persistent scheduler owner required')
    player=actor.player;g=player.growth;damage=actor.damage
    if physical.active!=damage.records432 or physical.active!=g.units432_cells:raise ValueError('Combat/physical/growth rows must agree')
    if damage.rng_words!=g.rng_words or damage.counter2408<0:raise ValueError('Actual combat RNG/counter required')
    path=None if distance_map is None else DistanceMap139V2(tuple(distance_map.values_u16),distance_map.field24)
    return replace(state,records432=physical.storage,count=physical.count,rng_words=tuple(damage.rng_words),counter2408=damage.counter2408,player_xyz=tuple(player.player_xyz),kill_cost2420_bits=damage.killcost2420_bits,now_bits=g.now_bits,pickups=OpeningVector139(56,damage.pickups.storage,damage.pickups.count),player_level1432=g.level,distance_map=path)

def projection139(state):
    return dict(player_level1432=state.player_level1432,last_wave2586=state.last_wave2586,windows=dict(capacity=state.windows.capacity,count=state.windows.count,storage=[list(r)for r in state.windows.storage]),count=state.count,capacity=len(state.records432),records432_cells=[list(r)for r in state.records432],rng_words=list(state.rng_words),counter2408=state.counter2408,now_bits=state.now_bits,budget2416_bits=state.budget2416_bits,kill_cost2420_bits=state.kill_cost2420_bits,previous_player_xyz=list(state.previous_player_xyz),velocity_xy=list(state.velocity_xy),timer_fields={str(k):v for k,v in ((2424,state.next_wave2424_bits),(2440,state.next_elite2440_bits),(2444,state.next_pickup2444_bits),(2448,state.next_pickup2448_bits),(2452,state.next_pickup2452),(2456,state.boss_index2456))},packets=[list(p)for p in state.packets],pickups=dict(capacity=state.pickups.capacity,count=state.pickups.count,storage=[list(r)for r in state.pickups.storage]))

def thread_spawn_result139(actor,result):
    """Return updated actor owners; caller retains incoming/history/other systems."""
    from .death_pickups139 import PickupVector139
    state=result.state;active=tuple(state.records432[:state.count]);g=replace(actor.player.growth,units432_cells=active,rng_words=tuple(state.rng_words),now_bits=state.now_bits)
    player=replace(actor.player,growth=g)
    damage=replace(actor.damage,records432=active,rng_words=tuple(state.rng_words),now_bits=state.now_bits,counter2408=state.counter2408,killcost2420_bits=state.kill_cost2420_bits,pickups=PickupVector139(state.pickups.storage,state.pickups.count))
    return replace(actor,player=player,damage=damage)
