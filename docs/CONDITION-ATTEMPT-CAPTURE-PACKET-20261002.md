# Condition attempts and immunity contrast, October 2, 2026

Prepared profile `ConditionAttempt` uses four execution slots: effect DBE40,
condition request 7F750, insertion return 7FD63, common request return 7FDE7.
It uses the launcher's manual sentinel mode, with no duration/hit cutoff.
Exact executable SHA-256:
`d8b2911d1576216bdc22d070550e4f531e105de7ed2981885849669f4acf8aaf`.

Native disassembly verifies that 7F750 saves source RDX at RSP+60 and retains
manager R15, key EBP and descriptor R12. Eight register pushes plus 1B8 stack
bytes recover the original entry frame at common return RSP+1F8. 7FDE7 precedes
cookie checking and restoration. Both insertion success and early zero returns
reach it. Zero may also arise from invalid key/descriptor or other native paths;
it must not automatically receive an immune/resisted label.

Snapshots preserve full RAX, complete bounded condition collections, descriptor,
source/target status, and original frame. Request/return candidates require
same thread, manager, frame, key and descriptor pointer/bytes. Pairing survives
the intervening insertion observation but resets on gaps or capture boundaries.
Unknown conditions and unmatched returns remain visible. Core/WPF display the
native return with cause unresolved; raw snapshots stay authoritative.

Offline snapshot and replay tests cover null return, frame recovery, intervening
insertion, mismatched identities and sequence gaps. Build and core checks pass.
The actual WPF viewer also passes evidence selection, refresh and malformed-update
retention on a six-record synthetic null-return fixture, without game attachment.
Actual native request/return coverage still requires the next live contrast.

Minimum live sequence after arming and verifying bridge/viewer source proof:

1. Prefer Sylphen Guard on one ally; report caster, exact move and target.
   Sylpharion also grants one arts reflection, which confounded the first live
   contrast. If using it, consume reflection before the condition attempt being
   tested, while Debuff Immunity remains active.
2. Bait the same enemy's Pommification against that protected ally. Report
   whether it applied or was visibly blocked. If it applies, cure it normally.
3. Finish combat and report the sequence. Inspect saved observations before
   sentinel cleanup; verify detach, helper/viewer exits and game survival.

The prior successful Pommify capture supplies the positive application evidence.
Target selection belongs to the player; no repeated ordinary attacks, item uses
or buff-expiration control is necessary. If the enemy targets a different ally,
preserve that outcome without pretending it tested the protected target.

The [first live result](CONDITION-ATTEMPT-LIVE-RESULT-20261002.md) verifies all
58 request/common-return pairs, including null and successful condition-record
returns. It records reflection, later Pommify application, and Overdrive before
the queued second Sylpharion. Direct immunity rejection remains the live gap.
