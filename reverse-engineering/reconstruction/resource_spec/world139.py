"""Independent139 Elwynn world from raw asset bytes and static declarations.

The terrain/M2/WMO/raster arithmetic is shared with the existing pure resource
library. Its135 names do not transfer135 acceptance:139 buffers and query
behavior require separately pinned139 observations/differentials. No snapshot,
original executable, precomputed world, profile or original function is input.
"""
from dataclasses import dataclass
from core_spec import binary32 as f
from .terrain135 import load_terrain_tiles
from .world_placements135 import load_world_placements,select_collision_instances
from .world_cache135 import produce_world_cache135

VERSION139='0.139.0'
BUILD139='f79c5e2b4'
# Actual139 zone152[0] at5871348, offsets96/104/108/112/120.
MAP_ID139=0
CENTER139=(3323121664,3290316800)
FALLBACK139=0x42880000
RADIUS139=0x42f00000


@dataclass(frozen=True)
class WorldBuild139:
    world:object
    grid:object
    ground_bits:tuple
    nav_before_connectivity:bytes
    stats:dict
    terrain_tiles:tuple
    selected:dict
    version:str=VERSION139
    build:str=BUILD139


def build_world139(provider,*,progress=None):
    """Declared default no-primary Elwynn path, not all maps/cache ownership."""
    if not callable(provider):raise TypeError('Explicit raw-asset provider required')
    tiles=load_terrain_tiles(MAP_ID139,CENTER139,provider)
    placements=load_world_placements(MAP_ID139,CENTER139,provider)
    extent=f.add(RADIUS139,0x41a00000)
    selected={phase:select_collision_instances(placements,CENTER139,extent,phase=phase)
              for phase in('nav_m2','nav_wmo','secondary_wmo')}
    built=produce_world_cache135(tuple(tile for _,tile in tiles),CENTER139,RADIUS139,
        FALLBACK139,selected['nav_m2'],selected['nav_wmo'],selected['secondary_wmo'],
        provider,progress=progress)
    return WorldBuild139(built.world,built.grid,built.ground_bits,
        built.nav_before_connectivity,built.stats,tiles,selected)
