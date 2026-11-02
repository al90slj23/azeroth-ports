"""Independent fixed135 G656/660/664 auxiliary112 owner, empty admitted slice.

This is distinct from G1856/1860/1864 secondary areas. Initial state comes from
1560's own writes, not an observed snapshot. An admitted transition preserves
the existing owner; it never creates a replacement empty owner at fatal time.
Nonempty producers, network imports and unsupported source paths stay unknown.
"""
from dataclasses import dataclass
import hashlib
from .initial_state135 import InitialState135
from .record_cells135 import cells135

class UnknownMotionAuxOwner135(NotImplementedError):pass

# Whole fixed88-byte declarations, independently checked against original data
# by the static research reader. Execution/effect numbers alone are insufficient.
ADMITTED_DEFINITIONS135={
 5467428:('cleave',5,0,'94281eef645dca10bc2406b318b97728cd8c49f5258b93f958058925efd5acc3'),
 5467604:('thunder_clap',2,1,'e7b75d6bc9db235aa33b3bf4670cced4e004e433ea0e8aaaac3695ec9b49a33a'),
 5467868:('demo_shout',2,11,'bf645af63f09644fa87d9a45ff7181064a6a865565d791a9f5dce1f96414a7aa'),
 5467956:('battle_shout',9,8,'8c11d5b18081fcdba0d591ab4add6e0ef4290e0df8fc77b639e79deab7f865d7'),
 5476580:('perception',9,8,'7bcd41eea4340dead5a2f6cd22be55025e264bd63f1e4b0b633c48130a9527c3'),
}
EMPTY_SOURCE_COUNTS135=(604,652,2032,2056,1804,1852,1816,1828,1840,1864,2116)
TAIL_EVENTS135=('player','extra','owned_effects','hits','area','effects','deadline','secondary','ai','collect','claims','spawn','special','terminal')
MOTION_EVENTS135=('motion2328','motion968_199')
FATAL_TAIL_EVENTS135=('collect','claims','spawn','special','terminal')

def _u(value):
 if type(value)is not int or not 0<=value<1<<32:raise ValueError('Explicit unsigned word required')
 return value

@dataclass(frozen=True)
class MotionAuxOwner135:
 capacity656:int
 pointer660:int|None
 storage112:tuple
 count664:int
 def __post_init__(self):
  _u(self.capacity656);_u(self.count664)
  if self.pointer660 is not None:_u(self.pointer660)
  if type(self.storage112)is not tuple or len(self.storage112)!=self.capacity656 or self.count664>self.capacity656:raise ValueError('Explicit physical auxiliary backing/capacity/count required')
  for row in self.storage112:cells135(row,112)
 def stopped_motion_input135(self):return self.storage112,self.count664

def from_empty_profile1560_aux135(initial):
 """1560 scratch740=0 and scratch748=8, copied from scratch+88 to Game.

 G656cap=0, G660pointer=8 aligned dangling sentinel, G664count=0. This
 initializer belongs at the actual independent empty-profile constructor, not
 at a consumer that discovers its owner is missing. No original input is read.
 """
 if not isinstance(initial,InitialState135):raise TypeError('Independent empty-profile1560 result required')
 if initial.level.phase2587 not in(0,1):raise UnknownMotionAuxOwner135('Constructor/opening handoff required for initial auxiliary owner')
 return MotionAuxOwner135(0,8,(),0)

