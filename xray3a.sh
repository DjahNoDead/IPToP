#!/bin/bash

# Xray Ultimate Pro - Installation Complète
# Version: 5.0
# Fonctionnalités :
# - Génération de configurations valides
# - URLs parfaitement formatées
# - Tests automatiques
# - Support multi-protocoles

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
EMAIL="admin@${DOMAIN}"
IP=$(curl -4s ifconfig.co)

# Initialisation
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
    
    if [[ -f /etc/debian_version ]]; then
        apt update && apt upgrade -y
        apt install -y curl uuid-runtime openssl jq certbot nginx python3-certbot-nginx qrencode >> $LOG_FILE 2>&1
    elif [[ -f /etc/redhat-release ]]; then
        yum update -y
        yum install -y curl util-linux openssl jq certbot nginx python3-certbot-nginx qrencode >> $LOG_FILE 2>&1
    fi

    # Installation Xray
    echo -e "${YELLOW}[*] Installation de Xray...${NC}" | tee -a $LOG_FILE
    bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install >> $LOG_FILE 2>&1
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
    
    location /grpc {
        grpc_pass grpc://127.0.0.1:50051;
    }
    
    location /ws {
        proxy_pass http://127.0.0.1:10000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
}
EOL

    systemctl enable --now nginx
}

# Obtention des certificats
get_certificates() {
    echo -e "${YELLOW}[*] Obtention des certificats SSL...${NC}" | tee -a $LOG_FILE
    
    if [ -z "$EMAIL" ]; then
        certbot certonly --nginx -d $DOMAIN --non-interactive --agree-tos >> $LOG_FILE 2>&1
    else
        certbot certonly --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL >> $LOG_FILE 2>&1
    fi

    # Configuration automatique du renouvellement
    (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook \"systemctl restart xray nginx\"") | crontab -
}

# Encodage URL
urlencode() {
    echo "$1" | sed -e 's/%/%25/g' -e 's/ /%20/g' -e 's/!/%21/g' -e 's/"/%22/g' \
    -e 's/#/%23/g' -e 's/\$/%24/g' -e 's/\&/%26/g' -e 's/'\''/%27/g' -e 's/(/%28/g' \
    -e 's/)/%29/g' -e 's/\*/%2a/g' -e 's/+/%2b/g' -e 's/,/%2c/g' -e 's/-/%2d/g' \
    -e 's/\./%2e/g' -e 's/\//%2f/g' -e 's/:/%3a/g' -e 's/;/%3b/g' -e 's//%3e/g' \
    -e 's/?/%3f/g' -e 's/@/%40/g' -e 's/\[/%5b/g' -e 's/\\/%5c/g' -e 's/\]/%5d/g' \
    -e 's/\^/%5e/g' -e 's/_/%5f/g' -e 's/`/%60/g' -e 's/{/%7b/g' -e 's/|/%7c/g' \
    -e 's/}/%7d/g' -e 's/~/%7e/g'
}

