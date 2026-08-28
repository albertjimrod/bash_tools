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
  Avahi — con botón. Los que tienen interfaz web propia (Ollama, Netdata,
  CUPS) muestran un enlace directo para abrirla; los que no, indican
  "sin interfaz web" en vez de dejar el hueco vacío.
- **Solo información**: firewall (UFW), actualizaciones automáticas, snapd —
  se muestran pero no tienen botón, para no arriesgar a dejarte sin red o sin
  sesión gráfica por un clic.
- **Contenedores Docker**: todos los que tengas, activos o parados, agrupados
  por prefijo de nombre, con botón arrancar/parar. Cada uno con puerto
  publicado muestra su enlace `http://localhost:<puerto>` — se calcula a
  partir de la configuración del contenedor, así que se ve aunque esté
  parado, no solo cuando está arrancado.
- **Estado del sistema**: carga/uptime, RAM, disco, GPU, actualizaciones
  pendientes de `apt`, estado del firewall.

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
`docker`.

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
2. Si quieres que tenga botón, añade sus 3 líneas (start/stop/restart) a
   `sudoers-panel-control` y reinstálalo (paso 1).
