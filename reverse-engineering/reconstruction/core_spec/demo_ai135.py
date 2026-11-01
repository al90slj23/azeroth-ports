"""Typed fixed135 ordinary-AI continuation for demo weakness and4543 expiry.

No original values are read. The complete declaration must match the physical
independent record; an unbound/non1160 status remains outside ordinary AI.
Only360 is cleared at expiry. Aura removal is deliberately deferred until
after the phase's queued contact attacks, in original921 order.
"""
from dataclasses import replace
from . import binary32 as f
from .record_cells135 import u32,u64,put_u32
from .demo_shout135 import DemoDebuff135,_aura


class PendingDemoAi135(NotImplementedError):
    pass


def validate_demo_binding135(raw,declaration):
    if not isinstance(declaration,DemoDebuff135):
        raise TypeError('Explicit DemoDebuff135 producer declaration required')
    if declaration.spell360 not in(0,1160):
        raise PendingDemoAi135('Only declared demo1160/cleared status source restored')
    actual=(u64(raw,112,consumer='demo_ai135.GUID'),u32(raw,0,consumer='demo_ai135.marker'),
        tuple(u32(raw,o,consumer='demo_ai135.weakness')for o in(128,132,136,140)),
        u32(raw,360,consumer='demo_ai135.spell'),u32(raw,364,consumer='demo_ai135.duration'),
        tuple(u32(raw,168+4*i,consumer='demo_ai135.aura')for i in range(16)),
        u32(raw,240,consumer='demo_ai135.ability_count'))
    expected=(declaration.guid,declaration.marker,declaration.words128_140,
        declaration.spell360,declaration.duration364_bits,declaration.aura_slots168,
        declaration.ability_count240)
    if actual!=expected:
        raise PendingDemoAi135('Demo producer declaration differs from the complete physical owner')
    if declaration.marker!=0 or declaration.ability_count240:
        raise PendingDemoAi135('Only live ordinary empty44B-ability demo AI restored')
    if any(x not in(0,1160)for x in declaration.aura_slots168)or declaration.aura_slots168.count(1160)>1:
        raise PendingDemoAi135('Other or duplicate NPC Aura producers require their earlier921 cleanup')


def demo_bindings135(raws,declarations):
    if type(declarations)is not tuple:
        raise TypeError('Explicit ordered tuple of known demo producer declarations required')
    if not declarations:return{}
    by_guid={u64(raw,112,consumer='demo_ai135.owner'):raw for raw in raws}
    if len(by_guid)!=len(raws):raise PendingDemoAi135('Demo AI requires unique physical target GUIDs')
    result={}
    for row in declarations:
        if not isinstance(row,DemoDebuff135)or row.guid in result or row.guid not in by_guid:
            raise PendingDemoAi135('Unique existing GUID-bound demo declaration required')
        validate_demo_binding135(by_guid[row.guid],row);result[row.guid]=row
    return result


def begin_demo_expiry135(raw,declaration,now_bits):
    """921 local26==0 continuation, before fear/stun and U400 freeze guard.

    The caller preserves the existing admitted local mode/phase and owner
    routing restrictions. Primary/backup expiry is selected, never promoted.
    """
    if declaration is None:return None
    spell=u32(raw,360,consumer='demo_ai135.expiry_spell')
    if not spell:return None
    primary=u32(raw,132,consumer='demo_ai135.primary_expiry')
    expiry=primary if f.to_float(primary)>f.to_float(now_bits)else u32(raw,140,consumer='demo_ai135.backup_expiry')
    if f.to_float(expiry)<=f.to_float(now_bits):
        put_u32(raw,360,0)
        return(declaration.guid,spell)
    return None


def finish_demo_expiry135(raws,bindings,removals):
    """Original921 late remove queue ->4543(...,add=0), after contact damage."""
    if not bindings:return(),(),()
    indices={u64(raw,112,consumer='demo_ai135.final_owner'):i for i,raw in enumerate(raws)}
    packets=[];fields=[]
    for guid,spell in removals:
        raw=raws[indices[guid]];old=bindings[guid]
        current=replace(old,spell360=u32(raw,360),
            words128_140=tuple(u32(raw,o)for o in(128,132,136,140)),
            aura_slots168=tuple(u32(raw,168+4*i)for i in range(16)))
        updated,packet,keys=_aura(current,spell,False)
        for i,(a,b)in enumerate(zip(current.aura_slots168,updated.aura_slots168)):
            if a!=b:put_u32(raw,168+4*i,b)
        if packet is not None:packets.append(packet);fields.append((guid,keys))
    declarations=[]
    for old in bindings.values():
        raw=raws[indices[old.guid]]
        declarations.append(replace(old,spell360=u32(raw,360),
            words128_140=tuple(u32(raw,o)for o in(128,132,136,140)),
            aura_slots168=tuple(u32(raw,168+4*i)for i in range(16))))
    return tuple(declarations),tuple(packets),tuple(fields)
