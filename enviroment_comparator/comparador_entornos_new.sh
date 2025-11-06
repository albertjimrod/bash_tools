#!/bin/bash

# Colores para mejor visualización
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para obtener descripción de paquete
get_package_description() {
    local package="$1"
    
    # Base de datos de descripciones de paquetes comunes
    case "$package" in
        "numpy") echo "Biblioteca fundamental para computación científica con Python" ;;
        "pandas") echo "Biblioteca de análisis y manipulación de datos" ;;
        "matplotlib") echo "Biblioteca de visualización de datos 2D" ;;
        "scipy") echo "Biblioteca de algoritmos científicos y matemáticos" ;;
        "scikit-learn") echo "Biblioteca de machine learning" ;;
        "tensorflow") echo "Plataforma de machine learning de código abierto" ;;
        "pytorch") echo "Framework de deep learning dinámico" ;;
        "jupyter") echo "Entorno interactivo de notebooks" ;;
        "flask") echo "Framework web minimalista para Python" ;;
        "django") echo "Framework web de alto nivel para Python" ;;
        "requests") echo "Biblioteca HTTP elegante y simple" ;;
        "beautifulsoup4") echo "Biblioteca para extraer datos de HTML y XML" ;;
        "selenium") echo "Herramienta de automatización web" ;;
        "pillow") echo "Biblioteca de procesamiento de imágenes" ;;
        "opencv") echo "Biblioteca de visión por computadora" ;;
        "seaborn") echo "Biblioteca de visualización estadística" ;;
        "plotly") echo "Biblioteca de gráficos interactivos" ;;
        "streamlit") echo "Framework para crear aplicaciones web de datos" ;;
        "fastapi") echo "Framework web moderno y rápido para APIs" ;;
        "sqlalchemy") echo "Toolkit SQL y ORM para Python" ;;
        "psycopg2") echo "Adaptador PostgreSQL para Python" ;;
        "pymongo") echo "Driver MongoDB para Python" ;;
        "redis") echo "Cliente Redis para Python" ;;
        "celery") echo "Cola de tareas distribuida" ;;
        "pytest") echo "Framework de testing para Python" ;;
        "black") echo "Formateador de código Python" ;;
        "flake8") echo "Linter de código Python" ;;
        "mypy") echo "Checker de tipos estáticos para Python" ;;
        "jupyterlab") echo "Entorno de desarrollo interactivo basado en web" ;;
        "ipython") echo "Shell interactivo mejorado para Python" ;;
        "dask") echo "Computación paralela flexible para analytics" ;;
        "numba") echo "Compilador JIT para Python y NumPy" ;;
        "cython") echo "Lenguaje de programación que extiende Python" ;;
        "networkx") echo "Biblioteca para análisis de redes complejas" ;;
        "sympy") echo "Biblioteca de matemáticas simbólicas" ;;
        "statsmodels") echo "Biblioteca de modelado estadístico" ;;
        "xgboost") echo "Biblioteca de gradient boosting optimizada" ;;
        "lightgbm") echo "Framework de gradient boosting rápido" ;;
        "catboost") echo "Biblioteca de gradient boosting para datos categóricos" ;;
        "boto3") echo "SDK de AWS para Python" ;;
        "azure-storage-blob") echo "Cliente Azure Blob Storage para Python" ;;
        "google-cloud-storage") echo "Cliente Google Cloud Storage para Python" ;;
        "docker") echo "Cliente Docker para Python" ;;
        "kubernetes") echo "Cliente Kubernetes para Python" ;;
        "pydantic") echo "Validación de datos usando type hints" ;;
        "typer") echo "Biblioteca para crear interfaces de línea de comandos" ;;
        "click") echo "Framework para crear interfaces de línea de comandos" ;;
        "rich") echo "Biblioteca para texto enriquecido y formato en terminal" ;;
        "tqdm") echo "Barras de progreso para bucles de Python" ;;
        "joblib") echo "Biblioteca de computación paralela ligera" ;;
        "h5py") echo "Interfaz Python para el formato de datos HDF5" ;;
        "xlrd") echo "Biblioteca para leer archivos Excel" ;;
        "openpyxl") echo "Biblioteca para leer/escribir archivos Excel 2010" ;;
        "lxml") echo "Biblioteca para procesamiento XML y HTML" ;;
        "pyyaml") echo "Parser y emisor YAML para Python" ;;
        "configparser") echo "Parser de archivos de configuración" ;;
        "argparse") echo "Parser de argumentos de línea de comandos" ;;
        "logging") echo "Biblioteca de logging flexible" ;;
        "datetime") echo "Biblioteca para manejo de fechas y horas" ;;
        "collections") echo "Tipos de datos de contenedores especializados" ;;
        "itertools") echo "Funciones para crear iteradores eficientes" ;;
        "functools") echo "Herramientas de programación funcional" ;;
        "pathlib") echo "Biblioteca orientada a objetos para rutas del sistema" ;;
        "asyncio") echo "Biblioteca para programación asíncrona" ;;
        "multiprocessing") echo "Biblioteca para programación multiproceso" ;;
        "threading") echo "Biblioteca para programación con hilos" ;;
        *) echo "Paquete de Python" ;;
    esac
}

