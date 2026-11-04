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
import ipaddress
import json
import os
import pwd
import re
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8990
STATIC_DIR = Path(__file__).parent / "static"

SYSTEMCTL = "/usr/bin/systemctl"
SUDO = "/usr/bin/sudo"
DOCKER = "/usr/bin/docker"

# Agent Reach (pipx): CLI que le da a Claude Code acceso de lectura a LinkedIn,
# Reddit, YouTube, etc. No es un servicio: se "activa" instalando su SKILL.md.
AGENT_REACH = str(Path.home() / ".local/bin/agent-reach")
AGENT_REACH_SKILL = Path.home() / ".claude/skills/agent-reach/SKILL.md"

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
    # Unidades de USUARIO (no de sistema): no necesitan sudo, systemctl --user
    # habla directamente con la sesión de systemd de 'ion'.
    {"unit": "herdr.service", "label": "Herdr (agentes en terminal)", "url": None, "scope": "user"},
    {"unit": "syncthing.service", "label": "Syncthing", "url": "http://localhost:8384", "scope": "user"},
    {"unit": "syncthing-tunnel-v15.service", "label": "Túnel SSH a v15 (Syncthing remoto)", "url": "http://localhost:8385", "scope": "user"},
    {"unit": "fabric.service", "label": "Fabric (API IA)", "url": "http://localhost:8099", "scope": "user"},
]

INFO_ONLY = [
    {"unit": "ufw.service", "label": "Firewall (UFW)"},
    {"unit": "unattended-upgrades.service", "label": "Actualizaciones automáticas"},
    {"unit": "snapd.service", "label": "Snapd"},
]

TOGGLEABLE_UNITS = {s["unit"]: s for s in REMOTE_ACCESS + SERVICES}


def _run(cmd: list[str], timeout: int = 15) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
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
            "id": inspected_by_id.get(cid, {}).get("Id", cid),
            "name": name,
            "image": image,
            "status": status,
            "running": status.lower().startswith("up"),
            "urls": _container_urls(inspected_by_id.get(cid, {})),
        })
    return containers


# --- Proyectos Docker Compose que NO están arrancados como contenedores:
# 'docker ps' nunca los muestra porque, hasta que se levantan una vez, no
# existe ningún contenedor que listar. Se controlan por nombre de proyecto
# (-p), no por fichero, para no depender de en qué carpeta corre el panel y
# para evitar que un proyecto sin 'name:' propio se mezcle por accidente con
# otro que comparte carpeta (es el caso de 'umami', que vive en el mismo
# directorio que el stack principal de intellisynthprice).

COMPOSE_PROJECTS = [
    {
        "id": "mi-wordpress",
        "label": "mi-wordpress (WordPress)",
        "compose_file": "/home/ion/Documentos/albertjimrod/mi-wordpress/docker-compose.yml",
        "url": "http://localhost:3000",
        "note": "puerto 3000 — compite con Sim Studio y Umami, solo uno a la vez",
    },
    {
        "id": "sim",
        "label": "Sim Studio (local)",
        "compose_file": "/home/ion/sim/docker-compose.local.yml",
        "url": "http://localhost:3000",
        "note": "puerto 3000 — compite con mi-wordpress y Umami. Primer arranque puede tardar (compila la imagen)",
    },
    {
        "id": "umami",
        "label": "Umami (analítica IntelliSynthPrice)",
        "compose_file": "/home/ion/dev/github/intellisynthprice/docker-compose.umami.yml",
        "url": "http://localhost:3000",
        "note": "puerto 3000 — compite con mi-wordpress y Sim Studio",
    },
]

COMPOSE_BY_ID = {p["id"]: p for p in COMPOSE_PROJECTS}


def compose_projects_status() -> list[dict]:
    result = []
    for p in COMPOSE_PROJECTS:
        code, out = _run([DOCKER, "compose", "-p", p["id"], "ps", "-q"])
        running = code == 0 and bool(out.strip())
        result.append({**p, "running": running})
    return result


