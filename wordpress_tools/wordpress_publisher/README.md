# wp_publisher

Herramienta de línea de comandos para publicar artículos en WordPress de forma masiva y automatizada via REST API. Diseñada para flujos donde un modelo de IA genera artículos en local que deben subirse a WordPress con fechas distribuidas uniformemente.

Command-line tool to bulk-publish articles to WordPress automatically via REST API. Designed for workflows where a local AI model generates articles that need to be uploaded to WordPress with evenly distributed publication dates.

---

## Características / Features

- **Publicación y borradores** / **Publish and drafts**: sube artículos como `publish` o `draft` según convenga / upload articles as `publish` or `draft`
- **Modo espera** / **Wait mode**: monitoriza un directorio en bucle y publica en cuanto la IA genera nuevos archivos / watches a directory in a loop and publishes as soon as new files appear
- **Checkpoint automático** / **Auto checkpoint**: guarda el progreso en disco; si se interrumpe, retoma desde donde lo dejó / saves progress to disk and resumes from where it left off if interrupted
- **Reintentos con backoff exponencial** / **Exponential backoff retries**: maneja errores 500/502/503/504 y rate limiting (429) automáticamente / handles 500/502/503/504 errors and rate limiting (429) automatically
- **Gestión de fechas** / **Date management**: distribuye los posts en el tiempo (fecha base: hace 2 años, +2 días por artículo) / spreads posts over time (base date: 2 years ago, +2 days per article)
- **Tags automáticos** / **Automatic tags**: detecta el tema del artículo y crea o reutiliza los tags en WordPress / detects the article topic and creates or reuses tags in WordPress
- **Deduplicación** / **Deduplication**: comprueba si el post ya existe antes de crearlo / checks if the post already exists before creating it
- **Diagnóstico integrado** / **Built-in diagnostics**: verifica credenciales, conexión, permisos y capacidad del servidor sin publicar nada / verifies credentials, connection, permissions and server capacity without publishing anything
- **Opciones CLI flexibles** / **Flexible CLI options**: límite de artículos, delay configurable, directorio por argumento / article limit, configurable delay, directory override

---

## Requisitos / Requirements

```bash
pip install requests python-dotenv
```

---

## Configuración / Configuration

Crea un archivo `.env` en el mismo directorio que el script / Create a `.env` file in the same directory as the script:

```env
WP_URL=https://your-domain.com/wp-json/wp/v2/posts
WP_TAGS_URL=https://your-domain.com/wp-json/wp/v2/tags
WP_USER=your_username
WP_PASSWORD=xxxx xxxx xxxx xxxx
ARTICULOS_DIR=/absolute/path/to/your/articles
```

La contraseña debe ser una **contraseña de aplicación** de WordPress, no la contraseña del usuario /
The password must be a WordPress **application password**, not the user login password:
`WordPress Admin → Users → Your profile → Application Passwords`

---

## Uso / Usage

```bash
python3 wp_publisher.py [COMMAND] [OPTIONS]
```

### Comandos / Commands

| Comando / Command | Descripción / Description |
|-------------------|--------------------------|
| `publish` | Publica los artículos pendientes (por defecto) / Publish pending articles (default) |
| `draft` | Sube los artículos como borradores / Upload articles as drafts |
| `wait` | Monitoriza el directorio en bucle y publica en cuanto aparecen archivos nuevos / Watch directory in a loop and publish as soon as new files appear |
| `update-dates` | Recorre los posts existentes y corrige sus fechas / Update publication dates of existing posts |
| `diagnose` | Comprueba variables de entorno, conexión, autenticación y permisos / Check env variables, connection, authentication and permissions |
| `verify` | Muestra el número de posts por estado / Show post count by status (publish, draft, future…) |
| `reset` | Borra el checkpoint para empezar desde cero / Delete checkpoint to start from scratch |
| `help` | Muestra la ayuda completa / Show full help |

### Opciones / Options

| Opción / Option | Descripción / Description |
|-----------------|--------------------------|
| `--dir PATH` | Directorio de artículos (sobreescribe `ARTICULOS_DIR` del .env) / Articles directory (overrides `ARTICULOS_DIR` from .env) |
| `--limit N` | Procesar como máximo N artículos en esta ejecución / Process at most N articles in this run |
| `--delay N` | Segundos de espera entre requests (por defecto: 8) / Seconds between requests (default: 8) |

### Ejemplos / Examples

