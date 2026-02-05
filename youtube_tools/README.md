# YouTube Tools

Herramientas para descargar transcripciones de YouTube y crear corpus de texto.

## Scripts

| Script | Descripción | Uso |
|--------|-------------|-----|
| `youtube_pipeline.sh` | Pipeline completo: canal → transcripciones → corpus | `./youtube_pipeline.sh <URL_CANAL> [LANG] [PART_SIZE]` |
| `full_pipeline.sh` | Pipeline alternativo con más opciones | `./full_pipeline.sh <URL_CANAL> [LANG] [PART_SIZE]` |
| `yt_channel_to_corpus.sh` | Extrae subtítulos de canal y genera corpus MD | `./yt_channel_to_corpus.sh <URL>` |
| `yt_simple_v2.sh` | Descarga subtítulos desde lista de URLs | `./yt_simple_v2.sh <urls.txt> <dir_salida>` |
| `make_corpus.sh` | Crea corpus Markdown desde archivos de texto | `./make_corpus.sh` |
| `debug_video.sh` | Prueba descarga de subtítulos para un vídeo | `./debug_video.sh <URL> [LANG]` |

## Requisitos

```bash
pip install -U yt-dlp
```

## Ejemplo

```bash
# Descargar transcripciones de un canal
./youtube_pipeline.sh "https://www.youtube.com/@canal/videos" es

# Crear corpus desde archivos descargados
./make_corpus.sh
```
