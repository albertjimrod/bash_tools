# El panel en dos máquinas: R7 y V15

El panel de control corre en las dos máquinas con **el mismo código**. R7
(sobremesa) es la máquina **maestra**: ahí se edita el panel, y cada cambio
se propaga solo a V15 (portátil) en unos segundos. Cada panel muestra y
controla **su propia máquina**.

> Este documento no da IPs, MACs ni nombres de red: el repo es público. Donde
> hace falta una dirección se escribe `IP_R7` / `IP_V15`; los valores reales
> están solo en la configuración local de cada máquina (ver más abajo).

```
                 R7 (maestra)                              V15
  ┌───────────────────────────────────────┐   ┌────────────────────────────────────┐
  │ repo bash_tools/…/panel_control/      │   │ ~/.local/share/panel-control/      │
  │   panel_server.py  static/index.html  │   │   panel_server.py  static/         │
  │          │ (guardas un fichero)       │   │          ▲                         │
  │          ▼                            │   │          │                         │
  │ panel-deploy-v15.path ──► deploy-v15.sh ─rsync+ssh──┘                          │
  │ panel-deploy-v15.timer ─┘  (cada 15 min, por si V15 estaba apagado)            │
  │                                       │   │                                    │
  │ panel-control.service                 │   │ panel-control.service              │
  │   escucha 127.0.0.1:8990              │   │   escucha 0.0.0.0:8990             │
  │   (solo R7)                           │   │   (V15 y R7; filtro por IP)        │
  └───────────────────────────────────────┘   └────────────────────────────────────┘
```

## Cómo se accede

| Desde | Panel de R7 | Panel de V15 |
|---|---|---|
| R7  | `http://127.0.0.1:8990` | `http://IP_V15:8990` |
| V15 | — (no expuesto) | `http://127.0.0.1:8990` |

- El panel de **R7 no sale de R7**: escucha solo en `127.0.0.1`, como siempre.
- El panel de **V15** escucha en todas las interfaces, pero solo atiende a la
  propia V15 y a las IPs de `PANEL_ALLOW` (R7). Cualquier otra, incluida la
  IP de Tailscale de R7, recibe `403 cliente no permitido`.
- Por eso las dos IPs deben estar **reservadas en el router** (DHCP estático):
  si el router le da otra IP a V15, la dirección para entrar cambia; si se la
  da a R7, V15 la rechazará.
- La cabecera de la página dice en qué máquina estás: *Panel de control · R7*
  o *· V15*.

## Cómo se propagan los cambios

1. Editas `panel_server.py`, `static/index.html` o `panel-control-v15.service`
   en el repo de **R7** y guardas.
2. `panel-deploy-v15.path` (unidad de usuario de R7) detecta el guardado y
   lanza `panel-deploy-v15.service`, que ejecuta `deploy-v15.sh`:
   1. **Comprueba que el Python compila.** Si no compila, no despliega nada en
      ninguna máquina (y el log lo dice). Así un guardado a medias no tumba
      el panel de V15.
   2. **R7:** si cambió `panel_server.py`, reinicia el panel local (el HTML se
      lee del disco en cada petición y no necesita reinicio).
   3. **V15:** `rsync` sobre `ssh v15` copia solo lo que ha cambiado a
      `~/.local/share/panel-control/` y la unidad a
      `~/.config/systemd/user/panel-control.service`. Si cambió el Python o
      la unidad, reinicia el panel de V15.
3. Si V15 está apagado o sin red, el script termina sin error y
   `panel-deploy-v15.timer` lo reintenta cada 15 minutos (y 3 minutos después
   de arrancar R7). Repetirlo no cuesta nada: si ya está al día, `rsync` no
   copia nada.

No hace falta hacer commit ni push para que el cambio llegue a V15. El commit
sigue siendo cosa tuya, para el historial.

**No edites el panel en V15**: la copia de `~/.local/share/panel-control` se
sobrescribe en el siguiente despliegue. El repo `bash_tools` de V15 no se usa
para el panel (por eso no se ensucia y `git pull` sigue funcionando allí).

## Qué se adapta solo a cada máquina

El código no tiene nada específico de R7 o V15; se adapta así:

- **Unidades que no existen se ocultan.** Las listas `REMOTE_ACCESS`,
  `SERVICES` e `INFO_ONLY` son las mismas en ambas, pero el panel pregunta a
  systemd y descarta las `not-found` (p.ej. Ollama, Herdr o Fabric en V15).
  Por eso hay dos túneles en la lista: `syncthing-tunnel-v15` (existe en R7)
  y `syncthing-tunnel-r7` (existe en V15).
