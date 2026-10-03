# Action stream progress and next evidence gate

The goal remains an authoritative ordered action/event stream, including unknown
events, followed by evidence-backed enrichment. The present raw research ledger
is lossless for recorded observations, but is not a complete battle event stream.
Preserving what was recorded does not prove every game event was observed.

## What the captures established

| Capture | New evidence | Limit |
| --- | --- | --- |
| Last night | An exact Tear descriptor and a direct numeric healing request/calculation route. | No independent post-heal HP confirmation; not a universal action boundary. |
| Morning conditions | Clock Up EX and Saint reached condition application paths without requiring damage; raw condition collections and source/target contexts were saved. | Condition IDs and parameter words do not yet have verified stat semantics. |
| Queue capture | Forte and Saint had distinct pending-store/resume observations. Wild Rage II occurred between Saint preparation and resume without consuming Saint's identity. Morale EX and Dragon Dive descriptors reached effects. | These observations cover selected routes, not all actions. |
| Setup capture | Zodiac showed that the proposed setup hook repeats while a cast is pending: 1,210 pending setup visits versus one post-resume setup visit. An actor-to-effect-source pointer chain was corroborated. | The setup helper is rejected as an execution boundary. A five-minute cutoff missed later actions in the second fight. Crit, miss, counter, Sacred Arrow, and Overdrive identities remain unresolved. |

The controlled actions were sometimes similar, but the hooks and questions changed.
The setup result is useful negative evidence: counting or deduplicating those calls
would produce a misleading action log. Further captures with that unchanged hook
would not address the problem.

## Recording changes implemented

1. Player-controlled research uses a unique stop sentinel, without a time or hit
   limit. Check saved observations after the player finishes; then stop and verify
   detach. Synthetic tests exercise survival beyond both previous limits.
2. Every serialized observation has an ordered sequence and monotonic timestamp.
   The replay embeds every input record, including unknown hooks, IDs, markers,
   and incomplete snapshots. Gaps invalidate correlation rather than create an
   inferred interrupt or cancellation.
3. Queue correlation requires the same thread, actor, descriptor pointer and all
   inline descriptor bytes. Names are separate exact-table candidates; pointer
   equality across sessions is not lookup evidence.
4. The revised `Stages` profile observes actor handler entry, the animation queue
   call return, broad effect dispatch, and resource setter entry together. It
   retains pending descriptors inline. Resource changes are not automatically
   attributed to the latest action, and effect rows are not counted as actions.
5. Verified repeated state updates are filtered before serialization. Unknown or
   unreadable layouts remain recorded. First state entry and animation launch
   are separate candidates, each explicitly marked execution-unconfirmed.

Offline disassembly found a Guard path that skips a fresh animation launch when
the defend bit is already present. That ruled out using animation launch alone.
The common actor state callback at `+0x7A68B` selects the registered handler before
its update counter increments. The candidate layout has owner `RCX`, embedded
machine `RBX = owner + 0x88`, and selected state record base `RSI`; counter zero
identifies a first update. This is exact-build static evidence, pending live
validation. It does not imply every first state update is one player action.

## Verification and remaining work

Nine snapshot checks and 22 reconciliation checks pass. Synthetic hardware probe
attach/hit/detach, manual-stop, and live bridge checks pass. Release solution build
has no warnings/errors; core replay, projection, recorder and persistence checks
pass. The PowerShell launcher parses successfully. The three saved captures replay
with all 2,459 records preserved and raw hashes unchanged. These are offline and
synthetic checks, not proof of the revised hook's live behavior or desktop display.

The immediate dependency when this note was written was one live `Stages` capture described in
[the capture packet](ACTOR-STAGES-CAPTURE-PACKET-20261002.md). Existing traces cannot
provide register snapshots at addresses they did not watch. After that capture,
continue offline reconciliation and implementation without another permission
checkpoint. If the proposed boundary fails, preserve the failure and follow its
actual route before requesting another player batch.

That capture has since completed. See [actor stages live result](ACTOR-STAGES-LIVE-RESULT-20261002.md)
for distinct repeated guards/attacks, two pending/resume/main cast links, support
descriptor candidates, resources, and launch-register recovery. This supersedes
the immediate live dependency above; production gates below remain open.

Remaining project gates include validated event boundaries and coverage, durable
production ingestion and encounter boundaries, verified source/target naming,
effect/resource attribution, desktop event presentation and replay verification.
Crit/miss/counter, support procs, turn-free activations, explicit interrupts, and
stat deltas require their own evidence. Four hardware breakpoint slots constrain
this research profile; a production recorder must cover the validated routes
without presenting a single research profile as a complete stream.

