#!/bin/bash

# Configuración
USUARIO_DESTINO="ion"        # Cambia esto por el nombre de usuario de la máquina destino
MAQUINA_DESTINO="192.168.98.102"        # Cambia esto por la IP o el hostname de la máquina destino
DIRECTORIO_DESTINO="~/"       # Cambia esto por el directorio en la máquina destino donde guardarás los archivos

# Crear una carpeta temporal para almacenar los archivos YAML
TEMP_DIR="./entornos_yaml"
mkdir -p $TEMP_DIR

echo "Exportando los entornos de Conda..."

# Exportar todos los entornos de Conda excepto el base
for ENV in $(conda env list | awk '{print $1}' | grep -v "#" | grep -v "base"); do
    echo "Exportando entorno: $ENV"
    conda env export --name $ENV > $TEMP_DIR/${ENV}.yaml
done

echo "Todos los entornos han sido exportados a la carpeta $TEMP_DIR."

# Transferir los archivos YAML a la otra máquina
echo "Copiando los archivos YAML a $USUARIO_DESTINO@$MAQUINA_DESTINO:$DIRECTORIO_DESTINO..."
scp $TEMP_DIR/*.yaml $USUARIO_DESTINO@$MAQUINA_DESTINO:$DIRECTORIO_DESTINO

if [ $? -eq 0 ]; then
    echo "¡Archivos transferidos exitosamente!"
else
    echo "Hubo un error al transferir los archivos."
fi

# Limpiar la carpeta temporal
rm -rf $TEMP_DIR
echo "Carpeta temporal eliminada. Proceso completado."