# Función para obtener comando de instalación
get_install_command() {
    local package="$1"
    
    # Comandos especiales para algunos paquetes
    case "$package" in
        "pytorch") echo "conda install pytorch torchvision torchaudio -c pytorch" ;;
        "tensorflow") echo "conda install tensorflow" ;;
        "scikit-learn") echo "conda install scikit-learn" ;;
        "opencv") echo "conda install opencv" ;;
        "beautifulsoup4") echo "conda install beautifulsoup4" ;;
        "pillow") echo "conda install pillow" ;;
        "psycopg2") echo "conda install psycopg2" ;;
        "pymongo") echo "conda install pymongo" ;;
        "azure-storage-blob") echo "pip install azure-storage-blob" ;;
        "google-cloud-storage") echo "pip install google-cloud-storage" ;;
        "boto3") echo "conda install boto3" ;;
        "fastapi") echo "conda install fastapi" ;;
        "streamlit") echo "conda install streamlit" ;;
        "xgboost") echo "conda install xgboost" ;;
        "lightgbm") echo "conda install lightgbm" ;;
        "catboost") echo "conda install catboost" ;;
        *) echo "conda install $package" ;;
    esac
}

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [opciones]"
    echo "Opciones:"
    echo "  -h, --help     Muestra esta ayuda"
    echo "  -o, --output   Guarda el resultado en un archivo CSV con descripciones"
    echo "  -v, --verbose  Muestra información detallada durante el proceso"
    echo "  -d, --details  Incluye descripciones en la salida de consola"
    echo ""
    echo "Esta herramienta compara los paquetes instalados en todos los entornos de Conda"
    echo "y genera una matriz mostrando qué paquetes están presentes en cada entorno,"
    echo "incluyendo descripciones y comandos de instalación."
}

# Variables por defecto
OUTPUT_FILE=""
VERBOSE=false
SHOW_DETAILS=false

# Procesar argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -d|--details)
            SHOW_DETAILS=true
            shift
            ;;
        *)
            echo "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Inicializa Conda en el entorno del script
eval "$(conda shell.bash hook)" || { 
    echo -e "${RED}Error: No se pudo inicializar Conda.${NC}" 
    exit 1 
}

echo -e "${BLUE}🔍 Analizando entornos de Conda...${NC}"

# Obtiene la lista de entornos de Conda (excluyendo base si está presente)
envs_raw=$(conda info --envs | awk 'NR > 2 && !/^#/ {print $1}' | grep -v '^$')

# Convierte a array para mejor manejo
declare -a envs
while IFS= read -r line; do
    [[ -n "$line" ]] && envs+=("$line")
done <<< "$envs_raw"

