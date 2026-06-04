#!/usr/bin/env bash
set -euo pipefail

# yt_channel_to_corpus.sh
# Extrae transcripciones de un canal de YouTube y genera un corpus Markdown
#
# Uso:
#   ./yt_channel_to_corpus.sh @NombreCanal
#   ./yt_channel_to_corpus.sh @NombreCanal -l es -n 50
#   ./yt_channel_to_corpus.sh @NombreCanal -u          # usar corpus existente, saltar descarga
#
# Opciones:
#   -l, --lang LANG       Idioma preferido (en|es|..., por defecto: es)
#   -n, --limit NUM       Limitar número de vídeos (por defecto: todos)
#   -o, --output DIR      Directorio de salida (por defecto: channel_corpus)
#   -b, --browser NAME    Navegador para cookies (brave|firefox|chrome|chromium|edge)
#   -u, --use-existing    Usar corpus ya generado y saltar la descarga
#   -h, --help            Mostrar ayuda

CHANNEL=""
LANG="es"
LIMIT=""
OUTDIR="channel_corpus"
BROWSER="brave"
USE_EXISTING=false

# ─── PARSEO DE ARGUMENTOS ────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    -l|--lang)         LANG="$2";    shift 2 ;;
    -n|--limit)        LIMIT="$2";   shift 2 ;;
    -o|--output)       OUTDIR="$2";  shift 2 ;;
    -b|--browser)      BROWSER="$2"; shift 2 ;;
    -u|--use-existing) USE_EXISTING=true; shift ;;
    -h|--help)
      grep '^#' "$0" | sed -E 's/^# ?//'
      exit 0
      ;;
    @*|http*://*)  CHANNEL="$1"; shift ;;
    *)
      if [[ -z "$CHANNEL" ]]; then CHANNEL="$1"; shift
      else echo "❌ Parámetro desconocido: $1" >&2; exit 1; fi
      ;;
  esac
done

# ─── VALIDACIONES ────────────────────────────────────────────────────────────
if [[ -z "$CHANNEL" ]]; then
  echo "❌ Error: Debes especificar un canal (ej: @NombreCanal)" >&2; exit 1
fi

python -m yt_dlp --version >/dev/null 2>&1 || {
  echo "❌ yt-dlp no instalado en este entorno. Instalar con: pip install -U yt-dlp" >&2; exit 1
}

python3 -c "from youtube_transcript_api import YouTubeTranscriptApi" 2>/dev/null || {
  echo "❌ youtube-transcript-api no instalado. Instalar con: pip install youtube-transcript-api" >&2
  exit 1
}

# ─── COMPROBACIÓN DE VERSIÓN yt-dlp ──────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 COMPROBANDO VERSIÓN DE yt-dlp"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

INSTALLED=$(python -m yt_dlp --version 2>/dev/null || echo "desconocida")
echo "   Versión instalada: $INSTALLED"

normalize_ver() { echo "$1" | awk -F. '{printf "%d.%d.%d\n", $1, $2, $3}'; }

LATEST=$(pip index versions yt-dlp 2>/dev/null \
  | head -1 | grep -oP '[\d]+\.[\d]+\.[\d]+' | head -1 || echo "")

INSTALLED_NORM=$(normalize_ver "$INSTALLED")
LATEST_NORM=$(normalize_ver "$LATEST")

if [[ -z "$LATEST" ]]; then
  echo "   ⚠️  No se pudo consultar PyPI. Continúa con precaución."
elif [[ "$INSTALLED_NORM" == "$LATEST_NORM" ]]; then
  echo "   ✅ Versión al día ($INSTALLED). OK."
else
  echo ""
  echo "   ┌─────────────────────────────────────────────────────┐"
  echo "   │  ⚠️  AVISO: hay una versión más nueva en PyPI        │"
  echo "   │  Instalada:  $INSTALLED"
  echo "   │  Disponible: $LATEST"
  echo "   │  Actualiza:  pip install -U python -m yt_dlp                  │"
  echo "   └─────────────────────────────────────────────────────┘"
  echo ""
  read -rp "   ¿Continuar de todas formas? [s/N]: " CONT
  [[ "$CONT" =~ ^[sS]$ ]] || { echo "   Cancelado."; exit 0; }
