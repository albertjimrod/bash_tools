"""PASO 1: descarga de transcripciones por vídeo (youtube-transcript-api, fallback a yt-dlp)."""
import json
import logging
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

from youtube_transcript_api import AgeRestricted, RequestBlocked, YouTubeTranscriptApi

import config
from .channel import enumerate_sources, list_single_video
from .utils import clean_subtitle_text, retry_call, slugify, strip_sound_tags, append_line

logger = logging.getLogger(__name__)
_YTDLP_CMD = [sys.executable, "-m", "yt_dlp"]

# Una vez YouTube bloquea la IP para youtube_transcript_api, seguir reintentando
# esa misma vía en los vídeos siguientes es inútil (el bloqueo no se levanta en
# segundos) y solo desperdicia tiempo. Se marca a nivel de módulo y el resto de
# la ejecución de 'fetch' va directa al fallback de yt-dlp (cookies, camino
# distinto).
_transcript_api_blocked = False

# Mismo razonamiento para yt-dlp: si YouTube empieza a devolver 429 (nos ha
# pasado en tandas grandes, con o sin youtube_transcript_api ya bloqueado
# aparte), seguir intentando la rejilla completa de idiomas/tipos/cookies por
# cada vídeo siguiente son ~30s desperdiciados por vídeo sin ninguna
# posibilidad de éxito.
_ytdlp_blocked = False
_RATE_LIMIT_SIGNATURES = ("429", "too many requests")


def _video_dir(video_id: str, title: str) -> Path:
    """Directorio del vídeo: reutiliza uno ya existente para ese video_id aunque
    el título haya cambiado en YouTube desde que se descargó (algunos canales
    editan títulos), para no perder la idempotencia y volver a intentar un
    fetch innecesario (y potencialmente fallido si hay un bloqueo de IP)."""
    existing = list(config.TRANSCRIPTS_DIR.glob(f"*-{video_id}"))
    if existing:
        return existing[0]
    slug = slugify(title)[:80] or "video"
    return config.TRANSCRIPTS_DIR / f"{slug}-{video_id}"


def _fetch_via_transcript_api(video_id: str) -> Optional[tuple[str, str]]:
    """Prioridad de idioma LANG_PRIORITY. Devuelve (texto, idioma) o None si no hay es/en."""
    api = YouTubeTranscriptApi()
    available = list(api.list(video_id))

    chosen = None
    for lang in config.LANG_PRIORITY:
        for t in available:
            if t.language_code == lang or t.language_code.startswith(f"{lang}-"):
                chosen = t
                break
        if chosen:
            break

    if chosen is None:
        return None

    snippets = chosen.fetch()
    text = " ".join(s.text for s in snippets)
    return strip_sound_tags(text), chosen.language_code


def _find_sub_file(tmp_dir: Path, video_id: str) -> Optional[Path]:
    for ext in ("vtt", "srt"):
        matches = sorted(tmp_dir.glob(f"{video_id}.*.{ext}"))
        if matches:
            return matches[0]
    return None


def _fetch_via_ytdlp(video_id: str, url: str) -> Optional[tuple[str, str, str]]:
    """Prueba subs manuales y luego automáticos, en orden de LANG_PRIORITY.

    Primero SIN cookies: las cookies de Brave (aunque se descifren bien) hacen
    que YouTube devuelva 'the page needs to be reloaded' en la mayoría de
    peticiones — es más fiable no mandarlas. Solo si esa pasada entera falla
    se reintenta CON cookies, que hace falta para contenido con restricción de
    edad (a costa de arriesgarse a ese mismo error). Devuelve (texto, idioma, tipo).
    """
    global _ytdlp_blocked
    if _ytdlp_blocked:
        return None

    cookie_passes = [False, True] if config.YT_COOKIES_FROM_BROWSER else [False]
    for use_cookies in cookie_passes:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for lang in config.LANG_PRIORITY:
                for flag, sub_type in (("--write-sub", "manual"), ("--write-auto-sub", "auto")):
                    cmd = [
                        *_YTDLP_CMD, "--skip-download", flag,
                        "--sub-langs", lang, "--sub-format", "vtt/srt/best",
                    ]
                    if use_cookies:
                        cmd += ["--cookies-from-browser", config.YT_COOKIES_FROM_BROWSER]
                    cmd += ["-o", str(tmp_path / "%(id)s.%(ext)s"), url]

                    result = subprocess.run(cmd, capture_output=True, text=True)
                    found = _find_sub_file(tmp_path, video_id)
                    if found:
                        text = clean_subtitle_text(found.read_text(encoding="utf-8", errors="ignore"))
                        return strip_sound_tags(text), lang, sub_type

                    stderr_lower = (result.stderr or "").lower()
                    if any(sig in stderr_lower for sig in _RATE_LIMIT_SIGNATURES):
                        _ytdlp_blocked = True
                        logger.warning(
                            "YouTube ha empezado a devolver 429 también en yt-dlp; "
                            "el resto de esta ejecución de 'fetch' se saltará el fallback de yt-dlp"
                        )
                        return None

                    for f in tmp_path.iterdir():
                        f.unlink(missing_ok=True)
    return None


