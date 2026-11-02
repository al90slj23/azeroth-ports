"""Ordered ordinary incoming queue over explicit same-run owners.

This composes recovered1073 prefix/history, proved inert callbacks and the
mode0/no-revival death consumer. Physical queue headers/allocation addresses
remain unknown; semantic stop packets and defeat JSON are produced exactly.
It does not plan units, discard post-death events or implement910/1453 queues.
"""
from dataclasses import dataclass, replace
import struct

from . import binary32 as f
from .ai135 import unit_position
from .cast_catalogue135 import definition
from .incoming_callbacks135 import (
    CallbackVector135, IncomingCallbacksInput135, prove_post_history_callbacks135,
)
from .player_death135 import defeat_notification135
from .run_ledger135 import RunLedger135, record_incoming_prefix135
from .run_summary135 import summary_counters135
from .terminal_transition135 import COUNTER_KEYS, CLASSES, RACES, ZONES
from .world_motion_stop135 import WorldMotionStopInput135, stop_world_motion135


class UnknownRunIncoming135(NotImplementedError):
    pass


@dataclass(frozen=True)
class DefeatSummary135:
    """Only fields consumed by1938; unused queue headers are not invented."""
    now_bits: int
    counters: tuple
    damage984_f64_bits: int
    taken992_f64_bits: int
    class_byte: int
    race_byte: int
    region_index: int
    hero: str
    left2567: int
    localization_profile: str

    def __post_init__(self):
        if len(self.counters)!=len(COUNTER_KEYS)or {k for k,v in self.counters}!={k for k,_ in COUNTER_KEYS}:
            raise ValueError('All seven event/progression/currency-maintained summary counters required')
        for value in (self.now_bits,*(v for k,v in self.counters)):
            if type(value)is not int or not 0<=value<1<<32:raise ValueError('Explicit summary u32 required')
        for value in (self.damage984_f64_bits,self.taken992_f64_bits):
            if type(value)is not int or not 0<=value<1<<64:raise ValueError('Explicit total f64 bits required')
        if self.class_byte not in CLASSES or self.race_byte not in RACES or not 0<=self.region_index<len(ZONES):
            raise UnknownRunIncoming135('Summary labels require their actual class/race/map producer')
        if type(self.hero)is not str or type(self.left2567)is not int or not 0<=self.left2567<256:
            raise ValueError('Explicit profile hero and left byte required')
        self.hero.encode('utf-8')


@dataclass(frozen=True)
class RunIncomingDrain135:
    incoming: object
    ledger: RunLedger135
    unit_storage: tuple
    records: tuple
    claims_storage: tuple
    movement_sequence2412: int
    packets: tuple
    notifications: tuple
    paused408: int|None
    paused412_bits: int|None
    physical_queue_pending: tuple


def _f64_bits(value):
    return struct.unpack('<Q',struct.pack('<d',value))[0]


def drain_run_incoming135(state, incoming, attacks, *, records, unit_storage,
        movement_sequence2412, auxiliary_owner):
    """921's queued ordinary hits, after all unit owners have been planned.

    Each actual entry guard is executed even after phase becomes4. The later
    910/1453 queues are the controller's responsibility and are not replaced
    by a blanket phase guard. A missing source/auxiliary owner is a boundary.
    """
    ledger=state.run_ledger
    if not isinstance(ledger,RunLedger135)or state.player_sources is None:
        raise UnknownRunIncoming135('Full live owner and explicit same-run ledger required')
    level=state.collection.level;maximum=dict(level.derived_bits)[1536]
    if state.special_mode2582 or level.stats.flag2574 or state.collection.currency.local_peer:
        raise UnknownRunIncoming135('Only the restored local mode0 ordinary incoming drain is admitted')
    records=tuple(records);unit_storage=tuple(unit_storage)
    if tuple(unit_storage[:len(records)])!=records:
        raise ValueError('Planned records and full canonical backing disagree')
    current=replace(incoming,units=tuple(unit_position(row)for row in records))
    claims=state.tail.claims88_storage;sequence=movement_sequence2412
    packets=[];notifications=[];pending=[];paused=state.paused408;pause_time=state.paused412_bits
    for guid,amount in attacks:
        before=current
        recorded=record_incoming_prefix135(ledger,before,amount,guid,
            source_records=records,maximum_hp_bits=maximum,category=0)
        ledger=recorded.ledger;prefix=recorded.prefix;current=prefix.state
        if prefix.status=='returned':
            continue
        # Entry guards above do not consume the shield path. A reached
        # positive-shield prefix needs1202/physical live-owner continuation.
        if f.to_float(before.shield_1532_bits)>0:
            raise UnknownRunIncoming135('Shield-break/reserve callbacks need their full live-owner adapter')
        hp_at_history=f.sub(before.hp_1528_bits,prefix.amount_bits)
        live=state.player_sources.live
        proof=prove_post_history_callbacks135(IncomingCallbacksInput135(
            before.now_bits,hp_at_history,guid,1,before.phase_2579,amount,
            CallbackVector135(32,live.count,live.storage,live.capacity),
            ledger.callback_sources.items8,ledger.callback_sources.modifiers36))
        if not proof.callbacks_complete or proof.hp_before_minimum_one1440_bits!=hp_at_history:
            raise UnknownRunIncoming135('Actual post-history HP callback continuation is unresolved')
        # resolve_incoming_prefix has already applied the same minimum-one
        # clamp. The proved callbacks preserve its pre-clamp HP value.
        if not f.to_float(current.hp_1528_bits)<=0:
            continue
        #1073 compares definition+0 to12, not the dispatch byte at+84.
        innate_kind=definition(state.racial.definition_pointer).effect_tag
        if innate_kind==12 and not f.to_float(state.racial.remaining_cooldown_bits)>0:
            raise UnknownRunIncoming135('An available intrinsic12 can attempt resurrection922')
        if ledger.callback_sources.modifiers36.count or ledger.lives1632:
            raise UnknownRunIncoming135('Modifier31/lives revival requires its actual continuation')
        if auxiliary_owner is None:
            raise UnknownRunIncoming135('G656 auxiliary motion requires its constructor/event-maintained owner')
        # This input consumes the real G656-domain owner, never the unrelated
        # same-stride secondary-hit vector at G1856.
        aux=auxiliary_owner
        stopped=stop_world_motion135(WorldMotionStopInput135(
            current.now_bits,sequence,unit_storage,len(records),
            aux.storage112,aux.count664,claims,state.tail.claims88_count,None,None),state.world)
        unit_storage=stopped.state.units_storage;records=unit_storage[:len(records)]
        ledger=replace(ledger,auxiliary_motion=replace(aux,storage112=stopped.state.auxiliary_storage))
        claims=stopped.state.claims_storage;sequence=stopped.state.movement_sequence2412
        packets.extend(stopped.packets)
        pending.extend(stopped.pending)
        summary=DefeatSummary135(current.now_bits,
            summary_counters135(ledger.counters,level,state.collection.currency),
            _f64_bits(state.outgoing_total),_f64_bits(current.incoming_total_992),
            level.stats.class_byte,level.stats.race_byte,state.zone,
            ledger.hero.text,ledger.left2567,ledger.localization_profile)
        notifications.append(defeat_notification135(summary,history=ledger.history))
        paused=1;pause_time=current.now_bits
        current=replace(current,hp_1528_bits=0,phase_2579=4,
            units=tuple(unit_position(row)for row in records))
    return RunIncomingDrain135(current,ledger,unit_storage,records,claims,sequence,
        tuple(packets),tuple(notifications),paused,pause_time,tuple(dict.fromkeys(pending)))
