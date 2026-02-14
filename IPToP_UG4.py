#!/usr/bin/env python3
"""
Script de gestion des utilisateurs VPS - Version Professionnelle Ultra-Robuste
Conçu par DjahNoDead - Version 2.0
"""

import os
import sys
import subprocess
import getpass
import json
import hashlib
import logging
import re
import shutil
import signal
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
from typing import Dict, List, Optional, Tuple, Any, Union
from functools import wraps
import contextlib

# ============================================================================
# CONFIGURATION AVANCÉE
# ============================================================================

class Config:
    """Configuration centralisée du script"""
    
    # Chemins
    USER_DATA_FILE = os.path.expanduser("~/.user_management_data.json")
    USER_DATA_BACKUP_DIR = os.path.expanduser("~/.user_management_backups")
    LOG_DIR = "/var/log"
    FALLBACK_LOG_DIR = os.path.expanduser("~/.local/log")
    
    # Groupes système
    SSH_GROUP = "ssh-users"
    ADMIN_GROUP = "sudo"
    
    # Docker
    DOCKER_IMAGE = "ubuntu:latest"
    DOCKER_BASE_IMAGE = "ubuntu:22.04"  # Image plus stable
    
    # Sécurité
    MIN_PASSWORD_LENGTH = 8
    BACKUP_RETENTION_DAYS = 7
    DEFAULT_EXPIRATION_DAYS = 30
    MAX_LOGIN_ATTEMPTS = 3
    SESSION_TIMEOUT = 300  # secondes
    
    # Regex patterns
    USERNAME_PATTERN = r'^[a-z_][a-z0-9_-]*$'
    SSH_KEY_PATTERNS = [
        r'ssh-rsa AAAA[0-9A-Za-z+/]+[=]{0,3}( [^@]+@[^@]+)?',
        r'ecdsa-sha2-nistp256 AAAA[0-9A-Za-z+/]+[=]{0,3}( [^@]+@[^@]+)?',
        r'ssh-ed25519 AAAA[0-9A-Za-z+/]+[=]{0,3}( [^@]+@[^@]+)?'
    ]
    
    DATE_FORMATS = [
        '%Y-%m-%d',    # 2024-01-31
        '%d/%m/%Y',    # 31/01/2024
        '%d-%m-%Y',    # 31-01-2024
        '%d.%m.%Y',    # 31.01.2024
    ]
    
    # Messages
    MSG = {
        'root_required': "Ce script doit être exécuté en tant que root!",
        'sudo_required': "Utilisez: sudo {}",
        'keyboard_interrupt': "\n\nInterruption par l'utilisateur. Au revoir!",
        'goodbye': "\nMerci d'avoir utilisé ce script!"
    }


# ============================================================================
# GESTIONNAIRE DE COULEURS
# ============================================================================

class Colors:
    """Gestionnaire de couleurs ANSI avec fallback"""
    
    _colors = {
        'header': '\033[95m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'bold': '\033[1m',
        'underline': '\033[4m',
        'end': '\033[0m'
    }
    
    # Désactiver les couleurs si non supportées
    _no_color = not sys.stdout.isatty() or os.environ.get('NO_COLOR')
    
    @classmethod
    def get(cls, color_name: str) -> str:
        """Retourne le code couleur ou chaîne vide"""
        if cls._no_color:
            return ''
        return cls._colors.get(color_name, '')
    
    @classmethod
    def wrap(cls, text: str, *color_names: str) -> str:
        """Encapsule le texte avec les couleurs spécifiées"""
        if cls._no_color:
            return text
        colors = ''.join(cls.get(c) for c in color_names if cls.get(c))
        return f"{colors}{text}{cls.get('end')}"


# ============================================================================
# GESTIONNAIRE DE LOGGING ROBUSTE
# ============================================================================

class RobustLogger:
    """Logger avec fallback multiple"""
    
    def __init__(self, name: str = 'UserManager'):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure le logging avec plusieurs handlers"""
        self.logger.setLevel(logging.DEBUG)
        
        # Formatteur
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler fichier avec fallback
        file_handler = self._create_file_handler(formatter)
        if file_handler:
            self.logger.addHandler(file_handler)
        
        # Handler console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
    
    def _create_file_handler(self, formatter):
        """Crée un handler fichier avec fallback"""
        # Essayer /var/log
        for log_dir in [Config.LOG_DIR, Config.FALLBACK_LOG_DIR]:
            try:
                Path(log_dir).mkdir(parents=True, exist_ok=True)
                log_file = Path(log_dir) / 'user_manager.log'
                
                handler = logging.FileHandler(log_file)
                handler.setFormatter(formatter)
                handler.setLevel(logging.DEBUG)
                
                # Test d'écriture
                with open(log_file, 'a'):
                    pass
                
                return handler
            except (PermissionError, OSError):
                continue
        
        return None
    
    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        self.logger.exception(msg, *args, **kwargs)


# ============================================================================
# DÉCORATEURS ET UTILITAIRES
# ============================================================================

class UserManagerError(Exception):
    """Exception personnalisée pour UserManager"""
    pass


def requires_root(func):
    """Décorateur pour vérifier les privilèges root"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if os.geteuid() != 0:
            print(Colors.wrap(Config.MSG['root_required'], 'red', 'bold'))
            print(Colors.wrap(Config.MSG['sudo_required'].format(sys.argv[0]), 'yellow'))
            sys.exit(1)
        return func(*args, **kwargs)
    return wrapper


def handle_exceptions(func):
    """Décorateur pour la gestion centralisée des exceptions"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except KeyboardInterrupt:
            print(Colors.wrap(Config.MSG['keyboard_interrupt'], 'yellow'))
            sys.exit(0)
        except UserManagerError as e:
            self.print_error(str(e))
            return False
        except Exception as e:
            self.print_error(f"Erreur inattendue: {e}")
            self.logger.exception("Exception non gérée")
            if self.debug_mode:
                traceback.print_exc()
            return False
    return wrapper


def timeout(seconds: int):
    """Décorateur pour timeout d'exécution"""
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(f"Fonction {func.__name__} timeout après {seconds}s")
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return wrapper
    return decorator


# ============================================================================
# GESTIONNAIRE DE CONTEXTE
# ============================================================================

@contextlib.contextmanager
def temporary_umask(umask):
    """Context manager pour changer temporairement l'umask"""
    old_umask = os.umask(umask)
    try:
        yield
    finally:
        os.umask(old_umask)


@contextlib.contextmanager
def working_directory(path):
    """Context manager pour changer temporairement de répertoire"""
    old_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)


