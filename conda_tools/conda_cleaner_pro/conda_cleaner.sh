#!/usr/bin/env bash
# ==============================================================================
# 🧹 CONDA CLEANER PRO - Detecta duplicados, calcula espacio e inspecciona riesgos
# ==============================================================================
set -euo pipefail

# --- CONFIGURACIÓN ---
WARN_SIZE_DIFF=104857600      # Alerta si diferencia > 100MB
LARGE_FILE_THRESHOLD="50M"    # Archivos grandes > 50MB

# --- COLORES ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- FUNCIONES ---
format_size() {
  local bytes=$1
  if (( bytes >= 1073741824 )); then awk "BEGIN {printf \"%.2f GB\", $bytes/1073741824}"
  elif (( bytes >= 1048576 )); then awk "BEGIN {printf \"%.2f MB\", $bytes/1048576}"
  elif (( bytes >= 1024 )); then awk "BEGIN {printf \"%.2f KB\", $bytes/1024}"
  else echo "${bytes} B"; fi
}

print_header() { echo -e "\n${BLUE}════════════════════════════════════════════════════════${NC}"; }
print_section() { echo -e "\n${YELLOW}▶ $1${NC}"; }

check_conda() {
  if ! command -v conda >/dev/null 2>&1; then
    echo -e "${RED}❌ Error: conda no está disponible en el PATH${NC}"; exit 1
  fi
}

# --- INSPECCIÓN DE ARCHIVOS PERSONALES ---
inspect_env() {
  local env_name=$1
  local env_path=$2
  
  print_section "📂 Inspección profunda: $env_name"
  echo "   📍 Ruta: $env_path"
  echo "   📏 Tamaño: $(du -sh "$env_path" 2>/dev/null | cut -f1)"
  
  # Archivos personales fuera de librerías
  local personal=$(find "$env_path" -type f \( -name "*.py" -o -name "*.ipynb" -o -name "*.csv" -o -name "*.json" \) \
    -not -path "*/site-packages/*" -not -path "*/lib/*" -not -path "*/share/*" \
    -not -path "*/conda-meta/*" 2>/dev/null | head -n 15)
  
  if [[ -n "$personal" ]]; then
    echo -e "   ${RED}⚠️  Archivos personales detectados:${NC}"
    echo "$personal" | sed 's/^/      /'
  else
    echo -e "   ${GREEN}✅ No hay archivos personales evidentes${NC}"
  fi
  
  # Archivos grandes
  local large=$(find "$env_path" -type f -size +$LARGE_FILE_THRESHOLD -exec ls -lh {} \; 2>/dev/null | awk '{print $5, $9}' | head -n 10)
  if [[ -n "$large" ]]; then
    echo -e "   ${YELLOW}🐘 Archivos grandes (>50MB):${NC}"
    echo "$large" | sed 's/^/      /'
  fi
  
  # Basura
  local pycache=$(du -sh "$env_path/__pycache__" 2>/dev/null | cut -f1 || echo "0")
  local logs=$(find "$env_path" -name "*.log" -exec du -ch {} + 2>/dev/null | tail -1 | cut -f1 || echo "0")
  echo -e "   🗑️  Basura: __pycache__ ($pycache) | Logs ($logs)"
}

# --- MAIN ---
check_conda

ACTIVE_ENV=$(conda env list | grep '\*' | awk '{print $1}' || echo "")
declare -A NAME_LIST SIZE_MAP PATH_MAP

print_header
echo -e "${GREEN}🔍 Escaneando entornos Conda...${NC}"

while read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  ENV_NAME=$(echo "$line" | awk '{print $1}')
  ENV_PATH=$(echo "$line" | awk '{print $NF}')
  
  [[ "$ENV_NAME" == "base" || "$ENV_NAME" == "$ACTIVE_ENV" || -z "$ENV_NAME" ]] && continue
  
  SIZE_BYTES=$(du -sb "$ENV_PATH" 2>/dev/null | awk '{print $1}' || echo "0")
  
  if HASH=$(conda list --prefix "$ENV_PATH" --export 2>/dev/null | md5sum | awk '{print $1}'); then
    if [[ -v NAME_LIST[$HASH] ]]; then
      NAME_LIST[$HASH]+="|$ENV_NAME"
      SIZE_MAP[$HASH]+="|$SIZE_BYTES"
      PATH_MAP[$HASH]+="|$ENV_PATH"  # ✅ CORRECCIÓN: Guardar TODAS las rutas
    else
      NAME_LIST[$HASH]="$ENV_NAME"
      SIZE_MAP[$HASH]="$SIZE_BYTES"
      PATH_MAP[$HASH]="$ENV_PATH"
    fi
  fi
