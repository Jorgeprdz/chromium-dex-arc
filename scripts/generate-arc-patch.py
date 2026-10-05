#!/usr/bin/env python3
"""Generate the reviewable diff from pinned originals, modified files and new native sources."""
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'cfd94726b7b5fb48aedcc32662f2f3fbdbadec35'


def main():
    modified = ROOT / '.source-modified'
    original = ROOT / '.source-reference'
    new_sources = ROOT / 'chromium'
    originals = {}
    new_hashes = {}
    chunks = []
    for base in (modified, new_sources):
        for file in sorted(base.rglob('*')):
            if not file.is_file():
                continue
            name = file.relative_to(base).as_posix()
            before = (original / name).read_bytes() if base == modified else b''
            after = file.read_bytes()
            if before == after:
                continue
            if name in originals:
                raise ValueError('duplicate modified/new path: ' + name)
            originals[name] = hashlib.sha256(before).hexdigest() if base == modified else None
            new_hashes[name] = hashlib.sha256(after).hexdigest()
            chunks.append('diff --git a/' + name + ' b/' + name + '\n')
            if base == new_sources:
                chunks.append('new file mode 100644\n')
            chunks.extend(difflib.unified_diff(before.decode().splitlines(True),
                after.decode().splitlines(True),
                fromfile='a/' + name if base == modified else '/dev/null', tofile='b/' + name))
    if not originals:
        raise ValueError('no source changes found')
    patch = ''.join(chunks)
    (ROOT / 'patches').mkdir(exist_ok=True)
    (ROOT / 'patches/archium-desktop.patch').write_text(patch)
    manifest = {'revision': REVISION, 'originals': originals, 'modified': new_hashes,
                'patch_sha256': hashlib.sha256(patch.encode()).hexdigest()}
    (ROOT / 'patches/upstream-files.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Generated Archium patch:', len(originals), 'files')


if __name__ == '__main__':
    main()