def toggle_compose(project_id: str, action: str) -> tuple[bool, str]:
    project = COMPOSE_BY_ID.get(project_id)
    if project is None:
        return False, "proyecto no permitido"
    base = [DOCKER, "compose", "-p", project_id, "-f", project["compose_file"]]
    if action == "start":
        cmd = base + ["up", "-d"]
    elif action == "stop":
        cmd = base + ["down"]
    else:
        return False, "acción no permitida"
    # 'up' puede tener que compilar una imagen (p.ej. Sim Studio) — más
    # margen que las acciones de systemd/contenedores sueltos.
    code, out = _run(cmd, timeout=600)
    if code != 0:
        return False, out or "fallo al ejecutar docker compose"
    return True, "ok"


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


# --- Agent Reach: no es un servicio systemd ni un contenedor, es una "skill"
# de Claude Code. Está ACTIVA cuando existe su SKILL.md en ~/.claude/skills/;
# el botón hace `agent-reach skill --install/--uninstall` (mismo usuario que
# el panel, sin sudo). El desglose de canales (`agent-reach doctor`) hace
# sondeos de red y tarda, así que se cachea 10 min en vez de lanzarlo en cada
# refresco del panel (cada 5 s).

_doctor_cache = {"at": 0.0, "data": None}


def _agent_reach_channels() -> dict:
    now = time.time()
    cached = _doctor_cache["data"]
    if cached is not None and now - _doctor_cache["at"] < 600:
        return cached

    ready, total, names = 0, 0, []
    code, out = _run([AGENT_REACH, "doctor", "--json"], timeout=45)
    if code == 0 and out:
        try:
            for key, val in json.loads(out).items():
                total += 1
                if val.get("status") == "ok":
                    ready += 1
                    names.append(key)
        except Exception:
            pass
    data = {"ready": ready, "total": total, "ready_names": names}
    _doctor_cache.update(at=now, data=data)
    return data


def agent_reach_status() -> dict | None:
    if not Path(AGENT_REACH).exists():
        return None
    active = AGENT_REACH_SKILL.exists()
    version = ""
    code, out = _run([AGENT_REACH, "version"])
    if code == 0:
        version = out.replace("Agent Reach", "").strip()
    return {
        "skill_active": active,
        "version": version,
        "channels": _agent_reach_channels() if active else None,
    }


def toggle_agent_reach(action: str) -> tuple[bool, str]:
    if not Path(AGENT_REACH).exists():
        return False, "agent-reach no está instalado"
    flag = {"start": "--install", "stop": "--uninstall"}.get(action)
    if flag is None:
        return False, "acción no permitida"
    # `agent-reach skill --install` solo copia la skill en las carpetas que YA
    # existen; si ~/.claude/skills/ no existe, la instala en ~/.agents/skills/
    # y Claude Code no la ve. Creamos la carpeta para forzar que aterrice donde
    # el panel la busca.
    if action == "start":
        AGENT_REACH_SKILL.parent.parent.mkdir(parents=True, exist_ok=True)
    code, out = _run([AGENT_REACH, "skill", flag], timeout=30)
    if code != 0:
        return False, out or "fallo al ejecutar agent-reach skill"
    _doctor_cache.update(at=0.0, data=None)  # fuerza refresco del doctor
    return True, "ok"


# --- Puertos en uso: se calcula en cada refresco con `ss`, sin ninguna lista
# fija de puertos en el código (no se documentan puertos concretos en el repo).
# Sin sudo, `ss -p` solo ve el proceso de los sockets propios; los de root se
# identifican por su cgroup (`ss -e`), que sí es visible para cualquiera y da
# la unidad systemd exacta (netdata.service, ssh.socket...) o el contenedor
# Docker (docker-<id>.scope). docker.service a secas es docker-proxy, y se
# resuelve cruzando el puerto con los puertos publicados de cada contenedor.

