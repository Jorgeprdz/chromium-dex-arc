"""Run ownership guards with files only, as CI cannot rely on ancestor Git objects."""
import pathlib, shutil, subprocess, sys, tempfile, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]

class MobilePremiumShallowCheckoutTest(unittest.TestCase):
    def run_guards(self, mutate=False):
        files = [
            'tests/test_mobile_premium_contract.py', 'tests/arc_toolbar_probe.py',
            'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcPhonePullReveal.java',
            'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcCameraControls.java',
            'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcPhoneStatusFade.java',
            'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcPhoneGlass.java',
            '.source-modified/chrome/android/java/src/org/chromium/chrome/browser/SwipeRefreshHandler.java',
            '.source-modified/chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/top/ToolbarPhone.java',
            '.source-modified/chrome/browser/ui/android/theme/java/src/org/chromium/chrome/browser/theme/ToolbarThemeColorProvider.java',
            '.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java',
            '.source-modified/chrome/android/java/src/org/chromium/chrome/browser/ChromeTabbedActivity.java',
        ]
        with tempfile.TemporaryDirectory(prefix='archium-no-history-') as directory:
            target = pathlib.Path(directory)
            for name in files:
                output = target / name
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, output)
            fixtures = ROOT / 'tests/pinned/mobile-premium-baseline.json'
            if fixtures.exists():
                output = target / 'tests/pinned/mobile-premium-baseline.json'
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(fixtures, output)
            if mutate:
                protected = target / 'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcPhonePullReveal.java'
                protected.write_bytes(protected.read_bytes() + b'\n// changed protected owner\n')
            result = subprocess.run(
                [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests',
                 '-p', 'test_mobile_premium_contract.py'],
                cwd=target, text=True, capture_output=True)
            return result

    def test_ownership_guards_without_git_history(self):
        result = self.run_guards()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_changed_pull_owner_still_fails_without_git_history(self):
        result = self.run_guards(mutate=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn('test_approved_pull_and_native_owners_are_byte_identical', result.stderr)
        self.assertIn('FAIL:', result.stderr)
