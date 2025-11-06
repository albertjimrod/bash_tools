#!/bin/bash
set -euo pipefail
# Uso:
#   ./yt_simple.sh <archivo_urls.txt> <directorio_salida>
#
# Requisitos: yt-dlp (pip install -U yt-dlp)
# Opcional: export YT_COOKIES_FROM_BROWSER=chrome   # o edge / firefox / brave...
#           export YT_COOKIES_FILE=/ruta/a/cookies.txt
if [ "$#" -lt 2 ]; then
  echo "Uso: $0 <archivo_urls.txt> <directorio_salida>"
  exit 1
fi

URLS_FILE="$1"
OUT_DIR="$2"
[ -f "$URLS_FILE" ] || { echo "❌ No existe: $URLS_FILE"; exit 1; }
command -v yt-dlp >/dev/null 2>&1 || { echo "❌ Falta yt-dlp. Instálalo: pip install -U yt-dlp"; exit 1; }
mkdir -p "$OUT_DIR"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT INT TERM

# Pregunta de idioma (por defecto inglés)
ANS=""
if [ -t 0 ]; then
  printf "¿Quieres la transcripción en inglés [S/n]? "
  read -r ANS
fi
case "${ANS,,}" in
  ""|"s"|"si"|"yes"|"y") LANG_CODE="en" ;;
  "n"|"no") LANG_CODE="es" ;;
  *) LANG_CODE="en" ;;
esac

# Parámetros opcionales de cookies
COOKIES_ARGS=""
if [ -n "${YT_COOKIES_FROM_BROWSER:-}" ]; then
  COOKIES_ARGS="--cookies-from-browser ${YT_COOKIES_FROM_BROWSER}"
elif [ -n "${YT_COOKIES_FILE:-}" ]; then
  COOKIES_ARGS="--cookies ${YT_COOKIES_FILE}"
fi

