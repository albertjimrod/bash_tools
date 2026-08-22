#!/usr/bin/env python3
"""Genera un BORRADOR de post de LinkedIn (texto + imagen) a partir de una
pestaña del dashboard. NO publica nada en LinkedIn ni usa su API/scraping:
deja los ficheros listos en data/linkedin_posts/<fecha>-<pestana>/ para que
tú los revises y subas a mano.

Todo corre en local salvo la llamada a la API de Anthropic para redactar el
texto del post. La clave se lee siempre de la variable de entorno
ANTHROPIC_API_KEY (vía .env, cargado por config.py) — nunca hardcodeada ni
escrita en ningún fichero de salida.

Las cifras que cita el post se calculan aquí, en Python, directamente sobre
data/methods_norm.json (+ embeddings para la pestaña de similitud) — nunca
las inventa el LLM.
"""
import argparse
import datetime
import json
import logging
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import httpx

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("generate_post")

# Modelo de la familia Claude usado solo por este script (independiente del
# LLM_PROVIDER del resto del pipeline, que por defecto es Ollama).
CLAUDE_MODEL = "claude-sonnet-5"

PROMPT_PATH = config.PROMPTS_DIR / "linkedin_post.md"
METHODS_NORM = config.DATA_DIR / "methods_norm.json"
NORM_CONFIG = config.BASE_DIR / "configs" / "normalization.json"
DASHBOARD_HTML = config.DATA_DIR / "dashboard.html"

TABS = ["expediente", "huecos", "similitud", "combinador", "constructor", "panorama"]
TAB_TITULOS = {
    "expediente": "Expediente de métodos",
    "huecos": "Rejilla de huecos",
    "similitud": "Similitud entre métodos",
    "combinador": "Combinador de primitivos",
    "constructor": "Constructor de proyecto",
    "panorama": "Panorama del corpus",
}
IDIOMA_NOMBRE = {"es": "español", "en": "inglés"}
ENFOQUE_INSTRUCCIONES = {
    "metodologia": (
        "ENFOQUE: metodología, ANONIMIZADO. No menciones en ningún momento el nombre del canal "
        "de YouTube analizado ni de ningún creador de contenido, ni directa ni indirectamente "
        "(no cites títulos de vídeos con nombres propios, no digas 'el canal que analicé' de forma "
        "identificable). Habla del MÉTODO de análisis (el pipeline, el enfoque de extracción y "
        "normalización) y usa las cifras como ejemplo agregado de un corpus de vídeos sobre "
        "generación de ingresos, sin identificar la fuente."
    ),
    "nombres_reales": (
        "ENFOQUE: nombres reales. Puedes mencionar que el análisis es sobre un canal de YouTube "
        "concreto si el hallazgo lo justifica, con naturalidad, sin que sea el centro del post "
        "(el centro sigue siendo el método de análisis, no el canal)."
    ),
}

# Misma paleta que pipeline/dashboard_template.html (tema claro), para que la
# tarjeta encaje visualmente con el dashboard sin duplicar el CSS entero.
PALETTE = {
    "bg": "#F2EFE9", "surface": "#FFFFFF", "border": "#E1DCD0",
    "ink": "#23201B", "ink_muted": "#756E5F", "accent": "#2B6E68",
}


# --- Carga de datos y helpers de agregación (réplica en Python de la lógica
# que ya usa el dashboard en JS, sobre la misma fuente de verdad) ---

def load_data():
    if not METHODS_NORM.exists():
        raise SystemExit("No existe data/methods_norm.json. Ejecuta 'normalize' primero.")
    videos = json.loads(METHODS_NORM.read_text(encoding="utf-8"))
    norm_cfg = json.loads(NORM_CONFIG.read_text(encoding="utf-8")) if NORM_CONFIG.exists() else {}
    pares = (norm_cfg.get("incompatibilidades_mecanismo_canal") or {}).get("pares", [])
    return videos, pares


def mean_potencial(vids):
    if not vids:
        return None
    return sum(v.get("potencial", 0) for v in vids) / len(vids)


