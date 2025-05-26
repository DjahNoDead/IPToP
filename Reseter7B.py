import os
import subprocess
import sys
import importlib.util

# ========== Configuration silencieuse des dépendances ==========
ESSENTIAL_PACKAGES = [
    ("rich", "rich"),
    ("tabulate", "tabulate"),
    ("packaging", "packaging"),
    ("psutil", "psutil"),
    ("importlib_metadata", "importlib.metadata"),
    ("setuptools", "pkg_resources")
]

class DependencyManager:
    """Gestionnaire silencieux des dépendances"""
    
    @staticmethod
    def _install_packages(packages):
        """Installation silencieuse des packages"""
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check"] + packages,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except subprocess.CalledProcessError:
            return False

    @classmethod
    def setup_environment(cls):
        """Configure l'environnement Python"""
        # Phase 1: Installation minimale silencieuse
        bootstrap_pkgs = [pkg for pkg, _ in ESSENTIAL_PACKAGES[:3]]
        if not cls._install_packages(bootstrap_pkgs):
            sys.exit("Échec de l'installation des dépendances critiques")

        # Phase 2: Vérification complète avec feedback minimal
        from rich.console import Console
        console = Console()
        
        missing = []
        for pkg, import_name in ESSENTIAL_PACKAGES:
            if importlib.util.find_spec(import_name) is None:
                missing.append(pkg)
        
        if missing:
            console.print(f"🔍 Installation des dépendances...", style="dim")
            if not cls._install_packages(missing):
                console.print("[red]✗ Échec de l'installation[/red]", style="bold")
                sys.exit(1)
            console.print("[green]✓ Environnement configuré[/green]", style="bold")

# Configuration initiale
DependencyManager.setup_environment()

# ========== Imports après installation ==========
from rich.console import Console
from rich.panel import Panel
import psutil
import time
import shutil
import tarfile
from datetime import datetime, timedelta
import fnmatch
import glob
import zipfile
import getpass
import logging
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from tabulate import tabulate
from rich.table import Table
from rich.text import Text
from rich.live import Live

# ========== Initialisation ==========
console = Console()

# Couleurs ANSI (si besoin ailleurs dans le script)
cyan = "\033[1;36m"
green = "\033[1;32m"
yellow = "\033[1;33m"
red = "\033[1;31m"
reset = "\033[0m"
magenta = "\033[35m"

# ========== Fonctions utilitaires ==========
def clear_screen():
    """Efface l'écran du terminal"""
    os.system('clear' if os.name != 'nt' else 'cls')

def typewriter(text, delay=0.02):
    """Affiche le texte caractère par caractère avec style."""
    for char in text:
        console.print(char, end="", style="bold cyan", soft_wrap=True)
        time.sleep(delay)
    print()

