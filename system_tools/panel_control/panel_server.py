#!/usr/bin/env python3
"""Panel de control local del sistema.

Sirve una página web en 127.0.0.1 (nunca en la red) que muestra el estado
de accesos remotos, servicios systemd y contenedores Docker instalados en
la máquina, con botones para activar/desactivarlos, más un vistazo rápido
al estado general (carga, RAM, disco, GPU, actualizaciones pendientes).

Solo usa la librería estándar de Python: no requiere ningún entorno virtual
ni paquete instalado, para poder arrancarlo siempre con /usr/bin/python3.

El arranque/parada de servicios de SISTEMA usa `sudo -n systemctl ...`, que
requiere que `/etc/sudoers.d/panel-control` esté instalado (ver README.md);
si no lo está, el botón simplemente fallará con un error explicativo en
vez de quedarse colgado pidiendo contraseña. Los servicios marcados como
`"scope": "user"` (p.ej. Herdr) usan `systemctl --user`, que no necesita
sudo ni sudoers: son unidades propias de la sesión de systemd del usuario.
"""
import json
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8990
STATIC_DIR = Path(__file__).parent / "static"

SYSTEMCTL = "/usr/bin/systemctl"
SUDO = "/usr/bin/sudo"
DOCKER = "/usr/bin/docker"

# --- Listas blancas: el panel solo puede tocar lo que está aquí ---

REMOTE_ACCESS = [
    {"unit": "ssh.socket", "label": "SSH"},
    {"unit": "tailscaled.service", "label": "Tailscale"},
    {"unit": "teamviewerd.service", "label": "TeamViewer"},
    {"unit": "gnome-remote-desktop.service", "label": "GNOME Remote Desktop"},
    {"unit": "openvpn.service", "label": "OpenVPN"},
]

SERVICES = [
    {"unit": "docker.service", "label": "Docker (motor)", "url": None, "scope": "system"},
    {"unit": "ollama.service", "label": "Ollama", "url": "http://localhost:11434", "scope": "system"},
    {"unit": "netdata.service", "label": "Netdata", "url": "http://localhost:19999", "scope": "system"},
    {"unit": "libvirtd.service", "label": "libvirt (máquinas virtuales)", "url": None, "scope": "system"},
    {"unit": "cups.service", "label": "CUPS (impresión)", "url": "http://localhost:631", "scope": "system"},
    {"unit": "avahi-daemon.service", "label": "Avahi (mDNS)", "url": None, "scope": "system"},
    # Unidad de USUARIO (no de sistema): no necesita sudo, systemctl --user
    # habla directamente con la sesión de systemd de 'ion'.
    {"unit": "herdr.service", "label": "Herdr (agentes en terminal)", "url": None, "scope": "user"},
]

INFO_ONLY = [
    {"unit": "ufw.service", "label": "Firewall (UFW)"},
    {"unit": "unattended-upgrades.service", "label": "Actualizaciones automáticas"},
    {"unit": "snapd.service", "label": "Snapd"},
]

TOGGLEABLE_UNITS = {s["unit"]: s for s in REMOTE_ACCESS + SERVICES}


def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return p.returncode, (p.stdout or p.stderr).strip()
    except Exception as e:
        return 1, str(e)


def _systemctl(scope: str) -> list[str]:
    return [SYSTEMCTL, "--user"] if scope == "user" else [SYSTEMCTL]


def unit_status(unit: str, scope: str = "system") -> str:
    _, out = _run(_systemctl(scope) + ["is-active", unit])
    return out or "inactive"


def unit_enabled(unit: str, scope: str = "system") -> bool:
    # 'static' (sin sección [Install]) también sale con código 0, pero no
    # arranca solo — solo cuenta como habilitado el 'enabled' real.
    _, out = _run(_systemctl(scope) + ["is-enabled", unit])
    return out.strip() == "enabled"


def toggle_unit(unit: str, action: str) -> tuple[bool, str]:
    entry = TOGGLEABLE_UNITS.get(unit)
    if entry is None:
        return False, "servicio no permitido"
    if action not in ("start", "stop", "restart"):
        return False, "acción no permitida"

    scope = entry.get("scope", "system")
    if scope == "user":
        cmd = _systemctl(scope) + [action, unit]
    else:
        cmd = [SUDO, "-n"] + _systemctl(scope) + [action, unit]

    code, out = _run(cmd)
    if code != 0:
        default_err = (
            "fallo al ejecutar systemctl --user"
            if scope == "user"
            else "sudo sin permiso: revisa /etc/sudoers.d/panel-control"
        )
        return False, out or default_err
    return True, "ok"


