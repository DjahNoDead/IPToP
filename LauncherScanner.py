#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LauncherScanner Pro - Version 4.4 (FINAL)
By DjahNoDead 🕵️‍♂️
"""

import os
import sys
import time
import json
import hashlib
import base64
import threading
import subprocess
import importlib.util
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import itertools
import socket

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Configuration centralisée"""
    
    # URLs
    REPO_BASE = "https://raw.githubusercontent.com/DjahNoDead/IPToP/main/"
    VERSION_LAUNCHER_URL = REPO_BASE + "versionLaun.txt"
    LAUNCHER_URL = REPO_BASE + "LauncherScanner.py"
    VERSION_SCRIPT_URL = REPO_BASE + "versionScan.txt"
    SCRIPT_URL = REPO_BASE + "iptp.py"
    
    # Chemins
    BASE_DIR = Path.home() / ".config" / ".iptp_secure"
    CACHE_FILE = BASE_DIR / "cache.dat"
    VERSION_FILE = BASE_DIR / "version.local"
    CONFIG_FILE = BASE_DIR / "config.json"
    LOCK_FILE = BASE_DIR / "update.lock"
    LOG_FILE = BASE_DIR / "launcher.log"
    INSTALL_DONE_FILE = BASE_DIR / "install_done.flag"
    LAST_CHECK_FILE = BASE_DIR / "last_check.time"
    
    # Sécurité
    SECRET_KEY = hashlib.sha256(
        b"MaCleSecretePersonnalisableS@int_Saint-S@int!Est#Le&Tout?Puissant!"
    ).digest()
    
    # Timeouts (secondes)
    CONNECTION_TIMEOUT = 5
    DOWNLOAD_TIMEOUT = 15
    LOCK_TIMEOUT = 300
    CACHE_DURATION = 3600
    
    # Modules requis (psutil devient optionnel)
    REQUIRED_MODULES = {
        "colorama": "colorama",
        "requests": "requests",
        "Cryptodome": "pycryptodome",
        "dns": "dnspython",
    }
    
    OPTIONAL_MODULES = {
        "psutil": "psutil",
    }


# ============================================================================
# UTILS - COULEURS
# ============================================================================

class Colors:
    """Gestion des couleurs ANSI"""
    
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    RESET = "\033[0m"
    
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    
    @classmethod
    def disable(cls):
        for attr in dir(cls):
            if not attr.startswith('_') and isinstance(getattr(cls, attr), str):
                if attr not in ['RESET', 'disable']:
                    setattr(cls, attr, '')
    
    @classmethod
    def colorize(cls, text: str, color: str, style: str = "") -> str:
        return f"{style}{color}{text}{cls.RESET}"


# ============================================================================
# UTILS - LOGGER
# ============================================================================

class Logger:
    """Système de logging avancé"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.silent = False
    
    def log(self, level: str, message: str, print_msg: bool = True):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except:
            pass
        
        if print_msg and not self.silent:
            color_map = {
                "INFO": Colors.GREEN,
                "WARN": Colors.YELLOW,
                "ERROR": Colors.RED,
                "DEBUG": Colors.BLUE,
                "SUCCESS": Colors.CYAN
            }
            color = color_map.get(level, Colors.WHITE)
            print(f"{color}[{level}]{Colors.RESET} {message}")
    
    def info(self, msg: str): self.log("INFO", msg)
    def warn(self, msg: str): self.log("WARN", msg)
    def error(self, msg: str): self.log("ERROR", msg)
    def debug(self, msg: str): self.log("DEBUG", msg)
    def success(self, msg: str): self.log("SUCCESS", msg)


# ============================================================================
# UTILS - SPINNER
# ============================================================================

class Spinner:
    """Animation de chargement élégante"""
    
    def __init__(self, message: str = "", style: str = "dots"):
        self.message = message
        self.running = False
        self.thread = None
        
        self.styles = {
            "dots": ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
            "line": ['|', '/', '-', '\\'],
            "circle": ['◜', '◠', '◝', '◞', '◡', '◟'],
            "square": ['▖', '▘', '▝', '▗'],
            "clock": ['🕛', '🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚'],
        }
        self.frames = self.styles.get(style, self.styles["dots"])
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()
    
    def _animate(self):
        for frame in itertools.cycle(self.frames):
            if not self.running:
                break
            sys.stdout.write(f"\r{self.message} {Colors.CYAN}{frame}{Colors.RESET}")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stdout.flush()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)


# ============================================================================
# BANNER
# ============================================================================

class Banner:
    """Bannière animée"""
    
    @staticmethod
    def show():
        banner = f"""
{Colors.CYAN}___ ____ _____     ____
{Colors.CYAN}|_ _|  _ \\_   _|__ |  _ \\
{Colors.CYAN} | || |_) || |/ _ \\| |_) |
{Colors.CYAN} | ||  __/ | | (_) |  __/
{Colors.CYAN}|___|_|    |_|\\___/|_|
{Colors.GREEN}         Scanner 4.4 Pro{Colors.RESET}
{Colors.BLUE}     DjahNoDead 🕵️‍♂️{Colors.RESET}
{Colors.MAGENTA}https://t.me/+44xRl7P_SoBkOTVk{Colors.RESET}

