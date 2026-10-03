# Enemy Diamond Dust execution, October 3, 2026

Batch `5e1f55e98ab34a38831dd07cf0b32a1c`: 1,092 observations, source SHA-256
`7909392da5d90a3402d4f480c544a95d497022ac179f28102947dad3bd275420`.
Stages used DBE40 effect, 7A68B first-state dispatch, 21558F accepted animation,
F8DB0 resource setter. No duration/hit cutoff. The player reports Diamond Dust
hit everyone and combat ended by retreating. Retreat remains a player annotation:
this profile did not watch the battle outcome. Later field/movement observations
are preserved alongside combat, with no invented battle classification.

## Execution and effects

Enemy actor 0x21aaa2a77b0 reaches resume handler 68FF0 at 140 and main descriptor
handler 68320 at 142. Its inline packed descriptor is EA8C0406 (runtime owner
60044, generated low key 1030). Accepted animation 143 has caller 686F1,
verified saved-owner recovery, same actor/context/descriptor pointer and full B0
bytes. Its script label is `btlmagic.AniBtlArtsWater02`.

That accepted launch links three dispatch runs, 200/208/216, with independently
captured enemy source status and Estelle/Agate/Kevin targets. Fifteen effect
observations are retained, including selectors 15/32 and zeros; they are not
fifteen player commands. The projection has four primary candidates: three
Estelle Guards and this enemy execution. There is no linked queue candidate;
resume/animation evidence is not relabeled as a fully observed enemy queue.

HP setter observations 205/213/221 independently read requested HP values
21085/-1/23542 for Estelle/Agate/Kevin, with respective pre-values
25997/6005/37880, at caller E4DB1. They remain setter observations. This profile
has no post-set clamp/readback, so -1 is not called a final HP value, and resource
causality is not assigned solely by nearest animation. Critical/damage-class
fields stay unknown.

## Name and script evidence

Exact shared spell row 155 has name Diamond Dust and the same animation label,
but packed ID FFFF0075 and different effect power/cast parameters. Therefore
the generated descriptor does not receive a false exact SkillParam match.
Accepted-animation lookup is separate metadata: unique name/row, exact table
payload hash and explicit animation-only provenance. Core/WPF display
`Diamond Dust (animation candidate)` with original generated move ID and all
three targets unchanged. Raw descriptor lookup remains unknown.

The 256 captured animation bytes contain 251 immutable bytes to the end of a
script payload, followed by five bytes beyond its file boundary. Matching all
251 file-backed bytes against the hash-validated script archive uniquely selects
`script_en/ai/ai_mon5045.dat`, offset 4579, payload size 4830, payload SHA-256
`81bcea458452a2d7d1081c349f75ebf2666e47ffe2ee9cd33f4291564f384e7f`.
Its static unit name is Knight Ammonite. Local `enemy-script-window-<batch>.json`
retains full raw window, archive hash, match bounds and source observation ID.
This establishes the script-window match, not a direct runtime unit-key field
or a universal skill-number conversion. Shared AI-script aliases stay unknown.

## Validation and cleanup

The finished report and saved observations were checked before manual sentinel
stop. Disarm/detach, launcher exit, bridge exit and actual viewer close were
verified independently. Game PID 29960 remained alive. The growing WPF observer
displayed/source-verified all 1,092 original records before exit. The first
ledger is retained as `.before-animation-enrichment` beside derived replay.

Build, 40 reconciliation tests, 28 snapshot/timeline/bridge tests, synthetic
probe attach/hit/detach, core saved transcript and actual WPF selection/refresh/
malformed-update checks pass. The actual core case specifically asserts Diamond
Dust's animation-only label, EA8C0406, fifteen effect observations and all three
targets. All seventeen completed batches preserve every raw observation and
timeline position.

## Next missing bytes

Accepted animations now supply a scoped candidate label for generated enemy
Arts. Generic enemy craft names need their own evidence. The current captures
contain descriptor pointer slots 90/98 but not text read through slot 98 at the
event. Those historical bytes cannot be reconstructed from a later heap read.
Bounded 256-byte neutral companion reads are now implemented and offline tested
for main-descriptor and effect snapshots. The [text capture packet](ENEMY-DESCRIPTOR-TEXT-CAPTURE-PACKET-20261003.md)
needs one named enemy craft plus an ordinary Guard as a known descriptor control.
No second Diamond Dust or Pom behavior repetition is required.
