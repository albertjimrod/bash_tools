#!/usr/bin/env python3
"""
WordPress Publisher - Publicador automático de posts con gestión de fechas y tags
Características: Deduplica, crea tags automáticos, modifica fechas, sin credenciales expuestas
"""

import os
import sys
import re
import logging
from datetime import datetime, timedelta
from base64 import b64encode
import requests

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[WARNING] Instala python-dotenv: pip install python-dotenv")
    sys.exit(1)

# ==================== CONFIGURACIÓN ====================

WP_URL = os.getenv("WP_URL", "https://datablogcafe.com/wp-json/wp/v2/posts")
WP_TAGS_URL = os.getenv("WP_TAGS_URL", "https://datablogcafe.com/wp-json/wp/v2/tags")
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")
ARTICULOS_DIR = os.getenv("ARTICULOS_DIR")

# Palabras clave para detectar temas (por tema)
TEMAS_KEYWORDS = {
    "data": ["data", "dataset", "database", "sql", "csv", "json"],
    "linux": ["linux", "bash", "shell", "command", "terminal", "grep", "sed", "awk"],
    "pandas": ["pandas", "dataframe", "series", "groupby", "merge"],
    "bash": ["bash", "script", "shell", "for", "while", "if", "function"],
    "python": ["python", "django", "flask", "pip", "virtualenv"],
    "machine-learning": ["machine learning", "model", "training", "algorithm", "neural", "network"],
    "deep-learning": ["deep learning", "tensorflow", "keras", "pytorch", "cnn", "lstm"],
    "web": ["html", "css", "javascript", "react", "vue", "api", "rest"],
}

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ==================== VALIDACIÓN INICIAL ====================

if not all([WP_USER, WP_PASSWORD, ARTICULOS_DIR]):
    logger.error("Faltan variables de entorno. Asegúrate de tener .env configurado.")
    logger.error(f"WP_USER: {bool(WP_USER)}, WP_PASSWORD: {bool(WP_PASSWORD)}, ARTICULOS_DIR: {bool(ARTICULOS_DIR)}")
    sys.exit(1)

if not os.path.exists(ARTICULOS_DIR):
    logger.error(f"Directorio no existe: {ARTICULOS_DIR}")
    sys.exit(1)

# ==================== FUNCIONES ====================

def get_headers():
    """Genera headers de autenticación básica para WordPress"""
    credentials = f"{WP_USER}:{WP_PASSWORD}"
    token = b64encode(credentials.encode()).decode('utf-8')
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }

def limpiar_contenido(texto):
    """Elimina etiquetas <think> y contenido no relevante"""
    # Eliminar secciones <think>
    texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL)
    # Eliminar espacios múltiples
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()

def generar_titulo_limpio(filename):
    """Genera título limpio desde nombre de archivo"""
    return filename.replace('.md', '').replace('.txt', '').replace('_', ' ').title()

def detectar_temas(titulo, contenido):
    """Detecta temas relevantes del título y contenido (optimizado con caché)"""
    texto_busqueda = (titulo + " " + contenido[:500]).lower()
    temas_detectados = set()
    
    for tema, keywords in TEMAS_KEYWORDS.items():
        if any(keyword in texto_busqueda for keyword in keywords):
            temas_detectados.add(tema)
    
    return sorted(list(temas_detectados))[:5]  # Máximo 5 tags

def obtener_o_crear_tags(temas, headers):
    """Obtiene IDs de tags existentes o los crea. Caché interno para evitar búsquedas repetidas"""
    tags_cache = {}
    ids = []
    
    for tema in temas:
        if tema in tags_cache:
            ids.append(tags_cache[tema])
            continue
        
        try:
            # Buscar tag existente
            response = requests.get(
                f"{WP_TAGS_URL}?search={tema}",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200 and response.json():
                tag_id = response.json()[0]['id']
                tags_cache[tema] = tag_id
                ids.append(tag_id)
            else:
                # Crear nuevo tag
                crear = requests.post(
                    WP_TAGS_URL,
                    headers=headers,
                    json={"name": tema},
                    timeout=5
                )
                
                if crear.status_code == 201:
                    tag_id = crear.json()['id']
                    tags_cache[tema] = tag_id
                    ids.append(tag_id)
                    logger.info(f"✓ Tag creado: {tema}")
                else:
                    logger.warning(f"✗ No se pudo crear tag '{tema}': {crear.status_code}")
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"✗ Error al procesar tag '{tema}': {e}")
    
    return ids

