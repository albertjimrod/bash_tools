#!/bin/bash

# Script de instalación del Conda Environment Manager

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     INSTALADOR - CONDA ENVIRONMENT MANAGER v2.0           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Obtener ruta de instalación
INSTALL_DIR="${1:-.local/bin}"
SCRIPT_NAME="conda-env-manager"

echo -e "\n${BLUE}Configuración de instalación:${NC}"
echo "Directorio de instalación: $INSTALL_DIR"
echo "Nombre del comando: $SCRIPT_NAME"

# Crear directorio si no existe
mkdir -p "$INSTALL_DIR"

# Copiar el script
echo -e "\n${BLUE}📋 Instalando script...${NC}"
cp conda_env_manager.sh "$INSTALL_DIR/$SCRIPT_NAME"
chmod +x "$INSTALL_DIR/$SCRIPT_NAME"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Script instalado correctamente${NC}"
else
    echo -e "${RED}❌ Error al instalar el script${NC}"
    exit 1
fi

# Verificar si el directorio está en PATH
if [[ ":$PATH:" == *":$INSTALL_DIR:"* ]]; then
    echo -e "${GREEN}✓ El directorio está en PATH${NC}"
else
    echo -e "${YELLOW}⚠️  El directorio no está en PATH${NC}"
    echo -e "\n${CYAN}Para agregar a PATH, ejecuta:${NC}"
    echo -e "  ${GREEN}export PATH=\"\$PATH:$INSTALL_DIR\"${NC}"
    echo -e "\n${CYAN}O para hacerlo permanente, agrega esta línea a ~/.bashrc:${NC}"
    echo -e "  ${GREEN}export PATH=\"\$PATH:$INSTALL_DIR\"${NC}"
fi

echo -e "\n${GREEN}═════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✨ ¡Instalación completada!${NC}"
echo -e "${GREEN}═════════════════════════════════════════════════════${NC}"

echo -e "\n${BLUE}Para usar el gestor:${NC}"
echo -e "  ${GREEN}$INSTALL_DIR/$SCRIPT_NAME${NC}"
echo -e "\n${BLUE}O simplemente (si está en PATH):${NC}"
echo -e "  ${GREEN}$SCRIPT_NAME${NC}"

echo ""
