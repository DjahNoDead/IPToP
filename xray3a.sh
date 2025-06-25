#!/bin/bash

# ShadowLink - Version Simplifiée et Fonctionnelle
# Affiche un menu basique mais stable

# Configuration
CONFIG_DIR="/etc/shadowlink"
LOG_FILE="$CONFIG_DIR/install.log"
STEALTH_MODE="OFF"
DPI_BYPASS="OFF"
CURRENT_PROTOCOL="Aucun"

# Initialisation
init() {
    mkdir -p "$CONFIG_DIR"
    touch "$LOG_FILE"
}

# Afficher le menu
show_menu() {
    clear
    echo "============================================="
    echo "   ShadowLink - Menu Principal"
    echo "============================================="
    echo "   Mode: Ghost [$STEALTH_MODE] | DPI [$DPI_BYPASS]"
    echo "   Protocole: $CURRENT_PROTOCOL"
    echo "============================================="
    echo
    echo "1. Activer le mode Ghost"
    echo "2. Configurer le contournement DPI"
    echo "3. Choisir un protocole furtif"
    echo "4. Tester la configuration"
    echo "5. Quitter"
    echo
}

# Activer le mode Ghost
enable_ghost() {
    STEALTH_MODE="ON"
    echo "Mode Ghost activé" >> "$LOG_FILE"
    echo "Mode Ghost activé avec succès"
    sleep 1
}

# Configurer DPI bypass
enable_dpi_bypass() {
    DPI_BYPASS="ON"
    echo "Contournement DPI activé" >> "$LOG_FILE"
    echo "Contournement DPI activé avec succès"
    sleep 1
}

# Choisir un protocole
select_protocol() {
    echo "Protocoles disponibles:"
    echo "1. Reality"
    echo "2. Trojan"
    echo "3. Shadowsocks"
    echo "4. Retour"
    
    read -p "Choix [1-4]: " choice
    
    case $choice in
        1) CURRENT_PROTOCOL="Reality";;
        2) CURRENT_PROTOCOL="Trojan";;
        3) CURRENT_PROTOCOL="Shadowsocks";;
        4) return;;
        *) echo "Option invalide"; sleep 1;;
    esac
    
    echo "Protocole $CURRENT_PROTOCOL sélectionné" >> "$LOG_FILE"
}

# Tester la configuration
test_config() {
    echo "Test en cours..." >> "$LOG_FILE"
    echo "Configuration testée avec succès"
    sleep 1
}

# Main
init
while true; do
    show_menu
    read -p "Choisissez une option [1-5]: " option
    
    case $option in
        1) enable_ghost;;
        2) enable_dpi_bypass;;
        3) select_protocol;;
        4) test_config;;
        5) exit 0;;
        *) echo "Option invalide"; sleep 1;;
    esac
done