Ending earlier turns at an offline milestone was a workflow mistake. User input
is not required to analyze existing captures, follow native callers, implement
supported changes, or run verification. The repository working protocol now says
to continue that work until an actual missing input or live-control dependency.

## Interrupt and durable transcript update

The [interrupt capture](INTERRUPT-LIVE-RESULT-20261002.md) corroborates a pending
enemy cast canceled through the native impede route while the enemy survived.
Its enemy spell label remains unknown. Seven primary action candidates and all
981 raw records persist in the research ledger and are displayed by the WPF
recorded action stream viewer, with actor/target candidates and raw evidence.
This is a separate research projection rather than verified meter history.

`action_transcript_bridge.py` now watches a growing raw file, waits for complete
lines, atomically publishes snapshots and completes after detach. Byte-length
and SHA-256 identify the exact committed prefix. The core reader verifies raw
content against that prefix; the viewer follows ledger updates and retains its
last valid snapshot if a later update fails. Unknown records survive both paths.
The Transcript launcher starts this bridge alongside the manual-stop probe.

Verification: Release solution build passes without warnings/errors; core
replay/persistence checks pass; 28 reconciliation checks and 16 snapshot/timeline/
bridge checks pass, including a watch subprocess that waits for detach. Synthetic
hardware pointer-write attach/detach and manual-stop checks pass. Actual WPF replay
of this batch displays seven candidates and 981 observations; automated WPF
refresh and malformed-update retention checks pass. Five simulated capture
shutdown modes also pass. Those tests use an isolated named pipe, avoiding the
running installed application's pipe; they do not attach to the live game.

The next actual input dependency is one field→command battle→field contrast
for the native mode flag. [The prepared packet](TRANSCRIPT-CAPTURE-PACKET-20261002.md)
collects that flag alongside first states, broad effects and resource setters
without a capture cutoff. Until validated, scope remains a candidate and cannot
be promoted into normal command-battle encounter creation. Production ingestion,
entry state, unobserved action families and complete outcomes remain incomplete.

The field/battle contrast has now completed; see
[the transcript live result](TRANSCRIPT-LIVE-RESULT-20261002.md). All 487 records
and six primary candidates are retained and saved WPF replay passes. The extra
code-3 interval was initially associated with the quick kill; later analysis
shows living enemies at that exit, so this timing interpretation is withdrawn.
Command-only scope and the exit enum remain candidates. A neighboring-byte watch event originally reset
the interval; exact native writer validation and unchanged-low-byte handling fix
that failure on this same saved capture. Both intervals now close in replay.
Raw exit arguments differ (1 and 3), but outcome/mode enums remain unresolved.

The probe now additionally snapshots bounded initializer flags and roster/status
bytes at mode writes. Offline snapshot, reconciliation, bridge, hardware lifecycle,
core and saved desktop checks pass (17 snapshot/timeline/bridge checks and 29
reconciliation checks). The new inline fields require a live control; existing
raw records cannot reconstruct memory they never read. The next prepared contrast
needs only one command Guard plus finish, then one quick field kill, rather than
repeating casts or interrupts. The current probe is detached; the game remains
running. Production command-only scope and actual live desktop display remain open.

The [revised multi-attempt capture](MODE-FLAGS-LIVE-RESULT-20261002.md) now retains
all five completed intervals, 28 primary candidates, 2,310 raw records and five
complete roster snapshots. The final Guard/Dragon Dive fight is isolated; 185
effect calls and 69 resource writes after its exit remain unframed. Flags 0x11
and 0x34 are observed opening-pattern candidates, not verified advantage enums.
Result code 3 appears with living enemies; an earlier-escape clarification is
now confirmed: the player intentionally used Wild Rage II for CP and escaped
to prepare the next fight. No more action repetition is currently needed.

The core reader/viewer now validate interval links and offer interval/unframed
filters. Refresh preserves the selected fight and unknown records. Effect-call
rows gain inline source/target/descriptor candidates even when no primary action
is linked; unknown/incomplete names remain explicit. Unrecognized future record
kinds remain unknown rather than being assumed capture markers. All raw data
stays unchanged. Saved WPF replay, filtering, refresh and malformed-update checks
pass, alongside core/build and 31 reconciliation/18 snapshot-timeline-bridge checks.
These are research capabilities; production ingestion, comprehensive event
semantics/outcomes, entry-state timing and real live desktop validation remain open.

The read-only viewer can now launch directly with `--recorded-stream <ledger>`,
independently of the normal meter and its elevation/capture startup. A tested
offscreen observer follows the same WPF path and audits displayed raw/action
counts and source-prefix verification until a manual stop sentinel. The next
prepared live gate is [game-to-viewer display](LIVE-TRANSCRIPT-DISPLAY-PACKET-20261002.md),
requiring only a brief fight or reported normal play, not repeated mechanics.

