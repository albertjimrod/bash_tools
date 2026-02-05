#!/bin/bash

DIRECTORY="/home/ion/Documentos/albertjimrod/ordenar"

if [ ! -d "$DIRECTORY" ]; then
    echo "Error: El directorio '$DIRECTORY' no existe."
    exit 1
fi

# Archivo temporal para hashes
temp_hashes=$(mktemp)
trap 'rm -f "$temp_hashes"' EXIT

echo "Escaneando archivos y calculando hashes SHA256..."

# Encuentra archivos y calcula hashes (maneja espacios en nombres)
find "$DIRECTORY" -type f -print0 | sort -z | xargs -0 sha256sum > "$temp_hashes"

# Leer en un array asociativo: hash -> lista de archivos
declare -A hash_files

while IFS= read -r line; do
    hash="${line:0:64}"                # primeros 64 caracteres = SHA256
    filepath="${line:66}"              # después del espacio
    hash_files["$hash"]+="$filepath"$'\n'
done < "$temp_hashes"

# Mostrar duplicados
duplicates_found=false
declare -a files_to_delete

echo ""
echo "🔍 Archivos duplicados (mismo contenido, distinto nombre/ubicación):"
echo "=================================================================="

for hash in "${!hash_files[@]}"; do
    # Convertir la lista en un array
    mapfile -t files < <(printf '%s' "${hash_files[$hash]}")
    if [ "${#files[@]}" -gt 1 ]; then
        duplicates_found=true
        echo "Hash: $hash"
        echo "  Mantenido: ${files[0]}"
        for ((i=1; i<${#files[@]}; i++)); do
            echo "  Duplicado: ${files[i]}"
            files_to_delete+=("${files[i]}")
        done
        echo ""
    fi
done

if [ "$duplicates_found" = false ]; then
    echo "✅ No se encontraron archivos duplicados."
    exit 0
fi

echo "Total de duplicados detectados: ${#files_to_delete[@]}"

read -p "¿Eliminar los duplicados? (s/n): " confirm
if [[ "$confirm" =~ ^[Ss]$ ]]; then
    for file in "${files_to_delete[@]}"; do
        if [ -f "$file" ]; then
            echo "🗑️ Eliminando: $file"
            rm -f "$file"
        fi
    done
    echo "✅ Duplicados eliminados."
else
    echo "❌ Operación cancelada."
fi
