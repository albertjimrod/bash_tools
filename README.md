# Scripts

Colección de scripts de automatización organizados por categoría.

## Estructura

```
scripts/
├── conda_tools/        # Gestión de entornos Conda
├── youtube_tools/      # Descarga de transcripciones YouTube
├── git_tools/          # Búsqueda y gestión de repos Git
├── utils/              # Utilidades varias
└── organize_with_ai/   # Organizador de archivos con IA (Ollama)
```

## Categorías

| Carpeta | Descripción | Scripts |
|---------|-------------|---------|
| [conda_tools](./conda_tools/) | Exportar, importar, comparar entornos Conda | 10 |
| [youtube_tools](./youtube_tools/) | Descargar subtítulos, crear corpus | 6 |
| [git_tools](./git_tools/) | Buscar repos, encontrar commits | 2 |
| [utils](./utils/) | Análisis texto, backups, duplicados | 6 |
| [organize_with_ai](./organize_with_ai/) | Organizar archivos con Ollama | 1 |

## Uso rápido

```bash
# Hacer ejecutable
chmod +x categoria/script.sh

# Ejecutar
./categoria/script.sh [argumentos]
```

## Requisitos generales

- Bash 4.0+
- Conda/Miniconda (para conda_tools)
- yt-dlp (para youtube_tools)
- Ollama (para organize_with_ai)

## Autor

**Alberto Jiménez** - [GitHub](https://github.com/albertjimrod)
