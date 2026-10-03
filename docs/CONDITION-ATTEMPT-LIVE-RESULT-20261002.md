# Condition-attempt capture, October 2, 2026

Batch `7f58aa12106143f59559fae15003beb2`: 464 observations, source SHA-256
`f120afa6cc806e2189fb318f9f9d67e4340cad7fdd478c2ec2fa3844e53858d9`.
Four execution slots: DBE40 effect, 7F750 request, 7FD63 insertion return,
7FDE7 common request return. All 58 common returns pair to request frames:
51 returned condition records, seven null returns. No unmatched common returns.
Null does not itself mean immunity, miss, cancellation or invalid cast.

The player reported Agate Clock Up EX -> Estelle, Estelle Sylpharion group,
Pommification aimed at Kevin while protected, another Pommification after
immunity expired, a second queued Sylpharion, Kevin Overdrive and craft/follow-up,
then Agate's killing attack. The subsequent clarification explicitly places
Kevin's Overdrive before the second Sylpharion resolves. Native order agrees.

## Reflection and condition application

Sylpharion inserts Reflect Arts key 18 and Debuff Immunity key 43, including
Kevin's key-43 return at record 43. At record 56, Kevin -> Reflect -> enemy
runtime status 60042 is independently read. Records 57/58 then read enemy
60042 as both source and target. Its Pommify key-55 request/return at 59/60
returns null with an empty collection. This is a reflected attempt against
the enemy, not evidence of a key-55 rejection on Kevin's immunity manager.
The enemy's exact table name and the null-return cause remain unresolved.

Records 237-239 show a later Pommify attempt against Kevin, with matching frame,
manager, key and descriptor. The returned record matches the full collection
at its native address. Key 55 is added active, initial/remaining counters 2/2;
key 43 is absent. This supplies actual successful application after protection
is no longer present, separately from the earlier reflected null return.

## Overdrive and the queued spell

Kevin's key-53 Overdrive request at 294 has exact native caller E8E97, the
return from E8E92 -> 7F750 inside E8E40. Records 295/296 still contain Pommify:
the common condition return occurs before Overdrive's later cure loop. Kevin's
next full condition snapshot at 360/361 has no key 55, while his craft's effects
start at 297. The second Sylpharion's effects start at 371; its Kevin key-43
return is 402. Therefore it cannot explain the earlier disappearance.

Exact-build disassembly shows E8E40 requests key 53, then removes the two native
debuff-table lists via 80730 at E8F4A/E8FBA (returns E8F4F/E8FBF), with R8B=1.
The earlier E8EE3 call removes Overdrive Sign key 52 and remains distinct.
Removal reconciliation now recognizes successful disabled/erased records from
the two debuff-list callers as `Dispelled`, cause candidate `Overdrive`.
Positive/negative offline tests pass. This batch did not watch 80730/80780, so
it supports Overdrive followed by disappearance, not a fabricated observed
removal entry/return or an exact removal timestamp. A removal-profile live
contrast would corroborate that specific native cause.

## Persistence, display and cleanup

The actual growing WPF observer displayed and source-verified all 464 records
before closing. On the finished report, controls were inspected, the manual
sentinel stopped capture, and disarmed/detached markers were checked. Launcher,
bridge and viewer each exited; game PID 29960 survived. No timer/hit cutoff.
The original ledger is retained as `.before-result-enrichment`; derived replay
adds exact condition names and native-result candidates without editing raw.
Core and actual WPF saved replay, selection, refresh and malformed-update
retention checks pass. All fourteen completed batches replay with every raw
observation and timeline position retained.

The first viewer raced the bridge's initial publication and exited before its
ledger existed. It was restarted after publication before requesting controls.
Observer startup now waits for the first ledger, without imposing a capture
limit. The same path was verified by launching with a missing ledger, publishing
it later, checking 464 source-verified WPF rows, then checking viewer exit.

## Remaining live dependency

This batch proves the general request/common-return probe but does not isolate
Debuff Immunity from reflection. Exact English Sylphen Guard describes dispelling
and nullifying debuffs; Sylpharion describes reflecting one arts attack. Use
Sylphen Guard if available, then bait Pommification against that ally. Otherwise
consume Sylpharion's reflection and bait a second attempt while Debuff Immunity
is still active. Preserve any different target/outcome without relabeling it.
