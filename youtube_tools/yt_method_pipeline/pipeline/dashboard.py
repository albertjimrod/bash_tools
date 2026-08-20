"""Genera un dashboard HTML autónomo: vista legible por vídeo, matriz de
correlación (similitud coseno de embeddings) y combinador de primitivos.
"""
import json
import logging
from pathlib import Path

import config

logger = logging.getLogger(__name__)

_TEMPLATE_PATH = config.BASE_DIR / "pipeline" / "dashboard_template.html"
DASHBOARD_HTML = config.DATA_DIR / "dashboard.html"


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def _channel_label() -> str:
    if config.CHANNEL_FILE.exists():
        try:
            return json.loads(config.CHANNEL_FILE.read_text(encoding="utf-8")).get("channel", "canal")
        except Exception:
            pass
    return "canal"


def _load_videos() -> list[dict]:
    videos = []
    for video_dir in sorted(p for p in config.TRANSCRIPTS_DIR.iterdir() if p.is_dir()):
        method_path = video_dir / "method.json"
        meta_path = video_dir / "meta.json"
        embedding_path = video_dir / "embedding.json"
        if not (method_path.exists() and embedding_path.exists()):
            continue
        method = json.loads(method_path.read_text(encoding="utf-8"))
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        embedding = json.loads(embedding_path.read_text(encoding="utf-8"))
        videos.append(
            {
                "id": video_dir.name,
                "title": meta.get("title"),
                "url": meta.get("url"),
                "method": method,
                "vector": embedding["vector"],
            }
        )
    return videos


def run() -> Path:
    videos = _load_videos()
    if not videos:
        raise RuntimeError(
            "No hay vídeos indexados (falta method.json o embedding.json). "
            "Ejecuta 'extract' e 'index' primero."
        )

    n = len(videos)
    similarity = [
        [round(_cosine(videos[i]["vector"], videos[j]["vector"]), 4) for j in range(n)]
        for i in range(n)
    ]

    payload = {
        "channel": _channel_label(),
        "videos": [
            {"id": v["id"], "title": v["title"], "url": v["url"], "method": v["method"]}
            for v in videos
        ],
        "similarity": similarity,
    }

    template = _TEMPLATE_PATH.read_text(encoding="utf-8")
    html = template.replace("__DATA_JSON__", json.dumps(payload, ensure_ascii=False))

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    DASHBOARD_HTML.write_text(html, encoding="utf-8")
    logger.info("Dashboard generado: %s", DASHBOARD_HTML)
    return DASHBOARD_HTML
