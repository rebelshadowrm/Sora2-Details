---
name: sora2-meter-distribution-ux
description: Audit or improve Sora 2 Details startup, elevation prompts, Windows trust, and distribution footprint. Use for onboarding or runtime packaging UX; use sora2-meter-publish for release publication.
---

# Audit Windows startup and distribution behavior

Read [the distribution audit](../../../docs/DISTRIBUTION-UX.md) and inspect Program, CaptureHost, session launchers and installer builder before changing privilege boundaries. Use [problem solving](../../../docs/PROBLEM-SOLVING-PROTOCOL.md) for startup, tray, update or shutdown defects.

Normal desktop startup requests elevation once; CaptureHost, bundled Python, bridge and updater inherit that approved session. Velopack startup hooks run first. Preserve the initiating user's explicit data path across credential UAC, separate host/server readiness PIDs, executable hash gating and fixed bundled capture scripts. Do not restore obsolete guidance to keep the production meter unelevated.

Research player batches use manual sentinel stop as specified by [the workflow](../../../docs/RESEARCH-WORKFLOW.md); startup readiness waits are not capture durations. Preserve traces and verify cleanup before restart/update. A hidden app, detached probe and exited desktop are separate outcomes.

Keep data outside installation files. Measure snapshot/runtime changes before changing them. Package smoke tests do not validate installed updates, Windows consent or publisher trust. Do not attach to a game merely to check branding.

Signing and SmartScreen reputation are separate from UAC. Use current authoritative guidance for new trust recommendations; never promise warning-free launches. Velopack must sign Setup, app and updater when a configured identity exists. `-RequireSigning` prevents silent unsigned fallback. Current unsigned previews must say so; user-authorized unsigned publication is permitted by the existing release policy.

Use build/test for repairs and checks, publish for release authorization and verification. Packaging does not authorize buying a signing identity or publishing unless the user requested it.
