"""Physical player-source ownership for the fixed135 controlled composition.

The level object alone owns stats, HP, time and RNG. This object owns only
live32 storage, the1202 Aura cache and explicit App notification context.
The resource context is constructed at each call boundary, never saved across
casts/selection as a second stale view of the live sources.
"""
from dataclasses import dataclass, replace

from . import binary32 as f
from .mixed_resource135 import MixedResourceContext135, validate_mixed_resource135
from .resource_consumer135 import LiveVector135
from .resource_aura135 import ResourceAuraState135, rebuild_resource_aura135
from .live_owner135 import live_active_view135, live_view_cells135, retain_live135


@dataclass(frozen=True)
class PlayerSources135:
    live: LiveVector135
    aura: ResourceAuraState135
    notification_next_id14340336: int
    locale_code: str
    live_auxiliary_origins: tuple = ()

    def __post_init__(self):
        if not isinstance(self.live, LiveVector135) or not isinstance(self.aura, ResourceAuraState135):
            raise TypeError('Complete physical live32 and Aura owners required')
        value = self.notification_next_id14340336
        if type(value) is not int or not 0 <= value <= f.MASK:
            raise ValueError('Explicit App notification counter required')
        if self.locale_code != 'en':
            raise NotImplementedError('Controlled player-source composition currently requires English rune context')
        if len(self.live_auxiliary_origins)!=self.live.capacity:
            raise ValueError('Every physical live capacity row needs an auxiliary origin slot')
        for row,origin in zip(self.live.storage,self.live_auxiliary_origins):
            if origin is not None and row[16:20]!=(None,)*4:
                raise ValueError('An opaque auxiliary origin cannot mask a known physical word')

    @classmethod
    def empty(cls, *, notification_next_id14340336, locale_code):
        #1560 writes live/Aura headers0,4,0 and initialized2569=0. No
        #unallocated row or object key is fabricated from an original output.
        return cls(LiveVector135((), 0), ResourceAuraState135((), 0),
            notification_next_id14340336, locale_code)

    def context(self, level, player_guid, action_sequence1644):
        value = MixedResourceContext135(self.live, self.aura, player_guid,
            action_sequence1644, self.notification_next_id14340336, self.locale_code, True)
        validate_mixed_resource135(level, value)
        return value

    def validate_view(self, records, unspecified):
        live_view_cells135(self.live, records, unspecified)

    def active_view(self):
        return live_active_view135(self.live)

    def adopt(self, context, *, live_owner=None):
        if not isinstance(context, MixedResourceContext135):
            raise TypeError('Returned typed resource context required')
        if context.locale_code != self.locale_code:
            raise ValueError('Locale owner changed during a consumer call')
        owner=self if live_owner is None else live_owner
        if owner.live.storage!=context.live.storage or owner.live.count!=context.live.count:
            raise ValueError('Explicit retain/append provenance must accompany live owner changes')
        return replace(owner, aura=context.aura,
            notification_next_id14340336=context.notification_next_id14340336)

    def retain(self, predicate):
        flags=tuple(predicate(row)for row in self.live.storage[:self.live.count])
        it=iter(flags);live=retain_live135(self.live,lambda row:next(it))
        origins=list(self.live_auxiliary_origins);write=0
        for read,keep in enumerate(flags):
            if keep:
                origins[write]=self.live_auxiliary_origins[read];write+=1
        return replace(self,live=live,live_auxiliary_origins=tuple(origins))

    def replace_live(self, live, *, scratch_write=None, origin=None):
        """Adopt an explicit append after its retain; preserve old tail origins."""
        if live.capacity<self.live.capacity:
            raise ValueError('Live capacity shrink has no producer in this domain')
        origins=list(self.live_auxiliary_origins)+( [None]*(live.capacity-self.live.capacity))
        if scratch_write is not None:
            index,offset,source=scratch_write
            if offset!=16 or not 0<=index<live.count:
                raise ValueError('Only a typed922 scratch48→live16 write is admitted')
            origins[index]=origin if source.bits is None else None
            if source.bits is None and origin is None:
                raise ValueError('Unresolved written source requires a named origin')
        return replace(self,live=live,live_auxiliary_origins=tuple(origins))

    def refresh_aura(self, level):
        result = rebuild_resource_aura135(self.live.storage, self.live.count,
            level.stats.now_bits, self.aura, level.player_fields)
        return replace(level, player_fields=result.player_fields), replace(self, aura=result.aura)
