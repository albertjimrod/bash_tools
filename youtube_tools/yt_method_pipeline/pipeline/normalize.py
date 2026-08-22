"""Capa de normalización: no destructiva, derivada de los method.json ya extraídos.

Lee configs/normalization.json (editable a mano), añade campos *_norm y un
escalar 'potencial' a cada vídeo, escribe data/methods_norm.json, y vuelca en
configs/normalization.json los valores crudos que no encuentre mapeados (bajo
cada '_pendientes') para que se completen a mano y se relance este paso.

También genera data/normalization_report.html con el estado de la
normalización (cobertura, pendientes, categorías re-etiquetadas).
"""
import datetime
import json
import logging
from collections import Counter
from pathlib import Path

import config

logger = logging.getLogger(__name__)

CONFIG_PATH = config.BASE_DIR / "configs" / "normalization.json"
METHODS_NORM = config.DATA_DIR / "methods_norm.json"
REPORT_HTML = config.DATA_DIR / "normalization_report.html"
_REPORT_TEMPLATE = config.BASE_DIR / "pipeline" / "normalization_report_template.html"

_FACETS = ("canal_apalancamiento", "mecanismo_valor", "audiencia", "categoria")

_EVIDENCIA_SCORE = {"pruebas_verificables": 1.0, "capturas_o_documentos": 0.6, "solo_afirmacion": 0.25}
_ESCALABILIDAD_SCORE = {"alta": 1.0, "media": 0.6, "baja": 0.25}
_SATURACION_SCORE = {"alta": 1.0, "media": 0.5, "baja": 0.0}
_INVERSION_SCORE = {"0": 0.0, "<100": 0.2, "100-1000": 0.5, "1000-10000": 0.8, ">10000": 1.0}
_DEFAULT_SUBSCORE = 0.5


def _load_norm_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _load_videos() -> list[dict]:
    videos = []
    for video_dir in sorted(p for p in config.TRANSCRIPTS_DIR.iterdir() if p.is_dir()):
        method_path = video_dir / "method.json"
        meta_path = video_dir / "meta.json"
        if not method_path.exists():
            continue
        method = json.loads(method_path.read_text(encoding="utf-8"))
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        videos.append({"id": video_dir.name, "title": meta.get("title"), "url": meta.get("url"), "method": method})
    return videos


def _map_facet(raw: str | None, facet_cfg: dict, pending: set) -> str | None:
    """Devuelve el valor normalizado, o None si no hay mapeo (y lo apunta a pendientes)."""
    if not raw:
        return None
    key = raw.strip().lower()
    mapped = facet_cfg.get("map", {}).get(key)
    if mapped is None:
        pending.add(raw.strip())
        return None
    return mapped


def _normalize_herramientas(tools: list, brand_corrections: dict, pending: set) -> list:
    out = []
    seen = set()
    for t in tools or []:
        key = (t or "").strip().lower()
        if not key:
            continue
        corrected = brand_corrections.get(key, key)
        if key not in brand_corrections:
            pending.add(t.strip())
        if corrected not in seen:
            seen.add(corrected)
            out.append(corrected)
    return out


def _potencial(method: dict, weights: dict) -> tuple[int, dict]:
    eco = method.get("economia") or {}
    evidencia = _EVIDENCIA_SCORE.get(method.get("evidencia"), _DEFAULT_SUBSCORE)
    escalabilidad = _ESCALABILIDAD_SCORE.get(eco.get("escalabilidad"), _DEFAULT_SUBSCORE)
    saturacion = _SATURACION_SCORE.get(method.get("saturacion_competencia"), _DEFAULT_SUBSCORE)
    inversion = _INVERSION_SCORE.get(eco.get("inversion_inicial"), _DEFAULT_SUBSCORE)

    we = weights.get("evidencia", 0.0)
    wsc = weights.get("escalabilidad", 0.0)
    wsat = weights.get("saturacion", 0.0)
    wi = weights.get("inversion", 0.0)

    raw = we * evidencia + wsc * escalabilidad + wsat * saturacion + wi * inversion
    # rango teórico alcanzable con estos pesos (cada subfactor en [0,1]), para
    # reescalar a 0-100 sin asumir signos fijos — si el usuario pone un peso
    # en positivo o negativo en el config, el rango se recalcula solo.
    pesos = (we, wsc, wsat, wi)
    raw_min = sum(min(w, 0) for w in pesos)
    raw_max = sum(max(w, 0) for w in pesos)
    span = (raw_max - raw_min) or 1.0
    score = round((raw - raw_min) / span * 100)
    score = max(0, min(100, score))

    breakdown = {
        "evidencia": evidencia, "escalabilidad": escalabilidad,
        "saturacion": saturacion, "inversion": inversion,
        "pesos": {"evidencia": we, "escalabilidad": wsc, "saturacion": wsat, "inversion": wi},
    }
    return score, breakdown


