#!/usr/bin/env bash
set -euo pipefail

# yt_channel_to_corpus.sh
# Extrae subtítulos de un canal de YouTube y genera un corpus Markdown
#
# Uso:
#   ./yt_channel_to_corpus.sh @NombreCanal
#   ./yt_channel_to_corpus.sh @NombreCanal -l es -n 50
#
# Opciones:
#   -l, --lang LANG     Idioma de subtítulos (en|es, por defecto: en)
#   -n, --limit NUM     Limitar número de vídeos (por defecto: todos)
#   -o, --output DIR    Directorio de salida (por defecto: channel_corpus)
#   -h, --help          Mostrar ayuda

# Variables por defecto
CHANNEL=""
LANG="en"
LIMIT=""
OUTDIR="channel_corpus"

# Parseo de argumentos
while [[ $# -gt 0 ]]; do
  case "$1" in
    -l|--lang)
      LANG="$2"
      shift 2
      ;;
    -n|--limit)
      LIMIT="$2"
      shift 2
      ;;
    -o|--output)
      OUTDIR="$2"
      shift 2
      ;;
    -h|--help)
      grep '^#' "$0" | sed -E 's/^# ?//'
      exit 0
      ;;
    @*|http*://*)
      CHANNEL="$1"
      shift
      ;;
    *)
      # Asumir que es el canal si no se ha especificado aún
      if [[ -z "$CHANNEL" ]]; then
        CHANNEL="$1"
        shift
      else
        echo "❌ Error: Parámetro desconocido: $1" >&2
        exit 1
      fi
      ;;
  esac
done

# Validación
if [[ -z "$CHANNEL" ]]; then
  echo "❌ Error: Debes especificar un canal (ej: @NombreCanal)" >&2
  exit 1
fi

command -v yt-dlp >/dev/null 2>&1 || {
  echo "❌ yt-dlp no instalado. Instalar con: pip install -U yt-dlp" >&2
  exit 1
}

# Crear estructura de directorios
mkdir -p "$OUTDIR"/{urls,subs}
URLS_FILE="$OUTDIR/urls/channel_urls.txt"
SUBS_DIR="$OUTDIR/subs"
CORPUS_FILE="$OUTDIR/knowledge_corpus.md"

# Paso 1: Extraer URLs del canal
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 PASO 1: Extrayendo URLs del canal $CHANNEL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PLAYLIST_ARGS="--flat-playlist -I :"
[[ -n "$LIMIT" ]] && PLAYLIST_ARGS="--flat-playlist -I 1:$LIMIT"

if ! yt-dlp $PLAYLIST_ARGS \
    --print "%(webpage_url)s" \
    "https://www.youtube.com/${CHANNEL}/videos" \
    > "$URLS_FILE" 2>/dev/null; then
  echo "❌ Error al extraer URLs. Verifica que el canal existe." >&2
  exit 1
fi

TOTAL_URLS=$(wc -l < "$URLS_FILE")
echo "✅ Extraídas $TOTAL_URLS URLs"
echo "📄 Guardadas en: $URLS_FILE"
echo

# Paso 2: Descargar subtítulos
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 PASO 2: Descargando subtítulos (idioma: $LANG)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Función: sanitizar nombres
sanitize() {
  printf "%s" "$1" | tr -d '\r' | sed 's/[\/\\]/-/g; s/:/ - /g; s/"/'\''/g; s/[?*<>|]//g' \
    | tr -d '\000-\037' | tr -s ' ' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | cut -c1-180
}

# Función: limpiar subtítulos
subs_to_text() {
  awk '
    /^(Kind:|WEBVTT|^[0-9]{2}:[0-9]{2}:|align:|position:)/ { next }
    { gsub(/<[^>]*>/, " "); gsub(/^[[:space:]]+|[[:space:]]+$/, "") }
    NF == 0 { next }
    { if ($0 != prev_line) { print; prev_line = $0 } }
  ' "$1" | awk '
    BEGIN { ORS = " " }
    { gsub(/[.!?]+[[:space:]]+/, ".\n"); gsub(/[[:space:]]+/, " "); if (length($0) > 0) printf "%s", $0 }
    END { print "" }
  ' | sed '/^$/d; s/^[[:space:]]*//; s/[[:space:]]*$//'
}

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT INT TERM

OK=0 NO_SUB=0 ERR=0

