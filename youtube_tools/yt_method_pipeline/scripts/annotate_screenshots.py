#!/usr/bin/env python3
"""Genera, para cada pestaña del dashboard, una captura de página completa
con una franja explicativa incrustada arriba (qué es esa vista y qué hace),
en el mismo estilo visual del dashboard. No usa ningún LLM: el texto de cada
franja es una descripción fija del funcionamiento de la pestaña, la misma
que ya está documentada en MANUAL.md.

100% local (Playwright/Chromium contra data/dashboard.html) — no hace
llamadas a ninguna API.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config

DASHBOARD_HTML = config.DATA_DIR / "dashboard.html"
OUT_DIR = config.DATA_DIR / "capturas_explicadas"

TABS = ["expediente", "huecos", "similitud", "combinador", "constructor", "panorama"]

# Misma paleta que pipeline/dashboard_template.html (tema claro).
PALETTE = {
    "bg": "#F2EFE9", "surface": "#FFFFFF", "border": "#E1DCD0",
    "ink": "#23201B", "ink_muted": "#756E5F", "accent": "#2B6E68",
}

# Título + explicación funcional de cada pestaña, condensados de MANUAL.md
# (paso 6) — no depende de los datos del corpus, así que no hay cifras que
# puedan quedar desactualizadas ni inventadas.
EXPLICACIONES = {
    "expediente": (
        "Expediente de métodos",
        "La ficha completa de cada vídeo: los 6 bloques extraídos por el LLM "
        "(identificación, economía, requisitos y barreras, ejecución, "
        "credibilidad/riesgo, meta/fuente) más el potencial calculado, "
        "vídeo a vídeo.",
    ),
    "huecos": (
        "Rejilla de huecos",
        "Cruza mecanismo, canal y audiencia (ya normalizados) para señalar qué "
        "combinaciones no cubre ningún vídeo todavía. Cada celda vacía muestra "
        "un score estimado y su n de respaldo; con n bajo se marca como señal "
        "frágil.",
    ),
    "similitud": (
        "Similitud entre métodos",
        "Compara los métodos por significado, no por palabra exacta: usa "
        "embeddings calculados sobre un resumen normalizado de cada vídeo "
        "para encontrar qué contenidos explican, en el fondo, lo mismo.",
    ),
    "combinador": (
        "Combinador de primitivos",
        "Mezcla piezas (mecanismo, canal, audiencia) tomadas de vídeos "
        "distintos y comprueba si esa combinación ya existe en el corpus o "
        "es nueva, respetando las incompatibilidades declaradas.",
    ),
    "constructor": (
        "Constructor de proyecto",
        "Al revés que la rejilla: aquí fijas tú, faceta a faceta, la "
        "composición de un proyecto, y ves en vivo cuántos vídeos reales la "
        "sostienen y con qué potencial medio.",
    ),
    "panorama": (
        "Panorama del corpus",
        "Vista de solo diagnóstico, sin generar ideas: mapas de calor, "
        "concentración por categoría y dispersión potencial/saturación, para "
        "leer el terreno antes de decidir nada.",
    ),
}

CAPTION_JS = """
([titulo, texto, palette]) => {
    const banner = document.createElement('div');
    banner.id = '__caption_banner';
    banner.style.cssText = `
        box-sizing: border-box;
        width: 100%;
        padding: 22px 32px;
        background: ${palette.surface};
        border-bottom: 3px solid ${palette.accent};
        font-family: Helvetica, Arial, sans-serif;
    `;
    const eyebrow = document.createElement('div');
    eyebrow.textContent = 'QUÉ HACE ESTA PESTAÑA';
    eyebrow.style.cssText = `
        font-family: 'Courier New', monospace;
        font-size: 12px;
        letter-spacing: 0.08em;
        color: ${palette.accent};
        margin-bottom: 6px;
    `;
    const h = document.createElement('div');
    h.textContent = titulo;
    h.style.cssText = `font-size: 24px; font-weight: 700; color: ${palette.ink}; margin-bottom: 8px;`;
    const p = document.createElement('div');
    p.textContent = texto;
    p.style.cssText = `font-size: 15.5px; line-height: 1.5; color: ${palette.ink_muted}; max-width: 980px;`;
    banner.appendChild(eyebrow);
    banner.appendChild(h);
    banner.appendChild(p);
    document.body.insertBefore(banner, document.body.firstChild);
}
"""


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


def capture_annotated(pestana: str, enfoque: str, n_total: int, out_path: Path) -> None:
    sync_playwright = _require_playwright()
    titulo, texto = EXPLICACIONES[pestana]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(DASHBOARD_HTML.resolve().as_uri())
        page.wait_for_selector(".tab-btn")
        if enfoque == "metodologia":
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
        page.locator(f'.tab-panel[data-tab="{pestana}"]').wait_for(state="visible")
        page.evaluate(CAPTION_JS, [titulo, texto, PALETTE])
        page.screenshot(path=str(out_path), full_page=True)
        browser.close()
    print(f"  {pestana} -> {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Genera capturas de página completa del dashboard, una por pestaña, con una "
        "franja explicativa incrustada arriba (qué hace esa vista). No usa ningún LLM."
    )
    parser.add_argument("--pestana", choices=TABS, default=None, help="Solo esta pestaña (por defecto, las 6)")
    parser.add_argument("--enfoque", default="metodologia", choices=["metodologia", "nombres_reales"])
    parser.add_argument("--salida", default=None, help="Carpeta de salida (por defecto data/capturas_explicadas/)")
    args = parser.parse_args()

    if not DASHBOARD_HTML.exists():
        raise SystemExit("No existe data/dashboard.html. Ejecuta '.venv/bin/python cli.py dashboard' primero.")

    import json
    videos = json.loads((config.DATA_DIR / "methods_norm.json").read_text(encoding="utf-8"))
    n_total = len(videos)

    out_dir = Path(args.salida) if args.salida else OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    tabs = [args.pestana] if args.pestana else TABS
    print(f"Generando {len(tabs)} captura(s) explicada(s) en {out_dir}/ ...")
    for pestana in tabs:
        capture_annotated(pestana, args.enfoque, n_total, out_dir / f"{pestana}.png")

    print("\nListo. Estas capturas son solo para explicar el funcionamiento (no citan cifras del "
          "corpus salvo el número total de vídeos en el subtítulo) — no publican nada.")


if __name__ == "__main__":
    main()