def axis_values(videos, key):
    return sorted({v[key] for v in videos if v.get(key)})


def pool_for_facet(videos, key, value):
    return [v for v in videos if v.get(key) == value]


def is_incompatible(pares, mecanismo, canal):
    return any(m == mecanismo and c == canal for m, c in pares)


def potential_score(method):
    """Réplica exacta de potentialScore() en dashboard_template.html."""
    eco = method.get("economia") or {}
    escalabilidad = {"alta": 1, "media": 0.6, "baja": 0.25}.get(eco.get("escalabilidad"), 0.4)
    accesibilidad = {"0": 1, "<100": 0.85, "100-1000": 0.6, "1000-10000": 0.35, ">10000": 0.15}.get(
        eco.get("inversion_inicial"), 0.5)
    velocidad = {"dias": 1, "semanas": 0.8, "1-3_meses": 0.55, ">3_meses": 0.3}.get(
        eco.get("tiempo_primer_ingreso"), 0.5)
    evidencia = {"pruebas_verificables": 1, "capturas_o_documentos": 0.6, "solo_afirmacion": 0.25}.get(
        method.get("evidencia"), 0.4)
    n_riesgos = len(method.get("riesgos_declarados") or []) + len(method.get("riesgos_omitidos") or [])
    sat_penalty = {"alta": 0.15, "media": 0.07, "baja": 0.0}.get(method.get("saturacion_competencia"), 0.05)
    sesgo_penalty = 0.15 if (method.get("sesgo_supervivencia") or {}).get("presente") else 0.0
    vende = method.get("vende_algo") or {}
    vende_penalty = 0.08 if vende.get("tipo") and vende.get("tipo") != "ninguno" else 0.0
    riesgo = max(0.0, 1 - 0.06 * n_riesgos - sat_penalty - sesgo_penalty - vende_penalty)
    score = 0.30 * escalabilidad + 0.20 * accesibilidad + 0.15 * velocidad + 0.15 * evidencia + 0.20 * riesgo
    return round(score * 100)


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def load_embeddings(videos):
    out = {}
    for v in videos:
        path = config.TRANSCRIPTS_DIR / v["id"] / "embedding.json"
        if not path.exists():
            continue
        try:
            out[v["id"]] = json.loads(path.read_text(encoding="utf-8"))["vector"]
        except Exception:
            continue
    return out


# --- Un "hallazgo" por pestaña, calculado sobre datos reales ---

def hallazgo_expediente(videos, pares):
    n = len(videos)
    evid = Counter(v["method"].get("evidencia") for v in videos if v["method"].get("evidencia"))
    return {
        "n_total": n,
        "solo_afirmacion": evid.get("solo_afirmacion", 0),
        "pruebas_verificables": evid.get("pruebas_verificables", 0),
        "capturas_o_documentos": evid.get("capturas_o_documentos", 0),
    }


def hallazgo_huecos(videos, pares):
    # 'otros' es el cajón de sastre de la normalización (config.categoria/etc.):
    # técnicamente real, pero un hueco 'otros × canal' no dice nada útil como
    # ejemplo público — se excluye igual que ya se excluye de comparaciones
    # específicas en el resto del proyecto.
    mecs = [m for m in axis_values(videos, "mecanismo_norm") if m != "otros"]
    canales = [c for c in axis_values(videos, "canal_norm") if c != "otros"]
    filled = {(v["mecanismo_norm"], v["canal_norm"]) for v in videos if v.get("mecanismo_norm") and v.get("canal_norm")}

    def candidatos(min_n):
        out = []
        for m in mecs:
            for c in canales:
                if (m, c) in filled or is_incompatible(pares, m, c):
                    continue
                pool_m, pool_c = pool_for_facet(videos, "mecanismo_norm", m), pool_for_facet(videos, "canal_norm", c)
                n_m, n_c = len(pool_m), len(pool_c)
                if n_m < min_n or n_c < min_n:
                    continue
                score_m, score_c = mean_potencial(pool_m), mean_potencial(pool_c)
                out.append({
                    "mecanismo": m, "canal": c, "n_mecanismo": n_m, "n_canal": n_c,
                    "score_mecanismo": round(score_m), "score_canal": round(score_c),
                    "score": round((score_m + score_c) / 2), "fragil": False,
                })
        out.sort(key=lambda x: -x["score"])
        return out

    solidos = candidatos(2)
    if solidos:
        return solidos[0]
    fragiles = candidatos(1)
    if not fragiles:
        return None
    best = fragiles[0]
    best["fragil"] = True
    return best


