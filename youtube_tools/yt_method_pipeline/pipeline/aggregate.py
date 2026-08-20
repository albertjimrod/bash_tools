"""PASO 3a: consolida todos los method.json en un único JSONL."""
import json
import logging

import config

logger = logging.getLogger(__name__)


def run() -> None:
    video_dirs = sorted(p for p in config.TRANSCRIPTS_DIR.iterdir() if p.is_dir())

    records = []
    pending = []
    for video_dir in video_dirs:
        method_path = video_dir / "method.json"
        meta_path = video_dir / "meta.json"
        if not method_path.exists():
            pending.append(video_dir.name)
            continue
        method = json.loads(method_path.read_text(encoding="utf-8"))
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        records.append(
            {
                "video_id": meta.get("video_id", video_dir.name),
                "title": meta.get("title"),
                "url": meta.get("url"),
                **method,
            }
        )

    if pending:
        preview = ", ".join(pending[:5]) + ("..." if len(pending) > 5 else "")
        logger.warning(
            "%d vídeos sin method.json (ejecuta 'extract' antes de 'report'): %s",
            len(pending), preview,
        )

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with config.METHODS_JSONL.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    logger.info("methods.jsonl generado con %d métodos (%s)", len(records), config.METHODS_JSONL)
