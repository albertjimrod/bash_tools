#!/bin/bash

# limpiar_duplicados_seguro.sh
# Detecta duplicados por hash (SHA-256) y confirma con diff.
# Soporta múltiples directorios y muestra progreso en tiempo real.

set -euo pipefail

# --- Verificar dependencias ---
for cmd in sha256sum pv diff; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "❌ Error: '$cmd' no está instalado."
        echo "   En Debian/Ubuntu: sudo apt install $([ "$cmd" = "pv" ] && echo "pv" || echo "coreutils")"
        exit 1
    fi
done

# --- Validar argumentos ---
if [ $# -eq 0 ]; then
    echo "Uso: $0 <directorio1> [directorio2] ... [directorioN]"
    echo "Ejemplo: $0 ~/Descargas ~/Documentos"
    exit 1
fi

for dir in "$@"; do
    if [ ! -d "$dir" ]; then
        echo "❌ Error: '$dir' no es un directorio válido."
        exit 1
    fi
done

DIRECTORIOS=("$@")

# --- Archivos temporales ---
temp_hashes=$(mktemp)
trap 'rm -f "$temp_hashes"' EXIT

# --- Contar archivos ---
echo "🔍 Contando archivos..."
total_files=$(find "${DIRECTORIOS[@]}" -type f -printf '.' | wc -c)
if [ "$total_files" -eq 0 ]; then
    echo "⚠️ No se encontraron archivos."
    exit 0
fi

echo "📁 Archivos a procesar: $total_files"
echo ""

# --- Calcular hashes con progreso ---
echo "⏳ Paso 1: Calculando hashes SHA-256..."
export LC_ALL=C

find "${DIRECTORIOS[@]}" -type f -print0 \
  | sort -z \
  | pv -0 -p -t -e -s "$total_files" \
  | xargs -0 sha256sum \
  > "$temp_hashes"

echo ""
echo "✅ Paso 1 completado."
echo ""

# --- Agrupar por hash ---
declare -A hash_groups

while IFS= read -r line; do
    [ -z "$line" ] && continue
    hash="${line:0:64}"
    filepath="${line:66}"
    [ -f "$filepath" ] || continue
    hash_groups["$hash"]+="$filepath"$'\n'
done < "$temp_hashes"

# --- Paso 2: Confirmar duplicados con diff ---
echo "🔍 Paso 2: Verificando duplicados con 'diff'..."
declare -a to_delete
total_duplicates=0

for hash in "${!hash_groups[@]}"; do
    mapfile -t candidates < <(printf '%s' "${hash_groups[$hash]}")
    
    if [ "${#candidates[@]}" -le 1 ]; then
        continue  # No es duplicado
    fi

    # Ordenar alfabéticamente
    IFS=$'\n' sorted_candidates=($(sort <<<"${candidates[*]}"))
    unset IFS

    ref="${sorted_candidates[0]}"
    confirmed_duplicates=()

    # Comparar cada archivo con la referencia usando diff
    for ((i=1; i<${#sorted_candidates[@]}; i++)); do
        candidate="${sorted_candidates[i]}"
        if [ -f "$candidate" ] && diff -q "$ref" "$candidate" >/dev/null 2>&1; then
            confirmed_duplicates+=("$candidate")
        fi
    done

    if [ ${#confirmed_duplicates[@]} -gt 0 ]; then
        echo "  📄 Grupo confirmado ($hash):"
        echo "     Original: $ref"
        for dup in "${confirmed_duplicates[@]}"; do
            echo "     Duplicado: $dup"
        done
        to_delete+=("${confirmed_duplicates[@]}")
        total_duplicates=$((total_duplicates + ${#confirmed_duplicates[@]}))
    fi
done

echo ""
if [ $total_duplicates -eq 0 ]; then
    echo "✅ No se encontraron archivos duplicados."
    exit 0
fi

echo "📊 Total de duplicados confirmados: $total_duplicates"
echo ""

# --- Confirmación y eliminación ---
read -p "¿Eliminar los $total_duplicates archivos duplicados? (s/n): " confirm
if [[ ! "$confirm" =~ ^[Ss]$ ]]; then
    echo "❌ Operación cancelada."
    exit 0
fi

echo ""
echo "🗑️ Eliminando archivos duplicados..."
for f in "${to_delete[@]}"; do
    if [ -f "$f" ]; then
        rm -f "$f"
        echo "  Eliminado: $f"
    fi
done

echo ""
echo "✅ ¡Listo! Se eliminaron $total_duplicates archivos duplicados."
