"""PASO 3b/3c: distribuciones, contraste y recombinación de primitivos en un informe Markdown."""
import json
import logging
from collections import Counter
from pathlib import Path

import config
from .llm_client import call_tool

logger = logging.getLogger(__name__)

TOP_N = 10
_INVERSION_ORDER = {"0": 0, "<100": 1, "100-1000": 2, "1000-10000": 3, ">10000": 4}


def _cell(value) -> str:
    """Escapa texto libre para que no rompa una celda de tabla Markdown."""
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def _channel_label() -> str:
    if config.CHANNEL_FILE.exists():
        try:
            return json.loads(config.CHANNEL_FILE.read_text(encoding="utf-8")).get("channel", "canal")
        except Exception:
            pass
    return "canal"


def _load_methods() -> list[dict]:
    if not config.METHODS_JSONL.exists():
        raise RuntimeError("No existe methods.jsonl. Ejecuta 'extract' y vuelve a intentarlo.")
    records = []
    with config.METHODS_JSONL.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _section_distribuciones(records: list[dict]) -> str:
    categorias = Counter(r.get("categoria") for r in records)
    tipos = Counter(r.get("tipo_ingreso") for r in records)
    inversiones = Counter((r.get("economia") or {}).get("inversion_inicial") for r in records)
    herramientas = Counter()
    for r in records:
        for h in r.get("herramientas") or []:
            herramientas[h] += 1

    lines = ["## Distribuciones\n", f"Total de métodos analizados: **{len(records)}**\n"]

    lines.append("### Por categoría\n")
    lines.append("| Categoría | Métodos |\n|---|---|")
    lines += [f"| {cat or 'null'} | {n} |" for cat, n in categorias.most_common()]

    lines.append("\n### Por tipo de ingreso\n")
    lines.append("| Tipo de ingreso | Métodos |\n|---|---|")
    lines += [f"| {tipo or 'null'} | {n} |" for tipo, n in tipos.most_common()]

    lines.append("\n### Por inversión inicial\n")
    lines.append("| Inversión inicial | Métodos |\n|---|---|")
    lines += [f"| {inv or 'null'} | {n} |" for inv, n in inversiones.most_common()]

    lines.append(f"\n### Herramientas más repetidas (top {TOP_N})\n")
    lines.append("| Herramienta | Menciones |\n|---|---|")
    lines += [f"| {_cell(h)} | {n} |" for h, n in herramientas.most_common(TOP_N)]

    return "\n".join(lines) + "\n"


def _section_contraste(records: list[dict]) -> str:
    def inv_rank(r):
        inv = (r.get("economia") or {}).get("inversion_inicial")
        return _INVERSION_ORDER.get(inv, 99)

    prometedores = sorted((r for r in records if inv_rank(r) < 99), key=inv_rank)[:TOP_N]

    con_red_flags = sorted(records, key=lambda r: len(r.get("red_flags") or []), reverse=True)
    con_red_flags = [r for r in con_red_flags if r.get("red_flags")][:TOP_N]

    solo_afirmacion = [r for r in records if r.get("evidencia") == "solo_afirmacion"]

    lines = ["## Contraste\n", "### Más prometedores con menos inversión\n"]
    lines.append("| Título | Inversión inicial | Categoría | Tipo de ingreso |\n|---|---|---|---|")
    for r in prometedores:
        inv = (r.get("economia") or {}).get("inversion_inicial")
        lines.append(
            f"| {_cell(r.get('title'))} | {_cell(inv)} | {_cell(r.get('categoria'))} | "
            f"{_cell(r.get('tipo_ingreso'))} |"
        )

    lines.append("\n### Más red flags declaradas\n")
    lines.append("| Título | Nº red flags | Detalle |\n|---|---|---|")
    for r in con_red_flags:
        detalle = "; ".join(r.get("red_flags") or [])
        lines.append(
            f"| {_cell(r.get('title'))} | {len(r.get('red_flags') or [])} | {_cell(detalle)} |"
        )

    lines.append(f"\n### Evidencia = solo afirmaciones ({len(solo_afirmacion)} métodos)\n")
    lines.append("| Título | Categoría |\n|---|---|")
    for r in solo_afirmacion:
        lines.append(f"| {_cell(r.get('title'))} | {_cell(r.get('categoria'))} |")

    return "\n".join(lines) + "\n"


def _distinct_primitivos(records: list[dict]):
    mecanismos, canales, audiencias, combos = set(), set(), set(), set()
    for r in records:
        p = r.get("primitivos") or {}
        m, c, a = p.get("mecanismo_valor"), p.get("canal_apalancamiento"), p.get("audiencia")
        if m:
            mecanismos.add(m)
        if c:
            canales.add(c)
        if a:
            audiencias.add(a)
        if m and c and a:
            combos.add((m, c, a))
    return mecanismos, canales, audiencias, combos


def _generar_ideas(records: list[dict]) -> list[dict]:
    mecanismos, canales, audiencias, combos = _distinct_primitivos(records)
    if not (mecanismos and canales and audiencias):
        logger.warning("no hay suficientes primitivos para recombinar ideas")
        return []

    schema = json.loads((config.SCHEMAS_DIR / "idea_recombination.json").read_text(encoding="utf-8"))
    template = (config.PROMPTS_DIR / "recombine_ideas.md").read_text(encoding="utf-8")

    prompt = template.format(
        combos_existentes="\n".join(f"- {m} + {c} + {a}" for m, c, a in sorted(combos)) or "(ninguna)",
        mecanismos="\n".join(f"- {m}" for m in sorted(mecanismos)),
        canales="\n".join(f"- {c}" for c in sorted(canales)),
        audiencias="\n".join(f"- {a}" for a in sorted(audiencias)),
    )

    tool = {
        "name": "propose_ideas",
        "description": "Propone combinaciones nuevas de primitivos con su justificación.",
        "input_schema": {k: v for k, v in schema.items() if k not in ("$schema", "title")},
    }

    ideas = call_tool(prompt, tool, think=True).get("ideas", [])
    return [
        idea for idea in ideas
        if (idea.get("mecanismo_valor"), idea.get("canal_apalancamiento"), idea.get("audiencia")) not in combos
    ]


def _section_ideas(ideas: list[dict]) -> str:
    lines = ["## Ideas nuevas (recombinación de primitivos)\n"]
    if not ideas:
        lines.append("_No se generaron ideas (datos insuficientes o fallo en la llamada a Claude)._\n")
        return "\n".join(lines)
    for idea in ideas:
        lines.append(
            f"- **{idea.get('mecanismo_valor')} × {idea.get('canal_apalancamiento')} × "
            f"{idea.get('audiencia')}** — {idea.get('razon')}"
        )
    return "\n".join(lines) + "\n"


def run() -> Path:
    records = _load_methods()
    if not records:
        raise RuntimeError("methods.jsonl está vacío. Ejecuta 'extract' primero.")

    partes = [
        f"# Informe de métodos — {_channel_label()}\n",
        _section_distribuciones(records),
        _section_contraste(records),
    ]

    try:
        ideas = _generar_ideas(records)
    except Exception as exc:
        logger.error("fallo generando ideas nuevas: %s", exc)
        ideas = []

    partes.append(_section_ideas(ideas))

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.REPORT_MD.write_text("\n".join(partes), encoding="utf-8")
    logger.info("Informe generado: %s", config.REPORT_MD)
    return config.REPORT_MD
