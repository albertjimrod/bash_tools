#!/bin/bash
# organize_with_ai.sh - Organiza archivos con sugerencias de Ollama
# USO: ./organize_with_ai.sh /ruta/a/analizar [max_archivos] [profundidad]

set -e

# Configuración
MODEL="qwen2.5:14b-instruct-q5_K_M"
REPORT_DIR="$HOME/.organize_reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORT_DIR/report_$TIMESTAMP.md"
SUGGESTIONS_FILE="$REPORT_DIR/suggestions_$TIMESTAMP.csv"

# Parámetros (sin límite por defecto)
MAX_FILES="${2:-0}"
MAX_DEPTH="${3:-0}"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Validar argumentos
if [ -z "$1" ]; then
    echo -e "${RED}Uso: $0 /ruta/a/analizar [max_archivos] [profundidad]${NC}"
    echo "  max_archivos: número máximo de archivos (0 = sin límite)"
    echo "  profundidad: niveles de subdirectorios (0 = sin límite)"
    exit 1
fi

TARGET_DIR="$1"
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${RED}Error: '$TARGET_DIR' no existe${NC}"
    exit 1
fi

mkdir -p "$REPORT_DIR"

echo -e "${GREEN}${BOLD}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║   ORGANIZADOR DE ARCHIVOS CON IA       ║${NC}"
echo -e "${GREEN}${BOLD}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Directorio:${NC} $TARGET_DIR"
echo -e "${CYAN}Modelo:${NC} $MODEL"
echo -e "${CYAN}Informe:${NC} $REPORT_FILE"
echo ""

# Fase 1: Escanear directorio
echo -e "${YELLOW}[1/3] Escaneando directorio...${NC}"

FIND_OPTS=""
[ "$MAX_DEPTH" -gt 0 ] 2>/dev/null && FIND_OPTS="-maxdepth $MAX_DEPTH"

if [ "$MAX_FILES" -gt 0 ] 2>/dev/null; then
    FILE_LIST=$(find "$TARGET_DIR" $FIND_OPTS -type f -printf "%P|%s\n" 2>/dev/null | head -$MAX_FILES)
else
    FILE_LIST=$(find "$TARGET_DIR" $FIND_OPTS -type f -printf "%P|%s\n" 2>/dev/null)
fi
DIR_LIST=$(find "$TARGET_DIR" $FIND_OPTS -type d -printf "%P\n" 2>/dev/null | tail -n +2)

FILE_COUNT=$(echo "$FILE_LIST" | grep -c "." || echo "0")
echo -e "Archivos encontrados: ${BOLD}$FILE_COUNT${NC}"

# Fase 2: Análisis con Ollama
echo -e "${YELLOW}[2/3] Analizando con IA (esto puede tardar)...${NC}"

PROMPT="Eres un experto en organización de archivos y productividad. Analiza estos archivos y sugiere cómo organizarlos.

ARCHIVOS (ruta|tamaño_bytes):
$FILE_LIST

CARPETAS EXISTENTES:
$DIR_LIST

RESPONDE con este formato EXACTO:

## Visión General
[2-3 frases: qué tipo de contenido hay, problemas de organización detectados, beneficio de reorganizar]

## Categorías Detectadas
[Lista las categorías/tipos de archivos que identificas y cuántos hay de cada tipo]

## Estructura Sugerida
[Lista de carpetas recomendadas con descripción de qué contendrá cada una]

## Movimientos
IMPORTANTE: En la columna 'razon' explica:
- QUÉ es el archivo (tipo, contenido)
- POR QUÉ debe moverse ahí (beneficio concreto)
- RELACIÓN con otros archivos similares

\`\`\`csv
archivo_origen,carpeta_destino,categoria,razon_detallada
\`\`\`

Ejemplo de razón buena: 'Notebook de Optuna para optimización de hiperparámetros. Agruparlo con otros experimentos ML facilita comparar resultados y mantener histórico.'
Ejemplo de razón mala: 'mover archivo relacionado'"

# Ejecutar Ollama
echo "$PROMPT" | ollama run "$MODEL" > "$REPORT_FILE" 2>/dev/null &
OLLAMA_PID=$!

while kill -0 $OLLAMA_PID 2>/dev/null; do
    echo -n "."
    sleep 2
done
echo " ¡Listo!"

# Extraer CSV
echo -e "${YELLOW}[3/3] Procesando sugerencias...${NC}"
sed -n '/```csv/,/```/p' "$REPORT_FILE" | grep -v '```' > "$SUGGESTIONS_FILE" 2>/dev/null || true

# Mostrar informe
echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}              INFORME DE ANÁLISIS          ${NC}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo ""

