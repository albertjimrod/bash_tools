#!/usr/bin/env python3
"""
WordPress Publisher - Script unificado
Publicar, gestionar fechas y diagnosticar posts en WordPress

Uso:
  python3 wp_publisher.py [COMANDO] [OPCIONES]

Comandos:
  publish       Publicar artículos nuevos (por defecto)
  draft         Publicar artículos como borradores
  wait          Esperar en bucle a que aparezcan archivos (GPU generando)
  update-dates  Solo actualizar fechas de posts existentes
  diagnose      Diagnóstico completo de conexión y servidor
  verify        Verificar estado y límites del servidor
  reset         Limpiar checkpoint y empezar desde cero
  help          Mostrar esta ayuda

Opciones:
  --dir PATH    Directorio de artículos (sobreescribe ARTICULOS_DIR del .env)
  --limit N     Procesar máximo N artículos
  --delay N     Segundos entre requests (por defecto: 8)
"""

import os
import sys
import re
import json
import logging
import time
from datetime import datetime, timedelta
from base64 import b64encode
from typing import Optional, Tuple, List, Dict

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# ==================== CARGAR .env ====================

try:
    from dotenv import load_dotenv
    load_dotenv(verbose=False)
except ImportError:
    print("[ERROR] Instala python-dotenv: pip install python-dotenv")
    sys.exit(1)

# ==================== CONFIGURACIÓN ====================

WP_URL      = os.getenv("WP_URL", "").strip()
WP_TAGS_URL = os.getenv("WP_TAGS_URL", "").strip()
WP_USER     = os.getenv("WP_USER", "").strip()
WP_PASSWORD = os.getenv("WP_PASSWORD", "").strip()
ARTICULOS_DIR = os.getenv("ARTICULOS_DIR", "").strip()

# Defaults conservadores (pensados para Hetzner con >2000 posts)
MAX_RETRIES     = 2
BACKOFF_FACTOR  = 10    # esperas: 10s, 100s
REQUEST_TIMEOUT = 45
DEFAULT_DELAY   = 8     # segundos entre posts
CHECKPOINT_FILE = ".wp_publisher_checkpoint.json"

TEMAS_KEYWORDS = {
    "data":            ["data", "dataset", "database", "sql", "csv", "json"],
    "linux":           ["linux", "bash", "shell", "command", "terminal", "grep", "sed", "awk"],
    "pandas":          ["pandas", "dataframe", "series", "groupby", "merge"],
    "bash":            ["bash", "script", "shell"],
    "python":          ["python", "django", "flask", "pip", "virtualenv"],
    "machine-learning":["machine learning", "model", "training", "algorithm", "neural"],
    "deep-learning":   ["deep learning", "tensorflow", "keras", "pytorch", "cnn", "lstm"],
    "web":             ["html", "css", "javascript", "react", "vue", "api", "rest"],
}

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# ==================== SESIÓN HTTP CON REINTENTOS ====================

def create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[500, 502, 503, 504, 429],
        allowed_methods=["GET", "POST", "DELETE"],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

http_session = create_session()

# ==================== UTILIDADES ====================

def get_headers() -> Dict[str, str]:
    token = b64encode(f"{WP_USER}:{WP_PASSWORD}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }

def limpiar_contenido(texto: str) -> str:
    texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()

def generar_titulo_limpio(filename: str) -> str:
    titulo = filename.replace(".md", "").replace(".txt", "").replace("_", " ")
    titulo = re.sub(r"\s+[Aa]rticulo$", "", titulo)
    return titulo.title()[:200]

def detectar_temas(titulo: str, contenido: str) -> List[str]:
    texto = (titulo + " " + contenido[:500]).lower()
    temas = set()
    for tema, keywords in TEMAS_KEYWORDS.items():
        if any(kw in texto for kw in keywords):
            temas.add(tema)
    return sorted(temas)[:5]

def safe_request(method: str, url: str, headers: Dict, delay: int = DEFAULT_DELAY, **kwargs) -> Optional[requests.Response]:
    """Request con backoff exponencial ante errores de servidor."""
    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                wait = BACKOFF_FACTOR ** (attempt + 1)
                logger.warning(f"  Esperando {wait}s antes de reintentar...")
                time.sleep(wait)

            response = http_session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                **kwargs
            )

            if response.status_code < 400:
                return response

            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 120))
                logger.warning(f"  Rate limit (429). Esperando {wait}s...")
                time.sleep(wait)
                continue

            if response.status_code >= 500:
                logger.warning(f"  Error {response.status_code}. Intento {attempt+1}/{MAX_RETRIES}")
                try:
                    msg = response.json().get("message", "")
                    if msg:
                        logger.warning(f"  -> {msg}")
                except Exception:
                    pass
                continue

            return response

        except requests.exceptions.Timeout:
            logger.warning(f"  Timeout. Intento {attempt+1}/{MAX_RETRIES}")
        except requests.exceptions.ConnectionError:
            logger.warning(f"  Error de conexión. Intento {attempt+1}/{MAX_RETRIES}")
        except Exception as e:
            logger.error(f"  Error inesperado: {e}")
            return None

    logger.error(f"  Falló después de {MAX_RETRIES} intentos")
    return None

