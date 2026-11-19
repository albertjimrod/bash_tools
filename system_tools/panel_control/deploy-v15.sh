#!/usr/bin/env bash
# Propaga el panel de control de R7 a V15 y aplica el cambio también en R7.
#
# Lo lanza panel-deploy-v15.path cada vez que guardas un fichero del panel, y
# panel-deploy-v15.timer cada 15 min (y al arrancar) para ponerse al día si V15
# estaba apagado cuando editaste. También se puede ejecutar a mano:
#
#   ./deploy-v15.sh
#
# El panel solo se edita en R7: en V15 vive una copia en
# ~/.local/share/panel-control que este script sobrescribe. Ver DOS-MAQUINAS.md.
set -euo pipefail

SRC="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
REMOTE="${PANEL_DEPLOY_HOST:-v15}"        # alias de ~/.ssh/config
REMOTE_DIR=".local/share/panel-control"   # relativo al home de V15
UNIT="panel-control.service"              # mismo nombre en las dos máquinas
SSH="ssh -o ConnectTimeout=15 -o BatchMode=yes"
STATE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/panel-control"

log() { echo "[panel-deploy] $*"; }

# 1. Nunca propagar un fichero roto: si no compila, no se toca ninguna máquina.
if ! python3 -I -c 'import sys; compile(open(sys.argv[1]).read(), sys.argv[1], "exec")' \
        "$SRC/panel_server.py"; then
    log "panel_server.py no compila: no se despliega nada"
    exit 1
fi

# 2. R7: el HTML se lee del disco en cada petición, pero el Python solo al
#    arrancar. Si cambió, se reinicia el panel local (solo si estaba corriendo).
mkdir -p "$STATE_DIR"
new_hash=$(sha256sum "$SRC/panel_server.py" | cut -d' ' -f1)
old_hash=$(cat "$STATE_DIR/local.sha256" 2>/dev/null || true)
if [[ "$new_hash" != "$old_hash" ]]; then
    if systemctl --user is-active --quiet "$UNIT"; then
        systemctl --user restart "$UNIT"
        log "R7: panel reiniciado con el código nuevo"
    fi
    echo "$new_hash" > "$STATE_DIR/local.sha256"
fi

# 3. V15: si no responde (apagado, sin red), se sale sin error; el temporizador
#    lo reintentará.
if ! $SSH "$REMOTE" true 2>/dev/null; then
    log "$REMOTE no responde: se reintentará en el próximo ciclo del temporizador"
    exit 0
fi

# rsync solo copia lo que ha cambiado; --itemize-changes dice qué ha copiado.
code_changes=$(rsync -a --delete --mkpath --itemize-changes --exclude '__pycache__' -e "$SSH" \
    "$SRC/panel_server.py" "$SRC/static" "$REMOTE:$REMOTE_DIR/")
unit_changes=$(rsync -a --itemize-changes -e "$SSH" \
    "$SRC/panel-control-v15.service" "$REMOTE:.config/systemd/user/$UNIT")

if [[ -z "$code_changes$unit_changes" ]]; then
    log "V15 ya estaba al día"
    exit 0
fi
[[ -n "$code_changes" ]] && log "V15: copiado -> $(echo "$code_changes" | awk '/^[<>c]f/{print $2}' | xargs)"

remote_cmd=""
if [[ -n "$unit_changes" ]]; then
    remote_cmd+="systemctl --user daemon-reload; "
    log "V15: unidad systemd actualizada"
fi
# Solo hace falta reiniciar si cambió el Python o la unidad (no por el HTML).
if [[ -n "$unit_changes" ]] || grep -q 'panel_server.py' <<<"$code_changes"; then
    remote_cmd+="systemctl --user try-restart $UNIT"
fi
if [[ -n "$remote_cmd" ]]; then
    $SSH "$REMOTE" "$remote_cmd"
    log "V15: panel reiniciado con el código nuevo"
fi
