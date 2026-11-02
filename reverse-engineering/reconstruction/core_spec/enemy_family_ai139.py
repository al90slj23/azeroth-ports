"""Current139925 ordinary tag0/Kobold+Wolf branch and stable corpse phase.

The numeric AI rules use actual row296/300/304/308, with declaration-checked
families and current1076 English identities. Full source records stay intact;
no pointer replacement, NPC filtering from physical storage, or IO occurs.
"""
from dataclasses import replace
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

def _validate_family(row):
    if any(word(row,o)!=f.MASK for o in(40,64,244)):raise PendingEnemyAI139('Nonordinary AI family40/64/244')
    definition=definition139(word(row,284))
    if row[424]!=0 or definition.word(68)!=0:raise PendingEnemyAI139('Only bound ordinary nonelite classifications')
    if any(word(row,o)for o in(0,8,16,240,360,380,388,396,416,420)):raise PendingEnemyAI139('Dead/pending/status/fear/alternate producer not yet restored')
    for o in(120,124,128,132,136,140,288,292,296,300,304,308,316,320,324,328,332,336,340,344,348,352,404,408,412):
        part=row[o:o+4]
        if None not in part and(f.is_nan(word(row,o))or f.is_inf(word(row,o))):raise PendingEnemyAI139('Finite current139 AI domain')

def update_enemy_family_branch139(value,world):
    if not isinstance(value,EnemyAIState139):raise TypeError('Typed current139 AI state required')
    if value.mode2582 or value.phase2587!=1 or value.zone!=0:raise PendingEnemyAI139('Only local active Elwynn phase1')
    if world.flat_height_bits is not None or world.primary is not None:raise PendingEnemyAI139('Current canonical nonflat/no-primary world required')
    if value.incoming.items8!=()or value.incoming.modifiers36:raise PendingEnemyAI139('Explicit complete empty item/modifier callback owners required')
    if len(value.records432)>512:raise ValueError('NPC budget')
    rows=[list(record432(row))for row in value.records432]
    for row in rows:_validate_family(row)
    path=update_distance_map135(world.nav,value.player_xyz[:2],value.now_bits,previous=value.distance_map,updated_at_bits=value.distance_clock2372_bits)
    motions=[];attacks=[];routing=[];now=value.now_bits;player=value.player_xyz
    for row in rows:
        if _lt(now,word(row,408)):continue
        pos=position_xyz139(row,now);timer=f.sub(word(row,352),value.dt_bits);_put(row,352,timer);target=guid(row)
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
            resolved=resolve_source139(incoming.records432,source,english_names=ENGLISH_NAMES139)
            history=append_incoming_history(history,now_bits=now,damage_bits=result.damage_bits,absorbed_bits=result.absorbed_bits,hp_after_prefix_bits=f.sub(before.hp1440_bits,result.damage_bits),maximum_hp_bits=incoming.maximum1536_bits,category=0,source_label=resolved.name,source_classification=resolved.classification)
            fields[22]=min(f.MASK,max(0,math.ceil(f.to_float(incoming.hp1440_bits))));fields[28]=min(f.MASK,max(0,math.ceil(f.to_float(incoming.maximum1536_bits))))
    state=replace(value,records432=tuple(tuple(r)for r in rows),incoming=incoming,history=history,player_fields=tuple(sorted(fields.items())),distance_map=path.distance_map,distance_clock2372_bits=path.updated_at_bits,movement_sequence2412=seq)
    return EnemyAIResult139(state,tuple(attacks),tuple(motions),tuple(packets),tuple(routing),path.recomputed)


def update_enemy_family139(ai_state,units,world):
    if not isinstance(ai_state,EnemyAIState139)or not isinstance(units,PhysicalNPCVector139):raise TypeError('Actual AI owner and physical NPC vector required')
    if ai_state.records432!=units.active or ai_state.incoming.records432!=units.active:raise ValueError('Actual count-domain projections must include retained dead rows')
    if f.is_nan(ai_state.now_bits)or f.is_inf(ai_state.now_bits)or f.is_nan(ai_state.dt_bits)or f.is_inf(ai_state.dt_bits)or f.to_float(ai_state.dt_bits)<0:raise ValueError('Finite explicit925 clock/delta required')
    ids=tuple(guid(row)for row in units.active)
    if len(set(ids))!=len(ids):raise PendingEnemyAIDead139('DuplicateGUID destructor/removal source not admitted')
    # Nearby damage scaling counts all NPCs in1076. Filtering the marker0
    #sub-loop is valid only in this explicit zero-nearby modifier domain.
    if ai_state.incoming.nearby1624_bits!=0:raise PendingEnemyAIDead139('Positive nearby1624 requires full-roster callback view')
    live_indices=[];pending=[];proofs=[]
    for index,row in enumerate(units.active):
        record432(row);marker=word(row,0)
        if marker==0:live_indices.append(index);continue
        if marker!=1:raise PendingEnemyAIDead139('Only actual913 marker1 corpse source')
        if word(row,40)!=f.MASK or row[424]!=0:raise PendingEnemyAIDead139('Nonordinary corpse family pending')
        definition139(word(row,284))
        _default_destructor(row);death=word(row,4)
        if f.is_nan(death)or f.is_inf(death):raise PendingEnemyAIDead139('Finite actual deathTime required')
        elapsed=f.sub(ai_state.now_bits,death);expired=f.to_float(elapsed)>f.to_float(0x3f99999a)
        proofs.append((ids[index],death,elapsed,expired))
        if expired:pending.append(ids[index])
    #This is an explicit execution view of925's marker0 branch, not a new
    #Game vector and not a claim that retained corpses have been deleted.
    live_rows=tuple(units.storage[i]for i in live_indices)
    branch=replace(ai_state,records432=live_rows,incoming=replace(ai_state.incoming,records432=live_rows))
    updated=update_enemy_family_branch139(branch,world)
    if len(updated.state.records432)!=len(live_indices):raise ValueError('Frozen marker0 branch changed physical membership')
    storage=list(units.storage)
    for index,row in zip(live_indices,updated.state.records432,strict=True):storage[index]=row
    before_removal=tuple(storage);count=units.count;packets=list(updated.packets)
    for target in pending:
        index=next((i for i in range(count)if guid(storage[i])==target),None)
        if index is None:raise ValueError('Queued actual corpse GUID must still be present')
        _default_destructor(storage[index])
        #Current40215 stable-forward copies all432 bytes. The final slot is
        #not cleared, and capacity is unchanged even when count becomes0.
        for i in range(index,count-1):storage[i]=tuple(storage[i+1])
        count-=1
    packets=[(170,struct.pack('<Q',target).hex())for target in pending]+packets
    vector=PhysicalNPCVector139(tuple(storage),count)
    ai=replace(updated.state,records432=vector.active,incoming=replace(updated.state.incoming,records432=vector.active))
    return EnemyAIDeadResult139(ai,vector,before_removal,tuple(pending),tuple(packets),updated.attacks,updated.motions,updated.routing,updated.path_recomputed,tuple(proofs))