# ==================== TAGS ====================

tags_cache: Dict[str, int] = {}

def obtener_o_crear_tags(temas: List[str], headers: Dict) -> List[int]:
    ids = []
    for tema in temas:
        if tema in tags_cache:
            ids.append(tags_cache[tema])
            continue

        r = safe_request("GET", f"{WP_TAGS_URL}?search={tema}", headers)
        if r and r.status_code == 200 and r.json():
            tag_id = r.json()[0]["id"]
            tags_cache[tema] = tag_id
            ids.append(tag_id)
        else:
            r = safe_request("POST", WP_TAGS_URL, headers, json={"name": tema})
            if r and r.status_code == 201:
                tag_id = r.json()["id"]
                tags_cache[tema] = tag_id
                ids.append(tag_id)
                logger.info(f"  Tag creado: {tema}")
            else:
                logger.warning(f"  No se pudo crear tag '{tema}'")

        time.sleep(1)

    return ids

# ==================== POSTS ====================

def post_existe(titulo: str, headers: Dict) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    r = safe_request("GET", f"{WP_URL}?search={titulo}&per_page=5", headers)
    if r and r.status_code == 200:
        for post in r.json():
            if post["title"]["rendered"].lower().strip() == titulo.lower().strip():
                return post["id"], post.get("date"), post.get("status")
    return None, None, None

def cambiar_estado_post(post_id: int, estado: str, headers: Dict) -> bool:
    r = safe_request("POST", f"{WP_URL}/{post_id}", headers, json={"status": estado})
    return bool(r and r.status_code == 200)

def modificar_fecha_post(post_id: int, fecha: datetime, headers: Dict) -> bool:
    r = safe_request("POST", f"{WP_URL}/{post_id}", headers, json={"date": fecha.isoformat()})
    return bool(r and r.status_code == 200)

def publicar_post(titulo: str, contenido: str, fecha: datetime,
                  tags_ids: List[int], headers: Dict, status: str = "publish") -> Optional[int]:
    if len(contenido) > 100_000:
        contenido = contenido[:100_000] + "\n\n[Contenido truncado]"
        logger.warning("  Contenido truncado (>100KB)")

    post = {
        "title": titulo,
        "content": contenido,
        "status": status,
        "date": fecha.isoformat(),
        "tags": tags_ids
    }

    r = safe_request("POST", WP_URL, headers, json=post)
    if r and r.status_code == 201:
        return r.json()["id"]
    elif r:
        logger.error(f"  Status: {r.status_code}")
        try:
            logger.error(f"  {r.json().get('message', r.text[:150])}")
        except Exception:
            logger.error(f"  {r.text[:150]}")
    return None

# ==================== CHECKPOINT ====================

def cargar_checkpoint() -> Dict:
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r") as f:
                data = json.load(f)
                procesados = len(data.get("procesados", []))
                if procesados:
                    logger.info(f"Checkpoint cargado: {procesados} archivos ya procesados")
                return data
        except Exception:
            pass
    return {"procesados": [], "exitosos": 0}

def guardar_checkpoint(data: Dict):
    try:
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"No se pudo guardar checkpoint: {e}")

def limpiar_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        logger.info("Checkpoint eliminado")

# ==================== PROCESAMIENTO ====================

