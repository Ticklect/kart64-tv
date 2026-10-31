# Smaller downloads implementation plan

Goal: remove the Android payload from Windows and distribute compressed, independently installable per-ABI Android APKs.
Architecture: retain GeckoView and existing local game provisioning. A pinned manifest supplies immutable release URLs, sizes and SHA-256 hashes. Windows selects the first supported ABI reported by the OS and caches the verified APK in LocalAppData. Keep a compressed universal APK at the existing stable Downloader filename.
Constraints: no physical TV access; no game files or keys in releases; preserve app identity and signing continuity; do not claim Android gameplay or new boot measurements.

- [x] Write failing download/cache tests: ABI order, unsupported CPU, verified cache reuse, tamper, interrupted/truncated/oversized/wrong-hash downloads and HTTPS downgrade.
- [x] Implement android_runtime.py; wire the Android worker to it; remove APK from the desktop spec. Verify the complete Python and Node suites.
- [x] Configure ABI APK outputs and compressed native libraries; increment Android version to 1.0.1/code 6. Build and verify signatures, manifest, architecture and contents.
- [x] Generate per-ABI release pins and update build/source instructions. Build the Windows EXE and verify frozen self/smoke tests and absence of embedded APK.
- [x] Publish v1.0.1 with hashes, corresponding sources, smaller APKs and compatible universal filename; verify remote assets and stable link. Keep physical TV testing explicitly pending.

Review focus: OS ABI order (32-bit OS on 64-bit hardware); poisoned cache; partial files; redirects losing HTTPS; Downloader universal compatibility. Tests cover download failures and ABI choice; actual artifacts and signed manifests verify packaging. Native library compression trades smaller downloads for extraction during installation; measure download bytes rather than promise installed disk savings.

Verified: Python 64/64, Node 35/35; all APK v2 signatures use the previous certificate; ABI contents, compression and private-file exclusions passed. Frozen Windows archive excludes APKs and passes self/smoke tests. API 36 x86-64 emulator installed and opened both x86-64 and universal builds, all four launcher capability checks true; private test marker survived update and was removed. Emulator stopped. Independent review found no important issues; stale development manifest description corrected. Physical TVs untouched.

Integrated remote Version 1 changes (Downloader UI/code, platform version labels). Android versionCode is 6, exceeding public Version 1 code 5. Rebuilt and reverified all signatures, ABI outputs and pinned hashes; rebuilt Windows and repeated frozen checks. Python 66/66 and Node 35/35 pass. A second emulator boot was prevented by the existing AVD disk-space check; earlier compression smoke checks used the same engine/app code with versionCode 5 before incrementing it to 6. No physical TV calls.

Published v1.0.1 as Latest. GitHub server-side SHA-256, byte size and upload state match all seven release assets. Anonymous APK and Windows download URLs return 200 with expected sizes. Existing universal Downloader URL resolves to 267,862,038 bytes. Production download helper fetched ARM32 from the public release and verified its pin successfully. GitHub CI run 41217494850 passed. Local dist and desktop EXE copies updated.
