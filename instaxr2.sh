#!/bin/bash

##############################################
# Script de gestion Xray avec multi-protocoles
# Améliorations :
# 1. Choix des ports personnalisés
# 2. Commentaires ajoutés
# 3. Meilleure gestion des erreurs
##############################################

CONFIG_PATH="/usr/local/etc/xray/config.json"
Xray_BIN="/usr/local/bin/xray"
DOMAIN=""
EMAIL=""

# Ports configurables (valeurs par défaut)
PORTS=(
  ["VLESS_WS"]=10000
  ["TROJAN_WS"]=10001
  ["VLESS_TCP"]=10002
  ["TROJAN_TCP"]=10003
  ["VMESS"]=10004
  ["SHADOWSOCKS"]=10005
)

# Listes utilisateurs
UUIDS_VLESS_WS=()
UUIDS_VLESS_TCP=()
UUIDS_VMESS=()
PASSWORDS_TROJAN_WS=()
PASSWORDS_TROJAN_TCP=()
PASSWORDS_SS=()

##############################################
# Génère un UUID aléatoire
# Retourne : UUID généré
##############################################
generate_uuid() {
  cat /proc/sys/kernel/random/uuid || {
    echo "❌ Erreur lors de la génération d'UUID" >&2
    exit 1
  }
}

##############################################
# Génère un mot de passe aléatoire
# Retourne : Mot de passe de 16 caractères
##############################################
random_password() {
  tr -dc A-Za-z0-9 </dev/urandom | head -c 16 || {
    echo "❌ Erreur lors de la génération du mot de passe" >&2
    exit 1
  }
}

##############################################
# Vérifie que le script est exécuté en root
# Sort en erreur si ce n'est pas le root
##############################################
check_root() {
  if [ "$EUID" -ne 0 ]; then
    echo "⚠️ Ce script doit être lancé en root." >&2
    exit 1
  fi
}

##############################################
# Pause l'exécution jusqu'à appui sur Entrée
##############################################
pause() {
  read -rp "Appuyez sur Entrée pour continuer..."
}

##############################################
# Configure les ports personnalisés
##############################################
configure_ports() {
  echo "=== Configuration des ports ==="
  echo "Laissez vide pour utiliser les valeurs par défaut"
  
  read -rp "Port VLESS WS (défaut ${PORTS[VLESS_WS]}): " input
  [ -n "$input" ] && PORTS["VLESS_WS"]=$input
  
  read -rp "Port Trojan WS (défaut ${PORTS[TROJAN_WS]}): " input
  [ -n "$input" ] && PORTS["TROJAN_WS"]=$input
  
  read -rp "Port VLESS TCP (défaut ${PORTS[VLESS_TCP]}): " input
  [ -n "$input" ] && PORTS["VLESS_TCP"]=$input
  
  read -rp "Port Trojan TCP (défaut ${PORTS[TROJAN_TCP]}): " input
  [ -n "$input" ] && PORTS["TROJAN_TCP"]=$input
  
  read -rp "Port VMess (défaut ${PORTS[VMESS]}): " input
  [ -n "$input" ] && PORTS["VMESS"]=$input
  
  read -rp "Port Shadowsocks (défaut ${PORTS[SHADOWSOCKS]}): " input
  [ -n "$input" ] && PORTS["SHADOWSOCKS"]=$input
  
  echo "✅ Ports configurés :"
  for proto in "${!PORTS[@]}"; do
    echo "- $proto : ${PORTS[$proto]}"
  done
  pause
}

