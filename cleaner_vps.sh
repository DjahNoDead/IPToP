#!/usr/bin/env python3
"""
VPS CLEANER - Script de réinitialisation complète
Pour repartir sur une base propre pour le hotspot MikroTik
"""

import os
import sys
import subprocess
import time
import shutil
from pathlib import Path

# Couleurs pour l'affichage
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    """Affiche l'en-tête du programme"""
    os.system('clear')
    print(f"{Colors.PURPLE}{'='*60}")
    print(f"{Colors.BOLD}      VPS CLEANER - Réinitialisation Complète")
    print(f"{Colors.PURPLE}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}🚀 Pour repartir sur une base propre")
    print(f"🔧 Hotspot MikroTik HTTPS{Colors.END}")
    print()

def run_command(cmd, description, fatal=False):
    """Exécute une commande shell avec gestion d'erreur"""
    print(f"{Colors.BLUE}[▶]{Colors.END} {description}...", end=' ', flush=True)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"{Colors.GREEN}✓{Colors.END}")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.END}")
            if fatal:
                print(f"{Colors.RED}Erreur: {result.stderr}{Colors.END}")
                sys.exit(1)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"{Colors.YELLOW}⏱️ Timeout{Colors.END}")
        return False
    except Exception as e:
        print(f"{Colors.RED}⚠️ Erreur: {e}{Colors.END}")
        return False

def check_root():
    """Vérifie que le script est exécuté en root"""
    if os.geteuid() != 0:
        print(f"{Colors.RED}❌ Ce script doit être exécuté en tant que root{Colors.END}")
        print(f"{Colors.YELLOW}Utilise: sudo python3 {sys.argv[0]}{Colors.END}")
        sys.exit(1)

def confirm_reset():
    """Demande confirmation pour la réinitialisation"""
    print(f"{Colors.YELLOW}{'⚠'*60}")
    print(f"ATTENTION: Cette opération va réinitialiser complètement ton VPS")
    print(f"Tous les services liés au hotspot seront supprimés")
    print(f"{'⚠'*60}{Colors.END}")
    print()
    
    response = input(f"{Colors.RED}❓ Es-tu ABSOLUMENT sûr ? (tape 'RESET' pour confirmer): {Colors.END}")
    return response.strip() == "RESET"

def stop_services():
    """Arrête tous les services liés au hotspot"""
    services = [
        "nginx",
        "wg-quick@wg0",
        "cloudflared",
        "docker",
        "mikrotik-tunnel"
    ]
    
    print(f"{Colors.CYAN}🛑 Arrêt des services...{Colors.END}")
    
    for service in services:
        # Arrête le service
        run_command(f"systemctl stop {service} 2>/dev/null", f"Arrêt {service}")
        
        # Désactive le démarrage automatique
        run_command(f"systemctl disable {service} 2>/dev/null", f"Désactivation {service}")

def remove_packages():
    """Supprime les paquets installés"""
    print(f"\n{Colors.CYAN}🗑️  Suppression des paquets...{Colors.END}")
    
    packages = [
        "nginx",
        "certbot",
        "python3-certbot-nginx",
        "wireguard",
        "wireguard-tools",
        "cloudflared",
        "docker.io",
        "docker-compose",
        "socat",
        "autossh",
        "qrencode"
    ]
    
    # Désinstalle les paquets
    for pkg in packages:
        run_command(f"apt remove --purge -y {pkg} 2>/dev/null", f"Suppression {pkg}")
    
    # Nettoyage
    run_command("apt autoremove -y", "Nettoyage paquets inutilisés")
    run_command("apt clean", "Nettoyage cache apt")
    run_command("apt autoclean", "Nettoyage automatique")

def clean_directories():
    """Nettoie les répertoires de configuration"""
    print(f"\n{Colors.CYAN}🧹 Nettoyage des répertoires...{Colors.END}")
    
    directories = [
        "/etc/nginx",
        "/etc/wireguard",
        "/etc/cloudflared",
        "/opt/nginx-proxy-manager",
        "/var/www/html",
        "/root/.cloudflared"
    ]
    
    for directory in directories:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print(f"{Colors.GREEN}✓{Colors.END} Supprimé: {directory}")
            except Exception as e:
                print(f"{Colors.YELLOW}⚠{Colors.END} Erreur suppression {directory}: {e}")

