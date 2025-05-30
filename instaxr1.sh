#!/bin/bash

CONFIG_PATH="/usr/local/etc/xray/config.json"
Xray_BIN="/usr/local/bin/xray"
DOMAIN=""
EMAIL=""

# Listes utilisateurs
UUIDS_VLESS_WS=()
UUIDS_VLESS_TCP=()
UUIDS_VMESS=()
PASSWORDS_TROJAN_WS=()
PASSWORDS_TROJAN_TCP=()
PASSWORDS_SS=()

generate_uuid() {
  cat /proc/sys/kernel/random/uuid
}

random_password() {
  tr -dc A-Za-z0-9 </dev/urandom | head -c 16
}

check_root() {
  if [ "$EUID" -ne 0 ]; then
    echo "⚠️ Ce script doit être lancé en root."
    exit 1
  fi
}

pause() {
  read -rp "Appuyez sur Entrée pour continuer..."
}

load_config() {
  if [ -f "$CONFIG_PATH" ]; then
    DOMAIN=$(grep -oP '(?<=server_name )[^;]+' /etc/nginx/sites-available/"$DOMAIN".conf 2>/dev/null)
    UUIDS_VLESS_WS=($(jq -r '.inbounds[] | select(.protocol=="vless" and .streamSettings.network=="ws") | .settings.clients[].id' "$CONFIG_PATH" 2>/dev/null))
    UUIDS_VLESS_TCP=($(jq -r '.inbounds[] | select(.protocol=="vless" and .streamSettings.network=="tcp") | .settings.clients[].id' "$CONFIG_PATH" 2>/dev/null))
    UUIDS_VMESS=($(jq -r '.inbounds[] | select(.protocol=="vmess") | .settings.clients[].id' "$CONFIG_PATH" 2>/dev/null))
    PASSWORDS_TROJAN_WS=($(jq -r '.inbounds[] | select(.protocol=="trojan" and .streamSettings.network=="ws") | .settings.clients[].password' "$CONFIG_PATH" 2>/dev/null))
    PASSWORDS_TROJAN_TCP=($(jq -r '.inbounds[] | select(.protocol=="trojan" and .streamSettings.network=="tcp") | .settings.clients[].password' "$CONFIG_PATH" 2>/dev/null))
    PASSWORDS_SS=($(jq -r '.inbounds[] | select(.protocol=="shadowsocks") | .settings.clients[].password' "$CONFIG_PATH" 2>/dev/null))
  fi
}

