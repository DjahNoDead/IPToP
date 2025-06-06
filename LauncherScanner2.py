# ===== Auto-update du launcher =====
import urllib.request
import hashlib
import importlib.util
import sys
import time
import os

# Couleurs ANSI pour la bannière
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_MAGENTA = "\033[95m"
COLOR_CYAN = "\033[96m"
COLOR_RESET = "\033[0m"

# Bannière d'accueil colorée avec animation
def display_banner():
    banner = f"""
{COLOR_CYAN}___ ____ _____     ____{COLOR_RESET}
{COLOR_CYAN}|_ _|  _ \\_   _|__ |  _ \\{COLOR_RESET}
{COLOR_CYAN} | || |_) || |/ _ \\| |_) |{COLOR_RESET}
{COLOR_CYAN} | ||  __/ | | (_) |  __/{COLOR_RESET}
{COLOR_CYAN}|___|_|    |_|\\___/|_|{COLOR_RESET}
{COLOR_GREEN}              Scanner3.0{COLOR_RESET}
{COLOR_BLUE}  DjahNoDead 🕵️‍♂️{COLOR_RESET}
https://t.me/+44xRl7P_SoBkOTVk

{COLOR_MAGENTA} IPToP💪👽(Internet Pour Tous ou Personne).{COLOR_RESET}
"""
    print(banner)
    time.sleep(2)  # Pause pour lisibilité

VERSION = "Basique"  # Version locale actuelle
VERSION_URL = "https://raw.githubusercontent.com/DjahNoDead/IPToP/main/versionLaun.txt"
LAUNCHER_URL = "https://raw.githubusercontent.com/DjahNoDead/IPToP/main/LauncherScanner2.py"

SCRIPT_VERSION = "Basique"
SCRIPT_URL = "https://raw.githubusercontent.com/DjahNoDead/IPToP/main/iptp.py"
SCRIPT_VERSION_URL = "https://raw.githubusercontent.com/DjahNoDead/IPToP/main/versionScan.txt"

def load_main_function():
    """Charge la fonction main() de manière sécurisée"""
    try:
        # Essayer depuis le module courant
        if 'main' in globals():
            return globals()['main']
        
        # Essayer depuis le script principal (iptp.py)
        spec = importlib.util.spec_from_file_location("iptp", "iptp.py")
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'main'):
                return module.main
        
        # Fallback basique
        def fallback_main():
            print("[ℹ️] Mode recovery - exécution minimale")
            # Ajoutez ici le strict minimum pour que votre script fonctionne
            from iptp import main as real_main
            real_main()
        
        return fallback_main
    except Exception as e:
        print(f"[⚠️] Erreur de chargement: {str(e)}")
        sys.exit(1)

def get_script_remote_version():
    try:
        with urllib.request.urlopen(SCRIPT_VERSION_URL, timeout=3) as r:
            return r.read().decode().strip()
    except:
        return None

def get_remote_version():
    try:
        with urllib.request.urlopen(VERSION_URL, timeout=3) as r:
            return r.read().decode().strip()
    except:
        return None

def get_remote_launcher():
    try:
        with urllib.request.urlopen(LAUNCHER_URL, timeout=5) as r:
            return r.read().decode('utf-8')
    except:
        return None

def get_self_path():
    return os.path.abspath(__file__)


def update_self_if_needed():
    """Version finale avec gestion parfaite des états"""
    # Fichiers de contrôle
    INIT_FLAG = os.path.join(CACHE_DIR, ".initialized")
    UPDATE_LOCK = os.path.join(CACHE_DIR, ".update_lock")
    UPDATE_DONE = os.path.join(CACHE_DIR, ".update_done")

    # Première installation
    if not os.path.exists(INIT_FLAG):
        try:
            os.makedirs(CACHE_DIR, mode=0o700, exist_ok=True)
            with open(INIT_FLAG, "w") as f:
                f.write("1")
            print("[🛠️] Configuration initiale terminée")
            return False
        except Exception as e:
            print(f"[⚠️] Erreur initialisation: {str(e)}")
            return False

    # Vérifier si une mise à jour vient d'être faite
    if os.path.exists(UPDATE_DONE):
        update_time = os.path.getmtime(UPDATE_DONE)
        if (time.time() - update_time) < 300:  # 5 minutes
            print("[ℹ️] Mise à jour récente déjà effectuée")
            return False

    # Verrouillage pour éviter les conflits
    if os.path.exists(UPDATE_LOCK):
        print("[⏳] Mise à jour déjà en cours...")
        return False

    try:
        # Création du verrou
        with open(UPDATE_LOCK, "w") as f:
            f.write(str(os.getpid()))

        display_banner()
        print("[🔍] Vérification des mises à jour...")

        remote_version = get_remote_version()
        if not remote_version:
            print("[⚠️] Impossible de contacter le serveur")
            return False

        if remote_version == VERSION:
            print(f"[✓] Version {VERSION} à jour")
            return False

        print(f"[🔄] Téléchargement de la v{remote_version}...")
        remote_code = get_remote_launcher()
        if not remote_code:
            print("[❌] Échec du téléchargement")
            return False

        # Processus atomique en 3 étapes
        temp_file = f"{get_self_path()}.tmp"
        backup_file = f"{get_self_path()}.bak"
        
        try:
            # 1. Sauvegarde
            if os.path.exists(get_self_path()):
                os.rename(get_self_path(), backup_file)
            
            # 2. Nouvelle version
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(remote_code)
                
            # 3. Remplacement
            os.rename(temp_file, get_self_path())
            
            # Marqueur de succès
            with open(UPDATE_DONE, "w") as f:
                f.write(str(time.time()))
            
            print("[✅] Mise à jour terminée avec succès")
            os.execv(sys.executable, [sys.executable] + sys.argv)
            return True
            
        except Exception as e:
            # Restauration en cas d'échec
            if os.path.exists(backup_file):
                os.rename(backup_file, get_self_path())
            print(f"[❌] Échec critique: {str(e)}")
            return False
            
    finally:
        # Nettoyage systématique
        if os.path.exists(UPDATE_LOCK):
            os.remove(UPDATE_LOCK)
        
