"""Execute pinned media GNI under a small synthetic Android context, with real GN."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/media-gn'
GN = os.environ.get('ARCHIUM_TEST_GN') or shutil.which('gn')

def evaluate(args_text):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        shutil.copytree(FIXTURES, root, dirs_exist_ok=True)
        shutil.copyfile(root / 'BUILDCONFIG.synthetic.gn', root / 'BUILDCONFIG.gn')
        (root / '.gn').write_text('buildconfig = "//BUILDCONFIG.gn"\n')
        for name in ['build/config/arm.gni', 'build/config/cast.gni',
                     'build/config/chrome_build.gni', 'build/config/chromeos/args.gni',
                     'build/config/ui.gni', 'media/gpu/args.gni',
                     'testing/libfuzzer/fuzzer_test.gni', 'third_party/libaom/options.gni',
                     'build/config/sanitizers/sanitizers.gni']:
            p = root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('# Synthetic non-media platform context.\n')
        (root / 'BUILD.gn').write_text('''import("//media/media_options.gni")
import("//third_party/ffmpeg/ffmpeg_options.gni")
import("//third_party/widevine/cdm/widevine.gni")
toolchain("default") { tool("stamp") { command = "touch {{output}}" } }
group("all") { }
''')
        (root / 'out').mkdir()
        (root / 'out/args.gn').write_text(args_text)
        subprocess.run([GN, 'gen', 'out'], cwd=root, capture_output=True, text=True, check=True)
        return subprocess.check_output([GN, 'args', 'out', '--list', '--short'], cwd=root, text=True)
