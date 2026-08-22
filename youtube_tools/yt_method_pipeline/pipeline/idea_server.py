"""Servidor HTTP local para el botón 'Generar idea' del dashboard.

Un HTML abierto por file:// no puede llamar a un LLM sin exponer credenciales
en el código fuente de la página (o, en el caso de Ollama, sin que el propio
navegador intente hablar directamente con localhost:11434, que tampoco es
ideal). Este servidor corre en localhost y expone
GET /generate?axisA=X&valA=Y&axisB=Z&valB=W — el dashboard le hace fetch()
desde JS (eso sí lo permite un navegador desde una página file://, a
diferencia de leer otro fichero local). Funciona con cualquier par de ejes
de la rejilla de huecos (mecanismo×canal, canal×audiencia,
categoría×inversión), no solo mecanismo×canal.

Usa el mismo proveedor que el resto del pipeline (config.LLM_PROVIDER: Ollama
por defecto, o Claude API si lo cambias en .env).

Cachea cada idea en disco (data/ideas/<coordenada>.json) para no volver a
llamar al LLM si ya se generó antes.
"""
import json
import logging
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import config
from .llm_client import call_tool
from .utils import slugify

logger = logging.getLogger(__name__)

PORT = 8765
TOOL_NAME = "generate_idea"
IDEAS_DIR = config.DATA_DIR / "ideas"
_SCHEMA_PATH = config.SCHEMAS_DIR / "idea_generation.json"
_PROMPT_PATH = config.PROMPTS_DIR / "generate_idea.md"
_CONTEXT_MAX_VIDEOS = 8

AXIS_LABELS = {
    "mecanismo_norm": "Mecanismo de valor",
    "canal_norm": "Canal de apalancamiento",
    "audiencia_norm": "Audiencia",
    "categoria_norm": "Categoría",
    "bucket_inversion": "Inversión inicial",
}
# Facetas "de negocio" que se ofrecen como señal adicional de contexto cuando
# no forman parte de la coordenada elegida (p.ej. si el eje es categoría x
# inversión, saber el mecanismo/canal/audiencia típico de ese grupo ayuda).
# Orden de preferencia: audiencia primero, para que el caso clásico
# mecanismo×canal siga teniendo su "tercera faceta" (audiencia) como en el
# diseño original de tres facetas.
_CONTEXT_FACETS = ["audiencia_norm", "mecanismo_norm", "canal_norm", "categoria_norm"]


def _load_methods_norm() -> list[dict]:
    path = config.DATA_DIR / "methods_norm.json"
    if not path.exists():
        raise RuntimeError("No existe data/methods_norm.json. Ejecuta 'normalize' primero.")
    return json.loads(path.read_text(encoding="utf-8"))


def _pool(videos: list[dict], axis_a: str, val_a: str, axis_b: str, val_b: str) -> list[dict]:
    seen_ids = set()
    pool = []
    for v in videos:
        if v.get(axis_a) == val_a or v.get(axis_b) == val_b:
            if v["id"] not in seen_ids:
                seen_ids.add(v["id"])
                pool.append(v)
    return pool


def _extra_signal(pool: list[dict], axis_a: str, axis_b: str) -> dict:
    """Faceta de negocio más frecuente en el pool que no sea ya uno de los dos
    ejes de la coordenada, con su propio n, para dar contexto extra sin
    duplicar lo ya dicho y sin fingir una confianza que no tiene."""
    for facet in _CONTEXT_FACETS:
        if facet in (axis_a, axis_b):
            continue
        counts = Counter(v[facet] for v in pool if v.get(facet))
        if counts:
            value, n = counts.most_common(1)[0]
            return {"facet": facet, "label": AXIS_LABELS[facet], "value": value, "n": n}
    return {"facet": None, "label": "ninguna", "value": "n/d", "n": 0}


def _n_for(pool: list[dict], axis: str, val: str) -> int:
    return sum(1 for v in pool if v.get(axis) == val)


def _score(pool: list[dict]) -> float:
    if not pool:
        return 0.0
    return sum(v.get("potencial", 0) for v in pool) / len(pool)