##############################################
# Charge la configuration existante
##############################################
load_config() {
  if [ -f "$CONFIG_PATH" ]; then
    echo "🔄 Chargement de la configuration existante..."
    DOMAIN=$(grep -oP '(?<=server_name )[^;]+' /etc/nginx/sites-available/"$DOMAIN".conf 2>/dev/null) || {
      echo "⚠️ Impossible de charger le domaine depuis Nginx"
      DOMAIN=""
    }
    
    # Chargement des utilisateurs existants
    UUIDS_VLESS_WS=($(jq -r '.inbounds[] | select(.protocol=="vless" and .streamSettings.network=="ws") | .settings.clients[].id' "$CONFIG_PATH" 2>/dev/null || echo ""))
    UUIDS_VLESS_TCP=($(jq -r '.inbounds[] | select(.protocol=="vless" and .streamSettings.network=="tcp") | .settings.clients[].id' "$CONFIG_PATH" 2>/dev/null || echo ""))
    UUIDS_VMESS=($(jq -r '.inbounds[] | select(.protocol=="vmess") | .settings.clients[].id' "$CONFIG_PATH" 2>/dev/null || echo ""))
    PASSWORDS_TROJAN_WS=($(jq -r '.inbounds[] | select(.protocol=="trojan" and .streamSettings.network=="ws") | .settings.clients[].password' "$CONFIG_PATH" 2>/dev/null || echo ""))
    PASSWORDS_TROJAN_TCP=($(jq -r '.inbounds[] | select(.protocol=="trojan" and .streamSettings.network=="tcp") | .settings.clients[].password' "$CONFIG_PATH" 2>/dev/null || echo ""))
    PASSWORDS_SS=($(jq -r '.inbounds[] | select(.protocol=="shadowsocks") | .settings.clients[].password' "$CONFIG_PATH" 2>/dev/null || echo ""))
    
    # Chargement des ports depuis la config existante
    PORTS["VLESS_WS"]=$(jq -r '.inbounds[] | select(.protocol=="vless" and .streamSettings.network=="ws") | .port' "$CONFIG_PATH" 2>/dev/null || echo "10000")
    PORTS["TROJAN_WS"]=$(jq -r '.inbounds[] | select(.protocol=="trojan" and .streamSettings.network=="ws") | .port' "$CONFIG_PATH" 2>/dev/null || echo "10001")
    PORTS["VLESS_TCP"]=$(jq -r '.inbounds[] | select(.protocol=="vless" and .streamSettings.network=="tcp") | .port' "$CONFIG_PATH" 2>/dev/null || echo "10002")
    PORTS["TROJAN_TCP"]=$(jq -r '.inbounds[] | select(.protocol=="trojan" and .streamSettings.network=="tcp") | .port' "$CONFIG_PATH" 2>/dev/null || echo "10003")
    PORTS["VMESS"]=$(jq -r '.inbounds[] | select(.protocol=="vmess") | .port' "$CONFIG_PATH" 2>/dev/null || echo "10004")
    PORTS["SHADOWSOCKS"]=$(jq -r '.inbounds[] | select(.protocol=="shadowsocks") | .port' "$CONFIG_PATH" 2>/dev/null || echo "10005")
  fi
}

