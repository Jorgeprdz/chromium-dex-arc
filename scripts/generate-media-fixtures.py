#!/usr/bin/env python3
"""Generate tiny owned test patterns/tones; byte identity depends on FFmpeg version."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'tests/runtime/media/data')
    args = parser.parse_args(); out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    base = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i',
            'testsrc2=size=320x180:rate=24', '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000',
            '-t', '2', '-map_metadata', '-1']
    avc = ['-c:v', 'libx264', '-profile:v', 'baseline', '-level:v', '3.0', '-pix_fmt', 'yuv420p',
           '-preset', 'veryfast', '-g', '24', '-threads', '1', '-c:a', 'aac', '-b:a', '64k']
    subprocess.run(base + avc + ['-movflags', '+faststart', str(out / 'avc-aac.mp4')], check=True)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(out / 'avc-aac.mp4'),
                    '-vn', '-c:a', 'copy', str(out / 'aac.m4a')], check=True)
    for codec, name, extra in [('libvpx', 'vp8-opus.webm', ['-deadline', 'realtime', '-cpu-used', '8']),
                               ('libvpx-vp9', 'vp9-opus.webm', ['-deadline', 'realtime', '-cpu-used', '8']),
                               ('libaom-av1', 'av1-opus.webm', ['-cpu-used', '8'])]:
        subprocess.run(base + ['-c:v', codec, '-b:v', '200k', '-threads', '2', *extra,
                               '-c:a', 'libopus', '-b:a', '64k', str(out / name)], check=True)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(out / 'avc-aac.mp4'),
                    '-c', 'copy', '-movflags', 'frag_keyframe+empty_moov+default_base_moof',
                    '-frag_duration', '500000', str(out / 'avc-aac-fragmented.mp4')], check=True)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(out / 'avc-aac.mp4'),
                    '-c', 'copy', '-hls_time', '1', '-hls_list_size', '0',
                    '-hls_segment_filename', str(out / 'hls-%02d.ts'), str(out / 'playlist.m3u8')], check=True)
    rows = []
    for path in sorted(out.iterdir()):
        if path.suffix not in ('.mp4', '.m4a', '.webm', '.ts', '.m3u8'):
            continue
        streams = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
            'stream=codec_name,codec_type,profile,level:format=duration', '-of', 'json', str(path)], text=True))
        rows.append(dict(file=path.name, bytes=path.stat().st_size,
                         sha256=hashlib.sha256(path.read_bytes()).hexdigest(), probe=streams))
    (out / 'manifest.json').write_text(json.dumps(dict(content='Owned synthetic test pattern and 440Hz tone',
        ffmpeg=subprocess.check_output(['ffmpeg', '-version'], text=True).splitlines()[0], files=rows), indent=2) + '\n')
    print(f'Generated {len(rows)} verified fixture files, {sum(r["bytes"] for r in rows)} bytes')


if __name__ == '__main__':
    main()
