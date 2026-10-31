Mario Kart 64 on your TV. The Windows app finds your TV, prepares your own game files and installs the TV app.

**Much smaller downloads:**

| Download | Size |
| --- | ---: |
| [Windows](https://github.com/Ticklect/kart64-tv/releases/download/v1.0.1/Kart64TV-1.0.1-Windows-x64.exe) | 36 MiB (was 272) |
| [Android / Fire OS — ARM32](https://github.com/Ticklect/kart64-tv/releases/download/v1.0.1/Kart64TV-Android-TV-armeabi-v7a.apk) | 94 MiB |
| [Android / Google TV — ARM64](https://github.com/Ticklect/kart64-tv/releases/download/v1.0.1/Kart64TV-Android-TV-arm64-v8a.apk) | 99 MiB |
| [Android — x86-64](https://github.com/Ticklect/kart64-tv/releases/download/v1.0.1/Kart64TV-Android-TV-x86_64.apk) | 105 MiB |
| [Universal APK](https://github.com/Ticklect/kart64-tv/releases/latest/download/Kart64TV-Android-TV.apk) | 255 MiB (was 509) |

Windows now downloads only the Android build your TV needs, verifies it and caches it for reuse. Samsung and LG users no longer download an Android APK. Unsure which processor you have? Use the Windows app or universal APK. Sizes exclude game files; Android extracts native libraries during installation.

**Downloader code: `7989374`** — the existing link now supplies the smaller universal APK. The Windows app is still required to prepare and transfer your own supported US ROM or `.o2r`; phone/USB import is not included. No game files are bundled.

Samsung has a tested race and Xbox controller. LG, Android/Google TV and Fire OS remain experimental; Vega OS is unsupported. New packaging passed PC checks and Android TV emulator launcher tests; it has not been tested on physical TVs. No new boot-speed or FPS claim in this update.

Built on Kart64/SpaghettiKart. [Credits and rebuild instructions](https://github.com/Ticklect/kart64-tv/blob/v1.0.1/packaging/SOURCES.md) · [Dependency sources and licenses](https://github.com/Ticklect/kart64-tv/releases/download/v1.0.1/Kart64TV-1.0.1-DependencySources.zip).
