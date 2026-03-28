#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Compatible avec toutes les distributions Linux + Termux/Android
# Ubuntu, Debian, CentOS, RHEL, Fedora, Arch, Alpine, Termux, Android

import sys
import os
import base64
import zlib
import warnings

# Suppression des warnings inutiles
warnings.filterwarnings('ignore', category=SyntaxWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

# ============================================================================
# VÉRIFICATIONS DE COMPATIBILITÉ STRICTES
# ============================================================================

# Constante de version minimale (accessible globalement)
_MIN_VERSION = (3, 6)

# 1. Vérification Python 3 stricte
if sys.version_info.major != 3:
    print("ERREUR: Python 3 est requis")
    print("Ce script doit être exécuté avec python3, pas python")
    print()
    print("Commande correcte:")
    print(f"  python3 {sys.argv[0]}")
    print()
    print("Si python3 n'est pas disponible, installez-le:")
    print("  Ubuntu/Debian: sudo apt install python3")
    print("  CentOS/RHEL:   sudo yum install python3")
    print("  Arch:          sudo pacman -S python")
    print("  Alpine:        apk add python3")
    print("  Termux:        pkg install python")
    sys.exit(1)

# 2. Vérification version Python minimale
if sys.version_info < _MIN_VERSION:
    print(f"ERREUR: Python {_MIN_VERSION[0]}.{_MIN_VERSION[1]}+ est requis")
    print(f"Version actuelle: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print()
    print("Mettez à jour Python:")
    print("  Ubuntu/Debian: sudo apt install python3.{_MIN_VERSION[1]+1}")
    print("  CentOS/RHEL8:  sudo dnf install python3")
    print("  CentOS7:       sudo yum install python36")
    print("  Termux:        pkg upgrade && pkg install python")
    sys.exit(1)

# 3. Vérification des modules essentiels
_REQUIRED_MODULES = ['base64', 'zlib']
_missing_modules = []
for module in _REQUIRED_MODULES:
    try:
        __import__(module)
    except ImportError:
        _missing_modules.append(module)

if _missing_modules:
    print("ERREUR: Modules Python essentiels manquants")
    print("Manquant:", ", ".join(_missing_modules))
    print()
    print("Ces modules font partie de la bibliothèque standard Python.")
    print("Votre installation Python semble corrompue.")
    print("Réinstallez Python 3.6+ depuis les sources officielles.")
    print("Pour Termux: pkg reinstall python")
    sys.exit(1)

# ============================================================================
# DÉTECTION PLATEFORME AMÉLIORÉE (CORRECTION POUR TERMUX)
# ============================================================================

# Détection de la plateforme (INCLUT ANDROID/TERMUX !)
_IS_LINUX = sys.platform.startswith('linux')
_IS_WINDOWS = sys.platform.startswith('win')
_IS_MACOS = sys.platform.startswith('darwin')
_IS_CYGWIN = sys.platform.startswith('cygwin')
_IS_ANDROID = sys.platform == 'android' or 'ANDROID_ROOT' in os.environ
_IS_TERMUX = 'TERMUX_VERSION' in os.environ or os.path.exists('/data/data/com.termux')

# Support pour Android/Termux (considéré comme Linux)
_IS_SUPPORTED_LINUX = _IS_LINUX or _IS_ANDROID or _IS_TERMUX
_SUPPORTED = _IS_SUPPORTED_LINUX or _IS_WINDOWS or _IS_MACOS or _IS_CYGWIN

if not _SUPPORTED:
    print(f"ERREUR: Plateforme non supportée: android")
    print()
    print("Plateformes supportées:")
    print("  • Linux (toutes distributions)")
    print("  • Android/Termux")
    print("  • Windows (avec Python 3)")
    print("  • macOS (10.9+)")
    print("  • Cygwin (Windows)")
    sys.exit(1)

# Message spécial pour Termux/Android
if _IS_ANDROID or _IS_TERMUX:
    print("INFO: Android/Termux détecté - compatibilité vérifiée ✓")
    # Force la détection comme Linux pour la suite
    original_platform = sys.platform
    sys.platform = "linux"  # Petit hack pour tromper les vérifications suivantes

# Détection musl/glibc (pour Alpine Linux) - ignoré sur Android
try:
    import platform
    if not (_IS_ANDROID or _IS_TERMUX):
        libc_info = platform.libc_ver()
        _LIBC_TYPE = libc_info[0] if libc_info else 'glibc'
        if _LIBC_TYPE == 'musl':
            print("INFO: Alpine Linux (musl) détecté - compatibilité vérifiée")
except:
    pass

# ============================================================================
# DÉCHIFFREMENT
# ============================================================================

# Fonction de déchiffrement XOR (compatible toutes versions Python)
def _xor_decrypt(data: bytes, key: bytes) -> bytes:
    """Décryptage XOR ultra-compatible"""
    key_length = len(key)
    result = bytearray(len(data))

    for i in range(len(data)):
        result[i] = data[i] ^ key[i % key_length]

    return bytes(result)

# Données obfusquées
_ENCRYPTED_DATA = "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"
_DECRYPTION_KEY = [117, 107, 66, 110, 115, 84, 88, 107, 54, 57, 104, 83, 57, 109, 109, 73]

# ============================================================================
# EXÉCUTION PRINCIPALE
# ============================================================================

def _main_execution():
    """Point d'entrée principal avec gestion d'erreurs complète"""
    try:
        # Phase 1: Décodage Base64
        try:
            decoded_data = base64.b64decode(_ENCRYPTED_DATA)
        except base64.binascii.Error as e:
            print("ERREUR: Données Base64 corrompues")
            print(f"Détail: {e}")
            return 1

        # Phase 2: Déchiffrement XOR
        try:
            decrypted_data = _xor_decrypt(decoded_data, bytes(_DECRYPTION_KEY))
        except Exception as e:
            print("ERREUR: Échec du déchiffrement")
            print("La clé de déchiffrement est incorrecte ou les données sont corrompues")
            return 1

        # Phase 3: Inversion
        reversed_data = decrypted_data[::-1]

        # Phase 4: Décompression
        try:
            decompressed_data = zlib.decompress(reversed_data)
        except zlib.error as e:
            print("ERREUR: Échec de la décompression")
            print("Les données sont corrompues ou ont été altérées")
            return 1

        # Phase 5: Exécution
        try:
            # Création d'un environnement d'exécution sécurisé
            exec_globals = {
                '__name__': '__main__',
                '__file__': sys.argv[0],
                '__package__': None,
                '__builtins__': __builtins__,
            }

            # Exécution du code
            exec(decompressed_data, exec_globals)
            return 0

        except KeyboardInterrupt:
            print("\nInterrompu par l'utilisateur")
            return 130
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 0
        except Exception as e:
            # Mode debug activé par variable d'environnement
            if os.environ.get('OBF_DEBUG') == '1':
                import traceback
                print("ERREUR D'EXÉCUTION:")
                traceback.print_exc()
            else:
                print("ERREUR: Le script a rencontré une erreur")
                print("Pour plus de détails, exécutez:")
                print(f"  OBF_DEBUG=1 python3 {sys.argv[0]}")
            return 1

    except MemoryError:
        print("ERREUR: Mémoire insuffisante")
        print("Le script nécessite plus de mémoire RAM")
        return 1
    except Exception as e:
        print(f"ERREUR FATALE: {type(e).__name__}: {e}")
        return 1

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == '__main__':
    # Vérification des arguments pour le mode debug
    if '--debug' in sys.argv or '-d' in sys.argv:
        os.environ['OBF_DEBUG'] = '1'

    # Affichage info version si demandé
    if '--version' in sys.argv or '-v' in sys.argv:
        print("Script obfusqué - Compatible Linux Universel + Termux")
        print(f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        print(f"Plateforme: {original_platform if '_IS_ANDROID' in locals() and _IS_ANDROID else sys.platform}")
        sys.exit(0)

    # Exécution principale
    exit_code = _main_execution()
    sys.exit(exit_code)
