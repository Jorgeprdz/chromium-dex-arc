# Archium R5 QEMU validation

Status: **QEMU_ABI_BLOCKED**

Local infrastructure observation on 2026-10-19 using the verified historical artifact from run 38602932971; this is not a new-APK validation. CI regenerates this report from its exact same-run artifact.

Hardware-specific validation: **PENDING_DEVICE_VALIDATION** (Galaxy GPU, Samsung Internet comparison, physical input and phone/DeX transitions).

```json
{
  "schema_version": 1,
  "status": "QEMU_ABI_BLOCKED",
  "source_sha": "90d3f9e5be9bccc047ebba5115aff3ae8a610e5f",
  "run_id": "38602932971",
  "apk_sha256": "cca0e5eba76bab179c5ae132dcb3353bfeb9e2d32dcc652a65d6bef8c3b4064d",
  "device_validation": "PENDING_DEVICE_VALIDATION",
  "artifact_verification": "PASS",
  "apk": {
    "package": "app.archium.android",
    "abi": "arm64-v8a",
    "signature": "VERIFIED",
    "package_version": "package: name='app.archium.android' versionCode='808600074' versionName='157.0.8086.0' platformBuildVersionName='' platformBuildVersionCode='' compileSdkVersion='37' compileSdkVersionCodename='17'"
  },
  "environment": {
    "host_arch": "aarch64",
    "host": "Linux-6.17.0-PRoot-Distro-aarch64-with-glibc2.36",
    "kvm_accessible": false,
    "emulator": null,
    "emulator_version": "UNAVAILABLE",
    "qemu_system_aarch64": null,
    "avds": [],
    "api": "NOT_EXECUTED",
    "abi": "NOT_EXECUTED",
    "renderer": "NOT_EXECUTED",
    "display": "NOT_EXECUTED",
    "acceleration_usable": false
  },
  "reason": "No usable native ARM64 host + accessible KVM + existing API36 ARM64 AVD/emulator. x86_64 acceleration does not execute ARM64 guests; no x86 substitute or slow unbounded software boot attempted."
}
```

| Case | Status | Evidence / reproduction |
| --- | --- | --- |
| Install, launch, activity foreground and screenshot | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Open deterministic local compositor fixture | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Five scroll cycles; inspect image/text/canvas tiles | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Alert, confirm, prompt, HTML dialog; scrim/focus restoration | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Keyboard and pointer/touch input; focus restoration | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Narrow/maximized resize, sidebar collapse/expand | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Minimize/restore, switch tabs, lock/unlock | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Repeat fixture and viewport transitions in incognito | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Inspect compositor/renderer output and crash diagnostics | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Continuous scroll with high-resolution images | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Long lists and dynamic page updates | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| CSS sticky and fixed elements during scroll | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| CSS transforms and animations | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Canvas and accelerated content | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Resize the window while scrolling | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Suspend and restore the rendering surface | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Inspect black blocks, tearing and duplicated content | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Native Chromium dialogs and actions | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Scrim visibility and window stacking order | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Switch tabs while a dialog is open | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Sidebar hover, focus and selected tab | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Omnibox focus, typing, navigation and cancellation | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Native back, forward and reload controls | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Footer geometry and residual lower clipping | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Tab and navigation-state persistence | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Viewport CSS dimensions, device scale and zoom | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Open and close multiple tabs without losing state | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Back and forward navigation preserves content | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Background and foreground lifecycle | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Activity recreation with retained state | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Orientation, density and display-size changes | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |
| Controlled memory pressure and recovery | BLOCKED | QEMU_ABI_BLOCKED; no Android execution, logs or screenshots |

Reproduce: download the same run’s `Archium-for-Android-arm64` artifact, then run
`python3 scripts/validate-r5-qemu.py --artifact-dir ARTIFACT --source-sha SOURCE_SHA --run-id RUN_ID --output-dir QEMU_OUTPUT`.

The existing local fixture is `tests/fixtures/rendering/r5-compositor.html`. Fixture, scroll, dialog, keyboard, window/lifecycle and incognito cases remain NOT_TESTED until exercised with observable evidence. Startup and a screenshot cannot establish visual correctness. No screenshot is claimed for a blocked run.

Infrastructure references: [Android emulator acceleration](https://developer.android.com/studio/run/emulator-acceleration), [emulator release notes](https://developer.android.com/studio/releases/emulator). ARM64 host support depends on the actual emulator/image distribution; absence here does not prove universal impossibility.
