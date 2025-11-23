#!/bin/bash
# Script para executar a CLI do Sistema de Proteção PETROBRAS

# Cores
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🔌 Iniciando Sistema de Proteção PETROBRAS...${NC}"

# Ativar ambiente virtual
source /Volumes/Mac_XIII/virtualenvs/rele_prot/bin/activate

# Executar CLI
python src/python/cli_interface.py

echo -e "\n${GREEN}✓ Sistema encerrado${NC}\n"
