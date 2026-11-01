# Gameplay phase135 independent review

Fixed0.135.1/0898d5e3. No original execution or author-source modification occurred.

- `evidence/full0135-oracle-20261101T060633.862339Z`: 285cases / 444stages, snapshot-model regeneration and strict raw result equality passed; source/init closure and non-export bytes passed.
- `evidence/full0135-oracle-20261101T061549.649714Z`: 396cases / 1136stages, snapshot-model regeneration and strict raw result equality passed; source/init closure and non-export bytes passed.

Movement:604 complete original221 packets independently decoded for GUID/sequence/stop flag; NPC records remain unchanged, sequence wraps and duplicate GUIDs preserve order. Pause/resume is not a no-op.

- Player2088 isolation uses actual racial record with Inf cooldown and empty learned vector; it is not a legal opening schedule.
- Physical heal/aura/account outputs and unmodeled player keys remain outside helper projection.
- Movement packet GUID/sequence/flag and complete NPC preservation are independently proven; packet geometry/terrain and nonempty112B auxiliary/88B claims remain unresolved.
- Command1371 tests pause1↔3; natural choice pause1↔2 and actual headless integration need their separate same-state receipt.
- Current builder/host may have coordinated additional exports; each reviewed batch is bound to its own intact snapshotted sources.

Receipt: `evidence/gameplay-phase0135-independent-review-20261101T062048.752446Z/review.json`
