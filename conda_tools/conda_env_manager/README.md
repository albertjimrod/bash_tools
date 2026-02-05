# conda_env_manager

Gestor avanzado de entornos Conda v2.0 con interfaz interactiva.

## Descripción

Herramienta completa para gestionar entornos Conda: listar, comparar, exportar, importar y analizar paquetes instalados con descripciones detalladas.

## Uso

```bash
./conda_env_manager.sh
```

Se abre un menú interactivo con todas las opciones.

## Características

- Listado de entornos con estadísticas
- Comparación de paquetes entre entornos
- Exportación/importación de entornos
- Descripciones de paquetes comunes
- Comandos de instalación sugeridos
- Interfaz con colores

## Funciones principales

| Función | Descripción |
|---------|-------------|
| `init_conda()` | Inicializa Conda en el script |
| `get_package_description()` | Devuelve descripción de paquetes conocidos |
| `get_install_command()` | Genera comando de instalación (conda/pip) |
| `get_env_info()` | Obtiene información de un entorno |

## Variables globales

```bash
declare -A env_packages   # Almacena paquetes por entorno
declare -A env_versions   # Almacena versiones: env:package -> version
declare -A env_info       # Info del entorno: ruta, tamaño, fecha
```

## Modificaciones sugeridas

### Añadir nuevo paquete con descripción
```bash
# En get_package_description(), añadir:
"mi_paquete") echo "Mi descripción personalizada" ;;
```

### Cambiar colores
```bash
# Modificar variables al inicio:
RED='\033[0;31m'    # Rojo
GREEN='\033[0;32m'  # Verde
# ...
```

### Exportar a formato específico
```bash
# Modificar función de exportación para usar:
conda env export --no-builds > environment.yml
```

## Requisitos

- Conda/Miniconda
- Bash 4.0+ (por `declare -A`)

## Autor

Alberto Jiménez - [GitHub](https://github.com/albertjimrod)
