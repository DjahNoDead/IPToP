#!/bin/bash

# Xray Config Generator - Contournement FAI
# Version: 1.0
# Fonctionnalités :
# - Génération de configurations Xray optimisées
# - Contournement DPI intégré
# - Support multi-protocoles
# - Installation automatique

# Vérification root
if [ "$(id -u)" != "0" ]; then
  echo "Ce script doit être exécuté en tant que root" 1>&2
  exit 1
fi

# Détection de l'OS
OS=$(grep -oP '^ID=\K\w+' /etc/os-release)
[ -z "$OS" ] && OS=$(uname -s)

# Installation des dépendances
install_deps() {
  echo "[*] Installation des dépendances..."
  if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt update && apt install -y curl openssl uuid-runtime
  elif [ "$OS" = "centos" ]; then
    yum install -y curl openssl util-linux
  fi

  # Installation Xray
  bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
}

# Génération de configuration
generate_config() {
  local protocol=$1
  local port=$2
  local uuid=$(uuidgen)
  local path="/$(openssl rand -hex 4)"
  local config_file="/usr/local/etc/xray/config.json"

  echo "[*] Génération configuration $protocol..."

  case $protocol in
    "vless-reality")
      cat > $config_file <<EOL
{
  "inbounds": [
    {
      "port": $port,
      "protocol": "vless",
      "settings": {
        "clients": [{"id": "$uuid"}],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "dest": "www.google.com:443",
          "serverNames": ["www.google.com"],
          "privateKey": "$(openssl rand -hex 32)",
          "shortIds": ["$(openssl rand -hex 8)"]
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
      ;;
    "trojan-tls")
      cat > $config_file <<EOL
{
  "inbounds": [
    {
      "port": $port,
      "protocol": "trojan",
      "settings": {
        "clients": [{"password": "$uuid"}]
      },
      "streamSettings": {
        "security": "tls",
        "tlsSettings": {
          "certificates": [
            {
              "certificateFile": "/etc/letsencrypt/live/domain.com/fullchain.pem",
              "keyFile": "/etc/letsencrypt/live/domain.com/privkey.pem"
            }
          ]
        }
      }
    }
  ]
}
EOL
      ;;
    "vmess-ws")
      cat > $config_file <<EOL
{
  "inbounds": [
    {
      "port": $port,
      "protocol": "vmess",
      "settings": {
        "clients": [{"id": "$uuid"}]
      },
      "streamSettings": {
        "network": "ws",
        "wsSettings": {"path": "$path"}
      }
    }
  ]
}
EOL
      ;;
  esac

  echo "[+] Configuration générée: $config_file"
}

# Menu principal
show_menu() {
  clear
  echo "======================================"
  echo "  Générateur de Configuration Xray"
  echo "  Pour contournement des restrictions FAI"
  echo "======================================"
  echo
  echo "1. VLESS + Reality (Recommandé)"
  echo "2. Trojan + TLS"
  echo "3. VMess + WebSocket"
  echo "4. Quitter"
  echo
  read -p "Choix [1-4]: " choice

  case $choice in
    1) generate_config "vless-reality" 443;;
    2) generate_config "trojan-tls" 8443;;
    3) generate_config "vmess-ws" 8080;;
    4) exit 0;;
    *) echo "Option invalide"; sleep 1;;
  esac

  # Redémarrer Xray
  systemctl restart xray
  echo "[*] Configuration appliquée. Utilisez ces paramètres:"
  echo " - UUID/Password: $uuid"
  [ -n "$path" ] && echo " - Path: $path"
  echo " - Port: $port"
}

# Point d'entrée
install_deps
show_menu