done < <(conda env list)

print_header
echo -e "${GREEN}=== Resultados ===${NC}"

FOUND=0
TOTAL_FREED=0

# Arrays separados para nombres y rutas (más seguro que usar :)
declare -a DELETE_NAMES
declare -a DELETE_PATHS

for hash in "${!NAME_LIST[@]}"; do
  IFS='|' read -ra ENVS <<< "${NAME_LIST[$hash]}"
  IFS='|' read -ra SIZES <<< "${SIZE_MAP[$hash]}"
  IFS='|' read -ra PATHS <<< "${PATH_MAP[$hash]}"  # ✅ CORRECCIÓN: Leer todas las rutas
  
  if (( ${#ENVS[@]} > 1 )); then
    FOUND=1
    GROUP_SIZE=0
    MAX_SIZE=0 MIN_SIZE=${SIZES[0]}
    
    print_section "⚠️  GRUPO DUPLICADO (${#ENVS[@]} entornos idénticos)"
    
    for s in "${SIZES[@]}"; do
      (( s > MAX_SIZE )) && MAX_SIZE=$s
      (( s < MIN_SIZE )) && MIN_SIZE=$s
    done
    DIFF=$((MAX_SIZE - MIN_SIZE))
    
    echo -e "   ${BLUE}Entornos y tamaños:${NC}"
    for i in "${!ENVS[@]}"; do
      echo "   [$i] ${ENVS[$i]} ($(format_size ${SIZES[$i]}))"
      (( i > 0 )) && GROUP_SIZE=$((GROUP_SIZE + ${SIZES[$i]}))
    done
    
    # Alerta de diferencia
    if (( DIFF > WARN_SIZE_DIFF )); then
      echo -e "   ${RED}⚠️  ALERTA: $(format_size $DIFF) de diferencia entre el más grande y pequeño${NC}"
    fi
    
    # Contenido compartido
    echo -e "   ${BLUE}📦 Paquetes compartidos (ejemplo):${NC}"
    conda list --prefix "${PATHS[0]}" --export 2>/dev/null | head -n 6 | sed 's/^/      /'
    echo "      ... ($(conda list --prefix "${PATHS[0]}" 2>/dev/null | wc -l) paquetes totales)"
    
    # ✅ CORRECCIÓN: Guardar nombre y ruta en arrays paralelos
    for i in "${!ENVS[@]}"; do
      if (( i > 0 )); then
        DELETE_NAMES+=("${ENVS[$i]}")
        DELETE_PATHS+=("${PATHS[$i]}")
      fi
    done
    
    TOTAL_FREED=$((TOTAL_FREED + GROUP_SIZE))
    echo -e "   ${GREEN}💾 Espacio liberable: $(format_size $GROUP_SIZE)${NC}"
    echo -e "   ${YELLOW}💡 Mantener: '${ENVS[0]}' | Borrar el resto${NC}"
  fi
done

if (( FOUND == 0 )); then
  echo -e "${GREEN}✅ No se detectaron duplicados${NC}"
  exit 0
fi

print_header
echo -e "${GREEN}=== Resumen ===${NC}"
echo -e "💾 Espacio TOTAL liberable: ${YELLOW}$(format_size $TOTAL_FREED)${NC}"
echo -e "📊 Entornos candidatos a borrar: ${YELLOW}${#DELETE_NAMES[@]}${NC}"

# --- INSPECCIÓN AUTOMÁTICA ---
print_header
read -p "¿Inspeccionar archivos personales antes de borrar? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  print_section "🔬 Inspeccionando entornos candidatos..."
  for i in "${!DELETE_NAMES[@]}"; do
    inspect_env "${DELETE_NAMES[$i]}" "${DELETE_PATHS[$i]}"  # ✅ CORRECCIÓN: Usar arrays paralelos
  done
  print_header
  echo -e "${GREEN}✅ Inspección finalizada${NC}"
fi

# --- MENSAJE FINAL ---
print_header
echo -e "${YELLOW}📋 Comandos para eliminar (uno por uno):${NC}"
for env_name in "${DELETE_NAMES[@]}"; do
  echo "   conda env remove -n $env_name"
done
echo -e "\n${RED}⚠️  Nunca elimines el entorno base o el activo${NC}"
print_header
