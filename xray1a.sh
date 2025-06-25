#!/bin/bash

# Configuration des couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables globales
CONFIG_FILE="/etc/v2ray/config.json"
LOG_FILE="/var/log/v2ray-install.log"
PROTOCOLS=("VMess" "VLESS" "Trojan" "Shadowsocks")
TRANSPORTS=("tcp" "ws" "grpc" "h2")
TLS_MODES=("tls" "none" "reality")

# Initialisation du journal
init_log() {
    echo "=== Journal d'installation V2Ray ===" > "$LOG_FILE"
    echo "Début: $(date)" >> "$LOG_FILE"
    log "Initialisation du journal"
}

# Journalisation
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Vérification root
check_root() {
    if [ "$(id -u)" != "0" ]; then
        echo -e "${RED}Erreur: Ce script doit être exécuté en tant que root!${NC}" >&2
        exit 1
    fi
}

# Affichage menu
show_menu() {
    local title="$1"
    local options=("${!2}")
    
    echo -e "${GREEN}=== $title ===${NC}"
    for i in "${!options[@]}"; do
        echo -e "$((i+1)). ${YELLOW}${options[i]}${NC}"
    done
}

# Sélection protocole
select_protocol() {
    show_menu "Choix du protocole" PROTOCOLS[@]
    
    while true; do
        read -p "Votre choix [1-${#PROTOCOLS[@]}]: " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#PROTOCOLS[@]} ]; then
            local protocol=${PROTOCOLS[$((choice-1))]}
            echo -e "${GREEN}Protocole sélectionné: ${YELLOW}$protocol${NC}"
            echo "${protocol,,}"
            break
        else
            echo -e "${RED}Choix invalide!${NC}"
        fi
    done
}

# Installation dépendances
install_dependencies() {
    log "Installation des dépendances"
    echo -e "${YELLOW}Installation des dépendances...${NC}"
    
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update -y >> "$LOG_FILE" 2>&1
        apt-get install -y curl wget jq uuid-runtime net-tools openssl >> "$LOG_FILE" 2>&1
    elif command -v yum >/dev/null 2>&1; then
        yum update -y >> "$LOG_FILE" 2>&1
        yum install -y curl wget jq util-linux net-tools openssl >> "$LOG_FILE" 2>&1
    else
        echo -e "${RED}Aucun gestionnaire de paquets compatible trouvé!${NC}"
        exit 1
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Échec de l'installation des dépendances!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Dépendances installées avec succès.${NC}"
}

# Installation V2Ray
install_v2ray() {
    log "Installation de V2Ray"
    echo -e "${YELLOW}Installation de V2Ray...${NC}"
    
    if ! bash <(curl -sL https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh) >> "$LOG_FILE" 2>&1; then
        echo -e "${RED}Échec de l'installation de V2Ray!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}V2Ray installé avec succès.${NC}"
}

# Configuration VMess
generate_vmess_config() {
    local port=$1
    local uuid=$2
    local transport=$3
    local tls_mode=$4
    
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

# Installation complète
complete_installation() {
    check_root
    init_log
    
    echo -e "${GREEN}=== Installation de V2Ray ===${NC}"
    
    # 1. Protocole
    protocol=$(select_protocol)
    
    # 2. Port
    while true; do
        read -p "Port à utiliser [défaut: 443]: " port
        port=${port:-443}
        if [[ "$port" =~ ^[0-9]+$ ]] && [ "$port" -ge 1 ] && [ "$port" -le 65535 ]; then
            if ! netstat -tuln | grep -q ":$port "; then
                break
            else
                echo -e "${RED}Le port $port est déjà utilisé!${NC}"
            fi
        else
            echo -e "${RED}Port invalide!${NC}"
        fi
    done
    
    # 3. Identifiants
    if [ "$protocol" == "trojan" ]; then
        password=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 16)
        echo -e "${GREEN}Mot de passe généré: ${YELLOW}$password${NC}"
        id_value=$password
    else
        uuid=$(uuidgen | tr '[:upper:]' '[:lower:]')
        echo -e "${GREEN}UUID généré: ${YELLOW}$uuid${NC}"
        id_value=$uuid
    fi
    
    # 4. Transport
    show_menu "Choix du transport" TRANSPORTS[@]
    while true; do
        read -p "Votre choix [1-${#TRANSPORTS[@]}]: " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#TRANSPORTS[@]} ]; then
            transport=${TRANSPORTS[$((choice-1))]}
            echo -e "${GREEN}Transport sélectionné: ${YELLOW}$transport${NC}"
            break
        else
            echo -e "${RED}Choix invalide!${NC}"
        fi
    done
    
    # 5. Sécurité
    show_menu "Choix de la sécurité" TLS_MODES[@]
    while true; do
        read -p "Votre choix [1-${#TLS_MODES[@]}]: " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#TLS_MODES[@]} ]; then
            tls_mode=${TLS_MODES[$((choice-1))]}
            echo -e "${GREEN}Mode sélectionné: ${YELLOW}$tls_mode${NC}"
            break
        else
            echo -e "${RED}Choix invalide!${NC}"
        fi
    done
    
    # Récapitulatif
    echo -e "${GREEN}=== Configuration finale ===${NC}"
    echo -e "• Protocole: ${YELLOW}$protocol${NC}"
    echo -e "• Port: ${YELLOW}$port${NC}"
    echo -e "• Identifiant: ${YELLOW}$id_value${NC}"
    echo -e "• Transport: ${YELLOW}$transport${NC}"
    echo -e "• Sécurité: ${YELLOW}$tls_mode${NC}"
    
    read -p "Confirmer l'installation (o/N)? " confirm
    [[ "$confirm" =~ ^[oO]$ ]] || { echo -e "${RED}Installation annulée.${NC}"; exit 1; }
    
    # Installation
    echo -e "${YELLOW}Installation en cours...${NC}"
    install_dependencies
    install_v2ray
    
    # Configuration
    case $protocol in
        "vmess")
            generate_vmess_config "$port" "$id_value" "$transport" "$tls_mode" ;;
        *)
            echo -e "${RED}Protocole $protocol non implémenté dans cette version${NC}"
            exit 1 ;;
    esac
    
    # Redémarrage
    systemctl restart v2ray
    systemctl enable v2ray
    
    echo -e "${GREEN}=== Installation réussie ===${NC}"
    echo -e "Fichier de configuration: ${YELLOW}$CONFIG_FILE${NC}"
    echo -e "Journal d'installation: ${YELLOW}$LOG_FILE${NC}"
}

complete_installation