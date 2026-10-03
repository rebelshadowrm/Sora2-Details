# Interrupt capture result

Raw batch `968637d343ac43479ff126b80a978ad9`, supported executable SHA-256
`D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`.
Armed 14:27:57.641, explicitly disarmed 14:29:56.701 and detached
14:29:57.026 (UTC-05:00). No duration or hit-count cutoff. Game remained running.
981 records, 974 hits: 505 launch returns, 52 first state updates,
105 broad effect calls, 312 resource setters. Raw SHA-256
`d57fe9abbd60704956b1d5a1cf2db17131641a07d95cbe3b96ef3c899500fff5`.
Raw and derived files remain in `%LOCALAPPDATA%/Sora2 Details/research/action-stream`.

Player reported Agate Guard twice; Knight Ammonite began a spell, possibly
Diamond Dust; Estelle True Comet with impede, critical and selected follow-up;
Dragon Dive critical plus Chain finished the battle. These are player controls,
not automatically resolved critical flags or enemy/spell labels.

## Observed cancellation evidence

Agate guards occur at hit sequences 294 and 302. Enemy actor
`0x21aa4e1ebb0`, raw status ID 60016, enters preparation at 309 and pending
cast at 311 with packed descriptor `EA700406`. True Comet enters at 315;
its broad effect selector 47 reaches that same pending enemy context at 416.
The next idle state at 458 has pending descriptor pointer cleared, actor flag
`+E24` transitioning from bit 0x1000 clear to set, and HP 193456: the caster
is still alive. This distinguishes cancellation from the later death.

Exact-build native tracing shows selector 47 routes through `DE49E`; its
successful path calls `71A40` at `DE52D` and sets actor `+E24` bit 0x1000
on return at `DE532`. `71A40` calls the script `btlcom.AniBtlCancelAria`
and clears actor `+C78` at `71B6F`. The captured selector, pending identity,
flag transition, cleared pointer and living target corroborate this impede
route. The cancellation callback itself was not directly breakpoint-observed.
Selector 45 is a separate delay route and is excluded from interrupt inference.

Follow-up state 462 retains an unresolved descriptor variant `FFFF0044`.
Dragon Dive starts at 483; Kevin's Chain state starts at 636. Each observation
and unknown descriptor remains retained. Static enemy AI names are local to
their unit script; the current unit identity has no verified join. Diamond Dust
therefore remains unknown in the automatic transcript.

## Persistence and display

Reconciliation preserves all 981 records, six dispatch runs, seven primary
action candidates and one corroborated interrupt. The interrupted pending cast
is its own timeline candidate; True Comet's effects remain attached to the
attacking action rather than being reassigned to the interrupted cast.
The desktop research viewer displays all candidates and all raw records with
linked raw evidence. This remains a partial research transcript, separate from
verified encounter history and meter totals.

No additional interrupt repetition is currently needed. The next live gate is
the field/battle boundary contrast in the [transcript packet](TRANSCRIPT-CAPTURE-PACKET-20261002.md).
Continuous normal capture, unobserved cancellation causes, critical/miss flags,
enemy names and complete resource/stat outcomes remain separate project gates.
