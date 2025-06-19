#!/bin/bash

# Colores para mejor visualización
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [opciones]"
    echo "Opciones:"
    echo "  -h, --help     Muestra esta ayuda"
    echo "  -o, --output   Guarda el resultado en un archivo CSV"
    echo "  -v, --verbose  Muestra información detallada durante el proceso"
    echo ""
    echo "Esta herramienta compara los paquetes instalados en todos los entornos de Conda"
    echo "y genera una matriz mostrando qué paquetes están presentes en cada entorno."
}

# Variables por defecto
OUTPUT_FILE=""
VERBOSE=false

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
header="Paquete"
for env in "${envs[@]}"; do
    header="$header,$env"
done

if [ -n "$OUTPUT_FILE" ]; then
    echo "$header" > "$OUTPUT_FILE"
fi

# Mostrar encabezado en consola
printf "%-30s" "Paquete"
for env in "${envs[@]}"; do
    printf " %-12s" "$env"
done
echo ""

# Línea separadora
printf "%-30s" "$(printf '%*s' 30 '' | tr ' ' '-')"
for env in "${envs[@]}"; do
    printf " %-12s" "$(printf '%*s' 12 '' | tr ' ' '-')"
done
echo ""

# Procesar cada paquete único
echo "$all_unique_packages" | while IFS= read -r package; do
    [ -z "$package" ] && continue
    
    row="$package"
    printf "%-30s" "$package"
    
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
    
    # Guardar en archivo CSV si se especificó
    if [ -n "$OUTPUT_FILE" ]; then
        echo "$row" >> "$OUTPUT_FILE"
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
fi

# Limpiar archivos temporales
rm -rf "$temp_dir"

echo -e "\n${GREEN}✨ Análisis completado exitosamente${NC}"

# Leyenda
echo -e "\n${YELLOW}Leyenda:${NC}"
echo "  ✅ = Paquete instalado en el entorno"
echo "  ❌ = Paquete no instalado en el entorno"
