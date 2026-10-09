#!/data/data/com.termux/files/usr/bin/bash
# Ejecutar en Termux: bash ~/storage/downloads/vigilar-compilacion-arc.sh
# Solo consultar una vez: añadir --once. Ctrl+C detiene el monitor, no el build.
set -uo pipefail

if [[ -d /data/data/com.termux/files/usr/bin ]]; then
    export PATH="/data/data/com.termux/files/usr/bin:$PATH"
fi
readonly repo='Jorgeprdz/chromium-dex-arc'
readonly run_id='37871846597'
readonly api="https://api.github.com/repos/$repo/actions/runs/$run_id"
readonly url="https://github.com/$repo/actions/runs/$run_id"
readonly interval=600
once=false
case "${1:-}" in
    --once) once=true ;;
    '') ;;
    *) printf 'Uso: bash %s [--once]\n' "$0"; exit 2 ;;
esac
for dependency in curl jq; do
    if ! command -v "$dependency" >/dev/null 2>&1; then
        printf 'Falta %s. En Termux: pkg install curl jq\n' "$dependency" >&2
        exit 2
    fi
done
trap 'printf "\nMonitor detenido. La compilación sigue en GitHub.\n"; exit 0' INT TERM
printf 'Archium: geometría Arc + media, sin contraseñas locales.\n%s\n' "$url"
printf 'Consulta cada 10 minutos; Ctrl+C para salir. No requiere iniciar sesión.\n'

while :; do
    printf '\n[%s]\n' "$(date '+%Y-%m-%d %H:%M:%S')"
    if data=$(curl --fail --silent --show-error --connect-timeout 15 --max-time 30 \
        -H 'Accept: application/vnd.github+json' "$api"); then
        if ! status=$(printf '%s' "$data" | jq -er '.status'); then
            printf 'Respuesta de GitHub sin estado válido.\n' >&2
            exit 2
        fi
        conclusion=$(printf '%s' "$data" | jq -r '.conclusion // "pendiente"')
        printf 'Estado: %s | Resultado: %s\n' "$status" "$conclusion"
        if jobs=$(curl --fail --silent --show-error --connect-timeout 15 --max-time 30 \
            -H 'Accept: application/vnd.github+json' "$api/jobs?per_page=100"); then
            printf '%s' "$jobs" | jq -r '.jobs[] | "Trabajo: \(.name) [\(.status)]", (.steps[] | "  \(.name): \(.conclusion // .status)")'
        fi
        if [[ "$status" == completed ]]; then
            printf '\nTerminó: %s. Detalles y logs: %s\n' "$conclusion" "$url"
            if [[ "$conclusion" == success ]]; then
                printf 'Build terminado. Verifica artifact, firma y pruebas antes de instalar o declarar aceptación.\n'
                exit 0
            fi
            exit 1
        fi
    else
        printf 'No se pudo consultar GitHub (red o límite de API).\n' >&2
        if "$once"; then exit 2; fi
    fi
    if "$once"; then exit 0; fi
    sleep "$interval"
done
