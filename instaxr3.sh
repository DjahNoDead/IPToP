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
  ["VLESS_WS"]=10000
  ["VLESS_TCP"]=10001
  ["VLESS_GRPC"]=10002
  ["VLESS_H2"]=10003
  ["VMESS_WS"]=10004
  ["VMESS_TCP"]=10005
  ["TROJAN_WS"]=10006
  ["TROJAN_TCP"]=10007
  ["SHADOWSOCKS"]=10008
  ["REALITY"]=10009
  ["REALITY_UDP"]=10010
)

# Listes utilisateurs
declare -A USERS=(
  ["VLESS_WS"]=()
  ["VLESS_TCP"]=()
  ["VLESS_GRPC"]=()
  ["VLESS_H2"]=()
  ["VMESS_WS"]=()
  ["VMESS_TCP"]=()
  ["TROJAN_WS"]=()
  ["TROJAN_TCP"]=()
  ["SHADOWSOCKS"]=()
  ["REALITY"]=()
  ["REALITY_UDP"]=()
)

# Paramètres Reality
REALITY_PRIVATE_KEY=""
REALITY_PUBLIC_KEY=""
REALITY_SHORT_IDS=()

# ============================================
# FONCTIONS D'AFFICHAGE
# ============================================

header() {
  clear
  echo -e "${BLUE}╔══════════════════════════════════════════════╗"
  echo -e "║   ${CYAN}Xray Manager Pro ${BLUE}- ${GREEN}DjahNoDead 👽${BLUE}     ║"
  echo -e "╚══════════════════════════════════════════════╝${NC}"
  echo -e " ${CYAN}Domaine: ${YELLOW}${DOMAIN:-Non configuré}${NC}"
  echo -e " ${CYAN}Reality: ${YELLOW}$([ -n "$REALITY_PUBLIC_KEY" ] && echo "Activé" || echo "Désactivé")${NC}"
  echo
}

status() {
  echo -e " ${GREEN}✓${NC} $1"
}

error() {
  echo -e " ${RED}✗${NC} $1" >&2
}

warning() {
  echo -e " ${YELLOW}⚠${NC} $1"
}

input() {
  echo -e " ${MAGENTA}?${NC} $1"
}

