"""Current139 ordinary AI925: genuine nav/path,432B motions,contact history.

Inputs are independent world data and explicit complete owner state. The
eight-neighbor/BFS/segment algorithms are shared pure algorithms, re-bound to
current925/30179/29237 bodies; no old runtime acceptance is transferred.
Unsupported families/status/death/callback branches raise. No IO/original
files/output/snapshots are read by this module.
"""
from dataclasses import dataclass,replace
import math,struct
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .position_math139 import sin_bits as _sin_small,cos_bits as _cos_small,hypot_bits,_sin_kernel,_cos_kernel,TAU
from .distance_map135 import ProducedDistanceMap135,update_distance_map135
from .ai_world135 import route_destination135
from .incoming139 import IncomingState139,record432,word,guid,resolve_prefix139,resolve_source139
from .incoming_history139 import IncomingHistory139,append_incoming_history

class PendingEnemyAI139(NotImplementedError):pass
@dataclass(frozen=True)
class EnemyAIState139:
    records432:tuple
    now_bits:int
    dt_bits:int
    player_xyz:tuple
    incoming:IncomingState139
    history:IncomingHistory139
    player_fields:tuple
    movement_sequence2412:int=0
    distance_map:ProducedDistanceMap135|None=None
    distance_clock2372_bits:int=0
    mode2582:int=0
    phase2587:int=1
    zone:int=0

@dataclass(frozen=True)
class EnemyAIResult139:
    state:EnemyAIState139
    attacks:tuple
    motions:tuple
    packets:tuple
    routing:tuple
    path_recomputed:bool

def _put(row,o,v):row[o:o+4]=struct.pack('<I',v)
def _lt(a,b):return f.to_float(a)<f.to_float(b)
def _le(a,b):return f.to_float(a)<=f.to_float(b)
def _max(a,b):return a if f.to_float(a)>f.to_float(b)else b
def _min(a,b):return a if f.to_float(a)<f.to_float(b)else b
def distance139(a,b):
    x,y=f.sub(a[0],b[0]),f.sub(a[1],b[1])
    return sqrt_bits(f.add(f.mul(x,x),f.mul(y,y)))
def position_xyz139(row,now):
    duration=word(row,344)
    if _le(duration,0):return tuple(word(row,o)for o in(328,332,336))
    t=_min(_max(f.div(f.sub(now,word(row,340)),duration),0),0x3f800000)
    return tuple(f.add(word(row,a),f.mul(f.sub(word(row,b),word(row,a)),t))for a,b in((316,328),(320,332),(324,336)))
def _packed(v):
    raw=v.to_bytes(8,'little');return bytes([sum(1<<i for i,b in enumerate(raw)if b)])+bytes(b for b in raw if b)
def _sat(v):
    x=f.to_float(v);return 0 if not x>0 else f.MASK if x>=f.MASK else math.trunc(x)
def _trig139(bits,cosine):
    absolute=bits&~f.SIGN
    if absolute<=0x40c90fdb:return(_cos_small if cosine else _sin_small)(bits)
    if absolute<1088565718:
        return _cos_kernel(abs(f.to_float(bits))-TAU)if cosine else _sin_kernel(abs(f.to_float(bits))-TAU)^(bits&f.SIGN)
    if absolute>1305022426:raise PendingEnemyAI139('Large Payne-Hanek trig reduction')
    x=f.to_float(bits);H=float.fromhex
    n=((x*H('0x1.45f306dc9c883p-1'))+H('0x1.8p52'))+H('-0x1.8p52')
    y=(x+n*H('-0x1.921fb5p0'))+n*H('-0x1.110b4611a6263p-26');q=int(n)&3
    return((_cos_kernel(y),_sin_kernel(y)^f.SIGN,_cos_kernel(y)^f.SIGN,_sin_kernel(y))if cosine else(_sin_kernel(y),_cos_kernel(y),_sin_kernel(y)^f.SIGN,_cos_kernel(y)^f.SIGN))[q]
def _project(world,xyz):
    h=world.height(*xyz[:2])
    if h.found:return(*xyz[:2],h.value_bits)
    n=world.nearest_primary(*xyz[:2]);return(*xyz[:2],n.xyz_bits[2])if n.found else xyz
def _packet221(world,target,start,end,duration,seq,player_guid=0):
    # Stop925 kind3 contains raw playerGUID64,256,duration1,count1,raw XYZ.
    prefix=_packed(target)
    if _le(duration,0):
        return(221,(prefix+struct.pack('<4I',*start,seq)+bytes([3])+struct.pack('<Q3I3I',player_guid,256,1,1,*start)).hex())
    milliseconds=max(1,_sat(f.mul(duration,0x447a0000)))
    return(221,(prefix+struct.pack('<4I',*_project(world,start),seq)+bytes([0])+struct.pack('<3I',256,milliseconds,1)+struct.pack('<3I',*_project(world,end))).hex())
def _validate(row):
    if any(word(row,o)!=f.MASK for o in(40,64,244)):raise PendingEnemyAI139('Nonordinary AI family40/64/244')
    if word(row,284)!=5830904:raise PendingEnemyAI139('Only independently declared default melee definition5830904')
    if any(word(row,o)for o in(0,8,16,240,360,380,388,396,416,420)):raise PendingEnemyAI139('Dead/pending/status/fear/alternate producer not yet restored')
    for o in(120,124,128,132,136,140,288,292,296,300,304,308,316,320,324,328,332,336,340,344,348,352,404,408,412):
        part=row[o:o+4]
        if None not in part and(f.is_nan(word(row,o))or f.is_inf(word(row,o))):raise PendingEnemyAI139('Finite current139 AI domain')

