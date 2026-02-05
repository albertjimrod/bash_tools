# Git Tools

Herramientas para búsqueda y gestión de repositorios Git.

## Scripts

| Script | Descripción | Uso |
|--------|-------------|-----|
| `buscar_git.sh` | Busca directorios que contengan repos Git | `./buscar_git.sh [directorio_base]` |
| `git-find-commit.sh` | Busca un commit específico en múltiples repos | `./git-find-commit.sh` |

## Ejemplo

```bash
# Buscar todos los repos Git en home
./buscar_git.sh ~

# Buscar repos en directorio actual
./buscar_git.sh .
```
