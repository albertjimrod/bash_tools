# Generador de Artículos con IA

Transforma notas técnicas en artículos profesionales usando Ollama (DeepSeek-R1:14b).

## Funcionalidades

- Procesa archivos `.md` recursivamente
- Genera artículos de 1200-1500 palabras
- Estructura profesional (intro, ejemplos, troubleshooting, conclusión)
- Optimizado para DeepSeek-R1:14b

## Requisitos

- Ollama instalado y ejecutándose
- Modelo DeepSeek-R1:14b descargado

```bash
# Instalar Ollama (si no lo tienes)
curl -fsSL https://ollama.com/install.sh | sh

# Descargar modelo
ollama pull deepseek-r1:14b
```

## Uso

```bash
python3 generar_articulos_mejorado.py DIRECTORIO_ENTRADA/
```

### Ejemplo

```bash
# Procesar notas en carpeta joplin_md/
python3 generar_articulos_mejorado.py joplin_md/

# Resultado: joplin_md_procesado/
```

## Variables de entorno (opcionales)

```bash
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="deepseek-r1:14b"
```

## Estructura de salida

```
entrada/
├── tema1/nota.md
└── tema2/otra_nota.md

entrada_procesado/           # Generado automáticamente
├── tema1/nota_articulo.md
└── tema2/otra_nota_articulo.md
```

## Formato del artículo generado

1. Título y subtítulo
2. Introducción (150-200 palabras)
3. Conceptos básicos
4. Sección práctica con ejemplos
5. Pro Tips (mínimo 5)
6. Troubleshooting (errores comunes)
7. Resumen y próximos pasos

## Combinación con WordPress Publisher

```bash
# Terminal 1: Generar artículos
python3 generar_articulos_mejorado.py notas/

# Terminal 2: Publicar automáticamente
cd ../wordpress_publisher/
python3 wordpress_publisher.py wait
```

## Rendimiento

- ~2-5 minutos por artículo (depende de GPU)
- Usa GPU si está disponible
- Procesa en secuencia para evitar sobrecarga
