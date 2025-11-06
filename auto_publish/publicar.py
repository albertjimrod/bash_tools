#!/usr/bin/env python3

import os
import requests
from datetime import datetime, timedelta
from base64 import b64encode

# CONFIGURACIÓN
print("[DEBUG] Configurando parámetros...")

wp_url = "https://datablogcafe.com/wp-json/wp/v2/posts"  # Reemplaza con tu URL real
wp_user = "albert"  # Reemplaza con tu usuario
wp_app_password = "Pi46 vmRq 5fxX qm9M kbUs iiQR"  # Reemplaza con tu contraseña
articulos_dir = "/home/ion/Documentos/albertjimrod/bash_tools/generar_articulos/backup-joplin_procesado/00_ML/Deep Learning/Sequential API"

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

# Procesar archivos
archivos = sorted(os.listdir(articulos_dir))
print(f"[DEBUG] Archivos encontrados: {len(archivos)}")

for i, filename in enumerate(archivos):
    if not filename.endswith(".md"):
        print(f"[DEBUG] Saltando archivo no .txt: {filename}")
        continue

    filepath = os.path.join(articulos_dir, filename)
    print(f"[DEBUG] Procesando: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            contenido = f.read()
    except Exception as e:
        print(f"[ERROR] No se pudo leer el archivo {filename}: {e}")
        continue

    # Fecha de publicación incremental
    fecha_publicacion = fecha_base + timedelta(days=i * 2)

    # Datos del post
    post = {
        "title": filename.replace('.txt', '').replace('_', ' ').title(),
        "content": contenido,
        "status": "publish",  # Cambia a "future" si quieres programarlos
        "date": fecha_publicacion.isoformat()
    }

    print(f"[DEBUG] Publicando '{post['title']}' con fecha {post['date']}...")

    try:
        response = requests.post(wp_url, headers=headers, json=post)
        if response.status_code == 201:
            print(f"[OK] Publicado: {filename}")
        else:
            print(f"[ERROR] Falló la publicación de {filename}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[ERROR] Excepción al publicar {filename}: {e}")