def post_existe(titulo, headers):
    """Verifica si un post con ese título ya existe en WordPress"""
    try:
        response = requests.get(
            f"{WP_URL}?search={titulo}",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            posts = response.json()
            # Buscar coincidencia exacta
            for post in posts:
                if post['title']['rendered'].lower() == titulo.lower():
                    return post['id'], post['date']
        return None, None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error al verificar existencia: {e}")
        return None, None

def publicar_post(titulo, contenido, fecha, tags_ids, headers):
    """Publica un post en WordPress"""
    post = {
        "title": titulo,
        "content": contenido,
        "status": "publish",
        "date": fecha.isoformat(),
        "tags": tags_ids
    }
    
    try:
        response = requests.post(WP_URL, headers=headers, json=post, timeout=10)
        if response.status_code == 201:
            post_id = response.json()['id']
            logger.info(f"✓ Publicado: {titulo} (ID: {post_id})")
            return post_id
        else:
            logger.error(f"✗ Error al publicar '{titulo}': {response.status_code}")
            logger.debug(f"  Respuesta: {response.text[:200]}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Excepción al publicar '{titulo}': {e}")
        return None

def modificar_fecha_post(post_id, nueva_fecha, headers):
    """Modifica la fecha de un post existente"""
    try:
        response = requests.post(
            f"{WP_URL}/{post_id}",
            headers=headers,
            json={"date": nueva_fecha.isoformat()},
            timeout=10
        )
        if response.status_code == 200:
            logger.info(f"  → Fecha actualizada a: {nueva_fecha.date()}")
            return True
        else:
            logger.warning(f"  → No se pudo actualizar fecha: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"  → Error al actualizar fecha: {e}")
        return False

def contar_archivos_pendientes():
    """Cuenta archivos .md y .txt sin procesar"""
    count = 0
    for root, _, files in os.walk(ARTICULOS_DIR):
        for filename in files:
            if filename.endswith((".md", ".txt")):
                count += 1
    return count

def procesar_articulos(modo="publish", esperar=False):
    """
    Procesa y publica artículos
    modo="publish": Nuevo + modificar fechas
    modo="update_dates": Solo modificar fechas de existentes
    esperar=True: Espera si no hay archivos (GPU generando)
    """
    headers = get_headers()
    fecha_base = datetime.now() - timedelta(days=730)
    
    archivos_procesados = 0
    archivos_publicados = 0
    ciclo = 0
    
    logger.info("=" * 60)
    logger.info(f"Iniciando proceso: {modo}")
    logger.info(f"Directorio: {ARTICULOS_DIR}")
    logger.info(f"Fecha base: {fecha_base.date()}")
    if esperar:
        logger.info("⏳ Modo ESPERA activado (esperando archivos de GPU)")
        logger.info("   Presiona Ctrl+C para detener cuando hayas terminado")
    logger.info("=" * 60)
    
    try:
        while True:
            ciclo += 1
            archivos_disponibles = contar_archivos_pendientes()
            
            if archivos_disponibles == 0:
                if esperar:
                    logger.info(f"\n[Ciclo {ciclo}] Sin archivos disponibles. Esperando...")
                    logger.info("   (GPU generando... presiona Ctrl+C cuando termines)")
                    import time
                    time.sleep(10)  # Espera 10 segundos antes de revisar de nuevo
                    continue
                else:
                    logger.warning("No hay archivos para procesar.")
                    break
            else:
                logger.info(f"\n[Ciclo {ciclo}] Archivos encontrados: {archivos_disponibles}")
            
            # Recorrer archivos recursivamente
            for root, _, files in os.walk(ARTICULOS_DIR):
                for filename in sorted(files):
                    if not filename.endswith((".md", ".txt")):
                        continue
                    
                    filepath = os.path.join(root, filename)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            contenido_bruto = f.read()
                    except Exception as e:
                        logger.error(f"✗ No se pudo leer {filename}: {e}")
                        continue
                    
                    contenido = limpiar_contenido(contenido_bruto)
                    titulo = generar_titulo_limpio(filename)
                    
                    # Calcular fecha incremental
                    fecha_publicacion = fecha_base + timedelta(days=archivos_procesados * 2)
                    
                    logger.info(f"\n[{archivos_procesados + 1}] {titulo}")
                    
                    # Verificar si existe
                    post_id, fecha_existente = post_existe(titulo, headers)
                    
                    if post_id:
                        logger.info(f"  → Post ya existe (ID: {post_id})")
                        
                        # Actualizar fecha si es diferente
                        if fecha_existente and fecha_existente.split('T')[0] != fecha_publicacion.date().isoformat():
                            logger.info(f"  → Fecha actual: {fecha_existente.split('T')[0]}")
                            modificar_fecha_post(post_id, fecha_publicacion, headers)
                    else:
                        # Publicar nuevo
                        temas = detectar_temas(titulo, contenido)
                        tags_ids = obtener_o_crear_tags(temas, headers)
                        
                        logger.info(f"  → Tags detectados: {temas}")
                        
                        if publicar_post(titulo, contenido, fecha_publicacion, tags_ids, headers):
                            archivos_publicados += 1
                    
                    archivos_procesados += 1
            
            # Si no está en modo espera, salir después del primer ciclo
            if not esperar:
                break
    
    except KeyboardInterrupt:
        logger.info("\n\n⏹ Proceso detenido por el usuario")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Resumen: {archivos_publicados} nuevos, {archivos_procesados} procesados")
    logger.info("=" * 60)

# ==================== MAIN ====================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "update_dates":
            logger.info("Modo: Actualizar solo fechas de posts existentes")
            procesar_articulos(modo="update_dates", esperar=False)
        elif sys.argv[1] == "wait" or sys.argv[1] == "esperar":
            logger.info("Modo: ESPERA (esperando que GPU genere archivos)")
            procesar_articulos(modo="publish", esperar=True)
        elif sys.argv[1] == "help" or sys.argv[1] == "--help":
            print("""
WordPress Publisher - Opciones disponibles:

  python3 wordpress_publisher.py
    → Publica nuevos posts + actualiza fechas (una sola vez)

  python3 wordpress_publisher.py wait
    → MODO ESPERA: Espera a que GPU genere archivos
       Revisa cada 10 segundos
       Presiona Ctrl+C cuando termines

  python3 wordpress_publisher.py update_dates
    → Solo actualiza fechas de posts existentes
    
  python3 wordpress_publisher.py help
    → Muestra esta ayuda
            """)
        else:
            logger.error(f"Opción desconocida: {sys.argv[1]}")
            print("Usa: python3 wordpress_publisher.py help")
    else:
        logger.info("Modo: Publicar nuevos + actualizar fechas (una sola vez)")
        procesar_articulos(modo="publish", esperar=False)