fi
echo ""

# ─── ESTRUCTURA DE DIRECTORIOS ───────────────────────────────────────────────
mkdir -p "$OUTDIR"/{urls,subs}
URLS_FILE="$OUTDIR/urls/channel_urls.txt"
SUBS_DIR="$OUTDIR/subs"
CORPUS_FILE="$OUTDIR/knowledge_corpus.md"

# ─── DETECCIÓN DE CORPUS EXISTENTE ───────────────────────────────────────────
if [[ "$USE_EXISTING" == false && -f "$CORPUS_FILE" ]]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  CORPUS_SIZE=$(du -sh "$CORPUS_FILE" 2>/dev/null | cut -f1)
  CORPUS_DATE=$(date -r "$CORPUS_FILE" "+%d/%m/%Y %H:%M" 2>/dev/null)
  echo "📄 Corpus existente encontrado: $CORPUS_FILE"
  echo "   Tamaño: $CORPUS_SIZE  |  Generado: $CORPUS_DATE"
  echo ""
  read -rp "   ¿Usar este corpus y saltar la descarga? [S/n]: " RESP
  [[ "$RESP" =~ ^[nN]$ ]] || USE_EXISTING=true
  echo ""
fi

if [[ "$USE_EXISTING" == true ]]; then
  if [[ ! -f "$CORPUS_FILE" ]]; then
    echo "❌ No existe corpus en $CORPUS_FILE. Ejecuta sin -u para generarlo." >&2
    exit 1
  fi
  echo "⏭  Saltando descarga — usando corpus existente: $CORPUS_FILE"
  echo ""
  # Saltar directamente al arranque del RAG
  RAG_SCRIPT="$(dirname "$0")/rag_youtube.py"
  if [[ -f "$RAG_SCRIPT" ]]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🤖 ARRANCAR RAG"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Modelos Ollama disponibles:"
    ollama list 2>/dev/null | tail -n +2 | awk '{print "  •", $1}' || echo "  (no se pudo consultar ollama)"
    echo ""
    while [[ -z "$MODELO" ]]; do
      read -rp "Modelo a usar (copia uno de la lista): " MODELO
    done
    CORPUS_ABS=$(realpath "$CORPUS_FILE")
    echo ""
    python "$RAG_SCRIPT" "$MODELO" "$CORPUS_ABS"
  else
    echo "⚠️  Script RAG no encontrado en $RAG_SCRIPT"
  fi
  exit 0
fi

# ─── PASO 1: EXTRAER URLs DEL CANAL ─────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 PASO 1: Extrayendo URLs del canal $CHANNEL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PLAYLIST_ARGS="--flat-playlist -I :"
[[ -n "$LIMIT" ]] && PLAYLIST_ARGS="--flat-playlist -I 1:$LIMIT"

# Si ya es URL completa la usamos tal cual, si es handle construimos la URL
if [[ "$CHANNEL" == http* ]]; then
  CHANNEL_URL="${CHANNEL%/videos}/videos"
else
  CHANNEL_URL="https://www.youtube.com/${CHANNEL}/videos"
fi

# Extraer URL y fecha de publicación (YYYYMMDD) separadas por tabulador
URLS_WITH_DATES="$OUTDIR/urls/channel_urls_dates.txt"
python -m yt_dlp $PLAYLIST_ARGS --cookies-from-browser "$BROWSER" \
    --print "%(webpage_url)s	%(upload_date)s" \
    "$CHANNEL_URL" \
    > "$URLS_WITH_DATES" 2>/dev/null || true

# Separar el fichero de URLs solo (para compatibilidad)
cut -f1 "$URLS_WITH_DATES" > "$URLS_FILE"

TOTAL_URLS=$(wc -l < "$URLS_FILE")
if [[ $TOTAL_URLS -eq 0 ]]; then
  echo "❌ No se extrajeron URLs. Verifica el canal y que $BROWSER tenga sesión en YouTube." >&2
  exit 1
