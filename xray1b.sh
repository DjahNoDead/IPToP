#!/bin/bash

# =============================================
# Script d'installation Xray Premium Ultimate
# Version: 3.1
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

# Configuration CDN améliorée avec gestion complète des erreurs
setup_cdn() {
    # Fonction interne pour vérifier les certificats existants
    check_existing_cert() {
        local domain=$1
        if [ -d "/etc/letsencrypt/live/$domain" ]; then
            echo -e "${GREEN}✓ Certificat existant détecté pour ${YELLOW}$domain${NC}"
            local cert_info=$(certbot certificates 2>/dev/null | awk -v dom="$domain" '/Domains:/ {if ($2 ~ dom) print}')
            
            if [ -n "$cert_info" ]; then
                echo -e "${BLUE}Informations du certificat:${NC}"
                certbot certificates | grep -A 3 -B 1 "Domains:.*$domain"
                read -p "Utiliser ce certificat existant ? [O/n]: " use_existing
                [[ "$use_existing" =~ ^[OoYy]?$ ]] && return 0
            else
                echo -e "${YELLOW}⚠ Certificat présent mais non reconnu par certbot${NC}"
            fi
        fi
        return 1
    }

    # Afficher le menu CDN
    show_menu "Configuration CDN" CDN_PROVIDERS[@]
    
    # Choix du CDN avec validation
    while true; do
        read -p "Choix CDN [1-${#CDN_PROVIDERS[@]}]: " cdn_choice
        if [[ "$cdn_choice" =~ ^[0-9]+$ ]] && [ "$cdn_choice" -ge 1 ] && [ "$cdn_choice" -le ${#CDN_PROVIDERS[@]} ]; then
            cdn_provider=${CDN_PROVIDERS[$((cdn_choice-1))]}
            echo -e "${GREEN}→ Sélectionné : ${YELLOW}$cdn_provider${NC}"
            break
        else
            echo -e "${RED}⨉ Choix invalide!${NC}"
        fi
    done
    
    # Saisie et validation du domaine
    while true; do
        read -p "Nom de domaine complet (ex: example.com): " domain
        domain=$(echo "$domain" | tr '[:upper:]' '[:lower:]' | xargs)
        
        # Validation avancée du domaine
        if [[ "$domain" =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]] && [[ ! "$domain" =~ \.\. ]]; then
            # Vérification DNS basique
            if ! dig +short "$domain" @8.8.8.8 | grep -q '[0-9]'; then
                echo -e "${YELLOW}⚠ Avertissement : Le domaine ne semble pas résoudre vers une IP${NC}"
                read -p "Continuer quand même ? [o/N]: " force_continue
                [[ "$force_continue" =~ ^[OoYy] ]] && break || continue
            else
                break
            fi
        else
            echo -e "${RED}⨉ Format de domaine invalide!${NC}"
        fi
    done
    
    # Vérification des certificats existants
    if check_existing_cert "$domain"; then
        # Vérification de la validité du certificat
        local cert_path="/etc/letsencrypt/live/$domain/fullchain.pem"
        if openssl x509 -checkend 86400 -noout -in "$cert_path" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Certificat valide pour au moins 1 jour${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ Certificat expiré ou sur le point d'expirer${NC}"
        fi
    fi
    
    # Saisie de l'email avec validation renforcée
    while true; do
        read -p "Email valide pour les certificats: " email
        if [[ "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            # Vérification supplémentaire de la structure
            if [[ "$email" == *@*.* && ! "$email" =~ \\.\\. && ! "$email" =~ @\\. ]]; then
                break
            else
                echo -e "${RED}⨉ Email invalide! Format attendu : user@domain.com${NC}"
            fi
        else
            echo -e "${RED}⨉ Email invalide! Format attendu : user@domain.com${NC}"
        fi
    done
    
    # Configuration spécifique à Cloudflare
		if [ "$cdn_provider" == "Cloudflare" ]; then
			echo -e "${YELLOW}⚙ Configuration Cloudflare...${NC}"
			echo -e "${BLUE}ℹ Créez un token avec ces permissions :${NC}"
			echo -e "  - Zone.DNS (Edit)\n  - Zone.Zone (Read)\n  - Zone: Include - All zones"
			
			# → SUPPRIMER LA SECONDE DEMANDE DE TOKEN PLUS BAS
			# → Utiliser directement le token déjà validé ($CF_Token)

			# Configuration Certbot
			mkdir -p ~/.secrets/certbot/
			echo "dns_cloudflare_api_token = $CF_Token" > ~/.secrets/certbot/cloudflare.ini
			chmod 600 ~/.secrets/certbot/cloudflare.ini

			# Commande Certbot (sans redemander le token)
			cert_cmd=(certbot certonly --dns-cloudflare --dns-cloudflare-credentials ~/.secrets/certbot/cloudflare.ini \
				-d "$domain" --non-interactive --agree-tos --email "$email")
		fi
            
            # Vérification de la longueur
            if [ ${#cf_api_key} -lt 30 ]; then
                echo -e "${RED}⨉ L'API Token semble trop court!${NC}"
                continue
            fi
            
            # Configuration des variables d'environnement
            export CF_Token="$cf_api_key"
            export CF_Email="$email"
            
            # Vérification approfondie de l'API Token
            echo -e "${YELLOW}⏳ Vérification de l'API Token...${NC}"
            api_response=$(curl -s -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
                -H "Authorization: Bearer $CF_Token" \
                -H "Content-Type: application/json" 2>/dev/null)
            
            if echo "$api_response" | jq -e '.success == true' >/dev/null 2>&1; then
                echo -e "${GREEN}✓ Token validé avec succès${NC}"
                
                # Récupération des zones disponibles
                zones_response=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones" \
                    -H "Authorization: Bearer $CF_Token" \
                    -H "Content-Type: application/json")
                
                if echo "$zones_response" | jq -e '.success == true' >/dev/null 2>&1; then
                    zone_id=$(echo "$zones_response" | jq -r --arg domain "$domain" '.result[] | select(.name == $domain) | .id')
                    
                    if [ -n "$zone_id" ]; then
                        echo -e "${GREEN}✓ Domaine trouvé - Zone ID : $zone_id${NC}"
                        break
                    else
                        echo -e "${RED}⨉ Le domaine $domain n'a pas été trouvé dans votre compte Cloudflare!${NC}"
                    fi
                else
                    error_msg=$(echo "$zones_response" | jq -r '.errors[0].message' 2>/dev/null || echo "Unknown error")
                    echo -e "${RED}⨉ Échec de vérification API Token : $error_msg${NC}"
                fi
            else
                error_msg=$(echo "$api_response" | jq -r '.errors[0].message' 2>/dev/null || echo "Unknown error")
                echo -e "${RED}⨉ Échec de vérification API Token : $error_msg${NC}"
            fi
        done
        
        # Configuration sécurisée des credentials
        mkdir -p ~/.secrets/certbot/
        echo "dns_cloudflare_api_token = $CF_Token" > ~/.secrets/certbot/cloudflare.ini
        chmod 600 ~/.secrets/certbot/cloudflare.ini
        echo -e "${GREEN}✓ Configuration Cloudflare sauvegardée de manière sécurisée${NC}"
    else
        echo -e "${YELLOW}⚠ Configuration manuelle nécessaire pour $cdn_provider${NC}"
        read -p "Avez-vous configuré manuellement les DNS ? [O/n]: " dns_configured
        [[ "$dns_configured" =~ ^[Nn]$ ]] && exit 1
    fi
    
    # Obtention du certificat
    echo -e "\n${YELLOW}⚙ Obtention du certificat SSL...${NC}"
    
    # Vérification de la disponibilité de certbot
    if ! command -v certbot &>/dev/null; then
        echo -e "${RED}⨉ Certbot n'est pas installé!${NC}"
        exit 1
    fi
    
    # Arrêt propre des services
    echo -e "${BLUE}ℹ Arrêt des services utilisant les ports 80/443...${NC}"
    systemctl stop nginx xray 2>/dev/null
    
    # Construction de la commande certbot
	local cert_cmd=(certbot certonly --dns-cloudflare --dns-cloudflare-credentials ~/.secrets/certbot/cloudflare.ini \
	  -d "$domain" --non-interactive --agree-tos --email "$email" --preferred-challenges dns-01)

	echo -e "${BLUE}ℹ Exécution de: ${cert_cmd[@]}${NC}"
	if ! "${cert_cmd[@]}"; then
	  echo -e "${RED}⨉ Échec de l'obtention du certificat!${NC}"
	  echo -e "${YELLOW}Message d'erreur complet :${NC}"
	  journalctl -u certbot --no-pager -n 20 | grep -i error
	  exit 1
	fi
    
    # Exécution avec gestion des erreurs
    echo -e "${BLUE}ℹ Commande exécutée :${NC}\n${cert_cmd[*]}"
    if ! "${cert_cmd[@]}"; then
        echo -e "${RED}⨉ Échec de l'obtention du certificat SSL!${NC}"
        echo -e "${YELLOW}Consultez les logs : journalctl -u certbot --no-pager -n 30${NC}"
        
        # Tentative de diagnostic
        if journalctl -u certbot --no-pager -n 20 | grep -q "too many certificates"; then
            echo -e "${YELLOW}⚠ Vous avez dépassé la limite de certificats Let's Encrypt${NC}"
            echo -e "Solution : Attendez 1 semaine ou utilisez un autre domaine"
        elif [ "$cdn_provider" == "Cloudflare" ]; then
            echo -e "${YELLOW}⚠ Problème probable avec l'API Cloudflare${NC}"
            echo -e "Vérifiez :"
            echo -e "1. Que le domaine $domain est bien dans votre compte Cloudflare"
            echo -e "2. Que l'API Token a les permissions Zone.DNS:Edit"
            echo -e "3. Que le proxy est désactivé pendant la validation DNS"
        fi
        
        # Redémarrage des services
        systemctl start nginx xray 2>/dev/null
        exit 1
    fi
    
    # Vérification post-installation
    local cert_path="/etc/letsencrypt/live/$domain/fullchain.pem"
    if [ ! -f "$cert_path" ]; then
        echo -e "${RED}⨉ Aucun certificat valide trouvé après traitement!${NC}"
        exit 1
    fi
    
    # Affichage des infos du certificat
    echo -e "\n${GREEN}✓ Certificat SSL configuré avec succès${NC}"
    echo -e "${BLUE}ℹ Informations du certificat :${NC}"
    openssl x509 -in "$cert_path" -noout -text | grep -E "Issuer:|Subject:|Not Before|Not After|DNS:"
    
    # Configuration automatique de Nginx
    if [ -x "$(command -v nginx)" ]; then
        echo -e "\n${YELLOW}⚙ Configuration automatique de Nginx...${NC}"
        
        # Création d'un fichier de configuration minimal
        local nginx_conf="/etc/nginx/sites-available/$domain"
        cat > "$nginx_conf" <<EOF
server {
    listen 80;
    server_name $domain;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $domain;

    ssl_certificate $cert_path;
    ssl_certificate_key /etc/letsencrypt/live/$domain/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;

    location / {
        proxy_pass http://127.0.0.1:10000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
}
EOF
        
        # Activation de la configuration
        ln -sf "$nginx_conf" "/etc/nginx/sites-enabled/" 2>/dev/null
        
        # Test de configuration
        if ! nginx -t; then
            echo -e "${RED}⨉ Configuration Nginx invalide!${NC}"
            echo -e "${YELLOW}Corrigez les erreurs ci-dessus avant de continuer${NC}"
            exit 1
        fi
    fi
    
    # Redémarrage sécurisé des services
    echo -e "\n${YELLOW}⚙ Redémarrage des services...${NC}"
    if [ -x "$(command -v nginx)" ]; then
        if ! systemctl restart nginx; then
            echo -e "${RED}⨉ Échec du redémarrage de Nginx!${NC}"
            echo -e "${YELLOW}Consultez les logs : journalctl -u nginx --no-pager -n 30${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ Nginx redémarré avec succès${NC}"
    fi
    
    if systemctl is-active --quiet xray; then
        if ! systemctl restart xray; then
            echo -e "${RED}⨉ Échec du redémarrage de Xray!${NC}"
            echo -e "${YELLOW}Consultez les logs : journalctl -u xray --no-pager -n 30${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ Xray redémarré avec succès${NC}"
    fi
    
    return 0
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

# Génération de liens améliorée avec support complet
generate_links() {
    local protocol=$1
    local id=$2
    local domain=$3
    local port=$4
    local transport=$5
    local tls_mode=$6
    local path=$7  # Optionnel : pour les chemins personnalisés
    local service_name=$8  # Optionnel : nom personnalisé du service

    # Valeurs par défaut
    local ps=${service_name:-"Xray-${protocol^}"}
    local host=${domain}
    local sni=${domain}
    local flow="xtls-rprx-vision"
    local encryption="none"
    local header_type="none"
    local fp="chrome"  # Fingerprint

    # Validation des entrées
    if [[ -z "$protocol" || -z "$id" || -z "$domain" || -z "$port" ]]; then
        echo -e "${RED}⨉ Paramètres manquants pour la génération du lien${NC}" >&2
        return 1
    fi

    # Conversion en minuscules pour la cohérence
    protocol=${protocol,,}
    transport=${transport,,}
    tls_mode=${tls_mode,,}

    case "$protocol" in
        "vmess")
            # Configuration VMess complète
            local config=$(jq -n \
                --arg id "$id" \
                --arg add "$domain" \
                --arg port "$port" \
                --arg ps "$ps" \
                --arg host "$host" \
                --arg sni "$sni" \
                --arg transport "$transport" \
                --arg tls "$tls_mode" \
                --arg path "$path" \
                --arg fp "$fp" \
                '{
                    v: "2", ps: $ps, add: $add, port: $port, id: $id,
                    aid: "0", net: $transport, type: $header_type, tls: $tls,
                    host: $host, sni: $sni, path: $path, fp: $fp
                } | del(..|nulls)')  # Supprime les champs null
            
            local base64_config=$(echo -n "$config" | base64 -w 0 | tr -d '\n')
            echo "vmess://${base64_config}"
            ;;

        "vless")
            # Construction du lien VLESS avec tous paramètres
            local query_string="type=${transport}&security=${tls_mode}&flow=${flow}&encryption=${encryption}"

            # Ajout des options conditionnelles
            [[ -n "$host" ]] && query_string+="&host=${host}"
            [[ -n "$sni" ]] && query_string+="&sni=${sni}"
            [[ -n "$path" ]] && query_string+="&path=${path}"
            [[ -n "$fp" ]] && query_string+="&fp=${fp}"
            [[ "$transport" == "grpc" ]] && query_string+="&mode=gun&serviceName=${ps// /}"

            echo "vless://${id}@${domain}:${port}?${query_string}#${ps// /_}"
            ;;

        "trojan")
            # Construction du lien Trojan
            local query_string="type=${transport}&security=${tls_mode}"

            # Ajout des options conditionnelles
            [[ -n "$host" ]] && query_string+="&host=${host}"
            [[ -n "$sni" ]] && query_string+="&sni=${sni}"
            [[ -n "$path" ]] && query_string+="&path=${path}"
            [[ -n "$fp" ]] && query_string+="&fp=${fp}"
            [[ "$transport" == "grpc" ]] && query_string+="&mode=gun"

            echo "trojan://${id}@${domain}:${port}?${query_string}#${ps// /_}"
            ;;

        "shadowsocks")
            # Construction du lien Shadowsocks
            local userinfo=$(echo -n "aes-256-gcm:${id}" | base64 -w 0)
            echo "ss://${userinfo}@${domain}:${port}/?plugin=obfs-local%3Bobfs%3Dhttp#${ps// /_}"
            ;;

        *)
            echo -e "${RED}⨉ Protocole non supporté : $protocol${NC}" >&2
            return 1
            ;;
    esac
}

# Fonction helper pour afficher les liens de manière lisible
show_connection_links() {
    local protocol=$1
    local id=$2
    local domain=$3
    local port=$4
    local transport=$5
    local tls_mode=$6
    local path=${7:-""}
    local service_name=${8:-"MyXrayService"}

    echo -e "\n${GREEN}=== Liens de connexion pour ${YELLOW}${service_name}${GREEN} ===${NC}"

    # Génération du lien principal
    local main_link=$(generate_links "$protocol" "$id" "$domain" "$port" "$transport" "$tls_mode" "$path" "$service_name")
    
    echo -e "${BLUE}Lien principal :${NC}"
    echo -e "${YELLOW}${main_link}${NC}"
    
    # Génération du QR Code
    if command -v qrencode &>/dev/null; then
        echo -e "\n${BLUE}QR Code :${NC}"
        qrencode -t UTF8 <<< "$main_link"
    else
        echo -e "${YELLOW}Installez 'qrencode' pour afficher les QR Codes${NC}"
    fi

    # Lien alternatif pour clients mobiles
    case "$protocol" in
        "vmess"|"vless"|"trojan")
            local mobile_link=$(generate_links "$protocol" "$id" "$domain" "$port" "tcp" "tls" "" "${service_name}-Mobile")
            echo -e "\n${BLUE}Lien mobile (fallback TCP) :${NC}"
            echo -e "${CYAN}${mobile_link}${NC}"
            ;;
    esac

    # Informations de configuration manuelle
    echo -e "\n${BLUE}Configuration manuelle :${NC}"
    echo -e "Protocole: ${YELLOW}${protocol^^}${NC}"
    echo -e "Adresse: ${YELLOW}${domain}${NC}"
    echo -e "Port: ${YELLOW}${port}${NC}"
    echo -e "ID/Mot de passe: ${YELLOW}${id}${NC}"
    [[ -n "$host" ]] && echo -e "Host: ${YELLOW}${host}${NC}"
    [[ -n "$sni" ]] && echo -e "SNI: ${YELLOW}${sni}${NC}"
    [[ -n "$path" ]] && echo -e "Chemin: ${YELLOW}${path}${NC}"
    echo -e "Transport: ${YELLOW}${transport^^}${NC}"
    echo -e "Sécurité: ${YELLOW}${tls_mode^^}${NC}"
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

complete_installation