"""WIP current139925 mixed ordinary/Guardian first-aggro/skill queue branch.

The numeric AI rules use actual row296/300/304/308, with declaration-checked
families and current1076 English identities. Full source records stay intact;
no pointer replacement, NPC filtering from physical storage, or IO occurs.
"""
from dataclasses import dataclass,replace
import math,struct
from . import binary32 as f
from .enemy_ai139 import (EnemyAIState139,EnemyAIResult139,PendingEnemyAI139,
    _put,_lt,_le,_max,_min,_trig139,_packet221,_sat,_packed,distance139,position_xyz139)
from .distance_map135 import update_distance_map135
from .ai_world135 import route_destination135
from .incoming139 import record432,word,guid,resolve_prefix139,resolve_source139
from .incoming_history139 import append_incoming_history
from .ordinary_family139_data import definition139,ENGLISH_NAMES139
from .enemy_ai_dead139 import (PhysicalNPCVector139,EnemyAIDeadResult139,
    PendingEnemyAIDead139,_default_destructor)

from .guardian_charge139 import (QueuedGuardianSkill139,GuardianChargeState139,EffectVector120139,DeferredGuardianVector56139,cast_guardian_charge139)
from .frame_systems139 import ScheduledSpellVector139
from .special_world139 import SpecialWorldState139,guardian_scalars139
from .special_world139_data import SPECIAL_DECLARATIONS139
from .guardian_ai139_data import GUARDIAN_PHASES139,ENGAGE_TEXT139

class PendingGuardianAI139(NotImplementedError):pass
GUARDIAN_ENGLISH139=dict(ENGLISH_NAMES139)|{d[1]:d[3]for d in SPECIAL_DECLARATIONS139}
def guardian_health_update139(row):
    values=tuple(min(f.MASK,max(0,math.ceil(f.to_float(word(row,o)))))for o in(288,292))
    #51773 wraps one values-update: outer count/transport, inner type/GUID,
    #one32bit mask word with ascending keys22 and28, then both values.
    return 169,(struct.pack('<IBB',1,0,0)+_packed(guid(row))+b'\1'+struct.pack('<I2I',0x10400000,*values)).hex()
def guardian_engage_notice139(row):
    name=GUARDIAN_ENGLISH139[word(row,284)].encode('utf8');text=ENGAGE_TEXT139.encode('utf8')
    payload=b'\x0c'+struct.pack('<IQI',0,guid(row),len(name)+1)+name+b'\0'+struct.pack('<QI',0,len(text)+1)+text+b'\0\0'
    return 150,payload.hex()
def _guardian_declaration(row):
    try:return next(d for d in SPECIAL_DECLARATIONS139 if d[1]==word(row,284))
    except StopIteration:raise PendingGuardianAI139('UnboundGuardian definition')from None
def _concurrent(flag):
    n=29 if flag<=2 else flag-3
    return n<=31 and bool((1<<n)&0xa0180006)
def _validate_guardian(row,owners):
    if any(word(row,o)!=f.MASK for o in(40,244)):raise PendingGuardianAI139('Currentspecial64family only')
    decl=_guardian_declaration(row);owner=owners.get(guid(row))
    if owner is None or owner.capacity!=3 or len(owner.timers_bits)!=3:raise PendingGuardianAI139('Real2372threeTimer owner required')
    if tuple(row[68:72])!=(None,)*4 or word(row,64)!=3 or word(row,72)!=3:raise PendingGuardianAI139('Physicaltimerpointerunknown; exactcapacity/count3')
    if word(row,96)!=decl[4]or any(word(row,o)!=decl[-2]for o in(76,84))or any(word(row,o)!=3 for o in(80,88)):raise PendingGuardianAI139('Actualdeclaration/header/sourceidentity')
    if row[424]!=1 or any(word(row,o)for o in(0,8,16,104,240,360,380,388,396,416,420)):raise PendingGuardianAI139('AlivefirstHPphase unstated/status-free source only')
    if row[108]not in(0,1):raise PendingGuardianAI139('KnownGuardianengagedflag')
    if word(row,288)!=word(row,292):raise PendingGuardianAI139('Guardian damage/HPphase transitions not yet admitted')

