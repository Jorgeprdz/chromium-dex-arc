# Shallow-checkout preflight recovery

Run `40832111956`, SHA `7a670e3ff4702c38f2fb0360cf8e93d95de98d9b`, stopped in
host preflight: 512 test cases ran, with six subtest errors from unavailable Git
objects for base `677c73fcebd14d37b52ec68e2dffba627282c0bf`. Native compilation
was skipped. The first run `40819836489` failed in native Java compilation;
its supplier API fix remains included in this branch.

The mobile ownership checks now compare current source with immutable SHA-256
values derived from that exact original base, including full protected files and
individual unchanged method bodies. They no longer read ancestor objects at runtime.
A filesystem-only regression first reproduced all six errors. It now passes and
also proves that modifying the protected pull owner still fails the checks.
No production source, camera, pull-to-reveal, workflow or geometry changed here.

The user authorized correction and relaunch with both desktop FIX/polish and mobile
polish together. The next single incremental chain uses the verified checkpoint
`archium-checkpoint-40819836489-1`, not the failed preflight run (which compiled
nothing). Retain the existing verified installer and notifications, with a separate
run state folder so the failed run cannot be mistaken for the active one.
Native build and physical acceptance remain pending until actual evidence exists.
