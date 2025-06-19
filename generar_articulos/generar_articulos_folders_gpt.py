#!/usr/bin/env python3
import os
import json
import time
import sys
import requests

# ⚙️ Configuración
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

if not API_KEY:
    print("❌ Falta la variable de entorno OPENAI_API_KEY.")
    sys.exit(1)

def generar_articulo_con_chatgpt(contenido_md):
    prompt_usuario = (
        "Convierte el siguiente contenido técnico en un artículo claro, educativo "
        "y disfrutable para un lector general interesado en ciencia de datos, "
        "machine learning o tecnología:\n\n" + contenido_md
    )

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt_usuario}],
        "temperature": 0.7,
        "stream": False
    }

    url = "https://api.openai.com/v1/chat/completions"

    print(f"🚀 Enviando solicitud a ChatGPT ({MODEL})...")
    start = time.time()

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        output = data["choices"][0]["message"]["content"].strip()
        duration = time.time() - start
        print(f"✅ Generado en {duration:.2f} segundos.\n")
        return output

    except requests.exceptions.RequestException as e:
        print(f"❌ Error en la solicitud: {e}")
        return f"[⚠️ Error de conexión: {e}]"
    except Exception as e:
        print(f"⚠️ Otro error: {e}")
        return f"[⚠️ Error inesperado: {e}]"

def procesar_archivos(directorio_entrada):
    if not os.path.isdir(directorio_entrada):
        print(f"❌ Directorio inválido: {directorio_entrada}")
        sys.exit(1)

    directorio_salida = f"{directorio_entrada.rstrip('/')}_procesado"
    os.makedirs(directorio_salida, exist_ok=True)

    print(f"📁 Explorando: {directorio_entrada}\n")
    total = 0

    for carpeta_raiz, _, archivos in os.walk(directorio_entrada):
        for archivo in archivos:
            if archivo.endswith(".md"):
                ruta_entrada = os.path.join(carpeta_raiz, archivo)
                subruta = os.path.relpath(carpeta_raiz, directorio_entrada)
                nombre_salida = archivo.replace(".md", "_articulo.md")
                ruta_salida = os.path.join(directorio_salida, subruta, nombre_salida)

                os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

                print(f"📄 Procesando: {ruta_entrada}")
                with open(ruta_entrada, "r", encoding="utf-8") as f:
                    contenido = f.read()

                articulo = generar_articulo_con_chatgpt(contenido)

                with open(ruta_salida, "w", encoding="utf-8") as f:
                    f.write(articulo)

                print(f"💾 Guardado en: {ruta_salida}\n")
                total += 1

    print(f"🧾 Finalizado. Artículos generados: {total}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❌ Uso: python3 generar_articulos_chatgpt.py <directorio_entrada>")
        sys.exit(1)

    procesar_archivos(sys.argv[1])

