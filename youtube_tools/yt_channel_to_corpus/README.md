# yt_channel_to_corpus

Extrae transcripciones de todos los vídeos de un canal de YouTube y genera un único archivo Markdown (`knowledge_corpus.md`) listo para usar como base de un sistema RAG.

Resultado real: **152/154 vídeos** con transcripción en una sola ejecución.

---

## Uso

```bash
# Básico (Brave, español, todos los vídeos)
./yt_channel_to_corpus.sh @NombreCanal

# Con opciones
./yt_channel_to_corpus.sh @NombreCanal -l es -n 50 -b firefox

# Directorio de salida personalizado
./yt_channel_to_corpus.sh @NombreCanal -l es -o mi_corpus
```

## Opciones

| Opción | Descripción | Por defecto |
|--------|-------------|-------------|
| `-l, --lang` | Idioma preferido (`es`, `en`, …) | `es` |
| `-n, --limit` | Limitar número de vídeos | todos |
| `-o, --output` | Directorio de salida | `channel_corpus` |
| `-b, --browser` | Navegador para cookies (`brave`, `firefox`, `chrome`, `chromium`, `edge`) | `brave` |
| `-h, --help` | Mostrar ayuda | — |

---

## Arquitectura

El script combina dos herramientas con responsabilidades distintas:

| Herramienta | Función |
|-------------|---------|
| `yt-dlp` | Extrae la lista de URLs del canal (paso 1) |
| `youtube-transcript-api` | Descarga las transcripciones (paso 2) |
| `rookiepy` | Lee las cookies del navegador y las pasa a las peticiones |

Esta separación es clave: `youtube-transcript-api` accede directamente a la API de transcripciones de YouTube **sin necesitar resolver formatos de vídeo**, lo que evita el n-challenge de YouTube que bloquea a yt-dlp.

---

## Flujo de ejecución

```
PASO 1 — yt-dlp extrae URLs de todos los vídeos del canal
PASO 2 — Por cada vídeo:
          1. Intentar transcripción en idioma preferido
          2. Si no existe, coger cualquier idioma disponible
          (via youtube-transcript-api + cookies de Brave/Firefox)
PASO 3 — Unir todos los .txt en knowledge_corpus.md con tabla de contenidos
```

Salida:
```
channel_corpus/           ← ignorado por git (datos regenerables)
├── urls/
│   └── channel_urls.txt
├── subs/
│   └── VIDEO_ID.txt      ← una transcripción por vídeo
└── knowledge_corpus.md   ← corpus final para el RAG
```

---

## ⚠️ Requisitos críticos

### 1. yt-dlp actualizado

El script comprueba automáticamente si hay una versión más nueva en PyPI al arrancar:

```
✅ Versión al día (2026.03.17). OK.
```

Si hay versión más nueva:

```
┌─────────────────────────────────────────────────────┐
│  ⚠️  AVISO: hay una versión más nueva en PyPI        │
│  Instalada:  2026.03.17                             │
│  Disponible: 2026.06.01                             │
│  Actualiza:  pip install -U yt-dlp                  │
└─────────────────────────────────────────────────────┘
¿Continuar de todas formas? [s/N]:
```

Actualizar antes de cada uso o al menos una vez al mes. YouTube cambia su API con frecuencia.

### 2. Cookies del navegador (obligatorio)

YouTube bloquea IPs con demasiadas peticiones anónimas. El script carga automáticamente las cookies de tu navegador mediante `rookiepy`, sin necesitar exportarlas manualmente.

**El navegador debe tener una sesión activa en YouTube** (no hace falta estar logado).

> Si el script dice `⚠️ rookiepy no disponible`, instala con `pip install rookiepy`.

---

## Dependencias

```bash
pip install -U yt-dlp
pip install youtube-transcript-api
pip install rookiepy
```

O dentro de tu entorno conda:

```bash
conda activate jupyterlab_new   # o prospector
pip install -U yt-dlp youtube-transcript-api rookiepy
```

**Versiones probadas:**
- `yt-dlp 2026.03.17`
- `youtube-transcript-api` (última versión pip)
- `rookiepy` (última versión pip)
- Python 3.11

---

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| Muchos "Sin transcripción disponible" | IP bloqueada por YouTube | Esperar 1-2 h y reintentar con cookies cargadas |
| `⚠️ rookiepy no disponible` | rookiepy no instalado | `pip install rookiepy` |
| `❌ yt-dlp no instalado` | yt-dlp ausente del entorno | `pip install -U yt-dlp` |
| `❌ youtube-transcript-api no instalado` | Librería ausente | `pip install youtube-transcript-api` |
| 0 URLs extraídas | Canal mal escrito o privado | Verificar `@NombreCanal` en YouTube |
| Cookies no cargan | Navegador incorrecto | Cambiar con `-b firefox` o `-b chrome` |

### Bloqueo de IP

YouTube bloquea temporalmente IPs que hacen demasiadas peticiones seguidas (habitual al hacer pruebas). Síntomas:

- Todos los vídeos devuelven "Sin transcripción disponible"
- El `list()` funciona pero el `fetch()` falla con `IpBlocked`

Solución: esperar 1-2 horas y volver a ejecutar. Con cookies cargadas correctamente el bloqueo es mucho menos frecuente.

---

## Integración con RAG (Ollama)

```bash
cd ~/projects/RAG_Agent/rag_corpus_procesador
python rag_corpus_procesador.py
# → selecciona channel_corpus/knowledge_corpus.md
# → elige modelo: qwen2.5:14b (calidad) o mistral (velocidad)
```

Comandos disponibles dentro del RAG: `fechas`, `validacion`, `fuentes`, `debug`, `ayuda`, `salir`.

---

## Autor

Alberto Jiménez — [GitHub](https://github.com/albertjimrod)
