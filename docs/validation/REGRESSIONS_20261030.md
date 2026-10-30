# Installed 0.9.119 regression repair

Owner reported Meet PiP stopped opening and favorites show one visible row.
Read-only device checks confirmed a live Meet document with the native PiP API,
whose tab-hide transition did not open a PiP. No camera controls were touched.

Favorite regression reproduced with the real production sidebar budget and eight
favorites: expected two complete rows, observed one, on both SDK30/36. The budget
subtracted160dp of collection chrome before ArcCollectionsView subtracted its own
chrome again. Remove the duplicate deduction; preserve the five external44dp rows,
112dp native tab reserve, caption, extensions row and frame padding. Tile size and
spacing are unchanged. GREEN:52/52 Android collection cases; footer24/24; geometry
policy1/1; SDK36 preparation6/6. Generated patch/manifest reproduced identically.

Roll back only the unaccepted native WebContents visibility observer adaptation:
its four upstream files now match the pinned, previously working selection owner.
Two host guards verify this exact restoration and one callback per tab transition.
This restores the original PiP route for device verification; the added automatic
entry on minimizing remains deferred. Do not infer physical recovery from host tests.
Camera processing, camera menu/defaults, omnibar, extension fixes and versioning are
unchanged. Owner authorized `go 4 fix n build`, permitted DeX disconnect, and requested
low quota mode. Reuse verified checkpoint41013119275-1; require full CI preflight and
normal native/APK/install gates. No clean build, profile reset or checkpoint deletion.