# ============================================================================
# VALIDATEURS
# ============================================================================

class Validators:
    """Collection de validateurs"""
    
    @staticmethod
    def username(username: str) -> Tuple[bool, str]:
        """Valide un nom d'utilisateur"""
        if not username:
            return False, "Le nom d'utilisateur ne peut pas être vide"
        
        if len(username) < 3:
            return False, "Le nom d'utilisateur doit contenir au moins 3 caractères"
        
        if len(username) > 32:
            return False, "Le nom d'utilisateur ne peut pas dépasser 32 caractères"
        
        if not re.match(Config.USERNAME_PATTERN, username):
            return False, "Le nom d'utilisateur ne peut contenir que des lettres minuscules, chiffres, tirets et underscores"
        
        return True, "Nom d'utilisateur valide"
    
    @staticmethod
    def password(password: str) -> Tuple[bool, str]:
        """Valide un mot de passe"""
        if not password:
            return True, "Aucun mot de passe"
        
        if len(password) < Config.MIN_PASSWORD_LENGTH:
            return False, f"Le mot de passe doit contenir au moins {Config.MIN_PASSWORD_LENGTH} caractères"
        
        # Score de complexité
        score = 0
        if any(c.isdigit() for c in password):
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.islower() for c in password):
            score += 1
        if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            score += 1
        
        if score < 3:
            return False, "Le mot de passe n'est pas assez complexe (utilisez minuscules, majuscules, chiffres et symboles)"
        
        return True, "Mot de passe valide"
    
    @staticmethod
    def ssh_key(ssh_key: str) -> Tuple[bool, str]:
        """Valide une clé SSH"""
        if not ssh_key:
            return True, "Aucune clé SSH"
        
        ssh_key = ssh_key.strip()
        
        for pattern in Config.SSH_KEY_PATTERNS:
            if re.match(pattern, ssh_key):
                return True, "Clé SSH valide"
        
        return False, "Format de clé SSH invalide"
    
    @staticmethod
    def expiration_date(date_str: str) -> Tuple[bool, str, Optional[datetime]]:
        """Valide et parse une date d'expiration"""
        if not date_str:
            default_date = datetime.now() + timedelta(days=Config.DEFAULT_EXPIRATION_DAYS)
            return True, f"Date par défaut: {default_date.strftime('%Y-%m-%d')}", default_date
        
        for fmt in Config.DATE_FORMATS:
            try:
                date = datetime.strptime(date_str, fmt)
                
                if date < datetime.now():
                    return False, "La date ne peut pas être dans le passé", None
                
                if date > datetime.now() + timedelta(days=365*5):  # Max 5 ans
                    return False, "La date ne peut pas dépasser 5 ans", None
                
                return True, f"Date valide: {date.strftime('%Y-%m-%d')}", date
            except ValueError:
                continue
        
        return False, f"Format invalide. Utilisez: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY ou DD.MM.YYYY", None
    
    @staticmethod
    def port(port_str: str) -> Tuple[bool, Optional[int]]:
        """Valide un numéro de port"""
        try:
            port = int(port_str)
            if 1 <= port <= 65535:
                return True, port
            return False, None
        except ValueError:
            return False, None


# ============================================================================
# GESTIONNAIRE SYSTÈME
# ============================================================================

