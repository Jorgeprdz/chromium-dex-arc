"""Check real GN action selection and fail-closed delivery coverage."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


def loader():
    spec=importlib.util.spec_from_file_location('java_preflight',ROOT/'scripts/archium-java-preflight.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class JavaPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.checkout=Path(self.temp.name);self.out=self.checkout/'out/Archium';self.out.mkdir(parents=True)
        self.paths=['chrome/new/Arc.java','chrome/tests/VerticalTabsTest.java']
        self.graph={
            '//chrome:arc__compile_java': {'type':'action','script':'//build/android/gyp/compile_java.py','inputs':['//chrome/new/Arc.java'],'outputs':['//out/Archium/obj/chrome/arc.javac.jar']},
            '//chrome:tests__compile_java': {'type':'action','script':'//build/android/gyp/compile_java.py','inputs':['//chrome/tests/VerticalTabsTest.java'],'outputs':['//out/Archium/obj/chrome/tests.javac.jar']},
            '//chrome:arc__header': {'type':'action','script':'//build/android/gyp/turbine.py','inputs':['//chrome/new/Arc.java'],'outputs':['//out/Archium/obj/chrome/arc.turbine.jar']},
        }

    def test_selects_real_compile_actions_for_new_and_modified_test_sources(self):
        targets, coverage=loader().resolve(self.graph,self.paths,self.checkout,self.out)
        self.assertEqual(targets,['obj/chrome/arc.javac.jar','obj/chrome/tests.javac.jar'])
        self.assertEqual(set(coverage),set(self.paths))
        self.assertNotIn('obj/chrome/arc.turbine.jar',targets)

    def test_missing_owner_fails_instead_of_excluding_source(self):
        del self.graph['//chrome:tests__compile_java']
        with self.assertRaisesRegex(RuntimeError,'VerticalTabsTest.java'):
            loader().resolve(self.graph,self.paths,self.checkout,self.out)

    def test_header_only_coverage_is_insufficient(self):
        del self.graph['//chrome:arc__compile_java']
        with self.assertRaisesRegex(RuntimeError,'Arc.java'):
            loader().resolve(self.graph,self.paths,self.checkout,self.out)

    def test_compile_output_must_belong_to_requested_build_directory(self):
        self.graph['//chrome:arc__compile_java']['outputs']=['//out/Other/arc.jar']
        with self.assertRaisesRegex(RuntimeError,'outside'):
            loader().resolve(self.graph,self.paths,self.checkout,self.out)
