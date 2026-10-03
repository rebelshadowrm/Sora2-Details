# Debuff-immunity contrast, October 2, 2026

Batch `96f8fcdf57c949f99af82cd7fd2626b4`: 376 observations, source SHA-256
`db838189feadb6ef35bffec9e2a4ff0ec1dd5dc5b3c86c7c837da7d804facabe`.
ConditionAttempt uses DBE40, 7F750, 7FD63, 7FDE7 with manual stop only.

The player selected Kevin's group Sacred Breath rather than single-target
Sylphen Guard or reflecting Sylpharion. Inline full descriptors independently
join the exact table to **Sacred Breath II**, irrespective of the chat label.
It adds Debuff Immunity key 43 to Kevin (16), Agate (27), Estelle (38), then
refreshes/adds it again at 177/188/199. No Reflect Arts key 18 is present on
either target during the protected Pommify attempts.

Pommify request/return records 66/67 target Kevin; 290/291 target Agate. Each
pairs same thread, manager, original frame, key and full descriptor. Both return
native RAX=0. Complete unique before/after collections are byte-identical,
contain active key 43 and do not contain requested key 55. Kevin's immunity
remaining/initial counters are 4/5; Agate's are 2/5. The enemy source's captured
runtime status ID is 60062; its exact name remains unknown.

The earlier [attempt batch](CONDITION-ATTEMPT-LIVE-RESULT-20261002.md) has a
positive key-55 return and added active Pommify on Kevin with no key 43 present.
Together these provide the protected/unprotected contrast that reflection
prevented in the first test. No further ordinary Pommify contrast is needed.
The exact native rejection branch was not watched, so the projection states
`native return 0; Debuff Immunity present (candidate)`, preserving context
separately from asserting a uniquely proven cause. Other null returns stay
unclassified. It does not convert absent HP/resource writes into miss labels.

The player reports the pom teleported away and regards this as a possible game
outcome. This focused profile has no battle-mode or outcome callback. Preserve
that report separately; do not manufacture Victory, Escape, enemy death or an
enemy Teleport action from the report alone.

The finished report and saved attempts were inspected before manual sentinel
cleanup. Disarm/detach, launcher exit, bridge exit and actual viewer close were
verified separately; game PID 29960 survived. The growing WPF viewer displayed
and source-verified all 376 original observations before it closed. The original
ledger remains `.before-immunity-context`; corrected derived replay adds names
and protective context without modifying raw source.

Build, 39 reconciliation tests, core transcript checks and actual saved WPF
selection/refresh/malformed-update checks pass. The protective-context tests
reject incomplete, changed, duplicate, inactive and non-null-return collections.
All fifteen completed batches preserve every raw record and timeline position.

The next independent live dependency is native Overdrive removal entry/return
corroboration, prepared in the [combined lifecycle packet](CONDITION-LIFECYCLE-CAPTURE-PACKET-20261002.md).
