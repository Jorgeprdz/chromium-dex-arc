"""Verify actual host orchestration includes all affected real Robolectric suites."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
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
            binary=checkout/'buildtools/linux64/gn';binary.parent.mkdir(parents=True)
            binary.write_bytes(b'\x7fELFbinary presence fixture, never executed');binary.chmod(0o755)
            calls=[]
            with patch.object(gates,'run',side_effect=lambda args,**kw:calls.append((args,kw))):
                gates.host_gate(jar,out)
        filters=[args[args.index('-f')+1] for args,kw in calls if args[0]==str(runner)]
        suite=next(kw for args,kw in calls if '-m' in args and 'unittest' in args)
        self.assertEqual(suite.get('env',{}).get('ARCHIUM_TEST_GN'),str(binary.resolve()))
        self.assertEqual(set(filters),{
            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabListCoordinatorUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.TabVerticalViewBinderUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabRailLayoutUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.NestedLayoutDelegateUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.TabListMediatorUnitTest.*',
            'org.chromium.chrome.browser.toolbar.top.ToolbarTabletUnitTest.*',
        })

    def test_host_gn_resolver_rejects_wrapper_and_accepts_pinned_native_binary(self):
        spec=importlib.util.spec_from_file_location('host_gn',ROOT/'scripts/archium-test-gates.py')
        gates=importlib.util.module_from_spec(spec);spec.loader.exec_module(gates)
        with tempfile.TemporaryDirectory() as tmp:
            checkout=Path(tmp);out=checkout/'out/Archium';out.mkdir(parents=True)
            binary=checkout/'buildtools/linux64/gn';binary.parent.mkdir(parents=True)
            binary.write_text('#!/bin/sh\nexit 2\n');binary.chmod(0o755)
            with self.assertRaises(SystemExit):gates.pinned_gn_binary(out)
            binary.write_bytes(b'\x7fELFnative binary presence fixture')
            self.assertEqual(gates.pinned_gn_binary(out),binary.resolve())
            primary=checkout/'third_party/gn/gn';primary.parent.mkdir(parents=True)
            primary.write_bytes(b'\x7fELFprimary binary presence fixture');primary.chmod(0o755)
            self.assertEqual(gates.pinned_gn_binary(out),primary.resolve())
