# Kart64 on Samsung Tizen — public preparation draft

## Uninstall from a TV

In the Qt dashboard, select the television under Devices and press **Uninstall Kart64 TV…**. Confirm the device name and IP in the dialog. Removing the app can remove TV-side game data and saves. Samsung, registered LG webOS, paired Android/Google TV and Fire OS routes use their respective tools; LG requires its CLI folder and matching registered target. The command is restricted to this project's fixed app ID, and the installer checks that the app is absent afterward. The legacy Kart64 Test app, if present, has a different ID and is not removed by this action. Unsupported platforms have no uninstall action.

This is a work-in-progress collection of TV compatibility and diagnostics code from a private experiment. **It includes an experimental Windows installer, but is not yet a clean one-click release or public release.** No game data or prebuilt runtime is included.

## What was tested

A privately built Samsung TV web app based on Edd Mann's [Kart64](https://eddmann.com/kart64/) and [SpaghettiKart](https://github.com/HarbourMasters/SpaghettiKart) ran a Mario Kart 64 race directly on one Samsung UE50U8000FKXXU (Tizen 9) TV. One Xbox controller was tested by its owner. Other devices, controllers, multiple players and clean installation on a second device are unverified.

The private experiment used locally generated, user-provided game assets. Do not commit or publish ROMs, game-derived archives, signed packages containing those files, private signing certificates, access tokens or user-specific network details. A .gitignore is only a secondary safeguard; review the staged files before publishing.

## Contents

- `src/community.cjs`: local-only experimental opt-in report validation and summary; no network or backend.
- `src/preflight.cjs`: local supported-game SHA-1 check and conservative TV compatibility classification. Tested on the owner’s private file; game content is not included.
- `src/diagnostics.js`: experimental TV diagnostics panel, local counters and sampling. CPU and available memory are system-wide; WebAssembly memory is an allocation, not total application memory. Buffer swaps are not necessarily distinct displayed frames. Race counts use a heuristic.
- `src/web-patch.cjs`: experimental adjustments for one specific upstream runtime shape. It deliberately rejects unexpected input. It is not a stable general-purpose Wasm patcher.

The Windows prototype builds a private package from a selected game-data archive and a hash-verified Kart64 runtime. It has only been tested end to end on one Samsung TV and relies on the existing runtime and Samsung installer tools.

## Work required before release

1. Confirm the source, versions and redistribution permissions of Kart64 and all upstream components; keep upstream notices and comply with their licences. Do not assume permission from a public website.
2. Build a reproducible installer that accepts the player's own supported game dump or locally generated game archive. Verify the exact game build and archive compatibility; keep user data on their machine and TV.
3. Provide pinned, integrity-checked upstream sources and tools or a reproducible build; do not bundle uncertain third-party code or game assets.
4. Support Samsung developer mode, account sign-in and device-specific signing clearly, without exposing credentials or private certificates.
5. Test the installation from an empty machine and a second TV, verify launch from the TV's Apps menu, controller input, saves across restart and practical error handling.
6. Establish accurate frame and resource measurements; GPU utilisation and temperatures were unavailable on the tested device. Document runtime limits and boot times honestly.
7. Review the complete repository, release packages, images and history for private data before publishing.

Kart64 is a browser project by Edd Mann; SpaghettiKart and the underlying Mario Kart 64 decompilation are their respective creators' work. This experimental TV adaptation is not affiliated with Nintendo.

## Preflight checks

Run `node --test test/preflight.test.cjs` with a current Node.js installation. The preflight module hashes a supplied file locally; it does not download or upload game data. Only a matching supported US ROM digest is accepted; this does not verify ownership.

