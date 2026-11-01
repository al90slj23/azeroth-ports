# 0.135.1 ordinary-death world placement

The new pure `ordinary_placement135.py` produces deathXYZ and both potential XP/coin placements from the live pre-hit424B entity. The existing death model still owns reward chance, record merging/caps, counters and entity RNG. No existing validated model, unit-record bridge or controller was changed.

- Duration<=0 reads endXYZ. Otherwise each coordinate uses the original binary32 interpolation and0..1 time clamp.
- XP uses deathXY. Coin adds binary32 0.8 independently to X and Y before applying its own world clamp.
- Each1417 request uses the fixed map center and max(1,radius−2). Outside this circle, each axis is center+((axis−center)/distance)*limit in that exact rounding order.
- Final record height comes from the flat/base world height, including nonzero V116 fallback when flat mode is disabled. DeathZ is preserved for the dead unit and can differ from both drops.
- Terrain/grid/navigation absence must be explicitlyTrue; defaults reject. Live unflagged ordinary tags and the current zone's definition are required.

The final fresh original differential is **924 cases,0 differences**:396 direct complete1417 calls and528 complete914 lethal hits with actual internal1417/1821 callees. All12 zones, centers/circle edges/outer positions, ±epsilon boundaries, pre/during/post movement clocks and48 nonzero base-height fallback cases are covered. 726 XP records and542 coin records were compared; 344 dual drops included335 distinct XP/coin XY cases. 516 lethal cases distinguish drop height from deathZ.

The complete56B records are compared bit-for-bit. Prior record slots are explicitly A5-filled, so even the unwritten arrival word is checked against its declared prior value; no field/address masks or NaN relaxation are used. RNG, spawn/message counters, kill-cost accumulator and death endpoint/time fields also match. Eight pure rejection checks are separate and are not added to original differential coverage.

Receipt: [`ordinary-placement135-comparison.json`](../evidence/full0135-oracle-20261101T052411.434992Z/ordinary-placement135-comparison.json), SHA256 `49def1217c03905bad0fcefaab63ae1ab195528905b965c30ef5d0290665209e`. Source snapshots/expectations precede original execution. Original bytes are fixed to `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`; only export section7 changes, all internal callees remain original,878 host imports throw. 58 fresh instances, peak20,709,376B, 1.824s; no app start, network, EXE or save access.

Real terrain/height grids and navigation remain pending. Existing-pickup merge/cap producers, nonordinary/flagged death routes, physical object/packet serialization and a complete natural game loop are not established by this bounded placement suite. The previous876 suite remains historical and is not added to924. Independent review is pending.

Final source freeze also includes package __init__.py and its upgrade_values dependency, as requested by independent review; no placement logic changed. Earlier924 receipt051809 remains retained.