def remove_files():
    """Supprime les fichiers spécifiques"""
    print(f"\n{Colors.CYAN}📄 Suppression des fichiers...{Colors.END}")
    
    files = [
        "/root/hotspot-wizard.sh",
        "/root/hotspot-wizard-main.sh",
        "/root/hotspot-quick.sh",
        "/root/hotspot-cloudflare.sh",
        "/root/hotspot-http-ready.sh",
        "/root/mikrotik-config.rsc",
        "/root/mikrotik-check.rsc",
        "/root/setup-http-hotspot.sh",
        "/root/test-hotspot.sh",
        "/root/test-final.sh",
        "/root/check-hotspot.sh",
        "/root/configure-npm.sh",
        "/root/reset-vps.sh",
        "/root/fix-dns-and-install.sh",
        "/etc/systemd/system/mikrotik-tunnel.service",
        "/etc/systemd/system/cloudflared.service",
        "/etc/nginx/sites-available/hotspot",
        "/etc/nginx/sites-enabled/hotspot"
    ]
    
    for file_path in files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"{Colors.GREEN}✓{Colors.END} Supprimé: {file_path}")
            except Exception as e:
                print(f"{Colors.YELLOW}⚠{Colors.END} Erreur suppression {file_path}: {e}")

def reset_firewall():
    """Réinitialise le firewall UFW"""
    print(f"\n{Colors.CYAN}🔥 Réinitialisation firewall...{Colors.END}")
    
    run_command("ufw --force reset", "Réinitialisation UFW")
    
    # Configuration de base
    run_command("ufw default deny incoming", "Default deny incoming")
    run_command("ufw default allow outgoing", "Default allow outgoing")
    run_command("ufw allow 22/tcp", "Autorisation SSH")
    
    # Active UFW
    print(f"{Colors.BLUE}[▶]{Colors.END} Activation UFW...", end=' ', flush=True)
    try:
        subprocess.run(
            "echo 'y' | ufw enable",
            shell=True,
            capture_output=True,
            text=True
        )
        print(f"{Colors.GREEN}✓{Colors.END}")
    except:
        print(f"{Colors.YELLOW}⚠{Colors.END}")

def update_system():
    """Met à jour le système"""
    print(f"\n{Colors.CYAN}🔄 Mise à jour système...{Colors.END}")
    
    run_command("apt update", "Mise à jour liste paquets")
    run_command("apt upgrade -y", "Mise à jour système")

def setup_basic_dns():
    """Configure un DNS de base"""
    print(f"\n{Colors.CYAN}🌐 Configuration DNS basique...{Colors.END}")
    
    dns_config = """nameserver 8.8.8.8
nameserver 1.1.1.1
nameserver 9.9.9.9
"""
    
    try:
        with open("/etc/resolv.conf", "w") as f:
            f.write(dns_config)
        print(f"{Colors.GREEN}✓{Colors.END} DNS configuré")
    except Exception as e:
        print(f"{Colors.YELLOW}⚠{Colors.END} Erreur configuration DNS: {e}")

def create_restart_script():
    """Crée un script pour redémarrer l'installation"""
    print(f"\n{Colors.CYAN}📝 Création script redémarrage...{Colors.END}")
    
    script_content = """#!/bin/bash
# ============================================
# REDÉMARRAGE INSTALLATION HOTSPOT
# Après nettoyage par vps-cleaner.py
# ============================================

echo "🚀 Redémarrage installation Hotspot HTTPS"
echo ""

# 1. Vérification système
echo "1. Vérification système..."
apt update
apt install -y curl wget git

# 2. Choix d'installation
echo ""
echo "2. Choisis la méthode d'installation:"
echo "   a) Installation guidée complète"
echo "   b) WireGuard seulement"
echo "   c) NGINX seulement"
echo "   d) Quitter"
echo ""

read -p "Choix [a-d]: " choice

case $choice in
    a)
        echo "Lancement installation guidée..."
        # Téléchargera le wizard plus tard
        ;;
    b)
        echo "Installation WireGuard..."
        apt install -y wireguard wireguard-tools
        ;;
    c)
        echo "Installation NGINX..."
        apt install -y nginx
        ;;
    d)
        echo "Au revoir !"
        exit 0
        ;;
    *)
        echo "Choix invalide"
        ;;
esac

echo ""
echo "✅ Prêt pour une nouvelle installation !"
"""

    try:
        with open("/root/restart-install.sh", "w") as f:
            f.write(script_content)
        
        os.chmod("/root/restart-install.sh", 0o755)
        print(f"{Colors.GREEN}✓{Colors.END} Script créé: /root/restart-install.sh")
    except Exception as e:
        print(f"{Colors.YELLOW}⚠{Colors.END} Erreur création script: {e}")

