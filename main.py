import os
import requests
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from colorama import Fore, Style, init

# Initialisation de colorama
init()

# Configuration
ENCRYPTED_SCRIPT_URL = "https://raw.githubusercontent.com/DjahNoDead/IPToP/main/dom1.py.enc"
VERSION_URL = "https://raw.githubusercontent.com/DjahNoDead/IPToP/main/version.txt"
ENCRYPTED_SCRIPT_PATH = "dom1.py.enc"
VERSION_PATH = "version.txt"
DECRYPTION_KEY = "3WDLBJSPHkxCBs/athEeI5lVPmON2t+vOVS0FZhUXc8="  # Clé de déchiffrement

# Fonction pour vérifier les mises à jour
def check_for_updates():
    print(f"{Fore.CYAN}[*] Vérification des mises à jour...{Style.RESET_ALL}")
    try:
        # Télécharger la version distante
        response = requests.get(VERSION_URL)
        response.raise_for_status()  # Lève une exception si le statut n'est pas 200
        remote_version = response.text.strip()

        # Lire la version locale
        if os.path.exists(VERSION_PATH):
            with open(VERSION_PATH, "r") as file:
                local_version = file.read().strip()
        else:
            local_version = "0.0.0"

        # Afficher les versions (pour débogage)
        print(f"{Fore.BLUE}[+] Version locale : {local_version}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}[+] Version distante : {remote_version}{Style.RESET_ALL}")

        # Comparer les versions
        if remote_version != local_version:
            print(f"{Fore.GREEN}[+] Nouvelle version disponible : {remote_version}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[*] Mise à jour en cours...{Style.RESET_ALL}")
            response = requests.get(ENCRYPTED_SCRIPT_URL)
            response.raise_for_status()  # Lève une exception si le statut n'est pas 200
            with open(ENCRYPTED_SCRIPT_PATH, "wb") as file:
                file.write(response.content)
            with open(VERSION_PATH, "w") as file:
                file.write(remote_version)
            print(f"{Fore.GREEN}[+] Mise à jour terminée.{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}[+] Le script est à jour.{Style.RESET_ALL}")
    except requests.exceptions.HTTPError as e:
        print(f"{Fore.RED}[-] Erreur HTTP : {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[!] Vérifiez que l'URL est correcte et que les fichiers existent sur GitHub.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[-] Erreur lors de la vérification des mises à jour : {e}{Style.RESET_ALL}")

# Fonction pour déchiffrer et exécuter le script
def run_encrypted_script():
    print(f"{Fore.CYAN}[*] Déchiffrement et exécution du script...{Style.RESET_ALL}")
    try:
        # Lire le script chiffré
        with open(ENCRYPTED_SCRIPT_PATH, "rb") as file:
            iv = file.read(16)  # Lire l'IV (16 premiers bytes)
            ciphertext = file.read()  # Lire le reste (texte chiffré)

        # Déchiffrer le script
        key = base64.b64decode(DECRYPTION_KEY)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)

        # Afficher le script déchiffré (pour débogage)
        print(f"{Fore.BLUE}[+] Script déchiffré :{Style.RESET_ALL}")
        print(decrypted_data.decode())

        # Exécuter le script déchiffré
        exec(decrypted_data.decode())
    except Exception as e:
        print(f"{Fore.RED}[-] Erreur lors du déchiffrement ou de l'exécution du script : {e}{Style.RESET_ALL}")

# Fonction principale
def main():
    print(f"{Fore.CYAN}\n===== Mode interactif ====={Style.RESET_ALL}")
    while True:
        print("1. Exécuter le script")
        print("2. Vérifier les mises à jour")
        print("3. Quitter")
        choice = input("Choisissez une option : ").strip()

        if choice == "1":
            if not os.path.exists(ENCRYPTED_SCRIPT_PATH):
                print(f"{Fore.YELLOW}[!] Script chiffré introuvable. Téléchargement en cours...{Style.RESET_ALL}")
                check_for_updates()
            run_encrypted_script()
        elif choice == "2":
            check_for_updates()
        elif choice == "3":
            print(f"{Fore.CYAN}[*] Au revoir !{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.RED}[-] Option invalide. Veuillez réessayer.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