- **Proyectos Compose cuyo `docker-compose.yml` no existe se ocultan** (p.ej.
  `sim`, que vive en `~/dev/terceros`, fuera de Syncthing).
- **Sin GPU NVIDIA o sin agent-reach**, sus tarjetas no aparecen.
- **Nombre de la máquina** (`hostname`) en la cabecera y el pie.
- **Enlaces**: el servidor los da como `http://localhost:<puerto>`. Si abres
  el panel de V15 desde R7, la página los reescribe a `http://IP_V15:<puerto>`
  para que no te lleven a R7 por error. Ojo: muchos de esos servicios solo
  escuchan en `localhost` de V15, así que el enlace solo abrirá si ese
  servicio también escucha en la red (la tabla "Puertos en uso" lo dice).

Para añadir algo que solo existe en una máquina basta con añadirlo a la
lista: en la otra no aparecerá.

## Configuración local de cada máquina

Lo que es distinto en cada máquina vive **fuera del repo**:

| | R7 | V15 |
|---|---|---|
| Código que ejecuta | el repo directamente | `~/.local/share/panel-control/` (copia) |
| Unidad | `panel-control.service` (copia manual de la del repo) | `panel-control.service` (la copia `deploy-v15.sh` desde `panel-control-v15.service`) |
| Variables de entorno | ninguna (valores por defecto: `127.0.0.1:8990`) | `~/.config/panel-control/env` |
| Despliegue | `panel-deploy-v15.{path,service,timer}` | — |

Variables que entiende `panel_server.py`:

| Variable | Por defecto | Para qué |
|---|---|---|
| `PANEL_HOST` | `127.0.0.1` | Dirección en la que escucha. `0.0.0.0` = todas. |
| `PANEL_PORT` | `8990` | Puerto. |
| `PANEL_ALLOW` | *(vacío)* | IPs o redes CIDR extra que pueden entrar, separadas por comas. La propia máquina siempre puede. |
| `PANEL_MACHINE` | `hostname` | Nombre que se muestra. |
| `PANEL_UNIT` | `panel-control.service` | Nombre de la unidad que sirve el panel (para identificarse en "Puertos en uso"). |

Plantilla del fichero de V15: [`panel-control.env.example`](panel-control.env.example).

## Seguridad

El panel no tiene contraseña y sus botones pueden parar SSH, Docker, etc.
Se protege por capas:

1. **IP del cliente** (`PANEL_ALLOW`): solo la propia máquina y R7.
2. **Cabecera `Host`**: solo IPs, `localhost` o el nombre de la máquina.
   Evita el *DNS rebinding* (una web cuyo dominio resuelve a tu IP para leer
   el panel desde tu navegador).
3. **Cabecera `Origin` en los POST**: los botones solo funcionan desde la
   propia página del panel. Evita que otra web abierta en tu navegador pulse
   los botones por ti (CSRF). Consecuencia: un `curl -X POST` a mano necesita
   `-H 'Origin: http://<host>:<puerto>'`.
4. **Firewall de V15** (UFW): regla que abre el 8990 solo a `IP_R7`.
5. **Listas blancas** de siempre: el panel solo toca las unidades, contenedores
   y proyectos de sus listas, y `sudo` solo para las unidades de
   `sudoers-panel-control`.

## Instalación desde cero

### R7 (maestra)

```bash
cd ~/dev/github/bash_tools/system_tools/panel_control
# Panel local (si no estaba): ver README.md, pasos 1 y 2
# Despliegue automático a V15
cp panel-deploy-v15.path panel-deploy-v15.service panel-deploy-v15.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now panel-deploy-v15.path panel-deploy-v15.timer
```

Requisito: `ssh v15` debe funcionar sin contraseña ni preguntas (clave SSH,
el mismo alias que usa el túnel de Syncthing).

### V15

```bash
# 1. Configuración local (IP de R7 en PANEL_ALLOW)
mkdir -p ~/.config/panel-control
cp panel-control.env.example ~/.config/panel-control/env   # y editar
chmod 600 ~/.config/panel-control/env

# 2. Desde R7: primer despliegue (copia código y unidad)
./deploy-v15.sh

# 3. En V15: habilitar el panel
systemctl --user daemon-reload
systemctl --user enable --now panel-control.service

# 4. En V15, con sudo: botones de servicios de sistema y firewall
sudo cp sudoers-panel-control /etc/sudoers.d/panel-control   # desde el repo de V15
sudo chmod 440 /etc/sudoers.d/panel-control
sudo visudo -c
sudo ufw allow from IP_R7 to any port 8990 proto tcp comment 'panel de control desde R7'
```