def hallazgo_similitud(videos, pares, umbral_cluster=0.85):
    embeds = load_embeddings(videos)
    by_id = {v["id"]: v for v in videos}
    ids = list(embeds.keys())
    best = None
    cluster_n = 0
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            sim = cosine(embeds[ids[i]], embeds[ids[j]])
            if sim >= umbral_cluster:
                cluster_n += 1
            if best is None or sim > best["similitud"]:
                best = {"id_a": ids[i], "id_b": ids[j], "similitud": sim}
    if best is None:
        return None
    va, vb = by_id[best["id_a"]], by_id[best["id_b"]]
    return {
        "titulo_a": va["title"], "titulo_b": vb["title"],
        "similitud": round(best["similitud"], 3),
        "pares_muy_similares": cluster_n, "umbral": umbral_cluster,
        "n_total": len(ids),
    }


def collect_primitivos(videos):
    dims = {"mecanismo_valor": [], "canal_apalancamiento": [], "audiencia": []}
    for v in videos:
        prim = v["method"].get("primitivos") or {}
        for key in dims:
            val = prim.get(key)
            if val:
                dims[key].append({"value": val, "video": v})
    return dims


def exists_combo(videos, mec, can, aud):
    for v in videos:
        p = v["method"].get("primitivos") or {}
        if ((p.get("mecanismo_valor") or "").lower() == mec.lower()
                and (p.get("canal_apalancamiento") or "").lower() == can.lower()
                and (p.get("audiencia") or "").lower() == aud.lower()):
            return v
    return None


def hallazgo_combinador(videos, pares, top_k=6):
    dims = collect_primitivos(videos)
    if not (dims["mecanismo_valor"] and dims["canal_apalancamiento"] and dims["audiencia"]):
        return None

    def top(entries):
        # colapsa por valor (varios vídeos pueden compartir el mismo primitivo
        # en texto libre) quedándose con el de mayor potencial de cada uno
        by_value = {}
        for e in entries:
            score = potential_score(e["video"]["method"])
            if e["value"] not in by_value or score > by_value[e["value"]][0]:
                by_value[e["value"]] = (score, e)
        ranked = sorted(by_value.values(), key=lambda t: -t[0])
        return [e for _, e in ranked[:top_k]]

    top_mec, top_can, top_aud = top(dims["mecanismo_valor"]), top(dims["canal_apalancamiento"]), top(dims["audiencia"])

    def es_incompatible(mec, can):
        m_norm, c_norm = mec["video"].get("mecanismo_norm"), can["video"].get("canal_norm")
        return bool(m_norm and c_norm and is_incompatible(pares, m_norm, c_norm))

    # Primero se busca una terna NUEVA (no existente ya en el corpus) entre
    # las mejores candidatas por dimensión — más interesante como ejemplo que
    # una que ya exista. Si ninguna combinación de las top-k es nueva, se cae
    # a la de mayor potencial media aunque ya exista (y se marca como tal).
    mejor_nueva, mejor_cualquiera = None, None
    for mec in top_mec:
        for can in top_can:
            if es_incompatible(mec, can):
                continue
            for aud in top_aud:
                score = (potential_score(mec["video"]["method"]) + potential_score(can["video"]["method"])
                         + potential_score(aud["video"]["method"])) / 3
                existing = exists_combo(videos, mec["value"], can["value"], aud["value"])
                candidato = (score, mec, can, aud, existing)
                if mejor_cualquiera is None or score > mejor_cualquiera[0]:
                    mejor_cualquiera = candidato
                if existing is None and (mejor_nueva is None or score > mejor_nueva[0]):
                    mejor_nueva = candidato

    elegido = mejor_nueva or mejor_cualquiera
    if elegido is None:
        return None
    score, mec, can, aud, existing = elegido
    return {
        "mecanismo": mec["value"], "canal": can["value"], "audiencia": aud["value"],
        "video_mecanismo": mec["video"]["title"], "video_canal": can["video"]["title"],
        "video_audiencia": aud["video"]["title"],
        "ya_existe": existing["title"] if existing else None,
        "potencial_medio": round(score),
    }


