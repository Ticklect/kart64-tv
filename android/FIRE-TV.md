# Experimental Fire OS TV route

This route reuses the Android APK and embedded GeckoView engine. It is offered only for an authorised private-network ADB target that reports the exact `amazon.hardware.fire_tv` package-manager feature. Amazon's brand name or an `AFT` model string alone is not enough.

Before installation, discovery and the installer check Android API level 26 or newer and a runtime ABI from arm64-v8a, armeabi-v7a or x86_64. Older Fire OS 5/6 devices are rejected. Recent Fire OS 7/8/14 devices may satisfy those checks; satisfying them is not a measured gameplay result. No physical Fire TV has been tested in this project.

Amazon Vega OS is not Android and is not covered by this APK route. The official Amazon device specifications must be checked for the actual OS of a model; recent Fire TV products use both systems.

Enable ADB debugging on the Fire OS device, open Devices in the installer and enter the TV's local address with its ADB port. Press Connect ADB and approve the debugging prompt on the TV. For modern Android wireless debugging, pairing may need to be completed with official platform-tools before connecting. Select the detected device and your supported local game file, then install. The game data stays in the app's private Android storage.

The APK declares the standard Android launcher and TV launcher intent filters, includes the custom icon and TV banner, and requires no touchscreen. Amazon documents that sideloaded apps can be launched from the Apps area or Settings → Applications → Manage Installed Applications. Actual Fire TV home-screen behaviour, remotes, gamepads, saves and gameplay remain unverified.

Primary references:

- https://developer.amazon.com/docs/device-specs/identify-fire-tv-devices.html
- https://developer.amazon.com/docs/fire-tv/fire-os-overview.html
- https://developer.amazon.com/docs/fire-tv/installing-and-running-your-app.html