sanitize() {
  local s="$1"
  s=$(printf "%s" "$s" | tr -d '\r')
  s=$(printf "%s" "$s" | sed 's/[\/\\]/-/g; s/:/ - /g; s/"/'\''/g; s/?//g; s/*//g; s/</(/g; s/>/)/g; s/|/-/g')
  s=$(printf "%s" "$s" | tr -d '\000-\037' | tr -s ' ' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  printf "%.180s" "$s"
}

# ✅ FUNCIÓN CORREGIDA Y MEJORADA: Elimina repeticiones y formatea para IA
subs_to_text() {
  local f="$1"
  # 1. Extraer el texto limpio de VTT/SRT (sin tiempos, sin etiquetas)
  awk '
    # Eliminar metadatos iniciales
    /^Kind: captions Language:/ { next }
    # Eliminar líneas de tiempo VTT
    /^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} --> [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}/ { next }
    # Eliminar líneas con align/position
    /align:/ { next }
    /position:/ { next }
    # Quitar etiquetas HTML
    { gsub(/<[^>]*>/, " ") }
    # Limpiar espacios al inicio y final
    { gsub(/^[[:space:]]+|[[:space:]]+$/, "") }
    # Eliminar líneas vacías
    NF == 0 { next }
    # Guardar línea actual
    { 
      current_line = $0
      # Si es igual a la línea anterior, no la imprimimos
      if (current_line == prev_line) {
        next
      }
      # Si la línea anterior era vacía, imprimimos esta línea como nueva oración
      if (prev_line == "" || length(prev_line) == 0) {
        print current_line
      } else {
        # Si no es igual a la anterior, imprimimos con salto de línea
        print current_line
      }
      prev_line = current_line
    }
  ' "$f" | \
  # 2. Agrupar en párrafos lógicos (cada oración en una línea, separadas por punto)
  awk '
    BEGIN { ORS = " " }
    {
      # Reemplazar puntos, signos de interrogación y exclamación seguidos de espacio por punto + salto
      gsub(/[.!?]+[[:space:]]+/, ".\n")
      # Asegurar que no haya más de un espacio
      gsub(/[[:space:]]+/, " ")
      # Eliminar espacios al inicio y final
      gsub(/^[[:space:]]+|[[:space:]]+$/, "")
      if (length($0) > 0) {
        printf "%s", $0
      }
    }
    END { print "" }
  ' | \
  # 3. Eliminar líneas vacías y espacios extra
  sed '/^$/d; s/^[[:space:]]*//; s/[[:space:]]*$//'
}

echo "✅ Idioma objetivo: $LANG_CODE"
[ -n "$COOKIES_ARGS" ] && echo "🔑 Usando cookies: $COOKIES_ARGS"
echo "📄 Archivo URLs: $URLS_FILE"
echo "📁 Salida: $OUT_DIR"
echo

TOTAL=0; OK=0; NO_SUB=0; ERR=0
while IFS= read -r URL || [ -n "$URL" ]; do
  URL=$(printf "%s" "$URL" | tr -d '\r')
  [ -z "$URL" ] && continue
  case "$URL" in \#*) continue ;; esac
  TOTAL=$((TOTAL + 1))
  echo "▶ $URL"
  VID_ID=$(yt-dlp $COOKIES_ARGS --skip-download --get-id "$URL" 2>/dev/null) || { echo "  ✖ Error obteniendo ID"; ERR=$((ERR + 1)); continue; }
  TITLE_RAW=$(yt-dlp $COOKIES_ARGS --skip-download -e "$URL" 2>/dev/null) || { echo "  ✖ Error obteniendo título"; ERR=$((ERR + 1)); continue; }
  TITLE=$(sanitize "$TITLE_RAW"); [ -z "$TITLE" ] && TITLE="video_${VID_ID}"
  OUT_TXT="$OUT_DIR/${TITLE}.txt"
  FOUND_FILE=""
  FOUND_LANG=""
  echo "  • Buscando subtítulos en $LANG_CODE (manual y automático)…"
  if yt-dlp $COOKIES_ARGS \
      --skip-download \
      --write-sub \
      --write-auto-sub \
      --sub-langs "$LANG_CODE" \
      --sub-format vtt \
      -o "$TMP_DIR/%(id)s.%(sub_format)s.%(ext)s" \
      "$URL" >/dev/null 2>&1; then
    FOUND_FILE=$(find "$TMP_DIR" -name "${VID_ID}.*.vtt" -o -name "${VID_ID}.*.srt" 2>/dev/null | head -n1)
    if [ -n "$FOUND_FILE" ]; then
      base=$(basename "$FOUND_FILE")
      FOUND_LANG=$(echo "$base" | sed -E 's/^[^.]+\.(.+)\.(vtt|srt)$/\1/')
      [ -z "$FOUND_LANG" ] && FOUND_LANG="desconocido"
    fi
  fi
  if [ -z "$FOUND_FILE" ]; then
    echo "  • No se encontró en $LANG_CODE. Buscando cualquier subtítulo disponible…"
    if yt-dlp $COOKIES_ARGS \
        --skip-download \
        --write-sub \
        --write-auto-sub \
        --sub-langs "all" \
        --sub-format vtt \
        -o "$TMP_DIR/%(id)s.%(sub_format)s.%(ext)s" \
        "$URL" >/dev/null 2>&1; then
      FOUND_FILE=$(find "$TMP_DIR" -name "${VID_ID}.*.vtt" -o -name "${VID_ID}.*.srt" 2>/dev/null | head -n1)
      if [ -n "$FOUND_FILE" ]; then
        base=$(basename "$FOUND_FILE")
        FOUND_LANG=$(echo "$base" | sed -E 's/^[^.]+\.(.+)\.(vtt|srt)$/\1/')
        [ -z "$FOUND_LANG" ] && FOUND_LANG="desconocido"
      fi
    fi
  fi
  if [ -n "$FOUND_FILE" ]; then
    {
      echo "# Título: $TITLE_RAW"
      echo "# URL: https://www.youtube.com/watch?v=${VID_ID}"
      echo "# Idioma detectado: $FOUND_LANG"
      echo "#"
      subs_to_text "$FOUND_FILE"
    } > "$OUT_TXT"
    echo "  ✓ Guardado: $OUT_TXT"
    OK=$((OK + 1))
  else
    echo "  ⚠ No se encontraron subtítulos (puede que no existan, requieran login, o estén restringidos por región)."
    NO_SUB=$((NO_SUB + 1))
  fi
  rm -f "$TMP_DIR/${VID_ID}"*.vtt "$TMP_DIR/${VID_ID}"*.srt 2>/dev/null || true
done < "$URLS_FILE"
echo
echo "📊 Resumen: Total: $TOTAL | Exitosas: $OK | Sin subtítulos: $NO_SUB | Errores: $ERR"