#===== Installateur automatique=====

import subprocess
import sys
import os
import threading
import itertools
import time
import importlib.util

required_modules = {
    "colorama": "colorama",
    "requests": "requests",
    "Cryptodome": "pycryptodome",
    "dns": "dnspython"
}

class Spinner:
    def __init__(self, message="Préparation de l'environnement... "):
        self.spinner = itertools.cycle(['|', '/', '-', '\\'])
        self.running = False
        self.thread = None
        self.message = message
        self.displayed_message = False

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()

    def _spin(self):
        while self.running:
            if not self.displayed_message:
                sys.stdout.write(f"\r{self.message}{next(self.spinner)}")
                sys.stdout.flush()
                self.displayed_message = True
            else:
                sys.stdout.write(f"\r{next(self.spinner)}")
                sys.stdout.flush()
            time.sleep(0.1)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write('\r[✓] Environnement prêt !           \n')
        sys.stdout.flush()

def is_module_installed(module_name):
    return importlib.util.find_spec(module_name) is not None

def install_missing_modules(modules):
    installed = []
    failed = []
    spinner = Spinner()

    try:
        for import_name, pip_name in modules.items():
            if not is_module_installed(import_name):
                if not spinner.running:
                    spinner.start()
                try:
                    with open(os.devnull, 'w') as devnull:
                        subprocess.check_call(
                            [sys.executable, "-m", "pip", "install", pip_name],
                            stdout=devnull,
                            stderr=devnull
                        )
                    installed.append(pip_name)
                except subprocess.CalledProcessError:
                    failed.append(pip_name)
        if spinner.running:
            spinner.stop()
    except KeyboardInterrupt:
        if spinner.running:
            spinner.stop()
        print("\n[!] Installation interrompue par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        if spinner.running:
            spinner.stop()
        print(f"\n[!] Une erreur est survenue : {e}")
        sys.exit(1)

    if installed:
        print(f"[+] Modules installés : {', '.join(installed)}")
    if failed:
        print(f"[!] Échec d'installation pour : {', '.join(failed)}")

install_missing_modules(required_modules)

# ===== LAUNCHER ========

import urllib.request
import tempfile
import socket
import hashlib
import base64
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
import ctypes
import platform

# 🔐 Configuration et sécurité
REPO_URL = "https://raw.githubusercontent.com/DjahNoDead/IPToP/main/"
SCRIPT_NAME = "iptp.py"
SECRET_KEY = hashlib.sha256(
    b"MaCleSecretePersonnalisableS@int_Saint-S@int!Est#Le&Tout?Puissant!"
).digest()

CACHE_DIR = os.path.expanduser("~/.config/.iptp_secure")
CACHE_PATH = os.path.join(CACHE_DIR, "cache.dat")
VERSION_FILE = os.path.join(CACHE_DIR, "iptp.version.local")

os.makedirs(CACHE_DIR, mode=0o700, exist_ok=True)

# 🔐 Chiffrement AES-256
def encrypt_content(content):
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(content.encode("utf-8"), AES.block_size))
    return base64.b64encode(cipher.iv + ct_bytes).decode("utf-8")

def decrypt_content(encrypted):
    try:
        data = base64.b64decode(encrypted)
        iv, ct = data[:16], data[16:]
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv=iv)
        return unpad(cipher.decrypt(ct), AES.block_size).decode("utf-8")
    except:
        return None

