"""Enumeración de vídeos a procesar, vía yt-dlp, a partir de entradas mixtas:
canal, playlist, vídeo suelto, fichero de lista o búsqueda por título.

Cada entrada se resuelve SIN descargar (--flat-playlist/--skip-download) a un
dict con el vídeo (id, título, url...) y su procedencia (fuente_origen,
fuente_detalle, canal_nombre/canal_id reales del vídeo, resuelto_por_titulo).
enumerate_sources() combina varias entradas y deduplica por video_id.
"""
import logging
import re
import subprocess
import sys
from typing import Optional

import config

logger = logging.getLogger(__name__)

_FIELDS = ["id", "title", "webpage_url", "upload_date", "duration"]
# Campos adicionales para poder rellenar canal_nombre/canal_id (el canal REAL
# del vídeo, no la fuente por la que llegó al corpus). En un listado de canal,
# el canal/channel_id por-entrada vuelve "NA" (no se resuelve en modo flat),
# así que ahí se usan los campos a nivel de listado (playlist_channel*), que
# sí corresponden al canal que se está enumerando. En una playlist o una
# búsqueda, channel/channel_id sí vienen resueltos por entrada (comprobado
# en vivo con yt-dlp) y pueden variar vídeo a vídeo.
_SOURCE_FIELDS = _FIELDS + ["channel", "channel_id", "playlist_channel", "playlist_channel_id"]
_YTDLP_CMD = [sys.executable, "-m", "yt_dlp"]
_TITLE_PREFIX = "titulo:"


def resolve_channel_url(channel: str) -> str:
    channel = channel.strip()
    if channel.startswith("http"):
        return channel.split("/videos")[0].rstrip("/") + "/videos"
    handle = channel if channel.startswith("@") else f"@{channel}"
    return f"https://www.youtube.com/{handle}/videos"


def detect_entry_kind(entry: str) -> str:
    """Clasifica una entrada de línea de comandos: 'titulo', 'playlist',
    'video' o 'canal' (por defecto si no encaja con las otras formas)."""
    e = entry.strip()
    if e.lower().startswith(_TITLE_PREFIX):
        return "titulo"
    if "list=" in e or "/playlist" in e:
        return "playlist"
    if "youtube.com/watch" in e or "youtu.be/" in e or re.fullmatch(r"[A-Za-z0-9_-]{11}", e):
        return "video"
    return "canal"


def _none_if_na(value: str) -> Optional[str]:
    return value if value and value != "NA" else None


def _run_ytdlp_print(cmd_extra: list[str], fields: list[str]) -> list[dict]:
    print_fmt = "\t".join(f"%({field})s" for field in fields)

    # Igual que en transcripts._fetch_via_ytdlp: probar SIN cookies primero.
    # Las cookies del navegador (Brave, aquí) provocan sistemáticamente "the
    # page needs to be reloaded" en bastantes peticiones; solo se usan como
    # último recurso, no por defecto.
    cookie_passes = [False, True] if config.YT_COOKIES_FROM_BROWSER else [False]
    result = None
    for use_cookies in cookie_passes:
        cmd = [*_YTDLP_CMD, "--skip-download"]
        if use_cookies:
            cmd += ["--cookies-from-browser", config.YT_COOKIES_FROM_BROWSER]
        cmd += ["--print", print_fmt, *cmd_extra]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout.strip():
            break

    if result.returncode != 0 and not result.stdout.strip():
        raise RuntimeError(f"yt-dlp falló ({' '.join(cmd_extra)}):\n{result.stderr.strip()}")

    rows = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = (line.split("\t") + [""] * len(fields))[: len(fields)]
        rows.append(dict(zip(fields, parts)))
    return rows


def _row_to_video(row: dict) -> dict:
    canal_nombre = _none_if_na(row.get("channel", "")) or _none_if_na(row.get("playlist_channel", ""))
    canal_id = _none_if_na(row.get("channel_id", "")) or _none_if_na(row.get("playlist_channel_id", ""))
    return {
        "video_id": row["id"],
        "title": row["title"],
        "url": row["webpage_url"],
        "upload_date": _none_if_na(row.get("upload_date", "")),
        "duration": _none_if_na(row.get("duration", "")),
        "canal_nombre": canal_nombre,
        "canal_id": canal_id,
    }