echo -e "${BLUE}${BOLD}▶ VISIÓN GENERAL${NC}"
sed -n '/## Visión General/,/## Categorías/p' "$REPORT_FILE" | grep -v "^##" | head -10
echo ""

echo -e "${BLUE}${BOLD}▶ CATEGORÍAS DETECTADAS${NC}"
sed -n '/## Categorías/,/## Estructura/p' "$REPORT_FILE" | grep -v "^##" | head -15
echo ""

echo -e "${BLUE}${BOLD}▶ ESTRUCTURA SUGERIDA${NC}"
sed -n '/## Estructura Sugerida/,/## Movimientos/p' "$REPORT_FILE" | grep -v "^##" | head -15
echo ""

# Contar sugerencias por categoría
if [ -s "$SUGGESTIONS_FILE" ]; then
    echo -e "${BLUE}${BOLD}▶ RESUMEN DE MOVIMIENTOS${NC}"
    TOTAL_MOVES=$(grep -c "," "$SUGGESTIONS_FILE" 2>/dev/null || echo "0")
    echo -e "Total de movimientos sugeridos: ${BOLD}$TOTAL_MOVES${NC}"
    echo ""
    echo "Por carpeta destino:"
    cut -d',' -f2 "$SUGGESTIONS_FILE" | grep -v "carpeta_destino" | sort | uniq -c | sort -rn | head -10
    echo ""
fi

# Menú interactivo
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}           REVISIÓN DE MOVIMIENTOS         ${NC}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo ""

if [ ! -s "$SUGGESTIONS_FILE" ]; then
    echo "No se extrajeron sugerencias."
    echo "Revisa el informe: cat $REPORT_FILE"
    exit 0
fi

# Preparar archivo de aprobados
APPROVED_FILE="$REPORT_DIR/approved_$TIMESTAMP.sh"
cat > "$APPROVED_FILE" << 'HEADER'
#!/bin/bash
# Movimientos aprobados
# Ejecutar: bash este_archivo.sh

set -e
echo "Ejecutando movimientos aprobados..."
HEADER

show_menu() {
    echo ""
    echo -e "${CYAN}Opciones:${NC}"
    echo "  [1] Revisar uno a uno"
    echo "  [2] Aprobar TODOS los movimientos"
    echo "  [3] Aprobar por CATEGORÍA/DESTINO"
    echo "  [4] Ver informe completo"
    echo "  [5] Salir sin cambios"
    echo ""
    read -p "Selecciona opción: " -n 1 -r
    echo ""
}

approve_all() {
    echo "" >> "$APPROVED_FILE"
    while IFS=',' read -r origen destino categoria razon; do
        [[ "$origen" == "archivo_origen" ]] && continue
        [[ -z "$origen" ]] && continue
        echo "mkdir -p \"$TARGET_DIR/$destino\"" >> "$APPROVED_FILE"
        echo "mv \"$TARGET_DIR/$origen\" \"$TARGET_DIR/$destino/\" 2>/dev/null || true" >> "$APPROVED_FILE"
    done < "$SUGGESTIONS_FILE"
    echo -e "${GREEN}✓ Todos los movimientos aprobados${NC}"
    return 0
}

approve_by_category() {
    echo ""
    echo -e "${CYAN}Carpetas destino disponibles:${NC}"
    CATEGORIES=$(cut -d',' -f2 "$SUGGESTIONS_FILE" | grep -v "carpeta_destino" | sort -u)

    i=1
    declare -A CAT_MAP
    while read -r cat; do
        COUNT=$(grep ",$cat," "$SUGGESTIONS_FILE" | wc -l)
        echo "  [$i] $cat ($COUNT archivos)"
        CAT_MAP[$i]="$cat"
        ((i++))
    done <<< "$CATEGORIES"
    echo "  [0] Volver"
    echo ""
    read -p "Aprobar categoría (número): " -r CAT_NUM

    if [ "$CAT_NUM" == "0" ]; then
        return 1
    fi

    SELECTED_CAT="${CAT_MAP[$CAT_NUM]}"
    if [ -z "$SELECTED_CAT" ]; then
        echo -e "${RED}Opción inválida${NC}"
        return 1
    fi

    echo "" >> "$APPROVED_FILE"
    echo "# Categoría: $SELECTED_CAT" >> "$APPROVED_FILE"
    while IFS=',' read -r origen destino categoria razon; do
        [[ "$destino" != "$SELECTED_CAT" ]] && continue
        [[ -z "$origen" ]] && continue
        echo "mkdir -p \"$TARGET_DIR/$destino\"" >> "$APPROVED_FILE"
        echo "mv \"$TARGET_DIR/$origen\" \"$TARGET_DIR/$destino/\" 2>/dev/null || true" >> "$APPROVED_FILE"
    done < "$SUGGESTIONS_FILE"

    echo -e "${GREEN}✓ Categoría '$SELECTED_CAT' aprobada${NC}"

    read -p "¿Aprobar otra categoría? [s/n] " -n 1 -r
    echo ""
    [[ $REPLY =~ ^[sS]$ ]] && approve_by_category
    return 0
}