Only UE50U8000FKXXU running Tizen 9 is recorded as tested, and only for the observed single-player scenario. The 6.5 minimum follows the experimental package metadata; it is not evidence that every 6.5+ TV works. Other models remain untested until real-device runs. Firmware changes can alter results. Samsung’s [web engine version table](https://developer.samsung.com/smarttv/develop/specifications/web-engine-specifications.html) helps identify differences but is not a compatibility guarantee.

The experimental Windows installer provides Samsung device discovery, automatic dependency setup, a GUI, local package generation and installation through Apps2Samsung. Samsung account sign-in and television developer-mode interaction can still require manual steps. An archive-based install has run on the TV; a ROM-to-package run has been tested with the final installation simulated. A complete ROM-to-TV install on a second device remains unverified.

## Community reporting prototype

This is local validation and aggregation code only: there is no submission service, consent UI, database or live predictions. A report is prepared only when consent is explicitly true, and only the specified model, OS, app version, scenario, swap-rate, system CPU percentage, free system memory and boolean outcome fields are retained. Unknown fields such as IP, account, ROM and serial are discarded. The render metric is explicitly buffer swaps per second, not verified FPS; CPU is TV-wide. Validate the specific device model against trusted device metadata before accepting submissions.

Summaries group by exact platform, model, OS, application version, scenario and metric type. Report counts are submissions, not verified unique devices. A min/median/max is descriptive only; confidence remains insufficient until a proper calibration and abuse/duplication policy exist. No auto-submission or upload occurs in this code. The eventual service must separately address network metadata, retention, consent, deletion, abuse and review.

Run all checks with `node --test`.

## Experimental Windows installer

The prototype has been tested on the developer's Windows PC and a Samsung UE50U8000FKXXU. It has not been tested on a clean computer, a second TV, or LG/other brands. Automatic ROM-to-package preparation has been tested locally; the final TV install in that test was simulated. An earlier archive-based test installed on the Samsung TV.

Requirements:

- Windows x64 and an internet connection. Running from source requires Python 3 with Tkinter and the Windows `py` launcher. The local Windows executable bundles Python but is an unsigned prototype. Node.js, Apps2Samsung and, for the TV check, Tizen SDB are downloaded on demand into a temporary folder and checked against pinned hashes. They are not installed system-wide.
- A Samsung TV with Developer Mode enabled and correctly configured for the PC.
- The [Apps2Samsung CLI](https://github.com/Apps2Samsung/Apps2Samsung) handles Samsung signing and may open a Samsung account sign-in window. This project does not request or store your Samsung password. A local CLI can optionally be selected instead of the automatic download.
- Your supported US Mario Kart 64 ROM in big-endian `.z64` format, or a compatible locally generated `mk64.o2r` archive. The app checks the ROM SHA-1 locally. For a ROM, it downloads the official pinned [SpaghettiKart release](https://github.com/HarbourMasters/SpaghettiKart/releases), verifies its SHA-256, and uses its executable locally in a temporary folder to prepare the archive. The app checks archive integrity but cannot verify archive compatibility or ownership.

Double-click the installer executable in `dist` (or `Start-Installer.bat` when running from source), and choose your game file. The installer uses local network discovery to find TVs from several brands as well as Samsung-specific discovery; some TVs may not advertise themselves or may be misidentified. Non-Samsung devices cannot use Samsung installation or testing. LG webOS has a separate experimental route in the Qt dashboard. If discovery fails, you can enter a Samsung TV's private LAN IP manually. Click **Prepare and install**. The prototype downloads upstream runtime files, verifies pinned SHA-256 hashes, applies the experimental Tizen patches and creates a package in a temporary folder. Apps2Samsung then signs and installs it on the selected TV. The temporary package contains game-derived data: do not share it. Temporary tools are removed when the installer closes normally.

The TV app is called **Kart64 TV**. On the tested TV, first launch took approximately 11 minutes; subsequent launches also took several minutes. An Xbox controller worked in a single-player race on that TV; other controllers, multiplayer and other models need testing. An existing app with the same package ID may be updated; the installer does not request removal of existing apps.

**Test TV compatibility** installs a temporary test app, checks browser capabilities and runs a short synthetic workload, then attempts to remove the test app. Its graphics callback rate is not actual game FPS and does not predict performance. The results remain local; there is no community submission service or live prediction. LG webOS has an experimental installation adapter in the Qt dashboard. Enable LG Developer Mode and register the TV using the official webOS CLI, then select its CLI bin folder and registered device name in Devices. The adapter verifies that the registration matches the selected IP, builds an IPK, installs it and checks the installed app list. IPK creation has been tested with the official CLI; installation, runtime and controller support on an actual LG TV remain unverified.

The TVs tab shows discovered devices and their installation status; identification is best effort. The Performance tab saves up to 100 compatibility checks locally under `%LOCALAPPDATA%\Kart64TV\performance.json`, containing the timestamp, brand, model and synthetic measurements. It does not store the TV IP or upload results. Real game FPS, GPU utilisation and temperatures are not provided by this check.

The newer `studio.py` desktop dashboard uses PySide6 and reuses the same installer workers. Running that interface from source requires PySide6 in addition to Python; the bundled executable includes it. Build the Windows prototype with `python -m PyInstaller --noconfirm Kart64TV.spec`; the spec avoids bundling an unrelated ICU library from the build machine. The earlier Tkinter installer remains available. PySide6 and Qt licensing and redistribution requirements must be reviewed before any public release.

Upstream dependency content and redistribution permissions require a separate release review. Download hashes pin exact bytes, not upstream publishing rights. The download can stop working when upstream changes; it intentionally rejects unexpected files rather than installing unverified code.

Application artwork is exported from `assets/kart64-master.png` by `create_icons.py` (requires Pillow). It supplies Windows, Samsung, LG and Android/Fire TV icons plus the Android TV banner. See [artwork notes](../assets/ARTWORK.md). Existing installations receive the artwork after rebuilding and updating their package. Android / Google TV now has an experimental adapter for already-paired network ADB targets; see android/README.md for setup and the emulator evidence. Fire OS TVs now have an experimental route using the same APK when the paired device reports the official Fire TV feature, API 26+ and a supported ABI. Fire OS hardware gameplay remains unverified. See android/FIRE-TV.md. Vega OS, VIDAA, Roku and tvOS still have no implemented installation adapter. Discovery does not establish gameplay compatibility.

`assets/android-runtime.json` records the local prototype APK hash. Rebuild and update this file when producing your own Android launcher; game content is not bundled in that APK.
