"""Independent flat-world ordinary melee update921 and incoming1073 projection.

Consumes explicit 424-byte entities. Unsupported AI families and producers are
rejected, rather than silently treated as ordinary melee. Network packet bytes,
registry/history/aura side effects and fatal/revival behavior remain separate.
"""
from dataclasses import dataclass,replace
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .spawn_geometry135 import sin_bits,cos_bits
from .incoming135 import IncomingState135,UnitPosition,resolve_incoming_prefix
from .ai135_data import MELEE_DEFINITIONS
from .record_cells135 import (cells135, u32, u64, put_u32, encode_row,
                              optional_u32)


@dataclass(frozen=True)
class AiFrame135:
    records:tuple
    now_bits:int
    dt_bits:int
    player_xyz_bits:tuple
    incoming:IncomingState135
    incoming_item_effects:tuple=()  # Actual G2028/G2032 8B item effects, not36B modifiers.
    other_incoming_sources_absent:bool=False


@dataclass(frozen=True)
class AiResult135:
    records:tuple
    incoming:IncomingState135
    attacks:tuple
    movements:tuple
    pending:tuple


def _get(raw,offset):return u32(raw,offset,consumer='ai135')
def _put(raw,offset,value):put_u32(raw,offset,value)
def _float(raw,offset):return f.to_float(_get(raw,offset))
def _maximum(a,b):return a if f.to_float(a)>f.to_float(b)else b
def _distance(a,b):
    x=f.sub(a[0],b[0]);y=f.sub(a[1],b[1])
    return sqrt_bits(f.add(f.mul(x,x),f.mul(y,y)))


def position(raw,now):
    duration=_get(raw,344)
    if f.to_float(duration)<=0:return tuple(_get(raw,o)for o in(328,332,336))
    ratio=f.div(f.sub(now,_get(raw,340)),duration)
    ratio=0 if f.to_float(ratio)<0 else ratio
    ratio=0x3f800000 if f.to_float(ratio)>1 else ratio
    return tuple(f.add(_get(raw,a),f.mul(f.sub(_get(raw,b),_get(raw,a)),ratio))
                 for a,b in((316,328),(320,332),(324,336)))


def _speed(raw,now):
    value=_get(raw,300)
    if _float(raw,124)>f.to_float(now):value=f.mul(value,f.sub(0x3f800000,_get(raw,120)))
    # Ordinary records have no alternate AI variant244; byte276 is therefore
    # ignored by the original helper80447 as well.
    if _float(raw,404)>f.to_float(now):value=f.mul(value,0x3faccccd)
    return value


def _attack(raw,now):
    weakness=(_get(raw,128)if _float(raw,132)>f.to_float(now)else
              _get(raw,136)if _float(raw,140)>f.to_float(now)else 0)
    return f.mul(_get(raw,296),f.sub(0x3f800000,weakness))


def unit_position(raw):
    return UnitPosition(marker=_get(raw,0),target_id=u64(raw,112,consumer='ai135.unit_position'),
        start_x_bits=_get(raw,316),start_y_bits=_get(raw,320),
        end_x_bits=_get(raw,328),end_y_bits=_get(raw,332),
        movement_time_bits=_get(raw,340),movement_duration_bits=_get(raw,344))


def _validate(raw,now):
    if len(raw)!=424:raise ValueError('A complete424-byte entity is required')
    if _get(raw,284)not in MELEE_DEFINITIONS:raise ValueError('Ranged/boss/unknown definition AI remains unresolved')
    if any(_get(raw,o)!=f.MASK for o in(40,64,244)):
        raise ValueError('Alternate AI families40/64/244 remain unresolved')
    if any(_get(raw,o)for o in(0,8,16,240,360)):
        raise ValueError('Dead/pending/cast/status entity producer remains unresolved')
    if any(_get(raw,o)for o in(372,380,388)):
        raise ValueError('Fear/stun/expiry producers remain unresolved')
    for offset in(120,124,128,132,136,140,288,292,296,300,304,308,316,320,324,
                  328,332,336,340,344,348,352,396,400,404):
        # This finite-domain guard must not turn an unconsumed magnitude into
        # a physical read. Known words retain the old guard; an unknown word
        # is required only if the selected branch actually consumes it below.
        value=optional_u32(raw,offset,consumer='ai135.finite_domain')
        if value is not None and(not f.to_float(value)==f.to_float(value)or abs(f.to_float(value))==float('inf')):
            raise ValueError('Finite ordinary AI fixture required')


