# Script para Exportar y Transferir Entornos de Conda

Este script de Bash automatiza el proceso de exportar todos tus entornos de Conda (excepto el entorno base) a archivos YAML y luego transferirlos a una máquina remota utilizando `scp`.

## Funcionalidades

* **Exportación de Entornos de Conda:** Exporta la configuración de cada entorno de Conda (excepto el `base`) a un archivo `.yaml` individual.
* **Transferencia Remota:** Utiliza `scp` para copiar todos los archivos YAML generados a un directorio específico en una máquina remota.
* **Limpieza Automática:** Elimina la carpeta temporal donde se almacenan los archivos YAML después de la transferencia.
* **Mensajes Informativos:** Proporciona mensajes en la terminal para informar al usuario sobre el progreso del script.

## Requisitos Previos

Antes de ejecutar este script, asegúrate de tener lo siguiente:

1.  **Bash:** El script está escrito en Bash, por lo que necesitarás un sistema operativo compatible (Linux, macOS, o un entorno Bash en Windows).
2.  **Conda:** Debes tener Conda instalado y configurado en tu sistema local.
3.  **Acceso SSH a la máquina destino:** Necesitarás tener acceso SSH a la máquina remota y conocer las credenciales (nombre de usuario y dirección IP o hostname). `scp` utiliza SSH para la transferencia de archivos.

## Configuración

Antes de ejecutar el script, debes modificar las siguientes variables al inicio del archivo:

* `USUARIO_DESTINO="ion"`: Reemplaza `"ion"` con el nombre de usuario que tienes en la máquina remota.
* `MAQUINA_DESTINO="192.168.98.102"`: Reemplaza `"192.168.98.102"` con la dirección IP o el hostname de la máquina a la que quieres transferir los entornos.
* `DIRECTORIO_DESTINO="~/"`: Reemplaza `"~/"` con la ruta del directorio en la máquina remota donde quieres guardar los archivos YAML. `~/` representa el directorio home del usuario remoto.

**Ejemplo de Configuración:**

```bash
#!/bin/bash

# Configuración
USUARIO_DESTINO="usuario_remoto"
MAQUINA_DESTINO="mi_[servidor.com](https://www.google.com/search?q=servidor.com)"
DIRECTORIO_DESTINO="/home/usuario_remoto/entornos_respaldo/"