def obtener_archivos(articulos_dir: str) -> List[str]:
    archivos = []
    for root, _, files in os.walk(articulos_dir):
        for f in sorted(files):
            if f.endswith((".md", ".txt")):
                archivos.append(os.path.join(root, f))
    return archivos

def procesar_articulos(status: str, articulos_dir: str, limit: Optional[int], delay: int):
    """
    Procesa artículos y los publica/borra.
    status: "publish" o "draft"
    """
    headers = get_headers()
    fecha_base = datetime.now() - timedelta(days=730)

    checkpoint = cargar_checkpoint()
    procesados_previos = set(checkpoint.get("procesados", []))
    errores_previos = checkpoint.get("errores", [])
    exitosos_previos = checkpoint.get("exitosos", 0)

    archivos = obtener_archivos(articulos_dir)
    total = len(archivos)
    pendientes = [f for f in archivos if f not in procesados_previos]

    if limit is not None:
        pendientes = pendientes[:limit]

    logger.info("=" * 70)
    logger.info(f"MODO: {status.upper()}")
    logger.info(f"Directorio: {articulos_dir}")
    logger.info(f"Total archivos:    {total}")
    logger.info(f"Ya procesados:     {len(procesados_previos)}")
    logger.info(f"A procesar ahora:  {len(pendientes)}{f' (límite: {limit})' if limit else ''}")
    logger.info(f"Delay entre posts: {delay}s")
    logger.info("=" * 70)

    if not pendientes:
        logger.info("Nada pendiente. Todos los archivos ya fueron procesados.")
        return

    stats = {
        "exitosos": exitosos_previos,
        "ya_existen": 0,
        "errores": 0,
        "inicio": time.time()
    }

    try:
        for i, filepath in enumerate(pendientes):
            filename = os.path.basename(filepath)
            progreso = len(procesados_previos) + i + 1
            pct = (progreso / total) * 100

            logger.info(f"\n{'='*70}")
            logger.info(f"[{progreso}/{total}] ({pct:.1f}%) {filename}")

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    contenido_bruto = f.read()
            except Exception as e:
                logger.error(f"  Error leyendo archivo: {e}")
                stats["errores"] += 1
                errores_previos.append({"archivo": filename, "error": str(e)})
                procesados_previos.add(filepath)
                guardar_checkpoint({"procesados": list(procesados_previos),
                                    "errores": errores_previos,
                                    "exitosos": stats["exitosos"]})
                continue

            contenido = limpiar_contenido(contenido_bruto)
            titulo = generar_titulo_limpio(filename)
            fecha_pub = fecha_base + timedelta(days=progreso * 2)

            logger.info(f"  Titulo: {titulo[:60]}")

            post_id, fecha_actual, estado_actual = post_existe(titulo, headers)

            if post_id:
                logger.info(f"  Ya existe (ID: {post_id}, Estado: {estado_actual})")
                stats["ya_existen"] += 1

                if estado_actual == "future":
                    if cambiar_estado_post(post_id, "draft", headers):
                        logger.info("  Estado: future → draft")
                    time.sleep(delay)

                if fecha_actual:
                    fecha_str = fecha_actual.split("T")[0]
                    if fecha_str != fecha_pub.date().isoformat():
                        if modificar_fecha_post(post_id, fecha_pub, headers):
                            logger.info(f"  Fecha: {fecha_str} → {fecha_pub.date()}")
                        time.sleep(delay)
            else:
                temas = detectar_temas(titulo, contenido)
                tags_ids = obtener_o_crear_tags(temas, headers)
                if temas:
                    logger.info(f"  Tags: {', '.join(temas)}")

                logger.info(f"  Esperando {delay}s...")
                time.sleep(delay)

                logger.info(f"  Creando post como {status.upper()}...")
                nuevo_id = publicar_post(titulo, contenido, fecha_pub, tags_ids, headers, status)

                if nuevo_id:
                    logger.info(f"  OK (ID: {nuevo_id})")
                    stats["exitosos"] += 1
                else:
                    logger.error("  FALLO después de reintentos")
                    stats["errores"] += 1
                    errores_previos.append({"archivo": filename, "titulo": titulo, "error": "500 persistente"})

            procesados_previos.add(filepath)
            guardar_checkpoint({"procesados": list(procesados_previos),
                                "errores": errores_previos,
                                "exitosos": stats["exitosos"]})

            if progreso % 10 == 0:
                tiempo = (time.time() - stats["inicio"]) / 60
                vel = (i + 1) / tiempo if tiempo > 0 else 0
                restante = (len(pendientes) - i - 1) / vel if vel > 0 else 0
                logger.info(f"\n  ESTADISTICAS:")
                logger.info(f"  Exitosos: {stats['exitosos']} | Ya existian: {stats['ya_existen']} | Errores: {stats['errores']}")
                logger.info(f"  Velocidad: {vel:.2f} posts/min | Tiempo restante: {restante:.0f} min ({restante/60:.1f}h)")

    except KeyboardInterrupt:
        logger.info("\n\nPROCESO DETENIDO. Checkpoint guardado. Ejecuta de nuevo para continuar.")
        sys.exit(0)

    tiempo_total = (time.time() - stats["inicio"]) / 60
    logger.info("\n" + "=" * 70)
    logger.info("RESUMEN FINAL")
    logger.info("=" * 70)
    logger.info(f"Posts exitosos:     {stats['exitosos']}")
    logger.info(f"Ya existian:        {stats['ya_existen']}")
    logger.info(f"Errores:            {stats['errores']}")
    logger.info(f"Total procesados:   {len(procesados_previos)}/{total}")
    logger.info(f"Tiempo total:       {tiempo_total:.1f} min ({tiempo_total/60:.2f}h)")
    logger.info(f"Tags en cache:      {len(tags_cache)}")
    logger.info("=" * 70)

    if status == "draft" and stats["exitosos"] > 0:
        logger.info(f"\nSIGUIENTE PASO: Publica los {stats['exitosos']} drafts desde WordPress:")
        logger.info("  https://datablogcafe.com/wp-admin/edit.php?post_status=draft")

    if len(procesados_previos) >= total:
        limpiar_checkpoint()
        logger.info("Proceso completado al 100%. Checkpoint eliminado.")


