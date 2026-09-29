# Healing attribution and ambiguous enemy lookup, 2026-09-28

The 02:54:42 command battle in the local encounter store contains nine effective
healing events. Every one has `sourceId: null` and `moveName: "Unattributed HP
write"`. The 02:54 fight also contains an unnamed main enemy, runtime ID
`60014`, whose six-stat signature matched **two** exact English `t_status`
rows. Its Broken Piece E and Guard Minion E adds matched unique rows. A second
fight at 02:57:29 similarly left main enemy `60016` ambiguous with two rows
while naming both Broken Piece E adds. Runtime IDs are battle-instance IDs,
not stable table keys.

The encounter snapshots record these observations, but their referenced raw
trace `probe-session-9cdd7363e4eb4354b300e219cfc51d90.jsonl` could not be
located during this audit. The old snapshot retained only `candidateCount`,
so the exact two candidate names for these historical fights cannot be
recovered from the snapshot. A player-reported on-screen name would identify
the historical instance, but would not prove an automatic runtime lookup.

The current `AttackEffectCall` hook verifies damaging results when paired to
the HP setter on the same thread. The HP setter reports target and before/after
HP but no verified healer, item, move, or support-proc identity. Therefore the
bridge preserves these healing events as unattributed. It must not assign the
nearest attack or prior command as the source. The bridge now leaves a pending
attack in place when an unrelated HP write occurs, so that a later matching
damage write can still be paired.

Future captures retain the observed six-stat signature and every exact table
candidate (`unitId`, `name`) on the enemy actor in encounter JSON. The HP
setter's raw JSONL record now includes 64 bytes of stack context and a frame
return **candidate**, for grouping healing paths offline. These fields are raw
research evidence only; they are not displayed as a verified source or move.

The next controlled live check needs one known ability heal and, if practical,
one random support-proc heal with user-reported actor/move/recipient. Compare
their HP setter frame context to one ordinary attack and to each other, then
trace back to a stable executed-action or effect descriptor. For the unnamed
enemy, capture its displayed name and inspect its two saved candidate keys;
seek a direct runtime unit key if both remain stat-identical. Any future
source/move join needs a second independent live validation before enabling
automatic attribution.

The probe can retain extra evidence at the HP setter before its memory changes.
For the first 16 positive HP writes per `BattleInit`, its raw JSONL record now
includes a `diagnostic_snapshot` with 256 bytes around the current stack and
frame, tagged `hp-write-without-attack-result`. This is a bounded research
snapshot; stack words are candidate pointers, not verified healer or move IDs.
Short live captures now retain the attack effect descriptor as well, so a later
`effect-descriptor-missing` or table mismatch can be reviewed against the raw
observation. If the descriptor itself cannot be read, the first eight such
results per battle also retain the bounded 512-byte result frame at the hook.
Enemy identity captures retain first-seen status/context and linked-object
bytes for each battle. The hash-gated exact English table is now loaded before
the probe attaches. If a live enemy signature matches zero or multiple unit
keys, the probe records candidate keys and a wider, bounded context/link/actor
snapshot while the attack breakpoint is paused (at most eight enemy pointers
per battle). This preserves evidence for a direct runtime key search; it does
not choose a name. A later bridge lookup result cannot safely request memory
after the breakpoint has resumed. AI-skill-ID failures still need a separate
action-context hypothesis before expanding their memory reads.
