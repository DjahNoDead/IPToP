#!/bin/bash

# =============================================
# V2Ray Ultimate Pro+ - Édition Enterprise
# Version: 4.0
# Fonctionnalités:
# - Domain Fronting avancé
# - Intégration Cloudflare (Proxy/Non-Proxy)
# - Support CDN complet
# - Protection anti-DPI
# - Optimisation Extreme
# =============================================

# Configuration Initiale
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'
UNDERLINE='\033[4m'

# Variables Globales
CONFIG_DIR="/etc/v2ray"
CONFIG_FILE="$CONFIG_DIR/config.json"
CLOUDFLARE_CONFIG="$CONFIG_DIR/cloudflare.json"
FRONTING_CONFIG="$CONFIG_DIR/fronting.json"
LOG_DIR="/var/log/v2ray"
INSTALL_LOG="$LOG_DIR/install.log"
SERVICE_FILE="/etc/systemd/system/v2ray.service"
TMP_DIR="/tmp/v2ray_pro"

# Protocoles Avancés
PROTOCOLS=("VMess+WS+TLS" "VLESS+XTLS+Reality" "Trojan+gRPC" "Shadowsocks2022" "WireGuard+CDN")
CDN_PROVIDERS=("Cloudflare" "Cloudfront" "Akamai" "Fastly" "BunnyCDN")
FRONTING_TYPES=("AWS" "Google" "Azure" "Cloudflare" "Custom")

# Détection Initiale
OS=""
OS_VERSION=""
ARCH=""
IP_ADDRESS=""
DOMAIN=""
EMAIL=""
USE_CDN=false
USE_FRONTING=false

## Fonctions Avancées ###

configure_cloudflare() {
    echo -e "${YELLOW}[~] Configuration Cloudflare...${NC}" | tee -a $INSTALL_LOG
    
    local subdomain="cdn-$(openssl rand -hex 3).${DOMAIN}"
    local cname_record="proxy-$(openssl rand -hex 2).${DOMAIN}"
    
    cat > $CLOUDFLARE_CONFIG <<EOF
{
    "cdn": {
        "enabled": true,
        "provider": "Cloudflare",
        "subdomain": "$subdomain",
        "cname": "$cname_record",
        "proxy_status": true,
        "ssl_mode": "full",
        "tls_1_3": true,
        "http2": true,
        "http3": false,
        "zero_rtt": true,
        "ip_geoblocking": false,
        "security_level": "medium",
        "cache_level": "aggressive",
        "waf": true,
        "bot_protection": false
    }
}
EOF

    echo -e "${GREEN}[✓] Configuration Cloudflare générée${NC}" | tee -a $INSTALL_LOG
    echo -e "${CYAN}Subdomain: ${YELLOW}$subdomain${NC}"
    echo -e "${CYAN}CNAME: ${YELLOW}$cname_record${NC}"
}

setup_domain_fronting() {
    echo -e "${YELLOW}[~] Configuration Domain Fronting...${NC}" | tee -a $INSTALL_LOG
    
    local front_domain=""
    case $1 in
        "AWS") front_domain="a0.awsstatic.com" ;;
        "Google") front_domain="www.google.com" ;;
        "Azure") front_domain="azure.microsoft.com" ;;
        "Cloudflare") front_domain="cdn.cloudflare.com" ;;
        *) front_domain="$2" ;;
    esac
    
    cat > $FRONTING_CONFIG <<EOF
{
    "fronting": {
        "enabled": true,
        "type": "$1",
        "front_domain": "$front_domain",
        "fallback": "www.microsoft.com",
        "http_redirect": true,
        "sni_masking": true,
        "tls_padding": 512,
        "request_spoofing": true,
        "header_order": "randomized"
    }
}
EOF

    echo -e "${GREEN}[✓] Domain Fronting configuré avec ${YELLOW}$front_domain${NC}" | tee -a $INSTALL_LOG
}

