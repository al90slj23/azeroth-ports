"""Current925 marker1 lifetime and40215 stable Vec432 removal.

Physical storage/count and the read-only branch projection are distinct. Dead
rows stay in the real count domain until f32(now-deathTime)>f32(1.2); only the
current925 marker0 sub-loop is delegated to frozen ordinary AI. Complete432B
rows, including allocator-unwritten None cells, move and persist in staleTail.
"""
from dataclasses import dataclass,replace
import struct
from . import binary32 as f
from .enemy_ai139 import EnemyAIState139,update_enemy_ai139
from .incoming139 import record432,word,guid


class PendingEnemyAIDead139(NotImplementedError):pass


@dataclass(frozen=True)
class PhysicalNPCVector139:
    storage:tuple
    count:int

    def __post_init__(self):
        if type(self.storage)is not tuple or type(self.count)is not int or not 0<=self.count<=len(self.storage)<=512:raise ValueError('Bounded physical432 vector required')
        for row in self.storage:
            if type(row)is not tuple or len(row)!=432 or any(v is not None and(type(v)is not int or not 0<=v<256)for v in row):raise ValueError('Explicit432-byte known/None rows required')

    @property
    def capacity(self):return len(self.storage)

    @property
    def active(self):return self.storage[:self.count]


@dataclass(frozen=True)
class EnemyAIDeadResult139:
    ai:EnemyAIState139
    units:PhysicalNPCVector139
    before_removal:tuple
    removed_guids:tuple
    packets:tuple
    attacks:tuple
    motions:tuple
    routing:tuple
    path_recomputed:bool
    lifetime_proofs:tuple


def _default_destructor(row):
    #40215 reads64/244 first, then232. Their skipped payload pointers stay
    #unknown; no zero allocation or invented free operation is introduced.
    if word(row,64)!=f.MASK or word(row,244)!=f.MASK or word(row,232)!=0:raise PendingEnemyAIDead139('Nonempty destructor owners64/232/244 not restored')


def update_enemy_ai_dead139(ai_state,units,world,*,english_names):
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
        if word(row,40)!=f.MASK or word(row,284)!=5830904 or row[424]!=0:raise PendingEnemyAIDead139('Nondefault corpse family pending')
        _default_destructor(row);death=word(row,4)
        if f.is_nan(death)or f.is_inf(death):raise PendingEnemyAIDead139('Finite actual deathTime required')
        elapsed=f.sub(ai_state.now_bits,death);expired=f.to_float(elapsed)>f.to_float(0x3f99999a)
        proofs.append((ids[index],death,elapsed,expired))
        if expired:pending.append(ids[index])
    #This is an explicit execution view of925's marker0 branch, not a new
    #Game vector and not a claim that retained corpses have been deleted.
    live_rows=tuple(units.storage[i]for i in live_indices)
    branch=replace(ai_state,records432=live_rows,incoming=replace(ai_state.incoming,records432=live_rows))
    updated=update_enemy_ai139(branch,world,english_names=english_names)
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
        count-=1;packets.append((170,struct.pack('<Q',target).hex()))
    vector=PhysicalNPCVector139(tuple(storage),count)
    ai=replace(updated.state,records432=vector.active,incoming=replace(updated.state.incoming,records432=vector.active))
    return EnemyAIDeadResult139(ai,vector,before_removal,tuple(pending),tuple(packets),updated.attacks,updated.motions,updated.routing,updated.path_recomputed,tuple(proofs))
