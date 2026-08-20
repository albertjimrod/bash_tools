"""PASO 1: descarga de transcripciones por vídeo (youtube-transcript-api, fallback a yt-dlp)."""
import json
import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

from youtube_transcript_api import YouTubeTranscriptApi

import config
from .channel import list_channel_videos
from .utils import clean_subtitle_text, retry_call, slugify, strip_sound_tags, append_line

logger = logging.getLogger(__name__)
_YTDLP_CMD = [sys.executable, "-m", "yt_dlp"]


def _video_dir(video_id: str, title: str) -> Path:
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
    """Prueba subs manuales y luego automáticos, en orden de LANG_PRIORITY. Devuelve (texto, idioma, tipo)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for lang in config.LANG_PRIORITY:
            for flag, sub_type in (("--write-sub", "manual"), ("--write-auto-sub", "auto")):
                cmd = [
                    *_YTDLP_CMD, "--skip-download", flag,
                    "--sub-langs", lang, "--sub-format", "vtt/srt/best",
                ]
                if config.YT_COOKIES_FROM_BROWSER:
                    cmd += ["--cookies-from-browser", config.YT_COOKIES_FROM_BROWSER]
                cmd += ["-o", str(tmp_path / "%(id)s.%(ext)s"), url]

                subprocess.run(cmd, capture_output=True, text=True)
                found = _find_sub_file(tmp_path, video_id)
                if found:
                    text = clean_subtitle_text(found.read_text(encoding="utf-8", errors="ignore"))
                    return strip_sound_tags(text), lang, sub_type

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

    text = lang = source = None

    try:
        result = retry_call(
            _fetch_via_transcript_api, video_id,
            max_retries=config.MAX_RETRIES, base=config.BACKOFF_BASE,
        )
        if result:
            text, lang = result
            source = "youtube_transcript_api"
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
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("ok [%s/%s]: %s", source, lang, title)
    return "ok"


def run(channel: str, limit: Optional[int] = None) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    config.CHANNEL_FILE.write_text(
        json.dumps({"channel": channel}, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    videos = list_channel_videos(channel, limit=limit)
    logger.info("canal: %d vídeos encontrados", len(videos))

    counts = {"ok": 0, "skip": 0, "fail": 0}
    for i, video in enumerate(videos, 1):
        logger.info("[%d/%d] %s", i, len(videos), video["title"])
        counts[download_transcript(video)] += 1

    logger.info(
        "Paso 1 completado: %(ok)d nuevas, %(skip)d ya existían, %(fail)d sin transcripción",
        counts,
    )
