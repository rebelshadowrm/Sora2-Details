# Distribution and elevation audit (2026-09-29)

## Launch and privilege boundary

The meter already starts capture automatically when exactly one game process is running. The previous prompt came from `start_probe_session.ps1` using `RunAs` on `python.exe`, so Windows correctly displayed Python's identity. The installer now includes `Sora2.Details.CaptureHost.exe`, a branded, trimmed, self-contained helper. The launcher elevates it; it runs only the bundled Python and fixed session script, without a shell or user-selected executable. The helper waits for the Python server and propagates its exit code. The readiness record includes both `hostPid` and `serverPid`; reuse and stop still track the server.

The desktop and Velopack updater stay unelevated. Saved-history use needs no prompt. Before the first elevation, the app explains the capture purpose, read-only boundary, and the option to continue without live capture; it remembers that explanation in the per-user data directory across updates. Capture startup requests approval, and cancelling leaves the meter available. Each new capture session can require approval; update application waits for detach, then the restarted meter begins a new capture session. This is not an installer privilege requirement. Avoiding approval across those sessions would require a different privilege lifetime, such as a persistent broker; it is not achieved by signing or changing an icon. Do not silently install a privileged service or scheduled task to suppress UAC.

The initiating data directory is passed explicitly into the helper and its Python environment so credential elevation does not redirect probe output into the administrator's profile. Cross-account filesystem permissions and interactive UAC remain manual validation gates. Source checkouts and the legacy external-Python ZIP retain the old Python launcher. The supported Velopack package uses the branded helper.

## Windows trust and release signing

UAC consent, Authenticode publisher identity, SmartScreen reputation, and Smart App Control are separate. An icon and product description improve recognition but do not establish a trusted publisher. The local preview remains unsigned until an actual signing identity is configured.

`tools/build_installer.ps1` accepts `-SignParams` or `VPK_SIGN_PARAMS`, forwarded to the pinned Velopack CLI. Use `-RequireSigning` for a distribution build that must not silently fall back to unsigned output. It rejects missing configuration before building and verifies the delivered portable desktop/helper/updater and final Setup signatures after packaging. Use certificate-store or managed signing credentials; do not commit private keys or put passwords in command arguments. Signing is performed by Velopack so its Setup/updater binaries are covered at the appropriate build stages, rather than signing only the desktop or signing Setup after packaging. CI must provision the signing tool, identity and credentials before enabling the gate; this change does not provision an account or credentials.

Microsoft says unsigned versions must accumulate reputation separately, while a consistent signing identity can carry publisher reputation across releases. Signing does not guarantee a warning-free first download. Microsoft's current guidance explicitly says EV certificates no longer receive an automatic SmartScreen bypass; the Velopack signing page still contains older conflicting claims. Prefer Microsoft's guidance for reputation and Velopack's documentation for packaging mechanics.

- [Microsoft SmartScreen guidance](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)
- [Velopack signing integration](https://docs.velopack.io/packaging/signing)

## Build and runtime findings

- Keep the .NET/Python bundle: it removes prerequisites from a friend's install. The helper is trimmed independently; WPF is not a suitable target for blindly enabling trimming. Both use self-contained single-file publishing, which can extract native libraries on first launch. Measure cold startup before changing that tradeoff.
- Installed scripts are allowlisted, Python is pinned by SHA-256, and saved data lives outside version replacement. Preserve these existing strengths.
- The helper adds a small process and bundled runtime footprint; this is a UX improvement, not a claimed CPU optimization. It sleeps while its child runs and exits with the session.
- The bridge reads the raw trace incrementally with a 100 ms idle wait. It also rewrites the full encounter JSON on saves. Long fights can therefore increase serialization and UI reload work. A future measured optimization is batching derived snapshots while retaining immediate raw evidence and flushing at encounter end/detach. Do not weaken durability merely to reduce writes.
- Startup runs several separate Python metadata checks and hashes the game before requesting elevation. These are compatibility gates; combining them could reduce interpreter startup overhead, but caching solely by file path would weaken patch rejection. No benchmark currently establishes them as a meaningful delay.

## Validation

Run the Release solution build and existing .NET checks, then `python -m unittest discover -s tools -p test_elevated_probe_session.py`. The readiness test uses a temporary directory and mocks target verification; it tests both legacy and branded identities and clean server stop without touching the game.

Build a local preview into an isolated output directory. The builder smoke-tests the packaged helper with `--check-package` without UAC. Inspect the portable ZIP for the helper, embedded runtime, fixed runtime script allowlist, icon and absence of local data. Regenerate the code-drawn multi-resolution ICO with `tools/build_app_icon.ps1`.

Before public release, manually check: UAC identity/icon, cancellation and retry, clean stop, launching without the game, standard-user credential elevation, and update from the previous installed preview with encounters preserved. Package tests do not prove those interactive paths. Signed builds additionally need a clean-machine download check; never claim SmartScreen is fixed from a local launch.

### Local evidence from this audit

- Release build: zero warnings/errors; existing replay, projection, recorder and persistence checks passed.
- Embedded-Python readiness test passed for branded and legacy launches; packaged helper accepted its package check and rejected invalid PID, duration, relative data path and arbitrary-command inputs.
- Missing signing configuration was rejected before build. The post-package signature gate was separately exercised against the unsigned artifacts and rejected them. A successful signed build is untested because no signing identity was configured.
- Local `0.2.0-preview.14` review artifacts are under `releases/ux-review-final`; no tag, installed replacement, or public release was created. The portable ZIP is 90,750,845 bytes and Setup is 98,273,830 bytes. The helper is 12,908,608 bytes uncompressed (about 5.9 MB in the ZIP). This package includes the current working-tree history changes as well as this audit's changes.
- Delivered executables have the expected Sora 2 Details product descriptions. ZIP inspection confirmed the runtime script allowlist and no raw capture traces, encounter store, session markers or signing keys. All three new/updated skills passed the skill validator.
- Interactive UAC, actual game attach/detach, cross-account access, installed upgrade, and signed clean-machine download behavior were not exercised.
