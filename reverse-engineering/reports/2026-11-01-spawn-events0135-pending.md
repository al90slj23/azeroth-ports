# Remaining0.135.1 timed spawn branches: static evidence only

These observations come from the fixed `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2` original and the full WAT indexed in `wasm0135-profile-20261101T031028.877964Z`. They have **not** been promoted to independent producer acceptance. The actual Boss and elite production receipts are separate reports.

## Function947

The independently restored ordinary phase precedes the following ordered branches:

| State | Trigger/update visible in original | Status |
|---|---|---|
| G2440 | now>=deadline; choose unlocked elite; if first spawn succeeds and difficulty!=0, generate paired elite; deadline=now+max(25,55−2.5*minutes) | Actual full947 differential549/0;340 elite productions |
| G2424 | deadline<=now; choose one of event kinds0..3, excluding last G2586 when candidates exist; kind-specific actual5736 producers; deadline=now+max(35,60−1.5*minutes) | Kind selection, eligible weighted definitions, four geometry/count producers and messages still need independent composition |
| G2456/G2460 | One due scheduled Boss; difficulty>=5 final flag adds random first-four Boss at scalar0.6; after five, nonzero endless byte permits random five Boss every300s | Actual2785/full947 differential871/0;751 Boss productions |
| G2444 | now>=deadline; update to now+45; examine G1872/G1876 records with56B stride, limit types3..5 before calling1417 | Object/resource production and max-count condition remain pending |
| G2448 | now>=deadline; update to now+70/groupFactor; group factor uses mode1, G2140+1−G2548 bounded unsigned arithmetic and half scaling | Object/resource selection and1417 record production remain pending |

This table is a branch inventory; no pending row is counted as a recovered producer. Full947 test fixtures explicitly hold unrelated deadlines in the future.

## Function2376

The G1920/G1924 vector contains40B entries. If G2576 is nonzero, the initial queue production phase is skipped. Otherwise an entry with qword tag0 is eligible when now>=entry32; xyz is copied from entry16/20/24 and definition index from entry28. It calls original16341 for HP,42327 for attack, builds a scaled model, chooses model/name/ability variants through32969, and appends an actual424B unit. The entry is then tagged1 and the new GUID stored at entry8. Later behavior also selects a queue target using float-total-order comparisons; G392/G396, G2564/G2565 and G2392 govern target/display transitions, including a strict elapsed>300 condition.

Pending work includes:

- Independently restore HP16341, including boss-death/milestone contributions, and attack42327 (time polynomial, player-level1092 and difficulty factors).
- Recover32969 static variant declarations and the allocated ability payload. Its bounded variant RNG consumes a rejection draw beyond the ordinary angle draw.
- Recover the complete queue entry lifecycle, target changes and player-state coupling; the observed fields alone do not establish a generic spawn schedule.
- Invoke full2376 with explicit queue entries, real callees and read back both produced units and queue transitions, including due, future, tagged and malformed-source guard cases. Do not substitute the original HP/attack or variant callees with callbacks.

Static WAT slices for2376,947,2785,16341 and42327 are retained in `evidence/spawn-remaining135-static-20261101T042731.609817Z/`. The profile's original function index remains the authoritative source. These unknowns remain open toward a complete-game reconstruction.
