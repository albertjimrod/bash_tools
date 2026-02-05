#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════════════════════
# full_pipeline.sh - Pipeline completo: YouTube → Transcripciones → Corpus
# Uso: ./full_pipeline.sh [CHANNEL_URL] [LANG] [PART_SIZE]
# Ej:  ./full_pipeline.sh "https://www.youtube.com/@GregIsenberg/videos" es 10M
# ═══════════════════════════════════════════════════════════════════════════════

CHANNEL="${1:-https://www.youtube.com/@AdrianSaenz}"
LANG="${2:-es}"
PART_SIZE="${3:-10M}"

DATA="./data"
LINKS="$DATA/links.txt"
TRANS="$DATA/transcriptions"
CORPUS="$DATA/knowledge_corpus.md"
PARTS="$DATA/parts"
TMP="$(mktemp -d)"

trap 'rm -rf "$TMP"; echo -e "\n⚠️  Interrumpido"; exit 130' INT TERM
trap 'rm -rf "$TMP"' EXIT

# ─────────────────────────────────────────────────────────────────────────────
# Precondición: verificar entorno conda/venv
# ─────────────────────────────────────────────────────────────────────────────
check_env() {
  local env_name="transcription"
  if [[ "${CONDA_DEFAULT_ENV:-}" != "$env_name" ]] && \
     [[ "${VIRTUAL_ENV:-}" != *"$env_name"* ]]; then
    echo "❌ Error: Ejecutar dentro del entorno '$env_name'"
    echo "   conda activate $env_name  |  source $env_name/bin/activate"
    exit 1
  fi
  command -v yt-dlp &>/dev/null || { echo "❌ Falta yt-dlp"; exit 1; }
}

# ─────────────────────────────────────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────────────────────────────────────
sanitize() {
  printf '%s' "$1" | tr -d '\r' | sed 's/[\/\\:?*<>|"]/-/g' | tr -d '\000-\037' | tr -s ' ' | sed 's/^ *//;s/ *$//' | cut -c1-180
}

progress() {
  local cur=${1:-0} tot=${2:-1} w=30
  [[ $tot -eq 0 ]] && tot=1
  local pct=$((cur*100/tot)) filled=$((cur*w/tot))
  [[ $filled -eq 0 ]] && filled=1
  printf "\r[%-${w}s] %d/%d (%d%%)" "$(printf '■%.0s' $(seq 1 $filled))" "$cur" "$tot" "$pct"
}

to_bytes() {
  case "${1^^}" in
    *K) echo $((${1%[Kk]}*1024));;
    *M) echo $((${1%[Mm]}*1048576));;
    *G) echo $((${1%[Gg]}*1073741824));;
    *) echo "$1";;
  esac
}

slugify() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g;s/^-|-$//g'
}

subs_to_text() {
  awk '
    /^WEBVTT|^Kind:|^Language:|^NOTE|^[0-9]{2}:[0-9]{2}.*-->|^[0-9]+$|align:|position:|^[[:space:]]*$/{next}
    {gsub(/<[^>]*>/," ");gsub(/&[a-z]+;/," ");gsub(/[[:space:]]+/," ");gsub(/^ | $/,"");if(length&&$0!=p){print;p=$0}}
  ' "$1" | awk '{b=b?b" "$0:$0}END{gsub(/([.!?]) /,"&\n",b);print b}' | sed '/^$/d'
}

# ─────────────────────────────────────────────────────────────────────────────
# FASE 1: Extracción de enlaces
# ─────────────────────────────────────────────────────────────────────────────
phase1_links() {
  echo "═══════════════════════════════════════════════════════════════"
  echo "  FASE 1: Extracción de enlaces"
  echo "═══════════════════════════════════════════════════════════════"
  mkdir -p "$DATA"
  echo "⏳ Descargando lista de vídeos de: $CHANNEL"
  yt-dlp --flat-playlist -I : --print "%(webpage_url)s" "$CHANNEL" > "$LINKS" 2>/dev/null
  local n=$(wc -l < "$LINKS")
  echo "✅ $n enlaces guardados en $LINKS"
}

