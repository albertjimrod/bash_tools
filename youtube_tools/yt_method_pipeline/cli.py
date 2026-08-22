#!/usr/bin/env python3
"""CLI del pipeline: canal de YouTube -> transcripciones -> extracción -> informe."""
import argparse
import logging
import sys

import config
from pipeline import (
    aggregate, classify, dashboard, embeddings, extraction, idea_server,
    normalize, report, search, transcripts,
)
from pipeline.utils import setup_logging

logger = logging.getLogger(__name__)


def cmd_fetch(args):
    transcripts.run(args.entries, list_files=args.list, title_channel=args.title_channel, limit=args.limit)


def cmd_reannotate(args):
    transcripts.reannotate(channel_hint=args.channel_hint)


def cmd_classify(args):
    classify.run()


def cmd_extract(args):
    extraction.run()


def cmd_index(args):
    embeddings.run()


def cmd_search(args):
    results = search.run(args.query, top_k=args.top)
    search.print_results(results)


def cmd_normalize(args):
    methods_path, report_path = normalize.run()
    print(f"methods_norm.json generado en: {methods_path}")
    print(f"Informe de normalización generado en: {report_path}")


def cmd_dashboard(args):
    path = dashboard.run()
    print(f"Dashboard generado en: {path}")


def cmd_idea_server(args):
    idea_server.run()


def cmd_report(args):
    aggregate.run()
    path = report.run()
    print(f"Informe generado en: {path}")


def cmd_run(args):
    transcripts.run(args.entries, list_files=args.list, title_channel=args.title_channel, limit=args.limit)
    classify.run()
    extraction.run()
    embeddings.run()
    aggregate.run()
    path = report.run()
    print(f"Informe generado en: {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yt-method-pipeline",
        description="Pipeline reanudable: canal de YouTube -> transcripciones -> extracción estructurada -> informe.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_fetch = sub.add_parser(
        "fetch",
        help="Paso 1: descarga transcripciones a partir de una o varias entradas mezclables "
        "(canal, playlist, vídeo suelto, fichero de lista, búsqueda por título)",
    )
    p_fetch.add_argument(
        "entries", nargs="+",
        help="Una o varias entradas: @canal / URL de canal, URL de playlist, URL o ID de vídeo, "
        "o 'titulo:texto a buscar'",
    )
    p_fetch.add_argument(
        "--list", action="append", default=[], metavar="FICHERO",
        help="Fichero de texto con una URL/ID por línea (# comentario, líneas vacías se ignoran); repetible",
    )
    p_fetch.add_argument(
        "--title-channel", default=None, metavar="@canal",
        help="Acota las entradas 'titulo:...' a este canal, para reducir falsos positivos de la búsqueda",
    )
    p_fetch.add_argument(
        "--limit", type=int, default=None,
        help="Límite de vídeos a procesar (solo aplica a entradas de tipo canal)",
    )
    p_fetch.set_defaults(func=cmd_fetch)

    p_reannotate = sub.add_parser(
        "reannotate",
        help="Rellena canal_nombre/canal_id/fuente_origen en meta.json ya existentes a los que "
        "les falte, sin volver a descargar transcripciones",
    )
    p_reannotate.add_argument(
        "--channel-hint", default=None, metavar="@canal",
        help="fuente_detalle a usar para vídeos antiguos sin procedencia (todos se asumen de un "
        "único canal, ya que es el único modo que existía antes de este cambio)",
    )
    p_reannotate.set_defaults(func=cmd_reannotate)

    p_classify = sub.add_parser(
        "classify", help="Paso 1b: filtra vídeos que no expliquen un método de negocio replicable"
    )
    p_classify.set_defaults(func=cmd_classify)

    p_extract = sub.add_parser("extract", help="Paso 2: extracción estructurada por dimensiones")
    p_extract.set_defaults(func=cmd_extract)

    p_index = sub.add_parser(
        "index", help="Paso 3: embedding de cada método sobre su resumen normalizado"
    )
    p_index.set_defaults(func=cmd_index)

    p_search = sub.add_parser("search", help="Búsqueda semántica sobre los métodos indexados")
    p_search.add_argument("query", help="Consulta en lenguaje natural")
    p_search.add_argument("--top", type=int, default=5, help="Número de resultados")
    p_search.set_defaults(func=cmd_search)

    p_normalize = sub.add_parser(
        "normalize", help="Normaliza primitivos/categoría/herramientas y calcula 'potencial'"
    )
    p_normalize.set_defaults(func=cmd_normalize)

    p_dashboard = sub.add_parser(
        "dashboard",
        help="Dashboard HTML: expediente, rejilla de huecos, similitud y combinador (requiere 'normalize')",
    )
    p_dashboard.set_defaults(func=cmd_dashboard)

    p_idea_server = sub.add_parser(
        "idea-server",
        help="Servidor local (localhost:8765) para el botón 'Generar idea' del dashboard — usa Ollama por defecto (LLM_PROVIDER)",
    )
    p_idea_server.set_defaults(func=cmd_idea_server)

    p_report = sub.add_parser("report", help="Paso 4: agregación y generación del informe")
    p_report.set_defaults(func=cmd_report)

    p_run = sub.add_parser(
        "run", help="Ejecuta fetch + classify + extract + index + report en secuencia"
    )
    p_run.add_argument(
        "entries", nargs="+",
        help="Una o varias entradas: @canal / URL de canal, URL de playlist, URL o ID de vídeo, "
        "o 'titulo:texto a buscar'",
    )
    p_run.add_argument(
        "--list", action="append", default=[], metavar="FICHERO",
        help="Fichero de texto con una URL/ID por línea; repetible",
    )
    p_run.add_argument(
        "--title-channel", default=None, metavar="@canal",
        help="Acota las entradas 'titulo:...' a este canal",
    )
    p_run.add_argument("--limit", type=int, default=None, help="Límite de vídeos a procesar")
    p_run.set_defaults(func=cmd_run)

    return parser


def main(argv=None):
    setup_logging(config.PIPELINE_LOG)
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except Exception as exc:
        logger.exception("Error fatal: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
