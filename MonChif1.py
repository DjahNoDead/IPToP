import sys
import os
import marshal
import zlib
import time
import random
import string
import hashlib
import argparse
import subprocess
import getpass
import platform

try:
    from Cryptodome.Cipher import AES
    from Cryptodome.Util.Padding import pad, unpad
except ImportError:
    AES = None
    pad = None
    unpad = None

try:
    import psutil
except ImportError:
    psutil = None

# Configuration
FAKE_LINES = 18000
TERMUX_MODE = True
MEMORY_LIMIT_MB = 250

G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
X = "\033[0m"

def check_memory_limit():
    import resource
    mem_bytes = MEMORY_LIMIT_MB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))

def is_vm_environment():
    vm_indicators = [
        "/sys/class/dmi/id/product_name",
        "/proc/scsi/scsi",
        "/sys/class/dmi/id/sys_vendor",
    ]
    keywords = ["VirtualBox", "VMware", "QEMU", "Bochs", "Parallels"]
    for path in vm_indicators:
        if os.path.exists(path):
            with open(path, 'r', errors='ignore') as f:
                content = f.read()
                if any(kw.lower() in content.lower() for kw in keywords):
                    return True
    return False

def check_environment():
    termux_indicators = [
        "/data/data/com.termux/files/usr",
        "TERMUX_VERSION" in os.environ,
        "com.termux" in os.getcwd()
    ]
    return any(termux_indicators) if TERMUX_MODE else True

def detect_debugger():
    if hasattr(sys, 'gettrace') and sys.gettrace() is not None:
        print(f"{R}Débogueur détecté !{X}")
        sys.exit(1)
    if psutil:
        for proc in psutil.process_iter(['pid', 'name']):
            if 'python' in proc.info['name'].lower() and proc.info['pid'] != os.getpid():
                print(f"{R}Débogueur externe détecté !{X}")
                sys.exit(1)

def check_dependencies():
    missing = []
    try:
        import Cryptodome
    except ImportError:
        missing.append("pycryptodome")
    try:
        import psutil
    except ImportError:
        missing.append("psutil")

    if missing:
        print(f"{Y}Installation des dépendances manquantes...{X}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)

def mangle_name():
    ts = str(int(time.time() * 1000))[-4:]
    return '_' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8)) + ts

def generate_fake_code():
    templates = [
        lambda: f"for i in range({random.randint(1,5)}): pass",
        lambda: f"{mangle_name()} = {random.randint(1, 100)} + {random.randint(1,100)}",
        lambda: f"try:\n    x = {random.randint(1,100)}\nexcept: pass",
        lambda: f"def {mangle_name()}(): return '{mangle_name()}'",
        lambda: f"if {random.randint(0,1)}:\n    print('{random.choice(['Debug','Log','Info'])}')"
    ]
    return '\n'.join([random.choice(templates)() for _ in range(FAKE_LINES)])

