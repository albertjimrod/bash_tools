#!/usr/bin/env bash
# debug_video.sh - Prueba de descarga de subtítulos para un vídeo específico

if [[ $# -lt 1 ]]; then
  echo "Uso: $0 <URL_del_video> [idioma]"
  echo "Ejemplo: $0 'https://www.youtube.com/watch?v=AGCrpaUs_J8' es"
  exit 1
fi

URL="$1"
LANG="${2:-es}"

echo "🔍 Analizando vídeo: $URL"
echo "📝 Idioma solicitado: $LANG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# 1. Ver qué subtítulos están disponibles
echo "📋 Subtítulos disponibles:"
yt-dlp --list-subs "$URL" 2>&1 | grep -A 50 "Available subtitles" || echo "Error al listar subtítulos"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# 2. Intentar descargar en idioma específico
echo "🎯 Intento 1: Descargando subtítulos en '$LANG'..."
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

yt-dlp --skip-download --write-sub --write-auto-sub \
    --sub-langs "$LANG" --sub-format vtt \
    -o "$TMPDIR/sub" "$URL" 2>&1 | tail -5

if ls "$TMPDIR"/*.vtt >/dev/null 2>&1; then
  echo "✅ Encontrado en '$LANG':"
  ls -lh "$TMPDIR"/*.vtt
  echo
  echo "📄 Primeras líneas:"
  head -20 "$TMPDIR"/*.vtt
else
  echo "❌ No se encontró en '$LANG'"
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# 3. Intentar con todos los idiomas
echo "🌍 Intento 2: Descargando cualquier subtítulo disponible..."
rm -f "$TMPDIR"/* 2>/dev/null

yt-dlp --skip-download --write-sub --write-auto-sub \
    --sub-langs "all" --sub-format vtt \
    -o "$TMPDIR/sub" "$URL" 2>&1 | tail -5

if ls "$TMPDIR"/*.vtt >/dev/null 2>&1; then
  echo "✅ Encontrados:"
  ls -lh "$TMPDIR"/*.vtt
  echo
  echo "📄 Archivos descargados:"
  for f in "$TMPDIR"/*.vtt; do
    echo "  - $(basename "$f")"
  done
else
  echo "❌ No se encontraron subtítulos"
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Debug completado"
