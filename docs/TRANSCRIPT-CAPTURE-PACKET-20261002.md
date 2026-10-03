# Continuous transcript boundary capture packet

The revised contrast is complete; see [mode flags result](MODE-FLAGS-LIVE-RESULT-20261002.md).
Five attempts, final Guard/Dragon Dive and subsequent field effects are retained.
Do not repeat this packet now. The previous quick-interval interpretation below
has been withdrawn; exit code 3 remains unknown pending a control clarification.

The first capture is complete; see [its result](TRANSCRIPT-LIVE-RESULT-20261002.md).
The native flag covers both command and quick field battles. The next contrast
adds inline root mode bytes and a bounded roster/status snapshot at each write.
Minimum revised control: one Guard then finish a command battle, followed by
one field quick kill. No cast/interrupt repetition. This revision is prepared
but has not been armed or live-validated.

Saved action, pending/resume, guard, chain and interrupt evidence is already
available. The missing contrast is command battle entry/exit versus field
activity. Do not repeat the interrupt just to obtain another sample.

Supported EXE SHA-256:
`D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`.
English skills payload SHA-256:
`ae81526bef7e1dedc601145961a0786df48fb1b2c96407d4571e1f3bae3bfe8a`;
names payload SHA-256:
`6101d18a87112e351c2ba1009933cc77b660630a0497c33d9119a81a9916c548`.
Both are read from exact-build `pac/steam/table_en.pac`; labels remain candidates.

## Prepared profile

`run_action_stream_probe.ps1 -TargetPid <current PID> -CaptureFocus Transcript`.
Four hardware slots: first actor state update at `7A68B`, effect entry at
`DBE40`, resource setter at `F8DB0`, and data writes to the runtime root read
from module `+C5D768`, offset `+2D30`. Root identity and addresses are recorded
at arm and on every write. Aligned four-byte watch retains surrounding bytes;
framing compares only the flag's low byte. Changed roots are rejected.

Static candidate entry is the 0→1 write ending at `C35AD`; candidate exit is
the 1→0 write ending at `C5753`. Writes ending at `C4A5B` and `C4A6D` temporarily
toggle the flag during an internal route; they do not open or close an interval.
These are native-route candidates until a live contrast confirms actual scope.
Unknown writers and field observations remain in the ledger rather than dropped.
Animation launch breakpoint is omitted to fit the hardware budget; action/effect
links use same-thread first state, full descriptor identity and source context.

The launcher starts `action_transcript_bridge.py --watch`. Complete raw lines
are reconciled into atomic ledger snapshots; partial trailing lines wait.
Snapshots include committed byte length and SHA-256. The desktop reader verifies
that exact source prefix even while the raw file grows. The viewer can open the
research ledger from the tray's recorded action stream command and follows
its atomic updates, retaining the last valid snapshot on refresh failure. This is not yet
the normal encounter bridge or a claim of fully verified command battle coverage.

## Minimum live contrast

Arm while in the field, verify attached/armed and the pointer write baseline.
Enter one fresh command battle. Guard twice, perform one normal attack, queue
one ordinary cast if practical, then finish and return to the field. Perform
one field attack without entering another command battle. Report which cast
and targets were used, battle end and return to field. No specific actor needed.

Manual stop only after the player's finished report and verification that the
planned records are present. No deadline/hit cutoff. If entry/exit are not
observed, preserve the partial interval and inspect the actual writer/root;
do not ask for another identical fight before understanding the failure.

Check framing against player controls, temporary toggles, outside-battle rows,
pending/resume links, resources, the live ledger's source prefix and desktop
selection during recording, then saved replay after detach. Do not infer victory
from the exit flag, do not merge unframed events into a verified encounter, and
do not call research attachment a working production recording path.