V15 tiene *lingering* activado (`loginctl show-user ion -p Linger` → `yes`),
así que el panel arranca con la máquina aunque no hayas iniciado sesión.

## Uso diario

| Quiero… | Comando (en R7) |
|---|---|
| Ver qué hizo el último despliegue | `journalctl --user -u panel-deploy-v15.service -n 20` |
| Forzar un despliegue ya | `systemctl --user start panel-deploy-v15.service` (o `./deploy-v15.sh`) |
| Ver cuándo toca el próximo reintento | `systemctl --user list-timers panel-deploy-v15.timer` |
| Pausar la propagación automática | `systemctl --user stop panel-deploy-v15.path panel-deploy-v15.timer` |
| Ver el estado del panel de V15 | `ssh v15 systemctl --user status panel-control` |
| Logs del panel de V15 | `ssh v15 journalctl --user -u panel-control -n 30` |

## Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| Desde R7 `http://IP_V15:8990` no carga | V15 apagado, cambió de IP o UFW bloquea | `ping IP_V15`; revisar la reserva en el router; `sudo ufw status` en V15 |
| `{"error": "cliente no permitido"}` | R7 entra con una IP que no está en `PANEL_ALLOW` (otra IP por DHCP, o por Tailscale) | Reservar la IP de R7 en el router, o añadirla a `~/.config/panel-control/env` en V15 y `systemctl --user restart panel-control` |
| `{"error": "cabecera Host no permitida"}` | Entras por un nombre DNS que no es el de la máquina | Usar la IP, o `PANEL_MACHINE`/nombre de la máquina |
| Botón → "Error: origen no permitido" | Petición POST que no viene de la página del panel | Normal para `curl`; ver Seguridad (3) |
| Botón de servicio de sistema → "sudo sin permiso" | Falta `/etc/sudoers.d/panel-control` en esa máquina | Paso 4 de la instalación de V15 |
| Cambio en R7 que no llega a V15 | El despliegue falló (no compila, V15 inaccesible) | `journalctl --user -u panel-deploy-v15.service -n 20` |
| Un servicio no aparece en V15 | No está instalado allí (se oculta a propósito) | Instalarlo en V15; aparece solo en el siguiente refresco |

## Si cambia algo de la red

- **Cambia la IP de V15**: nada que tocar en las máquinas; solo cambia la
  dirección que escribes en el navegador. Mejor evitarlo con la reserva.
- **Cambia la IP de R7**: actualiza `PANEL_ALLOW` en
  `~/.config/panel-control/env` de V15 y la regla de UFW, y reinicia el panel
  de V15.
- **Añadir una tercera máquina**: copiar `deploy-v15.sh` y las tres unidades
  `panel-deploy-v15.*` con otro nombre y `PANEL_DEPLOY_HOST=<alias ssh>`
  (variable que ya entiende el script), y repetir la instalación de V15 en
  ella.

## Ficheros

| Fichero | Dónde se instala | Papel |
|---|---|---|
| `panel_server.py` | R7: se ejecuta del repo · V15: copia en `~/.local/share/panel-control/` | Servidor del panel (el mismo en ambas) |
| `static/index.html` | Igual que el anterior | Página del panel |
| `panel-control.service` | R7: `~/.config/systemd/user/` | Unidad del panel en R7 |
| `panel-control-v15.service` | V15: `~/.config/systemd/user/panel-control.service` (lo copia `deploy-v15.sh`) | Unidad del panel en V15 |
| `panel-control.env.example` | V15: plantilla de `~/.config/panel-control/env` | Dirección, puerto e IPs permitidas |
| `deploy-v15.sh` | R7: se ejecuta del repo | Comprueba, copia y reinicia |
| `panel-deploy-v15.path` | R7: `~/.config/systemd/user/` | Lanza el despliegue al guardar |
| `panel-deploy-v15.service` | R7: `~/.config/systemd/user/` | Ejecuta `deploy-v15.sh` |
| `panel-deploy-v15.timer` | R7: `~/.config/systemd/user/` | Reintento cada 15 min |
| `sudoers-panel-control` | Ambas: `/etc/sudoers.d/panel-control` | Permiso sin contraseña para las unidades de la lista |
