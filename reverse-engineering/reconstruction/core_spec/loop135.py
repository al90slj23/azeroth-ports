"""Independent clock and phase rules for fixed0.135.1 /0898d5e3.

These small state projections do not call the original game, perform its queued
commands, construct a run, or execute its scheduler. Unknown system effects are
returned explicitly. Inputs are already resolved states, not implicit defaults
for an unexamined live game.
"""
from dataclasses import dataclass
import struct

from . import binary32 as f32

VERSION = '0.135.1'
BUILD = '0898d5e3'
SOURCE_SHA256 = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'


def _uint(value, bits, label):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < 1 << bits:
        raise ValueError(f'{label} must be a u{bits}')
    return value


def float64_bits(value):
    return struct.unpack('<Q', struct.pack('<d', value))[0]


def float64_from_bits(bits):
    return struct.unpack('<d', struct.pack('<Q', _uint(bits, 64, 'binary64 bits')))[0]


@dataclass(frozen=True)
class ClockState:
    previous_marker: int
    previous_time_bits: int
    simulation_clock_bits: int
    game_discriminant: int
    mode: int
    phase: int
    global_phase: int


@dataclass(frozen=True)
class ClockProjection:
    previous_marker: int
    previous_time_bits: int
    simulation_clock_bits: int
    delta_bits: int
    enters_simulation: bool
    pending_effects: tuple[str, ...]


def project_tick_clock(state: ClockState, now_bits: int) -> ClockProjection:
    """Project tick880's wall clock and the guarded simulation-clock write.

    The caller must first execute/resolve the tick's incoming command phase.
    The original drains commands before the simulation gate; this function does
    not silently assume that a live incoming command queue is empty.
    """
    _uint(state.previous_marker, 64, 'previous marker')
    _uint(state.simulation_clock_bits, 32, 'simulation clock')
    _uint(state.game_discriminant, 64, 'game discriminant')
    for label in ('mode', 'phase', 'global_phase'):
        _uint(getattr(state, label), 8, label)
    previous = float64_from_bits(state.previous_time_bits)
    now = float64_from_bits(now_bits)
    delta = 0.0
    if state.previous_marker == 1:
        delta = now - previous  # binary64 operation precedes all comparisons.
        # Ordered comparisons are deliberate: a NaN difference survives.
        if delta < 0.0:
            delta = 0.0
        if delta > 0.1:
            delta = 0.1
    delta_bits = f32.from_float(delta)
    phase = state.phase if state.mode == 0 else state.global_phase
    running = state.game_discriminant != 2 and phase == 1
    clock = (f32.add(state.simulation_clock_bits, delta_bits)
             if running else state.simulation_clock_bits)
    return ClockProjection(1, now_bits, clock, delta_bits, running,
                           ('incoming_commands_must_already_be_resolved',
                            'original_simulation_and_post_tick_drains'))


@dataclass(frozen=True)
class PauseResult:
    phase: int
    changed: bool
    effects: tuple[str, ...]


def apply_pause_command(*, game_discriminant: int, mode: int, phase: int,
                        payload_byte: int) -> PauseResult:
    """Raw command tag7; payload+4 zero requests resume, other bytes pause."""
    _uint(game_discriminant, 64, 'game discriminant')
    for value, label in ((mode, 'mode'), (phase, 'phase'), (payload_byte, 'payload')):
        _uint(value, 8, label)
    if game_discriminant == 2 or mode & 1:
        return PauseResult(phase, False, ())
    if payload_byte != 0 and phase == 1:
        return PauseResult(3, True, ('stop_movement35514', 'paused_notification'))
    if payload_byte == 0 and phase == 3:
        return PauseResult(1, True, ('resume_movement25472', 'unpaused_notification'))
    return PauseResult(phase, False, ())


def aggregate_party_phase(global_phase: int, player_phases: tuple[int, ...]) -> int:
    """The terminal aggregation block reached during a multi-state running tick.

    This is not an unconditional reducer for a menu/waiting session. The caller
    must establish that the original multi-state running block is reached.
    """
    _uint(global_phase, 8, 'global phase')
    for phase in player_phases:
        _uint(phase, 8, 'player phase')
    if any(phase in (1, 2) for phase in player_phases):
        return global_phase
    return 5 if 5 in player_phases else 4


@dataclass(frozen=True)
class EndlessResult:
    phase: int
    endless_flag: int
    deadline_bits: int
    effects: tuple[str, ...]


def continue_endless(*, phase: int, endless_flag: int,
                     simulation_clock_bits: int, previous_deadline_bits: int) -> EndlessResult:
    """Project39430's phase/flag/next300-second deadline, not its messages."""
    _uint(phase, 8, 'phase'); _uint(endless_flag, 8, 'endless flag')
    _uint(simulation_clock_bits, 32, 'simulation clock')
    _uint(previous_deadline_bits, 32, 'previous deadline')
    if phase != 5:
        return EndlessResult(phase, endless_flag, previous_deadline_bits, ())
    return EndlessResult(1, 1, f32.add(simulation_clock_bits, 0x43960000),
                         ('resume_packet', 'Endless_text_if_previous_flag_bit0_clear'))


def victory_phase(*, phase: int, required_field400: int, endless_flag: int) -> PauseResult:
    """Project49037's visible guard; field400's complete producer is unknown."""
    _uint(phase, 8, 'phase'); _uint(required_field400, 32, 'field400')
    _uint(endless_flag, 8, 'endless flag')
    if required_field400 != 0 and phase == 1 and endless_flag & 1 == 0:
        return PauseResult(5, True, ('stop_movement17119', 'victory_packets_and_notification'))
    return PauseResult(phase, False, ())


SINGLE_RUNNING_TAIL = (2088, 916, 975, 1754, 3757, 915, 38007,
                       2602, 921, 2862, 2573, 947, 2376, 49037)
CONDITIONALLY_SKIPPED_BY_FIELD2579 = (947, 2376)
