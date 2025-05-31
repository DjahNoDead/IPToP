#!/bin/bash

##############################################
# Xray Manager Pro - DjahNoDead 👽
# Script de gestion Xray multi-protocoles
# Version: 3.0
# Protocoles: VLESS, VMess, Trojan, Shadowsocks, Reality
# Transports: WS, TCP, gRPC, HTTP/2, HTTP Upgrade
##############################################

# Configuration
CONFIG_PATH="/usr/local/etc/xray/config.json"
XRAY_BIN="/usr/local/bin/xray"
DOMAIN=""
EMAIL=""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Ports configurables
declare -A PORTS=(
    [VLESS_WS]=10000
    [VLESS_TCP]=10001
    [VLESS_GRPC]=10002
    [VLESS_H2]=10003
    [VLESS_H2_UPGRADE]=10004
    [VMESS_WS]=10005
    [VMESS_TCP]=10006
    [TROJAN_WS]=10007
    [TROJAN_TCP]=10008
    [SHADOWSOCKS]=10009
    [REALITY]=10010
    [REALITY_UDP]=10011
)

# Initialisation des utilisateurs
declare -A USERS=(
    [VLESS_WS]=""
    [VLESS_TCP]=""
    [VLESS_GRPC]=""
    [VLESS_H2]=""
    [VLESS_H2_UPGRADE]=""
    [VMESS_WS]=""
    [VMESS_TCP]=""
    [TROJAN_WS]=""
    [TROJAN_TCP]=""
    [SHADOWSOCKS]=""
    [REALITY]=""
    [REALITY_UDP]=""
)

# Paramètres Reality
REALITY_PRIVATE_KEY=""
REALITY_PUBLIC_KEY=""
declare -a REALITY_SHORT_IDS=()

# ============================================
# FONCTIONS D'AFFICHAGE
# ============================================

# Définir la fonction input() si elle n'existe pas
if ! declare -f input >/dev/null; then
  input() {
    echo -e " ${MAGENTA}?${NC} $1"
    read -r
  }
fi

# Fonction header() corrigée
header() {
  clear
  echo -e "${BLUE}╔══════════════════════════════════════════════╗"
  echo -e "║   ${CYAN}Xray Manager Pro ${BLUE}- ${GREEN}DjahNoDead 👽${BLUE}     ║"
  echo -e "╚══════════════════════════════════════════════╝${NC}"
  
  # Charger la configuration si elle existe
  if [ -f "xray_config.sh" ]; then
    # Sauvegarde des variables actuelles
    local old_domain="$DOMAIN"
    local old_reality_pub="$REALITY_PUBLIC_KEY"
    
    # Chargement de la configuration
    source xray_config.sh 2>/dev/null
    
    # Restauration si le chargement échoue
    DOMAIN="${DOMAIN:-$old_domain}"
    REALITY_PUBLIC_KEY="${REALITY_PUBLIC_KEY:-$old_reality_pub}"
  fi
  
  echo -e " ${CYAN}Domaine: ${YELLOW}${DOMAIN:-Non configuré}${NC}"
  echo -e " ${CYAN}Reality: ${YELLOW}$([ -n "$REALITY_PUBLIC_KEY" ] && echo "Activé" || echo "Désactivé")${NC}"
  echo
}

# Fonction confirm() pour les confirmations
confirm() {
  echo -e " ${YELLOW}⚠${NC} $1"
  read -rp " Voulez-vous continuer ? (o/N) " response
  [[ "$response" =~ ^[oOyY]$ ]] && return 0 || return 1
}

# ============================================
# FONCTIONS UTILITAIRES
# ============================================

generate_uuid() {
  cat /proc/sys/kernel/random/uuid || {
    error "Erreur lors de la génération d'UUID"
    return 1
  }
}

random_password() {
  tr -dc A-Za-z0-9 </dev/urandom | head -c 16 || {
    error "Erreur lors de la génération du mot de passe"
    return 1
  }
}

generate_reality_keys() {
  local output=$(xray x25519)
  REALITY_PRIVATE_KEY=$(echo "$output" | awk '/Private key:/ {print $3}')
  REALITY_PUBLIC_KEY=$(echo "$output" | awk '/Public key:/ {print $3}')
  
  # Générer 3 short IDs aléatoires
  REALITY_SHORT_IDS=()
  for i in {1..3}; do
    REALITY_SHORT_IDS+=("$(openssl rand -hex 8)")
  done
}

generate_short_id() {
  openssl rand -hex 8 || {
    error "Erreur génération Short ID"
    return 1
  }
}

check_root() {
  if [ "$EUID" -ne 0 ]; then
    error "Ce script doit être exécuté en tant que root"
    exit 1
  fi
}

load_config() {
  if [ -f "xray_config.sh" ]; then
    source xray_config.sh
    status "Configuration chargée"
  else
    warning "Aucune configuration trouvée, utilisation des valeurs par défaut"
  fi
}