def cmd_update_dates(articulos_dir: str, limit: Optional[int], delay: int):
    """Recorre los archivos y actualiza las fechas de los posts existentes."""
    headers = get_headers()
    fecha_base = datetime.now() - timedelta(days=730)

    archivos = obtener_archivos(articulos_dir)
    total = len(archivos)

    if limit is not None:
        archivos = archivos[:limit]

    logger.info("=" * 70)
    logger.info("MODO: UPDATE-DATES")
    logger.info(f"Directorio: {articulos_dir}")
    logger.info(f"Archivos a revisar: {len(archivos)}{f' (límite: {limit})' if limit else ''}")
    logger.info("=" * 70)

    actualizados = 0
    no_encontrados = 0
    errores = 0

    try:
        for i, filepath in enumerate(archivos):
            filename = os.path.basename(filepath)
            titulo = generar_titulo_limpio(filename)
            fecha_objetivo = fecha_base + timedelta(days=(i + 1) * 2)

            logger.info(f"\n[{i+1}/{len(archivos)}] {titulo[:60]}")

            post_id, fecha_actual, estado = post_existe(titulo, headers)

            if not post_id:
                logger.info("  No encontrado en WordPress, omitiendo.")
                no_encontrados += 1
                continue

            fecha_str = fecha_actual.split("T")[0] if fecha_actual else None

            if fecha_str == fecha_objetivo.date().isoformat():
                logger.info(f"  Fecha ya correcta: {fecha_str}")
            else:
                logger.info(f"  Fecha actual: {fecha_str} → nueva: {fecha_objetivo.date()}")
                time.sleep(delay)
                if modificar_fecha_post(post_id, fecha_objetivo, headers):
                    logger.info("  OK")
                    actualizados += 1
                else:
                    logger.error("  Error al actualizar")
                    errores += 1

    except KeyboardInterrupt:
        logger.info("\n\nPROCESO DETENIDO.")
        sys.exit(0)

    logger.info("\n" + "=" * 70)
    logger.info("RESUMEN UPDATE-DATES")
    logger.info("=" * 70)
    logger.info(f"Fechas actualizadas: {actualizados}")
    logger.info(f"No encontrados:      {no_encontrados}")
    logger.info(f"Errores:             {errores}")
    logger.info("=" * 70)