save_config() {
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

  cat > "$CONFIG_PATH" <<EOF
{
  "log": {
    "access": "/var/log/xray/access.log",
    "error": "/var/log/xray/error.log",
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "port": 10000,
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
      "port": 10001,
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
      "port": 10002,
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
      "port": 10003,
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
      "port": 10004,
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
      "port": 10005,
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
}

install_all() {
  echo "🔄 Mise à jour et installation des paquets..."
  apt update && apt upgrade -y
  apt install -y curl wget unzip nginx socat ufw certbot python3-certbot-nginx fail2ban jq

  echo "✅ Configuration UFW..."
  ufw allow 'OpenSSH'
  ufw allow 80
  ufw allow 443
  ufw --force enable

  echo "✅ Activation Fail2ban..."
  systemctl enable fail2ban
  systemctl start fail2ban

  echo "✅ Installation Xray-core..."
  bash <(curl -Ls https://raw.githubusercontent.com/XTLS/Xray-install/main/install-release.sh)

  mkdir -p /usr/local/etc/xray
  mkdir -p /var/log/xray

  read -rp "➡️ Entrez le nom de domaine FRONTEND (exemple : proxy.exemple.com) : " DOMAIN
  read -rp "➡️ Entrez votre email pour Let's Encrypt : " EMAIL

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
  ln -sf /etc/nginx/sites-available/"$DOMAIN".conf /etc/nginx/sites-enabled/
  nginx -t && systemctl reload nginx

  certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive

  echo "✅ Configuration Nginx reverse proxy..."
  cat > /etc/nginx/sites-available/"$DOMAIN".conf <<EOF
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    location /ws {
        proxy_redirect off;
        proxy_pass http://127.0.0.1:10000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
    location /vmessws {
        proxy_redirect off;
        proxy_pass http://127.0.0.1:10004;
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
  nginx -t && systemctl reload nginx

  # Init arrays
  UUIDS_VLESS_WS=()
  UUIDS_VLESS_TCP=()
  UUIDS_VMESS=()
  PASSWORDS_TROJAN_WS=()
  PASSWORDS_TROJAN_TCP=()
  PASSWORDS_SS=()

  # Générer 1 utilisateur de chaque type par défaut
  UUIDS_VLESS_WS+=("$(generate_uuid)")
  UUIDS_VLESS_TCP+=("$(generate_uuid)")
  UUIDS_VMESS+=("$(generate_uuid)")
  PASSWORDS_TROJAN_WS+=("$(random_password)")
  PASSWORDS_TROJAN_TCP+=("$(random_password)")
  PASSWORDS_SS+=("$(random_password)")

  save_config

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

  systemctl daemon-reexec
  systemctl enable xray
  systemctl restart xray

  echo "✅ Installation terminée avec un utilisateur par protocole créé."
  pause
}

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
      id=$(generate_uuid)
      UUIDS_VLESS_WS+=("$id")
      echo "Utilisateur VLESS WS ajouté : $id"
      ;;
    2)
      id=$(generate_uuid)
      UUIDS_VLESS_TCP+=("$id")
      echo "Utilisateur VLESS TCP ajouté : $id"
      ;;
    3)
      id=$(generate_uuid)
      UUIDS_VMESS+=("$id")
      echo "Utilisateur VMess WS ajouté : $id"
      ;;
    4)
      pwd=$(random_password)
      PASSWORDS_TROJAN_WS+=("$pwd")
      echo "Utilisateur Trojan WS ajouté : $pwd"
      ;;
    5)
      pwd=$(random_password)
      PASSWORDS_TROJAN_TCP+=("$pwd")
      echo "Utilisateur Trojan TCP ajouté : $pwd"
      ;;
    6)
      pwd=$(random_password)
      PASSWORDS_SS+=("$pwd")
      echo "Utilisateur Shadowsocks ajouté : $pwd"
      ;;
    0) return ;;
    *) echo "Option invalide." ; pause ;;
  esac
  save_config
  echo "✅ Utilisateur ajouté et configuration mise à jour."
  pause
}

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
      echo "Utilisateurs VLESS WS existants :"
      for i in "${!UUIDS_VLESS_WS[@]}"; do
        echo "$i) ${UUIDS_VLESS_WS[$i]}"
      done
      read -rp "Entrez le numéro de l'utilisateur à supprimer : " num
      if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 0 ] && [ "$num" -lt "${#UUIDS_VLESS_WS[@]}" ]; then
        unset 'UUIDS_VLESS_WS[num]'
        UUIDS_VLESS_WS=("${UUIDS_VLESS_WS[@]}") # Ré-indexer
        echo "✅ Utilisateur supprimé."
      else
        echo "❌ Numéro invalide."
      fi
      ;;
    2)
      echo "Utilisateurs VLESS TCP existants :"
      for i in "${!UUIDS_VLESS_TCP[@]}"; do
        echo "$i) ${UUIDS_VLESS_TCP[$i]}"
      done
      read -rp "Entrez le numéro de l'utilisateur à supprimer : " num
      if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 0 ] && [ "$num" -lt "${#UUIDS_VLESS_TCP[@]}" ]; then
        unset 'UUIDS_VLESS_TCP[num]'
        UUIDS_VLESS_TCP=("${UUIDS_VLESS_TCP[@]}") # Ré-indexer
        echo "✅ Utilisateur supprimé."
      else
        echo "❌ Numéro invalide."
      fi
      ;;
    3)
      echo "Utilisateurs VMess WS existants :"
      for i in "${!UUIDS_VMESS[@]}"; do
        echo "$i) ${UUIDS_VMESS[$i]}"
      done
      read -rp "Entrez le numéro de l'utilisateur à supprimer : " num
      if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 0 ] && [ "$num" -lt "${#UUIDS_VMESS[@]}" ]; then
        unset 'UUIDS_VMESS[num]'
        UUIDS_VMESS=("${UUIDS_VMESS[@]}") # Ré-indexer
        echo "✅ Utilisateur supprimé."
      else
        echo "❌ Numéro invalide."
      fi
      ;;
    4)
      echo "Utilisateurs Trojan WS existants :"
      for i in "${!PASSWORDS_TROJAN_WS[@]}"; do
        echo "$i) ${PASSWORDS_TROJAN_WS[$i]}"
      done
      read -rp "Entrez le numéro de l'utilisateur à supprimer : " num
      if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 0 ] && [ "$num" -lt "${#PASSWORDS_TROJAN_WS[@]}" ]; then
        unset 'PASSWORDS_TROJAN_WS[num]'
        PASSWORDS_TROJAN_WS=("${PASSWORDS_TROJAN_WS[@]}") # Ré-indexer
        echo "✅ Utilisateur supprimé."
      else
        echo "❌ Numéro invalide."
      fi
      ;;
    5)
      echo "Utilisateurs Trojan TCP existants :"
      for i in "${!PASSWORDS_TROJAN_TCP[@]}"; do
        echo "$i) ${PASSWORDS_TROJAN_TCP[$i]}"
      done
      read -rp "Entrez le numéro de l'utilisateur à supprimer : " num
      if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 0 ] && [ "$num" -lt "${#PASSWORDS_TROJAN_TCP[@]}" ]; then
        unset 'PASSWORDS_TROJAN_TCP[num]'
        PASSWORDS_TROJAN_TCP=("${PASSWORDS_TROJAN_TCP[@]}") # Ré-indexer
        echo "✅ Utilisateur supprimé."
      else
        echo "❌ Numéro invalide."
      fi
      ;;
    6)
      echo "Utilisateurs Shadowsocks TCP existants :"
      for i in "${!PASSWORDS_SS[@]}"; do
        echo "$i) ${PASSWORDS_SS[$i]}"
      done
      read -rp "Entrez le numéro de l'utilisateur à supprimer : " num
      if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 0 ] && [ "$num" -lt "${#PASSWORDS_SS[@]}" ]; then
        unset 'PASSWORDS_SS[num]'
        PASSWORDS_SS=("${PASSWORDS_SS[@]}") # Ré-indexer
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
  save_config
  pause
}