configure_nginx() {
  header
  echo -e " ${CYAN}Configuration Nginx pour multi-protocoles sur 443${NC}\n"
  
  cat > /etc/nginx/sites-available/"$DOMAIN".conf <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;

    # VLESS WS
    location /vlessws {
        proxy_pass http://127.0.0.1:443;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    # VMESS WS
    location /vmessws {
        proxy_pass http://127.0.0.1:443;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    # TROJAN WS
    location /trojanws {
        proxy_pass http://127.0.0.1:443;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    # VLESS gRPC
    location /vlessgrpc {
        grpc_pass grpc://127.0.0.1:443;
    }

    # Page par défaut
    location / {
        root /var/www/html;
        index index.html;
        return 404;
    }
}
EOF

  # Test et recharge
  if nginx -t && systemctl reload nginx; then
    status "Nginx configuré pour multi-protocoles sur 443"
  else
    error "Erreur de configuration Nginx"
    return 1
  fi
  pause
}

# ============================================
# FONCTIONS DE CONFIGURATION
# ============================================

configure_ports() {
  header
  echo -e " ${CYAN}Configuration des ports (Tous sur 443 recommandé)${NC}\n"
  
  # Définir tous les ports sur 443 par défaut
  for proto in "${!PORTS[@]}"; do
    PORTS["$proto"]=443
  done

  status "Tous les ports sont maintenant configurés sur 443"
  echo -e "\n${YELLOW}Note:${NC} Les protocoles seront différenciés par:"
  echo -e " - Path WS (/vlessws, /vmessws, etc.)"
  echo -e " - Type de transport (TCP/UDP/GRPC)"
  echo -e " - Configuration Reality"
  pause
}

configure_reality() {
  header
  echo -e " ${CYAN}Configuration de Reality${NC}\n"
  
  if [ -z "$REALITY_PUBLIC_KEY" ]; then
    echo -n " Génération des clés Reality..."
    generate_reality_keys
    echo -e "${GREEN} ✓${NC}"
  fi
  
  echo -e " ${CYAN}Clé Publique: ${YELLOW}$REALITY_PUBLIC_KEY${NC}"
  echo -e " ${CYAN}Clé Privée: ${YELLOW}$REALITY_PRIVATE_KEY${NC}"
  echo -e " ${CYAN}Short IDs:${NC}"
  for id in "${REALITY_SHORT_IDS[@]}"; do
    echo -e "  ${YELLOW}- $id${NC}"
  done
  
  echo
  read -rp " Voulez-vous générer de nouvelles clés ? (o/N) " regen
  if [[ "$regen" =~ ^[oO]$ ]]; then
    generate_reality_keys
    status "Nouvelles clés Reality générées"
  fi
  
  pause
}

save_config() {
  # Préparation des configurations
  local common_tls_settings="\"tlsSettings\": {\"certificates\": [{\"certificateFile\": \"/etc/letsencrypt/live/$DOMAIN/fullchain.pem\", \"keyFile\": \"/etc/letsencrypt/live/$DOMAIN/privkey.pem\"}]}"
  
  # Génération des configurations clients pour tous les protocoles
  local vless_ws_clients="" vless_tcp_clients="" vless_grpc_clients="" vless_h2_clients=""
  local vmess_ws_clients="" vmess_tcp_clients=""
  local trojan_ws_clients="" trojan_tcp_clients=""
  local ss_clients="" reality_clients="" reality_udp_clients=""

  # Fonction pour générer les configurations clients
  generate_clients() {
    local protocol=$1
    local clients=""
    
    for user in ${USERS[$protocol]}; do
      case $protocol in
        VLESS_WS|VLESS_TCP|VLESS_GRPC|VLESS_H2|REALITY|REALITY_UDP)
          clients+="{\"id\":\"$user\",\"flow\":\"$([ "$protocol" = "VLESS_TCP" ] && echo "xtls-rprx-vision" || [ "$protocol" = "REALITY" ] && echo "xtls-rprx-vision" || echo "")\",\"email\":\"user@${protocol,,}\"},"
          ;;
        VMESS_WS|VMESS_TCP)
          clients+="{\"id\":\"$user\",\"alterId\":0,\"email\":\"user@${protocol,,}\"},"
          ;;
        TROJAN_WS|TROJAN_TCP|SHADOWSOCKS)
          clients+="{\"password\":\"$user\",\"email\":\"user@${protocol,,}\"}$([ "$protocol" = "TROJAN_TCP" ] && echo ",\"flow\":\"xtls-rprx-direct\""),"
          ;;
      esac
    done
    echo "${clients%,}"
  }

  # Générer toutes les configurations clients
  vless_ws_clients=$(generate_clients VLESS_WS)
  vless_tcp_clients=$(generate_clients VLESS_TCP)
  vless_grpc_clients=$(generate_clients VLESS_GRPC)
  vless_h2_clients=$(generate_clients VLESS_H2)
  vmess_ws_clients=$(generate_clients VMESS_WS)
  vmess_tcp_clients=$(generate_clients VMESS_TCP)
  trojan_ws_clients=$(generate_clients TROJAN_WS)
  trojan_tcp_clients=$(generate_clients TROJAN_TCP)
  ss_clients=$(generate_clients SHADOWSOCKS)
  reality_clients=$(generate_clients REALITY)
  reality_udp_clients=$(generate_clients REALITY_UDP)

  # Écriture du fichier de configuration
  cat > "$CONFIG_PATH" <<EOF
{
  "log": {"loglevel": "warning"},
  "inbounds": [
    {
      "port": 443,
      "protocol": "vless",
      "settings": {"clients": [$vless_ws_clients], "decryption": "none"},
      "streamSettings": {
        "network": "ws",
        "security": "tls",
        $common_tls_settings,
        "wsSettings": {"path": "/vlessws"}
      }
    },
    {
      "port": 443,
      "protocol": "vless",
      "settings": {"clients": [$vless_tcp_clients], "decryption": "none"},
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        $common_tls_settings
      }
    },
    {
      "port": 443,
      "protocol": "vmess",
      "settings": {"clients": [$vmess_ws_clients]},
      "streamSettings": {
        "network": "ws",
        "security": "tls",
        $common_tls_settings,
        "wsSettings": {"path": "/vmessws"}
      }
    },
    {
      "port": 443,
      "protocol": "vmess",
      "settings": {"clients": [$vmess_tcp_clients]},
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        $common_tls_settings
      }
    },
    {
      "port": 443,
      "protocol": "trojan",
      "settings": {"clients": [$trojan_ws_clients]},
      "streamSettings": {
        "network": "ws",
        "security": "tls",
        $common_tls_settings,
        "wsSettings": {"path": "/trojanws"}
      }
    },
    {
      "port": 443,
      "protocol": "trojan",
      "settings": {"clients": [$trojan_tcp_clients]},
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        $common_tls_settings
      }
    },
    {
      "port": 443,
      "protocol": "vless",
      "settings": {"clients": [$vless_grpc_clients], "decryption": "none"},
      "streamSettings": {
        "network": "grpc",
        "security": "tls",
        $common_tls_settings,
        "grpcSettings": {"serviceName": "vlessgrpc"}
      }
    },
    {
      "port": 443,
      "protocol": "vless",
      "settings": {"clients": [$vless_h2_clients], "decryption": "none"},
      "streamSettings": {
        "network": "h2",
        "security": "tls",
        $common_tls_settings,
        "httpSettings": {"host": ["$DOMAIN"], "path": "/vlessh2"}
      }
    },
    {
      "port": 443,
      "protocol": "shadowsocks",
      "settings": {
        "clients": [$ss_clients],
        "method": "aes-128-gcm"
      },
      "streamSettings": {"network": "tcp"}
    },
    {
      "port": 443,
      "protocol": "vless",
      "settings": {"clients": [$reality_clients], "decryption": "none"},
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "show": false,
          "dest": "$DOMAIN:443",
          "xver": 1,
          "serverNames": ["$DOMAIN"],
          "privateKey": "$REALITY_PRIVATE_KEY",
          "shortIds": [$(printf "\"%s\"," "${REALITY_SHORT_IDS[@]}" | sed 's/,$//')]
        }
      }
    },
    {
      "port": 443,
      "protocol": "vless",
      "settings": {"clients": [$reality_udp_clients], "decryption": "none"},
      "streamSettings": {
        "network": "udp",
        "security": "reality",
        "realitySettings": {
          "show": false,
          "dest": "$DOMAIN:443",
          "xver": 1,
          "serverNames": ["$DOMAIN"],
          "privateKey": "$REALITY_PRIVATE_KEY",
          "shortIds": [$(printf "\"%s\"," "${REALITY_SHORT_IDS[@]}" | sed 's/,$//')]
        }
      }
    }
  ],
  "outbounds": [
    {"protocol": "freedom", "tag": "direct"},
    {"protocol": "blackhole", "tag": "block"}
  ],
  "routing": {
    "domainStrategy": "IPIfNonMatch",
    "rules": [
      {
        "type": "field",
        "ip": ["geoip:private"],
        "outboundTag": "block"
      },
      {
        "type": "field",
        "domain": ["geosite:category-ads-all"],
        "outboundTag": "block"
      }
    ]
  }
}
EOF

  # Vérification de la configuration
  if ! jq empty "$CONFIG_PATH" &>/dev/null; then
    error "Configuration JSON invalide"
    return 1
  fi

  # Sauvegarde des paramètres
  local saved_vars=(
    PORTS USERS REALITY_PRIVATE_KEY 
    REALITY_PUBLIC_KEY REALITY_SHORT_IDS DOMAIN
  )
  
  {
    for var in "${saved_vars[@]}"; do
      declare -p "$var"
    done
  } > xray_config.sh && status "Configuration multi-protocoles sauvegardée" || {
    error "Erreur lors de la sauvegarde"
    return 1
  }

  return 0
}

