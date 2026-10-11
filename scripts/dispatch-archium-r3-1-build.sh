#!/usr/bin/env bash
# Retired R3.1 push bridge. R4 dispatches require explicit SHA/checkpoint inputs.
set -euo pipefail
printf 'The R3.1 push dispatcher is retired; no GitHub call or build was made.\n' >&2
printf 'Use baseline-build.yml workflow_dispatch with expected_sha and exact checkpoint source inputs after authorization.\n' >&2
exit 2
