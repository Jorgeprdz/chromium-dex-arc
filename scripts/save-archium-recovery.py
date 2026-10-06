#!/usr/bin/env python3
"""Save prepared code and recovery documents to an explicitly selected Android device.

This does not read account quota or user passwords. Refresh the recovery document
before calling it; the generated snapshot records current HEAD and uncommitted paths.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(*args, capture=False):
    return subprocess.check_output(list(map(str, args)), cwd=ROOT, text=True) if capture else subprocess.run(
        list(map(str, args)), cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', required=True)
    args = parser.parse_args()
    prompt = ROOT / 'docs/Archium-PROMPT-RECUPERACION.md'
    if not prompt.is_file():
        raise SystemExit('Missing recovery prompt; write the actual state first')
    branch = run('git', 'branch', '--show-current', capture=True).strip()
    if not branch:
        raise SystemExit('Recovery bundle needs the active branch')
    snapshot = {
        'head': run('git', 'rev-parse', 'HEAD', capture=True).strip(),
        'branch': branch,
        'status': run('git', 'status', '--short', capture=True),
        'patch_sha256': hashlib.sha256((ROOT / 'patches/archium-desktop.patch').read_bytes()).hexdigest(),
        'native_build_completed': False,
        'note': 'Tar captures preparation directories including WIP; bundle records committed history. No quota counter.',
    }
    destination = ROOT / '.sync-audit/recovery'
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination) as temporary:
        temporary = Path(temporary)
        bundle = temporary / 'Archium-codigo.bundle'
        archive_path = temporary / 'Archium-preparacion.tar.gz'
        run('git', 'bundle', 'create', bundle, branch)
        run('git', 'bundle', 'verify', bundle)
        with tarfile.open(archive_path, 'w:gz') as archive:
            for name in ('.source-reference', '.source-modified', 'chromium', 'patches',
                         'docs', 'config', 'scripts', 'tests', '.github'):
                for file in sorted((ROOT / name).rglob('*')):
                    if file.is_file() and '__pycache__' not in file.parts:
                        archive.add(file, arcname=file.relative_to(ROOT).as_posix(), recursive=False)
            for file in sorted((ROOT / '.superpowers/sdd').rglob('*.md')):
                archive.add(file, arcname=file.relative_to(ROOT).as_posix(), recursive=False)
        bundle.replace(destination / bundle.name)
        archive_path.replace(destination / archive_path.name)
    snapshot_file = destination / 'Archium-respaldo-estado.json'
    snapshot_file.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n')
    phone_folder = '/sdcard/Download/Archium-documentos'
    run('adb', '-s', args.device, 'shell', 'mkdir', '-p', phone_folder)
    files = {
        prompt: '/sdcard/Download/Archium-PROMPT-RECUPERACION.txt',
        ROOT / 'docs/archium-current-handoff.md': phone_folder + '/Estado-implementacion-Archium.md',
        ROOT / 'docs/validation/local-passwords-results.md': phone_folder + '/Resultados-parciales-contraseñas.md',
        destination / 'Archium-codigo.bundle': phone_folder + '/Archium-codigo.bundle',
        destination / 'Archium-preparacion.tar.gz': phone_folder + '/Archium-preparacion.tar.gz',
        snapshot_file: phone_folder + '/' + snapshot_file.name,
    }
    for source, target in files.items():
        run('adb', '-s', args.device, 'push', source, target)
        expected = hashlib.sha256(source.read_bytes()).hexdigest()
        actual = run('adb', '-s', args.device, 'shell', 'sha256sum', target, capture=True).split()[0]
        if actual != expected:
            raise SystemExit('Recovery copy hash mismatch: ' + target)
    print('Recovery prompt, code bundle, preparation archive and state copied; all device hashes matched.')


if __name__ == '__main__':
    main()