# ============================================
# FONCTIONS PRINCIPALES
# ============================================

install_all() {
  header
  echo -e " ${CYAN}Installation complète (Multi-protocole sur 443)${NC}\n"
  
  if [ -f "$CONFIG_PATH" ]; then
    if ! confirm "Xray semble déjà être installé. Voulez-vous vraiment continuer ?"; then
      return
    fi
  fi

  # Étape 1: Mise à jour système
  echo -n " [1/9] Mise à jour des paquets..."
  if apt update &>/dev/null && apt upgrade -y &>/dev/null; then
    echo -e "${GREEN} ✓${NC}"
  else
    error "Échec de la mise à jour"
    return 1
  fi

  # Étape 2: Installation dépendances
  echo -n " [2/9] Installation des dépendances..."
  if apt install -y curl wget unzip nginx socat ufw certbot python3-certbot-nginx fail2ban jq openssl &>/dev/null; then
    echo -e "${GREEN} ✓${NC}"
  else
    error "Échec de l'installation des dépendances"
    return 1
  fi

  # Étape 3: Configuration UFW
  echo -n " [3/9] Configuration du pare-feu (443 seulement)..."
  ufw allow 'OpenSSH' &>/dev/null
  ufw allow 80/tcp &>/dev/null   # Pour Certbot
  ufw allow 443/tcp &>/dev/null  # Seul port ouvert
  ufw allow 443/udp &>/dev/null  # Pour Reality UDP
  if ufw --force enable &>/dev/null; then
    echo -e "${GREEN} ✓${NC}"
  else
    error "Échec de la configuration du pare-feu"
    return 1
  fi

  # Étape 4: Configuration Fail2ban
  echo -n " [4/9] Configuration de Fail2ban..."
  if systemctl enable --now fail2ban &>/dev/null; then
    echo -e "${GREEN} ✓${NC}"
  else
    error "Échec de la configuration Fail2ban"
    return 1
  fi

  # Étape 5: Installation Xray
  echo -n " [5/9] Installation de Xray..."
  if bash <(curl -Ls https://raw.githubusercontent.com/XTLS/Xray-install/main/install-release.sh) &>/dev/null; then
    echo -e "${GREEN} ✓${NC}"
  else
    error "Échec de l'installation de Xray"
    return 1
  fi

  # Étape 6: Configuration des répertoires
  mkdir -p /usr/local/etc/xray /var/log/xray

  # Étape 7: Configuration automatique des ports sur 443
  echo -n " [6/9] Configuration des ports (unifié sur 443)..."
  declare -A PORTS=(
    [VLESS_WS]=443
    [VLESS_TCP]=443
    [VLESS_GRPC]=443
    [VLESS_H2]=443
    [VMESS_WS]=443
    [VMESS_TCP]=443
    [TROJAN_WS]=443
    [TROJAN_TCP]=443
    [SHADOWSOCKS]=443
    [REALITY]=443
    [REALITY_UDP]=443
  )
  echo -e "${GREEN} ✓${NC}"

  # Étape 8: Configuration Reality
  echo -n " [7/9] Configuration de Reality..."
  generate_reality_keys
  echo -e "${GREEN} ✓${NC}"

  # Étape 9: Configuration du domaine
  header
  while [[ -z "$DOMAIN" ]]; do
    input "Entrez le nom de domaine (ex: proxy.exemple.com) : "
    read -r DOMAIN
  done

  while [[ ! "$EMAIL" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; do
    input "Entrez votre email valide (pour Certbot) : "
    read -r EMAIL
  done

  # Étape 10: Configuration Nginx et certificat
  echo -n " [8/9] Configuration du certificat TLS..."
  rm -f /etc/nginx/sites-enabled/default
  cat > /etc/nginx/sites-available/"$DOMAIN".conf <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    location / { return 301 https://\$host\$request_uri; }
}
EOF
  ln -sf /etc/nginx/sites-available/"$DOMAIN".conf /etc/nginx/sites-enabled/
  
  if certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive &>/dev/null; then
    echo -e "${GREEN} ✓${NC}"
  else
    error "Échec de l'obtention du certificat TLS"
    return 1
  fi

  # Étape 11: Configuration finale Nginx pour multi-protocole
  echo -n " [9/9] Configuration Nginx multi-protocole..."
  cat > /etc/nginx/sites-available/"$DOMAIN".conf <<EOF
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;

    # VLESS WS
    location /vlessws {
        proxy_pass http://127.0.0.1:443;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    # VMess WS
    location /vmessws {
        proxy_pass http://127.0.0.1:443;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    # Trojan WS
    location /trojanws {
        proxy_pass http://127.0.0.1:443;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    # VLESS gRPC
    location /vlessgrpc {
        grpc_pass grpc://127.0.0.1:443;
    }

    # VLESS HTTP/2
    location /vlessh2 {
        proxy_pass http://127.0.0.1:443;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host \$host;
    }

    # Page par défaut
    location / {
        root /var/www/html;
        index index.html;
        return 404;
    }
}
EOF

  if systemctl reload nginx &>/dev/null; then
    echo -e "${GREEN} ✓${NC}"
  else
    error "Échec de la configuration Nginx"
    return 1
  fi

  # Création des utilisateurs par défaut
  status "Création des utilisateurs par défaut..."
  USERS["VLESS_WS"]=$(generate_uuid) || return 1
  USERS["VLESS_TCP"]=$(generate_uuid) || return 1
  USERS["VLESS_GRPC"]=$(generate_uuid) || return 1
  USERS["VLESS_H2"]=$(generate_uuid) || return 1
  USERS["VMESS_WS"]=$(generate_uuid) || return 1
  USERS["VMESS_TCP"]=$(generate_uuid) || return 1
  USERS["TROJAN_WS"]=$(random_password) || return 1
  USERS["TROJAN_TCP"]=$(random_password) || return 1
  USERS["SHADOWSOCKS"]=$(random_password) || return 1
  USERS["REALITY"]=$(generate_uuid) || return 1
  USERS["REALITY_UDP"]=$(generate_uuid) || return 1

  # Sauvegarde de la configuration
  save_config || {
    error "Échec de la sauvegarde de la configuration"
    return 1
  }

  # Configuration du service Xray
  cat > /etc/systemd/system/xray.service <<EOF
[Unit]
Description=Xray Service
After=network.target nginx.service

[Service]
User=nobody
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
ExecStart=$XRAY_BIN run -config $CONFIG_PATH
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable --now xray &>/dev/null && status "Service Xray activé"

  # Finalisation
  header
  status "Installation terminée avec succès"
  echo -e " ${CYAN}Tous les protocoles fonctionnent sur le port 443${NC}"
  echo -e " ${YELLOW}Configuration des chemins :${NC}"
  echo -e "  - VLESS WS: /vlessws"
  echo -e "  - VMESS WS: /vmessws"
  echo -e "  - TROJAN WS: /trojanws"
  echo -e "  - VLESS gRPC: /vlessgrpc"
  
  generate_links
  pause
}

# Fin d'installation
header
status "Installation terminée avec succès"
echo -e " ${CYAN}Un utilisateur par protocole a été créé${NC}"

# Afficher directement les configurations
echo -e "\n${YELLOW}=== CONFIGURATIONS GÉNÉRÉES ===${NC}"
generate_links | tee -a config_clients.txt
pause

# ============================================
# FONCTIONS DE GESTION DES UTILISATEURS
# ============================================

add_user() {
    header
    echo -e " ${CYAN}Ajouter un utilisateur${NC}\n"
    echo -e " ${BLUE}1.${NC} VLESS WS (Recommandé)"
    echo -e " ${BLUE}2.${NC} VLESS TCP"
    echo -e " ${BLUE}3.${NC} VLESS gRPC"
    echo -e " ${BLUE}4.${NC} VLESS HTTP/2"
    echo -e " ${BLUE}5.${NC} VLESS HTTP Upgrade"
    echo -e " ${BLUE}6.${NC} VMess WS"
    echo -e " ${BLUE}7.${NC} VMess TCP"
    echo -e " ${BLUE}8.${NC} Trojan WS"
    echo -e " ${BLUE}9.${NC} Trojan TCP"
    echo -e " ${BLUE}10.${NC} Shadowsocks"
    echo -e " ${BLUE}11.${NC} Reality TCP"
    echo -e " ${BLUE}12.${NC} Reality UDP"
    echo -e " ${BLUE}0.${NC} Retour\n"
    
    read -rp " Choisissez le type d'utilisateur : " choice
    
    case $choice in
        1)
            id=$(generate_uuid) || return
            USERS[VLESS_WS]+=" $id"
            status "Nouvel utilisateur VLESS WS :"
            echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
            echo -e " ${YELLOW}Port: ${CYAN}${PORTS[VLESS_WS]}${NC}"
            echo -e " ${YELLOW}Path: ${CYAN}/vlessws${NC}"
            echo -e " ${YELLOW}Flow: ${CYAN}xtls-rprx-vision${NC}"
            ;;
        2)
            id=$(generate_uuid) || return
            USERS[VLESS_TCP]+=" $id"
            status "Nouvel utilisateur VLESS TCP :"
            echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
            echo -e " ${YELLOW}Port: ${CYAN}${PORTS[VLESS_TCP]}${NC}"
            echo -e " ${YELLOW}Flow: ${CYAN}xtls-rprx-vision${NC}"
            ;;
        3)
            id=$(generate_uuid) || return
            USERS[VLESS_GRPC]+=" $id"
            status "Nouvel utilisateur VLESS gRPC :"
            echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
            echo -e " ${YELLOW}Port: ${CYAN}${PORTS[VLESS_GRPC]}${NC}"
            echo -e " ${YELLOW}ServiceName: ${CYAN}vlessgrpc${NC}"
            ;;
        4)
            id=$(generate_uuid) || return
            USERS[VLESS_H2]+=" $id"
            status "Nouvel utilisateur VLESS HTTP/2 :"
            echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
            echo -e " ${YELLOW}Port: ${CYAN}${PORTS[VLESS_H2]}${NC}"
            echo -e " ${YELLOW}Path: ${CYAN}/vlessh2${NC}"
            ;;
        5)
            id=$(generate_uuid) || return
            USERS[VLESS_H2_UPGRADE]+=" $id"
            status "Nouvel utilisateur VLESS HTTP Upgrade :"
            echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
            echo -e " ${YELLOW}Port: ${CYAN}${PORTS[VLESS_H2_UPGRADE]}${NC}"
            echo -e " ${YELLOW}Path: ${CYAN}/httpupgrade${NC}"
            ;;
        6)
            id=$(generate_uuid) || return
            USERS[VMESS_WS]+=" $id"
            status "Nouvel utilisateur VMess WS :"
            echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
            echo -e " ${YELLOW}Port: ${CYAN}${PORTS[VMESS_WS]}${NC}"
            echo -e " ${YELLOW}Path: ${CYAN}/vmessws${NC}"
            ;;
        7)
            id=$(generate_uuid) || return
            USERS[VMESS_TCP]+=" $id"
            status "Nouvel utilisateur VMess TCP :"
            echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
            echo -e " ${YELLOW}Port: ${CYAN}${PORTS[VMESS_TCP]}${NC}"
            ;;
        8)
            pwd=$(random_password) || return
            USERS[TROJAN_WS]+=" $pwd"
            status "Nouvel utilisateur Trojan WS :"
            echo -e " ${YELLOW}Mot de passe: ${CYAN}$pwd${NC}"
            echo -e " ${YELLOW}Port: ${CYAN}${PORTS[TROJAN_WS]}${NC}"
            echo -e " ${YELLOW}Path: ${CYAN}/trojanws${NC}"
            ;;
        9)
            pwd=$(random_password) || return
            USERS[TROJAN_TCP]+=" $pwd"
            status "Nouvel utilisateur Trojan TCP :"
            echo -e " ${YELLOW}Mot de passe: ${CYAN}$pwd${NC}"
            echo -e " ${YELLOW}Port: ${CYAN}${PORTS[TROJAN_TCP]}${NC}"
            echo -e " ${YELLOW}Flow: ${CYAN}xtls-rprx-direct${NC}"
            ;;
        10)
            pwd=$(random_password) || return
            USERS[SHADOWSOCKS]+=" $pwd"
            status "Nouvel utilisateur Shadowsocks :"
            echo -e " ${YELLOW}Mot de passe: ${CYAN}$pwd${NC}"
            echo -e " ${YELLOW}Port: ${CYAN}${PORTS[SHADOWSOCKS]}${NC}"
            echo -e " ${YELLOW}Méthode: ${CYAN}aes-128-gcm${NC}"
            ;;
        11)
            id=$(generate_uuid) || return
            USERS[REALITY]+=" $id"
            status "Nouvel utilisateur Reality TCP :"
            echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
            echo -e " ${YELLOW}Port: ${CYAN}${PORTS[REALITY]}${NC}"
            echo -e " ${YELLOW}Public Key: ${CYAN}$REALITY_PUBLIC_KEY${NC}"
            echo -e " ${YELLOW}Short ID: ${CYAN}${REALITY_SHORT_IDS[0]}${NC}"
            echo -e " ${YELLOW}Fingerprint: ${CYAN}chrome${NC}"
            ;;
        12)
            id=$(generate_uuid) || return
            USERS[REALITY_UDP]+=" $id"
            status "Nouvel utilisateur Reality UDP :"
            echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
            echo -e " ${YELLOW}Port: ${CYAN}${PORTS[REALITY_UDP]}${NC}"
            echo -e " ${YELLOW}Public Key: ${CYAN}$REALITY_PUBLIC_KEY${NC}"
            echo -e " ${YELLOW}Short ID: ${CYAN}${REALITY_SHORT_IDS[0]}${NC}"
            ;;
        0) return ;;
        *) 
            error "Option invalide"
            pause
            return 1
            ;;
    esac
    
    save_config || error "Erreur lors de la sauvegarde"
    pause
}

