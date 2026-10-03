# Buff expiration and bulk clearing, October 2, 2026

Batch `53a210c438994ec5901f9cb3e6436993`: Estelle cast Forte on Agate. The player
reports five rounds, many intervening guards because Agate acted relatively
late, and believes the affected actor's actions advance the timer.
All 457 raw observations remain intact. SHA-256:
`d0a4491e46c92e28c72e7a4a9c3ff50cb38de56fb59ad89be6c1cc20cb4265c3`.
No primary-action or boundary hook was allocated; finishing effects are not an
automatic Victory result.

Record 113's key-27 STR UP record has +2C=5 and +30=5. Same-manager snapshots
read remaining counters 4 (154), 2 (170/182), 1 (192), then 0 at removal entry
193. Value 3 was not sampled. Entry 193/return 194 match thread, manager and
original stack frame. Native AL=1; full records differ only at +4 (1 to 0).
The post-call array still contains the disabled record; the caller erases it
after the watched return. Immediate array presence is not proof of an active buff.

Native return **813BE** follows 813A6's record+2C=0 gate and 813B9's removal
call. Successful callers subsequently erase at 813D0. `Expired` candidates now
require this exact caller, zero counter, clear +45 byte, successful AL and full
disabled-record comparison. Unknown caller, nonzero counter, failed return or
missing bytes stays unclassified. Estelle STR UP and Agate CP Regen also expire.

Native 81200 decrements +2C at 8130C/81311, gated by condition+34 flags and the
incoming mask. Actor wrapper 63C80 resolves that actor's manager through +328,
+1D90 and +598. BD050's roster loop passes masks 5/4 according to equality with
its actor argument; this STR UP record has flags 81. This supports actor-scoped
timing rather than global guard counts. Separate caller 7276F and queued-cast
guards exist; no universal rule covering every cast/counter/extra action is claimed.

Later native return **E6932** belongs to E6910's collection-clear loop. Estelle's
STR UP still has counter 3; Kevin's STR UP/ATS UP have counter 4. They become
`BulkClear` candidates, not expired buffs. The player-finished sequence supplies
cleanup context, but this profile does not prove an engine battle boundary.
There are three expiration candidates, seven bulk clears and twenty unclassified
or failed removal returns. Unknown sources/causes remain unknown.

The growing WPF viewer verified all 457 final observations. Offline enrichment
keeps the same raw hash and exact embedded records, with old ledger and derived
lifetime summary preserved. Core/WPF checks distinguish Agate's STR UP expiry
from later clearing; raw selection, refresh and malformed-update retention pass.
All twelve saved batches preserve every observation/timeline position. Release
build, 37 reconciliation checks, 25 snapshot/timeline/bridge checks, four item
checks and synthetic debugger attach/hit/detach pass.

Manual stop produced disarmed 23:06:10.777 and detached 23:06:11.103. Launcher
25628/bridge 24960 exited; viewer 41664 verified the final hash and closed at
23:06:25.126. Game 29960 survived. Session archived, active marker removed.
Evidence is under `%LOCALAPPDATA%/Sora2 Details/research/action-stream`, keyed
by the batch ID. No cleanup reconfirmation was required.

The next missing contrast is an explicit cure of an active debuff. The player
will choose a suitable fight; use the [prepared cure packet](CONDITION-CURE-CAPTURE-PACKET-20261002.md).
