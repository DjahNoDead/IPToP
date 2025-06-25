#!/bin/bash

# =============================================
# Script d'installation V2Ray Premium FR
# Version: 2.1
# Auteur: Expert en réseaux
# Dernière mise à jour: $(date +"%Y-%m-%d")
# =============================================

# Configuration des couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Variables globales
CONFIG_FILE="/etc/v2ray/config.json"
SERVICE_FILE="/etc/systemd/system/v2ray.service"
LOG_FILE="/var/log/v2ray-install.log"
OS=""
OS_VERSION=""
ARCH=""
INSTALL_MODE=""
PROTOCOLS=("VMess" "VLESS" "Trojan" "Shadowsocks")
TRANSPORTS=("TCP" "WebSocket" "gRPC" "HTTP/2")
TLS_MODES=("TLS" "None" "Reality")

# Initialisation du journal d'installation
init_log() {
    echo "=== Journal d'installation V2Ray ===" > "$LOG_FILE"
    echo "Début: $(date)" >> "$LOG_FILE"
    echo "User: $(whoami)" >> "$LOG_FILE"
    echo "Host: $(hostname)" >> "$LOG_FILE"
    log "Initialisation du journal de installation"
}

# Journalisation des actions
log() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $message" >> "$LOG_FILE"
}

# Vérification des privilèges root
check_root() {
    if [ "$(id -u)" != "0" ]; then
        echo -e "${RED}Erreur: Ce script doit être exécuté en tant que root!${NC}" 1>&2
        exit 1
    fi
    log "Vérification des privilèges root réussie"
}

# Détection du système d'exploitation
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
        OS_VERSION=$(lsb_release -sr)
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        OS=$DISTRIB_ID
        OS_VERSION=$DISTRIB_RELEASE
    elif [ -f /etc/debian_version ]; then
        OS=debian
        OS_VERSION=$(cat /etc/debian_version)
    elif [ -f /etc/redhat-release ]; then
        OS=centos
        OS_VERSION=$(grep -oE '[0-9]+\.[0-9]+' /etc/redhat-release)
    else
        OS=$(uname -s | tr '[:upper:]' '[:lower:]')
        OS_VERSION=$(uname -r)
    fi

    ARCH=$(uname -m)
    case $ARCH in
        x86_64) ARCH="amd64" ;;
        aarch64) ARCH="arm64" ;;
        armv7l) ARCH="arm" ;;
        *) ARCH="unsupported" ;;
    esac

    log "Système détecté: $OS $OS_VERSION $ARCH"
}

# Installation des dépendances
install_dependencies() {
    log "Installation des dépendances pour $OS"
    
    echo -e "${YELLOW}Installation des dépendances système...${NC}"
    
    case $OS in
        ubuntu|debian)
            apt-get update >> "$LOG_FILE" 2>&1
            apt-get install -y curl wget sudo jq uuid-runtime net-tools openssl >> "$LOG_FILE" 2>&1
            ;;
        centos|rhel|fedora)
            yum update -y >> "$LOG_FILE" 2>&1
            yum install -y curl wget sudo jq util-linux net-tools openssl >> "$LOG_FILE" 2>&1
            ;;
        *)
            echo -e "${RED}Système d'exploitation non supporté!${NC}"
            exit 1
            ;;
    esac

    if [ $? -ne 0 ]; then
        echo -e "${RED}Échec de l'installation des dépendances!${NC}"
        exit 1
    fi
    
    log "Dépendances installées avec succès"
}

# Installation de V2Ray
install_v2ray() {
    log "Début de l'installation de V2Ray"
    echo -e "${YELLOW}Téléchargement et installation de V2Ray...${NC}"
    
    bash <(curl -sL https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh) >> "$LOG_FILE" 2>&1
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Échec de l'installation de V2Ray!${NC}"
        exit 1
    fi
    
    log "V2Ray installé avec succès"
}

# Configuration de base de V2Ray
configure_v2ray() {
    local protocol=$1
    local port=$2
    local uuid=$3
    local transport=$4
    local tls_mode=$5
    
    log "Configuration de V2Ray avec $protocol sur le port $port"
    
    echo -e "${YELLOW}Création de la configuration V2Ray...${NC}"
    
    # Sauvegarde de l'ancienne configuration
    if [ -f "$CONFIG_FILE" ]; then
        mv "$CONFIG_FILE" "$CONFIG_FILE.bak"
    fi
    
    # Génération du fichier de configuration
    case $protocol in
        VMess|vmess)
            generate_vmess_config "$port" "$uuid" "$transport" "$tls_mode" ;;
        VLESS|vless)
            generate_vless_config "$port" "$uuid" "$transport" "$tls_mode" ;;
        Trojan|trojan)
            generate_trojan_config "$port" "$uuid" "$transport" "$tls_mode" ;;
        *)
            echo -e "${RED}Protocole non supporté!${NC}"
            exit 1 ;;
    esac
    
    # Redémarrage du service
    systemctl restart v2ray >> "$LOG_FILE" 2>&1
    systemctl enable v2ray >> "$LOG_FILE" 2>&1
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Échec du démarrage du service V2Ray!${NC}"
        exit 1
    fi
    
    log "Configuration V2Ray terminée avec succès"
}

