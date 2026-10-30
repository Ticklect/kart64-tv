# Experimental Android / Google TV route

This app embeds Mozilla GeckoView 159.0.20261022150525 and serves private local game files to that engine through a loopback-only server. It does not open a remote game website. The game files are supplied separately by the player. No ROM, extracted game archive or signing key belongs in this repository.

The Android TV emulator installed the APK, opened the launcher, reported shared WebAssembly memory, WebGL2 and cross-origin isolation, accepted private game files and reached the Kart64 browser start page. A complete game boot, race, physical controllers, saves across restart and real-TV performance remain unverified. Browser gamepad API presence is not proof of physical controller support.

The earlier WebView experiment lacked shared memory support in the emulator. The shipping prototype uses GeckoView instead; its native engine makes the universal APK large (approximately 509 MiB). The manifest targets Android TV launcher discovery, supplies a banner and the custom icon, and does not require touch input. Minimum Android API is 26; this does not guarantee every Android 8+ TV can run the game.

## User setup

The standalone APK is available at [this stable download URL](https://github.com/Ticklect/kart64-tv/releases/latest/download/Kart64TV-Android-TV.apk). It can be entered into AFTVnews's URL shortener for use in Downloader on compatible Android/Google TV and Fire OS devices. The APK installs the launcher only; phone/USB import is not implemented. Continue with the PC setup below to prepare and transfer your own game data.

1. Enable debugging and pair the Android TV with the PC using official Android platform-tools. Modern wireless debugging may use a port other than 5555. The installer does not turn debugging on or grant access for you.
2. Ensure `adb` is on PATH and the paired network target is shown as `device` by `adb devices -l`.
3. Scan in Kart64 TV. Discovery queries only already-authorised private-network ADB targets and verifies the Android TV feature before offering the experimental adapter. Emulator and USB targets are excluded from production discovery.
4. Select that device and your own supported ROM or compatible archive. The installer verifies the bundled APK hash, prepares game data locally, installs the APK and streams an allowlisted tar into the application's private storage. It does not stage game files in shared Android storage.
5. Open Kart64 TV from the television's app list and run its capability check. Physical controller pairing still occurs in TV settings.

Brands are not operating systems. Sony, TCL, Hisense and Philips examples apply only when their selected model actually runs Android TV / Google TV. Roku, VIDAA, Titan OS and other variants are not covered by this adapter. Eligible Amazon Fire OS TVs now have a separate experimental detection route reusing this APK; see FIRE-TV.md. Fire OS gameplay is not hardware-tested. Vega OS is not covered.

## Build

Requires JDK 21, Gradle 9.7.1, Android SDK platform 37 and installed Android build tools. From the repository folder run `gradle -p android assembleDebug`. Dependencies are downloaded from Google, Maven Central and Mozilla's Maven repository. The current prototype is a debug-signed app because provisioning uses ADB `run-as`; it is not a Play Store release build.

After a verified build, copy the APK to `assets/kart64-android.apk` and refresh `assets/android-runtime.json` with its SHA-256 and size. Alternatively set `KART64_ANDROID_APK` to a verified APK with that filename when building the desktop executable. The desktop spec rejects a hash mismatch. Review Mozilla, NanoHTTPD, Android and bundled native-library notices and signing/update policy before public distribution.
