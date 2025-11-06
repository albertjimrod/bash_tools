#!/bin/bash
commit_msg="$1"
search_dir="${2:-.}"  # Usa el directorio actual si no se especifica

find "$search_dir" -type d -name ".git" -exec sh -c '
  cd "$(dirname "{}")"
  if git log --grep="$0" --oneline | grep -q .; then
    echo "Commit encontrado en: $(pwd)"
  fi
' "$commit_msg" \;

