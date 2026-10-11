#!/usr/bin/env python3
"""Check the uploaded Actions artifact's real metadata against its build identity."""
import json
import os
from pathlib import Path
import sys


def validate(metadata, source_sha, artifact_id, digest):
    if (metadata.get('id') != int(artifact_id)
            or metadata.get('name') != 'Archium-for-Android-arm64'
            or metadata.get('expired') is not False
            or not isinstance(metadata.get('size_in_bytes'), int)
            or metadata['size_in_bytes'] <= 0
            or metadata.get('workflow_run', {}).get('head_sha') != source_sha
            or metadata.get('digest') != 'sha256:' + digest):
        raise ValueError('Uploaded artifact metadata differs from verified build')
    return metadata['size_in_bytes']


if __name__ == '__main__':
    size = validate(json.loads(Path(sys.argv[1]).read_text()), os.environ['GITHUB_SHA'],
                    os.environ['ARTIFACT_ID'], os.environ['ARTIFACT_DIGEST'])
    print('APK_ARTIFACT_METADATA=PASS bytes=' + str(size))
