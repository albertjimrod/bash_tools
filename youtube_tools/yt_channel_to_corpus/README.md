# yt_channel_to_corpus

Pipeline completo para extraer las transcripciones de un canal de YouTube y consultarlas mediante un sistema RAG local con Ollama.

---

## ¿Qué hace?

1. **Descarga** las transcripciones de todos los vídeos de un canal
2. **Genera** un corpus Markdown unificado (`knowledge_corpus.md`)
3. **Arranca** un RAG local donde puedes hacer preguntas en lenguaje natural sobre el contenido del canal

---

## Comandos

```bash
# ─── EXTRACCIÓN + RAG (primera vez) ──────────────────────────────────────────

# Canal con handle
./yt_channel_to_corpus.sh @NombreCanal -l es -b brave

# Canal con URL completa
./yt_channel_to_corpus.sh "https://www.youtube.com/@NombreCanal" -l es -b brave

# Limitar a los últimos N vídeos
./yt_channel_to_corpus.sh @NombreCanal -l es -n 50

# Directorio de salida personalizado (para tener varios canales separados)
./yt_channel_to_corpus.sh @NombreCanal -l es -o corpus_NombreCanal


# ─── USAR CORPUS YA DESCARGADO ───────────────────────────────────────────────

# Detecta automáticamente el corpus y pregunta si reutilizarlo
./yt_channel_to_corpus.sh @NombreCanal

# Forzar uso del corpus existente sin preguntar
./yt_channel_to_corpus.sh @NombreCanal -u

# Con directorio concreto
./yt_channel_to_corpus.sh @NombreCanal -u -o corpus_NombreCanal


# ─── SOLO RAG (sin pasar por el script de extracción) ────────────────────────

python rag_youtube.py qwen2.5:14b-instruct-q5_K_M corpus_NombreCanal/knowledge_corpus.md


# ─── DENTRO DEL RAG ──────────────────────────────────────────────────────────

salir    # cerrar el RAG
```

Al terminar la descarga, el script lista los modelos Ollama disponibles, pide que elijas uno y arranca el RAG directamente.

---

## Opciones

| Opción | Descripción | Por defecto |
|--------|-------------|-------------|
| `-l, --lang` | Idioma preferido de las transcripciones | `es` |
| `-n, --limit` | Número máximo de vídeos a procesar | todos |
| `-o, --output` | Directorio de salida del corpus | `channel_corpus` |
| `-b, --browser` | Navegador del que leer cookies (`brave`, `firefox`, `chrome`…) | `brave` |
| `-u, --use-existing` | Usar el corpus ya generado, saltar la descarga | — |

---

## Cómo funciona por dentro

### Paso 1 — Extracción de URLs

`yt-dlp` lista todos los vídeos del canal y guarda sus URLs en `channel_corpus/urls/`.

### Paso 2 — Descarga de transcripciones

Para cada vídeo, `youtube-transcript-api` descarga la transcripción directamente desde la API de YouTube. Intenta primero el idioma preferido; si no existe, coge cualquier otro disponible.

Las cookies del navegador (vía `rookiepy`) se pasan en las peticiones para evitar bloqueos de IP por parte de YouTube.

### Paso 3 — Generación del corpus

Todos los textos se unen en un único archivo `knowledge_corpus.md` con una sección por vídeo.

### Paso 4 — RAG

`rag_youtube.py` carga el corpus, lo divide en fragmentos, genera embeddings con `nomic-embed-text` y los almacena en ChromaDB. Después abre un bucle interactivo: escribes una pregunta, el sistema recupera los fragmentos más relevantes y el LLM genera una respuesta.

```
Tu pregunta
    ↓
Búsqueda semántica en ChromaDB (nomic-embed-text)
    ↓
Top 6 fragmentos más relevantes
    ↓
LLM Ollama (el modelo que elijas) → Respuesta
```

---

## Estructura de archivos generados

```
channel_corpus/               ← ignorado por git (datos regenerables)
├── urls/
│   ├── channel_urls.txt
│   └── channel_urls_dates.txt
├── subs/
│   └── VIDEO_ID.txt          ← transcripción de cada vídeo
└── knowledge_corpus.md       ← corpus final (entrada del RAG)

chroma_yt_db/                 ← base vectorial (se regenera en cada ejecución)
```

---

## Dependencias

```bash
pip install yt-dlp youtube-transcript-api rookiepy secretstorage
pip install langchain langchain-community langchain-ollama langchain-core chromadb
```

Modelos Ollama necesarios:
```bash
ollama pull nomic-embed-text   # para embeddings (obligatorio)
ollama pull qwen2.5:14b-instruct-q5_K_M  # o el LLM que prefieras
```

Entorno recomendado: `conda activate rag_gpu` (tiene todo instalado).

---

## Solución de problemas

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `❌ No se extrajeron URLs` | Canal mal escrito o privado | Verificar el handle en YouTube; también puedes pasar la URL completa |
| Muchos "Sin transcripción disponible" | IP bloqueada por demasiadas peticiones | Esperar 1-2 horas y reintentar |
| `rookiepy no disponible` | Librería no instalada | `pip install rookiepy` |
| `model not found` en Ollama | Nombre de modelo incorrecto | Ejecutar `ollama list` para ver los nombres exactos |
| Embeddings lentos | `nomic-embed-text` no descargado | `ollama pull nomic-embed-text` |

### Sobre las cookies

YouTube bloquea IPs con muchas peticiones anónimas. El script carga las cookies de tu navegador automáticamente con `rookiepy`. **El navegador debe tener YouTube abierto o haber iniciado sesión previamente.**

Si usas Brave y el script no encuentra las cookies, prueba cerrando Brave antes de ejecutar.

### Sobre yt-dlp

El script comprueba al inicio si hay una versión más nueva disponible en PyPI. Si la hay, avisa y pide confirmación. Para actualizar:

```bash
pip install -U yt-dlp
```

---

## Archivos del proyecto

| Archivo | Función |
|---------|---------|
| `yt_channel_to_corpus.sh` | Script principal: extracción + arranque del RAG |
| `rag_youtube.py` | Sistema RAG: indexación y preguntas |

---

## Autor

Alberto Jiménez — [GitHub](https://github.com/albertjimrod)