remove_user_type() {
    local protocol_name=$1
    local protocol_key=$2
    
    header
    echo -e " ${CYAN}Supprimer un utilisateur $protocol_name${NC}\n"
    
    # Convertir la chaîne en tableau
    IFS=' ' read -ra users <<< "${USERS[$protocol_key]}"
    
    if [ ${#users[@]} -eq 0 ]; then
        error "Aucun utilisateur à supprimer"
        pause
        return
    fi
    
    echo -e " ${YELLOW}Utilisateurs disponibles:${NC}"
    for i in "${!users[@]}"; do
        echo -e " ${BLUE}$((i+1)).${NC} ${users[i]}"
    done
    
    read -rp " Choisissez l'utilisateur à supprimer (1-${#users[@]}) : " choice
    
    if [[ ! "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt ${#users[@]} ]; then
        error "Choix invalide"
        pause
        return
    fi
    
    # Supprimer l'utilisateur
    new_users=()
    for i in "${!users[@]}"; do
        if [ $((i+1)) -ne "$choice" ]; then
            new_users+=("${users[i]}")
        fi
    done
    
    USERS[$protocol_key]="${new_users[*]}"
    status "Utilisateur supprimé avec succès"
}

remove_user() {
    header
    echo -e " ${CYAN}Supprimer un utilisateur${NC}\n"
    echo -e " ${BLUE}1.${NC} VLESS WS"
    echo -e " ${BLUE}2.${NC} VLESS TCP"
    echo -e " ${BLUE}3.${NC} VLESS gRPC"
    echo -e " ${BLUE}4.${NC} VLESS HTTP/2"
    echo -e " ${BLUE}5.${NC} VLESS HTTP Upgrade"
    echo -e " ${BLUE}6.${NC} VMess WS"
    echo -e " ${BLUE}7.${NC} VMess TCP"
    echo -e " ${BLUE}8.${NC} Trojan WS"
    echo -e " ${BLUE}9.${NC} Trojan TCP"
    echo -e " ${BLUE}10.${NC} Shadowsocks"
    echo -e " ${BLUE}11.${NC} Reality TCP"
    echo -e " ${BLUE}12.${NC} Reality UDP"
    echo -e " ${BLUE}0.${NC} Retour\n"
    
    read -rp " Choisissez le type d'utilisateur : " choice
    
    case $choice in
        1) remove_user_type "VLESS WS" "VLESS_WS" ;;
        2) remove_user_type "VLESS TCP" "VLESS_TCP" ;;
        3) remove_user_type "VLESS gRPC" "VLESS_GRPC" ;;
        4) remove_user_type "VLESS HTTP/2" "VLESS_H2" ;;
        5) remove_user_type "VLESS HTTP Upgrade" "VLESS_H2_UPGRADE" ;;
        6) remove_user_type "VMess WS" "VMESS_WS" ;;
        7) remove_user_type "VMess TCP" "VMESS_TCP" ;;
        8) remove_user_type "Trojan WS" "TROJAN_WS" ;;
        9) remove_user_type "Trojan TCP" "TROJAN_TCP" ;;
        10) remove_user_type "Shadowsocks" "SHADOWSOCKS" ;;
        11) remove_user_type "Reality TCP" "REALITY" ;;
        12) remove_user_type "Reality UDP" "REALITY_UDP" ;;
        0) return ;;
        *) 
            error "Option invalide"
            pause
            ;;
    esac
    
    save_config
    pause
}

