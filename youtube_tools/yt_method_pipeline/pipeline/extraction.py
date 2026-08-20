"""PASO 2: extracción normalizada de cada transcripción vía Claude API (tool use)."""
import json
import logging
from pathlib import Path

import jsonschema

import config
from .llm_client import call_tool
from .utils import is_excluded

logger = logging.getLogger(__name__)

TOOL_NAME = "extract_method"


def _load_schema() -> dict:
    return json.loads((config.SCHEMAS_DIR / "method_extraction.json").read_text(encoding="utf-8"))


def _load_prompt_template() -> str:
    return (config.PROMPTS_DIR / "extract_method.md").read_text(encoding="utf-8")


def _build_tool(schema: dict) -> dict:
    input_schema = {k: v for k, v in schema.items() if k not in ("$schema", "title")}
    return {
        "name": TOOL_NAME,
        "description": "Extrae de forma estructurada el método de ingresos descrito en la transcripción.",
        "input_schema": input_schema,
    }


def _unwrap_stray_key(data: dict, schema: dict) -> dict:
    """A veces el modelo envuelve el JSON esperado en una única clave espuria
    (p.ej. '$PARAMETER_NAME'). Si ninguna clave del nivel superior coincide con
    el schema pero hay un único valor tipo dict, se desenvuelve."""
    expected = schema.get("properties", {}).keys()
    if isinstance(data, dict) and not (expected & data.keys()) and len(data) == 1:
        inner = next(iter(data.values()))
        if isinstance(inner, dict):
            return inner
    return data


def _clean_stray_nulls(value):
    """El modelo a veces escribe el string literal 'null' en vez del null de JSON
    en campos nullable; pasa la validación (es un string válido) pero ensucia
    los datos. Se recorre recursivamente y se convierte a None."""
    if isinstance(value, str):
        return None if value.strip().lower() == "null" else value
    if isinstance(value, list):
        return [_clean_stray_nulls(v) for v in value]
    if isinstance(value, dict):
        return {k: _clean_stray_nulls(v) for k, v in value.items()}
    return value


def extract_one(video_dir: Path, schema: dict, tool: dict, template: str) -> str:
    """Devuelve 'ok', 'skip' o 'fail'."""
    method_path = video_dir / "method.json"
    if method_path.exists():
        return "skip"

    transcript_path = video_dir / "transcript.txt"
    meta_path = video_dir / "meta.json"
    if not transcript_path.exists() or not meta_path.exists():
        logger.warning("faltan ficheros en %s, se omite", video_dir.name)
        return "fail"

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    transcript = transcript_path.read_text(encoding="utf-8")
    prompt = template.format(
        title=meta.get("title", ""), url=meta.get("url", ""), transcript=transcript
    )

    for attempt in range(2):
        try:
            data = call_tool(prompt, tool)
            data = _unwrap_stray_key(data, schema)
            data = _clean_stray_nulls(data)
            jsonschema.validate(data, schema)
            method_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            logger.info("ok: %s", video_dir.name)
            return "ok"
        except jsonschema.ValidationError as exc:
            logger.warning(
                "validación falló (intento %d/2) en %s: %s", attempt + 1, video_dir.name, exc.message
            )
        except Exception as exc:
            logger.warning(
                "error de extracción (intento %d/2) en %s: %s", attempt + 1, video_dir.name, exc
            )

    logger.error("fallo definitivo extrayendo %s", video_dir.name)
    return "fail"


def run() -> None:
    schema = _load_schema()
    tool = _build_tool(schema)
    template = _load_prompt_template()

    all_dirs = sorted(p for p in config.TRANSCRIPTS_DIR.iterdir() if p.is_dir())
    excluded = [d for d in all_dirs if is_excluded(d)]
    video_dirs = [d for d in all_dirs if d not in excluded]
    logger.info(
        "Paso 2: %d directorios de transcripción encontrados (%d excluidos por 'classify')",
        len(video_dirs), len(excluded),
    )

    counts = {"ok": 0, "skip": 0, "fail": 0}
    for i, video_dir in enumerate(video_dirs, 1):
        logger.info("[%d/%d] %s", i, len(video_dirs), video_dir.name)
        counts[extract_one(video_dir, schema, tool, template)] += 1

    logger.info(
        "Paso 2 completado: %(ok)d nuevas, %(skip)d ya existían, %(fail)d fallidas", counts
    )
