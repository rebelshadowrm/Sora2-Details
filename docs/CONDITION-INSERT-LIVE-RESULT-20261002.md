# Condition insertion and repeated application, October 2, 2026

Batch `c96528cbd8894c4a848b8de92d73b9e7` captured the player's Estelle sequence
Forte, Forte, Saint, approximately three defends, then Agate's Dragon Dive.
Inline source/target status identities identify Agate as the buff target.

Final raw count: 679. SHA-256:
`7ca09003c15fe352f22a3d6d09c7726adb494cc2609d7be31bf14a95ab0cc6c9`.
All unknown and later observations remain stored. This profile observes effect
and condition routes; it has no primary-action or battle-boundary hook. Its zero
primary action candidates are not evidence that no actions occurred. Dragon Dive
has 45 effect calls, not 45 proven hits. No automatic Victory result is asserted.

## Controlled record changes

| Return record | Descriptor candidate | Condition key/name candidate | Observed change |
| --- | --- | --- | --- |
| 41 | Forte | 27 / STR UP | Record added; collection 0 to 1 |
| 44 | Forte | 22 / CP Regen | Record added; collection 1 to 2 |
| 79 | Forte | 27 / STR UP | Existing payload updated; collection stays 2 |
| 82 | Forte | 22 / CP Regen | Existing payload updated; collection stays 2 |
| 119 | Saint | 27 / STR UP | Existing payload updated |
| 121, 123, 125, 127, 129 | Saint | 28–32 / DEF, ATS, ADF, SPD, MOV UP | Five records added |
| 132 | Saint | 56 / Fortune | Record added; collection 7 to 8 |

Each controlled pair has adjacent request/return sequence numbers, the same
thread, manager, requested key, descriptor pointer and full B0 descriptor bytes.
Both collections are complete and uniquely keyed. The returned RAX record
matches the requested key and the independently captured post-call array.
Partial arrays, sequence gaps, descriptor/context mismatches and duplicate keys
do not acquire transition labels. Parameters at record +4 and +10 change across
the three STR UP returns (1/15, 2/30, 3/45); their units remain undecoded. Agate's
six raw stat words at status+24 stay unchanged (6627,1212,3923,1209,190,44).
Neither those parameters nor the unchanged snapshot are substituted for an
effective stat delta. Native runtime calculations require separate tracing.

Additional key-52 Overdrive Sign changes retain unknown source/move. Dragon Dive
returns records with keys 37 STR DOWN and 39 ATS DOWN; enemy target identity is
unresolved. Requests without a matching insertion return, including key 1 Poison
and key 5 Burn, remain requests and are not declared applied or resisted.

## Persistence, presentation and cleanup

The actual growing WPF observer verified all 679 final observations before
closing. Offline enrichment retains the original source hash and exact embedded
raw records. The pre-enrichment ledger and derived transition summary are kept
alongside the raw, controls, session and audit in
`%LOCALAPPDATA%/Sora2 Details/research/action-stream`, using the batch ID.
Core and actual WPF observation rows now show source, descriptor, target and
Added/Updated candidate changes. Saved replay verifies these rows, raw selection,
refresh and malformed-update retention. Snapshot/timeline/bridge checks (24),
reconciliation checks (36), item checks (4), core checks and Release build pass.

After the finished report and initial saved-sequence inspection, manual sentinel
yielded disarmed 22:48:11.513, detached 22:48:11.837. Launcher 40704 and bridge
37452 exited; viewer 22268 verified the final hash and closed at 22:48:25.903.
Game 29960 remained running. The completed manifest is archived and the separate
active-condition-session marker removed. No second confirmation was requested.

This closes the insertion/repeated-application gate, including Saint's previously
unwatched key-56 post-call route. Expiration, explicit removal and battle cleanup
are distinct missing lifetime observations. The next
[removal packet](CONDITION-REMOVE-CAPTURE-PACKET-20261002.md) prepares that route.
