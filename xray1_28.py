#!/usr/bin/env python3
import os
import sys
import json
import base64
from typing import Dict, Any
import uuid
import random
import string
import subprocess
import socket
import inspect  # Ajoutez cette ligne
from datetime import datetime
from typing import List, Dict, Any

# Configuration des couleurs
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color
    CYAN = '\033[0;36m'  # Ajoutez cette ligne

# Variables globales
CONFIG_FILE = "/etc/v2ray/config.json"
LOG_FILE = "/var/log/v2ray_install.log"
PROTOCOLS = ["VMess", "VLESS", "Trojan", "Shadowsocks"]
TRANSPORTS = ["tcp", "ws", "grpc", "h2"]
TLS_MODES = ["tls", "none", "reality"]

class CloudflareManager:
    def __init__(self):
        self.api_key = ""
        self.email = ""
        self.zone_id = ""
        self.domain = ""

    def test_connection(self) -> bool:
        """Vérifie les credentials API"""
        headers = {
            "X-Auth-Email": self.email,
            "X-Auth-Key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            response = requests.get(
                "https://api.cloudflare.com/client/v4/user/tokens/verify",
                headers=headers
            )
            return response.status_code == 200
        except:
            return False

    def configure_dns(self) -> bool:
        """Configure les enregistrements DNS"""
        # Implémentation de la configuration DNS via API
        pass

    def setup_ssl(self) -> bool:
        """Configure les certificats SSL"""
        # Implémentation de la configuration SSL
        pass

    def configure_firewall_rules(self) -> bool:
        """Configure les règles de firewall et cache"""
        # Implémentation des règles
        pass

    def configure_cloudflare(self):
        """Configuration automatique via API Cloudflare"""
        print(f"\n{Colors.GREEN}=== Configuration Cloudflare API ==={Colors.NC}")
        
        # Récupération des credentials
        self.email = input("Email du compte Cloudflare: ")
        self.api_key = input("Clé API Global Cloudflare: ")
        self.domain = input("Domaine complet (ex: mon-domaine.com): ")
        
        # Récupération de la Zone ID
        try:
            headers = {
                "X-Auth-Email": self.email,
                "X-Auth-Key": self.api_key,
                "Content-Type": "application/json"
            }
            response = requests.get(
                f"https://api.cloudflare.com/client/v4/zones?name={self.domain}",
                headers=headers
            )
            self.zone_id = response.json()["result"][0]["id"]
        except Exception as e:
            print(f"{Colors.RED}Erreur API Cloudflare: {e}{Colors.NC}")
            return False
        
        return True

    def get_ssl_certificates(self):
        """Récupération des certificats via API Cloudflare"""
        try:
            headers = {
                "X-Auth-Email": self.email,
                "X-Auth-Key": self.api_key,
                "Content-Type": "application/json"
            }
            response = requests.get(
                f"https://api.cloudflare.com/client/v4/zones/{self.zone_id}/ssl/certificate_packs",
                headers=headers
            )
            return response.json()["result"][0]
        except Exception as e:
            print(f"{Colors.RED}Erreur récupération certificats: {e}{Colors.NC}")
            return None

