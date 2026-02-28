#!/bin/bash

# ============================================
# ANALIZADOR INTELIGENTE DE ENTORNOS CONDA
# Versión: 3.0 (Final Estable)
# ============================================

OLLAMA_API="http://localhost:11434/api/generate"
MODEL="mistral:latest"
DEBUG=false

# Colores
COLOR_BLUE='\033[0;34m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_CYAN='\033[0;36m'
COLOR_RESET='\033[0m'
COLOR_BOLD='\033[1m'

log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${COLOR_YELLOW}[DEBUG]${COLOR_RESET} $1" >&2
    fi
}

check_ollama() {
    echo -e "${COLOR_BLUE}🔍 Verificando Ollama...${COLOR_RESET}"
    if ! curl -s "http://localhost:11434/api/tags" | grep -q "\"name\":\"$MODEL\""; then
        echo -e "${COLOR_RED}❌ Modelo '$MODEL' no encontrado${COLOR_RESET}"
        exit 1
    fi
    echo -e "${COLOR_GREEN}✅ Ollama OK | Modelo: $MODEL${COLOR_RESET}"
}

filter_packages() {
    grep -vE "^(pip|setuptools|wheel|certifi|idna|urllib3|packaging|typing|markupsafe|jinja2|click|pyyaml|filelock|fsspec|networkx|numpy|pandas|pyarrow|scipy|pillow|cycler|fonttools|kiwisolver|pyparsing|python-dateutil|pytz|six|zipp|importlib)"
}

ask_ai() {
    local env_name=$1
    local python_ver=$2
    local pkg_list=$3
    
    local prompt="Analiza este entorno Python: NOMBRE=$env_name PYTHON=$python_ver PAQUETES=$pkg_list. Responde exactamente: PROPÓSITO:[frase] HERRAMIENTAS:[3-5 librerías] DIFERENCIADOR:[único] USAR_PARA:[cuándo]. Sé breve."
    
    local json_data=$(jq -n --arg model "$MODEL" --arg prompt "$prompt" '{model: $model, prompt: $prompt, stream: false}')
    
    local response=$(curl -s -X POST "$OLLAMA_API" -H "Content-Type: application/json" -d "$json_data" --max-time 120 2>&1)
    local extracted=$(echo "$response" | jq -r '.response // empty' 2>/dev/null)
    
    if [ -z "$extracted" ]; then return 1; fi
    echo "$extracted"
}