# ============================================
# GENERATION DES LIENS CLIENTS
# ============================================

generate_links() {
  header
  
  # Vérification du domaine
  if [ -z "$DOMAIN" ]; then
    error "Domaine non configuré - Impossible de générer les liens"
    pause
    return 1
  fi

  echo -e "\n${CYAN}=== CONFIGURATIONS GÉNÉRÉES ===${NC}"
  
  # Liste de tous les protocoles à afficher
  local protocols=(
    "VLESS_WS:/vlessws"
    "VLESS_TCP:"
    "VLESS_GRPC:/vlessgrpc"
    "VMESS_WS:/vmessws"
    "TROJAN_WS:/trojanws"
    "SHADOWSOCKS:"
    "REALITY:"
  )

  for proto_path in "${protocols[@]}"; do
    local proto=${proto_path%:*}
    local path=${proto_path#*:}
    local users=${USERS[$proto]}
    
    if [ -n "$users" ]; then
      echo -e "\n${YELLOW}=== $proto ===${NC}"
      
      if [[ "$proto" == "SHADOWSOCKS" ]]; then
        for pwd in $users; do
          echo "ss://$(echo -n "aes-128-gcm:$pwd" | base64)@$DOMAIN:443#$DOMAIN-SS"
        done
      elif [[ "$proto" == "REALITY" ]]; then
        for uuid in $users; do
          echo "vless://$uuid@$DOMAIN:443?type=tcp&security=reality&pbk=$REALITY_PUBLIC_KEY&sid=${REALITY_SHORT_IDS[0]}#$DOMAIN-REALITY"
        done
      elif [[ "$proto" == "VLESS_TCP" ]]; then
        for uuid in $users; do
          echo "vless://$uuid@$DOMAIN:443?security=tls&flow=xtls-rprx-vision#$DOMAIN-VLESS-TCP"
        done
      else
        for user in $users; do
          if [[ "$proto" == "VMESS_WS" ]]; then
            local vmess_json=$(jq -n \
              --arg uuid "$user" \
              --arg host "$DOMAIN" \
              '{
                v: "2", ps: "vmess-ws", add: $host,
                port: "443", id: $uuid, aid: "0",
                net: "ws", type: "none", host: $host,
                path: "/vmessws", tls: "tls"
              }')
            echo "vmess://$(echo "$vmess_json" | base64 -w 0)"
          else
            echo "vless://$user@$DOMAIN:443?type=ws&security=tls&path=%2F${path#/}#$DOMAIN-$proto"
          fi
        done
      fi
    fi
  done

  echo -e "\n${CYAN}=== INSTRUCTIONS ===${NC}"
  echo "- Reality: Nécessite Xray v1.8.0+ ou Shadowrocket"
  echo "- gRPC: Client compatible requis"
  echo "- WS: Compatible avec la plupart des clients"
  
  # Sauvegarde dans un fichier
  {
    echo "=== Configurations Xray ==="
    echo "Généré le: $(date)"
    echo "Domaine: $DOMAIN"
    echo "Reality Key: $REALITY_PUBLIC_KEY"
    echo "Short IDs: ${REALITY_SHORT_IDS[*]}"
    echo
    generate_links
  } > config_clients.txt

  echo -e "\n${GREEN}✓${NC} Configurations sauvegardées dans ${YELLOW}config_clients.txt${NC}"
  pause
}

# ============================================
# FONCTIONS D'AFFICHAGE
# ============================================

show_config() {
  header
  echo -e " ${CYAN}Configuration Multi-Port 443${NC}\n"
  
  echo -e " ${YELLOW}=== Tous les protocoles écoutent sur le port : 443 ===${NC}"
  echo -e " ${BLUE}•${NC} Différenciation par chemins :"
  echo -e "   ${GREEN}-${NC} /vlessws (VLESS WS)"
  echo -e "   ${GREEN}-${NC} /vmessws (VMESS WS)"
  echo -e "   ${GREEN}-${NC} /trojanws (Trojan WS)"
  echo -e "   ${GREEN}-${NC} vlessgrpc (VLESS gRPC)"
  
  echo -e "\n ${YELLOW}=== Utilisateurs ===${NC}"
  for proto in "${!USERS[@]}"; do
    if [ -n "${USERS[$proto]}" ]; then
      echo -e " ${BLUE}•${NC} $proto :"
      for user in ${USERS[$proto]}; do
        echo -e "   ${GREEN}-${NC} $user"
      done
    fi
  done
  
  if [ -n "$REALITY_PUBLIC_KEY" ]; then
    echo -e "\n ${YELLOW}=== Reality ===${NC}"
    echo -e " ${BLUE}•${NC} Public Key: $REALITY_PUBLIC_KEY"
    echo -e " ${BLUE}•${NC} Short IDs: ${REALITY_SHORT_IDS[*]}"
  fi
  
  pause
}

# ============================================
# MENUS
# ============================================

user_menu() {
  while true; do
    header
    echo -e " ${CYAN}Gestion des utilisateurs${NC}\n"
    echo -e " ${BLUE}1.${NC} Ajouter un utilisateur"
    echo -e " ${BLUE}2.${NC} Supprimer un utilisateur"
    echo -e " ${BLUE}3.${NC} Afficher les utilisateurs"
    echo -e " ${BLUE}0.${NC} Retour\n"
    
    read -rp " Choisissez une option (0-3) : " choice
    
    case $choice in
      1) add_user ;;
      2) remove_user ;;
      3) show_config ;;
      0) break ;;
      *) 
        error "Option invalide"
        pause
        ;;
    esac
  done
}

