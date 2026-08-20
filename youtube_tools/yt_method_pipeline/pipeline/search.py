"""Búsqueda semántica sobre los embeddings ya calculados (PASO 4)."""
import json
import logging
import math
from pathlib import Path

import config
from .llm_client import embed

logger = logging.getLogger(__name__)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _load_indexed() -> list[dict]:
    entries = []
    for video_dir in sorted(p for p in config.TRANSCRIPTS_DIR.iterdir() if p.is_dir()):
        embedding_path = video_dir / "embedding.json"
        meta_path = video_dir / "meta.json"
        method_path = video_dir / "method.json"
        if not embedding_path.exists():
            continue
        embedding = json.loads(embedding_path.read_text(encoding="utf-8"))
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        method = json.loads(method_path.read_text(encoding="utf-8")) if method_path.exists() else {}
        entries.append(
            {
                "video_dir": video_dir.name,
                "title": meta.get("title"),
                "url": meta.get("url"),
                "resumen_frase": method.get("resumen_frase") or method.get("resumen"),
                "vector": embedding["vector"],
            }
        )
    return entries


def run(query: str, top_k: int = 5) -> list[dict]:
    entries = _load_indexed()
    if not entries:
        raise RuntimeError("No hay ningún vídeo indexado. Ejecuta 'index' primero.")

    query_vector = embed(query)
    for entry in entries:
        entry["score"] = _cosine(query_vector, entry["vector"])

    entries.sort(key=lambda e: e["score"], reverse=True)
    return entries[:top_k]


def print_results(results: list[dict]) -> None:
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['score']:.3f}] {r['title']}")
        print(f"   {r['resumen_frase']}")
        print(f"   {r['url']}")
