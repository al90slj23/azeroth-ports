"""Independent921 expired ordinary-corpse GUID cleanup, after AI planning.

39635 stably removes every matching GUID, notswap-remove. Numeric wrappers
must keep younger corpses without feeding them to the alive-only AI135 model.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f


@dataclass(frozen=True)
class CorpseCleanup135:
    records:tuple
    removed_guids:tuple
    packet_count:int
    pending:tuple=('Physical39635 resource deallocation and170despawn packet bytes remain separate',)


def cleanup_ordinary_corpses(records,now_bits,*,mode,local_peer,explicit_other_sources_absent=False):
    if explicit_other_sources_absent is not True:raise ValueError('Explicit ordinary corpse source domain required')
    if type(now_bits)is not int or not 0<=now_bits<=f.MASK or type(mode)is not int or not 0<=mode<=255:
        raise ValueError('Raw clock word andmodebyte required')
    if type(local_peer)is not int or not 0<=local_peer<=f.MASK:raise ValueError('Localpeer u32 required')
    rows=[bytes.fromhex(x)for x in records];ids=[]
    for raw in rows:
        if len(raw)!=424:raise ValueError('Complete424B unit records required')
        u=lambda o:struct.unpack_from('<I',raw,o)[0]
        if u(0)not in(0,1):raise ValueError('Canonical live/dead marker0/1 required')
        if any(u(o)!=f.MASK for o in(40,64,244))or u(232)or u(240):
            raise ValueError('Alternate/resource-owning corpse family not restored')
        if u(0)==1 and f.to_float(f.sub(now_bits,u(4)))>f.to_float(0x3f99999a)and(mode==0 or u(280)==local_peer):
            ids.append(struct.unpack_from('<Q',raw,112)[0])
    removed=set(ids)
    kept=tuple(raw.hex()for raw in rows if struct.unpack_from('<Q',raw,112)[0]not in removed)
    return CorpseCleanup135(kept,tuple(ids),len(ids))
