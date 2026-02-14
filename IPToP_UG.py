#!/usr/bin/env python3
import os
import sys
import subprocess
import getpass
import json
import hashlib
import importlib.util
import time  # Import manquant ajouté
from pathlib import Path

"""
Script de gestion des utilisateurs VPS
Conçu par DjahNoDead
Version: 2.4 - Finale complète
"""

# Configuration
USER_DATA_FILE = "/root/user_management_data.json"
SSH_GROUP = "ssh-users"
ADMIN_GROUP = "sudo"
DOCKER_IMAGE = "ubuntu:latest"

class UserManager:
    def __init__(self):
        self.check_dependencies()
        self.setup_groups()
        self.load_user_data()
    
    def check_dependencies(self):
        """Vérifie et installe les dépendances nécessaires"""
        required_pkgs = ['docker.io', 'python3-docker']
        print("Vérification des dépendances...")
        
        missing_pkgs = []
        for pkg in required_pkgs:
            if not self.is_package_installed(pkg):
                missing_pkgs.append(pkg)
        
        if missing_pkgs:
            print(f"Installation des paquets manquants: {', '.join(missing_pkgs)}")
            try:
                subprocess.run(['apt-get', 'update'], check=True)
                subprocess.run(['apt-get', 'install', '-y'] + missing_pkgs, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Échec de l'installation des dépendances: {e}")
                sys.exit(1)
        
        global docker
        try:
            import docker
        except ImportError:
            print("Échec de l'importation du module docker")
            print("Essayez: sudo apt-get install python3-docker")
            sys.exit(1)
    
    def is_package_installed(self, pkg_name):
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
                print(f"Création du groupe {group}...")
                try:
                    subprocess.run(['groupadd', group], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Erreur lors de la création du groupe {group}: {e}")
                    sys.exit(1)
    
    def group_exists(self, group_name):
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
        except (FileNotFoundError, json.JSONDecodeError):
            self.user_data = {}
    
    def save_user_data(self):
        """Sauvegarde les données utilisateurs dans le fichier JSON"""
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(self.user_data, f, indent=4)
    
    def hash_password(self, password):
        """Hash le mot de passe avec SHA-512"""
        return hashlib.sha512(password.encode()).hexdigest()
    
    def user_exists(self, username):
        """Vérifie si l'utilisateur existe sur le système"""
        try:
            subprocess.check_output(['id', username], stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def create_user(self, username, password, is_admin=False, ssh_key=None, dockerized=False):
        """Crée un nouvel utilisateur"""
        if self.user_exists(username):
            print(f"L'utilisateur {username} existe déjà!")
            return False
        
        try:
            if dockerized:
                self.create_dockerized_user(username, password, is_admin, ssh_key)
            else:
                self.create_standard_user(username, password, is_admin, ssh_key)
            
            self.user_data[username] = {
                'is_admin': is_admin,
                'password_hash': self.hash_password(password),
                'has_ssh_key': ssh_key is not None,
                'dockerized': dockerized
            }
            self.save_user_data()
            
            print(f"\nUtilisateur {username} créé avec succès!")
            print(f"  - Type: {'Docker' if dockerized else 'Standard'}")
            if is_admin:
                print("  - Accès admin accordé")
            if ssh_key:
                print("  - Clé SSH configurée")
            return True
            
        except Exception as e:
            print(f"Erreur lors de la création de l'utilisateur: {e}")
            return False
    
    def create_standard_user(self, username, password, is_admin, ssh_key):
        """Crée un utilisateur standard sur le système"""
        cmd = ['adduser', '--disabled-password', '--gecos', '""', username]
        subprocess.run(cmd, check=True)
        
        proc = subprocess.Popen(['chpasswd'], stdin=subprocess.PIPE, universal_newlines=True)
        proc.communicate(f"{username}:{password}")
        
        groups = [SSH_GROUP]
        if is_admin:
            groups.append(ADMIN_GROUP)
        
        if groups:
            subprocess.run(['usermod', '-aG', ','.join(groups), username], check=True)
        
        if ssh_key:
            ssh_dir = Path(f"/home/{username}/.ssh")
            ssh_dir.mkdir(mode=0o700, exist_ok=True)
            
            auth_keys = ssh_dir / "authorized_keys"
            with auth_keys.open('w') as f:
                f.write(ssh_key)
            auth_keys.chmod(0o600)
            subprocess.run(['chown', '-R', f'{username}:{username}', str(ssh_dir)], check=True)
    
    def create_dockerized_user(self, username, password, is_admin, ssh_key):
        """Crée un utilisateur dans un conteneur Docker - Version finale fonctionnelle"""
        client = docker.from_env()
        container_name = f"user_{username}"
        
        self.cleanup_docker_container(container_name)
        
        try:
            # Création du conteneur avec l'utilisateur directement
            print("Création du conteneur Docker...")
            
            # Création du répertoire home sur l'hôte
            host_home = Path(f"/home/{username}")
            host_home.mkdir(mode=0o755, exist_ok=True)
            
            # Commandes pour créer l'utilisateur
            user_cmds = [
                f"useradd -m -s /bin/bash {username}",
                f"echo '{username}:{password}' | chpasswd",
                f"chown -R {username}:{username} /home/{username}"
            ]
            
            if is_admin:
                user_cmds.extend([
                    "apt-get update",
                    "apt-get install -y sudo",
                    f"echo '{username} ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"
                ])
            
            if ssh_key:
                user_cmds.extend([
                    f"mkdir -p /home/{username}/.ssh",
                    f"echo '{ssh_key}' > /home/{username}/.ssh/authorized_keys",
                    f"chmod 700 /home/{username}/.ssh",
                    f"chmod 600 /home/{username}/.ssh/authorized_keys",
                    f"chown -R {username}:{username} /home/{username}/.ssh"
                ])
            
            # Création du conteneur avec toutes les commandes
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
                command=f"/bin/sh -c \"{' && '.join(user_cmds)} && su {username}\"",
                cap_drop=['ALL'],
                security_opt=['no-new-privileges']
            )
            
            print(f"Conteneur Docker créé avec succès pour {username}")
            return container
            
        except docker.errors.APIError as e:
            print(f"Erreur Docker API: {e}")
            self.cleanup_docker_container(container_name)
            raise
        except Exception as e:
            print(f"Erreur lors de la configuration Docker: {e}")
            self.cleanup_docker_container(container_name)
            raise
    
    def cleanup_docker_container(self, container_name):
        """Nettoie les conteneurs Docker existants"""
        client = docker.from_env()
        try:
            container = client.containers.get(container_name)
            print(f"Nettoyage du conteneur existant {container_name}...")
            try:
                container.stop()
            except:
                pass
            container.remove()
        except docker.errors.NotFound:
            pass
        except Exception as e:
            print(f"Avertissement: échec du nettoyage du conteneur {container_name}: {e}")
    
    def delete_user(self, username):
        """Supprime un utilisateur"""
        if not self.user_exists(username):
            print(f"L'utilisateur {username} n'existe pas!")
            return False
        
        try:
            if self.user_data.get(username, {}).get('dockerized', False):
                self.cleanup_docker_container(f"user_{username}")
            
            subprocess.run(['userdel', '-r', username], check=True)
            
            if username in self.user_data:
                del self.user_data[username]
                self.save_user_data()
            
            print(f"Utilisateur {username} supprimé avec succès!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de la suppression de l'utilisateur: {e}")
            return False
    
    def list_users(self):
        """Liste tous les utilisateurs gérés"""
        if not self.user_data:
            print("Aucun utilisateur géré pour le moment.")
            return
        
        print("\nListe des utilisateurs gérés:")
        print("{:<20} {:<10} {:<15} {:<10}".format("Nom", "Admin", "Authentification", "Type"))
        print("-" * 60)
        
        for username, data in self.user_data.items():
            auth_method = "SSH Key" if data.get('has_ssh_key') else "Password"
            admin_status = "Oui" if data.get('is_admin') else "Non"
            user_type = "Docker" if data.get('dockerized') else "Standard"
            print("{:<20} {:<10} {:<15} {:<10}".format(
                username, admin_status, auth_method, user_type))
    
    def interactive_menu(self):
        """Menu interactif de gestion des utilisateurs"""
        while True:
            print("\n=== Gestion des utilisateurs VPS ===")
            print("Conçu par DjahNoDead\n")
            print("1. Créer un nouvel utilisateur")
            print("2. Supprimer un utilisateur")
            print("3. Lister les utilisateurs")
            print("4. Quitter")
            
            choice = input("\nVotre choix (1-4): ").strip()
            
            if choice == '1':
                self.interactive_create_user()
            elif choice == '2':
                self.interactive_delete_user()
            elif choice == '3':
                self.list_users()
            elif choice == '4':
                print("Au revoir!")
                break
            else:
                print("Choix invalide, veuillez réessayer.")
    
    def interactive_create_user(self):
        """Interface interactive pour créer un utilisateur"""
        print("\nCréation d'un nouvel utilisateur")
        
        username = input("Nom d'utilisateur: ").strip()
        if not username:
            print("Le nom d'utilisateur ne peut pas être vide!")
            return
        
        while True:
            password = getpass.getpass("Mot de passe (laisser vide pour SSH key seulement): ")
            confirm = getpass.getpass("Confirmer le mot de passe: ")
            
            if password and password != confirm:
                print("Les mots de passe ne correspondent pas!")
            else:
                break
        
        ssh_key = None
        if input("Ajouter une clé SSH? (o/n): ").lower() == 'o':
            print("Collez la clé publique SSH:")
            ssh_key = sys.stdin.read().strip()
            if not ssh_key:
                print("Aucune clé SSH fournie")
            elif not (ssh_key.startswith('ssh-rsa ') or 
                     ssh_key.startswith('ecdsa-sha2-nistp256 ') or 
                     ssh_key.startswith('ssh-ed25519 ')):
                print("Format de clé SSH invalide!")
                return
        
        if not password and not ssh_key:
            print("Vous devez fournir au moins un mot de passe ou une clé SSH!")
            return
        
        is_admin = input("Accorder les droits admin (sudo)? (o/n): ").lower() == 'o'
        dockerized = input("Dockeriser le compte utilisateur? (o/n): ").lower() == 'o'
        
        self.create_user(username, password, is_admin, ssh_key, dockerized)
    
    def interactive_delete_user(self):
        """Interface interactive pour supprimer un utilisateur"""
        print("\nSuppression d'un utilisateur")
        
        if not self.user_data:
            print("Aucun utilisateur à supprimer.")
            return
        
        self.list_users()
        username = input("\nNom de l'utilisateur à supprimer: ").strip()
        
        if username not in self.user_data:
            print(f"Attention: {username} n'est pas dans la liste des utilisateurs gérés.")
            confirm = input("Voulez-vous quand même essayer de le supprimer? (o/n): ").lower() == 'o'
            if not confirm:
                return
        
        confirm = input(f"Êtes-vous sûr de vouloir supprimer l'utilisateur {username}? (o/n): ").lower() == 'o'
        if confirm:
            self.delete_user(username)

def check_root():
    """Vérifie que le script est exécuté en root"""
    if os.geteuid() != 0:
        print("Ce script doit être exécuté en tant que root!")
        sys.exit(1)

def main():
    check_root()
    manager = UserManager()
    manager.interactive_menu()

if __name__ == "__main__":
    main()