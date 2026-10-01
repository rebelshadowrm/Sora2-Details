# Working protocol

When a user reports a defect, treat it as a request to resolve it unless they explicitly ask only to record or discuss it. Follow [the problem-solving protocol](docs/PROBLEM-SOLVING-PROTOCOL.md): investigate the failing path, use existing code and runtime evidence, make the best supported fix, and verify the same path before calling it resolved. Do not substitute agreement or an apology for progress.

Keep related outcomes distinct. For example, a probe detaching does not prove the desktop app exited, and a meter-only UI test does not validate shutdown while capture is active.
