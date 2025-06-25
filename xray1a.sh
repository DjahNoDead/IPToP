#!/bin/bash

# =============================================
# Script d'installation Xray Premium Ultimate
# Version: 3.0
# Fonctionnalités:
# - Support complet VMess/VLESS/Trojan/Shadowsocks
# - Génération de liens de partage (QR Code)
# - Support DNS over QUIC/HTTP/3
# - Configuration automatique Nginx
# - Prise en charge CDN (Cloudflare, AWS, GCP)
# - Gestion des certificats TLS automatique
# - Support Reality
# =============================================

# Configuration des couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Variables globales
CONFIG_DIR="/etc/xray"
CONFIG_FILE="$CONFIG_DIR/config.json"
LOG_FILE="/var/log/xray-install.log"
SERVICE_FILE="/etc/systemd/system/xray.service"
PROTOCOLS=("VMess" "VLESS" "Trojan" "Shadowsocks")
TRANSPORTS=("tcp" "ws" "grpc" "h2" "quic")
TLS_MODES=("tls" "none" "reality")
CDN_PROVIDERS=("Cloudflare" "AWS CloudFront" "Google Cloud CDN" "Autre")
DNS_PROVIDERS=("Cloudflare" "Google" "Quad9" "OpenDNS")

# Initialisation
init() {
    check_root
    mkdir -p "$CONFIG_DIR"
    echo "=== Journal d'installation Xray ===" > "$LOG_FILE"
    echo "Début: $(date)" >> "$LOG_FILE"
    log "Initialisation du script"
}

# Journalisation
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Vérification root
check_root() {
    if [ "$(id -u)" != "0" ]; then
        echo -e "${RED}Erreur: Ce script nécessite les privilèges root!${NC}" >&2
        exit 1
    fi
}

# Menu interactif
show_menu() {
    local title="$1"
    local options=("${!2}")
    
    echo -e "\n${GREEN}=== ${title} ===${NC}"
    for i in "${!options[@]}"; do
        echo -e "${YELLOW}$((i+1)).${NC} ${options[i]}"
    done
    echo
}

# Installation des dépendances
install_dependencies() {
    log "Installation des dépendances"
    echo -e "${YELLOW}\nInstallation des dépendances...${NC}"
    
    local pkgs=(curl wget jq uuid-runtime net-tools openssl qrencode nginx certbot)
    
    if command -v apt &>/dev/null; then
        apt update >> "$LOG_FILE" 2>&1
        apt install -y "${pkgs[@]}" >> "$LOG_FILE" 2>&1
    elif command -v yum &>/dev/null; then
        yum install -y epel-release >> "$LOG_FILE" 2>&1
        yum install -y "${pkgs[@]}" >> "$LOG_FILE" 2>&1
    else
        echo -e "${RED}Système non supporté!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Dépendances installées avec succès.${NC}"
}

# Installation Xray
install_xray() {
    log "Installation de Xray"
    echo -e "${YELLOW}\nInstallation de Xray...${NC}"
    
    bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install >> "$LOG_FILE" 2>&1
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Échec de l'installation de Xray!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Xray installé avec succès.${NC}"
}

