# Desktop follow-up approved requirements

The owner approved keeping Archium in 0.9.x, with an increment per new build,
stable numbering across resumptions, separate Chromium identification, and the
About/info action last in its footer row. Other requested corrections: adaptive
favorite columns and enough complete rows, unchanged 50dp tiles and 3dp margins,
some air before folders, and an intact New Folder action above its separator.
Opening the native extensions menu must work from the general menu.

Meet's current physical behavior is verified: switching tabs opens Document PiP;
minimizing directly does not; an existing PiP survives minimization. Zoom did not
open PiP in either path. Preserve native meeting behavior and distinguish these
two implementations; do not claim that enabling a browser API makes Zoom use it.

Camera is the owner's highest-priority working feature. Only simplify its menu:
90°, 180°, 270°, with existing selection retained and 90° as the default. Remove
Auto, Manual wording, Rotate and automatic Reset. Leave the delivered VideoFrame
adapter, resolution math, buffers, mirroring, screen-capture exclusion and capture
lifecycle byte-identical. No running meeting is modified for implementation tests.

The owner subsequently authorized implementation of all changes, incremental
build and installation, and requested the Linux monitor at the end. DeX will be
disconnected during work. No checkpoint deletion or profile reset is authorized.
Pending physical acceptance must be reported explicitly.

Approach: retain existing native owners and add the minimum browser integration.
Build metadata must be packaged independently of Chromium's versionCode and
versionName; the checkpointed metadata identifies resumptions. All changes are
reviewed as source/host results before any native build.

The 0.9.N sequence uses the CI workflow number (it may skip numbers), with a
checkpoint lower bound to prevent regressions. Repeated stages or continuations
of the same source keep their original version. Native package version and
signing identity stay compatible with the installed application.

The owner also requested a very subtle omnibar enlargement on sidebar and Mobile.
Increase the visible capsule by 2dp, retaining layout, editor, focus, touch,
gestures and viewport geometry. Desktop topbar and command overlay are excluded.