def list_channel_videos(channel: str, limit: Optional[int] = None) -> list[dict]:
    url = resolve_channel_url(channel)

    print_fmt = "\t".join(f"%({field})s" for field in _SOURCE_FIELDS)
    logger.info("listando vídeos de %s", url)

    cookie_passes = [False, True] if config.YT_COOKIES_FROM_BROWSER else [False]
    result = None
    for use_cookies in cookie_passes:
        cmd = [*_YTDLP_CMD, "--flat-playlist", "--skip-download"]
        if use_cookies:
            cmd += ["--cookies-from-browser", config.YT_COOKIES_FROM_BROWSER]
        if limit:
            cmd += ["-I", f"1:{limit}"]
        cmd += ["--print", print_fmt, url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout.strip():
            break

    if result.returncode != 0 and not result.stdout.strip():
        raise RuntimeError(f"yt-dlp no pudo listar el canal {url}:\n{result.stderr.strip()}")

    videos = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = (line.split("\t") + [""] * len(_SOURCE_FIELDS))[: len(_SOURCE_FIELDS)]
        row = dict(zip(_SOURCE_FIELDS, parts))
        videos.append(_row_to_video(row))
    return videos


def list_playlist_videos(playlist_url: str) -> list[dict]:
    """El canal real de cada vídeo puede variar de uno a otro dentro de la
    misma playlist (playlists con vídeos de varios canales), así que se lee
    canal/channel_id por entrada, no del conjunto de la playlist."""
    logger.info("listando playlist %s", playlist_url)
    rows = _run_ytdlp_print(["--flat-playlist", playlist_url], _SOURCE_FIELDS)
    return [_row_to_video(r) for r in rows]


def list_single_video(url_or_id: str) -> dict:
    url = url_or_id if url_or_id.startswith("http") else f"https://www.youtube.com/watch?v={url_or_id}"
    logger.info("resolviendo vídeo suelto %s", url)
    # --flat-playlist también en un vídeo suelto: evita que yt-dlp intente
    # resolver firmas de formato de descarga (innecesario con --skip-download)
    # y que falle por eso incluso teniendo toda la metadata que necesitamos.
    rows = _run_ytdlp_print(["--flat-playlist", url], _SOURCE_FIELDS)
    if not rows:
        raise RuntimeError(f"yt-dlp no devolvió metadatos para {url}")
    return _row_to_video(rows[0])


def list_file_videos(path: str) -> list[dict]:
    """Usa el soporte nativo de yt-dlp para ficheros de lista (-a): ignora
    líneas vacías y las que empiezan por '#' sin que haya que filtrarlas."""
    logger.info("listando fichero de lista %s", path)
    rows = _run_ytdlp_print(["--flat-playlist", "-a", path], _SOURCE_FIELDS)
    return [_row_to_video(r) for r in rows]


def search_by_title(query: str, title_channel: Optional[str] = None, n: int = 5) -> Optional[dict]:
    """Busca por título con yt-dlp (ytsearchN:). Si se da title_channel,
    prefiere entre los N primeros resultados el que coincida con ese canal
    (por nombre o channel_id) para reducir falsos positivos; si ninguno
    coincide, se queda con el primer resultado (equivalente a ytsearch1)."""
    logger.info("buscando por título: %r (canal=%s)", query, title_channel)
    rows = _run_ytdlp_print(["--flat-playlist", f"ytsearch{n}:{query}"], _SOURCE_FIELDS)
    if not rows:
        return None
    videos = [_row_to_video(r) for r in rows]
    if title_channel:
        needle = title_channel.strip().lstrip("@").lower()
        for v in videos:
            nombre = (v.get("canal_nombre") or "").lower()
            cid = (v.get("canal_id") or "").lower()
            if needle and (needle in nombre or needle == cid):
                return v
    return videos[0]


def _resolve_canal(entry: str, limit: Optional[int]) -> list[dict]:
    videos = list_channel_videos(entry, limit=limit)
    for v in videos:
        v["fuente_origen"] = "canal"
        v["fuente_detalle"] = entry
        v["resuelto_por_titulo"] = False
    return videos


def _resolve_playlist(entry: str) -> list[dict]:
    videos = list_playlist_videos(entry)
    for v in videos:
        v["fuente_origen"] = "playlist"
        v["fuente_detalle"] = entry
        v["resuelto_por_titulo"] = False
    return videos


def _resolve_video(entry: str) -> list[dict]:
    video = list_single_video(entry)
    video["fuente_origen"] = "video"
    video["fuente_detalle"] = entry
    video["resuelto_por_titulo"] = False
    return [video]


def _resolve_lista_fichero(path: str) -> list[dict]:
    videos = list_file_videos(path)
    for v in videos:
        v["fuente_origen"] = "lista_fichero"
        v["fuente_detalle"] = path
        v["resuelto_por_titulo"] = False
    return videos


def _resolve_titulo(query: str, title_channel: Optional[str]) -> list[dict]:
    video = search_by_title(query, title_channel=title_channel)
    if video is None:
        raise RuntimeError(f"la búsqueda por título no devolvió resultados: {query!r}")
    video["fuente_origen"] = "busqueda_titulo"
    video["fuente_detalle"] = query
    video["resuelto_por_titulo"] = True
    return [video]


def enumerate_sources(
    entries: list[str],
    list_files: Optional[list[str]] = None,
    title_channel: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[dict]:
    """Resuelve entradas mixtas (canal/playlist/vídeo/'titulo:...') más
    ficheros de lista, deduplica por video_id (se queda con la primera
    procedencia con la que llegó) y devuelve la lista unificada de vídeos.
    Una entrada que falle (p.ej. una búsqueda por título sin resultados) se
    registra y no interrumpe la resolución del resto."""
    resolved: list[dict] = []
    seen_ids: set[str] = set()

    def _add(videos: list[dict]) -> None:
        for v in videos:
            vid = v.get("video_id")
            if not vid or vid in seen_ids:
                continue
            seen_ids.add(vid)
            resolved.append(v)

    for entry in entries:
        kind = detect_entry_kind(entry)
        try:
            if kind == "canal":
                _add(_resolve_canal(entry, limit))
            elif kind == "playlist":
                _add(_resolve_playlist(entry))
            elif kind == "video":
                _add(_resolve_video(entry))
            else:
                _add(_resolve_titulo(entry[len(_TITLE_PREFIX):].strip(), title_channel))
        except Exception as exc:
            logger.warning("no se pudo resolver la entrada %r: %s", entry, exc)

    for path in list_files or []:
        try:
            _add(_resolve_lista_fichero(path))
        except Exception as exc:
            logger.warning("no se pudo resolver el fichero de lista %r: %s", path, exc)

    return resolved
