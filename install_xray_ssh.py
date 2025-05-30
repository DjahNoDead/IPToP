import os
import subprocess
import uuid
import json
import secrets
import sys

def run_command(command, check=True):
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur: {e.stderr.strip()}")
        sys.exit(1)

def generate_uuid():
    return str(uuid.uuid4())

def generate_reality_keys():
    # Génère une clé privée
    priv_key = run_command("xray x25519")
    # Extrait la clé privée pure (sans le texte)
    priv_key_clean = priv_key.split("Private key: ")[1].strip()
    # Génère la clé publique correspondante
    pub_key = run_command(f"xray x25519 -i {priv_key_clean}")
    pub_key_clean = pub_key.split("Public key: ")[1].strip()
    return priv_key_clean, pub_key_clean

def install_xray():
    print("🔄 Mise à jour du système...")
    run_command("sudo apt update -y && sudo apt upgrade -y")

    print("📦 Installation des dépendances...")
    run_command("sudo apt install -y curl wget unzip nginx certbot python3-certbot-nginx")

    print("⬇️ Téléchargement et installation de Xray...")
    run_command("bash -c \"$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)\" @ install")

def configure_xray(domain, priv_key, pub_key):
    vless_uuid = generate_uuid()
    vmess_uuid = generate_uuid()
    trojan_password = generate_uuid()
    shadowsocks_password = generate_uuid()

    print("\n🔑 Identifiants générés :")
    print(f"  - VLESS (Reality) UUID: {vless_uuid}")
    print(f"  - VMess UUID: {vmess_uuid}")
    print(f"  - Trojan Password: {trojan_password}")
    print(f"  - Shadowsocks Password: {shadowsocks_password}")
    print(f"  - Reality Private Key: {priv_key}")
    print(f"  - Reality Public Key: {pub_key}\n")

    xray_config = {
        "inbounds": [
            # Reality (XTLS)
            {
                "port": 443,
                "protocol": "vless",
                "settings": {
                    "clients": [{"id": vless_uuid, "flow": "xtls-rprx-vision"}],
                    "decryption": "none",
                    "fallbacks": [
                        {"dest": 80},
                        {"path": "/grpc", "dest": 50051, "xver": 1}
                    ]
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": "reality",
                    "realitySettings": {
                        "show": False,
                        "dest": f"{domain}:443",
                        "xver": 1,
                        "serverNames": [domain],
                        "privateKey": priv_key,
                        "shortIds": ["88", "1234abcd"]
                    }
                }
            },
            # VMess + WebSocket
            {
                "port": 8443,
                "protocol": "vmess",
                "settings": {
                    "clients": [{"id": vmess_uuid}]
                },
                "streamSettings": {
                    "network": "ws",
                    "wsSettings": {"path": "/vmess"}
                }
            },
            # Trojan + TLS
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
            # Shadowsocks
            {
                "port": 8445,
                "protocol": "shadowsocks",
                "settings": {
                    "method": "chacha20-ietf-poly1305",
                    "password": shadowsocks_password,
                    "network": "tcp,udp"
                }
            },
            # gRPC
            {
                "port": 50051,
                "protocol": "vless",
                "settings": {
                    "clients": [{"id": generate_uuid()}],
                    "decryption": "none"
                },
                "streamSettings": {
                    "network": "grpc",
                    "grpcSettings": {"serviceName": "grpc"}
                }
            }
        ],
        "outbounds": [{"protocol": "freedom"}]
    }

    with open("/usr/local/etc/xray/config.json", "w") as f:
        json.dump(xray_config, f, indent=2)

    print("✅ Configuration Xray appliquée.")

def setup_nginx_and_ssl(domain):
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

    print("🔐 Obtention du certificat SSL...")
    run_command(f"sudo certbot --nginx -d {domain} --non-interactive --agree-tos --email admin@{domain}")

def restart_services():
    print("🔄 Redémarrage des services...")
    run_command("sudo systemctl restart xray")
    run_command("sudo systemctl restart nginx")
    run_command("sudo systemctl enable xray")

def main():
    if not os.getenv("SSH_CONNECTION"):
        print("⚠️ Ce script doit être exécuté en SSH sur le VPS.")
        sys.exit(1)

    domain = input("🌍 Entrez votre nom de domaine (ex: vpn.mondomaine.com): ").strip()
    priv_key, pub_key = generate_reality_keys()

    install_xray()
    configure_xray(domain, priv_key, pub_key)
    setup_nginx_and_ssl(domain)
    restart_services()

    print("\n🎉 Installation terminée !")
    print("🔗 Partagez ces identifiants avec vos utilisateurs :")
    print(f"""
    🔹 Reality (VLESS + XTLS):
      - Address: {domain}
      - Port: 443
      - UUID: {generate_uuid()}
      - Public Key: {pub_key}
      - Short ID: 88
      - Flow: xtls-rprx-vision

    🔹 VMess (WebSocket):
      - Address: {domain}
      - Port: 8443
      - UUID: {generate_uuid()}
      - Path: /vmess

    🔹 Trojan (TLS):
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
