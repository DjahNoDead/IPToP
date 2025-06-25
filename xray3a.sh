#!/bin/bash

# Xray Config Generator - Version Complète
# Contournement FAI avec configurations opérationnelles
# Version: 2.0

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables
CONFIG_DIR="/usr/local/etc/xray"
LOG_FILE="/var/log/xray-config.log"

# Initialisation
init() {
    clear
    mkdir -p $CONFIG_DIR
    touch $LOG_FILE
    chmod 600 $LOG_FILE
    echo -e "${GREEN}[*] Initialisation terminée${NC}" | tee -a $LOG_FILE
}

# Installation des dépendances
install_deps() {
    echo -e "${YELLOW}[*] Installation des dépendances...${NC}" | tee -a $LOG_FILE
    
    if [[ -f /etc/debian_version ]]; then
        apt update && apt install -y curl uuid-runtime openssl jq >> $LOG_FILE 2>&1
    elif [[ -f /etc/redhat-release ]]; then
        yum install -y curl util-linux openssl jq >> $LOG_FILE 2>&1
    fi

    # Installation Xray
    bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install >> $LOG_FILE 2>&1
    
    echo -e "${GREEN}[+] Xray installé avec succès${NC}" | tee -a $LOG_FILE
}

# Génération VLESS Reality
generate_reality() {
    local port=443
    local uuid=$(uuidgen)
    local private_key=$(xray x25519 | awk '{print $3}')
    local short_id=$(openssl rand -hex 8)
    local public_ip=$(curl -4s ifconfig.co)
    local sni="www.google.com"
    
    cat > $CONFIG_DIR/config.json <<EOL
{
    "inbounds": [
        {
            "port": $port,
            "protocol": "vless",
            "settings": {
                "clients": [
                    {
                        "id": "$uuid",
                        "flow": "xtls-rprx-vision"
                    }
                ],
                "decryption": "none"
            },
            "streamSettings": {
                "network": "tcp",
                "security": "reality",
                "realitySettings": {
                    "dest": "$sni:443",
                    "xver": 0,
                    "serverNames": ["$sni"],
                    "privateKey": "$private_key",
                    "minClientVer": "",
                    "maxClientVer": "",
                    "maxTimeDiff": 0,
                    "shortIds": ["$short_id"]
                }
            }
        }
    ],
    "outbounds": [
        {
            "protocol": "freedom",
            "settings": {}
        }
    ]
}
EOL

    systemctl restart xray
    
    clear
    echo -e "${BLUE}=============================================="
    echo -e " VLESS REALITY - CONFIGURATION COMPLETE"
    echo -e "==============================================${NC}"
    echo -e "${GREEN}Adresse du serveur: ${YELLOW}$public_ip${NC}"
    echo -e "${GREEN}Port: ${YELLOW}$port${NC}"
    echo -e "${GREEN}UUID: ${YELLOW}$uuid${NC}"
    echo -e "${GREEN}Flow: ${YELLOW}xtls-rprx-vision${NC}"
    echo -e "${GREEN}SNI: ${YELLOW}$sni${NC}"
    echo -e "${GREEN}Public Key: ${YELLOW}$private_key${NC}"
    echo -e "${GREEN}Short ID: ${YELLOW}$short_id${NC}"
    echo -e "${BLUE}=============================================="
    echo -e "${GREEN}URL de partage (Shadowrocket/Reality):${NC}"
    echo -e "vless://$uuid@$public_ip:$port?security=reality&flow=xtls-rprx-vision&sni=$sni&pbk=$private_key&sid=$short_id&type=tcp#Xray-Reality"
    echo -e "${BLUE}=============================================="
    echo -e "${GREEN}Configuration client Nekoray:${NC}"
    echo -e "Type: VLESS"
    echo -e "Adresse: $public_ip"
    echo -e "Port: $port"
    echo -e "UUID: $uuid"
    echo -e "Flow: xtls-rprx-vision"
    echo -e "TLS: Reality"
    echo -e "Public Key: $private_key"
    echo -e "Short ID: $short_id"
    echo -e "SNI: $sni"
    echo -e "${BLUE}==============================================${NC}"
}

# Génération Trojan TLS
generate_trojan() {
    local port=8443
    local password=$(openssl rand -hex 12)
    local public_ip=$(curl -4s ifconfig.co)
    local domain=""
    
    read -p "Entrez votre domaine (requis pour Trojan TLS): " domain
    [ -z "$domain" ] && { echo -e "${RED}[!] Un domaine est nécessaire${NC}"; return; }
    
    cat > $CONFIG_DIR/config.json <<EOL
{
    "inbounds": [
        {
            "port": $port,
            "protocol": "trojan",
            "settings": {
                "clients": [
                    {
                        "password": "$password",
                        "flow": "xtls-rprx-direct"
                    }
                ],
                "fallbacks": [
                    {
                        "dest": 80
                    }
                ]
            },
            "streamSettings": {
                "network": "tcp",
                "security": "tls",
                "tlsSettings": {
                    "serverName": "$domain",
                    "certificates": [
                        {
                            "certificateFile": "/etc/letsencrypt/live/$domain/fullchain.pem",
                            "keyFile": "/etc/letsencrypt/live/$domain/privkey.pem"
                        }
                    ],
                    "alpn": ["http/1.1"]
                }
            }
        }
    ],
    "outbounds": [
        {
            "protocol": "freedom",
            "settings": {}
        }
    ]
}
EOL

    echo -e "${YELLOW}[*] Configuration Trojan générée. Installez les certificats avec:${NC}"
    echo -e "certbot certonly --standalone -d $domain"
    echo -e "systemctl restart xray"
    
    clear
    echo -e "${BLUE}=============================================="
    echo -e " TROJAN TLS - CONFIGURATION COMPLETE"
    echo -e "==============================================${NC}"
    echo -e "${GREEN}Adresse du serveur: ${YELLOW}$domain${NC}"
    echo -e "${GREEN}Port: ${YELLOW}$port${NC}"
    echo -e "${GREEN}Mot de passe: ${YELLOW}$password${NC}"
    echo -e "${GREEN}Flow: ${YELLOW}xtls-rprx-direct${NC}"
    echo -e "${BLUE}=============================================="
    echo -e "${GREEN}URL de partage:${NC}"
    echo -e "trojan://$password@$domain:$port?security=tls&flow=xtls-rprx-direct&type=tcp&sni=$domain#Trojan-TLS"
    echo -e "${BLUE}=============================================="
}

# Menu principal
main_menu() {
    init
    install_deps
    
    while true; do
        clear
        echo -e "${BLUE}=============================================="
        echo -e " XRAY CONFIG GENERATOR - MENU PRINCIPAL"
        echo -e "==============================================${NC}"
        echo -e "${GREEN}1. ${YELLOW}Générer configuration VLESS Reality (Recommandé)"
        echo -e "${GREEN}2. ${YELLOW}Générer configuration Trojan TLS (Nécessite domaine)"
        echo -e "${GREEN}3. ${YELLOW}Quitter"
        echo -e "${BLUE}=============================================="
        
        read -p "Choix [1-3]: " choice
        
        case $choice in
            1) generate_reality ;;
            2) generate_trojan ;;
            3) exit 0 ;;
            *) echo -e "${RED}[!] Option invalide${NC}"; sleep 1 ;;
        esac
        
        read -p "Appuyez sur Entrée pour continuer..."
    done
}

# Démarrer
main_menu