def show_summary():
    """Affiche le résumé des actions effectuées"""
    print(f"\n{Colors.GREEN}{'='*60}")
    print(f"{Colors.BOLD}✅ RÉINITIALISATION TERMINÉE !")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    print()
    
    print(f"{Colors.CYAN}📊 RÉSUMÉ DES ACTIONS:{Colors.END}")
    print(f"  • Services arrêtés et désactivés")
    print(f"  • Paquets supprimés")
    print(f"  • Configurations nettoyées")
    print(f"  • Firewall réinitialisé")
    print(f"  • Système mis à jour")
    print(f"  • DNS configuré")
    print()
    
    print(f"{Colors.YELLOW}📁 ÉTAT DU VPS:{Colors.END}")
    print(f"  • Stockage utilisé: {get_disk_usage()}")
    print(f"  • Mémoire disponible: {get_memory_info()}")
    print()
    
    print(f"{Colors.BLUE}🚀 POUR REDÉMARRER:{Colors.END}")
    print(f"  • Script: /root/restart-install.sh")
    print(f"  • Commandes utiles:")
    print(f"    sudo apt update && sudo apt upgrade")
    print(f"    sudo apt install wireguard nginx")
    print()
    
    print(f"{Colors.PURPLE}🔧 POUR DEMAIN:{Colors.END}")
    print(f"  1. Exécute: sudo /root/restart-install.sh")
    print(f"  2. Suis l'installation guidée")
    print(f"  3. Configure Cloudflare DNS")
    print(f"  4. Teste: https://wifi.fifion.space")
    print()

def get_disk_usage():
    """Récupère l'utilisation du disque"""
    try:
        result = subprocess.run(
            "df -h / | tail -1 | awk '{print $5}'",
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except:
        return "N/A"

def get_memory_info():
    """Récupère les informations mémoire"""
    try:
        result = subprocess.run(
            "free -h | grep Mem | awk '{print $4}'",
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except:
        return "N/A"

def main():
    """Fonction principale"""
    
    # Vérifications initiales
    check_root()
    print_header()
    
    # Demande confirmation
    if not confirm_reset():
        print(f"\n{Colors.YELLOW}❌ Opération annulée{Colors.END}")
        sys.exit(0)
    
    print(f"\n{Colors.RED}🔥 Début de la réinitialisation...{Colors.END}")
    time.sleep(2)
    
    # Étape 1: Arrêt services
    stop_services()
    time.sleep(1)
    
    # Étape 2: Suppression paquets
    remove_packages()
    time.sleep(1)
    
    # Étape 3: Nettoyage répertoires
    clean_directories()
    time.sleep(1)
    
    # Étape 4: Suppression fichiers
    remove_files()
    time.sleep(1)
    
    # Étape 5: Firewall
    reset_firewall()
    time.sleep(1)
    
    # Étape 6: Mise à jour
    update_system()
    time.sleep(1)
    
    # Étape 7: DNS
    setup_basic_dns()
    time.sleep(1)
    
    # Étape 8: Script redémarrage
    create_restart_script()
    time.sleep(1)
    
    # Résumé final
    show_summary()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⏹️  Interrompu par l'utilisateur{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}💥 Erreur critique: {e}{Colors.END}")
        sys.exit(1)
