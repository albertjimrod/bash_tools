#!/bin/bash

# Directorio base donde buscar (por defecto, el directorio actual)
BASE_DIR="${1:-.}"

echo "Buscando repositorios Git en: $BASE_DIR"

# Buscar directorios que contengan una carpeta .git
find "$BASE_DIR" -type d -name ".git" 2>/dev/null | while read gitdir; do
    # Imprimir el directorio padre del .git
    echo "Repositorio Git encontrado en: $(dirname "$gitdir")"
done

