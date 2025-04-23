import os, requests, base64, hashlib
from datetime import datetime
from crypto_engine import decrypt, verify_signature, verify_file_hash

SCRIPT_URL = "https://raw.githubusercontent.com/DjahNoDead/IPToP/refs/heads/main/encrypted_a.py.txt"
SIGNATURE = "Rp4gR33G/kA4s7AnKBCMXa/YZHMYO4U0njyTqmSXgMu+gK64H+gGF6VpCSW0jy8xjbm5RL2TcZFejcaiu1ydYxZ/zVl8WknjzBWG7ba2oJA4J2+sB1xwp1O7A3yVN2h6fvIay4uhRF01KwS6aYFhozZ74LLcLbV/MfnZtyk7tecNRy6ZQmd00D6Akq2pko5jwTke8uM/mGcH3FCqXUk6EBErN7uAto6SA8ZbjnAzmpSszfw9cBNtdmln8uwiQkvqPpqY5rw3UNdhggJnMYKZn1W+DEoTbuxrAscfUskIpi6z/TJ+W07+mXQ6up8/Rgcrc0j01UU1nlId43NNApAkzA=="
EXPECTED_HASH = "189238861c1793fc962fa6a8ece3fec141521e1eead4b73372432ccb99ed4d2e"
SALT = "yp.a_custom_salt"
EXPIRATION_DATE = datetime.strptime("2025-05-02", "%Y-%m-%d")

CACHE_FILE = "script_cache.txt"

def fetch_remote_script():
    try:
        print("[*] Tentative de téléchargement du script...")
        r = requests.get(SCRIPT_URL, timeout=5)
        if r.status_code == 200:
            print("[+] Script téléchargé.")
            return r.text.strip()
        else:
            print("[-] Erreur HTTP :", r.status_code)
    except Exception as e:
        print(f"[!] Échec du téléchargement : {e}")
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
    if not verify_signature(encoded_script, SIGNATURE) or not verify_file_hash(encoded_script, EXPECTED_HASH):
        print("[!] Intégrité ou authenticité compromise. Exécution bloquée.")
        return
    try:
        decrypted_code = decrypt(encoded_script, SALT)
        print("[+] Script déchiffré. Exécution en mémoire...")
        exec(decrypted_code, {'__name__': '__main__'})
    except Exception as err:
        print(f"[!] Erreur d'exécution : {err}")

def main():
    if datetime.today() > EXPIRATION_DATE:
        print("[-] Période expirée. Mise à jour autorisée.")

    script = fetch_remote_script() or load_cached_script()
    if script:
        with open(CACHE_FILE, "w") as f:
            f.write(script)
        execute_script(script)
    else:
        print("[-] Impossible d'exécuter le script.")

if __name__ == "__main__":
    main()
