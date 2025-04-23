import os
import requests
import base64
import hashlib
from datetime import datetime
from crypto_engine import decrypt

SCRIPT_URL = 'https://raw.githubusercontent.com/DjahNoDead/IPToP/refs/heads/main/encrypted_a.py.txt'
SIGNATURE_URL = 'https://raw.githubusercontent.com/DjahNoDead/IPToP/refs/heads/main/signature_encrypted_a.py.txt'
SALT = 'yp.a_custom_salt'
CACHE_FILE = "script_cache.txt"
EXPIRATION_DATE = datetime.strptime("2025-05-02", "%Y-%m-%d")

def verify_signature(data, expected_hash):
    actual_hash = hashlib.sha256(data.encode()).hexdigest()
    return actual_hash == expected_hash

def fetch_remote_script():
    try:
        print("[*] Tentative de téléchargement du script...")
        r = requests.get(SCRIPT_URL, timeout=5)
        if r.status_code == 200:
            content = r.text.strip()
            sig_resp = requests.get(SIGNATURE_URL, timeout=5)
            if sig_resp.status_code == 200:
                signature = sig_resp.text.strip()
                if verify_signature(content, signature):
                    print("[+] Intégrité vérifiée (SHA-256).")
                    with open(CACHE_FILE, "w") as f:
                        f.write(content)
                    return content
                else:
                    print("[!] Signature invalide ! Fichier altéré.")
            else:
                print("[!] Signature introuvable.")
        else:
            print("[-] Erreur HTTP :", r.status_code)
    except Exception as e:
        print("[!] Erreur de téléchargement :", e)
    return None

def load_cached_script():
    if os.path.exists(CACHE_FILE):
        print("[*] Utilisation du cache local...")
        with open(CACHE_FILE, "r") as f:
            return f.read().strip()
    else:
        print("[-] Aucun cache disponible.")
    return None

def execute_script(encoded_script):
    try:
        decrypted = decrypt(encoded_script, SALT)
        print("[+] Script déchiffré. Exécution en mémoire...")
        exec(decrypted, {'__name__': '__main__'})
    except Exception as e:
        print("[!] Erreur d'exécution :", e)

def main():
    if datetime.today() > EXPIRATION_DATE:
        print("[-] Période expirée. Mise à jour requise.")
    encrypted_script = fetch_remote_script() or load_cached_script()
    if encrypted_script:
        execute_script(encrypted_script)
    else:
        print("[-] Impossible d'exécuter le script.")

if __name__ == "__main__":
    main()