pause() {
  echo
  read -rp " Appuyez sur ${CYAN}[Entrée]${NC} pour continuer..." dummy
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

# ============================================
# FONCTIONS DE CONFIGURATION
# ============================================

configure_ports() {
  header
  echo -e " ${CYAN}Configuration des ports${NC}\n"
  echo -e " ${YELLOW}Laissez vide pour conserver les valeurs actuelles${NC}\n"
  
  for proto in "${!PORTS[@]}"; do
    input "Port $proto (actuel: ${PORTS[$proto]}) : "
    read -r input
    [[ -n "$input" ]] && PORTS["$proto"]=$input
  done
  
  status "Ports mis à jour :"
  for proto in "${!PORTS[@]}"; do
    echo -e "  ${CYAN}•${NC} $proto : ${YELLOW}${PORTS[$proto]}${NC}"
  done
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
  # Préparation des configurations pour chaque protocole
  local vless_ws_clients=""
  local vless_tcp_clients=""
  local vless_grpc_clients=""
  local vless_h2_clients=""
  local vmess_ws_clients=""
  local vmess_tcp_clients=""
  local trojan_ws_clients=""
  local trojan_tcp_clients=""
  local ss_clients=""
  local reality_clients=""
  local reality_udp_clients=""

  # Générer les configurations clients pour chaque protocole
  for proto in "${!USERS[@]}"; do
    case $proto in
      VLESS_WS)
        for uuid in "${USERS[VLESS_WS][@]}"; do
          vless_ws_clients+="{\"id\":\"$uuid\",\"flow\":\"xtls-rprx-vision\",\"email\":\"user@vless-ws\"},"
        done
        vless_ws_clients=${vless_ws_clients%,}
        ;;
      VLESS_TCP)
        for uuid in "${USERS[VLESS_TCP][@]}"; do
          vless_tcp_clients+="{\"id\":\"$uuid\",\"flow\":\"xtls-rprx-vision\",\"email\":\"user@vless-tcp\"},"
        done
        vless_tcp_clients=${vless_tcp_clients%,}
        ;;
      VLESS_GRPC)
        for uuid in "${USERS[VLESS_GRPC][@]}"; do
          vless_grpc_clients+="{\"id\":\"$uuid\",\"flow\":\"\",\"email\":\"user@vless-grpc\"},"
        done
        vless_grpc_clients=${vless_grpc_clients%,}
        ;;
      VLESS_H2)
        for uuid in "${USERS[VLESS_H2][@]}"; do
          vless_h2_clients+="{\"id\":\"$uuid\",\"flow\":\"\",\"email\":\"user@vless-h2\"},"
        done
        vless_h2_clients=${vless_h2_clients%,}
        ;;
      VMESS_WS)
        for uuid in "${USERS[VMESS_WS][@]}"; do
          vmess_ws_clients+="{\"id\":\"$uuid\",\"alterId\":0,\"email\":\"user@vmess-ws\"},"
        done
        vmess_ws_clients=${vmess_ws_clients%,}
        ;;
      VMESS_TCP)
        for uuid in "${USERS[VMESS_TCP][@]}"; do
          vmess_tcp_clients+="{\"id\":\"$uuid\",\"alterId\":0,\"email\":\"user@vmess-tcp\"},"
        done
        vmess_tcp_clients=${vmess_tcp_clients%,}
        ;;
      TROJAN_WS)
        for pwd in "${USERS[TROJAN_WS][@]}"; do
          trojan_ws_clients+="{\"password\":\"$pwd\",\"email\":\"user@trojan-ws\"},"
        done
        trojan_ws_clients=${trojan_ws_clients%,}
        ;;
      TROJAN_TCP)
        for pwd in "${USERS[TROJAN_TCP][@]}"; do
          trojan_tcp_clients+="{\"password\":\"$pwd\",\"flow\":\"xtls-rprx-direct\",\"email\":\"user@trojan-tcp\"},"
        done
        trojan_tcp_clients=${trojan_tcp_clients%,}
        ;;
      SHADOWSOCKS)
        for pwd in "${USERS[SHADOWSOCKS][@]}"; do
          ss_clients+="{\"password\":\"$pwd\",\"method\":\"aes-128-gcm\",\"email\":\"user@ss\"},"
        done
        ss_clients=${ss_clients%,}
        ;;
      REALITY)
        for uuid in "${USERS[REALITY][@]}"; do
          reality_clients+="{\"id\":\"$uuid\",\"flow\":\"xtls-rprx-vision\",\"email\":\"user@reality\"},"
        done
        reality_clients=${reality_clients%,}
        ;;
      REALITY_UDP)
        for uuid in "${USERS[REALITY_UDP][@]}"; do
          reality_udp_clients+="{\"id\":\"$uuid\",\"flow\":\"\",\"email\":\"user@reality-udp\"},"
        done
        reality_udp_clients=${reality_udp_clients%,}
        ;;
    esac
  done

  # Écriture du fichier de configuration
  cat > "$CONFIG_PATH" <<EOF
{
  "log": {"loglevel": "warning"},
  "inbounds": [
    {
      "port": ${PORTS[VLESS_WS]},
      "protocol": "vless",
      "settings": {"clients": [$vless_ws_clients], "decryption": "none"},
      "streamSettings": {
        "network": "ws",
        "security": "tls",
        "tlsSettings": {"certificates": [{"certificateFile": "/etc/letsencrypt/live/$DOMAIN/fullchain.pem", "keyFile": "/etc/letsencrypt/live/$DOMAIN/privkey.pem"}]},
        "wsSettings": {"path": "/vlessws"}
      }
    },
    {
      "port": ${PORTS[VLESS_TCP]},
      "protocol": "vless",
      "settings": {"clients": [$vless_tcp_clients], "decryption": "none"},
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {"certificates": [{"certificateFile": "/etc/letsencrypt/live/$DOMAIN/fullchain.pem", "keyFile": "/etc/letsencrypt/live/$DOMAIN/privkey.pem"}]}
      }
    },
    {
      "port": ${PORTS[VLESS_GRPC]},
      "protocol": "vless",
      "settings": {"clients": [$vless_grpc_clients], "decryption": "none"},
      "streamSettings": {
        "network": "grpc",
        "security": "tls",
        "tlsSettings": {"certificates": [{"certificateFile": "/etc/letsencrypt/live/$DOMAIN/fullchain.pem", "keyFile": "/etc/letsencrypt/live/$DOMAIN/privkey.pem"}]},
        "grpcSettings": {"serviceName": "vlessgrpc"}
      }
    },
    {
      "port": ${PORTS[VLESS_H2]},
      "protocol": "vless",
      "settings": {"clients": [$vless_h2_clients], "decryption": "none"},
      "streamSettings": {
        "network": "h2",
        "security": "tls",
        "tlsSettings": {"certificates": [{"certificateFile": "/etc/letsencrypt/live/$DOMAIN/fullchain.pem", "keyFile": "/etc/letsencrypt/live/$DOMAIN/privkey.pem"}]},
        "httpSettings": {"host": ["$DOMAIN"], "path": "/vlessh2"}
      }
    },
    {
      "port": ${PORTS[VMESS_WS]},
      "protocol": "vmess",
      "settings": {"clients": [$vmess_ws_clients]},
      "streamSettings": {
        "network": "ws",
        "security": "tls",
        "tlsSettings": {"certificates": [{"certificateFile": "/etc/letsencrypt/live/$DOMAIN/fullchain.pem", "keyFile": "/etc/letsencrypt/live/$DOMAIN/privkey.pem"}]},
        "wsSettings": {"path": "/vmessws"}
      }
    },
    {
      "port": ${PORTS[VMESS_TCP]},
      "protocol": "vmess",
      "settings": {"clients": [$vmess_tcp_clients]},
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {"certificates": [{"certificateFile": "/etc/letsencrypt/live/$DOMAIN/fullchain.pem", "keyFile": "/etc/letsencrypt/live/$DOMAIN/privkey.pem"}]}
      }
    },
    {
      "port": ${PORTS[TROJAN_WS]},
      "protocol": "trojan",
      "settings": {"clients": [$trojan_ws_clients]},
      "streamSettings": {
        "network": "ws",
        "security": "tls",
        "tlsSettings": {"certificates": [{"certificateFile": "/etc/letsencrypt/live/$DOMAIN/fullchain.pem", "keyFile": "/etc/letsencrypt/live/$DOMAIN/privkey.pem"}]},
        "wsSettings": {"path": "/trojanws"}
      }
    },
    {
      "port": ${PORTS[TROJAN_TCP]},
      "protocol": "trojan",
      "settings": {"clients": [$trojan_tcp_clients]},
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {"certificates": [{"certificateFile": "/etc/letsencrypt/live/$DOMAIN/fullchain.pem", "keyFile": "/etc/letsencrypt/live/$DOMAIN/privkey.pem"}]}
      }
    },
    {
      "port": ${PORTS[SHADOWSOCKS]},
      "protocol": "shadowsocks",
      "settings": {"clients": [$ss_clients], "method": "aes-128-gcm"},
      "streamSettings": {"network": "tcp"}
    },
    {
      "port": ${PORTS[REALITY]},
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
          "minClientVer": "",
          "maxClientVer": "",
          "maxTimeDiff": 0,
          "shortIds": [$(printf "\"%s\"," "${REALITY_SHORT_IDS[@]}" | sed 's/,$//')]
        }
      }
    },
    {
      "port": ${PORTS[REALITY_UDP]},
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
    {"protocol": "freedom"},
    {"protocol": "blackhole", "tag": "block"}
  ],
  "routing": {
    "domainStrategy": "AsIs",
    "rules": [
      {"type": "field", "ip": ["geoip:private"], "outboundTag": "block"},
      {"type": "field", "domain": ["geosite:category-ads-all"], "outboundTag": "block"}
    ]
  }
}
EOF

  # Vérification
  if ! jq empty "$CONFIG_PATH" &>/dev/null; then
    error "Configuration JSON invalide"
    return 1
  fi
  return 0
}

