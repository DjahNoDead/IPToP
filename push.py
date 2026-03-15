import os
import requests
import json
import time
from datetime import datetime
from base64 import b64encode

CONFIG_FILE = os.path.expanduser("~/.push_config.json")

# Couleurs ANSI
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"


def splash_screen():
    os.system('clear')
    print(f"{CYAN}{BOLD}Bienvenue dans le script de push sur GitHub {RESET}")
    print("=" * 60)
    loading_animation("Initialisation")


def loading_animation(text="Chargement"):
    print(f"{YELLOW}{text}", end="", flush=True)
    for _ in range(3):
        time.sleep(0.5)
        print(".", end="", flush=True)
    print(f"{RESET}\n")


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def verifier_token_github(token):
    """Vérifie que le token GitHub est valide via l'API GitHub"""
    headers = {'Authorization': f'token ' + token}
    try:
        r = requests.get("https://api.github.com/user", headers=headers, timeout=5)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        print(f"{RED}[!] Impossible de se connecter à l'API GitHub (vérifiez votre connexion Internet).{RESET}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"{RED}[!] Erreur lors de la requête : {e}{RESET}")
        return None

def verifier_depot_et_branche(token, owner, repo, branch):
    """Vérifie si le dépôt et la branche existent via l'API GitHub"""
    headers = {'Authorization': f'token ' + token}
    url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            return True
        elif r.status_code == 404:
            return False
        else:
            print(f"{RED}[!] Erreur inattendue ({r.status_code}) lors de la vérification du dépôt.{RESET}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"{RED}[!] Impossible de se connecter à GitHub (connexion réseau absente).{RESET}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"{RED}[!] Erreur lors de la requête : {e}{RESET}")
        return None

def prompt_config():
    config = {}

    # Saisie et validation du token GitHub
    while True:
        token = input("Entrez votre token GitHub: ").strip()
        if not token:
            print(f"{RED}[!] Le token ne peut pas être vide.{RESET}")
            continue

        print(f"{YELLOW}[*] Vérification du token...{RESET}")
        valid = verifier_token_github(token)

        if valid is True:
            print(f"{GREEN}[✔] Token valide.{RESET}")
            config['token'] = token
            break
        elif valid is None:
            choix = input(f"{YELLOW}Impossible de vérifier le token. Continuer quand même ? (o/n): {RESET}").strip().lower()
            if choix == 'o':
                config['token'] = token
                break
        else:
            print(f"{RED}[!] Token invalide. Veuillez réessayer.{RESET}")

    # Saisie et validation du dépôt + branche
    while True:
        owner = input("Nom de l'utilisateur ou organisation sur GitHub: ").strip()
        if not owner:
            print(f"{RED}[!] Le nom d'utilisateur/organisation ne peut pas être vide.{RESET}")
            continue

        repo = input("Nom du dépôt: ").strip()
        if not repo:
            print(f"{RED}[!] Le nom du dépôt ne peut pas être vide.{RESET}")
            continue

        branch = input("Nom de la branche (par défaut 'main'): ").strip()
        branch = branch if branch else 'main'

        print(f"{YELLOW}[*] Vérification du dépôt et de la branche...{RESET}")
        valid_repo = verifier_depot_et_branche(config['token'], owner, repo, branch)

        if valid_repo is True:
            print(f"{GREEN}[✔] Dépôt et branche valides.{RESET}")
            config['repo_owner'] = owner
            config['repo_name'] = repo
            config['branch'] = branch
            break
        elif valid_repo is None:
            choix = input(f"{YELLOW}Impossible de vérifier le dépôt. Continuer quand même ? (o/n): {RESET}").strip().lower()
            if choix == 'o':
                config['repo_owner'] = owner
                config['repo_name'] = repo
                config['branch'] = branch
                break
        else:
            print(f"{RED}[!] Le dépôt '{owner}/{repo}' ou la branche '{branch}' est introuvable.{RESET}")

    save_config(config)
    print(f"{GREEN}[✔] Configuration mise à jour.{RESET}")
    return config

def upload_file_to_github(token, file_path, repo_owner, repo_name, commit_message, branch):
    file_name = os.path.basename(file_path)
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_name}"
    
    headers = {'Authorization': f'token {token}'}

    with open(file_path, 'rb') as f:
        file_content = f.read()

    encoded_content = b64encode(file_content).decode('utf-8')
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        sha = response.json().get('sha')
        print(f"{YELLOW}[!] Le fichier '{file_name}' existe déjà. Il sera remplacé. SHA: {sha}{RESET}")
    else:
        sha = None
        print(f"{GREEN}[+] Le fichier '{file_name}' sera ajouté au dépôt.{RESET}")

    data = {
        "message": commit_message,
        "content": encoded_content,
        "branch": branch
    }
    if sha:
        data["sha"] = sha

    put_response = requests.put(url, headers=headers, json=data)

    if put_response.status_code in [200, 201]:
        print(f"{GREEN}[✔] Upload de '{file_name}' réussi !{RESET}\n")
    else:
        print(f"{RED}[!] Erreur pendant l'upload de '{file_name}': {put_response.status_code}\n{put_response.text}{RESET}")


