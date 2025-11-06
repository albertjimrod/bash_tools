#!/usr/bin/env python3

import os
import re
import requests
from datetime import datetime, timedelta
from base64 import b64encode

# CONFIGURACIÓN
print("[DEBUG] Configurando parámetros...")

wp_url = "https://datablogcafe.com/wp-json/wp/v2/posts"
wp_user = "albert"
wp_app_password = "Pi46 vmRq 5fxX qm9M kbUs iiQR"
articulos_dir = "/home/ion/Documentos/albertjimrod/bash_tools/generar_articulos/backup-joplin_procesado/00_ML/Deep Learning"
wp_tags_url = "https://datablogcafe.com/wp-json/wp/v2/tags"

if not os.path.exists(articulos_dir):
    print(f"[ERROR] El directorio no existe: {articulos_dir}")
    exit(1)

# Autenticación
print("[DEBUG] Codificando credenciales...")
credentials = f"{wp_user}:{wp_app_password}"
token = b64encode(credentials.encode())
headers = {
    "Authorization": f"Basic {token.decode('utf-8')}",
    "Content-Type": "application/json"
}

# Fecha base
fecha_base = datetime.now() - timedelta(days=730)
print(f"[DEBUG] Fecha base de publicación: {fecha_base.strftime('%Y-%m-%d')}")

# Función para limpiar contenido
def limpiar_contenido(texto):
    return re.sub(r'<think>.*?</think>', '', texto, flags=re.DOTALL)

# Función para generar o recuperar tags
def obtener_ids_tags(posibles_tags):
    ids = []
    for tag in posibles_tags:
        tag = tag.lower().strip()
        # Buscar si ya existe
        response = requests.get(f"{wp_tags_url}?search={tag}", headers=headers)
        if response.status_code == 200 and response.json():
            ids.append(response.json()[0]['id'])
        else:
            # Crear nueva etiqueta
            crear = requests.post(wp_tags_url, headers=headers, json={"name": tag})
            if crear.status_code == 201:
                ids.append(crear.json()['id'])
            else:
                print(f"[WARNING] No se pudo crear el tag '{tag}': {crear.text}")
    return ids

# Procesar artículos
for i, filename in enumerate(sorted(os.listdir(articulos_dir))):
    if not filename.endswith(".txt") and not filename.endswith(".md"):
        continue

    filepath = os.path.join(articulos_dir, filename)
    print(f"[DEBUG] Procesando: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            contenido_bruto = f.read()
    except Exception as e:
        print(f"[ERROR] No se pudo leer el archivo {filename}: {e}")
        continue

    contenido = limpiar_contenido(contenido_bruto)

    # Generar fecha
    fecha_publicacion = fecha_base + timedelta(days=i*2)

    # Generar título
    titulo = filename.replace('.txt', '').replace('.md', '').replace('_', ' ').title()

    # Generar tags a partir del título (puedes cambiar esta lógica)
    palabras_clave = [palabra.lower() for palabra in titulo.split() if len(palabra) > 3]
    tags_ids = obtener_ids_tags(palabras_clave)

    post = {
            "title": titulo,
            "content": contenido,
            "status": "future",  # Cambiar a "future" para programar en vez de publicar inmediato
            "date": fecha_publicacion.isoformat(),
            "tags": tags_ids
            }

    print(f"[DEBUG] Publicando '{titulo}' con fecha {fecha_publicacion.isoformat()} y tags {palabras_clave}...")
    
    response = requests.post(wp_url, headers=headers, json=post)
    if response.status_code == 201:
        print(f"[OK] Publicado: {filename}")
    else:
        print(f"[ERROR] Falló la publicación de {filename}: {response.status_code} - {response.text}")
