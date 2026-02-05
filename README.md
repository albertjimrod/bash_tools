# Bash Tools

Colección de scripts de automatización organizados por categoría. Cada script tiene su propio directorio con README detallado.

## Estructura

```
bash_tools/
├── conda_tools/           # Gestión de entornos Conda (10 scripts)
│   ├── check_conda_package/
│   ├── conda_env_manager/
│   └── ...
├── youtube_tools/         # Transcripciones YouTube (6 scripts)
│   ├── youtube_pipeline/
│   ├── yt_channel_to_corpus/
│   └── ...
├── git_tools/             # Búsqueda repos Git (2 scripts)
│   ├── buscar_git/
│   └── git-find-commit/
├── utils/                 # Utilidades varias (6 scripts)
│   ├── compare_files/
│   └── ...
└── organize_with_ai/      # Organizador con IA (1 script)
```

## Categorías

| Carpeta | Descripción | Scripts |
|---------|-------------|---------|
| [conda_tools](./conda_tools/) | Exportar, importar, comparar entornos Conda | 10 |
| [youtube_tools](./youtube_tools/) | Descargar subtítulos, crear corpus | 6 |
| [git_tools](./git_tools/) | Buscar repos, encontrar commits | 2 |
| [utils](./utils/) | Análisis texto, backups, duplicados | 6 |
| [organize_with_ai](./organize_with_ai/) | Organizar archivos con Ollama | 1 |

## Uso

```bash
# Navegar al script deseado
cd conda_tools/conda_env_manager/

# Ver documentación
cat README.md

# Ejecutar
chmod +x conda_env_manager.sh
./conda_env_manager.sh
```

## Requisitos generales

- Bash 4.0+
- Conda/Miniconda (para conda_tools)
- yt-dlp (para youtube_tools)
- Ollama (para organize_with_ai)

## Autor

**Alberto Jiménez** - [GitHub](https://github.com/albertjimrod)
