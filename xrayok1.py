#!/data/data/com.termux/files/usr/bin/python3
import os
import sys
import json
import uuid
import random
import string
import subprocess
import logging
from typing import List, Dict, Optional, Tuple
import urllib.request
import urllib.error
import base64
import shutil
import socket
import time
import importlib.util

# Configuration des couleurs
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

# Configuration globale
HOME_DIR = os.path.expanduser("~")
CONFIG_DIR = os.path.join(HOME_DIR, ".xray")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
LOG_FILE = os.path.join(HOME_DIR, "xray-install.log")
SSH_DIR = os.path.join(HOME_DIR, ".ssh")
SSH_CONFIG = os.path.join(SSH_DIR, "config")
SSH_KEY = os.path.join(SSH_DIR, "xray_vps_key")

# Dépendances
TERMUX_PACKAGES = [
    "curl", "wget", "jq", "openssl-tool", 
    "python", "git", "proot", "openssh", 
    "unzip"
]

PYTHON_PACKAGES = [
    "requests", "pyopenssl", "urllib3", 
    "cryptography"
]

# Options de configuration
PROTOCOLS = ["VMess", "VLESS", "Trojan", "Shadowsocks"]
TRANSPORTS = ["tcp", "ws", "grpc", "h2", "quic"]
TLS_MODES = ["tls", "none", "reality"]
CDN_PROVIDERS = ["Cloudflare", "AWS CloudFront", "Google Cloud CDN", "Autre"]

def init_logging():
    """Initialise le système de logging"""
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='[%(asctime)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.info("=== Journal d'installation Xray ===")
    logging.info(f"Début: {time.strftime('%Y-%m-%d %H:%M:%S')}")

def log(message: str):
    """Journalise un message"""
    logging.info(message)
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def print_color(message: str, color: str):
    """Affiche un message coloré"""
    print(f"{color}{message}{Colors.NC}")

def check_termux():
    """Vérifie l'environnement Termux"""
    if not os.path.exists("/data/data/com.termux/files/usr"):
        print_color("Ce script nécessite Termux", Colors.RED)
        sys.exit(1)

def install_dependencies():
    """Installe toutes les dépendances"""
    print_color("\n=== Installation des dépendances ===", Colors.BLUE)
    
    # Packages Termux
    run_command("pkg update -y && pkg upgrade -y")
    run_command(f"pkg install -y {' '.join(TERMUX_PACKAGES)}")
    
    # Modules Python
    run_command(f"pip install --upgrade {' '.join(PYTHON_PACKAGES)}")
    
    # Configuration SSH
    os.makedirs(SSH_DIR, exist_ok=True)
    os.chmod(SSH_DIR, 0o700)

