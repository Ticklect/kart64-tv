# Release build

Use Python 3.12.10, PySide6 6.11.1 and PyInstaller 6.22.3. Keep game files and signing keys outside the release directory.

Build the game-free Android launchers following `android/README.md`. Verify signatures, signing continuity, application ID, version and processor contents. Publish each APK separately and pin immutable versioned URLs, byte sizes and SHA-256 hashes in `assets/android-runtime.json`. The desktop app downloads and caches only the ABI reported by the selected TV OS; Windows contains no APK.

Collect notices and corresponding source using any verified APK from that build:

```sh
python packaging/prepare_release.py --cache SOURCE_CACHE --output RELEASE_DIR --apk PATH_TO_APK
```

Set `KART64_RELEASE_LEGAL` to `RELEASE_DIR/legal`, then build:

```sh
python -m PyInstaller --noconfirm Kart64TV.spec
```

Run the frozen EXE with `--self-test` and `--smoke-test`. Set `QT_QPA_PLATFORM=offscreen` for the synthetic UI check; it never scans the network or touches a TV. Inspect the frozen archive to confirm the APK is absent and the runtime pin matches the release. Publish the EXE, APKs, dependency-source ZIP and SHA256SUMS with the matching source tag.

Retain the filename `Kart64TV-Android-TV.apk` for the compressed universal build so existing `/releases/latest/download/Kart64TV-Android-TV.apk` Downloader links keep working. Also publish `Kart64TV-Android-TV-arm64-v8a.apk`, `Kart64TV-Android-TV-armeabi-v7a.apk` and `Kart64TV-Android-TV-x86_64.apk` as smaller alternatives. These are complete APKs, not install-multiple split packages.

APK installation does not provision game data. Keep the PC preparation/transfer requirement visible. Download sizes exclude game files and installed native-library extraction. New packaging has not been tested on physical TVs.
