# Camera and Document PiP follow-up

Installed baseline: `8f312c0519ec143ae414723bf356d5212339827d`, run40545718060. Candidate changes below are not installed and are not physical acceptance.

## Evidence

- User: Auto shows enlarged portrait camera inside landscape output; manual90 corrects orientation. This rejects automatic aspect calibration as an orientation fix. No cache/data deletion is justified.
- Physical Meet, no other participants reported: system selector captured external DeX2400×1350 and Samsung Notes application2400×1294. Camera1280×720 remained locally live/enabled. This is not remote transmission confirmation.
- Document PiP initial outer361×220 versus inner1503×766. Notes PiP enlarged natively from1059×712 to1358×898 while inner remained2681×1702; visualViewport.scale≈0.527174, no viewport meta. Lower controls were partially outside view. A sustained shrinking loop after manual enlargement was not reproduced; Zoom report is user evidence only.
- Native Android capture ended (`dumpsys media_projection`:null). No note was edited/deleted; accidental selection during a resize attempt was cancelled. Evidence contains private screenshots and stays outside Git: `/workspace/.local/state/archium-pip-resize-20261027/`.
- Returning through native Main launch opened Meet home. Restoration navigation coincided with user DeX disconnect; do not claim the original call was left joined. User opened a new meeting (target1112), detected active. Further layout-control attempt after reconnect was NOT RUN: focusing Archium was unreliable, and no URL/text was typed into other apps. Termux restored; own forward/server removed; network/DPI/orientation settings unchanged.

## Local changes

Camera: restore the pinned `AdaptFrameResolution` body exactly. Auto/native and Manual0 keep native constraints and frame geometry. Explicit manual quarter-turn composes metadata only after native adaptation, retaining visible rect, natural size, mirror and buffers. Rotation is applied once per cached target result, so cloned tracks do not rotate repeatedly. Screen capture is excluded. Automatic physical camera orientation remains unresolved; no arbitrary automatic90 is introduced.

PiP: apply desktop viewport defaults only to Android WebContents with `GetPictureInPictureOptions()`. Those options are set before initial renderer preferences in pinned WebContentsImpl. The generic Android desktop preference path checks device form factor and skips phone-class hardware; the observed child inherited mobile shrink-to-fit. The candidate disables mobile viewport/meta/shrink/orientation-resize behavior for the child and uses upstream desktop min/max scales1/4. It does not force a page-scale value, inject site CSS/JS, alter the opener/ordinary pages or change native window bounds. Exact visual correction and any remaining resize loop require the candidate APK in DeX.

Added an opt-in layout-only PiP fixture, with/without child viewport meta as a control. No camera, microphone or screen request on that page. The control comparison did not run on device; do not report it PASS.

## Validation

- RED saved before changes: camera native-adapter invariant/manual policy; child-only PiP policy absent.
- GREEN:3 camera tests execute delivered policy/size math and compare native resolution adapter with pinned implementation;1 PiP policy test executes delivered block with explicit value-type seams. These are not native frame/Android window tests.
- Final focused cohort17/17 PASS (camera3, PiP1, Googlebook/JNI12, header style1); full preparation with Android SDK36 PASS, including6 embedded tests (Chrome/JNI dependency boundaries are fixtures).
- Patch generation/reproducibility and delivered transition are required before candidate publication. Full final host/native compilation, physical camera/manual reset, PiP fit/resize, camera+mic+screen with another participant and performance remain PENDING.
- No workflow dispatch, installation, checkpoint deletion or clean build authorized/performed in this follow-up.