# ============================================
# FONCTIONS PRINCIPALES
# ============================================

install_all() {
  header
  echo -e " ${CYAN}Installation complète${NC}\n"
  
  if [ -f "$CONFIG_PATH" ]; then
    warning "Xray semble déjà être installé"
    read -rp " Voulez-vous vraiment continuer ? (o/N) " confirm
    [[ ! "$confirm" =~ ^[oO]$ ]] && return
  fi

  # Mise à jour système
  echo -n " [1/9] Mise à jour des paquets..."
  if apt update &>/dev/null && apt upgrade -y &>/dev/null; then
    echo -e "${GREEN} ✓${NC}"
  else
    error "Échec"
    return 1
  fi

  # Installation dépendances
  echo -n " [2/9] Installation des dépendances..."
  if apt install -y curl wget unzip nginx socat ufw certbot python3-certbot-nginx fail2ban jq openssl &>/dev/null; then
    echo -e "${GREEN} ✓${NC}"
  else
    error "Échec"
    return 1
  fi

  # Configuration UFW
  echo -n " [3/9] Configuration du pare-feu..."
  ufw allow 'OpenSSH' &>/dev/null
  ufw allow 80 &>/dev/null
  ufw allow 443 &>/dev/null
  if ufw --force enable &>/dev/null; then
    echo -e "${GREEN} ✓${NC}"
  else
    error "Échec"
    return 1
  fi

  # Configuration Fail2ban
  echo -n " [4/9] Configuration de Fail2ban..."
  if systemctl enable --now fail2ban &>/dev/null; then
    echo -e "${GREEN} ✓${NC}"
  else
    error "Échec"
    return 1
  fi

  # Installation Xray
  echo -n " [5/9] Installation de Xray..."
  if bash <(curl -Ls https://raw.githubusercontent.com/XTLS/Xray-install/main/install-release.sh) &>/dev/null; then
    echo -e "${GREEN} ✓${NC}"
  else
    error "Échec"
    return 1
  fi

  # Création répertoires
  mkdir -p /usr/local/etc/xray /var/log/xray

  # Configuration des ports
  configure_ports || return 1

  # Configuration Reality
  echo -n " [6/9] Configuration de Reality..."
  generate_reality_keys
  echo -e "${GREEN} ✓${NC}"

  # Demande informations
  header
  while [[ -z "$DOMAIN" ]]; do
    input "Entrez le nom de domaine (ex: proxy.exemple.com) : "
    read -r DOMAIN
  done

  while [[ ! "$EMAIL" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; do
    input "Entrez votre email valide : "
    read -r EMAIL
  done

  # Configuration Nginx et certificat
  echo -n " [7/9] Configuration du certificat TLS..."
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
    error "Échec"
    return 1
  fi

  # Configuration finale Nginx
  echo -n " [8/9] Configuration de Nginx..."
  cat > /etc/nginx/sites-available/"$DOMAIN".conf <<EOF
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # VLESS WS
    location /vlessws {
        proxy_pass http://127.0.0.1:${PORTS[VLESS_WS]};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    # VMess WS
    location /vmessws {
        proxy_pass http://127.0.0.1:${PORTS[VMESS_WS]};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    # Trojan WS
    location /trojanws {
        proxy_pass http://127.0.0.1:${PORTS[TROJAN_WS]};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    # VLESS gRPC
    location /vlessgrpc {
        grpc_pass grpc://127.0.0.1:${PORTS[VLESS_GRPC]};
    }

    # VLESS HTTP/2
    location /vlessh2 {
        proxy_pass http://127.0.0.1:${PORTS[VLESS_H2]};
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location / {
        root /var/www/html;
        index index.html;
    }
}
EOF

  if systemctl reload nginx &>/dev/null; then
    echo -e "${GREEN} ✓${NC}"
  else
    error "Échec"
    return 1
  fi

  # Création utilisateurs par défaut
  echo -n " [9/9] Création des utilisateurs..."
  USERS["VLESS_WS"]+=("$(generate_uuid)") || return 1
  USERS["VLESS_TCP"]+=("$(generate_uuid)") || return 1
  USERS["VLESS_GRPC"]+=("$(generate_uuid)") || return 1
  USERS["VLESS_H2"]+=("$(generate_uuid)") || return 1
  USERS["VMESS_WS"]+=("$(generate_uuid)") || return 1
  USERS["VMESS_TCP"]+=("$(generate_uuid)") || return 1
  USERS["TROJAN_WS"]+=("$(random_password)") || return 1
  USERS["TROJAN_TCP"]+=("$(random_password)") || return 1
  USERS["SHADOWSOCKS"]+=("$(random_password)") || return 1
  USERS["REALITY"]+=("$(generate_uuid)") || return 1
  USERS["REALITY_UDP"]+=("$(generate_uuid)") || return 1

  save_config || return 1

  # Configuration service Xray
  cat > /etc/systemd/system/xray.service <<EOF
[Unit]
Description=Service Xray
After=network.target

[Service]
User=nobody
ExecStart=$XRAY_BIN run -c $CONFIG_PATH
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reexec
  systemctl enable --now xray &>/dev/null && status "Service Xray activé"

  # Fin d'installation
  header
  status "Installation terminée avec succès"
  echo -e " ${CYAN}Un utilisateur par protocole a été créé${NC}"
  generate_links
  pause
}

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
      USERS["VLESS_WS"]+=("$id")
      status "Nouvel utilisateur VLESS WS :"
      echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
      echo -e " ${YELLOW}Port: ${CYAN}443${NC}"
      echo -e " ${YELLOW}Path: ${CYAN}/vlessws${NC}"
      echo -e " ${YELLOW}Flow: ${CYAN}xtls-rprx-vision${NC}"
      ;;
    2)
      id=$(generate_uuid) || return
      USERS["VLESS_TCP"]+=("$id")
      status "Nouvel utilisateur VLESS TCP :"
      echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
      echo -e " ${YELLOW}Port: ${CYAN}${PORTS[VLESS_TCP]}${NC}"
      echo -e " ${YELLOW}Flow: ${CYAN}xtls-rprx-vision${NC}"
      ;;
    3)
      id=$(generate_uuid) || return
      USERS["VLESS_GRPC"]+=("$id")
      status "Nouvel utilisateur VLESS gRPC :"
      echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
      echo -e " ${YELLOW}Port: ${CYAN}${PORTS[VLESS_GRPC]}${NC}"
      echo -e " ${YELLOW}ServiceName: ${CYAN}vlessgrpc${NC}"
      ;;
    4)
      id=$(generate_uuid) || return
      USERS["VLESS_H2"]+=("$id")
      status "Nouvel utilisateur VLESS HTTP/2 :"
      echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
      echo -e " ${YELLOW}Port: ${CYAN}${PORTS[VLESS_H2]}${NC}"
      echo -e " ${YELLOW}Path: ${CYAN}/vlessh2${NC}"
      ;;
    5)
      id=$(generate_uuid) || return
      USERS["VLESS_H2_UPGRADE"]+=("$id")
      status "Nouvel utilisateur VLESS HTTP Upgrade :"
      echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
      echo -e " ${YELLOW}Port: ${CYAN}${PORTS[VLESS_H2_UPGRADE]}${NC}"
      echo -e " ${YELLOW}Path: ${CYAN}/httpupgrade${NC}"
      ;;
    6)
      id=$(generate_uuid) || return
      USERS["VMESS_WS"]+=("$id")
      status "Nouvel utilisateur VMess WS :"
      echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
      echo -e " ${YELLOW}Port: ${CYAN}${PORTS[VMESS_WS]}${NC}"
      echo -e " ${YELLOW}Path: ${CYAN}/vmessws${NC}"
      ;;
    7)
      id=$(generate_uuid) || return
      USERS["VMESS_TCP"]+=("$id")
      status "Nouvel utilisateur VMess TCP :"
      echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
      echo -e " ${YELLOW}Port: ${CYAN}${PORTS[VMESS_TCP]}${NC}"
      ;;
    8)
      pwd=$(random_password) || return
      USERS["TROJAN_WS"]+=("$pwd")
      status "Nouvel utilisateur Trojan WS :"
      echo -e " ${YELLOW}Mot de passe: ${CYAN}$pwd${NC}"
      echo -e " ${YELLOW}Port: ${CYAN}${PORTS[TROJAN_WS]}${NC}"
      echo -e " ${YELLOW}Path: ${CYAN}/trojanws${NC}"
      ;;
    9)
      pwd=$(random_password) || return
      USERS["TROJAN_TCP"]+=("$pwd")
      status "Nouvel utilisateur Trojan TCP :"
      echo -e " ${YELLOW}Mot de passe: ${CYAN}$pwd${NC}"
      echo -e " ${YELLOW}Port: ${CYAN}${PORTS[TROJAN_TCP]}${NC}"
      echo -e " ${YELLOW}Flow: ${CYAN}xtls-rprx-direct${NC}"
      ;;
    10)
      pwd=$(random_password) || return
      USERS["SHADOWSOCKS"]+=("$pwd")
      status "Nouvel utilisateur Shadowsocks :"
      echo -e " ${YELLOW}Mot de passe: ${CYAN}$pwd${NC}"
      echo -e " ${YELLOW}Port: ${CYAN}${PORTS[SHADOWSOCKS]}${NC}"
      echo -e " ${YELLOW}Méthode: ${CYAN}aes-128-gcm${NC}"
      ;;
    11)
      id=$(generate_uuid) || return
      USERS["REALITY"]+=("$id")
      status "Nouvel utilisateur Reality TCP :"
      echo -e " ${YELLOW}UUID: ${CYAN}$id${NC}"
      echo -e " ${YELLOW}Port: ${CYAN}${PORTS[REALITY]}${NC}"
      echo -e " ${YELLOW}Public Key: ${CYAN}$REALITY_PUBLIC_KEY${NC}"
      echo -e " ${YELLOW}Short ID: ${CYAN}${REALITY_SHORT_IDS[0]}${NC}"
      echo -e " ${YELLOW}Fingerprint: ${CYAN}chrome${NC}"
      ;;
    12)
      id=$(generate_uuid) || return
      USERS["REALITY_UDP"]+=("$id")
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

