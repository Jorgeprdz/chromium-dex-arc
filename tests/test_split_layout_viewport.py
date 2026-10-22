"""Trace validator and native integration source contracts; not renderer acceptance."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('trace', ROOT/'scripts/check-split-viewport-trace.py')
trace = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trace)


class SplitLayoutViewportTests(unittest.TestCase):
    def row(self, width, root=None, narrow=None, **overrides):
        state = dict(width=width, rootWidth=width if root is None else root,
                     narrow=width <= 700 if narrow is None else narrow,
                     visual=width, scale=1, dpr=1, timeOrigin=123)
        state.update(overrides)
        return dict(stage=str(width), pages=[dict(id='test', state=dict(result=dict(result=dict(value=json.dumps(state)))))])

    def test_known_device_failure_is_rejected(self):
        problems = trace.errors([self.row(980), self.row(488, root=908, narrow=False), self.row(980)])
        self.assertEqual(len(problems), 2)

    def test_independent_reversible_widths_are_accepted(self):
        for widths in ([980, 488, 980], [488, 1460, 488]):
            self.assertEqual(trace.errors([self.row(w) for w in widths]), [])

    def test_document_reload_or_scale_change_is_rejected(self):
        self.assertTrue(trace.errors([self.row(980), self.row(488, timeOrigin=456)]))
        self.assertTrue(trace.errors([self.row(488, scale=2)]))

    def test_policy_is_scoped_and_preserves_mobile_viewport_preferences(self):
        path = ROOT/'.source-modified/chrome/browser/android/compositor/scene_layer/static_tab_scene_layer.cc'
        self.assertTrue(path.is_file(), 'Native split layout policy not implemented')
        source = path.read_text()
        self.assertIn('ApplyArcSplitViewportPreferences', source)
        self.assertIn('!prefs->viewport_meta_enabled', source)
        self.assertIn('prefs->viewport_enabled = false;', source)
        self.assertIn('OnWebPreferencesChanged()', source)
        for forbidden in ['SetUserAgent', 'SetPageScale', 'Reload(', 'default_minimum_page_scale_factor =']:
            self.assertNotIn(forbidden, source)

    def test_native_hook_survives_preference_recomputation_and_scene_cleanup(self):
        client = ROOT/'.source-modified/chrome/browser/chrome_content_browser_client.cc'
        self.assertTrue(client.is_file(), 'Browser preference hook not implemented')
        self.assertIn('android::ApplyArcSplitViewportPreferences(web_contents, web_prefs);', client.read_text())
        layer = (ROOT/'.source-modified/chrome/browser/android/compositor/scene_layer/static_tab_scene_layer.cc').read_text()
        self.assertIn('UpdateArcSplitViewportPolicy();', layer)
        self.assertIn('SetArcSplitViewportOwner(contents.get(), this, false)', layer)
        self.assertIn('SetArcSplitViewportOwner(contents.get(), this, true)', layer)
        header = (ROOT/'.source-modified/chrome/browser/android/compositor/scene_layer/static_tab_scene_layer.h').read_text()
        self.assertIn('base::WeakPtr<content::WebContents>', header)
