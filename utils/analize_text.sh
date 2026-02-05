#!/bin/bash
# Script para analizar un texto con múltiples patrones en Fabric

# Comprobar si se proporcionaron los argumentos necesarios
if [ $# -lt 1 ]; then
    echo "Uso: $0 <archivo_texto.xml> [archivo_salida.md]"
    exit 1
fi

INPUT_FILE=$1
OUTPUT_FILE=${2:-"analisis_completo.md"}

# Array de patrones a aplicar
PATTERNS=(
    "extract_main_idea"
    "extract_patterns"
    "extract_insights"
    "extract_ideas"
    "extract_recommendations"
    "extract_questions"
    "summarize"
    "create_micro_summary"
    "analyze_prose"
    "analyze_claims"
    "extract_article_wisdom"
)

# Crear o limpiar el archivo de salida
echo "# Análisis completo del texto" > "$OUTPUT_FILE"
echo "Archivo analizado: $INPUT_FILE" >> "$OUTPUT_FILE"
echo "Fecha: $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Procesar cada patrón
for pattern in "${PATTERNS[@]}"; do
    echo "Procesando patrón: $pattern..."
    echo "## $pattern" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    # Ejecutar fabric con el patrón actual y filtrar la salida
    cat "$INPUT_FILE" | fabric --model deepseek-r1:14b -sp "$pattern" | python3 filter_fabric.py >> "$OUTPUT_FILE"
    
    echo "" >> "$OUTPUT_FILE"
    echo "---" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
done

echo "Análisis completado. Resultados guardados en $OUTPUT_FILE"