class SystemManager:
    """Gestionnaire des opérations système"""
    
    def __init__(self, logger: RobustLogger):
        self.logger = logger
    
    @staticmethod
    def is_termux() -> bool:
        """Vérifie si on est dans Termux"""
        return os.path.exists('/data/data/com.termux/files/usr')
    
    def is_package_installed(self, pkg_name: str) -> bool:
        """Vérifie si un paquet est installé"""
        try:
            if self.is_termux():
                result = subprocess.run(['pkg', 'list-installed', pkg_name], 
                                      capture_output=True, text=True)
                return pkg_name in result.stdout
            else:
                subprocess.run(['dpkg', '-s', pkg_name], 
                             check=True, capture_output=True)
                return True
        except subprocess.CalledProcessError:
            return False
    
    def install_packages(self, packages: List[str]) -> bool:
        """Installe des paquets système"""
        if self.is_termux():
            cmd = ['pkg', 'install', '-y'] + packages
        else:
            cmd = ['apt-get', 'install', '-y'] + packages
        
        try:
            subprocess.run(['apt-get', 'update'] if not self.is_termux() else ['pkg', 'update'],
                         check=True, capture_output=True)
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Échec installation: {e}")
            return False
    
    def user_exists(self, username: str) -> bool:
        """Vérifie si un utilisateur existe"""
        try:
            subprocess.run(['id', username], check=True, 
                         capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def group_exists(self, group_name: str) -> bool:
        """Vérifie si un groupe existe"""
        try:
            subprocess.run(['getent', 'group', group_name], 
                         check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def create_group(self, group_name: str) -> bool:
        """Crée un groupe système"""
        try:
            subprocess.run(['groupadd', group_name], 
                         check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Échec création groupe {group_name}: {e}")
            return False


# ============================================================================
# GESTIONNAIRE DOCKER
# ============================================================================

class DockerManager:
    """Gestionnaire des opérations Docker"""
    
    def __init__(self, logger: RobustLogger):
        self.logger = logger
        self.client = None
        self.available = False
        self._init_docker()
    
    def _init_docker(self):
        """Initialise la connexion Docker"""
        try:
            # Tentative d'import du module
            import docker
            
            # Tentative de connexion
            self.client = docker.from_env()
            self.client.ping()
            self.available = True
            self.logger.info("Docker disponible")
        except ImportError:
            self.logger.warning("Module docker non installé")
        except Exception as e:
            self.logger.warning(f"Docker non disponible: {e}")
    
    def cleanup_container(self, container_name: str) -> bool:
        """Nettoie un conteneur existant"""
        if not self.available:
            return False
        
        try:
            container = self.client.containers.get(container_name)
            
            # Arrêt graceful
            try:
                container.stop(timeout=10)
            except:
                pass
            
            # Suppression
            try:
                container.remove(force=True)
            except:
                pass
            
            return True
        except:
            return False
    
    def create_container(self, username: str, password: str, 
                        is_admin: bool, ssh_key: Optional[str]) -> Tuple[bool, Optional[str], Optional[int]]:
        """Crée un conteneur pour un utilisateur"""
        if not self.available:
            return False, None, None
        
        container_name = f"user_{username}"
        self.cleanup_container(container_name)
        
        try:
            # Préparation du répertoire home
            host_home = Path(f"/home/{username}")
            if host_home.exists():
                shutil.rmtree(host_home)
            host_home.mkdir(mode=0o755, parents=True)
            
            # Construction des commandes
            setup_cmds = self._build_setup_commands(username, password, is_admin, ssh_key)
            
            # Création du conteneur
            container = self.client.containers.run(
                Config.DOCKER_BASE_IMAGE,
                name=container_name,
                detach=True,
                tty=True,
                hostname=username,
                user="root",
                volumes={
                    str(host_home): {'bind': f'/home/{username}', 'mode': 'rw'}
                },
                command=f"/bin/sh -c \"{setup_cmds}\"",
                cap_drop=['ALL'],
                security_opt=['no-new-privileges'],
                ports={'22/tcp': None},
                restart_policy={"Name": "unless-stopped"}
            )
            
            # Attente du démarrage
            for _ in range(30):
                container.reload()
                if container.status == 'running':
                    break
                sleep(1)
            else:
                raise Exception("Timeout démarrage conteneur")
            
            # Récupération du port SSH
            container.reload()
            ssh_port = None
            port_info = container.attrs['NetworkSettings']['Ports'].get('22/tcp')
            if port_info and len(port_info) > 0:
                ssh_port = int(port_info[0]['HostPort'])
            
            return True, container.id[:12], ssh_port
            
        except Exception as e:
            self.logger.error(f"Erreur création conteneur: {e}")
            self.cleanup_container(container_name)
            return False, None, None
    
    def _build_setup_commands(self, username: str, password: str, 
                            is_admin: bool, ssh_key: Optional[str]) -> str:
        """Construit les commandes de configuration"""
        cmds = []
        
        # Installation des paquets essentiels
        cmds.extend([
            "apt-get update -qq",
            "apt-get install -y openssh-server sudo >/dev/null 2>&1"
        ])
        
        # Création utilisateur
        cmds.extend([
            f"useradd -m -s /bin/bash {username}",
            f"echo '{username}:{password}' | chpasswd"
        ])
        
        # Configuration sudo
        if is_admin:
            cmds.extend([
                f"usermod -aG sudo {username}",
                f"echo '{username} ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/{username}",
                f"chmod 440 /etc/sudoers.d/{username}"
            ])
        
        # Configuration SSH
        if ssh_key:
            cmds.extend([
                f"mkdir -p /home/{username}/.ssh",
                f"echo '{ssh_key}' > /home/{username}/.ssh/authorized_keys",
                f"chmod 700 /home/{username}/.ssh",
                f"chmod 600 /home/{username}/.ssh/authorized_keys",
                f"chown -R {username}:{username} /home/{username}/.ssh"
            ])
        
        # Démarrage SSH
        cmds.extend([
            "mkdir -p /run/sshd",
            "chmod 0755 /run/sshd",
            "/usr/sbin/sshd -D"
        ])
        
        return " && ".join(cmds)


# ============================================================================
# GESTIONNAIRE DE SAUVEGARDE
# ============================================================================

class BackupManager:
    """Gestionnaire des sauvegardes"""
    
    def __init__(self, logger: RobustLogger):
        self.logger = logger
        self.backup_dir = Path(Config.USER_DATA_BACKUP_DIR)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, data_file: str) -> bool:
        """Crée une sauvegarde"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"user_data_backup_{timestamp}.json"
        
        try:
            shutil.copy2(data_file, backup_file)
            self.logger.info(f"Sauvegarde créée: {backup_file}")
            self._cleanup_old()
            return True
        except Exception as e:
            self.logger.error(f"Échec sauvegarde: {e}")
            return False
    
    def _cleanup_old(self):
        """Nettoie les anciennes sauvegardes"""
        now = datetime.now()
        
        for backup_file in self.backup_dir.glob("user_data_backup_*.json"):
            try:
                # Extraction date du nom
                date_str = backup_file.stem.replace("user_data_backup_", "")
                file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                
                # Suppression si trop vieux
                if (now - file_date).days > Config.BACKUP_RETENTION_DAYS:
                    backup_file.unlink()
                    self.logger.info(f"Ancienne sauvegarde supprimée: {backup_file}")
            except:
                continue
    
    def list_backups(self) -> List[Path]:
        """Liste les sauvegardes disponibles"""
        backups = sorted(
            self.backup_dir.glob("user_data_backup_*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        return backups
    
    def restore_backup(self, backup_file: Path, target_file: str) -> bool:
        """Restaure une sauvegarde"""
        try:
            shutil.copy2(backup_file, target_file)
            self.logger.info(f"Restauration depuis {backup_file}")
            return True
        except Exception as e:
            self.logger.error(f"Échec restauration: {e}")
            return False


# ============================================================================
# CLASSE PRINCIPALE
# ============================================================================

class UserManager:
    """Gestionnaire principal des utilisateurs"""
    
    def __init__(self, debug: bool = False):
        self.debug_mode = debug
        self.logger = RobustLogger()
        self.system = SystemManager(self.logger)
        self.docker = DockerManager(self.logger)
        self.backup = BackupManager(self.logger)
        self.user_data: Dict[str, Any] = {}
        self.docker_ports: Dict[str, int] = {}
        
        self._initialize()
    
    def _initialize(self):
        """Initialisation du gestionnaire"""
        self._setup_groups()
        self._load_user_data()
    
    def _setup_groups(self):
        """Configuration des groupes système"""
        for group in [Config.SSH_GROUP, Config.ADMIN_GROUP]:
            if not self.system.group_exists(group):
                self.logger.info(f"Création du groupe {group}")
                if not self.system.create_group(group):
                    self.logger.warning(f"Impossible de créer le groupe {group}")
    
    def _load_user_data(self):
        """Charge les données utilisateur"""
        try:
            with open(Config.USER_DATA_FILE, 'r') as f:
                self.user_data = json.load(f)
            self.logger.info("Données utilisateur chargées")
        except FileNotFoundError:
            self.user_data = {}
            self.logger.info("Nouveau fichier de données")
        except json.JSONDecodeError as e:
            self.logger.error(f"Erreur JSON: {e}")
            self.user_data = {}
    
    def _save_user_data(self):
        """Sauvegarde les données utilisateur"""
        # Sauvegarde automatique
        if os.path.exists(Config.USER_DATA_FILE):
            self.backup.create_backup(Config.USER_DATA_FILE)
        
        try:
            with open(Config.USER_DATA_FILE, 'w') as f:
                json.dump(self.user_data, f, indent=4, default=str)
            self.logger.info("Données utilisateur sauvegardées")
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde: {e}")
    
    # ========================================================================
    # MÉTHODES D'AFFICHAGE
    # ========================================================================
    
    def print_header(self):
        """Affiche l'en-tête"""
        os.system('clear' if os.name == 'posix' else 'cls')
        print(Colors.wrap('='*60, 'header'))
        print(Colors.wrap('GESTION DES UTILISATEURS VPS - V2.0', 'bold', 'header'))
        print(Colors.wrap('='*60, 'header'))
        print(Colors.wrap('Conçu par DjahNoDead', 'blue'))
        print()
    
    def print_success(self, message: str):
        """Message de succès"""
        print(Colors.wrap(f'[✓] {message}', 'green'))
        self.logger.info(message)
    
    def print_error(self, message: str):
        """Message d'erreur"""
        print(Colors.wrap(f'[✗] {message}', 'red'))
        self.logger.error(message)
    
    def print_warning(self, message: str):
        """Message d'avertissement"""
        print(Colors.wrap(f'[!] {message}', 'yellow'))
        self.logger.warning(message)
    
    def print_info(self, message: str):
        """Message d'information"""
        print(Colors.wrap(f'[i] {message}', 'cyan'))
        self.logger.info(message)
    
    # ========================================================================
    # MÉTHODES DE VALIDATION
    # ========================================================================
    
    @handle_exceptions
    def validate_username(self, username: str) -> Tuple[bool, str]:
        """Valide un nom d'utilisateur"""
        valid, msg = Validators.username(username)
        if valid and self.system.user_exists(username):
            return False, f"L'utilisateur {username} existe déjà"
        return valid, msg
    
    @handle_exceptions
    def validate_password(self, password: str) -> Tuple[bool, str]:
        """Valide un mot de passe"""
        return Validators.password(password)
    
    @handle_exceptions
    def validate_ssh_key(self, ssh_key: str) -> Tuple[bool, str]:
        """Valide une clé SSH"""
        return Validators.ssh_key(ssh_key)
    
    @handle_exceptions
    def validate_expiration(self, date_str: str) -> Tuple[bool, str, Optional[datetime]]:
        """Valide une date d'expiration"""
        return Validators.expiration_date(date_str)
    
    # ========================================================================
    # MÉTHODES PRINCIPALES
    # ========================================================================
    
    @handle_exceptions
    @requires_root
    def create_user(self, username: str, password: Optional[str] = None,
                   is_admin: bool = False, ssh_key: Optional[str] = None,
                   dockerized: bool = False, 
                   expiration_date: Optional[datetime] = None) -> bool:
        """Crée un nouvel utilisateur"""
        
        # Validation préalable
        valid, msg = self.validate_username(username)
        if not valid:
            self.print_error(msg)
            return False
        
        if password:
            valid, msg = self.validate_password(password)
            if not valid:
                self.print_error(msg)
                return False
        
        if ssh_key:
            valid, msg = self.validate_ssh_key(ssh_key)
            if not valid:
                self.print_error(msg)
                return False
        
        # Date d'expiration par défaut
        if not expiration_date:
            expiration_date = datetime.now() + timedelta(days=Config.DEFAULT_EXPIRATION_DAYS)
        
        try:
            container_id = None
            ssh_port = None
            
            if dockerized and self.docker.available:
                # Création Docker
                success, container_id, ssh_port = self.docker.create_container(
                    username, password or '', is_admin, ssh_key
                )
                if not success:
                    self.print_error("Échec création conteneur Docker")
                    return False
            else:
                # Création standard
                self._create_standard_user(username, password, is_admin, ssh_key)
            
            # Sauvegarde des données
            self.user_data[username] = {
                'is_admin': is_admin,
                'has_ssh_key': bool(ssh_key),
                'dockerized': dockerized and self.docker.available,
                'created_at': datetime.now().isoformat(),
                'expiration_date': expiration_date.isoformat(),
                'container_id': container_id,
                'ssh_port': ssh_port
            }
            
            if ssh_port:
                self.docker_ports[username] = ssh_port
            
            self._save_user_data()
            
            # Affichage succès
            self.print_success(f"Utilisateur {username} créé avec succès!")
            self._display_user_info(username, dockerized and self.docker.available, ssh_port, expiration_date)
            
            return True
            
        except Exception as e:
            self.print_error(f"Erreur création: {e}")
            self.logger.exception("Détails erreur création")
            return False
    
    def _create_standard_user(self, username: str, password: Optional[str],
                             is_admin: bool, ssh_key: Optional[str]):
        """Crée un utilisateur standard"""
        
        # Création utilisateur
        subprocess.run(
            ['adduser', '--disabled-password', '--gecos', '""', username],
            check=True, capture_output=True
        )
        
        # Mot de passe
        if password:
            proc = subprocess.Popen(['chpasswd'], stdin=subprocess.PIPE, 
                                  universal_newlines=True)
            proc.communicate(f"{username}:{password}")
        
        # Groupes
        groups = [Config.SSH_GROUP]
        if is_admin:
            groups.append(Config.ADMIN_GROUP)
        
        if groups:
            subprocess.run(
                ['usermod', '-aG', ','.join(groups), username],
                check=True, capture_output=True
            )
        
        # Clé SSH
        if ssh_key:
            ssh_dir = Path(f"/home/{username}/.ssh")
            ssh_dir.mkdir(mode=0o700, exist_ok=True)
            
            auth_keys = ssh_dir / "authorized_keys"
            auth_keys.write_text(ssh_key)
            auth_keys.chmod(0o600)
            
            subprocess.run(
                ['chown', '-R', f'{username}:{username}', str(ssh_dir)],
                check=True, capture_output=True
            )
    
    def _display_user_info(self, username: str, dockerized: bool, 
                          ssh_port: Optional[int], expiration_date: datetime):
        """Affiche les informations de l'utilisateur"""
        print()
        print(Colors.wrap('INFORMATIONS DE CONNEXION:', 'underline'))
        
        if dockerized and ssh_port:
            print(f"  SSH: ssh -p {ssh_port} {username}@localhost")
        else:
            print(f"  SSH: ssh {username}@localhost")
        
        days = (expiration_date - datetime.now()).days
        print(f"  Expiration: {expiration_date.strftime('%Y-%m-%d')} ({days} jours)")
    
    @handle_exceptions
    @requires_root
    def delete_user(self, username: str) -> bool:
        """Supprime un utilisateur"""
        
        if username not in self.user_data:
            self.print_error(f"Utilisateur {username} non trouvé")
            return False
        
        # Suppression Docker
        if self.user_data[username].get('dockerized'):
            container_name = f"user_{username}"
            self.docker.cleanup_container(container_name)
        
        # Suppression système
        try:
            subprocess.run(['userdel', '-r', username], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            self.print_warning(f"Suppression système: {e}")
        
        # Nettoyage données
        del self.user_data[username]
        self.docker_ports.pop(username, None)
        self._save_user_data()
        
        self.print_success(f"Utilisateur {username} supprimé")
        return True
    
    def list_users(self):
        """Liste les utilisateurs"""
        if not self.user_data:
            self.print_warning("Aucun utilisateur")
            return
        
        print()
        print(Colors.wrap('UTILISATEURS GÉRÉS:', 'underline'))
        print()
        
        headers = ['Nom', 'Admin', 'Type', 'SSH', 'Expiration', 'Jours']
        print(Colors.wrap(f"{headers[0]:<15} {headers[1]:<6} {headers[2]:<8} "
                         f"{headers[3]:<4} {headers[4]:<12} {headers[5]:<6}", 'bold'))
        print('-' * 65)
        
        now = datetime.now()
        
        for username, data in sorted(self.user_data.items()):
            admin = '✓' if data.get('is_admin') else '✗'
            u_type = 'Docker' if data.get('dockerized') else 'Std'
            ssh = '✓' if data.get('has_ssh_key') else '✗'
            
            exp_date = datetime.fromisoformat(data.get('expiration_date', now.isoformat()))
            days = (exp_date - now).days
            exp_str = exp_date.strftime('%Y-%m-%d')
            
            # Coloration selon expiration
            if days < 0:
                exp_str = Colors.wrap(exp_str, 'red')
                days_str = Colors.wrap(str(days), 'red')
            elif days <= 7:
                exp_str = Colors.wrap(exp_str, 'yellow')
                days_str = Colors.wrap(str(days), 'yellow')
            else:
                days_str = str(days)
            
            print(f"{username:<15} {admin:<6} {u_type:<8} {ssh:<4} "
                  f"{exp_str:<12} {days_str:<6}")
    
    def check_expirations(self):
        """Vérifie les expirations"""
        now = datetime.now()
        expired = []
        expiring = []
        
        for username, data in self.user_data.items():
            exp_date = datetime.fromisoformat(data.get('expiration_date', now.isoformat()))
            days = (exp_date - now).days
            
            if days < 0:
                expired.append((username, exp_date, -days))
            elif days <= 7:
                expiring.append((username, exp_date, days))
        
        if expired:
            print(Colors.wrap('\nUTILISATEURS EXPIRÉS:', 'red', 'bold'))
            for u, d, days in expired:
                print(f"  {u}: expiré depuis {days} jours (le {d.strftime('%Y-%m-%d')})")
        
        if expiring:
            print(Colors.wrap('\nEXPIRENT BIENTÔT:', 'yellow', 'bold'))
            for u, d, days in expiring:
                print(f"  {u}: expire dans {days} jours (le {d.strftime('%Y-%m-%d')})")
        
        if not expired and not expiring:
            self.print_success("Aucune expiration à signaler")
    
    # ========================================================================
    # INTERFACES INTERACTIVES
    # ========================================================================
    
    @handle_exceptions
    def interactive_create(self):
        """Interface interactive de création"""
        self.print_header()
        print(Colors.wrap('CRÉATION NOUVEL UTILISATEUR', 'underline'))
        print()
        
        # Nom d'utilisateur
        while True:
            username = input(Colors.wrap('Nom d\'utilisateur: ', 'bold')).strip()
            valid, msg = self.validate_username(username)
            if valid:
                break
            self.print_error(msg)
        
        # Mot de passe
        password = None
        while True:
            use_password = input(Colors.wrap('Ajouter mot de passe? (o/n): ', 'bold')).lower() == 'o'
            if use_password:
                password = getpass.getpass(Colors.wrap('Mot de passe: ', 'bold'))
                valid, msg = self.validate_password(password)
                if not valid:
                    self.print_error(msg)
                    continue
                
                confirm = getpass.getpass(Colors.wrap('Confirmation: ', 'bold'))
                if password != confirm:
                    self.print_error("Les mots de passe ne correspondent pas")
                    continue
                break
            else:
                break
        
        # Clé SSH
        ssh_key = None
        use_ssh = input(Colors.wrap('Ajouter clé SSH? (o/n): ', 'bold')).lower() == 'o'
        if use_ssh:
            print(Colors.wrap('Collez votre clé publique SSH:', 'yellow'))
            ssh_key = sys.stdin.readline().strip()
            valid, msg = self.validate_ssh_key(ssh_key)
            if not valid:
                self.print_error(msg)
                return
        
        if not password and not ssh_key:
            self.print_error("Au moins un mode d'authentification requis")
            return
        
        # Droits admin
        is_admin = input(Colors.wrap('Droits administrateur? (o/n): ', 'bold')).lower() == 'o'
        
        # Docker
        dockerized = False
        if self.docker.available:
            dockerized = input(Colors.wrap('Conteneur Docker? (o/n): ', 'bold')).lower() == 'o'
        
        # Date expiration
        expiration_date = None
        use_custom = input(Colors.wrap('Date expiration personnalisée? (o/n): ', 'bold')).lower() == 'o'
        if use_custom:
            print(Colors.wrap('Date (YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY):', 'yellow'))
            date_str = input().strip()
            valid, msg, exp_date = self.validate_expiration(date_str)
            if not valid:
                self.print_error(msg)
                return
            expiration_date = exp_date
        
        # Confirmation
        print()
        print(Colors.wrap('RÉSUMÉ:', 'bold'))
        print(f"  Utilisateur: {Colors.wrap(username, 'blue')}")
        print(f"  Admin: {Colors.wrap('Oui' if is_admin else 'Non', 'blue')}")
        print(f"  Type: {Colors.wrap('Docker' if dockerized else 'Standard', 'blue')}")
        print(f"  Auth: {Colors.wrap('Password+SSH' if password and ssh_key else 'Password' if password else 'SSH', 'blue')}")
        
        if expiration_date:
            days = (expiration_date - datetime.now()).days
            print(f"  Expiration: {Colors.wrap(expiration_date.strftime('%Y-%m-%d'), 'blue')} ({days} jours)")
        
        confirm = input(Colors.wrap('\nConfirmer création? (o/n): ', 'bold')).lower() == 'o'
        if confirm:
            self.create_user(username, password, is_admin, ssh_key, dockerized, expiration_date)
        
        input(Colors.wrap('\nAppuyez sur Entrée pour continuer...', 'cyan'))
    
    @handle_exceptions
    def interactive_delete(self):
        """Interface interactive de suppression"""
        self.print_header()
        print(Colors.wrap('SUPPRESSION UTILISATEUR', 'underline'))
        print()
        
        if not self.user_data:
            self.print_warning("Aucun utilisateur")
            input(Colors.wrap('\nAppuyez sur Entrée...', 'cyan'))
            return
        
        self.list_users()
        username = input(Colors.wrap('\nNom à supprimer: ', 'bold')).strip()
        
        if username not in self.user_data:
            self.print_error("Utilisateur non trouvé")
            input(Colors.wrap('\nAppuyez sur Entrée...', 'cyan'))
            return
        
        confirm = input(Colors.wrap(f'Supprimer {username}? (o/n): ', 'bold')).lower() == 'o'
        if confirm:
            self.delete_user(username)
        
        input(Colors.wrap('\nAppuyez sur Entrée pour continuer...', 'cyan'))
    
    @handle_exceptions
    def interactive_modify(self):
        """Interface interactive de modification"""
        self.print_header()
        print(Colors.wrap('MODIFICATION UTILISATEUR', 'underline'))
        print()
        
        if not self.user_data:
            self.print_warning("Aucun utilisateur")
            input(Colors.wrap('\nAppuyez sur Entrée...', 'cyan'))
            return
        
        self.list_users()
        username = input(Colors.wrap('\nNom à modifier: ', 'bold')).strip()
        
        if username not in self.user_data:
            self.print_error("Utilisateur non trouvé")
            input(Colors.wrap('\nAppuyez sur Entrée...', 'cyan'))
            return
        
        data = self.user_data[username]
        
        print()
        print(Colors.wrap('OPTIONS:', 'bold'))
        print("1. Changer mot de passe")
        print("2. Changer clé SSH")
        print("3. Changer droits admin")
        print("4. Changer expiration")
        print("5. Annuler")
        
        choice = input(Colors.wrap('\nChoix (1-5): ', 'bold')).strip()
        
        if choice == '1':
            self._modify_password(username)
        elif choice == '2':
            self._modify_ssh_key(username)
        elif choice == '3':
            self._modify_admin(username, data.get('is_admin', False))
        elif choice == '4':
            self._modify_expiration(username)
        else:
            return
        
        input(Colors.wrap('\nAppuyez sur Entrée pour continuer...', 'cyan'))
    
    def _modify_password(self, username: str):
        """Modifie le mot de passe"""
        password = getpass.getpass(Colors.wrap('Nouveau mot de passe: ', 'bold'))
        valid, msg = self.validate_password(password)
        if not valid:
            self.print_error(msg)
            return
        
        confirm = getpass.getpass(Colors.wrap('Confirmation: ', 'bold'))
        if password != confirm:
            self.print_error("Les mots de passe ne correspondent pas")
            return
        
        try:
            proc = subprocess.Popen(['chpasswd'], stdin=subprocess.PIPE, 
                                  universal_newlines=True)
            proc.communicate(f"{username}:{password}")
            self.print_success("Mot de passe modifié")
        except Exception as e:
            self.print_error(f"Erreur: {e}")
    
    def _modify_ssh_key(self, username: str):
        """Modifie la clé SSH"""
        print(Colors.wrap('Nouvelle clé publique SSH:', 'yellow'))
        ssh_key = sys.stdin.readline().strip()
        
        valid, msg = self.validate_ssh_key(ssh_key)
        if not valid:
            self.print_error(msg)
            return
        
        try:
            ssh_dir = Path(f"/home/{username}/.ssh")
            ssh_dir.mkdir(mode=0o700, exist_ok=True)
            
            auth_keys = ssh_dir / "authorized_keys"
            auth_keys.write_text(ssh_key)
            auth_keys.chmod(0o600)
            
            self.user_data[username]['has_ssh_key'] = True
            self._save_user_data()
            
            self.print_success("Clé SSH modifiée")
        except Exception as e:
            self.print_error(f"Erreur: {e}")
    
    def _modify_admin(self, username: str, current: bool):
        """Modifie les droits admin"""
        new_status = not current
        
        try:
            if new_status:
                subprocess.run(['usermod', '-aG', Config.ADMIN_GROUP, username],
                             check=True, capture_output=True)
                self.print_success("Droits admin accordés")
            else:
                subprocess.run(['gpasswd', '-d', username, Config.ADMIN_GROUP],
                             check=True, capture_output=True)
                self.print_success("Droits admin retirés")
            
            self.user_data[username]['is_admin'] = new_status
            self._save_user_data()
        except Exception as e:
            self.print_error(f"Erreur: {e}")
    
    def _modify_expiration(self, username: str):
        """Modifie la date d'expiration"""
        print(Colors.wrap('Nouvelle date (YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY):', 'yellow'))
        date_str = input().strip()
        
        valid, msg, exp_date = self.validate_expiration(date_str)
        if not valid:
            self.print_error(msg)
            return
        
        self.user_data[username]['expiration_date'] = exp_date.isoformat()
        self._save_user_data()
        self.print_success(f"Expiration modifiée: {exp_date.strftime('%Y-%m-%d')}")
    
    @handle_exceptions
    def interactive_backup(self):
        """Interface de sauvegarde"""
        self.print_header()
        print(Colors.wrap('SAUVEGARDE', 'underline'))
        print()
        
        if self.backup.create_backup(Config.USER_DATA_FILE):
            self.print_success("Sauvegarde effectuée")
        else:
            self.print_error("Échec sauvegarde")
        
        input(Colors.wrap('\nAppuyez sur Entrée...', 'cyan'))
    
    @handle_exceptions
    def interactive_restore(self):
        """Interface de restauration"""
        self.print_header()
        print(Colors.wrap('RESTAURATION', 'underline'))
        print()
        
        backups = self.backup.list_backups()
        
        if not backups:
            self.print_warning("Aucune sauvegarde")
            input(Colors.wrap('\nAppuyez sur Entrée...', 'cyan'))
            return
        
        print(Colors.wrap('SAUVEGARDES DISPONIBLES:', 'bold'))
        for i, backup in enumerate(backups[:10], 1):
            size = backup.stat().st_size
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"{i:2}. {backup.name} ({size} octets) - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        choice = input(Colors.wrap('\nNuméro à restaurer (0 pour annuler): ', 'bold')).strip()
        
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(backups):
                confirm = input(Colors.wrap(f'Restaurer {backups[idx].name}? (o/n): ', 'bold')).lower() == 'o'
                if confirm:
                    if self.backup.restore_backup(backups[idx], Config.USER_DATA_FILE):
                        self._load_user_data()
                        self.print_success("Restauration effectuée")
                    else:
                        self.print_error("Échec restauration")
        
        input(Colors.wrap('\nAppuyez sur Entrée...', 'cyan'))
    
    # ========================================================================
    # MENU PRINCIPAL
    # ========================================================================
    
    @requires_root
    def run(self):
        """Lance le menu principal"""
        while True:
            self.print_header()
            
            print(Colors.wrap('MENU PRINCIPAL', 'underline'))
            print()
            print("1. Créer utilisateur")
            print("2. Supprimer utilisateur")
            print("3. Modifier utilisateur")
            print("4. Lister utilisateurs")
            print("5. Vérifier expirations")
            print("6. Sauvegarder")
            print("7. Restaurer")
            print("8. Quitter")
            print()
            
            choice = input(Colors.wrap('Choix (1-8): ', 'bold')).strip()
            
            if choice == '1':
                self.interactive_create()
            elif choice == '2':
                self.interactive_delete()
            elif choice == '3':
                self.interactive_modify()
            elif choice == '4':
                self.print_header()
                self.list_users()
                input(Colors.wrap('\nAppuyez sur Entrée...', 'cyan'))
            elif choice == '5':
                self.print_header()
                self.check_expirations()
                input(Colors.wrap('\nAppuyez sur Entrée...', 'cyan'))
            elif choice == '6':
                self.interactive_backup()
            elif choice == '7':
                self.interactive_restore()
            elif choice == '8':
                print(Colors.wrap(Config.MSG['goodbye'], 'green'))
                break


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

def main():
    """Fonction principale"""
    debug = '--debug' in sys.argv
    
    try:
        manager = UserManager(debug=debug)
        manager.run()
    except KeyboardInterrupt:
        print(Colors.wrap(Config.MSG['keyboard_interrupt'], 'yellow'))
        sys.exit(0)
    except Exception as e:
        print(Colors.wrap(f"Erreur fatale: {e}", 'red'))
        if debug:
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