def hallazgo_constructor(videos, pares):
    combos = Counter()
    for v in videos:
        m, c = v.get("mecanismo_norm"), v.get("canal_norm")
        if m and c:
            combos[(m, c)] += 1
    if not combos:
        return None
    (m, c), n = combos.most_common(1)[0]
    pool = [v for v in videos if v.get("mecanismo_norm") == m and v.get("canal_norm") == c]
    audiencias = Counter(v.get("audiencia_norm") for v in pool if v.get("audiencia_norm"))
    aud = audiencias.most_common(1)[0][0] if audiencias else None
    return {"mecanismo": m, "canal": c, "audiencia": aud, "n": n, "score": round(mean_potencial(pool))}


def hallazgo_panorama(videos, pares):
    total = len(videos)
    if not total:
        return None
    mejor = None
    for facet, label in (("mecanismo_norm", "mecanismo"), ("canal_norm", "canal"), ("audiencia_norm", "audiencia")):
        for val in axis_values(videos, facet):
            pool = pool_for_facet(videos, facet, val)
            n = len(pool)
            if n < 2:
                continue
            score = mean_potencial(pool)
            cuota = n / total
            metrica = score * (1 - cuota)
            if mejor is None or metrica > mejor["metrica"]:
                mejor = {"faceta": label, "valor": val, "n": n, "score": round(score), "cuota": round(cuota, 3), "metrica": metrica}
    cat_counts = Counter(v["categoria_norm"] for v in videos if v.get("categoria_norm"))
    top_cat, top_n = cat_counts.most_common(1)[0] if cat_counts else (None, 0)
    return {
        "primitivo": mejor,
        "categoria_dominante": top_cat, "categoria_dominante_n": top_n,
        "categoria_dominante_pct": round(top_n / total, 3) if total else 0,
        "n_categorias_distintas": len(cat_counts), "n_total": total,
    }


HALLAZGO_FUNCS = {
    "expediente": hallazgo_expediente,
    "huecos": hallazgo_huecos,
    "similitud": hallazgo_similitud,
    "combinador": hallazgo_combinador,
    "constructor": hallazgo_constructor,
    "panorama": hallazgo_panorama,
}


