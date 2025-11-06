#!/usr/bin/env python3

import os
import requests
from datetime import datetime, timedelta
from base64 import b64encode

# CONFIGURACIÓN
print("[DEBUG] Configurando parámetros...")

wp_url = "https://datablogcafe.com/wp-json/wp/v2/posts"
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
                contenido = f.read()
        except Exception as e:
            print(f"[ERROR] No se pudo leer el archivo {filename}: {e}")
            continue

        # Fecha de publicación incremental
        fecha_publicacion = fecha_base + timedelta(days=indice * 2)

        # Título desde el nombre del archivo
        titulo = filename.replace('.md', '').replace('_', ' ').title()

        # Datos del post
        post = {
            "title": titulo,
            "content": contenido,
            "status": "publish",  # Cambia a "future" si quieres programarlos
            "date": fecha_publicacion.isoformat()
        }

        print(f"[DEBUG] Publicando '{titulo}' con fecha {fecha_publicacion.isoformat()}...")

        try:
            response = requests.post(wp_url, headers=headers, json=post)
            if response.status_code == 201:
                print(f"[OK] Publicado: {filename}")
            else:
                print(f"[ERROR] Falló la publicación de {filename}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[ERROR] Excepción al publicar {filename}: {e}")

        indice += 1  # Solo contar archivos válidos

