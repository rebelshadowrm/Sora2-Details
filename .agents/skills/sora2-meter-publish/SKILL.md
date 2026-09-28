---
name: sora2-meter-publish
description: Package and publish Sora 2 Details Windows preview installers, portable builds, GitHub prereleases, and Velopack updates. Use for release preparation or publishing; use sora2-meter-build for combat-log implementation.
---

# Publish a Sora 2 Details build

Work in this repository. Read [README](../../../README.md), [release notes](../../../RELEASE-NOTES.md), [the installer builder](../../../tools/build_installer.ps1), and [the preview workflow](../../../.github/workflows/preview-release.yml) before changing release behavior. Inspect `git status`, the current tags/releases, and the requested distribution scope. Packaging alone does not imply publishing; when the user requests a release, carry it through publication and verification within their authorization.

The supported shareable path is the **Windows x64 Velopack preview**. `tools/build_installer.ps1 -Version X.Y.Z-preview.N` builds the self-contained .NET app, bundles a hash-checked embedded Python runtime, runs the .NET checks, and produces Setup, portable ZIP, full package, delta package when a predecessor is present, and the `win-x64-preview` feed under ignored `releases/velopack-preview`. The older `tools/build_release.ps1` makes a ZIP that needs an external Python installation; use it only when that format is requested.

Choose a new version from existing tags, not from a hard-coded example in README. Update release notes for user-visible changes and ensure their claims match the verified behavior. Run focused Python checks for changed capture/lookup code, then build the installer locally. Inspect the resulting artifact names and confirm raw traces, saved encounters, and local credentials are absent from the package. User data belongs under `%LOCALAPPDATA%\Sora2 Details`, outside the replaceable installation directory; preserve that boundary when changing packaging.

For an authorized GitHub preview, commit the intended files, tag that commit `vX.Y.Z-preview.N`, and push the branch and new tag. Do not replace an existing tag or release to recover from a failed run; diagnose it and use a new version if the published artifact would change. The tag triggers `.github/workflows/preview-release.yml`, which fetches the previous preview for a delta, builds/tests on Windows, and uploads the public prerelease plus update feed. Wait for the workflow to finish and verify the release is published with Setup, portable ZIP, full package, delta where expected, and `releases.win-x64-preview.json`. A successful local pack is not proof that GitHub publishing or the updater feed succeeded.

When updater or installer behavior changes, test the installed app and update path from a prior preview when practical; distinguish this from package/build tests. The app's update control checks with **↻**, then downloads/applies with **↑** after capture detaches. Do not restart over an active capture or discard raw traces. If publication is unavailable, leave the tested local artifacts and state the exact blocker.

Report the version, release URL or local artifact path, validation performed, and any remaining live-capture limitations. The combat log remains **partial** until action, heal, and status paths are verified; a release must not imply completeness from meter totals alone.