def format_hallazgo(pestana, videos, data, enfoque, destacado):
    base = f"Idea a destacar (fijada por el usuario): {destacado}\n\n" if destacado else ""
    citar_titulos = enfoque == "nombres_reales"

    if data is None:
        fallback = hallazgo_expediente(videos, [])
        return base + (
            f"No se encontró un hallazgo automático con suficiente respaldo en la pestaña '{pestana}' "
            f"ahora mismo. Contexto general del corpus: {fallback['n_total']} vídeos analizados, "
            f"{fallback['pruebas_verificables']} con pruebas verificables, "
            f"{fallback['solo_afirmacion']} solo con afirmaciones sin pruebas."
        )

    if pestana == "expediente":
        return base + (
            f"{data['n_total']} vídeos analizados en el corpus.\n"
            f"Evidencia: {data['pruebas_verificables']} con pruebas verificables, "
            f"{data['capturas_o_documentos']} con capturas/documentos, "
            f"{data['solo_afirmacion']} solo con afirmaciones sin pruebas (de {data['n_total']} totales).\n"
            "Esto es exactamente por lo que hace falta normalizar antes de comparar métodos entre sí: "
            "mezclar 'solo afirmación' con 'pruebas verificables' como si pesaran igual sesga cualquier comparación."
        )

    if pestana == "huecos":
        aviso = ""
        if data["fragil"]:
            aviso = (" ⚠ Aviso: el respaldo de esta combinación es bajo (n=1 en alguna de las dos "
                     "facetas) — trátalo como señal débil, no como hallazgo sólido.")
        return base + (
            f"Hueco: la combinación mecanismo='{data['mecanismo']}' × canal='{data['canal']}' "
            f"no la cubre ningún vídeo del corpus todavía.\n"
            f"Por separado: '{data['mecanismo']}' tiene potencial medio {data['score_mecanismo']} "
            f"(n={data['n_mecanismo']} vídeos), '{data['canal']}' tiene potencial medio {data['score_canal']} "
            f"(n={data['n_canal']} vídeos).{aviso}\n"
            "El potencial es un ordenador relativo del propio corpus (0-100, comprimido), no una nota objetiva."
        )

    if pestana == "similitud":
        detalle_par = f"El par más parecido tiene una similitud de {data['similitud']} sobre 1"
        if citar_titulos:
            detalle_par += f" (\"{data['titulo_a']}\" y \"{data['titulo_b']}\")"
        detalle_par += "."
        return base + (
            f"De {data['n_total']} vídeos indexados, {data['pares_muy_similares']} pares superan una "
            f"similitud de {data['umbral']} sobre 1. {detalle_par}\n"
            "Esto ilustra que el corpus tiene menos métodos realmente distintos de los que aparenta el "
            "número de vídeos: varios títulos distintos explican, en el fondo, el mismo método."
        )

    if pestana == "combinador":
        existe = " (ya existe en el corpus, en un vídeo)" if data["ya_existe"] else " (combinación nueva, no existe todavía en el corpus)"
        return base + (
            f"Terna de ejemplo: mecanismo='{data['mecanismo']}' × canal='{data['canal']}' × "
            f"audiencia='{data['audiencia']}'{existe}.\n"
            f"Potencial operativo medio de los tres métodos de origen: {data['potencial_medio']}/100 "
            "(fórmula transparente y declarada: escalabilidad, accesibilidad, velocidad, evidencia y "
            "riesgo del propio vídeo, no un dato externo)."
        )

    if pestana == "constructor":
        return base + (
            f"Ejemplo de composición: fijar mecanismo='{data['mecanismo']}' y canal='{data['canal']}' deja "
            f"n={data['n']} vídeo(s) del corpus que sostienen exactamente esa combinación, con un potencial "
            f"medio de {data['score']}.\n"
            "Así funciona el constructor: fijas atributos uno a uno y ves en vivo cuántos vídeos reales "
            "respaldan cada elección, en vez de proponer una combinación a ciegas."
        )

    if pestana == "panorama":
        prim = data["primitivo"]
        prim_txt = (
            f"El primitivo con mejor combinación de potencial alto y cuota baja es "
            f"{prim['faceta']}='{prim['valor']}' (potencial medio {prim['score']}, presente en solo el "
            f"{round(prim['cuota'] * 100)}% del corpus, n={prim['n']})."
            if prim else "No hay un primitivo con n>=2 que destaque especialmente ahora mismo."
        )
        return base + (
            f"{prim_txt}\n"
            f"Además, el corpus se concentra: la categoría '{data['categoria_dominante']}' por sí sola es "
            f"el {round(data['categoria_dominante_pct'] * 100)}% de los vídeos "
            f"({data['categoria_dominante_n']} de {data['n_total']}), repartidos entre solo "
            f"{data['n_categorias_distintas']} categorías distintas en total."
        )

    return base + json.dumps(data, ensure_ascii=False)


