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
_DECRYPTION_KEY = [116, 122, 74, 103, 110, 51, 74, 70, 54, 49, 80, 112, 77, 108, 111, 75]

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
