#!/bin/bash
# conda_finder.sh
# Analiza los imports de un script Python (o directorio) y recomienda
# el entorno conda que mejor satisface sus dependencias.
#
# Uso:
#   ./conda_finder.sh script.py
#   ./conda_finder.sh /ruta/al/proyecto/
#   ./conda_finder.sh script.py --top 5
#   ./conda_finder.sh script.py --detail
#
# Opciones:
#   --top N      Mostrar solo los N mejores entornos
#   --detail     Mostrar qué paquetes faltan en cada entorno
#   -h, --help   Mostrar esta ayuda

# ==================== COLORES ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

show_help() {
    echo ""
    echo -e "${BOLD}conda_finder${NC} — Recomienda el entorno conda para un script Python"
    echo ""
    echo -e "${BOLD}USO:${NC}"
    echo "  ./conda_finder.sh <archivo.py | directorio/> [OPCIONES]"
    echo ""
    echo -e "${BOLD}OPCIONES:${NC}"
    echo "  --top N     Mostrar solo los N mejores entornos"
    echo "  --detail    Mostrar paquetes encontrados y faltantes"
    echo "  -h, --help  Mostrar esta ayuda"
    echo ""
    echo -e "${BOLD}EJEMPLOS:${NC}"
    echo "  ./conda_finder.sh mi_script.py"
    echo "  ./conda_finder.sh ~/proyecto/ --top 3"
    echo "  ./conda_finder.sh analisis.py --detail"
    echo ""
}

# ==================== ARGUMENTOS ====================
TARGET=""
TOP_N=999
DETAIL="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)   show_help; exit 0 ;;
        --top)       TOP_N="$2"; shift 2 ;;
        --detail)    DETAIL="true"; shift ;;
        *)
            if [[ -z "$TARGET" ]]; then
                TARGET="$1"
            else
                echo -e "${RED}Opción desconocida: $1${NC}"
                show_help; exit 1
            fi
            shift ;;
    esac
done

if [[ -z "$TARGET" ]]; then
    echo -e "${RED}Error: debes indicar un archivo Python o directorio.${NC}"
    show_help; exit 1
fi

if [[ ! -e "$TARGET" ]]; then
    echo -e "${RED}Error: '$TARGET' no existe.${NC}"
    exit 1
fi

# ==================== VERIFICAR DEPENDENCIAS ====================
if ! command -v conda &>/dev/null; then
    echo -e "${RED}Error: conda no está disponible en el PATH.${NC}"
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    echo -e "${RED}Error: python3 no está disponible.${NC}"
    exit 1
fi

# ==================== SCRIPT PYTHON PRINCIPAL ====================
# Todo el análisis se hace en Python para evitar problemas
# con heredocs anidados y caracteres especiales en bash.

python3 << PYEOF
import ast
import os
import sys
import json
import subprocess

# ── Parámetros desde bash ──────────────────────────────────────────
TARGET = """$TARGET"""
TOP_N  = $TOP_N
DETAIL = $DETAIL == "true" if False else """$DETAIL""" == "true"

# ── Colores ────────────────────────────────────────────────────────
R   = "\033[0;31m"
G   = "\033[0;32m"
Y   = "\033[1;33m"
B   = "\033[0;34m"
C   = "\033[0;36m"
BOL = "\033[1m"
NC  = "\033[0m"

# ── Biblioteca estándar ────────────────────────────────────────────
STDLIB = {
    "abc","aifc","argparse","array","ast","asynchat","asyncio","asyncore",
    "atexit","audioop","base64","bdb","binascii","binhex","bisect","builtins",
    "bz2","calendar","cgi","cgitb","chunk","cmath","cmd","code","codecs",
    "codeop","collections","colorsys","compileall","concurrent","configparser",
    "contextlib","contextvars","copy","copyreg","cProfile","csv","ctypes",
    "curses","dataclasses","datetime","dbm","decimal","difflib","dis",
    "doctest","email","encodings","enum","errno","faulthandler","fcntl",
    "filecmp","fileinput","fnmatch","fractions","ftplib","functools","gc",
    "getopt","getpass","gettext","glob","grp","gzip","hashlib","heapq",
    "hmac","html","http","idlelib","imaplib","imghdr","imp","importlib",
    "inspect","io","ipaddress","itertools","json","keyword","linecache",
    "locale","logging","lzma","mailbox","marshal","math","mimetypes","mmap",
    "modulefinder","multiprocessing","netrc","numbers","operator","optparse",
    "os","pathlib","pdb","pickle","pickletools","pkgutil","platform",
    "plistlib","poplib","posix","posixpath","pprint","profile","pstats",
    "pty","pwd","py_compile","pyclbr","pydoc","queue","random","re",
    "readline","reprlib","resource","rlcompleter","runpy","sched","secrets",
    "select","selectors","shelve","shlex","shutil","signal","site","smtplib",
    "socket","socketserver","sqlite3","ssl","stat","statistics","string",
    "struct","subprocess","sys","sysconfig","tarfile","tempfile","textwrap",
    "threading","time","timeit","tkinter","token","tokenize","tomllib",
    "trace","traceback","tracemalloc","types","typing","unicodedata",
    "unittest","urllib","uuid","venv","warnings","wave","weakref",
    "webbrowser","xml","xmlrpc","zipapp","zipfile","zipimport","zlib",
    "zoneinfo","_thread","__future__","typing_extensions","distutils",
    "lib2to3","ntpath","posixpath","genericpath","fnmatch","sre_compile",
    "sre_constants","sre_parse","nis","tty","termios","fcntl","grp","spwd",
}

