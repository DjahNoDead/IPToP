#!/bin/bash

# Configuration des couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables globales
CONFIG_FILE="/etc/v2ray/config.json"
PROTOCOLS=("VMess" "VLESS" "Trojan" "Shadowsocks")
TRANSPORTS=("tcp" "ws" "grpc" "h2")
TLS_MODES=("tls" "none" "reality")

# Fonction pour afficher les menus correctement
show_menu() {
    clear
    local title="$1"
    local options=("${!2}")
    
    echo -e "${GREEN}=== ${title} ===${NC}"
    for i in "${!options[@]}"; do
        echo -e "$((i+1)). ${YELLOW}${options[$i]}${NC}"
    done
}

# Version corrigée de select_protocol
select_protocol() {
    show_menu "Choix du protocole" PROTOCOLS[@]
    
    while true; do
        read -p "Votre choix [1-${#PROTOCOLS[@]}]: " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#PROTOCOLS[@]}" ]; then
            local protocol=${PROTOCOLS[$((choice-1))]}
            echo -e "${GREEN}Protocole sélectionné: ${YELLOW}$protocol${NC}"
            echo "${protocol,,}"  # Retourne en minuscules
            break
        else
            echo -e "${RED}Choix invalide!${NC}"
        fi
    done
}

# Version corrigée de configure_v2ray
configure_v2ray() {
    local protocol=$1
    local port=$2
    local uuid_or_password=$3
    local transport=$4
    local tls_mode=$5
    
    # Conversion en minuscules pour la compatibilité
    protocol=${protocol,,}
    transport=${transport,,}
    tls_mode=${tls_mode,,}

    log "Configuration de V2Ray avec $protocol sur $port via $transport ($tls_mode)"
    
    case $protocol in
        "vmess")
            generate_vmess_config "$port" "$uuid_or_password" "$transport" "$tls_mode"
            ;;
        "vless")
            generate_vless_config "$port" "$uuid_or_password" "$transport" "$tls_mode"
            ;;
        "trojan")
            generate_trojan_config "$port" "$uuid_or_password" "$transport" "$tls_mode"
            ;;
        "shadowsocks")
            generate_shadowsocks_config "$port" "$uuid_or_password" "$transport" "$tls_mode"
            ;;
        *)
            echo -e "${RED}Erreur critique: Protocole $protocol non implémenté${NC}"
            exit 1
            ;;
    esac
}

# Fonction d'installation complète corrigée
complete_installation() {
    clear
    echo -e "${GREEN}=== Installation de V2Ray ===${NC}"
    
    # 1. Sélection du protocole
    protocol=$(select_protocol)
    
    # 2. Sélection du port
    while true; do
        read -p "Port à utiliser [défaut: 443]: " port
        port=${port:-443}
        if [[ "$port" =~ ^[0-9]+$ ]] && [ "$port" -ge 1 ] && [ "$port" -le 65535 ]; then
            if ! netstat -tuln | grep -q ":${port} "; then
                break
            else
                echo -e "${RED}Le port $port est déjà utilisé!${NC}"
            fi
        else
            echo -e "${RED}Port invalide!${NC}"
        fi
    done
    
    # 3. Génération des identifiants
    if [ "$protocol" == "trojan" ]; then
        password=$(generate_password)
        echo -e "${GREEN}Mot de passe généré: ${YELLOW}$password${NC}"
        id_value=$password
    else
        uuid=$(generate_uuid)
        echo -e "${GREEN}UUID généré: ${YELLOW}$uuid${NC}"
        id_value=$uuid
    fi
    
    # 4. Sélection du transport
    show_menu "Choix du transport" TRANSPORTS[@]
    transport=$(select_transport)
    
    # 5. Sélection du mode TLS
    show_menu "Choix de la sécurité" TLS_MODES[@]
    tls_mode=$(select_tls_mode)
    
    # Récapitulatif final
    echo -e "${GREEN}=== Configuration finale ===${NC}"
    echo -e "• Protocole: ${YELLOW}$protocol${NC}"
    echo -e "• Port: ${YELLOW}$port${NC}"
    echo -e "• Identifiant: ${YELLOW}$id_value${NC}"
    echo -e "• Transport: ${YELLOW}$transport${NC}"
    echo -e "• Sécurité: ${YELLOW}$tls_mode${NC}"
    echo
    
    read -p "Confirmer l'installation (o/N)? " confirm
    [[ "$confirm" =~ ^[oO]$ ]] || { echo -e "${RED}Installation annulée.${NC}"; exit 1; }
    
    # Installation
    echo -e "${YELLOW}Installation en cours...${NC}"
    install_dependencies
    install_v2ray
    configure_v2ray "$protocol" "$port" "$id_value" "$transport" "$tls_mode"
    
    echo -e "${GREEN}=== Installation réussie ===${NC}"
    echo -e "Fichier de configuration: ${YELLOW}$CONFIG_FILE${NC}"
}

# Fonctions manquantes à ajouter
select_transport() {
    while true; do
        read -p "Votre choix [1-${#TRANSPORTS[@]}]: " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#TRANSPORTS[@]}" ]; then
            local transport=${TRANSPORTS[$((choice-1))]}
            echo -e "${GREEN}Transport sélectionné: ${YELLOW}$transport${NC}"
            echo "$transport"
            break
        else
            echo -e "${RED}Choix invalide!${NC}"
        fi
    done
}

select_tls_mode() {
    while true; do
        read -p "Votre choix [1-${#TLS_MODES[@]}]: " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#TLS_MODES[@]}" ]; then
            local tls_mode=${TLS_MODES[$((choice-1))]}
            echo -e "${GREEN}Mode sélectionné: ${YELLOW}$tls_mode${NC}"
            echo "$tls_mode"
            break
        else
            echo -e "${RED}Choix invalide!${NC}"
        fi
    done
}

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