# ==================== MODO ESPERA ====================

def cmd_wait(articulos_dir: str, limit: Optional[int], delay: int):
    """Espera en bucle a que aparezcan archivos nuevos y los publica (útil cuando GPU genera artículos)."""
    logger.info("=" * 70)
    logger.info("MODO: WAIT (esperando archivos generados por GPU)")
    logger.info(f"Directorio: {articulos_dir}")
    logger.info("Revisa cada 10 segundos. Presiona Ctrl+C para detener.")
    logger.info("=" * 70)

    try:
        while True:
            checkpoint = cargar_checkpoint()
            procesados_previos = set(checkpoint.get("procesados", []))
            archivos = obtener_archivos(articulos_dir)
            pendientes = [f for f in archivos if f not in procesados_previos]

            if pendientes:
                logger.info(f"\n{len(pendientes)} archivos nuevos encontrados. Procesando...")
                procesar_articulos("publish", articulos_dir, limit, delay)
            else:
                logger.info("Sin archivos pendientes. Esperando 10s... (Ctrl+C para salir)")
                time.sleep(10)

    except KeyboardInterrupt:
        logger.info("\n\nModo espera detenido.")
        sys.exit(0)


# ==================== DIAGNÓSTICO ====================

def cmd_diagnose():
    logger.info("=" * 70)
    logger.info("DIAGNOSTICO COMPLETO")
    logger.info("=" * 70)

    # 1. Variables de entorno
    logger.info("\n1. Variables de entorno:")
    vars_ok = True
    for var, val in [("WP_URL", WP_URL), ("WP_TAGS_URL", WP_TAGS_URL),
                     ("WP_USER", WP_USER), ("WP_PASSWORD", WP_PASSWORD),
                     ("ARTICULOS_DIR", ARTICULOS_DIR)]:
        if val:
            display = "*" * 20 if "PASSWORD" in var else val
            logger.info(f"   OK  {var}: {display}")
        else:
            logger.info(f"   ✗ {var}: NO CONFIGURADO")
            vars_ok = False

    if not vars_ok:
        logger.error("   Faltan variables en .env. Abortando diagnóstico.")
        return

    # 2. Directorio de artículos
    logger.info("\n2. Directorio de artículos:")
    if ARTICULOS_DIR and os.path.exists(ARTICULOS_DIR):
        archivos = sum(1 for r, _, fs in os.walk(ARTICULOS_DIR)
                       for f in fs if f.endswith((".md", ".txt")))
        logger.info(f"   OK  Existe: {ARTICULOS_DIR}")
        logger.info(f"      Archivos .md/.txt: {archivos}")
    else:
        logger.info(f"   ✗  No existe: {ARTICULOS_DIR}")

    headers = get_headers()

    # 3. Test GET
    logger.info("\n3. Test GET (autenticación):")
    try:
        r = requests.get(WP_URL, headers=headers, params={"per_page": 1}, timeout=10)
        logger.info(f"   Status: {r.status_code}")
        if r.status_code == 200:
            logger.info(f"   OK  Conexión y autenticación correctas")
            logger.info(f"      Total posts: {r.headers.get('X-WP-Total', 'N/A')}")
        elif r.status_code == 401:
            logger.info("   ✗  Autenticación fallida (401). Verifica credenciales.")
        elif r.status_code == 403:
            logger.info("   ✗  Acceso denegado (403). El usuario necesita rol Editor o Admin.")
        else:
            logger.info(f"   ⚠  Respuesta inesperada: {r.text[:200]}")
    except Exception as e:
        logger.info(f"   ✗  Error de conexión: {e}")

    # 4. Test POST + DELETE
    logger.info("\n4. Test POST (crear draft de prueba):")
    try:
        test = {
            "title": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "content": "Post de prueba. Puede eliminarse.",
            "status": "draft"
        }
        r = requests.post(WP_URL, headers=headers, json=test, timeout=20)
        logger.info(f"   Status: {r.status_code}")
        if r.status_code == 201:
            post_id = r.json()["id"]
            logger.info(f"   OK  Post creado (ID: {post_id})")
            del_r = requests.delete(f"{WP_URL}/{post_id}", headers=headers,
                                    params={"force": True}, timeout=10)
            if del_r.status_code == 200:
                logger.info("   OK  Post eliminado automáticamente")
            else:
                logger.info(f"   ⚠  Elimínalo manualmente (ID: {post_id})")
        elif r.status_code == 500:
            logger.info("   ✗  Error 500. Posibles causas:")
            logger.info("      - memory_limit de PHP insuficiente")
            logger.info("      - Plugin conflictivo (Wordfence, Jetpack...)")
            logger.info("      - Base de datos con problemas")
            try:
                logger.info(f"      Detalle: {r.json().get('message', r.text[:200])}")
            except Exception:
                pass
        elif r.status_code == 403:
            logger.info("   ✗  Error 403. Permisos insuficientes.")
        else:
            logger.info(f"   ⚠  {r.status_code}: {r.text[:200]}")
    except Exception as e:
        logger.info(f"   ✗  Excepción: {e}")

    # 5. Info del servidor
    logger.info("\n5. Información del servidor:")
    try:
        r = requests.get(WP_URL, headers=headers, timeout=5)
        for h in ["Server", "X-Powered-By", "X-RateLimit-Limit",
                   "X-RateLimit-Remaining", "CF-Ray"]:
            if h in r.headers:
                logger.info(f"   {h}: {r.headers[h]}")
    except Exception:
        pass

    logger.info("\n" + "=" * 70)
    logger.info("Diagnostico completado")
    logger.info("=" * 70)


