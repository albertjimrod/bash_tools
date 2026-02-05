#!/bin/bash
DEST=~/inventario_$(date +%Y%m%d)
mkdir -p $DEST/{apt,python,conda,services,runtimes}

apt-mark showmanual > $DEST/apt/apt_manual.txt
comm -23 <(apt-mark showmanual | sort) <(gzip -dc /var/log/installer/initial-status.gz 2>/dev/null | sed -n 's/^Package: //p' | sort) > $DEST/apt/apt_personal.txt 2>/dev/null || echo "No disponible initial-status.gz" > $DEST/apt/apt_personal.txt

conda env list > $DEST/conda/envs.txt 2>/dev/null && for env in $(conda env list 2>/dev/null | grep -v "^#" | grep -v "^base" | awk '{print $1}'); do conda env export -n $env > $DEST/conda/${env}.yml 2>/dev/null; done

pip list --user > $DEST/python/pip_user.txt 2>/dev/null
systemctl list-unit-files --type=service | grep enabled > $DEST/services/systemd.txt

which docker && { docker --version > $DEST/services/docker_version.txt; docker images --format "{{.Repository}}:{{.Tag}}" > $DEST/services/docker_images.txt; }
which snap && snap list > $DEST/runtimes/snap.txt
which flatpak && flatpak list > $DEST/runtimes/flatpak.txt

echo "✅ Inventario guardado en $DEST"
tar -czf $DEST.tar.gz $DEST && echo "📦 Archivo comprimido: $DEST.tar.gz"
