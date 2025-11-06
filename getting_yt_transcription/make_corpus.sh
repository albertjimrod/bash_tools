#!/usr/bin/env bash
set -euo pipefail

# make_corpus.sh
# Crea un corpus Markdown a partir de archivos de texto (.txt, .md, etc.) con metadatos en formato:
#   # Título: ...
#   # URL: ...
#
# El corpus resultante incluye:
# - Portada con metadatos de generación
# - Tabla de contenidos con enlaces a secciones
# - Índice de metadatos en tabla Markdown
# - Contenido de cada archivo con delimitadores claros
#
# Uso:
#   ./make_corpus.sh                # crea knowledge_corpus.md con *.txt y *.md
#   ./make_corpus.sh -o out.md      # especifica el archivo de salida
#   ./make_corpus.sh -e "txt md"    # extensiones a incluir (separadas por espacio)
#
# Variables de entorno opcionales:
#   CORPUS_TITLE="Mi Corpus"        # Título de la portada
#   FILE_GLOB_EXCLUDE="*draft*"     # Patrón para excluir archivos (ej. "*draft*", "*temp*")

OUTFILE="knowledge_corpus.md"
EXTENSIONS=("txt" "md")
TITLE="${CORPUS_TITLE:-Knowledge Corpus}"
EXCLUDE_PATTERN="${FILE_GLOB_EXCLUDE:-}"

# --- Parseo de argumentos ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      OUTFILE="$2"
      shift 2
      ;;
    -e|--ext)
      IFS=' ' read -r -a EXTENSIONS <<< "$2"
      shift 2
      ;;
    -h|--help)
      grep '^#' "$0" | sed -E 's/^# ?//'
      exit 0
      ;;
    *)
      echo "Error: Parámetro desconocido: $1" >&2
      exit 1
      ;;
  esac
done

# --- Preparación temporal ---
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT INT TERM

# --- Validar extensiones ---
if [[ ${#EXTENSIONS[@]} -eq 0 ]]; then
  echo "Error: No se especificaron extensiones válidas." >&2
  exit 1
fi

# --- Construir lista de archivos seguros ---
# Usamos nullglob y evitamos globbing en nombres con espacios
mapfile -t FILES < <(
  shopt -s nullglob dotglob
  for ext in "${EXTENSIONS[@]}"; do
    # Generar patrón para cada extensión
    for file in *."$ext"; do
      # Excluir archivo de salida
      [[ "$file" == "$(basename -- "$OUTFILE")" ]] && continue
      # Excluir si coincide con patrón de exclusión
      [[ -n "$EXCLUDE_PATTERN" ]] && [[ "$file" == $EXCLUDE_PATTERN ]] && continue
      # Verificar que es un archivo regular
      [[ -f "$file" ]] && printf '%s\n' "$file"
    done
  done | sort -f
)

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "Error: No se encontraron archivos con extensiones: ${EXTENSIONS[*]}" >&2
  exit 1
fi

# --- Función: slugify seguro para Markdown anchors ---
slugify() {
  local input="$1"
  # Convertir a minúsculas, reemplazar no alfanuméricos por '-', comprimir guiones
  printf '%s' "$input" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g; s/-+/-/g' \
    || printf 'unknown'
}

# --- Función: extraer metadatos (Título y URL) con manejo robusto de espacios ---
extract_meta() {
  local file="$1"
  local title="" url=""

  # Extraer Título: (ignorar líneas vacías o comentarios)
  title=$(grep -m1 -E '^[#[:space:]]*Título:[[:space:]]' "$file" 2>/dev/null \
    | sed -E 's/^[#[:space:]]*Título:[[:space:]]*//; s/^[[:space:]]+|[[:space:]]+$//g') || true

  # Extraer URL:
  url=$(grep -m1 -E '^[#[:space:]]*URL:[[:space:]]' "$file" 2>/dev/null \
    | sed -E 's/^[#[:space:]]*URL:[[:space:]]*//; s/^[[:space:]]+|[[:space:]]+$//g') || true

  # Fallback: primera línea no vacía como título
  if [[ -z "$title" ]]; then
    title=$(awk 'NF { print; exit }' "$file" 2>/dev/null | tr -d '\r' | cut -c1-120)
    [[ -z "$title" ]] && title="$(basename -- "$file")"
  fi

  # Escapar tabuladores y pipes en título para evitar romper la tabla
  # Devolver como campo separado por tabulador (seguro para read)
  printf '%s\t%s\n' "$title" "$url"
}

# --- Generar portada ---
{
  echo "# $TITLE"
  echo
  echo "- **Generado en:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
  echo "- **Directorio:** \`$(pwd)\`"
  echo "- **Archivos incluidos:** ${#FILES[@]}"
  echo "- **Extensiones:** ${EXTENSIONS[*]}"
  echo
  echo "---"
  echo
  echo "## Tabla de contenidos"
} > "$OUTFILE"

# --- Generar TOC y metadatos en archivos temporales ---
TOC_FILE="$TMPDIR/toc.txt"
META_FILE="$TMPDIR/meta.tsv"
> "$TOC_FILE" && > "$META_FILE"

for f in "${FILES[@]}"; do
  IFS=$'\t' read -r title url < <(extract_meta "$f")
  anchor=$(slugify "$title")
  echo "- [$title](#${anchor}) — \`$f\`" >> "$TOC_FILE"
  printf '%s\t%s\t%s\t%s\n' "$f" "$title" "$url" "$anchor" >> "$META_FILE"
done

cat "$TOC_FILE" >> "$OUTFILE"
echo -e "\n---\n" >> "$OUTFILE"

# --- Índice de metadatos en tabla Markdown ---
{
  echo "## Índice de archivos (metadatos)"
  echo
  echo "| Archivo | Título detectado | URL | Anchor |"
  echo "|---|---|---|---|"
  while IFS=$'\t' read -r f title url anchor; do
    # Escapar pipes en título y URL para evitar romper tabla Markdown
    title="${title//|/\\|}"
    url="${url//|/\\|}"
    [[ -z "$url" ]] && url="N/A"
    echo "| \`$f\` | $title | $url | \`#${anchor}\` |"
  done < "$META_FILE"
  echo -e "\n---\n"
} >> "$OUTFILE"

# --- Agregar contenido de cada archivo ---
while IFS=$'\t' read -r f title url anchor; do
  {
    echo "## $title"
    echo
    echo "**Archivo fuente:** \`$f\`  "
    if [[ -n "$url" ]]; then
      echo "**URL:** $url  "
    else
      echo "**URL:** N/A  "
    fi
    echo "**Anchor:** \`#${anchor}\`"
    echo
    echo "<!-- ---8<--- [BEGIN FILE: $f] ---8<--- -->"
    echo

    # Normalización del contenido:
    # - Convertir CRLF → LF
    # - Eliminar caracteres nulos
    # - Reemplazar tabuladores por 4 espacios
    # - Eliminar espacios en blanco al final de cada línea
    # - Comprimir múltiples líneas vacías consecutivas a una sola
    tr -d '\000' < "$f" \
      | sed -E 's/\r$//' \
      | sed 's/\t/    /g' \
      | sed 's/[[:space:]]*$//' \
      | awk '
          BEGIN { prev_empty = 0 }
          {
            if (/^[[:space:]]*$/) {
              if (!prev_empty) { print }
              prev_empty = 1
            } else {
              print
              prev_empty = 0
            }
          }'
    echo
    echo "<!-- ---8<--- [END FILE: $f] ---8<--- -->"
    echo -e "\n---\n"
  } >> "$OUTFILE"
done < "$META_FILE"

echo "✅ Corpus creado: $OUTFILE"
