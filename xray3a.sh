#!/bin/bash

# Xray Ultimate Installer - Version Complète
# Installation et configuration clé en main
# Version: 3.0

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables
CONFIG_DIR="/usr/local/etc/xray"
LOG_FILE="/var/log/xray-install.log"
DOMAIN=""
EMAIL=""

# Fonction d'initialisation
init() {
    clear
    echo -e "${GREEN}[*] Initialisation du système...${NC}" | tee -a $LOG_FILE
    mkdir -p $CONFIG_DIR
    touch $LOG_FILE
    chmod 600 $LOG_FILE
}

# Installation des dépendances
install_deps() {
    echo -e "${YELLOW}[*] Installation des dépendances...${NC}" | tee -a $LOG_FILE
    
    # Détection de l'OS
    if [[ -f /etc/debian_version ]]; then
        apt update && apt upgrade -y
        apt install -y curl uuid-runtime openssl jq certbot nginx python3-certbot-nginx >> $LOG_FILE 2>&1
    elif [[ -f /etc/redhat-release ]]; then
        yum update -y
        yum install -y curl util-linux openssl jq certbot nginx python3-certbot-nginx >> $LOG_FILE 2>&1
    else
        echo -e "${RED}[!] Système d'exploitation non supporté${NC}" | tee -a $LOG_FILE
        exit 1
    fi

    # Installation Xray
    echo -e "${YELLOW}[*] Installation de Xray...${NC}" | tee -a $LOG_FILE
    bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install >> $LOG_FILE 2>&1
    
    # Vérification
    if [ -f /usr/local/bin/xray ]; then
        echo -e "${GREEN}[+] Xray installé avec succès${NC}" | tee -a $LOG_FILE
    else
        echo -e "${RED}[!] Échec de l'installation de Xray${NC}" | tee -a $LOG_FILE
        exit 1
    fi
}

# Configuration Nginx
setup_nginx() {
    echo -e "${YELLOW}[*] Configuration de Nginx...${NC}" | tee -a $LOG_FILE
    
    cat > /etc/nginx/conf.d/xray.conf <<EOL
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    
    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOL

    systemctl restart nginx
}

# Obtention des certificats
get_certificates() {
    echo -e "${YELLOW}[*] Obtention des certificats SSL...${NC}" | tee -a $LOG_FILE
    
    if [ -z "$EMAIL" ]; then
        certbot certonly --nginx -d $DOMAIN --non-interactive --agree-tos >> $LOG_FILE 2>&1
    else
        certbot certonly --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL >> $LOG_FILE 2>&1
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[+] Certificats obtenus avec succès${NC}" | tee -a $LOG_FILE
    else
        echo -e "${RED}[!] Échec de l'obtention des certificats${NC}" | tee -a $LOG_FILE
        exit 1
    fi
}

# Génération VLESS + Reality
setup_reality() {
    local port=443
    local uuid=$(uuidgen)
    local private_key=$(xray x25519 | awk '{print $3}')
    local short_id=$(openssl rand -hex 8)
    local sni="www.google.com"
    
    echo -e "${YELLOW}[*] Configuration VLESS Reality...${NC}" | tee -a $LOG_FILE
    
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
    
    # Affichage des informations
    clear
    echo -e "${BLUE}=============================================="
    echo -e " VLESS REALITY - CONFIGURATION COMPLETE"
    echo -e "==============================================${NC}"
    echo -e "${GREEN}Domaine: ${YELLOW}$DOMAIN${NC}"
    echo -e "${GREEN}Port: ${YELLOW}$port${NC}"
    echo -e "${GREEN}UUID: ${YELLOW}$uuid${NC}"
    echo -e "${GREEN}Flow: ${YELLOW}xtls-rprx-vision${NC}"
    echo -e "${GREEN}SNI: ${YELLOW}$sni${NC}"
    echo -e "${GREEN}Public Key: ${YELLOW}$private_key${NC}"
    echo -e "${GREEN}Short ID: ${YELLOW}$short_id${NC}"
    echo -e "${BLUE}=============================================="
    echo -e "${GREEN}URL de partage:${NC}"
    echo -e "vless://$uuid@$DOMAIN:$port?security=reality&flow=xtls-rprx-vision&sni=$sni&pbk=$private_key&sid=$short_id&type=tcp#Xray-Reality"
    echo -e "${BLUE}=============================================="
}

# Génération Trojan + TLS
setup_trojan() {
    local port=443
    local password=$(openssl rand -hex 16)
    
    echo -e "${YELLOW}[*] Configuration Trojan TLS...${NC}" | tee -a $LOG_FILE
    
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
                    "serverName": "$DOMAIN",
                    "certificates": [
                        {
                            "certificateFile": "/etc/letsencrypt/live/$DOMAIN/fullchain.pem",
                            "keyFile": "/etc/letsencrypt/live/$DOMAIN/privkey.pem"
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

    systemctl restart xray
    
    # Affichage des informations
    clear
    echo -e "${BLUE}=============================================="
    echo -e " TROJAN TLS - CONFIGURATION COMPLETE"
    echo -e "==============================================${NC}"
    echo -e "${GREEN}Domaine: ${YELLOW}$DOMAIN${NC}"
    echo -e "${GREEN}Port: ${YELLOW}$port${NC}"
    echo -e "${GREEN}Mot de passe: ${YELLOW}$password${NC}"
    echo -e "${GREEN}Flow: ${YELLOW}xtls-rprx-direct${NC}"
    echo -e "${BLUE}=============================================="
    echo -e "${GREEN}URL de partage:${NC}"
    echo -e "trojan://$password@$DOMAIN:$port?security=tls&flow=xtls-rprx-direct&type=tcp&sni=$DOMAIN#Trojan-TLS"
    echo -e "${BLUE}=============================================="
}

# Menu principal
main_menu() {
    init
    install_deps
    
    # Demander le domaine
    while [ -z "$DOMAIN" ]; do
        read -p "Entrez votre nom de domaine (ex: vpn.mondomaine.com): " DOMAIN
    done
    
    read -p "Entrez votre email (pour Let's Encrypt, optionnel): " EMAIL
    
    # Configuration Nginx et certificats
    setup_nginx
    get_certificates
    
    while true; do
        clear
        echo -e "${BLUE}=============================================="
        echo -e " XRAY ULTIMATE INSTALLER - MENU PRINCIPAL"
        echo -e "==============================================${NC}"
        echo -e "${GREEN}1. ${YELLOW}Configurer VLESS Reality (Recommandé)"
        echo -e "${GREEN}2. ${YELLOW}Configurer Trojan TLS"
        echo -e "${GREEN}3. ${YELLOW}Quitter"
        echo -e "${BLUE}=============================================="
        
        read -p "Choix [1-3]: " choice
        
        case $choice in
            1) setup_reality ;;
            2) setup_trojan ;;
            3) exit 0 ;;
            *) echo -e "${RED}[!] Option invalide${NC}"; sleep 1 ;;
        esac
        
        read -p "Appuyez sur Entrée pour continuer..."
    done
}

# Point d'entrée
main_menu