##############################################
# Sauvegarde la configuration dans config.json
# Gestion améliorée des erreurs
##############################################
save_config() {
  echo "🔄 Sauvegarde de la configuration..."
  
  # Préparation des clients pour chaque protocole
  local vless_ws_clients=""
  local vless_tcp_clients=""
  local vmess_clients=""
  local trojan_ws_clients=""
  local trojan_tcp_clients=""
  local ss_clients=""

  for uuid in "${UUIDS_VLESS_WS[@]}"; do
    vless_ws_clients+="{\"id\":\"$uuid\",\"level\":0,\"email\":\"user@vless-ws\"},"
  done
  vless_ws_clients=${vless_ws_clients%,}

  for uuid in "${UUIDS_VLESS_TCP[@]}"; do
    vless_tcp_clients+="{\"id\":\"$uuid\",\"level\":0,\"email\":\"user@vless-tcp\"},"
  done
  vless_tcp_clients=${vless_tcp_clients%,}

  for uuid in "${UUIDS_VMESS[@]}"; do
    vmess_clients+="{\"id\":\"$uuid\",\"alterId\":0,\"email\":\"user@vmess\"},"
  done
  vmess_clients=${vmess_clients%,}

  for pwd in "${PASSWORDS_TROJAN_WS[@]}"; do
    trojan_ws_clients+="{\"password\":\"$pwd\"},"
  done
  trojan_ws_clients=${trojan_ws_clients%,}

  for pwd in "${PASSWORDS_TROJAN_TCP[@]}"; do
    trojan_tcp_clients+="{\"password\":\"$pwd\"},"
  done
  trojan_tcp_clients=${trojan_tcp_clients%,}

  for pwd in "${PASSWORDS_SS[@]}"; do
    ss_clients+="{\"password\":\"$pwd\",\"method\":\"aes-128-gcm\"},"
  done
  ss_clients=${ss_clients%,}

  # Écriture du fichier de configuration
  cat > "$CONFIG_PATH" <<EOF
{
  "log": {
    "access": "/var/log/xray/access.log",
    "error": "/var/log/xray/error.log",
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "port": ${PORTS[VLESS_WS]},
      "protocol": "vless",
      "settings": {
        "clients": [
          $vless_ws_clients
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "ws",
        "wsSettings": {
          "path": "/ws"
        }
      }
    },
    {
      "port": ${PORTS[TROJAN_WS]},
      "protocol": "trojan",
      "settings": {
        "clients": [
          $trojan_ws_clients
        ]
      },
      "streamSettings": {
        "network": "ws",
        "wsSettings": {
          "path": "/ws"
        }
      }
    },
    {
      "port": ${PORTS[VLESS_TCP]},
      "protocol": "vless",
      "settings": {
        "clients": [
          $vless_tcp_clients
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {}
      }
    },
    {
      "port": ${PORTS[TROJAN_TCP]},
      "protocol": "trojan",
      "settings": {
        "clients": [
          $trojan_tcp_clients
        ]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {}
      }
    },
    {
      "port": ${PORTS[VMESS]},
      "protocol": "vmess",
      "settings": {
        "clients": [
          $vmess_clients
        ]
      },
      "streamSettings": {
        "network": "ws",
        "wsSettings": {
          "path": "/vmessws"
        }
      }
    },
    {
      "port": ${PORTS[SHADOWSOCKS]},
      "protocol": "shadowsocks",
      "settings": {
        "clients": [
          $ss_clients
        ],
        "method": "aes-128-gcm"
      },
      "streamSettings": {
        "network": "tcp"
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom"
    }
  ]
}
EOF

  # Vérification que le fichier a bien été créé
  if [ ! -f "$CONFIG_PATH" ]; then
    echo "❌ Erreur : impossible de créer le fichier de configuration" >&2
    return 1
  fi
  
  # Vérification que le JSON est valide
  if ! jq empty "$CONFIG_PATH" >/dev/null 2>&1; then
    echo "❌ Erreur : fichier de configuration JSON invalide" >&2
    return 1
  fi
  
  echo "✅ Configuration sauvegardée avec succès"
  return 0
}

##############################################
# Installation complète des composants
# Avec gestion améliorée des erreurs
##############################################
install_all() {
  echo "🔄 Mise à jour et installation des paquets..."
  if ! apt update; then
    echo "❌ Erreur lors de la mise à jour des paquets" >&2
    return 1
  fi
  
  if ! apt upgrade -y; then
    echo "⚠️ Attention : échec partiel de la mise à jour des paquets" >&2
  fi
  
  if ! apt install -y curl wget unzip nginx socat ufw certbot python3-certbot-nginx fail2ban jq; then
    echo "❌ Erreur lors de l'installation des paquets requis" >&2
    return 1
  fi

  echo "✅ Configuration UFW..."
  ufw allow 'OpenSSH' || echo "⚠️ Impossible d'autoriser OpenSSH dans UFW" >&2
  ufw allow 80 || echo "⚠️ Impossible d'autoriser le port 80 dans UFW" >&2
  ufw allow 443 || echo "⚠️ Impossible d'autoriser le port 443 dans UFW" >&2
  ufw --force enable || {
    echo "❌ Impossible d'activer UFW" >&2
    return 1
  }

  echo "✅ Activation Fail2ban..."
  systemctl enable fail2ban || echo "⚠️ Impossible d'activer Fail2ban" >&2
  systemctl start fail2ban || {
    echo "❌ Impossible de démarrer Fail2ban" >&2
    return 1
  }

  echo "✅ Installation Xray-core..."
  if ! bash <(curl -Ls https://raw.githubusercontent.com/XTLS/Xray-install/main/install-release.sh); then
    echo "❌ Erreur lors de l'installation de Xray" >&2
    return 1
  fi

  mkdir -p /usr/local/etc/xray || {
    echo "❌ Impossible de créer le dossier de configuration Xray" >&2
    return 1
  }
  
  mkdir -p /var/log/xray || {
    echo "⚠️ Impossible de créer le dossier de logs Xray" >&2
  }

  # Demande des ports personnalisés
  configure_ports

  read -rp "➡️ Entrez le nom de domaine FRONTEND (exemple : proxy.exemple.com) : " DOMAIN
  if [[ -z "$DOMAIN" ]]; then
    echo "❌ Domaine invalide" >&2
    return 1
  fi

  read -rp "➡️ Entrez votre email pour Let's Encrypt : " EMAIL
  if [[ ! "$EMAIL" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
    echo "❌ Email invalide" >&2
    return 1
  fi

  echo "✅ Obtention certificat TLS..."
  rm -f /etc/nginx/sites-enabled/default
  cat > /etc/nginx/sites-available/"$DOMAIN".conf <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOF

  ln -sf /etc/nginx/sites-available/"$DOMAIN".conf /etc/nginx/sites-enabled/ || {
    echo "❌ Impossible de créer le lien symbolique Nginx" >&2
    return 1
  }

  if ! nginx -t; then
    echo "❌ Configuration Nginx invalide" >&2
    return 1
  fi
  
  systemctl reload nginx || {
    echo "❌ Impossible de recharger Nginx" >&2
    return 1
  }

  if ! certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive; then
    echo "❌ Erreur lors de l'obtention du certificat TLS" >&2
    return 1
  fi

  echo "✅ Configuration Nginx reverse proxy..."
  cat > /etc/nginx/sites-available/"$DOMAIN".conf <<EOF
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    location /ws {
        proxy_redirect off;
        proxy_pass http://127.0.0.1:${PORTS[VLESS_WS]};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
    location /vmessws {
        proxy_redirect off;
        proxy_pass http://127.0.0.1:${PORTS[VMESS]};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
    location / {
        root /var/www/html;
        index index.html;
    }
}
EOF

  if ! nginx -t; then
    echo "❌ Configuration Nginx invalide après modification" >&2
    return 1
  fi
  
  systemctl reload nginx || {
    echo "❌ Impossible de recharger Nginx après modification" >&2
    return 1
  }

  # Init arrays
  UUIDS_VLESS_WS=()
  UUIDS_VLESS_TCP=()
  UUIDS_VMESS=()
  PASSWORDS_TROJAN_WS=()
  PASSWORDS_TROJAN_TCP=()
  PASSWORDS_SS=()

  # Générer 1 utilisateur de chaque type par défaut
  UUIDS_VLESS_WS+=("$(generate_uuid)") || return 1
  UUIDS_VLESS_TCP+=("$(generate_uuid)") || return 1
  UUIDS_VMESS+=("$(generate_uuid)") || return 1
  PASSWORDS_TROJAN_WS+=("$(random_password)") || return 1
  PASSWORDS_TROJAN_TCP+=("$(random_password)") || return 1
  PASSWORDS_SS+=("$(random_password)") || return 1

  save_config || return 1

  # Créer service systemd
  cat > /etc/systemd/system/xray.service <<EOF
[Unit]
Description=Service Xray
After=network.target

[Service]
User=nobody
ExecStart=$Xray_BIN run -c $CONFIG_PATH
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reexec || echo "⚠️ Impossible de recharger le démon systemd" >&2
  systemctl enable xray || {
    echo "❌ Impossible d'activer le service Xray" >&2
    return 1
  }
  
  systemctl restart xray || {
    echo "❌ Impossible de démarrer Xray" >&2
    return 1
  }

  echo "✅ Installation terminée avec un utilisateur par protocole créé."
  generate_links
  pause
}

##############################################
# Ajoute un utilisateur selon le protocole
# Gestion des erreurs améliorée
##############################################
add_user() {
  echo "=== Ajouter un utilisateur ==="
  echo "1) VLESS WS"
  echo "2) VLESS TCP"
  echo "3) VMess WS"
  echo "4) Trojan WS"
  echo "5) Trojan TCP"
  echo "6) Shadowsocks TCP"
  echo "0) Retour"
  read -rp "Choisissez le type d'utilisateur à ajouter : " choice
  
  case $choice in
    1)
      if ! id=$(generate_uuid); then
        pause
        return 1
      fi
      UUIDS_VLESS_WS+=("$id")
      echo "Utilisateur VLESS WS ajouté : $id"
      ;;
    2)
      if ! id=$(generate_uuid); then
        pause
        return 1
      fi
      UUIDS_VLESS_TCP+=("$id")
      echo "Utilisateur VLESS TCP ajouté : $id"
      ;;
    3)
      if ! id=$(generate_uuid); then
        pause
        return 1
      fi
      UUIDS_VMESS+=("$id")
      echo "Utilisateur VMess WS ajouté : $id"
      ;;
    4)
      if ! pwd=$(random_password); then
        pause
        return 1
      fi
      PASSWORDS_TROJAN_WS+=("$pwd")
      echo "Utilisateur Trojan WS ajouté : $pwd"
      ;;
    5)
      if ! pwd=$(random_password); then
        pause
        return 1
      fi
      PASSWORDS_TROJAN_TCP+=("$pwd")
      echo "Utilisateur Trojan TCP ajouté : $pwd"
      ;;
    6)
      if ! pwd=$(random_password); then
        pause
        return 1
      fi
      PASSWORDS_SS+=("$pwd")
      echo "Utilisateur Shadowsocks ajouté : $pwd"
      ;;
    0) return ;;
    *) 
      echo "Option invalide." 
      pause
      return 1
      ;;
  esac
  
  if ! save_config; then
    echo "❌ Erreur lors de la sauvegarde de la configuration" >&2
    pause
    return 1
  fi
  
  echo "✅ Utilisateur ajouté et configuration mise à jour."
  pause
}

