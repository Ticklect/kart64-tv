# Startup work

The game runs, but booting on the tested Samsung UE50U8000FKXXU (Tizen 9) is too slow.

An existing installation was first observed engine-ready about 285 seconds after Start during the current debug test. The preceding observation was still loading at 260 seconds, so this is a range, not an exact boot time. Earlier diagnostic runs recorded about 263–296 seconds, and one first launch recorded about 659 seconds. These are individual observations on one TV.

The current investigation separates runtime file reads, WebAssembly compilation, saved-data restore, asset loading and engine startup. Desktop timings do not predict TV boot speed. First launch after an update and repeat launches are being checked separately.

The first candidate removes an extraction-only preload and records startup stages. It is still under test: no TV speed-up is claimed yet. Large packaged-file reads are a confirmed source of delay; one observed WebAssembly read alone took 157 seconds before compilation.

Saves and settings must survive updates. Game files and raw private test outputs stay off GitHub.