```bash
# Publicar todos los artículos pendientes / Publish all pending articles
python3 wp_publisher.py publish

# Subir como borradores para revisar antes de publicar / Upload as drafts to review before publishing
python3 wp_publisher.py draft

# Esperar a que un modelo de IA genere artículos y publicarlos en cuanto aparezcan
# Wait for an AI model to generate articles and publish them as soon as they appear
python3 wp_publisher.py wait

# Probar con los primeros 10 artículos y poco delay / Test with the first 10 articles and low delay
python3 wp_publisher.py publish --limit 10 --delay 3

# Publicar desde un directorio distinto al del .env / Publish from a directory other than the one in .env
python3 wp_publisher.py publish --dir /path/to/other/articles

# Actualizar solo las fechas de posts ya existentes / Update only the dates of existing posts
python3 wp_publisher.py update-dates

# Verificar que todo está bien antes de lanzar un proceso largo / Verify everything is fine before a long run
python3 wp_publisher.py diagnose

# Empezar desde cero ignorando el progreso anterior / Start from scratch ignoring previous progress
python3 wp_publisher.py reset && python3 wp_publisher.py publish
```

---

## Flujo de trabajo con IA local / Local AI workflow

El caso de uso principal es el siguiente: un modelo local (Ollama, etc.) genera artículos en un directorio mientras `wp_publisher` los sube en paralelo.

The main use case: a local model (Ollama, etc.) generates articles into a directory while `wp_publisher` uploads them in parallel.

```
[AI Model] → generates .md → [directory] ← watches → [wp_publisher wait]
                                                               ↓
                                                      WordPress REST API
```

El modo `wait` comprueba el directorio cada 10 segundos. Cuando detecta archivos que no están en el checkpoint, los procesa y vuelve a esperar. Se detiene con `Ctrl+C`.

The `wait` mode checks the directory every 10 seconds. When it detects files not recorded in the checkpoint, it processes them and goes back to waiting. Stop it with `Ctrl+C`.

---

## Distribución de fechas / Date distribution

Los posts se distribuyen automáticamente en el tiempo para que no aparezcan todos publicados el mismo día.

Posts are automatically spread over time so they don't all appear published on the same day.

- **Fecha base / Base date**: hace 2 años desde la ejecución / 2 years before the current date
- **Incremento / Increment**: +2 días por cada artículo según su posición / +2 days per article based on its position
- Si un post ya existe con una fecha distinta, la actualiza para mantener la coherencia / If a post already exists with a different date, it is updated to keep consistency

---

## Tags automáticos / Automatic tags

El script detecta el tema del artículo leyendo el título y el inicio del contenido / The script detects the article topic by reading the title and the beginning of the content:

| Tag | Keywords |
|-----|----------|
| `data` | data, dataset, database, sql, csv, json |
| `linux` | linux, bash, shell, command, terminal, grep, sed, awk |
| `pandas` | pandas, dataframe, series, groupby, merge |
| `bash` | bash, script, shell |
| `python` | python, django, flask, pip, virtualenv |
| `machine-learning` | machine learning, model, training, algorithm, neural |
| `deep-learning` | deep learning, tensorflow, keras, pytorch, cnn, lstm |
| `web` | html, css, javascript, react, vue, api, rest |

Los tags se crean en WordPress si no existen, y se reutilizan si ya están creados (caché en memoria durante la ejecución) / Tags are created in WordPress if they don't exist, and reused if they already exist (in-memory cache during the run).

---

## Solución de problemas / Troubleshooting

| Error | Causa / Cause | Solución / Solution |
|-------|---------------|---------------------|
| `Missing variables in .env` | Archivo `.env` incompleto o no encontrado / Incomplete or missing `.env` file | Ejecuta `diagnose` / Run `diagnose` |
| `401 Unauthorized` | Credenciales incorrectas / Wrong credentials | Usa contraseña de aplicación / Use an application password |
| `403 Forbidden` | Permisos insuficientes / Insufficient permissions | El usuario necesita rol Editor o Admin / User needs Editor or Admin role |
| `500` persistente / persistent | PHP sin memoria, plugin conflictivo / Low PHP memory, conflicting plugin | Ejecuta `diagnose` para más detalle / Run `diagnose` for details |
| Directory not found | Ruta relativa o con `~/` / Relative path or `~/` | Usa ruta absoluta / Use absolute path (`/home/…`) |

---

## Seguridad / Security

- Añade `.env` a `.gitignore` para no subir credenciales al repositorio / Add `.env` to `.gitignore` to avoid committing credentials
- Usa siempre contraseñas de aplicación, nunca la contraseña principal de WordPress / Always use application passwords, never the main WordPress login password
- El checkpoint (`.wp_publisher_checkpoint.json`) no contiene credenciales, pero tampoco es necesario versionarlo / The checkpoint file contains no credentials, but there is no need to version it either
