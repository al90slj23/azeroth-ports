"""New2123 adapter admitting actual hurt HP with default regeneration.

Frozen player_update139 remains unchanged. Expiry/Aura/racial producers and
the quiet1238 scheduler are composed as their actual dependencies; near owned
success/basic attacks remain for a later auto-loop composition.
"""
from dataclasses import dataclass,replace
from . import binary32 as f
from .player_update139 import (PlayerUpdateState139,LiveVector139,
    PendingPlayerUpdate139,word139,_uint,_replace_live,recalculate_player139,
    _callback139,_minnum,tick_default_owned139)
from .healing139 import (DefaultHealingSources139,HealingLedger139,
    regenerate_player139)


@dataclass(frozen=True)
class PlayerRegenerationResult139:
    state: PlayerUpdateState139
    healing: HealingLedger139
    heal_events: tuple
    expired_spells: tuple
    retained_source_indices: tuple
    expiry_recalculate1542_called: bool
    expiry_sync1173_called: bool
    regen_request_bits: int
    regen_accounted_bits: int
    packets: tuple
    events: tuple


def update_player_regeneration139(state,healing,now_bits,dt_bits,*,
                                  sync_aura139,cast_perception139):
    if not isinstance(state,PlayerUpdateState139) or not isinstance(healing,HealingLedger139):
        raise TypeError('Actual inherited player and healing owners required')
    for v in(now_bits,dt_bits):
        _uint(v)
        if f.is_nan(v) or f.is_inf(v):
            raise PendingPlayerUpdate139('Finite actual clock/delta required')
    if f.to_float(dt_bits)<0:
        raise PendingPlayerUpdate139('Nonnegative actual clock delta')
    if any((state.conditional1344,state.conditional1348_bits,state.pool1444_bits,
            state.pool1448_bits,state.pool764_bits)):
        raise PendingPlayerUpdate139('Nonempty shield/pool source not covered')
    state=replace(state,growth=replace(state.growth,now_bits=now_bits));expired=[]
    for row in state.live.active:
        kind,spell=word139(row,8),word139(row,20)
        if not(kind==12 and spell==1020 or kind==8 and spell==20600):
            raise PendingPlayerUpdate139('Other live source not restored')
        if word139(row,28)!=0:
            raise PendingPlayerUpdate139('Nonempty periodic remaining budget')
        if f.to_float(now_bits)>=f.to_float(word139(row,24)):
            expired.append(spell)
    packets=[];events=[];retained=tuple(range(state.live.count))
    if expired:
        rows=list(state.live.storage)
        retained=tuple(j for j,row in enumerate(state.live.active)
            if f.to_float(now_bits)<f.to_float(word139(row,24)))
        for j,i in enumerate(retained):rows[j]=state.live.storage[i]
        state=_replace_live(state,LiveVector139(tuple(rows),len(retained)))
        state=recalculate_player139(state)
        state,value=_callback139(state,sync_aura139,'Aura1173')
        packets.extend(value['packets']);events.append(('expire',tuple(expired),'1542','1173'))
    state=replace(state,pool1448_bits=_minnum(state.pool1444_bits,state.pool1448_bits))
    g=state.growth;sources=DefaultHealingSources139(1,g.source_counts)
    heal=regenerate_player139(g.current_hp_bits,g.derived_bits[1536],
        g.derived_bits[1576],g.derived_bits[1620],state.last_hit1652_bits,
        now_bits,dt_bits,healing,sources,heal_gate387=state.heal_gate387)
    fields=dict(g.player_fields);fields.update(heal.key_writes)
    state=replace(state,growth=replace(g,current_hp_bits=heal.hp_bits,player_fields=fields))
    events.append(('regen',heal.request_bits,heal.actual_delta_bits,heal.accounted_bits,'1466'))
    state,more,owned=tick_default_owned139(state,dt_bits,cast_perception139=cast_perception139)
    packets.extend(more);events.extend(owned)
    return PlayerRegenerationResult139(state,heal.ledger,heal.events,tuple(expired),
        retained,bool(expired),bool(expired),heal.request_bits,heal.accounted_bits,
        tuple(packets),tuple(events))
