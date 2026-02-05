# WordPress Publisher

Publicador automático de artículos en WordPress con gestión de fechas y tags.

## Funcionalidades

- Publica archivos `.md` y `.txt` via REST API
- Modifica fechas de publicación (espaciado automático)
- Detecta y crea tags automáticamente
- Evita duplicados
- Modo espera para generación continua (GPU/IA)

## Requisitos

```bash
pip install requests python-dotenv
```

## Configuración

1. Crea archivo `.env` en el mismo directorio:

```env
WP_URL=https://tu-dominio.com/wp-json/wp/v2/posts
WP_TAGS_URL=https://tu-dominio.com/wp-json/wp/v2/tags
WP_USER=tu_usuario
WP_PASSWORD=xxxx xxxx xxxx xxxx
ARTICULOS_DIR=/ruta/absoluta/a/articulos
```

2. Genera **contraseña de aplicación** en WordPress:
   - WordPress Admin → Usuarios → Perfil → Contraseñas de aplicación

## Uso

```bash
# Publicar nuevos + actualizar fechas
python3 wordpress_publisher.py

# Solo actualizar fechas de posts existentes
python3 wordpress_publisher.py update_dates

# Modo espera (para generación continua)
python3 wordpress_publisher.py wait

# Ayuda
python3 wordpress_publisher.py help
```

## Funcionamiento de fechas

- Fecha base: hace 2 años desde hoy
- Incremento: +2 días por cada artículo
- Resultado: posts espaciados uniformemente

## Tags automáticos

| Tag | Keywords detectados |
|-----|---------------------|
| data | data, dataset, database, sql, csv, json |
| linux | linux, bash, shell, command, terminal |
| pandas | pandas, dataframe, series, groupby |
| python | python, django, flask, pip |
| machine-learning | machine learning, model, training |
| deep-learning | tensorflow, keras, pytorch |

## Solución de problemas

| Error | Solución |
|-------|----------|
| "Faltan variables de entorno" | Verifica que `.env` existe y tiene todas las variables |
| "401 Unauthorized" | Usa contraseña de aplicación, no la normal |
| "Directorio no existe" | Usa ruta absoluta `/home/...` no `~/` |

## Seguridad

- Nunca subas `.env` a Git
- Usa contraseñas de aplicación
- Rota credenciales regularmente