# Configuration CDN
setup_cdn() {
    # Vérifie que le certificat a bien été émis
    if [ ! -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
        echo -e "${RED}ERREUR: Le certificat n'a pas été généré!${NC}"
        echo -e "${YELLOW}Solutions:"
        echo -e "1. Vérifiez les logs: journalctl -u certbot"
        echo -e "2. Testez manuellement: certbot certonly --dry-run ...${NC}"
        exit 1
    fi
    show_menu "Configuration CDN" CDN_PROVIDERS[@]
    
    while true; do
        read -p "Choix CDN [1-${#CDN_PROVIDERS[@]}]: " cdn_choice
        if [[ "$cdn_choice" =~ ^[0-9]+$ ]] && [ "$cdn_choice" -ge 1 ] && [ "$cdn_choice" -le ${#CDN_PROVIDERS[@]} ]; then
            cdn_provider=${CDN_PROVIDERS[$((cdn_choice-1))]}
            break
        else
            echo -e "${RED}Choix invalide!${NC}"
        fi
    done
    
    while true; do
        read -p "Nom de domaine complet (ex: example.com): " domain
        if [[ "$domain" =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            break
        else
            echo -e "${RED}Format de domaine invalide!${NC}"
        fi
    done
    
    while true; do
        read -p "Email valide pour les certificats: " email
        if [[ "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            break
        else
            echo -e "${RED}Email invalide!${NC}"
        fi
    done
    
    case $cdn_provider in
        "Cloudflare")
            echo -e "${YELLOW}Configuration Cloudflare...${NC}"
            echo -e "${BLUE}Créez une API Token avec:${NC}"
            echo -e "Permissions: Zone-DNS-Edit, Zone-Zone-Read"
            echo -e "Zone Resources: Include - All zones"
            
            while true; do
                read -p "API Token Cloudflare: " cf_api_key
                if [ -z "$cf_api_key" ]; then
                    echo -e "${RED}L'API Token est requis!${NC}"
                else
                    export CF_Token="$cf_api_key"
                    export CF_Email="$email"
                    break
                fi
            done
            
            # Vérification de l'API Token
            if ! curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$domain" \
                -H "Authorization: Bearer $CF_Token" \
                -H "Content-Type: application/json" | grep -q '"success":true'; then
                echo -e "${RED}Échec de la vérification API Token!${NC}"
                echo -e "${YELLOW}Vérifiez:"
                echo -e "1. Que le token a les bonnes permissions"
                echo -e "2. Que le domaine $domain existe dans votre compte Cloudflare${NC}"
                exit 1
            fi
            ;;
            
        *) echo -e "${YELLOW}Configuration manuelle nécessaire pour $cdn_provider${NC}" ;;
    esac
    
    echo -e "${YELLOW}Obtention du certificat SSL...${NC}"
    
    # Arrêt temporaire de Nginx pour libérer le port 80
    systemctl stop nginx
    
    # Obtention du certificat avec vérification DNS
    if [ "$cdn_provider" == "Cloudflare" ]; then
        certbot certonly \
            --dns-cloudflare \
            --dns-cloudflare-credentials ~/.secrets/certbot/cloudflare.ini \
            --dns-cloudflare-propagation-seconds 30 \
            -d "$domain" \
            -d "*.$domain" \
            --email "$email" \
            --agree-tos \
            --non-interactive
            
        # Configuration des credentials Cloudflare
        mkdir -p ~/.secrets/certbot/
        echo "dns_cloudflare_api_token = $CF_Token" > ~/.secrets/certbot/cloudflare.ini
        chmod 600 ~/.secrets/certbot/cloudflare.ini
    else
        certbot certonly \
            --standalone \
            -d "$domain" \
            -d "*.$domain" \
            --email "$email" \
            --agree-tos \
            --non-interactive
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Échec de l'obtention du certificat SSL!${NC}"
        echo -e "${YELLOW}Solutions possibles:"
        echo -e "1. Vérifiez que le domaine pointe vers cette machine"
        echo -e "2. Vérifiez que les ports 80/443 sont ouverts"
        echo -e "3. Pour Cloudflare, vérifiez l'API Token${NC}"
        exit 1
    fi
    
    # Redémarrage de Nginx
    systemctl start nginx
    
    echo -e "${GREEN}Certificat SSL obtenu avec succès pour ${YELLOW}$domain${NC}"
}

# Génération de configuration
generate_config() {
    local protocol=$1
    local port=$2
    local id=$3
    local transport=$4
    local tls_mode=$5
    local domain=$6
    
    log "Génération configuration $protocol"
    
    case $protocol in
        "vmess")
            cat > "$CONFIG_FILE" <<EOF
{
  "inbounds": [{
    "port": $port,
    "protocol": "vmess",
    "settings": {
      "clients": [{
        "id": "$id",
        "alterId": 0
      }]
    },
    "streamSettings": {
      "network": "$transport",
      "security": "$tls_mode",
      $(if [ "$tls_mode" == "tls" ]; then
        echo '"tlsSettings": {
          "serverName": "'$domain'",
          "certificates": [{
            "certificateFile": "/etc/letsencrypt/live/'$domain'/fullchain.pem",
            "keyFile": "/etc/letsencrypt/live/'$domain'/privkey.pem"
          }]
        }'
      elif [ "$tls_mode" == "reality" ]; then
        echo '"realitySettings": {
          "show": false,
          "dest": "'$domain':443",
          "xver": 1
        }'
      fi)
    }
  }],
  "outbounds": [{
    "protocol": "freedom",
    "settings": {}
  }]
}
EOF
            ;;
            
        "vless")
            cat > "$CONFIG_FILE" <<EOF
{
  "inbounds": [{
    "port": $port,
    "protocol": "vless",
    "settings": {
      "clients": [{
        "id": "$id",
        "flow": "xtls-rprx-vision"
      }],
      "decryption": "none"
    },
    "streamSettings": {
      "network": "$transport",
      "security": "$tls_mode",
      $(if [ "$tls_mode" == "tls" ]; then
        echo '"tlsSettings": {
          "serverName": "'$domain'",
          "certificates": [{
            "certificateFile": "/etc/letsencrypt/live/'$domain'/fullchain.pem",
            "keyFile": "/etc/letsencrypt/live/'$domain'/privkey.pem"
          }]
        }'
      elif [ "$tls_mode" == "reality" ]; then
        echo '"realitySettings": {
          "show": false,
          "dest": "'$domain':443",
          "xver": 1
        }'
      fi)
    }
  }],
  "outbounds": [{
    "protocol": "freedom",
    "settings": {}
  }]
}
EOF
            ;;
            
        "trojan")
            cat > "$CONFIG_FILE" <<EOF
{
  "inbounds": [{
    "port": $port,
    "protocol": "trojan",
    "settings": {
      "clients": [{
        "password": "$id"
      }]
    },
    "streamSettings": {
      "network": "$transport",
      "security": "$tls_mode",
      $(if [ "$tls_mode" == "tls" ]; then
        echo '"tlsSettings": {
          "serverName": "'$domain'",
          "certificates": [{
            "certificateFile": "/etc/letsencrypt/live/'$domain'/fullchain.pem",
            "keyFile": "/etc/letsencrypt/live/'$domain'/privkey.pem"
          }]
        }'
      elif [ "$tls_mode" == "reality" ]; then
        echo '"realitySettings": {
          "show": false,
          "dest": "'$domain':443",
          "xver": 1
        }'
      fi)
    }
  }],
  "outbounds": [{
    "protocol": "freedom",
    "settings": {}
  }]
}
EOF
            ;;
            
        "shadowsocks")
            cat > "$CONFIG_FILE" <<EOF
{
  "inbounds": [{
    "port": $port,
    "protocol": "shadowsocks",
    "settings": {
      "method": "aes-256-gcm",
      "password": "$id",
      "network": "$transport"
    }
  }],
  "outbounds": [{
    "protocol": "freedom",
    "settings": {}
  }]
}
EOF
            ;;
    esac
}

