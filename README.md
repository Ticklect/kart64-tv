<p align="center"><img src="assets/kart64.png" width="88" alt="Kart64 TV icon"></p>
<h1 align="center">Kart64 TV</h1>
<p align="center">Mario Kart 64 on your TV. Bring your own ROM.</p>

![Kart64 TV installer](docs/screenshot.png)

I started this to get Mario Kart 64 running directly on my Samsung TV. It worked, so I'm turning the setup into something other people can use.

The desktop app finds TVs, prepares your game files locally, installs the TV app and can uninstall it again. It also keeps local compatibility-check results.

### Where it works

| Platform | Status |
| --- | --- |
| Samsung Tizen | A race tested on UE50U8000FKXXU with an Xbox controller |
| LG webOS | Experimental installer; needs hardware testing |
| Android / Google TV | Emulator reaches the start page; gameplay unverified |
| Fire OS TV | Experimental installer; needs hardware testing |

This is an early prototype. TV model and operating system matter. Roku, VIDAA and Vega OS aren't supported yet.

Startup on the tested Samsung still takes several minutes. Making that faster is the current priority; see [boot notes](docs/STARTUP.md).

### Try it

On Windows, install Python 3.12+, then run:

```sh
pip install -r requirements.txt
python studio.py
```

Select a TV and your own supported US Mario Kart 64 ROM (`.z64`) or SpaghettiKart archive (`.o2r`). Developer Mode and platform-specific pairing are required. No game files are included.

Android and Fire OS installation also require a locally built launcher APK; build instructions are below.

[Setup and development](docs/DEVELOPMENT.md) · [Android / Google TV](android/README.md) · [Fire TV](android/FIRE-TV.md)

Built on [Edd Mann's Kart64](https://eddmann.com/kart64/) and [Harbour Masters' SpaghettiKart](https://github.com/HarbourMasters/SpaghettiKart). This project adds the TV installer and integration. Not affiliated with Nintendo.
