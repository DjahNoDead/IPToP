#!/bin/bash

# Xray Config Generator - Contournement FAI
# Version: 1.2 - Affichage Complet
# Fonctionnalités :
# - Génération de configurations Xray optimisées
# - Affichage clair des paramètres
# - URLs de partage automatiques

# Vérification root
if [ "$(id -u)" != "0" ]; then
  echo -e "\033[1;31m[ERREUR] Ce script doit être exécuté en tant que root\033[0m" 1>&2
  exit 1
fi

# Détection de l'OS
OS=$(grep -oP '^ID=\K\w+' /etc/os-release 2>/dev/null)
[ -z "$OS" ] && OS=$(uname -s)

# Installation des dépendances
install_deps() {
  echo -e "\033[1;33m[*] Installation des dépendances...\033[0m"
  
  if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt update && apt install -y curl openssl uuid-runtime jq
  elif [ "$OS" = "centos" ]; then
    yum install -y curl openssl util-linux jq
  else
    echo -e "\033[1;33m[!] OS non supporté - continuation sans installer de paquets\033[0m"
  fi

  # Installation Xray
  echo -e "\033[1;33m[*] Installation de Xray...\033[0m"
  bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
}

# Génération de configuration
generate_config() {
  local protocol=$1
  local port=$2
  local uuid=$(uuidgen)
  local path="/$(openssl rand -hex 4)"
  local config_file="/usr/local/etc/xray/config.json"
  local public_ip=$(curl -4s ifconfig.co)

  echo -e "\033[1;33m[*] Génération configuration $protocol...\033[0m"

  case $protocol in
    "vless-reality")
      local private_key=$(openssl rand -hex 32)
      local short_id=$(openssl rand -hex 8)
      cat > $config_file <<EOL
{
  "inbounds": [
    {
      "port": $port,
      "protocol": "vless",
      "settings": {
        "clients": [{"id": "$uuid", "flow": "xtls-rprx-vision"}],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "dest": "www.google.com:443",
          "serverNames": ["www.google.com"],
          "privateKey": "$private_key",
          "shortIds": ["$short_id"]
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
  esac

  # Retourner les valeurs générées
  echo "$uuid:$path:$private_key:$short_id:$public_ip"
}

# Affichage complet
show_config() {
  clear
  echo -e "\033[1;36m"
  echo "================================================"
  echo "   CONFIGURATION XRAY GENEREE AVEC SUCCES       "
  echo "================================================"
  echo -e "\033[0m"
  echo -e "\033[1;32mType:\033[0m $config_type"
  echo -e "\033[1;32mAdresse IP:\033[0m $public_ip"
  echo -e "\033[1;32mPort:\033[0m $config_port"
  echo -e "\033[1;32mUUID/Password:\033[0m $uuid"
  
  case $choice in
    1)
      echo -e "\033[1;32mFlow:\033[0m xtls-rprx-vision"
      echo -e "\033[1;32mSNI:\033[0m www.google.com"
      echo -e "\033[1;32mPrivate Key:\033[0m $private_key"
      echo -e "\033[1;32mShort ID:\033[0m $short_id"
      ;;
    2)
      echo -e "\033[1;33m[NOTE] Configurez TLS avec Certbot pour une utilisation réelle"
      ;;
    3)
      echo -e "\033[1;32mPath WebSocket:\033[0m $path"
      ;;
  esac

  echo
  echo -e "\033[1;36mURL de partage:\033[0m"
  case $choice in
    1)
      echo -e "\033[1;35mvless://$uuid@$public_ip:$config_port?type=tcp&security=reality&sni=www.google.com&flow=xtls-rprx-vision&pbk=$private_key&sid=$short_id#Xray_Reality\033[0m"
      ;;
    2)
      echo -e "\033[1;35mtrojan://$uuid@$public_ip:$config_port?security=tls&type=tcp&headerType=none#Xray_Trojan\033[0m"
      ;;
    3)
      local vmess_config="{\"v\":\"2\",\"ps\":\"Xray_VMess\",\"add\":\"$public_ip\",\"port\":\"$config_port\",\"id\":\"$uuid\",\"aid\":\"0\",\"scy\":\"none\",\"net\":\"ws\",\"type\":\"none\",\"path\":\"$path\"}"
      echo -e "\033[1;35mvmess://$(echo "$vmess_config" | base64 -w 0)\033[0m"
      ;;
  esac

  echo
  echo -e "\033[1;36mFichier de configuration:\033[0m $config_file"
  echo -e "\033[1;36mRedémarrer Xray:\033[0m systemctl restart xray"
  echo
  echo -e "\033[1;33mCopiez l'URL ci-dessus directement dans votre client VPN\033[0m"
  echo -e "\033[1;36m================================================\033[0m"
}

# Menu principal
main_menu() {
  while true; do
    clear
    echo -e "\033[1;36m"
    echo "================================================"
    echo "   Générateur de Configuration Xray             "
    echo "   Pour contournement des restrictions FAI      "
    echo "================================================"
    echo -e "\033[0m"
    echo -e "\033[1;33m1. VLESS + Reality (Recommandé - Meilleure furtivité)"
    echo "2. Trojan + TLS (Nécessite un domaine et certificat)"
    echo "3. VMess + WebSocket (Compatibilité maximale)"
    echo "4. Quitter"
    echo -e "\033[0m"
    read -p "Choix [1-4]: " choice

    case $choice in
      1)
        config_data=$(generate_config "vless-reality" 443)
        IFS=':' read -r uuid path private_key short_id public_ip <<< "$config_data"
        config_port=443
        config_type="VLESS + Reality"
        show_config
        ;;
      2)
        config_data=$(generate_config "trojan-tls" 8443)
        IFS=':' read -r uuid path _ _ public_ip <<< "$config_data"
        config_port=8443
        config_type="Trojan + TLS"
        show_config
        ;;
      3)
        config_data=$(generate_config "vmess-ws" 8080)
        IFS=':' read -r uuid path _ _ public_ip <<< "$config_data"
        config_port=8080
        config_type="VMess + WebSocket"
        show_config
        ;;
      4)
        exit 0
        ;;
      *)
        echo -e "\033[1;31mOption invalide!\033[0m"
        sleep 1
        ;;
    esac

    read -p "Appuyez sur Entrée pour revenir au menu..."
  done
}

# Point d'entrée
install_deps
main_menu