SS = "/usr/bin/ss"
PANEL_UNIT = "panel-control.service"


def _ephemeral_low() -> int:
    try:
        return int(Path("/proc/sys/net/ipv4/ip_local_port_range").read_text().split()[0])
    except Exception:
        return 32768


def _url_port(url: str | None) -> int | None:
    if not url:
        return None
    tail = url.rsplit(":", 1)[-1].split("/")[0]
    return int(tail) if tail.isdigit() else None


def _listen_scope(host: str) -> str:
    """Desde dónde se llega al puerto: 'localhost', 'red' (todas las
    interfaces), 'tailscale', 'multicast' o la dirección concreta."""
    iface = ""
    if "%" in host:
        host, iface = host.split("%", 1)
    if iface == "lo":
        return "localhost"
    if iface.startswith("tailscale"):
        return "tailscale"
    if iface:
        return f"solo {iface}"
    if host == "*":
        return "red"
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return host
    if ip.is_loopback:
        return "localhost"
    if ip.is_unspecified:
        return "red"
    if ip.is_multicast:
        return "multicast"
    if ip in ipaddress.ip_network("100.64.0.0/10") or ip in ipaddress.ip_network("fd7a:115c:a1e0::/48"):
        return "tailscale"
    return f"solo {host}"


# Si un mismo servicio escucha en varias direcciones, manda la más expuesta.
_SCOPE_RANK = {"red": 0, "tailscale": 2, "multicast": 3, "localhost": 4}


def _parse_ss() -> list[dict]:
    code, out = _run([SS, "-tulnHpe"])
    if code != 0:
        return []
    sockets = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        host, _, port = parts[4].rpartition(":")
        if not port.isdigit():
            continue
        proc = re.search(r'users:\(\("([^"]+)"', line)
        uid = re.search(r"\buid:(\d+)", line)
        cgroup = re.search(r"\bcgroup:(\S+)", line)
        sockets.append({
            "proto": parts[0],
            "port": int(port),
            "scope": _listen_scope(host.strip("[]").replace("]%", "%")),
            "process": proc.group(1) if proc else None,
            "uid": int(uid.group(1)) if uid else 0,
            "cgroup": cgroup.group(1) if cgroup else "",
        })
    return sockets


def _identify(sock: dict, containers: list[dict], units: dict) -> dict:
    """Devuelve label/origen/url de un socket y si es algo que el panel ya
    conoce (contenedor, o servicio de la lista blanca en su puerto web)."""
    leaf = sock["cgroup"].rsplit("/", 1)[-1]
    port = sock["port"]

    m = re.match(r"docker-([0-9a-f]{12,})\.scope$", leaf)
    if m:
        c = next((c for c in containers if c["id"].startswith(m.group(1))), None)
        if c:
            return {"label": c["name"], "source": "Docker",
                    "url": f"http://localhost:{port}" if sock["proto"] == "tcp" else None,
                    "known": True}
    if leaf == "docker.service":
        for c in containers:
            if port in (_url_port(u) for u in c["urls"]):
                return {"label": c["name"], "source": "Docker",
                        "url": f"http://localhost:{port}", "known": True}
        return {"label": "docker-proxy", "source": "Docker", "url": None, "known": False}

    if leaf == PANEL_UNIT:
        return {"label": "Panel de control (esta página)", "source": "systemd usuario",
                "url": None, "known": True}

    if leaf.endswith((".service", ".socket")):
        source = "systemd usuario" if "/user@" in sock["cgroup"] else "systemd"
        entry = units.get(leaf)
        if entry:
            web = _url_port(entry.get("url")) == port
            return {"label": entry["label"], "source": source,
                    "url": entry["url"] if web else None, "known": web}
        return {"label": leaf.rsplit(".", 1)[0], "source": source, "url": None, "known": False}

    # Aplicación de escritorio: el nombre del snap y, si no, el del proceso
    # (solo visible si es nuestro) son más claros que el del scope (Joplin
    # sale como 'Chromium', Freeplane como 'java').
    snap = re.match(r"snap\.([^.]+)\.", leaf)
    if snap:
        label = f"{snap.group(1)} (snap)"
    elif sock["process"]:
        label = sock["process"]
    else:
        app = re.match(r"app-(?:[a-z]+\.)*([^-.]+)", leaf)
        if app:
            label = app.group(1)
        else:
            try:
                label = pwd.getpwuid(sock["uid"]).pw_name
            except KeyError:
                label = f"uid {sock['uid']}"
    return {"label": label, "source": "aplicación" if leaf.endswith(".scope") else "?",
            "url": None, "known": False}


