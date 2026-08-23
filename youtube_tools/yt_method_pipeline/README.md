# yt_method_pipeline

Pipeline reanudable, 100% local (Ollama), que a partir de una o varias
fuentes de YouTube extrae y analiza los métodos de generar ingresos
explicados en sus vídeos:

1. **fetch** — resuelve una o varias entradas mezclables (canal, playlist,
   vídeo suelto, fichero de lista con `--list`, o `"titulo:..."` buscado vía
   `ytsearch`) a una lista de vídeos deduplicada por `video_id`, y descarga
   la transcripción de cada uno (`youtube-transcript-api`, con fallback a
   subtítulos de yt-dlp si falla o está bloqueado). Cada `meta.json` guarda
   su procedencia (`canal_nombre`/`canal_id` reales, `fuente_origen`,
   `fuente_detalle`, `resuelto_por_titulo`). Idempotente: si `transcript.txt`
   ya existe para un `video_id`, se salta — relanzar `fetch` nunca borra ni
   repite descargas, solo añade vídeos nuevos. `reannotate` rellena esos
   campos de procedencia en vídeos descargados antes de que existiera este
   campo, sin volver a bajar ninguna transcripción.
2. **classify** — filtra los vídeos descargados, quedándose solo con los que
   explican un método de negocio replicable (nada de entrevistas, noticias,
   documentales...). Ve el título + el principio de la transcripción, no solo
   el título — un vídeo titulado "El rentable negocio de..." puede ser una
   entrevista y no un tutorial. No borra `transcript.txt`/`meta.json`: si un
   vídeo se clasifica como excluido, solo se elimina su `method.json`/
   `embedding.json` (si existían) para que no aparezca en el análisis.
   Si no se ejecuta este paso, `extract` procesa todo sin filtrar.
3. **extract** — por cada transcripción no excluida, extracción estructurada
   por seis bloques de dimensiones (identificación, economía, requisitos y
   barreras de entrada, ejecución, credibilidad y riesgo, meta/fuente) vía LLM
   (proveedor configurable: Ollama local por defecto usando su modo de salida
   estructurada nativo, o Claude API con tool use y `tool_choice` forzado) +
   validación contra JSON Schema.
4. **index** — calcula el embedding de cada método sobre un resumen
   normalizado construido determinísticamente a partir del `method.json` ya
   validado (no sobre la transcripción cruda), para poder buscar por método
   semánticamente en vez de por coincidencia léxica.
5. **normalize** — capa derivada y no destructiva sobre los `method.json`:
   colapsa `canal_apalancamiento`, `mecanismo_valor`, `audiencia` y `categoria`
   a un vocabulario canónico corto (editable en `configs/normalization.json`),
   corrige nombres de herramientas, y calcula un escalar `potencial` con pesos
   declarados (no hardcodeados) en ese mismo config. Escribe
   `data/methods_norm.json` (añade campos `*_norm`, no borra los originales) y
   `data/normalization_report.html` — revísalo antes de fiarte de la rejilla
   de huecos del dashboard: si la cobertura es baja, completa los
   `_pendientes` del config y vuelve a lanzar `normalize`.
6. **dashboard** — genera un HTML autónomo (sin llamadas externas, ni a
   Claude ni a nadie — tipografías incrustadas incluidas) con seis vistas:
   **Expediente** (las respuestas de los 6 bloques por vídeo + potencial, con
   botones para exportar el estado actual del dashboard a Markdown o PDF),
   **Rejilla de huecos** (combinaciones normalizadas que ningún vídeo cubre —
   cada celda vacía lleva un `score_estimado` y su `n` de vídeos de apoyo,
   con aviso de baja evidencia; las combinaciones incompatibles declaradas en
   el config, o descartadas por inviables por el propio generador de ideas,
   se pintan como descartadas; panel "Top 50 huecos"; botón "Generar idea"
   que convierte una celda vacía en una propuesta de negocio concreta vía
   LLM — ver paso `idea-server`), **Similitud** (temática por embeddings, o
   ponderada por las facetas que tú elijas con sliders), **Combinador**
   (combinador de primitivos + comparador manual, ambos con "potencial
   operativo"), **Constructor de proyecto** (fijas tú mismo, faceta a
   faceta, la composición de un proyecto y ves en vivo qué respaldo tiene en
   el canal, con autocompletado y el mismo generador de ideas) y
   **Panorama** (seis gráficos de solo diagnóstico — mapas de calor
   mecanismo×canal y categoría×inversión, dispersión potencial/saturación
   coloreada por evidencia, barras de potencial y cuota por primitivo,
   concentración por categoría, y comparación por fuente — para leer el
   terreno antes de decidir). Si el corpus mezcla vídeos de más de una
   fuente (ver `fetch` con entradas mixtas), aparece un filtro global por
   fuente que recalcula Huecos/Similitud/Combinador/Constructor/Panorama
   sobre el subconjunto elegido; con una sola fuente no se muestra y nada
   cambia respecto al comportamiento anterior.
