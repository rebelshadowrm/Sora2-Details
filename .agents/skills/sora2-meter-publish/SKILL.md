---
name: sora2-meter-publish
description: Package and publish Sora 2 Details Windows preview installers, portable builds, GitHub prereleases, and Velopack updates. Use for release preparation or publishing; use sora2-meter-build for combat-log implementation.
---

# Package and publish a verified preview

Read [README](../../../README.md), [release notes](../../../RELEASE-NOTES.md), [installer builder](../../../tools/build_installer.ps1), and [preview workflow](../../../.github/workflows/preview-release.yml). Inspect dirty files, remote tags/releases and requested scope. Use distribution-ux for privilege/trust changes.

Choose a version newer than both current remote tags and locally distributed candidates. Reusing a candidate's version can prevent its installed app from recognizing an update. Fetch a published predecessor into a clean output directory so an unpublished local package cannot become the delta base. Release notes must describe verified user-visible progress and distinguish research candidates from production totals. Complete audit/repairs, Release/Core/WPF and focused Python checks first. Follow [the research workflow](../../../docs/RESEARCH-WORKFLOW.md); full capture coverage must not be inferred from passing tests.

The shareable Windows x64 path is `tools/build_installer.ps1 -Version X.Y.Z-preview.N`: self-contained .NET, branded capture host, hash-checked embedded Python, Setup, portable ZIP, full/delta packages and `win-x64-preview` feed. Fetch the previous preview when testing deltas. Exercise the embedded runtime and inspect assets for missing dependencies, raw traces, saved data or credentials. Keep user data under LocalAppData, outside install files.

Current previews are unsigned while signing provisioning is pending. Preserve the documented policy. When signing is configured, use Velopack signing for the complete lifecycle and `-RequireSigning`; never call an unsigned package trusted.

For a user-authorized publication, commit intended files, create a new version tag, and push the branch/tag. Do not request another approval between these steps. Never replace an existing published tag/artifact to recover a failure. Wait for the workflow and verify the public prerelease, Setup, portable ZIP, full/delta where expected and `releases.win-x64-preview.json` version/assets. A local pack is not publication proof.

When installer/updater behavior changes, test an installed update from a prior preview when practical, separately from smoke tests. Detach before restart and preserve data. If publishing is blocked, retain tested local artifacts and state the exact blocker. Report version, release URL, validation and remaining live-capture limits.
