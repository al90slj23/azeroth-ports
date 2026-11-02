"""Current139 real Thunder slow owners -> complete ordinary925 component.

This adapter carries the actual selected live/Aura/racial/owned owners. Only
player placement and clock are controls. The frozen AI implementation already
has the current81682 slow speed formula; this adds its real2189 producer chain,
not a second source of fabricated NPC statuses or a full-game scheduler.
"""
from dataclasses import dataclass,replace
from . import binary32 as f
from .enemy_ai139 import EnemyAIState139,update_enemy_ai139
from .incoming139 import IncomingState139,word as _word,guid
from .incoming_history139 import from_raw_storage
from .player_update139 import PlayerUpdateState139
from .thunder_clap139 import ThunderClapResult139


class PendingEnemyAIStatus139(NotImplementedError):pass


def word(row,offset):return _word(tuple(row),offset)


@dataclass(frozen=True)
class InheritedGuard12View139:
    """Only1076's declared kind/expiry metadata; unread payload stays unknown."""
    kind:int
    spell_id:int
    expires_bits:int
    value_bits:None=None


@dataclass(frozen=True)
class EnemyAIStatusState139:
    player:PlayerUpdateState139
    ai:EnemyAIState139
    thunder_state:object
    slowed_guids:tuple


@dataclass(frozen=True)
class EnemyAIStatusResult139:
    state:EnemyAIStatusState139
    attacks:tuple
    motions:tuple
    packets:tuple
    routing:tuple
    path_recomputed:bool
    motion_speed_proofs:tuple
    active_guard12:bool


def from_thunder_slow139(player,cast,player_xyz):
    if not isinstance(player,PlayerUpdateState139)or not isinstance(cast,ThunderClapResult139):raise TypeError('Actual selected player and real Thunder result required')
    g=player.growth;s=cast.state
    if g.source_counts!=(0,)*7 or g.phase2587!=1 or g.mode2582 or g.flags2576 or len(g.owned_records80)!=2:raise PendingEnemyAIStatus139('Only inherited active default two-owned source')
    if any((player.pool1444_bits,player.pool1448_bits,player.conditional1344,player.conditional1348_bits,player.pool764_bits)):raise PendingEnemyAIStatus139('Nonempty shield/reserve source')
    if tuple(word(r,0)for r in g.owned_records80)!=(5882740,5882916):raise PendingEnemyAIStatus139('Actual cleave/Thunder owned records required')
    if any(word(row,0)for row in s.records432)or len(s.records432)!=4:raise PendingEnemyAIStatus139('Nonfatal actual fourNPC slow prefix only')
    if tuple(guid(row)for row in g.units432_cells)!=tuple(guid(row)for row in s.records432):raise PendingEnemyAIStatus139('NPC owners changed')
    slowed=tuple(guid(row)for row in s.records432 if word(row,120)==0x3f000000 and word(row,124)==0x40400000)
    if not cast.success or not slowed or s.now_bits!=0:raise PendingEnemyAIStatus139('Real t0 Thunder slow producer required')
    for row in s.records432:
        if word(row,376)or word(row,356):raise PendingEnemyAIStatus139('Nonempty slow spell/effect49 family')
    live=[]
    for row in player.live.active:
        if word(row,8)!=12 or word(row,20)!=1020 or word(row,24)!=0x3f800000:raise PendingEnemyAIStatus139('Only actual selected1020 guard source')
        #Never read or fill selected kind12 bytes12..19.
        live.append(InheritedGuard12View139(12,1020,word(row,24)))
    if len(live)!=1:raise PendingEnemyAIStatus139('Actual inherited selected live12 must be retained')
    growth=replace(g,units432_cells=s.records432,rng_words=s.rng_words,current_hp_bits=s.player_hp1440_bits,now_bits=s.now_bits)
    player=replace(player,growth=growth,spell_sets=cast.spell_sets,player_xyz=tuple(player_xyz))
    incoming=IncomingState139(1,0,0,0,growth.current_hp_bits,growth.derived_bits[1536],growth.derived_bits[1568],growth.derived_bits[1572],nearby1624_bits=growth.derived_bits[1624],items8=(),last_hit1652_bits=player.last_hit1652_bits,player_xy=tuple(player_xyz[:2]),records432=s.records432,live32=tuple(live))
    ai=EnemyAIState139(s.records432,0,0,tuple(player_xyz),incoming,from_raw_storage((),0,0),tuple(sorted(growth.player_fields.items())),movement_sequence2412=s.movement_sequence2412)
    return EnemyAIStatusState139(player,ai,s,slowed)


def update_enemy_ai_status139(value,now_bits,dt_bits,player_xyz,world,*,english_names):
    if not isinstance(value,EnemyAIStatusState139):raise TypeError('Typed real slow-chain state required')
    if f.to_float(now_bits)<=f.to_float(value.ai.now_bits)or f.sub(now_bits,value.ai.now_bits)!=dt_bits:raise ValueError('Explicit increasing exact clock/dt controls')
    ai=replace(value.ai,now_bits=now_bits,dt_bits=dt_bits,player_xyz=tuple(player_xyz));result=update_enemy_ai139(ai,world,english_names=english_names);after=result.state
    proofs=[]
    for target,start,end,duration in result.motions:
        if not f.to_float(duration)>0:continue
        row=next(row for row in value.ai.records432 if guid(row)==target);speed=word(row,300);active=f.to_float(now_bits)<f.to_float(word(row,124))
        if active:speed=f.mul(speed,f.sub(0x3f800000,word(row,120)))
        if f.to_float(now_bits)<f.to_float(word(row,412)):speed=f.mul(speed,0x3faccccd)
        proofs.append((target,word(row,120),word(row,124),active,speed,duration))
    growth=replace(value.player.growth,units432_cells=after.records432,current_hp_bits=after.incoming.hp1440_bits,now_bits=now_bits,player_fields=dict(after.player_fields))
    player=replace(value.player,growth=growth,player_xyz=tuple(player_xyz),last_hit1652_bits=after.incoming.last_hit1652_bits)
    thunder=replace(value.thunder_state,records432=after.records432,now_bits=now_bits,player_hp1440_bits=after.incoming.hp1440_bits,movement_sequence2412=after.movement_sequence2412)
    state=replace(value,player=player,ai=after,thunder_state=thunder)
    guard=any(b.kind==12 and f.to_float(now_bits)<f.to_float(b.expires_bits)for b in after.incoming.live32)
    return EnemyAIStatusResult139(state,result.attacks,result.motions,result.packets,result.routing,result.path_recomputed,tuple(proofs),guard)
