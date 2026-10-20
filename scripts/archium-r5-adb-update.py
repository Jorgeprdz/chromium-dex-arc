#!/usr/bin/env python3
"""Authorized, single-attempt ADB update with installed-byte verification."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

PACKAGE='app.archium.android'
def command(args):
    return subprocess.check_output(args,text=True,stderr=subprocess.STDOUT,timeout=180)

def update(state,folder,run=command):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    cfg=state['adb_update'];apk=Path(state['apk_path']);digest=state['apk_sha256']
    if hashlib.sha256(apk.read_bytes()).hexdigest()!=digest:raise ValueError('APK bytes changed after verification')
    adb=['adb','-s',cfg['serial']]
    def result(status,**extra):
        value=dict(status=status,run_id=str(state['run_id']),source_sha=state['expected_sha'],apk_sha256=digest,package=PACKAGE,**extra)
        (folder/'adb-install-receipt.json').write_text(json.dumps(value,indent=2)+'\n');return value
    def cert(path):
        text=run([cfg['apksigner'],'verify','--print-certs',str(path)])
        values=re.findall(r'certificate SHA-256 digest: ([0-9a-f]{64})',text)
        if not values:raise ValueError('Certificate evidence absent')
        return values
    def version(path):
        text=run([cfg['aapt2'],'dump','badging',str(path)])
        match=re.search(r"package: name='app\.archium\.android' versionCode='(\d+)'",text)
        if not match:raise ValueError('Unexpected Android package')
        return int(match[1])
    def installed(name):
        paths=run(adb+['shell','pm','path',PACKAGE]).strip().splitlines()
        if len(paths)!=1 or not paths[0].startswith('package:/') or not paths[0].endswith('.apk'):raise ValueError('Installed package must be unambiguous and monolithic')
        p=folder/name;run(adb+['pull',paths[0][8:],str(p)]);return p
    try:
        if run(adb+['get-state']).strip()!='device':return result('INSTALL_PENDING_DEVICE')
        if run(adb+['shell','getprop','ro.serialno']).strip()!=cfg['hardware_serial']:return result('INSTALL_PENDING_DEVICE',reason='Device identity differs')
    except (OSError,subprocess.SubprocessError):return result('INSTALL_PENDING_DEVICE')
    expected_cert=cert(apk);expected_version=version(apk)
    before=installed('installed-before.apk');old_cert=cert(before);old_version=version(before)
    if old_cert!=expected_cert:return result('BLOCKED_SIGNATURE')
    if expected_version<old_version:return result('BLOCKED_VERSION')
    if hashlib.sha256(before.read_bytes()).hexdigest()!=digest:
        marker=folder/'adb-update-attempt.json'
        if marker.exists():return result('INSTALL_RESULT_UNCONFIRMED',reason='Previous attempt exists; automatic duplicate refused')
        # Durable intent before invoking PackageInstaller; never retry ambiguous updates.
        with marker.open('x') as f:
            json.dump(dict(run_id=state['run_id'],apk_sha256=digest,serial=cfg['serial']),f);f.flush();os.fsync(f.fileno())
        try:output=run(adb+['install','-r',str(apk)])
        except subprocess.CalledProcessError as error:
            output=error.output or ''
            (folder/'installer-output.txt').write_text(output)
            return result('USER_CONFIRMATION_REQUIRED' if 'USER_RESTRICTED' in output or 'ABORTED' in output else 'INSTALL_FAILED')
        except (OSError,subprocess.SubprocessError):return result('INSTALL_RESULT_UNCONFIRMED')
        (folder/'installer-output.txt').write_text(output)
        if 'Success' not in output.splitlines():return result('USER_CONFIRMATION_REQUIRED' if 'USER_RESTRICTED' in output or 'ABORTED' in output else 'INSTALL_FAILED')
    after=installed('installed-after.apk');system=run(adb+['shell','dumpsys','package',PACKAGE])
    (folder/'installed-package.txt').write_text(system)
    if (hashlib.sha256(after.read_bytes()).hexdigest()!=digest or cert(after)!=expected_cert
            or version(after)!=expected_version or not re.search(r'\bversionCode='+str(expected_version)+r'\b',system)):
        return result('INSTALL_VERIFICATION_FAILED')
    return result('INSTALL_SUCCESS',certificate_verified=True,version_verified=True,version_code=str(expected_version),
                  certificate_sha256=expected_cert,installed_apk_file=str(after),installed_apk_sha256=digest)
