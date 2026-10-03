# Interrupt capture packet

Player found a spell-casting enemy and offered an immediate controlled interrupt.
Use the already verified `Stages` observation profile: first actor state callback
`0x7A68B`, animation queue return `0x21558F`, broad effects `0xDBE40`, and resource
setter `0xF8DB0`. Exact supported EXE SHA-256, manual stop sentinel, no cutoff.
The corrected launch owner reader now uses verified caller-saved registers.

Observe enemy pending descriptor and subsequent stages alongside the interrupting
actor's descriptor/effects. If practical let one enemy cast resolve as a contrast,
then interrupt another while the enemy survives. Record spell start, interruption
move/actor/target and the visible outcome separately. Do not interpret absent
effects or a cleared pending pointer as automatic interruption. Killing a caster
is a separate outcome. Current profile has no independently verified native
interrupt signal; this batch discovers that route rather than claiming it exists.

After the finished player report inspect the saved interval, stop via its unique
sentinel and verify detach. Continue offline route tracing, descriptor comparison,
transcript integration and verification without another permission checkpoint.
