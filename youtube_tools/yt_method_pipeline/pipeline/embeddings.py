"""PASO 4: embedding de cada método sobre un resumen normalizado (no la transcripción cruda).

El texto que se embebe se construye determinísticamente en Python a partir del
`method.json` ya validado contra el schema — no hay una llamada a LLM de por
medio, así que es consistente entre vídeos y no añade coste ni variabilidad.
"""
import json
import logging
from pathlib import Path

import config
from .llm_client import embed
from .utils import is_excluded

logger = logging.getLogger(__name__)


def _join(items) -> str:
    return ", ".join(items) if items else "ninguna"


def normalized_text(method: dict, meta: dict) -> str:
    economia = method.get("economia") or {}
    requisitos = method.get("requisitos") or {}
    vende_algo = method.get("vende_algo") or {}
    sesgo = method.get("sesgo_supervivencia") or {}
    publico = method.get("publico_objetivo") or {}
    primitivos = method.get("primitivos") or {}

    partes = [
        f"Título: {meta.get('title', '')}.",
        f"Método: {method.get('resumen_frase') or method.get('resumen') or ''}",
        f"Categoría: {method.get('categoria')}.",
        f"Tipo de ingreso: {method.get('tipo_ingreso')}"
        f" ({'evergreen' if method.get('evergreen') else 'no evergreen'}).",
        f"Economía: ingreso declarado {economia.get('ingreso_declarado') or 'no especificado'},"
        f" inversión inicial {economia.get('inversion_inicial') or 'no especificada'},"
        f" costes recurrentes {economia.get('costes_recurrentes') or 'ninguno declarado'},"
        f" primer ingreso en {economia.get('tiempo_primer_ingreso') or 'no especificado'},"
        f" monetización: {economia.get('mecanismo_monetizacion') or 'no especificada'},"
        f" escalabilidad {economia.get('escalabilidad') or 'no especificada'}.",
        f"Requisitos: habilidades {_join(requisitos.get('habilidades_necesarias'))},"
        f" conocimiento previo {requisitos.get('conocimiento_previo') or 'no especificado'},"
        f" dedicación {requisitos.get('dedicacion_horas_semana') or 'no especificada'}.",
        f"Herramientas: {_join(method.get('herramientas'))}.",
        f"Pasos: {_join(method.get('pasos'))}.",
        f"Tácticas: {_join(method.get('tacticas'))}.",
        f"Recursos citados: {_join(method.get('recursos_citados'))}.",
        f"Riesgos declarados: {_join(method.get('riesgos_declarados'))}.",
        f"Riesgos omitidos: {_join(method.get('riesgos_omitidos'))}.",
        f"Saturación/competencia: {method.get('saturacion_competencia') or 'no especificada'}.",
        f"Evidencia aportada: {method.get('evidencia') or 'no especificada'}.",
        f"Red flags: {_join(method.get('red_flags'))}.",
        f"Vende: {vende_algo.get('tipo') or 'no especificado'}"
        f" ({vende_algo.get('detalle') or 'sin detalle'}).",
        f"Sesgo de supervivencia: {'sí' if sesgo.get('presente') else 'no'}"
        f" ({sesgo.get('detalle') or 'sin detalle'}).",
        f"Público objetivo: nivel {publico.get('nivel') or 'no especificado'},"
        f" {'requiere' if publico.get('requiere_capital') else 'no requiere'} capital inicial.",
        f"Incentivo del creador: {method.get('incentivo_creador') or 'no especificado'}.",
        f"Primitivos: {primitivos.get('mecanismo_valor')} x"
        f" {primitivos.get('canal_apalancamiento')} x {primitivos.get('audiencia')}.",
    ]
    return "\n".join(partes)


def embed_one(video_dir: Path) -> str:
    """Devuelve 'ok', 'skip' o 'fail'."""
    embedding_path = video_dir / "embedding.json"
    if embedding_path.exists():
        return "skip"

    method_path = video_dir / "method.json"
    meta_path = video_dir / "meta.json"
    if not method_path.exists():
        logger.warning("sin method.json en %s, se omite (ejecuta 'extract' antes)", video_dir.name)
        return "fail"

    method = json.loads(method_path.read_text(encoding="utf-8"))
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    text = normalized_text(method, meta)

    try:
        vector = embed(text)
    except Exception as exc:
        logger.warning("fallo generando embedding de %s: %s", video_dir.name, exc)
        return "fail"

    embedding_path.write_text(
        json.dumps({"model": config.OLLAMA_EMBED_MODEL, "text": text, "vector": vector}),
        encoding="utf-8",
    )
    logger.info("ok: %s", video_dir.name)
    return "ok"


def run() -> None:
    all_dirs = sorted(p for p in config.TRANSCRIPTS_DIR.iterdir() if p.is_dir())
    excluded = [d for d in all_dirs if is_excluded(d)]
    video_dirs = [d for d in all_dirs if d not in excluded]
    logger.info(
        "Paso 4: %d directorios de transcripción encontrados (%d excluidos por 'classify')",
        len(video_dirs), len(excluded),
    )

    counts = {"ok": 0, "skip": 0, "fail": 0}
    for i, video_dir in enumerate(video_dirs, 1):
        logger.info("[%d/%d] %s", i, len(video_dirs), video_dir.name)
        counts[embed_one(video_dir)] += 1

    logger.info(
        "Paso 4 completado: %(ok)d nuevos, %(skip)d ya existían, %(fail)d fallidos", counts
    )
