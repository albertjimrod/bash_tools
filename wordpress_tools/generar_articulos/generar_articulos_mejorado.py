#!/usr/bin/env python3
"""
Script mejorado para generar articulos con Ollama
Optimizado para DeepSeek-R1:14b
Version: 2.0
Fecha: Noviembre 2025
"""

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
    print("Debes indicar un directorio de entrada.")
    print("Ejemplo: python3 generar_articulos_MEJORADO.py DQ/")
    sys.exit(1)

base_nombre = os.path.basename(os.path.normpath(DIRECTORIO_ENTRADA))
DIRECTORIO_SALIDA = f"{base_nombre}_procesado"

print("=" * 80)
print("GENERADOR DE ARTICULOS CON IA - VERSION MEJORADA 2.0")
print("=" * 80)
print(f"OLLAMA_HOST = {OLLAMA_HOST}")
print(f"OLLAMA_MODEL = {OLLAMA_MODEL}")
print(f"Explorando directorio: {DIRECTORIO_ENTRADA}")
print(f"Guardando resultados en: {DIRECTORIO_SALIDA}\n")


def generar_articulo_con_ollama(contenido_md):
    """
    Genera un articulo usando Ollama con prompt optimizado para DeepSeek-R1
    """
    
    # PROMPT OPTIMIZADO PARA DEEPSEEK-R1:14B
    prompt_usuario = (
        "INSTRUCCION PRINCIPAL:\n"
        "Eres un redactor tecnico experto en ciencia de datos, machine learning e ingenieria de software. "
        "Tu mision es transformar notas tecnicas desorganizadas en articulos profesionales, educativos "
        "y altamente legibles. El resultado debe ser comparable a articulos publicados en blogs tecnico "
        "de alto nivel (Medium, Dev.to, blogs corporativos).\n\n"

        "OBJETIVO FINAL:\n"
        "Crear un articulo que sea:\n"
        "- Preciso en contenido tecnico\n"
        "- Accesible para nivel medio-avanzado\n"
        "- Bien estructurado y facil de seguir\n"
        "- Practico con ejemplos ejecutables\n"
        "- Atractivo para lectores profesionales\n\n"

        "ESTRUCTURA DEL ARTICULO (OBLIGATORIA):\n\n"

        "A) TITULO Y SUBTITULO\n"
        "   - Titulo: Atractivo, descriptivo, 60-70 caracteres maximo\n"
        "   - Subtitulo: Explica beneficio o resultado en 1 linea\n"
        "   - Ejemplo: 'Docker en Linux: Instalacion, Configuracion y Primeros Pasos'\n\n"

        "B) INTRODUCCION (1-2 parrafos, 150-200 palabras)\n"
        "   - Empieza con una pregunta o problema real\n"
        "   - Explica POR QUE esto es importante para el lector\n"
        "   - Menciona el beneficio principal\n"
        "   - Anuncia lo que el lector aprendera\n\n"

        "C) CONCEPTOS BASICOS (si es necesario)\n"
        "   - Explica conceptos clave sin asumirlos conocidos\n"
        "   - Usa analogias del mundo real para conceptos complejos\n"
        "   - Secciona con headers claros\n\n"

        "D) SECCION PRACTICA PRINCIPAL\n"
        "   - Divide en pasos numerados si es procedimiento\n"
        "   - O en subsecciones tematicas si es concepto\n"
        "   - Cada paso: Explicacion + Codigo/Ejemplo + Resultado esperado\n"
        "   - Formato de codigo: Bloques con tres acentos grave (```bash o ```python)\n"
        "   - Incluye comentarios en codigo explicando que hace\n\n"

        "E) EJEMPLOS PRACTICOS\n"
        "   - Minimo 2-3 ejemplos reales y diferentes\n"
        "   - Con comandos exactos que pueden copiar-pegar\n"
        "   - Mostrar entrada, proceso, salida esperada\n"
        "   - Advertencias de errores comunes\n\n"

        "F) MEJORES PRACTICAS Y TIPS (minimo 5)\n"
        "   - Agrupa en seccion 'Pro Tips' o 'Consideraciones Importantes'\n"
        "   - Include rendimiento, seguridad, escalabilidad\n"
        "   - Usa formato de viñetas\n\n"

        "G) TROUBLESHOOTING (Errores Comunes)\n"
        "   - Formato: [ERROR] | Causa | Solucion\n"
        "   - Minimo 2-3 errores tipicos\n"
        "   - Soluciones paso a paso\n\n"

        "H) RESUMEN Y LLAMADO A ACCION\n"
        "   - Recapitula puntos principales (3-4 lineas)\n"
        "   - Proximo paso logico: 'Ahora que dominas esto, prueba...'\n"
        "   - Invita a experimentar\n\n"

        "ESTILO DE ESCRITURA:\n\n"

        "TONO:\n"
        "- Profesional pero amigable (como un mentor senior)\n"
        "- Confiado pero no arrogante\n"
        "- Educativo sin ser condescendiente\n"
        "- Practico y orientado a resultados\n\n"

        "LENGUAJE:\n"
        "- Evita jerga innecesaria o explica la que uses\n"
        "- Parrafos cortos (3-5 lineas maximo)\n"
        "- Oraciones directas y claras\n"
        "- No uses palabras complejas si simples dicen lo mismo\n"
        "- Espanol correcto, CERO caracteres asiaticos\n\n"

        "FORMATO:\n"
        "- Usa ### para subsecciones principales\n"
        "- Usa viñetas (-) para listas\n"
        "- Usa numeros (1. 2. 3.) solo para procedimientos con orden\n"
        "- Resalta comandos importantes en codigo\n"
        "- Usa negrita **para enfasis** en puntos clave\n"
        "- Usa cursiva *para terminos introducidos por primera vez*\n\n"

        "CRITERIOS DE CALIDAD MINIMO:\n"
        "- Articulo debe tener 1200-1500 palabras\n"
        "- Minimo 2-3 bloques de codigo ejecutables\n"
        "- Explicacion clara del que hace cada comando\n"
        "- Ejemplos con entrada/proceso/salida\n"
        "- Minimo 5 Pro Tips o mejores practicas\n"
        "- Seccion de Troubleshooting con errores comunes\n"
        "- Conclusion con proximo paso recomendado\n"
        "- CERO caracteres asiaticos (solo espanol e ingles)\n"
        "- Lenguaje profesional y accesible\n"
        "- Formato consistente y bien organizado\n"
        "- Informacion tecnica precisa y verificable\n\n"

        "REGLAS ESPECIALES:\n\n"

        "SI ES TUTORIAL:\n"
        "- Numero cada paso claramente\n"
        "- Indica tiempo estimado total\n"
        "- Requisitos previos al inicio\n"
        "- Verificacion de exito para cada paso\n\n"

        "SI ES CONCEPTO:\n"
        "- Empieza con analogia del mundo real\n"
        "- Ejemplos graduados (simple -> complejo)\n"
        "- Casos de uso reales al final\n\n"

        "SI HAY CODIGO:\n"
        "- Primero la version simple/comentada\n"
        "- Luego version con opciones avanzadas\n"
        "- Explica cada seccion importante\n"
        "- Indica que librerias/dependencias se necesitan\n\n"

        "SI HAY CONFIGURACION TECNICA:\n"
        "- Convierte en ejemplos genericos cuando sea apropiado\n"
        "- Pero muestra resultado con ejemplo concreto\n"
        "- Explica que significa cada valor\n"
        "- Menciona donde puede encontrar estos valores\n\n"

        "AHORA, TRANSFORMA ESTE CONTENIDO EN UN ARTICULO PROFESIONAL:\n\n"
        "===========================================================================\n\n"
        + contenido_md +
        "\n\n"
        "===========================================================================\n\n"
        "IMPORTANTE:\n"
        "1. Respeta la estructura de 8 pasos descrita arriba\n"
        "2. Asegúrate de minimo 1200-1500 palabras\n"
        "3. Verifica: CERO caracteres asiaticos, espanol correcto\n"
        "4. Haz el articulo interesante, practico y profesional\n"
        "5. El lector debe terminar el articulo sabiendo COMO HACER ESTO\n"
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
            return "[ERROR] Articulo vacio"

        return output

    except Exception as e:
        return f"[ERROR] Error generando articulo: {e}"
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def procesar_archivos():
    """
    Procesa todos los archivos .md en el directorio especificado
    """
    if not os.path.isdir(DIRECTORIO_ENTRADA):
        print(f"[ERROR] El directorio no existe: {DIRECTORIO_ENTRADA}")
        sys.exit(1)

    total = 0
    errores = 0
    os.makedirs(DIRECTORIO_SALIDA, exist_ok=True)

    print("\nIniciando procesamiento...\n")

    for carpeta_raiz, _, archivos in os.walk(DIRECTORIO_ENTRADA):
        for archivo in archivos:
            if archivo.endswith(".md"):
                ruta_entrada = os.path.join(carpeta_raiz, archivo)
                subruta = os.path.relpath(carpeta_raiz, DIRECTORIO_ENTRADA)
                nombre_salida = archivo.replace(".md", "_articulo.md")
                ruta_salida = os.path.join(DIRECTORIO_SALIDA, subruta, nombre_salida)

                os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

                print(f"[{total+1}] Procesando: {ruta_entrada}")
                
                try:
                    with open(ruta_entrada, 'r', encoding='utf-8') as f:
                        contenido = f.read()

                    if not contenido.strip():
                        print(f"     [ADVERTENCIA] Archivo vacio\n")
                        errores += 1
                        continue

                    start = time.time()
                    articulo = generar_articulo_con_ollama(contenido)
                    duracion = time.time() - start

                    if "[ERROR]" in articulo:
                        print(f"     [ERROR] {articulo}\n")
                        errores += 1
                        continue

                    with open(ruta_salida, 'w', encoding='utf-8') as f:
                        f.write(articulo)

                    # Estadisticas
                    palabras = len(articulo.split())
                    caracteres = len(articulo)
                    
                    print(f"     [OK] Guardado en: {ruta_salida}")
                    print(f"     Tiempo: {duracion:.2f}s | Palabras: {palabras} | Caracteres: {caracteres}\n")
                    total += 1

                except Exception as e:
                    print(f"     [ERROR] {str(e)}\n")
                    errores += 1

    print("=" * 80)
    print(f"PROCESAMIENTO FINALIZADO")
    print("=" * 80)
    print(f"Total procesados: {total}")
    print(f"Total errores: {errores}")
    print(f"Directorio de salida: {DIRECTORIO_SALIDA}/")
    print()


if __name__ == "__main__":
    procesar_archivos()