{Colors.YELLOW}IPToP💪👽 (Internet Pour Tous ou Personne){Colors.RESET}
"""
        print(banner)
        time.sleep(0.5)


# ============================================================================
# CRYPTO
# ============================================================================

class Crypto:
    """Gestion du chiffrement AES-256"""
    
    def __init__(self, key: bytes):
        self.key = key
    
    def encrypt(self, content: str) -> str:
        try:
            from Cryptodome.Cipher import AES
            from Cryptodome.Util.Padding import pad
        except ImportError:
            try:
                from Crypto.Cipher import AES
                from Crypto.Util.Padding import pad
            except ImportError:
                raise ImportError("PyCryptodome requis")
        
        cipher = AES.new(self.key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(content.encode("utf-8"), AES.block_size))
        iv = cipher.iv
        return base64.b64encode(iv + ct_bytes).decode("utf-8")
    
    def decrypt(self, encrypted: str) -> Optional[str]:
        try:
            from Cryptodome.Cipher import AES
            from Cryptodome.Util.Padding import unpad
        except ImportError:
            try:
                from Crypto.Cipher import AES
                from Crypto.Util.Padding import unpad
            except ImportError:
                raise ImportError("PyCryptodome requis")
        
        try:
            data = base64.b64decode(encrypted)
            if len(data) < 16:
                return None
            iv = data[:16]
            ct = data[16:]
            cipher = AES.new(self.key, AES.MODE_CBC, iv=iv)
            decrypted = unpad(cipher.decrypt(ct), AES.block_size)
            return decrypted.decode("utf-8")
        except Exception:
            return None


# ============================================================================
# GESTIONNAIRE DE PAQUETS
# ============================================================================

class PackageManager:
    """Gestionnaire d'installation des dépendances"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.installed = []
        self.failed = []
        self.optional_failed = []
    
    def is_installed(self, module_name: str) -> bool:
        return importlib.util.find_spec(module_name) is not None
    
    def install_module(self, pip_name: str, is_optional: bool = False) -> bool:
        """Installe un module avec gestion des erreurs"""
        try:
            cmd = [sys.executable, "-m", "pip", "install", "--quiet", pip_name]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                if not is_optional:
                    self.installed.append(pip_name)
                return True
            else:
                if is_optional:
                    self.optional_failed.append(pip_name)
                else:
                    self.failed.append(pip_name)
                return False
                
        except subprocess.TimeoutExpired:
            if is_optional:
                self.optional_failed.append(pip_name)
            else:
                self.failed.append(pip_name)
            return False
        except Exception as e:
            if is_optional:
                self.optional_failed.append(pip_name)
            else:
                self.failed.append(pip_name)
            return False
    
    def install_all(self, modules: Dict[str, str]) -> bool:
        """Installe tous les modules requis"""
        to_install = []
        
        for import_name, pip_name in modules.items():
            if not self.is_installed(import_name):
                to_install.append(pip_name)
        
        if not to_install:
            self.logger.success("Tous les modules requis sont déjà installés")
            return True
        
        self.logger.info(f"Installation de {len(to_install)} module(s)...")
        
        for pip_name in to_install:
            print(f"{Colors.CYAN}[INSTALL]{Colors.RESET} Installation de {pip_name}...")
            if self.install_module(pip_name, is_optional=False):
                print(f"{Colors.GREEN}✓{Colors.RESET} {pip_name} installé")
            else:
                print(f"{Colors.RED}✗{Colors.RESET} {pip_name} échec")
        
        if self.installed:
            self.logger.success(f"Modules installés: {', '.join(self.installed)}")
        if self.failed:
            self.logger.warn(f"Échecs critiques: {', '.join(self.failed)}")
        
        return len(self.failed) == 0
    
    def install_optional(self, modules: Dict[str, str]):
        """Installe les modules optionnels sans bloquer"""
        for import_name, pip_name in modules.items():
            if not self.is_installed(import_name):
                if self.install_module(pip_name, is_optional=True):
                    self.logger.debug(f"Module optionnel {pip_name} installé")
                else:
                    self.logger.debug(f"Module optionnel {pip_name} non disponible")


