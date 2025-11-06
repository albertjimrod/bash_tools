¡Por supuesto! Aquí tienes un **README** claro, profesional y listo para usar en tu repositorio o junto al script **git-find-commit.sh**.

# git-find-commit.sh

Busca **recursivamente** en todos los repositorios Git dentro de una ruta especificada aquellos que contienen un commit con un mensaje específico.

## **¿Para qué sirve?**

Este script es útil cuando tienes **muchos repositorios Git** dispersos en tu sistema y necesitas encontrar rápidamente en cuál de ellos existe un commit con un mensaje concreto (por ejemplo, para localizar un cambio específico o un proyecto antiguo).

## **¿Cómo se usa?**

### **Sintaxis básica**

```bash
./git-find-commit.sh "mensaje del commit" [directorio_de_busqueda]
```

- **"mensaje del commit"**: El mensaje exacto (o parte de él) que quieres buscar en los commits.
- **[directorio_de_busqueda]**: (Opcional) La ruta desde donde empezar la búsqueda. Si no se especifica, se usará el directorio actual (`.`).

### **Ejemplos**

- Buscar en el directorio actual:
  ```bash
  ./git-find-commit.sh "v.0 Exploring Ebay"
  ```
- Buscar en una ruta específica:
  ```bash
  ./git-find-commit.sh "fix login bug" /home/usuario/proyectos
  ```

## **¿Cómo funciona?**

1. **Busca recursivamente** todos los directorios `.git` dentro de la ruta especificada.
2. Para cada repositorio encontrado, **verifica** si existe al menos un commit cuyo mensaje coincida con el texto proporcionado.
3. **Muestra la ruta** de cada repositorio donde se encontró el commit.

## **Requisitos**

- **Bash** (casi cualquier versión reciente de Linux/macOS lo incluye).
- **Git** instalado y accesible desde la línea de comandos.
- Permisos de **lectura** en los directorios que se van a inspeccionar.

## **Personalización**

Puedes modificar el script para que, por ejemplo, muestre información adicional del commit (hash, fecha, etc.) o para que busque coincidencias parciales (usando `--grep` sin comillas).

## **Notas**

- **Distinción de mayúsculas/minúsculas**: La búsqueda es sensible a mayúsculas y minúsculas.
- **Rendimiento**: En sistemas con muchos repositorios grandes, la búsqueda puede tardar varios segundos o minutos.
- **Seguridad**: El script solo lee información de Git, no modifica ningún repositorio.

**¿Problemas o sugerencias?**  
¡Abre un issue o contribuye al proyecto!

¿Te gustaría el README en otro formato (Markdown, texto plano, etc.)? ¿O necesitas agregar alguna sección adicional? ¡Dímelo y lo adapto!