7. **idea-server** — servidor HTTP local (`localhost:8765`) que el botón
   "Generar idea" del dashboard llama por `fetch()`. Necesario porque un HTML
   abierto por `file://` no puede llamar a un LLM sin exponer credenciales en
   el propio código de la página (o, con Ollama, sin que el navegador hable
   directamente con tu servidor local). Usa el mismo `LLM_PROVIDER` que el
   resto del pipeline. El prompt (`prompts/generate_idea.md`) primero valida
   si las dos facetas son económicamente compatibles antes de redactar nada
   — si no lo son, devuelve un motivo y una alternativa en vez de una idea —
   y marca `confianza: "baja"` si alguna faceta se apoya en un solo vídeo.
   Cachea cada idea en `data/ideas/`, así que no se vuelve a llamar al LLM
   por la misma combinación.
8. **report** — agrega todos los `method.json`, genera distribuciones,
   contraste y propone combinaciones nuevas de primitivos (mecanismo de
   valor × canal de apalancamiento × audiencia) que no existan en el canal.

Cada paso guarda su resultado en disco y comprueba lo ya hecho antes de
volver a trabajar, así que se puede cortar y relanzar sin repetir descargas
ni llamadas al LLM.

## Instalación

```bash
cd yt_method_pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Por defecto usa un modelo local vía [Ollama](https://ollama.com) — asegúrate de
tenerlo corriendo (`ollama serve`) y el modelo descargado
(`ollama pull qwen3:14b`). Si prefieres Claude API, pon `LLM_PROVIDER=anthropic`
en `.env` y rellena `ANTHROPIC_API_KEY`.

## Uso

```bash
# Paso 1: descargar transcripciones (idempotente). Entradas mezclables:
# canal, playlist, vídeo suelto, --list fichero.txt, "titulo:..." (ytsearch)
.venv/bin/python cli.py fetch @NombreCanal
.venv/bin/python cli.py fetch @NombreCanal --limit 20
.venv/bin/python cli.py fetch @NombreCanal "https://youtu.be/XXXXXXXXXXX" --list otros.txt
.venv/bin/python cli.py fetch "titulo:texto a buscar" --title-channel @NombreCanal

# Rellena canal_nombre/fuente_origen en vídeos descargados antes de este campo
.venv/bin/python cli.py reannotate --channel-hint @NombreCanal

# Paso 2: filtrar vídeos que no sean métodos de negocio (entrevistas, etc.)
.venv/bin/python cli.py classify

# Paso 3: extraer método estructurado de cada transcripción pendiente
.venv/bin/python cli.py extract

# Paso 4: indexar (embedding) cada método ya extraído
.venv/bin/python cli.py index

# Búsqueda semántica sobre los métodos indexados
.venv/bin/python cli.py search "dropshipping con poca inversión inicial"
.venv/bin/python cli.py search "métodos que dependen de vender un curso" --top 3

# Paso 5: normalizar primitivos/categoría/herramientas y calcular 'potencial'
.venv/bin/python cli.py normalize
# revisa data/normalization_report.html (cobertura, pendientes, re-etiquetado),
# completa configs/normalization.json y relanza 'normalize' cuantas veces quieras.

# Dashboard local (Expediente, rejilla de huecos, similitud, combinador,
# constructor de proyecto, panorama)
.venv/bin/python cli.py dashboard
# abre data/dashboard.html directamente en el navegador — funciona sin
# conexión a internet salvo el botón "Generar idea" (rejilla de huecos y
# constructor de proyecto).

# Para que ese botón funcione: en OTRA terminal, déjalo corriendo mientras
# usas el dashboard. Usa el mismo LLM_PROVIDER que el resto del pipeline
# (Ollama por defecto, gratis y local; o Claude API si pones
# LLM_PROVIDER=anthropic y ANTHROPIC_API_KEY en .env)
.venv/bin/python cli.py idea-server

# Paso 6: agregación + informe (requiere que 'extract' esté completo)
.venv/bin/python cli.py report

# Toda la secuencia (fetch + classify + extract + index + report;
# 'normalize' y 'dashboard' quedan fuera porque quieres revisarlos a mano)
.venv/bin/python cli.py run @NombreCanal
```

Variables de entorno:

- `LLM_PROVIDER` — `ollama` (por defecto) o `anthropic`.
- `OLLAMA_HOST` — por defecto `http://localhost:11434`.
- `OLLAMA_MODEL` — por defecto `qwen3:14b`. Cualquier modelo con soporte de
  salida estructurada (`ollama show <modelo>` debe listar `tools` o
  `completion` + soporte de `format`) sirve; `qwen2.5:14b-instruct` es otra
  buena opción ya descargada.
