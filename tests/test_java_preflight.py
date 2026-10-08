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

    def test_disabled_keystore_sources_are_not_required_in_generated_graph(self):
        prefix='chrome/browser/password_manager/android/java/src/org/chromium/chrome/browser/password_manager/'
        conditional=[prefix+'ArchiumPasswordKey.java',prefix+'ArchiumPasswordKeyBridge.java']
        targets,coverage=loader().resolve(self.graph,self.paths+conditional,self.checkout,self.out,
                                          local_passwords_enabled=False)
        self.assertEqual(set(coverage),set(self.paths))
        self.assertEqual(targets,['obj/chrome/arc.javac.jar','obj/chrome/tests.javac.jar'])

    def test_disabled_passwords_do_not_exempt_other_delivered_sources(self):
        prefix='chrome/browser/password_manager/android/java/src/org/chromium/chrome/browser/password_manager/'
        with self.assertRaisesRegex(RuntimeError,'ArchiumPasswordManagerBridge.java'):
            loader().resolve(self.graph,self.paths+[prefix+'ArchiumPasswordManagerBridge.java'],
                             self.checkout,self.out,local_passwords_enabled=False)

    def test_effective_password_flag_requires_one_explicit_boolean(self):
        module=loader()
        self.assertFalse(module.parse_local_passwords_enabled('enable_archium_local_passwords = false\n'))
        self.assertTrue(module.parse_local_passwords_enabled('enable_archium_local_passwords = true\n'))
        for body in ('','enable_archium_local_passwords = 0\n',
                     'enable_archium_local_passwords = false\nenable_archium_local_passwords = true\n'):
            with self.subTest(body=body):
                with self.assertRaises(RuntimeError):
                    module.parse_local_passwords_enabled(body)
