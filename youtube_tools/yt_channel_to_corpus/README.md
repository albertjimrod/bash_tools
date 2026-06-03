# yt_channel_to_corpus

Extrae subtítulos de todos los vídeos de un canal de YouTube y genera un único archivo Markdown (`knowledge_corpus.md`) listo para usar como base de un sistema RAG.

---

## ⚠️ REQUISITOS CRÍTICOS — LEE ESTO ANTES DE EJECUTAR

Hay dos condiciones sin las cuales el script falla silenciosamente (descarga 0 transcripciones sin dar error claro):

### 1. yt-dlp debe estar actualizado

YouTube cambia su API interna con mucha frecuencia. Una versión de yt-dlp con más de 30 días de antigüedad puede:
- No poder descifrar las URLs de vídeo (`nsig extraction failed`)
- Ser bloqueada como bot
- Descargar archivos de subtítulos vacíos

**El script comprueba la fecha de versión automáticamente** al arrancar y avisa si tiene más de 30 días:

```
┌─────────────────────────────────────────────────────┐
│  ⚠️  AVISO: yt-dlp tiene 47 días sin actualizar     │
│  Actualiza con:  pip install -U yt-dlp              │
└─────────────────────────────────────────────────────┘
¿Continuar de todas formas? [s/N]:
```

**Actualizar:**
```bash
pip install -U yt-dlp
```

**Regla práctica:** actualiza yt-dlp antes de cada uso o al menos una vez al mes.

---

### 2. Las cookies del navegador son obligatorias

YouTube exige autenticación para confirmar que no eres un bot. Sin cookies, el script obtiene el error:

```
Sign in to confirm you're not a bot.
```

El script pasa automáticamente las cookies del navegador que le indiques (por defecto: Firefox). **El navegador debe tener una sesión activa en YouTube** (no hace falta estar logado, pero sí haber visitado YouTube).

**Navegadores soportados:** `firefox`, `chrome`, `chromium`, `brave`, `edge`

Para usar un navegador distinto a Firefox:
```bash
./yt_channel_to_corpus.sh @NombreCanal -b chrome
```

> **Nota:** Cierra el navegador o al menos la pestaña activa de YouTube si el script da error de acceso a cookies. Algunos navegadores bloquean el acceso mientras están abiertos.

---

## Uso

```bash
# Básico (Firefox, inglés, todos los vídeos)
./yt_channel_to_corpus.sh @NombreCanal

# Canal en español con Chrome, limitado a 50 vídeos
./yt_channel_to_corpus.sh @NombreCanal -l es -n 50 -b chrome

# Directorio de salida personalizado
./yt_channel_to_corpus.sh @NombreCanal -l es -o mi_corpus
```

## Opciones

| Opción | Descripción | Por defecto |
|--------|-------------|-------------|
| `-l, --lang` | Idioma de subtítulos (`en`, `es`, …) | `en` |
| `-n, --limit` | Limitar número de vídeos | todos |
| `-o, --output` | Directorio de salida | `channel_corpus` |
| `-b, --browser` | Navegador para cookies | `firefox` |
| `-h, --help` | Mostrar ayuda | — |

---

## Flujo completo

```
PASO 1 — Extrae URLs de todos los vídeos del canal
PASO 2 — Por cada vídeo, intenta descargar subtítulos:
          1º idioma solicitado → 2º español → 3º cualquier idioma
PASO 3 — Une todos los .txt en knowledge_corpus.md con tabla de contenidos
```

La salida queda así:
```
channel_corpus/
├── urls/
│   └── channel_urls.txt      # lista de URLs del canal
├── subs/
│   └── Título del vídeo.txt  # transcripción limpia por vídeo
└── knowledge_corpus.md       # corpus final para el RAG
```

---

## Requisitos técnicos

- Bash 4.0+
- `yt-dlp` actualizado: `pip install -U yt-dlp`
- Navegador con sesión en YouTube (Firefox por defecto)

---

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| `Sign in to confirm you're not a bot` | Sin cookies | Añade `-b firefox` o `-b chrome` |
| Error acceso a cookies | Navegador abierto | Cierra el navegador e intenta de nuevo |
| `nsig extraction failed` | yt-dlp desactualizado | `pip install -U yt-dlp` |
| Muchos "⚠ Sin subtítulos" | yt-dlp desactualizado o sin cookies | Actualiza y añade cookies |
| 0 URLs extraídas | Canal mal escrito o privado | Verifica `@NombreCanal` en YouTube |

---

## Integración con RAG (Ollama)

Una vez generado el corpus, úsalo con el sistema RAG:

```bash
cd ~/projects/RAG_Agent/rag_corpus_procesador
python rag_corpus_procesador.py
# → selecciona channel_corpus/knowledge_corpus.md
# → elige modelo (recomendado: qwen2.5:14b o mistral)
```

---

## Autor

Alberto Jiménez — [GitHub](https://github.com/albertjimrod)
