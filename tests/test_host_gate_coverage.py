"""Verify actual host orchestration includes all affected real Robolectric suites."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import contextlib
import io
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


class HostGateCoverageTests(unittest.TestCase):
    def test_host_runs_affected_native_group_binder_rail_toolbar_suites(self):
        spec=importlib.util.spec_from_file_location('host_gate',ROOT/'scripts/archium-test-gates.py')
        gates=importlib.util.module_from_spec(spec);spec.loader.exec_module(gates)
        with tempfile.TemporaryDirectory() as tmp:
            checkout=Path(tmp);out=checkout/'out/Archium';(out/'bin').mkdir(parents=True)
            jar=checkout/'android.jar';jar.write_bytes(b'synthetic SDK presence fixture')
            runner=out/'bin/run_chrome_junit_tests';runner.write_text('synthetic runner boundary')
            gn=checkout/'buildtools/linux64/gn';gn.parent.mkdir(parents=True);gn.write_text('routing boundary');gn.chmod(0o755)
            calls=[]
            with patch.object(gates,'run',side_effect=lambda args,**kw:calls.append(args)), \
                 patch.object(gates,'resolve_pinned_android_sdk',return_value=(checkout,'37.0','37.0.0',jar)), \
                 contextlib.redirect_stdout(io.StringIO()):
                gates.host_gate(jar,out)
        filters=[args[args.index('-f')+1] for args in calls if args[0]==str(runner)]
        self.assertEqual(set(filters),{
            "org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearanceTest.*",
            "org.chromium.chrome.browser.arc.ArcColorPickerTest.*",
            "org.chromium.chrome.browser.arc.ArcFrameDispatchTest.*",
            "org.chromium.chrome.browser.arc.ArcNavigationControlsTest.*",
            "org.chromium.chrome.browser.arc.ArcCollectionsFocusTest.*",

            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabListCoordinatorUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.TabVerticalViewBinderUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabRailLayoutUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.NestedLayoutDelegateUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.TabListMediatorUnitTest.*',
            'org.chromium.chrome.browser.toolbar.top.ToolbarTabletUnitTest.*',
        })
