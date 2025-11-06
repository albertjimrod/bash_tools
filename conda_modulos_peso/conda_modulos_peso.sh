#!/bin/bash

# Mostrar entorno conda activo
echo "Entorno Conda activo: $CONDA_DEFAULT_ENV"
echo

# Verificar que conda esté disponible
if ! command -v conda &> /dev/null; then
    echo "Conda no está instalado o no está en el PATH."
    exit 1
fi

# Verificar si hay un entorno activo
if [ -z "$CONDA_PREFIX" ]; then
    echo "No hay un entorno conda activo."
    echo "Activa un entorno conda antes de ejecutar este script."
    exit 1
fi

# Obtener ruta del entorno
ENV_PATH="$CONDA_PREFIX/lib/python*/site-packages"

# Mostrar paquetes instalados y su peso
echo "Listando paquetes en: $ENV_PATH"
echo

# Calcular tamaño de cada paquete
du -sh $CONDA_PREFIX/lib/python*/site-packages/* 2>/dev/null | sort -hr | head -n 50

