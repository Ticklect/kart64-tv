# Startup

Version 0.1.3 reached the engine in **127.9 seconds** on its first launch after updating the Samsung UE50U8000FKXXU (Tizen 9). A repeat launch took **172.1 seconds**. Startup still takes roughly two to three minutes on this TV.

| Observation | Start to engine ready |
| --- | --- |
| Previous existing installation | Between 260 and 285 seconds |
| Earlier recorded first launch | About 659 seconds |
| 0.1.3 first launch after update | 127.9 seconds |
| 0.1.3 repeat launch | 172.1 seconds |

These are individual debug-mode observations on one TV, with different cache conditions. Timing starts at the app's Start action, rather than turning on the TV. It ends at the engine-ready signal, rather than a completed race. Other TVs may behave differently.

## What changed

- Samsung reads installed runtime and game files through its native package reader, with a browser fallback. An isolated 8 MB read took about 3.2 seconds; one earlier browser-loader read took 157 seconds.
- Saved-data restore uses a bulk key lookup instead of walking 204 database entries one at a time. The restore stage fell from about 105 seconds in the preceding candidate to 23 seconds in this run.
- The app skips an 8 MB extraction-only preload. Game data is already prepared on the PC, so the TV does not need those recipes.
- Installed game archives stay separate from save-data sync. Existing saves and settings are restored, and local diagnostics retain each boot stage.

The Samsung package declares the read-only filesystem privilege for its installed assets. The native reader follows Samsung's [file-operation API](https://developer.samsung.com/smarttv/develop/guides/data-handling/managing-file-operations.html). It accepts fixed runtime filenames and bundled course paths. Other platforms retain the browser reader; their hardware performance is unverified.

Validation includes 88 automated tests, actual browser cold/repeat game boots and a saved-file round trip. On the TV, the existing save file's SHA-256 stayed unchanged across a complete app restart. A separate temporary test file also survived the restart and was then removed from both memory and IndexedDB. Game files and raw private test outputs stay off GitHub.
