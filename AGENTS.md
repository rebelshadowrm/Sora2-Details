# Working protocol

When a user reports a defect, treat it as a request to resolve it unless they explicitly ask only to record or discuss it. Follow [the problem-solving protocol](docs/PROBLEM-SOLVING-PROTOCOL.md): investigate the failing path, use existing code and runtime evidence, make the best supported fix, and verify the same path before calling it resolved. Do not substitute agreement or an apology for progress.

Keep related outcomes distinct. For example, a probe detaching does not prove the desktop app exited, and a meter-only UI test does not validate shutdown while capture is active.

For player-controlled live research batches, keep capture armed until the player
reports the sequence finished and the saved observations have been checked, then
stop via the manual sentinel and verify detach. The finished report authorizes
this cleanup; do not require a keyword or another confirmation. Do not use a duration or hit-count cutoff
unless the user specifically requests one. Use the action-stream launcher's
manual-stop mode; game exit and genuine capture errors remain separate outcomes.

Continue authorized offline investigation, implementation, replay, and verification
without requesting confirmation between milestones. Stop only at an actual missing
input or live-control dependency, after completing work that does not depend on it.
