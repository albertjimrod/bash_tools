"""Slugify, limpieza de subtítulos, retry/backoff y logging compartidos."""
import json
import logging
import re
import time
import unicodedata
from pathlib import Path

logger = logging.getLogger(__name__)


def is_excluded(video_dir: Path) -> bool:
    """True si 'classify' marcó este vídeo como no-método-de-negocio.

    Si no existe classification.json (no se ha ejecutado 'classify'), no se
    excluye nada.
    """
    classification_path = video_dir / "classification.json"
    if not classification_path.exists():
        return False
    try:
        data = json.loads(classification_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return not data.get("es_metodo_negocio", True)

_TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->")
_TAG_RE = re.compile(r"<[^>]+>")
_SOUND_TAG_RE = re.compile(
    r"\[(m[uú]sica|music|aplausos|applause|risas|laughter)\]", re.IGNORECASE
)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def strip_sound_tags(text: str) -> str:
    text = _SOUND_TAG_RE.sub("", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def clean_subtitle_text(raw: str) -> str:
    """Convierte un .vtt/.srt en texto plano: sin timestamps, etiquetas ni líneas repetidas."""
    lines = []
    prev = None
    for line in raw.splitlines():
        line = line.strip("﻿\r").strip()
        if not line:
            continue
        if line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        if _TIMESTAMP_RE.match(line):
            continue
        if line.isdigit():
            continue
        if "align:" in line or "position:" in line:
            continue
        line = _TAG_RE.sub(" ", line)
        line = line.replace("&nbsp;", " ").replace("&amp;", "&")
        line = line.replace("&lt;", "<").replace("&gt;", ">")
        line = re.sub(r"\s+", " ", line).strip()
        if not line or line == prev:
            continue
        lines.append(line)
        prev = line

    text = " ".join(lines)
    text = re.sub(r"([.!?])\s+", r"\1\n", text)
    return text.strip()


def retry_call(fn, *args, max_retries=4, base=2.0, no_retry=(), **kwargs):
    """Reintenta `fn(*args, **kwargs)` con backoff exponencial salvo excepciones en `no_retry`."""
    attempt = 0
    while True:
        try:
            return fn(*args, **kwargs)
        except no_retry:
            raise
        except Exception as exc:
            attempt += 1
            if attempt > max_retries:
                raise
            wait = base ** attempt
            logger.warning(
                "reintento %d/%d tras error (%s); esperando %.1fs",
                attempt, max_retries, exc, wait,
            )
            time.sleep(wait)


def append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def setup_logging(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
