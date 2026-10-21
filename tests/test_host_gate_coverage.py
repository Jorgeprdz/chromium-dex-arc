"""Verify actual host orchestration includes all affected real Robolectric suites."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import contextlib
import io
import os
import shutil
import subprocess
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


class HostGateCoverageTests(unittest.TestCase):
    def test_restored_path_wrapper_cannot_replace_pinned_ninja_in_host_suite(self):
        spec=importlib.util.spec_from_file_location('host_gate',ROOT/'scripts/archium-test-gates.py')
        gates=importlib.util.module_from_spec(spec);spec.loader.exec_module(gates)
        ninja=os.environ.get('ARCHIUM_TEST_NINJA') or shutil.which('ninja')
        self.assertTrue(ninja,'Genuine Ninja required for host environment regression')
        with tempfile.TemporaryDirectory() as tmp:
            checkout=Path(tmp);out=checkout/'out/Archium';(out/'bin').mkdir(parents=True)
            jar=checkout/'android.jar';jar.write_bytes(b'SDK presence boundary')
            (out/'bin/run_chrome_junit_tests').write_text('runner boundary')
            gn=checkout/'buildtools/linux64/gn';gn.parent.mkdir(parents=True);gn.write_text('GN boundary');gn.chmod(0o755)
            pinned=checkout/'third_party/ninja/ninja';pinned.parent.mkdir(parents=True);pinned.symlink_to(Path(ninja).resolve())
            wrapper=checkout/'depot_tools/ninja';wrapper.parent.mkdir()
            # Reproduce the real launcher: it resolves python-bin beside argv[0].
            wrapper.write_text('#!/bin/sh\nexec "$(dirname "$0")/python-bin/python3" "$@"\n');wrapper.chmod(0o755)
            executions=[]
            def boundary(argv,**kwargs):
                if '-m' in argv and 'unittest' in argv:
                    # Only the two real Ninja/routing tests that failed in CI.
                    # Compilation/SDK/Robo boundaries remain mocked and earn no PASS.
                    env=dict(kwargs['env']);env.pop('ARCHIUM_TEST_NINJA',None)
                    env['PATH']=str(wrapper.parent)+':'+env['PATH']
                    if 'ARCHIUM_TEST_NINJA' in kwargs['env']:
                        env['ARCHIUM_TEST_NINJA']=kwargs['env']['ARCHIUM_TEST_NINJA']
                    result=subprocess.run([sys.executable,'-m','unittest',
                        'test_recovery_ninja_query.RecoveryNinjaQueryTests.test_siso_query_uses_pinned_binary_without_writing_incremental_state',
                        'test_recovery_ninja_query.RecoveryNinjaQueryTests.test_query_failure_stops_fanout_and_requests_quiescent_checkpoint'],
                        cwd=ROOT/'tests',env=env,capture_output=True,text=True,timeout=120)
                    executions.append(result)
            ambient=dict(os.environ);ambient.pop('ARCHIUM_TEST_NINJA',None)
            with patch.dict(os.environ,ambient,clear=True), patch.object(gates,'run',side_effect=boundary), \
                 patch.object(gates,'resolve_pinned_android_sdk',return_value=(checkout,'37.0','37.0.0',jar)), \
                 contextlib.redirect_stdout(io.StringIO()):
                gates.host_gate(jar,out)
            self.assertEqual(len(executions),1)
            self.assertEqual(executions[0].returncode,0,executions[0].stdout+executions[0].stderr)

    def test_host_runs_affected_native_group_binder_rail_toolbar_suites(self):
        spec=importlib.util.spec_from_file_location('host_gate',ROOT/'scripts/archium-test-gates.py')
        gates=importlib.util.module_from_spec(spec);spec.loader.exec_module(gates)
        with tempfile.TemporaryDirectory() as tmp:
            checkout=Path(tmp);out=checkout/'out/Archium';(out/'bin').mkdir(parents=True)
            jar=checkout/'android.jar';jar.write_bytes(b'synthetic SDK presence fixture')
            runner=out/'bin/run_chrome_junit_tests';runner.write_text('synthetic runner boundary')
            gn=checkout/'buildtools/linux64/gn';gn.parent.mkdir(parents=True);gn.write_text('routing boundary');gn.chmod(0o755)
            ninja=checkout/'third_party/ninja/ninja';ninja.parent.mkdir(parents=True);ninja.write_text('Ninja boundary');ninja.chmod(0o755)
            calls=[]
            with patch.object(gates,'run',side_effect=lambda args,**kw:calls.append(args)), \
                 patch.object(gates,'resolve_pinned_android_sdk',return_value=(checkout,'37.0','37.0.0',jar)), \
                 contextlib.redirect_stdout(io.StringIO()):
                gates.host_gate(jar,out)
        filters=[args[args.index('-f')+1] for args in calls if args[0]==str(runner)]
        self.assertEqual(set(filters),{
            "org.chromium.chrome.browser.arc.ArcAboutDialogTest.*",
            "org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearanceTest.*",
            "org.chromium.chrome.browser.arc.ArcColorPickerTest.*",
            "org.chromium.chrome.browser.arc.ArcFrameDispatchTest.*",
            "org.chromium.chrome.browser.arc.ArcNavigationControlsTest.*",
            "org.chromium.chrome.browser.arc.ArcCommandBarTest.*",
            "org.chromium.chrome.browser.arc.ArcSplitStateTest.*",
            "org.chromium.chrome.browser.arc.ArcSplitViewportPolicyTest.*",
            "org.chromium.chrome.browser.arc.ArcSplitContentHostTest.*",
            "org.chromium.chrome.browser.arc.ArcSplitControlsTest.*",
            "org.chromium.chrome.browser.arc.ArcSplitViewCoordinatorTest.*",
            "org.chromium.chrome.browser.arc.ArcOmniboxPlacementTest.*",
            "org.chromium.chrome.browser.arc.ArcCollectionsFocusTest.*",
            "org.chromium.chrome.browser.arc.ArcMobileControlsTest.*",
            "org.chromium.chrome.browser.arc.ArcCompactOmniboxTest.*",
            "org.chromium.chrome.browser.toolbar.top.ArcToolbarReparentingTest.*",
            "org.chromium.chrome.browser.omnibox.OmniboxSuggestionsDropdownEmbedderImplUnitTest.*",
            "org.chromium.chrome.browser.omnibox.LocationBarTabletUnitTest.*",
            "org.chromium.chrome.browser.omnibox.LocationBarMediatorUnitTest.testArc*",
            "org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.ArcTabSelectionTest.*",
            "org.chromium.chrome.browser.tabbed_mode.TabbedRootUiCoordinatorUnitTest.*",

            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabListCoordinatorUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.TabVerticalViewBinderUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabRailLayoutUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.NestedLayoutDelegateUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.TabListMediatorUnitTest.*',
            'org.chromium.chrome.browser.toolbar.top.ToolbarTabletUnitTest.*',
        })
