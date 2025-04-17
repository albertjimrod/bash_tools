# Script para Instalar Entornos de Conda desde Archivos YAML

Este script de Bash automatiza el proceso de crear entornos de Conda a partir de archivos YAML que se encuentren en un directorio especificado.

## Funcionalidades

* **Instalación de Entornos:** Crea entornos de Conda utilizando las definiciones encontradas en archivos `.yaml`.
* **Búsqueda Automática:** Busca todos los archivos con extensión `.yaml` dentro del directorio configurado.
* **Validación de Directorio:** Verifica que el directorio especificado para buscar los archivos YAML exista.
* **Informes Detallados:** Muestra mensajes en la terminal indicando el estado de la instalación de cada entorno.
* **Manejo de Errores:** Informa si no se encuentran archivos YAML o si hay errores durante la creación de algún entorno.

## Requisitos Previos

Antes de ejecutar este script, asegúrate de tener lo siguiente:

1.  **Bash:** El script está escrito en Bash, por lo que necesitarás un sistema operativo compatible (Linux, macOS, o un entorno Bash en Windows).
2.  **Conda:** Debes tener Conda instalado y configurado en tu sistema local. Los archivos YAML deben ser válidos para que `conda env create` funcione correctamente.

## Configuración

Antes de ejecutar el script, puedes modificar la siguiente variable al inicio del archivo:

* `DIRECTORIO_YAML="./"`: Reemplaza `"./"` con la ruta del directorio donde tienes guardados los archivos `.yaml` que definen tus entornos de Conda. Por defecto, busca en el directorio actual.

**Ejemplo de Configuración:**

```bash
#!/bin/bash

# Configuración
DIRECTORIO_YAML="/ruta/a/mis/entornos_yaml"
