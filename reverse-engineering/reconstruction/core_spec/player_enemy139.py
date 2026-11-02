"""Current139 consecutive2123→925 components, explicit432B physical owner.

This is the actual relative order within884, not a full884 replacement. Other
intervening and following stages remain outside the component contract.
"""
from dataclasses import dataclass,replace
from . import binary32 as f
from .player_autocast139 import PlayerAutocastState139,update_player_autocast139
from .enemy_ai139 import EnemyAIState139
from .enemy_ai_dead139 import PhysicalNPCVector139 as NPCVector139,update_enemy_ai_dead139
from .incoming139 import IncomingState139,Buff139,word,guid
from .incoming_history139 import IncomingHistory139
from .distance_map135 import ProducedDistanceMap135


class PendingPlayerEnemy139(NotImplementedError):pass


@dataclass(frozen=True)
class PlayerEnemyState139:
    actor:PlayerAutocastState139
    units:NPCVector139
    incoming:IncomingState139
    history:IncomingHistory139
    distance_map:ProducedDistanceMap135|None
    distance_clock2372_bits:int

    def __post_init__(self):
        if self.actor.damage.records432!=self.units.active:raise ValueError('Physical and logical NPC owners disagree')
        if self.actor.player.growth.units432_cells!=self.units.active:raise ValueError('Growth NPC owner mismatch')


def _incoming_after_player(state):
    p=state.actor.player;g=p.growth
    live=tuple(Buff139(word(r,8),None if word(r,8)==12 else word(r,12),word(r,20),word(r,24))for r in p.live.active)
    return replace(state.incoming,now_bits=g.now_bits,hp1440_bits=g.current_hp_bits,
        maximum1536_bits=g.derived_bits[1536],armor1568_bits=g.derived_bits[1568],
        armor_cap1572_bits=g.derived_bits[1572],nearby1624_bits=g.derived_bits[1624],
        last_hit1652_bits=p.last_hit1652_bits,player_xy=p.player_xyz[:2],
        records432=state.units.active,live32=live)


@dataclass(frozen=True)
class PlayerEnemyResult139:
    state:PlayerEnemyState139
    player_result:object
    ai_result:object
    ai_before_removal:tuple
    removed_guids:tuple
    packets:tuple


def update_player_enemy139(state,now,dt,world):
    """Full2123 then full925 behavior, retaining dead432 and strict>1.2 expiry."""
    if not isinstance(state,PlayerEnemyState139):raise TypeError('Typed complete owner required')
    player=update_player_autocast139(state.actor,now,dt,world)
    units=NPCVector139(tuple(player.state.damage.records432)+state.units.storage[state.units.count:],state.units.count)
    state=replace(state,actor=player.state,units=units)
    incoming=_incoming_after_player(state)
    ai_state=EnemyAIState139(units.active,now,dt,player.state.player.player_xyz,
        incoming,state.history,tuple(player.state.player.growth.player_fields.items()),
        player.state.damage.movement_sequence2412,state.distance_map,state.distance_clock2372_bits)
    ai_result=update_enemy_ai_dead139(ai_state,units,world,english_names={5830904:'Kobold Vermin'})
    ai=ai_result.ai;units=ai_result.units;incoming=ai.incoming
    p=player.state.player;g=replace(p.growth,units432_cells=units.active,
        current_hp_bits=incoming.hp1440_bits,player_fields=dict(ai.player_fields))
    p=replace(p,growth=g,last_hit1652_bits=incoming.last_hit1652_bits)
    d=replace(player.state.damage,records432=units.active,player_hp1440_bits=incoming.hp1440_bits,
        movement_sequence2412=ai.movement_sequence2412)
    actor=replace(player.state,player=p,damage=d)
    result=PlayerEnemyState139(actor,units,incoming,ai.history,ai.distance_map,ai.distance_clock2372_bits)
    return PlayerEnemyResult139(result,player,ai_result,ai_result.before_removal,
        ai_result.removed_guids,player.packets+ai_result.packets)
