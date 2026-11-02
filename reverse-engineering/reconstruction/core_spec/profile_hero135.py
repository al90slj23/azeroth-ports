"""Selected-profile name -> Game216/220/224 ->1938 hero, fixed135.

Only explicit input names are produced here. EmptyOpeningInput135 has no name
field and does not by itself prove an empty name. The research-empty helper
below refers specifically to browser_entry_world135's declared zero376 input,
not the game's natural menu/profile producer. No snapshot or original is read.
"""
from dataclasses import dataclass

class UnknownProfileHero135(NotImplementedError):pass

@dataclass(frozen=True)
class SelectedProfileHeroInput135:
    length208:int|None
    resolved_utf8:bytes|None=None

@dataclass(frozen=True)
class ProfileHero135:
    text:str
    utf8:bytes
    cloned_capacity200:int
    cloned_pointer204:int|None
    cloned_length208:int

    @property
    def game_words(self):
        #1560 copies profile376 to scratch104 then scratch88 toGame.
        return((216,self.cloned_capacity200),(220,self.cloned_pointer204),(224,self.cloned_length208))

def produce_profile_hero135(value):
    """75442 String clone;0 length returns sentinel1 without reading payload.

    Positive lengths require an explicitly resolved UTF8 payload. Its new
    allocator address stays None. Original75442 ignores input capacity and
    allocates exactly length bytes; this function never invents the pointer.
    """
    if not isinstance(value,SelectedProfileHeroInput135):raise TypeError('Explicit selected-profile hero input required')
    n=value.length208
    if n is None:raise UnknownProfileHero135('Selected profile name length208 is unknown;opening input omits it')
    if type(n)is not int or not 0<=n<=0xffffffff:raise ValueError('Explicit profile length u32 required')
    if n==0:return ProfileHero135('',b'',0,1,0)
    if value.resolved_utf8 is None:raise UnknownProfileHero135('Nonempty profile name requires resolved UTF8 bytes')
    if type(value.resolved_utf8)is not bytes or len(value.resolved_utf8)!=n:raise ValueError('Resolved UTF8 byte length differs from profile208')
    return ProfileHero135(value.resolved_utf8.decode('utf8'),value.resolved_utf8,n,None,n)

def empty_research_selected_profile_hero135():
    """Declared all-zero selected376 input of browser_entry_world135:41.

    The later opening harness preserves its name header while changing
    class/race/GUID/seed/companion slots. This is a fixture/profile contract,
    never an inference from absent fields or a natural account/menu default.
    """
    return produce_profile_hero135(SelectedProfileHeroInput135(0))
