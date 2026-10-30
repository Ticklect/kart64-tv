# Windows release build

This packages the existing app as a standalone Windows x64 EXE. It does not change the TV or start discovery during verification.

Use Python 3.12.10, PySide6 6.11.1 and PyInstaller 6.22.3. Build the game-free Android launcher following `android/README.md` and update its size/hash pin. Keep all game files and signing keys outside the package.

```sh
python packaging/prepare_release.py --cache SOURCE_CACHE --output RELEASE_DIR --apk PATH_TO_APK
```

The script verifies the Qt/PySide source archives against `dependency-sources.json`, collects notices and writes the dependency-source ZIP. Set `KART64_ANDROID_APK` to the APK path and `KART64_RELEASE_LEGAL` to `RELEASE_DIR/legal`, then run:

```sh
python -m PyInstaller --noconfirm Kart64TV.spec
```

Run the frozen EXE with `--self-test` and `--smoke-test`. For an offscreen UI check, set `QT_QPA_PLATFORM=offscreen`; the smoke test uses synthetic devices and does not scan the network. Verify that the frozen source, artwork, Android pin and launcher match the release inputs. Publish the EXE, dependency-source ZIP and SHA256SUMS together, with the source tag and release notes.

Publish the same verified, game-free Android launcher separately as `Kart64TV-Android-TV.apk`, and include its hash in SHA256SUMS. Keep that filename on future releases so the `/releases/latest/download/Kart64TV-Android-TV.apk` URL remains suitable for a Downloader code. APK installation does not provision game data; keep that limitation visible in release notes until an on-TV import route exists.