generate_links() {
  echo "=== Génération des liens clients ==="
  if [ -z "$DOMAIN" ]; then
    echo "❌ Domaine FRONTEND non configuré."
    pause
    return
  fi

  cat > config_clients.txt <<EOF
===== Configurations clients Xray pour $DOMAIN =====

-- VLESS WS TLS --
EOF
  for uuid in "${UUIDS_VLESS_WS[@]}"; do
    echo "vless://$uuid@$DOMAIN:443?encryption=none&security=tls&type=ws&path=%2Fws#$DOMAIN-VLESS-WS" >> config_clients.txt
  done

  echo -e "\n-- VLESS TCP TLS --" >> config_clients.txt
  for uuid in "${UUIDS_VLESS_TCP[@]}"; do
    echo "vless://$uuid@$DOMAIN:10002?security=tls&encryption=none&type=tcp#$DOMAIN-VLESS-TCP" >> config_clients.txt
  done

  echo -e "\n-- VMess WS TLS --" >> config_clients.txt
  for uuid in "${UUIDS_VMESS[@]}"; do
    vmess_json=$(jq -n --arg id "$uuid" --arg host "$DOMAIN" '{
      v: "2",
      ps: "vmess-ws",
      add: $host,
      port: "10004",
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
    echo "trojan://$pwd@$DOMAIN:10003?security=tls&type=tcp#$DOMAIN-Trojan-TCP" >> config_clients.txt
  done

  echo -e "\n-- Shadowsocks TCP --" >> config_clients.txt
  for pwd in "${PASSWORDS_SS[@]}"; do
    ss_link="ss://$(echo -n "aes-128-gcm:$pwd" | base64 -w 0)@$DOMAIN:10005#$DOMAIN-SS"
    echo "$ss_link" >> config_clients.txt
  done

  echo -e "\n===== Fin des configurations ====="
  echo "✅ Les liens clients ont été enregistrés dans le fichier config_clients.txt"
  pause
}

changer_domaine() {
  read -rp "Entrez le nouveau domaine FRONTEND à utiliser : " newdomain
  if [[ -z "$newdomain" ]]; then
    echo "❌ Domaine invalide."
    pause
    return
  fi
  DOMAIN="$newdomain"
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
  ln -sf /etc/nginx/sites-available/"$DOMAIN".conf /etc/nginx/sites-enabled/

  nginx -t && systemctl reload nginx

  certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive --redirect

  cat > /etc/nginx/sites-available/"$DOMAIN".conf <<EOF
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    location /ws {
        proxy_redirect off;
        proxy_pass http://127.0.0.1:10000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
    location /vmessws {
        proxy_redirect off;
        proxy_pass http://127.0.0.1:10004;
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
  nginx -t && systemctl reload nginx
  pause
}

show_menu() {
  clear
  echo "==============================="
  echo "         Gestion Xray VPS       "
  echo "==============================="
  echo "Domaine FRONTEND actuel : $DOMAIN"
  echo ""
  echo "1) Installer Xray + Nginx + TLS"
  echo "2) Ajouter un utilisateur"
  echo "3) Supprimer un utilisateur"
  echo "4) Générer et afficher les liens clients"
  echo "5) Modifier le domaine FRONTEND"
  echo "6) Redémarrer Xray"
  echo "0) Quitter"
  echo ""
  echo -n "Choisissez une option : "
}

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
    6) systemctl restart xray && echo "✅ Xray redémarré." && pause ;;
    0) echo "👋 Au revoir !" && exit 0 ;;
    *) echo "❌ Option invalide." && pause ;;
  esac
done