@dataclass(frozen=True)
class MotionAuxAdmission135:
 """Caller-owned sources before/after one admitted offline event.

 Definition rows are (pointer, complete88-byte hex), including all owned skills
 and the racial. Empty count tuples name original count offsets, not inferred
 class labels. They must originate in the same canonical independent state.
 """
 event:str
 phase2587:int
 mode2582:int
 flag2576:int
 class360:int
 race361:int
 definitions88:tuple
 source_counts:tuple
 selected_kind2585:int|None=None
 def __post_init__(self):
  if self.event not in('opening1089','selection1072')+TAIL_EVENTS135+MOTION_EVENTS135:raise UnknownMotionAuxOwner135('Unrestored auxiliary-owner event producer')
  for value in(self.phase2587,self.mode2582,self.flag2576,self.class360,self.race361):_u(value)
  if self.phase2587 not in(0,1,2,4)or self.mode2582!=0 or self.flag2576!=0:raise UnknownMotionAuxOwner135('Only admitted offline unprotected run transitions restored')
  if self.class360!=1 or self.race361!=1:raise UnknownMotionAuxOwner135('Only current Warrior/Human admitted gameplay source closure restored')
  if type(self.definitions88)is not tuple or not self.definitions88:raise ValueError('All owned/racial fixed declarations required')
  pointers=[]
  for pointer,text in self.definitions88:
   if pointer not in ADMITTED_DEFINITIONS135:raise UnknownMotionAuxOwner135('Unsupported skill may produce auxiliary motion sources')
   raw=bytes.fromhex(text);name,execution,effect,expected=ADMITTED_DEFINITIONS135[pointer]
   if len(raw)!=88 or hashlib.sha256(raw).hexdigest()!=expected:raise UnknownMotionAuxOwner135('Fixed skill declaration differs')
   pointers.append(pointer)
  if 5476580 not in pointers:raise UnknownMotionAuxOwner135('Current actual perception racial declaration required')
  if type(self.source_counts)is not tuple or tuple(offset for offset,_ in self.source_counts)!=EMPTY_SOURCE_COUNTS135:raise ValueError('All declared source count owners required in fixed order')
  for offset,count in self.source_counts:
   _u(count)
   if count:raise UnknownMotionAuxOwner135('Nonempty producer/consumer at G'+str(offset)+' needs its own auxiliary-owner continuation')
  if self.event=='selection1072':
   _u(self.selected_kind2585)
   if self.selected_kind2585!=0:raise UnknownMotionAuxOwner135('Only actual kind0 skill/gold selection source closure restored')
  if self.event!='selection1072'and self.selected_kind2585 is not None:raise ValueError('Selection kind belongs only to the selection event')

def inherit_motion_aux135(owner,before,after):
 """Retain one already-owned empty vector across a proven admitted event.

 Returns the identical owner object, never substitutes (). A future producer
 must provide its actual updated storage/header implementation. Nonempty data
 is refused here rather than erased or mislabeled as secondary-area backing.
 """
 if not isinstance(owner,MotionAuxOwner135):raise TypeError('Persistent auxiliary-motion owner required')
 if owner.capacity656 or owner.count664 or owner.storage112 or owner.pointer660!=8:raise UnknownMotionAuxOwner135('Nonempty or reallocated auxiliary owner is outside this empty-source inheritance proof')
 if not isinstance(before,MotionAuxAdmission135)or not isinstance(after,MotionAuxAdmission135):raise TypeError('Explicit before/after admitted source states required')
 if before.event!=after.event:raise ValueError('Before/after event identities differ')
 if before.event=='opening1089'and(before.phase2587,after.phase2587)!=(0,1):raise UnknownMotionAuxOwner135('Opening must inherit actual phase0 to phase1')
 if before.event=='selection1072'and(before.phase2587!=2 or after.phase2587 not in(1,2)):raise UnknownMotionAuxOwner135('Actual skill selection/resume phases required')
 if before.event in TAIL_EVENTS135+MOTION_EVENTS135:
  if before.phase2587==4:
   if before.event not in FATAL_TAIL_EVENTS135 or after.phase2587!=4:raise UnknownMotionAuxOwner135('Only remaining same-frame tail events inherit fatal phase4 without restarting planning')
  elif before.phase2587 not in(1,2):raise UnknownMotionAuxOwner135('Admitted ordered tail/motion requires the actual running/choice prephase')
 return owner
