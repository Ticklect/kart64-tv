# Binary notices and source

Kart64 TV's installer and integration are MIT licensed. The app includes Python 3.12.10, PySide6/Shiboken6 and Qt 6.11.1, and the PyInstaller bootloader with its distribution exception. Their licenses are supplied alongside this file.

The experimental Android launcher includes Mozilla GeckoView 159.0.20261022150525 (MPL 2.0 and the third-party licenses in `GeckoView-LICENSES.html`), NanoHTTPD 2.3.1 (BSD) and AndroidX components (Apache 2.0). No game files are included.

## Corresponding source

- Application and Android launcher: https://github.com/Ticklect/kart64-tv/tree/v1.0.1
- Qt, Qt SVG, Qt Image Formats, PySide6 and Shiboken6: the unmodified source archives in this release's `Kart64TV-1.0.1-DependencySources.zip`. Exact upstream URLs and SHA-256 values are in `dependency-sources.json`.
- GeckoView: the unmodified Mozilla Firefox source revision recorded inside the shipped engine's build configuration: https://github.com/mozilla-firefox/firefox/tree/9a2dc53c369c7ae5172018b35988e1d2ffeff402 . Full source archive: https://github.com/mozilla-firefox/firefox/archive/9a2dc53c369c7ae5172018b35988e1d2ffeff402.tar.gz . Its third-party libraries, including the LGPL components, are in that source tree.
- NanoHTTPD: https://github.com/NanoHttpd/nanohttpd/tree/nanohttpd-project-2.3.1
- AndroidX: https://android.googlesource.com/platform/frameworks/support/
- Python: https://www.python.org/downloads/release/python-31210/
- PyInstaller: https://github.com/pyinstaller/pyinstaller/tree/v6.22.3

## Rebuilding with modified Qt libraries

Modification and reverse engineering for debugging modified LGPL libraries are permitted. The application does not check signatures or hashes of Qt/PySide libraries. The Android runtime hash check is separate.

Build your modified Qt/PySide6/Shiboken6 using the supplied source archives and their build instructions, then install that PySide6 build into a Python 3.12 environment. Check out this application's release tag. Install PyInstaller 6.22.3. The application's complete Python source and `Kart64TV.spec` are provided; no private application object files are required.

The Windows EXE no longer contains an Android APK. An Android build is not required to rebuild Windows or replace Qt. To modify the separate Android launcher, follow `android/README.md` and update its download manifest before rebuilding Windows.

Rebuild using `python -m PyInstaller --noconfirm Kart64TV.spec`. This uses your installed, potentially modified Qt/PySide6 libraries. If you rebuild the Android launcher, update its local hash pin as described in its README. No signing key or ROM is needed to rebuild the Windows application.