@dataclass(frozen=True)
class GuardianAIContext139:
    ai:EnemyAIState139
    special:SpecialWorldState139
    effects:EffectVector120139
    deferred:DeferredGuardianVector56139
    scheduled:ScheduledSpellVector139
    counter2356:int

@dataclass(frozen=True)
class GuardianAIResult139:
    context:GuardianAIContext139
    attacks:tuple
    motions:tuple
    packets:tuple
    queued_actions:tuple
    aggro_guids:tuple
    routing:tuple
    path_recomputed:bool


def _validate_family(row):
    if any(word(row,o)!=f.MASK for o in(40,64,244)):raise PendingEnemyAI139('Nonordinary AI family40/64/244')
    definition=definition139(word(row,284))
    if row[424]!=0 or definition.word(68)!=0:raise PendingEnemyAI139('Only bound ordinary nonelite classifications')
    if any(word(row,o)for o in(0,8,16,240,360,380,388,396,416,420)):raise PendingEnemyAI139('Dead/pending/status/fear/alternate producer not yet restored')
    for o in(120,124,128,132,136,140,288,292,296,300,304,308,316,320,324,328,332,336,340,344,348,352,404,408,412):
        part=row[o:o+4]
        if None not in part and(f.is_nan(word(row,o))or f.is_inf(word(row,o))):raise PendingEnemyAI139('Finite current139 AI domain')

