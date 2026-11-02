"""Current139 defaultWarrior positive-target1238 and composed2123.

Actual fourNPC/owned/racial/live/Aura owners are inputs. Basicflag1 differs
from inheritedGame908. No ability, racial, moving actor or hurtHP is disabled.
"""
from dataclasses import dataclass,replace
import math,struct
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .rng import next_u32_words
from .player_update139 import (PlayerUpdateState139,LiveVector139,word139,
    _callback139,_replace_live,recalculate_player139,_definition139,_minnum,_maxnum)
from .player_effects139 import sync_aura139,cast_perception139
from .healing139 import DefaultHealingSources139,HealingLedger139,regenerate_player139
from .death139 import OrdinaryDamageState139
from .default_damage139 import (DefaultOutgoingLedger139,targets8673_cells139,
    resolve_default_damage139,cast_cleave_default139,cast_thunder_clap_default139)
from .cast139 import CleaveDefinition139
from .thunder_clap139 import ThunderClapDefinition139


class PendingPlayerAutocast139(NotImplementedError):pass


def _owned_word(row,offset,value):
    out=bytearray(row);out[offset:offset+4]=struct.pack('<I',value);return bytes(out)


def _packed(value):
    raw=struct.pack('<Q',value)
    return bytes([sum((v!=0)<<j for j,v in enumerate(raw))])+bytes(v for v in raw if v)


def basic330139(source,target,amount_bits,critical):
    value=f.to_float(amount_bits)
    if not math.isfinite(value):raise PendingPlayerAutocast139('Finitebasicvisualamount')
    shown=max(0,min(f.MASK,int(value)))
    return(330,(struct.pack('<I',130 if critical else 2)+_packed(source)+_packed(target)
        +struct.pack('<I',shown)+b'\1'+struct.pack('<IfI6I',0,float(shown),shown,0,0,1,0,0,0)
        +b'Melee\0melee\0').hex())


def _cooldown_packets(source,spell,remaining):
    ms=max(0,min(f.MASK,int(f.to_float(f.mul(remaining,0x447a0000)))))
    return((308,struct.pack('<QII',source,spell,ms).hex()),
           (309,struct.pack('<IQ',spell,source).hex()))


@dataclass(frozen=True)
class PlayerAutocastState139:
    player:PlayerUpdateState139
    damage:OrdinaryDamageState139
    ledger:HealingLedger139
    player_guid:int
    inherited_context908:int

    def __post_init__(self):
        if not isinstance(self.player,PlayerUpdateState139)or not isinstance(self.damage,OrdinaryDamageState139)or not isinstance(self.ledger,HealingLedger139):raise TypeError('Actualplayer/damage/ledgerownersrequired')
        g=self.player.growth
        if(self.damage.records432!=g.units432_cells or self.damage.rng_words!=g.rng_words
                or self.damage.player_hp1440_bits!=g.current_hp_bits or self.damage.maximum1536_bits!=g.derived_bits[1536]):raise ValueError('Duplicatedownerprojectionmismatch')
        if self.player_guid!=0 or self.inherited_context908!=0:raise PendingPlayerAutocast139('DefaultactualGUID0/Game908=0only')
        if tuple(word139(row,0)for row in g.owned_records80)!=(5882740,5882916):raise PendingPlayerAutocast139('Actualcleave+firstnewThunderownersrequired')
        if word139(g.racial_record80,0)!=5891892:raise PendingPlayerAutocast139('ActualHumanracialrequired')
        if g.phase2587!=1 or g.source_counts!=(0,)*7:raise PendingPlayerAutocast139('Runningdefaultemptysourceownersrequired')


def _adopt(state,result):
    p=state.player;d=result.state;fields=dict(p.growth.player_fields);fields.update(result.player_key_writes)
    g=replace(p.growth,units432_cells=d.records432,rng_words=d.rng_words,
        current_hp_bits=d.player_hp1440_bits,player_fields=fields)
    if hasattr(result,'spell_sets'):p=replace(p,spell_sets=result.spell_sets)
    return replace(state,player=replace(p,growth=g),damage=d,ledger=result.healing)


