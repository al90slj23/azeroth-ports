# Fixed135 initial player Aura and notification ID: scoped independent review

**Local static rules and the stated historical observation pass. Full indirect reachability remains unresolved.** No original, model, checker or trace producer was executed by this reader; no new original cases or mainloop frames are added.

- Original diagnostic trace: [4207c163…](/Volumes/RuiRui4TB/CloudBackup/Mac/code/github/al90slj23/azeroth-ports/reverse-engineering/evidence/player-aura-origin0135-static-20261101T220416.107301Z/trace.json), SHA `4207c163c4d5ed12aaae6c31f5d2fecf36126b2255e3a9a5e73b30a952dbaf37`. Its producer was8b72e813… without a saved producer source snapshot.
- Corrected trace: [38254937…](/Volumes/RuiRui4TB/CloudBackup/Mac/code/github/al90slj23/azeroth-ports/reverse-engineering/evidence/player-aura-origin0135-static-20261101T220724.149178Z/trace.json), SHA `38254937fd50ca7aa6c440ed9fc4aa32d25c8d1cb1862499737779be744c7474`; current producer SHA `ca6810fd59c74ced7be46d4aa343ded688614b65987a7b14bbda30f1511e2c1c`.
- Independent receipt: [review.json](/Volumes/RuiRui4TB/CloudBackup/Mac/code/github/al90slj23/azeroth-ports/reverse-engineering/evidence/player-aura-origin135-independent-review-owned-20261101T221224.005426Z/review/review.json), SHA `5511f8a811d71be384c2770f20073f147b3806eabd1831bd76269f4fe29d46b5`.
- Reader: [review_player_aura_origin135.py](/Volumes/RuiRui4TB/CloudBackup/Mac/code/github/al90slj23/azeroth-ports/reverse-engineering/scripts/review_player_aura_origin135.py), SHA `e9398f237d8dbf4ca7e6611c07c64faa45b0e485ca8f73c2d2c8cc25d4a0a97c`.
- Reader PID/PGID319 exited0, both absent,1.167876833s /60s; terminal SHA `b8598e9218ed060259ec91033d3fb0ce2dccaeb38d606f06c7f4f2b90fc1e45b`.

The source is original0.135.1 / actual build90898d5e3, WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`. The reader independently bound243 original function bodies and bounded WAT slices totaling2,953,961B, queried the profile read-only, and read no full1.3GB WAT. Original binary function identities, all primary windows and lexical direct calls match the indexed body evidence. The corrected trace preserves the old body/graph data while explicitly removing its overbroad final-state/no-ID-writer conclusion.

## Constructor writes: verified local rules

Original1560 allocates a2976B stack frame in local3. Its actual Game base is **local3+88**, passed to1512 and then copied as2592B to the output pointer. Therefore:

| Frame-relative write | Actual Game field/result |
| --- | --- |
| i64 store17179869184 at2088 | G2000 capacity0, G2004 pointer4 |
| i64 store0 at2096 | G2008 count0 |
| i16 store0 at2657 | G2569 initialized0 (also the adjacent byte) |

The function has one direct1512 call and no direct1202 call. These are actual body rules, not deductions from a caller graph. They support an explicitly empty Aura owner `(capacity,pointer,count)=(0,4,0)` before later effects. They do **not** prove by themselves that every indirect callee leaves Aura or App globals unchanged. Do not confuse frame offsets with Game offsets or use G1976 as the player Aura header.

## Conditional default-opening gates

The reader built structured block ranges from the real1089 body. Its first `G2576` conditional is the if at lines16–1214; all five2785 boss calls are inside its true arm. At the second check, branch line1890 is `br_if1` after `G2576.eqz`; its target block is1719–2517 and encloses the only direct5745 call. Thus a zero value **at each guard read** excludes those respective branches. This is a conditional statement, not proof that every possible caller or indirect callee preserves that value.

Original10146 builds its definition iterator from G2052 plus `36×G2056`; the zero-count path emits no followup definition rows and bypasses the5745 traversal. This gate likewise requires G2056=0 at that read. Nonempty definitions/debug/profile inputs are outside the rule.

Independently reproduced conditional direct graphs contain103 functions /297 edges from1560 and206 /670 from1089, excluding the three explicitly gated edges. They contain none of1202 or the known literal App14340336 increment consumers23581/42920/44447. The original constant index references14340336 in those three function bodies, and their load/+1/store sequences are verified.

**That is not an indirect or alias-complete nonwriter proof.** The union of the239 admitted direct-graph functions contains19 `call_indirect` sites (nine in the constructor graph,19 in the opening graph). This includes4546, which1089 directly calls before the first debug guard. The extra known ID-writer bodies contain another three indirect sites, giving22 across all243 inspected bodies. Every site is listed in the body proof. Their dynamic targets were not resolved; computed-pointer aliases to App14340336 were not exhaustively analyzed. “No target in this conditional direct graph” must not be rewritten as “no target can execute” or “the counter was never written.”

## Separate existing original observation

The reader also independently reread two complete historical memory captures from the prior entry-world probe, whose receipt SHA is `530f079d322365691ce897120ac0014be0da416eb048861b4d42ab988160556c`. They are **existing controlled observations**, not new cases, fresh model differences or a complete selected-profile/menu producer.

Their exact input identity is **Elwynn / class1 / race1 / object0 / app seed0 / explicitly empty372-live-byte selected profile in376B allocation**. This is not the750 trajectory's object42 or every character/profile route. The original functions6730 and1089 and every non-export WASM section are unchanged. Receipt artifacts, frozen historical sources, runtime capture hashes and full snapshot sizes match.

| Existing capture | Bytes | Snapshot SHA |
| --- | ---: | --- |
| after real world6730 | 117,440,512 | `f651042520491d22e9910b1c01b34eaf90c73e004a4cd60ce310428186d9291a` |
| after real begin1089 | 166,395,904 | `23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf` |

At Game14554176, **both** snapshots have Aura `(0,4,0)`, initialized2569=0, flags2576=0 and definitions2056=0. The four actual bytes at App14340336 equal1 in both. Each raw Game2592 slice also agrees with the historical observation readback. Original process54944 exited0; the old probe used its explicitly allowed local asset/import bridge, not this reader or a denied-all-import component runner.

These endpoint bytes prove those observed values for that controlled route. They do not prove that no intervening1202 call or ID write ever occurred, resolve the19 indirect sites, establish a universal origin rule, or validate the current object42 natural producer. A new controller may carry typed App nextID=1 explicitly with source-static initial data and this same-version example as provenance; the corresponding object42 natural producer still needs its own captured/independent input dependency evidence. These historical outputs must not be read into a new expected-first model to patch an otherwise unknown same-case result.

## Preserved identity rejection and boundary

The first auditor-only run99319 exited1/missing before body review because it incorrectly required today's corrected producer to have the old diagnostic producer hash. That rejection is preserved in `/Volumes/RuiRui4TB/CloudBackup/Mac/code/github/al90slj23/azeroth-ports/reverse-engineering/evidence/player-aura-origin135-independent-review-owned-20261101T221124.816964Z`. The successful reader binds the old diagnostic and corrected trace separately; neither trace nor production source was modified by this reviewer.

This report verifies the constructor constants/body gates, corrects the direct-graph scope, and records a narrowly identified historical endpoint observation. It does not close indirect-call targets, computed-memory writer aliases, arbitrary profiles/classes/objects, the menu producer, a current object42 natural initial state, full880 or a complete game. No production file, primary report, registry, installation or save was changed, and this reviewer staged or committed nothing.
