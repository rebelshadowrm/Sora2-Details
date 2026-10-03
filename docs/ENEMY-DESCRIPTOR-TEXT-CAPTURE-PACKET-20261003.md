# Runtime enemy descriptor text, October 3, 2026

Use tested Stages profile, same four hooks and manual-stop policy as the
[Diamond Dust result](DIAMOND-DUST-LIVE-RESULT-20261003.md). Exact executable:
`d8b2911d1576216bdc22d070550e4f531e105de7ed2981885849669f4acf8aaf`.
No new hardware slot or timer is introduced.

Main-descriptor and effect snapshots now read neutral B0 pointer slots 90/98
into bounded 256-byte companions. The exact static SkillParam parser uses those
slots for animation/name strings; runtime names still need controlled evidence.
Store pointer and full raw bytes, including unlocalized text and inaccessible
reads. Short/missing descriptors do not trigger companion reads. No name is
automatically promoted by this capture-only extension.

The missing bytes are event-time text pointed to by generated enemy descriptors.
The saved inline descriptor and AI tagged numbers are insufficient: Pommify's
runtime key 1007 differs from the AI name key 1006. Direct metadata may provide
the needed action name without guessing an arithmetic conversion or unit alias.

After arming and source-verifying bridge/viewer, Guard until an enemy uses a
visibly named craft. Report displayed enemy move and target; let it resolve,
then finish combat. Guard is the known party-descriptor/text control. Prefer
an ordinary named enemy craft; no rare Pom roll or repeated Diamond Dust needed.
Preserve unknown, ambiguous and unlocalized strings. Only after same-event
descriptor/text checks should lookup/UI enrichment use a verified relation.

Offline tests cover exact bounded companion reads, missing text, short B0
descriptors and retention of raw fields. Generic probe lifecycle still passes.
The remaining dependency is the next controlled native callback with those
additional bytes. Inspect the finished report before sentinel cleanup; verify
detach, helpers, viewer and game survival separately.