def update_guardian_ai139(context,world):
    value=context.ai
    special=context.special
    timer_owners={o.guid:o for o in special.timer_owners}
    updated_timers=dict(timer_owners);queued=[];aggro=[]
    if not isinstance(value,EnemyAIState139):raise TypeError('Typed current139 AI state required')
    if value.mode2582 or value.phase2587!=1 or value.zone!=0:raise PendingEnemyAI139('Only local active Elwynn phase1')
    if world.flat_height_bits is not None or world.primary is not None:raise PendingEnemyAI139('Current canonical nonflat/no-primary world required')
    if value.incoming.items8!=()or value.incoming.modifiers36:raise PendingEnemyAI139('Explicit complete empty item/modifier callback owners required')
    if len(value.records432)>512:raise ValueError('NPC budget')
    rows=[list(record432(row))for row in value.records432]
    for row in rows:
        if word(row,64)==f.MASK:_validate_family(row)
        else:_validate_guardian(row,timer_owners)
    path=update_distance_map135(world.nav,value.player_xyz[:2],value.now_bits,previous=value.distance_map,updated_at_bits=value.distance_clock2372_bits)
    motions=[];attacks=[];routing=[];now=value.now_bits;player=value.player_xyz
    for unit_index,row in enumerate(rows):
        if _lt(now,word(row,408)):continue
        pos=position_xyz139(row,now);timer=f.sub(word(row,352),value.dt_bits);_put(row,352,timer);target=guid(row)
        if word(row,64)!=f.MASK:
            home_index=word(row,92)
            home=tuple(word(special.special40_storage[home_index],16+4*j)for j in range(3))if home_index<special.special_count else pos
            if row[108]==0:
                if word(row,288)!=word(row,292):raise PendingGuardianAI139('DamagedGuardian activation source not yet admitted')
                engaged=_le(distance139(pos,home),0x40400000)and _le(distance139(pos,player),0x41a00000)
                if engaged:row[108]=1;aggro.append(target)
                else:
                    if _lt(0,word(row,344))and _lt(now,f.add(word(row,340),word(row,344))):continue
                    if _le(distance139(pos,home),0x40000000):continue
                    speed=word(row,300)
                    if _lt(now,word(row,124)):speed=f.mul(speed,f.sub(0x3f800000,word(row,120)))
                    if _lt(now,word(row,412)):speed=f.mul(speed,0x3faccccd)
                    duration=f.div(distance139(pos,home),_max(speed,0x3f000000))
                    for j,v in enumerate(pos):_put(row,316+4*j,v)
                    for j,v in enumerate(home):_put(row,328+4*j,v)
                    _put(row,340,now);_put(row,344,duration);motions.append((target,pos,home,duration));continue
            elif not _le(distance139(home,player),f.from_float(97.5)):
                raise PendingGuardianAI139('ActualGuardian leash reset/timerreallocation source Pending')
            owner=updated_timers[target];timers=list(owner.timers_bits);decl=_guardian_declaration(row)
            header=bytes.fromhex(decl[5])
            if word(row,104)!=0:raise PendingGuardianAI139('ActualHPphase-bit transition Pending')
            ratio=f.div(word(row,288),_max(word(row,292),0x3f800000))
            for phase in GUARDIAN_PHASES139[decl[4]]:
                if _lt(ratio,struct.unpack_from('<I',bytes.fromhex(phase),8)[0]):raise PendingGuardianAI139('ActualHPphase threshold reached; not skipped')
            for ability_index,(clock,hx)in enumerate(zip(timers,decl[-1],strict=True)):
                clock=f.sub(clock,value.dt_bits);timers[ability_index]=clock
                raw=bytes.fromhex(hx)
                if not _le(clock,0):continue
                flag=raw[37];normalized=29 if flag<=2 else flag-3
                concurrent=normalized<=31 and bool((1<<normalized)&0xa0180006)
                if _lt(now,word(row,100))and not concurrent:continue
                if not concurrent and any(a.unit_index==unit_index and not _concurrent(a.raw40[37])for a in queued):continue
                timers[ability_index]=f.mul(struct.unpack_from('<I',raw,40)[0],0x3f333333 if _lt(word(row,288),f.mul(word(row,292),0x3e99999a))else 0x3f800000)
                queued.append(QueuedGuardianSkill139(unit_index,ability_index,decl[-2],raw[:40]))
            updated_timers[target]=replace(owner,timers_bits=tuple(timers))
        if _le(distance139(pos,player),word(row,308)):
            if _lt(0,word(row,344))and _lt(now,f.add(word(row,340),word(row,344))):
                for j,v in enumerate(pos):_put(row,316+4*j,v);_put(row,328+4*j,v)
                _put(row,340,now);_put(row,344,0);motions.append((target,pos,pos,0))
            if _le(timer,0)and _le(word(row,412),now):
                _put(row,352,word(row,304));weak=word(row,128)if _lt(now,word(row,132))else word(row,136)if _lt(now,word(row,140))else 0
                attacks.append((target,f.mul(word(row,296),f.sub(0x3f800000,weak))))
            continue
        if _lt(now,word(row,348)):continue
        angle=f.add(word(row,404),0x3e19999a);_put(row,404,angle)
        radius=_max(f.mul(word(row,308),0x3f4ccccd),0x3fc00000)
        # Ordinary non-ranged8=0 takes br2@6, bypassing the ranged circle ray.
        dest=(f.add(player[0],f.mul(radius,_trig139(angle,True))),f.add(player[1],f.mul(radius,_trig139(angle,False))),player[2]);length=distance139(pos,dest)
        if _lt(0x41600000,length):
            factor=f.div(0x41600000,length);dest=(f.add(pos[0],f.mul(f.sub(dest[0],pos[0]),factor)),f.add(pos[1],f.mul(f.sub(dest[1],pos[1]),factor)),pos[2])
        dest,route=route_destination135(world.nav,path.distance_map,pos,dest);routing.append((target,route))
        speed=word(row,300)
        if _lt(now,word(row,124)):speed=f.mul(speed,f.sub(0x3f800000,word(row,120)))
        if _lt(now,word(row,412)):speed=f.mul(speed,0x3faccccd)
        duration=f.div(distance139(pos,dest),_max(speed,0x3f000000))
        for j,v in enumerate(pos):_put(row,316+4*j,v)
        for j,v in enumerate(dest):_put(row,328+4*j,v)
        _put(row,340,now);_put(row,344,duration);_put(row,348,f.add(now,_min(_max(duration,0x3e800000),0x3f333333)))
        motions.append((target,pos,dest,duration))
    incoming=replace(value.incoming,now_bits=now,player_xy=player[:2],records432=tuple(tuple(r)for r in rows));history=value.history;fields=dict(value.player_fields)
    packets=[];seq=value.movement_sequence2412
    for target,start,end,duration in motions:
        seq=(seq+1)&f.MASK;packets.append(_packet221(world,target,start,end,duration,seq))
    for source,amount in attacks:
        #925 emits noncrit direct damage packet before full1076.
        shown=_sat(_max(f.mul(amount,f.sub(0x3f800000,incoming.armor1568_bits)),0x3f800000))
        packets.append((330,(struct.pack('<I',2)+_packed(source)+_packed(0)+struct.pack('<I',shown)+b'\1'+struct.pack('<IfI6I',0,float(shown),shown,0,0,1,0,0,0)).hex()))
        before=incoming;result=resolve_prefix139(incoming,amount,source_guid=source,contact_flag=1);incoming=result.state
        if result.history_required:
            resolved=resolve_source139(incoming.records432,source,english_names=GUARDIAN_ENGLISH139)
            history=append_incoming_history(history,now_bits=now,damage_bits=result.damage_bits,absorbed_bits=result.absorbed_bits,hp_after_prefix_bits=f.sub(before.hp1440_bits,result.damage_bits),maximum_hp_bits=incoming.maximum1536_bits,category=0,source_label=resolved.name,source_classification=resolved.classification)
            fields[22]=min(f.MASK,max(0,math.ceil(f.to_float(incoming.hp1440_bits))));fields[28]=min(f.MASK,max(0,math.ceil(f.to_float(incoming.maximum1536_bits))))
    charge=GuardianChargeState139(tuple(tuple(r)for r in rows),now,player,context.effects,context.deferred,context.scheduled,context.counter2356,seq)
    for action in queued:
        result=cast_guardian_charge139(charge,action,world)
        charge=result.state;packets.extend(result.packets)
    rows=[list(r)for r in charge.records432]
    for target in aggro:
        row=next(r for r in rows if guid(r)==target);decl=_guardian_declaration(row)
        scaled=replace(special,now_bits=now,player_xyz=player)
        hp,attack=guardian_scalars139(scaled,bytes.fromhex(decl[2]))
        previous=word(row,292)
        if _lt(previous,hp):_put(row,292,hp);_put(row,288,f.mul(hp,_min(_max(f.div(word(row,288),previous),0),0x3f800000)))
        _put(row,296,_max(word(row,296),attack))
        #Current925 emits these only after queued916 actions and the actual
        #16381/42922 refresh. Neither packet is moved to the firstrow loop.
        packets.extend((guardian_health_update139(row),guardian_engage_notice139(row)))
    state=replace(value,records432=tuple(tuple(r)for r in rows),incoming=replace(incoming,records432=tuple(tuple(r)for r in rows)),history=history,player_fields=tuple(sorted(fields.items())),distance_map=path.distance_map,distance_clock2372_bits=path.updated_at_bits,movement_sequence2412=charge.sequence2412)
    physical=tuple(tuple(r)for r in rows)+special.units432_storage[special.units_count:]
    special=replace(special,units432_storage=physical,units_count=len(rows),now_bits=now,player_xyz=player,timer_owners=tuple(updated_timers[o.guid]for o in special.timer_owners))
    result=GuardianAIContext139(state,special,charge.effects,charge.deferred,charge.scheduled,charge.counter2356)
    return GuardianAIResult139(result,tuple(attacks),tuple(motions),tuple(packets),tuple(queued),tuple(aggro),tuple(routing),path.recomputed)
