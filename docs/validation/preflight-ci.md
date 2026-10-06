# Archium preflight

Result: PASS
Trigger commit: fa28b2c0468188bfa3667ed4c029fcc079e3970b

```text
+ python3 scripts/generate-arc-patch.py
Generated Archium patch: 85 files
+ python3 scripts/check-arc-preparation.py --android-jar /usr/local/lib/android/sdk/platforms/android-36/android.jar
Pinned patch: all 85 files applied and hashes matched
ArchiumWindowClass: boundaries, reversible resize and repeated layout passed
ArcDesktopPolicy: AUTO/ARC/MOBILE, independent navigation and 4,238 palette cases passed
ArcSidebarState: identity, Spaces, closed pins, folders, roundtrip and invalid operations passed
ArcSidebarStore: restart, draft isolation, failed write, private memory and damaged state passed
ArcTabActions: reopen/select/close, native failure, failed metadata retry and lifecycle passed (command boundary simulated)
ArcCollectionsController: native pin/select/unpin, stable conversion, Spaces/folders, reopen and failures passed (command boundary simulated)
ArchiumAutofillPolicy: provider routing tests passed
ArchiumPasswordCsv: 21 synthetic cases passed
New Android adapters: isolated SDK API compilation passed (dependency contracts stubbed)
NullAccountManagerDelegate: unavailable account operation reported without exception
Full Chromium build/native tests and browser password/Arc/adaptive/input acceptance remain pending
+ python3 -m unittest discover -s tests -p 'test_*.py'
..........Checkpoint part 0: 64 bytes uploaded
Checkpoint part 1: 64 bytes uploaded
Checkpoint part 2: 64 bytes uploaded
Checkpoint part 3: 64 bytes uploaded
Checkpoint part 4: 64 bytes uploaded
Checkpoint part 5: 64 bytes uploaded
Checkpoint part 6: 64 bytes uploaded
Checkpoint part 7: 53 bytes uploaded
Checkpoint complete: 8 parts
Complete workspace restored, including timestamps and Ninja state
..................
----------------------------------------------------------------------
Ran 28 tests in 1.674s

OK
+ git diff --check -- . ':!patches/archium-desktop.patch'
+ bash -n scripts/build-archium.sh
```
