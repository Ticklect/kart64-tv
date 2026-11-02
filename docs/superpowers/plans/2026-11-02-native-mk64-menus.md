# Native MK64 menu revision

The previous preview's blue panels and generic italic type failed the requested game fidelity. This revision follows Nintendo's original Game Select, Player Select and pause references: https://www.nintendo.co.jp/wii/vc/vc_mk64/vc_mk64_02.html . The player's existing archive supplies the original artwork and font locally; the public source, installer and APK contain conversion code, not those assets.

- Generate one bounded private `tv-game-theme.css` from explicitly allowlisted O2R textures. Decode RGBA32/RGBA16/I4; produce embedded PNGs, a cropped font atlas and native title graphics. Incompatible archives retain accessible fallback text. Never extract arbitrary ZIP paths or publish the generated stylesheet.
- Include the derived skin only in private Tizen, webOS and Android game content. Both supported ROM conversion and archive input converge on the same path. Existing Android game content must be prepared/transferred once for authentic artwork; APK-only upgrades retain the fallback interface until then.
- Shared progressive text renderer keeps accessible labels and DOM text stable. No remote fonts/images or engine changes. Main pause uses the actual paused canvas; secondary pages use tinted original menu artwork. TV launcher uses the original title art. Keep remapping, save/exit protection and raw menu controls.
- Verify synthetic decoder fixtures and private packaging, missing-art startup, real-game PC pause/remap/save integration, and launcher D-pad/stick/keyboard navigation. Capture actual PC screens at 720p. Android build and standalone PC package checks precede any new release. No physical TV access.

Current evidence: seven new synthetic-only texture/package checks pass, all 78 Python and 45 Node checks pass, owned-game PC browser integration passes, launcher horizontal D-pad/stick and PS5-layout confirm pass. Missing optional artwork still boots with a usable menu. Android compilation passes. Physical controller and TV validation remain pending. The user explicitly approved this original MK64 direction. Final delta review found no additional important issues; the reviewer’s stale-skin finding was fixed and regression-tested.


Final refinements: shared TV startup replaces the browser setup, readable fallback remains usable without artwork, early focus skips disabled Play and does not jump away from Controllers when readiness changes. Player colours follow assigned player slots. HUD hints are pointer/focus-only; diagnostics stay visible when explicitly opened. Upstream engine authors are credited on startup. Emulator confirmed the genuine artwork/font render in Gecko and exposed a short-viewport footer issue, which was corrected. No physical TV access.


Final checks: the native APK reached engine-ready in the isolated Android emulator and Back displayed the themed pause menu over the game intro. The emulator was stopped. First-paint cover is validated with JavaScript disabled in the PC browser and by the compiled Java upgrade/idempotency check. This prevents the previous browser setup flashing while local scripts load. Final public packages contain only the converter/renderer, not the generated skin.