def delete_files_from_repo(config):
    url = f"https://api.github.com/repos/{config['repo_owner']}/{config['repo_name']}/contents"
    headers = {'Authorization': f'token {config["token"]}'}

    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"{RED}[!] Impossible de récupérer les fichiers du dépôt.{RESET}")
        return

    files = r.json()
    if not files:
        print(f"{YELLOW}[!] Aucun fichier trouvé dans le dépôt.{RESET}")
        return

    print(f"{CYAN}Fichiers existants sur le dépôt :{RESET}")
    for idx, file in enumerate(files, 1):
        print(f"{idx}. {file['name']}")

    selected = input("\nEntrez les numéros des fichiers à supprimer (séparés par des virgules) : ").strip()
    if not selected:
        print(f"{YELLOW}[!] Aucune suppression effectuée.{RESET}")
        return

    indices = [int(i.strip()) - 1 for i in selected.split(',') if i.strip().isdigit() and 0 <= int(i.strip()) - 1 < len(files)]

    for idx in indices:
        file_info = files[idx]
        delete_url = file_info['url']
        data = {
            "message": f"Suppression de {file_info['name']}",
            "sha": file_info['sha'],
            "branch": config['branch']
        }
        del_response = requests.delete(delete_url, headers=headers, json=data)
        if del_response.status_code == 200:
            print(f"{GREEN}[✔] Fichier '{file_info['name']}' supprimé avec succès.{RESET}")
        else:
            print(f"{RED}[!] Erreur lors de la suppression de '{file_info['name']}': {del_response.text}{RESET}")


def update_config():
    print(f"{CYAN}Mise à jour de la configuration :{RESET}")
    new_config = prompt_config()
    print(f"{GREEN}[✔] Configuration mise à jour.{RESET}")
    return new_config

def telecharger_fichiers_depuis_github(config):
    url = f"https://api.github.com/repos/{config['repo_owner']}/{config['repo_name']}/contents"
    headers = {'Authorization': f'token {config["token"]}'}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"{RED}[!] Impossible de récupérer les fichiers du dépôt : {response.status_code}{RESET}")
        return

    files = response.json()
    if not files:
        print(f"{YELLOW}[!] Aucun fichier trouvé dans le dépôt.{RESET}")
        return

    print(f"{CYAN}Fichiers disponibles dans le dépôt :{RESET}")
    for idx, file in enumerate(files, 1):
        print(f"{idx}. {file['name']}")

    selection = input("\nEntrez les numéros des fichiers à télécharger (séparés par virgules) : ").strip()
    if not selection:
        print(f"{YELLOW}[!] Aucune sélection effectuée.{RESET}")
        return

    indices = [int(i.strip()) - 1 for i in selection.split(',') if i.strip().isdigit() and 0 <= int(i.strip()) - 1 < len(files)]

    for idx in indices:
        file = files[idx]
        raw_url = f"https://raw.githubusercontent.com/{config['repo_owner']}/{config['repo_name']}/{config['branch']}/{file['name']}"
        try:
            r = requests.get(raw_url)
            r.raise_for_status()
            with open(file['name'], 'w') as f:
                f.write(r.text)
            print(f"{GREEN}[✔] Fichier '{file['name']}' téléchargé avec succès.{RESET}")
        except Exception as e:
            print(f"{RED}[!] Erreur lors du téléchargement de '{file['name']}' : {e}{RESET}")

def upload_script_install_serveur(config):
    files_input = input("\nEntrez les noms des scripts à uploader (séparés par des virgules) : ").strip()
    file_paths = [f.strip() for f in files_input.split(',') if os.path.isfile(f.strip())]

    if not file_paths:
        print(f"{YELLOW}[!] Aucun fichier valide n'a été saisi.{RESET}")
        return

    commit_message = input("Message de commit (Entrée pour valeur par défaut): ").strip()
    if not commit_message:
        commit_message = f"Upload script install du {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

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
        print(f"{CYAN}[→] Lien raw GitHub : {raw_url}{RESET}")

        if file_name.endswith(".sh"):
            print(f"{YELLOW}[⚙] Commande serveur :{RESET}\n    curl -O {raw_url}\n    bash {file_name}")
        elif file_name.endswith(".py"):
            print(f"{YELLOW}[⚙] Commande serveur :{RESET}\n    curl -O {raw_url}\n    python3 {file_name}")
        else:
            print(f"{YELLOW}[⚙] Commande serveur :{RESET}\n    curl -O {raw_url}")