def card_summary_and_stats(pestana, data):
    """Resumen corto y 2-4 cifras para la tarjeta — calculado en Python
    directamente del hallazgo, no por el LLM, para que sea trazable 1:1."""
    if data is None:
        return "Análisis de datos sobre métodos de generación de ingresos.", []

    if pestana == "expediente":
        return (
            f"{data['n_total']} vídeos analizados, comparando evidencia declarada frente a solo afirmaciones.",
            [
                {"valor": data["n_total"], "label": "vídeos analizados"},
                {"valor": data["pruebas_verificables"], "label": "con pruebas verificables"},
                {"valor": data["solo_afirmacion"], "label": "solo con afirmaciones"},
            ],
        )
    if pestana == "huecos":
        return (
            f"Hueco con respaldo: '{data['mecanismo']}' × '{data['canal']}', sin cubrir todavía.",
            [
                {"valor": data["score_mecanismo"], "label": f"potencial · {data['mecanismo']}"},
                {"valor": data["score_canal"], "label": f"potencial · {data['canal']}"},
                {"valor": f"{data['n_mecanismo']}/{data['n_canal']}", "label": "n de respaldo"},
            ],
        )
    if pestana == "similitud":
        return (
            f"{data['pares_muy_similares']} pares de vídeos con similitud ≥{data['umbral']} — menos métodos distintos de lo que parece.",
            [
                {"valor": data["n_total"], "label": "vídeos indexados"},
                {"valor": data["pares_muy_similares"], "label": f"pares ≥{data['umbral']} similitud"},
                {"valor": f"{round(data['similitud'] * 100)}%", "label": "similitud del par más parecido"},
            ],
        )
    if pestana == "combinador":
        return (
            f"Terna de ejemplo: '{data['mecanismo']}' × '{data['canal']}' × '{data['audiencia']}'.",
            [
                {"valor": data["potencial_medio"], "label": "potencial medio de los 3 métodos"},
                {"valor": "sí" if data["ya_existe"] else "no", "label": "¿ya existe en el corpus?"},
            ],
        )
    if pestana == "constructor":
        return (
            f"Fijar '{data['mecanismo']}' × '{data['canal']}' deja n={data['n']} vídeo(s) de respaldo real.",
            [
                {"valor": data["n"], "label": "vídeos de respaldo"},
                {"valor": data["score"], "label": "potencial medio"},
            ],
        )
    if pestana == "panorama":
        prim = data["primitivo"]
        resumen = (
            f"'{prim['valor']}' combina potencial alto con baja cuota ({round(prim['cuota'] * 100)}%) — hueco bueno."
            if prim else f"El corpus se concentra en la categoría '{data['categoria_dominante']}'."
        )
        cifras = [
            {"valor": data["n_categorias_distintas"], "label": "categorías distintas"},
            {"valor": f"{round(data['categoria_dominante_pct'] * 100)}%", "label": f"en '{data['categoria_dominante']}'"},
        ]
        if prim:
            cifras.insert(0, {"valor": prim["score"], "label": f"potencial · {prim['valor']}"})
        return resumen, cifras

    return "Análisis de datos sobre métodos de generación de ingresos.", []


# --- Redacción del texto vía Claude API ---

def build_prompt(pestana, enfoque, idioma, hallazgo_texto):
    if not PROMPT_PATH.exists():
        raise SystemExit(f"Falta el fichero de prompt editable: {PROMPT_PATH}")
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.format(
        pestana=pestana,
        enfoque_instrucciones=ENFOQUE_INSTRUCCIONES[enfoque],
        idioma_nombre=IDIOMA_NOMBRE[idioma],
        hallazgo=hallazgo_texto,
    )


def call_claude_text(prompt: str) -> str:
    try:
        import anthropic
    except ImportError:
        raise SystemExit("Falta el paquete 'anthropic'. Instálalo con: .venv/bin/pip install anthropic")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit(
            "Falta ANTHROPIC_API_KEY en el entorno. Ponlo en .env (ANTHROPIC_API_KEY=sk-...) "
            "o expórtalo antes de ejecutar este script. Nunca se escribe en ningún fichero de salida."
        )
    client = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno, nunca hardcodeada
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIStatusError as exc:
        raise SystemExit(f"La API de Anthropic devolvió un error ({exc.status_code}): {exc.message}")
    return "".join(block.text for block in response.content if block.type == "text").strip()