class V2RayInstaller:
    def __init__(self):
        self.os_info = {}
        self.arch = ""
        self.protocol = ""
        self.port = 443
        self.uuid_or_password = ""
        self.transport = ""
        self.tls_mode = ""
        self.cf_manager = CloudflareManager()  # Ajoutez cette ligne

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

    def _validate_config(self, config):
        """Validation approfondie de la configuration"""
        if not config.get("inbounds"):
            raise ValueError("Aucune configuration inbound")
    
        for inbound in config["inbounds"]:
            if inbound["protocol"] == "vless" and not inbound["settings"].get("clients"):
                raise ValueError("VLESS nécessite des clients configurés")
    
    def generate_uuid(self):
        """Génère un UUID sécurisé pour les clients"""
        import uuid
        return str(uuid.uuid4())

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

    def verify_dns(self, domain: str) -> bool:
        """Vérification basique DNS"""
        try:
            import socket
            server_ip = subprocess.getoutput('curl -s ifconfig.me')
            resolved_ip = socket.gethostbyname(domain)
            return resolved_ip == server_ip
        except:
            return False
    
    def generate_self_signed_cert(self):
        """Génère un certificat auto-signé"""
        cert_dir = "/etc/v2ray/ssl"
        os.makedirs(cert_dir, exist_ok=True)
        
        subprocess.run([
            "openssl", "req", "-new", "-x509", "-nodes",
            "-days", "365", "-newkey", "rsa:2048",
            "-keyout", f"{cert_dir}/self.key",
            "-out", f"{cert_dir}/self.crt",
            "-subj", "/CN=localhost"
        ], check=True)
    
    def configure_tls(self, domain: str) -> None:
        """Configure les certificats TLS pour un domaine"""
        print(f"\n{Colors.YELLOW}Configuration TLS pour le domaine {domain}...{Colors.NC}")
        
        # Chemin des certificats
        cert_dir = "/etc/v2ray/certs"
        cert_file = f"{cert_dir}/{domain}.pem"
        key_file = f"{cert_dir}/{domain}.key"
        
        try:
            # Créer le répertoire si inexistant
            os.makedirs(cert_dir, exist_ok=True)
            
            # Option 1: Certificats existants
            if os.path.exists(cert_file) and os.path.exists(key_file):
                print(f"{Colors.GREEN}Certificats existants trouvés.{Colors.NC}")
                return
            
            # Option 2: Certificats auto-signés (temporaires)
            print(f"{Colors.YELLOW}Génération de certificats auto-signés...{Colors.NC}")
            subprocess.run([
                "openssl", "req", "-new", "-x509", "-nodes",
                "-days", "365", "-newkey", "rsa:2048",
                "-keyout", key_file,
                "-out", cert_file,
                "-subj", f"/CN={domain}"
            ], check=True)
            
            print(f"{Colors.GREEN}Certificats générés dans {cert_dir}{Colors.NC}")
            
        except Exception as e:
            print(f"{Colors.RED}Erreur lors de la configuration TLS: {e}{Colors.NC}")
            sys.exit(1)
        
    def install_dependencies(self):
        """Installation complète des dépendances"""
        deps = {
            'ubuntu': ['curl', 'wget', 'jq', 'uuid-runtime', 'net-tools', 'openssl', 'certbot', 'qrencode'],
            'centos': ['curl', 'wget', 'jq', 'util-linux', 'net-tools', 'openssl', 'certbot', 'qrencode']
        }
        
        print(f"{Colors.YELLOW}Installation des dépendances...{Colors.NC}")
        
        try:
            if self.os_info.get('ID') in ['ubuntu', 'debian']:
                subprocess.run(['apt-get', 'update'], check=True)
                subprocess.run(['apt-get', 'install', '-y'] + deps['ubuntu'], check=True)
            elif self.os_info.get('ID') in ['centos', 'rhel']:
                subprocess.run(['yum', 'install', '-y'] + deps['centos'], check=True)
                subprocess.run(['systemctl', 'enable', 'certbot.timer'], check=True)
            
            print(f"{Colors.GREEN}Dépendances installées avec succès!{Colors.NC}")
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}Échec de l'installation des dépendances: {e}{Colors.NC}")
            sys.exit(1)
            
    def generate_random_path(self) -> str:
        """Génère un chemin aléatoire pour WS/HTTP"""
        segments = [
            "api", "data", "graphql", "rest", 
            "v2ray", "app", "ws", "stream"
        ]
        return f"/{random.choice(segments)}-{random.randint(1000,9999)}/path"
    
    def generate_random_service_name(self) -> str:
        """Génère un nom de service gRPC aléatoire"""
        prefixes = ["api", "data", "sync", "cloud", "grpc"]
        suffixes = ["service", "channel", "gateway", "stream"]
        return f"{random.choice(prefixes)}-{random.choice(suffixes)}-{random.randint(100,999)}"

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

    # À la place des 4 anciennes fonctions, gardez juste :   
    def generate_full_config(self, cloudflare=False):
        """Génère une configuration complète V2Ray avec options avancées
        
        Args:
            cloudflare (bool): Si True, adapte la config pour Cloudflare (ports spécifiques, etc.)
        
        Returns:
            dict: Configuration V2Ray complète avec entrées valides
        """
        # Configuration de base obligatoire
        config = {
            "inbounds": [{
                "port": 443 if not cloudflare else 8443,
                "protocol": "vless",
                "settings": {
                    "clients": [{
                        "id": self.generate_uuid(),
                        "flow": "xtls-rprx-vision"
                    }],
                    "decryption": "none"
                },
                "streamSettings": {
                    "network": "ws",
                    "security": "tls",
                    "tlsSettings": {
                        "certificates": [{
                            "certificateFile": "/path/to/cert.pem",
                            "keyFile": "/path/to/privkey.pem"
                        }],
                        "alpn": ["h2", "http/1.1"],
                        "fingerprint": "chrome"
                    },
                    "wsSettings": {
                        "path": "/your-path",
                        "headers": {
                            "Host": self.domain
                        }
                    }
                }
            }],
            "outbounds": [{
                "protocol": "freedom"
            }]
        }
    
        # Adaptations spécifiques pour Cloudflare
        if cloudflare:
            config["inbounds"][0]["port"] = 8443  # Port recommandé pour Cloudflare
            config["inbounds"][0]["streamSettings"]["tlsSettings"]["serverName"] = self.domain
            config["inbounds"][0]["streamSettings"]["wsSettings"]["headers"]["Host"] = self.domain
    
        # Validation finale
        self._validate_config(config)
        return config
        
    def verify_domain(self, domain: str) -> bool:
        """Vérification complète du domaine"""
        try:
            # Vérification DNS
            ip = socket.gethostbyname(domain)
            server_ip = self.get_public_ip()
            
            # Vérification certificat
            cert_path = f"/etc/letsencrypt/live/{domain}"
            if not os.path.exists(cert_path):
                print(f"{Colors.YELLOW}Certificat Let's Encrypt manquant pour {domain}{Colors.NC}")
                return False
                
            return ip == server_ip
        except Exception as e:
            print(f"{Colors.RED}Erreur de vérification du domaine: {e}{Colors.NC}")
            return False
    
    def get_public_ip(self) -> str:
        """Récupère l'IP publique du serveur avec plusieurs méthodes de fallback"""
        methods = [
            # Méthodes de récupération d'IP avec timeout
            ('curl -s ifconfig.me', 2),
            ('curl -s icanhazip.com', 2),
            ('curl -s ipinfo.io/ip', 2),
            ('curl -s api.ipify.org', 2)
        ]
        
        for cmd, timeout in methods:
            try:
                ip = subprocess.run(
                    cmd.split(),
                    capture_output=True,
                    text=True,
                    timeout=timeout
                ).stdout.strip()
                
                if ip and self._is_valid_ip(ip):
                    return ip
            except:
                continue
        
        return "VOTRE_IP_PUBLIQUE"  # Fallback manuel
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Valide qu'une chaîne est une IPv4 valide"""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) < 256 for part in parts)
        except:
            return False
            
    def configure_v2ray(self, use_cdn: bool = False) -> None:
        """Configuration unifiée de V2Ray avec support CDN avancé"""
        self.log(f"Configuration de V2Ray avec {self.protocol} sur le port {self.port} via {self.transport} (TLS: {self.tls_mode})")
        
        # 1. Préparation de l'environnement
        self.ensure_v2ray_dir()
        self.ensure_ssl_dir()
    
        # 2. Génération de la configuration unifiée
        config = {
            "log": {
                "access": "/var/log/v2ray/access.log",
                "error": "/var/log/v2ray/error.log",
                "loglevel": "warning"
            },
            "inbounds": [self._generate_inbound(use_cdn)],
            "outbounds": [
                {
                    "protocol": "freedom",
                    "tag": "direct"
                },
                {
                    "protocol": "blackhole",
                    "tag": "blocked"
                }
            ],
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "rules": [
                    {
                        "type": "field",
                        "ip": ["geoip:private"],
                        "outboundTag": "blocked"
                    }
                ]
            }
        }
    
        # 3. Sauvegarde de la configuration
        config_path = "/etc/v2ray/config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"{Colors.GREEN}Configuration sauvegardée dans {config_path}{Colors.NC}")
    
    def _generate_inbound(self, use_cdn: bool) -> dict:
        """Génère la configuration inbound unifiée"""
        inbound = {
            "port": self.port,
            "protocol": self.protocol,
            "settings": self._get_protocol_settings(),
            "streamSettings": self._get_stream_settings(use_cdn),
            "sniffing": {
                "enabled": True,
                "destOverride": ["http", "tls"]
            }
        }
    
        # Ajout des fallbacks pour CDN
        if use_cdn:
            inbound["settings"]["fallbacks"] = [
                {
                    "dest": 80,
                    "xver": 1
                },
                {
                    "path": "/cdn-test",
                    "dest": 80,
                    "xver": 1
                }
            ]
        
        return inbound
    
    def _get_protocol_settings(self) -> dict:
        """Retourne les paramètres spécifiques au protocole"""
        common_settings = {
            "clients": [self._get_client_config()],
            "disableInsecureEncryption": True
        }
    
        if self.protocol == "trojan":
            return {
                "clients": [{
                    "password": self.uuid_or_password,
                    "flow": "xtls-rprx-vision" if self.tls_mode == "tls" else ""
                }],
                "fallbacks": [
                    {
                        "dest": 80,
                        "xver": 1
                    }
                ]
            }
        elif self.protocol == "trojan":
            return {
                **common_settings,
                "clients": [{
                    "password": self.uuid_or_password,
                    **common_settings["clients"][0]
                }]
            }
        else:  # vmess/shadowsocks
            return common_settings
    
    def _get_client_config(self) -> dict:
        """Configuration de base du client"""
        return {
            "id": self.uuid_or_password,
            "level": 0,
            "email": f"user@{socket.gethostname()}"
        }

    def _get_stream_settings(self, use_cdn: bool) -> dict:
        """Configuration avancée du transport corrigée"""
        stream_settings = {
            "network": self.transport,
            "security": self.tls_mode,
            "tlsSettings": {
                "serverName": self.domain if use_cdn else "",
                "alpn": ["h2", "http/1.1"],
                "certificates": [self._get_certificate_config(use_cdn)],
                "fingerprint": "chrome"
            } if self.tls_mode == "tls" else None,
        }
    
        # Configuration spécifique au transport
        if self.transport == "ws":
            stream_settings["wsSettings"] = {
                "path": self.generate_random_path(),
                "headers": {
                    "Host": self.domain if use_cdn else ""
                }
            }
        elif self.transport == "grpc":
            stream_settings["grpcSettings"] = {
                "serviceName": self.generate_random_service_name(),
                "multiMode": True
            }
        
        return {k: v for k, v in stream_settings.items() if v is not None}
    
    def generate_random_service_name(self) -> str:
        """Génère un nom de service gRPC discret"""
        prefixes = ["api", "data", "sync", "update", "cloud"]
        suffixes = ["service", "gateway", "stream", "channel"]
        return f"{random.choice(prefixes)}-{random.choice(suffixes)}-{random.randint(1000,9999)}"
            
    def _get_certificate_config(self, use_cdn: bool) -> dict:
        """Gestion robuste des certificats SSL"""
        cert_dir = "/etc/letsencrypt/live" if use_cdn else "/etc/v2ray/ssl"
        
        if use_cdn and os.path.exists(f"{cert_dir}/{self.domain}"):
            return {
                "certificateFile": f"{cert_dir}/{self.domain}/fullchain.pem",
                "keyFile": f"{cert_dir}/{self.domain}/privkey.pem"
            }
        else:
            # Générer un certificat auto-signé si nécessaire
            self.generate_self_signed_cert()
            return {
                "certificateFile": "/etc/v2ray/ssl/self.crt",
                "keyFile": "/etc/v2ray/ssl/self.key"
            }
    
    def ensure_ssl_dir(self):
        """Crée le répertoire SSL si inexistant"""
        ssl_dir = "/etc/v2ray/ssl"
        if not os.path.exists(ssl_dir):
            os.makedirs(ssl_dir, mode=0o755, exist_ok=True)
            self.log(f"Création du répertoire SSL {ssl_dir}")
        
    def _get_certificates(self, use_cdn):
        """Gère les certificats selon le mode CDN"""
        if use_cdn:
            return [{
                "certificateFile": f"/etc/letsencrypt/live/{self.domain}/fullchain.pem",
                "keyFile": f"/etc/letsencrypt/live/{self.domain}/privkey.pem"
            }]
        return []
    
    def ensure_ssl_dir(self):
        """Crée le répertoire SSL si inexistant"""
        ssl_dir = "/etc/v2ray/ssl"
        if not os.path.exists(ssl_dir):
            os.makedirs(ssl_dir, mode=0o755, exist_ok=True)
            self.log(f"Création du répertoire SSL {ssl_dir}")
    
        def configure_cloudflare_integration(self) -> bool:
            """Gère toute la configuration Cloudflare avec gestion des erreurs"""
            try:
                if not hasattr(self, 'cf_manager'):
                    self.cf_manager = CloudflareManager()
                    
                print(f"\n{Colors.BLUE}=== Configuration Cloudflare ==={Colors.NC}")
                
                # Étape 1: Credentials
                self.cf_manager.email = input("Email du compte Cloudflare: ").strip()
                self.cf_manager.api_key = input("Clé API Global Cloudflare: ").strip()
                self.cf_manager.domain = self.domain
                
                # Étape 2: Configuration DNS
                if not self.cf_manager.configure_dns():
                    print(f"{Colors.RED}Échec de la configuration DNS{Colors.NC}")
                    return False
                    
                # Étape 3: Récupération des certificats
                if not self.cf_manager.setup_ssl():
                    print(f"{Colors.YELLOW}Avertissement: Échec de la configuration SSL{Colors.NC}")
                    
                return True
                
            except Exception as e:
                print(f"{Colors.RED}Erreur Cloudflare: {str(e)}{Colors.NC}")
                return False

    def _confirm_installation(self) -> bool:
        """Demande confirmation avant l'installation"""
        print(f"\n{Colors.YELLOW}=== Récapitulatif avant installation ==={Colors.NC}")
        print(f"Protocole: {Colors.CYAN}{self.protocol.upper()}{Colors.NC}")
        print(f"Adresse: {Colors.CYAN}{getattr(self, 'domain', self.get_public_ip())}{Colors.NC}")
        print(f"Port: {Colors.CYAN}{self.port}{Colors.NC}")
        print(f"Transport: {Colors.CYAN}{self.transport.upper()}{Colors.NC}")
        print(f"Sécurité: {Colors.CYAN}{self.tls_mode.upper()}{Colors.NC}")
        
        confirm = input("\nConfirmer l'installation (o/N)? ").strip().lower()
        return confirm == 'o'
        
    def complete_installation(self) -> None:
        """Installation complète avec gestion robuste des cas TLS"""
        print(f"{Colors.GREEN}=== Installation de V2Ray Premium ==={Colors.NC}")
        
        # 1. Sélection du protocole
        self.protocol = self.select_protocol()
        
        # 2. Configuration du domaine
        use_domain = False
        self.domain = ""
        if input("Utiliser un domaine personnalisé ? (o/N): ").lower() == 'o':
            self.domain = input("Entrez votre domaine complet (ex: exemple.com): ").strip()
            if not self.verify_dns(self.domain):
                print(f"{Colors.YELLOW}Avertissement: Le domaine ne pointe pas vers cette IP{Colors.NC}")
            use_domain = True
        
        # 3. Sélection du port avec vérification TLS
        while True:
            try:
                port_input = input(f"Port à utiliser [défaut: 443]: ") or "443"
                self.port = int(port_input)
                
                # Vérification cohérence TLS
                if self.port == 443 and not use_domain:
                    print(f"{Colors.YELLOW}Attention: Le port 443 nécessite généralement un domaine pour TLS{Colors.NC}")
                    if input("Continuer quand même ? (o/N): ").lower() != 'o':
                        continue
                
                if self.check_port(self.port):
                    break
            except ValueError:
                print(f"{Colors.RED}Port invalide!{Colors.NC}")
    
        # 4. Génération des identifiants
        if self.protocol == "trojan":
            self.uuid_or_password = self.generate_password()
        else:
            self.uuid_or_password = self.generate_uuid()
        print(f"{Colors.GREEN}Identifiant généré: {Colors.YELLOW}{self.uuid_or_password}{Colors.NC}")
    
        # 5. Sélection du transport
        self.transport = self.select_transport()
        
        # 6. Configuration TLS intelligente
        if use_domain or self.port == 443:
            print(f"{Colors.BLUE}Configuration TLS recommandée{Colors.NC}")
            self.tls_mode = "tls"
            if not use_domain:
                print(f"{Colors.YELLOW}Utilisation d'un certificat auto-signé (domaine recommandé){Colors.NC}")
        else:
            self.tls_mode = self.select_tls_mode()
        
        # Configuration automatique pour Reality
        if self.tls_mode == "reality":
            self.configure_reality()
            use_domain = True  # Reality nécessite un domaine
        
        # 7. Finalisation
        self._finalize_installation(use_domain)

    def generate_qr_code(self, config):
        """Génère un QR Code de la configuration"""
        try:
            import qrcode
            qr = qrcode.QRCode()
            qr.add_data(json.dumps(config))
            qr.print_ascii()
        except ImportError:
            print(f"{Colors.YELLOW}Installez 'qrcode' pour les QR Codes: pip install qrcode{Colors.NC}")

    def generate_v2ray_url(config, as_qrcode=False):
        """
        Génère un lien d'importation V2Ray valide avec gestion d'erreur améliorée
        et option de génération de QR Code.
    
        Args:
            config (dict): Configuration V2Ray/VLess
            as_qrcode (bool): Si True, retourne un objet QR Code plutôt qu'une URL
    
        Returns:
            str|qrcode.QRCode: URL ou QR Code selon le paramètre as_qrcode
    
        Raises:
            ValueError: Si la configuration est invalide
        """
        try:
            # Validation approfondie
            required_fields = {
                'protocol': ['vless', 'vmess', 'trojan'],
                'address': str,
                'port': (int, lambda x: 0 < x <= 65535),
                'id': (str, lambda x: len(x) == 36)  # UUID validation
            }
    
            for field, validator in required_fields.items():
                if field not in config:
                    raise ValueError(f"Champ obligatoire manquant : {field}")
                
                if isinstance(validator, list):  # Check valid protocol
                    if config[field] not in validator:
                        raise ValueError(f"Protocole invalide : {config[field]}")
                elif isinstance(validator, tuple):  # Type and value check
                    if not isinstance(config[field], validator[0]):
                        raise TypeError(f"{field} doit être de type {validator[0].__name__}")
                    if not validator[1](config[field]):
                        raise ValueError(f"Valeur invalide pour {field}")
            
            # Construction URL sécurisée
            params = {
                'type': config.get('network', 'tcp'),
                'security': 'tls' if config.get('tls', {}).get('enabled', False) else 'none',
                'flow': config.get('flow', ''),
                'encryption': 'none',
                'sni': config.get('tls', {}).get('serverName', config['address']),
                'fp': config.get('tls', {}).get('fingerprint', 'chrome'),
                'alpn': ','.join(config.get('tls', {}).get('alpn', ['h2', 'http/1.1'])),
                'pbk': config.get('tls', {}).get('publicKey', ''),
                'sid': config.get('tls', {}).get('shortId', '')
            }
    
            # Nettoyage des paramètres
            params = {k: urllib.parse.quote(str(v)) for k, v in params.items() if v and str(v) not in ('none', '')}
            
            # Construction finale
            url = f"{config['protocol']}://{config['id']}@{config['address']}:{config['port']}?{'&'.join(f'{k}={v}' for k, v in params.items())}#{urllib.parse.quote(config.get('remark', config['address']))}"
    
            if as_qrcode:
                try:
                    import qrcode
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(url)
                    qr.make(fit=True)
                    return qr.make_image(fill_color="black", back_color="white")
                except ImportError:
                    raise ImportError("Le module 'qrcode' est requis. Installez-le avec: pip install qrcode")
    
            return url
    
        except Exception as e:
            raise ValueError(f"Erreur de génération d'URL: {str(e)}") from e
    
    def generate_config_url(self, config):
        """Génère le lien URL de confirmation"""
        try:
            import urllib.parse
            base_url = f"vless://{config['id']}@{config['address']}:{config['port']}"
            params = {
                'type': config.get('network', 'tcp'),
                'security': 'tls',
                'flow': config.get('flow', ''),
                'encryption': 'none',
                'host': config.get('address', ''),
                'fp': config.get('tls', {}).get('fingerprint', 'chrome'),
                'alpn': ','.join(config.get('tls', {}).get('alpn', [])),
                'sni': config.get('tls', {}).get('serverName', config['address'])
            }
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v})
            return f"{base_url}?{query}#{config['address']}"
        except Exception as e:
            print(f"Erreur lors de la génération du lien: {str(e)}")
            return None

    def validate_config(config):
        errors = []
        
        # Vérification des champs obligatoires
        required_fields = ['protocol', 'address', 'port', 'id']
        for field in required_fields:
            if field not in config:
                errors.append(f"Champ obligatoire manquant : {field}")
        
        # Validation spécifique à VLess
        if config.get('protocol') == 'vless':
            if 'flow' not in config and config.get('tls', {}).get('enabled', False):
                errors.append("Le champ 'flow' est requis pour VLESS avec TLS")
        
        # Validation TLS
        if config.get('tls', {}).get('enabled', False):
            if 'serverName' not in config.get('tls', {}):
                errors.append("serverName est requis quand TLS est activé")
        
        return errors if errors else None

    def format_config(config):
        # Structure de base obligatoire
        formatted = {
            "protocol": config.get("protocol"),
            "address": config.get("address"),
            "port": config.get("port"),
            "id": config.get("id"),
            "flow": config.get("flow", ""),
            "network": config.get("network", "tcp"),
            "security": "tls" if config.get("tls", {}).get("enabled", False) else "none"
        }
        
        # Section TLS si activée
        if config.get("tls", {}).get("enabled", False):
            formatted["tls"] = {
                "enabled": True,
                "serverName": config["tls"].get("serverName", config["address"]),
                "alpn": config["tls"].get("alpn", ["h2", "http/1.1"]),
                "fingerprint": config["tls"].get("fingerprint", "chrome")
            }
        
        # Suppression des champs vides
        return {k: v for k, v in formatted.items() if v}
                
    def _finalize_installation(self, use_domain: bool):
        """Gère les étapes finales de l'installation"""
        print(f"\n{Colors.GREEN}=== Configuration Finale ==={Colors.NC}")
        print(f"• Protocole: {Colors.YELLOW}{self.protocol.upper()}{Colors.NC}")
        print(f"• Adresse: {Colors.YELLOW}{self.domain if use_domain else self.get_public_ip()}{Colors.NC}")
        print(f"• Port: {Colors.YELLOW}{self.port}{Colors.NC}")
        print(f"• Transport: {Colors.YELLOW}{self.transport.upper()}{Colors.NC}")
        print(f"• Sécurité: {Colors.YELLOW}{self.tls_mode.upper()}{Colors.NC}")
    
        # Appel à la méthode de confirmation
        if not hasattr(self, '_confirm_installation') or not self._confirm_installation():
            print(f"{Colors.RED}Installation annulée.{Colors.NC}")
            return False
    
        # Installation
        print(f"\n{Colors.YELLOW}Installation en cours...{Colors.NC}")
        try:
            self.install_dependencies()
            self.install_v2ray()
            
            if self.tls_mode == "tls":
                if use_domain:
                    self.configure_tls(self.domain)
                else:
                    print(f"{Colors.YELLOW}Génération d'un certificat auto-signé...{Colors.NC}")
                    self.generate_self_signed_cert()
            
            self.configure_v2ray(use_cdn=False)
            
            # Corriger l'appel à show_client_config
            if hasattr(self, 'show_client_config'):
                self.show_client_config(use_domain)
                
            else:
                print(f"{Colors.YELLOW}Avertissement: Méthode show_client_config non trouvée{Colors.NC}")
            
            return True
        except Exception as e:  # Ajout du bloc except manquant
            print(f"{Colors.RED}Erreur lors de l'installation: {e}{Colors.NC}")
            return False
      
    def show_installation_summary(self, use_domain: bool, use_cdn: bool):
        """Affiche un récapitulatif complet de l'installation"""
        address = self.domain if use_domain else self.get_public_ip()
        
        print(f"\n{Colors.GREEN}=== Installation Réussie ==={Colors.NC}")
        print(f"Fichier de configuration: {Colors.YELLOW}{CONFIG_FILE}{Colors.NC}")
        
        # Configuration client optimisée
        print(f"\n{Colors.BLUE}=== Configuration Client ==={Colors.NC}")
        
        if self.protocol == "vless":
            client_config = f"vless://{self.uuid_or_password}@{address}:{self.port}?" \
                           f"type={self.transport}&security={self.tls_mode}" \
                           f"&sni={self.domain if use_domain else ''}" \
                           f"&fp=chrome&alpn=h2,http/1.1" \
                           f"&path=%2F{self.protocol}-cdn-path" \
                           f"#{self.protocol}-cdn"
        
        elif self.protocol == "vmess":
            vmess_config = {
                "v": "2",
                "ps": f"V2Ray-{address}",
                "add": address,
                "port": str(self.port),
                "id": self.uuid_or_password,
                "aid": "0",
                "net": self.transport,
                "type": "none",
                "host": self.domain if use_domain else "",
                "path": f"/{self.protocol}-cdn-path",
                "tls": self.tls_mode if self.tls_mode != "none" else "",
                "sni": self.domain if use_domain else "",
                "alpn": "h2,http/1.1",
                "fp": "chrome"
            }
            client_config = f"vmess://{base64.b64encode(json.dumps(vmess_config).encode()).decode()}"
        
        elif self.protocol == "trojan":
            client_config = f"trojan://{self.uuid_or_password}@{address}:{self.port}?" \
                          f"security={self.tls_mode}&type={self.transport}" \
                          f"&sni={self.domain if use_domain else ''}" \
                          f"&alpn=h2,http/1.1" \
                          f"&path=%2F{self.protocol}-cdn-path" \
                          f"#{self.protocol}-cdn"
        
        print(client_config)
        
        # QR Code pour mobile
        try:
            import qrcode
            qr = qrcode.QRCode()
            qr.add_data(client_config)
            qr.print_ascii()
        except:
            print(f"{Colors.YELLOW}Installez le module 'qrcode' pour afficher un QR Code{Colors.NC}")
        
        # Paramètres avancés
        print(f"\n{Colors.BLUE}=== Paramètres Avancés ==={Colors.NC}")
        print(f"• Adresse: {Colors.YELLOW}{address}{Colors.NC}")
        print(f"• Port: {Colors.YELLOW}{self.port}{Colors.NC}")
        print(f"• ID: {Colors.YELLOW}{self.uuid_or_password}{Colors.NC}")
        print(f"• Transport: {Colors.YELLOW}{self.transport.upper()}{Colors.NC}")
        print(f"• Chemin: {Colors.YELLOW}/{self.protocol}-cdn-path{Colors.NC}")
        print(f"• SNI: {Colors.YELLOW}{self.domain if use_domain else 'auto'}{Colors.NC}")
        print(f"• Fingerprint: {Colors.YELLOW}chrome{Colors.NC}")
        print(f"• ALPN: {Colors.YELLOW}h2,http/1.1{Colors.NC}")
        
        # Instructions CDN
        if use_cdn:
            print(f"\n{Colors.GREEN}=== Configuration Cloudflare ==={Colors.NC}")
            print("1. Dans l'interface Cloudflare:")
            print("   • SSL/TLS: Full (strict)")
            print("   • Network: WebSockets activé")
            print("   • Rules: Cache Level = Bypass")
            print("2. Vérifiez que le proxy est activé (icône orange)")
            print("3. Recommandé: Activer TLS 1.3 et HTTP/3")
        
        input("\nAppuyez sur Entrée pour continuer...")

    def show_client_config(self, use_domain: bool = False):
        """Génère une configuration client optimisée pour tous les protocoles"""
        address = self.domain if use_domain and hasattr(self, 'domain') else self.get_public_ip()
        config = {}
    
        if self.protocol == "trojan":
            config = {
                "protocol": "trojan",
                "address": address,
                "port": self.port,
                "password": self.uuid_or_password,
                "network": self.transport,
                "tls": {
                    "enabled": self.tls_mode == "tls",
                    "serverName": self.domain if use_domain and hasattr(self, 'domain') else address,
                    "alpn": ["h2", "http/1.1"],
                    "fingerprint": "chrome"
                }
            }
            if self.transport == "grpc":
                config["grpc"] = {
                    "serviceName": getattr(self, 'grpc_service_name', 'trojan-grpc')
                }
            elif self.transport == "ws":
                config["ws"] = {
                    "path": getattr(self, 'ws_path', '/trojan-ws')
                }
    
        elif self.protocol == "vless":
            config = {
                "protocol": "vless",
                "address": address,
                "port": self.port,
                "id": self.uuid_or_password,
                "flow": "xtls-rprx-vision" if self.tls_mode == "tls" else "",
                "network": self.transport,
                "tls": {
                    "enabled": self.tls_mode == "tls",
                    "serverName": self.domain if use_domain and hasattr(self, 'domain') else address,
                    "alpn": ["h2", "http/1.1"],
                    "fingerprint": "chrome"
                }
            }
    
        elif self.protocol == "vmess":
            config = {
                "v": "2",
                "ps": f"V2Ray-{address}",
                "add": address,
                "port": str(self.port),
                "id": self.uuid_or_password,
                "aid": "0",
                "net": self.transport,
                "type": "none",
                "tls": self.tls_mode if self.tls_mode != "none" else ""
            }
    
        if not config:
            print(f"{Colors.RED}Protocole non supporté: {self.protocol}{Colors.NC}")
            return
    
        print(f"\n{Colors.GREEN}=== Configuration Client ==={Colors.NC}")
        print(json.dumps(config, indent=2))
        
        # Générer le QR Code si possible
        self.generate_qr_code(config)
        
    def show_full_client_config(self, use_cdn: bool = False) -> None:
        """
        Affiche une configuration client complète avec tous les paramètres nécessaires
        pour une importation facile dans les clients V2Ray.
        
        Args:
            use_cdn: Booléen indiquant si Cloudflare/CDN est utilisé
        """
        # Obtenir l'adresse de connexion
        address = self.domain if hasattr(self, 'domain') and self.domain else self.get_public_ip()
        
        print(f"\n{Colors.BLUE}=== CONFIGURATION CLIENT COMPLÈTE ===")
        print(f"Protocole: {self.protocol.upper()} | Transport: {self.transport.upper()}")
        print(f"CDN: {'Activé' if use_cdn else 'Désactivé'}{Colors.NC}\n")
        
        # Configuration de base pour tous les protocoles
        print(f"{Colors.GREEN}● Paramètres de Base:{Colors.NC}")
        print(f"Adresse: {Colors.YELLOW}{address}{Colors.NC}")
        print(f"Port: {Colors.YELLOW}{self.port}{Colors.NC}")
        print(f"ID/Mot de passe: {Colors.YELLOW}{self.uuid_or_password}{Colors.NC}")
        print(f"Transport: {Colors.YELLOW}{self.transport}{Colors.NC}")
        print(f"Sécurité: {Colors.YELLOW}{self.tls_mode}{Colors.NC}\n")
        
        # Paramètres avancés spécifiques au protocole
        print(f"{Colors.GREEN}● Paramètres Avancés:{Colors.NC}")
        
        # VLESS
        if self.protocol == "vless":
            print(f"Flow: {Colors.YELLOW}xtls-rprx-vision{Colors.NC}")
            print(f"Encryption: {Colors.YELLOW}none{Colors.NC}")
            if self.transport == "ws":
                print(f"Chemin WS: {Colors.YELLOW}/vless-ws-path{Colors.NC}")
                print(f"Header Host: {Colors.YELLOW}{self.domain if use_cdn else ''}{Colors.NC}")
        
        # VMess
        elif self.protocol == "vmess":
            print(f"Alter ID: {Colors.YELLOW}0{Colors.NC} (Recommandé)")
            print(f"Security: {Colors.YELLOW}auto{Colors.NC}")
            if self.transport == "ws":
                print(f"Chemin WS: {Colors.YELLOW}/vmess-ws-path{Colors.NC}")
        
        # Trojan
        elif self.protocol == "trojan":
            print(f"ALPN: {Colors.YELLOW}h2,http/1.1{Colors.NC}")
            if self.transport == "grpc":
                print(f"Service Name: {Colors.YELLOW}trojan-grpc-service{Colors.NC}")
        
        # Paramètres communs avancés
        print(f"\n{Colors.GREEN}● Paramètres Réseau:{Colors.NC}")
        print(f"Fingerprint TLS: {Colors.YELLOW}chrome{Colors.NC}")
        print(f"SNI: {Colors.YELLOW}{self.domain if use_cdn and hasattr(self, 'domain') else 'auto'}{Colors.NC}")
        print(f"ALPN: {Colors.YELLOW}h2,http/1.1{Colors.NC}")
        
        # Liens d'importation
        print(f"\n{Colors.GREEN}● Liens d'Importation:{Colors.NC}")
        
        # Génération des liens selon le protocole
        if self.protocol == "vless":
            vless_link = f"vless://{self.uuid_or_password}@{address}:{self.port}?" \
                        f"type={self.transport}&security={self.tls_mode}" \
                        f"&sni={self.domain if use_cdn else ''}" \
                        f"&fp=chrome&alpn=h2,http/1.1" \
                        f"&path=%2Fvless-path" \
                        f"&flow=xtls-rprx-vision" \
                        f"#VLess-{self.transport.upper()}"
            print(vless_link)
            
        elif self.protocol == "vmess":
            vmess_config = {
                "v": "2",
                "ps": f"VMess-{address}",
                "add": address,
                "port": str(self.port),
                "id": self.uuid_or_password,
                "aid": "0",
                "net": self.transport,
                "type": "none",
                "host": self.domain if use_cdn else "",
                "path": "/vmess-path",
                "tls": self.tls_mode if self.tls_mode != "none" else "",
                "sni": self.domain if use_cdn else "",
                "alpn": "h2,http/1.1",
                "fp": "chrome"
            }
            vmess_link = f"vmess://{base64.b64encode(json.dumps(vmess_config).encode()).decode()}"
            print(vmess_link)
            
        elif self.protocol == "trojan":
            trojan_link = f"trojan://{self.uuid_or_password}@{address}:{self.port}?" \
                         f"security={self.tls_mode}&type={self.transport}" \
                         f"&sni={self.domain if use_cdn else ''}" \
                         f"&alpn=h2,http/1.1" \
                         f"&path=%2Ftrojan-path" \
                         f"#Trojan-{self.transport.upper()}"
            print(trojan_link)
        
        # QR Code
        try:
            import qrcode
            qr = qrcode.QRCode()
            qr.add_data(vless_link if self.protocol == "vless" else 
                       vmess_link if self.protocol == "vmess" else 
                       trojan_link)
            print(f"\n{Colors.GREEN}● QR Code pour clients mobiles:{Colors.NC}")
            qr.print_ascii()
        except ImportError:
            print(f"\n{Colors.YELLOW}Installez 'qrcode' pour afficher un QR Code: pip install qrcode{Colors.NC}")
        
        # Instructions CDN
        if use_cdn:
            print(f"\n{Colors.GREEN}● Configuration CDN Requise:{Colors.NC}")
            print("- Mode Proxy: Activé (icône orange dans Cloudflare)")
            print("- SSL/TLS: Full (strict)")
            print("- WebSockets: Activé")
            print("- Règles de Cache: Bypass pour les chemins V2Ray")
            print("- Recommandé: Activer HTTP/3 et 0-RTT")
        
        # Conseils de dépannage
        print(f"\n{Colors.GREEN}● Conseils:{Colors.NC}")
        print("- Testez la connexion avec: curl -v https://{address}")
        print("- Vérifiez les logs: journalctl -u v2ray -f")
        print("- Redémarrez le service après modifications: systemctl restart v2ray")
        
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

    def show_installation_summary(self, use_domain: bool, use_cdn: bool):
        """Affiche un récapitulatif complet de l'installation"""
        address = self.domain if use_domain else self.get_public_ip()
        
        print(f"\n{Colors.GREEN}=== Installation Réussie ==={Colors.NC}")
        print(f"Fichier de configuration: {Colors.YELLOW}{CONFIG_FILE}{Colors.NC}")
        
        # Configuration client optimisée
        print(f"\n{Colors.BLUE}=== Configuration Client ==={Colors.NC}")
        
        if self.protocol == "vless":
            client_config = f"vless://{self.uuid_or_password}@{address}:{self.port}?" \
                           f"type={self.transport}&security={self.tls_mode}" \
                           f"&sni={self.domain if use_domain else ''}" \
                           f"&fp=chrome&alpn=h2,http/1.1" \
                           f"&path=%2F{self.protocol}-path" \
                           f"#{self.protocol}-{self.transport}"
        
        elif self.protocol == "vmess":
            vmess_config = {
                "v": "2",
                "ps": f"V2Ray-{address}",
                "add": address,
                "port": str(self.port),
                "id": self.uuid_or_password,
                "aid": "0",
                "net": self.transport,
                "type": "none",
                "host": self.domain if use_domain else "",
                "path": f"/{self.protocol}-path",
                "tls": self.tls_mode if self.tls_mode != "none" else "",
                "sni": self.domain if use_domain else "",
                "alpn": "h2,http/1.1",
                "fp": "chrome"
            }
            client_config = f"vmess://{base64.b64encode(json.dumps(vmess_config).encode()).decode()}"
        
        elif self.protocol == "trojan":
            client_config = f"trojan://{self.uuid_or_password}@{address}:{self.port}?" \
                           f"security={self.tls_mode}&type={self.transport}" \
                           f"&sni={self.domain if use_domain else ''}" \
                           f"&alpn=h2,http/1.1" \
                           f"&path=%2F{self.protocol}-path" \
                           f"#{self.protocol}-{self.transport}"
        
        print(client_config)
        
        # QR Code pour mobile
        try:
            import qrcode
            qr = qrcode.QRCode()
            qr.add_data(client_config)
            qr.print_ascii()
        except ImportError:
            print(f"{Colors.YELLOW}Installez le module 'qrcode' pour afficher un QR Code{Colors.NC}")
        
        # Paramètres avancés
        print(f"\n{Colors.BLUE}=== Paramètres Avancés ==={Colors.NC}")
        print(f"• Adresse: {Colors.YELLOW}{address}{Colors.NC}")
        print(f"• Port: {Colors.YELLOW}{self.port}{Colors.NC}")
        print(f"• ID: {Colors.YELLOW}{self.uuid_or_password}{Colors.NC}")
        print(f"• Transport: {Colors.YELLOW}{self.transport.upper()}{Colors.NC}")
        print(f"• Chemin: {Colors.YELLOW}/{self.protocol}-path{Colors.NC}")
        print(f"• SNI: {Colors.YELLOW}{self.domain if use_domain else 'auto'}{Colors.NC}")
        print(f"• Fingerprint: {Colors.YELLOW}chrome{Colors.NC}")
        print(f"• ALPN: {Colors.YELLOW}h2,http/1.1{Colors.NC}")
        
        # Instructions CDN
        if use_cdn:
            print(f"\n{Colors.GREEN}=== Configuration Cloudflare ==={Colors.NC}")
            print("1. Dans l'interface Cloudflare:")
            print("   • SSL/TLS: Full (strict)")
            print("   • Network: WebSockets activé")
            print("   • Rules: Cache Level = Bypass")
            print("2. Vérifiez que le proxy est activé (icône orange)")
            print("3. Recommandé: Activer TLS 1.3 et HTTP/3")
        
        input("\nAppuyez sur Entrée pour continuer...")
        
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