# Génération de configuration
generate_config() {
    local protocol=$1
    local transport=$2
    local port=$3
    local path="/$(openssl rand -hex 4)"
    local service_name="$(openssl rand -hex 2)"
    local url=""
    local client_config=""

    # Génération des identifiants
    case "$protocol" in
        "vless")
            local uuid=$(uuidgen)
            local flow="xtls-rprx-vision"
            ;;
        "vmess")
            local uuid=$(uuidgen)
            ;;
        "trojan")
            local password=$(openssl rand -hex 16)
            ;;
        "shadowsocks")
            local password=$(openssl rand -hex 16)
            local method="aes-256-gcm"
            ;;
    esac

    # Construction de la configuration JSON
    config="{
        \"inbounds\": [{
            \"port\": $port,
            \"protocol\": \"$protocol\","

    case "$protocol" in
        "vless")
            config+="
            \"settings\": {
                \"clients\": [{
                    \"id\": \"$uuid\",
                    \"flow\": \"$flow\"
                }],
                \"decryption\": \"none\"
            },"
            ;;
        "vmess")
            config+="
            \"settings\": {
                \"clients\": [{
                    \"id\": \"$uuid\",
                    \"alterId\": 0
                }]
            },"
            ;;
        "trojan")
            config+="
            \"settings\": {
                \"clients\": [{
                    \"password\": \"$password\",
                    \"flow\": \"xtls-rprx-direct\"
                }]
            },"
            ;;
        "shadowsocks")
            config+="
            \"settings\": {
                \"clients\": [{
                    \"method\": \"$method\",
                    \"password\": \"$password\"
                }],
                \"network\": \"tcp,udp\"
            },"
            ;;
    esac

    case "$transport" in
        "tcp")
            config+="
            \"streamSettings\": {
                \"network\": \"tcp\",
                \"security\": \"tls\",
                \"tlsSettings\": {
                    \"serverName\": \"$DOMAIN\",
                    \"certificates\": [{
                        \"certificateFile\": \"/etc/letsencrypt/live/$DOMAIN/fullchain.pem\",
                        \"keyFile\": \"/etc/letsencrypt/live/$DOMAIN/privkey.pem\"
                    }]
                }
            }"
            ;;
        "ws")
            config+="
            \"streamSettings\": {
                \"network\": \"ws\",
                \"security\": \"tls\",
                \"wsSettings\": {
                    \"path\": \"$path\",
                    \"headers\": {
                        \"Host\": \"$DOMAIN\"
                    }
                },
                \"tlsSettings\": {
                    \"serverName\": \"$DOMAIN\",
                    \"certificates\": [{
                        \"certificateFile\": \"/etc/letsencrypt/live/$DOMAIN/fullchain.pem\",
                        \"keyFile\": \"/etc/letsencrypt/live/$DOMAIN/privkey.pem\"
                    }]
                }
            }"
            ;;
        "grpc")
            config+="
            \"streamSettings\": {
                \"network\": \"grpc\",
                \"security\": \"tls\",
                \"grpcSettings\": {
                    \"serviceName\": \"$service_name\"
                },
                \"tlsSettings\": {
                    \"serverName\": \"$DOMAIN\",
                    \"certificates\": [{
                        \"certificateFile\": \"/etc/letsencrypt/live/$DOMAIN/fullchain.pem\",
                        \"keyFile\": \"/etc/letsencrypt/live/$DOMAIN/privkey.pem\"
                    }]
                }
            }"
            ;;
    esac

    config+="
        }],
        \"outbounds\": [{
            \"protocol\": \"freedom\",
            \"settings\": {}
        }]
    }"

    echo "$config" > $CONFIG_DIR/config.json
    systemctl restart xray

    # Génération des URLs et configurations client
    case "$protocol-$transport" in
        "vless-tcp")
            url="vless://$uuid@$DOMAIN:$port?security=tls&type=tcp&flow=$flow#Xray-VLESS-TCP"
            client_config="\nAdresse: $DOMAIN\nPort: $port\nID: $uuid\nFlow: $flow\nSecurity: tls"
            ;;
        "vless-ws")
            encoded_path=$(urlencode "$path")
            url="vless://$uuid@$DOMAIN:$port?type=ws&security=tls&path=$encoded_path&host=$DOMAIN#Xray-VLESS-WS"
            client_config="\nAdresse: $DOMAIN\nPort: $port\nID: $uuid\nPath: $path\nHost: $DOMAIN\nTLS: true"
            ;;
        "vmess-ws")
            vmess_config="{
                \"v\":\"2\",\"ps\":\"Xray-VMess-WS\",
                \"add\":\"$DOMAIN\",\"port\":\"$port\",
                \"id\":\"$uuid\",\"aid\":\"0\",
                \"net\":\"ws\",\"type\":\"none\",
                \"host\":\"$DOMAIN\",\"path\":\"$path\",
                \"tls\":\"tls\"
            }"
            url="vmess://$(echo -n "$vmess_config" | base64 -w 0)"
            client_config="\nAdresse: $DOMAIN\nPort: $port\nID: $uuid\nPath: $path\nTLS: true"
            ;;
        "trojan-tcp")
            url="trojan://$password@$DOMAIN:$port?security=tls&type=tcp#Xray-Trojan-TCP"
            client_config="\nAdresse: $DOMAIN\nPort: $port\nPassword: $password\nTLS: true"
            ;;
    esac

    # Affichage des résultats
    clear
    echo -e "${BLUE}=============================================="
    echo -e " CONFIGURATION XRAY - $protocol ${transport^^}"
    echo -e "==============================================${NC}"
    
    echo -e "${GREEN}URL de partage:${NC}"
    echo -e "${YELLOW}$url${NC}"
    
    echo -e "${GREEN}Configuration manuelle:${NC}"
    echo -e "$client_config"
    
    if command -v qrencode >/dev/null; then
        echo -e "\n${GREEN}QR Code:${NC}"
        qrencode -t UTF8 "$url"
    fi
    
    # Test de la configuration
    test_configuration
}

# Test de configuration
test_configuration() {
    echo -e "\n${BLUE}[*] Validation de la configuration...${NC}"
    
    # Vérification JSON
    if ! jq empty $CONFIG_DIR/config.json 2>/dev/null; then
        echo -e "${RED}[!] Erreur dans le fichier de configuration JSON${NC}"
        return 1
    fi
    
    # Vérification du service
    if ! systemctl is-active --quiet xray; then
        echo -e "${RED}[!] Le service Xray n'est pas actif${NC}"
        return 1
    fi
    
    # Vérification du port
    if ! ss -tulnp | grep -q ":$port"; then
        echo -e "${RED}[!] Aucun service n'écoute sur le port $port${NC}"
        return 1
    fi
    
    echo -e "${GREEN}[+] Configuration valide et service actif${NC}"
    return 0
}

# Menu principal
main_menu() {
    init
    install_deps
    
    while [ -z "$DOMAIN" ]; do
        read -p "Entrez votre nom de domaine (ex: vpn.mondomaine.com): " DOMAIN
    done
    
    read -p "Entrez votre email (pour Let's Encrypt, optionnel): " EMAIL
    
    setup_nginx
    get_certificates
    
    while true; do
        clear
        echo -e "${BLUE}=============================================="
        echo -e " XRAY ULTIMATE PRO - MENU PRINCIPAL"
        echo -e "==============================================${NC}"
        echo -e "${GREEN}1. ${YELLOW}Configurer VLESS + WebSocket (Recommandé)"
        echo -e "${GREEN}2. ${YELLOW}Configurer VLESS + gRPC (Haute furtivité)"
        echo -e "${GREEN}3. ${YELLOW}Configurer VMess + WebSocket"
        echo -e "${GREEN}4. ${YELLOW}Configurer Trojan + TLS"
        echo -e "${GREEN}5. ${YELLOW}Quitter"
        echo -e "${BLUE}=============================================="
        
        read -p "Choix [1-5]: " choice
        
        case $choice in
            1) generate_config "vless" "ws" 8443 ;;
            2) generate_config "vless" "grpc" 50051 ;;
            3) generate_config "vmess" "ws" 8080 ;;
            4) generate_config "trojan" "tcp" 443 ;;
            5) exit 0 ;;
            *) echo -e "${RED}[!] Option invalide${NC}"; sleep 1 ;;
        esac
        
        read -p "Appuyez sur Entrée pour continuer..."
    done
}

# Point d'entrée
main_menu