analyze_single_env() {
    local name=$1
    local path=$2
    local is_active=$3
    
    echo -e "${COLOR_YELLOW}----------------------------------------${COLOR_RESET}"
    if [ "$is_active" = "true" ]; then
        echo -e "${COLOR_BOLD}Entorno: ${COLOR_GREEN}$name ${COLOR_RED}● ACTIVO${COLOR_RESET}"
    else
        echo -e "${COLOR_BOLD}Entorno: ${COLOR_GREEN}$name${COLOR_RESET}"
    fi
    
    # Búsqueda de binarios
    local has_r=false
    local has_python=false
    local python_bin=""
    local rscript_bin=""
    
    # Check R
    if [ -f "$path/bin/R" ] || [ -f "$path/bin/Rscript" ]; then
        has_r=true
        rscript_bin="$path/bin/Rscript"
    fi
    
    # Check Python
    if [ -f "$path/bin/python3" ]; then
        python_bin="$path/bin/python3"
        has_python=true
    elif [ -f "$path/bin/python" ]; then
        python_bin="$path/bin/python"
        has_python=true
    fi
    
    # Lógica de decisión
    if [ "$has_r" = true ] && [ "$has_python" = false ]; then
        echo -e "${COLOR_CYAN}📍 Tipo: Entorno R${COLOR_RESET}"
        if [ -f "$rscript_bin" ]; then
            echo -e "${COLOR_GREEN}Paquetes R:${COLOR_RESET}"
            "$rscript_bin" -e "installed.packages()[,1]" 2>/dev/null | head -n 8 | sed 's/^/   - /'
        fi
        echo -e "${COLOR_YELLOW}💡 Nota: Entorno R puro.${COLOR_RESET}"
        return 0
        
    elif [ "$has_python" = true ]; then
        echo -e "${COLOR_CYAN}📍 Tipo: Entorno Python${COLOR_RESET}"
        local py_ver=$("$python_bin" --version 2>&1 | awk '{print $2}')
        echo -e "Python: $py_ver"
        
        local pkg_list=""
        local pip_bin=""
        if [ -f "$path/bin/pip3" ]; then pip_bin="$path/bin/pip3"
        elif [ -f "$path/bin/pip" ]; then pip_bin="$path/bin/pip"; fi
        
        if [ -n "$pip_bin" ]; then
            pkg_list=$("$pip_bin" list --format=freeze 2>/dev/null | filter_packages | head -n 20)
        fi
        
        if [ -z "$pkg_list" ]; then
            pkg_list=$(conda list -p "$path" 2>/dev/null | awk 'NR>3 {print $1"="$2}' | filter_packages | head -n 20)
        fi
        
        if [ -z "$pkg_list" ]; then
            echo -e "${COLOR_RED}⚠️  No se pudieron leer los paquetes${COLOR_RESET}"
            return 1
        fi
        
        echo -e "Paquetes: ${COLOR_CYAN}$(echo "$pkg_list" | wc -l)${COLOR_RESET}"
        [ "$has_r" = true ] && echo -e "${COLOR_YELLOW}ℹ️  Nota: Híbrido (Python + R)${COLOR_RESET}"
        
        echo -e "${COLOR_BLUE}🤖 Analizando...${COLOR_RESET}"
        local analysis=$(ask_ai "$name" "$py_ver" "$pkg_list")
        
        if [ -n "$analysis" ]; then
            echo -e "${COLOR_GREEN}$analysis${COLOR_RESET}"
            return 0
        else
            echo -e "${COLOR_RED}⚠️  Sin análisis de IA${COLOR_RESET}"
            return 1
        fi
    else
        echo -e "${COLOR_RED}⚠️  Entorno vacío o sin binarios detectables${COLOR_RESET}"
        echo -e "${COLOR_YELLOW}💡 Sugerencia: Ejecuta 'conda list -n $name' para verificar.${COLOR_RESET}"
        return 1
    fi
}

main() {
    echo -e "${COLOR_BLUE}========================================${COLOR_RESET}"
    echo -e "${COLOR_BLUE}   ANALIZADOR INTELIGENTE DE ENTORNOS   ${COLOR_RESET}"
    echo -e "${COLOR_BLUE}========================================${COLOR_RESET}\n"
    
    check_ollama
    
    if ! command -v jq &> /dev/null; then
        echo -e "${COLOR_RED}❌ jq no instalado.${COLOR_RESET}"
        exit 1
    fi
    
    local envs_raw=$(conda info --envs 2>/dev/null)
    local count=0
    local total=0
    
    while IFS= read -r line; do
        [[ "$line" =~ ^#.* ]] && continue
        [[ -z "$line" ]] && continue
        
        local name path is_active="false"
        if [[ "$line" == *"*"* ]]; then
            is_active="true"
            name=$(echo "$line" | sed 's/\*//g' | awk '{print $1}')
            path=$(echo "$line" | awk '{print $2}')
        else
            name=$(echo "$line" | awk '{print $1}')
            path=$(echo "$line" | awk '{print $2}')
        fi
        
        name=$(echo "$name" | tr -d '[:space:]')
        [[ -z "$name" ]] && continue
        
        if [ "$name" = "base" ] && { [ -z "$path" ] || [ "$path" = "None" ]; }; then
            path="$CONDA_PREFIX"
        fi
        
        if [ -z "$path" ] || [ "$path" = "None" ] || [ ! -d "$path" ]; then
            continue
        fi
        
        ((total++))
        analyze_single_env "$name" "$path" "$is_active" && ((count++))
        echo ""
    done <<< "$envs_raw"
    
    echo -e "${COLOR_BLUE}========================================${COLOR_RESET}"
    echo -e "Resumen: ${COLOR_GREEN}$count/$total${COLOR_RESET} entornos analizados"
    echo -e "${COLOR_BLUE}========================================${COLOR_RESET}"
}

main
