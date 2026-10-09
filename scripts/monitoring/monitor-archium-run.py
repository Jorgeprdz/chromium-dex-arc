#!/usr/bin/env python3
"""Read-only GitHub run monitor, refreshed every ten minutes."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import textwrap
import re
import sys
import urllib.request

REPO = 'Jorgeprdz/chromium-dex-arc'
RUN = '37871846597'


def get_json(path):
    if shutil.which('gh'):
        result = subprocess.run(['gh', 'api', path], text=True, capture_output=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
    request = urllib.request.Request('https://api.github.com/' + path,
        headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'Archium-run-monitor'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def describe(run, jobs, now):
    start = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
    elapsed = max(0, int((now - start).total_seconds()))
    active = [job for job in jobs if job['status'] == 'in_progress']
    finished = [job for job in jobs if job['status'] == 'completed']
    lines = [f"Run {run['id']}: {run['status']} {run.get('conclusion') or ''}".strip(),
             f'Tiempo transcurrido: {elapsed // 3600} h {(elapsed % 3600) // 60} min']
    events = []
    for job in jobs:
        events.append(f"{job['name']}: {job['status']} {job.get('conclusion') or ''}".strip())
        for step in job.get('steps', []):
            if step['status'] in ('in_progress', 'completed'):
                events.append(f"{job['name']} / {step['name']}: {step['status']} {step.get('conclusion') or ''}".strip())
    if active:
        for job in active:
            lines.append('Etapa actual: ' + job['name'])
            for step in job.get('steps', []):
                if step['status'] == 'in_progress':
                    lines.append('Paso: ' + step['name'])
    elif run['status'] != 'completed':
        lines.append('Esperando runner o siguiente etapa.')
    lines += [f'Jobs terminados: {len(finished)}',
              'Cada bloque compila hasta 2 h; despues guarda el avance.',
              'ETA orientativa: 75-100 min desde el inicio; builds recientes: 63 y 88 min.',
              'Porcentaje Ninja: no disponible en el log publico en vivo.',
              run['html_url']]
    return '\n'.join(lines), events


def show_window(snapshot, old_window):
    if old_window is not None and old_window.poll() is None:
        old_window.terminate()
        old_window.wait(timeout=5)
    if not os.environ.get('DISPLAY'):
        return None
    if shutil.which('zenity'):
        command = ['zenity', '--text-info', '--title=Archium: estado de compilacion',
                   '--width=720', '--height=460', '--timeout=90', '--filename=' + str(snapshot)]
    elif shutil.which('xmessage'):
        command = ['xmessage', '-center', '-title', 'Archium: estado de compilacion',
                   '-buttons', 'Cerrar:0', '-timeout', '90', '-file', str(snapshot)]
    else:
        return None
    return subprocess.Popen(command, stdout=subprocess.DEVNULL)


def ascii_window(text):
    width = max(36, min(88, shutil.get_terminal_size((80, 24)).columns - 2))
    inside = width - 4
    colors = os.environ.get('NO_COLOR') is None and (sys.stdout.isatty() or os.environ.get('CLICOLOR_FORCE') == '1')
    palette = {'cyan': '\033[96m', 'purple': '\033[95m', 'green': '\033[92m',
               'yellow': '\033[93m', 'red': '\033[91m', 'dim': '\033[90m', 'white': '\033[97m'}
    def paint(value, color):
        return palette[color] + value + '\033[0m' if colors else value
    def simplify(value):
        value = re.sub(r'Run actions/checkout@[a-f0-9]+', 'Descargar codigo', value)
        for old, new in [('Compile, run gates and checkpoint', 'Compilación y pruebas'),
                         ('Restore checkpoint and prepare Chromium', 'Preparar Chromium'),
                         ('Check repository before checkpoint restore', 'Verificar repositorio'),
                         ('Compile for two hours and checkpoint', 'Compilar / guardar avance'),
                         ('Set up job', 'Preparar runner'), ('Save completed APK', 'Guardar APK'),
                         ('in_progress', 'EN CURSO'), ('completed', 'TERMINADO'),
                         ('success', 'CORRECTO'), ('failure', 'FALLO'), ('cancelled', 'CANCELADO'),
                         ('queued', 'EN COLA'), ('skipped', 'OMITIDO')]:
            value = value.replace(old, new)
        return value
    lines = text.splitlines()
    log_at = next((i for i, line in enumerate(lines) if line == 'Ultimos eventos:'), len(lines))
    main = lines[:log_at]
    get = lambda prefix: next((line[len(prefix):] for line in main if line.startswith(prefix)), '--')
    status = next((line for line in main if line.startswith('Run ')), 'Sin conexión con GitHub')
    status_color = 'red' if any(x in status for x in ('failure', 'cancelled', 'timed_out')) else ('green' if 'success' in status else 'yellow')
    run_id = status.split(':', 1)[0].removeprefix('Run ')
    rows = [paint('┌' + '─' * (width - 2) + '┐', 'cyan')]
    def row(value, color='white'):
        for line in textwrap.wrap(simplify(value), width=inside) or ['']:
            rows.append(paint('│', 'cyan') + ' ' + paint(line.ljust(inside), color) + ' ' + paint('│', 'cyan'))
    def separator():
        rows.append(paint('├' + '─' * (width - 2) + '┤', 'cyan'))
    row('ARCHIUM · ' + (run_id if status.startswith('Run ') else 'MONITOR'), 'purple')
    separator()
    row('Estado: ' + (status.split(':', 1)[1].strip() if ':' in status else status), status_color)
    if status.startswith('Run '):
        phase = get('Paso: ')
        if phase != '--':
            row('Fase: ' + phase)
        row('Tiempo: ' + get('Tiempo transcurrido: '))
        installation = get('Instalación: ')
        if installation != '--':
            row('Instalación: ' + installation,
                'green' if installation == 'CONFIRMADA' else 'yellow')
        if 'completed' not in status:
            row('ETA: 80–110 min desde el inicio, si pasan los gates.')
    else:
        errors = [line for line in main if line.strip()]
        row(errors[-1] if errors else 'Esperando conexión', 'red')
    row('Actualizado: ' + get('Actualizado: ') + ' · cada 10 min', 'dim')
    separator()
    row('r Actualizar · q Salir', 'green')
    rows.append(paint('└' + '─' * (width - 2) + '┘', 'cyan'))
    return '\n'.join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', default=RUN)
    parser.add_argument('--interval', type=int, default=600)
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--no-window', action='store_true')
    parser.add_argument('--ascii', action='store_true', help='Render a terminal ASCII window')
    parser.add_argument('--state-dir', type=Path, default=Path(__file__).resolve().parent / 'archium-monitor')
    parser.add_argument('--update-state-dir', type=Path)
    args = parser.parse_args()
    if not args.run.isdigit() or args.interval < 10:
        parser.error('run must be numeric; interval must be >=10 seconds')
    args.state_dir.mkdir(parents=True, exist_ok=True)
    lock = (args.state_dir / 'monitor.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('El monitor ya esta activo.')
    (args.state_dir / 'monitor.pid').write_text(str(os.getpid()) + '\n')
    log = args.state_dir / 'actividad.log'
    snapshot = args.state_dir / 'estado.txt'
    events_cache = args.state_dir / 'events.json'
    try:
        seen = set(json.loads(events_cache.read_text()))
    except (OSError, ValueError):
        seen = set()
    window = None
    try:
        while True:
            stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
            done = False
            try:
                run = get_json(f'repos/{REPO}/actions/runs/{args.run}')
                jobs = []
                page = 1
                while True:
                    response = get_json(f'repos/{REPO}/actions/runs/{args.run}/jobs?per_page=100&page={page}')
                    jobs.extend(response['jobs'])
                    if len(jobs) >= response['total_count']:
                        break
                    page += 1
                summary, events = describe(run, jobs, datetime.now(timezone.utc))
                new_events = [event for event in events if event not in seen]
                seen.update(events)
                events_cache.write_text(json.dumps(sorted(seen)))
                with log.open('a') as output:
                    output.write(f'[{stamp}] Consulta: {run["status"]} {run.get("conclusion") or ""}\n')
                    for event in new_events:
                        output.write(f'[{stamp}] {event}\n')
                done = run['status'] == 'completed'
                if args.update_state_dir:
                    try:
                        update = json.loads((args.update_state_dir / 'status.json').read_text())
                    except (OSError, ValueError):
                        update = {'stage': 'waiting_build'}
                    stage = update.get('stage')
                    label = {'installed': 'CONFIRMADA', 'waiting_device': 'Esperando dispositivo',
                             'error': 'ERROR: ' + update.get('error', ''),
                             'retrying': 'Reintentando conexión',
                             'waiting_build': 'Pendiente del build'}.get(stage, 'En curso')
                    summary += '\nInstalación: ' + label
                    if done and run.get('conclusion') == 'success':
                        done = stage in ('installed', 'error')
            except Exception as error:
                summary = f'No se pudo consultar GitHub. Se intentara de nuevo en {args.interval} segundos.\n' + str(error)
                with log.open('a') as output:
                    output.write(f'[{stamp}] Error: {error}\n')
            recent = log.read_text().splitlines()[-12:]
            snapshot.write_text(f'Actualizado: {stamp}\n\n{summary}\n\nUltimos eventos:\n' + '\n'.join(recent) + '\n')
            display_text = snapshot.read_text()
            print(ascii_window(display_text) if args.ascii else display_text, flush=True)
            if not args.no_window:
                window = show_window(snapshot, window)
            if args.once or done:
                break
            time.sleep(args.interval)
    finally:
        (args.state_dir / 'monitor.pid').unlink(missing_ok=True)
        lock.close()


if __name__ == '__main__':
    main()
