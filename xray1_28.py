#!/usr/bin/env python3
import os
import sys
import json
import uuid
import random
import string
import subprocess
import socket
from datetime import datetime
from typing import List, Dict, Any

# Configuration des couleurs
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

# Variables globales
CONFIG_FILE = "/etc/v2ray/config.json"
LOG_FILE = "/var/log/v2ray_install.log"
PROTOCOLS = ["VMess", "VLESS", "Trojan", "Shadowsocks"]
TRANSPORTS = ["tcp", "ws", "grpc", "h2"]
TLS_MODES = ["tls", "none", "reality"]

class V2RayInstaller:
    def __init__(self):
        self.os_info = {}
        self.arch = ""
        self.protocol = ""
        self.port = 443
        self.uuid_or_password = ""
        self.transport = ""
        self.tls_mode = ""

    def log(self, message: str) -> None:
        """Journalisation des actions"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")

    def init_log(self) -> None:
        """Initialisation du journal d'installation"""
        with open(LOG_FILE, 'w') as f:
            f.write("=== Journal d'installation V2Ray ===\n")
            f.write(f"Début: {datetime.now()}\n")
            f.write(f"User: {os.getenv('USER')}\n")
            f.write(f"Host: {socket.gethostname()}\n")
        self.log("Initialisation du journal de installation")

    def check_root(self) -> None:
        """Vérification des privilèges root"""
        if os.geteuid() != 0:
            print(f"{Colors.RED}Erreur: Ce script doit être exécuté en tant que root!{Colors.NC}", file=sys.stderr)
            sys.exit(1)
        self.log("Vérification des privilèges root réussie")

    def detect_os(self) -> None:
        """Détection du système d'exploitation"""
        try:
            with open('/etc/os-release') as f:
                lines = f.readlines()
                for line in lines:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        self.os_info[key] = value.strip('"')
        except FileNotFoundError:
            self.os_info['ID'] = 'unknown'
        
        # Détection de l'architecture
        machine = os.uname().machine
        if machine == "x86_64":
            self.arch = "amd64"
        elif machine == "aarch64":
            self.arch = "arm64"
        elif machine.startswith("armv7"):
            self.arch = "arm"
        else:
            self.arch = "unsupported"
        
        self.log(f"Système détecté: {self.os_info.get('ID', 'unknown')} {self.os_info.get('VERSION_ID', 'unknown')} {self.arch}")

    def ensure_v2ray_dir(self):
        """S'assurer que le répertoire /etc/v2ray existe"""
        v2ray_dir = os.path.dirname(CONFIG_FILE)
        if not os.path.exists(v2ray_dir):
            os.makedirs(v2ray_dir, mode=0o755, exist_ok=True)
            self.log(f"Création du répertoire {v2ray_dir}")
    
    def show_menu(self, title: str, options: List[str]) -> None:
        """Afficher un menu"""
        print(f"{Colors.GREEN}=== {title} ==={Colors.NC}")
        for i, option in enumerate(options, 1):
            print(f"{i}. {Colors.YELLOW}{option}{Colors.NC}")

    def select_protocol(self) -> str:
        """Sélection du protocole"""
        self.show_menu("Choix du protocole", PROTOCOLS)
        
        while True:
            try:
                choice = int(input(f"Votre choix [1-{len(PROTOCOLS)}]: "))
                if 1 <= choice <= len(PROTOCOLS):
                    self.protocol = PROTOCOLS[choice-1].lower()
                    print(f"{Colors.GREEN}Protocole sélectionné: {Colors.YELLOW}{self.protocol}{Colors.NC}")
                    return self.protocol
                else:
                    print(f"{Colors.RED}Choix invalide!{Colors.NC}")
            except ValueError:
                print(f"{Colors.RED}Entrez un nombre valide!{Colors.NC}")

    def select_transport(self) -> str:
        """Sélection du transport"""
        self.show_menu("Choix du transport", TRANSPORTS)
        
        while True:
            try:
                choice = int(input(f"Votre choix [1-{len(TRANSPORTS)}]: "))
                if 1 <= choice <= len(TRANSPORTS):
                    self.transport = TRANSPORTS[choice-1].lower()
                    print(f"{Colors.GREEN}Transport sélectionné: {Colors.YELLOW}{self.transport}{Colors.NC}")
                    return self.transport
                else:
                    print(f"{Colors.RED}Choix invalide!{Colors.NC}")
            except ValueError:
                print(f"{Colors.RED}Entrez un nombre valide!{Colors.NC}")

    def select_tls_mode(self) -> str:
        """Sélection du mode TLS"""
        self.show_menu("Choix de la sécurité", TLS_MODES)
        
        while True:
            try:
                choice = int(input(f"Votre choix [1-{len(TLS_MODES)}]: "))
                if 1 <= choice <= len(TLS_MODES):
                    self.tls_mode = TLS_MODES[choice-1].lower()
                    print(f"{Colors.GREEN}Mode sélectionné: {Colors.YELLOW}{self.tls_mode}{Colors.NC}")
                    return self.tls_mode
                else:
                    print(f"{Colors.RED}Choix invalide!{Colors.NC}")
            except ValueError:
                print(f"{Colors.RED}Entrez un nombre valide!{Colors.NC}")

    def generate_uuid(self) -> str:
        """Génération d'UUID"""
        return str(uuid.uuid4()).lower()

    def generate_password(self, length: int = 16) -> str:
        """Génération de mot de passe aléatoire"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def check_port(self, port: int) -> bool:
        """Vérification des ports"""
        if not 1 <= port <= 65535:
            print(f"{Colors.RED}Port invalide! Doit être entre 1 et 65535{Colors.NC}")
            return False
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                if s.connect_ex(('0.0.0.0', port)) == 0:
                    print(f"{Colors.RED}Le port {port} est déjà utilisé!{Colors.NC}")
                    return False
        except Exception as e:
            print(f"{Colors.RED}Erreur lors de la vérification du port: {e}{Colors.NC}")
            return False
        
        return True

    def configure_domain(self):
        """Configuration pour domaine et CDN"""
        print(f"\n{Colors.GREEN}=== Configuration Domaine/CDN ==={Colors.NC}")
        print("1. Pour utiliser avec Cloudflare ou autre CDN:")
        print("   - Activez le proxy (orange cloud)")
        print("   - Configurez le DNS avec:")
        print(f"     Type: A ou CNAME")
        print(f"     Nom: votre.sous-domaine")
        print(f"     Valeur: {subprocess.getoutput('curl -s ifconfig.me')}")
        print("2. Paramètres recommandés:")
        print("   - TLS: activé")
        print("   - Port: 443 (ou 8443, 2096 pour CDN)")
        print("   - WebSocket path: /v2ray (si WS)")
        print("3. Dans Cloudflare:")
        print("   - SSL/TLS: Full (strict)")
        print("   - WebSockets: Activé")
        print("   - Always Use HTTPS: Activé")
    
    def install_dependencies(self) -> None:
        """Installation des dépendances"""
        self.log(f"Installation des dépendances pour {self.os_info.get('ID', 'unknown')}")
        print(f"{Colors.YELLOW}Installation des dépendances système...{Colors.NC}")
        
        try:
            if self.os_info.get('ID') in ['ubuntu', 'debian']:
                subprocess.run(['apt-get', 'update'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(['apt-get', 'install', '-y', 'curl', 'wget', 'sudo', 'jq', 'uuid-runtime', 'net-tools', 'openssl'], 
                              check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif self.os_info.get('ID') in ['centos', 'rhel', 'fedora']:
                subprocess.run(['yum', 'update', '-y'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(['yum', 'install', '-y', 'curl', 'wget', 'sudo', 'jq', 'util-linux', 'net-tools', 'openssl'], 
                              check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                print(f"{Colors.RED}Système d'exploitation non supporté!{Colors.NC}")
                sys.exit(1)
            
            self.log("Dépendances installées avec succès")
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}Échec de l'installation des dépendances!{Colors.NC}")
            self.log(f"Erreur d'installation des dépendances: {e}")
            sys.exit(1)

    def install_v2ray(self) -> None:
        """Installation de V2Ray"""
        self.log("Début de l'installation de V2Ray")
        print(f"{Colors.YELLOW}Téléchargement et installation de V2Ray...{Colors.NC}")
        
        try:
            subprocess.run(['bash', '-c', 'curl -sL https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh | bash'], 
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.log("V2Ray installé avec succès")
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}Échec de l'installation de V2Ray!{Colors.NC}")
            self.log(f"Erreur d'installation de V2Ray: {e}")
            sys.exit(1)

    def generate_vmess_config(self) -> None:
        """Génération de configuration VMess optimisée"""
        config = {
            "inbounds": [{
                "port": self.port,
                "protocol": "vmess",
                "settings": {
                    "clients": [{
                        "id": self.uuid_or_password,
                        "alterId": 0,  # Modern clients use 0
                        "email": f"user@{socket.gethostname()}"
                    }],
                    "disableInsecureEncryption": True  # Sécurité renforcée
                },
                "streamSettings": {
                    "network": self.transport,
                    "security": self.tls_mode,
                    "wsSettings": {
                        "path": "/vmess",
                        "headers": {
                            "Host": ""  # Remplacer par votre domaine
                        }
                    },
                    "tlsSettings": {
                        "serverName": "",  # Remplacer par votre domaine
                        "alpn": ["http/1.1"]
                    }
                },
                "sniffing": {
                    "enabled": True,
                    "destOverride": ["http", "tls"]
                }
            }],
            "outbounds": [{
                "protocol": "freedom",
                "settings": {}
            }]
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
            
    def generate_vless_config(self) -> None:
        """Génération de configuration VLESS avec support CDN"""
        config = {
            "inbounds": [{
                "port": self.port,
                "protocol": "vless",
                "settings": {
                    "clients": [{
                        "id": self.uuid_or_password,
                        "flow": "xtls-rprx-direct" if self.tls_mode == "tls" else ""
                    }],
                    "decryption": "none",
                    "fallbacks": [
                        {
                            "dest": 80,  # Port de fallback pour le déguisement
                            "xver": 1
                        }
                    ]
                },
                "streamSettings": {
                    "network": self.transport,
                    "security": self.tls_mode,
                    "wsSettings": {
                        "path": "/v2ray",
                        "headers": {
                            "Host": ""  # À remplacer par votre domaine
                        }
                    }
                },
                "sniffing": {
                    "enabled": True,
                    "destOverride": ["http", "tls"]
                }
            }],
            "outbounds": [{
                "protocol": "freedom",
                "settings": {}
            }]
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
            
    def generate_trojan_config(self) -> None:
        """Génération de configuration Trojan avec fallback"""
        config = {
            "inbounds": [{
                "port": self.port,
                "protocol": "trojan",
                "settings": {
                    "clients": [{
                        "password": self.uuid_or_password,
                        "email": f"user@{socket.gethostname()}"
                    }],
                    "fallbacks": [
                        {
                            "dest": 80,  # Port de déguisement
                            "xver": 1
                        }
                    ]
                },
                "streamSettings": {
                    "network": self.transport,
                    "security": self.tls_mode,
                    "tlsSettings": {
                        "serverName": "",  # Remplacer par votre domaine
                        "alpn": ["h2", "http/1.1"],
                        "certificates": []
                    },
                    "wsSettings": {
                        "path": "/trojan",
                        "headers": {
                            "Host": ""  # Remplacer par votre domaine
                        }
                    }
                },
                "sniffing": {
                    "enabled": True,
                    "destOverride": ["http", "tls"]
                }
            }],
            "outbounds": [{
                "protocol": "freedom",
                "settings": {}
            }]
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    
    def generate_shadowsocks_config(self) -> None:
        """Génération de configuration Shadowsocks moderne"""
        config = {
            "inbounds": [{
                "port": self.port,
                "protocol": "shadowsocks",
                "settings": {
                    "method": "chacha20-ietf-poly1305",  # Méthode recommandée
                    "password": self.uuid_or_password,
                    "network": self.transport,
                    "level": 0,
                    "email": f"user@{socket.gethostname()}"
                },
                "streamSettings": {
                    "security": self.tls_mode,
                    "tlsSettings": {
                        "serverName": "",  # Remplacer par votre domaine
                        "alpn": ["http/1.1"]
                    }
                },
                "sniffing": {
                    "enabled": True,
                    "destOverride": ["http", "tls"]
                }
            }],
            "outbounds": [{
                "protocol": "freedom",
                "settings": {}
            }]
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    
    def configure_v2ray(self) -> None:
        """Configuration de V2Ray"""
        self.log(f"Configuration de V2Ray avec {self.protocol} sur le port {self.port} via {self.transport} (TLS: {self.tls_mode})")
        
        self.ensure_v2ray_dir()  # <-- Ajoutez cette ligne
        
        if self.protocol == "vmess":
            self.generate_vmess_config()
        elif self.protocol == "vless":
            self.generate_vless_config()
        elif self.protocol == "trojan":
            self.generate_trojan_config()
        elif self.protocol == "shadowsocks":
            self.generate_shadowsocks_config()
        else:
            print(f"{Colors.RED}Erreur critique : Protocole '{self.protocol}' non implémenté.{Colors.NC}")
            sys.exit(1)

    def complete_installation(self) -> None:
        """Installation complète de V2Ray"""
        print(f"{Colors.GREEN}=== Installation de V2Ray ==={Colors.NC}")
        
        # 1. Sélection du protocole
        self.protocol = self.select_protocol()
        
        # 2. Sélection du port
        while True:
            try:
                port_input = input(f"Port à utiliser [défaut: 443]: ") or "443"
                self.port = int(port_input)
                if self.check_port(self.port):
                    break
            except ValueError:
                print(f"{Colors.RED}Port invalide!{Colors.NC}")
        
        # 3. Génération des identifiants
        if self.protocol == "trojan":
            self.uuid_or_password = self.generate_password()
            print(f"{Colors.GREEN}Mot de passe généré: {Colors.YELLOW}{self.uuid_or_password}{Colors.NC}")
        else:
            self.uuid_or_password = self.generate_uuid()
            print(f"{Colors.GREEN}UUID généré: {Colors.YELLOW}{self.uuid_or_password}{Colors.NC}")
        
        # 4. Sélection du transport
        self.transport = self.select_transport()
        
        # 5. Sélection du mode TLS
        self.tls_mode = self.select_tls_mode()
        
        # Récapitulatif final
        print(f"{Colors.GREEN}=== Configuration finale ==={Colors.NC}")
        print(f"• Protocole: {Colors.YELLOW}{self.protocol}{Colors.NC}")
        print(f"• Port: {Colors.YELLOW}{self.port}{Colors.NC}")
        print(f"• Identifiant: {Colors.YELLOW}{self.uuid_or_password}{Colors.NC}")
        print(f"• Transport: {Colors.YELLOW}{self.transport}{Colors.NC}")
        print(f"• Sécurité: {Colors.YELLOW}{self.tls_mode}{Colors.NC}")
        print()
        
        confirm = input("Confirmer l'installation (o/N)? ").lower()
        if confirm != 'o':
            print(f"{Colors.RED}Installation annulée.{Colors.NC}")
            sys.exit(1)
        
        # Installation
        print(f"{Colors.YELLOW}Installation en cours...{Colors.NC}")
        self.install_dependencies()
        self.install_v2ray()
        self.configure_v2ray()
        
        # Affichage des résultats
        print(f"\n{Colors.GREEN}=== Installation réussie ==={Colors.NC}")
        print(f"Fichier de configuration: {Colors.YELLOW}{CONFIG_FILE}{Colors.NC}")
        
        # Obtenir l'adresse IP publique ou le domaine
        try:
            public_ip = subprocess.getoutput('curl -s ifconfig.me')
        except:
            public_ip = "VOTRE_DOMAINE_OU_IP"
        
        # Afficher la configuration formatée pour les clients
        print(f"\n{Colors.BLUE}=== Configuration pour client V2Ray ==={Colors.NC}")
        print(f"{Colors.YELLOW}Remplacez 'VOTRE_DOMAINE_OU_IP' par votre domaine ou IP réelle{Colors.NC}\n")
        
        if self.protocol == "vless":
            print(f"vless://{self.uuid_or_password}@{public_ip}:{self.port}?type={self.transport}&security={self.tls_mode}&flow=xtls-rprx-direct#{self.protocol}-{self.transport}")
        elif self.protocol == "vmess":
            vmess_config = {
                "v": "2",
                "ps": f"V2Ray-{self.protocol}-{self.transport}",
                "add": public_ip,
                "port": str(self.port),
                "id": self.uuid_or_password,
                "aid": "64",
                "net": self.transport,
                "type": "none",
                "tls": self.tls_mode if self.tls_mode != "none" else ""
            }
            print(f"vmess://{base64.b64encode(json.dumps(vmess_config).encode()).decode()}")
        elif self.protocol == "trojan":
            print(f"trojan://{self.uuid_or_password}@{public_ip}:{self.port}?security={self.tls_mode}&type={self.transport}#Trojan-{self.transport}")
        
        print(f"\n{Colors.BLUE}=== Paramètres détaillés ==={Colors.NC}")
        print(f"Protocole: {self.protocol.upper()}")
        print(f"Adresse: {public_ip} (remplacez par votre domaine si configuré)")
        print(f"Port: {self.port}")
        print(f"ID/Mot de passe: {self.uuid_or_password}")
        print(f"Transport: {self.transport}")
        print(f"Sécurité: {self.tls_mode}")
        if self.protocol == "vless":
            print("Flow: xtls-rprx-direct (pour VLESS+XTLS)")
        
        # Ajouter des notes pour Cloudflare
        print(f"\n{Colors.BLUE}=== Configuration Cloudflare/CDN ==={Colors.NC}")
        print("1. Configurez votre domaine dans Cloudflare avec proxy activé (icône orange)")
        print("2. Utilisez ces paramètres:")
        print(f"   - Type: {self.transport.upper()}")
        print(f"   - Port: 443 (ou votre port TLS)")
        print("3. Désactivez les options de chiffrement dans Cloudflare si vous utilisez TLS")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def update_v2ray(self) -> None:
        """Mise à jour de V2Ray"""
        self.log("Début de la mise à jour de V2Ray")
        print(f"{Colors.YELLOW}Mise à jour de V2Ray...{Colors.NC}")
        
        try:
            subprocess.run(['bash', '-c', 'curl -sL https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh | bash'], 
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(['systemctl', 'restart', 'v2ray'], check=True)
            print(f"{Colors.GREEN}Mise à jour terminée avec succès!{Colors.NC}")
            self.log("Mise à jour de V2Ray terminée")
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}Échec de la mise à jour de V2Ray!{Colors.NC}")
            self.log(f"Erreur de mise à jour de V2Ray: {e}")

    def uninstall_v2ray(self) -> None:
        """Désinstallation de V2Ray"""
        self.log("Début de la désinstallation de V2Ray")
        print(f"{Colors.RED}Attention: Cette action va supprimer complètement V2Ray!{Colors.NC}")
        confirm = input("Êtes-vous sûr de vouloir continuer? [o/N]: ").lower()
        
        if confirm == 'o':
            try:
                subprocess.run(['bash', '-c', 'curl -sL https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh --remove | bash'], 
                              check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(['rm', '-rf', '/etc/v2ray', '/var/log/v2ray', '/usr/local/bin/v2ray', '/usr/local/share/v2ray'], check=True)
                print(f"{Colors.GREEN}V2Ray a été complètement désinstallé!{Colors.NC}")
                self.log("V2Ray désinstallé avec succès")
            except subprocess.CalledProcessError as e:
                print(f"{Colors.RED}Échec de la désinstallation de V2Ray!{Colors.NC}")
                self.log(f"Erreur de désinstallation de V2Ray: {e}")
        else:
            print(f"{Colors.YELLOW}Désinstallation annulée.{Colors.NC}")
            self.log("Désinstallation annulée par l'utilisateur")

    def service_status(self) -> None:
        """Affichage du statut du service"""
        print(f"{Colors.GREEN}=== Statut du service V2Ray ==={Colors.NC}")
        subprocess.run(['systemctl', 'status', 'v2ray', '--no-pager'])

    def show_client_config(self):
        """Affiche la configuration client optimisée"""
        public_ip = self.get_public_ip()
        
        print(f"\n{Colors.BLUE}=== Configuration Client ({self.protocol.upper()}) ==={Colors.NC}")
        
        if self.protocol == "vless":
            print(f"vless://{self.uuid_or_password}@{public_ip}:{self.port}?type={self.transport}&security={self.tls_mode}&flow=xtls-rprx-direct#{self.protocol}-{self.transport}")
        elif self.protocol == "vmess":
            vmess_config = {
                "v": "2",
                "ps": f"V2Ray-{socket.gethostname()}",
                "add": public_ip,
                "port": str(self.port),
                "id": self.uuid_or_password,
                "aid": "0",
                "net": self.transport,
                "type": "none",
                "host": "",
                "path": "/vmess",
                "tls": "tls" if self.tls_mode == "tls" else ""
            }
            print(f"vmess://{base64.b64encode(json.dumps(vmess_config).encode()).decode()}")
        elif self.protocol == "trojan":
            print(f"trojan://{self.uuid_or_password}@{public_ip}:{self.port}?security={self.tls_mode}&type={self.transport}&path=/trojan#{self.protocol}-{self.transport}")
        elif self.protocol == "shadowsocks":
            print(f"ss://{base64.b64encode(f'chacha20-ietf-poly1305:{self.uuid_or_password}'.encode()).decode()}@{public_ip}:{self.port}#{self.protocol}-{self.transport}")
        
        print(f"\n{Colors.YELLOW}Paramètres avancés:{Colors.NC}")
        print(f"Protocole: {self.protocol.upper()}")
        print(f"Adresse: {public_ip} (ou votre domaine)")
        print(f"Port: {self.port}")
        print(f"ID/Mot de passe: {self.uuid_or_password}")
        print(f"Transport: {self.transport}")
        print(f"Sécurité: {self.tls_mode}")
        
        if self.protocol in ["vless", "trojan"]:
            print("Path: /" + self.protocol)
        
        self.show_cdn_instructions()
    
    def show_cdn_instructions(self):
        """Affiche les instructions CDN communes"""
        print(f"\n{Colors.GREEN}=== Configuration CDN (Cloudflare) ==={Colors.NC}")
        print("1. Dans les paramètres DNS:")
        print("   - Type: A ou CNAME")
        print("   - Nom: votre.sous-domaine")
        print("   - Valeur: Votre IP ou domaine racine")
        print("   - Proxy: Activé (icône orange)")
        print("2. Paramètres recommandés:")
        print(f"   - Port: {self.port} (TCP)")
        print(f"   - Type de proxy: {self.transport.upper()}")
        print("3. Dans SSL/TLS:")
        print("   - Mode: Full (strict)")
        print("   - TLS 1.3: Activé")
        print("4. Dans Network:")
        print("   - WebSockets: Activé")
    
    def main_menu(self) -> None:
        """Menu principal"""
        while True:
            print(f"{Colors.GREEN}=== Menu Principal V2Ray Premium ==={Colors.NC}")
            print("1. Installation complète")
            print("2. Mise à jour de V2Ray")
            print("3. Désinstaller V2Ray")
            print("4. Gérer les configurations")
            print("5. Voir le statut du service")
            print("6. Quitter")
            
            choice = input("Choisissez une option [1-6]: ")
            
            if choice == '1':
                self.complete_installation()
            elif choice == '2':
                self.update_v2ray()
            elif choice == '3':
                self.uninstall_v2ray()
            elif choice == '4':
                self.manage_configurations()
            elif choice == '5':
                self.service_status()
            elif choice == '6':
                sys.exit(0)
            else:
                print(f"{Colors.RED}Option invalide!{Colors.NC}")
            
            input("Appuyez sur Entrée pour continuer...")

    def manage_configurations(self) -> None:
        """Gestion des configurations"""
        print(f"{Colors.GREEN}=== Gestion des configurations ==={Colors.NC}")
        print("1. Afficher la configuration actuelle")
        print("2. Sauvegarder la configuration")
        print("3. Restaurer une configuration")
        print("4. Modifier la configuration manuellement")
        print("5. Retour")
        
        choice = input("Choisissez une option [1-5]: ")
        
        if choice == '1':
            self.show_config()
        elif choice == '2':
            self.backup_config()
        elif choice == '3':
            self.restore_config()
        elif choice == '4':
            self.edit_config()
        elif choice == '5':
            return
        else:
            print(f"{Colors.RED}Option invalide!{Colors.NC}")

    def show_config(self) -> None:
        """Afficher la configuration actuelle"""
        try:
            with open(CONFIG_FILE) as f:
                config = json.load(f)
                print(json.dumps(config, indent=2))
        except Exception as e:
            print(f"{Colors.RED}Erreur lors de la lecture du fichier de configuration: {e}{Colors.NC}")

    def backup_config(self) -> None:
        """Sauvegarder la configuration"""
        backup_file = f"{CONFIG_FILE}.bak"
        try:
            subprocess.run(['cp', CONFIG_FILE, backup_file], check=True)
            print(f"{Colors.GREEN}Configuration sauvegardée dans {backup_file}{Colors.NC}")
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}Échec de la sauvegarde de la configuration: {e}{Colors.NC}")

    def restore_config(self) -> None:
        """Restaurer une configuration"""
        backup_file = f"{CONFIG_FILE}.bak"
        if not os.path.exists(backup_file):
            print(f"{Colors.RED}Aucune sauvegarde trouvée!{Colors.NC}")
            return
        
        try:
            subprocess.run(['cp', backup_file, CONFIG_FILE], check=True)
            subprocess.run(['systemctl', 'restart', 'v2ray'], check=True)
            print(f"{Colors.GREEN}Configuration restaurée depuis {backup_file}{Colors.NC}")
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}Échec de la restauration de la configuration: {e}{Colors.NC}")

    def edit_config(self) -> None:
        """Modifier la configuration manuellement"""
        editor = os.getenv('EDITOR', 'nano')
        try:
            subprocess.run([editor, CONFIG_FILE], check=True)
            subprocess.run(['systemctl', 'restart', 'v2ray'], check=True)
            print(f"{Colors.GREEN}Configuration modifiée avec succès{Colors.NC}")
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}Échec de la modification de la configuration: {e}{Colors.NC}")

    def main(self) -> None:
        """Point d'entrée principal"""
        self.check_root()
        self.init_log()
        self.detect_os()
        self.main_menu()

if __name__ == "__main__":
    installer = V2RayInstaller()
    installer.main()