# Génération de configuration VMess
generate_vmess_config() {
    local port=$1
    local uuid=$2
    local transport=$3
    local tls_mode=$4
    
    log "Génération de la configuration VMess"
    
    cat > "$CONFIG_FILE" <<EOF
{
  "inbounds": [{
    "port": $port,
    "protocol": "vmess",
    "settings": {
      "clients": [
        {
          "id": "$uuid",
          "alterId": 64
        }
      ]
    },
    "streamSettings": {
      "network": "$transport",
      "security": "$tls_mode"
    }
  }],
  "outbounds": [{
    "protocol": "freedom",
    "settings": {}
  }]
}
EOF
}

# Génération de configuration VLESS
generate_vless_config() {
    local port=$1
    local uuid=$2
    local transport=$3
    local tls_mode=$4
    
    log "Génération de la configuration VLESS"
    
    cat > "$CONFIG_FILE" <<EOF
{
  "inbounds": [{
    "port": $port,
    "protocol": "vless",
    "settings": {
      "clients": [
        {
          "id": "$uuid",
          "flow": "xtls-rprx-direct"
        }
      ],
      "decryption": "none"
    },
    "streamSettings": {
      "network": "$transport",
      "security": "$tls_mode"
    }
  }],
  "outbounds": [{
    "protocol": "freedom",
    "settings": {}
  }]
}
EOF
}

# Génération de configuration Trojan
generate_trojan_config() {
    local port=$1
    local password=$2
    local transport=$3
    local tls_mode=$4
    
    log "Génération de la configuration Trojan"
    
    cat > "$CONFIG_FILE" <<EOF
{
  "inbounds": [{
    "port": $port,
    "protocol": "trojan",
    "settings": {
      "clients": [
        {
          "password": "$password"
        }
      ]
    },
    "streamSettings": {
      "network": "$transport",
      "security": "$tls_mode"
    }
  }],
  "outbounds": [{
    "protocol": "freedom",
    "settings": {}
  }]
}
EOF
}

# Génération d'UUID
generate_uuid() {
    uuidgen | tr '[:upper:]' '[:lower:]'
}

# Génération de mot de passe aléatoire
generate_password() {
    tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 16
}

# Vérification des ports
check_port() {
    local port=$1
    if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
        echo -e "${RED}Port invalide! Doit être entre 1 et 65535${NC}"
        return 1
    fi
    
    if netstat -tuln | grep -q ":$port "; then
        echo -e "${RED}Le port $port est déjà utilisé!${NC}"
        return 1
    fi
    
    return 0
}

# Menu de sélection du protocole (version corrigée)
select_protocol() {
    clear
    echo -e "${GREEN}=== Choix du protocole ===${NC}"
    for i in "${!PROTOCOLS[@]}"; do
        echo -e "$((i+1)). ${YELLOW}${PROTOCOLS[$i]}${NC}"
    done
    
    while true; do
        echo
        read -p "Votre choix [1-${#PROTOCOLS[@]}]: " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#PROTOCOLS[@]}" ]; then
            selected_protocol=${PROTOCOLS[$((choice-1))]}
            echo -e "${GREEN}Protocole sélectionné : ${YELLOW}$selected_protocol${NC}"
            break
        else
            echo -e "${RED}Choix invalide!${NC}"
        fi
    done
    
    echo "$selected_protocol" | tr '[:upper:]' '[:lower:]'  # Conversion en minuscules pour la compatibilité
}

# Menu de sélection du mode TLS
select_tls_mode() {
    echo -e "${GREEN}Modes de sécurité disponibles:${NC}"
    for i in "${!TLS_MODES[@]}"; do
        echo "$((i+1)). ${TLS_MODES[$i]}"
    done
    
    while true; do
        read -p "Choisissez un mode de sécurité [1-${#TLS_MODES[@]}]: " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#TLS_MODES[@]}" ]; then
            selected_tls_mode=${TLS_MODES[$((choice-1))]}
            break
        else
            echo -e "${RED}Choix invalide!${NC}"
        fi
    done
    
    echo "$selected_tls_mode" | tr '[:upper:]' '[:lower:]'
}