# ============================================================================
# GESTIONNAIRE DE MISE À JOUR (ULTRA INTELLIGENT)
# ============================================================================

class UpdateManager:
    """Gestionnaire de mises à jour intelligent avec cache de version"""
    
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self.crypto = Crypto(config.SECRET_KEY)
        self._version_cache = {}  # Cache en mémoire pour la session
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare deux versions
        Retourne: 1 si v1 > v2, -1 si v1 < v2, 0 si égal
        """
        def normalize(v):
            return [int(x) for x in v.split('.')]
        
        try:
            v1_parts = normalize(v1)
            v2_parts = normalize(v2)
            
            for i in range(max(len(v1_parts), len(v2_parts))):
                v1_val = v1_parts[i] if i < len(v1_parts) else 0
                v2_val = v2_parts[i] if i < len(v2_parts) else 0
                if v1_val > v2_val:
                    return 1
                elif v1_val < v2_val:
                    return -1
            return 0
        except:
            # En cas d'erreur, comparaison simple
            if v1 == v2:
                return 0
            return 1 if v1 > v2 else -1
    
    def get_cached_remote_version(self, url_key: str) -> Optional[str]:
        """Récupère la version distante depuis le cache disque"""
        cache_file = self.config.BASE_DIR / f"version_cache_{url_key}.txt"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
            
            # Vérifier si le cache est encore valide (1 heure)
            cache_time = data.get("timestamp", 0)
            if time.time() - cache_time > 3600:  # 1 heure
                return None
            
            return data.get("version")
        except:
            return None
    
    def cache_remote_version(self, url_key: str, version: str):
        """Met en cache la version distante"""
        cache_file = self.config.BASE_DIR / f"version_cache_{url_key}.txt"
        
        try:
            with open(cache_file, "w") as f:
                json.dump({
                    "version": version,
                    "timestamp": time.time()
                }, f)
        except:
            pass
    
    def get_remote_version(self, url: str, url_key: str, force: bool = False) -> Optional[str]:
        """
        Récupère la version distante avec cache intelligent
        force=True: ignore le cache et force la requête
        """
        # Vérifier le cache en mémoire d'abord
        if not force and url_key in self._version_cache:
            return self._version_cache[url_key]
        
        # Vérifier le cache disque
        if not force:
            cached = self.get_cached_remote_version(url_key)
            if cached:
                self._version_cache[url_key] = cached
                return cached
        
        # Requête réseau
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=self.config.CONNECTION_TIMEOUT) as r:
                version = r.read().decode().strip()
                
                if version:
                    # Mettre en cache
                    self._version_cache[url_key] = version
                    self.cache_remote_version(url_key, version)
                    return version
                
        except Exception as e:
            self.logger.debug(f"Impossible de récupérer {url}: {str(e)}")
        
        return None
    
    def download_file(self, url: str) -> Optional[str]:
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=self.config.DOWNLOAD_TIMEOUT) as r:
                return r.read().decode('utf-8')
        except Exception as e:
            self.logger.debug(f"Échec téléchargement {url}: {str(e)}")
            return None
    
    def check_launcher_update(self, current_version: str, force: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Vérifie la mise à jour du launcher
        force=True: ignore le cache et force la vérification
        """
        remote_version = self.get_remote_version(
            self.config.VERSION_LAUNCHER_URL, 
            "launcher", 
            force=force
        )
        
        if not remote_version:
            return False, None
        
        # Comparaison intelligente des versions
        if self._compare_versions(remote_version, current_version) <= 0:
            return False, None
        
        self.logger.info(f"Nouvelle version du launcher disponible: v{remote_version} (actuelle: v{current_version})")
        return True, remote_version
    
    def check_script_update(self, current_version: Optional[str], force: bool = False) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Vérifie la mise à jour du script
        Retourne: (has_update, new_version, script_content)
        force=True: ignore le cache et force la vérification
        """
        # Récupérer la version distante
        remote_version = self.get_remote_version(
            self.config.VERSION_SCRIPT_URL, 
            "script", 
            force=force
        )
        
        if not remote_version:
            return False, None, None
        
        # Si pas de version locale, c'est une première installation
        if not current_version:
            self.logger.info(f"Première installation: version distante v{remote_version}")
            script_content = self.download_file(self.config.SCRIPT_URL)
            if script_content:
                return True, remote_version, script_content
            return False, None, None
        
        # Comparaison intelligente des versions
        if self._compare_versions(remote_version, current_version) <= 0:
            self.logger.debug(f"Version à jour: v{current_version} (distante: v{remote_version})")
            return False, None, None
        
        # Nouvelle version disponible
        self.logger.info(f"Nouvelle version du script disponible: v{remote_version} (actuelle: v{current_version})")
        
        # Télécharger la nouvelle version
        script_content = self.download_file(self.config.SCRIPT_URL)
        if not script_content:
            self.logger.error("Échec du téléchargement du script")
            return False, None, None
        
        return True, remote_version, script_content
    
    def update_script(self, script_content: str, version: str) -> bool:
        """Met à jour le script en cache"""
        try:
            # Vérifier si le contenu a vraiment changé
            if self.config.CACHE_FILE.exists():
                with open(self.config.CACHE_FILE, "r", encoding="utf-8") as f:
                    old_encrypted = f.read().strip()
                old_content = self.crypto.decrypt(old_encrypted)
                
                if old_content == script_content:
                    self.logger.debug("Contenu identique, mise à jour ignorée")
                    return True
            
            # Chiffrer et sauvegarder
            encrypted = self.crypto.encrypt(script_content)
            with open(self.config.CACHE_FILE, "w", encoding="utf-8") as f:
                f.write(encrypted)
            self.config.CACHE_FILE.chmod(0o600)
            
            # Sauvegarder la version
            with open(self.config.VERSION_FILE, "w", encoding="utf-8") as f:
                f.write(version)
            self.config.VERSION_FILE.chmod(0o600)
            
            self.logger.success(f"Script mis à jour vers v{version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Échec sauvegarde: {str(e)}")
            return False
    
    def update_launcher(self) -> bool:
        """Met à jour le launcher avec vérification d'intégrité"""
        self.logger.info("Téléchargement de la nouvelle version...")
        new_code = self.download_file(self.config.LAUNCHER_URL)
        
        if not new_code:
            self.logger.error("Échec du téléchargement")
            return False
        
        current_file = Path(__file__).resolve()
        backup_file = current_file.with_suffix('.py.bak')
        temp_file = current_file.with_suffix('.py.tmp')
        
        try:
            # Vérifier que le contenu téléchargé est valide
            if "LauncherScanner" not in new_code or "class Launcher" not in new_code:
                self.logger.error("Fichier téléchargé invalide")
                return False
            
            if current_file.exists():
                import shutil
                shutil.copy2(current_file, backup_file)
            
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(new_code)
            
            temp_file.replace(current_file)
            
            self.logger.success("Mise à jour du launcher réussie")
            return True
            
        except Exception as e:
            self.logger.error(f"Échec mise à jour: {str(e)}")
            
            if backup_file.exists():
                backup_file.replace(current_file)
            
            return False
    
    def force_check_updates(self) -> Dict[str, Any]:
        """
        Force une vérification complète des mises à jour
        Utile pour le mode debug ou pour forcer une mise à jour
        """
        results = {
            "launcher": {"has_update": False, "version": None},
            "script": {"has_update": False, "version": None}
        }
        
        # Vérifier le launcher
        has_update, version = self.check_launcher_update(Launcher.VERSION, force=True)
        results["launcher"] = {"has_update": has_update, "version": version}
        
        # Vérifier le script
        script_version = None
        version_file = self.config.VERSION_FILE
        if version_file.exists():
            try:
                with open(version_file, "r") as f:
                    script_version = f.read().strip()
            except:
                pass
        
        has_update, version, content = self.check_script_update(script_version, force=True)
        results["script"] = {"has_update": has_update, "version": version}
        
        return results

