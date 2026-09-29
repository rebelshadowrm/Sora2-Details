---
name: sora2-meter-distribution-ux
description: Audit or improve Sora 2 Details startup, elevation prompts, Windows trust, and distribution footprint. Use for onboarding or runtime packaging UX; use sora2-meter-publish for release publication.
---

Read [the distribution audit](../../../docs/DISTRIBUTION-UX.md) and inspect `tools/start_probe_session.ps1`, `src/Sora2.Details.CaptureHost/Program.cs`, and `tools/build_installer.ps1` before changing the privilege boundary.

The supported installer elevates the branded capture host, which launches only its bundled Python and fixed session script. Keep the meter/updater unelevated. Preserve explicit initiating-user data paths across credential UAC, separate host/server PID readiness, game hash verification, bounded session lifetime, and clean detach before updates. Source and legacy ZIP launches still use Python directly.

Distinguish UAC from publisher trust and SmartScreen reputation. Signing can improve reputation across versions but cannot promise no warnings or suppress consent. Check current Microsoft guidance before making signing recommendations; older Velopack reputation claims conflict with Microsoft's EV guidance. Use Velopack to sign the complete package lifecycle. `-RequireSigning` prevents an intended signed build from silently becoming unsigned; no configured identity means local unsigned artifacts only, not a claim of trusted distribution.

Measure before changing snapshot frequency or runtime bundling. Keep raw capture durable and data outside replaceable install files. Check the audit's interactive validation gates, and distinguish a package smoke check from an installed update/UAC test. Do not attach to a live game just to test branding.

Use the build skill's Release checks plus the focused host-readiness test. Update the audit with measured findings and validation limits. Packaging alone does not authorize publication or provisioning a paid signing identity.