# Verifica si hay entornos disponibles
if [ ${#envs[@]} -eq 0 ]; then
    echo -e "${RED}No se encontraron entornos de Conda.${NC}"
    exit 1
fi

echo -e "${GREEN}Entornos encontrados: ${#envs[@]}${NC}"
if [ "$VERBOSE" = true ]; then
    printf '%s\n' "${envs[@]}" | sed 's/^/  - /'
fi

# Crear archivo temporal para almacenar todos los paquetes
temp_dir=$(mktemp -d)
all_packages_file="$temp_dir/all_packages.txt"

echo -e "${BLUE}📦 Recopilando paquetes de todos los entornos...${NC}"

# Recopilar todos los paquetes de todos los entornos
declare -A env_packages
for env in "${envs[@]}"; do
    if [ "$VERBOSE" = true ]; then
        echo -e "  ${YELLOW}Procesando entorno: $env${NC}"
    fi
    
    # Activa el entorno y obtiene la lista de paquetes
    packages=$(conda activate "$env" 2>/dev/null && conda list --json 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for pkg in data:
        print(pkg['name'])
except:
    pass
" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$packages" ]; then
        # Almacenar paquetes para este entorno
        env_packages["$env"]="$packages"
        # Agregar paquetes a la lista general
        echo "$packages" >> "$all_packages_file"
    else
        echo -e "${RED}❌ Error al obtener paquetes del entorno $env${NC}"
        env_packages["$env"]=""
    fi
    
    conda deactivate 2>/dev/null
done

# Obtener lista única de todos los paquetes
all_unique_packages=$(sort "$all_packages_file" | uniq)
package_count=$(echo "$all_unique_packages" | wc -l)

echo -e "${GREEN}📊 Total de paquetes únicos encontrados: $package_count${NC}"

# Crear encabezado de la matriz
echo -e "\n${BLUE}🗂️  Matriz de Comparación de Entornos${NC}"
echo "=================================================================="

# Preparar datos para la matriz
declare -a matrix_data
if [ "$SHOW_DETAILS" = true ]; then
    header="Paquete,Descripción,Instalación"
else
    header="Paquete"
fi
for env in "${envs[@]}"; do
    header="$header,$env"
done

if [ -n "$OUTPUT_FILE" ]; then
    echo "$header" > "$OUTPUT_FILE"
fi

# Mostrar encabezado en consola
if [ "$SHOW_DETAILS" = true ]; then
    printf "%-25s %-40s %-35s" "Paquete" "Descripción" "Instalación"
else
    printf "%-30s" "Paquete"
fi
for env in "${envs[@]}"; do
    printf " %-12s" "$env"
done
echo ""

# Línea separadora
if [ "$SHOW_DETAILS" = true ]; then
    printf "%-25s %-40s %-35s" "$(printf '%*s' 25 '' | tr ' ' '-')" "$(printf '%*s' 40 '' | tr ' ' '-')" "$(printf '%*s' 35 '' | tr ' ' '-')"
else
    printf "%-30s" "$(printf '%*s' 30 '' | tr ' ' '-')"
fi
for env in "${envs[@]}"; do
    printf " %-12s" "$(printf '%*s' 12 '' | tr ' ' '-')"
done
echo ""

# Procesar cada paquete único
echo "$all_unique_packages" | while IFS= read -r package; do
    [ -z "$package" ] && continue
    
    # Obtener información del paquete
    description=$(get_package_description "$package")
    install_cmd=$(get_install_command "$package")
    
    # Preparar fila para CSV
    if [ "$SHOW_DETAILS" = true ] || [ -n "$OUTPUT_FILE" ]; then
        row="$package,\"$description\",\"$install_cmd\""
    else
        row="$package"
    fi
    
    # Mostrar en consola
    if [ "$SHOW_DETAILS" = true ]; then
        printf "%-25s %-40s %-35s" "$package" "${description:0:38}" "${install_cmd:0:33}"
    else
        printf "%-30s" "$package"
    fi
    
    # Verificar presencia en cada entorno
    for env in "${envs[@]}"; do
        if echo "${env_packages[$env]}" | grep -q "^$package$"; then
            printf " %-12s" "✅"
            row="$row,✅"
        else
            printf " %-12s" "❌"
            row="$row,❌"
        fi
    done
    echo ""
    
    # Guardar en archivo CSV si se especificó (siempre con detalles en CSV)
    if [ -n "$OUTPUT_FILE" ]; then
        if [ "$SHOW_DETAILS" = false ]; then
            # Si no se muestran detalles en consola, pero sí en CSV
            csv_row="$package,\"$description\",\"$install_cmd\""
            for env in "${envs[@]}"; do
                if echo "${env_packages[$env]}" | grep -q "^$package$"; then
                    csv_row="$csv_row,✅"
                else
                    csv_row="$csv_row,❌"
                fi
            done
            echo "$csv_row" >> "$OUTPUT_FILE"
        else
            echo "$row" >> "$OUTPUT_FILE"
        fi
    fi
done

echo ""
echo "=================================================================="

# Generar estadísticas
echo -e "${BLUE}📈 Estadísticas:${NC}"
echo "  • Entornos analizados: ${#envs[@]}"
echo "  • Paquetes únicos: $package_count"

if [ -n "$OUTPUT_FILE" ]; then
    echo -e "  • Archivo CSV generado: ${GREEN}$OUTPUT_FILE${NC}"
    echo -e "    ${YELLOW}💡 El archivo CSV incluye descripciones y comandos de instalación${NC}"
fi

# Limpiar archivos temporales
rm -rf "$temp_dir"

echo -e "\n${GREEN}✨ Análisis completado exitosamente${NC}"

# Leyenda
echo -e "\n${YELLOW}Leyenda:${NC}"
echo "  ✅ = Paquete instalado en el entorno"
echo "  ❌ = Paquete no instalado en el entorno"
if [ -n "$OUTPUT_FILE" ]; then
    echo -e "\n${BLUE}💡 Consejos para usar el archivo CSV:${NC}"
    echo "  • Abre el archivo en Excel/LibreOffice para mejor visualización"
    echo "  • Usa la columna 'Instalación' para instalar paquetes faltantes"
    echo "  • Filtra por entorno para ver qué paquetes necesitas"
fi
if [ "$SHOW_DETAILS" = false ]; then
    echo -e "\n${BLUE}💡 Consejo: Usa -d para ver descripciones en consola${NC}"
fi
