#!/usr/bin/env bash
# Cheap checks run before checkpoint download on the same Python line as Actions.
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"
python_bin="${ARCHIUM_REPOSITORY_PYTHON:-python3}"
if [[ -n "${JAVA_HOME_17_X64:-}" ]]; then
    export JAVA_HOME="$JAVA_HOME_17_X64"
    export PATH="$JAVA_HOME/bin:$PATH"
fi
"$python_bin" -c 'import sys; print(sys.version); assert sys.version_info[:2] == (3, 12), "Repository preflight requires Python 3.12, matching Ubuntu 24.04 Actions"'
java -version
git diff --check
for script in scripts/*.sh; do bash -n "$script"; done
"$python_bin" -m compileall -q scripts tests
ARCHIUM_TEST_GN=$("$python_bin" scripts/fetch-repository-gn.py \
    --cache-dir "$repo_root/.sync-audit/repository-tools")
export ARCHIUM_TEST_GN
"$ARCHIUM_TEST_GN" --version
"$python_bin" -m unittest discover -s tests -p 'test_*.py'
printf 'ARCHIUM_REPOSITORY_PREFLIGHT=PASS\n'