def download_transcript(video: dict) -> str:
    """Descarga la transcripción de un vídeo. Devuelve 'ok', 'skip' o 'fail'."""
    video_id = video["video_id"]
    title = video["title"] or f"video_{video_id}"
    out_dir = _video_dir(video_id, title)
    transcript_path = out_dir / "transcript.txt"

    if transcript_path.exists():
        logger.info("skip (ya existe): %s", out_dir.name)
        return "skip"

    global _transcript_api_blocked
    text = lang = source = None

    if not _transcript_api_blocked:
        try:
            result = retry_call(
                _fetch_via_transcript_api, video_id,
                max_retries=config.MAX_RETRIES, base=config.BACKOFF_BASE,
                no_retry=(RequestBlocked, AgeRestricted),
            )
            if result:
                text, lang = result
                source = "youtube_transcript_api"
        except RequestBlocked:
            _transcript_api_blocked = True
            logger.warning(
                "YouTube ha bloqueado la IP para youtube_transcript_api; "
                "el resto de esta ejecución usará solo el fallback de yt-dlp"
            )
        except Exception as exc:
            logger.warning("transcript-api falló para %s (%s): %s", video_id, title, exc)

    if text is None:
        fallback = _fetch_via_ytdlp(video_id, video["url"])
        if fallback:
            text, lang, sub_type = fallback
            source = f"yt-dlp:{sub_type}"

    if not text:
        append_line(config.NO_TRANSCRIPT_LOG, f"{video_id}\t{title}\t{video['url']}")
        logger.warning("sin transcripción: %s", title)
        return "fail"

    out_dir.mkdir(parents=True, exist_ok=True)
    transcript_path.write_text(text, encoding="utf-8")

    meta = {
        "video_id": video_id,
        "title": title,
        "url": video["url"],
        "language": lang,
        "source": source,
        "upload_date": video.get("upload_date"),
        "duration": video.get("duration"),
        "canal_nombre": video.get("canal_nombre"),
        "canal_id": video.get("canal_id"),
        "fuente_origen": video.get("fuente_origen"),
        "fuente_detalle": video.get("fuente_detalle"),
        "resuelto_por_titulo": video.get("resuelto_por_titulo", False),
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("ok [%s/%s]: %s", source, lang, title)
    return "ok"


def run(
    entries: list[str],
    list_files: Optional[list[str]] = None,
    title_channel: Optional[str] = None,
    limit: Optional[int] = None,
) -> None:
    global _transcript_api_blocked, _ytdlp_blocked
    _transcript_api_blocked = False
    _ytdlp_blocked = False

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Registro informativo de qué se pidió en esta ejecución (reannotate() lo
    # usa como pista de canal para vídeos antiguos sin procedencia propia).
    # La procedencia real de cada vídeo vive en su meta.json, no aquí.
    config.CHANNEL_FILE.write_text(
        json.dumps({"entries": entries, "list_files": list_files or []}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    videos = enumerate_sources(entries, list_files=list_files, title_channel=title_channel, limit=limit)
    logger.info("%d vídeos resueltos de %d entrada(s)", len(videos), len(entries) + len(list_files or []))

    counts = {"ok": 0, "skip": 0, "fail": 0}
    for i, video in enumerate(videos, 1):
        logger.info("[%d/%d] %s", i, len(videos), video["title"])
        result = download_transcript(video)
        counts[result] += 1
        if result != "skip":
            time.sleep(config.FETCH_DELAY)

    logger.info(
        "Paso 1 completado: %(ok)d nuevas, %(skip)d ya existían, %(fail)d sin transcripción",
        counts,
    )


_SOURCE_META_KEYS = ("canal_nombre", "canal_id", "fuente_origen", "fuente_detalle", "resuelto_por_titulo")


def reannotate(channel_hint: Optional[str] = None) -> None:
    """Rellena los campos de procedencia en los meta.json de vídeos ya
    descargados a los que les falten (procesados antes de que existiera este
    campo). No vuelve a descargar ninguna transcripción: solo reescribe
    meta.json. canal_nombre/canal_id se resuelven de verdad contra YouTube;
    fuente_origen se deja en 'canal' (es la única procedencia que pudo tener
    un vídeo descargado antes de este cambio) y fuente_detalle usa el
    'channel_hint' que le pases (p.ej. '@AdrianSaenz') — data/channel.json
    NO se usa como pista porque un 'fetch' posterior con otra fuente lo
    sobrescribe, y adivinar de ahí puede etiquetar mal vídeos antiguos."""
    counts = {"anotado": 0, "ya_tenia": 0, "fallo": 0}
    for video_dir in sorted(p for p in config.TRANSCRIPTS_DIR.iterdir() if p.is_dir()):
        meta_path = video_dir / "meta.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if all(key in meta for key in _SOURCE_META_KEYS):
            counts["ya_tenia"] += 1
            continue
        try:
            video = list_single_video(meta["video_id"])
        except Exception as exc:
            logger.warning("no se pudo re-anotar %s: %s", meta.get("video_id"), exc)
            counts["fallo"] += 1
            continue
        meta.setdefault("canal_nombre", video.get("canal_nombre"))
        meta.setdefault("canal_id", video.get("canal_id"))
        meta.setdefault("fuente_origen", "canal")
        meta.setdefault("fuente_detalle", channel_hint)
        meta.setdefault("resuelto_por_titulo", False)
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("re-anotado: %s (%s)", meta.get("title"), meta.get("canal_nombre"))
        counts["anotado"] += 1

    logger.info(
        "Re-anotado completado: %(anotado)d actualizados, %(ya_tenia)d ya tenían los campos, %(fallo)d fallos",
        counts,
    )
