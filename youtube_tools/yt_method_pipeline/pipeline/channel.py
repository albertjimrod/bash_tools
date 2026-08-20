"""Enumeración de los vídeos de un canal de YouTube vía yt-dlp."""
import logging
import subprocess
import sys
from typing import Optional

import config

logger = logging.getLogger(__name__)

_FIELDS = ["id", "title", "webpage_url", "upload_date", "duration"]
_YTDLP_CMD = [sys.executable, "-m", "yt_dlp"]


def resolve_channel_url(channel: str) -> str:
    channel = channel.strip()
    if channel.startswith("http"):
        return channel.split("/videos")[0].rstrip("/") + "/videos"
    handle = channel if channel.startswith("@") else f"@{channel}"
    return f"https://www.youtube.com/{handle}/videos"


def list_channel_videos(channel: str, limit: Optional[int] = None) -> list[dict]:
    url = resolve_channel_url(channel)

    cmd = [*_YTDLP_CMD, "--flat-playlist", "--skip-download"]
    if config.YT_COOKIES_FROM_BROWSER:
        cmd += ["--cookies-from-browser", config.YT_COOKIES_FROM_BROWSER]
    if limit:
        cmd += ["-I", f"1:{limit}"]
    print_fmt = "\t".join(f"%({field})s" for field in _FIELDS)
    cmd += ["--print", print_fmt, url]

    logger.info("listando vídeos de %s", url)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and not result.stdout.strip():
        raise RuntimeError(f"yt-dlp no pudo listar el canal {url}:\n{result.stderr.strip()}")

    videos = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = (line.split("\t") + [""] * len(_FIELDS))[: len(_FIELDS)]
        videos.append(
            {
                "video_id": parts[0],
                "title": parts[1],
                "url": parts[2],
                "upload_date": parts[3],
                "duration": parts[4],
            }
        )
    return videos
