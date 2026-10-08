"""Verify actual host orchestration includes all affected real Robolectric suites."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


class HostGateCoverageTests(unittest.TestCase):
    def test_host_suites_execute_java_assertions_and_preserve_existing_options(self):
        """Catch launching assertion-dependent suites with official-build JVM defaults."""
        spec=importlib.util.spec_from_file_location('host_assertions',ROOT/'scripts/archium-test-gates.py')
        gates=importlib.util.module_from_spec(spec);spec.loader.exec_module(gates)
        java=shutil.which('java');javac=shutil.which('javac')
        self.assertIsNotNone(java, 'Real JVM required for the host assertion regression')
        self.assertIsNotNone(javac, 'Real Java compiler required for the host assertion regression')
        with tempfile.TemporaryDirectory() as tmp:
            checkout=Path(tmp);out=checkout/'out/Archium';(out/'bin').mkdir(parents=True)
            jar=checkout/'android.jar';jar.write_bytes(b'SDK presence boundary; not compiled')
            binary=checkout/'buildtools/linux64/gn';binary.parent.mkdir(parents=True)
            binary.write_bytes(b'\x7fELFnative tool presence boundary; not executed');binary.chmod(0o755)
            # Repository preparation is a separate tested boundary. Keep all actual
            # host subprocess calls and the JVM assertion behavior real in this fixture.
            (checkout/'scripts').mkdir();(checkout/'tests').mkdir()
            (checkout/'scripts/check-arc-preparation.py').write_text('pass\n')
            # Python 3.12 returns exit 5 for an empty discovered suite. Exercise
            # this subprocess boundary with a real test, as the production gate does.
            repository_record=checkout/'repository-suite-ran.txt'
            (checkout/'tests/test_repository_boundary.py').write_text(
                'import unittest\nfrom pathlib import Path\n'
                'class RepositoryBoundaryTest(unittest.TestCase):\n'
                '    def test_checkout_contains_preparation_script(self):\n'
                f'        self.assertTrue(Path({str(checkout / "scripts/check-arc-preparation.py")!r}).is_file())\n'
                f'        Path({str(repository_record)!r}).write_text("executed")\n')
            source=checkout/'AssertionGateProbe.java'
            source.write_text('''public class AssertionGateProbe {
    public static void main(String[] args) {
        if (!"kept".equals(System.getProperty("archium.gate.marker"))) {
            throw new IllegalStateException("Existing JVM options lost");
        }
        try {
            assert false : "Non-flat layout requires AssertionError";
        } catch (AssertionError expected) {
            System.out.println("ASSERTION_CAUGHT " + args[0]);
            return;
        }
        throw new IllegalStateException("Expected exception: java.lang.AssertionError");
    }
}
''')
            subprocess.run([javac,str(source)],check=True,capture_output=True,text=True)
            record=checkout/'executed-suites.txt'
            runner=out/'bin/run_chrome_junit_tests'
            runner.write_text(f'#!{sys.executable}\n'+
                'import subprocess,sys\nfrom pathlib import Path\n'+
                f'command={[java,"-cp",str(checkout),"AssertionGateProbe"]!r}\n'+
                'result=subprocess.run(command+[sys.argv[2]],capture_output=True,text=True)\n'+
                'print(result.stdout+result.stderr,end="")\n'+
                'if result.returncode:sys.exit(result.returncode)\n'+
                f'with Path({str(record)!r}).open("a") as log:log.write(result.stdout)\n')
            runner.chmod(0o755)
            with patch.object(gates,'ROOT',checkout),patch.dict(
                    os.environ,{'JAVA_TOOL_OPTIONS':'-Darchium.gate.marker=kept -da'}):
                gates.host_gate(jar,out)
                self.assertEqual(os.environ['JAVA_TOOL_OPTIONS'],'-Darchium.gate.marker=kept -da')
            self.assertEqual(repository_record.read_text(),'executed')
            executed=record.read_text().splitlines()
            self.assertEqual(len(executed),6)
            self.assertTrue(all(line.startswith('ASSERTION_CAUGHT ') for line in executed))

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
