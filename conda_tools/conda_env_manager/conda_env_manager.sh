#!/bin/bash

################################################################################
#                    CONDA ENVIRONMENT MANAGER v2.0                           #
#                     Gestor Avanzado de Entornos Conda                       #
################################################################################

# Colores para mejor visualización
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Variables globales
declare -A env_packages      # env_name -> lista de paquetes
declare -A env_versions      # env_name:package -> versión
declare -A env_info          # env_name -> info (ruta, tamaño, fecha)
TEMP_DIR=$(mktemp -d)
VERBOSE=false

################################################################################
#                           FUNCIONES AUXILIARES                              #
################################################################################

# Inicializar Conda
init_conda() {
    eval "$(conda shell.bash hook)" 2>/dev/null || { 
        echo -e "${RED}❌ Error: No se pudo inicializar Conda.${NC}" 
        exit 1 
    }
}

# Obtener descripción del paquete
get_package_description() {
    local package="$1"
    case "$package" in
        "langchain") echo "Framework para construir aplicaciones con LLMs" ;;
        "langchain-core") echo "Core components de LangChain" ;;
        "langchain-community") echo "Integraciones comunitarias de LangChain" ;;
        "langchain-ollama") echo "Integración de LangChain con Ollama" ;;
        "chromadb") echo "Vector database para embeddings" ;;
        "ollama") echo "Cliente para ejecutar LLMs localmente" ;;
        "numpy") echo "Computación numérica" ;;
        "pandas") echo "Análisis y manipulación de datos" ;;
        "scikit-learn") echo "Machine learning" ;;
        "tensorflow") echo "Deep learning (Google)" ;;
        "pytorch") echo "Deep learning (Facebook)" ;;
        "matplotlib") echo "Visualización de datos" ;;
        "seaborn") echo "Visualización estadística" ;;
        "plotly") echo "Gráficos interactivos" ;;
        "jupyter") echo "Notebooks interactivos" ;;
        "jupyterlab") echo "Entorno de desarrollo interactivo" ;;
        "flask") echo "Framework web minimalista" ;;
        "django") echo "Framework web completo" ;;
        "fastapi") echo "Framework web moderno para APIs" ;;
        "requests") echo "Cliente HTTP" ;;
        "beautifulsoup4") echo "Web scraping" ;;
        "selenium") echo "Automatización web" ;;
        "sqlalchemy") echo "ORM y SQL toolkit" ;;
        "psycopg2") echo "Driver PostgreSQL" ;;
        "pymongo") echo "Driver MongoDB" ;;
        "pytest") echo "Testing framework" ;;
        "black") echo "Formateador de código" ;;
        "flake8") echo "Linter de código" ;;
        "pydantic") echo "Validación de datos" ;;
        "pyyaml") echo "Parser YAML" ;;
        *) echo "Paquete de Python" ;;
    esac
}

# Obtener comando de instalación
get_install_command() {
    local package="$1"
    local version="${2:-latest}"
    
    case "$package" in
        *"pytorch"*) echo "conda install pytorch torchvision torchaudio -c pytorch" ;;
        *"tensorflow"*) echo "conda install tensorflow" ;;
        *"scikit-learn"*) echo "conda install scikit-learn" ;;
        *"psycopg2"*) echo "conda install psycopg2" ;;
        *"pymongo"*) echo "conda install pymongo" ;;
        *"xgboost"*) echo "conda install xgboost" ;;
        *"lightgbm"*) echo "conda install lightgbm" ;;
        *) 
            if [ "$version" != "latest" ]; then
                echo "pip install $package==$version"
            else
                echo "pip install $package"
            fi
            ;;
    esac
}

