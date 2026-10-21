"""Verified update boundary: system evidence, no destructive installer actions."""
import importlib.util
from pathlib import Path
import hashlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'scripts/archium-r5-adb-update.py'
spec=importlib.util.spec_from_file_location('adb_update',p)
m=importlib.util.module_from_spec(spec)
if p.exists():spec.loader.exec_module(m)
class AdbUpdateTests(unittest.TestCase):
    def scenario(self,*,cert='a'*64,version=10,connected=True,installed=False,post_good=True,ambiguous=False,confirm=False):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name);apk=root/'new.apk';apk.write_bytes(b'new');calls=[];did=[installed]
        state=dict(run_id='123',expected_sha='b'*40,apk_sha256=hashlib.sha256(b'new').hexdigest(),apk_path=str(apk),adb_update=dict(serial='phone',hardware_serial='hardware',apksigner='signer',aapt2='aapt2'))
        def run(args):
            calls.append(args)
            if args[0]=='signer':return 'Signer #1 certificate SHA-256 digest: '+('a'*64 if args[-1]==str(apk) or did[0] else cert)
            if args[0]=='aapt2':return "package: name='app.archium.android' versionCode='"+str(11 if args[-1]==str(apk) or did[0] else version)+"'\nnative-code: 'arm64-v8a'"
            command=args[4:]
            if args[-1]=='get-state':return 'device' if connected else 'unauthorized'
            if command==['getprop','ro.serialno']:return 'hardware'
            if command==['pm','path','app.archium.android']:return 'package:/data/app/base.apk'
            if command[:2]==['dumpsys','package']:return 'versionCode=11' if did[0] else 'versionCode='+str(version)
            if args[3]=='pull':Path(args[5]).write_bytes(b'new' if did[0] and post_good else b'old');return 'pulled'
            if args[3]=='install':
                if confirm:raise subprocess.CalledProcessError(1,args,output='Failure [INSTALL_FAILED_USER_RESTRICTED]')
                did[0]=True;return 'Success'
            raise AssertionError(args)
        if ambiguous:(root/'adb-update-attempt.json').write_text('{}')
        result=m.update(state,root,run=run)
        return result,calls,root
    def test_verified_system_bytes_required_for_success(self):
        result,calls,root=self.scenario();self.assertEqual(result['status'],'INSTALL_SUCCESS');self.assertTrue((root/'adb-install-receipt.json').exists());self.assertEqual([a[4] for a in calls if len(a)>3 and a[3]=='install'],['-r'])
    def test_incompatible_certificate_blocks_before_install(self):
        result,calls,_=self.scenario(cert='c'*64);self.assertEqual(result['status'],'BLOCKED_SIGNATURE');self.assertFalse(any('install' in a for a in calls))
    def test_downgrade_blocks(self):
        result,calls,_=self.scenario(version=12);self.assertEqual(result['status'],'BLOCKED_VERSION');self.assertFalse(any('install' in a for a in calls))
    def test_no_authorized_device_is_pending(self):
        result,calls,_=self.scenario(connected=False);self.assertEqual(result['status'],'INSTALL_PENDING_DEVICE');self.assertFalse(any('install' in a for a in calls))
    def test_installer_success_without_matching_system_bytes_is_not_success(self):
        result,_,_=self.scenario(post_good=False);self.assertEqual(result['status'],'INSTALL_VERIFICATION_FAILED')
    def test_already_installed_exact_bytes_never_reinstalls(self):
        result,calls,_=self.scenario(installed=True);self.assertEqual(result['status'],'INSTALL_SUCCESS');self.assertFalse(any('install' in a for a in calls))
    def test_ambiguous_previous_attempt_never_repeats_install(self):
        result,calls,_=self.scenario(ambiguous=True);self.assertEqual(result['status'],'INSTALL_RESULT_UNCONFIRMED');self.assertFalse(any('install' in a for a in calls))

    def test_android_confirmation_is_preserved_without_retry(self):
        result,calls,_=self.scenario(confirm=True);self.assertEqual(result['status'],'USER_CONFIRMATION_REQUIRED');self.assertEqual(sum('install' in a for a in calls),1)