- `OLLAMA_NUM_CTX` — contexto en tokens, por defecto `40960` (el máximo de
  qwen3:14b). Bájalo si tu GPU no tiene VRAM suficiente y el proceso se
  vuelve muy lento o se cae a CPU.
- `OLLAMA_EMBED_MODEL` — modelo de embeddings para el paso `index`/`search`,
  por defecto `qwen3-embedding:8b` (4096 dims, buen soporte de español). Se
  usa siempre vía Ollama, aunque `LLM_PROVIDER=anthropic` — Claude API no
  tiene endpoint de embeddings.
- `ANTHROPIC_API_KEY` / `CLAUDE_MODEL` — solo si `LLM_PROVIDER=anthropic`.
- `YT_COOKIES_FROM_BROWSER` — navegador del que leer cookies (`brave`,
  `firefox`, `chrome`...), útil si YouTube empieza a bloquear peticiones.
- `PIPELINE_MAX_RETRIES` / `PIPELINE_BACKOFF_BASE` — reintentos y backoff
  exponencial para llamadas a yt-dlp, transcript-api y al LLM.

## Generar borradores de post de LinkedIn

```bash
# Requiere dashboard.html + methods_norm.json ya generados.
# La primera vez: .venv/bin/pip install playwright && .venv/bin/playwright install chromium

.venv/bin/python scripts/generate_post.py --pestana huecos
```

`scripts/generate_post.py` calcula en Python (sobre `methods_norm.json` +
embeddings, nunca inventadas) el hallazgo más relevante de una pestaña del
dashboard, redacta el post vía la API de Anthropic (o `--provider ollama` si
la API no está disponible), y genera con Playwright una captura de página
completa de esa pestaña más una tarjeta social 1200×627. **No publica nada**
— deja `post.txt`, las imágenes y un `meta.json` trazable en
`data/linkedin_posts/<fecha>-<pestana>/` para que revises y subas a mano.

Flags: `--pestana` (obligatoria: `expediente`/`huecos`/`similitud`/
`combinador`/`constructor`/`panorama`), `--enfoque metodologia` (por
defecto, anonimiza canal y creadores) o `nombres_reales`, `--imagen
captura|tarjeta|ambas`, `--idioma es|en`, `--destacado "texto libre"` para
fijar tú la idea a resaltar, `--provider claude|ollama` (+
`--ollama-model`), `--salida` para la carpeta de destino. El prompt de
redacción es editable en `prompts/linkedin_post.md`.

## Estructura generada en `data/` (ignorada por git)

```
data/
├── channel.json
├── transcripts/
│   └── <titulo-slugificado>-<video_id>/
│       ├── transcript.txt
│       ├── meta.json
│       ├── classification.json
│       ├── method.json
│       └── embedding.json
├── logs/
│   ├── pipeline.log
│   └── no_transcript.log
├── methods.jsonl
├── methods_norm.json
├── normalization_report.html
├── ideas/
│   └── <eje_a>=<valor_a>__<eje_b>=<valor_b>.json
├── linkedin_posts/
│   └── <fecha>-<pestana>/
│       ├── post.txt
│       ├── captura.png
│       ├── tarjeta.png
│       └── meta.json
├── report.md
└── dashboard.html
```

`configs/normalization.json` (fuera de `data/`, **sí** va en git) es el mapa de
normalización editable a mano — ver el paso `normalize` arriba.

El nombre del directorio de cada vídeo lleva el `video_id` como sufijo
(no solo el título slugificado) para evitar colisiones entre vídeos con
títulos iguales o muy parecidos.

## Supuestos sobre el schema

El enunciado no fijaba los valores concretos de algunos campos enum; se
han definido así — ajusta `schemas/method_extraction.json` si no encajan:

- `tipo_ingreso`: `activo` | `semipasivo` | `pasivo`
- `economia.escalabilidad`: `baja` | `media` | `alta`
- `evidencia`: `pruebas_verificables` | `capturas_o_documentos` | `solo_afirmacion`
- `saturacion_competencia`: `baja` | `media` | `alta`
- `vende_algo.tipo`: `curso` | `mentoria` | `enlace_afiliado` | `herramienta_propia` | `ninguno` | `otro`
- `publico_objetivo.nivel`: `principiante` | `intermedio` | `avanzado`

Todos los campos enum aceptan también `null` cuando el dato no aparece en
la transcripción.