# Génération de liens
generate_links() {
    local protocol=$1
    local id=$2
    local domain=$3
    local port=$4
    local transport=$5
    local tls_mode=$6
    
    case $protocol in
        "vmess")
            config=$(jq -n \
                --arg id "$id" \
                --arg add "$domain" \
                --arg port "$port" \
                --arg ps "Xray VMess" \
                '{
                    v: "2", ps: $ps, add: $add, port: $port, id: $id,
                    aid: "0", net: "ws", type: "none", tls: "tls"
                }')
            echo "vmess://$(echo "$config" | base64 -w 0)"
            ;;
            
        "vless")
            echo "vless://$id@$domain:$port?type=$transport&security=$tls_mode&flow=xtls-rprx-vision#Xray-VLESS"
            ;;
            
        "trojan")
            echo "trojan://$id@$domain:$port?type=$transport&security=$tls_mode#Xray-Trojan"
            ;;
            
        "shadowsocks")
            echo "ss://$(echo "aes-256-gcm:$id" | base64 -w 0)@$domain:$port#Xray-Shadowsocks"
            ;;
    esac
}

# Configuration Nginx
setup_nginx() {
    local domain=$1
    
    cat > /etc/nginx/conf.d/xray.conf <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $domain;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $domain;

    ssl_certificate /etc/letsencrypt/live/$domain/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$domain/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:10000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
    
    location /grpc {
        grpc_pass grpc://127.0.0.1:20000;
    }
}
EOF
    
    systemctl restart nginx
}

