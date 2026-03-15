#!/data/data/com.termux/files/usr/bin/python

import os
import requests
import json
import time
import sys
import subprocess
from datetime import datetime
from base64 import b64encode
import getpass

# Vérification et installation automatique des dépendances légères
def install_if_missing(package):
    """Installe un package pip si manquant"""
    try:
        __import__(package)
    except ImportError:
        print(f"📦 Installation de {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Installation des dépendances nécessaires
for pkg in ['rich']:
    install_if_missing(pkg)

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.prompt import Prompt, Confirm

console = Console()

# Fichiers de configuration
CONFIG_FILE = os.path.expanduser("~/.push_config.json")
LOCAL_CONFIG = "push_config.json"
VPS_CONFIG_FILE = os.path.expanduser("~/.vps_config.json")

# Constantes pour les couleurs (conservées pour compatibilité)
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"


def splash_screen():
    os.system('clear')
    title = Text("Bienvenue dans le script de push", style="bold cyan")
    subtitle = Text("GitHub Manager", style="bold yellow")
    
    console.print(Panel.fit(
        f"\n{title}\n{subtitle}\n",
        border_style="cyan",
        box=box.DOUBLE_EDGE
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Initialisation...", total=None)
        time.sleep(1)


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)


def load_config():
    if os.path.exists(LOCAL_CONFIG):
        with open(LOCAL_CONFIG, 'r') as f:
            console.print("[green]✔[/green] Configuration GitHub chargée depuis le dossier local")
            return json.load(f)
    elif os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            console.print("[green]✔[/green] Configuration GitHub chargée depuis le dossier utilisateur")
            return json.load(f)
    return {}

def save_vps_config(config):
    with open(VPS_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    console.print("[green]✔[/green] Configuration VPS sauvegardée")

def load_vps_config():
    if os.path.exists(VPS_CONFIG_FILE):
        with open(VPS_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

# ============ FONCTIONS DE COPIE POUR TERMUX ============

def copy_to_termux_clipboard(text, description="Texte"):
    """Copie dans le presse-papier Termux"""
    try:
        # Méthode 1: termux-clipboard-set (si disponible)
        result = subprocess.run(['termux-clipboard-set'], input=text, 
                              text=True, capture_output=True, timeout=2)
        if result.returncode == 0:
            console.print(f"[green]✔ {description} copié dans le presse-papier Termux ![/green]")
            return True
    except:
        pass
    
    # Méthode 2: Affichage avec instruction de copie manuelle
    console.print(f"\n[yellow]📋 {description} (sélectionnez et copiez manuellement):[/yellow]")
    console.print(Panel(text, border_style="yellow"))
    console.print("[dim]Pour copier: sélectionnez le texte avec votre doigt et appuyez sur Copier[/dim]")
    return False

# ============ FONCTIONS GITHUB ============

def verifier_token_github(token):
    headers = {'Authorization': f'token ' + token}
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Vérification du token GitHub...", total=None)
            r = requests.get("https://api.github.com/user", headers=headers, timeout=5)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        console.print("[red]✖[/red] Impossible de se connecter à l'API GitHub")
        return None
    except Exception as e:
        console.print(f"[red]✖ Erreur: {e}[/red]")
        return None

def verifier_depot_et_branche(token, owner, repo, branch):
    headers = {'Authorization': f'token ' + token}
    url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Vérification du dépôt GitHub...", total=None)
            r = requests.get(url, headers=headers, timeout=5)
        
        if r.status_code == 200:
            return True
        elif r.status_code == 404:
            return False
        else:
            return None
    except Exception as e:
        console.print(f"[red]✖ Erreur: {e}[/red]")
        return None

def prompt_config():
    config = {}

    console.print(Panel.fit(
        "[bold cyan]Configuration GitHub[/bold cyan]",
        border_style="cyan"
    ))
    
    while True:
        token = Prompt.ask("[cyan]Entrez votre token GitHub[/cyan]").strip()
        if not token:
            console.print("[red]Le token ne peut pas être vide[/red]")
            continue

        valid = verifier_token_github(token)

        if valid is True:
            console.print("[green]✔ Token valide[/green]")
            config['token'] = token
            break
        elif valid is None:
            choix = Prompt.ask(
                "[yellow]Impossible de vérifier le token. Continuer quand même ?[/yellow]",
                choices=["o", "n"],
                default="n"
            )
            if choix == 'o':
                config['token'] = token
                break
        else:
            console.print("[red]Token invalide[/red]")

    while True:
        owner = Prompt.ask("[cyan]Nom de l'utilisateur ou organisation[/cyan]").strip()
        if not owner:
            console.print("[red]Le nom ne peut pas être vide[/red]")
            continue

        repo = Prompt.ask("[cyan]Nom du dépôt[/cyan]").strip()
        if not repo:
            console.print("[red]Le nom du dépôt ne peut pas être vide[/red]")
            continue

        branch = Prompt.ask("[cyan]Nom de la branche[/cyan]", default="main").strip()

        valid_repo = verifier_depot_et_branche(config['token'], owner, repo, branch)

        if valid_repo is True:
            console.print("[green]✔ Dépôt et branche valides[/green]")
            config['repo_owner'] = owner
            config['repo_name'] = repo
            config['branch'] = branch
            break
        elif valid_repo is None:
            choix = Prompt.ask(
                "[yellow]Impossible de vérifier le dépôt. Continuer quand même ?[/yellow]",
                choices=["o", "n"],
                default="n"
            )
            if choix == 'o':
                config['repo_owner'] = owner
                config['repo_name'] = repo
                config['branch'] = branch
                break
        else:
            console.print(f"[red]Le dépôt '{owner}/{repo}' ou la branche '{branch}' est introuvable[/red]")

    save_config(config)
    console.print("[green]✔ Configuration GitHub mise à jour[/green]")
    return config

def upload_file_to_github(token, file_path, repo_owner, repo_name, commit_message, branch):
    file_name = os.path.basename(file_path)
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_name}"
    
    headers = {'Authorization': f'token {token}'}

    with open(file_path, 'rb') as f:
        file_content = f.read()

    encoded_content = b64encode(file_content).decode('utf-8')
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=f"Upload de {file_name}...", total=None)
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            sha = response.json().get('sha')
        else:
            sha = None

        data = {
            "message": commit_message,
            "content": encoded_content,
            "branch": branch
        }
        if sha:
            data["sha"] = sha

        put_response = requests.put(url, headers=headers, json=data)

    if put_response.status_code in [200, 201]:
        console.print(f"[green]✔ Upload de '{file_name}' réussi ![/green]")
    else:
        console.print(f"[red]✖ Erreur upload '{file_name}': {put_response.status_code}[/red]")

def delete_files_from_repo(config):
    url = f"https://api.github.com/repos/{config['repo_owner']}/{config['repo_name']}/contents"
    headers = {'Authorization': f'token {config["token"]}'}

    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        console.print("[red]✖ Impossible de récupérer les fichiers[/red]")
        return

    files = r.json()
    if not files:
        console.print("[yellow]Aucun fichier trouvé[/yellow]")
        return

    table = Table(title="Fichiers sur GitHub", box=box.ROUNDED)
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Nom", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Taille", style="magenta")

    for idx, file in enumerate(files, 1):
        file_type = "Dossier" if file['type'] == "dir" else "Fichier"
        size = file.get('size', 0)
        size_str = f"{size} bytes" if size < 1024 else f"{size/1024:.1f} KB"
        table.add_row(str(idx), file['name'], file_type, size_str)

    console.print(table)

    selected = Prompt.ask(
        "\n[cyan]Entrez les numéros des fichiers à supprimer[/cyan]",
        default=""
    ).strip()
    
    if not selected:
        console.print("[yellow]Aucune suppression effectuée[/yellow]")
        return

    indices = [int(i.strip()) - 1 for i in selected.split(',') 
               if i.strip().isdigit() and 0 <= int(i.strip()) - 1 < len(files)]

    for idx in indices:
        file_info = files[idx]
        delete_url = file_info['url']
        data = {
            "message": f"Suppression de {file_info['name']}",
            "sha": file_info['sha'],
            "branch": config['branch']
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Suppression de {file_info['name']}...", total=None)
            del_response = requests.delete(delete_url, headers=headers, json=data)
        
        if del_response.status_code == 200:
            console.print(f"[green]✔ {file_info['name']} supprimé[/green]")
        else:
            console.print(f"[red]✖ Erreur suppression {file_info['name']}[/red]")

def telecharger_fichiers_depuis_github(config):
    """Téléchargement avec affichage des tailles - Commandes sur UNE SEULE LIGNE"""
    url = f"https://api.github.com/repos/{config['repo_owner']}/{config['repo_name']}/contents"
    headers = {'Authorization': f'token {config["token"]}'}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        console.print(f"[red]✖ Erreur: {response.status_code}[/red]")
        return

    files = response.json()
    if not files:
        console.print("[yellow]Aucun fichier trouvé[/yellow]")
        return

    def format_size(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} o"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f} Ko"
        else:
            return f"{size_bytes/(1024*1024):.1f} Mo"

    console.print("\n[bold cyan]📂 Fichiers disponibles :[/bold cyan]")
    console.print("─" * 80)
    console.print(f"{'#':<4} {'Nom':<50} {'Taille':<10}")
    console.print("─" * 80)
    
    for idx, file in enumerate(files, 1):
        name = file['name']
        size = file.get('size', 0)
        size_str = format_size(size)
        
        if len(name) > 48:
            name = name[:45] + "..."
        
        console.print(f"  [bold yellow]{idx:2}.[/bold yellow] [green]{name:<48}[/green] [magenta]{size_str:>8}[/magenta]")
    
    console.print("─" * 80)

    selection = Prompt.ask(
        "\n[cyan]Entrez les numéros des fichiers à télécharger[/cyan]",
        default=""
    ).strip()
    
    if not selection:
        console.print("[yellow]Aucune sélection[/yellow]")
        return

    indices = [int(i.strip()) - 1 for i in selection.split(',') 
               if i.strip().isdigit() and 0 <= int(i.strip()) - 1 < len(files)]

    total_size = 0
    for idx in indices:
        file = files[idx]
        total_size += file.get('size', 0)
    
    if len(indices) > 1:
        console.print(f"[dim]Taille totale à télécharger: {format_size(total_size)}[/dim]")
        console.print()
        
        # Afficher la commande groupée pour télécharger tous les fichiers
        all_files = [files[i]['name'] for i in indices]
        all_urls = [f"https://raw.githubusercontent.com/{config['repo_owner']}/{config['repo_name']}/{config['branch']}/{files[i]['name']}" for i in indices]
        
        console.print("[bold cyan]📋 Commande pour tout télécharger (une seule ligne) :[/bold cyan]")
        curl_all = " && ".join([f"curl -O {url}" for url in all_urls])
        console.print(Panel(curl_all, border_style="green", width=100))
        console.print()
    
    for idx in indices:
        file = files[idx]
        raw_url = f"https://raw.githubusercontent.com/{config['repo_owner']}/{config['repo_name']}/{config['branch']}/{file['name']}"
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description=f"Téléchargement de {file['name']}...", total=None)
                r = requests.get(raw_url)
                r.raise_for_status()
                
            with open(file['name'], 'w') as f:
                f.write(r.text)
            console.print(f"[green]✔ {file['name']} téléchargé[/green]")
        except Exception as e:
            console.print(f"[red]✖ Erreur: {e}[/red]")
            
def generer_commandes_installation(config):
    """Version avec taille des fichiers - Commandes sur UNE SEULE LIGNE"""
    url = f"https://api.github.com/repos/{config['repo_owner']}/{config['repo_name']}/contents"
    headers = {'Authorization': f'token {config["token"]}'}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        console.print(f"[red]✖ Erreur: {response.status_code}[/red]")
        return

    files = response.json()
    scripts = [f for f in files if f['name'].endswith(('.sh', '.py'))]
    
    if not scripts:
        console.print("[yellow]Aucun script trouvé[/yellow]")
        return

    # Fonction pour formater la taille
    def format_size(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} o"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f} Ko"
        else:
            return f"{size_bytes/(1024*1024):.1f} Mo"

    # Affichage des scripts avec taille
    console.print("\n[bold cyan]📜 Scripts disponibles :[/bold cyan]")
    console.print("─" * 80)
    console.print(f"{'#':<4} {'Nom':<40} {'Type':<12} {'Taille':<10}")
    console.print("─" * 80)
    
    for idx, script in enumerate(scripts, 1):
        script_type = "🐚 Shell" if script['name'].endswith('.sh') else "🐍 Python"
        size = script.get('size', 0)
        size_str = format_size(size)
        
        console.print(f"  [bold yellow]{idx:2}.[/bold yellow] [green]{script['name']:<38}[/green] {script_type:<12} [magenta]{size_str:>8}[/magenta]")
    
    console.print("─" * 80)

    selection = Prompt.ask(
        "\n[cyan]Entrez les numéros des scripts (séparés par virgules)[/cyan]",
        default=""
    ).strip()
    
    if not selection:
        console.print("[yellow]Aucune sélection[/yellow]")
        return

    # Traitement de la sélection
    selected_indices = []
    for num in selection.split(','):
        num = num.strip()
        if num.isdigit() and 1 <= int(num) <= len(scripts):
            selected_indices.append(int(num) - 1)
        else:
            console.print(f"[red]Numéro invalide ignoré: {num}[/red]")

    if not selected_indices:
        console.print("[red]Aucune sélection valide[/red]")
        return

    console.print("\n[bold green]=== COMMANDES D'INSTALLATION (À COPIER EN UNE SEULE LIGNE) ===[/bold green]\n")
    
    total_size = 0
    all_curl = []
    all_wget = []
    all_install = []
    
    for idx in selected_indices:
        script = scripts[idx]
        file_name = script['name']
        size = script.get('size', 0)
        total_size += size
        raw_url = f"https://raw.githubusercontent.com/{config['repo_owner']}/{config['repo_name']}/{config['branch']}/{file_name}"
        
        # Commandes sur UNE SEULE LIGNE
        curl_cmd = f"curl -O {raw_url}"
        wget_cmd = f"wget {raw_url}"
        
        if file_name.endswith(".sh"):
            exec_cmd = f"bash {file_name}"
            install_cmd = f"curl -O {raw_url} && chmod +x {file_name} && ./{file_name}"
        else:  # .py
            exec_cmd = f"python3 {file_name}"
            install_cmd = f"curl -O {raw_url} && python3 {file_name}"
        
        console.print(f"[bold cyan]► {file_name}[/bold cyan] [dim]({format_size(size)})[/dim]")
        console.print(f"  [dim]Lien:[/dim] {raw_url}")
        console.print(f"  [yellow]Téléchargement:[/yellow] {curl_cmd}")
        console.print(f"  [magenta]Alternative:[/magenta] {wget_cmd}")
        console.print(f"  [green]Exécution:[/green] {exec_cmd}")
        console.print(f"  [blue]Installation complète:[/blue] {install_cmd}")
        console.print()
        
        all_curl.append(curl_cmd)
        all_wget.append(wget_cmd)
        all_install.append(install_cmd)
    
    # Afficher le total
    if len(selected_indices) > 1:
        console.print(f"[dim]Taille totale: {format_size(total_size)}[/dim]")
        console.print()
    
    # Commandes groupées
    if len(selected_indices) > 1:
        console.print("[bold cyan]📋 Commandes groupées (une seule ligne) :[/bold cyan]")
        
        # Grouper par type d'opération
        all_curl_group = " && ".join(all_curl)
        all_wget_group = " && ".join(all_wget)
        all_install_group = " && ".join(all_install)
        
        console.print(Panel(
            f"[yellow]Tous les téléchargements (curl):[/yellow]\n"
            f"{all_curl_group}\n\n"
            f"[magenta]Tous les téléchargements (wget):[/magenta]\n"
            f"{all_wget_group}\n\n"
            f"[blue]Toutes les installations:[/blue]\n"
            f"{all_install_group}",
            border_style="green",
            width=100
        ))
        
        # Version simplifiée pour tout installer d'un coup
        console.print("\n[bold cyan]⚡ Commande tout-en-un :[/bold cyan]")
        
        # Construire la commande tout-en-un sans f-string imbriquées
        all_in_one_parts = []
        for i in selected_indices:
            script = scripts[i]
            file_name = script['name']
            raw_url = f"https://raw.githubusercontent.com/{config['repo_owner']}/{config['repo_name']}/{config['branch']}/{file_name}"
            
            if file_name.endswith('.py'):
                all_in_one_parts.append(f"curl -O {raw_url} && python3 {file_name}")
            else:
                all_in_one_parts.append(f"curl -O {raw_url} && bash {file_name}")
        
        all_in_one = " && ".join(all_in_one_parts)
        console.print(Panel(all_in_one, border_style="yellow", width=100))

# ============ FONCTIONS VPS POUR TERMUX ============

def test_connexion_vps_termux(host, port, username, password=None):
    """Test la connexion SSH en utilisant la commande système ssh"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Test de connexion au VPS...", total=None)
            
            # Utiliser ssh -o ConnectTimeout=5 pour tester rapidement
            cmd = ['ssh', '-o', 'ConnectTimeout=5', '-o', 'BatchMode=yes', 
                   '-p', str(port), f'{username}@{host}', 'exit']
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                return True, "Connexion réussie"
            elif "Permission denied" in result.stderr.decode():
                return False, "Permission refusée - mot de passe/clé incorrect"
            else:
                return False, f"Échec de connexion (code {result.returncode})"
    except subprocess.TimeoutExpired:
        return False, "Timeout - serveur non joignable"
    except Exception as e:
        return False, str(e)

def upload_to_vps_termux(config_vps, files, remote_subdir=""):
    """Upload via SCP en utilisant les commandes système"""
    try:
        # Construire la commande scp
        remote_base = config_vps['remote_path'].rstrip('/')
        if remote_subdir:
            remote_dest = f"{remote_base}/{remote_subdir}"
            # Créer le dossier distant
            ssh_cmd = ['ssh', '-p', str(config_vps['port']), 
                      f"{config_vps['username']}@{config_vps['host']}", 
                      f"mkdir -p {remote_dest}"]
            subprocess.run(ssh_cmd, capture_output=True)
        else:
            remote_dest = remote_base
        
        valid_files = []
        for file_path in files:
            if os.path.exists(file_path):
                valid_files.append(file_path)
            else:
                console.print(f"[red]✖ Fichier non trouvé: {file_path}[/red]")
        
        if not valid_files:
            console.print("[yellow]Aucun fichier valide à transférer[/yellow]")
            return False
        
        # Transférer chaque fichier avec scp
        for file_path in valid_files:
            file_name = os.path.basename(file_path)
            console.print(f"[cyan]Transfert de {file_name}...[/cyan]")
            
            scp_cmd = ['scp', '-P', str(config_vps['port']), 
                      file_path, 
                      f"{config_vps['username']}@{config_vps['host']}:{remote_dest}/{file_name}"]
            
            result = subprocess.run(scp_cmd, capture_output=True)
            
            if result.returncode == 0:
                console.print(f"[green]✔ {file_name} transféré[/green]")
            else:
                error = result.stderr.decode()
                console.print(f"[red]✖ Erreur transfert {file_name}: {error}[/red]")
        
        # Mettre à jour la date de dernière utilisation
        config_vps['last_used'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_vps_config(config_vps)
        
        if valid_files:
            console.print("\n")
            cmd_panel = Panel(
                f"[yellow]Commandes pour exécuter sur le VPS:[/yellow]\n\n"
                f"[cyan]Connexion SSH:[/cyan]\n"
                f"  ssh {config_vps['username']}@{config_vps['host']} -p {config_vps['port']}\n\n"
                f"[cyan]Exécution des scripts:[/cyan]",
                title="🚀 Commandes d'accès",
                border_style="green"
            )
            console.print(cmd_panel)
            
            for file_path in valid_files:
                file_name = os.path.basename(file_path)
                console.print(f"  cd {remote_dest} && chmod +x {file_name} && ./{file_name}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✖ Erreur lors du transfert: {e}[/red]")
        return False

def prompt_vps_config_termux():
    """Configuration VPS adaptée à Termux"""
    console.print(Panel.fit(
        "[bold cyan]Configuration du VPS[/bold cyan]",
        border_style="cyan"
    ))
    
    config = {}
    existing = load_vps_config()
    
    if existing:
        console.print("[yellow]Configuration existante trouvée[/yellow]")
        if Confirm.ask("Utiliser la configuration existante ?", default=True):
            return existing
    
    config['host'] = Prompt.ask("[cyan]Adresse IP ou hostname du VPS[/cyan]")
    config['port'] = int(Prompt.ask("[cyan]Port SSH[/cyan]", default="22"))
    config['username'] = Prompt.ask("[cyan]Nom d'utilisateur SSH[/cyan]", default="root")
    
    console.print("[yellow]Note: L'authentification utilisera votre clé SSH configurée[/yellow]")
    
    config['remote_path'] = Prompt.ask(
        "[cyan]Dossier de destination sur le VPS[/cyan]",
        default=f"/root/"
    )
    
    console.print("\n[yellow]Test de la connexion...[/yellow]")
    success, message = test_connexion_vps_termux(
        config['host'], 
        config['port'], 
        config['username']
    )
    
    if success:
        console.print("[green]✔ Connexion au VPS réussie ![/green]")
        config['last_used'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_vps_config(config)
    else:
        console.print(f"[red]✖ Échec de la connexion: {message}[/red]")
        console.print("[yellow]Vérifiez que vous avez bien configuré votre clé SSH:[/yellow]")
        console.print(f"  ssh-copy-id -p {config['port']} {config['username']}@{config['host']}")
        if Confirm.ask("Voulez-vous réessayer ?", default=True):
            return prompt_vps_config_termux()
        else:
            return None
    
    return config

def push_to_vps_menu_termux():
    """Menu VPS adapté à Termux"""
    config_vps = load_vps_config()
    
    if not config_vps:
        console.print("[yellow]Aucune configuration VPS trouvée[/yellow]")
        if Confirm.ask("Voulez-vous configurer un VPS maintenant ?"):
            config_vps = prompt_vps_config_termux()
            if not config_vps:
                return
        else:
            return
    
    # Afficher la configuration
    table = Table(title="Configuration VPS", box=box.ROUNDED)
    table.add_column("Paramètre", style="cyan")
    table.add_column("Valeur", style="green")
    table.add_row("Host", config_vps['host'])
    table.add_row("Port", str(config_vps['port']))
    table.add_row("Utilisateur", config_vps['username'])
    table.add_row("Dossier distant", config_vps['remote_path'])
    console.print(table)
    
    # Sélection des fichiers
    files_input = Prompt.ask(
        "\n[cyan]Entrez les noms des fichiers à envoyer (séparés par virgules)[/cyan]"
    ).strip()
    
    file_paths = [f.strip() for f in files_input.split(',')]
    
    valid_files = [f for f in file_paths if os.path.exists(f)]
    invalid_files = [f for f in file_paths if not os.path.exists(f)]
    
    if invalid_files:
        console.print("[yellow]Fichiers non trouvés:[/yellow]")
        for f in invalid_files:
            console.print(f"  • {f}")
    
    if not valid_files:
        console.print("[yellow]Aucun fichier valide à transférer[/yellow]")
        return
    
    subdir = Prompt.ask(
        "[cyan]Sous-dossier sur le VPS (optionnel)[/cyan]",
        default=""
    ).strip()
    
    console.print("\n[yellow]Début du transfert vers VPS...[/yellow]")
    success = upload_to_vps_termux(config_vps, valid_files, subdir)
    
    if success:
        console.print("[green]✔ Transfert terminé avec succès ![/green]")

# ============ MAIN ============

def main():
    splash_screen()
    
    # Vérifier si on est dans Termux
    is_termux = 'TERMUX_VERSION' in os.environ
    
    if is_termux:
        console.print("[blue]📱 Environnement Termux détecté[/blue]")
    
    config = load_config()
    if not config:
        config = prompt_config()
    else:
        info_table = Table(title="Configuration GitHub actuelle", box=box.SIMPLE, show_header=False)
        info_table.add_column("Clé", style="cyan")
        info_table.add_column("Valeur", style="green")
        info_table.add_row("Dépôt", f"{config.get('repo_owner', '?')}/{config.get('repo_name', '?')}")
        info_table.add_row("Branche", config.get('branch', 'main'))
        info_table.add_row("Token", "••••••••" + config.get('token', '')[-4:] if config.get('token') else "Non défini")
        
        console.print(info_table)

    while True:
        menu_table = Table(title="Menu principal", box=box.ROUNDED, show_header=False)
        menu_table.add_column("Option", style="cyan", justify="right")
        menu_table.add_column("Description", style="white")
        
        menu_items = [
            ("1", "📤 Upload de fichiers vers GitHub"),
            ("2", "🚀 Upload script d'installation (GitHub)"),
            ("3", "📥 Télécharger depuis GitHub"),
            ("4", "🗑️  Supprimer des fichiers (GitHub)"),
            ("5", "⚙️  Modifier configuration GitHub"),
            ("6", "📋 Générer commandes d'installation"),
            ("7", "🌐 PUSH VERS VPS"),
            ("0", "❌ Quitter")
        ]
        
        for opt, desc in menu_items:
            menu_table.add_row(opt, desc)
        
        console.print("\n")
        console.print(menu_table)
        
        choice = Prompt.ask(
            "[cyan]Votre choix[/cyan]",
            choices=["0", "1", "2", "3", "4", "5", "6", "7"],
            default="1"
        )

        if choice == '1':
            files_input = Prompt.ask("\n[cyan]Fichiers à uploader (séparés par virgules)[/cyan]").strip()
            file_paths = [f.strip() for f in files_input.split(',') if os.path.exists(f.strip())]
            
            if not file_paths:
                console.print("[yellow]Aucun fichier valide[/yellow]")
                input("\nAppuyez sur Entrée pour continuer...")
                continue

            commit_message = Prompt.ask(
                "[cyan]Message de commit[/cyan]",
                default=f"Upload du {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            for file_path in file_paths:
                upload_file_to_github(
                    config['token'], 
                    file_path, 
                    config['repo_owner'], 
                    config['repo_name'], 
                    commit_message, 
                    config['branch']
                )
            
            input("\nAppuyez sur Entrée pour continuer...")

        elif choice == '2':
            files_input = Prompt.ask("\n[cyan]Scripts à uploader (séparés par virgules)[/cyan]").strip()
            file_paths = [f.strip() for f in files_input.split(',') if os.path.isfile(f.strip())]

            if not file_paths:
                console.print("[yellow]Aucun script valide[/yellow]")
                input("\nAppuyez sur Entrée pour continuer...")
                continue

            commit_message = Prompt.ask(
                "[cyan]Message de commit[/cyan]",
                default=f"Upload script du {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                upload_file_to_github(
                    config['token'],
                    file_path,
                    config['repo_owner'],
                    config['repo_name'],
                    commit_message,
                    config['branch']
                )

                raw_url = f"https://raw.githubusercontent.com/{config['repo_owner']}/{config['repo_name']}/{config['branch']}/{file_name}"
                
                cmd_panel = Panel(
                    f"[cyan]Lien:[/cyan] {raw_url}\n\n"
                    f"[yellow]Commande:[/yellow] curl -O {raw_url} && python3 {file_name}",
                    title="📦 Script prêt",
                    border_style="green"
                )
                console.print(cmd_panel)
            
            input("\nAppuyez sur Entrée pour continuer...")

        elif choice == '3':
            telecharger_fichiers_depuis_github(config)
            input("\nAppuyez sur Entrée pour continuer...")

        elif choice == '4':
            delete_files_from_repo(config)
            input("\nAppuyez sur Entrée pour continuer...")

        elif choice == '5':
            config = prompt_config()
            input("\nAppuyez sur Entrée pour continuer...")

        elif choice == '6':
            generer_commandes_installation(config)
            input("\nAppuyez sur Entrée pour continuer...")

        elif choice == '7':
            push_to_vps_menu_termux()
            input("\nAppuyez sur Entrée pour continuer...")

        elif choice == '0':
            console.print("[green]👋 Au revoir ![/green]")
            break

if __name__ == '__main__':
    main()
