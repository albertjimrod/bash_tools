#!/bin/bash

# Script de demostración del Conda Environment Manager

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     DEMOSTRACIÓN - CONDA ENVIRONMENT MANAGER v2.0          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar que conda esté disponible
if ! command -v conda &> /dev/null; then
    echo -e "${RED}❌ Error: Conda no está instalado o no está en PATH${NC}"
    echo -e "${YELLOW}Instala Miniconda o Anaconda antes de usar este script${NC}"
    exit 1
fi

echo -e "\n${GREEN}✓ Conda encontrado: $(conda --version)${NC}"

# Verificar que el script principal existe
if [ ! -f "conda_env_manager.sh" ]; then
    echo -e "${RED}❌ Error: conda_env_manager.sh no encontrado${NC}"
    echo -e "${YELLOW}Asegúrate de estar en el directorio correcto${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Script principal encontrado${NC}"

# Hacer ejecutable
chmod +x conda_env_manager.sh
chmod +x install_manager.sh

echo -e "\n${BLUE}═════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Opciones de demostración:${NC}"
echo -e "${NC}"
echo "1. 📋 Instalar gestor en \$HOME/.local/bin"
echo "2. 🚀 Ejecutar gestor directamente"
echo "3. 📚 Ver manual completo"
echo "4. 📄 Ver archivos de ejemplo"
echo "5. ✅ Verificar requisitos del sistema"
echo "0. ❌ Salir"
echo ""

read -p "Selecciona opción (0-5): " choice

case $choice in
    1)
        echo -e "\n${BLUE}Instalando en \$HOME/.local/bin...${NC}"
        bash install_manager.sh ~/.local/bin
        echo -e "\n${YELLOW}📌 Añade a tu PATH:${NC}"
        echo -e "${GREEN}export PATH=\"\$PATH:\$HOME/.local/bin\"${NC}"
        ;;
    2)
        echo -e "\n${BLUE}Ejecutando gestor...${NC}"
        bash conda_env_manager.sh
        ;;
    3)
        echo -e "\n${BLUE}Abriendo manual...${NC}"
        if command -v less &> /dev/null; then
            less MANUAL_COMPLETO.md
        else
            cat MANUAL_COMPLETO.md
        fi
        ;;
    4)
        echo -e "\n${BLUE}Archivos de ejemplo disponibles:${NC}\n"
        
        echo -e "${CYAN}1. requirements_example.txt${NC}"
        echo "   Formato pip para validar requerimientos"
        echo ""
        
        echo -e "${CYAN}2. environment_example.yml${NC}"
        echo "   Formato conda para crear nuevos entornos"
        echo ""
        
        read -p "¿Ver archivo? (1/2/0): " file_choice
        
        case $file_choice in
            1)
                echo -e "\n${BLUE}═══ requirements_example.txt ═══${NC}\n"
                cat requirements_example.txt | head -30
                ;;
            2)
                echo -e "\n${BLUE}═══ environment_example.yml ═══${NC}\n"
                cat environment_example.yml | head -30
                ;;
            0) ;;
            *) echo -e "${RED}Opción inválida${NC}" ;;
        esac
        ;;
    5)
        echo -e "\n${BLUE}Verificando requisitos del sistema...${NC}\n"
        
        # Conda
        if command -v conda &> /dev/null; then
            echo -e "${GREEN}✓${NC} Conda: $(conda --version)"
        else
            echo -e "${RED}✗${NC} Conda: No encontrado"
        fi
        
        # Python
        if command -v python3 &> /dev/null; then
            echo -e "${GREEN}✓${NC} Python: $(python3 --version)"
        else
            echo -e "${RED}✗${NC} Python: No encontrado"
        fi
        
        # Bash
        if [ -n "$BASH_VERSION" ]; then
            echo -e "${GREEN}✓${NC} Bash: version $BASH_VERSION"
        else
            echo -e "${RED}✗${NC} Bash: No encontrado"
        fi
        
        # grep
        if command -v grep &> /dev/null; then
            echo -e "${GREEN}✓${NC} grep: Encontrado"
        else
            echo -e "${RED}✗${NC} grep: No encontrado"
        fi
        
        # awk
        if command -v awk &> /dev/null; then
            echo -e "${GREEN}✓${NC} awk: Encontrado"
        else
            echo -e "${RED}✗${NC} awk: No encontrado"
        fi
        
        # sort
        if command -v sort &> /dev/null; then
            echo -e "${GREEN}✓${NC} sort: Encontrado"
        else
            echo -e "${RED}✗${NC} sort: No encontrado"
        fi
        
        echo ""
        echo -e "${CYAN}Entornos Conda disponibles:${NC}"
        conda info --envs | tail -n +2
        ;;
    0)
        echo -e "\n${GREEN}¡Hasta luego!${NC}\n"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Opción inválida${NC}"
        exit 1
        ;;
esac

echo ""