# ── Mapeo import → nombre de paquete conda/pip ────────────────────
PKG_MAP = {
    "sklearn":          "scikit-learn",
    "skimage":          "scikit-image",
    "PIL":              "pillow",
    "cv2":              "opencv",
    "bs4":              "beautifulsoup4",
    "yaml":             "pyyaml",
    "dotenv":           "python-dotenv",
    "Crypto":           "pycryptodome",
    "git":              "gitpython",
    "wx":               "wxpython",
    "serial":           "pyserial",
    "OpenGL":           "pyopengl",
    "googleapiclient":  "google-api-python-client",
    "pydantic":         "pydantic",
    "fastapi":          "fastapi",
    "uvicorn":          "uvicorn",
    "sqlalchemy":       "sqlalchemy",
    "alembic":          "alembic",
    "celery":           "celery",
    "aiohttp":          "aiohttp",
    "httpx":            "httpx",
    "paramiko":         "paramiko",
    "click":            "click",
    "rich":             "rich",
    "typer":            "typer",
    "librosa":          "librosa",
    "soundfile":        "soundfile",
    "pyaudio":          "pyaudio",
    "spacy":            "spacy",
    "nltk":             "nltk",
    "gensim":           "gensim",
    "transformers":     "transformers",
    "datasets":         "datasets",
    "diffusers":        "diffusers",
    "accelerate":       "accelerate",
    "langchain":        "langchain",
    "openai":           "openai",
    "anthropic":        "anthropic",
    "tiktoken":         "tiktoken",
    "chromadb":         "chromadb",
    "qdrant_client":    "qdrant-client",
    "faiss":            "faiss-cpu",
    "streamlit":        "streamlit",
    "gradio":           "gradio",
    "plotly":           "plotly",
    "bokeh":            "bokeh",
    "altair":           "altair",
    "dash":             "dash",
    "flask":            "flask",
    "django":           "django",
    "starlette":        "starlette",
    "pyspark":          "pyspark",
    "dask":             "dask",
    "numba":            "numba",
    "cudf":             "cudf",
    "cuml":             "cuml",
    "xgboost":          "xgboost",
    "lightgbm":         "lightgbm",
    "catboost":         "catboost",
    "optuna":           "optuna",
    "mlflow":           "mlflow",
    "wandb":            "wandb",
    "pyarrow":          "pyarrow",
    "polars":           "polars",
    "openpyxl":         "openpyxl",
    "docx":             "python-docx",
    "pptx":             "python-pptx",
    "fitz":             "pymupdf",
    "scrapy":           "scrapy",
    "selenium":         "selenium",
    "playwright":       "playwright",
    "pytesseract":      "pytesseract",
    "sympy":            "sympy",
    "statsmodels":      "statsmodels",
    "pymc":             "pymc",
}

