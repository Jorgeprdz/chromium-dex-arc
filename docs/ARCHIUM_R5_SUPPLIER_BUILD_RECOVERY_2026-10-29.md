# Native supplier API correction and incremental recovery

Run 40819836489 at `677c73fcebd14d37b52ec68e2dffba627282c0bf` failed during Java compilation:
`MonotonicObservableSupplier<TabBookmarker>` has no `onAvailable()` method.
The previous isolated adapter gate did not compile this coordinator registration.

Use the pinned API `addSyncObserverAndCallIfNonNull`, wrapped by the existing
callback controller so activity destruction cancels delivery. The already-created
Archium coordinator receives an available bookmarker synchronously or its later
non-null publication. No bookmark, camera, profile, viewport or pull-to-reveal
behavior is otherwise changed. Mobile polish remains the separate preceding commit
`ade31be26b742f6ffafbfa4a351a1dfe776ae30c`.

The new host regression first reproduced the exact missing-method diagnostic, then
passed with the corrected registration and verifies lifecycle cancellation wrapping.
The upstream API fixture is immutable and SHA-256 checked. The SDK preparation gate
also passes; neither proves a full native build or physical acceptance.

Recovery source: `archium-checkpoint-40819836489-1`, commit `677c73f...`.
All four artifact identities/digests/expiry and the 25-part embedded manifest were
validated using only 5,381 remote bytes. Manifest SHA-256:
`6aa28137ce4d470fbd58f7e71edc18be3072316ccceec3e91bb75140bf395258`.
The immutable receipt is in `config/checkpoint-receipts/`.
Runner capacity, full part hashes and restored workspace remain `PENDING_CI`.
No clean fallback is authorized.

User subsequently authorized the next incremental build and verified installation.
The private watchdog may recover this identified failed run only after this tested
fix, exact source/ref guards, verified checkpoint, and terminal old installer with
`BUILD_FAILED` / `NO_APK`. One dispatch intent prevents duplicate independent builds.
Installation remains conditional on a successful APK, source/package/ABI/checksum/
signature checks and the authorized device being available without active capture.
No data clear, uninstall or forced camera interruption is used.

Native build and Samsung appearance/functional acceptance: pending next run/device.