generate_advanced_config() {
    local protocol=$1
    local uuid=$2
    local transport=$3
    
    case $protocol in
        "VMess+WS+TLS")
            config_template='{
                "inbounds": [{
                    "port": 443,
                    "protocol": "vmess",
                    "settings": {
                        "clients": [{
                            "id": "'$uuid'",
                            "alterId": 0,
                            "email": "user@'$DOMAIN'"
                        }],
                        "disableInsecureEncryption": true
                    },
                    "streamSettings": {
                        "network": "ws",
                        "security": "tls",
                        "wsSettings": {
                            "path": "/'$(openssl rand -hex 4)'",
                            "headers": {
                                "Host": "'$DOMAIN'"
                            }
                        },
                        "tlsSettings": {
                            "serverName": "'$DOMAIN'",
                            "certificates": [{
                                "certificateFile": "/etc/letsencrypt/live/'$DOMAIN'/fullchain.pem",
                                "keyFile": "/etc/letsencrypt/live/'$DOMAIN'/privkey.pem"
                            }],
                            "alpn": ["http/1.1"],
                            "fingerprint": "randomized"
                        }
                    }
                }],
                "outbounds": [{
                    "protocol": "freedom",
                    "settings": {
                        "domainStrategy": "UseIP"
                    }
                }]
            }'
            ;;
            
        "VLESS+XTLS+Reality")
            local private_key=$(openssl rand -hex 32)
            local public_key=$(echo "$private_key" | openssl ec -pubout 2>/dev/null | openssl base64 -A | tr -d '\n')
            local short_id=$(openssl rand -hex 8)
            
            config_template='{
                "inbounds": [{
                    "port": 443,
                    "protocol": "vless",
                    "settings": {
                        "clients": [{
                            "id": "'$uuid'",
                            "flow": "xtls-rprx-vision"
                        }],
                        "decryption": "none"
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "security": "reality",
                        "realitySettings": {
                            "show": false,
                            "dest": "'$DOMAIN':443",
                            "xver": 0,
                            "serverNames": ["'$DOMAIN'"],
                            "privateKey": "'$private_key'",
                            "minClientVer": "",
                            "maxClientVer": "",
                            "maxTimeDiff": 0,
                            "shortIds": ["'$short_id'"]
                        }
                    }
                }],
                "outbounds": [{
                    "protocol": "freedom",
                    "settings": {
                        "domainStrategy": "UseIPv6"
                    }
                }]
            }'
            ;;
            
        "Trojan+gRPC")
            config_template='{
                "inbounds": [{
                    "port": 443,
                    "protocol": "trojan",
                    "settings": {
                        "clients": [{
                            "password": "'$uuid'",
                            "email": "user@'$DOMAIN'"
                        }]
                    },
                    "streamSettings": {
                        "network": "grpc",
                        "security": "tls",
                        "grpcSettings": {
                            "serviceName": "'$(openssl rand -hex 4)'",
                            "multiMode": true
                        },
                        "tlsSettings": {
                            "serverName": "'$DOMAIN'",
                            "certificates": [{
                                "certificateFile": "/etc/letsencrypt/live/'$DOMAIN'/fullchain.pem",
                                "keyFile": "/etc/letsencrypt/live/'$DOMAIN'/privkey.pem"
                            }],
                            "alpn": ["h2"],
                            "fingerprint": "chrome"
                        }
                    }
                }],
                "outbounds": [{
                    "protocol": "freedom",
                    "settings": {
                        "domainStrategy": "AsIs"
                    }
                }]
            }'
            ;;
    esac
    
    echo "$config_template" > $CONFIG_FILE
}

