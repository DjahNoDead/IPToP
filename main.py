import os
import requests
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# Configuration
ENCRYPTED_SCRIPT_URL = "https://raw.githubusercontent.com/DjahNoDead/IPToP/main/dom1.py.enc"
VERSION_URL = "https://raw.githubusercontent.com/DjahNoDead/IPToP/main/version.txt"
ENCRYPTED_SCRIPT_PATH = "dom1.py.enc"
VERSION_PATH = "version.txt"
DECRYPTION_KEY = "iiCxImwY4vNOqR3tS/KpgogvLIp3ykXEHmr9845r5OE="  # Clé de déchiffrement

# Fonction pour vérifier les mises à jour
def check_for_updates():
    print("Vérification des mises à jour...")
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

        # Comparer les versions
        if remote_version != local_version:
            print(f"Nouvelle version disponible : {remote_version}")
            print("Mise à jour en cours...")
            response = requests.get(ENCRYPTED_SCRIPT_URL)
            response.raise_for_status()  # Lève une exception si le statut n'est pas 200
            with open(ENCRYPTED_SCRIPT_PATH, "wb") as file:
                file.write(response.content)
            with open(VERSION_PATH, "w") as file:
                file.write(remote_version)
            print("Mise à jour terminée.")
        else:
            print("Le script est à jour.")
    except requests.exceptions.HTTPError as e:
        print(f"Erreur HTTP : {e}")
        print("Vérifiez que l'URL est correcte et que les fichiers existent sur GitHub.")
    except Exception as e:
        print(f"Erreur lors de la vérification des mises à jour : {e}")

# Fonction pour déchiffrer et exécuter le script
def run_encrypted_script():
    print("Déchiffrement et exécution du script...")
    try:
        # Lire le script chiffré
        with open(ENCRYPTED_SCRIPT_PATH, "rb") as file:
            iv = file.read(16)  # Lire l'IV (16 premiers bytes)
            ciphertext = file.read()  # Lire le reste (texte chiffré)

        # Déchiffrer le script
        key = base64.b64decode(DECRYPTION_KEY)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)

        # Exécuter le script déchiffré
        exec(decrypted_data.decode())
    except Exception as e:
        print(f"Erreur lors du déchiffrement ou de l'exécution du script : {e}")

# Fonction principale
def main():
    print("===== Mode interactif =====")
    while True:
        print("1. Exécuter le script")
        print("2. Vérifier les mises à jour")
        print("3. Quitter")
        choice = input("Choisissez une option : ").strip()

        if choice == "1":
            if not os.path.exists(ENCRYPTED_SCRIPT_PATH):
                print("Script chiffré introuvable. Téléchargement en cours...")
                check_for_updates()
            run_encrypted_script()
        elif choice == "2":
            check_for_updates()
        elif choice == "3":
            print("Au revoir !")
            break
        else:
            print("Option invalide. Veuillez réessayer.")

if __name__ == "__main__":
    main()
