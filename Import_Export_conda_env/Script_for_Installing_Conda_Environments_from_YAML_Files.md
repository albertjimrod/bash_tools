# Script for Installing Conda Environments from YAML Files

This Bash script automates the process of creating Conda environments from YAML files located in a specified directory.

## Features

* **Environment Installation:** Creates Conda environments using definitions found in `.yaml` files.
* **Automatic Search:** Automatically searches for all `.yaml` files within the configured directory.
* **Directory Validation:** Checks if the specified directory to search for YAML files exists.
* **Detailed Reports:** Displays messages in the terminal indicating the status of each environment installation.
* **Error Handling:** Notifies if no `.yaml` files are found or if there are errors during the creation of any environment.

## Prerequisites

Before running this script, ensure you have:

1.  **Bash:** The script is written in Bash, so you need a compatible operating system (Linux, macOS, or a Bash environment on Windows).
2.  **Conda:** Conda should be installed and configured on your local system. The YAML files must be valid for `conda env create` to work correctly.

## Configuration

Before running the script, you can modify the following variable at the beginning of the file:

* `DIRECTORIO_YAML="./"`: Replace `"./"` with the path to the directory where you have stored your `.yaml` files that define your Conda environments. By default, it looks in the current directory.

**Example Configuration:**

```bash
#!/bin/bash

# Configuration
DIRECTORIO_YAML="/path/to/my/conda_yaml_files/"
```
