# Panel de control

Página web local (`http://127.0.0.1:8990`) para ver y activar/desactivar de
un vistazo lo que tienes corriendo en la máquina: accesos remotos, servicios
systemd, contenedores Docker, y el estado general del sistema (carga, RAM,
disco, GPU, actualizaciones pendientes, firewall).

Solo escucha en `127.0.0.1`: no es accesible desde la red, solo desde esta
máquina.

## Qué muestra

- **Accesos remotos** (destacado): SSH, Tailscale, TeamViewer, GNOME Remote
  Desktop, OpenVPN — con botón para activar/desactivar cada uno.
- **Servicios y herramientas**: Docker, Ollama, Netdata, libvirt (VMs), CUPS,
  Avahi, Herdr, Syncthing, un túnel SSH, Fabric — con botón. Los que tienen
  interfaz web propia muestran un enlace directo para abrirla; los que no,
  indican "sin interfaz web" en vez de dejar el hueco vacío. La mayoría son
  unidades de **sistema** (necesitan sudo, ver instalación); Herdr, Syncthing,
  el túnel y Fabric son unidades de **usuario** (`systemctl --user`, sin
  sudo). Herdr y Fabric arrancan "static" a propósito — nunca se activan
  solas al iniciar sesión, solo cuando le das al botón; Syncthing y el túnel
  ya venían activas de antes (se muestran, no se fuerza su estado).
- **Solo información**: firewall (UFW), actualizaciones automáticas, snapd —
  se muestran pero no tienen botón, para no arriesgar a dejarte sin red o sin
  sesión gráfica por un clic.
- **Contenedores Docker**: todos los que tengas, activos o parados, agrupados
  por prefijo de nombre, con botón arrancar/parar. Cada uno con puerto
  publicado muestra su enlace `http://localhost:<puerto>` — se calcula a
  partir de la configuración del contenedor, así que se ve aunque esté
  parado, no solo cuando está arrancado.
- **Proyectos Docker Compose**: a diferencia de "Contenedores Docker" (que
  solo puede mostrar lo que `docker ps` ya conoce), esta sección lista stacks
  completos definidos por un `docker-compose.yml` **aunque nunca se hayan
  levantado** — para eso exactamente sirve: que no se te olvide que tienes
  algo instalado. El botón hace `docker compose up -d` / `down` sobre el
  proyecto entero. El primer arranque de un stack que compila su propia
  imagen puede tardar varios minutos.
- **Skills de agente (Claude Code)**: solo aparece si tienes instalado
  `agent-reach` (pipx). No es un servicio ni un contenedor: es una *skill*
  que le da a Claude Code acceso de lectura a LinkedIn, Reddit, YouTube, X,
  etc. Está "activa" cuando existe `~/.claude/skills/agent-reach/SKILL.md`;
  el botón hace `agent-reach skill --install` / `--uninstall` (mismo usuario,
  sin sudo). La badge muestra cuántos canales están listos según
  `agent-reach doctor` (cacheado 10 min). Tras activar/desactivar hay que
  reiniciar Claude Code para que note el cambio; los logins de cada
  plataforma se hacen aparte con `agent-reach setup`.
- **Puertos en uso**: todo lo que está escuchando ahora mismo, calculado en
  cada refresco con `ss` (no hay ninguna lista de puertos en el código). Sin
  sudo: cada socket se identifica por su cgroup, que da la unidad systemd
  exacta o el contenedor Docker aunque el proceso sea de root; los de
  docker-proxy se cruzan con los puertos publicados de cada contenedor, y las
  apps de escritorio usan el nombre del snap o del proceso. La tabla principal
  muestra los servicios con interfaz web que el panel ya conoce, las apps
  propias en puertos fijos y todo lo que escucha en **toda la red**
  (resaltado, con badge de cuántos hay). El resto (UDP, DNS, Tailscale,
  puertos internos, puertos aleatorios) va en un bloque plegable "Sistema y
  otros". Debajo se listan los servicios, contenedores y proyectos Compose
  con puerto configurado que no están escuchando, y si un proyecto Compose
  parado reclama un puerto que ya usa otro, la fila lo avisa.
- **Estado del sistema**: carga/uptime, RAM, disco, GPU, actualizaciones
  pendientes de `apt`, estado del firewall.
- **Pie de página**: dónde está el código del panel y qué unidad lo sirve.

> Qué puertos y servicios tienes expuestos en concreto solo lo ves tú, en tu
> propio navegador — deliberadamente no se documenta aquí para no dar pistas
> a quien mire este repo desde fuera.

## Instalación

No requiere ningún paquete Python (solo librería estándar).

### 1. Permiso para arrancar/parar servicios sin contraseña

Los botones de "Servicios" necesitan `sudo systemctl start/stop`. Para que no
te pida la contraseña cada vez, instala la regla de sudoers **restringida
únicamente a esos servicios concretos** (nunca da sudo general):

```bash
cd system_tools/panel_control
sudo cp sudoers-panel-control /etc/sudoers.d/panel-control
sudo chmod 440 /etc/sudoers.d/panel-control
sudo visudo -c   # comprueba que todo el sudoers del sistema sigue siendo válido
```

Si añades algún servicio nuevo a la lista blanca en `panel_server.py`
(`TOGGLEABLE_UNITS`), repite este paso tras añadir sus líneas en
`sudoers-panel-control`.

Los contenedores Docker no necesitan este paso: ya perteneces al grupo
`docker`. Los servicios de **usuario** (Herdr) tampoco: se instalan aparte
(paso 1b) y no requieren sudo.

### 1b. Servicios de usuario (Herdr, Fabric)

No van en el sudoers. Se instalan como unidades de systemd **de usuario**,
sin activarlas automáticamente (las enciendes/apagas tú desde el panel):

```bash
cp herdr.service fabric.service ~/.config/systemd/user/
systemctl --user daemon-reload
```

Con eso ya aparecen en el panel, apagadas, listas para el botón "Activar".
Syncthing y el túnel SSH a v15 no necesitan este paso: ya existían como
unidades de usuario antes de tener el panel, solo hubo que añadirlas a la
lista blanca en `panel_server.py`.

### 2. Arranque automático (opcional pero recomendado)

Para que el panel esté siempre disponible sin tener que lanzarlo a mano:

```bash
mkdir -p ~/.config/systemd/user
cp panel-control.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now panel-control.service
```

Comprobar que está corriendo:

```bash
systemctl --user status panel-control.service
```

### 3. Uso manual (sin instalar el servicio)

```bash
python3 panel_server.py
```

Y abre `http://127.0.0.1:8990` en el navegador.

## Añadir un servicio nuevo a la lista

1. Añádelo a `REMOTE_ACCESS`, `SERVICES` o `INFO_ONLY` en `panel_server.py`.
2. Si es un servicio de **sistema** y quieres que tenga botón, añade sus 3
   líneas (start/stop/restart) a `sudoers-panel-control` y reinstálalo
   (paso 1).
3. Si es un servicio de **usuario** (`"scope": "user"`, como Herdr), no toca
   sudoers — solo necesita su unidad en `~/.config/systemd/user/` (paso 1b).
   Antes de fijarle un puerto en `--address`/similar, comprueba que no choca
   con otro servicio que ya tengas corriendo.
4. Para un stack de Docker Compose que quieras poder arrancar/parar aunque
   no esté levantado, añádelo a `COMPOSE_PROJECTS` en `panel_server.py` con
   un `"id"` propio (úsalo siempre con `-p`, para que no se mezcle con otro
   proyecto que viva en la misma carpeta).
