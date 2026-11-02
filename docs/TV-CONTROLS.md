# TV controls preview

This preview adds a TV menu around the existing game. Xbox/PS5 browser-standard layouts have matching labels. Xbox previously worked on the tested Samsung; physical PS5, Android controllers and multiplayer still need hardware testing. Four browser player slots are implemented, not a four-player performance certification.

## Open the menu

- TV remote: Back. On Android, the host intercepts Back during the game so it opens the TV menu instead of closing the app.
- Xbox: View + Menu together. PS5: Create + Options together.
- Keyboard: Esc or F1. The on-screen TV menu button works with a pointer.
- Navigate with the original D-pad / left stick, A / Cross to select and B / Circle to go back. TV remote D-pad / OK and keyboard arrows / Enter also work. Gameplay remaps do not change menu navigation.

Back returns to the main TV menu; only selecting Resume resumes play. This avoids Android browser/native Back events accidentally toggling play.

The menu stops the supported engine main loop and mutes its audio output while open. Single Menu / Options keeps the original game's Start function. Backgrounding and a watched controller disconnect request a pause. Reconnection never resumes automatically. If a controller will not return, explicitly choose Continue with connected controllers, then Resume.

## Bindings and controller testing

Open Controllers & bindings. Each detected controller shows physical button names, live axes, current player slot and a remap editor. Press a button to make already-paired hardware visible to the browser. Pairing itself remains in TV settings.

Select a logical gamepad input, release all controls, then press its replacement physical button. For an axis, centre the sticks and move the replacement axis right or down; inversion is recorded. TV Back / Esc cancels listening; capture times out after 15 seconds. Reset restores defaults. Deadzone is adjustable. Controller IDs and bindings are stored locally; absent-controller profiles are retained. Identical controller models or changed browser connection indices may need manual reassignment.

Player assignment swaps an occupied slot rather than giving two pads the same player. Gameplay input stays neutral while the menu is open and until held controls are released after resuming. TV/system-reserved buttons are controlled by the TV OS and may not be exposed to the browser.

## Sound, display and exit

Volume/mute controls the actual game audio gain. Render scale offers 50%, 75% and 100%; this changes internal rendering, not HDMI output mode. No FPS gain is promised. Preferences are local and restored on startup.

Exit requires a separate confirmation and synchronises existing saved files before navigation. Saving errors or a timeout cancel exit and leave the game paused. Menu navigation is locked while an exit save is pending. This preserves game save files, not the current mid-race state. OS termination, power loss and hardware Home remain outside that confirmation flow.

## Loading

The loading screen shows actual startup marks from Kart64Boot, the runtime's status message and elapsed time. It does not invent a completion percentage. Runtime failures expose their message and a retry action. TV builds suppress the upstream mobile touch deck, even on devices reporting touch points.

## Validation

- 123 automated checks: 78 Python (including a compiled Java page-upgrade check) and 45 Node.
- Real PC browser game boot with owned private game data: engine pause stops buffer swaps; resume restarts them. Synthetic Xbox/PS5 raw input exercises remapping, menu navigation independent of bindings, player assignment, sound gain, render scale, disconnect/reconnect, save-error exit protection and a saved-file round trip.
- Android TV API 36 x86-64 emulator: APK installs/updates, private files survive, game reaches engine-ready, Back opens the TV pause menu, and D-pad/OK reaches controller setup. These checks do not establish race visuals, physical controller behaviour or Android-TV performance.
- No physical TV was accessed for this preview.

For the opt-in browser integration check, install Playwright, prepare a private runtime directory and set `KART64_TEST_RUNTIME` to it, then run `node packaging/verify_tv_browser.cjs`. Optional `PLAYWRIGHT_MODULE` and `CHROMIUM_EXECUTABLE` select local tooling. The harness binds only to PC loopback and never sends game data to a remote server. Do not publish that directory.

The new Android APK bundles the TV shell and augments the supported existing installed page in memory; upgrading the APK does not replace private game files or saves. Other platforms receive the shell when their package is rebuilt by the desktop installer. Physical-TV validation remains pending.


## Second preview: interface redesign

Preview 2 replaces the original form-style interface with a consistent navy/gold racing menu. Both controllers fit side by side with live diagrams, physical button highlights and stick movement. Bindings are grouped into Buttons, D-pad & clicks, and Sticks & deadzone. The sound screen has a real volume meter and selected render-scale cards. Focus remains on the chosen volume control after changing its value. Engine pause, safe exit, remapping persistence and disconnect protection retain their existing tests. Screenshots use simulated controller input; physical hardware validation is still pending.


## Third preview: classic kart-racer theme

Preview 3 applies a stronger Mario Kart 64-inspired menu style to the TV launcher, loading screen, pause menu, controller setup, bindings, sound/display and exit confirmation. Bright blue frames, orange/yellow outlined headings, bevelled buttons, selection arrows and original CSS chequered artwork replace the navy/gold dashboard styling. No Nintendo artwork or fonts are bundled. No extra image downloads or game changes are involved.

The 1280 × 720 launcher and standard menu pages fit their main controls without scrolling. The PC browser game integration checks are rerun with synthetic Xbox/PS5 inputs. These are real app screenshots on PC, not TV captures. The earlier Android emulator checks above apply to Preview 1; Preview 3 is not a fresh emulator or physical-TV validation.


## Fourth preview: original-game menus

The launcher uses the original title, background and Game Select artwork; controller setup uses Player Select styling, and the sound screen uses the original Option heading. The pause menu uses the game's sprite font over the actual paused canvas. Tizen/webOS receive a matching in-game startup screen instead of the upstream browser setup. Mouse-only menu/diagnostic hints disappear during controller play; Back, the controller chords and F8 still open their tools.

These assets are prepared **locally from the player's supported archive**, including archives converted from a supported ROM. They are not bundled in the public APK or Windows EXE. A bounded, allowlisted converter writes one private `tv-game-theme.css` into the installed game content. No external artwork/font downloads are needed. Incompatible/custom archives keep readable fallback text. Android transfers explicitly reset an old skin when the replacement archive lacks native assets.

**Existing installs:** prepare and transfer game content once using this preview's Windows app to obtain the original artwork/font. Installing only the new APK updates the layout and controls, but cannot supply game assets. APK updates preserve private game files and saves.

Seven synthetic-only decoder/packaging tests cover formats, byte order, alpha, invalid resources, private output and stale-skin reset. PC browser checks cover both native and missing-art startup, TV-remote keyboard navigation, independent raw controller input, pause/resume, saved remaps, safe exit and actual saved-file round trips. A separate game-free launcher check covers horizontal D-pad/stick navigation, PS5-layout confirm, missing game content and unsupported device states. Screenshots show the real app in a PC browser, using simulated controllers; the pause screenshot was captured in an actual race. Physical controller, real-TV performance and multiplayer validation remain pending.


Preview 4 was also checked in the API 36 Android TV emulator: original artwork/font render in Gecko, the compact launcher footer fits, remote D-pad/OK opens controller setup, the game reaches engine-ready and native Back opens the themed pause menu over the intro. The old browser setup is covered before JavaScript executes. These checks do not certify Android race performance or physical controllers. The emulator was stopped after testing.
