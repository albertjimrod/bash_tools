#!/bin/bash

# Configuración
DIRECTORIO_YAML="./"  # Cambia esto por el directorio donde tienes los archivos .yaml

# Verifica si el directorio existe
if [ ! -d "$DIRECTORIO_YAML" ]; then
    echo "El directorio $DIRECTORIO_YAML no existe. Por favor, verifica la ruta."
    exit 1
fi

echo "Buscando archivos .yaml en $DIRECTORIO_YAML..."

# Buscar archivos .yaml en el directorio especificado
ARCHIVOS_YAML=$(ls $DIRECTORIO_YAML/*.yaml 2>/dev/null)

# Verifica si hay archivos .yaml
if [ -z "$ARCHIVOS_YAML" ]; then
    echo "No se encontraron archivos .yaml en $DIRECTORIO_YAML."
    exit 1
fi

# Iterar sobre los archivos .yaml y crear los entornos
for ARCHIVO in $ARCHIVOS_YAML; do
    NOMBRE_ENTORNO=$(basename "$ARCHIVO" .yaml)  # Obtener el nombre del entorno del archivo
    echo "Instalando el entorno $NOMBRE_ENTORNO desde $ARCHIVO..."

    # Crear el entorno desde el archivo YAML
    conda env create --file "$ARCHIVO"

    # Verificar si el entorno se creó correctamente
    if [ $? -eq 0 ]; then
        echo "Entorno $NOMBRE_ENTORNO instalado correctamente."
    else
        echo "Hubo un error al instalar el entorno $NOMBRE_ENTORNO. Revisa el archivo $ARCHIVO."
    fi
done

echo "Proceso de instalación de entornos completado."

