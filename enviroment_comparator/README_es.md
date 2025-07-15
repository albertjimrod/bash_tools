# 🐍 Comparador de Entornos Conda  
Una herramienta avanzada de línea de comandos en Bash para comparar paquetes instalados entre diferentes entornos de Conda, con descripciones detalladas y comandos de instalación integrados.

![Bash](https://img.shields.io/badge/bash-4.0+-green.svg)  
![Python](https://img.shields.io/badge/python-3.6+-blue.svg)  
![License](https://img.shields.io/badge/license-MIT-blue.svg)  
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20WSL-lightgrey.svg)

---

## 📋 Tabla de Contenidos
- [¿Qué es?](#qué-es)
- [¿Para qué sirve?](#para-qué-sirve)
- [Características principales](#características-principales)
- [Requisitos](#requisitos)
- [Cómo usarlo](#cómo-usarlo)
- [Ejemplos de uso](#ejemplos-de-uso)
- [Formatos de salida](#formatos-de-salida)
- [Licencia](#licencia)

---

## ¿Qué es?

`conda-comparator.sh` es un script en Bash diseñado para ayudarte a comparar los paquetes instalados en múltiples entornos de Conda. Muestra una **matriz visual** que indica qué paquetes están presentes o ausentes en cada entorno, junto con descripciones y comandos de instalación útiles.

!()[comparador_entornos.png]

---

## ¿Para qué sirve?

Este script es ideal cuando tienes varios entornos de desarrollo y quieres:
- Comparar fácilmente qué paquetes están instalados.
- Identificar inconsistencias entre entornos.
- Exportar resultados para auditorías, migraciones o documentación.
- Encontrar rápidamente comandos de instalación específicos por paquete.

---

## Características principales

- 🔍 **Análisis automático** de todos los entornos Conda disponibles.
- 📊 **Matriz visual** mostrando la presencia/ausencia de paquetes por entorno.
- 📚 **Base de datos integrada** con descripciones de más de 60 paquetes populares.
- 🛠️ **Comandos de instalación específicos** para cada paquete.
- 📁 **Exportación CSV** con información completa (descripción, comando e instalación por entorno).
- 🎨 **Interfaz colorizada** para mejor legibilidad en terminal.
- 📈 Estadísticas y consejos contextuales durante la ejecución.

---

## Requisitos

- **Conda/Miniconda/Anaconda** instalado y configurado.
- **Bash** 4.0 o superior.
- **Python 3.6+** (requerido para procesamiento JSON).
- Sistema operativo: Linux, macOS o WSL en Windows.

---

## Cómo usarlo

### Descarga y preparación
```bash
# Descargar el script
curl -O https://raw.githubusercontent.com/tu-usuario/conda-env-comparator/main/comparador_entornos.sh
# Dar permisos de ejecución
chmod +x comparador_entornos.sh
```

### Ejecutar análisis básico
```bash
./comparador_entornos.sh
```

### Ver detalles con descripciones
```bash
./comparador_entornos.sh -d
```

### Exportar resultados a CSV
```bash
./comparador_entornos.sh -o analisis.csv
```

### Ver ayuda completa
```bash
./comparador_entornos.sh --help
```

---

## Ejemplos de Uso

| Propósito | Comando |
|----------|---------|
| Análisis rápido | `./comparador_entornos.sh` |
| Análisis detallado | `./comparador_entornos.sh -d` |
| Exportar a CSV | `./comparador_entornos.sh -o reporte.csv` |
| Análisis completo | `./comparador_entornos.sh -v -d -o completo.csv` |

---

## Formatos de Salida

### Consola
- **Modo estándar:** Matriz compacta sin descripciones.
- **Modo detallado (-d):** Incluye descripción y comando de instalación.

### Archivo CSV
- Siempre incluye:
  - Nombre del paquete
  - Descripción
  - Comando de instalación
  - Estado por entorno (`✅` / `❌`)

---

## Licencia

Este proyecto está bajo la **Licencia MIT**.  
Verifica el archivo [LICENSE](LICENSE) para más detalles.

---

## ¡Contribuye!
Las contribuciones son bienvenidas: desde añadir nuevos paquetes a la base de datos hasta mejorar el diseño del script.  
👉 [Ver Contributing Guidelines](#contribución)

---

## Autor

Desarrollado con ❤️ para la comunidad de **Data Science** y **Python**.  
¿Te ha sido útil? ¡Considera darle una ⭐ al repositorio!

---

## Contacto

- **Email:** albert@datablogcafe.com


---

<div align="center">
**🚀 ¡Optimiza tu flujo de trabajo con Conda Environment Comparator! 🚀**
</div>
```