remove_user() {
  header
  echo -e " ${CYAN}Supprimer un utilisateur${NC}\n"
  echo -e " ${BLUE}1.${NC} VLESS WS"
  echo -e " ${BLUE}2.${NC} VLESS TCP"
  echo -e " ${BLUE}3.${NC} VLESS gRPC"
  echo -e " ${BLUE}4.${NC} VLESS HTTP/2"
  echo -e " ${BLUE}5.${NC} VMess WS"
  echo -e " ${BLUE}6.${NC} VMess TCP"
  echo -e " ${BLUE}7.${NC} Trojan WS"
  echo -e " ${BLUE}8.${NC} Trojan TCP"
  echo -e " ${BLUE}9.${NC} Shadowsocks"
  echo -e " ${BLUE}10.${NC} Reality TCP"
  echo -e " ${BLUE}11.${NC} Reality UDP"
  echo -e " ${BLUE}0.${NC} Retour\n"
  
  read -rp " Choisissez le type d'utilisateur : " choice
  
  case $choice in
    1) remove_user_type "VLESS WS" USERS["VLESS_WS"] ;;
    2) remove_user_type "VLESS TCP" USERS["VLESS_TCP"] ;;
    3) remove_user_type "VLESS gRPC" USERS["VLESS_GRPC"] ;;
    4) remove_user_type "VLESS HTTP/2" USERS["VLESS_H2"] ;;
    5) remove_user_type "VMess WS" USERS["VMESS_WS"] ;;
    6) remove_user_type "VMess TCP" USERS["VMESS_TCP"] ;;
    7) remove_user_type "Trojan WS" USERS["TROJAN_WS"] ;;
    8) remove_user_type "Trojan TCP" USERS["TROJAN_TCP"] ;;
    9) remove_user_type "Shadowsocks" USERS["SHADOWSOCKS"] ;;
    10) remove_user_type "Reality TCP" USERS["REALITY"] ;;
    11) remove_user_type "Reality UDP" USERS["REALITY_UDP"] ;;
    0) return ;;
    *) 
      error "Option invalide"
      pause
      ;;
  esac
  
  save_config
  pause
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
    1) remove_user_type "VLESS WS" USERS["VLESS_WS"] ;;
    2) remove_user_type "VLESS TCP" USERS["VLESS_TCP"] ;;
    3) remove_user_type "VLESS gRPC" USERS["VLESS_GRPC"] ;;
    4) remove_user_type "VLESS HTTP/2" USERS["VLESS_H2"] ;;
    5) remove_user_type "VLESS HTTP Upgrade" USERS["VLESS_H2_UPGRADE"] ;;
    6) remove_user_type "VMess WS" USERS["VMESS_WS"] ;;
    7) remove_user_type "VMess TCP" USERS["VMESS_TCP"] ;;
    8) remove_user_type "Trojan WS" USERS["TROJAN_WS"] ;;
    9) remove_user_type "Trojan TCP" USERS["TROJAN_TCP"] ;;
    10) remove_user_type "Shadowsocks" USERS["SHADOWSOCKS"] ;;
    11) remove_user_type "Reality TCP" USERS["REALITY"] ;;
    12) remove_user_type "Reality UDP" USERS["REALITY_UDP"] ;;
    0) return ;;
    *) 
      error "Option invalide"
      pause
      ;;
  esac
  
  save_config
  pause
}

