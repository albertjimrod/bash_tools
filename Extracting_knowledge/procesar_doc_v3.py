# procesar_documento.py
import os
import subprocess
import re
from datetime import datetime
from tag_extractor import extract_tags  # Importamos la función del script anterior
from bs4 import BeautifulSoup  # Importamos BeautifulSoup

def obtener_contenido_fabric(ruta_archivo):
    """Ejecuta fabric y obtiene el contenido después de </think>, extrayendo el texto del HTML si es necesario."""
    try:
        comando = f'cat "{ruta_archivo}" | fabric --model deepseek-r1:14b -sp to_flashcards'
        proceso = subprocess.run(comando, shell=True, capture_output=True, text=True, check=True)
        output = proceso.stdout
        # Buscar el contenido después de la primera aparición de </think>
        match = re.search(r'</think>\s*(.*)', output, re.DOTALL | re.IGNORECASE)
        if match:
            contenido_post_think = match.group(1).strip()
            # Intentar parsear como HTML y extraer el texto
            if contenido_post_think.startswith("<!DOCTYPE html>") or "<html" in contenido_post_think:
                soup = BeautifulSoup(contenido_post_think, 'html.parser')
                # Extraer el texto principal, excluyendo quizás el título del head
                body_text = soup.body.get_text(separator='\n', strip=True) if soup.body else soup.get_text(separator='\n', strip=True)
                return body_text
            else:
                return contenido_post_think
        else:
            # Intentar parsear todo el output como HTML si no se encuentra </think>
            if output.startswith("<!DOCTYPE html>") or "<html" in output:
                soup = BeautifulSoup(output, 'html.parser')
                body_text = soup.body.get_text(separator='\n', strip=True) if soup.body else soup.get_text(separator='\n', strip=True)
                return body_text
            else:
                return output.strip()  # Si no es HTML, devolver el output tal cual
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar fabric: {e}")
        return None
    except FileNotFoundError:
        print(f"Error: El archivo en la ruta '{ruta_archivo}' no fue encontrado.")
        return None
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return None

def formatear_para_obsidian(ruta_archivo, etiquetas, contenido_fabric):
    """Formatea el contenido para un documento de Obsidian."""
    nombre_archivo = os.path.basename(ruta_archivo)
    titulo = os.path.splitext(nombre_archivo)[0].replace("-", " ").replace("_", " ").title()
    fecha_creacion = datetime.now().strftime("%Y-%m-%d")
    hora_creacion = datetime.now().strftime("%H:%M")

    frontmatter = f"""---
title: {titulo}
date: {fecha_creacion}
tags:
"""
    for tag in etiquetas:
        frontmatter += f"  - {tag}\n"
    frontmatter += f"""status: Pendiente
created: {fecha_creacion} {hora_creacion}
modified: {fecha_creacion} {hora_creacion}
---
"""

    body = f"""## {titulo}

{contenido_fabric}
"""

    return frontmatter + body, titulo  # Devolvemos también el título

def guardar_en_obsidian(nombre_archivo, contenido, directorio_destino="."):
    """Guarda el contenido en un archivo Markdown para Obsidian en el directorio especificado."""
    nombre_archivo_seguro = nombre_archivo.replace(" ", "-").replace(":", "").replace("/", "").replace("\\", "") + ".md"
    ruta_completa = os.path.join(directorio_destino, nombre_archivo_seguro)
    try:
        with open(ruta_completa, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"El contenido de '{nombre_archivo}.xml' se ha guardado en el archivo: {ruta_completa}")
    except Exception as e:
        print(f"Ocurrió un error al guardar el archivo '{nombre_archivo}.xml': {e}")

if __name__ == "__main__":
    directorio_entrada = input("Por favor, introduce la ruta del directorio que contiene los archivos .xml a analizar: ")
    directorio_salida = input("Por favor, introduce la ruta del directorio donde guardar los archivos .md (deja en blanco para el mismo directorio): ")
    if not directorio_salida:
        directorio_salida = directorio_entrada

    try:
        archivos_xml = [f for f in os.listdir(directorio_entrada) if f.endswith(".xml")]
        if not archivos_xml:
            print(f"No se encontraron archivos .xml en el directorio: {directorio_entrada}")
        else:
            print(f"Se encontraron {len(archivos_xml)} archivos .xml para procesar.")
            for archivo_xml in archivos_xml:
                ruta_completa_xml = os.path.join(directorio_entrada, archivo_xml)
                nombre_base_xml = os.path.splitext(archivo_xml)[0]

                print(f"\nProcesando archivo: {archivo_xml}")
                etiquetas = extract_tags(ruta_completa_xml)
                if etiquetas:
                    contenido_fabric, titulo_nota = formatear_para_obsidian(ruta_completa_xml, etiquetas, obtener_contenido_fabric(ruta_completa_xml))
                    if contenido_fabric:
                        guardar_en_obsidian(titulo_nota, contenido_fabric, directorio_salida)
                    else:
                        print(f"No se pudo obtener el contenido de fabric para: {archivo_xml}")
                else:
                    print(f"No se pudieron extraer etiquetas para: {archivo_xml}")

    except FileNotFoundError:
        print(f"Error: El directorio '{directorio_entrada}' no fue encontrado.")
    except Exception as e:
        print(f"Ocurrió un error general: {e}")