# 💾 Cache
def save_encrypted(content):
    try:
        encrypted = encrypt_content(content)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            f.write(encrypted)
        os.chmod(CACHE_PATH, 0o600)
        return True
    except Exception as e:
        print(f"[!] Erreur chiffrement: {e}")
        return False

def load_encrypted():
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return decrypt_content(f.read())
    except:
        return None

# 📦 Version du script principal
def save_local_script_version(version):
    try:
        with open(VERSION_FILE, "w") as f:
            f.write(version)
        os.chmod(VERSION_FILE, 0o600)
    except Exception as e:
        print(f"[!] Erreur sauvegarde version: {e}")

def load_local_script_version():
    try:
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    except:
        return None

# 🔗 Connexion
def is_connected():
    try:
        urllib.request.urlopen("https://1.1.1.1", timeout=3)
        return True
    except:
        return False

# ⬇️ Téléchargement
def download_script():
    try:
        with urllib.request.urlopen(REPO_URL + SCRIPT_NAME, timeout=5) as r:
            return r.read().decode("utf-8")
    except Exception as e:
        print(f"[DEBUG] Erreur téléchargement: {str(e)}")
        return None

# 🧼 Nettoyage
def clean_old_versions():
    if not os.path.exists(CACHE_DIR) or not is_connected():
        return
    current_file = os.path.basename(CACHE_PATH)
    try:
        for filename in os.listdir(CACHE_DIR):
            if filename != current_file:
                try:
                    os.remove(os.path.join(CACHE_DIR, filename))
                except:
                    pass
    except:
        pass

# 📂 Initialisation
def ensure_cache_dir():
    try:
        os.makedirs(CACHE_DIR, mode=0o700, exist_ok=True)
        return True
    except Exception as e:
        print(f"[ERREUR] Impossible de créer le cache: {str(e)}")
        return False

def initialize():
    if not ensure_cache_dir():
        sys.exit(1)
    try:
        test_file = os.path.join(CACHE_DIR, "test.tmp")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return True
    except Exception as e:
        print(f"[ERREUR] Permission refusée dans {CACHE_DIR}")
        return False

if not initialize():
    sys.exit(1)

# 🔧 Permissions (optionnel mais utile)
def fix_permissions():
    try:
        os.makedirs(CACHE_DIR, mode=0o700, exist_ok=True)
        if not os.access(CACHE_DIR, os.W_OK):
            print("\n[!] Correction automatique des permissions...")
            os.system(f"chmod 700 {CACHE_DIR}")
        return True
    except Exception as e:
        print(f"[DEBUG] Erreur permissions: {str(e)}")
        return False
        
def main():
    """Fonction principale avec gestion robuste des mises à jour"""
    try:
        # Initialisation
        if not getattr(main, "_init_done", False):
            display_banner()
            main._init_done = True
            time.sleep(1)
            print("[🚀] Initialisation du système...")

        # Installation des dépendances
        install_missing_modules(required_modules)
        
        # Nettoyage en arrière-plan
        threading.Thread(target=clean_old_versions, daemon=True).start()

        # Vérification mise à jour script principal
        remote_version = get_script_remote_version()
        local_version = load_local_script_version()

        if remote_version and remote_version != local_version:
            print(f"[⬇️] Mise à jour du script (v{remote_version})...")
            script = download_script()
            
            if script:
                # Sauvegarde de l'ancienne version
                if os.path.exists(CACHE_PATH):
                    os.rename(CACHE_PATH, f"{CACHE_PATH}.backup")
                
                # Nouvelle version
                if save_encrypted(script):
                    save_local_script_version(remote_version)
                    exec(script, globals())
                    return
                else:
                    # Restauration si échec
                    if os.path.exists(f"{CACHE_PATH}.backup"):
                        os.rename(f"{CACHE_PATH}.backup", CACHE_PATH)
                    print("[⚠️] Échec de sauvegarde, version précédente restaurée")

        # Chargement depuis cache
        cached_script = load_encrypted()
        if cached_script:
            exec(cached_script, globals())
            return

        # Mode urgence si tout échoue
        print("\n[❌] Aucune version valide disponible")
        if os.path.exists(f"{CACHE_PATH}.backup"):
            print("[⚠️] Tentative de restauration d'urgence...")
            os.rename(f"{CACHE_PATH}.backup", CACHE_PATH)
            main()  # Réessaye avec la version sauvegardée
        else:
            sys.exit(1)

    except Exception as e:
        print(f"\n[💥] ERREUR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Gestion des mises à jour du launcher
    if os.environ.get("IPT_UPDATE_DONE") != "1":
        if update_self_if_needed():  # Si mise à jour effectuée
            os.environ["IPT_UPDATE_DONE"] = "1"
            os.execv(sys.executable, [sys.executable] + sys.argv)
    
    # Lancement principal
    main()