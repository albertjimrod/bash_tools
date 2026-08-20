"""PASO 1b: filtra los vídeos descargados, quedándose solo con los que explican
un método de negocio replicable (nada de entrevistas, noticias, etc.).

No borra transcripciones: si un vídeo ya tenía method.json/embedding.json de una
ejecución anterior y ahora se clasifica como 'no es método de negocio', se borran
esos dos artefactos derivados (quedan obsoletos) pero transcript.txt y meta.json
se mantienen en disco.
"""
import json
import logging
from pathlib import Path

import config
from .llm_client import call_tool

logger = logging.getLogger(__name__)

TOOL_NAME = "classify_video"
_EXCERPT_CHARS = 4000


def _load_schema() -> dict:
    return json.loads((config.SCHEMAS_DIR / "classification.json").read_text(encoding="utf-8"))


def _load_prompt_template() -> str:
    return (config.PROMPTS_DIR / "classify_video.md").read_text(encoding="utf-8")


def _build_tool(schema: dict) -> dict:
    input_schema = {k: v for k, v in schema.items() if k not in ("$schema", "title")}
    return {
        "name": TOOL_NAME,
        "description": "Clasifica si el vídeo explica un método de negocio replicable.",
        "input_schema": input_schema,
    }


def classify_one(video_dir: Path, schema: dict, tool: dict, template: str) -> str:
    """Devuelve 'ok', 'skip' o 'fail'."""
    classification_path = video_dir / "classification.json"
    if classification_path.exists():
        return "skip"

    transcript_path = video_dir / "transcript.txt"
    meta_path = video_dir / "meta.json"
    if not transcript_path.exists():
        return "fail"

    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    excerpt = transcript_path.read_text(encoding="utf-8")[:_EXCERPT_CHARS]
    prompt = template.format(title=meta.get("title", ""), transcript_excerpt=excerpt)

    try:
        data = call_tool(prompt, tool, max_tokens=512)
    except Exception as exc:
        logger.warning("fallo clasificando %s: %s", video_dir.name, exc)
        return "fail"

    classification_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    if not data.get("es_metodo_negocio", True):
        logger.info("excluido (%s): %s", data.get("motivo", ""), video_dir.name)
        removed = []
        for stale in ("method.json", "embedding.json"):
            stale_path = video_dir / stale
            if stale_path.exists():
                stale_path.unlink()
                removed.append(stale)
        if removed:
            logger.info("limpiados artefactos obsoletos de %s: %s", video_dir.name, ", ".join(removed))
    else:
        logger.info("incluido: %s", video_dir.name)

    return "ok"


def run() -> None:
    schema = _load_schema()
    tool = _build_tool(schema)
    template = _load_prompt_template()

    video_dirs = sorted(p for p in config.TRANSCRIPTS_DIR.iterdir() if p.is_dir())
    logger.info("Paso 1b: %d directorios de transcripción encontrados", len(video_dirs))

    counts = {"ok": 0, "skip": 0, "fail": 0}
    for i, video_dir in enumerate(video_dirs, 1):
        logger.info("[%d/%d] %s", i, len(video_dirs), video_dir.name)
        counts[classify_one(video_dir, schema, tool, template)] += 1

    logger.info(
        "Paso 1b completado: %(ok)d clasificados, %(skip)d ya existían, %(fail)d fallidos", counts
    )