def _container_urls(inspected: dict) -> list[str]:
    """Puertos configurados de un contenedor (esté arrancado o no), a partir
    de 'docker inspect' en vez de 'docker ps': HostConfig.PortBindings es la
    configuración estática (-p host:contenedor) y no depende de que el
    contenedor esté corriendo, al contrario que el campo 'Ports' de
    'docker ps', que solo refleja puertos realmente abiertos ahora mismo."""
    host_ports = set()
    bindings = (inspected.get("HostConfig") or {}).get("PortBindings") or {}
    for specs in bindings.values():
        for spec in specs or []:
            p = (spec or {}).get("HostPort", "")
            if p.isdigit():
                host_ports.add(int(p))

    # Contenedores con --network host no usan PortBindings (comparten la red
    # del host directamente): el puerto real es el que declara la imagen.
    if not host_ports and (inspected.get("HostConfig") or {}).get("NetworkMode") == "host":
        exposed = (inspected.get("Config") or {}).get("ExposedPorts") or {}
        for p in exposed:
            base = p.split("/")[0]
            if base.isdigit():
                host_ports.add(int(base))

    return [f"http://localhost:{p}" for p in sorted(host_ports)]


def docker_containers() -> list[dict]:
    code, out = _run([
        DOCKER, "ps", "-a", "--format", "{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}",
    ])
    if code != 0 or not out:
        return []

    rows = []
    ids = []
    for line in out.splitlines():
        parts = line.split("|", 3)
        if len(parts) != 4:
            continue
        rows.append(parts)
        ids.append(parts[0])

    inspected_by_id = {}
    if ids:
        code, raw = _run([DOCKER, "inspect"] + ids)
        if code == 0 and raw:
            try:
                for entry in json.loads(raw):
                    inspected_by_id[entry.get("Id", "")[:12]] = entry
            except Exception:
                pass

    containers = []
    for cid, name, image, status in rows:
        containers.append({
            "name": name,
            "image": image,
            "status": status,
            "running": status.lower().startswith("up"),
            "urls": _container_urls(inspected_by_id.get(cid, {})),
        })
    return containers


def toggle_container(name: str, action: str) -> tuple[bool, str]:
    names = {c["name"] for c in docker_containers()}
    if name not in names:
        return False, "contenedor no encontrado"
    if action not in ("start", "stop", "restart"):
        return False, "acción no permitida"
    code, out = _run([DOCKER, action, name])
    if code != 0:
        return False, out or "fallo al ejecutar docker"
    return True, "ok"


def system_info() -> dict:
    info = {}

    _, up = _run(["uptime", "-p"])
    info["uptime"] = up

    _, load = _run(["cat", "/proc/loadavg"])
    info["load"] = " ".join(load.split()[:3]) if load else "?"

    _, mem = _run(["free", "-h"])
    mem_line = next((l for l in mem.splitlines() if l.startswith("Mem:")), "")
    mem_parts = mem_line.split()
    if len(mem_parts) >= 7:
        info["mem_total"] = mem_parts[1]
        info["mem_used"] = mem_parts[2]
        info["mem_available"] = mem_parts[6]

    _, disk = _run(["df", "-h", "/"])
    disk_lines = disk.splitlines()
    if len(disk_lines) >= 2:
        d = disk_lines[1].split()
        if len(d) >= 5:
            info["disk_total"] = d[1]
            info["disk_used"] = d[2]
            info["disk_free"] = d[3]
            info["disk_pct"] = d[4]

    code, gpu = _run([
        "nvidia-smi",
        "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total",
        "--format=csv,noheader,nounits",
    ])
    if code == 0 and gpu:
        parts = [p.strip() for p in gpu.split(",")]
        if len(parts) == 5:
            info["gpu"] = {
                "name": parts[0], "temp": parts[1], "util": parts[2],
                "mem_used": parts[3], "mem_total": parts[4],
            }

    code, upgrades = _run(
        ["bash", "-c", "apt list --upgradable 2>/dev/null | tail -n +2 | wc -l"]
    )
    info["pending_updates"] = upgrades.strip() if code == 0 else "?"
    info["firewall_active"] = unit_status("ufw.service") == "active"

    return info


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, name):
        path = STATIC_DIR / name
        if not path.exists():
            self.send_error(404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._serve_static("index.html")
        elif self.path == "/api/status":
            def block(items):
                return [
                    {
                        **s,
                        "active": unit_status(s["unit"], s.get("scope", "system")) == "active",
                        "enabled": unit_enabled(s["unit"], s.get("scope", "system")),
                    }
                    for s in items
                ]

            self._json({
                "remote_access": block(REMOTE_ACCESS),
                "services": block(SERVICES),
                "info_only": block(INFO_ONLY),
                "containers": docker_containers(),
                "system": system_info(),
            })
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw)
        except Exception:
            self._json({"ok": False, "error": "json inválido"}, 400)
            return

        if self.path == "/api/service/toggle":
            ok, msg = toggle_unit(data.get("unit", ""), data.get("action", ""))
        elif self.path == "/api/docker/toggle":
            ok, msg = toggle_container(data.get("name", ""), data.get("action", ""))
        else:
            self.send_error(404)
            return

        self._json({"ok": ok, "error": None if ok else msg})


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Panel de control en http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