def listening_ports(containers: list[dict], compose: list[dict]) -> dict:
    units = {s["unit"]: s for s in REMOTE_ACCESS + SERVICES + INFO_ONLY}
    eph_low = _ephemeral_low()
    my_uid = os.getuid()

    rows = {}
    for sock in _parse_ss():
        ident = _identify(sock, containers, units)
        key = (sock["proto"], sock["port"], ident["label"])
        row = rows.get(key)
        if row is None:
            rows[key] = row = {
                "proto": sock["proto"], "port": sock["port"], "scope": sock["scope"],
                "uid": sock["uid"], **ident,
            }
        elif _SCOPE_RANK.get(sock["scope"], 1) < _SCOPE_RANK.get(row["scope"], 1):
            row["scope"] = sock["scope"]

    listening_tcp = {r["port"] for r in rows.values() if r["proto"] == "tcp"}

    # Proyectos Compose parados que reclaman un puerto que ya usa otro.
    for p in compose:
        port = _url_port(p.get("url"))
        if p["running"] or port not in listening_tcp:
            continue
        for r in rows.values():
            if r["proto"] == "tcp" and r["port"] == port:
                r.setdefault("contenders", []).append(p["label"])

    main, system = [], []
    for r in sorted(rows.values(), key=lambda r: (r["port"], r["proto"])):
        is_main = r["proto"] == "tcp" and r["scope"] != "tailscale" and (
            r["known"]
            or r["scope"] == "red"
            or (r["uid"] == my_uid and r["port"] < eph_low)
        )
        (main if is_main else system).append(r)

    # Configurado con puerto pero sin nadie escuchando en él ahora mismo.
    idle = []
    for s in SERVICES:
        port = _url_port(s.get("url"))
        if port and port not in listening_tcp:
            idle.append({"label": s["label"], "port": port, "kind": "servicio"})
    for c in containers:
        if c["running"]:
            continue
        for u in c["urls"]:
            port = _url_port(u)
            if port and port not in listening_tcp:
                idle.append({"label": c["name"], "port": port, "kind": "contenedor"})
    for p in compose:
        port = _url_port(p.get("url"))
        if port and not p["running"] and port not in listening_tcp:
            idle.append({"label": p["label"], "port": port, "kind": "compose"})

    return {"main": main, "system": system, "idle": idle}


def panel_location() -> dict:
    return {
        "dir": str(Path(__file__).resolve().parent),
        "unit": PANEL_UNIT,
        "address": f"{HOST}:{PORT}",
    }


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

            containers = docker_containers()
            compose = compose_projects_status()
            self._json({
                "remote_access": block(REMOTE_ACCESS),
                "services": block(SERVICES),
                "info_only": block(INFO_ONLY),
                "containers": containers,
                "compose_projects": compose,
                "agent_reach": agent_reach_status(),
                "system": system_info(),
                "ports": listening_ports(containers, compose),
                "panel": panel_location(),
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
        elif self.path == "/api/compose/toggle":
            ok, msg = toggle_compose(data.get("id", ""), data.get("action", ""))
        elif self.path == "/api/skill/toggle":
            ok, msg = toggle_agent_reach(data.get("action", ""))
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
