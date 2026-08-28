# CONTEXT — bash_tools

Documento de retoma. Destilado del repo a 2026-08-28. Rama `main`.

## 1. Qué es

Monorepo-taller personal de scripts de automatización (Bash + Python) del autor
(Alberto Jiménez / `albert@datablogcafe.com`), organizados por categoría. Cada
herramienta vive en su propio directorio con README propio y se usa de forma
independiente; no hay un producto único ni un runtime común. El hilo conductor
es la automatización local con IA (Ollama) para tareas de entornos Conda,
transcripciones de YouTube, publicación en WordPress y control del sistema.

## 2. Stack

- **Lenguajes:** Bash 4+ y Python 3.10+ (sintaxis de tipos moderna `str | None`).
- **IA:** Ollama local como motor por defecto de todo lo que usa LLM
  (extracción, embeddings, clasificación, organización de ficheros,
  generación de artículos). Claude API (`anthropic`) queda como alternativa
  opcional vía `LLM_PROVIDER=anthropic`.
- **Dependencias Python:** no hay fichero central. El único `requirements.txt`
  está en `youtube_tools/yt_method_pipeline/` (`yt-dlp`, `youtube-transcript-api`,
  `anthropic`, `httpx`, `jsonschema`, `python-dotenv`, `secretstorage`,
  `playwright`). `wordpress_tools` usa `requests` + `python-dotenv`.
  `system_tools/panel_control` usa **solo librería estándar** (`http.server`).
- **Herramientas externas:** `yt-dlp`, `conda`/`miniconda`, `docker` +
  `docker compose`, `systemd` (unidades de sistema y de usuario), `fabric`.
- **Despliegue:** ninguno. Todo corre en la máquina local del autor. El panel
  de control escucha solo en `127.0.0.1`. No hay CI (`.github/` solo tiene un
  asset de imagen).

## 3. Arquitectura

Directorios de primer nivel = categorías independientes:

- **`conda_tools/`** (~13 scripts): exportar/importar entornos, comparadores,
  `conda_env_manager`, `conda_ai_analyzer` (analiza cada entorno con Ollama),
  `conda_cleaner_pro`, `install_manager`, etc.
- **`youtube_tools/`** (7 dirs): utilidades de subtítulos/corpus
  (`yt_simple_v2`, `make_corpus`, `yt_channel_to_corpus`, `youtube_pipeline`,
  `full_pipeline`, `debug_video`) y la pieza más desarrollada,
  **`yt_method_pipeline/`**: pipeline reanudable e idempotente de 8 pasos
  (`fetch` → `classify` → `extract` → `index` → `normalize` → `dashboard` →
  `idea-server` → `report`). CLI en `cli.py`, lógica en `pipeline/`, prompts en
  `prompts/`, JSON Schema en `schemas/`, config editable en `configs/`
  (vocabulario de normalización y pesos de `potencial`). Salida: HTML de
  dashboard autónomo con 6 vistas (Expediente, Rejilla de huecos, Similitud,
  Combinador, Constructor de proyecto, Panorama) + `idea-server` HTTP local
  (`localhost:8765`) para el botón "Generar idea". Cada paso persiste en `data/`
  y comprueba lo ya hecho antes de rehacer.
- **`git_tools/`**: `buscar_git` (localiza repos), `git-find-commit`.
- **`utils/`**: `analize_text`, `backup_inventario`, `compare_files`,
  `detect_openwebui`, `direcciones_unicas`, `user_packages`.
- **`wordpress_tools/`**: `wordpress_publisher/wp_publisher.py` (publicación
  masiva vía REST API con checkpoint, reintentos con backoff, deduplicación,
  reparto de fechas, tags automáticos, modo espera) y `generar_articulos/`
  (genera borradores con IA local; carpetas `00_EDA_procesado*` con datos).
- **`organize_with_ai/`**: organizador de ficheros con Ollama
  (`qwen2.5:14b-instruct-q5_K_M`), aprobación interactiva, nunca borra.
- **`system_tools/panel_control/`** (lo más reciente): web local en
  `127.0.0.1:8990` (stdlib) para ver/activar accesos remotos, servicios
  systemd (sistema y usuario), contenedores Docker, proyectos Docker Compose y
  estado del sistema. Incluye `fabric.service`, `herdr.service`,
  `panel-control.service` y una regla `sudoers-panel-control` restringida solo
  a los servicios concretos.

## 4. Decisiones clave

- **IA local (Ollama) por defecto, no API de pago.** Motivo: coste cero y no
  depender de una cuota externa que se agota a mitad de una tanda de ~100
  vídeos (pasó). Claude API se mantiene solo como fallback conmutable.
- **`yt_method_pipeline` reanudable y no destructivo.** Cada paso escribe a
  disco y detecta trabajo previo; `fetch` es idempotente por `video_id`;
  `normalize` añade campos `*_norm` sin tocar los originales; los pesos de
  `potencial` viven en config, no hardcodeados. Dashboard = HTML autónomo (sin
  llamadas externas, tipografías incrustadas). `idea-server` existe porque un
  HTML abierto por `file://` no puede llamar a un LLM sin exponer credenciales.
