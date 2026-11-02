#!/usr/bin/env python3
"""Pure bounded input discovery for13563 f32norm vs50441hypot difference.

Reads independentcanonical world only. Doesnotexecuteoriginal, writeoldsource,
or loadoriginalmemory. These are candidate counterexamples, not acceptance.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,random,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'reconstruction')]
from load_world_position139_inputs import load_world139_canonical
from core_spec import binary32 as f
from core_spec.binary32_sqrt import sqrt_bits
from core_spec.position_math139 import sin_bits,cos_bits,hypot_bits
from core_spec.rng import uniform_range_bits

def main():
 world,_=load_world139_canonical(ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model','46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48');cx,cy=3323121664,3290316800;limit=0x42f00000;rng=random.Random(0x13913563);gaps=[];attempts=0
 for dxp,dyp in((110,0),(-110,0),(0,110),(0,-110)):
  px,py=f.add(cx,f.from_float(dxp)),f.add(cy,f.from_float(dyp));ph=world.height(px,py)
  if not ph.found:continue
  for _ in range(5000):
   attempts+=1;words=tuple(rng.getrandbits(32)for _ in range(4));a=uniform_range_bits(words,0,0x40c90fdb);r=uniform_range_bits(a.state,0x41900000,0x42480000);x=f.add(px,f.mul(cos_bits(f.add(a.bits,0)),r.bits));y=f.add(py,f.mul(sin_bits(f.add(a.bits,0)),r.bits));dx,dy=f.sub(x,cx),f.sub(y,cy)
   n32=sqrt_bits(f.add(f.mul(dx,dx),f.mul(dy,dy)));nh=hypot_bits(dx,dy)
   if n32==nh or min(f.to_float(n32),f.to_float(nh))<=120:continue
   def project(norm):
    xx=f.add(cx,f.mul(limit,f.div(dx,norm)));yy=f.add(cy,f.mul(limit,f.div(dy,norm)));nav=world.nav_probe(xx,yy);height=world.height(xx,yy)
    accepted=not(nav.present and nav.in_bounds and nav.value)and height.found and f.to_float(f.sub(height.value_bits,ph.value_bits)&~f.SIGN)<25
    return dict(XYZ_bits=[xx,yy,height.value_bits]if height.found else[xx,yy,None],accepted_first_trial=bool(accepted))
   new,old=project(n32),project(nh)
   if new['accepted_first_trial']and old['accepted_first_trial']and new['XYZ_bits']!=old['XYZ_bits']:
    gaps.append(dict(input=dict(zone=0,player_xyz=[px,py,ph.value_bits],velocity_xy=[0,0],low_radius_bits=0x41900000,high_radius_bits=0x42480000,bias_probability_bits=0x3f000000,rng_words=words,distance_map=None),f32_norm_bits=n32,hypot_bits=nh,true_f32_first_trial=new,hypot_first_trial=old,post_rng_words=r.state,draws=a.draws+r.draws))
    if len(gaps)>=4:break
  if len(gaps)>=4:break
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('position139-rounding-gap-%Y%m%dT%H%M%S.%fZ');out.mkdir();p=out/'candidate-inputs.json';p.write_text(json.dumps(dict(kind='pure_model_inputdiscovery_notoriginaldifferential',attempts=attempts,candidates=gaps,original_executions=0,oldsource_changed=False),indent=2)+'\n');print(json.dumps(dict(directory=str(out),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),attempts=attempts,gaps=len(gaps),first=gaps[:1])),flush=True)
if __name__=='__main__':main()
