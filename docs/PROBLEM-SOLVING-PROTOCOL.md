# Problem-solving protocol

Treat a reported problem as a request to solve it unless the user says they only want it recorded or explained. Acknowledge the report briefly, then keep working toward resolution.

1. Compare the failing path with any working path. Inspect relevant code, launch arguments, settings, logs, raw traces, process IDs, and timestamps before attributing a cause.
2. Trace the full path from the user action through its event handler, state gates, asynchronous work, child processes, and observable completion. Check where work stopped instead of assuming the first handler ran.
3. Keep related facts separate. A menu closing is not proof its command ran; a helper detaching is not proof its parent app exited; a successful build is not proof of interactive behavior; and a passing adjacent mode does not validate the failing mode.
4. Use saved evidence before asking the user to reproduce anything. If the cause remains unclear, add focused low-impact diagnostics or isolate the smallest failing case before requesting another live action.
5. Make the narrowest supported fix and verify the same failing path. Label build, automated, and interactive evidence separately. Do not report a fix as complete based only on an inference or a different mode passing.
6. If only the user can complete a live or interactive check, finish independent investigation first, then request one precise action and state exactly what evidence it will establish. Do not ask the user to repeat actions that existing evidence can answer.

If work cannot be completed, report the concrete blocker and the next evidence needed. Do not stop at echoing the problem or leave a known defect framed as resolved.