def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Exécute une commande shell"""
    log(f"Exécution: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        log(f"Échec: {cmd}")
        log(f"Erreur: {e.stderr}")
        if check:
            print_color(f"Échec: {e.stderr}", Colors.RED)
            sys.exit(1)
        return e

def setup_ssh_connection():
    """Version améliorée avec vérifications supplémentaires"""
    print_color("\n=== Configuration SSH ===", Colors.BLUE)
    
    vps_ip = input("IP du VPS: ").strip()
    vps_user = input("Utilisateur [root]: ").strip() or "root"
    ssh_port = input("Port SSH [22]: ").strip() or "22"
    
    # Vérification de la connectivité
    print_color("\nVérification de la connectivité...", Colors.YELLOW)
    ping_result = run_command(f"ping -c 4 {vps_ip}", check=False)
    if ping_result.returncode != 0:
        print_color("Échec: Le serveur ne répond pas aux pings", Colors.RED)
        return False
    
    # Vérification du port SSH
    nc_result = run_command(f"nc -zv {vps_ip} {ssh_port}", check=False)
    if nc_result.returncode != 0:
        print_color(f"Échec: Le port {ssh_port} n'est pas accessible", Colors.RED)
        return False
    
    # Génération des clés SSH
    if not os.path.exists(SSH_KEY):
        run_command(f"ssh-keygen -t ed25519 -f {SSH_KEY} -N ''")
    
    # Configuration SSH
    with open(SSH_CONFIG, "w") as f:
        f.write(f"Host xray-vps\n")
        f.write(f"    HostName {vps_ip}\n")
        f.write(f"    User {vps_user}\n")
        f.write(f"    Port {ssh_port}\n")
        f.write(f"    IdentityFile {SSH_KEY}\n")
        f.write(f"    StrictHostKeyChecking no\n")
    
    print_color("\n1. Copiez MANUELLEMENT cette clé sur votre VPS:", Colors.YELLOW)
    print_color("   Ouvrez ~/.ssh/xray_vps_key.pub et copiez son contenu", Colors.CYAN)
    print_color("   Collez-le dans ~/.ssh/authorized_keys sur votre VPS", Colors.CYAN)
    print_color("2. Assurez-vous que les permissions sont correctes:", Colors.YELLOW)
    print_color("   chmod 700 ~/.ssh", Colors.CYAN)
    print_color("   chmod 600 ~/.ssh/authorized_keys", Colors.CYAN)
    
    input("Appuyez sur Entrée après avoir effectué ces étapes...")
    return True

def deploy_to_vps():
    """Version améliorée avec meilleure gestion des erreurs"""
    if not setup_ssh_connection():
        return
    
    print_color("\nTest de connexion SSH...", Colors.YELLOW)
    test_cmd = f"ssh -i {SSH_KEY} root@66.103.210.231 'echo \"Test de connexion réussi\"'"
    result = run_command(test_cmd, check=False)
    
    if result.returncode != 0:
        print_color("\nÉchec de la connexion SSH. Causes possibles:", Colors.RED)
        print_color("1. La clé publique n'est pas dans authorized_keys", Colors.YELLOW)
        print_color("2. Le serveur SSH n'écoute pas sur le port spécifié", Colors.YELLOW)
        print_color("3. Le firewall bloque la connexion", Colors.YELLOW)
        print_color("4. L'utilisateur n'a pas les permissions adéquates", Colors.YELLOW)
        
        # Tentative de diagnostic
        print_color("\nTentative de connexion en mode verbeux...", Colors.BLUE)
        run_command(f"ssh -vvv -i {SSH_KEY} root@66.103.210.231", check=False)
        return
        
def generate_config(protocol: str, port: int, id: str, transport: str, tls_mode: str, domain: str = ""):
    """Génère la configuration Xray"""
    config = {
        "inbounds": [{
            "port": port,
            "protocol": protocol.lower(),
            "settings": {
                "clients": [{"id": id}] if protocol != "Shadowsocks" else {"password": id}
            },
            "streamSettings": {
                "network": transport,
                "security": tls_mode
            }
        }],
        "outbounds": [{"protocol": "freedom"}]
    }
    
    if tls_mode == "tls" and domain:
        config["inbounds"][0]["streamSettings"]["tlsSettings"] = {
            "serverName": domain,
            "certificates": [{
                "certificateFile": f"/etc/letsencrypt/live/{domain}/fullchain.pem",
                "keyFile": f"/etc/letsencrypt/live/{domain}/privkey.pem"
            }]
        }
    
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    
    print_color(f"Configuration générée: {CONFIG_FILE}", Colors.GREEN)

def configure_for_vps():
    """Génère une configuration pour VPS"""
    print_color("\n=== Configuration VPS ===", Colors.GREEN)
    
    # Sélection des options
    show_menu("Protocole", PROTOCOLS)
    protocol = select_from_menu(PROTOCOLS, "Choix: ")
    
    port = int(input("Port [443]: ") or 443)
    id = generate_id(protocol)
    
    show_menu("Transport", TRANSPORTS)
    transport = select_from_menu(TRANSPORTS, "Choix: ")
    
    show_menu("Sécurité", TLS_MODES)
    tls_mode = select_from_menu(TLS_MODES, "Choix: ")
    
    domain = ""
    if tls_mode != "none":
        domain = input("Domaine (pour TLS): ").strip()
        show_menu("CDN", CDN_PROVIDERS)
        cdn = select_from_menu(CDN_PROVIDERS, "Choix CDN: ")
        if cdn == "cloudflare":
            configure_cloudflare(domain)
    
    generate_config(protocol, port, id, transport, tls_mode, domain)

def manage_vps():
    """Gère le service Xray sur le VPS"""
    print_color("\n=== Gestion du VPS ===", Colors.BLUE)
    
    print("1. Démarrer Xray")
    print("2. Arrêter Xray")
    print("3. Redémarrer Xray")
    print("4. Voir le statut")
    print("5. Voir les logs")
    print("6. Retour")
    
    choice = input("Choix: ").strip()
    
    commands = {
        "1": "systemctl start xray",
        "2": "systemctl stop xray",
        "3": "systemctl restart xray",
        "4": "systemctl status xray --no-pager",
        "5": "journalctl -u xray -n 30 --no-pager"
    }
    
    if choice in commands:
        result = run_command(f"ssh xray-vps '{commands[choice]}'", check=False)
        print(result.stdout)
    elif choice != "6":
        print_color("Choix invalide", Colors.RED)

def show_menu(title: str, options: List[str]):
    """Affiche un menu interactif"""
    print_color(f"\n=== {title} ===", Colors.GREEN)
    for i, option in enumerate(options, 1):
        print_color(f"{i}. {option}", Colors.YELLOW)
    print()

def select_from_menu(options: List[str], prompt: str) -> str:
    """Sélection depuis un menu"""
    while True:
        try:
            choice = int(input(prompt).strip())
            if 1 <= choice <= len(options):
                return options[choice-1].lower()
        except ValueError:
            pass
        print_color("Choix invalide!", Colors.RED)

def generate_id(protocol: str) -> str:
    """Génère un ID selon le protocole"""
    if protocol.lower() in ("trojan", "shadowsocks"):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    return str(uuid.uuid4())

def configure_cloudflare(domain: str):
    """Configure Cloudflare pour le domaine"""
    print_color("\n=== Configuration Cloudflare ===", Colors.YELLOW)
    print("1. Allez sur: https://dash.cloudflare.com/profile/api-tokens")
    print("2. Créez un token avec les permissions:")
    print("   - Zone.DNS (Edit)")
    print("   - Zone.Zone (Read)")
    
    api_token = input("Token API: ").strip()
    email = input("Email Cloudflare: ").strip()
    
    # Sauvegarde sécurisée
    os.makedirs(f"{HOME_DIR}/.secrets", exist_ok=True)
    with open(f"{HOME_DIR}/.secrets/cloudflare.ini", "w") as f:
        f.write(f"dns_cloudflare_api_token = {api_token}")
    os.chmod(f"{HOME_DIR}/.secrets/cloudflare.ini", 0o600)
    
    print_color("Configuration Cloudflare sauvegardée!", Colors.GREEN)

def main_menu():
    """Menu principal"""
    while True:
        print_color("\n=== Xray Manager ===", Colors.GREEN)
        print("1. Configurer pour VPS")
        print("2. Déployer sur VPS")
        print("3. Gérer le VPS")
        print("4. Quitter")
        
        choice = input("Choix: ").strip()
        
        if choice == "1":
            configure_for_vps()
        elif choice == "2":
            deploy_to_vps()
        elif choice == "3":
            manage_vps()
        elif choice == "4":
            sys.exit(0)

if __name__ == "__main__":
    try:
        check_termux()
        init_logging()
        install_dependencies()
        main_menu()
    except KeyboardInterrupt:
        print_color("\nOpération annulée", Colors.RED)
        sys.exit(1)