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
    if not GN:
        raise RuntimeError('Real GN is required; set ARCHIUM_TEST_GN to the pinned executable')
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
        command = [str(GN), 'gen', 'out']
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=120)
        if result.returncode:
            version = subprocess.run([str(GN), '--version'], capture_output=True,
                                     text=True, timeout=30, check=False)
            diag_dir = os.environ.get('ARCHIUM_GN_DIAGNOSTICS_DIR')
            bundle = None
            if diag_dir:
                Path(diag_dir).mkdir(parents=True, exist_ok=True)
                bundle = Path(tempfile.mkdtemp(prefix='media-gn-failure-', dir=diag_dir))
                shutil.copytree(root, bundle / 'fixture')
            raise RuntimeError(
                f'GN_MEDIA_FIXTURE_FAILED code={result.returncode} '
                f'command={command!r} cwd={root} gn_version={version.stdout.strip()} '
                f'diagnostic_bundle={bundle}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}')
        values = subprocess.run([str(GN), 'args', 'out', '--list', '--short'],
                                cwd=root, capture_output=True, text=True, timeout=120)
        if values.returncode:
            raise RuntimeError(f'GN args failed code={values.returncode}\n'
                               f'stdout:\n{values.stdout}\nstderr:\n{values.stderr}')
        return values.stdout
