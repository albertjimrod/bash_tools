
# 🐍 Conda Environment Comparator  
An advanced command-line tool in Bash for comparing installed packages between different Conda environments, with detailed descriptions and integrated installation commands.

![Bash](https://img.shields.io/badge/bash-4.0+-green.svg)  
![Python](https://img.shields.io/badge/python-3.6+-blue.svg)  
![License](https://img.shields.io/badge/license-MIT-blue.svg)  
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20WSL-lightgrey.svg)

---

## 📋 Table of Contents
- [What is it?](#what-is-it)
- [What is it for?](#what-is-it-for)
- [Main features](#main-features)
- [Requirements](#requirements)
- [How to use it](#how-to-use-it)
- [Usage examples](#usage-examples)
- [Output formats](#output-formats)
- [License](#license)

---

## What is it?

`conda-comparator.sh` is a Bash script designed to help you compare the packages installed across multiple Conda environments. It displays a **visual matrix** showing which packages are present or missing in each environment, along with helpful descriptions and installation commands.

!()[comparador_entornos.png]

---

## What is it for?

This script is perfect when you have multiple development environments and want to:
- Easily compare what packages are installed.
- Identify inconsistencies between environments.
- Export results for audits, migrations, or documentation.
- Quickly find specific installation commands per package.

---

## Main Features

- 🔍 **Automatic analysis** of all available Conda environments.
- 📊 **Visual matrix** showing package presence/absence per environment.
- 📚 **Integrated database** with descriptions of over 60 popular packages.
- 🛠️ **Specific installation commands** for each package.
- 📁 **CSV export** with full information (description, command, and installation status per environment).
- 🎨 **Colorized interface** for better terminal readability.
- 📈 Statistics and contextual tips during execution.

---

## Requirements

- **Conda/Miniconda/Anaconda** installed and configured.
- **Bash** 4.0 or higher.
- **Python 3.6+** (required for JSON processing).
- Operating System: Linux, macOS, or WSL on Windows.

---

## How to Use It

### Download and Setup
```bash
# Download the script
curl -O https://raw.githubusercontent.com/your-username/conda-env-comparator/main/environment_comparator.sh
# Grant execution permissions
chmod +x environment_comparator.sh
```

### Run basic analysis
```bash
./environment_comparator.sh
```

### Show details with descriptions
```bash
./environment_comparator.sh -d
```

### Export results to CSV
```bash
./environment_comparator.sh -o analysis.csv
```

### View full help
```bash
./environment_comparator.sh --help
```

---

## Usage Examples

| Purpose | Command |
|-------|---------|
| Quick analysis | `./environment_comparator.sh` |
| Detailed analysis | `./environment_comparator.sh -d` |
| Export to CSV | `./environment_comparator.sh -o report.csv` |
| Full analysis | `./environment_comparator.sh -v -d -o full.csv` |

---

## Output Formats

### Console
- **Standard mode:** Compact matrix without descriptions.
- **Detailed mode (-d):** Includes description and installation command.

### CSV File
- Always includes:
  - Package name
  - Description
  - Installation command
  - Status per environment (`✅` / `❌`)

---

## License

This project is under the **MIT License**.  
See the [LICENSE](LICENSE) file for more details.

---

## ✨ Want to contribute?
Contributions are welcome: from adding new packages to improving the script design.  
👉 [View Contribution Guidelines](#contribution)

---

## Author

Developed with ❤️ for the **Data Science** and **Python** community.  
Was this helpful to you? Consider giving a ⭐ to the repository!

---

## Contact

- **Email:** albert@datablogcafe.com

---

<div align="center">
**🚀 Optimize your workflow with Conda Environment Comparator! 🚀**
</div>
```

---