##############################################
# Supprime un utilisateur selon le protocole
##############################################
remove_user() {
  echo "=== Supprimer un utilisateur ==="
  echo "1) VLESS WS"
  echo "2) VLESS TCP"
  echo "3) VMess WS"
  echo "4) Trojan WS"
  echo "5) Trojan TCP"
  echo "6) Shadowsocks TCP"
  echo "0) Retour"
  read -rp "Choisissez le type d'utilisateur à supprimer : " choice
  
  case $choice in
    1)
      if [ ${#UUIDS_VLESS_WS[@]} -eq 0 ]; then
        echo "❌ Aucun utilisateur VLESS WS à supprimer"
        pause
        return
      fi
      
      echo "Utilisateurs VLESS WS existants :"
      for i in "${!UUIDS_VLESS_WS[@]}"; do
        echo "$i) ${UUIDS_VLESS_WS[$i]}"
      done
      read -rp "Entrez le numéro de l'utilisateur à supprimer : " num
      
      if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 0 ] && [ "$num" -lt "${#UUIDS_VLESS_WS[@]}" ]; then
        unset 'UUIDS_VLESS_WS[num]'
        UUIDS_VLESS_WS=("${UUIDS_VLESS_WS[@]}")
        echo "✅ Utilisateur supprimé."
      else
        echo "❌ Numéro invalide."
      fi
      ;;
      
    2)
      if [ ${#UUIDS_VLESS_TCP[@]} -eq 0 ]; then
        echo "❌ Aucun utilisateur VLESS TCP à supprimer"
        pause
        return
      fi
      
      echo "Utilisateurs VLESS TCP existants :"
      for i in "${!UUIDS_VLESS_TCP[@]}"; do
        echo "$i) ${UUIDS_VLESS_TCP[$i]}"
      done
      read -rp "Entrez le numéro de l'utilisateur à supprimer : " num
      
      if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 0 ] && [ "$num" -lt "${#UUIDS_VLESS_TCP[@]}" ]; then
        unset 'UUIDS_VLESS_TCP[num]'
        UUIDS_VLESS_TCP=("${UUIDS_VLESS_TCP[@]}")
        echo "✅ Utilisateur supprimé."
      else
        echo "❌ Numéro invalide."
      fi
      ;;
      
    3)
      if [ ${#UUIDS_VMESS[@]} -eq 0 ]; then
        echo "❌ Aucun utilisateur VMess à supprimer"
        pause
        return
      fi
      
      echo "Utilisateurs VMess existants :"
      for i in "${!UUIDS_VMESS[@]}"; do
        echo "$i) ${UUIDS_VMESS[$i]}"
      done
      read -rp "Entrez le numéro de l'utilisateur à supprimer : " num
      
      if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 0 ] && [ "$num" -lt "${#UUIDS_VMESS[@]}" ]; then
        unset 'UUIDS_VMESS[num]'
        UUIDS_VMESS=("${UUIDS_VMESS[@]}")
        echo "✅ Utilisateur supprimé."
      else
        echo "❌ Numéro invalide."
      fi
      ;;
      
    4)
      if [ ${#PASSWORDS_TROJAN_WS[@]} -eq 0 ]; then
        echo "❌ Aucun utilisateur Trojan WS à supprimer"
        pause
        return
      fi
      
      echo "Utilisateurs Trojan WS existants :"
      for i in "${!PASSWORDS_TROJAN_WS[@]}"; do
        echo "$i) ${PASSWORDS_TROJAN_WS[$i]}"
      done
      read -rp "Entrez le numéro de l'utilisateur à supprimer : " num
      
      if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 0 ] && [ "$num" -lt "${#PASSWORDS_TROJAN_WS[@]}" ]; then
        unset 'PASSWORDS_TROJAN_WS[num]'
        PASSWORDS_TROJAN_WS=("${PASSWORDS_TROJAN_WS[@]}")
        echo "✅ Utilisateur supprimé."
      else
        echo "❌ Numéro invalide."
      fi
      ;;
      
    5)
      if [ ${#PASSWORDS_TROJAN_TCP[@]} -eq 0 ]; then
        echo "❌ Aucun utilisateur Trojan TCP à supprimer"
        pause
        return
      fi
      
      echo "Utilisateurs Trojan TCP existants :"
      for i in "${!PASSWORDS_TROJAN_TCP[@]}"; do
        echo "$i) ${PASSWORDS_TROJAN_TCP[$i]}"
      done
      read -rp "Entrez le numéro de l'utilisateur à supprimer : " num
      
      if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 0 ] && [ "$num" -lt "${#PASSWORDS_TROJAN_TCP[@]}" ]; then
        unset 'PASSWORDS_TROJAN_TCP[num]'
        PASSWORDS_TROJAN_TCP=("${PASSWORDS_TROJAN_TCP[@]}")
        echo "✅ Utilisateur supprimé."
      else
        echo "❌ Numéro invalide."
      fi
      ;;
      
    6)
      if [ ${#PASSWORDS_SS[@]} -eq 0 ]; then
        echo "❌ Aucun utilisateur Shadowsocks à supprimer"
        pause
        return
      fi
      
      echo "Utilisateurs Shadowsocks existants :"
      for i in "${!PASSWORDS_SS[@]}"; do
        echo "$i) ${PASSWORDS_SS[$i]}"
      done
      read -rp "Entrez le numéro de l'utilisateur à supprimer : " num
      
      if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 0 ] && [ "$num" -lt "${#PASSWORDS_SS[@]}" ]; then
        unset 'PASSWORDS_SS[num]'
        PASSWORDS_SS=("${PASSWORDS_SS[@]}")
        echo "✅ Utilisateur supprimé."
      else
        echo "❌ Numéro invalide."
      fi
      ;;
      
    0) return ;;
    *) 
      echo "Option invalide."
      ;;
  esac
  
  if ! save_config; then
    echo "❌ Erreur lors de la sauvegarde de la configuration" >&2
  fi
  
  pause
}

