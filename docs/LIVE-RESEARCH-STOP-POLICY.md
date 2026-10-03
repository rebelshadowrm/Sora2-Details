# Player-controlled capture completion

The October 2 Setup batch expired before the player finished reporting two
combats. Its missing later sequence was a capture-window failure, not proof
that those moves had no watched event. Future player-controlled batches must
remain armed until the player reports completion and the saved observations
have been checked. Then write the batch's explicit stop sentinel and verify
`disarmed` and `detached`. Do not wait for another player action during analysis.
The player's report that the sequence/fight is finished authorizes this manual
cleanup. No special "done" keyword or separate stop approval is required. This
clarifies the player's October 2 instruction to work autonomously except where
new live controls are needed.
If evidence is missing, stop on the player's completion report and investigate
offline rather than leaving the player in combat or silently restarting capture.

`tools/run_action_stream_probe.ps1` now always passes `--until-stop-file` and a
unique stop path. It no longer accepts a duration, and applies neither a timeout
nor a hit-count ceiling. `tools/lifecycle_probe.py` retains its bounded mode for
existing automated/desktop callers, but its new explicit-stop mode disables both
limits and requires a stop-file path. A `capture_policy` marker records which
mode and limits actually apply. Genuine errors and game exit still end capture;
those outcomes must be reported distinctly from completion.

Synthetic validation attached to a disposable process with a 0.01-second duration
and one-hit ceiling supplied alongside explicit-stop mode. The probe remained
attached beyond both limits, collected further hits, and detached after its
sentinel appeared. The existing timed attach/detach tests and target survival
checks also pass. This validates the stopping mechanism without asking the player
to repeat the lost combat. No game probe was armed while making this change.