# ==================== VERIFICAR ====================

def cmd_verify():
    logger.info("=" * 70)
    logger.info("VERIFICACION DE ESTADO DEL SERVIDOR")
    logger.info("=" * 70)

    headers = get_headers()

    # Posts por estado
    logger.info("\nPosts por estado:")
    try:
        r = requests.get(WP_URL, headers=headers,
                         params={"per_page": 1, "status": "any"}, timeout=10)
        if r.status_code == 200:
            logger.info(f"   Total (todos los estados): {r.headers.get('X-WP-Total', 'N/A')}")

        for estado in ["publish", "draft", "future", "pending", "private"]:
            r = requests.get(WP_URL, headers=headers,
                             params={"per_page": 1, "status": estado}, timeout=5)
            if r.status_code == 200:
                count = r.headers.get("X-WP-Total", "0")
                logger.info(f"   {estado.capitalize():10}: {count}")
    except Exception as e:
        logger.error(f"   Error: {e}")

    # Capacidad de escritura
    logger.info("\nCapacidad de escritura:")
    try:
        test = {
            "title": "TEST CAPACIDAD - ELIMINAR",
            "content": "Post de prueba.",
            "status": "draft"
        }
        r = requests.post(WP_URL, headers=headers, json=test, timeout=20)
        logger.info(f"   Status: {r.status_code}")
        if r.status_code == 201:
            post_id = r.json()["id"]
            logger.info("   OK  Puedes crear posts")
            del_r = requests.delete(f"{WP_URL}/{post_id}", headers=headers,
                                    params={"force": True}, timeout=10)
            if del_r.status_code == 200:
                logger.info("   OK  Post de prueba eliminado")
        elif r.status_code == 500:
            logger.info("   ✗  No puedes crear posts (Error 500)")
            logger.info("      Ejecuta: python3 wp_publisher.py diagnose")
        else:
            logger.info(f"   ⚠  {r.status_code}: {r.text[:150]}")
    except Exception as e:
        logger.error(f"   Excepción: {e}")

    logger.info("\n" + "=" * 70)


# ==================== PARSEO DE ARGUMENTOS ====================

def parse_args():
    args = sys.argv[1:]
    cmd = "publish"
    dir_override = None
    limit = None
    delay = DEFAULT_DELAY

    if args and not args[0].startswith("--"):
        cmd = args[0].lower()
        args = args[1:]

    i = 0
    while i < len(args):
        if args[i] == "--dir" and i + 1 < len(args):
            dir_override = args[i + 1]
            i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                logger.error(f"--limit debe ser un número entero, no '{args[i+1]}'")
                sys.exit(1)
            i += 2
        elif args[i] == "--delay" and i + 1 < len(args):
            try:
                delay = int(args[i + 1])
            except ValueError:
                logger.error(f"--delay debe ser un número entero, no '{args[i+1]}'")
                sys.exit(1)
            i += 2
        else:
            logger.warning(f"Opción desconocida: {args[i]}")
            i += 1

    return cmd, dir_override, limit, delay