def _normalize_video(video: dict, norm_cfg: dict, pending: dict) -> dict:
    method = video["method"]
    prim = method.get("primitivos") or {}
    eco = method.get("economia") or {}

    canal_norm = _map_facet(prim.get("canal_apalancamiento"), norm_cfg["canal_apalancamiento"], pending["canal_apalancamiento"])
    mecanismo_norm = _map_facet(prim.get("mecanismo_valor"), norm_cfg["mecanismo_valor"], pending["mecanismo_valor"])
    audiencia_norm = _map_facet(prim.get("audiencia"), norm_cfg["audiencia"], pending["audiencia"])
    categoria_norm = _map_facet(method.get("categoria"), norm_cfg["categoria"], pending["categoria"])

    # categoria_por_mecanismo manda sobre el mapeo identidad de categoria: la
    # categoría que pone el LLM en extract resultó poco fiable (ver _doc del
    # config), mecanismo_norm es una señal mejor.
    if mecanismo_norm is not None and mecanismo_norm != "otros":
        reasignada = norm_cfg["categoria_por_mecanismo"]["map"].get(mecanismo_norm)
        if reasignada is not None:
            categoria_norm = reasignada
        else:
            pending["categoria_por_mecanismo"].add(mecanismo_norm)

    herramientas_norm = _normalize_herramientas(
        method.get("herramientas"), norm_cfg["brand_corrections"], pending["herramientas"]
    )
    potencial, potencial_breakdown = _potencial(method, norm_cfg["potencial_weights"])

    resuelto = all(v is not None for v in (canal_norm, mecanismo_norm, audiencia_norm, categoria_norm))

    return {
        "id": video["id"],
        "title": video["title"],
        "url": video["url"],
        "method": method,
        "categoria_norm": categoria_norm,
        "canal_norm": canal_norm,
        "mecanismo_norm": mecanismo_norm,
        "audiencia_norm": audiencia_norm,
        "herramientas_norm": herramientas_norm,
        "bucket_inversion": eco.get("inversion_inicial"),
        "potencial": potencial,
        "potencial_breakdown": potencial_breakdown,
        "resuelto": resuelto,
    }


def _merge_pending(norm_cfg: dict, pending: dict) -> None:
    for facet in _FACETS:
        existing = set(norm_cfg[facet].get("_pendientes", []))
        norm_cfg[facet]["_pendientes"] = sorted(existing | pending[facet])
    for extra in ("herramientas", "categoria_por_mecanismo"):
        existing = set(norm_cfg[extra].get("_pendientes", []))
        norm_cfg[extra]["_pendientes"] = sorted(existing | pending[extra])


def _build_report_data(videos: list[dict], norm_cfg: dict, pending: dict) -> dict:
    n = len(videos)
    resueltos = sum(1 for v in videos if v["resuelto"])

    pendientes_counts = {}
    for facet in list(_FACETS) + ["herramientas"]:
        raw_counter = Counter()
        if facet == "herramientas":
            for v in videos:
                for t in v["method"].get("herramientas") or []:
                    if t and t.strip() in pending["herramientas"]:
                        raw_counter[t.strip()] += 1
        else:
            for v in videos:
                raw = v["method"].get("categoria") if facet == "categoria" else (v["method"].get("primitivos") or {}).get(facet)
                if raw and raw.strip() in pending[facet]:
                    raw_counter[raw.strip()] += 1
        pendientes_counts[facet] = [{"valor": k, "n": c} for k, c in raw_counter.most_common()]

    categoria_remap = Counter()
    changed = 0
    for v in videos:
        original = v["method"].get("categoria")
        normalizada = v["categoria_norm"]
        categoria_remap[(original, normalizada)] += 1
        if original != normalizada:
            changed += 1
    categoria_table = [
        {"original": o, "normalizada": n, "n": c}
        for (o, n), c in sorted(categoria_remap.items(), key=lambda kv: -kv[1])
    ]

    baja_varianza = []
    for campo in norm_cfg["baja_varianza"]["campos"]:
        counter = Counter()
        for v in videos:
            m = v["method"]
            if campo == "sesgo_supervivencia":
                val = (m.get("sesgo_supervivencia") or {}).get("presente")
            else:
                val = m.get(campo)
            counter[val] += 1
        top_val, top_n = counter.most_common(1)[0] if counter else (None, 0)
        pct = round(top_n / n * 100) if n else 0
        baja_varianza.append({
            "campo": campo,
            "valor_dominante": top_val,
            "pct": pct,
            "distribucion": [{"valor": k, "n": c} for k, c in counter.most_common()],
        })

    return {
        "generado_en": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_videos": n,
        "cobertura": {"resueltos": resueltos, "total": n, "pct": round(resueltos / n * 100) if n else 0},
        "pendientes": pendientes_counts,
        "categoria_remap": categoria_table,
        "categoria_cambiados": changed,
        "baja_varianza": baja_varianza,
        "baja_varianza_doc": norm_cfg["baja_varianza"].get("_doc", ""),
        "potencial_weights": {k: v for k, v in norm_cfg["potencial_weights"].items() if not k.startswith("_")},
    }


def run() -> tuple[Path, Path]:
    norm_cfg = _load_norm_config()
    videos = _load_videos()
    if not videos:
        raise RuntimeError("No hay vídeos extraídos. Ejecuta 'extract' primero.")

    pending = {facet: set() for facet in _FACETS}
    pending["herramientas"] = set()
    pending["categoria_por_mecanismo"] = set()

    normalized = [_normalize_video(v, norm_cfg, pending) for v in videos]

    _merge_pending(norm_cfg, pending)
    CONFIG_PATH.write_text(json.dumps(norm_cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    METHODS_NORM.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("methods_norm.json generado con %d vídeos (%s)", len(normalized), METHODS_NORM)

    report_data = _build_report_data(normalized, norm_cfg, pending)
    template = _REPORT_TEMPLATE.read_text(encoding="utf-8")
    html = template.replace("__DATA_JSON__", json.dumps(report_data, ensure_ascii=False))
    REPORT_HTML.write_text(html, encoding="utf-8")
    logger.info("Informe de normalización generado: %s", REPORT_HTML)

    total_pending = sum(len(v) for v in pending.values())
    logger.info(
        "Cobertura: %d/%d vídeos (%d%%) con las 4 facetas resueltas. %d valores pendientes de mapear en total.",
        report_data["cobertura"]["resueltos"], report_data["cobertura"]["total"],
        report_data["cobertura"]["pct"], total_pending,
    )

    return METHODS_NORM, REPORT_HTML
