# Shared setup lead rejected as an execution boundary, October 2, 2026

## Result and capture limits

The Setup profile supplied a useful negative result: +0x68F80 is repeatedly
called while Zodiac is pending and is not one observation per executed action.
Keep it as target-setup evidence, not an action counter. The saved inline graph
does corroborate the controlled Estelle source context, including Clock Up EX's
reciprocal target. No repeat of the unchanged Setup profile is needed.

Batch `8973f6d63c694138bc96dd6ed635f606`, game PID 29960, was armed at
`2026-10-02T12:58:15.032-05:00`. The bounded timeout disarmed at `13:03:15.091`
and detached at `13:03:15.416`. The player's combined report arrived afterward;
the stop sentinel was written after detachment and did not cause an early stop.
The trace ends with Estelle's first reported attack in the second fight at
`13:03:13.788`. Later second-fight Saint, Sacred Arrow, Morale EX, repeated attacks,
Overdrive and Dragon Dive are player annotations outside this trace. Their
absence does not demonstrate a hook coverage failure.

Executable SHA-256:
`D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`.
Module base `0x7FF6D4480000`. Raw trace:
`%LOCALAPPDATA%/Sora2 Details/research/action-stream/action-stream-8973f6d63c694138bc96dd6ed635f606.jsonl`.
Raw SHA-256:
`920586D843B09374D49DF880FC4204D284D50F233C39C555A5588B1970AFCCAF`.

There are 1,505 hits: 1,212 setup observations, 290 dispatch observations, one
store and two resumes. Six markers bring the retained record count to 1,511.
No partial JSON lines, sequence gaps, hit-limit or error marker were found. The
offline reconciler preserves every raw record and reports one linked Zodiac
queue/resume/effect candidate. This was raw-only research, with no bridge,
encounter boundary validation or meter update. The two player-reported battles
are not automatically segmented into complete encounters.

## Caller and inline evidence

| Observation | Evidence |
| --- | --- |
| Zodiac store, sequence 66 | `13:00:54.876`, descriptor `0xFFFF00C8` |
| Repeated Zodiac setup | 1,210 calls from `13:00:55.382` through `13:01:09.386`, native return RVA +0x68F72 |
| Zodiac resume, sequence 1277 | `13:01:09.920`, matching pending descriptor |
| Zodiac setup, sequence 1278 | `13:01:09.921`, return RVA +0x69123 |
| Zodiac dispatch | 15 rows at `13:01:11.227` through `.232` |
| Clock Up EX resume/setup | Sequences 1294/1295 at `13:01:39.680/.681`; setup return RVA +0x69123; no paired store |
| Clock Up EX dispatch | Five rows at `13:01:40.297` through `.299` |
| Kevin Normal Attack descriptor | 50 dispatch rows at `13:01:41.884` through `.901` |
| Estelle Normal Attack descriptor | 40 dispatch rows at `13:03:13.775` through `.788` |

The full exact-English descriptor matches identify Zodiac and Clock Up EX under
the research lookup ranges and exclusions already documented. They do not decode
Zodiac's all-stats/Fortune semantics, critical flags or hit/miss outcomes.

All three setup groups have actor pointer `0x21A9F34F010`. Its inline +0x328
context leads through +0x1D90 to `0x21A994CD750`, whose first linked status pointer
is `0x21ADF7845C8` and raw status ID is 0. Zodiac includes a self-recipient dispatch
with both contexts equal to that linked context. Clock Up EX instead records
RDX as `0x21A994CD750` and RCX as `0x21A9D047AB0`, with status pointers
`0x21ADF7845C8` and `0x21ADF788768` respectively. This supports the previously
observed source/target roles for Estelle -> Kevin on that path, with the actor
pointer graph now captured inline. It does not validate every dispatcher caller.

## Why the setup lead is rejected

The exact-build caller at +0x68F00 reads actor +0xC78 each visit. A non-null
pending descriptor takes the branch to +0x68F6D, calls +0x68F80, and returns to
+0x68F72. That path has no phase-zero guard around the setup call, explaining
the repeated observations while the cast remains pending. The separate
+0x68FF0 path gates its resume work on actor state phase zero, restores +0xC70,
clears +0xC78 and calls the same helper from +0x6911E. Its native return is
+0x69123. Equal helper arguments across these routes do not mean equal event
semantics. Deduplicating identical helper callbacks cannot create a trustworthy
action stream: it would conceal the route difference and could merge later
repeated actions.

## Player annotations and remaining gates

The player reported repeated Agate Guards, an enemy hit followed by a counter
killing Ducker Moth, queued Zodiac, Kevin's missed attack, Clock Up EX and a
critical Kevin attack ending the first fight. Raw dispatch keys alone do not
establish which observed callback is the miss, counter or critical result.
Agate attack descriptors and unknown `0xFFFF0042` rows remain present, without
automatic counter or support-proc labels.

The second fight reportedly involved Mini Gourd Boar and Gourd Boar, further
guards/counters, and Estelle's first critical attack with follow-up declined.
Subsequent reported actions are retained in batch metadata, including Saint on
Estelle, further noncritical attacks, Kevin's Sacred Arrow, Morale EX and Agate's
Overdrive followed by critical Dragon Dive. The exact runtime identity of the
reported Sacred Arrow and Overdrive remains unresolved. Do not silently equate
Sacred Arrow with a similarly named static table row or classify Overdrive as a
turn-consuming action from the chat report.

The subsequent offline investigation is recorded in
[action stream progress](ACTION-STREAM-PROGRESS-20261002.md), with a prepared
[actor stages capture packet](ACTOR-STAGES-CAPTURE-PACKET-20261002.md).

The next offline lead identified by this batch was the actor state/animation launch path and its transitions,
with a scoped source pointer graph now available. Any next probe must distinguish
selection, pending updates, resumed execution, support activation and repeated
same-actor actions. The expired batch does not justify another unchanged capture.
No additional live actions are requested until that revised observation is
prepared and tested. Stats, critical detection and explicit interruptions remain
separate downstream evidence gates.