fi
echo "✅ Extraídas $TOTAL_URLS URLs"
echo "📄 Guardadas en: $URLS_FILE"
echo ""

# ─── PASO 2: DESCARGAR TRANSCRIPCIONES ───────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 PASO 2: Descargando transcripciones (idioma preferido: $LANG)"
echo "   Usando: youtube-transcript-api (sin n-challenge)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "🍪 Cargando cookies de $BROWSER con rookiepy..."
export YT_BROWSER="$BROWSER"
python3 -c "
import sys
try:
    import rookiepy
    fn = getattr(rookiepy, '$BROWSER', None)
    if fn is None:
        print('   ⚠️  Navegador no soportado por rookiepy')
        sys.exit(0)
    cookies = fn(['.youtube.com'])
    print(f'   ✅ {len(cookies)} cookies de YouTube cargadas')
except Exception as e:
    print(f'   ⚠️  rookiepy no disponible: {e}')
" 2>&1
echo ""

sanitize() {
  printf "%s" "$1" | tr -d '\r' | \
    sed 's/[\/\\]/-/g; s/:/ - /g; s/"/'\''/g; s/[?*<>|]//g' | \
    tr -d '\000-\037' | tr -s ' ' | \
    sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | cut -c1-180
}

OK=0; NO_SUB=0; ERR=0

while IFS=$'\t' read -r URL UPLOAD_DATE || [[ -n "$URL" ]]; do
  URL=$(printf "%s" "$URL" | tr -d '\r')
  [[ -z "$URL" || "$URL" == \#* ]] && continue

  VID_ID=$(echo "$URL" | grep -oP '(?<=v=)[^&]+' || true)
  if [[ -z "$VID_ID" ]]; then
    echo "▶ $URL → ✖ No se pudo extraer el ID"; ERR=$(( ERR + 1 )); continue
  fi

  echo "▶ $VID_ID"

  # Obtener transcripción con youtube-transcript-api
  RESULT=$(python3 - "$VID_ID" "$LANG" "$YT_BROWSER" <<'PYEOF'
import sys, json, os
import requests
from youtube_transcript_api import YouTubeTranscriptApi

vid_id  = sys.argv[1]
lang    = sys.argv[2]
browser = sys.argv[3] if len(sys.argv) > 3 else ""

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
})
if browser:
    try:
        import rookiepy
        fn = getattr(rookiepy, browser, None)
        if fn:
            for c in fn(['.youtube.com']):
                session.cookies.set(c['name'], c['value'], domain=c['domain'])
    except Exception:
        pass

api = YouTubeTranscriptApi(http_client=session)

try:
    # Listar todas las transcripciones disponibles
    tl = api.list(vid_id)
    available = list(tl)

    # 1. Buscar idioma preferido (manual o auto)
    chosen = None
    found_lang = None
    for t in available:
        if t.language_code == lang or t.language_code.startswith(lang + "-"):
            chosen = t
            found_lang = t.language_code
            break

    # 2. Si no hay en el idioma preferido, coger la primera disponible
    if chosen is None and available:
        chosen = available[0]
        found_lang = chosen.language_code

    if chosen is None:
        print(json.dumps({"ok": False, "reason": "no transcripts"}))
        sys.exit(0)

    snippets = list(chosen.fetch())
    text = " ".join(s.text for s in snippets)
    print(json.dumps({"ok": True, "lang": found_lang, "text": text}))

except Exception as e:
    print(json.dumps({"ok": False, "reason": str(e)}))
PYEOF
  )

  OK_FLAG=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ok','false'))" 2>/dev/null || echo "False")

  if [[ "$OK_FLAG" == "True" ]]; then
    FOUND_LANG=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('lang',''))" 2>/dev/null)
    TEXT=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('text',''))" 2>/dev/null)
    OUT_TXT="$SUBS_DIR/${VID_ID}.txt"
    # Convertir YYYYMMDD → DD/MM/YYYY para que el RAG detecte la fecha
    if [[ "$UPLOAD_DATE" =~ ^[0-9]{8}$ ]]; then
      DATE_FMT="${UPLOAD_DATE:6:2}/${UPLOAD_DATE:4:2}/${UPLOAD_DATE:0:4}"
    else
      DATE_FMT="$UPLOAD_DATE"
    fi
    {
      echo "# URL: https://www.youtube.com/watch?v=${VID_ID}"
      echo "# Fecha: $DATE_FMT"
      echo "# Idioma: $FOUND_LANG"
      echo "#"
      echo "$TEXT"
    } > "$OUT_TXT"
    echo "  ✓ [$FOUND_LANG] → $OUT_TXT"
    OK=$(( OK + 1 ))
  else
    echo "  ⚠ Sin transcripción disponible"
    NO_SUB=$(( NO_SUB + 1 ))
  fi

