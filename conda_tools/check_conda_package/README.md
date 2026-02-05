# check_conda_package

Busca un paquete específico en todos los entornos Conda instalados.

## Descripción

Este script itera sobre todos los entornos Conda del sistema y verifica si un paquete específico está instalado en cada uno de ellos.

## Uso

```bash
./check_conda_package.sh
```

El script preguntará interactivamente qué paquete buscar.

## Ejemplo

```
$ ./check_conda_package.sh
¿Qué paquete de Conda estás buscando? pandas
Verificando en el entorno: base
✅ pandas está instalado en el entorno base
Verificando en el entorno: ml_env
❌ pandas no está instalado en el entorno ml_env
```

## Funciones del código

| Línea | Función |
|-------|---------|
| 4 | `eval "$(conda shell.bash hook)"` - Inicializa Conda en el contexto del script |
| 7 | `read -p` - Solicita al usuario el nombre del paquete |
| 10 | `conda info --envs` - Obtiene lista de entornos, filtra con `awk` |
| 19 | `conda activate` - Activa cada entorno para inspeccionar |
| 26 | `conda list` + `grep` - Busca el paquete en el entorno activo |

## Modificaciones sugeridas

### Cambiar a modo no interactivo
```bash
# Línea 7: cambiar de
read -p "¿Qué paquete de Conda estás buscando? " busco
# a
busco="${1:-pandas}"  # Acepta argumento o usa default
```

### Añadir salida en formato CSV
```bash
# Después de línea 26, añadir:
echo "$env,$busco,$?" >> resultados.csv
```

### Filtrar entornos específicos
```bash
# Línea 10: cambiar de
envs=$(conda info --envs | awk 'NR > 2 {print $1}')
# a
envs=$(conda info --envs | awk 'NR > 2 {print $1}' | grep -E "^(ml_|data_)")
```

## Requisitos

- Conda/Miniconda instalado
- Bash 4.0+

## Autor

Alberto Jiménez - [GitHub](https://github.com/albertjimrod)