- **venv con ruta explícita `.venv/bin/python`.** Motivo: el `yt-dlp` del
  sistema (snap) está sandboxed y no lee cookies del navegador; y es fácil
  tener un entorno conda con el mismo nombre que la carpeta que enmascara al
  venv real.
- **panel_control minimalista y defensivo.** Solo stdlib; bind a `127.0.0.1`;
  sudoers acotado a servicios concretos (nunca sudo general); firewall,
  actualizaciones y snapd son "solo información" sin botón para no dejar la
  máquina sin red/sesión; puertos y servicios expuestos deliberadamente **no**
  se documentan en el repo. Unidades Herdr/Fabric son `static` (no arrancan
  al iniciar sesión, solo con el botón). Proyectos Compose se controlan por
  nombre de proyecto (`-p`), no por fichero, para no mezclar stacks que
  comparten carpeta (caso `umami` / `intellisynthprice`).
- **`fabric.service` fijado a `127.0.0.1:8099`.** El puerto por defecto `:8080`
  escucha en todas las interfaces sin autenticación y choca con openwebui.
- **Alternativa descartada:** no se centralizan dependencias ni empaquetado
  común; cada herramienta se mantiene autónoma con su README.

## 5. Estado actual

**Funciona:** cada herramienta es usable de forma independiente con su README.
`yt_method_pipeline` es la más completa (8 pasos + dashboard de 6 vistas +
`idea-server` + generador de post de LinkedIn). `panel_control` operativo y con
soporte reciente para servicios de usuario y proyectos Docker Compose.

**Ramas:** solo `main` es real. `main` está **1 commit por delante de
`origin/main`** (sin push). Existen ramas y ficheros basura de Syncthing:
`main.sync-conflict-*` (local y en origin) y varios
`*.sync-conflict-20260701-*.md/.sh` sin rastrear en la raíz,
`wordpress_publisher/` y `yt_channel_to_corpus/`.

**Cambios sin commitear (relevantes):**

- `system_tools/panel_control/panel_server.py` + `static/index.html`: nueva
  sección "Proyectos Docker Compose" (`/api/compose/toggle`, `up -d`/`down`
  por `-p`, timeout 600s), servicios de usuario Syncthing + túnel SSH +
  Fabric, y refactor del front (render desde `lastData`, helper `toggleButton`).
  `README.md` del panel actualizado. `fabric.service` nuevo sin rastrear.
- `wordpress_tools/wordpress_publisher/wp_publisher.py`: **⚠️ SEGURIDAD** — el
  diff sin commitear sustituye los defaults vacíos por credenciales reales
  hardcodeadas (URL, usuario y **contraseña de aplicación de WordPress en
  claro**) y una ruta absoluta local. No debe commitearse así; la contraseña
  debería rotarse. PENDIENTE DE CONFIRMAR si ese valor se ha expuesto en algún
  sitio ya.
- ~20 scripts `.sh` marcados como modificados pero **solo por pérdida del bit
  de ejecución** (`100755` → `100644`), contenido intacto. Probablemente
  efecto colateral de Syncthing; conviene restaurar permisos en vez de
  commitear la regresión.
- Borrados sin commitear en `youtube_tools/yt_channel_to_corpus/channel_corpus/`
  (2 ficheros de subtítulos + `urls/channel_urls.txt`, 154 líneas). PENDIENTE
  DE CONFIRMAR si el borrado es intencionado.
- Otros sin rastrear: `wordpress_publisher.py` (¿duplicado/renombrado de
  `wp_publisher.py`?), `conda_tools/conda_finder/import requestes.py` (fichero
  de prueba con typo), `wordpress_tools/generar_articulos/00_EDA_procesado/` y
  `00_EDA_procesado (Copiar)/`, `system_tools/panel_control/fabric.service`.
- `migration_log_20260205_180455.txt` en la raíz: registro de una migración
  previa de estructura (5 feb 2026).

**No existen** `DECISIONS.md`, `TODO.md` ni `JOURNAL/`. Documentación =
`README.md` raíz + README por herramienta + `yt_method_pipeline/MANUAL.md`.

## 6. Próximos pasos (priorizados)

1. **Seguridad:** quitar las credenciales hardcodeadas de `wp_publisher.py`
   (volver a `os.getenv(..., "")` + `.env`) y **rotar la contraseña de
   aplicación de WordPress** expuesta en el working tree.
2. **Restaurar el bit de ejecución** de los ~20 `.sh` (`chmod +x` /
   `git checkout -- <archivos>`) para no commitear la pérdida de permisos.
3. **Limpiar Syncthing:** borrar los ficheros `*.sync-conflict-*` y las ramas
   `main.sync-conflict-*` (local y `origin`); revisar por qué Syncthing toca
   el `.git`.
4. **Revisar borrados** de `yt_channel_to_corpus/channel_corpus/` y decidir si
   commitear o revertir.
5. **Triage de sin-rastrear:** aclarar `wordpress_publisher.py` vs
   `wp_publisher.py`; decidir `.gitignore` para `00_EDA_procesado*/` y
   `__pycache__/`; borrar `conda_finder/import requestes.py`.
6. **Commit + push** de los cambios legítimos del panel de control
   (server + html + README + `fabric.service`) y del commit local pendiente.
7. Opcional: añadir `TODO.md` / `DECISIONS.md` en la raíz para no depender de
   este documento.
