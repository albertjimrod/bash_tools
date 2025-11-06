#!/usr/bin/env python3
import os
import subprocess
import json
import time
import tempfile
import sys

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:14b")

if len(sys.argv) >= 2:
    DIRECTORIO_ENTRADA = sys.argv[1]
else:
    print("❌ Debes indicar un directorio de entrada.")
    print("👉 Ejemplo: python3 generar_articulos.py DQ/")
    sys.exit(1)

base_nombre = os.path.basename(os.path.normpath(DIRECTORIO_ENTRADA))
DIRECTORIO_SALIDA = f"{base_nombre}_procesado"

print("📡 OLLAMA_HOST =", OLLAMA_HOST)
print("📦 OLLAMA_MODEL =", OLLAMA_MODEL)
print(f"📁 Explorando directorio: {DIRECTORIO_ENTRADA}")
print(f"📤 Guardando resultados en: {DIRECTORIO_SALIDA}\n")


def generar_articulo_con_ollama(contenido_md):
    prompt_usuario = (
        "Eres un redactor técnico especializado en ciencia de datos y machine learning. "
        "Tu tarea es convertir notas técnicas en artículos claros, educativos y atractivos "
        "para lectores interesados en tecnología, ciencia de datos y ML.\n\n"

        "INSTRUCCIONES ESPECÍFICAS:\n\n"

        "1. ANÁLISIS DE CONTENIDO:\n"
        "- Si encuentras bloques de código con comandos de instalación → crea una sección tutorial paso a paso\n"
        "- Si ves configuraciones técnicas → explícalas de forma didáctica con contexto\n"
        "- Si hay comandos SSH o Docker → desarrolla una guía práctica con explicaciones\n"
        "- Si hay IPs, usuarios o configuraciones específicas → usa ejemplos genéricos cuando sea útil\n\n"

        "2. ESTRUCTURA DEL ARTÍCULO:\n"
        "- Título atractivo y descriptivo\n"
        "- Introducción que explique el 'por qué' es útil esto\n"
        "- Desarrollo técnico explicado de forma clara\n"
        "- Secciones prácticas con comandos (formateados como código)\n"
        "- Consejos, mejores prácticas o consideraciones importantes\n"
        "- Conclusión con valor práctico\n\n"

        "3. TONO Y ESTILO:\n"
        "- Lenguaje claro, profesional pero accesible\n"
        "- Evita jerga innecesaria, explica términos técnicos\n"
        "- Usa viñetas, listas y formato amigable para lectura\n"
        "- Incluye llamados a la acción ('prueba esto', 'considera esto')\n\n"

        "4. PÚBLICO OBJETIVO:\n"
        "- Profesionales de datos, desarrolladores, entusiastas de ML\n"
        "- Nivel técnico medio a avanzado\n"
        "- Interés en herramientas prácticas y soluciones reales\n\n"

        "CONTEXTO ADICIONAL:\n"
        "- El contenido original puede incluir configuraciones de Ollama, Docker, SSH, modelos de lenguaje\n"
        "- Debes mantener la precisión técnica pero hacerlo entretenido y útil\n"
        "- Crea plantillas reutilizables cuando sea apropiado\n"
        "- Si ves información de conexión (IPs, puertos), úsala como ejemplo concreto\n\n"

        "Convierte el siguiente contenido técnico en un artículo claro, educativo "
        "y disfrutable para un lector general interesado en ciencia de datos, "
        "machine learning o tecnología:\n\n" + contenido_md
    )

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt_usuario}],
        "stream": False
    }

    try:
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as temp_file:
            json.dump(payload, temp_file)
            temp_file_path = temp_file.name

        result = subprocess.run(
            ["curl", f"{OLLAMA_HOST}/api/chat", "-s",
             "-H", "Content-Type: application/json",
             "-d", f"@{temp_file_path}"],
            check=True,
            stdout=subprocess.PIPE
        )
        data = json.loads(result.stdout.decode("utf-8"))
        output = data.get("message", {}).get("content", "").strip()

        if not output:
            return "[⚠️ Artículo vacío]"

        return output

    except Exception as e:
        return f"[⚠️ Error generando artículo: {e}]"
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def procesar_archivos():
    if not os.path.isdir(DIRECTORIO_ENTRADA):
        print(f"❌ El directorio no existe: {DIRECTORIO_ENTRADA}")
        sys.exit(1)

    total = 0
    os.makedirs(DIRECTORIO_SALIDA, exist_ok=True)

    for carpeta_raiz, _, archivos in os.walk(DIRECTORIO_ENTRADA):
        for archivo in archivos:
            if archivo.endswith(".md"):
                ruta_entrada = os.path.join(carpeta_raiz, archivo)
                subruta = os.path.relpath(carpeta_raiz, DIRECTORIO_ENTRADA)
                nombre_salida = archivo.replace(".md", "_articulo.md")
                ruta_salida = os.path.join(DIRECTORIO_SALIDA, subruta, nombre_salida)

                os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

                print(f"📄 Procesando: {ruta_entrada}")
                with open(ruta_entrada, 'r', encoding='utf-8') as f:
                    contenido = f.read()

                start = time.time()
                articulo = generar_articulo_con_ollama(contenido)
                duracion = time.time() - start

                with open(ruta_salida, 'w', encoding='utf-8') as f:
                    f.write(articulo)

                print(f"✅ Guardado en: {ruta_salida} ({duracion:.2f} s)\n")
                total += 1

    print(f"🧾 Proceso finalizado: {total} artículos generados.")


if __name__ == "__main__":
    procesar_archivos()
