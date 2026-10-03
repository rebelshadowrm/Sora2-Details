# Project audit — October 3, 2026

## Release decision

The available captures and regression checks support publishing **0.2.0-preview.21**
as a partial Windows preview. The project has made measurable forward progress;
the complete authoritative action stream is still unfinished. Research candidates
remain separate from verified encounter history and meter totals.

The source baseline was `274879fc9ba9078b42a60774088cc532578f4c42` plus this
thread's capture, projection, desktop, documentation and audit changes. The normal
Start Menu shortcut targets LocalAppData `Sora2.Details/current` and reports
`0.2.0-preview.20`, an unpublished audit candidate. A separate source-launched
desktop was running as PID 37444 and held its normal build files open. No game
was running during this night's audit, and no new player controls were requested.

Preview 21 is newer than both public preview 19 and the installed candidate.
Local packaging uses a separate output directory containing the downloaded public
preview 19 predecessor, so its delta cannot depend on an unpublished preview 20.
Publication and public feed verification are separate from local packaging.

## Evidence gained

| Family | Observed progress | Remaining limit |
| --- | --- | --- |
| Actions without damage | Ordered state, accepted launch and effect candidates survive independently of HP writes | No single profile captures every selected/executed/cancelled action |
| Casts and interrupts | Same-actor inline pending/resume linkage and a controlled impede interruption | Not a general cancellation decoder; instant Arts do not imply every Art queues |
| Items | Generated descriptor and original item IDs corroborate Tear Balm and EP Charge I | Item boost ownership and general item coverage remain incomplete |
| Conditions | Exact condition names, insertion/stacking, timer-zero expiry and scoped successful removal candidates | Parameters/timers are not observed effective-stat changes |
| Cures and immunity | Curia removal, null-return attempts with active immunity context, and Overdrive cleansing | Candidate cause evidence is scoped; reflection and immunity are different paths |
| Enemy action | Diamond Dust accepted execution links to three target effect/resource paths | Name is animation-only; native descriptor/unit identity stays unresolved |
| Persistence and display | Lossless research ledgers, source verification, growing/saved WPF transcript and unknown records | Research records do not silently contribute to production totals |

The Diamond Dust result preserves native move ID `0xEA8C0406` rather than
substituting the shared Art's ID. The named Shining Pom craft annotation does not
justify shifting every AI low ID. The newly added descriptor slots `+0x90/+0x98`
are bounded neutral raw snapshots; they still require a live named craft contrast.

## Audit repairs

- Action-stream startup previously accepted a living bridge before its first armed
  ledger was published. It now waits for that observation in the committed
  projection. A Windows regression executes the actual launcher readiness branch
  against missing, pre-arm and armed bridge snapshots; only the armed case passes.
- Installer builds previously wrote over the normal source output, failing while
  a source desktop held its assemblies open. Isolated build artifacts allow the
  same package path to succeed while that desktop remains running.
- Embedded Python excluded the checkout from its import path, exposing an absent
  timeline test-fixture module. The test loads only its fixtures by file; runtime
  imports continue resolving from bundled application tools. Embedded checks pass.
- Eight project skills were rebuilt with shared maintained workflow guidance.
  Stale timed capture, extra completion confirmation, old lookup-gap assertions,
  obsolete privilege guidance and release-version assumptions were removed.
  Skill metadata and relative links validate; historical result packets remain
  intact. New batches follow manual stop after the player's finished report and
  saved-observation inspection, followed by autonomous offline work.

## Validation

- Release solution build: zero warnings/errors after isolation.
- Core replay, projection, recorder, pipe, persistence, corrupt history and
  research transcript checks: passed.
- Focused Python checks: 29 action snapshot/timeline/bridge tests, 40 reconciliation
  tests, four item tests and two host-readiness tests passed. Standalone lifecycle
  and live bridge checks also passed; discovery alone would not run them.
- Exact installed English table linkage and AI archive controls: passed. These
  static checks do not establish a new runtime join.
- Actual WPF settings, live-file refresh, timeline and seven X/tray shutdown cases:
  passed with simulated helpers. Desktop closure and helper cleanup are distinct
  assertions. No new live game attachment was performed tonight.
- Saved Diamond Dust WPF replay: all 1,092 observations and four candidates
  displayed; raw selection, refresh and malformed-update retention passed.
- All 20 available completed research ledgers replayed from immutable raw sources:
  **13,471 observations**, source hashes, raw objects and timeline order preserved.
- History inventory: **652 encounters / 14,548 events / 36 inventoried legacy
  traces**, zero structural errors. **91 evidence warnings** identify encounters
  with unavailable original traces; these are retained evidence limits.
- Embedded Python/runtime and capture-host package checks: passed. Packaging and
  public asset verification are recorded in the release workflow and local audit
  artifacts; they do not prove Windows consent or installed live combat behavior.
- Final preview 21 package: Setup, portable ZIP, full package and public-preview-19
  delta built successfully. All 72 portable entries were inspected for private
  data; delivered runtime imports passed. The delivered standalone saved-transcript
  WPF viewer opened and closed successfully without elevation or game attachment.

Local detailed results and screenshots are under `.research-deps/audit-20261003`.
Raw captures remain in the user's LocalAppData research directory and are excluded
from the published application. The preview retains the existing unsigned policy.
No claim of bug-free general gameplay or complete capture follows from these checks.

## Next live dependency

One known Guard plus a named enemy craft can test the new inline descriptor text
slots and distinguish craft text from animation-only labels. The player can supply
this tomorrow. Full critical/miss decoding, direct enemy unit keys, general support
ownership, effective-stat deltas and unified action/outcome coverage remain separate
downstream work; they do not require repeating already-captured condition controls.
