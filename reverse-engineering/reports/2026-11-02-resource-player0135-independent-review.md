# Fixed135 resource player2088: independent read-only review

**Scoped pass:** all **38 cases /56 complete original2088 calls**, independently reread and recomputed with **0 new original/model/checker executions**. The implementation under review is a resource-live expiry/stat/Aura/regeneration prefix; its original oracle executes unchanged full2088 with controlled empty learned entries and future basic/prelude timers. This is not mainloop, natural pickup or full-game acceptance.

- Original comparison: [comparison.json](/Volumes/RuiRui4TB/CloudBackup/Mac/code/github/al90slj23/azeroth-ports/reverse-engineering/evidence/resource-player0135-oracle-20261101T214934.226082Z/comparison.json), SHA `82719c31ea3de180d1a4b0c036d1a6764bd1518f3a1cdea17e3a627b6d85024d`.
- Independent receipt: [review.json](/Volumes/RuiRui4TB/CloudBackup/Mac/code/github/al90slj23/azeroth-ports/reverse-engineering/evidence/resource-player135-independent-review-owned-20261101T215955.300921Z/review/review.json), SHA `8d3159228fe880c3f9153b08a3e36adb8226bd7c5c82ca309b5e8f0429b5de10`.
- Reader: [review_resource_player135.py](/Volumes/RuiRui4TB/CloudBackup/Mac/code/github/al90slj23/azeroth-ports/reverse-engineering/scripts/review_resource_player135.py), SHA `38ed70f2962075a01de9c7e99c9b8acd3ae94efabf9538bd1f52436ad4874535`; six local reviewer sources are separately snapshotted.
- Original WASM version0.135.1, actual build90898d5e3, SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`.
- Original Node PID/PGID75587 exited0, both absent,3.148874917s /60s. Reader PID/PGID87925 exited0, both absent,6.634226959s /60s; independent body is bound in the receipt.

## Verified state, data and source closure

All37 execution sources /30 production files /124 local import edges match both frozen snapshots and current files. Production AST has no original/evidence/network reads or dynamic execution. All frozen inputs, labels, expected data, module and manifest hashes match. The original export section alone adds2088 and stack-global bindings; all function bodies and every other WASM section remain unchanged. Seven function identities and bounded WAT slices (2088/1512/1202/1453/1076/10529/29537) were rebound to the original and the read-only profile index.

The frozen launcher generated expectations before original execution. Runtime proves38 fresh instances,56 full2088 calls,221 returned/restored stack guards,0 host calls,878 denied imports, peak20,578,304B under32MiB WASM and512MiB JS heap caps. Original stdout is1,207,982B under4MiB. The reader launches none of these execution components.

| Independent comparison | Result |
| --- | ---: |
| Known values | 23,309 |
| Physical `None` cells | 30,416 |
| Unknown cells nonzero in original | 6,085 |
| Live `None` bytes exactly retaining A5/5A input poison | 692 |
| Dirty1512 recalculations /1202 Aura rebuilds | 49 /49 |
| Aura writes / forced66-key initializations / valid48-cache comparisons | 1,645 /24 /25 |
| New exact226 packets / action u32 wraps | 35 /1 |
| Cumulative raw queue observations | 47 |
| No-dirty stages / full32 stable compaction stages | 7 /14 |
| Regeneration HP-key writes / negative-dt / zero-dt stages | 52 /1 /1 |

All23 derived words, known HP/pool/speed fields, keyed fields, action sequence, RNG/counters, every full32B live backing row including inactive shifted tail, and the48×16B Aura owner with known masks were independently compared. No dirty state retains byte-identical actual Aura backing across subsequent stages; initial no-dirty Aura fixtures also preserve their exact injected bytes. Aura unknown cells remain explicit, rather than being asserted zero. All226 payload bytes and their cumulative order match; other wire shapes and1453 statistics/presentation remain outside the prediction scope. There happen to be **0 non226 raw packet observations** in this controlled batch, which does not reconstruct the unexercised1453 wire branches.

The known projection was rebound to raw Game8192, vector headers, full stored rows, keyed-field readback, queue metadata/lengths/payload bounds and Aura initialization byte. FullGame arbitrary writes and allocator/BTree addresses are observed, not claimed independently predicted. The manual Game8192 / World128 / empty-source and single-leaf initial keyed fixture is not a full original constructor or memory snapshot. Notification global14340336 starts1 and stays1. Actual locale/once state starts28 zero bytes and naturally reaches once flag3 in all38 instances; the runner did not inject it.

## Rules independently checked

The actual original order is2088 scan/dirty retain →1512 recalculation →1202 Aura → pool minimum/HP regeneration →1453 accounting →1076. The independent prefix stops before1076. Full original2088 still invokes1076, but the learned vector is empty and the real cleave80/basic cooldown plus class-prelude timer areInfinity; their physical owner bytes remain unchanged, so no learned/basic attack behavior is silently attributed to this prefix.

The reader reconstructs the dirty predicate `now >= expiry`, followed by stable retain `now < expiry` only when at least one expiry made the pass dirty. It retains full32B rows and inactive bytes, checks strict10s/15s boundary sequences, all six record permutations, duplicate kind0 first-owner behavior, positive unique kind8 coexistence, and cold/valid/bit-initialized Aura caches. Kind0 resource23451/23505 never reads its unknown+12 magnitude; only the separate kind8 branch reads a finite positive magnitude. Every modeled live unknown byte preserves its exact nonzero input poison.

HP and regeneration cover below-cap, near-cap, at-cap and above-cap inputs; heal gates0/5; finite dt0/.001/1/-.1; pool1448=min(pool1444,pool1448); controlled classes1/2/8/9; keyed HP ceilings and speed/action overflow. All full raw226 packets are rebuilt from the actual player GUID, previous action word and independently computed speed. The seven refused-domain artifacts were read and hash-bound, not rerun or counted as original verification.

**Three-second scope:** elapsed inputs immediately below/equal/above3s were compared, but all tested derived1620 values are0. The nonzero `maxHP ×1620` extra-regeneration path is **not dynamically validated** by these cases. Other periodic/shield/proc/live families are pending.

## NaN distinction and retained reader failure

The original2088 pass does not dirty on a NaN expiry (`now >= NaN` is false). A NaN record alone therefore remains; when another record causes dirty, strict retain `now < NaN` is also false and removes it. The fresh original cases independently confirm2 no-dirty NaN-retention stages and2 co-dirty NaN removals.

A separate subtlety is static: **1512 skips only when `expiry <= now`**, so NaN is not skipped, whereas **1202 accepts only strict `expiry > now`**, so NaN is not selected for Aura. The new reviewer reproduces this distinction when reconstructing the manually prepared initial state. This batch's actual dirty retain removes NaN *before* the subsequent1512/1202 calls; it therefore does **not** add dynamic original validation of1512/1202 with a still-present NaN. Keep this static/fixture evidence separate from actual2088 NaN differential evidence.

The first auditor-only run PID85303 failed during the initial stats check because a reused earlier reviewer helper had only been scoped to finite expiries and used strict live selection. Its stderr and exit1/missing terminal remain in `/Volumes/RuiRui4TB/CloudBackup/Mac/code/github/al90slj23/azeroth-ports/reverse-engineering/evidence/resource-player135-independent-review-owned-20261101T215803.883842Z`. Only this new reviewer was corrected after checking original1512's ordered `f32.le`; no production source, input, expectation or original execution changed. That failed run did not snapshot its reviewer source before failing, so this report does not invent a preserved old source hash. The successful reader snapshots all six of its sources.

No1453 presentation/logging/statistics implementation, full1076 scheduling, natural resource collection, full880, full game or native platform acceptance is claimed. Existing installations/saves, primary reports and registry were untouched; no staging or commit was performed by this reviewer.
