# Code signing policy

**Free code signing provided by SignPath.io, certificate by SignPath Foundation**

SignPath Foundation signing is being prepared. The currently published Windows previews are unsigned. Signing will be enabled only after the project is approved and the owner has completed SignPath and GitHub configuration. A SignPath Foundation signature identifies SignPath Foundation as the certificate publisher; it does not imply that this application is complete or endorsed by the game publisher.

## Project and signing roles

The project currently has one maintainer: the GitHub repository owner, [@rebelshadowrm](https://github.com/rebelshadowrm). That maintainer is responsible for:

- **Author:** maintaining the project source and build/release scripts.
- **Reviewer:** reviewing changes proposed by people who are not project committers before they are merged.
- **Approver:** manually reviewing and approving each SignPath release signing request.

No additional authors, reviewers, or approvers are currently assigned. If the project adds maintainers, this policy will be updated to identify their responsibilities before they receive signing access. The maintainer must use multi-factor authentication for GitHub and SignPath accounts.

## Privacy and network behavior

The desktop app automatically checks the project's GitHub Releases feed for a newer preview when its main window loads. The **↻** control checks again when selected. Finding an update does not install it: the user must select **↑** to download it, and confirm first if live capture is active. The app then applies the update and restarts after capture detaches.

These HTTPS requests go to GitHub for release metadata and, after the user requests an update, release assets. GitHub receives the connection's IP address and ordinary request metadata and handles it under [GitHub's Privacy Statement](https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement). The app does not send encounter history, raw capture traces, game-memory contents, or telemetry to GitHub or to the project maintainer. Those files and preferences are stored locally under `%LOCALAPPDATA%\Sora2 Details`. The application has no analytics or crash-report upload service. The updater check is automatic on launch; the update download and installation are user-initiated. The current app has no setting to disable the automatic launch check; blocking GitHub at the network level also prevents release checks and downloads.

No other application runtime network destination was found in the repository audit. Build tooling does use the network: `tools/build_installer.ps1` downloads the pinned embedded Python runtime from python.org when it is not cached, and .NET/Velopack restore and the release workflow contact their configured package and GitHub services. The Python archive is checked against a pinned SHA-256 before packaging. Once SignPath is configured, the release workflow will submit the unsigned build artifact and GitHub build metadata to SignPath for signing; SignPath's [Privacy Policy](https://signpath.io/privacy-policy) applies to that service-side processing.

## Build and provenance

Preview releases are built from the source commit named by a `vX.Y.Z-preview.N` tag on a GitHub-hosted Windows runner. The workflow restores the pinned Velopack CLI, builds the .NET solution, runs the repository checks and packaging readiness checks, and creates the Windows x64 Velopack artifacts. The tag, GitHub workflow run, and commit identify the source used for that build.

When SignPath is approved and configured, the workflow will use the GitHub Trusted Build System with origin verification, upload the unsigned release artifact to GitHub Actions storage, submit it through SignPath's GitHub Actions integration, wait for the required manual approval and signing completion, retrieve the signed artifact, refresh the package-feed hashes, and verify its Authenticode signatures before publication. Signing-enabled releases use full update packages: a delta made before signing could recreate unsigned executable bytes. A signing-enabled workflow run will not publish if submission, approval, retrieval, or signature verification fails. Until then, the existing unsigned preview workflow remains available and releases are identified as unsigned. This preparation follows the [published SignPath Foundation terms](https://signpath.org/terms.html); the owner must recheck them when applying and configuring the project.

## Artifacts intended for signing

For the GitHub preview workflow, the intended signed project artifacts are the Sora 2 Details Windows installer (`Setup.exe`) and the project executables `Sora2.Details.Desktop.exe` and `Sora2.Details.CaptureHost.exe` contained in the portable and full update packages. The checked-in [SignPath artifact configuration](.signpath/artifact-configurations/velopack-preview.xml) scopes signing to those files. The separate legacy ZIP-only builder is not part of that workflow and remains unsigned. The Velopack-generated portable launcher and updater, along with bundled CPython executables, remain unsigned upstream components. The same product name and release product-version metadata are applied to the installer and both project executables; the two project executables also use a numeric Windows file version. The workflow verifies those executable signatures and the installer signature before publishing a signing-enabled release.

## Capture security properties

Live capture is limited to the exact supported game executable SHA-256 embedded in the capture tooling. It opens the game process for query/read operations and uses `ReadProcessMemory`; it does not write game memory. It does not inject a DLL or other code, patch the executable, or attempt to bypass anti-cheat or other security controls. Unsupported executable hashes are rejected before capture proceeds.

The probe opens a separate `PROCESS_VM_READ` handle for memory inspection and uses `ReadProcessMemory`; it does not call a process-memory write API. `DebugActiveProcess` attaches to the supported process so Windows can deliver lifecycle and result events. The debugger-provided process handle has broader rights, but the probe retains it for debugger control and uses the separate read-only handle for memory reads. Hardware breakpoints are armed through thread debug-register context and restored during detach; some watch selected values for writes made by the game so those changes can be observed, but the probe does not write those values. This changes debugger state, not game-memory bytes or executable code. Windows may require an elevated process token to read or debug a game running at a higher integrity level; the app explains and requests that approval at startup. Capture behavior is partial and is not represented as a complete combat log.

## License

The repository is licensed under the [MIT License](LICENSE). This policy covers the Sora 2 Details project and does not replace the licenses or privacy practices of third-party components and services.
