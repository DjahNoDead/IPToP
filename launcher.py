#!/usr/bin/env python3
import os, sys, urllib.request, ssl, json, shutil
from datetime import datetime

VERSION = "1.2"
SCRIPT_NAME = "cOr_obf.py"
UPDATE_URL = "https://raw.githubusercontent.com/DjahNoDead/IPToP/refs/heads/main/update.json"
EXPIRATION_DATE = "None"  # Ajout ici

def check_expiration():
    if EXPIRATION_DATE and EXPIRATION_DATE.lower() != "none":
        today = datetime.now().strftime("%d-%m-%y")
        exp_day, exp_month, exp_year = map(int, EXPIRATION_DATE.split("-"))
        today_day, today_month, today_year = map(int, today.split("-"))
        exp_date = datetime(exp_year+2000, exp_month, exp_day)
        today_date = datetime(today_year+2000, today_month, today_day)
        if today_date > exp_date:
            print(f"\033[91mVotre version a expiré le {EXPIRATION_DATE}.\033[0m")
            sys.exit(1)

def check_for_update():
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(UPDATE_URL, context=ctx) as response:
            update_info = json.loads(response.read().decode())
            if update_info.get("version") != VERSION:
                print("\033[93mNouvelle version disponible : v" + update_info.get("version") + "\033[0m")
                return update_info
    except Exception as e:
        print(f"\033[91mErreur lors de la vérification de mise à jour : {e}\033[0m")
    return None

def apply_update(update_info):
    try:
        print("\033[93mTéléchargement de la nouvelle version...\033[0m")
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(update_info["download_url"], context=ctx) as response:
            new_code = response.read()
        backup_name = SCRIPT_NAME + ".bak"
        if os.path.exists(SCRIPT_NAME):
            shutil.copyfile(SCRIPT_NAME, backup_name)
            print("\033[92mSauvegarde réalisée :\033[0m", backup_name)
        with open(SCRIPT_NAME, "wb") as f:
            f.write(new_code)
        print("\033[92mMise à jour appliquée avec succès.\033[0m")
        os.execv(sys.executable, [sys.executable, SCRIPT_NAME])
    except Exception as e:
        print(f"\033[91mErreur lors de l'application de mise à jour : {e}\033[0m")

def main():
    check_expiration()
    update_info = check_for_update()
    if update_info:
        apply_update(update_info)
    else:
        try:
            with open(SCRIPT_NAME, "rb") as f:
                exec(compile(f.read(), SCRIPT_NAME, "exec"))
        except Exception as e:
            print(f"\033[91mErreur lors de l'exécution du script : {e}\033[0m")

if __name__ == "__main__":
    main()
