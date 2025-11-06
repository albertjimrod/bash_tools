#!/usr/bin/env python3
"""
Script para analizar texto con múltiples patrones en Fabric,
extraer tags relevantes y añadirlos al texto final.
"""
import sys
import re
import argparse
import subprocess
import os
import json
from collections import Counter

def filter_think_tags(input_text):
    """Elimina el contenido entre las etiquetas <think></think> de la entrada"""
    pattern = r'<think>.*?</think>'
    filtered_text = re.sub(pattern, '', input_text, flags=re.DOTALL)
    filtered_text = re.sub(r'\n\s*\n', '\n\n', filtered_text)
    return filtered_text.strip()

def run_fabric_pattern(input_file, pattern, model="deepseek-r1:14b"):
    """Ejecuta Fabric con un patrón específico y devuelve la salida filtrada"""
    try:
        cmd = f"cat '{input_file}' | fabric --model {model} -sp {pattern}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error al ejecutar Fabric con el patrón {pattern}: {result.stderr}", file=sys.stderr)
            return ""
        
        # Filtrar los tags <think>
        return filter_think_tags(result.stdout)
    except Exception as e:
        print(f"Error al procesar el patrón {pattern}: {str(e)}", file=sys.stderr)
        return ""

def extract_tags_from_output(output, pattern_name):
    """
    Extrae posibles tags del resultado de un patrón específico.
    Diferentes patrones pueden requerir diferentes estrategias de extracción.
    """
    tags = []
    
    # Buscar listas de palabras clave, tags, etc.
    tag_sections = re.findall(r'(?:tags|keywords|key terms|main topics|key concepts):\s*(.*?)(?:\n\n|\n(?=[A-Z])|\Z)', 
                              output, re.IGNORECASE | re.DOTALL)
    
    for section in tag_sections:
        # Limpiar y dividir la sección en palabras clave individuales
        lines = section.strip().split('\n')
        for line in lines:
            # Eliminar numeración de lista y símbolos de viñetas
            line = re.sub(r'^\s*\d+\.\s*|\s*-\s*|\s*\*\s*', '', line.strip())
            # Dividir en comas si parece una lista separada por comas
            if ',' in line:
                keywords = [k.strip() for k in line.split(',')]
                tags.extend(keywords)
            else:
                tags.append(line)
    
    # Si no se encontraron secciones explícitas de tags, extraer frases clave
    if not tags:
        # Extraer sustantivos y frases nominales (simplificado)
        # Buscar términos con mayúsculas o entre comillas
        quoted_terms = re.findall(r'"([^"]+)"|\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', output)
        if quoted_terms:
            for term_pair in quoted_terms:
                # Cada coincidencia es una tupla con dos grupos, uno de los cuales estará vacío
                term = term_pair[0] if term_pair[0] else term_pair[1]
                if len(term.split()) <= 3:  # Limitar a frases de máximo 3 palabras
                    tags.append(term)
    
    # Extraer frases clave basadas en el patrón específico
    if pattern_name == "extract_main_idea":
        # Buscar frases después de "main idea" o "central theme"
        main_ideas = re.findall(r'(?:main idea|central theme|core concept)(?:[:\s]+)([^\.]+)', output, re.IGNORECASE)
        for idea in main_ideas:
            # Dividir en frases cortas si es necesario
            parts = [p.strip() for p in re.split(r'[,;]', idea) if len(p.strip()) > 0]
            tags.extend(parts[:2])  # Tomar solo las dos primeras partes si hay muchas
    
    elif pattern_name == "extract_insights":
        # Buscar insights explícitamente mencionados
        insights = re.findall(r'(?:insight|key point)(?:[:\s]+)([^\.]+)', output, re.IGNORECASE)
        tags.extend([i.strip() for i in insights])
    
    # Filtrar tags vacíos y duplicados mientras se mantiene el orden
    seen = set()
    filtered_tags = []
    for tag in tags:
        tag = tag.strip()
        if tag and tag.lower() not in seen and len(tag) > 2:
            filtered_tags.append(tag)
            seen.add(tag.lower())
    
    return filtered_tags

def process_text_for_tags(input_file, output_file=None, patterns=None, model="deepseek-r1:14b"):
    """
    Procesa un archivo de texto con múltiples patrones y extrae tags relevantes
    """
    if not os.path.exists(input_file):
        print(f"Error: El archivo {input_file} no existe.", file=sys.stderr)
        return None
    
    # Patrones predeterminados si no se especifican
    if not patterns:
        patterns = [
            "extract_main_idea",
            "extract_patterns",
            "extract_insights",
            "extract_ideas"
        ]
    
    # Leer el contenido original del archivo
    with open(input_file, 'r') as f:
        original_content = f.read()
    
    all_tags = []
    pattern_outputs = {}
    
    # Procesar cada patrón
    for pattern in patterns:
        print(f"Procesando patrón: {pattern}...")
        output = run_fabric_pattern(input_file, pattern, model)
        if output:
            pattern_outputs[pattern] = output
            tags = extract_tags_from_output(output, pattern)
            all_tags.extend(tags)
    
    # Contar frecuencias de tags para identificar los más relevantes
    tag_counter = Counter(all_tags)
    most_common_tags = [tag for tag, _ in tag_counter.most_common(15)]
    
    # Preparar el contenido final
    final_content = original_content
    
    # Agregar los tags como metadatos al principio del contenido
    if most_common_tags:
        tags_section = "---\ntags: " + ", ".join(most_common_tags) + "\n---\n\n"
        final_content = tags_section + final_content
    
    # Agregar el análisis completo al final si se desea
    analysis_section = "\n\n## Análisis del contenido\n\n"
    for pattern, output in pattern_outputs.items():
        analysis_section += f"### {pattern}\n\n{output}\n\n"
    
    final_content += analysis_section
    
    # Guardar o mostrar el resultado
    if output_file:
        with open(output_file, 'w') as f:
            f.write(final_content)
        print(f"Contenido procesado guardado en {output_file}")
    else:
        print("\n=== TAGS EXTRAÍDOS ===")
        print(", ".join(most_common_tags))
        print("\n=== CONTENIDO CON TAGS ===")
        print(tags_section)
    
    return {
        "tags": most_common_tags,
        "content": final_content
    }

def main():
    parser = argparse.ArgumentParser(description='Analiza texto con Fabric y extrae tags relevantes')
    parser.add_argument('input', help='Archivo de entrada a analizar')
    parser.add_argument('-o', '--output', help='Archivo de salida (opcional)')
    parser.add_argument('-m', '--model', default='deepseek-r1:14b', help='Modelo de Fabric a usar')
    parser.add_argument('-p', '--patterns', nargs='+', help='Patrones específicos a usar (opcional)')
    args = parser.parse_args()

    process_text_for_tags(args.input, args.output, args.patterns, args.model)

if __name__ == "__main__":
    main()