# ─────────────────────────────────────────────────────────────────────────────
# FASE 2: Transcripción
# ─────────────────────────────────────────────────────────────────────────────
phase2_transcribe() {
  echo
  echo "═══════════════════════════════════════════════════════════════"
  echo "  FASE 2: Descarga de subtítulos ($LANG)"
  echo "═══════════════════════════════════════════════════════════════"
  mkdir -p "$TRANS"
  
  local total cur=0 ok=0 fail=0
  total=$(wc -l < "$LINKS")
  echo "⏳ Procesando $total vídeos..."
  
  while IFS= read -r url || [[ -n "$url" ]]; do
    [[ -z "$url" || "$url" == \#* ]] && continue
    cur=$((cur + 1))
    progress $cur $total
    
    local vid title out found=""
    vid=$(yt-dlp --skip-download --get-id "$url" 2>/dev/null) || { fail=$((fail + 1)); continue; }
    title=$(yt-dlp --skip-download -e "$url" 2>/dev/null) || title="video_$vid"
    title=$(sanitize "$title")
    out="$TRANS/${title}.txt"
    
    rm -f "$TMP"/* 2>/dev/null || true
    
    # Intentar subs manuales
    yt-dlp --skip-download --write-sub --sub-langs "$LANG" --sub-format "vtt/srt/best" \
      -o "$TMP/%(id)s.%(ext)s" "$url" &>/dev/null || true
    
    for f in "$TMP"/*.vtt "$TMP"/*.srt; do
      [[ -f "$f" ]] && { found="$f"; break; }
    done 2>/dev/null || true
    
    # Si no hay manuales, intentar automáticos
    if [[ -z "$found" ]]; then
      yt-dlp --skip-download --write-auto-sub --sub-langs "$LANG" --sub-format "vtt/srt/best" \
        -o "$TMP/%(id)s.%(ext)s" "$url" &>/dev/null || true
      for f in "$TMP"/*.vtt "$TMP"/*.srt; do
        [[ -f "$f" ]] && { found="$f"; break; }
      done 2>/dev/null || true
    fi
    
    if [[ -n "$found" ]]; then
      { echo "# Título: $title"; echo "# URL: $url"; echo "#"; subs_to_text "$found"; } > "$out"
      ok=$((ok + 1))
    else
      fail=$((fail + 1))
    fi
  done < "$LINKS"
  
  echo -e "\n✅ Completado: $ok exitosos, $fail fallidos de $total"
}

# ─────────────────────────────────────────────────────────────────────────────
# FASE 3: Construcción del corpus
# ─────────────────────────────────────────────────────────────────────────────
phase3_corpus() {
  echo
  echo "═══════════════════════════════════════════════════════════════"
  echo "  FASE 3: Construcción del corpus"
  echo "═══════════════════════════════════════════════════════════════"
  
  mapfile -t files < <(find "$TRANS" -maxdepth 1 -name "*.txt" -type f | sort)
  local n=${#files[@]}
  [[ $n -eq 0 ]] && { echo "❌ Sin transcripciones"; exit 1; }
  
  {
    echo "# Knowledge Corpus"
    echo -e "\n- **Generado:** $(date -u +"%Y-%m-%d %H:%M UTC")"
    echo "- **Archivos:** $n"
    echo -e "\n---\n"
    echo "## Tabla de contenidos"
    
    for f in "${files[@]}"; do
      local title=$(grep -m1 "^# Título:" "$f" 2>/dev/null | sed 's/^# Título: //' || basename "$f")
      local anchor=$(slugify "$title")
      echo "- [$title](#$anchor)"
    done
    
    echo -e "\n---\n"
    
    for f in "${files[@]}"; do
      local bn=$(basename "$f")
      local title=$(grep -m1 "^# Título:" "$f" 2>/dev/null | sed 's/^# Título: //' || echo "$bn")
      local url=$(grep -m1 "^# URL:" "$f" 2>/dev/null | sed 's/^# URL: //' || echo "N/A")
      
      echo "## $title"
      echo -e "\n**Archivo:** \`$bn\` | **URL:** $url\n"
      echo "<!-- ---8<--- [BEGIN FILE: $bn] ---8<--- -->"
      grep -v "^#" "$f" | tr -d '\000' | sed 's/\r$//;s/[[:space:]]*$//'
      echo -e "\n<!-- ---8<--- [END FILE: $bn] ---8<--- -->\n\n---\n"
    done
  } > "$CORPUS"
  
  echo "✅ Corpus creado: $CORPUS ($(du -h "$CORPUS" | cut -f1))"
}

# ─────────────────────────────────────────────────────────────────────────────
# FASE 4: División del corpus
# ─────────────────────────────────────────────────────────────────────────────
phase4_split() {
  echo
  echo "═══════════════════════════════════════════════════════════════"
  echo "  FASE 4: División del corpus (max $PART_SIZE/parte)"
  echo "═══════════════════════════════════════════════════════════════"
  
  mkdir -p "$PARTS"
  local max part=1 pfile files_count=0 sz
  max=$(to_bytes "$PART_SIZE")
  pfile="$PARTS/part_$(printf %02d $part).md"
  local in_block=false
  
  { echo "# Corpus - Parte $part"; echo -e "\n- **Max:** $PART_SIZE\n- **Archivos:**"; } > "$pfile"
  
  while IFS= read -r line; do
    if [[ "$line" == *'[BEGIN FILE:'* ]]; then
      local fn
      fn=$(echo "$line" | grep -oP '(?<=\[BEGIN FILE: ).*(?=\] ---)') || fn="unknown"
      echo "  - \`$fn\`" >> "$pfile"
      in_block=true
      files_count=$((files_count + 1))
    fi
    
    echo "$line" >> "$pfile"
    
    [[ "$line" == *'[END FILE:'* ]] && in_block=false
    
    sz=$(stat -c%s "$pfile" 2>/dev/null || echo 0)
    if [[ $sz -gt $max && $files_count -gt 0 && "$in_block" == false ]]; then
      echo "✅ Parte $part: $(du -h "$pfile" | cut -f1)"
      part=$((part + 1))
      pfile="$PARTS/part_$(printf %02d $part).md"
      files_count=0
      { echo "# Corpus - Parte $part"; echo -e "\n- **Max:** $PART_SIZE\n- **Archivos:**"; } > "$pfile"
    fi
  done < "$CORPUS"
  
  echo "✅ Parte $part: $(du -h "$pfile" | cut -f1)"
  
  # Índice
  {
    echo "# Índice de partes"
    echo -e "\n| # | Archivo | Tamaño |"
    echo "|---|---|---|"
    local i
    for i in $(seq 1 $part); do
      local f="$PARTS/part_$(printf %02d $i).md"
      [[ -f "$f" ]] && echo "| $i | \`$(basename "$f")\` | $(du -h "$f" | cut -f1) |"
    done
  } > "$PARTS/index.md"
  
  echo -e "\n✅ División completada: $part partes en $PARTS/"
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
main() {
  echo
  echo "╔═══════════════════════════════════════════════════════════════╗"
  echo "║       PIPELINE: YouTube → Corpus de Conocimiento              ║"
  echo "╚═══════════════════════════════════════════════════════════════╝"
  echo
  
  check_env
  phase1_links
  phase2_transcribe
  phase3_corpus
  phase4_split
  
  echo
  echo "═══════════════════════════════════════════════════════════════"
  echo "  ✅ PIPELINE COMPLETADO"
  echo "═══════════════════════════════════════════════════════════════"
  echo "  📁 Estructura:"
  echo "     $DATA/"
  echo "     ├── links.txt"
  echo "     ├── transcriptions/"
  echo "     ├── knowledge_corpus.md"
  echo "     └── parts/"
  echo "         ├── part_01.md ... part_XX.md"
  echo "         └── index.md"
  echo "═══════════════════════════════════════════════════════════════"
}

main "$@"