def generate_strong_password(length=16):
    """ Génère un mot de passe fort de longueur spécifiée """
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def obfuscate(args):
    print(f"\n{Y}=== Obfuscateur Marshal Ultra Pro ===")
    print(f"{G}► Protection renforcée v3.0{X}\n")

    if args.check_deps:
        check_dependencies()

    if args.vm_protect and is_vm_environment():
        print(f"{R}Environnement VM détecté. Arrêt du script.{X}")
        sys.exit(1)

    if not check_environment():
        print(f"{R}Environnement non sécurisé détecté.{X}")
        sys.exit(1)

    if args.mem_limit:
        check_memory_limit()

    detect_debugger()

    input_file = args.script
    if not os.path.exists(input_file):
        print(f"{R}Fichier introuvable.{X}")
        return

    # Demande de la première clé
    user_key1 = getpass.getpass(f"{Y}Clé 1 (laisser vide = auto-générée) : {X}").encode()
    if not user_key1:
        user_key1 = os.urandom(32)
        print(f"{G}Clé 1 auto-générée utilisée.{X}")

    # Demande de la seconde clé
    user_key2 = getpass.getpass(f"{Y}Clé 2 (laisser vide = auto-générée) : {X}")
    if not user_key2:
        user_key2 = generate_strong_password()
        print(f"{G}Clé 2 auto-générée utilisée : {user_key2}{X}")
    user_key2 = user_key2.encode()

    salt = os.urandom(16)
    key = hashlib.scrypt(user_key1, salt=salt, n=2**14, r=8, p=1, dklen=32)

    with open(input_file, 'rb') as f:
        compiled = marshal.dumps(compile(f.read(), '<string>', 'exec'))

    checksum = hashlib.sha256(compiled).digest()
    compressed = zlib.compress(compiled)

    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(compressed, AES.block_size))
    encrypted = cipher.iv + ct_bytes

    decrypt_func_name = mangle_name()
    decrypt_code = ""
    decrypt_code += "from Cryptodome.Cipher import AES\n"
    decrypt_code += "from Cryptodome.Util.Padding import unpad\n"
    decrypt_code += "import hashlib, zlib\n"
    decrypt_code += f"def {decrypt_func_name}():\n"
    decrypt_code += f"    data = {encrypted!r}\n"
    decrypt_code += "    cipher = AES.new(hashlib.scrypt(\n"
    decrypt_code += f"        {user_key1!r},\n"
    decrypt_code += f"        salt={salt!r},\n"
    decrypt_code += "        n=2**14, r=8, p=1, dklen=32\n"
    decrypt_code += "    ), AES.MODE_CBC, data[:16])\n"
    decrypt_code += "    decrypted = unpad(cipher.decrypt(data[16:]), AES.block_size)\n"
    decrypt_code += f"    if hashlib.sha256(zlib.decompress(decrypted)).digest() != {checksum!r}:\n"
    decrypt_code += "        __import__('os')._exit(1)\n"
    decrypt_code += "    return decrypted\n"

    output_file = args.output or f"{os.path.splitext(input_file)[0]}_obf.py"

    # On redirige la sortie vers os.devnull pour supprimer les faux messages
    fake_code = generate_fake_code()
    fake_code = f"import sys\nsys.stdout = open(os.devnull, 'w')\n{fake_code}\nsys.stdout = sys.__stdout__\n"

    payload = "#!/usr/bin/env python3\n"
    payload += "import sys, os, marshal, zlib\n"
    payload += "if sys.gettrace() is not None: os._exit(1)\n"
    payload += "# Redirection de stdout pour supprimer tous les messages\n"
    payload += "_original_stdout = sys.stdout\n"
    payload += "sys.stdout = open(os.devnull, 'w')\n"
    payload += fake_code + "\n"
    payload += "sys.stdout = _original_stdout\n"
    payload += decrypt_code.strip() + "\n"  # Nettoyer decrypt_code
    payload += f"exec(marshal.loads(zlib.decompress({decrypt_func_name}())))\n"

    with open(output_file, 'w') as f:
        f.write(payload)

    print(f"\n{G}Obfuscation terminée avec succès !")
    print(f"{Y}► Script généré : {output_file}{X}")

def interactive_mode():
    print(f"\n{Y}=== Mode interactif ==={X}")
    script_name = input(f"{Y}Nom du script à obfusquer : {X}")
    obfuscate(type('Args', (), {
        'script': script_name,
        'output': None,
        'vm_protect': False,
        'mem_limit': False,
        'check_deps': False
    }))

def main():
    # Si aucun argument n'est passé, active le mode interactif
    if len(sys.argv) < 2:
        interactive_mode()
    else:
        parser = argparse.ArgumentParser(description="Obfuscateur Python Ultra Pro")
        parser.add_argument("script", help="Fichier Python à obfusquer")
        parser.add_argument("-o", "--output", help="Fichier de sortie")
        parser.add_argument("--vm-protect", action="store_true", help="Activer la détection de machine virtuelle")
        parser.add_argument("--mem-limit", action="store_true", help="Limiter la mémoire à 250 Mo")
        parser.add_argument("--check-deps", action="store_true", help="Vérifie et installe les dépendances")
        args = parser.parse_args()

        obfuscate(args)

if __name__ == "__main__":
    main()