done < "$URLS_WITH_DATES"

echo ""
echo "📊 Total: $TOTAL_URLS | Éxito: $OK | Sin transcripción: $NO_SUB | Errores: $ERR"
echo ""

# ─── PASO 3: GENERAR CORPUS ──────────────────────────────────────────────────
if [[ $OK -eq 0 ]]; then
  echo "⚠️  No se descargó ninguna transcripción. No hay corpus que generar."
  exit 0
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 PASO 3: Generando corpus Markdown"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

slugify() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | \
    sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g; s/-+/-/g' || echo 'unknown'
}

{
  echo "# Corpus de transcripciones: $CHANNEL"
  echo ""
  echo "- **Generado:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
  echo "- **Canal:** $CHANNEL"
  echo "- **Idioma preferido:** $LANG"
  echo "- **Vídeos con transcripción:** $OK"
  echo ""
  echo "---"
  echo ""
  echo "## Tabla de contenidos"
  echo ""
} > "$CORPUS_FILE"

for f in "$SUBS_DIR"/*.txt; do
  [[ ! -f "$f" ]] && continue
  vid=$(basename "$f" .txt)
  url=$(grep -m1 '^# URL:' "$f" | sed 's/^# URL:[[:space:]]*//')
  echo "- [$vid]($url)" >> "$CORPUS_FILE"
done

echo -e "\n---\n" >> "$CORPUS_FILE"

for f in "$SUBS_DIR"/*.txt; do
  [[ ! -f "$f" ]] && continue
  vid=$(basename "$f" .txt)
  url=$(grep -m1 '^# URL:' "$f" | sed 's/^# URL:[[:space:]]*//')
  fecha=$(grep -m1 '^# Fecha:' "$f" | sed 's/^# Fecha:[[:space:]]*//')
  idioma=$(grep -m1 '^# Idioma:' "$f" | sed 's/^# Idioma:[[:space:]]*//')
  # El encabezado incluye la fecha para que el RAG la detecte
  {
    echo "## $fecha - $vid"
    echo ""
    echo "**URL:** $url  "
    echo "**Idioma:** $idioma"
    echo ""
    grep -v '^#' "$f" | sed 's/[[:space:]]*$//'
    echo -e "\n---\n"
  } >> "$CORPUS_FILE"
done

echo "✅ Corpus generado: $CORPUS_FILE"
echo "📁 Directorio de salida: $OUTDIR"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ PROCESO COMPLETADO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─── ARRANQUE AUTOMÁTICO DEL RAG ─────────────────────────────────────────────
RAG_SCRIPT="$(dirname "$0")/rag_youtube.py"

if [[ ! -f "$RAG_SCRIPT" ]]; then
  echo "⚠️  No se encontró el script RAG en: $RAG_SCRIPT"
  echo "   Puedes arrancarlo manualmente con:"
  echo "   python $RAG_SCRIPT"
  exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 ARRANCAR RAG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Modelos Ollama disponibles:"
ollama list 2>/dev/null | tail -n +2 | awk '{print "  •", $1}' || echo "  (no se pudo consultar ollama)"
echo ""
while [[ -z "$MODELO" ]]; do
  read -rp "Modelo a usar (copia uno de la lista): " MODELO
done

CORPUS_ABS=$(realpath "$CORPUS_FILE")
echo ""
echo "Modelo:  $MODELO"
echo "Corpus:  $CORPUS_ABS"
echo ""

python "$RAG_SCRIPT" "$MODELO" "$CORPUS_ABS"