setup_certbot() {
    echo -e "${YELLOW}[~] Configuration Certbot...${NC}" | tee -a $INSTALL_LOG
    
    if [ -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
        echo -e "${GREEN}[✓] Certificat existant trouvé${NC}" | tee -a $INSTALL_LOG
        return 0
    fi
    
    apt-get install -y certbot python3-certbot-nginx >> $INSTALL_LOG 2>&1
    certbot certonly --standalone --non-interactive --agree-tos --email $EMAIL -d $DOMAIN >> $INSTALL_LOG 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[✓] Certificat Let's Encrypt obtenu${NC}" | tee -a $INSTALL_LOG
        return 0
    else
        echo -e "${RED}[✗] Échec de l'obtention du certificat${NC}" | tee -a $INSTALL_LOG
        return 1
    fi
}

## Interface Utilisateur ###

show_menu() {
    clear
    echo -e "${BLUE}${BOLD}"
    echo "==================================================="
    echo "   V2Ray Enterprise Pro+ - Configuration Avancée"
    echo "   Version: 4.0 | Sécurité Maximale | Performances"
    echo "==================================================="
    echo -e "${NC}"
    
    echo -e "${GREEN}Options de Configuration:${NC}"
    echo -e "1. Configurer avec Cloudflare CDN"
    echo -e "2. Activer Domain Fronting"
    echo -e "3. Configurer un protocole avancé"
    echo -e "4. Optimiser les performances réseau"
    echo -e "5. Configurer la protection DPI"
    echo -e "6. Appliquer les paramètres"
    echo -e "7. Tester la configuration"
    echo -e "8. Quitter"
}

apply_settings() {
    echo -e "${YELLOW}[~] Application des paramètres...${NC}" | tee -a $INSTALL_LOG
    
    systemctl restart v2ray >> $INSTALL_LOG 2>&1
    systemctl enable v2ray >> $INSTALL_LOG 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[✓] Configuration appliquée avec succès${NC}" | tee -a $INSTALL_LOG
        show_connection_info
    else
        echo -e "${RED}[✗] Échec de l'application de la configuration${NC}" | tee -a $INSTALL_LOG
    fi
}

show_connection_info() {
    local protocol=$(jq -r '.inbounds[0].protocol' $CONFIG_FILE)
    local port=$(jq -r '.inbounds[0].port' $CONFIG_FILE)
    local uuid=""
    local path=""
    local host=""
    local security=""
    
    case $protocol in
        "vmess")
            uuid=$(jq -r '.inbounds[0].settings.clients[0].id' $CONFIG_FILE)
            path=$(jq -r '.inbounds[0].streamSettings.wsSettings.path' $CONFIG_FILE)
            host=$(jq -r '.inbounds[0].streamSettings.wsSettings.headers.Host' $CONFIG_FILE)
            security="tls"
            ;;
        "vless")
            uuid=$(jq -r '.inbounds[0].settings.clients[0].id' $CONFIG_FILE)
            security="reality"
            ;;
        "trojan")
            uuid=$(jq -r '.inbounds[0].settings.clients[0].password' $CONFIG_FILE)
            path=$(jq -r '.inbounds[0].streamSettings.grpcSettings.serviceName' $CONFIG_FILE)
            security="tls"
            ;;
    esac
    
    clear
    echo -e "${GREEN}Configuration Finale:${NC}"
    echo -e "Protocole: ${YELLOW}$protocol${NC}"
    echo -e "Domaine: ${YELLOW}$DOMAIN${NC}"
    echo -e "Port: ${YELLOW}$port${NC}"
    echo -e "UUID/Password: ${YELLOW}$uuid${NC}"
    [ -n "$path" ] && echo -e "Path: ${YELLOW}$path${NC}"
    [ -n "$host" ] && echo -e "Host: ${YELLOW}$host${NC}"
    echo -e "Sécurité: ${YELLOW}$security${NC}"
    
    if [ -f $CLOUDFLARE_CONFIG ]; then
        local cdn_subdomain=$(jq -r '.cdn.subdomain' $CLOUDFLARE_CONFIG)
        echo -e "\n${CYAN}Configuration CDN:${NC}"
        echo -e "Subdomain: ${YELLOW}$cdn_subdomain${NC}"
        echo -e "Proxy: ${YELLOW}Actif${NC}"
    fi
    
    if [ -f $FRONTING_CONFIG ]; then
        local front_domain=$(jq -r '.fronting.front_domain' $FRONTING_CONFIG)
        echo -e "\n${CYAN}Domain Fronting:${NC}"
        echo -e "Front Domain: ${YELLOW}$front_domain${NC}"
    fi
}

## Installation Principale ###

main_install() {
    check_root
    detect_system
    install_dependencies
    
    read -p "Entrez votre domaine principal: " DOMAIN
    read -p "Entrez votre email (pour Let's Encrypt): " EMAIL
    
    setup_certbot
    
    # Génération UUID
    local uuid=$(generate_uuid)
    
    # Menu de sélection
    show_menu
    read -p "Choisissez un protocole [1-8]: " choice
    
    case $choice in
        1) configure_cloudflare ;;
        2) 
            echo -e "${GREEN}Types de Domain Fronting disponibles:${NC}"
            for i in "${!FRONTING_TYPES[@]}"; do
                echo "$((i+1)). ${FRONTING_TYPES[$i]}"
            done
            read -p "Choisissez un type [1-${#FRONTING_TYPES[@]}]: " front_choice
            setup_domain_fronting "${FRONTING_TYPES[$((front_choice-1))]}"
            ;;
        3)
            echo -e "${GREEN}Protocoles disponibles:${NC}"
            for i in "${!PROTOCOLS[@]}"; do
                echo "$((i+1)). ${PROTOCOLS[$i]}"
            done
            read -p "Choisissez un protocole [1-${#PROTOCOLS[@]}]: " proto_choice
            generate_advanced_config "${PROTOCOLS[$((proto_choice-1))]}" "$uuid"
            ;;
        6) apply_settings ;;
        7) test_configuration ;;
        8) exit 0 ;;
        *) echo -e "${RED}Choix invalide!${NC}"; sleep 1 ;;
    esac
    
    show_connection_info
}

## Point d'Entrée ###

if [[ $# -eq 0 ]]; then
    main_install
else
    case $1 in
        --install) main_install ;;
        --uninstall) uninstall_v2ray ;;
        --upgrade) upgrade_v2ray ;;
        *) echo "Usage: $0 [--install|--uninstall|--upgrade]" ;;
    esac
fi
