# 🧹 Conda Cleaner Pro

[![Bash](https://img.shields.io/badge/Bash-Script-4285F4?style=flat&logo=gnu-bash)](https://www.gnu.org/software/bash/)
[![Conda](https://img.shields.io/badge/Conda-Compatible-44A833?style=flat&logo=anaconda)](https://conda.io/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS-lightgrey)]()

**Automatically detect and safely remove duplicate Conda environments to reclaim disk space.**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [How It Works](#how-it-works)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Output Examples](#output-examples)
- [Safety Features](#safety-features)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)
- [License](#license)

---

## 📖 Overview

**Conda Cleaner Pro** is a Bash script that identifies duplicate Conda environments by comparing their installed packages using MD5 hash fingerprinting. It calculates disk usage, warns about size discrepancies, and inspects for personal files before deletion—helping you safely reclaim gigabytes of disk space.

### Why This Exists

Conda environments can accumulate over time, often with multiple copies of the same package configuration created during experimentation. Each environment can consume **500MB to 5GB+** of disk space. This tool helps you:

- ✅ Identify exact duplicate environments
- ✅ Calculate recoverable space
- ✅ Detect personal files before deletion
- ✅ Avoid accidental data loss

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Hash-Based Detection** | Uses MD5 hash of `conda list --export` to find identical environments |
| 💾 **Disk Space Analysis** | Calculates size of each environment and total recoverable space |
| ⚠️ **Size Discrepancy Alerts** | Warns if duplicate environments differ by >100MB (possible personal files) |
| 📂 **Personal File Inspection** | Scans for `.py`, `.ipynb`, `.csv`, `.json` outside `site-packages` |
| 🐘 **Large File Detection** | Flags files larger than 50MB within environments |
| 🛡️ **Safety Protections** | Never suggests deleting `base` or currently active environment |
| 🎨 **Color-Coded Output** | Clear visual indicators for warnings, errors, and safe operations |
| 📊 **Summary Report** | Shows total space recoverable across all duplicate groups |

---

## ⚙️ How It Works

### 1. Environment Scanning
```bash
conda env list  # Get all environment names and paths
```

### 2. Hash Generation
For each environment, the script creates a unique fingerprint:
```bash
conda list --prefix <ENV_PATH> --export | md5sum
```
This produces an MD5 hash based on **exact package versions**. If two environments have the same hash, they are functionally identical.

### 3. Size Calculation
```bash
du -sb <ENV_PATH>  # Get size in bytes
```

### 4. Duplicate Grouping
Environments with matching hashes are grouped together. The first in each group is marked as "keep," the rest as "candidates for deletion."

### 5. Safety Inspection (Optional)
Before deletion, the script can scan for:
- Personal files (`.py`, `.ipynb`, `.csv`, `.json`)
- Large files (>50MB)
- Cache and log files

### 6. Report Generation
Displays actionable commands to remove duplicates safely.

---

## 📦 Requirements

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Bash** | 4.0+ | Required for associative arrays |
| **Conda** | Any | Miniconda or Anaconda |
| **OS** | Linux/macOS | Windows requires WSL |
| **Commands** | `md5sum`, `du`, `find`, `awk` | Pre-installed on most Unix systems |

### Check Your Bash Version
```bash
bash --version  # Should be 4.0 or higher
```

---

## 🚀 Installation

### Option 1: Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/conda-cleaner-pro.git
cd conda-cleaner-pro
chmod +x conda_cleaner.sh
```

### Option 2: Direct Download
```bash
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/conda-cleaner-pro/main/conda_cleaner.sh
chmod +x conda_cleaner.sh
```

### Option 3: Manual Copy
1. Copy the script content to a file named `conda_cleaner.sh`
2. Make it executable:
```bash
chmod +x conda_cleaner.sh
```

---

## 📖 Usage

### Basic Execution
```bash
./conda_cleaner.sh
```

### With Full Path
```bash
bash /path/to/conda_cleaner.sh
```

### Recommended: Add to PATH
```bash
# Move to local bin
sudo mv conda_cleaner.sh /usr/local/bin/conda-cleaner

# Run from anywhere
conda-cleaner
```

---

## 📊 Output Examples

### Scan Phase
```
════════════════════════════════════════════════════════
🔍 Escaneando entornos Conda...
```

### Duplicate Detection
```
════════════════════════════════════════════════════════
=== Resultados ===

▶ ⚠️  GRUPO DUPLICADO (8 entornos idénticos)
   Entornos y tamaños:
   [0] ml_env_v1 (1.25 GB)
   [1] ml_env_v2 (1.25 GB)
   [2] test_env (1.25 GB)
   ...
   
   ⚠️  ALERTA: 150.00 MB de diferencia entre el más grande y pequeño
   
   📦 Paquetes compartidos (ejemplo):
      # This file may be used to create an environment using:
      # $ conda create --name <env> --file <this file>
      @EXPLICIT
      https://repo.anaconda.com/pkgs/main/linux-64/python-3.9.0...
      ... (y 145 paquetes totales)
   
   💾 Espacio liberable: 8.75 GB
   💡 Mantener: 'ml_env_v1' | Borrar el resto
```

### Inspection Phase
```
▶ 📂 Inspección profunda: ml_env_v2
   📍 Ruta: /home/user/miniconda4/envs/ml_env_v2
   📏 Tamaño: 1.25 GB
   ✅ No hay archivos personales evidentes
   🐘 Archivos grandes (>50MB):
      148M /home/user/miniconda4/envs/ml_env_v2/lib/python3.10/site-packages/faiss/_swigfaiss.cpython-310-x86_64-linux-gnu.so
   🗑️  Basura: __pycache__ (2.5 MB) | Logs (1.2 MB)
```

### Summary
```
════════════════════════════════════════════════════════
=== Resumen ===
💾 Espacio TOTAL liberable: 8.75 GB
📊 Entornos candidatos a borrar: 7

📋 Comandos para eliminar (uno por uno):
   conda env remove -n ml_env_v2
   conda env remove -n test_env
   ...

⚠️  Nunca elimines el entorno base o el activo
════════════════════════════════════════════════════════
```

---

## 🛡️ Safety Features

| Protection | Description |
|------------|-------------|
| **Base Environment** | Never includes `base` in scan results |
| **Active Environment** | Skips currently active environment (marked with `*`) |
| **Size Discrepancy Warning** | Alerts if duplicates differ by >100MB |
| **Personal File Detection** | Scans for user files outside `site-packages` |
| **Manual Confirmation** | Requires user confirmation before any deletion |
| **No Auto-Delete** | Script never deletes automatically—only suggests commands |
| **Path Validation** | Verifies environment paths exist before inspection |

### Files Considered "Personal" (Warning Triggered)
- `*.py` — Python scripts
- `*.ipynb` — Jupyter notebooks
- `*.csv` — Data files
- `*.json` — Configuration/data files
- `*.txt`, `*.md` — Documentation

### Files Considered "Safe to Delete"
- `__pycache__/` — Python bytecode cache
- `*.pyc` — Compiled Python files
- `*.log` — Log files
- `pip-cache/` — Pip installation cache
- `*.tmp` — Temporary files

---

## 🔧 Troubleshooting

### Issue: "conda no está disponible en el PATH"
**Solution:**
```bash
# Initialize conda for your shell
conda init bash
source ~/.bashrc
```

### Issue: "md5sum: command not found"
**Solution (macOS):**
```bash
# macOS uses md5 instead of md5sum
# Replace md5sum with md5 -r in the script
```

### Issue: "Permission denied"
**Solution:**
```bash
chmod +x conda_cleaner.sh
```

### Issue: Script shows all environments with same path
**Solution:** Ensure you're using the latest version (v2.0+) which fixed the PATH_MAP array bug.

### Issue: False positives on duplicates
**Explanation:** Environments with identical package versions will match. This is intended behavior—if packages are the same, one environment is redundant.

---

## ⚙️ Technical Details

### Hash Algorithm
```bash
# Creates fingerprint from exact package versions
conda list --prefix <PATH> --export | md5sum | awk '{print $1}'
```

### Size Calculation
```bash
# Gets total directory size in bytes
du -sb <ENV_PATH> | awk '{print $1}'
```

### Personal File Detection
```bash
# Finds user files outside conda-managed directories
find <PATH> -type f \( -name "*.py" -o -name "*.ipynb" \) \
  -not -path "*/site-packages/*" \
  -not -path "*/lib/*" \
  -not -path "*/share/*"
```

### Configuration Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `WARN_SIZE_DIFF` | 104857600 | Alert threshold (100MB in bytes) |
| `LARGE_FILE_THRESHOLD` | "50M" | Large file detection threshold |

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📧 Support

For issues, questions, or suggestions:
- 🐛 Open an [Issue](https://github.com/YOUR_USERNAME/conda-cleaner-pro/issues)
- 📧 Contact: [your.email@example.com](mailto:your.email@example.com)

---

## 🙏 Acknowledgments

- [Conda](https://conda.io/) - Package and environment management
- [GNU Bash](https://www.gnu.org/software/bash/) - Shell scripting
- Community contributors for bug reports and feature suggestions

---

<div align="center">

**Made with ❤️ for the Data Science Community**

[⬆ Back to Top](#-conda-cleaner-pro)

</div>