def call_ollama_text(prompt: str, model: str) -> str:
    """Alternativa 100% local a call_claude_text(), mismo prompt y mismas
    cifras — solo cambia quién redacta. Útil cuando la API de Anthropic no
    está disponible (cuota, sin conexión...). Sin salida forzada por schema:
    aquí el post es texto libre, no un JSON estructurado."""
    try:
        resp = httpx.post(
            f"{config.OLLAMA_HOST}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "think": False,
                "options": {"temperature": 0.4, "num_ctx": 8192},
            },
            timeout=180,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise SystemExit(
            f"No se pudo hablar con Ollama en {config.OLLAMA_HOST} (modelo '{model}'): {exc}\n"
            "Comprueba que 'ollama serve' está corriendo y que el modelo está descargado (ollama pull ...)."
        )
    return resp.json()["message"]["content"].strip()


# --- Imágenes (Playwright) ---

def _require_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit(
            "Playwright no está instalado. Instálalo con:\n"
            "  .venv/bin/pip install playwright\n"
            "  .venv/bin/playwright install chromium"
        )
    return sync_playwright


def capture_tab(pestana: str, enfoque: str, out_path: Path, n_total: int) -> None:
    sync_playwright = _require_playwright()
    if not DASHBOARD_HTML.exists():
        raise SystemExit("No existe data/dashboard.html. Ejecuta 'dashboard' primero.")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(DASHBOARD_HTML.resolve().as_uri())
        page.wait_for_selector(".tab-btn")
        if enfoque == "metodologia":
            # Anonimizado hecho en el DOM ya cargado, vía Playwright — no
            # toca pipeline/dashboard_template.html para nada.
            page.evaluate(
                """(n) => {
                    const st = document.getElementById('subtitle');
                    if (st) st.textContent = n + ' vídeos analizados — extracción por 6 bloques de dimensiones + búsqueda semántica local.';
                    document.querySelectorAll('.source-filter').forEach(e => e.remove());
                    if (window.SOURCE_OPTIONS) {
                        document.querySelectorAll('.badge').forEach(b => {
                            if (window.SOURCE_OPTIONS.includes(b.textContent)) b.textContent = 'fuente ocultada';
                        });
                    }
                }""",
                n_total,
            )
        page.click(f'.tab-btn[data-tab="{pestana}"]')
        panel = page.locator(f'.tab-panel[data-tab="{pestana}"]')
        panel.wait_for(state="visible")
        panel.screenshot(path=str(out_path))
        browser.close()
    logger.info("captura guardada: %s", out_path)


def build_card_html(titulo: str, resumen: str, cifras: list) -> str:
    stats_html = "".join(
        f'<div class="stat"><div class="num">{c["valor"]}</div><div class="lbl">{c["label"]}</div></div>'
        for c in cifras
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; width: 1200px; height: 627px; display: flex; flex-direction: column; justify-content: center;
    padding: 70px 80px; font-family: Georgia, 'Times New Roman', serif;
    background: {PALETTE['bg']}; color: {PALETTE['ink']};
  }}
  .eyebrow {{ font-family: 'Courier New', monospace; font-size: 15px; letter-spacing: 0.08em; text-transform: uppercase; color: {PALETTE['accent']}; margin-bottom: 14px; }}
  h1 {{ font-size: 40px; line-height: 1.15; margin: 0 0 22px; font-weight: 700; max-width: 950px; }}
  p {{ font-family: Helvetica, Arial, sans-serif; font-size: 20px; line-height: 1.5; color: {PALETTE['ink_muted']}; max-width: 900px; margin: 0 0 28px; }}
  .stats {{ display: flex; gap: 28px; flex-wrap: wrap; }}
  .stat {{ background: {PALETTE['surface']}; border: 1px solid {PALETTE['border']}; border-radius: 12px; padding: 14px 22px; }}
  .num {{ font-family: 'Courier New', monospace; font-size: 28px; font-weight: 700; color: {PALETTE['accent']}; white-space: nowrap; }}
  .lbl {{ font-family: Helvetica, Arial, sans-serif; font-size: 12.5px; color: {PALETTE['ink_muted']}; margin-top: 2px; }}
</style></head>
<body>
  <div class="eyebrow">Análisis de datos · pipeline local</div>
  <h1>{titulo}</h1>
  <p>{resumen}</p>
  <div class="stats">{stats_html}</div>
