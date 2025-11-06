#!/usr/bin/env bash
# detectar_openwebui.sh — se auto-eleva a root y detecta cómo/ dónde corre OpenWebUI

# Auto-elevación
if [[ $EUID -ne 0 ]]; then
  exec sudo -E bash "$0" "$@"
fi

set -euo pipefail

echo "== Usuario efectivo: $(id -un) (UID $EUID) =="

echo
echo "== Buscar contenedores Docker/Podman =="
if command -v docker >/dev/null 2>&1; then
  docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}" | grep -Ei "open[-_]?webui|ghcr.io/open-webui" || echo "(no hay contenedores OpenWebUI en docker en ejecución)"
else
  echo "(docker no instalado)"
fi
if command -v podman >/dev/null 2>&1; then
  podman ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}" | grep -Ei "open[-_]?webui|ghcr.io/open-webui" || echo "(no hay contenedores OpenWebUI en podman en ejecución)"
else
  echo "(podman no instalado)"
fi

echo
echo "== systemd (servicios) =="
if command -v systemctl >/dev/null 2>&1; then
  systemctl list-units --type=service --all | grep -Ei "open[-_]?webui" || echo "(no hay servicios con nombre parecido)"
  (systemctl status openwebui || true) >/dev/null 2>&1 && systemctl status openwebui || true
  (systemctl status open-webui || true) >/dev/null 2>&1 && systemctl status open-webui || true
else
  echo "(systemctl no disponible)"
fi

echo
echo "== pip/pipx (CLI) =="
if command -v pipx >/dev/null 2>&1; then
  pipx list | grep -Ei "open[-_]?webui" || echo "(no encontrado en pipx)"
else
  echo "(pipx no instalado)"
fi
python3 - <<'PY' || true
import shutil
for cmd in ("open-webui","openwebui"):
    p = shutil.which(cmd)
    if p:
        print(f"Encontrado binario: {cmd} -> {p}")
PY

echo
echo "== Snap / Brew =="
if command -v snap >/dev/null 2>&1; then
  snap list | grep -Ei "open[-_]?webui" || echo "(no encontrado en snap)"
else
  echo "(snap no instalado)"
fi
if command -v brew >/dev/null 2>&1; then
  brew list --formula | grep -Ei "open[-_]?webui" || echo "(no encontrado en brew)"
else
  echo "(brew no instalado)"
fi

echo
echo "== Puertos típicos (3000/8080/11434) =="
for p in 3000 8080 11434; do
  resp=$( (curl -sS -I http://127.0.0.1:$p | head -n1) 2>/dev/null || true )
  [[ -z "$resp" ]] && resp="no responde"
  echo "  $p -> $resp"
done

echo
echo "== Procesos relacionados y puertos en LISTEN =="
pgrep -af "open-webui|openwebui|uvicorn|fastapi|node" || echo "(no hay procesos coincidentes)"
if command -v ss >/dev/null 2>&1; then
  ss -ltnp | grep -Ei "uvicorn|python|open[-_]?webui|node" || echo "(ningún socket en LISTEN relacionado)"
elif command -v lsof >/dev/null 2>&1; then
  lsof -iTCP -sTCP:LISTEN -P | grep -Ei "uvicorn|python|open[-_]?webui|node" || echo "(ningún socket en LISTEN relacionado)"
else
  echo "(ni ss ni lsof disponibles)"
fi

echo
echo "== Sugerencia =="
echo "Si no aparece nada arriba, probablemente OpenWebUI no está corriendo."
echo "Para iniciarlo con Docker (como root):"
echo "  docker run -d --name openwebui -p 3000:8080 -e OLLAMA_BASE_URL=http://host.docker.internal:11434 -v openwebui:/app/backend/data ghcr.io/open-webui/open-webui:main"
echo "Luego abre: http://localhost:3000"

