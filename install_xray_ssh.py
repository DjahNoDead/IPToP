import os
import subprocess
import uuid
import json

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur: {e}")
        exit(1)

def generate_uuid():
    return str(uuid.uuid4())

def install_xray():
    print("🔄 Mise à jour du système...")
    run_command("sudo apt update -y && sudo apt upgrade -y")

    print("📦 Installation des dépendances...")
    run_command("sudo apt install -y curl wget unzip nginx certbot python3-certbot-nginx")

    print("⬇️ Installation de Xray...")
    run_command("bash -c \"$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)\" @ install")

def configure_xray(domain):
    # Génération des identifiants
    vless_uuid = generate_uuid()
    vmess_uuid = generate_uuid()
    trojan_password = generate_uuid()
    shadowsocks_password = generate_uuid()

    print(f"🔑 UUID VLESS: {vless_uuid}")
    print(f"🔑 UUID VMess: {vmess_uuid}")
    print(f"🔑 Mot de passe Trojan: {trojan_password}")
    print(f"🔑 Mot de passe Shadowsocks: {shadowsocks_password}")

    # Configuration Xray (sans Reality)
    xray_config = {
        "inbounds": [
            # VLESS + TLS (Port 443)
            {
                "port": 443,
                "protocol": "vless",
                "settings": {
                    "clients": [{"id": vless_uuid}],
                    "decryption": "none"
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": "tls",
                    "tlsSettings": {
                        "certificates": [
                            {
                                "certificateFile": f"/etc/letsencrypt/live/{domain}/fullchain.pem",
                                "keyFile": f"/etc/letsencrypt/live/{domain}/privkey.pem"
                            }
                        ]
                    }
                }
            },
            # VMess (Port 8443)
            {
                "port": 8443,
                "protocol": "vmess",
                "settings": {
                    "clients": [{"id": vmess_uuid}]
                }
            },
            # Trojan (Port 8444)
            {
                "port": 8444,
                "protocol": "trojan",
                "settings": {
                    "clients": [{"password": trojan_password}]
                },
                "streamSettings": {
                    "security": "tls",
                    "tlsSettings": {
                        "certificates": [
                            {
                                "certificateFile": f"/etc/letsencrypt/live/{domain}/fullchain.pem",
                                "keyFile": f"/etc/letsencrypt/live/{domain}/privkey.pem"
                            }
                        ]
                    }
                }
            },
            # Shadowsocks (Port 8445)
            {
                "port": 8445,
                "protocol": "shadowsocks",
                "settings": {
                    "method": "chacha20-ietf-poly1305",
                    "password": shadowsocks_password,
                    "network": "tcp,udp"
                }
            }
        ],
        "outbounds": [{"protocol": "freedom"}]
    }

    with open("/usr/local/etc/xray/config.json", "w") as f:
        json.dump(xray_config, f, indent=2)

    print("✅ Configuration Xray appliquée.")

def setup_nginx_and_ssl(domain):
    # Création des dossiers si inexistants
    os.makedirs("/etc/nginx/sites-available", exist_ok=True)
    os.makedirs("/etc/nginx/sites-enabled", exist_ok=True)
    
    print("🌐 Configuration de Nginx...")
    nginx_conf = f"""
    server {{
        listen 80;
        server_name {domain};
        location / {{
            return 301 https://$host$request_uri;
        }}
    }}
    """
    run_command(f"sudo rm -f /etc/nginx/sites-enabled/default")
    with open(f"/etc/nginx/sites-available/{domain}", "w") as f:
        f.write(nginx_conf.strip())
    run_command(f"sudo ln -sf /etc/nginx/sites-available/{domain} /etc/nginx/sites-enabled/")
    run_command("sudo systemctl restart nginx")

def restart_services():
    print("🔄 Redémarrage des services...")
    run_command("sudo systemctl restart xray")
    run_command("sudo systemctl restart nginx")
    run_command("sudo systemctl enable xray")

def main():
    domain = input("🌍 Entrez votre nom de domaine (ex: vpn.mondomaine.com): ").strip()
    
    install_xray()
    configure_xray(domain)
    setup_nginx_and_ssl(domain)
    restart_services()

    print("\n🎉 Installation terminée !")
    print("🔗 Partagez ces identifiants avec vos utilisateurs :")
    print(f"""
    🔹 VLESS (TLS):
      - Address: {domain}
      - Port: 443
      - UUID: {generate_uuid()}

    🔹 VMess:
      - Address: {domain}
      - Port: 8443
      - UUID: {generate_uuid()}

    🔹 Trojan:
      - Address: {domain}
      - Port: 8444
      - Password: {generate_uuid()}

    🔹 Shadowsocks:
      - Address: {domain}
      - Port: 8445
      - Password: {generate_uuid()}
      - Method: chacha20-ietf-poly1305
    """)

if __name__ == "__main__":
    main()