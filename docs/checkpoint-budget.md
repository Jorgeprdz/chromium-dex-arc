# Archium staged build budgets

GitHub's six-hour job limit is the final limit, not the trigger for saving work.
The existing twelve-stage workflow keeps its mandatory compile and execution gates.

| Operation | Limit |
| --- | --- |
| Preparation: restore, dependencies, transition, hooks and GN | 60 minutes total |
| Compilation slice | 120 minutes |
| Host execution gate | 30 minutes total |
| Work deadline, including preparation and time between job steps | 4 hours |
| Checkpoint compression, upload and verification | 90 minutes |
| Successful APK artifact upload | 30 minutes |

Preparation and work are separate Actions steps so the monitor's metadata fallback
can show preparation accurately. Work requires a preparation marker for this job
and implementation SHA. The marker carries the original start time; splitting
the steps does not restart the work budget. Budget overrides may only shorten
the maximums. Shutdown grace periods fit inside the remaining job margin.

Preparation failures preserve the selected source checkpoint. A partially
restored or transitioned workspace is never published under the new commit.

After preparation, a compilation or global work timeout interrupts the backend
and waits for it to exit before packing the workspace. The pinned autoninja
interpreter runs through a thin loader with a callable SIGINT handler: Python
wrappers must not raise KeyboardInterrupt and kill their backend during flushing.
Native Ninja/Siso still handle the group interrupt. Forced SIGKILL is a failure
and cannot claim a verified, quiescent checkpoint.

A host gate timeout can preserve compiled work, but the job still fails. It does
not approve tests or permit APK compilation. Every continuation executes the
mandatory gates again. Ordinary compile/test failures also remain failures.

Checkpoint parts are uploaded first. GitHub must report every part as uploaded
with the correct size and SHA256 before `checkpoint.json` is published. The
small manifest is downloaded and compared after upload. Only then may the
stage output `complete=false`; APK success alone outputs `complete=true`.
Failed packing/upload/verification produces no resumable-success output.

This change affects future workflow dispatches. A running workflow retains its
original commit and configuration. No extra run is launched while one is active.