# ── Extracción de imports ──────────────────────────────────────────
def extract_imports(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return set()
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports

raw_imports = set()
files_analyzed = []

if os.path.isfile(TARGET):
    if not TARGET.endswith(".py"):
        print(f"{R}Error: '{TARGET}' no es un archivo .py{NC}")
        sys.exit(1)
    raw_imports = extract_imports(TARGET)
    files_analyzed = [TARGET]
elif os.path.isdir(TARGET):
    for root, _, files in os.walk(TARGET):
        for fname in files:
            if fname.endswith(".py"):
                fp = os.path.join(root, fname)
                raw_imports |= extract_imports(fp)
                files_analyzed.append(fp)

third_party = {imp for imp in raw_imports if imp not in STDLIB}
packages = {imp: PKG_MAP.get(imp, imp).lower() for imp in third_party}

# ── Cabecera ───────────────────────────────────────────────────────
print(f"\n{BOL}{B}══════════════════════════════════════════════════{NC}")
print(f"{BOL}{B}   CONDA FINDER — Análisis de dependencias{NC}")
print(f"{BOL}{B}══════════════════════════════════════════════════{NC}\n")
print(f"{C}Analizando:{NC} {TARGET}")
if os.path.isdir(TARGET):
    print(f"{C}Archivos .py encontrados:{NC} {len(files_analyzed)}")
print()
print(f"{BOL}Imports detectados:{NC}")
print(f"  Stdlib (descartados):  {len(raw_imports - third_party)}")
print(f"  Terceros a analizar:   {BOL}{len(third_party)}{NC}")

if not packages:
    print(f"\n{Y}No hay dependencias de terceros. Cualquier entorno servirá.{NC}\n")
    sys.exit(0)

print(f"\n  {C}Paquetes a buscar:{NC}")
for imp, pkg in sorted(packages.items()):
    arrow = f"  → {pkg}" if imp.lower() != pkg else ""
    print(f"    {imp}{arrow}")

# ── Obtener entornos conda ─────────────────────────────────────────
print(f"\n{C}Analizando entornos conda...{NC}\n")

try:
    result = subprocess.run(
        ["conda", "info", "--envs"],
        capture_output=True, text=True, timeout=30
    )
    env_lines = result.stdout.strip().split("\n")
except Exception as e:
    print(f"{R}Error al obtener entornos: {e}{NC}")
    sys.exit(1)

envs = []
for line in env_lines:
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    parts = line.split()
    name = parts[0]
    if name == "*":
        name = "base"
    envs.append(name)

print(f"  Entornos encontrados: {len(envs)}")
print()

# ── Analizar cada entorno ──────────────────────────────────────────
results = []
total = len(packages)

for i, env in enumerate(envs):
    print(f"  [{i+1:2d}/{len(envs)}] {env:<30}", end="", flush=True)

    try:
        r = subprocess.run(
            ["conda", "list", "-n", env],
            capture_output=True, text=True, timeout=30
        )
        env_pkgs = set()
        for line in r.stdout.strip().split("\n"):
            if line.startswith("#") or not line.strip():
                continue
            pkg_name = line.split()[0].lower()
            env_pkgs.add(pkg_name)

        found   = []
        missing = []
        for imp, pkg in packages.items():
            pkg_base = pkg.split("-")[0]  # faiss-cpu → faiss
            if (pkg in env_pkgs or
                    imp.lower() in env_pkgs or
                    pkg_base in env_pkgs or
                    any(p.startswith(pkg_base) for p in env_pkgs)):
                found.append(imp)
            else:
                missing.append(imp)

        score = len(found)
        pct   = (score / total * 100) if total > 0 else 0
        results.append((pct, score, env, found, missing))
        print(f"  {score}/{total} paquetes ({pct:.0f}%)")

    except subprocess.TimeoutExpired:
        print(f"  timeout")
    except Exception as e:
        print(f"  error: {e}")

# ── Mostrar resultados ─────────────────────────────────────────────
results.sort(reverse=True, key=lambda x: x[0])
top_results = results[:TOP_N]

print(f"\n{BOL}{B}══════════════════════════════════════════════════{NC}")
print(f"{BOL}{B}   RESULTADOS — Entornos por compatibilidad{NC}")
print(f"{BOL}{B}══════════════════════════════════════════════════{NC}\n")

for rank, (pct, score, env, found, missing) in enumerate(top_results, 1):
    if pct == 100:
        color, badge = G, "PERFECTO ✓"
    elif pct >= 75:
        color, badge = G, "MUY BUENO"
    elif pct >= 50:
        color, badge = Y, "PARCIAL"
    elif pct >= 25:
        color, badge = Y, "BAJO"
    else:
        color, badge = R, "POBRE"

    bar_len = 25
    filled  = int(bar_len * pct / 100)
    bar     = "█" * filled + "░" * (bar_len - filled)

    print(f"{BOL}#{rank}{NC}  {color}{BOL}{env}{NC}")
    print(f"    [{color}{bar}{NC}] {color}{pct:.0f}%{NC}  ({score}/{total})  {BOL}{color}{badge}{NC}")

    if DETAIL:
        if found:
            print(f"    {G}Encontrados:{NC} {', '.join(found)}")
        if missing:
            print(f"    {R}Faltan:     {NC} {', '.join(missing)}")
    print()

if top_results:
    best_env = top_results[0][2]
    best_pct = top_results[0][0]
    print(f"{'='*50}")
    print(f"{BOL}{C}RECOMENDACIÓN:{NC}  conda activate {BOL}{best_env}{NC}  ({best_pct:.0f}% compatible)")
    print(f"{'='*50}\n")
PYEOF
