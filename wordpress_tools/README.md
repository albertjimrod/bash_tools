# WordPress Tools

Herramientas para automatizar publicación de contenido en WordPress.

## Scripts disponibles

| Directorio | Descripción |
|------------|-------------|
| [wordpress_publisher](./wordpress_publisher/) | Publica artículos via REST API con gestión de fechas |
| [generar_articulos](./generar_articulos/) | Genera artículos con Ollama (DeepSeek-R1) |

## Flujo de trabajo típico

```
1. Notas en Markdown (.md)
        ↓
2. generar_articulos/ → Artículos profesionales
        ↓
3. wordpress_publisher/ → Publicados en WordPress
```

## Requisitos

- Python 3.7+
- Ollama (para generar_articulos)
- WordPress con REST API habilitado

```bash
pip install requests python-dotenv
```