##############################################
# Génère les liens de configuration clients
# Vérifie que le domaine est configuré
##############################################
generate_links() {
  echo "=== Génération des liens clients ==="
  if [ -z "$DOMAIN" ]; then
    echo "❌ Domaine FRONTEND non configuré."
    pause
    return 1
  fi

  cat > config_clients.txt <<EOF
===== Configurations clients Xray pour $DOMAIN =====
Ports utilisés:
- VLESS WS: ${PORTS[VLESS_WS]}
- Trojan WS: ${PORTS[TROJAN_WS]}
- VLESS TCP: ${PORTS[VLESS_TCP]}
- Trojan TCP: ${PORTS[TROJAN_TCP]}
- VMess: ${PORTS[VMESS]}
- Shadowsocks: ${PORTS[SHADOWSOCKS]}

-- VLESS WS TLS --
EOF

  for uuid in "${UUIDS_VLESS_WS[@]}"; do
    echo "vless://$uuid@$DOMAIN:443?encryption=none&security=tls&type=ws&path=%2Fws#$DOMAIN-VLESS-WS" >> config_clients.txt
  done

  echo -e "\n-- VLESS TCP TLS --" >> config_clients.txt
  for uuid in "${UUIDS_VLESS_TCP[@]}"; do
    echo "vless://$uuid@$DOMAIN:${PORTS[VLESS_TCP]}?security=tls&encryption=none&type=tcp#$DOMAIN-VLESS-TCP" >> config_clients.txt
  done

  echo -e "\n-- VMess WS TLS --" >> config_clients.txt
  for uuid in "${UUIDS_VMESS[@]}"; do
    vmess_json=$(jq -n --arg id "$uuid" --arg host "$DOMAIN" '{
      v: "2",
      ps: "vmess-ws",
      add: $host,
      port: "'${PORTS[VMESS]}'",
      id: $id,
      aid: "0",
      net: "ws",
      type: "none",
      host: $host,
      path: "/vmessws",
      tls: "tls"
    }')
    vmess_link="vmess://$(echo "$vmess_json" | base64 -w 0)"
    echo "$vmess_link" >> config_clients.txt
  done

  echo -e "\n-- Trojan WS TLS --" >> config_clients.txt
  for pwd in "${PASSWORDS_TROJAN_WS[@]}"; do
    echo "trojan://$pwd@$DOMAIN:443?security=tls&type=ws&path=%2Fws#$DOMAIN-Trojan-WS" >> config_clients.txt
  done

  echo -e "\n-- Trojan TCP TLS --" >> config_clients.txt
  for pwd in "${PASSWORDS_TROJAN_TCP[@]}"; do
    echo "trojan://$pwd@$DOMAIN:${PORTS[TROJAN_TCP]}?security=tls&type=tcp#$DOMAIN-Trojan-TCP" >> config_clients.txt
  done

  echo -e "\n-- Shadowsocks TCP --" >> config_clients.txt
  for pwd in "${PASSWORDS_SS[@]}"; do
    ss_link="ss://$(echo -n "aes-128-gcm:$pwd" | base64 -w 0)@$DOMAIN:${PORTS[SHADOWSOCKS]}#$DOMAIN-SS"
    echo "$ss_link" >> config_clients.txt
  done

  echo -e "\n===== Fin des configurations ====="
  echo "✅ Les liens clients ont été enregistrés dans le fichier config_clients.txt"
  pause
}