def generer_commandes_installation(config):
    url = f"https://api.github.com/repos/{config['repo_owner']}/{config['repo_name']}/contents"
    headers = {'Authorization': f'token {config["token"]}'}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"{RED}[!] Impossible de récupérer les fichiers du dépôt : {response.status_code}{RESET}")
        return

    files = response.json()
    if not files:
        print(f"{YELLOW}[!] Aucun fichier trouvé dans le dépôt.{RESET}")
        return

    # Filtrer seulement les scripts (.sh et .py)
    scripts = [f for f in files if f['name'].endswith(('.sh', '.py'))]
    if not scripts:
        print(f"{YELLOW}[!] Aucun script (.sh ou .py) trouvé dans le dépôt.{RESET}")
        return

    # Afficher la liste des scripts disponibles
    print(f"\n{CYAN}{BOLD}Scripts disponibles dans le dépôt :{RESET}")
    print("-" * 60)
    for idx, script in enumerate(scripts, 1):
        print(f"{idx}. {script['name']}")
    print("-" * 60)

    # Demander à l'utilisateur de sélectionner les scripts
    selection = input("\nEntrez les numéros des scripts (séparés par des virgules) : ").strip()
    if not selection:
        print(f"{YELLOW}[!] Aucune sélection effectuée.{RESET}")
        return

    # Traiter la sélection
    selected_indices = []
    for num in selection.split(','):
        num = num.strip()
        if num.isdigit() and 1 <= int(num) <= len(scripts):
            selected_indices.append(int(num) - 1)

    if not selected_indices:
        print(f"{RED}[!] Aucune sélection valide.{RESET}")
        return

    # Afficher les commandes dans un tableau professionnel
    print(f"\n{CYAN}{BOLD}Commandes d'installation :{RESET}")
    print("=" * 90)
    print(f"{BOLD}| {'Script':<30} | {'Lien RAW':<40} | {'Commande':<50} |{RESET}")
    print("=" * 90)
    
    for idx in selected_indices:
        script = scripts[idx]
        file_name = script['name']
        raw_url = f"https://raw.githubusercontent.com/{config['repo_owner']}/{config['repo_name']}/{config['branch']}/{file_name}"
        
        if file_name.endswith(".sh"):
            commande = f"curl -O {raw_url} && bash {file_name}"
        elif file_name.endswith(".py"):
            commande = f"curl -O {raw_url} && python3 {file_name}"
        else:
            commande = f"curl -O {raw_url}"

        # Afficher chaque ligne du tableau avec des couleurs différentes
        print(f"| {GREEN}{file_name:<30}{RESET} | {CYAN}{raw_url:<40}{RESET} | {YELLOW}{commande:<50}{RESET} |")
    
    print("=" * 90)
    print(f"\n{YELLOW}Copiez les commandes ci-dessus pour installer les scripts sur votre serveur.{RESET}")

def pause_retour_menu():
    input(f"\n{CYAN}Appuyez sur Entrée pour revenir au menu...{RESET}")

def main():
    splash_screen()
    config = load_config()
    if not config:
        config = prompt_config()
    else:
        print(f"{CYAN}[*] Informations chargées depuis la configuration existante.{RESET}")

    while True:
        print("\n" + "=" * 60)
        print(f"{BOLD}Menu :{RESET}")
        print("1. Upload de fichiers")
        print("2. Uploader un script de lancement pour serveur (raw install)")
        print("3. Télécharger des fichiers depuis le dépôt GitHub")     
        print("4. Supprimer des fichiers")
        print("5. Modifier la configuration")
        print("6. Générer les commandes d'installation des scripts")
        print("0. Quitter")

        choice = input("Choisissez une option (0-6) : ").strip()

        if choice == '1':
            files_input = input("\nEntrez les noms des fichiers à uploader (séparés par des virgules) : ").strip()
            file_paths = [f.strip() for f in files_input.split(',') if os.path.exists(f.strip())]
            if not file_paths:
                print(f"{YELLOW}[!] Aucun fichier valide n'a été saisi.{RESET}")
                pause_retour_menu()
                continue

            commit_message = input("Message de commit (Entrée pour valeur par défaut): ").strip()
            if not commit_message:
                commit_message = f"Upload du {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            for file_path in file_paths:
                upload_file_to_github(config['token'], file_path, config['repo_owner'], config['repo_name'], commit_message, config['branch'])
            pause_retour_menu()

        elif choice == '2':
            upload_script_install_serveur(config)
            pause_retour_menu()

        elif choice == '3':
            telecharger_fichiers_depuis_github(config)
            pause_retour_menu()

        elif choice == '4':
            delete_files_from_repo(config)
            pause_retour_menu()

        elif choice == '5':
            config = update_config()
            pause_retour_menu()

        elif choice == '6':
            generer_commandes_installation(config)
            pause_retour_menu()

        elif choice == '0':
            print(f"{GREEN}[✔] Au revoir !{RESET}")
            break

        else:
            print(f"{RED}[!] Choix invalide.{RESET}")
            pause_retour_menu()

if __name__ == '__main__':
    main()