</body></html>"""


def render_card(pestana: str, resumen: str, cifras: list, out_path: Path) -> None:
    sync_playwright = _require_playwright()
    html = build_card_html(TAB_TITULOS[pestana], resumen, cifras)
    tmp_html = out_path.with_suffix(".card.html")
    tmp_html.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 627})
        page.goto(tmp_html.resolve().as_uri())
        page.screenshot(path=str(out_path))
        browser.close()
    tmp_html.unlink(missing_ok=True)
    logger.info("tarjeta guardada: %s", out_path)


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="Genera un borrador de post de LinkedIn (texto + imagen) a partir de una "
        "pestaña del dashboard. NO publica nada — deja los ficheros listos para revisión manual."
    )
    parser.add_argument("--pestana", required=True, choices=TABS)
    parser.add_argument("--enfoque", default="metodologia", choices=["metodologia", "nombres_reales"])
    parser.add_argument("--imagen", default="ambas", choices=["captura", "tarjeta", "ambas"])
    parser.add_argument("--idioma", default="es", choices=["es", "en"])
    parser.add_argument("--destacado", default=None, help="Idea concreta a resaltar (opcional)")
    parser.add_argument("--salida", default=None, help="Carpeta de salida (por defecto data/linkedin_posts/<fecha>-<pestana>/)")
    parser.add_argument(
        "--provider", default="claude", choices=["claude", "ollama"],
        help="Quién redacta el texto: 'claude' (por defecto, vía API) u 'ollama' (100% local, "
        "útil si la API de Anthropic no está disponible)",
    )
    parser.add_argument(
        "--ollama-model", default=config.OLLAMA_MODEL,
        help=f"Modelo de Ollama a usar con --provider ollama (por defecto: {config.OLLAMA_MODEL})",
    )
    args = parser.parse_args()

    videos, pares = load_data()
    if not videos:
        raise SystemExit("data/methods_norm.json está vacío.")

    data = HALLAZGO_FUNCS[args.pestana](videos, pares)
    hallazgo_texto = format_hallazgo(args.pestana, videos, data, args.enfoque, args.destacado)

    prompt = build_prompt(args.pestana, args.enfoque, args.idioma, hallazgo_texto)
    if args.provider == "ollama":
        modelo_usado = args.ollama_model
        logger.info("llamando a Ollama (%s) para redactar el post...", modelo_usado)
        post_texto = call_ollama_text(prompt, modelo_usado)
    else:
        modelo_usado = CLAUDE_MODEL
        logger.info("llamando a Claude (%s) para redactar el post...", modelo_usado)
        post_texto = call_claude_text(prompt)

    fecha = datetime.date.today().isoformat()
    out_dir = Path(args.salida) if args.salida else config.DATA_DIR / "linkedin_posts" / f"{fecha}-{args.pestana}"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "post.txt").write_text(post_texto + "\n", encoding="utf-8")
    logger.info("post.txt guardado en %s", out_dir / "post.txt")

    imagenes = []
    if args.imagen in ("captura", "ambas"):
        capture_tab(args.pestana, args.enfoque, out_dir / "captura.png", len(videos))
        imagenes.append("captura.png")
    if args.imagen in ("tarjeta", "ambas"):
        resumen, cifras = card_summary_and_stats(args.pestana, data)
        render_card(args.pestana, resumen, cifras, out_dir / "tarjeta.png")
        imagenes.append("tarjeta.png")

    meta = {
        "pestana": args.pestana, "enfoque": args.enfoque, "imagen": args.imagen, "idioma": args.idioma,
        "destacado": args.destacado, "provider": args.provider, "modelo": modelo_usado,
        "generado_en": datetime.datetime.now().isoformat(),
        "cifras_citadas": data, "imagenes": imagenes,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nBorrador listo en: {out_dir}")
    print("Recuerda: esto NO publica nada — revisa post.txt y las imágenes, y sube a mano a LinkedIn cuando quieras.")


if __name__ == "__main__":
    main()