# ============================================================================
# LAUNCHER PRINCIPAL
# ============================================================================

class Launcher:
    """Classe principale du launcher"""
    
    VERSION = "4.4"
    
    def __init__(self):
        self.start_time = time.time()
        self.config = Config()
        self.logger = Logger(self.config.LOG_FILE)
        self.update_manager = UpdateManager(self.config, self.logger)
        self.package_manager = PackageManager(self.logger)
        
        self.script_version = None
        self.script_content = None
        self.is_restart = os.environ.get("LAUNCHER_RESTART") == "1"
    
    def initialize(self):
        self.config.BASE_DIR.mkdir(parents=True, mode=0o700, exist_ok=True)
        
        test_file = self.config.BASE_DIR / "test.tmp"
        try:
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            self.logger.error(f"Permission refusée: {str(e)}")
            sys.exit(1)
        
        self._cleanup_stale_locks()
    
    def _cleanup_stale_locks(self):
        if self.config.LOCK_FILE.exists():
            try:
                with open(self.config.LOCK_FILE, "r") as f:
                    pid = f.read().strip()
                
                if pid and pid.isdigit():
                    try:
                        os.kill(int(pid), 0)
                    except OSError:
                        self.config.LOCK_FILE.unlink()
                        self.logger.debug("Lock orphelin nettoyé")
                else:
                    self.config.LOCK_FILE.unlink()
            except:
                self.config.LOCK_FILE.unlink()
    
    def acquire_lock(self) -> bool:
        if self.config.LOCK_FILE.exists():
            return False
        
        try:
            with open(self.config.LOCK_FILE, "w") as f:
                f.write(str(os.getpid()))
            return True
        except:
            return False
    
    def release_lock(self):
        try:
            if self.config.LOCK_FILE.exists():
                self.config.LOCK_FILE.unlink()
        except:
            pass
    
    def load_script_from_cache(self) -> Optional[str]:
        if not self.config.CACHE_FILE.exists():
            self.logger.debug("Fichier cache inexistant")
            return None
        
        try:
            with open(self.config.CACHE_FILE, "r", encoding="utf-8") as f:
                encrypted = f.read().strip()
            
            if not encrypted:
                self.logger.debug("Cache vide")
                return None
            
            decrypted = self.update_manager.crypto.decrypt(encrypted)
            if decrypted:
                return decrypted
            else:
                self.logger.warn("Échec du déchiffrement du cache")
                return None
                
        except Exception as e:
            self.logger.debug(f"Erreur lecture cache: {str(e)}")
            return None
    
    def load_script_version(self) -> Optional[str]:
        if not self.config.VERSION_FILE.exists():
            return None
        
        try:
            with open(self.config.VERSION_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            return None
    
    def is_online(self) -> bool:
        hosts = [
            ("1.1.1.1", 53),
            ("8.8.8.8", 53),
            ("github.com", 80)
        ]
        
        for host, port in hosts:
            try:
                socket.setdefaulttimeout(self.config.CONNECTION_TIMEOUT)
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
                return True
            except:
                continue
        
        try:
            urllib.request.urlopen("https://1.1.1.1", timeout=self.config.CONNECTION_TIMEOUT)
            return True
        except:
            pass
        
        return False
    
    def ensure_script_available(self) -> bool:
        """S'assure que le script est disponible"""
        self.script_content = self.load_script_from_cache()
        
        if self.script_content:
            self.logger.success("Script chargé depuis le cache")
            return True
        
        if self.is_online():
            self.logger.info("Téléchargement initial du script...")
            script_content = self.update_manager.download_file(self.config.SCRIPT_URL)
            if script_content:
                try:
                    encrypted = self.update_manager.crypto.encrypt(script_content)
                    with open(self.config.CACHE_FILE, "w", encoding="utf-8") as f:
                        f.write(encrypted)
                    self.config.CACHE_FILE.chmod(0o600)
                    
                    remote_version = self.update_manager.get_remote_version(self.config.VERSION_SCRIPT_URL)
                    if remote_version:
                        with open(self.config.VERSION_FILE, "w", encoding="utf-8") as f:
                            f.write(remote_version)
                    
                    self.script_content = script_content
                    self.logger.success("Script téléchargé et mis en cache")
                    return True
                except Exception as e:
                    self.logger.error(f"Erreur lors de la mise en cache: {str(e)}")
                    self.script_content = script_content
                    return True
        
        return False
    
    def run(self):
        """Point d'entrée principal"""
        
        try:
            # Initialisation
            self.initialize()
            
            # Bannière
            Banner.show()
            
            # Vérifier si c'est un redémarrage
            is_restart = os.environ.get("LAUNCHER_RESTART") == "1"
            install_already_done = self.config.INSTALL_DONE_FILE.exists()
            
            # Mode force update via variable d'environnement
            force_update = os.environ.get("LAUNCHER_FORCE_UPDATE") == "1"
            
            # Vérification connexion
            online = self.is_online()
            if not online:
                self.logger.warn("Mode hors-ligne - utilisation du cache")
            else:
                self.logger.info("Connexion internet détectée")
            
            # Installation des dépendances (UNIQUEMENT à la première exécution)
            if online and not is_restart and not install_already_done:
                print(f"{Colors.CYAN}[INFO] Vérification et installation des dépendances...{Colors.RESET}")
                
                deps_ok = self.package_manager.install_all(self.config.REQUIRED_MODULES)
                self.package_manager.install_optional(self.config.OPTIONAL_MODULES)
                
                try:
                    self.config.INSTALL_DONE_FILE.touch()
                except:
                    pass
                
                if not deps_ok:
                    self.logger.warn("Certaines dépendances critiques manquent")
                    time.sleep(2)
            
            # Chargement de la version locale du script
            self.script_version = self.load_script_version()
            self.logger.debug(f"Version locale du script: {self.script_version or 'aucune'}")
            
            # Mise à jour du script (vérification intelligente)
            if online:
                has_update, new_version, new_script = self.update_manager.check_script_update(
                    self.script_version, 
                    force=force_update
                )
                
                if has_update and new_script:
                    self.logger.info(f"📥 Mise à jour du script v{self.script_version} → v{new_version}")
                    
                    if self.update_manager.update_script(new_script, new_version):
                        self.script_content = new_script
                        self.script_version = new_version
                        self.logger.success(f"✅ Script mis à jour vers v{new_version}")
                    else:
                        self.logger.error("❌ Échec de la mise à jour, utilisation de l'ancienne version")
                        self.script_content = self.load_script_from_cache()
                else:
                    # Charger depuis le cache
                    self.script_content = self.load_script_from_cache()
                    if self.script_content and self.script_version:
                        self.logger.debug(f"Script à jour: v{self.script_version}")
            
            # Si toujours pas de script (première exécution ou cache vide)
            if not self.script_content:
                if not self.ensure_script_available():
                    self.logger.error("Impossible d'obtenir le script")
                    sys.exit(1)
            
            # Mise à jour du launcher (seulement si pas un redémarrage)
            if online and not is_restart and self.acquire_lock():
                try:
                    has_update, new_version = self.update_manager.check_launcher_update(
                        self.VERSION,
                        force=force_update
                    )
                    
                    if has_update:
                        self.logger.info(f"📥 Mise à jour du launcher v{self.VERSION} → v{new_version}")
                        if self.update_manager.update_launcher():
                            os.environ["LAUNCHER_RESTART"] = "1"
                            self.logger.info("🔄 Redémarrage avec la nouvelle version...")
                            time.sleep(1)
                            os.execv(sys.executable, [sys.executable] + sys.argv)
                            return
                finally:
                    self.release_lock()
            
            # Exécution du script principal
            self._execute_script()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Interruption utilisateur{Colors.RESET}")
            sys.exit(0)
        except Exception as e:
            self.logger.error(f"Erreur fatale: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
            
    def _execute_script(self):
        """Exécute le script principal"""
        if not self.script_content:
            self.logger.error("Aucun script à exécuter")
            sys.exit(1)
        
        load_time = time.time() - self.start_time
        self.logger.debug(f"Chargé en {load_time:.2f}s")
        
        try:
            exec_globals = {
                '__name__': '__main__',
                '__file__': str(Path(__file__).resolve()),
                '__package__': None,
            }
            exec(self.script_content, exec_globals)
            
        except Exception as e:
            self.logger.error(f"Erreur d'exécution: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    launcher = Launcher()
    launcher.run()