while IFS= read -r URL || [[ -n "$URL" ]]; do
  URL=$(printf "%s" "$URL" | tr -d '\r')
  [[ -z "$URL" || "$URL" == \#* ]] && continue
  
  echo "▶ $URL"
  
  VID_ID=$(yt-dlp --skip-download --get-id "$URL" 2>/dev/null) || { echo "  ✖ Error ID"; ((ERR++)); continue; }
  TITLE_RAW=$(yt-dlp --skip-download -e "$URL" 2>/dev/null) || { echo "  ✖ Error título"; ((ERR++)); continue; }
  TITLE=$(sanitize "$TITLE_RAW")
  [[ -z "$TITLE" ]] && TITLE="video_${VID_ID}"
  
  OUT_TXT="$SUBS_DIR/${TITLE}.txt"
  FOUND=""
  FOUND_LANG=""
  
  # Intento 1: idioma específico solicitado
  echo "  • Buscando subtítulos en $LANG (manual y automático)…"
  if yt-dlp --skip-download --write-sub --write-auto-sub \
      --sub-langs "$LANG" --sub-format vtt \
      -o "$TMPDIR/%(id)s.%(sub_format)s.%(ext)s" \
      "$URL" >/dev/null 2>&1; then
    FOUND=$(find "$TMPDIR" -name "${VID_ID}.*.vtt" -o -name "${VID_ID}.*.srt" 2>/dev/null | head -n1)
    if [[ -n "$FOUND" ]]; then
      base=$(basename "$FOUND")
      FOUND_LANG=$(echo "$base" | sed -E 's/^[^.]+\.(.+)\.(vtt|srt)$/\1/')
      [[ -z "$FOUND_LANG" ]] && FOUND_LANG="desconocido"
    fi
  fi
  
  # Intento 2: español si no se pidió español
  if [[ -z "$FOUND" && "$LANG" != "es" ]]; then
    echo "  • No encontrado en $LANG. Probando en español…"
    if yt-dlp --skip-download --write-sub --write-auto-sub \
        --sub-langs "es" --sub-format vtt \
        -o "$TMPDIR/%(id)s.%(sub_format)s.%(ext)s" \
        "$URL" >/dev/null 2>&1; then
      FOUND=$(find "$TMPDIR" -name "${VID_ID}.*.vtt" -o -name "${VID_ID}.*.srt" 2>/dev/null | head -n1)
      if [[ -n "$FOUND" ]]; then
        base=$(basename "$FOUND")
        FOUND_LANG=$(echo "$base" | sed -E 's/^[^.]+\.(.+)\.(vtt|srt)$/\1/')
        [[ -z "$FOUND_LANG" ]] && FOUND_LANG="es"
      fi
    fi
  fi
  
  # Intento 3: cualquier idioma disponible
  if [[ -z "$FOUND" ]]; then
    echo "  • No encontrado. Buscando cualquier subtítulo disponible…"
    if yt-dlp --skip-download --write-sub --write-auto-sub \
        --sub-langs "all" --sub-format vtt \
        -o "$TMPDIR/%(id)s.%(sub_format)s.%(ext)s" \
        "$URL" >/dev/null 2>&1; then
      FOUND=$(find "$TMPDIR" -name "${VID_ID}.*.vtt" -o -name "${VID_ID}.*.srt" 2>/dev/null | head -n1)
      if [[ -n "$FOUND" ]]; then
        base=$(basename "$FOUND")
        FOUND_LANG=$(echo "$base" | sed -E 's/^[^.]+\.(.+)\.(vtt|srt)$/\1/')
        [[ -z "$FOUND_LANG" ]] && FOUND_LANG="desconocido"
      fi
    fi
  fi
  
  if [[ -n "$FOUND" ]]; then
    {
      echo "# Título: $TITLE_RAW"
      echo "# URL: https://www.youtube.com/watch?v=${VID_ID}"
      echo "# Idioma: $FOUND_LANG"
      echo "#"
      subs_to_text "$FOUND"
    } > "$OUT_TXT"
    echo "  ✓ [$FOUND_LANG] $OUT_TXT"
    ((OK++))
  else
    echo "  ⚠ Sin subtítulos"
    ((NO_SUB++))
  fi
  
  # Limpiar archivos temporales de este vídeo
  rm -f "$TMPDIR/${VID_ID}"*.vtt "$TMPDIR/${VID_ID}"*.srt 2>/dev/null || true
done < "$URLS_FILE"

echo
echo "📊 Total: $TOTAL_URLS | Éxito: $OK | Sin subs: $NO_SUB | Errores: $ERR"
echo

# Paso 3: Crear corpus
if [[ $OK -eq 0 ]]; then
  echo "⚠️  No se descargó ningún subtítulo. No hay corpus que generar."
  exit 0
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 PASO 3: Generando corpus Markdown"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

slugify() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g; s/-+/-/g' || echo 'unknown'
}

extract_meta() {
  local title=$(grep -m1 '^# Título:' "$1" 2>/dev/null | sed 's/^# Título:[[:space:]]*//' || basename "$1")
  local url=$(grep -m1 '^# URL:' "$1" 2>/dev/null | sed 's/^# URL:[[:space:]]*//' || echo "N/A")
  printf '%s\t%s\n' "$title" "$url"
}

{
  echo "# Corpus de subtítulos: $CHANNEL"
  echo
  echo "- **Generado:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
  echo "- **Canal:** $CHANNEL"
  echo "- **Idioma:** $LANG"
  echo "- **Archivos:** $OK"
  echo
  echo "---"
  echo
  echo "## Tabla de contenidos"
  echo
} > "$CORPUS_FILE"

for f in "$SUBS_DIR"/*.txt; do
  [[ ! -f "$f" ]] && continue
  IFS=$'\t' read -r title url < <(extract_meta "$f")
  anchor=$(slugify "$title")
  echo "- [$title](#${anchor}) — \`$(basename "$f")\`" >> "$CORPUS_FILE"
done

echo -e "\n---\n" >> "$CORPUS_FILE"

for f in "$SUBS_DIR"/*.txt; do
  [[ ! -f "$f" ]] && continue
  IFS=$'\t' read -r title url < <(extract_meta "$f")
  anchor=$(slugify "$title")
  {
    echo "## $title"
    echo
    echo "**Archivo:** \`$(basename "$f")\`  "
    echo "**URL:** $url  "
    echo "**Anchor:** \`#${anchor}\`"
    echo
    echo "<!-- ---8<--- [BEGIN FILE: $(basename "$f")] ---8<--- -->"
    echo
    tr -d '\000' < "$f" | sed -E 's/\r$//' | sed 's/\t/    /g' | sed 's/[[:space:]]*$//' | \
      awk 'BEGIN { p = 0 } { if (/^[[:space:]]*$/) { if (!p) print; p = 1 } else { print; p = 0 } }'
    echo
    echo "<!-- ---8<--- [END FILE: $(basename "$f")] ---8<--- -->"
    echo -e "\n---\n"
  } >> "$CORPUS_FILE"
done

echo "✅ Corpus generado: $CORPUS_FILE"
echo "📁 Directorio de salida: $OUTDIR"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ PROCESO COMPLETADO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