def update_ordinary_units(state:AiFrame135, *, trig_sin_bits=sin_bits, trig_cos_bits=cos_bits):
    """Original order: update every entity, then apply queued contact attacks.

    This API supports finite ordinary melee records and flat terrain, with no
    remote-owner routing, no owned status producers and no alternate family.
    It returns exact entity bytes and scalar incoming state plus logical events.
    """
    if len(state.records)>512 or len(state.player_xyz_bits)!=3:raise ValueError('Frame budget/input shape')
    if state.other_incoming_sources_absent is not True:
        raise ValueError('Explicit absence of unmodeled incoming sources is required')
    if state.incoming_item_effects:
        raise ValueError('G2028/G2032 item effects including kind22 retaliation remain unresolved')
    if any(x.tag not in(7,12)for x in state.incoming.buffs):
        raise ValueError('Only shield7/protection12 buffs accepted; buff13 retaliation and other buff producers unresolved')
    if any(x.tag!=54 or x.byte4!=1 for x in state.incoming.modifiers):
        raise ValueError('Only effective-armor54 variant1 accepted; other984 modifier producers unresolved')
    if state.incoming.mode_2574 not in(0,1):raise ValueError('Unknown multiplayer mode')
    if state.incoming.mode_2574 and state.incoming.phase_2579==2:
        raise ValueError('Remote multiplayer phase interpolation remains unresolved')
    if any(not(-1e20<f.to_float(x)<1e20)for x in(state.now_bits,state.dt_bits,*state.player_xyz_bits)):
        raise ValueError('Finite bounded frame inputs required')
    raws=[cells135(x)for x in state.records]
    for raw in raws:_validate(raw,state.now_bits)
    if state.incoming.mode_2574 and any(_get(raw,280)!=0 for raw in raws):
        raise ValueError('Remote owner routing remains unresolved; local peer0 required')
    now=state.now_bits;now_value=f.to_float(now);attacks=[];moves=[]
    for raw in raws:
        if _float(raw,400)>now_value:continue
        pos=position(raw,now);timer=f.sub(_get(raw,352),state.dt_bits);_put(raw,352,timer)
        distance=_distance(pos,state.player_xyz_bits);guid=u64(raw,112,consumer='ai135.update.guid')
        if f.to_float(distance)<=_float(raw,308):
            if _float(raw,344)>0 and now_value<f.to_float(f.add(_get(raw,340),_get(raw,344))):
                for i in range(3):_put(raw,316+4*i,pos[i]);_put(raw,328+4*i,pos[i])
                _put(raw,340,now);_put(raw,344,0);moves.append((guid,pos,pos,0))
            if f.to_float(timer)<=0 and _float(raw,404)<=now_value:
                _put(raw,352,_get(raw,304));attacks.append((guid,_attack(raw,now)))
            continue
        if _float(raw,348)>now_value:continue
        angle=f.add(_get(raw,396),0x3e19999a);_put(raw,396,angle)
        radius=_maximum(f.mul(_get(raw,308),0x3f4ccccd),0x3fc00000)
        dest=(f.add(state.player_xyz_bits[0],f.mul(radius,trig_cos_bits(angle))),
              f.add(state.player_xyz_bits[1],f.mul(radius,trig_sin_bits(angle))),state.player_xyz_bits[2])
        length=_distance(pos,dest)
        if f.to_float(length)>14:
            factor=f.div(0x41600000,length)
            dest=(f.add(pos[0],f.mul(f.sub(dest[0],pos[0]),factor)),
                  f.add(pos[1],f.mul(f.sub(dest[1],pos[1]),factor)),pos[2])
        duration=f.div(_distance(pos,dest),_maximum(_speed(raw,now),0x3f000000))
        for i in range(3):_put(raw,316+4*i,pos[i]);_put(raw,328+4*i,dest[i])
        _put(raw,340,now);_put(raw,344,duration)
        deadline=_maximum(duration,0x3e800000)
        deadline=0x3f333333 if f.to_float(deadline)>.7 else deadline
        _put(raw,348,f.add(now,deadline));moves.append((guid,pos,dest,duration))
    incoming=replace(state.incoming,now_bits=now,player_x_1504_bits=state.player_xyz_bits[0],
        player_y_1508_bits=state.player_xyz_bits[1],units=tuple(unit_position(x)for x in raws))
    pending=set(('movement_and_hit_packet_bytes','source_registry_history_aura_metadata'))
    for guid,amount in attacks:
        result=resolve_incoming_prefix(incoming,amount,guid)
        if result.stage not in('scalar_nonfatal_projection','phase_guard','protection_guard','active_raw_buff12_guard'):
            raise ValueError('Incoming callback/death boundary: '+result.stage)
        incoming=result.state
    return AiResult135(tuple(encode_row(x)for x in raws),incoming,tuple(attacks),tuple(moves),tuple(sorted(pending)))
