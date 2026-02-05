#!/bin/bash

# Inicializa Conda en el entorno del script
eval "$(conda shell.bash hook)" || { echo "Error: No se pudo inicializar Conda."; exit 1; }

# Solicita el paquete que el usuario quiere buscar
read -p "¿Qué paquete de Conda estás buscando? " busco

# Obtiene la lista de entornos de Conda
envs=$(conda info --envs | awk 'NR > 2 {print $1}')  # Excluye encabezados

# Verifica si hay entornos disponibles
if [ -z "$envs" ]; then
    echo "No se encontraron entornos de Conda."
    exit 1
fi

# Itera sobre cada entorno
for env in $envs; do
    echo "Verificando en el entorno: $env"

    # Activa el entorno
    conda activate "$env" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "❌ Error al activar el entorno $env. Continuando con el siguiente..."
        continue
    fi

    # Comprueba si el paquete está instalado
    if conda list "$busco" | grep  "$busco"; then
        echo "✅ $busco está instalado en el entorno $env"
    else
        echo "❌ $busco no está instalado en el entorno $env"
    fi

    # Desactiva el entorno
    conda deactivate
done

