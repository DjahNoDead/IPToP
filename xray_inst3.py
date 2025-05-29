#!/usr/bin/env python3
import os
import sys
import json
import uuid
import subprocess
from getpass import getpass
import re
import shutil
from datetime import datetime
import socket

# Configuration
DOMAINS = ["votre-domaine1.com", "votre-domaine2.com"]  # À modifier
EMAIL = "votre@email.com"  # Pour Let's Encrypt
XRAY_CONFIG_PATH = "/usr/local/etc/xray/config.json"
ACME_SH_INSTALL_CMD = "curl https://get.acme.sh | sh"

# Couleurs pour l'affichage
class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_section(title):
    print(f"\n{Color.BOLD}{Color.BLUE}{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}{Color.RESET}")

def print_info(msg):
    print(f"{Color.GREEN}[INFO]{Color.RESET} {msg}")

def print_error(msg):
    print(f"{Color.RED}[ERREUR]{Color.RESET} {msg}")

def run_command(cmd, check=True):
    print_info(f"Exécution : {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=check)
    except subprocess.CalledProcessError as e:
        print_error(f"Échec de la commande : {cmd}")
        sys.exit(1)

def install_dependencies():
    print_section("Installation des dépendances")
    run_command("apt update && apt install -y curl socat jq unzip uuid-runtime")

def install_xray():
    print_section("Installation de Xray")
    run_command("curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh -o xray-install.sh")
    run_command("bash xray-install.sh install")

def setup_ssl_certificates():
    print_section("Configuration des certificats SSL")
    run_command(ACME_SH_INSTALL_CMD, check=False)
    
    for domain in DOMAINS:
        print_info(f"Traitement du domaine : {domain}")
        
        # Émission du certificat
        run_command(f"~/.acme.sh/acme.sh --issue -d {domain} --standalone -k ec-256 --accountemail {EMAIL}")
        
        # Création du dossier de certificat
        run_command(f"mkdir -p /etc/letsencrypt/live/{domain}")
        
        # Installation du certificat
        run_command(f"~/.acme.sh/acme.sh --install-cert -d {domain} --ecc "
                   f"--key-file /etc/letsencrypt/live/{domain}/privkey.pem "
                   f"--fullchain-file /etc/letsencrypt/live/{domain}/fullchain.pem")

def generate_xray_config():
    print_section("Génération de la configuration Xray")

    inbounds = []
    client_configs = []

    port_counter = 10000  # port de départ arbitraire pour éviter conflits

    for domain in DOMAINS:
        for proto in SELECTED_PROTOCOLS:
            for transport in SELECTED_TRANSPORTS:
                user_uuid = str(uuid.uuid4())

                inbound = {
                    "port": port_counter,
                    "protocol": proto,
                    "settings": {"clients": []},
                    "streamSettings": {
                        "network": transport,
                        "security": "tls",
                        "tlsSettings": {
                            "certificates": [{
                                "certificateFile": f"/etc/letsencrypt/live/{domain}/fullchain.pem",
                                "keyFile": f"/etc/letsencrypt/live/{domain}/privkey.pem"
                            }]
                        }
                    }
                }

                if proto == "vless":
                    inbound["settings"] = {
                        "clients": [{"id": user_uuid, "flow": "xtls-rprx-vision"}],
                        "decryption": "none"
                    }
                elif proto == "vmess":
                    inbound["settings"] = {
                        "clients": [{"id": user_uuid, "alterId": 0}],
                        "disableInsecureEncryption": True
                    }
                elif proto == "trojan":
                    inbound["settings"] = {
                        "clients": [{"password": user_uuid}]
                    }
                elif proto == "shadowsocks":
                    inbound["settings"] = {
                        "method": "aes-128-gcm",
                        "password": user_uuid,
                        "network": transport
                    }

                if transport == "ws":
                    inbound["streamSettings"]["wsSettings"] = {
                        "path": f"/{proto}",
                        "headers": {"Host": domain}
                    }
                elif transport == "grpc":
                    inbound["streamSettings"]["grpcSettings"] = {
                        "serviceName": f"{proto}_grpc"
                    }
                elif transport == "h2":
                    inbound["streamSettings"]["httpSettings"] = {
                        "path": f"/{proto}"
                    }

                inbounds.append(inbound)

                client_config = {
                    "domain": domain,
                    "protocol": proto,
                    "uuid": user_uuid,
                    "port": port_counter,
                    "path": f"/{proto}",
                    "transport": transport,
                    "security": "tls"
                }
                client_configs.append(client_config)

                port_counter += 1

    config = {
        "log": {"loglevel": "warning"},
        "inbounds": inbounds,
        "outbounds": [{"protocol": "freedom"}]
    }

    if os.path.exists(XRAY_CONFIG_PATH):
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = f"{XRAY_CONFIG_PATH}.bak.{timestamp}"
        shutil.copy2(XRAY_CONFIG_PATH, backup_path)
        print_info(f"Ancienne configuration sauvegardée : {backup_path}")

    os.makedirs(os.path.dirname(XRAY_CONFIG_PATH), exist_ok=True)
    with open(XRAY_CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

    return client_configs

def show_client_configs(client_configs):
    print_section("Configurations client")
    for config in client_configs:
        print_info(f"\nDomaine: {config['domain']}")
        print(f"Protocole: {Color.BOLD}{config['protocol']}{Color.RESET}")
        print(f"UUID/Password: {config['uuid']}")
        print(f"Port: {config['port']}")
        print(f"Transport: {config['transport']}")
        print(f"Path/Service: {config.get('path', '-')}")
        print(f"Sécurité: {config['security']}")

        if config["protocol"] in {"vless", "vmess"}:
            link = (
                f"{config['protocol']}://{config['uuid']}@{config['domain']}:{config['port']}?"
                f"encryption=none&security={config['security']}&type={config['transport']}&"
                f"path={config['path']}&host={config['domain']}#{config['domain']}"
            )
            print(f"\n{Color.BOLD}Lien de configuration:{Color.RESET}")
            print(link)

def prompt_protocols():
    print_section("Choix des protocoles")
    print("Protocoles disponibles : vless, vmess, trojan, shadowsocks")
    print("Exemple : vless, vmess")
    selected = input("Entrez les protocoles souhaités (séparés par des virgules) : ").strip().lower()
    valid = {"vless", "vmess", "trojan", "shadowsocks"}
    selected = [p.strip() for p in selected.split(",") if p.strip() in valid]
    if not selected:
        print_error("Aucun protocole valide sélectionné.")
        sys.exit(1)
    return selected

def prompt_transports():
    print_section("Choix des transports")
    print("Transports disponibles : ws, tcp, grpc, h2, quic")
    print("Exemple : ws, grpc")
    selected = input("Entrez les transports souhaités (séparés par des virgules) : ").strip().lower()
    valid = {"ws", "tcp", "grpc", "h2", "quic"}
    selected = [t.strip() for t in selected.split(",") if t.strip() in valid]
    if not selected:
        print_error("Aucun transport valide sélectionné.")
        sys.exit(1)
    return selected

def restart_xray_service():
    print_section("Redémarrage du service Xray")
    run_command("systemctl restart xray")
    run_command("systemctl enable xray")

def test_connectivity(domains):
    print_section("Test de connectivité")
    for domain in domains:
        print_info(f"Test de ping sur {domain} ...")
        result = subprocess.run(["ping", "-c", "2", domain], stdout=subprocess.DEVNULL)
        if result.returncode != 0:
            print_error(f"Échec du ping vers {domain}")
        else:
            print_info(f"Ping réussi pour {domain}")
        
        print_info(f"Test de port 443 sur {domain} ...")
        try:
            with socket.create_connection((domain, 443), timeout=5):
                print_info(f"Port 443 ouvert sur {domain}")
        except Exception:
            print_error(f"Port 443 fermé ou inaccessible sur {domain}")

def validate_domain(domain):
    return re.match(r"^(?!\-)([a-zA-Z0-9\-]{1,63}(?<!\-)\.)+[a-zA-Z]{2,}$", domain)

def validate_email(email):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email)

def get_user_inputs():
    print_section("Configuration utilisateur")
    domains = []
    while True:
        domain = input("Entrez un nom de domaine (laisser vide pour terminer): ").strip()
        if not domain:
            break
        if validate_domain(domain):
            domains.append(domain)
        else:
            print_error("Domaine invalide.")
    
    if not domains:
        print_error("Aucun domaine valide fourni.")
        sys.exit(1)

    while True:
        email = input("Entrez votre adresse email (pour Let's Encrypt): ").strip()
        if validate_email(email):
            break
        print_error("Email invalide.")

    protocols = prompt_protocols()
    transports = prompt_transports()

    return domains, email, protocols, transports

def main():
    print_section("INSTALLATEUR XRAY - VERSION INTERACTIVE")

    # Vérification des privilèges
    if os.geteuid() != 0:
        print_error("Ce script doit être exécuté en tant que root!")
        sys.exit(1)

    # Collecte des entrées utilisateur
    domains, email, selected_protocols, selected_transports = get_user_inputs()

    # Mise à jour des variables globales
    global DOMAINS, EMAIL, SELECTED_PROTOCOLS, SELECTED_TRANSPORTS
    DOMAINS = domains
    EMAIL = email
    SELECTED_PROTOCOLS = selected_protocols
    SELECTED_TRANSPORTS = selected_transports

    # Étapes d'installation
    install_dependencies()
    install_xray()
    setup_ssl_certificates()
    client_configs = generate_xray_config()
    restart_xray_service()
    show_client_configs(client_configs)
    test_connectivity(domains)

    print_section("Installation terminée avec succès!")
    
if __name__ == "__main__":
    main()