##############################################
# Change le domaine frontend
# Avec vérification des entrées et gestion des erreurs
##############################################
changer_domaine() {
  read -rp "Entrez le nouveau domaine FRONTEND à utiliser : " newdomain
  if [[ -z "$newdomain" ]]; then
    echo "❌ Domaine invalide."
    pause
    return 1
  fi
  
  read -rp "Confirmez votre email pour Let's Encrypt : " email
  if [[ ! "$email" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
    echo "❌ Email invalide"
    pause
    return 1
  fi
  
  DOMAIN="$newdomain"
  EMAIL="$email"
  echo "✅ Domaine FRONTEND modifié en : $DOMAIN"

  echo "🔄 Reconfiguration de Nginx et renouvellement certificat TLS..."

  rm -f /etc/nginx/sites-enabled/*
  rm -f /etc/nginx/sites-available/*

  cat > /etc/nginx/sites-available/"$DOMAIN".conf <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOF

  if ! ln -sf /etc/nginx/sites-available/"$DOMAIN".conf /etc/nginx/sites-enabled/; then
    echo "❌ Impossible de créer le lien symbolique Nginx" >&2
    return 1
  fi

  if ! nginx -t; then
    echo "❌ Configuration Nginx invalide" >&2
    return 1
  fi
  
  if ! systemctl reload nginx; then
    echo "❌ Impossible de recharger Nginx" >&2
    return 1
  fi

  if ! certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive --redirect; then
    echo "❌ Erreur lors du renouvellement du certificat TLS" >&2
    return 1
  fi

  cat > /etc/nginx/sites-available/"$DOMAIN".conf <<EOF
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    location /ws {
        proxy_redirect off;
        proxy_pass http://127.0.0.1:${PORTS[VLESS_WS]};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
    location /vmessws {
        proxy_redirect off;
        proxy_pass http://127.0.0.1:${PORTS[VMESS]};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
    location / {
        root /var/www/html;
        index index.html;
    }
}
EOF

  if ! nginx -t; then
    echo "❌ Configuration Nginx invalide après modification" >&2
    return 1
  fi
  
  if ! systemctl reload nginx; then
    echo "❌ Impossible de recharger Nginx après modification" >&2
    return 1
  fi
  
  if ! systemctl restart xray; then
    echo "⚠️ Impossible de redémarrer Xray" >&2
  fi

  echo "✅ Domaine et certificat mis à jour avec succès"
  pause
}

##############################################
# Affiche le menu principal
##############################################
show_menu() {
  clear
  echo "==============================="
  echo "         Gestion Xray VPS       "
  echo "==============================="
  echo "Domaine FRONTEND actuel : ${DOMAIN:-Non configuré}"
  echo ""
  echo "1) Installer Xray + Nginx + TLS"
  echo "2) Ajouter un utilisateur"
  echo "3) Supprimer un utilisateur"
  echo "4) Générer et afficher les liens clients"
  echo "5) Modifier le domaine FRONTEND"
  echo "6) Configurer les ports"
  echo "7) Redémarrer Xray"
  echo "0) Quitter"
  echo ""
  echo -n "Choisissez une option : "
}

##############################################
# Point d'entrée principal du script
##############################################
check_root
load_config

while true; do
  show_menu
  read -r choice
  case $choice in
    1) install_all ;;
    2) add_user ;;
    3) remove_user ;;
    4) generate_links ;;
    5) changer_domaine ;;
    6) configure_ports ;;
    7) 
      systemctl restart xray && echo "✅ Xray redémarré." || echo "❌ Échec du redémarrage de Xray" >&2
      pause 
      ;;
    0) 
      echo "👋 Au revoir !" 
      exit 0 
      ;;
    *) 
      echo "❌ Option invalide." 
      pause 
      ;;
  esac
done