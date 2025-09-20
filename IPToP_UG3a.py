#!/usr/bin/env python3
import os
import sys
import subprocess
import getpass
import json
import hashlib
import logging
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
from typing import Dict, List, Optional, Tuple

# Configuration du logging avec gestion d'erreur pour Termux
try:
    # Essayer de créer le répertoire de log s'il n'existe pas
    log_dir = "/var/log"
    if not os.path.exists(log_dir):
        log_dir = os.path.expanduser("~/.local/log")
        os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'user_manager.log')),
            logging.StreamHandler(sys.stdout)
        ]
    )
except Exception as e:
    # Fallback vers un logging simple si échec
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.warning(f"Impossible de configurer le logging fichier: {e}")

logger = logging.getLogger('UserManager')

# Import Docker après vérification des dépendances
docker = None

"""
Script de gestion des utilisateurs VPS - Version Professionnelle Améliorée
Conçu par DjahNoDead
"""

# Configuration
USER_DATA_FILE = os.path.expanduser("~/.user_management_data.json")
USER_DATA_BACKUP_DIR = os.path.expanduser("~/.user_management_backups")
SSH_GROUP = "ssh-users"
ADMIN_GROUP = "sudo"
DOCKER_IMAGE = "ubuntu:latest"
MIN_PASSWORD_LENGTH = 8
BACKUP_RETENTION_DAYS = 7
DEFAULT_EXPIRATION_DAYS = 30  # Expiration par défaut après 30 jours