# Fonction complete_installation corrigée
complete_installation() {
    clear
    echo -e "${GREEN}=== Installation de V2Ray ===${NC}"
    
    # Sélection du protocole avec affichage clair
    protocol=$(select_protocol)
    
    # Sélection du port avec vérification
    while true; do
        echo
        read -p "Port à utiliser [défaut: 443]: " port
        port=${port:-443}
        if check_port "$port"; then
            echo -e "${GREEN}Port sélectionné : ${YELLOW}$port${NC}"
            break
        else
            echo -e "${RED}Ce port n'est pas disponible!${NC}"
        fi
    done
    
    # Génération des identifiants
    if [ "$protocol" == "trojan" ]; then
        read -p "Mot de passe Trojan [laissez vide pour générer]: " password
        password=${password:-$(generate_password)}
        echo -e "${GREEN}Mot de passe : ${YELLOW}$password${NC}"
    else
        read -p "UUID [laissez vide pour générer]: " uuid
        uuid=${uuid:-$(generate_uuid)}
        echo -e "${GREEN}UUID : ${YELLOW}$uuid${NC}"
    fi
    
    # Sélection du transport
    transport=$(select_transport)
    
    # Sélection du mode TLS
    tls_mode=$(select_tls_mode)
    
    # Récapitulatif final
    echo -e "${GREEN}=== Récapitulatif ===${NC}"
    echo -e "Protocole : ${YELLOW}$protocol${NC}"
    echo -e "Port : ${YELLOW}$port${NC}"
    [ "$protocol" == "trojan" ] && echo -e "Mot de passe : ${YELLOW}$password${NC}" || echo -e "UUID : ${YELLOW}$uuid${NC}"
    echo -e "Transport : ${YELLOW}$transport${NC}"
    echo -e "Sécurité : ${YELLOW}$tls_mode${NC}"
    
    read -p "Confirmer l'installation (o/N)? " confirm
    [[ "$confirm" =~ ^[oO]$ ]] || { echo "Annulation."; exit 1; }
    
    # Installation
    install_dependencies
    install_v2ray
    
    # Utilisation de la bonne variable pour Trojan
    if [ "$protocol" == "trojan" ]; then
        configure_v2ray "$protocol" "$port" "$password" "$transport" "$tls_mode"
    else
        configure_v2ray "$protocol" "$port" "$uuid" "$transport" "$tls_mode"
    fi
    
    # Message final
    echo -e "${GREEN}=== Installation réussie ===${NC}"
    echo -e "Configuration sauvegardée dans : ${YELLOW}$CONFIG_FILE${NC}"
}

# Menu principal
main_menu() {
    while true; do
        clear
        echo -e "${GREEN}=== Menu Principal V2Ray Premium ===${NC}"
        echo -e "1. Installation complète"
        echo -e "2. Mise à jour de V2Ray"
        echo -e "3. Désinstaller V2Ray"
        echo -e "4. Gérer les configurations"
        echo -e "5. Voir le statut du service"
        echo -e "6. Quitter"
        
        read -p "Choisissez une option [1-6]: " choice
        
        case $choice in
            1) complete_installation ;;
            2) update_v2ray ;;
            3) uninstall_v2ray ;;
            4) manage_configurations ;;
            5) service_status ;;
            6) exit 0 ;;
            *) echo -e "${RED}Option invalide!${NC}" ;;
        esac
        
        read -p "Appuyez sur Entrée pour continuer..." -n 1 -r
    done
}

# Fonction de mise à jour
update_v2ray() {
    log "Début de la mise à jour de V2Ray"
    echo -e "${YELLOW}Mise à jour de V2Ray...${NC}"
    bash <(curl -sL https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh) >> "$LOG_FILE" 2>&1
    systemctl restart v2ray >> "$LOG_FILE" 2>&1
    echo -e "${GREEN}Mise à jour terminée avec succès!${NC}"
    log "Mise à jour de V2Ray terminée"
}

# Fonction de désinstallation
uninstall_v2ray() {
    log "Début de la désinstallation de V2Ray"
    echo -e "${RED}Attention: Cette action va supprimer complètement V2Ray!${NC}"
    read -p "Êtes-vous sûr de vouloir continuer? [o/N]: " confirm
    
    if [[ "$confirm" =~ ^[oO]$ ]]; then
        bash <(curl -sL https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh) --remove >> "$LOG_FILE" 2>&1
        rm -rf /etc/v2ray /var/log/v2ray /usr/local/bin/v2ray /usr/local/share/v2ray
        echo -e "${GREEN}V2Ray a été complètement désinstallé!${NC}"
        log "V2Ray désinstallé avec succès"
    else
        echo -e "${YELLOW}Désinstallation annulée.${NC}"
        log "Désinstallation annulée par l'utilisateur"
    fi
}

# Gestion des configurations
manage_configurations() {
    echo -e "${GREEN}=== Gestion des configurations ===${NC}"
    echo -e "1. Afficher la configuration actuelle"
    echo -e "2. Sauvegarder la configuration"
    echo -e "3. Restaurer une configuration"
    echo -e "4. Modifier la configuration manuellement"
    echo -e "5. Retour"
    
    read -p "Choisissez une option [1-5]: " choice
    
    case $choice in
        1) show_config ;;
        2) backup_config ;;
        3) restore_config ;;
        4) edit_config ;;
        5) return ;;
        *) echo -e "${RED}Option invalide!${NC}" ;;
    esac
}

# Affichage du statut du service
service_status() {
    echo -e "${GREEN}=== Statut du service V2Ray ===${NC}"
    systemctl status v2ray --no-pager
}

# Point d'entrée principal
main() {
    check_root
    init_log
    detect_os
    main_menu
}

# Exécution
main