# ==================== MAIN ====================

HELP_TEXT = """
WordPress Publisher - Script unificado para datablogcafe.com

USO:
  python3 wp_publisher.py [COMANDO] [OPCIONES]

COMANDOS:
  publish       Publicar artículos nuevos (por defecto)
  draft         Publicar artículos como borradores
  wait          Esperar en bucle a que aparezcan archivos (GPU generando)
  update-dates  Solo actualizar fechas de posts existentes
  diagnose      Diagnóstico completo: .env, conexión, autenticación
  verify        Verificar estado y capacidad del servidor
  reset         Limpiar checkpoint (empezar desde cero)
  help          Mostrar esta ayuda

OPCIONES:
  --dir PATH    Directorio de artículos (sobreescribe ARTICULOS_DIR del .env)
  --limit N     Procesar máximo N artículos
  --delay N     Segundos entre requests (por defecto: 8)

EJEMPLOS:
  # Publicar todos los artículos pendientes
  python3 wp_publisher.py publish

  # Esperar a que la GPU genere archivos y publicarlos automáticamente
  python3 wp_publisher.py wait

  # Publicar solo los primeros 50 como borradores
  python3 wp_publisher.py draft --limit 50

  # Publicar desde un directorio concreto con delay menor
  python3 wp_publisher.py publish --dir /ruta/a/articulos --delay 5

  # Solo actualizar fechas de los primeros 100
  python3 wp_publisher.py update-dates --limit 100

  # Verificar conexión y estado del servidor
  python3 wp_publisher.py diagnose

  # Ver cuántos posts hay por estado
  python3 wp_publisher.py verify

  # Empezar desde cero (ignorar checkpoint)
  python3 wp_publisher.py reset && python3 wp_publisher.py publish

VARIABLES DE ENTORNO (.env):
  WP_URL         https://datablogcafe.com/wp-json/wp/v2/posts
  WP_TAGS_URL    https://datablogcafe.com/wp-json/wp/v2/tags
  WP_USER        tu_usuario
  WP_PASSWORD    xxxx xxxx xxxx xxxx
  ARTICULOS_DIR  /ruta/a/tus/articulos
"""

if __name__ == "__main__":
    cmd, dir_override, limit, delay = parse_args()

    if cmd in ("help", "--help", "-h"):
        print(HELP_TEXT)
        sys.exit(0)

    if cmd == "reset":
        limpiar_checkpoint()
        sys.exit(0)

    if cmd == "diagnose":
        if not all([WP_URL, WP_USER, WP_PASSWORD]):
            logger.error("Faltan variables en .env (WP_URL, WP_USER, WP_PASSWORD)")
            sys.exit(1)
        cmd_diagnose()
        sys.exit(0)

    if cmd == "verify":
        if not all([WP_URL, WP_USER, WP_PASSWORD]):
            logger.error("Faltan variables en .env (WP_URL, WP_USER, WP_PASSWORD)")
            sys.exit(1)
        cmd_verify()
        sys.exit(0)

    # Para publish / draft / update-dates se necesita ARTICULOS_DIR
    articulos_dir = dir_override or ARTICULOS_DIR

    if not all([WP_URL, WP_TAGS_URL, WP_USER, WP_PASSWORD]):
        logger.error("Faltan variables en .env. Ejecuta primero: python3 wp_publisher.py diagnose")
        sys.exit(1)

    if not articulos_dir:
        logger.error("ARTICULOS_DIR no configurado. Usa --dir PATH o configúralo en .env")
        sys.exit(1)

    if not os.path.exists(articulos_dir):
        logger.error(f"Directorio no existe: {articulos_dir}")
        sys.exit(1)

    if cmd == "wait":
        cmd_wait(articulos_dir, limit, delay)
    elif cmd == "update-dates":
        cmd_update_dates(articulos_dir, limit, delay)
    elif cmd in ("publish", "draft"):
        procesar_articulos(cmd, articulos_dir, limit, delay)
    else:
        logger.error(f"Comando desconocido: '{cmd}'. Usa: python3 wp_publisher.py help")
        sys.exit(1)