def _build_context(pool: list[dict]) -> str:
    blocks = []
    for v in pool[:_CONTEXT_MAX_VIDEOS]:
        m = v["method"]
        blocks.append(
            f"- {v['title']}\n"
            f"  resumen: {m.get('resumen_frase') or m.get('resumen') or ''}\n"
            f"  pasos: {'; '.join((m.get('pasos') or [])[:5])}\n"
            f"  herramientas: {', '.join(v.get('herramientas_norm') or [])}\n"
            f"  riesgos declarados: {'; '.join(m.get('riesgos_declarados') or [])}"
        )
    return "\n".join(blocks)


def _cache_path(axis_a: str, val_a: str, axis_b: str, val_b: str) -> Path:
    return IDEAS_DIR / f"{axis_a}={slugify(val_a)}__{axis_b}={slugify(val_b)}.json"


def generate_idea(axis_a: str, val_a: str, axis_b: str, val_b: str) -> dict:
    if axis_a not in AXIS_LABELS or axis_b not in AXIS_LABELS:
        raise ValueError(f"eje desconocido: {axis_a!r} / {axis_b!r}")

    cache_path = _cache_path(axis_a, val_a, axis_b, val_b)
    if cache_path.exists():
        logger.info("idea servida de caché: %s=%s x %s=%s", axis_a, val_a, axis_b, val_b)
        return json.loads(cache_path.read_text(encoding="utf-8"))

    videos = _load_methods_norm()
    pool = _pool(videos, axis_a, val_a, axis_b, val_b)
    if not pool:
        raise ValueError(f"Ningún vídeo sostiene {axis_a}={val_a!r} ni {axis_b}={val_b!r}")

    score = _score(pool)
    contexto = _build_context(pool)
    n_a = _n_for(pool, axis_a, val_a)
    n_b = _n_for(pool, axis_b, val_b)
    extra = _extra_signal(pool, axis_a, axis_b)

    template = _PROMPT_PATH.read_text(encoding="utf-8")
    prompt = template.format(
        label_a=AXIS_LABELS[axis_a], val_a=val_a, n_a=n_a,
        label_b=AXIS_LABELS[axis_b], val_b=val_b, n_b=n_b,
        extra_label=extra["label"], extra_val=extra["value"], extra_n=extra["n"],
        score=round(score), contexto=contexto,
    )

    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    tool = {
        "name": TOOL_NAME,
        "description": "Propone una idea de negocio concreta combinando dos facetas normalizadas.",
        "input_schema": {k: v for k, v in schema.items() if k not in ("$schema", "title")},
    }

    # think=True: es una llamada puntual (una por idea pedida, no una por
    # vídeo), compensa razonar más para una propuesta mejor argumentada.
    idea = call_tool(prompt, tool, max_tokens=2048, think=True)
    idea["_coordenada"] = {axis_a: val_a, axis_b: val_b}
    idea["_score_estimado"] = round(score)

    IDEAS_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(idea, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("idea generada y cacheada: %s=%s x %s=%s -> %s", axis_a, val_a, axis_b, val_b, cache_path)
    return idea


class _Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 (nombre fijado por BaseHTTPRequestHandler)
        parsed = urlparse(self.path)
        if parsed.path != "/generate":
            self._send_json(404, {"error": "ruta no encontrada, usa /generate"})
            return
        qs = parse_qs(parsed.query)
        axis_a = (qs.get("axisA") or [None])[0]
        val_a = (qs.get("valA") or [None])[0]
        axis_b = (qs.get("axisB") or [None])[0]
        val_b = (qs.get("valB") or [None])[0]
        if not all([axis_a, val_a, axis_b, val_b]):
            self._send_json(400, {"error": "faltan parámetros 'axisA', 'valA', 'axisB' y/o 'valB'"})
            return
        try:
            idea = generate_idea(axis_a, val_a, axis_b, val_b)
            self._send_json(200, idea)
        except Exception as exc:
            logger.exception("fallo generando idea")
            self._send_json(500, {"error": str(exc)})

    def log_message(self, fmt, *args):  # silencia el log por defecto de http.server
        logger.info("%s - %s", self.address_string(), fmt % args)


def run() -> None:
    server = ThreadingHTTPServer(("localhost", PORT), _Handler)
    logger.info(
        "Servidor de ideas escuchando en http://localhost:%d (proveedor: %s) — Ctrl+C para parar",
        PORT, config.LLM_PROVIDER,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Servidor de ideas detenido")
