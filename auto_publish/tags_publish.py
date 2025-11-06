#!/usr/bin/env python3

import os
import re
import requests
from datetime import datetime, timedelta
from base64 import b64encode

# CONFIGURACIÓN
print("[DEBUG] Configurando parámetros...")

wp_url = "https://datablogcafe.com/wp-json/wp/v2/posts"
wp_tags_url = "https://datablogcafe.com/wp-json/wp/v2/tags"
wp_user = "albert"
wp_app_password = "Pi46 vmRq 5fxX qm9M kbUs iiQR"
articulos_dir = "/home/ion/Documentos/albertjimrod/bash_tools/generar_articulos/backup-joplin_procesado"

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

# Fecha base: hace 2 años
fecha_base = datetime.now() - timedelta(days=730)
print(f"[DEBUG] Fecha base de publicación: {fecha_base.strftime('%Y-%m-%d')}")

def limpiar_contenido(texto):
    # Eliminar secciones <think>...</think>
    texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL)

    # Eliminar párrafos claramente en inglés (heurística simple: frases con muchas palabras en inglés comunes)
    lineas = texto.split("\n")
    lineas_filtradas = [
        linea for linea in lineas
        if not re.search(r"\b(the|this|that|with|from|have|can|you|should|use|model|dataset|data|analysis|steps)\b", linea, re.IGNORECASE)
    ]
    return "\n".join(lineas_filtradas).strip()

def generar_tags_desde_titulo(titulo):
    palabras = [p.lower() for p in re.findall(r"\b\w{4,}\b", titulo)]
    return list(set(palabras))[:5]  # máximo 5 tags simples

def obtener_ids_tags(tags):
    ids = []
    for tag in tags:
        response = requests.get(f"{wp_tags_url}?search={tag}", headers=headers)
        if response.status_code == 200 and response.json():
            ids.append(response.json()[0]['id'])
        else:
            crear = requests.post(wp_tags_url, headers=headers, json={"name": tag})
            if crear.status_code == 201:
                ids.append(crear.json()['id'])
            else:
                print(f"[WARNING] No se pudo crear el tag '{tag}': {crear.status_code}")
    return ids

# Contador de artículos válidos
indice = 0

# Recorrer directorios recursivamente
for root, _, files in os.walk(articulos_dir):
    for filename in sorted(files):
        if not filename.endswith(".md"):
            print(f"[DEBUG] Saltando archivo no .md: {filename}")
            continue

        filepath = os.path.join(root, filename)
        print(f"[DEBUG] Procesando: {filepath}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                contenido_bruto = f.read()
        except Exception as e:
            print(f"[ERROR] No se pudo leer el archivo {filename}: {e}")
            continue

        contenido = limpiar_contenido(contenido_bruto)

        # Fecha de publicación incremental
        fecha_publicacion = fecha_base + timedelta(days=indice * 2)

        # Título desde el nombre del archivo
        titulo = filename.replace('.md', '').replace('_', ' ').title()

        # Generar tags
        tags = generar_tags_desde_titulo(titulo)
        tags_ids = obtener_ids_tags(tags)

        # Datos del post
        post = {
            "title": titulo,
            "content": contenido,
            "status": "publish",  # Cambiar a "future" si deseas programar
            "date": fecha_publicacion.isoformat(),
            "tags": tags_ids
        }

        print(f"[DEBUG] Publicando '{titulo}' con fecha {fecha_publicacion.isoformat()} y tags: {tags}")

        try:
            response = requests.post(wp_url, headers=headers, json=post)
            if response.status_code == 201:
                print(f"[OK] Publicado: {filename}")
            else:
                print(f"[ERROR] Falló la publicación de {filename}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[ERROR] Excepción al publicar {filename}: {e}")

        indice += 1

