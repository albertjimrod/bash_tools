#!/usr/bin/env python3
"""
Script para filtrar los pensamientos (<think>...</think>) de la salida de Fabric
y guardar solo el contenido curado en un archivo.
"""
import sys
import re
import argparse

def filter_think_tags(input_text):
    """
    Elimina el contenido entre las etiquetas <think></think> de la entrada
    """
    # Patrón para encontrar contenido entre etiquetas <think></think>
    pattern = r'<think>.*?</think>'
    # Eliminar el contenido que coincide con el patrón (incluidas las etiquetas), usando DOTALL para que . incluya saltos de línea
    filtered_text = re.sub(pattern, '', input_text, flags=re.DOTALL)
    # Eliminar líneas vacías extras
    filtered_text = re.sub(r'\n\s*\n', '\n\n', filtered_text)
    return filtered_text.strip()

def main():
    parser = argparse.ArgumentParser(description='Filtra la salida de Fabric para eliminar etiquetas <think>')
    parser.add_argument('-i', '--input', help='Archivo de entrada (por defecto: stdin)')
    parser.add_argument('-o', '--output', help='Archivo de salida (por defecto: stdout)')
    parser.add_argument('-p', '--pattern', help='Patrón de Fabric a usar (ej: extract_questions)')
    args = parser.parse_args()

    # Leer la entrada desde un archivo o stdin
    if args.input:
        with open(args.input, 'r') as file:
            input_text = file.read()
    else:
        input_text = sys.stdin.read()
    
    # Filtrar el texto
    filtered_text = filter_think_tags(input_text)
    
    # Escribir la salida a un archivo o stdout
    if args.output:
        with open(args.output, 'w') as file:
            file.write(filtered_text)
    else:
        print(filtered_text)

if __name__ == "__main__":
    main()