# Obtener información del entorno
get_env_info() {
    local env_name="$1"
    local env_path
    
    env_path=$(conda run -n "$env_name" python -c "import sys; print(sys.prefix)" 2>/dev/null)
    
    if [ -d "$env_path" ]; then
        local size=$(du -sh "$env_path" 2>/dev/null | cut -f1)
        local date=$(stat -c %y "$env_path" 2>/dev/null | cut -d' ' -f1-2 || stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$env_path" 2>/dev/null)
        echo "$env_path|$size|$date"
    else
        echo "unknown|0B|unknown"
    fi
}

# Mostrar encabezado
show_header() {
    clear
    echo -e "${CYAN}"
    echo "╔═════════════════════════════════════════════════════════╗"
    echo "║     CONDA ENVIRONMENT MANAGER v2.0                     ║"
    echo "║     Gestor Avanzado de Entornos Conda                  ║"
    echo "╚═════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Mostrar menú principal
show_main_menu() {
    echo -e "\n${BLUE}═══ MENÚ PRINCIPAL ═══${NC}\n"
    echo "1. 🔍 Buscar paquete en todos los entornos"
    echo "2. 📋 Validar archivo de requerimientos"
    echo "3. ⚖️  Comparar entornos"
    echo "4. 📊 Ver información de entornos"
    echo "5. 💾 Exportar a CSV"
    echo "6. 🔧 Ver detalles completos de un entorno"
    echo "7. 🗑️  Analizar duplicados/similares"
    echo "8. 📝 Ver resumen general"
    echo "0. ❌ Salir"
    echo ""
}

# Cargar todos los entornos
load_all_environments() {
    echo -e "${BLUE}📦 Cargando información de entornos...${NC}"
    
    local envs_raw=$(conda info --envs 2>/dev/null | awk 'NR > 2 && !/^#/ {print $1}' | grep -v '^$')
    local env_count=0
    
    while IFS= read -r env; do
        [ -z "$env" ] && continue
        
        echo -ne "\r  Procesando: $env                    "
        
        # Obtener paquetes y versiones
        local packages=$(conda run -n "$env" pip list --format json 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for pkg in data:
        print(pkg['name'])
except:
    pass
" 2>/dev/null)
        
        if [ -n "$packages" ]; then
            env_packages["$env"]="$packages"
            
            # Obtener versiones
            local versions=$(conda run -n "$env" pip list --format json 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for pkg in data:
        print(pkg['name'] + '||' + pkg['version'])
except:
    pass
" 2>/dev/null)
            
            # Guardar versiones
            while IFS='||' read -r pkg_name version; do
                [ -z "$pkg_name" ] && continue
                env_versions["$env:$pkg_name"]="$version"
            done <<< "$versions"
            
            # Obtener info del entorno
            local info=$(get_env_info "$env")
            env_info["$env"]="$info"
            
            ((env_count++))
        fi
    done <<< "$envs_raw"
    
    echo -e "\r${GREEN}✓ Se cargaron $env_count entornos${NC}                    "
}

################################################################################
#                        FUNCIÓN 1: BUSCAR PAQUETE                            #
################################################################################

search_package() {
    show_header
    echo -e "\n${BLUE}🔍 BÚSQUEDA DE PAQUETE${NC}\n"
    
    read -p "Ingresa nombre del paquete: " package_name
    [ -z "$package_name" ] && { echo -e "${RED}❌ Nombre vacío${NC}"; return; }
    
    echo -e "\n${YELLOW}¿Tipo de búsqueda?${NC}"
    echo "1. Exacta (solo coincidencias exactas)"
    echo "2. Parcial (contiene el texto)"
    read -p "Opción (1-2): " search_type
    
    echo -e "\n${BLUE}Resultados:${NC}\n"
    
    local found=false
    local total_found=0
    
    for env in "${!env_packages[@]}"; do
        local matches=""
        
        if [ "$search_type" = "1" ]; then
            # Búsqueda exacta
            if echo "${env_packages[$env]}" | grep -q "^${package_name}$"; then
                matches="$package_name"
            fi
        else
            # Búsqueda parcial
            matches=$(echo "${env_packages[$env]}" | grep -i "$package_name")
        fi
        
        if [ -n "$matches" ]; then
            found=true
            echo -e "${GREEN}✅ Entorno: ${CYAN}$env${NC}"
            
            while IFS= read -r match; do
                [ -z "$match" ] && continue
                local version="${env_versions[$env:$match]:-desconocida}"
                local desc=$(get_package_description "$match")
                local install=$(get_install_command "$match" "$version")
                
                echo -e "   ${WHITE}Paquete:${NC} $match"
                echo -e "   ${WHITE}Versión:${NC} $version"
                echo -e "   ${WHITE}Descripción:${NC} $desc"
                echo -e "   ${WHITE}Instalación:${NC} $install"
                echo ""
                
                ((total_found++))
            done <<< "$matches"
        fi
    done
    
    if [ "$found" = false ]; then
        echo -e "${RED}❌ No se encontró '$package_name' en ningún entorno${NC}"
    else
        echo -e "${GREEN}✓ Total de coincidencias: $total_found${NC}"
    fi
    
    read -p "Presiona Enter para continuar..."
}

################################################################################
#                   FUNCIÓN 2: VALIDAR REQUERIMIENTOS                         #
################################################################################

validate_requirements() {
    show_header
    echo -e "\n${BLUE}📋 VALIDAR ARCHIVO DE REQUERIMIENTOS${NC}\n"
    
    read -p "Ruta del archivo de requerimientos: " req_file
    [ ! -f "$req_file" ] && { echo -e "${RED}❌ Archivo no encontrado${NC}"; read -p "Enter..."; return; }
    
    read -p "Nombre del entorno a validar: " env_name
    
    # Verificar que el entorno existe
    if ! conda info --envs 2>/dev/null | grep -q "^$env_name"; then
        echo -e "${RED}❌ Entorno '$env_name' no existe${NC}"
        read -p "Enter..."
        return
    fi
    
    echo -e "\n${BLUE}Validando entorno: ${CYAN}$env_name${NC}\n"
    
    local missing_packages=()
    local version_mismatch=()
    local total_required=0
    local total_satisfied=0
    
    # Procesar archivo de requerimientos
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        [[ "$line" =~ ^# ]] && continue
        
        # Parsear diferentes formatos
        local pkg_name=""
        local required_version=""
        
        if [[ "$line" =~ ^([a-zA-Z0-9_-]+)==([a-zA-Z0-9._]+) ]]; then
            pkg_name="${BASH_REMATCH[1]}"
            required_version="${BASH_REMATCH[2]}"
        elif [[ "$line" =~ ^([a-zA-Z0-9_-]+)= ]]; then
            pkg_name=$(echo "$line" | cut -d'=' -f1)
            required_version=$(echo "$line" | cut -d'=' -f3)
        elif [[ "$line" =~ ^([a-zA-Z0-9_-]+) ]]; then
            pkg_name="$line"
            required_version="any"
        fi
        
        [ -z "$pkg_name" ] && continue
        ((total_required++))
        
        local installed_version="${env_versions[$env_name:$pkg_name]:-}"
        
        if [ -z "$installed_version" ]; then
            missing_packages+=("$pkg_name|$required_version")
            echo -e "${RED}❌ Falta:${NC} $pkg_name (requerido: $required_version)"
        elif [ "$required_version" != "any" ] && [ "$installed_version" != "$required_version" ]; then
            version_mismatch+=("$pkg_name|$required_version|$installed_version")
            echo -e "${YELLOW}⚠️  Versión diferente:${NC} $pkg_name"
            echo -e "    Requerida: $required_version"
            echo -e "    Instalada: $installed_version"
        else
            ((total_satisfied++))
            echo -e "${GREEN}✅ OK:${NC} $pkg_name (v$installed_version)"
        fi
    done < "$req_file"
    
    # Resumen
    echo -e "\n${BLUE}═══ RESUMEN ═══${NC}"
    echo -e "Total de paquetes requeridos: $total_required"
    echo -e "${GREEN}Satisfechos: $total_satisfied${NC}"
    echo -e "${YELLOW}Versiones diferentes: ${#version_mismatch[@]}${NC}"
    echo -e "${RED}Faltantes: ${#missing_packages[@]}${NC}"
    
    # Mostrar sugerencias
    if [ ${#missing_packages[@]} -gt 0 ]; then
        echo -e "\n${BLUE}🔧 SUGERENCIAS DE INSTALACIÓN:${NC}\n"
        
        for item in "${missing_packages[@]}"; do
            IFS='|' read -r pkg req_ver <<< "$item"
            local install_cmd=$(get_install_command "$pkg" "$req_ver")
            echo -e "${CYAN}$install_cmd${NC}"
        done
        
        echo -e "\n${YELLOW}⚠️  NOTA: Instala uno por uno para verificar compatibilidad${NC}"
    fi
    
    # Guardar reporte
    read -p "¿Guardar reporte en CSV? (s/n): " save_report
    if [ "$save_report" = "s" ] || [ "$save_report" = "S" ]; then
        local output="${req_file%.txt}_validation_$(date +%Y%m%d_%H%M%S).csv"
        {
            echo "Paquete,Requerido,Instalado,Estado"
            while IFS= read -r line; do
                [ -z "$line" ] && continue
                [[ "$line" =~ ^# ]] && continue
                
                local pkg_name=""
                local required_version=""
                
                if [[ "$line" =~ ^([a-zA-Z0-9_-]+)==([a-zA-Z0-9._]+) ]]; then
                    pkg_name="${BASH_REMATCH[1]}"
                    required_version="${BASH_REMATCH[2]}"
                elif [[ "$line" =~ ^([a-zA-Z0-9_-]+)= ]]; then
                    pkg_name=$(echo "$line" | cut -d'=' -f1)
                    required_version=$(echo "$line" | cut -d'=' -f3)
                else
                    pkg_name="$line"
                    required_version="any"
                fi
                
                [ -z "$pkg_name" ] && continue
                
                local installed_version="${env_versions[$env_name:$pkg_name]:-MISSING}"
                local status="MISSING"
                
                if [ "$installed_version" != "MISSING" ]; then
                    if [ "$required_version" = "any" ] || [ "$installed_version" = "$required_version" ]; then
                        status="OK"
                    else
                        status="VERSION_MISMATCH"
                    fi
                fi
                
                echo "$pkg_name,$required_version,$installed_version,$status"
            done < "$req_file"
        } > "$output"
        echo -e "${GREEN}✓ Reporte guardado en: $output${NC}"
    fi
    
    read -p "Presiona Enter para continuar..."
}

################################################################################
#                       FUNCIÓN 3: COMPARAR ENTORNOS                          #
################################################################################

compare_environments() {
    show_header
    echo -e "\n${BLUE}⚖️  COMPARAR ENTORNOS${NC}\n"
    
    local envs_array=()
    for env in "${!env_packages[@]}"; do
        envs_array+=("$env")
    done
    
    if [ ${#envs_array[@]} -lt 2 ]; then
        echo -e "${RED}❌ Se necesitan al menos 2 entornos para comparar${NC}"
        read -p "Enter..."
        return
    fi
    
    echo "Entornos disponibles:"
    for i in "${!envs_array[@]}"; do
        echo "$((i+1)). ${envs_array[$i]}"
    done
    
    echo ""
    read -p "Selecciona primer entorno (número): " env1_idx
    read -p "Selecciona segundo entorno (número): " env2_idx
    
    ((env1_idx--))
    ((env2_idx--))
    
    if [ $env1_idx -lt 0 ] || [ $env1_idx -ge ${#envs_array[@]} ] || \
       [ $env2_idx -lt 0 ] || [ $env2_idx -ge ${#envs_array[@]} ]; then
        echo -e "${RED}❌ Índice inválido${NC}"
        read -p "Enter..."
        return
    fi
    
    local env1="${envs_array[$env1_idx]}"
    local env2="${envs_array[$env2_idx]}"
    
    echo -e "\n${BLUE}Comparando: ${CYAN}$env1${BLUE} vs ${CYAN}$env2${NC}\n"
    
    # Paquetes comunes
    local common=$(comm -12 <(echo "${env_packages[$env1]}" | sort) <(echo "${env_packages[$env2]}" | sort))
    local common_count=$(echo "$common" | grep -c '^' || echo 0)
    
    # Paquetes únicos de env1
    local unique1=$(comm -23 <(echo "${env_packages[$env1]}" | sort) <(echo "${env_packages[$env2]}" | sort))
    local unique1_count=$(echo "$unique1" | grep -c '^' || echo 0)
    
    # Paquetes únicos de env2
    local unique2=$(comm -13 <(echo "${env_packages[$env1]}" | sort) <(echo "${env_packages[$env2]}" | sort))
    local unique2_count=$(echo "$unique2" | grep -c '^' || echo 0)
    
    echo -e "${CYAN}═══ ANÁLISIS DE SIMILITUD ═══${NC}"
    echo -e "Paquetes comunes: ${GREEN}$common_count${NC}"
    echo -e "Solo en $env1: ${YELLOW}$unique1_count${NC}"
    echo -e "Solo en $env2: ${YELLOW}$unique2_count${NC}"
    
    # Calcular similitud
    local total_unique=$((unique1_count + unique2_count))
    local similarity=0
    if [ $common_count -gt 0 ]; then
        similarity=$(( (common_count * 100) / (common_count + total_unique / 2) ))
    fi
    
    echo -e "Similitud: ${MAGENTA}${similarity}%${NC}"
    
    if [ "$similarity" -gt 80 ]; then
        echo -e "${YELLOW}⚠️  Estos entornos son muy similares. Considera eliminar uno.${NC}"
    fi
    
    # Mostrar detalles
    echo -e "\n${BLUE}═══ PAQUETES COMUNES ═══${NC}"
    if [ -n "$common" ]; then
        echo "$common" | head -20
        if [ $common_count -gt 20 ]; then
            echo "... y $(($common_count - 20)) más"
        fi
    fi
    
    echo -e "\n${BLUE}═══ SOLO EN ${env1} ═══${NC}"
    if [ -n "$unique1" ]; then
        echo "$unique1"
    else
        echo "Ninguno"
    fi
    
    echo -e "\n${BLUE}═══ SOLO EN ${env2} ═══${NC}"
    if [ -n "$unique2" ]; then
        echo "$unique2"
    else
        echo "Ninguno"
    fi
    
    read -p "Presiona Enter para continuar..."
}

################################################################################
#                    FUNCIÓN 4: VER INFORMACIÓN DE ENTORNOS                   #
################################################################################

view_env_info() {
    show_header
    echo -e "\n${BLUE}📊 INFORMACIÓN DE ENTORNOS${NC}\n"
    
    printf "%-30s %-15s %-10s %-20s\n" "Entorno" "Paquetes" "Tamaño" "Fecha"
    echo "═══════════════════════════════════════════════════════════════════"
    
    for env in "${!env_info[@]}"; do
        local info="${env_info[$env]}"
        IFS='|' read -r path size date <<< "$info"
        local pkg_count=$(echo "${env_packages[$env]}" | grep -c '^' || echo 0)
        
        printf "%-30s %-15s %-10s %-20s\n" "$env" "$pkg_count" "$size" "${date:0:19}"
    done
    
    echo ""
    echo -e "${BLUE}═══ ESTADÍSTICAS TOTALES ═══${NC}"
    local total_envs=${#env_packages[@]}
    local total_pkgs=0
    local total_size=0
    
    for env in "${!env_packages[@]}"; do
        total_pkgs=$(($total_pkgs + $(echo "${env_packages[$env]}" | grep -c '^' || echo 0)))
    done
    
    echo -e "Total de entornos: ${GREEN}$total_envs${NC}"
    echo -e "Total de paquetes únicos: ${GREEN}$total_pkgs${NC}"
    
    read -p "Presiona Enter para continuar..."
}

################################################################################
#                      FUNCIÓN 5: EXPORTAR A CSV                              #
################################################################################

export_to_csv() {
    show_header
    echo -e "\n${BLUE}💾 EXPORTAR A CSV${NC}\n"
    
    echo "1. Exportar todos los entornos"
    echo "2. Exportar un entorno específico"
    read -p "Opción: " export_opt
    
    if [ "$export_opt" = "1" ]; then
        local output="conda_envs_complete_$(date +%Y%m%d_%H%M%S).csv"
        
        echo -e "${BLUE}Generando CSV completo...${NC}"
        
        # Obtener lista de entornos para headers
        local header="Paquete,Descripción,Comando_Instalación"
        for env in "${!env_packages[@]}"; do
            header="$header,$env"
        done
        
        {
            echo "$header"
            
            # Obtener todos los paquetes únicos
            local all_packages=$(for env in "${!env_packages[@]}"; do echo "${env_packages[$env]}"; done | sort -u)
            
            while IFS= read -r pkg; do
                [ -z "$pkg" ] && continue
                
                local desc=$(get_package_description "$pkg")
                local install=$(get_install_command "$pkg")
                local row="$pkg,\"$desc\",\"$install\""
                
                for env in "${!env_packages[@]}"; do
                    if echo "${env_packages[$env]}" | grep -q "^$pkg$"; then
                        local version="${env_versions[$env:$pkg]:-?}"
                        row="$row,✅ ($version)"
                    else
                        row="$row,❌"
                    fi
                done
                
                echo "$row"
            done <<< "$all_packages"
        } > "$output"
        
        echo -e "${GREEN}✓ Guardado en: $output${NC}"
        
    elif [ "$export_opt" = "2" ]; then
        echo "Entornos disponibles:"
        local envs_array=()
        local i=1
        for env in "${!env_packages[@]}"; do
            echo "$i. $env"
            envs_array+=("$env")
            ((i++))
        done
        
        read -p "Selecciona entorno: " env_idx
        ((env_idx--))
        
        if [ $env_idx -ge 0 ] && [ $env_idx -lt ${#envs_array[@]} ]; then
            local env="${envs_array[$env_idx]}"
            local output="conda_env_${env}_$(date +%Y%m%d_%H%M%S).csv"
            
            echo -e "${BLUE}Generando CSV para: $env${NC}"
            
            {
                echo "Paquete,Versión,Descripción,Comando_Instalación"
                
                local pkgs=$(echo "${env_packages[$env]}" | sort)
                while IFS= read -r pkg; do
                    [ -z "$pkg" ] && continue
                    
                    local version="${env_versions[$env:$pkg]:-desconocida}"
                    local desc=$(get_package_description "$pkg")
                    local install=$(get_install_command "$pkg" "$version")
                    
                    echo "$pkg,$version,\"$desc\",\"$install\""
                done <<< "$pkgs"
            } > "$output"
            
            echo -e "${GREEN}✓ Guardado en: $output${NC}"
        fi
    fi
    
    read -p "Presiona Enter para continuar..."
}

################################################################################
#                  FUNCIÓN 6: VER DETALLES DE UN ENTORNO                      #
################################################################################

view_env_details() {
    show_header
    echo -e "\n${BLUE}🔧 DETALLES DE ENTORNO${NC}\n"
    
    echo "Entornos disponibles:"
    local envs_array=()
    local i=1
    for env in "${!env_packages[@]}"; do
        echo "$i. $env"
        envs_array+=("$env")
        ((i++))
    done
    
    read -p "Selecciona entorno: " env_idx
    ((env_idx--))
    
    if [ $env_idx -lt 0 ] || [ $env_idx -ge ${#envs_array[@]} ]; then
        echo -e "${RED}❌ Índice inválido${NC}"
        read -p "Enter..."
        return
    fi
    
    local env="${envs_array[$env_idx]}"
    local info="${env_info[$env]}"
    IFS='|' read -r path size date <<< "$info"
    
    echo -e "\n${CYAN}═══ ENTORNO: $env ═══${NC}"
    echo -e "Ruta: $path"
    echo -e "Tamaño: $size"
    echo -e "Creado: $date"
    echo ""
    
    local pkg_count=$(echo "${env_packages[$env]}" | grep -c '^' || echo 0)
    echo -e "Total de paquetes: ${GREEN}$pkg_count${NC}\n"
    
    echo -e "${BLUE}Paquetes instalados:${NC}\n"
    
    echo "${env_packages[$env]}" | sort | while IFS= read -r pkg; do
        [ -z "$pkg" ] && continue
        local version="${env_versions[$env:$pkg]:-desconocida}"
        printf "  %-30s v%-15s\n" "$pkg" "$version"
    done
    
    read -p "Presiona Enter para continuar..."
}

################################################################################
#                   FUNCIÓN 7: ANALIZAR DUPLICADOS/SIMILARES                  #
################################################################################

analyze_duplicates() {
    show_header
    echo -e "\n${BLUE}🗑️  ANÁLISIS DE DUPLICADOS/SIMILARES${NC}\n"
    
    local envs_array=()
    for env in "${!env_packages[@]}"; do
        envs_array+=("$env")
    done
    
    if [ ${#envs_array[@]} -lt 2 ]; then
        echo -e "${RED}❌ Se necesitan al menos 2 entornos${NC}"
        read -p "Enter..."
        return
    fi
    
    echo -e "${BLUE}Analizando similitud entre entornos...${NC}\n"
    
    local similar_groups=()
    
    for ((i=0; i<${#envs_array[@]}; i++)); do
        for ((j=i+1; j<${#envs_array[@]}; j++)); do
            local env1="${envs_array[$i]}"
            local env2="${envs_array[$j]}"
            
            local common=$(comm -12 <(echo "${env_packages[$env1]}" | sort) <(echo "${env_packages[$env2]}" | sort))
            local common_count=$(echo "$common" | grep -c '^' || echo 0)
            
            local unique1=$(comm -23 <(echo "${env_packages[$env1]}" | sort) <(echo "${env_packages[$env2]}" | sort) | grep -c '^' || echo 0)
            local unique2=$(comm -13 <(echo "${env_packages[$env1]}" | sort) <(echo "${env_packages[$env2]}" | sort) | grep -c '^' || echo 0)
            
            local similarity=0
            if [ $common_count -gt 0 ]; then
                similarity=$(( (common_count * 100) / (common_count + (unique1 + unique2) / 2) ))
            fi
            
            # Guardar grupos similares (>70%)
            if [ $similarity -gt 70 ]; then
                similar_groups+=("$env1|$env2|$similarity|$common_count|$unique1|$unique2")
            fi
        done
    done
    
    if [ ${#similar_groups[@]} -eq 0 ]; then
        echo -e "${GREEN}✓ No se encontraron entornos muy similares${NC}"
    else
        echo -e "${YELLOW}⚠️  Se encontraron ${#similar_groups[@]} pares de entornos similares:${NC}\n"
        
        # Ordenar por similitud descendente
        for group in "${similar_groups[@]}"; do
            IFS='|' read -r env1 env2 sim common u1 u2 <<< "$group"
            
            echo -e "${CYAN}$env1${NC} ↔ ${CYAN}$env2${NC}"
            echo -e "  Similitud: ${MAGENTA}${sim}%${NC}"
            echo -e "  Paquetes comunes: $common"
            echo -e "  Solo en $env1: $u1"
            echo -e "  Solo en $env2: $u2"
            
            if [ $sim -gt 90 ]; then
                echo -e "  ${RED}→ RECOMENDACIÓN: Considera eliminar uno de estos entornos${NC}"
            fi
            echo ""
        done
    fi
    
    read -p "Presiona Enter para continuar..."
}

################################################################################
#                      FUNCIÓN 8: RESUMEN GENERAL                             #
################################################################################

show_summary() {
    show_header
    echo -e "\n${BLUE}📝 RESUMEN GENERAL${NC}\n"
    
    local total_envs=${#env_packages[@]}
    local total_unique_pkgs=0
    local total_size_mb=0
    
    # Contar paquetes únicos
    local all_pkgs=$(for env in "${!env_packages[@]}"; do echo "${env_packages[$env]}"; done | sort -u)
    total_unique_pkgs=$(echo "$all_pkgs" | grep -c '^' || echo 0)
    
    echo -e "${CYAN}═══ ESTADÍSTICAS GENERALES ═══${NC}"
    echo -e "Total de entornos: ${GREEN}$total_envs${NC}"
    echo -e "Paquetes únicos en el sistema: ${GREEN}$total_unique_pkgs${NC}"
    
    echo -e "\n${CYAN}═══ INFORMACIÓN POR ENTORNO ═══${NC}\n"
    
    printf "%-25s %-15s %-12s %-20s\n" "Entorno" "Paquetes" "Tamaño" "Fecha Creación"
    echo "────────────────────────────────────────────────────────────────"
    
    for env in "${!env_packages[@]}"; do
        local info="${env_info[$env]}"
        IFS='|' read -r path size date <<< "$info"
        local pkg_count=$(echo "${env_packages[$env]}" | grep -c '^' || echo 0)
        
        printf "%-25s %-15s %-12s %-20s\n" "$env" "$pkg_count" "$size" "${date:0:19}"
    done
    
    echo -e "\n${CYAN}═══ TOP 10 PAQUETES MÁS COMUNES ═══${NC}\n"
    
    {
        for env in "${!env_packages[@]}"; do
            echo "${env_packages[$env]}"
        done
    } | sort | uniq -c | sort -rn | head -10 | while read count pkg; do
        local percentage=$((count * 100 / total_envs))
        printf "%-30s %2d enviros (%3d%%)\n" "$pkg" "$count" "$percentage"
    done
    
    read -p "Presiona Enter para continuar..."
}

################################################################################
#                            FUNCIÓN PRINCIPAL                                #
################################################################################

main_loop() {
    while true; do
        show_header
        show_main_menu
        
        read -p "Selecciona opción (0-8): " option
        
        case $option in
            1) search_package ;;
            2) validate_requirements ;;
            3) compare_environments ;;
            4) view_env_info ;;
            5) export_to_csv ;;
            6) view_env_details ;;
            7) analyze_duplicates ;;
            8) show_summary ;;
            0) 
                echo -e "\n${GREEN}¡Hasta luego!${NC}\n"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Opción inválida${NC}"
                sleep 1
                ;;
        esac
    done
}

################################################################################
#                          ENTRADA PRINCIPAL                                  #
################################################################################

init_conda
load_all_environments
main_loop
