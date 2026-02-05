# Utils

Utilidades varias para tareas del sistema.

## Scripts

| Script | Descripción | Uso |
|--------|-------------|-----|
| `analize_text.sh` | Analiza texto con múltiples patrones usando Fabric | `./analize_text.sh <archivo> [salida.md]` |
| `backup_inventario.sh` | Crea backup de inventario con fecha | `./backup_inventario.sh` |
| `compare_files.sh` | Compara archivos por hash para encontrar duplicados | `./compare_files.sh` |
| `detect_openwebui.sh` | Detecta cómo/dónde corre OpenWebUI | `./detect_openwebui.sh` |
| `direcciones_unicas.sh` | Extrae direcciones únicas | `./direcciones_unicas.sh` |
| `user_packages.sh` | Muestra paquetes instalados manualmente con descripciones | `./user_packages.sh` |

## Requisitos

- `analize_text.sh`: Requiere [Fabric](https://github.com/danielmiessler/fabric)
- `detect_openwebui.sh`: Requiere permisos root (se auto-eleva)