@dataclass(frozen=True)
class PlayerAutocastResult139:
    state:PlayerAutocastState139
    packets:tuple
    events:tuple
    heal_events:tuple=()
    expired_spells:tuple=()
    retained_source_indices:tuple=()
    regen_request_bits:int=0
    regen_accounted_bits:int=0


def tick_default_autocast139(state,dt,world):
    """1238 actualbasic→orderedowned→Humanracial, both success/failure."""
    if not isinstance(state,PlayerAutocastState139):raise TypeError('PlayerAutocastState139')
    if f.is_nan(dt)or f.is_inf(dt)or f.to_float(dt)<0:raise PendingPlayerAutocast139('Finitenonnegativedelta')
    packets=[];events=[];heals=[];p=state.player;g=p.growth
    sources=DefaultHealingSources139(1,g.source_counts);timer=f.sub(p.timer1628_bits,dt)
    if f.to_float(timer)<=0:
        chosen=targets8673_cells139(state.damage.records432,p.player_xyz,g.now_bits,0x40c00000)
        if chosen:
            sample,words=next_u32_words(state.damage.rng_words);roll=f.mul(f.from_u32(sample>>8),0x33800000)
            critical=int(f.to_float(g.derived_bits[1548])>f.to_float(roll))
            base=f.mul(f.mul(f.mul(0x41dc0000,0x3fc00000),0x3f800000),g.derived_bits[1540])
            amount=f.mul(base,g.derived_bits[1552])if critical else base
            packets.append(basic330139(state.player_guid,chosen[0],amount,critical))
            result=resolve_default_damage139(replace(state.damage,rng_words=words),chosen[0],amount,world,
                spell_id=0,school=0,critical=critical,inherited_context908=state.inherited_context908,
                healing=state.ledger,healing_sources=sources,outgoing_owned80=None,
                suppress_spell_damage_packet=1,heal_on_kill1600_bits=g.derived_bits[1600])
            state=_adopt(state,result);packets.extend(result.known_packets);heals.extend(result.heal_events)
            timer=f.mul(f.mul(0x3fcccccd,0x3f99999a),sqrt_bits(g.derived_bits[1544]))
            events.append(('basic_success',chosen[0],amount,critical,timer,1))
        else:timer=0x3e19999a;events.append(('basic_no_target',timer))
    state=replace(state,player=replace(state.player,timer1628_bits=timer))
    owned=list(state.player.growth.owned_records80)
    for index,row in enumerate(owned):
        name,raw=_definition139(word139(row,0));remaining=f.sub(word139(row,8),dt)
        owned[index]=_owned_word(row,8,remaining)
        state=replace(state,player=replace(state.player,growth=replace(state.player.growth,owned_records80=tuple(owned))))
        if f.to_float(remaining)>0:continue
        p=state.player;g=p.growth;derived={str(k):v for k,v in g.derived_bits.items()}
        common=dict(healing=state.ledger,healing_sources=sources,source_id=state.player_guid,
                    heal_on_kill1600_bits=g.derived_bits[1600])
        if name=='cleave':
            result=cast_cleave_default139(state.damage,p.player_xyz,derived,
                CleaveDefinition139(5882740,b'cleave',raw),owned[index],p.spell_sets,world,
                inherited_context908=state.inherited_context908,**common)
        elif name=='thunder_clap':
            result=cast_thunder_clap_default139(state.damage,p.player_xyz,derived,
                ThunderClapDefinition139(5882916,raw),owned[index],p.spell_sets,world,
                context908=state.inherited_context908,**common)
        else:raise PendingPlayerAutocast139('Otherownedability')
        state=_adopt(state,result);packets.extend(result.known_packets);heals.extend(result.heal_events)
        if result.success:
            remaining=_maxnum(f.mul(f.mul(f.mul(f.mul(word139(raw,52),0x3fb33333),word139(row,16)),word139(row,56)),state.player.growth.derived_bits[1544]),0x3e800000)
            packets.extend(_cooldown_packets(state.player_guid,word139(raw,44),remaining))
        else:remaining=0x3e4ccccd
        owned[index]=_owned_word(owned[index],8,remaining)
        state=replace(state,player=replace(state.player,growth=replace(state.player.growth,owned_records80=tuple(owned))))
        events.append(('owned',index,name,result.success,result.selected_ids,remaining))
    p=state.player;racial=_owned_word(p.growth.racial_record80,8,f.sub(word139(p.growth.racial_record80,8),dt))
    p=replace(p,growth=replace(p.growth,racial_record80=racial));remaining=word139(racial,8)
    if f.to_float(remaining)<=0:
        p,result=_callback139(p,cast_perception139,'perception922')
        if result['success']:
            name,raw=_definition139(5891892);r=p.growth.racial_record80
            remaining=_maxnum(f.mul(f.mul(f.mul(f.mul(word139(raw,52),0x3fb33333),word139(r,16)),word139(r,56)),p.growth.derived_bits[1544]),0x3e800000)
            packets.extend(result['packets']);packets.extend(_cooldown_packets(state.player_guid,20600,remaining))
        else:remaining=0x3f000000;packets.extend(result['packets'])
        p=replace(p,growth=replace(p.growth,racial_record80=_owned_word(p.growth.racial_record80,8,remaining)))
        events.append(('racial',result['success'],remaining))
    d=replace(state.damage,records432=p.growth.units432_cells,rng_words=p.growth.rng_words,
        player_hp1440_bits=p.growth.current_hp_bits,maximum1536_bits=p.growth.derived_bits[1536])
    state=replace(state,player=p,damage=d)
    return PlayerAutocastResult139(state,tuple(packets),tuple(events),tuple(heals))