The confirmed Escape control now enriches exact-route exit code 3 as Escape
(candidate), with the explicit earlier Victory/code-1 control as contrast. Other
codes and verified outcomes remain unknown. Raw registers and player provenance
are retained separately; invalid values or neighboring writes do not gain labels.
32 reconciliation checks and the saved desktop/core checks verify this change.

The [real growing transcript display](LIVE-TRANSCRIPT-DISPLAY-RESULT-20261002.md)
now passes: Guard, Heat Up II effect observations, Dragon Dive, and a Victory
candidate reached the actual WPF viewer while armed. Every raw observation was
preserved; final 206-record source proof matches the saved ledger. Probe/bridge
exit, viewer exit and game survival were checked independently. The initial
writer-sharing failure was repaired and verified on the same active recording.

Action stream (partial) is now wired to normal desktop start/stop and active-ledger
opening, with a separate long-lived manual recording owner and registered helper
PIDs. Seven simulated shutdown cases pass. This remains research ingestion,
separate from verified encounter history and meter projections. A dedicated
real-game lifecycle harness exercises normal desktop handlers without requesting
another combat sequence; its elevation requirement matches production startup.

That elevated real-game lifecycle check now passes, including live source proof,
active-ledger opening, manual Stop, separate helper exit, owned-viewer/app close,
and game survival. A PowerShell lost-exit-code defect discovered during the first
run was fixed and the strengthened same-path check repeated successfully. The
pinned embedded runtime reproduces the finalized live ledger exactly using the
new installer dependency list. No release was published or installed.

The next missing player-controlled contrast is
[selected item identity](ITEM-IDENTITY-CAPTURE-PACKET-20261002.md). EP Charge II's
earlier chat annotation never proved a runtime item key, and later first-handler
batches did not include controlled items. The prepared unchanged Transcript
profile needs two distinct items used by one actor, rather than more repetitions
of the already-recorded guard/cast/interrupt/finisher sequences. Native key/table
joins remain unknown until that evidence is present.

The [completed item contrast](ITEM-IDENTITY-LIVE-RESULT-20261002.md) now resolves
both generated action descriptors to Tear Balm and EP Charge I using a native
constructor reconstruction and exact table bytes. These are generated keys,
not original item IDs; 398 eligible rows include two photos before Tear Balm.
Both names reach the saved WPF action rows, and all 467 observations/raw bytes
remain preserved. Independent later snapshots show HP +1950 and EP +195 without
substituting base table values. A transient Windows atomic-replace defect was
fixed and reproduced with a real locking reader; live projection was recovered
without repeating controls or restarting the raw probe. All helpers/viewer exited
and the game survived. The remaining direct-ID gate needs one item use with the
new bounded B8 companion read; no more EP consumables are needed.

The [direct item-ID follow-up](DIRECT-ITEM-ID-LIVE-RESULT-20261002.md) passed:
Agate's Tear Balm action and effect snapshots independently read native item ID
1, agreeing with the generated descriptor and exact item-table row. All 154
observations and the +1950 HP readback remain source-verified. Manual cleanup,
helper/viewer exit, and game survival were checked separately.

Further offline work now joins saved condition keys to exact candidate names,
including SPD UP/MOV UP for Clock Up EX and six stat buffs for Saint. Ten saved
batches replay without changing raw observations or hashes, and actual WPF
condition rows pass. The [prepared insertion probe](CONDITION-INSERT-CAPTURE-PACKET-20261002.md)
replaces the narrow dispatch return with a general insertion-return observation.
Its live validation needs initial/repeated Forte and Saint on the same ally;
stat changes and complete condition lifetime remain unresolved.

The [condition insertion live result](CONDITION-INSERT-LIVE-RESULT-20261002.md)
now closes that gate: Forte first adds STR UP/CP Regen, repeated Forte updates
those existing payloads, and Saint updates STR UP and adds five stat records
plus Fortune. Source/target identities independently read Estelle/Agate.
All 679 observations are source-verified and preserved; exact before/after
transition candidates now reach core and WPF rows. Parameters are not mislabeled
as measured stat deltas. Cleanup completed without another confirmation.
The next live dependency is a disappearing buff under the prepared
[removal-route probe](CONDITION-REMOVE-CAPTURE-PACKET-20261002.md), with native
failed returns and battle cleanup kept separate from within-fight expiration.

The [removal live result](CONDITION-REMOVE-LIVE-RESULT-20261002.md) now captures
Agate STR UP's five-to-zero counter and exact zero-counter expiration caller,
separate from later bulk clearing with nonzero timers. `Expired`/`BulkClear`
candidates reach core/WPF; all 457 observations and all twelve saved batches
remain intact. Timing is actor-scoped, with special cases still unresolved.
The next [cure contrast](CONDITION-CURE-CAPTURE-PACKET-20261002.md) uses exact
dispatcher cure callers and bounded source/descriptor reads; the player chooses
a fight and available cure. No repeated Forte/expiration control is required.

