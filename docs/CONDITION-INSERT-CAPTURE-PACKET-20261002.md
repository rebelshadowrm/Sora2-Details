# Condition insertion: offline result and next capture

The saved Conditions and Queue batches already contain populated 48-byte records.
Their first dword is the key used by native 7E470's exact table search.
`table_en.pac` payload at 13F659, size 8,963, SHA-256
`89d228d22acdb8bf3f064e4e0f921d29ca97d67ca457d8987639c96bb5908289`
has 52 unique ConditionInfoTableData rows (88 bytes each, starting at F8).
The parser checks payload hash, section layouts, unique keys and string bounds.

Exact candidate names: 27 STR UP, 28 DEF UP, 29 ATS UP, 30 ADF UP, 31 SPD UP,
32 MOV UP, 56 Fortune. Clock Up EX's recorded 31/32 records now carry names;
Saint's six recorded stat records and Wild Rage II's STR UP/CP Regen records
also gain candidate labels. Raw words remain uninterpreted parameters, not
measured stat changes. Unknown keys remain unnamed. Requests and post-call
collection snapshots are distinct observations; no request is called applied.

The reconciler previously omitted ConditionRequestEntry from its supported hook
map. It now accepts exact 7F750 under the same fingerprint/sequence guards and
preserves its pre-call collection with an application-unresolved stage. All ten
saved raw batches replay with identical embedded raw observations and hashes.
Candidate condition names reach actual WPF observation rows; saved replay,
refresh and malformed-update retention pass on the 160-record Queue batch.

The old return hook DE962 covers only one dispatch return site. It misses
Saint's separate selector-57/key-56 post-call route, and cannot establish general
condition lifetime. The new `ConditionInsert` profile uses four slots:

| Hook | RVA | Purpose |
| --- | --- | --- |
| EffectDispatchEntry | DBE40 | Descriptor and source/target inline context |
| ConditionRequestEntry | 7F750 | Requested key and pre-call collection |
| ConditionInsertReturnSite | 7FD63 | After 7FD5E calls insertion routine 7FE10 |
| ResourceSetEntry | F8DB0 | Independent HP/EP/CP writes |

Exact executable SHA-256 remains
`d8b2911d1576216bdc22d070550e4f531e105de7ed2981885849669f4acf8aaf`.
At 7FD63, R15 retains manager, R12 descriptor, EBP requested key, RAX returned
record; source context is saved at RSP+60. Manager[0] supplies target context.
Each context's 1D90 linked object's first pointer supplies bounded status bytes.
The existing vector bound remains 16 records; unreadable fields remain null.
This new profile is offline-prepared and has **not** been live-validated.
It does not claim complete refresh/removal coverage or primary action capture.

Next minimum player control: cast Forte on one living ally; let it resolve;
cast Forte on that same ally again; let it resolve; then cast Saint on that ally
and let it resolve. Report the actors/target and finish the fight normally.
First/second Forte compare initial insertion with repeated application; Saint
tests the previously unwatched Fortune return alongside its stat records.
No items, critical attacks or interrupt setup are required. This is a different
native observation path from previous cast tests.

Launch run_action_stream_probe.ps1 with `-CaptureFocus ConditionInsert` only
when the player is ready. Manual-stop mode has no duration/hit cutoff. Keep
armed through the finished report and inspection, stop via sentinel, verify
detach/helper exit/game survival, then project the saved raw source. No second
cleanup confirmation is needed. Remaining future gaps include refresh/removal,
measured stat deltas, automatic critical flags, and support ownership.