def update_player_autocast139(state,now,dt,world):
    """2123 realexpiry/stat/Aura→positive regeneration→positive1238."""
    p=state.player
    if any((p.pool1444_bits,p.pool1448_bits,p.conditional1344,p.conditional1348_bits,p.pool764_bits)):
        raise PendingPlayerAutocast139('Nonemptyshield/poolsource')
    p=replace(p,growth=replace(p.growth,now_bits=now));expired=[]
    for row in p.live.active:
        if not(word139(row,8)==12 and word139(row,20)==1020 or word139(row,8)==8 and word139(row,20)==20600)or word139(row,28)!=0:
            raise PendingPlayerAutocast139('Otherlive/periodicsource')
        if f.to_float(now)>=f.to_float(word139(row,24)):expired.append(word139(row,20))
    packets=[];events=[];retained=tuple(range(p.live.count))
    if expired:
        retained=tuple(j for j,row in enumerate(p.live.active)if f.to_float(now)<f.to_float(word139(row,24)))
        rows=list(p.live.storage)
        for j,i in enumerate(retained):rows[j]=p.live.storage[i]
        p=_replace_live(p,LiveVector139(tuple(rows),len(retained)));p=recalculate_player139(p)
        p,value=_callback139(p,sync_aura139,'Aura1173');packets.extend(value['packets']);events.append(('expiry',tuple(expired)))
    p=replace(p,pool1448_bits=_minnum(p.pool1444_bits,p.pool1448_bits));g=p.growth
    heal=regenerate_player139(g.current_hp_bits,g.derived_bits[1536],g.derived_bits[1576],g.derived_bits[1620],p.last_hit1652_bits,now,dt,state.ledger,DefaultHealingSources139(1,g.source_counts),heal_gate387=p.heal_gate387)
    fields=dict(g.player_fields);fields.update(heal.key_writes);p=replace(p,growth=replace(g,current_hp_bits=heal.hp_bits,player_fields=fields))
    d=replace(state.damage,now_bits=now,records432=p.growth.units432_cells,rng_words=p.growth.rng_words,player_hp1440_bits=p.growth.current_hp_bits,maximum1536_bits=p.growth.derived_bits[1536])
    value=tick_default_autocast139(replace(state,player=p,damage=d,ledger=heal.ledger),dt,world)
    return PlayerAutocastResult139(value.state,tuple(packets)+value.packets,
        tuple(events)+value.events,heal.events+value.heal_events,tuple(expired),retained,
        heal.request_bits,heal.accounted_bits)
