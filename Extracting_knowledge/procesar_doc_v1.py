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

    return frontmatter + body

if __name__ == "__main__":
    import readline

    def completer(text, state):
        text = os.path.expanduser(text)
        if text.startswith('~'):
            text = os.path.join(os.path.expanduser('~'), text[2:])
        dirname = os.path.dirname(text)
        if not dirname:
            dirname = '.'
        filenames = os.listdir(dirname)
        matches = [filename for filename in filenames if filename.startswith(os.path.basename(text))]
        if state < len(matches):
            return os.path.join(dirname, matches[state])
        else:
            return None

    readline.set_completer_delims(' \t\n;')
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")

    ruta_archivo = input("Por favor, introduce la ruta del archivo a analizar (puedes usar Tab para autocompletar): ")

    etiquetas = extract_tags(ruta_archivo)
    if etiquetas:
        contenido_fabric = obtener_contenido_fabric(ruta_archivo)
        if contenido_fabric:
            obsidian_output = formatear_para_obsidian(ruta_archivo, etiquetas, contenido_fabric)
            print("\nContenido formateado para Obsidian:")
            print(obsidian_output)