remove_user_type() {
  local type=$1
  local -n arr=$2
  
  if [ ${#arr[@]} -eq 0 ]; then
    warning "Aucun utilisateur $type à supprimer"
    return
  fi
  
  header
  echo -e " ${CYAN}Utilisateurs $type existants :${NC}\n"
  for i in "${!arr[@]}"; do
    if [[ "$type" =~ Trojan|Shadowsocks ]]; then
      echo -e " ${BLUE}$i.${NC} ${arr[$i]}"
    else
      echo -e " ${BLUE}$i.${NC} ${arr[$i]}"
    fi
  done
  
  read -rp "\n Entrez le numéro à supprimer : " num
  if [[ "$num" =~ ^[0-9]+$ ]] && [ -n "${arr[$num]}" ]; then
    unset 'arr[num]'
    arr=("${arr[@]}")
    status "Utilisateur supprimé"
  else
    error "Numéro invalide"
  fi
}

configure_nginx() {
  header
  echo -e " ${CYAN}Configuration de Nginx${NC}\n"
  
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
        proxy_pass http://127.0.0.1:${PORTS[VLESS_WS]};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    # VMess WS
    location /vmessws {
        proxy_pass http://127.0.0.1:${PORTS[VMESS_WS]};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    # Trojan WS
    location /trojanws {
        proxy_pass http://127.0.0.1:${PORTS[TROJAN_WS]};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    # VLESS gRPC
    location /vlessgrpc {
        grpc_pass grpc://127.0.0.1:${PORTS[VLESS_GRPC]};
    }

    # VLESS HTTP/2
    location /vlessh2 {
        proxy_pass http://127.0.0.1:${PORTS[VLESS_H2]};
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host \$host;
    }

    # HTTP Upgrade
    location /httpupgrade {
        proxy_pass http://127.0.0.1:${PORTS[VLESS_H2_UPGRADE]};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
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

  nginx -t && systemctl reload nginx && status "Nginx rechargé avec succès" || error "Erreur de configuration Nginx"
  pause
}

# ============================================
# GENERATION DES LIENS CLIENTS
# ============================================

generate_links() {
  header
  if [ -z "$DOMAIN" ]; then
    error "Domaine non configuré"
    pause
    return 1
  fi

  cat > config_clients.txt <<EOF
===========================================
=== Xray Client Configurations - DjahNoDead 👽 ===
=== Généré le: $(date) ===
=== Domaine: $DOMAIN ===
=== Reality Public Key: $REALITY_PUBLIC_KEY ===
=== Short IDs: ${REALITY_SHORT_IDS[*]} ===
===========================================

EOF

  # VLESS WS
  if [ ${#USERS[VLESS_WS][@]} -gt 0 ]; then
    echo -e "=== VLESS WS (Recommandé) ===\n" >> config_clients.txt
    for uuid in "${USERS[VLESS_WS][@]}"; do
      echo "vless://$uuid@$DOMAIN:443?encryption=none&security=tls&type=ws&path=%2Fvlessws#$DOMAIN-VLESS-WS" >> config_clients.txt
    done
    echo >> config_clients.txt
  fi

  # VLESS TCP
  if [ ${#USERS[VLESS_TCP][@]} -gt 0 ]; then
    echo -e "=== VLESS TCP ===\n" >> config_clients.txt
    for uuid in "${USERS[VLESS_TCP][@]}"; do
      echo "vless://$uuid@$DOMAIN:${PORTS[VLESS_TCP]}?security=tls&encryption=none&type=tcp#$DOMAIN-VLESS-TCP" >> config_clients.txt
    done
    echo >> config_clients.txt
  fi

  # VLESS gRPC
  if [ ${#USERS[VLESS_GRPC][@]} -gt 0 ]; then
    echo -e "=== VLESS gRPC ===\n" >> config_clients.txt
    for uuid in "${USERS[VLESS_GRPC][@]}"; do
      echo "vless://$uuid@$DOMAIN:${PORTS[VLESS_GRPC]}?type=grpc&serviceName=vlessgrpc&security=tls#$DOMAIN-VLESS-gRPC" >> config_clients.txt
    done
    echo >> config_clients.txt
  fi

  # VLESS HTTP/2
  if [ ${#USERS[VLESS_H2][@]} -gt 0 ]; then
    echo -e "=== VLESS HTTP/2 ===\n" >> config_clients.txt
    for uuid in "${USERS[VLESS_H2][@]}"; do
      echo "vless://$uuid@$DOMAIN:${PORTS[VLESS_H2]}?type=http&security=tls&path=%2Fvlessh2#$DOMAIN-VLESS-H2" >> config_clients.txt
    done
    echo >> config_clients.txt
  fi

  # VMESS WS
  if [ ${#USERS[VMESS_WS][@]} -gt 0 ]; then
    echo -e "=== VMESS WS ===\n" >> config_clients.txt
    for uuid in "${USERS[VMESS_WS][@]}"; do
      vmess_config=$(jq -n \
        --arg uuid "$uuid" \
        --arg host "$DOMAIN" \
        --arg port "${PORTS[VMESS_WS]}" \
        '{
          v: "2", ps: "vmess-ws", add: $host,
          port: $port, id: $uuid, aid: "0",
          net: "ws", type: "none", host: $host,
          path: "/vmessws", tls: "tls"
        }')
      echo "vmess://$(echo "$vmess_config" | base64 -w 0)" >> config_clients.txt
    done
    echo >> config_clients.txt
  fi

  # VMESS TCP
  if [ ${#USERS[VMESS_TCP][@]} -gt 0 ]; then
    echo -e "=== VMESS TCP ===\n" >> config_clients.txt
    for uuid in "${USERS[VMESS_TCP][@]}"; do
      vmess_config=$(jq -n \
        --arg uuid "$uuid" \
        --arg host "$DOMAIN" \
        --arg port "${PORTS[VMESS_TCP]}" \
        '{
          v: "2", ps: "vmess-tcp", add: $host,
          port: $port, id: $uuid, aid: "0",
          net: "tcp", type: "none", host: $host,
          tls: "tls"
        }')
      echo "vmess://$(echo "$vmess_config" | base64 -w 0)" >> config_clients.txt
    done
    echo >> config_clients.txt
  fi

  # Trojan WS
  if [ ${#USERS[TROJAN_WS][@]} -gt 0 ]; then
    echo -e "=== TROJAN WS ===\n" >> config_clients.txt
    for pwd in "${USERS[TROJAN_WS][@]}"; do
      echo "trojan://$pwd@$DOMAIN:443?security=tls&type=ws&path=%2Ftrojanws#$DOMAIN-TROJAN-WS" >> config_clients.txt
    done
    echo >> config_clients.txt
  fi

  # Trojan TCP
  if [ ${#USERS[TROJAN_TCP][@]} -gt 0 ]; then
    echo -e "=== TROJAN TCP ===\n" >> config_clients.txt
    for pwd in "${USERS[TROJAN_TCP][@]}"; do
      echo "trojan://$pwd@$DOMAIN:${PORTS[TROJAN_TCP]}?security=tls&type=tcp#$DOMAIN-TROJAN-TCP" >> config_clients.txt
    done
    echo >> config_clients.txt
  fi

  # Shadowsocks
  if [ ${#USERS[SHADOWSOCKS][@]} -gt 0 ]; then
    echo -e "=== SHADOWSOCKS ===\n" >> config_clients.txt
    for pwd in "${USERS[SHADOWSOCKS][@]}"; do
      echo "ss://$(echo -n "aes-128-gcm:$pwd" | base64 -w 0)@$DOMAIN:${PORTS[SHADOWSOCKS]}#$DOMAIN-SS" >> config_clients.txt
    done
    echo >> config_clients.txt
  fi

  # Reality TCP
  if [ ${#USERS[REALITY][@]} -gt 0 ]; then
    echo -e "=== REALITY TCP ===\n" >> config_clients.txt
    for uuid in "${USERS[REALITY][@]}"; do
      echo "vless://$uuid@$DOMAIN:${PORTS[REALITY]}?type=tcp&security=reality&pbk=$REALITY_PUBLIC_KEY&sid=${REALITY_SHORT_IDS[0]}&fp=chrome#${DOMAIN}-REALITY-TCP" >> config_clients.txt
    done
    echo >> config_clients.txt
  fi

  # Reality UDP
  if [ ${#USERS[REALITY_UDP][@]} -gt 0 ]; then
    echo -e "=== REALITY UDP ===\n" >> config_clients.txt
    for uuid in "${USERS[REALITY_UDP][@]}"; do
      echo "vless://$uuid@$DOMAIN:${PORTS[REALITY_UDP]}?type=udp&security=reality&pbk=$REALITY_PUBLIC_KEY&sid=${REALITY_SHORT_IDS[0]}&fp=chrome#${DOMAIN}-REALITY-UDP" >> config_clients.txt
    done
    echo >> config_clients.txt
  fi

  # HTTP Upgrade (Exemple)
  if [ ${#USERS[VLESS_H2_UPGRADE][@]} -gt 0 ]; then
    echo -e "=== VLESS HTTP Upgrade ===\n" >> config_clients.txt
    for uuid in "${USERS[VLESS_H2_UPGRADE][@]}"; do
      echo "vless://$uuid@$DOMAIN:${PORTS[VLESS_H2_UPGRADE]}?type=http&security=none&path=%2Fhttpupgrade#$DOMAIN-VLESS-HTTP-UPGRADE" >> config_clients.txt
    done
    echo >> config_clients.txt
  fi

  echo -e "===========================================" >> config_clients.txt
  echo -e "=== FIN DES CONFIGURATIONS ===" >> config_clients.txt
  echo -e "\n=== INSTRUCTIONS ===" >> config_clients.txt
  echo -e "- Reality: Utiliser Xray v1.8.0+ ou Shadowrocket" >> config_clients.txt
  echo -e "- gRPC: Nécessite un client supportant gRPC" >> config_clients.txt
  echo -e "- HTTP Upgrade: Compatible avec Cloudflare CDN" >> config_clients.txt

  status "Configurations sauvegardées dans ${YELLOW}config_clients.txt${NC}"
  echo -e "\n ${CYAN}Conseil:${NC} Utilisez ${YELLOW}cat config_clients.txt | qrencode -t UTF8${NC} pour générer des QR codes"
  pause
}

# [Les autres fonctions (add_user, remove_user, generate_links, etc.) restent similaires mais adaptées aux nouveaux protocoles]

# ============================================
# MENUS
# ============================================

show_menu() {
  header
  echo -e " ${BLUE}1.${NC} Installation complète"
  echo -e " ${BLUE}2.${NC} Gérer les utilisateurs"
  echo -e " ${BLUE}3.${NC} Générer les configurations"
  echo -e " ${BLUE}4.${NC} Paramètres avancés"
  echo -e " ${BLUE}0.${NC} Quitter\n"
  
  input "Choisissez une option (0-4) : "
  read -r choice
  
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
}

# ============================================
# POINT D'ENTRÉE
# ============================================

check_root
load_config

while true; do
  show_menu
done