The [cure live result](CONDITION-CURE-LIVE-RESULT-20261002.md) closes the explicit
removal contrast: Estelle's Curia erases Kevin's active Pommify at nonzero timer,
with independent caster/move/target snapshots and the exact cure caller. Kevin's
Curia on Agate supplies the no-debuff contrast. Corrected replay and actual WPF
checks pass; all 207 raw observations and thirteen completed batches remain
intact. Manual cleanup completed and the game survived.

Offline work has prepared and tested the
[condition-attempt profile](CONDITION-ATTEMPT-CAPTURE-PACKET-20261002.md), capturing
early null returns as well as successful insertion. Unknown rejection causes
remain unknown. Its remaining dependency is an enemy condition attempt against
an ally protected by a reported immunity skill; the previous probe cannot
reconstruct these missing native request/return bytes.

The [condition-attempt live result](CONDITION-ATTEMPT-LIVE-RESULT-20261002.md)
now verifies all 58 common returns (51 condition-record returns, seven nulls).
Sylpharion's first Pommification was reflected back to the enemy, so its null
return is not mislabeled as Kevin resisting. The later attempt adds Pommify to
Kevin. His Overdrive precedes both disappearance and the second Sylpharion's
resolution. Native Overdrive cure callers are mapped and offline tested; the
batch did not capture their removal entry/returns. All 464 records and fourteen
completed batches remain lossless. Capture/helpers/viewer stopped; game survived.
The next live immunity contrast should use Sylphen Guard without reflection,
or a second attempt after consuming reflection while immunity is still active.

The [group-immunity follow-up](DEBUFF-IMMUNITY-LIVE-RESULT-20261002.md) now supplies
direct Pommify null returns on Kevin and Agate while active Debuff Immunity is
present and Reflect Arts absent. The actual descriptor is Sacred Breath II.
Both complete collections are unchanged, and prior unprotected application
provides the contrast. Core/WPF now show protective context without claiming a
watched rejection branch. All 376 observations and fifteen completed batches
remain intact; cleanup and game survival pass. The reported enemy teleport
remains separate from unavailable native battle-outcome evidence.
The [combined lifecycle profile](CONDITION-LIFECYCLE-CAPTURE-PACKET-20261002.md)
is prepared for the remaining exact Overdrive removal-entry/return contrast;
ordinary immunity/Pommify controls do not need repetition.

The [October 3 Overdrive cleanse](OVERDRIVE-CLEANSE-LIVE-RESULT-20261003.md)
now observes Kevin's actual Pommify removal through E8F4F with successful AL,
erased record and remaining counter 2. It closes the temporal-only Overdrive
gap and reaches core/WPF as `Dispelled via Overdrive (candidate)`. All 135 raw
observations and sixteen completed batches remain intact; manual cleanup and
game survival pass. Another Overdrive/Pommify behavior test is unnecessary.
Offline enemy-name investigation finds the player's Let's Be Friends name in
the AI script as tagged key 1006, but the captured effect key is 1007 and the
level-adjusted source signature matches five unit variants. Keep these unknown
until a direct parent-action/unit/AI relation is evidenced; do not invent a
global minus-one mapping or pick an arbitrary Shining Pom variant.

The [next identity packet](ENEMY-ACTION-IDENTITY-CAPTURE-PACKET-20261003.md)
uses the existing tested Stages profile for one visibly named enemy action,
collecting the missing primary descriptor and accepted-animation relationship.
Any named enemy spell/craft is sufficient; another rare Pom ability roll is
not requested. Preparation and saved replay checks are complete; a controlled
enemy execution is the remaining input for this relation.

The [Diamond Dust result](DIAMOND-DUST-LIVE-RESULT-20261003.md) now links an enemy
main handler, accepted animation and three separately identified party effect
runs. Exact script-window bytes match Knight Ammonite's AI; a separate unique
animation-label join displays Diamond Dust while retaining the unknown generated
SkillParam identity and all targets. All 1,092 observations and seventeen
completed batches remain intact; saved core/WPF checks and manual cleanup pass.
Retreat stays a player annotation. The next
[descriptor-text packet](ENEMY-DESCRIPTOR-TEXT-CAPTURE-PACKET-20261003.md) gathers
the event-time pointer-slot text that historical captures lack, using the same
tested Stages hooks. It needs one ordinary named enemy craft with Guard as a
known descriptor control; Diamond Dust/Pom repetition is not requested.