advanced_menu() {
  while true; do
    header
    echo -e " ${CYAN}Paramètres avancés${NC}\n"
    echo -e " ${BLUE}1.${NC} Configurer les ports"
    echo -e " ${BLUE}2.${NC} Configurer Reality"
    echo -e " ${BLUE}3.${NC} Reconfigurer Nginx"
    echo -e " ${BLUE}4.${NC} Redémarrer Xray"
    echo -e " ${BLUE}0.${NC} Retour\n"
    
    read -rp " Choisissez une option (0-4) : " choice
    
    case $choice in
      1) configure_ports ;;
      2) configure_reality ;;
      3) configure_nginx ;;
      4) systemctl restart xray && status "Xray redémarré" || error "Erreur" ;;
      0) break ;;
      *) 
        error "Option invalide"
        pause
        ;;
    esac
  done
}

main_menu() {
  while true; do
    header
    echo -e " ${CYAN}Menu Principal${NC}\n"
    echo -e " ${BLUE}1.${NC} Installation complète"
    echo -e " ${BLUE}2.${NC} Gérer les utilisateurs"
    echo -e " ${BLUE}3.${NC} Générer les configurations"
    echo -e " ${BLUE}4.${NC} Paramètres avancés"
    echo -e " ${BLUE}0.${NC} Quitter\n"
    
    read -rp " Choisissez une option (0-4) : " choice
    
    case $choice in
      1) install_all ;;
      2) user_menu ;;
      3) generate_links ;;
      4) advanced_menu ;;
      0) 
        header
        echo -e " ${GREEN}Merci d'avoir utilisé Xray Manager Pro!${NC}"
        echo -e " ${CYAN}Crédits: ${YELLOW}DjahNoDead 👽${NC}\n"
        exit 0 
        ;;
      *) 
        error "Option invalide"
        pause
        ;;
    esac
  done
}

# ============================================
# POINT D'ENTRÉE
# ============================================

check_root
load_config

while true; do
  main_menu
done