def update_enemy_ai139(value,world,*,english_names):
    if not isinstance(value,EnemyAIState139):raise TypeError('Typed current139 AI state required')
    if value.mode2582 or value.phase2587!=1 or value.zone!=0:raise PendingEnemyAI139('Only local active Elwynn phase1')
    if world.flat_height_bits is not None or world.primary is not None:raise PendingEnemyAI139('Current canonical nonflat/no-primary world required')
    if value.incoming.items8!=()or value.incoming.modifiers36:raise PendingEnemyAI139('Explicit complete empty item/modifier callback owners required')
    if len(value.records432)>512:raise ValueError('NPC budget')
    rows=[list(record432(row))for row in value.records432]
    for row in rows:_validate(row)
    path=update_distance_map135(world.nav,value.player_xyz[:2],value.now_bits,previous=value.distance_map,updated_at_bits=value.distance_clock2372_bits)
    motions=[];attacks=[];routing=[];now=value.now_bits;player=value.player_xyz
    for row in rows:
        if _lt(now,word(row,408)):continue
        pos=position_xyz139(row,now);timer=f.sub(word(row,352),value.dt_bits);_put(row,352,timer);target=guid(row)
        if _le(distance139(pos,player),word(row,308)):
            if _lt(0,word(row,344))and _lt(now,f.add(word(row,340),word(row,344))):
                for j,v in enumerate(pos):_put(row,316+4*j,v);_put(row,328+4*j,v)
                _put(row,340,now);_put(row,344,0);motions.append((target,pos,pos,0))
            if _le(timer,0)and _le(word(row,412),now):
                _put(row,352,word(row,304));weak=word(row,128)if _lt(now,word(row,132))else word(row,136)if _lt(now,word(row,140))else 0
                attacks.append((target,f.mul(word(row,296),f.sub(0x3f800000,weak))))
            continue
        if _lt(now,word(row,348)):continue
        angle=f.add(word(row,404),0x3e19999a);_put(row,404,angle)
        radius=_max(f.mul(word(row,308),0x3f4ccccd),0x3fc00000)
        # Ordinary non-ranged8=0 takes br2@6, bypassing the ranged circle ray.
        dest=(f.add(player[0],f.mul(radius,_trig139(angle,True))),f.add(player[1],f.mul(radius,_trig139(angle,False))),player[2]);length=distance139(pos,dest)
        if _lt(0x41600000,length):
            factor=f.div(0x41600000,length);dest=(f.add(pos[0],f.mul(f.sub(dest[0],pos[0]),factor)),f.add(pos[1],f.mul(f.sub(dest[1],pos[1]),factor)),pos[2])
        dest,route=route_destination135(world.nav,path.distance_map,pos,dest);routing.append((target,route))
        speed=word(row,300)
        if _lt(now,word(row,124)):speed=f.mul(speed,f.sub(0x3f800000,word(row,120)))
        if _lt(now,word(row,412)):speed=f.mul(speed,0x3faccccd)
        duration=f.div(distance139(pos,dest),_max(speed,0x3f000000))
        for j,v in enumerate(pos):_put(row,316+4*j,v)
        for j,v in enumerate(dest):_put(row,328+4*j,v)
        _put(row,340,now);_put(row,344,duration);_put(row,348,f.add(now,_min(_max(duration,0x3e800000),0x3f333333)))
        motions.append((target,pos,dest,duration))
    incoming=replace(value.incoming,now_bits=now,player_xy=player[:2],records432=tuple(tuple(r)for r in rows));history=value.history;fields=dict(value.player_fields)
    packets=[];seq=value.movement_sequence2412
    for target,start,end,duration in motions:
        seq=(seq+1)&f.MASK;packets.append(_packet221(world,target,start,end,duration,seq))
    for source,amount in attacks:
        #925 emits noncrit direct damage packet before full1076.
        shown=_sat(_max(f.mul(amount,f.sub(0x3f800000,incoming.armor1568_bits)),0x3f800000))
        packets.append((330,(struct.pack('<I',2)+_packed(source)+_packed(0)+struct.pack('<I',shown)+b'\1'+struct.pack('<IfI6I',0,float(shown),shown,0,0,1,0,0,0)).hex()))
        before=incoming;result=resolve_prefix139(incoming,amount,source_guid=source,contact_flag=1);incoming=result.state
        if result.history_required:
            resolved=resolve_source139(incoming.records432,source,english_names=english_names)
            history=append_incoming_history(history,now_bits=now,damage_bits=result.damage_bits,absorbed_bits=result.absorbed_bits,hp_after_prefix_bits=f.sub(before.hp1440_bits,result.damage_bits),maximum_hp_bits=incoming.maximum1536_bits,category=0,source_label=resolved.name,source_classification=resolved.classification)
            fields[22]=min(f.MASK,max(0,math.ceil(f.to_float(incoming.hp1440_bits))));fields[28]=min(f.MASK,max(0,math.ceil(f.to_float(incoming.maximum1536_bits))))
    state=replace(value,records432=tuple(tuple(r)for r in rows),incoming=incoming,history=history,player_fields=tuple(sorted(fields.items())),distance_map=path.distance_map,distance_clock2372_bits=path.updated_at_bits,movement_sequence2412=seq)
    return EnemyAIResult139(state,tuple(attacks),tuple(motions),tuple(packets),tuple(routing),path.recomputed)