# ========== Affichage bannière stylisée ==========
def display_banner():
    banner_text = Text()
    banner_text.append("___ ____ _____     ____\n", style="bold cyan")
    banner_text.append("|_ _|  _ \\_   _|__ |  _ \\\n", style="bold cyan")
    banner_text.append(" | || |_) || |/ _ \\| |_) |\n", style="bold cyan")
    banner_text.append(" | ||  __/ | | (_) |  __/\n", style="bold cyan")
    banner_text.append("|___|_|    |_|\\___/|_|\n", style="bold cyan")
    banner_text.append("\n              Cleaner\n", style="bold green")
    banner_text.append("\nhttps://t.me/+mQxb0SaXMKUwYWQ0\n", style="bold blue")
    banner_text.append(" DjahNoDead👽", style="bold magenta")

    panel = Panel(banner_text, border_style="bright_yellow", title="[bold red]Welcome", subtitle="[bold white]LeC@fard💪")

    with Progress(
        SpinnerColumn(style="bold green"),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Chargement du programme...", total=None)
        time.sleep(2)

    console.print(panel)

# ========== Point d'entrée principal ==========
def main():
    clear_screen()
    typewriter(">> Lancement du système de nettoyage en cours...\n", delay=0.03)
    time.sleep(1)
    display_banner()

if __name__ == "__main__":
    main()

def get_choice(min_val, max_val):
    """
    Demande à l'utilisateur de choisir une option entre min_val et max_val
    avec gestion robuste des erreurs
    """
    while True:
        try:
            choice = int(input("❓ Votre choix : "))
            if min_val <= choice <= max_val:
                return choice
            console.print(f"[red]❌ Veuillez entrer un nombre entre {min_val} et {max_val}[/red]")
        except ValueError:
            console.print("[red]❌ Veuillez entrer un nombre valide[/red]")

# ==================== FONCTIONS DE NETOYAGE ====================

def show_python_modules_menu():
    """Menu unifié pour la gestion des modules Python"""
    menu_options = [
        "[1] Lister les modules installés",
        "[2] Installer un module spécifique",
        "[3] Installer les modules essentiels",
        "[4] Réparer l'environnement Python",
        "[5] Nettoyer les paquets corrompus",
        "[6] Retour au menu principal"
    ]
    
    console.print(Panel(
        "\n".join(menu_options),
        title="[bold cyan]GESTION DES MODULES PYTHON[/bold cyan]",
        border_style="blue"
    ))

def show_python_repair_submenu():
    """Sous-menu spécialisé pour la réparation"""
    repair_options = [
        "[1] Réparer les modules manquants",
        "[2] Nettoyer les doublons (.dist-info)",
        "[3] Restaurer les métadonnées",
        "[4] Vérifier l'intégrité",
        "[5] Retour"
    ]
    
    console.print(Panel(
        "\n".join(repair_options),
        title="[bold red]RÉPARATION AVANCÉE[/bold red]",
        border_style="red"
    ))

def manage_python_modules():
    """Fonction principale unifiée"""
    while True:
        show_python_modules_menu()
        choice = get_choice(1, 6)
        
        if choice == 1:
            manage_installed_modules_and_tools()
        elif choice == 2:
            module = input(f"{cyan}Nom du module à installer : {reset}").strip()
            if module:
                subprocess.run(f"pip install {module}", shell=True)
        elif choice == 3:
            install_essential_modules()
        elif choice == 4:
            while True:
                show_python_repair_submenu()
                repair_choice = get_choice(1, 5)
                
                if repair_choice == 1:
                    repair_python_modules()
                elif repair_choice == 2:
                    clean_duplicate_dist_info()
                elif repair_choice == 3:
                    restore_dist_info_menu()
                elif repair_choice == 4:
                    scan_python_environment()
                elif repair_choice == 5:
                    break
        elif choice == 5:
            clean_invalid_distributions()
        elif choice == 6:
            break

        input(f"\n{yellow}Appuyez sur Entrée pour continuer...{reset}")
        clear_screen()
            
def install_module():
    """Installe un module Python spécifique"""
    module = input("Nom du module à installer : ").strip()
    if module:
        subprocess.run(f"pip install {module}", shell=True)

def install_essential_modules():
    """Installe les modules Python essentiels avec gestion des erreurs améliorée"""
    from rich.progress import Progress
    from rich.table import Table

    essentials = [
        # Réseau et Internet
        ("requests", "Requêtes HTTP avancées"),
        ("ping3", "Ping réseau simple et efficace"),
        ("urllib3", "Client HTTP bas niveau"),
        ("bs4", "BeautifulSoup4 - Parsing HTML/XML"),
        ("dnspython", "Requêtes DNS avancées"),
        
        # Sécurité et chiffrement
        ("pycryptodomex", "Cryptographie robuste (version isolée)"),
        ("cryptography", "Cryptographie moderne"),
        ("hashlib", "Fonctions de hachage sécurisées"),
        
        # Interface utilisateur
        ("rich", "Interfaces console riches et stylisées"),
        ("colorama", "Couleurs en console multiplateforme"),
        ("tqdm", "Barres de progression intuitives"),
        ("tabulate", "Affichage de tableaux clairs"),
        
        # Données et traitement
        ("numpy", "Calcul numérique performant"),
        ("pandas", "Manipulation de données avancée"),
        ("matplotlib", "Visualisation de données"),
        
        # Utilitaires système
        ("psutil", "Monitoring système et processus"),
        ("pathlib", "Gestion moderne des chemins"),
        ("setuptools", "Packaging et distribution"),
        
        # Développement
        ("ipython", "Console interactive améliorée"),
        ("pylint", "Vérification de code Python"),
        ("autopep8", "Formatage de code automatique")
    ]

    console.print(Panel("[bold cyan]📦 INSTALLATION DES MODULES ESSENTIELS[/bold cyan]", border_style="blue"))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("N°", style="cyan", width=4)
    table.add_column("Module", style="green")
    table.add_column("Description", style="yellow")

    for i, (module, desc) in enumerate(essentials, 1):
        table.add_row(str(i), module, desc)

    console.print(table)
    console.print(f"\n[cyan]0.[/cyan] Tout installer")
    console.print(f"[cyan]M.[/cyan] Menu principal\n")

    while True:
        choice = input(f"{cyan}Votre choix (0-{len(essentials)}, M) : {reset}").strip().upper()

        if choice == "M":
            return
        elif choice == "0":
            with Progress() as progress:
                task = progress.add_task("[cyan]Installation...", total=len(essentials))
                
                for module, _ in essentials:
                    progress.update(task, description=f"[green]Installation de {module}...")
                    try:
                        result = subprocess.run(
                            f"pip install --upgrade {module}",
                            shell=True,
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            progress.console.print(f"[green]✔ {module} installé avec succès[/green]")
                        else:
                            progress.console.print(f"[red]❌ Échec pour {module}: {result.stderr}[/red]")
                    except Exception as e:
                        progress.console.print(f"[red]❌ Erreur avec {module}: {str(e)}[/red]")
                    progress.advance(task)
            break
        elif choice.isdigit() and 1 <= int(choice) <= len(essentials):
            module, desc = essentials[int(choice)-1]
            try:
                console.print(f"[yellow]Installation de {module}...[/yellow]")
                result = subprocess.run(
                    f"pip install --upgrade {module}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    console.print(f"[green]✔ {module} installé avec succès[/green]")
                else:
                    console.print(f"[red]❌ Échec d'installation: {result.stderr}[/red]")
            except Exception as e:
                console.print(f"[red]❌ Erreur: {str(e)}[/red]")
            break
        else:
            console.print("[red]❌ Choix invalide. Veuillez réessayer.[/red]")

    input(f"\n{yellow}Appuyez sur Entrée pour continuer...{reset}")
    
# ==============================================
# 1. Détection étendue des outils
# ==============================================
RECON_TOOLS = {
    # Subdomain Enumeration
    "Subfinder": ["/data/data/com.termux/files/usr/bin/subfinder", "~/.config/subfinder"],
    "Sublist3r": ["/data/data/com.termux/files/usr/bin/sublist3r", "~/Sublist3r"],
    "Amass": ["/data/data/com.termux/files/usr/bin/amass", "~/.config/amass"],
    "Assetfinder": ["/data/data/com.termux/files/usr/bin/assetfinder"],
    "Findomain": ["/data/data/com.termux/files/usr/bin/findomain", "~/.findomain"],
    # HTTP/Web Tools
    "HTTPx": ["/data/data/com.termux/files/usr/bin/httpx"],
    "Gau": ["/data/data/com.termux/files/usr/bin/gau"],
    "Waybackurls": ["/data/data/com.termux/files/usr/bin/waybackurls"],
    # Network Scanners
    "Naabu": ["/data/data/com.termux/files/usr/bin/naabu"],
    "Nuclei": ["/data/data/com.termux/files/usr/bin/nuclei", "~/.nuclei"],
    "Katana": ["/data/data/com.termux/files/usr/bin/katana"],
    "Dnsx": ["/data/data/com.termux/files/usr/bin/dnsx"],
    # Pentesting Tools
    "Sqlmap": ["/data/data/com.termux/files/usr/bin/sqlmap"],
    "Metasploit": ["/data/data/com.termux/files/usr/bin/msfconsole", "~/.msf4"],
    "Nikto": ["/data/data/com.termux/files/usr/bin/nikto"],
}

# ==============================================
# 2. Nettoyage des dépendances globales
# ==============================================
def clean_global_deps():
    """Nettoie les dépendances globales Go et pip avec explications Rich"""
    console.print(Panel.fit(
        "🧼 [bold cyan]Nettoyage des dépendances globales[/bold cyan]\n"
        "- Ce processus va :\n"
        "  • Vider le cache des modules Go\n"
        "  • Supprimer tous les modules Python installés globalement\n"
        "\n[bold yellow]Utilisez cette option si vous avez des erreurs de dépendance ou souhaitez repartir propre.[/bold yellow]",
        title="NETTOYAGE GLOBAL", border_style="blue"
    ))

    # Nettoyage Go
    console.print("[cyan]→ Nettoyage du cache Go...[/cyan]")
    if subprocess.run("command -v go", shell=True).returncode == 0:
        subprocess.run("go clean -modcache", shell=True)
        console.print("[green]✔ Cache Go vidé[/green]")
    else:
        console.print("[yellow]ℹ Go n’est pas installé, rien à nettoyer[/yellow]")

    # Nettoyage pip
    console.print("[cyan]→ Suppression des modules Python globaux...[/cyan]")
    try:
        subprocess.run("pip freeze | xargs pip uninstall -y", shell=True, check=True)
        console.print("[green]✔ Modules Python désinstallés avec succès[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Erreur lors de la désinstallation : {e}[/red]")

def deep_clean():
    standard_clean()

    console.print(Panel.fit(
        "🌀 Nettoyage approfondi\n\n- Supprime caches, temporaires et logs\n- Vide ~/.cache, ~/tmp, apt et logs",
        title="NIVEAU 3 - APPROFONDI", border_style="cyan"
    ))

    subprocess.run("rm -rf ~/.cache/*", shell=True)
    subprocess.run("rm -rf ~/tmp/*", shell=True)
    subprocess.run("apt-get clean", shell=True)
    subprocess.run("find ~ -name '*.log' -delete", shell=True)

    console.print("[green]✔ Nettoyage approfondi terminé[/green]")
    
def standard_clean():
    light_clean()

    console.print(Panel.fit(
        "🧹 Nettoyage standard\n\n- Inclut le nettoyage léger\n- Supprime Subfinder + répertoire ~/go",
        title="NIVEAU 2 - STANDARD", border_style="cyan"
    ))

    subprocess.run("rm -f /data/data/com.termux/files/usr/bin/subfinder", shell=True)
    subprocess.run("rm -rf ~/go", shell=True)

    console.print("[green]✔ Nettoyage standard terminé[/green]")

def light_clean():
    console.print(Panel.fit(
        "🧽 Nettoyage léger\n\n- Supprime les modules Python non essentiels\n- Vide le cache pip",
        title="NIVEAU 1 - LÉGER", border_style="cyan"
    ))

    modules = ["dnspython", "colorama", "tabulate", "ping3", "tqdm", "requests", "pycryptodome"]
    for module in modules:
        console.print(f"[yellow]→ Suppression de {module}[/yellow]")
        subprocess.run(f"pip uninstall -y {module}", shell=True, stdout=subprocess.DEVNULL)

    subprocess.run("pip cache purge", shell=True)
    console.print("[green]✔ Modules Python supprimés + cache pip vidé[/green]")

def clean_invalid_distributions():
    """
    Supprime les distributions Python corrompues ou invalides (~nommodule)
    repérées dans le dossier site-packages.
    """
    site_packages = "/data/data/com.termux/files/usr/lib/python3.12/site-packages"
    if not os.path.exists(site_packages):
        console.print("[yellow]ℹ Dossier site-packages introuvable[/yellow]")
        return

    corrupted = [f for f in os.listdir(site_packages) if f.startswith("~")]
    if not corrupted:
        console.print("[green]✅ Aucun paquet corrompu détecté[/green]")
        return

    console.print(Panel.fit(
        f"[bold red]⚠ Détection de distributions invalides :[/bold red]\n" +
        "\n".join(corrupted),
        title="NETTOYAGE CORRUPTION", border_style="red"
    ))

    for pkg in corrupted:
        path = os.path.join(site_packages, pkg)
        try:
            if os.path.isfile(path):
                os.remove(path)
            else:
                subprocess.run(f"rm -rf '{path}'", shell=True)
            console.print(f"[green]✔ Supprimé : {pkg}[/green]")
        except Exception as e:
            console.print(f"[red]❌ Erreur suppression {pkg}: {e}[/red]")

def scan_python_environment():
    """
    Analyse l’environnement Python :
    - Affiche les .dist-info présents
    - Demande confirmation pour suppression
    - Sauvegarde les fichiers dans ~/.backup-dist-info avant suppression
    """
    import shutil
    import os
    site_packages = "/data/data/com.termux/files/usr/lib/python3.12/site-packages"
    backup_dir = os.path.expanduser("~/.backup-dist-info")

    console.print(Panel(
        "🔎 ANALYSE DE L’ENVIRONNEMENT PYTHON",
        border_style="cyan"
    ))

    if not os.path.exists(site_packages):
        console.print("[red]❌ Dossier site-packages introuvable[/red]")
        return

    dist_infos = [f for f in os.listdir(site_packages) if f.endswith(".dist-info")]
    if not dist_infos:
        console.print("[green]✅ Aucun fichier .dist-info détecté[/green]")
        return

    # Affichage des .dist-info détectés
    console.print(Panel("\n".join(dist_infos), title="🔁 Fichiers .dist-info détectés", border_style="yellow"))

    confirm = input(f"\n{yellow}⚠ Voulez-vous les sauvegarder et les supprimer ? [y/n] : {reset}").strip().lower()
    if confirm not in ["y", "yes", "o", "oui"]:
        console.print("[cyan]↩ Aucun fichier n’a été supprimé[/cyan]")
        input(f"\n{yellow}Appuyez sur Entrée pour revenir au menu...{reset}")
        return

    # Créer le dossier de sauvegarde si besoin
    os.makedirs(backup_dir, exist_ok=True)
    deleted = []

    for entry in dist_infos:
        src = os.path.join(site_packages, entry)
        dst = os.path.join(backup_dir, entry)

        try:
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
                shutil.rmtree(src)
            else:
                shutil.copy2(src, dst)
                os.remove(src)
            deleted.append(entry)
            console.print(f"[green]✔ Sauvegardé et supprimé : {entry}[/green]")
        except Exception as e:
            console.print(f"[red]❌ Erreur pour {entry} : {e}[/red]")

    if deleted:
        console.print(Panel(
            f"[bold green]✅ {len(deleted)} fichier(s) sauvegardé(s) et supprimé(s)[/bold green]\n"
            f"→ Backup dans : {backup_dir}",
            border_style="green"
        ))
    else:
        console.print("[blue]ℹ Aucun fichier supprimé[/blue]")

    input(f"\n{yellow}Appuyez sur Entrée pour revenir au menu...{reset}")

def restore_dist_info_backups():
    """
    Permet de restaurer un fichier .dist-info depuis ~/.backup-dist-info vers site-packages.
    """
    import shutil
    import os

    backup_dir = os.path.expanduser("~/.backup-dist-info")
    site_packages = "/data/data/com.termux/files/usr/lib/python3.12/site-packages"

    if not os.path.exists(backup_dir):
        console.print("[red]❌ Aucun dossier de sauvegarde trouvé[/red]")
        return

    backups = sorted(os.listdir(backup_dir))
    if not backups:
        console.print("[yellow]⚠ Aucune sauvegarde .dist-info disponible[/yellow]")
        return

    console.print(Panel("[bold cyan]📦 FICHIERS DISPONIBLES À LA RESTAURATION[/bold cyan]", border_style="blue"))
    for i, b in enumerate(backups, 1):
        console.print(f"[cyan]{i}.[/cyan] {b}")

    console.print(f"\n[cyan]0.[/cyan] Annuler")

    choice = input(f"{yellow}Quel fichier souhaitez-vous restaurer ? (1-{len(backups)} ou 0) : {reset}").strip()
    if not choice.isdigit() or int(choice) < 0 or int(choice) > len(backups):
        console.print("[red]❌ Choix invalide[/red]")
        return
    if choice == "0":
        console.print("[blue]↩ Restauration annulée[/blue]")
        return

    selected = backups[int(choice)-1]
    src = os.path.join(backup_dir, selected)
    dst = os.path.join(site_packages, selected)

    try:
        if os.path.exists(dst):
            console.print(f"[yellow]⚠ Le fichier existe déjà dans site-packages : {selected}[/yellow]")
            overwrite = input(f"{yellow}Remplacer ? [y/n] : {reset}").strip().lower()
            if overwrite not in ["y", "yes", "o", "oui"]:
                console.print("[cyan]↩ Restauration annulée[/cyan]")
                return
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            else:
                os.remove(dst)

        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

        console.print(f"[green]✔ Restauration réussie : {selected}[/green]")

    except Exception as e:
        console.print(f"[red]❌ Erreur de restauration : {e}[/red]")

    input(f"\n{yellow}Appuyez sur Entrée pour revenir au menu...{reset}")

def repair_python_modules():
    from importlib.util import find_spec
    essentials = [
        ("requests", "HTTP"),
        ("colorama", "Couleurs console"),
        ("tqdm", "Barres de progression"),
        ("dnspython", "Requêtes DNS"),
        ("tabulate", "Tableaux"),
        ("rich", "Affichage CLI stylisé"),
        ("pycryptodomex", "Cryptographie isolée"),
        ("beautifulsoup4", "Analyse HTML/XML")
    ]

    console.print(Panel(
        "🔧 VÉRIFICATION DES MODULES\n\nRecherche des modules absents ou cassés...",
        title="RÉPARATION PYTHON", border_style="cyan"
    ))

    missing = []
    for mod, _ in essentials:
        mod_import = "bs4" if mod == "beautifulsoup4" else mod
        if not find_spec(mod_import):
            missing.append(mod)

    if not missing:
        console.print("[green]✅ Aucun module manquant[/green]")
        return
    else:
        console.print(f"[yellow]🔍 Modules à réinstaller : {', '.join(missing)}[/yellow]")

    confirm = input(f"{yellow}⚠ Confirmer la réparation ? [y/n] : {reset}").strip().lower()
    if confirm not in ["y", "yes", "o", "oui"]:
        console.print("[red]❌ Réparation annulée[/red]")
        return

    for mod in missing:
        console.print(f"[cyan]→ Réinstallation de {mod}...[/cyan]")
        result = subprocess.run(f"pip install --upgrade {mod}", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            console.print(f"[green]✔ {mod} installé avec succès[/green]")
        else:
            console.print(f"[red]❌ Erreur : {result.stderr}[/red]")

    input(f"\n{yellow}Appuyez sur Entrée pour continuer...{reset}")
    
def auto_repair_python_environment():
    """
    Réparation complète de l’environnement Python :
    - Supprime les paquets corrompus (~xxx)
    - Réinstalle les modules essentiels manquants
    - Affiche les étapes avec Rich
    """
    from importlib.util import find_spec

    essentials = [
        ("requests", "HTTP"),
        ("colorama", "Console colorée"),
        ("tqdm", "Progress bar"),
        ("dnspython", "DNS"),
        ("tabulate", "Tableaux"),
        ("rich", "Affichage CLI"),
        ("pycryptodome", "Crypto classique"),
        ("pycryptodomex", "Crypto isolée"),
        ("beautifulsoup4", "HTML parsing")
    ]

    site_packages = "/data/data/com.termux/files/usr/lib/python3.12/site-packages"

    console.print(Panel.fit(
        "🛠 [bold cyan]RÉPARATION AUTOMATIQUE DE PYTHON[/bold cyan]\n\n"
        "- Supprime les paquets corrompus (~xxx)\n"
        "- Réinstalle les modules essentiels manquants",
        title="AUTO-REPAIR PYTHON", border_style="blue"
    ))

    confirm = input(f"{yellow}⚠ Confirmer la réparation complète ? [y/n] : {reset}").strip().lower()
    if confirm not in ["y", "yes", "o", "oui"]:
        console.print("[red]❌ Réparation automatique annulée[/red]")
        return

    # 1. Suppression des paquets invalides
    if os.path.exists(site_packages):
        corrupted = [f for f in os.listdir(site_packages) if f.startswith("~")]
        for c in corrupted:
            try:
                full = os.path.join(site_packages, c)
                subprocess.run(f"rm -rf '{full}'", shell=True)
                console.print(f"[green]✔ Supprimé : {c}[/green]")
            except Exception as e:
                console.print(f"[red]❌ Erreur suppression {c}: {e}[/red]")
    else:
        console.print("[yellow]⚠ Dossier site-packages introuvable[/yellow]")

    # 2. Vérification des modules essentiels
    missing = []
    for mod, _ in essentials:
        mod_import = "bs4" if mod == "beautifulsoup4" else mod
        if not find_spec(mod_import):
            missing.append(mod)

    if not missing:
        console.print("[green]✅ Tous les modules essentiels sont présents[/green]")
    else:
        console.print(f"[yellow]🔍 Modules à réinstaller : {', '.join(missing)}[/yellow]")
        for mod in missing:
            console.print(f"[cyan]→ Installation de {mod}...[/cyan]")
            result = subprocess.run(f"pip install --upgrade {mod}", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                console.print(f"[green]✔ {mod} installé avec succès[/green]")
            else:
                console.print(f"[red]❌ Erreur avec {mod} : {result.stderr.strip()}[/red]")

    input(f"\n{yellow}Appuyez sur Entrée pour revenir au menu...{reset}")

def get_folder_size(path):
    """Calcule la taille totale d'un dossier en octets"""
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total

def clean_duplicate_dist_info():
    """
    Supprime les .dist-info obsolètes ou redondants,
    en conservant uniquement la version la plus récente pour chaque module.
    """
    import re
    site_packages = "/data/data/com.termux/files/usr/lib/python3.12/site-packages"

    if not os.path.exists(site_packages):
        console.print("[red]❌ Dossier site-packages introuvable[/red]")
        return

    console.print(Panel(
        "🧹 [bold cyan]NETTOYAGE DES FICHIERS .dist-info[/bold cyan]\n\n"
        "Suppression des métadonnées de modules en double ou anciens",
        title="NETTOYAGE dist-info", border_style="blue"
    ))

    dist_infos = [f for f in os.listdir(site_packages) if f.endswith(".dist-info")]
    modules = {}

    # Regrouper les dist-info par module
    for item in dist_infos:
        match = re.match(r"([a-zA-Z0-9_\-]+)-(\d+(?:\.\d+)+)", item)
        if match:
            name, version = match.groups()
            modules.setdefault(name.lower(), []).append((version, item))

    deleted = []
    for name, versions in modules.items():
        if len(versions) > 1:
            # Trier les versions (ordre naturel)
            versions.sort(key=lambda x: list(map(int, re.findall(r"\d+", x[0]))))
            # Garder la version la plus récente
            to_delete = versions[:-1]
            for _, folder in to_delete:
                full_path = os.path.join(site_packages, folder)
                try:
                    subprocess.run(f"rm -rf '{full_path}'", shell=True)
                    deleted.append(folder)
                    console.print(f"[green]✔ Supprimé : {folder}[/green]")
                except Exception as e:
                    console.print(f"[red]❌ Erreur suppression {folder}: {e}[/red]")

    if not deleted:
        console.print("[green]✅ Aucun doublon détecté ou supprimé[/green]")

    input(f"\n{yellow}Appuyez sur Entrée pour revenir au menu...{reset}")

def backup_termux_alternative():
    """Sauvegarde fiable avec détection automatique du chemin Termux"""
    from rich.progress import (
        Progress, BarColumn, TextColumn, 
        TimeRemainingColumn, TaskProgressColumn
    )
    
    # 1. Détection du chemin Termux (multiples méthodes)
    possible_paths = [
        os.path.expanduser("$PREFIX/../../files"),  # Standard Termux
        "/data/data/com.termux/files",              # Chemin Android
        os.path.expanduser("~/../usr"),             # Alternative
        "/usr/local/lib/termux/files"               # Cas particuliers
    ]
    
    source_dir = None
    for path in possible_paths:
        if os.path.exists(path):
            source_dir = path
            break
    
    if not source_dir:
        console.print(Panel(
            "[red]❌ INSTALLATION TERMUX INTROUVABLE[/red]\n\n"
            "Le script n'a pas pu localiser les fichiers Termux.\n"
            "Essayez cette commande manuelle :\n"
            "[cyan]tar -czf /sdcard/termux_backup.tar.gz /data/data/com.termux/files[/cyan]\n\n"
            "Chemins testés :\n" + 
            "\n".join(f"- {path}" for path in possible_paths),
            border_style="red"
        ))
        input("\nAppuyez sur Entrée pour continuer...")
        return

    # 2. Configuration de la sauvegarde
    backup_dir = "/sdcard/Termux_Backups"
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"termux_full_{timestamp}.tar.gz")

    # 3. Interface utilisateur
    console.print(Panel.fit(
        f"[bold cyan]💾 SAUVEGARDE COMPLÈTE[/bold cyan]\n"
        f"Source : [yellow]{source_dir}[/yellow]\n"
        f"Destination : [cyan]{backup_path}[/cyan]",
        border_style="blue"
    ))

    if not Confirm.ask("  Confirmer la sauvegarde ?", default=False):
        return

    try:
        # 4. Vérification de l'espace
        console.print("[dim]Calcul de l'espace nécessaire...[/dim]")
        size_cmd = f"du -sb {source_dir} | cut -f1"
        try:
            termux_size = int(subprocess.check_output(size_cmd, shell=True, text=True).strip())
        except:
            termux_size = 1000000000  # Valeur par défaut

        free_space = shutil.disk_usage("/sdcard").free
        if termux_size * 1.5 > free_space:
            raise ValueError(
                f"Espace insuffisant\n"
                f"Nécessaire : ~{termux_size*1.5/1024/1024:.1f} MB\n"
                f"Disponible : {free_space/1024/1024:.1f} MB"
            )

        # 5. Sauvegarde avec feedback
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            transient=True
        ) as progress:
            task = progress.add_task("[cyan]Sauvegarde...", total=termux_size)
            
            cmd = f"tar -czf {backup_path} -C {os.path.dirname(source_dir)} {os.path.basename(source_dir)}"
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stderr=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                text=True
            )
            
            # Simulation de progression (tar ne donne pas de vraie progression)
            while proc.poll() is None:
                if os.path.exists(backup_path):
                    progress.update(task, completed=os.path.getsize(backup_path))
                time.sleep(0.5)
            
            if proc.returncode != 0:
                error = proc.stderr.read()
                if "file changed while reading" in error:
                    console.print("[yellow]⚠ Certains fichiers ont été modifiés pendant la sauvegarde[/yellow]")
                raise subprocess.CalledProcessError(proc.returncode, cmd, error)

        # 6. Validation finale
        if os.path.getsize(backup_path) < 100000000:  # 100MB minimum
            raise ValueError(f"Archive trop petite ({os.path.getsize(backup_path)/1024/1024:.1f} MB)")
        
        console.print(Panel(
            f"[bold green]✅ SAUVEGARDE VALIDÉE[/bold green]\n"
            f"• Taille : [cyan]{os.path.getsize(backup_path)/1024/1024:.1f} MB[/cyan]\n"
            f"• Emplacement : [cyan]{backup_path}[/cyan]",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(Panel(
            f"[bold red]❌ ÉCHEC DE SAUVEGARDE[/bold red]\n"
            f"Erreur : {str(e)}\n\n"
            f"[yellow]Solutions :[/yellow]\n"
            f"1. Redémarrez Termux\n"
            f"2. Vérifiez l'espace (df -h)\n"
            f"3. Sauvegarde manuelle :\n"
            f"[dim]tar -czf /sdcard/backup_manual.tar.gz /data/data/com.termux/files[/dim]",
            border_style="red"
        ))
        if os.path.exists(backup_path):
            os.remove(backup_path)
    finally:
        input("\nAppuyez sur Entrée pour continuer...")

def restore_all_dist_info_backups():
    """
    Restaure automatiquement tous les fichiers .dist-info sauvegardés depuis ~/.backup-dist-info.
    """
    import shutil
    import os

    backup_dir = os.path.expanduser("~/.backup-dist-info")
    site_packages = "/data/data/com.termux/files/usr/lib/python3.12/site-packages"

    if not os.path.exists(backup_dir):
        console.print("[red]❌ Aucun dossier de sauvegarde trouvé[/red]")
        return

    files = sorted(os.listdir(backup_dir))
    if not files:
        console.print("[yellow]⚠ Aucun fichier .dist-info à restaurer[/yellow]")
        return

    console.print(Panel(
        f"📦 {len(files)} fichier(s) seront restaurés dans site-packages",
        title="RESTAURATION TOTALE", border_style="cyan"
    ))

    confirm = input(f"{yellow}⚠ Confirmer la restauration de tous les fichiers ? [y/n] : {reset}").strip().lower()
    if confirm not in ["y", "yes", "o", "oui"]:
        console.print("[cyan]↩ Restauration annulée[/cyan]")
        return

    restored = []

    for file in files:
        src = os.path.join(backup_dir, file)
        dst = os.path.join(site_packages, file)

        try:
            if os.path.exists(dst):
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                else:
                    os.remove(dst)

            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

            restored.append(file)
            console.print(f"[green]✔ Restauré : {file}[/green]")

        except Exception as e:
            console.print(f"[red]❌ Erreur restauration {file} : {e}[/red]")

    console.print(Panel(
        f"[bold green]✅ {len(restored)} fichier(s) restauré(s)[/bold green]",
        title="RÉSUMÉ", border_style="green"
    ))

    input(f"\n{yellow}Appuyez sur Entrée pour revenir au menu...{reset}")

def restore_dist_info_menu():
    """
    Menu unique pour restaurer un ou tous les fichiers .dist-info supprimés.
    Options :
    - Restaurer un fichier par numéro
    - Restaurer tous les fichiers [T]
    - Annuler [0]
    """
    import shutil
    import os

    backup_dir = os.path.expanduser("~/.backup-dist-info")
    site_packages = "/data/data/com.termux/files/usr/lib/python3.12/site-packages"

    if not os.path.exists(backup_dir):
        console.print("[red]❌ Aucun dossier de sauvegarde trouvé[/red]")
        return

    backups = sorted(os.listdir(backup_dir))
    if not backups:
        console.print("[yellow]⚠ Aucun fichier .dist-info à restaurer[/yellow]")
        return

    console.print(Panel(
        "[bold cyan]📦 RESTAURATION DE FICHIERS .dist-info[/bold cyan]",
        border_style="blue"
    ))

    for i, b in enumerate(backups, 1):
        console.print(f"[cyan]{i}.[/cyan] {b}")
    console.print("\n[cyan]T.[/cyan] Restaurer tous")
    console.print("[cyan]0.[/cyan] Annuler\n")

    choice = input(f"{yellow}Quel fichier souhaitez-vous restaurer ? (1-{len(backups)}, T, ou 0) : {reset}").strip().upper()

    if choice == "0":
        console.print("[blue]↩ Restauration annulée[/blue]")
        return
    elif choice == "T":
        confirm = input(f"{yellow}⚠ Confirmer la restauration de tous les fichiers ? [y/n] : {reset}").strip().lower()
        if confirm not in ["y", "yes", "o", "oui"]:
            console.print("[cyan]↩ Restauration annulée[/cyan]")
            return

        restored = []
        for f in backups:
            src = os.path.join(backup_dir, f)
            dst = os.path.join(site_packages, f)
            try:
                if os.path.exists(dst):
                    if os.path.isdir(dst):
                        shutil.rmtree(dst)
                    else:
                        os.remove(dst)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                restored.append(f)
                console.print(f"[green]✔ Restauré : {f}[/green]")
            except Exception as e:
                console.print(f"[red]❌ Erreur : {f} → {e}[/red]")

        console.print(Panel(
            f"[bold green]✅ {len(restored)} fichier(s) restauré(s)[/bold green]",
            border_style="green"
        ))
    elif choice.isdigit() and 1 <= int(choice) <= len(backups):
        selected = backups[int(choice) - 1]
        src = os.path.join(backup_dir, selected)
        dst = os.path.join(site_packages, selected)

        if os.path.exists(dst):
            confirm = input(f"{yellow}⚠ Le fichier existe déjà. Remplacer ? [y/n] : {reset}").strip().lower()
            if confirm not in ["y", "yes", "o", "oui"]:
                console.print("[cyan]↩ Restauration annulée[/cyan]")
                return
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            else:
                os.remove(dst)

        try:
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            console.print(f"[green]✔ {selected} restauré avec succès[/green]")
        except Exception as e:
            console.print(f"[red]❌ Erreur : {e}[/red]")
    else:
        console.print("[red]❌ Choix invalide[/red]")

    input(f"\n{yellow}Appuyez sur Entrée pour revenir au menu...{reset}")

def send_notification(title, message, success=True):
    icon = "backup" if success else "warning"
    color = "#4CAF50" if success else "#F44336"
    
    subprocess.run(
        f"""termux-notification \
        -t "{title}" \
        -c "{message}" \
        --icon "{icon}" \
        --led-color "{color}" \
        --priority high""",
        shell=True,
        stderr=subprocess.PIPE
    )

# Exemple d'usage :
send_notification("Backup Termux", "Sauvegarde configs terminée")

# ==============================================
# 3. Gestion des processus en cours
# ==============================================
def kill_running_process(process_name):
    """Termine un processus en cours d'exécution"""
    try:
        result = subprocess.run(f"pidof {process_name}", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split()
            for pid in pids:
                subprocess.run(f"kill -9 {pid}", shell=True)
                log_action("Processus terminé", f"{process_name} (PID:{pid})")
    except Exception as e:
        log_action("Erreur", f"Impossible de terminer {process_name}: {str(e)}")

def show_restore_menu():
    """Menu des options de restauration"""
    menu_options = [
        "[1] Restauration standard", 
        "[2] Restauration des configurations",
        "[3] Restauration brute (tout Termux)",
        "[4] Restauration depuis stockage externe",
        "[5] Retour"
    ]
    
    console.print(Panel(
        "\n".join(menu_options),
        title="[bold cyan]MENU DE RESTAURATION[/bold cyan]",
        border_style="yellow"
    ))
    
# ==========. SAUVEGARDE ET RESTAURATION =======================

def backup_termux():
    """Sauvegarde COMPLÈTE et FIABLE de Termux"""
    from datetime import datetime
    import tarfile
    import subprocess

    # 1. Configuration
    backup_dir = os.path.expanduser("~/.termux_backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"termux_full_{timestamp}.tar.gz"
    backup_path = os.path.join(backup_dir, backup_name)

    # 2. Préparation des éléments à sauvegarder
    essential_items = [
        # Fichiers de configuration
        "~/.termux",
        "~/.bashrc",
        "~/.zshrc",
        "~/.profile",
        "~/.vimrc",
        "~/.gitconfig",
        
        # Dossiers importants
        "~/.config",
        "~/.ssh",
        "~/.local/share",
        "~/bin",
        "~/scripts",
        "~/projects",
        
        # Données Termux
        "~/../usr/etc/termux",
        "~/../usr/var/lib/termux"
    ]

    # 3. Vérification des éléments
    console.print(Panel("[bold]VÉRIFICATION DES FICHIERS[/bold]", style="blue"))
    valid_items = []
    for item in essential_items:
        path = os.path.expanduser(item)
        if os.path.exists(path):
            size = get_folder_size(path) if os.path.isdir(path) else os.path.getsize(path)
            valid_items.append((path, os.path.basename(path), size))
            console.print(f"[green]✓ {item.ljust(20)} ({human_size(size)})[/green]")
        else:
            console.print(f"[yellow]⚠ {item.ljust(20)} (absent)[/yellow]")

    if not valid_items:
        console.print("[red]❌ Aucun élément valide à sauvegarder ![/red]")
        return

    # 4. Sauvegarde des paquets
    console.print("[cyan]→ Sauvegarde de la liste des paquets...[/cyan]")
    pkg_list_path = os.path.join(backup_dir, f"pkg_list_{timestamp}.txt")
    with open(pkg_list_path, "w") as f:
        subprocess.run("pkg list-installed", shell=True, stdout=f)

    # 5. Création de l'archive
    total_size = sum(item[2] for item in valid_items)
    console.print(Panel(
        f"[bold]DÉBUT DE LA SAUVEGARDE COMPLÈTE[/bold]\n"
        f"• Destination: [cyan]{backup_path}[/cyan]\n"
        f"• Taille estimée: [yellow]{human_size(total_size)}[/yellow]\n"
        f"• Éléments inclus: {len(valid_items)}",
        style="blue"
    ))

    try:
        with Progress() as progress:
            task = progress.add_task("[cyan]Création de l'archive...", total=total_size)
            
            with tarfile.open(backup_path, "w:gz") as tar:
                # Ajouter les fichiers/dossiers
                for path, arcname, size in valid_items:
                    if os.path.isdir(path):
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                rel_path = os.path.join(arcname, os.path.relpath(file_path, path))
                                tar.add(file_path, arcname=rel_path)
                                progress.update(task, advance=os.path.getsize(file_path))
                    else:
                        tar.add(path, arcname=arcname)
                        progress.update(task, advance=size)
                
                # Ajouter la liste des paquets
                tar.add(pkg_list_path, arcname="pkg_list.txt")

        # Vérification finale
        if os.path.getsize(backup_path) == 0:
            raise ValueError("Archive vide créée")

        # Rapport
        console.print(Panel(
            f"[bold green]✅ SAUVEGARDE COMPLÈTE RÉUSSIE[/bold green]\n\n"
            f"• Fichier: [cyan]{backup_name}[/cyan]\n"
            f"• Taille: [yellow]{human_size(os.path.getsize(backup_path))}[/yellow]\n"
            f"• Contenu: {len(valid_items)} éléments + liste des paquets\n"
            f"• Emplacement: {backup_dir}",
            border_style="green"
        ))

    except Exception as e:
        console.print(Panel(
            f"[bold red]❌ ÉCHEC DE SAUVEGARDE[/bold red]\n\n"
            f"Erreur: {str(e)}\n"
            f"Chemin: {backup_path}",
            border_style="red"
        ))
        if os.path.exists(backup_path):
            os.remove(backup_path)
        if os.path.exists(pkg_list_path):
            os.remove(pkg_list_path)
        return

    # Nettoyage
    if os.path.exists(pkg_list_path):
        os.remove(pkg_list_path)

    # Vérification supplémentaire
    is_valid, msg = verify_backup(backup_path)
    if is_valid:
        console.print(f"[green]✓ Vérification: {msg}[/green]")
    else:
        console.print(f"[red]❌ Problème détecté: {msg}[/red]")

    input("\nAppuyez sur Entrée pour continuer...")

def backup_termux_standard():
    """Sauvegarde standard complète avec exclusions intelligentes et vérifications"""
    try:
        home = os.path.expanduser("~")
        backup_dir = os.path.join(home, ".termux_backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"termux_std_{timestamp}.tar.gz")

        # 1. Configuration des exclusions
        EXCLUDE_PATTERNS = [
            '*.tmp', '*.log', '*cache*',
            '*.thumbnails*', '/Android/*',
            '/.cache/*', '/temp/*', '/.termux_backups/*'
        ]

        # 2. Recherche des fichiers utilisateur
        console.print("[cyan]🔍 Recherche des fichiers à sauvegarder...[/cyan]")
        cmd = f"""
        find {home} -type f \
            ! -path '{home}/.termux_backups/*' \
            ! -path '{home}/../usr/*' \
            -print0
        """
        try:
            files = subprocess.check_output(cmd, shell=True, executable='/bin/bash', text=True).split('\0')[:-1]
            files = [f for f in files if not any(fnmatch.fnmatch(f, p) for p in EXCLUDE_PATTERNS)]
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Erreur recherche fichiers : {e.stderr}")

        if not files:
            raise ValueError("Aucun fichier utilisateur valide trouvé")

        # 3. Estimation de la taille
        total_size = sum(os.path.getsize(f) for f in files if os.path.isfile(f)) / (1024**2)
        console.print(f"[yellow]ℹ Taille estimée : {total_size:.1f} MB[/yellow]")

        # 4. Création de l'archive avec barre de progression
        with Progress() as progress:
            task = progress.add_task("[green]Création de l'archive...", total=len(files))
            
            with tarfile.open(backup_file, "w:gz") as tar:
                for file_path in files:
                    try:
                        if os.path.exists(file_path) and os.path.isfile(file_path):
                            arcname = os.path.relpath(file_path, home)
                            tar.add(file_path, arcname=f"termux_backup/{arcname}")
                    except Exception as e:
                        logging.warning(f"Erreur ajout {file_path} : {str(e)}")
                    progress.update(task, advance=1)

        # 5. Vérification finale
        if os.path.getsize(backup_file) < 10240:  # 10KB minimum
            raise ValueError("Archive trop petite - vérifiez les exclusions")

        # 6. Nettoyage auto et notification
        cleanup_backups()
        send_notification("Termux Backup", f"Sauvegarde réussie ({len(files)} fichiers)")

        # Rapport final
        console.print(Panel(
            f"[bold green]✅ SAUVEGARDE STANDARD RÉUSSIE[/bold green]\n"
            f"• Fichiers : [cyan]{len(files)}[/cyan]\n"
            f"• Taille : [yellow]{os.path.getsize(backup_file)/1024/1024:.1f} MB[/yellow]\n"
            f"• Exclusions : [dim]{', '.join(EXCLUDE_PATTERNS[:3])}...[/dim]\n"
            f"• Emplacement : [cyan]{backup_file}[/cyan]",
            border_style="green"
        ))

    except Exception as e:
        console.print(Panel(
            f"[bold red]❌ ÉCHEC DE SAUVEGARDE[/bold red]\n"
            f"Erreur : {str(e)}\n\n"
            f"[yellow]CONSEILS :[/yellow]\n"
            f"1. Vérifiez 'ls -la ~'\n"
            f"2. Espace disque libre : {shutil.disk_usage('/').free/(1024**3):.1f} GB\n"
            f"3. Testez : find ~ -type f | wc -l",
            border_style="red"
        ))
        if 'backup_file' in locals() and os.path.exists(backup_file):
            os.remove(backup_file)
        send_notification("Termux Backup", "Échec de sauvegarde", success=False)

def list_user_files():
    """Liste les fichiers utilisateur pour debug"""
    home = os.path.expanduser("~")
    console.print(Panel(f"[bold]CONTENUT DU DOSSIER UTILISATEUR ({home}):[/bold]"))
    
    # Liste détaillée avec ls
    try:
        result = subprocess.run(f"ls -la {home}", shell=True, 
                              capture_output=True, text=True)
        console.print(result.stdout)
        
        # Vérification des dossiers clés
        for dir in [".termux", "scripts", "bin"]:
            path = os.path.join(home, dir)
            if os.path.exists(path):
                console.print(f"\n[bold]{dir}:[/bold]")
                console.print(subprocess.run(f"ls -la {path}", shell=True,
                                          capture_output=True, text=True).stdout)
    except Exception as e:
        console.print(f"[red]Erreur ls: {str(e)}[/red]")

def human_size(size):
    """Formatage lisible des tailles"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def verify_backup(backup_path):
    """Vérifie structure et contenu de l'archive"""
    try:
        with tarfile.open(backup_path) as tar:
            members = tar.getmembers()
            if not members:
                raise ValueError("Archive vide")
            
            # Vérifie la présence d'au moins un fichier de config
            config_files = [m for m in members if 'termux_configs' in m.path]
            if not config_files and 'cfg_' in backup_path:
                raise ValueError("Aucune configuration trouvée")
            
            # Test d'extraction d'un fichier
            test_file = next((m for m in members if m.isfile()), None)
            if test_file:
                tar.extractfile(test_file).read(16)  # Lit les premiers octets
        return True, "Archive valide"
    except Exception as e:
        return False, f"Erreur vérification : {str(e)}"

def estimate_backup_size(files):
    total = 0
    with Progress() as progress:
        task = progress.add_task("[cyan]Calcul de la taille...", total=len(files))
        
        for f in files:
            if os.path.islink(f):
                continue
                
            if os.path.isfile(f):
                total += os.path.getsize(f)
            elif os.path.isdir(f):
                for root, _, files in os.walk(f):
                    for file in files:
                        fp = os.path.join(root, file)
                        if not is_excluded(fp):
                            total += os.path.getsize(fp)
            progress.update(task, advance=1)
    
    size_mb = total / (1024 ** 2)
    console.print(f"\n[bold]Taille estimée :[/bold] {size_mb:.1f} MB")
    return size_mb
        
def convert_to_zip(tar_path, delete_original=False):
    """Convertit .tar.gz en .zip avec gestion des erreurs"""
    if not tar_path.endswith('.tar.gz'):
        raise ValueError("Format .tar.gz requis")
    
    zip_path = tar_path.replace('.tar.gz', '.zip')
    
    try:
        with tarfile.open(tar_path, 'r:gz') as tar:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for member in tar.getmembers():
                    if member.isfile() and not is_excluded(member.name):
                        try:
                            data = tar.extractfile(member).read()
                            zipf.writestr(member.name, data)
                        except Exception as e:
                            logging.warning(f"Erreur conversion {member.name}: {str(e)}")
        
        if delete_original and os.path.exists(zip_path):
            os.remove(tar_path)
            
        return zip_path
    except Exception as e:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        raise e
        
def cleanup_backups(backup_dir, max_count=5, max_size_gb=2):
    """Nettoie les anciennes sauvegardes selon 2 critères"""
    backups = sorted(
        glob.glob(f"{backup_dir}/*.tar.gz*") + glob.glob(f"{backup_dir}/*.zip*"),
        key=os.path.getmtime
    )
    
    # Critère 1: Nombre maximum
    if len(backups) > max_count:
        for old in backups[:-(max_count)]:
            os.remove(old)
            logging.info(f"Supprimé (max_count): {os.path.basename(old)}")
    
    # Critère 2: Taille totale
    backups = sorted(
        glob.glob(f"{backup_dir}/*.tar.gz*") + glob.glob(f"{backup_dir}/*.zip*"),
        key=os.path.getmtime
    )
    total_size = sum(os.path.getsize(f) for f in backups) / (1024**3)
    
    while total_size > max_size_gb and len(backups) > 1:
        oldest = backups.pop(0)
        size_gb = os.path.getsize(oldest) / (1024**3)
        os.remove(oldest)
        total_size -= size_gb
        logging.info(f"Supprimé (max_size): {os.path.basename(oldest)} ({size_gb:.2f} GB)")

EXCLUDE_PATTERNS = [
    '*.tmp', '*.log', '*cache*',
    '*.thumbnails*', '/Android/*',
    '/.cache/*', '/temp/*'
]

def should_exclude(path):
    """Détermine si un fichier doit être exclu"""
    path = os.path.normpath(path)
    return any(
        fnmatch.fnmatch(path, pattern) or 
        fnmatch.fnmatch(os.path.basename(path), pattern)
        for pattern in EXCLUDE_PATTERNS
    )
        
def restore_termux():
    """
    Restaure une sauvegarde complète de Termux
    """
    backup_dir = os.path.expanduser("~/.termux_backups")
    
    if not os.path.exists(backup_dir):
        console.print("[red]❌ Aucun dossier de sauvegarde trouvé[/red]")
        return
    
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.startswith("termux_backup_") and f.endswith(".tar.gz")],
        reverse=True
    )
    
    if not backups:
        console.print("[yellow]⚠ Aucune sauvegarde disponible[/yellow]")
        return
    
    console.print(Panel.fit(
        "[bold cyan]🔄 RESTAURATION DE TERMUX[/bold cyan]\n\n"
        "Cette opération va :\n"
        "• Extraire les fichiers utilisateur\n"
        "• Réinstaller les paquets (manuellement)\n"
        "• Remplacer les fichiers existants",
        title="RESTAURATION", border_style="blue"
    ))
    
    # Affichage des sauvegardes disponibles
    console.print("[bold]Sauvegardes disponibles :[/bold]")
    for i, backup in enumerate(backups, 1):
        size = os.path.getsize(os.path.join(backup_dir, backup)) / (1024*1024)
        console.print(f"[cyan]{i}.[/cyan] {backup} ({size:.2f} MB)")
    
    console.print(f"\n[cyan]0.[/cyan] Annuler")
    
    # Choix de la sauvegarde
    choice = input(f"{yellow}Choisissez une sauvegarde à restaurer (1-{len(backups)} ou 0) : {reset}").strip()
    if not choice.isdigit() or int(choice) < 0 or int(choice) > len(backups):
        console.print("[red]❌ Choix invalide[/red]")
        return
    if choice == "0":
        console.print("[blue]↩ Restauration annulée[/blue]")
        return
    
    selected_backup = backups[int(choice)-1]
    backup_path = os.path.join(backup_dir, selected_backup)
    pkg_list = backup_path.replace(".tar.gz", "_pkg_list.txt")
    
    if not confirm_action(f"RESTAURER la sauvegarde {selected_backup} (cela écrasera les fichiers existants)"):
        console.print("[red]❌ Restauration annulée[/red]")
        return
    
    # 1. Restauration des fichiers
    console.print("[cyan]→ Extraction des fichiers utilisateur...[/cyan]")
    try:
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(path=os.path.expanduser("~"))
        console.print("[green]✔ Fichiers restaurés avec succès[/green]")
    except Exception as e:
        console.print(f"[red]❌ Erreur lors de l'extraction : {str(e)}[/red]")
        return
    
    # 2. Réinstallation des paquets (manuellement)
    if os.path.exists(pkg_list):
        console.print(Panel.fit(
            "[bold yellow]📦 PAQUETS À REINSTALLER MANUELLEMENT[/bold yellow]\n\n"
            f"La liste des paquets est disponible dans :\n{pkg_list}\n"
            "Vous pouvez les réinstaller avec :\n"
            "`pkg install $(cat pkg_list.txt | awk '{print $1}')`",
            border_style="yellow"
        ))
    else:
        console.print("[yellow]⚠ Liste des paquets introuvable - vérifiez {pkg_list}[/yellow]")
    
    console.print(Panel(
        "[bold green]✅ RESTAURATION TERMINÉE[/bold green]\n"
        "Il est recommandé de redémarrer Termux",
        border_style="green"
    ))
    
    input(f"\n{yellow}Appuyez sur Entrée pour continuer...{reset}")

def backup_configs_only():
    """Sauvegarde robuste des configurations système essentielles"""
    try:
        home = os.path.expanduser("~")
        backup_dir = os.path.join(home, ".termux_backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"termux_cfg_{timestamp}.tar.gz")

        # 1. Liste exhaustive des configurations critiques
        CONFIG_PATHS = [
            ".termux", ".bashrc", ".zshrc", ".profile", ".vimrc",
            ".gitconfig", ".ssh", ".nanorc", ".tmux.conf",
            "../usr/etc/termux"
        ]

        # 2. Vérification et validation des fichiers
        valid_configs = []
        for path in CONFIG_PATHS:
            full_path = os.path.join(home, path)
            
            if os.path.exists(full_path):
                if os.path.isdir(full_path):
                    # Vérifie que le dossier n'est pas vide
                    if any(os.scandir(full_path)):
                        valid_configs.append(full_path)
                else:
                    # Vérifie que le fichier a du contenu
                    if os.path.getsize(full_path) > 0:
                        valid_configs.append(full_path)

        if not valid_configs:
            raise ValueError("Aucune configuration valide trouvée")

        # 3. Création de l'archive avec vérification en temps réel
        with tarfile.open(backup_file, "w:gz") as tar:
            for config_path in valid_configs:
                arcname = os.path.relpath(config_path, home)
                try:
                    tar.add(config_path, arcname=f"termux_configs/{arcname}")
                except Exception as e:
                    logging.warning(f"Erreur ajout {config_path} : {str(e)}")

        # 4. Vérification d'intégrité stricte
        is_valid, msg = verify_backup(backup_file)
        if not is_valid:
            raise ValueError(msg)

        # 5. Rapport et notification
        console.print(Panel(
            f"[bold green]✅ SAUVEGARDE CONFIGS RÉUSSIE[/bold green]\n"
            f"• Configurations : [cyan]{len(valid_configs)}[/cyan]\n"
            f"• Taille : [yellow]{os.path.getsize(backup_file)/1024:.1f} KB[/yellow]\n"
            f"• Contenu :\n[dim]{chr(10).join(os.path.basename(c) for c in valid_configs)}[/dim]",
            border_style="green"
        ))
        send_notification("Termux Configs", "Sauvegarde configs terminée")

    except Exception as e:
        console.print(Panel(
            f"[bold red]❌ ÉCHEC SAUVEGARDE CONFIGS[/bold red]\n"
            f"Erreur : {str(e)}\n\n"
            f"[yellow]VÉRIFIEZ :[/yellow]\n"
            f"1. ~/.termux/ existe\n"
            f"2. ~/.bashrc a du contenu\n"
            f"3. Permissions en lecture",
            border_style="red"
        ))
        if 'backup_file' in locals() and os.path.exists(backup_file):
            os.remove(backup_file)
        send_notification("Termux Configs", "Échec sauvegarde", success=False)
            
def incremental_backup():
    """Sauvegarde incrémentielle ultra-fiable des fichiers modifiés"""
    try:
        home = os.path.expanduser("~")
        backup_dir = os.path.join(home, ".termux_backups/incremental")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"incr_{timestamp}.tar.gz")

        # 1. Déterminer la date de la dernière sauvegarde
        last_backup = 0
        if os.path.exists(backup_dir):
            backups = [f for f in os.listdir(backup_dir) if f.startswith("incr_") and f.endswith(".tar.gz")]
            if backups:
                last_backup = os.path.getmtime(os.path.join(backup_dir, max(backups)))

        # 2. Liste des exclusions (dossiers système et cache)
        exclude_patterns = [
            '/.cache/*', '/.termux_backups/*', '/.local/*',
            '/../usr/*', '/tmp/*', '/.android/*', '/Android/*'
        ]

        # 3. Recherche des fichiers modifiés depuis la dernière sauvegarde
        console.print("[cyan]🔍 Recherche des fichiers modifiés...[/cyan]")
        find_cmd = f"""
        find {home} -type f \
            ! -path '{home}/.cache/*' \
            ! -path '{home}/.termux_backups/*' \
            ! -path '{home}/.local/*' \
            ! -path '{home}/../usr/*' \
            ! -path '{home}/tmp/*' \
            ! -path '{home}/.android/*' \
            ! -path '{home}/Android/*' \
            -newermt '@{last_backup}' -print0
        """
        modified_files = subprocess.check_output(
            find_cmd, shell=True, executable='/bin/bash', text=True
        ).split('\0')[:-1]

        if not modified_files:
            console.print("[yellow]ℹ Aucun fichier modifié depuis la dernière sauvegarde[/yellow]")
            return

        # 4. Création de l'archive incrémentielle
        console.print(f"[cyan]📦 Création de l'archive ({len(modified_files)} fichiers modifiés)...[/cyan]")
        
        # Fichier index pour le suivi
        index_file = os.path.join(backup_dir, f"incr_{timestamp}.index")
        with open(index_file, 'w') as f:
            f.write("\n".join(modified_files))

        with tarfile.open(backup_file, "w:gz") as tar:
            # Ajout des fichiers modifiés
            for file_path in modified_files:
                if os.path.exists(file_path):  # Double vérification
                    arcname = os.path.relpath(file_path, home)
                    tar.add(file_path, arcname=arcname)
            
            # Ajout du fichier index
            tar.add(index_file, arcname="backup.index")
        
        os.remove(index_file)  # Nettoyage

        # 5. Vérification finale
        archive_size = os.path.getsize(backup_file) / (1024 * 1024)  # en MB
        if archive_size < 0.01:  # Au moins 10KB
            raise ValueError(f"Archive trop petite ({archive_size:.2f} MB)")

        # Rapport complet
        console.print(Panel(
            f"[bold green]✅ SAUVEGARDE INCRÉMENTIELLE RÉUSSIE[/bold green]\n"
            f"• Fichiers : {len(modified_files)}\n"
            f"• Taille : {archive_size:.2f} MB\n"
            f"• Période : depuis {datetime.fromtimestamp(last_backup).strftime('%d/%m/%Y %H:%M') if last_backup else 'jamais'}\n"
            f"• Exclusions : {' '.join(exclude_patterns)}\n"
            f"• Emplacement : [cyan]{backup_file}[/cyan]",
            border_style="green"
        ))

        # 6. Nettoyage des anciennes sauvegardes (garder les 5 dernières)
        backups = sorted(
            [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) 
             if f.startswith("incr_") and f.endswith(".tar.gz")],
            key=os.path.getmtime
        )
        for old_backup in backups[:-5]:  # Garder seulement les 5 plus récentes
            os.remove(old_backup)
            console.print(f"[dim]🗑 Nettoyage : {os.path.basename(old_backup)}[/dim]")

    except subprocess.CalledProcessError as e:
        console.print(Panel(
            f"[bold red]❌ ERREUR DE RECHERCHE[/bold red]\n"
            f"Commande : {e.cmd}\n"
            f"Sortie : {e.stderr if e.stderr else 'Aucun message'}",
            border_style="red"
        ))
    except Exception as e:
        console.print(Panel(
            f"[bold red]❌ ERREUR DE SAUVEGARDE[/bold red]\n"
            f"Type : {type(e).__name__}\n"
            f"Message : {str(e)}\n\n"
            f"[yellow]DIAGNOSTIC :[/yellow]\n"
            f"1. Vérifiez l'espace disque\n"
            f"2. Testez la commande :\n"
            f"   find ~ -type f -newermt '2024-05-20' | wc -l\n"
            f"3. Vérifiez les permissions",
            border_style="red"
        ))
        # Nettoyage en cas d'échec
        if 'backup_file' in locals() and os.path.exists(backup_file):
            os.remove(backup_file)
        if 'index_file' in locals() and os.path.exists(index_file):
            os.remove(index_file)

def backup_to_external():
    """Sauvegarde vers le stockage externe - Version améliorée"""
    try:
        console.print(Panel.fit(
            "[bold cyan]📤 SAUVEGARDE VERS STOCKAGE EXTERNE[/bold cyan]\n\n"
            "Cette opération va :\n"
            "- Copier les fichiers essentiels vers le stockage externe\n"
            "- Créer une archive compressée\n"
            "- Vérifier l'intégrité de la sauvegarde",
            border_style="blue"
        ))

        # 1. Vérification du stockage externe
        storage_path = os.path.expanduser("~/storage/shared")
        if not os.path.exists(storage_path):
            console.print(Panel(
                "[red]❌ STOCKAGE NON CONFIGURÉ[/red]\n\n"
                "Exécutez d'abord :\n"
                "[bold green]termux-setup-storage[/bold green]\n"
                "Et autorisez l'accès au stockage",
                border_style="red"
            ))
            if Confirm.ask("[yellow]Configurer maintenant ?[/yellow]"):
                subprocess.run("termux-setup-storage", shell=True, check=True)
                console.print("[green]✔ Redémarrez le script après configuration[/green]")
            return

        # 2. Création du dossier de sauvegarde
        backup_dir = os.path.join(storage_path, "Termux_Backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # 3. Liste des éléments essentiels à sauvegarder (avec vérification)
        essential_items = [
            # Fichiers de configuration
            ("~/.termux", "dossier de configuration Termux"),
            ("~/.bashrc", "configuration Bash"),
            ("~/.zshrc", "configuration Zsh"),
            ("~/.profile", "profile shell"),
            ("~/.vimrc", "configuration Vim"),
            
            # Dossiers importants
            ("~/.ssh", "clés SSH"),
            ("~/bin", "scripts utilisateur"),
            ("~/scripts", "scripts personnels"),
            
            # Fichiers Termux système
            ("~/../usr/etc/termux", "configuration système Termux")
        ]

        # Filtrage des éléments existants
        valid_items = []
        for path, desc in essential_items:
            expanded = os.path.expanduser(path)
            if os.path.exists(expanded):
                size = get_folder_size(expanded) if os.path.isdir(expanded) else os.path.getsize(expanded)
                valid_items.append((expanded, os.path.basename(expanded), size, desc))
                console.print(f"[green]✓ {path.ljust(15)} ({human_size(size)}) - {desc}[/green]")
            else:
                console.print(f"[yellow]✗ {path.ljust(15)} (absent) - {desc}[/yellow]")

        if not valid_items:
            console.print(Panel(
                "[red]❌ AUCUN ÉLÉMENT VALIDE À SAUVEGARDER[/red]\n"
                "Vérifiez que vous avez des fichiers de configuration",
                border_style="red"
            ))
            return

        # 4. Création de l'archive
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"termux_ext_{timestamp}.tar.gz")
        
        console.print(Panel.fit(
            f"[cyan]📦 CRÉATION DE L'ARCHIVE ({len(valid_items)} éléments)[/cyan]\n"
            f"Destination : [bold]{backup_file}[/bold]",
            border_style="cyan"
        ))

        try:
            with tarfile.open(backup_file, "w:gz") as tar:
                for full_path, arcname, _, _ in valid_items:
                    tar.add(full_path, arcname=arcname)
                    console.print(f"[dim]→ Ajouté : {arcname}[/dim]")

            # Vérification de la taille minimale
            if os.path.getsize(backup_file) < 1024:  # 1KB minimum
                raise ValueError("Archive trop petite - vérifiez les fichiers sources")

            # Vérification d'intégrité
            with tarfile.open(backup_file) as test:
                if not test.getnames():
                    raise ValueError("Archive vide")

            console.print(Panel(
                f"[bold green]✅ SAUVEGARDE EXTERNE RÉUSSIE[/bold green]\n\n"
                f"• Fichier : [cyan]{os.path.basename(backup_file)}[/cyan]\n"
                f"• Taille : [yellow]{human_size(os.path.getsize(backup_file))}[/yellow]\n"
                f"• Emplacement : [cyan]{backup_file}[/cyan]",
                border_style="green"
            ))

            # Notification Android
            send_notification(
                "Termux Backup", 
                f"Sauvegarde externe réussie ({len(valid_items)} éléments)"
            )

        except Exception as e:
            console.print(Panel(
                f"[bold red]❌ ÉCHEC DE CRÉATION DE L'ARCHIVE[/bold red]\n"
                f"Erreur : {str(e)}",
                border_style="red"
            ))
            if os.path.exists(backup_file):
                os.remove(backup_file)
            send_notification("Termux Backup", "Échec sauvegarde externe", success=False)

    except PermissionError:
        console.print(Panel(
            "[red]❌ PERMISSION REFUSÉE[/red]\n\n"
            "Autorisations nécessaires :\n"
            "1. Accès au stockage externe\n"
            "2. Exécutez 'termux-setup-storage'",
            border_style="red"
        ))
    except Exception as e:
        console.print(Panel(
            f"[red]❌ ERREUR INATTENDUE[/red]\n"
            f"Type : {type(e).__name__}\n"
            f"Message : {str(e)}",
            border_style="red"
        ))

    input("\nAppuyez sur Entrée pour continuer...")

def get_free_space(path):
    """Retourne l'espace disque disponible en GB"""
    try:
        stat = os.statvfs(path)
        return (stat.f_bavail * stat.f_frsize) / (1024**3)
    except:
        return 0

def manage_backups():
    """Menu de gestion des sauvegardes"""
    while True:
        console.print(Panel(
            "[bold cyan]🗂 GESTION DES SAUVEGARDES[/bold cyan]\n\n"
            "Choisissez une action :\n"
            "[1] Lister les sauvegardes\n"
            "[2] Supprimer des sauvegardes\n"
            "[3] Vérifier l'intégrité d'une sauvegarde\n"
            "[4] Retour au menu principal",
            border_style="blue"
        ))

        choice = get_choice(1, 4)

        if choice == 1:
            list_backups()
        elif choice == 2:
            delete_backups()
        elif choice == 3:
            verify_existing_backup()
        elif choice == 4:
            break

        input(f"\n{yellow}Appuyez sur Entrée pour continuer...{reset}")

def list_backups():
    """Liste toutes les sauvegardes disponibles"""
    backup_locations = [
        os.path.expanduser("~/.termux_backups"),
        os.path.expanduser("~/storage/shared/Termux_Backups")
    ]

    console.print(Panel(
        "[bold cyan]📂 SAUVEGARDES DISPONIBLES[/bold cyan]",
        border_style="blue"
    ))

    found = False
    for location in backup_locations:
        if os.path.exists(location):
            backups = sorted(
                [f for f in os.listdir(location) if f.startswith(("termux_backup_", "termux_ext_", "termux_config_"))],
                reverse=True
            )
            
            if backups:
                found = True
                console.print(f"\n[bold]Emplacement : {location}[/bold]")
                for i, backup in enumerate(backups, 1):
                    size = os.path.getsize(os.path.join(location, backup)) / (1024*1024)
                    console.print(f"[cyan]{i}.[/cyan] {backup} ({size:.2f} MB)")

    if not found:
        console.print("[yellow]ℹ Aucune sauvegarde trouvée[/yellow]")

def delete_backups():
    """Supprime des sauvegardes existantes"""
    backup_locations = [
        os.path.expanduser("~/.termux_backups"),
        os.path.expanduser("~/storage/shared/Termux_Backups")
    ]

    all_backups = []
    for location in backup_locations:
        if os.path.exists(location):
            backups = sorted(
                [os.path.join(location, f) for f in os.listdir(location) 
                 if f.startswith(("termux_backup_", "termux_ext_", "termux_config_"))],
                reverse=True
            )
            all_backups.extend(backups)

    if not all_backups:
        console.print("[yellow]ℹ Aucune sauvegarde à supprimer[/yellow]")
        return

    console.print(Panel(
        "[bold red]🗑 SUPPRESSION DE SAUVEGARDES[/bold red]\n\n"
        "Sélectionnez les sauvegardes à supprimer :",
        border_style="red"
    ))

    for i, backup in enumerate(all_backups, 1):
        size = os.path.getsize(backup) / (1024*1024)
        console.print(f"[cyan]{i}.[/cyan] {os.path.basename(backup)} ({size:.2f} MB) - {os.path.dirname(backup)}")

    console.print(f"\n[cyan]0.[/cyan] Annuler")
    console.print(f"[cyan]T.[/cyan] Tout supprimer")

    choices = input(f"{yellow}Choix (numéros séparés par des virgules, 0 ou T) : {reset}").strip().upper()

    if choices == "0":
        console.print("[blue]↩ Annulé[/blue]")
        return
    elif choices == "T":
        if confirm_action("SUPPRIMER TOUTES LES SAUVEGARDES (action irréversible)"):
            deleted = 0
            for backup in all_backups:
                try:
                    os.remove(backup)
                    deleted += 1
                    console.print(f"[green]✔ Supprimé : {os.path.basename(backup)}[/green]")
                except Exception as e:
                    console.print(f"[red]❌ Erreur : {os.path.basename(backup)} - {str(e)}[/red]")
            
            console.print(Panel(
                f"[bold green]✅ {deleted} SAUVEGARDES SUPPRIMÉES[/bold green]",
                border_style="green"
            ))
    else:
        try:
            indexes = [int(i.strip()) - 1 for i in choices.split(",")]
            to_delete = [all_backups[i] for i in indexes if 0 <= i < len(all_backups)]
            
            if not to_delete:
                console.print("[red]❌ Aucune sauvegarde valide sélectionnée[/red]")
                return
            
            console.print(Panel(
                "[bold red]⚠ SAUVEGARDES SÉLECTIONNÉES :[/bold red]\n" +
                "\n".join([os.path.basename(b) for b in to_delete]),
                border_style="red"
            ))
            
            if confirm_action(f"Supprimer {len(to_delete)} sauvegarde(s)"):
                deleted = 0
                for backup in to_delete:
                    try:
                        os.remove(backup)
                        deleted += 1
                        console.print(f"[green]✔ Supprimé : {os.path.basename(backup)}[/green]")
                    except Exception as e:
                        console.print(f"[red]❌ Erreur : {os.path.basename(backup)} - {str(e)}[/red]")
                
                console.print(Panel(
                    f"[bold green]✅ {deleted}/{len(to_delete)} SAUVEGARDES SUPPRIMÉES[/bold green]",
                    border_style="green"
                ))
        except ValueError:
            console.print("[red]❌ Sélection invalide[/red]")

def verify_existing_backup():
    """Vérifie l'intégrité d'une sauvegarde existante"""
    backup_locations = [
        os.path.expanduser("~/.termux_backups"),
        os.path.expanduser("~/storage/shared/Termux_Backups")
    ]

    all_backups = []
    for location in backup_locations:
        if os.path.exists(location):
            backups = sorted(
                [os.path.join(location, f) for f in os.listdir(location) 
                 if f.endswith(".tar.gz")],
                reverse=True
            )
            all_backups.extend(backups)

    if not all_backups:
        console.print("[yellow]ℹ Aucune sauvegarde à vérifier[/yellow]")
        return

    console.print(Panel(
        "[bold cyan]🔍 VÉRIFICATION DE SAUVEGARDE[/bold cyan]",
        border_style="blue"
    ))

    for i, backup in enumerate(all_backups, 1):
        size = os.path.getsize(backup) / (1024*1024)
        console.print(f"[cyan]{i}.[/cyan] {os.path.basename(backup)} ({size:.2f} MB) - {os.path.dirname(backup)}")

    console.print(f"\n[cyan]0.[/cyan] Annuler")

    choice = input(f"{yellow}Choisissez une sauvegarde à vérifier : {reset}").strip()
    if choice == "0":
        return

    try:
        selected = all_backups[int(choice)-1]
        is_valid, msg = verify_backup(selected)
        
        if is_valid:
            console.print(Panel(
                f"[bold green]✅ SAUVEGARDE VALIDE[/bold green]\n\n"
                f"• Fichier : {os.path.basename(selected)}\n"
                f"• Emplacement : {os.path.dirname(selected)}\n"
                f"• Résultat : {msg}",
                border_style="green"
            ))
        else:
            console.print(Panel(
                f"[bold red]❌ SAUVEGARDE CORROMPUE[/bold red]\n\n"
                f"• Fichier : {os.path.basename(selected)}\n"
                f"• Problème : {msg}",
                border_style="red"
            ))
    except Exception as e:
        console.print(f"[red]❌ Erreur : {str(e)}[/red]")

# ========== Nouvelles fonctions de restauration ==========

def restore_configs_only():
    """Restaure seulement les fichiers de configuration"""
    backup_dir = os.path.expanduser("~/.termux_backups")
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.startswith("termux_configs_")],
        reverse=True
    )
    
    if not backups:
        console.print("[yellow]⚠ Aucune sauvegarde de configurations trouvée[/yellow]")
        return
    
    console.print(Panel.fit(
        "[bold cyan]🔄 RESTAURATION DES CONFIGURATIONS[/bold cyan]\n\n"
        "Seuls les fichiers de configuration seront restaurés\n"
        "Les fichiers existants seront écrasés",
        title="RESTAURATION CONFIGS", border_style="blue"
    ))
    
    # Afficher les sauvegardes disponibles
    for i, backup in enumerate(backups, 1):
        console.print(f"[cyan]{i}.[/cyan] {backup}")
    console.print(f"\n[cyan]0.[/cyan] Annuler")
    
    choice = input(f"{yellow}Choisissez une sauvegarde à restaurer (1-{len(backups)}) : {reset}").strip()
    if choice == "0":
        return
    
    backup_path = os.path.join(backup_dir, backups[int(choice)-1])
    
    if not confirm_action(f"RESTAURER les configurations depuis {backup_path}"):
        return
    
    try:
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(path=os.path.expanduser("~"))
        
        console.print(Panel(
            "[bold green]✅ CONFIGURATIONS RESTAURÉES[/bold green]\n"
            "Redémarrez Termux pour appliquer les changements",
            border_style="green"
        ))
    except Exception as e:
        console.print(f"[red]❌ Erreur : {str(e)}[/red]")
    
    input(f"\n{yellow}Appuyez sur Entrée pour continuer...{reset}")

def restore_from_external():
    """Restauration depuis stockage externe - Version sécurisée"""
    try:
        # Chemin standard Termux pour le stockage externe
        storage_path = os.path.expanduser("~/storage/shared")
        
        if not os.path.exists(storage_path):
            console.print(Panel(
                "[red]❌ STOCKAGE NON CONFIGURÉ[/red]\n\n"
                "Exécutez d'abord :\n"
                "[bold green]termux-setup-storage[/bold green]\n"
                "Et accordez les permissions",
                border_style="red"
            ))
            if Confirm.ask("[yellow]Essayer de configurer maintenant ?[/yellow]"):
                subprocess.run("termux-setup-storage", shell=True, check=True)
                console.print("[green]✔ Redémarrez le script après configuration[/green]")
            return

        # Recherche des sauvegardes
        backup_files = []
        for root, _, files in os.walk(storage_path):
            for file in files:
                if file.startswith(("termux_backup_", "termux_ext_")) and file.endswith(".tar.gz"):
                    backup_files.append(os.path.join(root, file))

        if not backup_files:
            console.print(Panel(
                "[red]❌ AUCUNE SAUVEGARDE TROUVÉE[/red]\n\n"
                "Placez votre sauvegarde dans :\n"
                f"[cyan]{storage_path}[/cyan]\n"
                "avec un nom commençant par 'termux_backup_' ou 'termux_ext_'",
                border_style="red"
            ))
            return

        # Affichage des sauvegardes disponibles
        console.print(Panel("[bold]SAUVEGARDES DISPONIBLES :[/bold]", border_style="green"))
        for i, backup in enumerate(sorted(backup_files, reverse=True), 1):
            size = os.path.getsize(backup)/(1024*1024)
            console.print(f"[cyan]{i}.[/cyan] {os.path.basename(backup)} ({size:.2f} MB)")

        # Sélection
        choice = int(input(f"\n{yellow}Choisissez une sauvegarde (1-{len(backup_files)}) : {reset}"))
        if choice < 1 or choice > len(backup_files):
            raise ValueError

        backup_path = backup_files[choice-1]

        # Confirmation
        console.print(Panel(
            f"[bold red]⚠ ATTENTION ![/bold red]\n\n"
            f"Vous allez restaurer :\n[cyan]{os.path.basename(backup_path)}[/cyan]\n"
            "Cette opération écrasera vos fichiers existants !",
            border_style="red"
        ))

        if not Confirm.ask("[bold red]Confirmer la restauration ?[/bold red]"):
            return

        # Commande de restauration sécurisée
        cmd = f"tar -xzvf '{backup_path}' -C /data/data/com.termux/files/ --warning=no-timestamp"
        with Progress() as progress:
            task = progress.add_task("[red]Restauration en cours...[/red]", total=None)
            subprocess.run(cmd, shell=True, check=True)

        console.print(Panel(
            "[bold green]✅ RESTAURATION RÉUSSIE[/bold green]\n\n"
            "[yellow]Redémarrez Termux pour appliquer les changements[/yellow]",
            border_style="green"
        ))

    except PermissionError:
        console.print(Panel(
            "[bold red]❌ PERMISSION REFUSÉE[/bold red]\n\n"
            "Termux n'a pas accès au stockage.\n"
            "1. Exécutez [green]termux-setup-storage[/green]\n"
            "2. Accordez les permissions\n"
            "3. Réessayez",
            border_style="red"
        ))
    except Exception as e:
        console.print(f"[red]❌ Erreur : {str(e)}[/red]")

    input("\nAppuyez sur Entrée pour continuer...")

def backup_termux_advanced():
    """Nouvelle méthode principale intelligente"""
    console.print(Panel.fit(
        "[bold cyan]🔍 DÉTECTION AUTOMATIQUE DE LA MEILLEURE MÉTHODE[/bold cyan]",
        border_style="blue"
    ))

    # 1. Vérification de rsync
    if shutil.which("rsync"):
        console.print("[green]✓ Méthode rsync disponible[/green]")
        try:
            return backup_termux_alternative_rsync()
        except Exception as e:
            console.print(f"[yellow]⚠ Échec rsync : {str(e)}[/yellow]")
            console.print("[yellow]↪ Tentative avec méthode standard...[/yellow]")
    
    # 2. Fallback sur tar avec exclusions renforcées
    console.print("[yellow]ℹ Utilisation de la méthode standard avec exclusions[/yellow]")
    return backup_termux_alternative_safe()

def backup_termux_alternative():
    """Sauvegarde fiable avec détection automatique du chemin Termux"""
    from rich.progress import (
        Progress, BarColumn, TextColumn, 
        TimeRemainingColumn, TaskProgressColumn
    )
    
    # 1. Détection automatique du chemin Termux
    termux_paths = [
        os.path.expanduser("$PREFIX/../.."),  # Chemin standard
        "/data/data/com.termux/files",         # Chemin alternatif
        os.path.expanduser("~/../..")          # Chemin racine
    ]
    
    source_dir = None
    for path in termux_paths:
        test_path = os.path.join(path, "files")
        if os.path.exists(test_path):
            source_dir = test_path
            break
    
    if not source_dir:
        console.print(Panel(
            "[red]❌ DOSSIER TERMUX INTROUVABLE[/red]\n\n"
            "Impossible de localiser l'installation Termux.\n"
            "Essayez de spécifier manuellement le chemin avec :\n"
            "[cyan]tar -czf /sdcard/backup_manual.tar.gz /data/data/com.termux/files[/cyan]",
            border_style="red"
        ))
        input("\nAppuyez sur Entrée pour continuer...")
        return

    # 2. Configuration de la sauvegarde
    backup_dir = "/sdcard/Termux_Backups"
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"termux_full_{timestamp}.tar.gz")

    console.print(Panel.fit(
        f"[bold cyan]💾 SAUVEGARDE COMPLÈTE DE TERMUX[/bold cyan]\n"
        f"Source : [yellow]{source_dir}[/yellow]",
        border_style="blue"
    ))

    if not Confirm.ask("  Confirmer la création de la sauvegarde ?", default=False):
        return

    try:
        # 3. Vérification de l'espace
        console.print("[dim]Calcul de l'espace nécessaire...[/dim]")
        size_cmd = f"du -sb {source_dir} | cut -f1"
        termux_size = int(subprocess.check_output(size_cmd, shell=True, text=True).strip())
        
        free_space = shutil.disk_usage("/sdcard").free
        if termux_size * 2 > free_space:
            raise ValueError(
                f"Espace insuffisant\n"
                f"Nécessaire : {termux_size*2/1024/1024:.1f} MB\n"
                f"Disponible : {free_space/1024/1024:.1f} MB"
            )

        # 4. Sauvegarde avec feedback visuel
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            transient=True
        ) as progress:
            task = progress.add_task("[cyan]Sauvegarde en cours...", total=termux_size)
            
            cmd = f"tar -czf {backup_path} -C {os.path.dirname(source_dir)} {os.path.basename(source_dir)}"
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stderr=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                text=True
            )
            
            # Mise à jour de la progression
            while proc.poll() is None:
                if os.path.exists(backup_path):
                    progress.update(task, completed=os.path.getsize(backup_path))
                time.sleep(0.5)
            
            if proc.returncode != 0:
                raise subprocess.CalledProcessError(proc.returncode, cmd, proc.stderr.read())

        # 5. Validation finale
        if os.path.getsize(backup_path) < 100000000:  # 100MB minimum
            raise ValueError(f"Archive trop petite ({os.path.getsize(backup_path)/1024/1024:.1f} MB)")
        
        console.print(Panel(
            f"[bold green]✅ SAUVEGARDE RÉUSSIE[/bold green]\n"
            f"• Taille : [cyan]{os.path.getsize(backup_path)/1024/1024:.1f} MB[/cyan]\n"
            f"• Emplacement : [cyan]{backup_path}[/cyan]",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(Panel(
            f"[bold red]❌ ÉCHEC DE SAUVEGARDE[/bold red]\n"
            f"Erreur : {str(e)}",
            border_style="red"
        ))
        if os.path.exists(backup_path):
            os.remove(backup_path)
            
    finally:
        input("\nAppuyez sur Entrée pour continuer...")
        
# ==============================================
# 7. Vérification des permissions
# ==============================================
def check_permissions():
    """Vérifie si le script a les permissions nécessaires"""
    if not os.access("/data/data/com.termux/files/usr", os.W_OK):
        console.print("[red]❌ Erreur: Permissions insuffisantes[/red]")
        console.print("[yellow]⇒ Essayez de lancer avec 'sudo' si nécessaire[/yellow]")
        return False
    return True

# ==============================================
# 8. Confirmations améliorées
# ==============================================
def confirm_action(action_name):
    messages = {
        "Nettoyer les dépendances globales": (
            "🧼 Nettoyage des dépendances globales\n\n"
            "• Supprime le cache de Go (`go clean -modcache`)\n"
            "• Désinstalle tous les modules Python installés globalement (`pip freeze | xargs pip uninstall -y`)\n"
            "→ Cela permet de repartir sur un environnement propre si des conflits ou doublons apparaissent."
        ),
        "Quitter le programme": (
            "🚪 Quitter Super Cleaner\n\n"
            "• Ferme le programme immédiatement\n"
            "• Aucune opération ne sera effectuée\n"
            "→ Vous pourrez le relancer plus tard sans perte."
        ),
        "RÉINITIALISATION COMPLÈTE du système (Cette action est irréversible)": (
            "💣 Réinitialisation complète du système\n\n"
            "• Supprime tous les outils, modules, fichiers utilisateurs et paquets non essentiels\n"
            "• Réinitialise Termux à un état de base\n"
            "→ Action IRRÉVERSIBLE, utilisez en dernier recours !"
        )
    }

    description = messages.get(action_name, "Cette action peut modifier votre environnement.")
    console.print(Panel.fit(description, title=f"[bold red]CONFIRMATION REQUISE[/bold red]", border_style="red"))

    confirm = input(f"{yellow}⚠ Confirmer: {action_name} ? [y/n] : {reset}").strip().lower()
    return confirm in ["y", "yes", "o", "oui"]
    
def confirm_task(action_name):
    messages = {
        "Nettoyage léger": (
            "🧽 Nettoyage léger\n\n"
            "• Supprime les modules Python non essentiels\n"
            "• Purge le cache pip\n"
            "→ Idéal pour un nettoyage rapide sans risque"
        ),
        "Nettoyage standard": (
            "🧹 Nettoyage standard\n\n"
            "• Inclut le nettoyage léger\n"
            "• Supprime Subfinder, Go et d'autres outils\n"
            "→ Recommandé après usage d'outils de pentest"
        ),
        "Nettoyage approfondi": (
            "🌀 Nettoyage approfondi\n\n"
            "• Supprime fichiers temporaires, logs, caches\n"
            "• Vide ~/.cache, ~/tmp et fichiers *.log\n"
            "→ Approprié pour libérer de l’espace"
        ),
        "Nettoyage COMPLET": (
            "💥 Nettoyage COMPLET (irréversible)\n\n"
            "• Termine les processus en cours\n"
            "• Supprime presque tous les paquets et configs\n"
            "• Réinitialise totalement l’environnement\n"
            "→ Dernier recours, nécessite réinstallation Termux"
        )
    }

    description = messages.get(action_name, "Aucune description disponible.")
    console.print(Panel.fit(description, title=f"[bold red]CONFIRMATION[/bold red]", border_style="red"))

    confirm = input(f"{yellow}⚠ Voulez-vous continuer avec : {action_name} ? [y/n] : {reset}").strip().lower()
    return confirm in ['y', 'yes', 'o', 'oui']
    
# ==============================================
# 9. Mode Dry Run
# ==============================================
def dry_run():
    """Simule les actions sans rien modifier"""
    console.print(Panel(
        "[bold yellow]🐉 MODE DRY RUN (simulation)[/bold yellow]\n"
        "Aucune modification ne sera effectuée",
        border_style="yellow"
    ))
    
    # Simulation nettoyage Python
    result = subprocess.run("pip list --format=freeze", shell=True, capture_output=True, text=True)
    modules = result.stdout.splitlines()
    console.print(f"[cyan]→ {len(modules)} modules Python seraient désinstallés[/cyan]")
    
    # Simulation suppression outils
    detected_tools = []
    for tool, paths in RECON_TOOLS.items():
        for path in paths:
            if os.path.exists(os.path.expanduser(path)):
                detected_tools.append(tool)
                break
                
    if detected_tools:
        console.print("[cyan]→ Outils détectés qui seraient supprimés:[/cyan]")
        for tool in detected_tools:
            console.print(f"  • {tool}")
    else:
        console.print("[green]→ Aucun outil supplémentaire détecté[/green]")

def get_size(path):
    """Retourne la taille totale d’un fichier ou dossier (en octets)."""
    total = 0
    path = os.path.expanduser(path)
    if os.path.isfile(path):
        total += os.path.getsize(path)
    elif os.path.isdir(path):
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
    return total
    
def dry_run_tool_cleanup():
    """Simule la suppression des outils de reconnaissance et affiche les tailles."""
    total_size = 0
    console.print(Panel("🐉 MODE DRY RUN (simulation)\nAucune modification ne sera effectuée", border_style="cyan"))

    tools_found = []

    for tool, paths in RECON_TOOLS.items():
        for path in paths:
            full = os.path.expanduser(path)
            if os.path.exists(full):
                size = get_size(full)
                total_size += size
                tools_found.append((tool, full, size))

    if not tools_found:
        console.print("[yellow]Aucun outil détecté pour suppression.[/yellow]")
    else:
        for tool, path, size in tools_found:
            console.print(f"[blue]→ {tool}[/blue] ({path}) — [magenta]{size / 1024:.2f} KB[/magenta]")

        console.print(f"\n[bold green]💾 Gain estimé : {total_size / (1024*1024):.2f} Mo[/bold green]")

    input(f"\n{yellow}Appuyez sur Entrée pour revenir...{reset}")
# ==============================================
# Journalisation (Logging)
# ==============================================
def setup_logging():
    """Configure le système de logging"""
    log_file = os.path.expanduser("~/supercleaner.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def log_action(action, details):
    """Journalise une action"""
    logging.info(f"{action}: {details}")
    console.print(f"[dim cyan]📝 Journal: {action} → {details}[/dim cyan]")

# ==============================================
# Fonctions principales modifiées
# ==============================================
def manage_installed_modules_and_tools():
    """Liste et désinstalle les modules Python et les outils de reconnaissance."""
    from rich.table import Table

    # Récupération des modules Python
    result = subprocess.run("pip list --format=columns", shell=True, capture_output=True, text=True)
    python_lines = result.stdout.splitlines()[2:]
    python_modules = [line.split()[0] for line in python_lines]

    # Liste des outils avec leurs chemins
    recon_tools = {
        "Subfinder": ["~/.config/subfinder", "/data/data/com.termux/files/usr/bin/subfinder"],
        "Sublist3r": ["~/Sublist3r", "/data/data/com.termux/files/usr/bin/sublist3r"],
        "Amass": ["~/.config/amass", "/data/data/com.termux/files/usr/bin/amass"],
        "Assetfinder": ["/data/data/com.termux/files/usr/bin/assetfinder"],
        "Findomain": ["/data/data/com.termux/files/usr/bin/findomain"],
        "Waybackurls": ["/data/data/com.termux/files/usr/bin/waybackurls"],
        "Gau": ["/data/data/com.termux/files/usr/bin/gau"],
        "Httprobe": ["/data/data/com.termux/files/usr/bin/httprobe"],
        "Naabu": ["/data/data/com.termux/files/usr/bin/naabu"],
        "Nuclei": ["/data/data/com.termux/files/usr/bin/nuclei"],
        "Katana": ["/data/data/com.termux/files/usr/bin/katana"],
        "Dnsx": ["/data/data/com.termux/files/usr/bin/dnsx"],
        "HTTPx": ["/data/data/com.termux/files/usr/bin/httpx"]
    }

    # Vérifier les outils installés
    installed_tools = []
    for tool, paths in recon_tools.items():
        for path in paths:
            if os.path.exists(os.path.expanduser(path)) or shutil.which(tool.lower()):
                installed_tools.append(tool)
                break

    # Fusion modules + outils
    all_items = python_modules + installed_tools

    if not all_items:
        console.print("[red]❌ Aucun module ou outil à désinstaller.[/red]")
        input(f"\n{yellow}Appuyez sur Entrée pour revenir...{reset}")
        return

    # Affichage
    table = Table(show_header=True, header_style="bold magenta", title="Modules & Outils Installés")
    table.add_column("N°", style="cyan", width=4)
    table.add_column("Nom", style="green")
    table.add_column("Type", style="yellow")

    for i, name in enumerate(all_items, 1):
        kind = "Module Python" if i <= len(python_modules) else "Outil Reconnaissance"
        table.add_row(str(i), name, kind)

    console.print(table)
    console.print(f"\n[cyan]0.[/cyan] Annuler")

    # Choix utilisateur
    try:
        to_uninstall = input(f"{yellow}Entrez les numéros à désinstaller (séparés par des virgules), ou 0 : {reset}").strip()
        if not to_uninstall or to_uninstall == "0":
            console.print("[blue]↩ Aucune désinstallation effectuée[/blue]")
            return

        indexes = [int(i.strip()) - 1 for i in to_uninstall.split(",")]

        for idx in indexes:
            if 0 <= idx < len(all_items):
                item = all_items[idx]

                # Python module
                if idx < len(python_modules):
                    subprocess.run(f"pip uninstall -y {item}", shell=True)
                    console.print(f"[green]✔ {item} désinstallé[/green]")

                # Reconnaissance tool
                else:
                    paths = recon_tools.get(item, [])
                    for path in paths:
                        expanded = os.path.expanduser(path)
                        if os.path.exists(expanded):
                            if os.path.isfile(expanded):
                                os.remove(expanded)
                            else:
                                subprocess.run(f"rm -rf '{expanded}'", shell=True)
                    console.print(f"[green]✔ {item} supprimé[/green]")
            else:
                console.print(f"[red]❌ Index invalide : {idx + 1}[/red]")

    except Exception as e:
        console.print(f"[red]❌ Erreur : {e}[/red]")

    input(f"\n{yellow}Appuyez sur Entrée pour revenir au menu...{reset}")

def full_reset():
    """
    Réinitialisation complète du système :
    - Termine les processus des outils de reconnaissance
    - Nettoie les dépendances globales (Go/pip)
    - Supprime les outils de reconnaissance
    - Effectue un nettoyage approfondi
    - Désinstalle les paquets non essentiels
    """
    # Confirmation avant action
    if not confirm_action("RÉINITIALISATION COMPLÈTE du système (Cette action est irréversible)"):
        console.print("[red]❌ Annulation de la réinitialisation complète[/red]")
        return

    console.print(Panel(
        "[bold red]💥 DÉBUT DE LA RÉINITIALISATION COMPLÈTE[/bold red]",
        border_style="red"
    ))

    # ==============================================
    # 1. Terminer les processus en cours
    # ==============================================
    console.print("[yellow]🔫 Termination des processus critiques...[/yellow]")
    for tool in RECON_TOOLS:
        kill_running_process(tool.lower())
    time.sleep(1)  # Pause pour laisser le temps aux processus de se terminer

    # ==============================================
    # 2. Nettoyage des dépendances globales
    # ==============================================
    console.print("[yellow]🧹 Nettoyage des dépendances globales...[/yellow]")
    clean_global_deps()

    # ==============================================
    # 3. Suppression des outils de reconnaissance
    # ==============================================
    console.print("[yellow]🗑️ Suppression des outils de reconnaissance...[/yellow]")
    removed_tools = []
    for tool, paths in RECON_TOOLS.items():
        tool_removed = False
        for path in paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                try:
                    if os.path.isfile(expanded_path):
                        os.remove(expanded_path)
                    else:
                        subprocess.run(f"rm -rf {expanded_path}", shell=True)
                    tool_removed = True
                    log_action("Suppression", f"{tool} ({expanded_path})")
                except Exception as e:
                    console.print(f"[red]❌ Erreur lors de la suppression de {tool}: {str(e)}[/red]")
        
        if tool_removed:
            removed_tools.append(tool)

    if removed_tools:
        console.print(f"[green]✔ Outils supprimés: {', '.join(removed_tools)}[/green]")
    else:
        console.print("[blue]ℹ Aucun outil supplémentaire à supprimer[/blue]")

    # ==============================================
    # 4. Nettoyage approfondi
    # ==============================================
    console.print("[yellow]🧽 Nettoyage approfondi du système...[/yellow]")
    deep_clean()  # Utilise la fonction existante mais améliorée

    # ==============================================
    # 5. Désinstallation des paquets non essentiels
    # ==============================================
    console.print("[yellow]📦 Désinstallation des paquets non essentiels...[/yellow]")
    try:
        # Liste des paquets essentiels à conserver
        essential_pkgs = ["termux-api", "termux-tools", "python", "openssh"]
        
        # Générer la liste des paquets à désinstaller
        cmd = "pkg list-installed | grep -v 'core' | awk '{print $1}'"
        installed = subprocess.check_output(cmd, shell=True, text=True).splitlines()
        
        # Filtrer les paquets essentiels
        to_remove = [pkg for pkg in installed if pkg not in essential_pkgs]
        
        if to_remove:
            console.print(f"[cyan]→ Paquets à désinstaller: {len(to_remove)}[/cyan]")
            subprocess.run(f"pkg uninstall -y {' '.join(to_remove)}", shell=True)
            console.print("[green]✔ Désinstallation des paquets terminée[/green]")
        else:
            console.print("[blue]ℹ Aucun paquet supplémentaire à désinstaller[/blue]")
    except Exception as e:
        console.print(f"[red]❌ Erreur lors de la désinstallation des paquets: {str(e)}[/red]")

    # ==============================================
    # 6. Suppression des fichiers de configuration
    # ==============================================
    console.print("[yellow]📂 Nettoyage des fichiers de configuration...[/yellow]")
    config_files = [
        "~/.bashrc", "~/.zshrc", "~/.profile",
        "~/.cache", "~/.config", "~/.local"
    ]
    
    for config in config_files:
        expanded_path = os.path.expanduser(config)
        if os.path.exists(expanded_path):
            try:
                if os.path.isfile(expanded_path):
                    os.remove(expanded_path)
                else:
                    subprocess.run(f"rm -rf {expanded_path}", shell=True)
                log_action("Suppression config", expanded_path)
            except Exception as e:
                console.print(f"[red]❌ Erreur suppression {config}: {str(e)}[/red]")

    # ==============================================
    # Finalisation
    # ==============================================
    console.print(Panel(
        "[bold green]✅ RÉINITIALISATION COMPLÈTE TERMINÉE[/bold green]\n"
        "Il est recommandé de redémarrer Termux",
        border_style="green"
    ))
    
    # Sauvegarde du rapport
    with open(os.path.expanduser("~/reset_report.txt"), "w") as f:
        f.write(f"SuperCleaner - Rapport de réinitialisation\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Outils supprimés: {', '.join(removed_tools) if removed_tools else 'Aucun'}\n")
        f.write(f"Paquets désinstallés: {len(to_remove) if 'to_remove' in locals() else 0}\n")
    
    log_action("Réinitialisation", "Terminée avec succès")
    
# ==============================================
# Main modifié
# ==============================================

# === MENUS PRINCIPAUX ===
def show_main_menu():
    """Menu principal réorganisé"""
    menu_options = [
        "[1] Options de nettoyage",
        "[2] Gestion des modules Python",
        "[3] Sauvegarde",
        "[4] Restauration",
        "[5] Quitter"
    ]
    
    console.print(Panel(
        "\n".join(menu_options),
        title="[bold cyan]MENU PRINCIPAL[/bold cyan]",
        border_style="green"
    ))

# === SOUS-MENUS ===
def show_cleaning_menu():
    """Menu des options de nettoyage"""
    menu_options = [
        "[1] Nettoyage léger",
        "[2] Nettoyage standard",
        "[3] Nettoyage approfondi", 
        "[4] Nettoyage COMPLET",
        "[5] Nettoyage des dépendances",
        "[6] Simulation de nettoyage",
        "[7] Retour"
    ]
    
    console.print(Panel(
        "\n".join(menu_options),
        title="[bold cyan]OPTIONS DE NETTOYAGE[/bold cyan]",
        border_style="blue"
    ))

def show_backup_menu():
    """Menu des options de sauvegarde"""
    menu_options = [
        "[1] Sauvegarde standard",
        "[2] Sauvegarde des configurations",
        "[3] Sauvegarde incrémentielle",
        "[4] Sauvegarde brute (tout Termux)",
        "[5] Sauvegarde externe",
        "[6] Gérer les sauvegardes",
        "[7] Retour"
    ]
    
    console.print(Panel(
        "\n".join(menu_options),
        title="[bold cyan]MENU DE SAUVEGARDE[/bold cyan]",
        border_style="magenta"
    ))

def show_restore_menu():
    """Menu des options de restauration"""
    menu_options = [
        "[1] Restauration standard", 
        "[2] Restauration des configurations",
        "[3] Restauration brute (tout Termux)",
        "[4] Restauration depuis stockage externe",
        "[5] Retour"
    ]
    
    console.print(Panel(
        "\n".join(menu_options),
        title="[bold cyan]MENU DE RESTAURATION[/bold cyan]",
        border_style="yellow"
    ))

def main():
    setup_logging()
    clear_screen()
    display_banner()
    
    if not check_permissions():
        sys.exit(1)
    
    while True:
        show_main_menu()
        choice = get_choice(1, 5)
        
        if choice == 1:  # Nettoyage
            while True:
                show_cleaning_menu()
                sub_choice = get_choice(1, 7)
                
                if sub_choice == 1:
                    if confirm_task("Nettoyage léger"):
                        light_clean()
                elif sub_choice == 2:
                    if confirm_task("Nettoyage standard"):
                        standard_clean()
                elif sub_choice == 3:
                    if confirm_task("Nettoyage approfondi"):
                        deep_clean()
                elif sub_choice == 4:
                    if confirm_task("Nettoyage COMPLET"):
                        full_reset()
                elif sub_choice == 5:
                    if confirm_action("Nettoyer les dépendances globales"):
                        clean_global_deps()
                elif sub_choice == 6:
                    dry_run()
                elif sub_choice == 7:
                    break
                    
        elif choice == 2:  # Modules Python
            manage_python_modules()
            
        elif choice == 3:  # Sauvegarde
            while True:
                show_backup_menu()
                sub_choice = get_choice(1, 7)
                
                if sub_choice == 1:
                    backup_termux_standard()
                elif sub_choice == 2:
                    backup_configs_only()
                elif sub_choice == 3:
                    incremental_backup()
                elif sub_choice == 4:
                    backup_termux_alternative()
                elif sub_choice == 5:
                    backup_to_external()
                elif sub_choice == 6:
                    manage_backups()
                elif sub_choice == 7:
                    break
                    
        elif choice == 4:  # Restauration
            while True:
                show_restore_menu()
                sub_choice = get_choice(1, 5)
                
                if sub_choice == 1:
                    restore_termux()
                elif sub_choice == 2:
                    restore_configs_only()
                elif sub_choice == 3:
                    restore_termux_alternative()
                elif sub_choice == 4:
                    restore_from_external()
                elif sub_choice == 5:
                    break
                    
        elif choice == 5:  # Quitter
            if confirm_action("Quitter le programme"):
                sys.exit(0)
         
if __name__ == "__main__":
    main()
