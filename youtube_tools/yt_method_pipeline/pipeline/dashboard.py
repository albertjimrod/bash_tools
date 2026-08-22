"""Genera un dashboard HTML autónomo: vista legible por vídeo (Expediente),
rejilla de huecos y similitud ponderada sobre facetas normalizadas, y
combinador de primitivos. Lee data/methods_norm.json (paso 'normalize').
"""
import json
import logging
from pathlib import Path

import config

logger = logging.getLogger(__name__)

_TEMPLATE_PATH = config.BASE_DIR / "pipeline" / "dashboard_template.html"
DASHBOARD_HTML = config.DATA_DIR / "dashboard.html"
METHODS_NORM = config.DATA_DIR / "methods_norm.json"
NORM_CONFIG = config.BASE_DIR / "configs" / "normalization.json"
IDEAS_DIR = config.DATA_DIR / "ideas"


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def _channel_label(videos: list[dict]) -> str:
    """A partir de los canal_nombre reales de los vídeos (no de
    data/channel.json, que se sobrescribe en cada 'fetch' y no representa
    ya el corpus completo si mezclas fuentes)."""
    nombres = sorted({v.get("canal_nombre") for v in videos if v.get("canal_nombre")})
    if not nombres:
        return "canal"
    if len(nombres) == 1:
        return nombres[0]
    return f"{len(nombres)} fuentes ({', '.join(nombres)})"


def _load_embedding(video_id: str) -> list[float] | None:
    embedding_path = config.TRANSCRIPTS_DIR / video_id / "embedding.json"
    if not embedding_path.exists():
        return None
    return json.loads(embedding_path.read_text(encoding="utf-8"))["vector"]


def _load_cached_ideas() -> dict:
    """Lee todas las ideas ya generadas y cacheadas (data/ideas/*.json) y las
    indexa por coordenada, en ambos órdenes de eje, para que el dashboard
    pueda saber en el momento de pintar la rejilla si una celda ya tiene una
    idea (viable, descartada o de baja confianza) sin llamar al servidor."""
    cached: dict[str, dict] = {}
    if not IDEAS_DIR.exists():
        return cached
    for path in IDEAS_DIR.glob("*.json"):
        try:
            idea = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        coord = idea.get("_coordenada")
        if not coord or len(coord) != 2:
            continue
        (axis_a, val_a), (axis_b, val_b) = list(coord.items())
        cached[f"{axis_a}={val_a}|{axis_b}={val_b}"] = idea
        cached[f"{axis_b}={val_b}|{axis_a}={val_a}"] = idea
    return cached


def run() -> Path:
    if not METHODS_NORM.exists():
        raise RuntimeError(
            "No existe data/methods_norm.json. Ejecuta 'normalize' primero "
            "(revisa después data/normalization_report.html antes de confiar en la rejilla de huecos)."
        )

    videos = json.loads(METHODS_NORM.read_text(encoding="utf-8"))
    videos = [v for v in videos if _load_embedding(v["id"]) is not None]
    if not videos:
        raise RuntimeError("Ningún vídeo normalizado tiene embedding.json. Ejecuta 'index' primero.")

    vectors = [_load_embedding(v["id"]) for v in videos]
    n = len(videos)
    similarity = [
        [round(_cosine(vectors[i], vectors[j]), 4) for j in range(n)]
        for i in range(n)
    ]

    coverage_pct = round(100 * sum(1 for v in videos if v.get("resuelto")) / n) if n else 0

    norm_cfg = json.loads(NORM_CONFIG.read_text(encoding="utf-8")) if NORM_CONFIG.exists() else {}
    incompatibilidades = (norm_cfg.get("incompatibilidades_mecanismo_canal") or {}).get("pares", [])

    fuentes = sorted({v.get("canal_nombre") for v in videos if v.get("canal_nombre")})

    payload = {
        "channel": _channel_label(videos),
        "videos": videos,
        "similarity": similarity,
        "coverage_pct": coverage_pct,
        "incompatibilidades_mecanismo_canal": incompatibilidades,
        "cached_ideas": _load_cached_ideas(),
        "fuentes": fuentes,
    }

    template = _TEMPLATE_PATH.read_text(encoding="utf-8")
    html = template.replace("__DATA_JSON__", json.dumps(payload, ensure_ascii=False))

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    DASHBOARD_HTML.write_text(html, encoding="utf-8")
    logger.info("Dashboard generado: %s", DASHBOARD_HTML)
    return DASHBOARD_HTML
