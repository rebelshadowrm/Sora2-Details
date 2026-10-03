# Selected item identity contrast

The player reported EP Charge II in the earlier capture, but the saved
[action packet](ACTION-STREAM-CAPTURE-PACKET-20261002.md) explicitly retains that
report as an annotation rather than a captured item identity. Subsequent
first-handler Transcript controls covered attacks, casts, buffs, reactions,
interrupts and boundaries; they did not supply two controlled item selections.
Do not repeat those covered mechanics. A live item-key contrast is the next
missing input; existing source bytes cannot reconstruct an unobserved selection.

## Existing capture and verified static metadata

Use the unchanged manual Transcript profile, supported executable SHA-256
`d8b2911d1576216bdc22d070550e4f531e105de7ed2981885849669f4acf8aaf`:
first actor-handler `7A68B`, effect-dispatch `DBE40`, resource setter `F8DB0`,
root `C5D768` plus byte `2D30` mode watch. First-handler snapshots preserve the
actor's bounded 0x1000 bytes, C70/C78/C88 descriptors, linked contexts and inline
status; dispatch and setter snapshots retain raw registers/descriptor/context
evidence. No additional hook slots or speculative item-pointer dereferences.

The exact-English ItemTableData payload at PAC offset `1A7CD4` has SHA-256
`16a8703a01e02ec9782d2d36dbdf1f3b150ba96982cf141c6a49f301a351abea`.
The existing fingerprinted parser verifies 1,382 unique IDs. EP Charge II is
item ID 6, row 148; Tear Balm is ID 1, row 143. Candidate table values 300 and
1500 are static metadata, not guaranteed applied amounts. Skills and party-name
joins keep their existing exact payload gates. No live field is currently
verified as the selected item ID; do not scan numeric coincidences into labels.

## Minimum player-controlled sequence

After the player confirms availability, arm capture and verify attached/armed,
the registered helper PIDs, committed ledger and source proof before requesting
actions. In one command fight, one character uses EP Charge II, then one
distinct healing item (Tear Balm preferred; exact alternative name is enough).
The same actor gives a cleaner selected-item contrast. Use a recipient with
missing EP/HP if practical; the actual selection remains useful if capped.
Other characters can guard. Finish normally and report actor, item, target and
execution order, plus any incidental effects. No particular enemy is required.

Keep recording armed until that finished report and recorded observations have
been checked. Request manual stop only then and verify detach/helper exit. No
duration or hit cutoff. If the sequence is unavailable, keep this packet ready;
do not ask the player to repeat guards, Dragon Dive, casts or interrupts instead.

## Offline interpretation and limits

Isolate both first-handler/context snapshots and each item's dispatch/setter
window without assigning the nearest resource write to an item. Compare raw
actor/descriptor fields, trace any differing key through exact native readers,
then test the exact item-table join against both selected items and non-item
skill snapshots. Preserve unknowns if no direct key is present; only then prepare
a targeted follow-up around the identified native item-selection/effect reader.
Do not infer an item ID from a heal amount, memory address or player report.

The app/viewer lifecycle and durable unknown-preserving stream are already
verified. This batch addresses the missing selected-item identity and its
resource outcome evidence, not another display or shutdown test. Full critical
flags, exact enemy unit identity, status applications and production command-only
boundaries remain separate coverage gaps.