# New implémenter

    def update_v2ray(self):
        """Mise à jour de V2Ray/Xray"""
        print("\nDébut de la mise à jour...")
        try:
            # Commande de mise à jour pour Xray (adaptez selon votre besoin)
            os.system("bash -c \"$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)\" @ install")
            print("Mise à jour terminée avec succès!")
        except Exception as e:
            print(f"Échec de la mise à jour: {str(e)}")
        input("Appuyez sur Entrée pour continuer...")

    def apply_config(self, config):
        """Écrit la configuration dans le fichier config.json"""
        config_path = "/usr/local/etc/xray/config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def start_service(self):
        """Démarre le service Xray"""
        os.system("systemctl enable --now xray")
    
    def rollback_installation(self):
        """Annule l'installation en cas d'échec"""
        print("\nAnnulation de l'installation...")
        os.system("rm -rf /usr/local/etc/xray")
        os.system("systemctl stop xray 2>/dev/null")
    
    def full_installation(self):
        """Effectue l'installation complète de V2Ray/Xray"""
        try:
            print("\n=== Installation Complète ===")
            
            # 1. Installation des dépendances
            self.install_dependencies()
            
            # 2. Installation de Xray/V2Ray
            self.install_v2ray()
            
            # 3. Génération de la configuration
            config = self.generate_config()
            
            # 4. Application de la configuration
            self.apply_config(config)
            
            # 5. Démarrage du service
            self.start_service()
            
            # 6. Affichage des informations de connexion
            print("\nInstallation terminée avec succès!")
            print(f"URL de configuration : {self.generate_v2ray_url(config)}")
            
        except Exception as e:
            print(f"\nErreur lors de l'installation: {str(e)}")
            self.rollback_installation()
        finally:
            input("\nAppuyez sur Entrée pour retourner au menu...")
    
    def uninstall(self):
        """Désinstalle complètement V2Ray/Xray"""
        print("\n=== Désinstallation ===")
        try:
            # Arrêt du service
            os.system("systemctl stop xray 2>/dev/null")
            
            # Désinstallation
            os.system("bash -c \"$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)\" @ remove --purge")
            
            # Nettoyage
            os.system("rm -rf /usr/local/etc/xray /var/log/xray")
            print("Désinstallation terminée avec succès!")
        except Exception as e:
            print(f"Erreur lors de la désinstallation: {str(e)}")
        input("\nAppuyez sur Entrée pour continuer...")
    
    def manage_configs(self):
        """Gère les configurations existantes"""
        print("\nGestion des configurations")
        # Implémentez la logique de gestion ici
        input("\nAppuyez sur Entrée pour continuer...")
    
    def check_status(self):
        """Vérifie le statut du service"""
        os.system("systemctl status xray")
        input("\nAppuyez sur Entrée pour continuer...")            

    def quit_installer(self):
        """Quitte proprement l'installateur"""
        print("\nFermeture de l'installateur...")
        exit(0)
    
    def update_v2ray(self):
        """Met à jour V2Ray/Xray en toute sécurité"""
        print("\n=== Mise à jour ===")
        try:
            # Sauvegarde de l'ancienne configuration
            if os.path.exists("/usr/local/etc/xray/config.json"):
                os.system("cp /usr/local/etc/xray/config.json /tmp/xray_config.bak")
            
            # Mise à jour
            os.system("bash -c \"$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)\" @ install")
            
            # Restauration de la configuration
            if os.path.exists("/tmp/xray_config.bak"):
                os.system("mv /tmp/xray_config.bak /usr/local/etc/xray/config.json")
                os.system("systemctl restart xray")
            
            print("\n✅ Mise à jour terminée avec succès!")
        except Exception as e:
            print(f"\n❌ Échec de la mise à jour: {str(e)}")
        input("\nAppuyez sur Entrée pour continuer...")
                      
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
            
   
    def main_menu(self):
        while True:
            print("\n" + "="*50)
            print("Menu Principal".center(50))
            print("="*50)
            print("1. Installation complète")
            print("2. Mise à jour de V2Ray")
            print("3. Désinstaller V2Ray")
            print("4. Gérer les configurations")
            print("5. Voir le statut du service")
            print("6. Quitter")
            
            choice = input("Choisissez une option [1-6]: ").strip()
            
            if choice == '1':
                self.full_installation()
            elif choice == '2':
                self.update_v2ray()  # Cette méthode doit exister
            elif choice == '3':
                self.uninstall()
            elif choice == '4':
                self.manage_configs()
            elif choice == '5':
                self.check_status()
            elif choice == '6':
                exit(0)
            else:
                print("Option invalide, veuillez réessayer.")
    
    def main(self) -> None:
        """Point d'entrée principal"""
        self.check_root()
        self.init_log()
        self.detect_os()
        self.main_menu()

if __name__ == "__main__":
    installer = V2RayInstaller()
    installer.main()