"""Current925 corpse phase emits170 before deferred motion221/attack330.

V1's numeric/physical rules are retained. Its144 isolated fixtures did not
co-occur with motion or attacks at removal; real consecutive components exposed
the packet-phase error. No old evidence or source is rewritten by this version.
"""
from dataclasses import replace
import struct
from .enemy_ai_dead139 import (
    PhysicalNPCVector139,EnemyAIDeadResult139,PendingEnemyAIDead139,
    update_enemy_ai_dead139)


def update_enemy_ai_dead139_v2(ai_state,units,world,*,english_names):
    result=update_enemy_ai_dead139(ai_state,units,world,english_names=english_names)
    if not result.removed_guids:return result
    despawns=tuple((170,struct.pack('<Q',target).hex())for target in result.removed_guids)
    if result.packets[-len(despawns):]!=despawns:raise ValueError('Legacy phase suffix disagrees with exact queued GUIDs')
    deferred=result.packets[:-len(despawns)]
    if any(packet[0]not in(221,330)for packet in deferred):raise PendingEnemyAIDead139('Unrestored deferred925 packet phase')
    #Current925 first consumes queued40215+170, then emits the deferred
    #motion/attack vectors. Preserve both phase orders; never sort packets.
    return replace(result,packets=despawns+deferred)
