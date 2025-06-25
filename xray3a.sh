#!/bin/bash

# Xray Ultimate Pro - Installateur Complet
# Version: 4.0
# Protocoles supportés: VLESS, VMess, Trojan, Shadowsocks
# Transports: TCP, gRPC, WebSocket, HTTP/2
# Fonctionnalités: Test automatique, Génération de certificats

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

# Génération de configuration
generate_config() {
    local protocol=$1
    local transport=$2
    local port=$3
    local path="/$(openssl rand -hex 4)"
    local service_name="$(openssl rand -hex 2)"
    local url=""
    local client_config=""

    case "$protocol" in
        "vless")
            local uuid=$(uuidgen)
            local flow="xtls-rprx-vision"
            ;;
        "vmess")
            local uuid=$(uuidgen)
            ;;
        "trojan")
            local password=$(openssl rand -hex 12)
            ;;
        "shadowsocks")
            local password=$(openssl rand -hex 16)
            local method="aes-256-gcm"
            ;;
    esac


    # Génération des URLs avec formatage strict
    case "$protocol-$transport" in
        "vless-tcp")
            url="vless://$uuid@$DOMAIN:$port?security=tls&type=tcp&flow=$flow#Xray-VLESS-TCP"
            client_config="\nAdresse: $DOMAIN\nPort: $port\nID: $uuid\nFlow: $flow\nSecurity: tls"
            ;;
        "vless-ws")
            url="vless://$uuid@$DOMAIN:$port?type=ws&security=tls&path=$(urlencode "$path")&host=$DOMAIN#Xray-VLESS-WS"
            client_config="\nAdresse: $DOMAIN\nPort: $port\nID: $uuid\nPath: $path\nHost: $DOMAIN"
            ;;
        "vmess-ws")
            local vmess_config="{
                \"v\":\"2\", \"ps\":\"Xray-VMess-WS\",
                \"add\":\"$DOMAIN\", \"port\":\"$port\",
                \"id\":\"$uuid\", \"aid\":\"0\",
                \"net\":\"ws\", \"type\":\"none\",
                \"host\":\"$DOMAIN\", \"path\":\"$path\",
                \"tls\":\"tls\"
            }"
            url="vmess://$(echo -n "$vmess_config" | base64 -w 0)"
            client_config="\nAdresse: $DOMAIN\nPort: $port\nID: $uuid\nPath: $path\nTLS: true"
            ;;
        "trojan-tcp")
            url="trojan://$password@$DOMAIN:$port?security=tls&type=tcp#Xray-Trojan-TCP"
            client_config="\nAdresse: $DOMAIN\nPort: $port\nPassword: $password"
            ;;
    esac

    # Affichage structuré
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

# Fonction pour encoder les URLs
urlencode() {
    echo "$1" | sed 's:/:%2F:g'
}

# Test de configuration amélioré
test_configuration() {
    echo -e "\n${BLUE}[*] Validation de la configuration...${NC}"
    
    # Vérification du fichier de config
    if ! jq empty $CONFIG_DIR/config.json 2>/dev/null; then
        echo -e "${RED}[!] Configuration JSON invalide${NC}"
        return 1
    fi
    
    # Vérification du service
    if ! systemctl is-active --quiet xray; then
        echo -e "${RED}[!] Service Xray non actif${NC}"
        return 1
    fi
    
    # Test de port
    if ! nc -z localhost $port; then
        echo -e "${RED}[!] Le port $port n'est pas en écoute${NC}"
        return 1
    fi
    
    echo -e "${GREEN}[+] Configuration valide et service actif${NC}"
    return 0
}

    # Construction de la configuration
    config="{
        \"inbounds\": [{
            \"port\": $port,
            \"protocol\": \"$protocol\","
    
    # Paramètres spécifiques au protocole
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
                    \"flow\": \"$flow\"
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

    # Paramètres de transport
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
        "h2")
            config+="
            \"streamSettings\": {
                \"network\": \"h2\",
                \"security\": \"tls\",
                \"httpSettings\": {
                    \"path\": \"$path\",
                    \"host\": [\"$DOMAIN\"]
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
        echo -e "${GREEN}1. ${YELLOW}Configurer VLESS"
        echo -e "${GREEN}2. ${YELLOW}Configurer VMess"
        echo -e "${GREEN}3. ${YELLOW}Configurer Trojan"
        echo -e "${GREEN}4. ${YELLOW}Configurer Shadowsocks"
        echo -e "${GREEN}5. ${YELLOW}Tester la connexion"
        echo -e "${GREEN}6. ${YELLOW}Quitter"
        echo -e "${BLUE}=============================================="
        
        read -p "Choix [1-6]: " choice
        
        case $choice in
            1)
                clear
                echo -e "${BLUE}=== VLESS ===${NC}"
                echo -e "1. TCP"
                echo -e "2. WebSocket"
                echo -e "3. gRPC"
                echo -e "4. HTTP/2"
                read -p "Transport [1-4]: " transport
                case $transport in
                    1) generate_config "vless" "tcp" 443 ;;
                    2) generate_config "vless" "ws" 8443 ;;
                    3) generate_config "vless" "grpc" 50051 ;;
                    4) generate_config "vless" "h2" 8080 ;;
                    *) echo -e "${RED}Option invalide${NC}"; sleep 1 ;;
                esac
                ;;
            2)
                clear
                echo -e "${BLUE}=== VMess ===${NC}"
                echo -e "1. WebSocket"
                echo -e "2. gRPC"
                echo -e "3. HTTP/2"
                read -p "Transport [1-3]: " transport
                case $transport in
                    1) generate_config "vmess" "ws" 8081 ;;
                    2) generate_config "vmess" "grpc" 50052 ;;
                    3) generate_config "vmess" "h2" 8082 ;;
                    *) echo -e "${RED}Option invalide${NC}"; sleep 1 ;;
                esac
                ;;
            3)
                clear
                echo -e "${BLUE}=== Trojan ===${NC}"
                echo -e "1. TCP"
                echo -e "2. WebSocket"
                read -p "Transport [1-2]: " transport
                case $transport in
                    1) generate_config "trojan" "tcp" 443 ;;
                    2) generate_config "trojan" "ws" 8443 ;;
                    *) echo -e "${RED}Option invalide${NC}"; sleep 1 ;;
                esac
                ;;
            4) generate_config "shadowsocks" "tcp" 8388 ;;
            5) test_connection ;;
            6) exit 0 ;;
            *) echo -e "${RED}Option invalide${NC}"; sleep 1 ;;
        esac
        
        read -p "Appuyez sur Entrée pour continuer..."
    done
}

# Démarrer
main_menu