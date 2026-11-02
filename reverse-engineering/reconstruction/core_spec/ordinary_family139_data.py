"""Fixed139 normal-melee declarations bound to actual72B static records.

Only two independently bound definitions are admitted. Container data is not
an assertion that every normal/caster/elite shares this execution behavior.
"""
from dataclasses import dataclass
import struct
from .spawn_schedule139_data import NORMAL_BASE,NORMALS72_HEX

@dataclass(frozen=True)
class OrdinaryDefinition139:
    pointer:int
    raw72:bytes
    english_name:str
    def __post_init__(self):
        if type(self.raw72)is not bytes or len(self.raw72)!=72 or self.pointer not in(5830904,5830976):raise ValueError('Bound current139 normal definition required')
        if self.raw72[0:4]!=bytes(4)or self.raw72[68:72]!=bytes(4):raise ValueError('Only ordinary nonelite tag0 definitions')
    def word(self,offset):return struct.unpack_from('<I',self.raw72,offset)[0]

ORDINARY_DEFINITIONS139=tuple(OrdinaryDefinition139(NORMAL_BASE+72*i,bytes.fromhex(NORMALS72_HEX[i]),name)for i,name in enumerate(('Kobold Vermin','Young Wolf')))
DEFINITION_BY_POINTER139={value.pointer:value for value in ORDINARY_DEFINITIONS139}
ENGLISH_NAMES139={value.pointer:value.english_name for value in ORDINARY_DEFINITIONS139}

def definition139(pointer):
    try:return DEFINITION_BY_POINTER139[pointer]
    except KeyError:raise NotImplementedError('Unbound normal-melee definition '+str(pointer))from None