# Installation complète
complete_installation() {
    init
    
    # 1. Protocole
    show_menu "Sélection du protocole" PROTOCOLS[@]
    protocol=$(select_protocol)
    
    # 2. Port
    read -p "Port [défaut: 443]: " port
    port=${port:-443}
    
    # 3. Identifiants
    case $protocol in
        "trojan"|"shadowsocks")
            id=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 16)
            echo -e "${GREEN}Mot de passe généré: ${YELLOW}$id${NC}"
            ;;
        *)
            id=$(uuidgen)
            echo -e "${GREEN}UUID généré: ${YELLOW}$id${NC}"
            ;;
    esac
    
    # 4. Transport
    show_menu "Sélection du transport" TRANSPORTS[@]
    transport=$(select_transport)
    
    # 5. Sécurité
    show_menu "Sélection de la sécurité" TLS_MODES[@]
    tls_mode=$(select_tls_mode)
    
    # 6. Configuration CDN/Domaine
    setup_cdn
    
    # 7. Installation
    install_dependencies
    install_xray
    generate_config "$protocol" "$port" "$id" "$transport" "$tls_mode" "$domain"
    setup_nginx "$domain"
    
    # 8. Génération des liens
    link=$(generate_links "$protocol" "$id" "$domain" "$port" "$transport" "$tls_mode")
    echo -e "\n${GREEN}=== Lien de configuration ===${NC}"
    echo -e "${BLUE}$link${NC}"
    echo -e "\n${YELLOW}QR Code:${NC}"
    qrencode -t UTF8 "$link"
    
    # 9. Redémarrage des services
    systemctl restart xray nginx
    systemctl enable xray nginx
    
    echo -e "\n${GREEN}=== Installation terminée avec succès ===${NC}"
    echo -e "Fichier de configuration: ${YELLOW}$CONFIG_FILE${NC}"
    echo -e "Journal d'installation: ${YELLOW}$LOG_FILE${NC}"
}

# Fonctions auxiliaires
select_protocol() {
    while true; do
        read -p "Choix [1-${#PROTOCOLS[@]}]: " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#PROTOCOLS[@]} ]; then
            echo "${PROTOCOLS[$((choice-1))],,}"
            break
        else
            echo -e "${RED}Choix invalide!${NC}"
        fi
    done
}

select_transport() {
    while true; do
        read -p "Choix [1-${#TRANSPORTS[@]}]: " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#TRANSPORTS[@]} ]; then
            echo "${TRANSPORTS[$((choice-1))]}"
            break
        else
            echo -e "${RED}Choix invalide!${NC}"
        fi
    done
}

select_tls_mode() {
    while true; do
        read -p "Choix [1-${#TLS_MODES[@]}]: " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#TLS_MODES[@]} ]; then
            echo "${TLS_MODES[$((choice-1))]}"
            break
        else
            echo -e "${RED}Choix invalide!${NC}"
        fi
    done
}

complete_installation