# Couleurs ANSI
COLORS = {
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

class UserManager:
    def __init__(self):
        self.check_dependencies()
        self.setup_groups()
        self.load_user_data()
        self.setup_backup_dir()
        self.docker_ports = {}  # Dictionnaire pour stocker les ports des conteneurs Docker
    
    def setup_backup_dir(self):
        """Crée le répertoire de sauvegarde s'il n'existe pas"""
        Path(USER_DATA_BACKUP_DIR).mkdir(exist_ok=True, parents=True)
    
    def print_header(self):
        """Affiche l'en-tête du script"""
        os.system('clear')
        print(f"{COLORS['header']}{'='*60}")
        print(f"{COLORS['bold']}GESTION DES UTILISATEURS VPS - VERSION AMÉLIORÉE{COLORS['end']}")
        print(f"{COLORS['header']}{'='*60}{COLORS['end']}")
        print(f"{COLORS['blue']}Conçu par DjahNoDead{COLORS['end']}\n")
    
    def print_success(self, message):
        """Affiche un message de succès"""
        print(f"{COLORS['green']}[✓] {message}{COLORS['end']}")
        logger.info(message)
    
    def print_error(self, message):
        """Affiche un message d'erreur"""
        print(f"{COLORS['red']}[✗] {message}{COLORS['end']}")
        logger.error(message)
    
    def print_warning(self, message):
        """Affiche un message d'avertissement"""
        print(f"{COLORS['yellow']}[!] {message}{COLORS['end']}")
        logger.warning(message)
    
    def print_info(self, message):
        """Affiche un message d'information"""
        print(f"{COLORS['cyan']}[i] {message}{COLORS['end']}")
        logger.info(message)
    
    def print_progress(self, message):
        """Affiche une progression"""
        print(f"{COLORS['blue']}[→] {message}{COLORS['end']}", end='\r')
    
    def validate_username(self, username: str) -> Tuple[bool, str]:
        """Valide le nom d'utilisateur"""
        if not username:
            return False, "Le nom d'utilisateur ne peut pas être vide"
        
        if len(username) < 3:
            return False, "Le nom d'utilisateur doit contenir au moins 3 caractères"
        
        if not re.match(r'^[a-z_][a-z0-9_-]*$', username):
            return False, "Le nom d'utilisateur ne peut contenir que des lettres minuscules, chiffres, tirets et underscores"
        
        if self.user_exists(username):
            return False, f"L'utilisateur {username} existe déjà"
        
        return True, "Nom d'utilisateur valide"
    
    def validate_password(self, password: str) -> Tuple[bool, str]:
        """Valide le mot de passe"""
        if not password:
            return True, "Aucun mot de passe (SSH key seulement)"
        
        if len(password) < MIN_PASSWORD_LENGTH:
            return False, f"Le mot de passe doit contenir au moins {MIN_PASSWORD_LENGTH} caractères"
        
        # Vérification de la complexité du mot de passe
        if not any(char.isdigit() for char in password):
            return False, "Le mot de passe doit contenir au moins un chiffre"
        
        if not any(char.isupper() for char in password):
            return False, "Le mot de passe doit contenir au moins une lettre majuscule"
        
        if not any(char.islower() for char in password):
            return False, "Le mot de passe doit contenir au moins une lettre minuscule"
        
        return True, "Mot de passe valide"
    
    def validate_ssh_key(self, ssh_key: str) -> Tuple[bool, str]:
        """Valide la clé SSH"""
        if not ssh_key:
            return True, "Aucune clé SSH fournie"
        
        ssh_key_patterns = [
            r'ssh-rsa AAAA[0-9A-Za-z+/]+[=]{0,3}( [^@]+@[^@]+)?',
            r'ecdsa-sha2-nistp256 AAAA[0-9A-Za-z+/]+[=]{0,3}( [^@]+@[^@]+)?',
            r'ssh-ed25519 AAAA[0-9A-Za-z+/]+[=]{0,3}( [^@]+@[^@]+)?'
        ]
        
        for pattern in ssh_key_patterns:
            if re.match(pattern, ssh_key):
                return True, "Clé SSH valide"
        
        return False, "Format de clé SSH invalide"
    
    def validate_expiration_date(self, expiration_str: str) -> Tuple[bool, str, Optional[datetime]]:
        """Valide et parse la date d'expiration"""
        if not expiration_str:
            # Date par défaut: maintenant + 30 jours
            default_date = datetime.now() + timedelta(days=DEFAULT_EXPIRATION_DAYS)
            return True, f"Date d'expiration par défaut: {default_date.strftime('%Y-%m-%d')}", default_date
        
        # Formats de date acceptés
        date_formats = [
            '%Y-%m-%d',    # 2024-01-31
            '%d/%m/%Y',    # 31/01/2024
            '%d-%m-%Y',    # 31-01-2024
            '%d.%m.%Y',    # 31.01.2024
        ]
        
        for date_format in date_formats:
            try:
                expiration_date = datetime.strptime(expiration_str, date_format)
                
                # Vérifier que la date n'est pas dans le passé
                if expiration_date < datetime.now():
                    return False, "La date d'expiration ne peut pas être dans le passé", None
                
                return True, f"Date d'expiration valide: {expiration_date.strftime('%Y-%m-%d')}", expiration_date
            except ValueError:
                continue
        
        return False, "Format de date invalide. Utilisez YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY ou DD.MM.YYYY", None
    
    def check_dependencies(self):
        """Vérifie et installe les dépendances nécessaires"""
        self.print_info("Vérification des dépendances...")
        
        # Vérifier si nous sommes dans Termux
        is_termux = os.path.exists('/data/data/com.termux/files/usr')
        
        if is_termux:
            self.print_warning("Détection de Termux - certaines fonctionnalités peuvent être limitées")
        
        required_pkgs = ['docker.io', 'python3-docker']
        missing_pkgs = []
        
        for pkg in required_pkgs:
            if not self.is_package_installed(pkg):
                missing_pkgs.append(pkg)
        
        if missing_pkgs:
            self.print_warning(f"Paquets manquants: {', '.join(missing_pkgs)}")
            
            if is_termux:
                self.print_info("Dans Termux, vous devrez peut-être installer manuellement ces paquets")
                return
            
            try:
                subprocess.run(['apt-get', 'update'], check=True, capture_output=True)
                subprocess.run(['apt-get', 'install', '-y'] + missing_pkgs, check=True, capture_output=True)
                self.print_success("Dépendances installées avec succès")
            except subprocess.CalledProcessError as e:
                self.print_error(f"Échec de l'installation des dépendances: {e}")
                logger.error(f"Erreur d'installation des dépendances: {e.stderr.decode() if e.stderr else str(e)}")
                sys.exit(1)
        
        global docker
        try:
            import docker
            self.print_success("Module Docker importé avec succès")
        except ImportError as e:
            self.print_error(f"Échec de l'importation du module docker: {e}")
            self.print_info("Essayez: pip install docker")
            logger.error(f"ImportError: {e}")
            
            # Dans Termux, on continue sans Docker
            if is_termux:
                self.print_warning("Fonctionnalité Docker désactivée dans Termux")
    
    def create_dockerized_user(self, username: str, password: str, is_admin: bool, ssh_key: Optional[str] = None):
        """Crée un utilisateur dans un conteneur Docker"""
        # Vérifier si Docker est disponible
        if docker is None:
            self.print_error("Docker n'est pas disponible. Impossible de créer un utilisateur dockerisé.")
            raise Exception("Docker non disponible")
        
        client = docker.from_env()
        container_name = f"user_{username}"
        
        self.cleanup_docker_container(container_name)
        
        try:
            self.print_progress("Préparation de l'environnement Docker")
            
            # Création du répertoire home sur l'hôte
            host_home = Path(f"/home/{username}")
            if host_home.exists():
                shutil.rmtree(host_home)
            host_home.mkdir(mode=0o755, parents=True, exist_ok=True)
            
            # Commandes de configuration
            user_cmds = [
                f"useradd -m -s /bin/bash {username}",
                f"echo '{username}:{password}' | chpasswd",
                f"chown -R {username}:{username} /home/{username}"
            ]
            
            if is_admin:
                user_cmds.extend([
                    "apt-get update -qq",
                    "apt-get install -y sudo >/dev/null",
                    f"usermod -aG sudo {username}",
                    f"echo '{username} ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers.d/{username}",
                    f"chmod 440 /etc/sudoers.d/{username}"
                ])
            
            if ssh_key:
                user_cmds.extend([
                    f"mkdir -p /home/{username}/.ssh",
                    f"echo '{ssh_key}' > /home/{username}/.ssh/authorized_keys",
                    f"chmod 700 /home/{username}/.ssh",
                    f"chmod 600 /home/{username}/.ssh/authorized_keys",
                    f"chown -R {username}:{username} /home/{username}/.ssh"
                ])
            
            # Ajout de la configuration SSH
            user_cmds.extend([
                "mkdir -p /run/sshd",
                "chmod 0755 /run/sshd"
            ])
            
            # Création du conteneur
            self.print_progress(f"Création du conteneur pour {username}")
            container = client.containers.run(
                DOCKER_IMAGE,
                name=container_name,
                detach=True,
                tty=True,
                hostname=username,
                user="root",
                volumes={
                    str(host_home): {'bind': f'/home/{username}', 'mode': 'rw'}
                },
                command=f"/bin/sh -c \"{' && '.join(user_cmds)} && /usr/sbin/sshd -D\"",
                cap_drop=['ALL'],
                security_opt=['no-new-privileges'],
                ports={'22/tcp': None},  # Mappage de port dynamique
                restart_policy={"Name": "unless-stopped"}
            )
            
            # Attente de la création
            for _ in range(30):
                if container.status == 'running':
                    break
                sleep(1)
                container.reload()
            else:
                raise Exception("Timeout lors du démarrage du conteneur")
            
            # Récupération du port mappé
            container.reload()
            port_info = container.attrs['NetworkSettings']['Ports']['22/tcp']
            ssh_port = None
            if port_info and len(port_info) > 0:
                ssh_port = port_info[0]['HostPort']
                # Stocker le port pour l'affichage ultérieur
                self.docker_ports[username] = ssh_port
                self.print_info(f"SSH accessible sur le port {ssh_port}")
            
            self.print_success(f"Conteneur Docker créé pour {username}")
            return container
            
        except Exception as e:
            self.print_error(f"Erreur lors de la création Docker: {e}")
            logger.exception("Erreur détaillée lors de la création Docker")
            self.cleanup_docker_container(container_name)
            raise
    
    def interactive_create_user(self):
        """Interface interactive améliorée pour créer un utilisateur"""
        self.print_header()
        print(f"{COLORS['underline']}CRÉATION D'UN NOUVEL UTILISATEUR{COLORS['end']}\n")
        
        # Saisie du nom d'utilisateur
        while True:
            username = input(f"{COLORS['bold']}Nom d'utilisateur:{COLORS['end']} ").strip()
            is_valid, message = self.validate_username(username)
            if not is_valid:
                self.print_error(message)
            else:
                break
        
        # Saisie du mot de passe
        password = None
        while True:
            password = getpass.getpass(f"{COLORS['bold']}Mot de passe (laisser vide pour SSH key seulement):{COLORS['end']} ")
            if not password:
                break  # Aucun mot de passe, seulement SSH key
                
            is_valid, message = self.validate_password(password)
            if not is_valid:
                self.print_error(message)
                continue
                
            confirm = getpass.getpass(f"{COLORS['bold']}Confirmer le mot de passe:{COLORS['end']} ")
            if password != confirm:
                self.print_error("Les mots de passe ne correspondent pas!")
            else:
                break
        
        # Clé SSH
        ssh_key = None
        use_ssh = input(f"{COLORS['bold']}Ajouter une clé SSH? (o/n):{COLORS['end']} ").lower() == 'o'
        if use_ssh:
            print(f"{COLORS['yellow']}Collez la clé publique SSH (commençant par ssh-rsa/ecdsa/ed25519):{COLORS['end']}")
            ssh_key = sys.stdin.readline().strip()
            is_valid, message = self.validate_ssh_key(ssh_key)
            if not is_valid:
                self.print_error(message)
                return
        
        if not password and not ssh_key:
            self.print_error("Vous devez fournir au moins un mot de passe ou une clé SSH!")
            return
        
        # Date d'expiration
        expiration_date = None
        use_custom_expiration = input(f"{COLORS['bold']}Définir une date d'expiration personnalisée? (o/n):{COLORS['end']} ").lower() == 'o'
        if use_custom_expiration:
            print(f"{COLORS['yellow']}Date d'expiration (YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY ou DD.MM.YYYY):{COLORS['end']}")
            print(f"{COLORS['yellow']}Laisser vide pour utiliser {DEFAULT_EXPIRATION_DAYS} jours par défaut:{COLORS['end']}")
            expiration_input = input().strip()
            
            is_valid, message, parsed_date = self.validate_expiration_date(expiration_input)
            if not is_valid:
                self.print_error(message)
                return
            expiration_date = parsed_date
        else:
            # Date d'expiration par défaut
            expiration_date = datetime.now() + timedelta(days=DEFAULT_EXPIRATION_DAYS)
        
        # Options
        is_admin = input(f"{COLORS['bold']}Accorder les droits admin (sudo)? (o/n):{COLORS['end']} ").lower() == 'o'
        
        # Vérifier si Docker est disponible avant d'offrir l'option
        docker_available = docker is not None
        dockerized = False
        
        if docker_available:
            dockerized = input(f"{COLORS['bold']}Dockeriser le compte utilisateur? (o/n):{COLORS['end']} ").lower() == 'o'
        else:
            self.print_warning("Docker n'est pas disponible - création d'un utilisateur standard")
        
        # Résumé
        print(f"\n{COLORS['underline']}Résumé de la création:{COLORS['end']}")
        print(f"- Nom d'utilisateur: {COLORS['blue']}{username}{COLORS['end']}")
        print(f"- Type: {COLORS['blue']}{'Docker' if dockerized else 'Standard'}{COLORS['end']}")
        print(f"- Admin: {COLORS['blue']}{'Oui' if is_admin else 'Non'}{COLORS['end']}")
        auth_method = "SSH Key" if ssh_key else "Password"
        if password and ssh_key:
            auth_method = "Password et SSH Key"
        print(f"- Authentification: {COLORS['blue']}{auth_method}{COLORS['end']}")
        print(f"- Expiration: {COLORS['blue']}{expiration_date.strftime('%Y-%m-%d')}{COLORS['end']}")
        
        confirm = input(f"\n{COLORS['bold']}Confirmer la création? (o/n):{COLORS['end']} ").lower() == 'o'
        if confirm:
            if self.create_user(username, password, is_admin, ssh_key, dockerized, expiration_date):
                # Afficher les informations de connexion
                self.print_connection_info(username, dockerized)
                input("\nAppuyez sur Entrée pour continuer...")
    
    def print_connection_info(self, username: str, dockerized: bool):
        """Affiche les informations de connexion pour l'utilisateur"""
        print(f"\n{COLORS['underline']}INFORMATIONS DE CONNEXION:{COLORS['end']}")
        print(f"- Utilisateur: {COLORS['blue']}{username}{COLORS['end']}")
        
        if dockerized and docker is not None:
            # Pour les utilisateurs Docker, afficher le port
            ssh_port = self.docker_ports.get(username)
            if ssh_port:
                print(f"- Port SSH: {COLORS['blue']}{ssh_port}{COLORS['end']}")
                print(f"- Commande de connexion: {COLORS['blue']}ssh -p {ssh_port} {username}@localhost{COLORS['end']}")
            else:
                print(f"- {COLORS['yellow']}Port SSH non disponible{COLORS['end']}")
        else:
            # Pour les utilisateurs standard
            print(f"- Port SSH: {COLORS['blue']}22 (défaut){COLORS['end']}")
            print(f"- Commande de connexion: {COLORS['blue']}ssh {username}@localhost{COLORS['end']}")
        
        # Afficher la date d'expiration
        user_data = self.user_data.get(username, {})
        expiration_date = user_data.get('expiration_date')
        if expiration_date:
            exp_date = datetime.fromisoformat(expiration_date)
            days_remaining = (exp_date - datetime.now()).days
            print(f"- Date d'expiration: {COLORS['blue']}{exp_date.strftime('%Y-%m-%d')}{COLORS['end']}")
            print(f"- Jours restants: {COLORS['blue']}{days_remaining}{COLORS['end']}")
    
    def interactive_modify_user(self):
        """Interface interactive pour modifier un utilisateur existant"""
        self.print_header()
        print(f"{COLORS['underline']}MODIFICATION D'UN UTILISATEUR{COLORS['end']}\n")
        
        if not self.user_data:
            self.print_warning("Aucun utilisateur à modifier.")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        self.list_users()
        username = input(f"\n{COLORS['bold']}Nom de l'utilisateur à modifier:{COLORS['end']} ").strip()
        
        if username not in self.user_data:
            self.print_error(f"L'utilisateur {username} n'existe pas dans les données gérées.")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        user_info = self.user_data[username]
        print(f"\n{COLORS['underline']}Modification de l'utilisateur {username}{COLORS['end']}")
        print(f"1. Changer le mot de passe")
        print(f"2. Ajouter/modifier la clé SSH")
        print(f"3. Modifier les privilèges admin")
        print(f"4. Modifier la date d'expiration")
        print(f"5. Afficher les informations de connexion")
        print(f"6. Annuler")
        
        choice = input(f"\n{COLORS['bold']}Votre choix (1-6):{COLORS['end']} ").strip()
        
        if choice == '1':
            self.change_user_password(username)
        elif choice == '2':
            self.change_user_ssh_key(username)
        elif choice == '3':
            self.toggle_admin_privileges(username)
        elif choice == '4':
            self.change_expiration_date(username)
        elif choice == '5':
            self.print_connection_info(username, user_info.get('dockerized', False))
        elif choice == '6':
            return
        else:
            self.print_error("Choix invalide.")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def change_expiration_date(self, username: str):
        """Change la date d'expiration d'un utilisateur"""
        if username not in self.user_data:
            self.print_error(f"L'utilisateur {username} n'existe pas dans les données gérées.")
            return False
        
        print(f"{COLORS['yellow']}Nouvelle date d'expiration (YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY ou DD.MM.YYYY):{COLORS['end']}")
        expiration_input = input().strip()
        
        is_valid, message, parsed_date = self.validate_expiration_date(expiration_input)
        if not is_valid:
            self.print_error(message)
            return False
        
        try:
            # Mettre à jour la date d'expiration
            self.user_data[username]['expiration_date'] = parsed_date.isoformat()
            self.save_user_data()
            
            self.print_success(f"Date d'expiration de {username} modifiée avec succès!")
            self.print_info(f"Nouvelle date: {parsed_date.strftime('%Y-%m-%d')}")
            
            return True
        except Exception as e:
            self.print_error(f"Erreur lors du changement de date d'expiration: {e}")
            logger.exception("Erreur détaillée lors du changement de date d'expiration")
            return False
    
    def change_user_password(self, username: str):
        """Change le mot de passe d'un utilisateur"""
        if not self.user_exists(username):
            self.print_error(f"L'utilisateur {username} n'existe pas sur le système.")
            return False
        
        password = getpass.getpass(f"{COLORS['bold']}Nouveau mot de passe:{COLORS['end']} ")
        confirm = getpass.getpass(f"{COLORS['bold']}Confirmer le mot de passe:{COLORS['end']} ")
        
        if password != confirm:
            self.print_error("Les mots de passe ne correspondent pas!")
            return False
        
        is_valid, message = self.validate_password(password)
        if not is_valid:
            self.print_error(message)
            return False
        
        try:
            # Changer le mot de passe
            proc = subprocess.Popen(['chpasswd'], stdin=subprocess.PIPE, universal_newlines=True)
            proc.communicate(f"{username}:{password}")
            
            # Mettre à jour les données
            if username in self.user_data:
                self.user_data[username]['password_hash'] = self.hash_password(password)
                self.save_user_data()
            
            self.print_success(f"Mot de passe de {username} modifié avec succès!")
            return True
        except Exception as e:
            self.print_error(f"Erreur lors du changement de mot de passe: {e}")
            logger.exception("Erreur détaillée lors du changement de mot de passe")
            return False
    
    def change_user_ssh_key(self, username: str):
        """Change la clé SSH d'un utilisateur"""
        if not self.user_exists(username):
            self.print_error(f"L'utilisateur {username} n'existe pas sur le système.")
            return False
        
        print(f"{COLORS['yellow']}Collez la nouvelle clé publique SSH:{COLORS['end']}")
        ssh_key = sys.stdin.readline().strip()
        
        is_valid, message = self.validate_ssh_key(ssh_key)
        if not is_valid:
            self.print_error(message)
            return False
        
        try:
            # Mettre à jour la clé SSH
            ssh_dir = Path(f"/home/{username}/.ssh")
            ssh_dir.mkdir(mode=0o700, exist_ok=True)
            
            auth_keys = ssh_dir / "authorized_keys"
            with auth_keys.open('w') as f:
                f.write(ssh_key)
            auth_keys.chmod(0o600)
            
            subprocess.run(['chown', '-R', f'{username}:{username}', str(ssh_dir)], check=True, capture_output=True)
            
            # Mettre à jour les données
            if username in self.user_data:
                self.user_data[username]['has_ssh_key'] = True
                self.save_user_data()
            
            self.print_success(f"Clé SSH de {username} modifiée avec succès!")
            return True
        except Exception as e:
            self.print_error(f"Erreur lors du changement de clé SSH: {e}")
            logger.exception("Erreur détaillée lors du changement de clé SSH")
            return False
    
    def toggle_admin_privileges(self, username: str):
        """Active ou désactive les privilèges admin d'un utilisateur"""
        if not self.user_exists(username):
            self.print_error(f"L'utilisateur {username} n'existe pas sur le système.")
            return False
        
        current_status = self.user_data.get(username, {}).get('is_admin', False)
        new_status = not current_status
        
        try:
            if new_status:
                # Ajouter aux groupes admin
                subprocess.run(['usermod', '-aG', ADMIN_GROUP, username], check=True, capture_output=True)
                self.print_success(f"Privilèges admin accordés à {username}")
            else:
                # Retirer des groupes admin
                subprocess.run(['gpasswd', '-d', username, ADMIN_GROUP], check=True, capture_output=True)
                self.print_success(f"Privilèges admin retirés à {username}")
            
            # Mettre à jour les données
            if username in self.user_data:
                self.user_data[username]['is_admin'] = new_status
                self.save_user_data()
            
            return True
        except Exception as e:
            self.print_error(f"Erreur lors de la modification des privilèges: {e}")
            logger.exception("Erreur détaillée lors de la modification des privilèges")
            return False
    
    def backup_user_data(self):
        """Crée une sauvegarde des données utilisateur"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = Path(USER_DATA_BACKUP_DIR) / f"user_data_backup_{timestamp}.json"
        
        try:
            shutil.copy2(USER_DATA_FILE, backup_file)
            self.print_info(f"Sauvegarde créée: {backup_file}")
            
            # Nettoyer les anciennes sauvegardes
            self.cleanup_old_backups()
            
            return True
        except Exception as e:
            self.print_error(f"Erreur lors de la sauvegarde: {e}")
            logger.exception("Erreur détaillée lors de la sauvegarde")
            return False
    
    def cleanup_old_backups(self):
        """Nettoie les anciennes sauvegardes"""
        backup_dir = Path(USER_DATA_BACKUP_DIR)
        now = datetime.now()
        
        for backup_file in backup_dir.glob("user_data_backup_*.json"):
            # Extraire la date du nom de fichier
            try:
                date_str = backup_file.stem.replace("user_data_backup_", "")
                file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                
                # Supprimer si plus vieux que la période de rétention
                if (now - file_date).days > BACKUP_RETENTION_DAYS:
                    backup_file.unlink()
                    self.print_info(f"Sauvegarde ancienne supprimée: {backup_file}")
            except ValueError:
                # Format de fichier invalide, ignorer
                continue
    
    def restore_from_backup(self):
        """Restaure les données utilisateur à partir d'une sauvegarde"""
        backup_dir = Path(USER_DATA_BACKUP_DIR)
        backups = list(backup_dir.glob("user_data_backup_*.json"))
        
        if not backups:
            self.print_warning("Aucune sauvegarde disponible.")
            return False
        
        # Trier par date (la plus récente en premier)
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        print(f"\n{COLORS['underline']}Sauvegardes disponibles:{COLORS['end']}")
        for i, backup in enumerate(backups[:5]):  # Afficher les 5 plus récentes
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"{i+1}. {backup.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        
        choice = input(f"\n{COLORS['bold']}Choisissez une sauvegarde à restaurer (1-{min(5, len(backups))}):{COLORS['end']} ").strip()
        
        try:
            choice_idx = int(choice) - 1
            if choice_idx < 0 or choice_idx >= len(backups[:5]):
                self.print_error("Choix invalide.")
                return False
            
            selected_backup = backups[choice_idx]
            confirm = input(f"\n{COLORS['bold']}Êtes-vous sûr de vouloir restaurer {selected_backup.name}? (o/n):{COLORS['end']} ").lower() == 'o'
            
            if confirm:
                shutil.copy2(selected_backup, USER_DATA_FILE)
                self.load_user_data()  # Recharger les données
                self.print_success(f"Données restaurées à partir de {selected_backup.name}")
                return True
            else:
                self.print_info("Restauration annulée.")
                return False
                
        except ValueError:
            self.print_error("Choix invalide.")
            return False
    
    def interactive_uninstall(self):
        """Interface interactive pour désinstaller le script"""
        self.print_header()
        print(f"{COLORS['underline']}DÉSINSTALLATION DU SCRIPT{COLORS['end']}\n")
        
        print(f"{COLORS['red']}ATTENTION: Cette action est irréversible!{COLORS['end']}")
        print(f"\nLa désinstallation va :")
        print(f"1. Supprimer tous les utilisateurs créés par ce script")
        print(f"2. Supprimer tous les conteneurs Docker créés")
        print(f"3. Supprimer les données de configuration")
        print(f"4. Supprimer les fichiers de sauvegarde")
        print(f"5. Supprimer les fichiers de log")
        
        confirm = input(f"\n{COLORS['bold']}Êtes-vous ABSOLUMENT sûr de vouloir désinstaller? (o/n):{COLORS['end']} ").lower() == 'o'
        
        if not confirm:
            self.print_info("Désinstallation annulée.")
            return
        
        # Demander confirmation supplémentaire
        confirm_final = input(f"\n{COLORS['red']}Pour confirmer, tapez 'SUPPRIMER':{COLORS['end']} ").strip()
        
        if confirm_final != "SUPPRIMER":
            self.print_info("Désinstallation annulée.")
            return
        
        # Commencer la désinstallation
        self.print_info("Début de la désinstallation...")
        
        # 1. Supprimer tous les utilisateurs
        if self.user_data:
            self.print_info("Suppression des utilisateurs...")
            users_to_delete = list(self.user_data.keys())
            for username in users_to_delete:
                self.delete_user(username)
        
        # 2. Supprimer les groupes créés (s'ils sont vides)
        self.print_info("Nettoyage des groupes...")
        try:
            # Vérifier si le groupe ssh-users est vide
            result = subprocess.run(['getent', 'group', SSH_GROUP], capture_output=True, text=True)
            if result.returncode == 0:
                # Vérifier si le groupe est vide
                group_info = result.stdout.strip()
                if ':' in group_info and group_info.split(':')[-1] == '':
                    subprocess.run(['groupdel', SSH_GROUP], capture_output=True)
                    self.print_info(f"Groupe {SSH_GROUP} supprimé")
        except Exception as e:
            self.print_error(f"Erreur lors de la suppression du groupe {SSH_GROUP}: {e}")
        
        # 3. Supprimer les fichiers de données
        self.print_info("Suppression des fichiers de données...")
        try:
            if os.path.exists(USER_DATA_FILE):
                os.remove(USER_DATA_FILE)
                self.print_info(f"Fichier de données {USER_DATA_FILE} supprimé")
        except Exception as e:
            self.print_error(f"Erreur lors de la suppression du fichier de données: {e}")
        
        # 4. Supprimer les sauvegardes
        self.print_info("Suppression des sauvegardes...")
        try:
            if os.path.exists(USER_DATA_BACKUP_DIR):
                shutil.rmtree(USER_DATA_BACKUP_DIR)
                self.print_info(f"Répertoire de sauvegarde {USER_DATA_BACKUP_DIR} supprimé")
        except Exception as e:
            self.print_error(f"Erreur lors de la suppression des sauvegardes: {e}")
        
        # 5. Supprimer les fichiers de log
        self.print_info("Suppression des fichiers de log...")
        try:
            log_file = os.path.join(log_dir, 'user_manager.log')
            if os.path.exists(log_file):
                os.remove(log_file)
                self.print_info(f"Fichier de log {log_file} supprimé")
        except Exception as e:
            self.print_error(f"Erreur lors de la suppression du fichier de log: {e}")
        
        self.print_success("Désinstallation terminée avec succès!")
        print(f"\n{COLORS['green']}Tous les éléments ont été supprimés. Au revoir!{COLORS['end']}")
        
        # Quitter le script
        sys.exit(0)
    
    def interactive_menu(self):
        """Menu interactif amélioré"""
        while True:
            self.print_header()
            print(f"{COLORS['underline']}MENU PRINCIPAL{COLORS['end']}\n")
            
            options = [
                "1. Créer un nouvel utilisateur",
                "2. Supprimer un utilisateur",
                "3. Modifier un utilisateur",
                "4. Lister les utilisateurs",
                "5. Sauvegarder les données",
                "6. Restaurer depuis sauvegarde",
                "7. Vérifier les expirations",
                "8. Désinstaller le script",
                "9. Quitter\n"
            ]
            
            for option in options:
                print(f"{COLORS['bold']}{option}{COLORS['end']}")
            
            choice = input(f"\n{COLORS['blue']}Votre choix (1-9):{COLORS['end']} ").strip()
            
            if choice == '1':
                self.interactive_create_user()
            elif choice == '2':
                self.interactive_delete_user()
            elif choice == '3':
                self.interactive_modify_user()
            elif choice == '4':
                self.list_users()
                input("\nAppuyez sur Entrée pour continuer...")
            elif choice == '5':
                if self.backup_user_data():
                    self.print_success("Sauvegarde effectuée avec succès!")
                input("\nAppuyez sur Entrée pour continuer...")
            elif choice == '6':
                self.restore_from_backup()
                input("\nAppuyez sur Entrée pour continuer...")
            elif choice == '7':
                self.check_expirations()
                input("\nAppuyez sur Entrée pour continuer...")
            elif choice == '8':
                self.interactive_uninstall()
                input("\nAppuyez sur Entrée pour continuer...")
            elif choice == '9':
                print(f"\n{COLORS['green']}Merci d'avoir utilisé ce script!{COLORS['end']}")
                break
            else:
                self.print_error("Choix invalide, veuillez réessayer.")
                sleep(1)
    
    def check_expirations(self):
        """Vérifie et affiche les utilisateurs expirés ou sur le point d'expirer"""
        self.print_header()
        print(f"{COLORS['underline']}VÉRIFICATION DES EXPIRATIONS{COLORS['end']}\n")
        
        if not self.user_data:
            self.print_warning("Aucun utilisateur à vérifier.")
            return
        
        now = datetime.now()
        expired_users = []
        expiring_soon = []
        
        for username, data in self.user_data.items():
            expiration_date_str = data.get('expiration_date')
            if not expiration_date_str:
                continue
                
            expiration_date = datetime.fromisoformat(expiration_date_str)
            days_remaining = (expiration_date - now).days
            
            if days_remaining < 0:
                expired_users.append((username, expiration_date, days_remaining))
            elif days_remaining <= 7:  # Expire dans moins d'une semaine
                expiring_soon.append((username, expiration_date, days_remaining))
        
        # Afficher les utilisateurs expirés
        if expired_users:
            print(f"{COLORS['red']}UTILISATEURS EXPIRÉS:{COLORS['end']}")
            for username, exp_date, days in expired_users:
                print(f"- {username}: expiré depuis {-days} jours (le {exp_date.strftime('%Y-%m-%d')})")
            print()
        
        # Afficher les utilisateurs sur le point d'expirer
        if expiring_soon:
            print(f"{COLORS['yellow']}UTILISATEURS EXPIRENT BIENTÔT:{COLORS['end']}")
            for username, exp_date, days in expiring_soon:
                print(f"- {username}: expire dans {days} jours (le {exp_date.strftime('%Y-%m-%d')})")
            print()
        
        if not expired_users and not expiring_soon:
            self.print_success("Aucun utilisateur expiré ou sur le point d'expirer.")
    
    def is_package_installed(self, pkg_name: str) -> bool:
        """Vérifie si un paquet est installé"""
        try:
            subprocess.run(['dpkg', '-s', pkg_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def setup_groups(self):
        """Crée les groupes nécessaires s'ils n'existent pas"""
        for group in [SSH_GROUP, ADMIN_GROUP]:
            if not self.group_exists(group):
                self.print_info(f"Création du groupe {group}...")
                try:
                    subprocess.run(['groupadd', group], check=True, capture_output=True)
                    self.print_success(f"Groupe {group} créé avec succès")
                except subprocess.CalledProcessError as e:
                    self.print_error(f"Échec de la création du groupe {group}: {e}")
                    logger.error(f"Erreur création groupe: {e.stderr.decode() if e.stderr else str(e)}")
                    # Dans Termux, on continue sans créer le groupe
                    if os.path.exists('/data/data/com.termux/files/usr'):
                        self.print_warning(f"Impossible de créer le groupe {group} dans Termux")
    
    def group_exists(self, group_name: str) -> bool:
        """Vérifie si un groupe existe"""
        try:
            subprocess.run(['getent', 'group', group_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def load_user_data(self):
        """Charge les données utilisateurs depuis le fichier JSON"""
        try:
            with open(USER_DATA_FILE, 'r') as f:
                self.user_data = json.load(f)
            self.print_info("Données utilisateur chargées avec succès")
        except FileNotFoundError:
            self.user_data = {}
            self.print_warning("Fichier de données utilisateur non trouvé, création d'un nouveau")
        except json.JSONDecodeError as e:
            self.print_error(f"Erreur de décodage JSON: {e}")
            logger.error(f"Erreur JSON: {e}")
            self.user_data = {}
    
    def save_user_data(self):
        """Sauvegarde les données utilisateurs dans le fichier JSON"""
        try:
            with open(USER_DATA_FILE, 'w') as f:
                json.dump(self.user_data, f, indent=4)
            self.print_info("Données utilisateur sauvegardées avec succès")
        except Exception as e:
            self.print_error(f"Erreur lors de la sauvegarde: {e}")
            logger.exception("Erreur détaillée lors de la sauvegarde")
    
    def hash_password(self, password: str) -> str:
        """Hash le mot de passe avec SHA-512 et un sel"""
        if not password:
            return ""
        salt = os.urandom(16).hex()
        return salt + hashlib.sha512((salt + password).encode()).hexdigest()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Vérifie un mot de passe contre son hash"""
        if not password_hash or len(password_hash) < 32:
            return False
        
        salt = password_hash[:32]
        return password_hash == salt + hashlib.sha512((salt + password).encode()).hexdigest()
    
    def user_exists(self, username: str) -> bool:
        """Vérifie si l'utilisateur existe sur le système"""
        try:
            subprocess.check_output(['id', username], stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def create_user(self, username: str, password: Optional[str], is_admin: bool = False, 
                   ssh_key: Optional[str] = None, dockerized: bool = False, expiration_date: Optional[datetime] = None) -> bool:
        """Crée un nouvel utilisateur"""
        if self.user_exists(username):
            self.print_error(f"L'utilisateur {username} existe déjà!")
            return False
        
        try:
            # Créer une sauvegarde avant toute modification
            self.backup_user_data()
            
            if dockerized and docker is not None:
                container = self.create_dockerized_user(username, password, is_admin, ssh_key)
                container_id = container.id[:12] if container else "unknown"
            else:
                self.create_standard_user(username, password, is_admin, ssh_key)
                container_id = None
            
            # Enregistrer les données utilisateur
            self.user_data[username] = {
                'is_admin': is_admin,
                'password_hash': self.hash_password(password) if password else None,
                'has_ssh_key': ssh_key is not None,
                'dockerized': dockerized,
                'created_at': datetime.now().isoformat(),
                'container_id': container_id,
                'expiration_date': expiration_date.isoformat() if expiration_date else None
            }
            self.save_user_data()
            
            self.print_success(f"Utilisateur {username} créé avec succès!")
            self.print_info(f"  - Type: {'Docker' if dockerized else 'Standard'}")
            if is_admin:
                self.print_info("  - Accès admin accordé")
            if ssh_key:
                self.print_info("  - Clé SSH configurée")
            if expiration_date:
                days_remaining = (expiration_date - datetime.now()).days
                self.print_info(f"  - Expiration: {expiration_date.strftime('%Y-%m-%d')} ({days_remaining} jours restants)")
            return True
            
        except Exception as e:
            self.print_error(f"Erreur lors de la création de l'utilisateur: {e}")
            logger.exception("Erreur détaillée lors de la création d'utilisateur")
            return False
    
    def create_standard_user(self, username: str, password: Optional[str], is_admin: bool, ssh_key: Optional[str]):
        """Crée un utilisateur standard sur le système"""
        # Créer l'utilisateur sans mot de passe
        cmd = ['adduser', '--disabled-password', '--gecos', '""', username]
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Définir le mot de passe si fourni
        if password:
            proc = subprocess.Popen(['chpasswd'], stdin=subprocess.PIPE, universal_newlines=True)
            proc.communicate(f"{username}:{password}")
        
        # Ajouter aux groupes
        groups = [SSH_GROUP]
        if is_admin:
            groups.append(ADMIN_GROUP)
        
        if groups:
            subprocess.run(['usermod', '-aG', ','.join(groups), username], check=True, capture_output=True)
        
        # Configurer la clé SSH si fournie
        if ssh_key:
            ssh_dir = Path(f"/home/{username}/.ssh")
            ssh_dir.mkdir(mode=0o700, exist_ok=True)
            
            auth_keys = ssh_dir / "authorized_keys"
            with auth_keys.open('w') as f:
                f.write(ssh_key)
            auth_keys.chmod(0o600)
            subprocess.run(['chown', '-R', f'{username}:{username}', str(ssh_dir)], check=True, capture_output=True)
    
    def cleanup_docker_container(self, container_name: str):
        """Nettoie les conteneurs Docker existants"""
        if docker is None:
            return
            
        client = docker.from_env()
        try:
            container = client.containers.get(container_name)
            self.print_info(f"Nettoyage du conteneur existant {container_name}...")
            try:
                container.stop(timeout=10)
            except docker.errors.APIError as e:
                self.print_warning(f"Impossible d'arrêter le conteneur: {e}")
            
            try:
                container.remove()
                self.print_success(f"Conteneur {container_name} supprimé")
            except docker.errors.APIError as e:
                self.print_warning(f"Impossible de supprimer le conteneur: {e}")
                
        except docker.errors.NotFound:
            pass  # Le conteneur n'existe pas, c'est ce qu'on veut
        except Exception as e:
            self.print_error(f"Erreur lors du nettoyage du conteneur {container_name}: {e}")
            logger.exception("Erreur détaillée lors du nettoyage Docker")
    
    def delete_user(self, username: str) -> bool:
        """Supprime un utilisateur"""
        if not self.user_exists(username):
            self.print_error(f"L'utilisateur {username} n'existe pas!")
            return False
        
        try:
            # Créer une sauvegarde avant toute modification
            self.backup_user_data()
            
            # Supprimer le conteneur Docker si applicable
            if self.user_data.get(username, {}).get('dockerized', False):
                self.cleanup_docker_container(f"user_{username}")
            
            # Supprimer l'utilisateur système
            subprocess.run(['userdel', '-r', username], check=True, capture_output=True)
            
            # Supprimer les données
            if username in self.user_data:
                del self.user_data[username]
                self.save_user_data()
            
            self.print_success(f"Utilisateur {username} supprimé avec succès!")
            return True
            
        except Exception as e:
            self.print_error(f"Erreur lors de la suppression de l'utilisateur: {e}")
            logger.exception("Erreur détaillée lors de la suppression d'utilisateur")
            return False
    
    def interactive_delete_user(self):
        """Interface interactive pour supprimer un utilisateur"""
        self.print_header()
        print(f"{COLORS['underline']}SUPPRESSION D'UN UTILISATEUR{COLORS['end']}\n")
        
        if not self.user_data:
            self.print_warning("Aucun utilisateur à supprimer.")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        self.list_users()
        username = input(f"\n{COLORS['bold']}Nom de l'utilisateur à supprimer:{COLORS['end']} ").strip()
        
        if username not in self.user_data:
            self.print_error(f"L'utilisateur {username} n'existe pas dans les données gérées.")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        confirm = input(f"\n{COLORS['bold']}Êtes-vous sûr de vouloir supprimer {username}? (o/n):{COLORS['end']} ").lower() == 'o'
        if confirm:
            if self.delete_user(username):
                self.print_success(f"Utilisateur {username} supprimé avec succès!")
            else:
                self.print_error(f"Échec de la suppression de {username}")
        else:
            self.print_info("Suppression annulée.")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def list_users(self):
        """Liste tous les utilisateurs gérés"""
        if not self.user_data:
            self.print_warning("Aucun utilisateur géré.")
            return
        
        print(f"{COLORS['underline']}UTILISATEURS GÉRÉS:{COLORS['end']}\n")
        print(f"{COLORS['bold']}{'Nom':<15} {'Admin':<6} {'Type':<8} {'SSH':<4} {'Expiration':<12} {'Jours':<6}{COLORS['end']}")
        print("-" * 60)
        
        now = datetime.now()
        
        for username, data in self.user_data.items():
            admin = "✓" if data.get('is_admin', False) else "✗"
            user_type = "Docker" if data.get('dockerized', False) else "Std"
            ssh_key = "✓" if data.get('has_ssh_key', False) else "✗"
            
            # Gestion de la date d'expiration
            expiration_date_str = data.get('expiration_date')
            if expiration_date_str:
                expiration_date = datetime.fromisoformat(expiration_date_str)
                days_remaining = (expiration_date - now).days
                expiration_display = expiration_date.strftime('%Y-%m-%d')
                days_display = f"{days_remaining}"
                
                # Colorer en rouge si expiré, en jaune si expire bientôt
                if days_remaining < 0:
                    days_display = f"{COLORS['red']}{days_remaining}{COLORS['end']}"
                    expiration_display = f"{COLORS['red']}{expiration_display}{COLORS['end']}"
                elif days_remaining <= 7:
                    days_display = f"{COLORS['yellow']}{days_remaining}{COLORS['end']}"
                    expiration_display = f"{COLORS['yellow']}{expiration_display}{COLORS['end']}"
            else:
                expiration_display = "N/A"
                days_display = "∞"
            
            print(f"{username:<15} {admin:<6} {user_type:<8} {ssh_key:<4} {expiration_display:<12} {days_display:<6}")

def main():
    """Fonction principale"""
    try:
        # Vérifier les privilèges root
        if os.geteuid() != 0:
            print(f"{COLORS['red']}Ce script doit être exécuté en tant que root!{COLORS['end']}")
            print(f"Utilisez: sudo {sys.argv[0]}")
            sys.exit(1)
        
        manager = UserManager()
        manager.interactive_menu()
        
    except KeyboardInterrupt:
        print(f"\n\n{COLORS['yellow']}Interruption par l'utilisateur. Au revoir!{COLORS['end']}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{COLORS['red']}Erreur inattendue: {e}{COLORS['end']}")
        logger.exception("Erreur inattendue dans main()")
        sys.exit(1)

if __name__ == "__main__":
    main()