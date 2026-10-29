# Mobile aura visibility follow-up

Installed build: run `40865729895`, SHA
`dba6ff7575970339db6fe855df4b709e4312056a`.

Owner feedback: the mobile improvement, particularly the button aura, is difficult
to perceive. A private phone inspection confirmed the neutral bar on an ordinary
website and that the native menu sheet covers the bar when opened. No screenshot
containing owner data is published. A later capture was interrupted by system UI;
no completed physical tab-selector or aura acceptance is claimed.

The production gradient's alpha at 72% of its radius was approximately 12.22/255
(4.8%), despite a 36/255 (14.1%) peak underneath the icon. On the existing
44x24dp pill this makes the surrounding halo weak. The new regression reproduced
this shortfall on Android API 30 and 36; all other 224 existing cases passed.

Change only the gradient stops: retain the 14.1% peak, carry the shoulder beyond
the icon, then fade to zero at the original boundary. Alpha at 72% radius becomes
approximately 30.56/255 (12.0%). Button/view bounds, hit targets, native actions,
context selection, page-derived colors, 220ms animations, glass, camera and
pull-to-reveal remain unchanged. No additional overlay, blur or sampling is added.
The follow-up question about an always-visible ambient aura is separate; this
change preserves the already-approved contextual behavior.

The shader regression reads the actual production drawable's gradient and checks
the shoulder, the 15% ceiling, transparent edge and selected strength. It measures
shader parameters with real Android views at mocked native boundaries; it is not
an exported render comparison or Samsung physical acceptance.

Validation: 226 Robolectric cases passed on API 30/36, 17 mobile host cases passed,
generated patch/manifest reproduced twice, and `git diff --check` passed.

Status: source follow-up only, pending new APK and device validation. The installed
APK is not modified by this source change. No new native build is launched here.
