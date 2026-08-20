# yt_method_pipeline

Pipeline reanudable, 100% local (Ollama), que a partir de un canal de YouTube
extrae y analiza los métodos de generar ingresos explicados en sus vídeos:

1. **fetch** — descarga transcripciones (yt-dlp para listar el canal,
   `youtube-transcript-api` para el texto con fallback a subtítulos de
   yt-dlp si falla o está bloqueado). Idempotente: si `transcript.txt` ya
   existe para un `video_id`, se salta — relanzar `fetch` nunca borra ni
   repite descargas, solo añade vídeos nuevos.
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
5. **dashboard** — genera un HTML autónomo (sin llamadas externas, ni a
   Claude ni a nadie — tipografías incrustadas incluidas) con una vista
   legible por vídeo de las respuestas de los 6 bloques, una matriz de
   correlación semántica entre métodos, un combinador interactivo de
   primitivos y un comparador manual de dos vídeos, ambos con una puntuación
   de "potencial operativo" (fórmula transparente, ver el propio dashboard).
6. **report** — agrega todos los `method.json`, genera distribuciones,
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
# Paso 1: descargar transcripciones de un canal (idempotente)
python cli.py fetch @NombreCanal
python cli.py fetch @NombreCanal --limit 20

# Paso 2: filtrar vídeos que no sean métodos de negocio (entrevistas, etc.)
python cli.py classify

# Paso 3: extraer método estructurado de cada transcripción pendiente
python cli.py extract

# Paso 4: indexar (embedding) cada método ya extraído
python cli.py index

# Búsqueda semántica sobre los métodos indexados
python cli.py search "dropshipping con poca inversión inicial"
python cli.py search "métodos que dependen de vender un curso" --top 3

# Dashboard local (vista por vídeo, correlación, combinador y comparador)
python cli.py dashboard
# abre data/dashboard.html directamente en el navegador — no depende de Claude
# ni de ningún otro servicio, funciona sin conexión a internet.

# Paso 5: agregación + informe (requiere que 'extract' esté completo)
python cli.py report

# Toda la secuencia (fetch + classify + extract + index + report)
python cli.py run @NombreCanal
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
├── report.md
└── dashboard.html
```

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
