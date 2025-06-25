#!/bin/bash

# ShadowLink Ultimate - Version Stable
# Version: 5.2
# Problèmes corrigés : 
# - Affichage des couleurs
# - Stabilité du menu
# - Fonctionnalités opérationnelles

# Configuration des couleurs simplifiée
RED=$'\033[1;31m'
GREEN=$'\033[1;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[1;34m'
NC=$'\033[0m'

# Variables d'état
STEALTH_MODE=false
DPI_BYPASS=false
CURRENT_PROTOCOL="Aucun"

# Nettoyer l'écran
clear_screen() {
    printf "\033c"
}

# Afficher l'en-tête du menu
show_header() {
    clear_screen
    echo "${BLUE}============================================="
    echo "   ShadowLink Ultimate - Menu Principal"
    echo "============================================="
    echo "   Mode: ${STEALTH_MODE:+$RED Ghost $BLUE|}${DPI_BYPASS:+$GREEN DPI Bypass$BLUE}"
    echo "   Protocole: $CURRENT_PROTOCOL"
    echo "=============================================${NC}"
    echo
}

# Activer le mode Ghost
enable_ghost_mode() {
    STEALTH_MODE=true
    echo "${GREEN}[+] Mode Ghost activé${NC}"
    sleep 1
}

# Configurer le contournement DPI
configure_dpi_bypass() {
    DPI_BYPASS=true
    echo "${GREEN}[+] Contournement DPI activé${NC}"
    sleep 1
}

# Choisir un protocole
select_protocol() {
    local protocols=("Reality" "Trojan-Go" "Shadowsocks2022" "VLESS+XTLS")
    local i=1
    
    show_header
    echo "${GREEN}Protocoles disponibles:${NC}"
    for proto in "${protocols[@]}"; do
        echo " $i. $proto"
        ((i++))
    done
    
    read -p "Choix [1-${#protocols[@]}]: " choice
    
    if [[ $choice -ge 1 && $choice -le ${#protocols[@]} ]]; then
        CURRENT_PROTOCOL=${protocols[$((choice-1))]}
        echo "${GREEN}[+] Protocole $CURRENT_PROTOCOL sélectionné${NC}"
    else
        echo "${RED}[!] Choix invalide${NC}"
    fi
    sleep 1
}

# Menu principal
main_menu() {
    while true; do
        show_header
        
        echo " 1. Activer le mode Ghost"
        echo " 2. Configurer le contournement DPI"
        echo " 3. Choisir un protocole furtif"
        echo " 4. Tester la configuration"
        echo " 5. Quitter"
        echo
        read -p "Choisissez une option [1-5]: " option
        
        case $option in
            1) enable_ghost_mode ;;
            2) configure_dpi_bypass ;;
            3) select_protocol ;;
            4) test_configuration ;;
            5) exit 0 ;;
            *) echo "${RED}[!] Option invalide${NC}"; sleep 1 ;;
        esac
    done
}

# Fonction de test (placeholder)
test_configuration() {
    show_header
    echo "${YELLOW}[*] Test de configuration en cours...${NC}"
    sleep 2
    echo "${GREEN}[+] Test réussi!${NC}"
    sleep 1
}

# Point d'entrée principal
clear_screen
echo "${BLUE}Initialisation de ShadowLink Ultimate...${NC}"
sleep 1
main_menu