review_one_by_one() {
    APPROVED=0
    REJECTED=0

    while IFS=',' read -r origen destino categoria razon; do
        [[ "$origen" == "archivo_origen" ]] && continue
        [[ -z "$origen" ]] && continue

        echo ""
        echo -e "${BOLD}────────────────────────────────────────${NC}"
        echo -e "${YELLOW}Archivo:${NC}   $origen"
        echo -e "${YELLOW}Mover a:${NC}   $destino"
        echo -e "${YELLOW}Categoría:${NC} $categoria"
        echo -e "${YELLOW}Razón:${NC}"
        echo -e "  ${CYAN}$razon${NC}"
        echo -e "${BOLD}────────────────────────────────────────${NC}"
        echo ""
        echo "[s]Aprobar  [n]Rechazar  [a]Aprobar resto  [q]Salir"
        read -p "> " -n 1 -r
        echo ""

        case $REPLY in
            [sS])
                echo "mkdir -p \"$TARGET_DIR/$destino\"" >> "$APPROVED_FILE"
                echo "mv \"$TARGET_DIR/$origen\" \"$TARGET_DIR/$destino/\" 2>/dev/null || true" >> "$APPROVED_FILE"
                echo -e "${GREEN}✓ Aprobado${NC}"
                ((APPROVED++))
                ;;
            [aA])
                echo "mkdir -p \"$TARGET_DIR/$destino\"" >> "$APPROVED_FILE"
                echo "mv \"$TARGET_DIR/$origen\" \"$TARGET_DIR/$destino/\" 2>/dev/null || true" >> "$APPROVED_FILE"
                ((APPROVED++))
                # Aprobar el resto
                while IFS=',' read -r o d c r; do
                    [[ "$o" == "archivo_origen" ]] && continue
                    [[ -z "$o" ]] && continue
                    echo "mkdir -p \"$TARGET_DIR/$d\"" >> "$APPROVED_FILE"
                    echo "mv \"$TARGET_DIR/$o\" \"$TARGET_DIR/$d/\" 2>/dev/null || true" >> "$APPROVED_FILE"
                    ((APPROVED++))
                done
                echo -e "${GREEN}✓ Resto aprobado${NC}"
                break
                ;;
            [qQ])
                break
                ;;
            *)
                echo -e "${RED}✗ Rechazado${NC}"
                ((REJECTED++))
                ;;
        esac
    done < "$SUGGESTIONS_FILE"

    echo ""
    echo -e "Aprobados: ${GREEN}$APPROVED${NC} | Rechazados: ${RED}$REJECTED${NC}"
}

# Loop principal
while true; do
    show_menu
    case $REPLY in
        1) review_one_by_one; break ;;
        2) approve_all; break ;;
        3) approve_by_category; break ;;
        4) cat "$REPORT_FILE"; echo "" ;;
        5) echo "Saliendo..."; exit 0 ;;
        *) echo -e "${RED}Opción inválida${NC}" ;;
    esac
done

# Verificar si hay movimientos aprobados
MOVE_COUNT=$(grep -c "^mv " "$APPROVED_FILE" 2>/dev/null || echo "0")

echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}                 RESUMEN                   ${NC}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo ""
echo -e "Movimientos aprobados: ${BOLD}$MOVE_COUNT${NC}"
echo -e "Script generado: ${CYAN}$APPROVED_FILE${NC}"
echo ""

if [ "$MOVE_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}Vista previa del script:${NC}"
    grep "^mv " "$APPROVED_FILE" | head -5
    [ "$MOVE_COUNT" -gt 5 ] && echo "  ... y $(($MOVE_COUNT - 5)) más"
    echo ""

    read -p "¿Ejecutar movimientos ahora? [s/n] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[sS]$ ]]; then
        echo "Ejecutando..."
        bash "$APPROVED_FILE"
        echo -e "${GREEN}${BOLD}¡Completado!${NC}"
    else
        echo -e "Ejecuta luego con: ${CYAN}bash $APPROVED_FILE${NC}"
    fi
fi

echo ""
echo -e "Informe completo: ${CYAN}cat $REPORT_FILE${NC}"
