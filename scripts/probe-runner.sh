#!/usr/bin/env bash
set -euo pipefail

# Read-only inventory: never deletes tools, changes mounts, or downloads Chromium.
printf 'Architecture: '
uname -m
printf '\nMemory (MiB):\n'
free -m
printf '\nAvailable storage (bytes):\n'
df -B1 / "${GITHUB_WORKSPACE:-.}" /mnt
printf '\nBlock devices:\n'
lsblk -b -o NAME,SIZE,TYPE,MOUNTPOINTS
printf '\nExisting toolchain storage (bytes):\n'
for tool_dir in /usr/share/dotnet /usr/local/lib/android /opt/hostedtoolcache /opt/ghc; do
    if [[ -d "$tool_dir" ]]; then
        du -sx -B1 "$tool_dir"
    fi
done

printf '\nChromium documented baseline: x86_64 Linux, >=8 GiB RAM, >=100 GB free disk.\n'
printf 'Inventory alone does not demonstrate build feasibility or completion time.\n'
