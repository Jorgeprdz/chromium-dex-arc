#!/usr/bin/env bash
# R3.1 guarded one-shot workflow_dispatch bridge. Never pushes a marker.
set -euo pipefail

repo="Jorgeprdz/chromium-dex-arc"
branch="assistant/archium-r3-visual-fixes"
workflow="baseline-build.yml"

if [[ "${GITHUB_REPOSITORY:-}" != "$repo" ||
      "${GITHUB_REF_NAME:-}" != "$branch" ||
      "${GITHUB_EVENT_NAME:-}" != push ||
      ! "${GITHUB_SHA:-}" =~ ^[0-9a-f]{40}$ ]]; then
    echo "Refusing dispatch outside the authorized repository, push, branch, and commit." >&2
    exit 2
fi
if [[ -z "${GH_TOKEN:-}" ]]; then
    echo "Missing GitHub Actions token." >&2
    exit 2
fi
remote="$(gh api "repos/$repo/branches/$branch" --jq '.commit.sha')"
if [[ "$remote" != "$GITHUB_SHA" ]]; then
    echo "Remote HEAD changed; refusing to dispatch a stale commit." >&2
    exit 2
fi
# An existing build, even queued, must be examined, not duplicated or cancelled.
runs="$(gh api "repos/$repo/actions/runs?per_page=100")"
busy="$(jq -r '
    [.workflow_runs[]
      | select((.status == "queued" or .status == "in_progress" or .status == "waiting"
                or .status == "requested" or .status == "pending")
               and (.name == "Archium for Android build in resumable stages"))] | length
' <<< "$runs")"
if [[ "$busy" != 0 ]]; then
    echo "A resumable Archium compilation is already active; no duplicate dispatched." >&2
    exit 3
fi
old_runs="$(gh api "repos/$repo/actions/workflows/$workflow/runs?per_page=100")"
existing="$(jq -r --arg sha "$GITHUB_SHA" --arg branch "$branch" '
    [.workflow_runs[]
     | select(.head_sha == $sha and .head_branch == $branch and .event == "workflow_dispatch")] | length
' <<< "$old_runs")"
if [[ "$existing" != 0 ]]; then
    echo "Build already exists for this exact commit; refusing duplicate dispatch." >&2
    exit 3
fi
# Gate checked by the preceding preflight job. This deliberately avoids an
# unverified checkpoint and dispatches one clean build with empty default inputs.
echo "Dispatching clean baseline build on $branch at $GITHUB_SHA."
gh workflow run "$workflow" --repo "$repo" --ref "$branch"

# GitHub can register a new workflow run asynchronously; read-only retries are safe.
id=""
for _ in $(seq 1 12); do
    response="$(gh api "repos/$repo/actions/workflows/$workflow/runs?per_page=100")"
    id="$(jq -r --arg sha "$GITHUB_SHA" --arg branch "$branch" '
        [.workflow_runs[]
         | select(.head_sha == $sha and .head_branch == $branch and .event == "workflow_dispatch")
         | .id] | first // empty
    ' <<< "$response")"
    [[ -n "$id" ]] && break
    sleep 5
done
if [[ -z "$id" ]]; then
    echo "Dispatch submitted, but run ID not visible. NEVER auto-dispatch again." >&2
    exit 4
fi
details="$(gh api "repos/$repo/actions/runs/$id")"
printf '%s\n' "$details" | jq -e --arg sha "$GITHUB_SHA" --arg branch "$branch" '
    .head_sha == $sha
    and .head_branch == $branch
    and .name == "Archium for Android build in resumable stages"
    and .event == "workflow_dispatch"
' >/dev/null || { echo "Unexpected run identity; no repeat dispatch." >&2; exit 5; }
status="$(jq -r '.status' <<< "$details")"
url="$(jq -r '.html_url' <<< "$details")"
echo "ARCHIUM_R3_1_RUN_ID=$id"
echo "ARCHIUM_R3_1_HEAD_SHA=$GITHUB_SHA"
echo "ARCHIUM_R3_1_RUN_URL=$url"
echo "ARCHIUM_R3_1_INITIAL_STATUS=$status"
# This job terminates after verification; no persistent 900s monitor is claimed.
