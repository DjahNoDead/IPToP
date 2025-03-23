import os
import requests
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import hashlib

# Configuration
ENCRYPTED_SCRIPT_URL = "https://github.com/DjahNoDead/IPToP/raw/refs/heads/main/httpG.enc"
VERSION_URL = "https://github.com/DjahNoDead/IPToP/raw/refs/heads/main/httpG_version.txt"
SIGNATURE_URL = "https://github.com/DjahNoDead/IPToP/raw/refs/heads/main/httpG.sig"
ENCRYPTED_SCRIPT_PATH = "httpG.enc"
VERSION_PATH = "httpG_version.txt"
SIGNATURE_PATH = "httpG.sig"

# Fonction pour vérifier l'intégrité du fichier
def verify_file_integrity(file_path, signature_path):
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
        with open(signature_path, "r") as f:
            stored_hash = f.read().strip()
        sha256_hash = hashlib.sha256(file_data).hexdigest()
        return sha256_hash == stored_hash
    except Exception as e:
        print(f"Erreur lors de la vérification de l'intégrité : {e}")
        return False

# Fonction pour vérifier les mises à jour
def check_for_updates():
    print("[*] Vérification des mises à jour...")
    try:
        # Télécharger la version distante
        response = requests.get(VERSION_URL)
        response.raise_for_status()
        remote_version = response.text.strip()

        # Lire la version locale
        if os.path.exists(VERSION_PATH):
            with open(VERSION_PATH, "r") as file:
                local_version = file.read().strip()
        else:
            local_version = "0.0.0"

        # Comparer les versions
        if remote_version != local_version:
            print(f"[+] Nouvelle version disponible : {remote_version}")
            print("[*] Mise à jour en cours...")
            response = requests.get(ENCRYPTED_SCRIPT_URL)
            response.raise_for_status()
            with open(ENCRYPTED_SCRIPT_PATH, "wb") as file:
                file.write(response.content)
            response = requests.get(SIGNATURE_URL)
            response.raise_for_status()
            with open(SIGNATURE_PATH, "wb") as file:
                file.write(response.content)
            with open(VERSION_PATH, "w") as file:
                file.write(remote_version)
            print("[+] Mise à jour terminée.")
        else:
            print("[+] Le script est à jour.")
    except Exception as e:
        print(f"[-] Erreur lors de la vérification des mises à jour : {e}")

# Fonction pour déchiffrer et exécuter le script
def run_encrypted_script():
    print("[*] Déchiffrement et exécution du script...")
    try:
        # Vérifier l'intégrité du fichier chiffré
        if not verify_file_integrity(ENCRYPTED_SCRIPT_PATH, SIGNATURE_PATH):
            print("[-] Le fichier chiffré est corrompu ou a été modifié.")
            return

        # Lire le script chiffré
        with open(ENCRYPTED_SCRIPT_PATH, "rb") as file:
            iv = file.read(16)  # Lire l'IV (16 premiers bytes)
            ciphertext = file.read()  # Lire le reste (texte chiffré)

        # Demander la clé de déchiffrement
        password = input("Entrez le mot de passe pour déchiffrer le script : ")
        key = hashlib.sha256(password.encode()).digest()

        # Déchiffrer le script
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)

        # Exécuter le script déchiffré
        exec(decrypted_data.decode())
    except Exception as e:
        print(f"[-] Erreur lors du déchiffrement ou de l'exécution du script : {e}")

# Fonction principale
def main():
    print("\n===== Mode interactif =====")
    while True:
        print("1. Exécuter le script")
        print("2. Vérifier les mises à jour")
        print("3. Quitter")
        choice = input("Choisissez une option : ").strip()

        if choice == "1":
            if not os.path.exists(ENCRYPTED_SCRIPT_PATH):
                print("[!] Script chiffré introuvable. Téléchargement en cours...")
                check_for_updates()
            run_encrypted_script()
        elif choice == "2":
            check_for_updates()
        elif choice == "3":
            print("[*] Au revoir !")
            break
        else:
            print("[-] Option invalide. Veuillez réessayer.")

if __name__ == "__main__":
    main()
