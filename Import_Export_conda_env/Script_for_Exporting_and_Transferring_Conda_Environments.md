# Script for Exporting and Transferring Conda Environments

This Bash script automates the process of exporting all your Conda environments (except the base environment) to individual YAML files and then transfers them to a remote machine using `scp`.

## Features

* **Conda Environment Exportation:** Exports the configuration of each Conda environment (excluding `base`) to an individual `.yaml` file.
* **Remote Transfer:** Uses `scp` to copy all generated YAML files to a specific directory on a remote machine.
* **Automatic Cleanup:** Automatically removes the temporary folder where the YAML files are stored after transfer.
* **Informative Messages:** Provides messages in the terminal to inform the user about the script's progress.

## Prerequisites

Before running this script, ensure you have:

1.  **Bash:** The script is written in Bash, so you need a compatible operating system (Linux, macOS, or a Bash environment on Windows).
2.  **Conda:** Conda should be installed and configured on your local system.
3.  **SSH Access to the Target Machine:** You need SSH access to the remote machine and know the credentials (username and IP address or hostname). `scp` uses SSH for file transfer.

## Configuration

Before running the script, you must modify the following variables at the beginning of the file:

* `USUARIO_DESTINO="ion"`: Replace `"ion"` with your username on the remote machine.
* `MAQUINA_DESTINO="192.168.98.102"`: Replace `"192.168.98.102"` with the IP address or hostname of the remote machine where you want to transfer the environments.
* `DIRECTORIO_DESTINO="~/"`: Replace `"~/"` with the path on the remote machine's directory where you want to save the YAML files. `~/` represents the home directory of the remote user.

**Example Configuration:**

```bash
#!/bin/bash

# Configuration
USUARIO_DESTINO="usuario_remoto"
MAQUINA_DESTINO="mi_servidor.com"
DIRECTORIO_DESTINO="/home/usuario_remoto/entornos_respaldo/"
```
