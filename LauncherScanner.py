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
_DECRYPTION_KEY = [70, 68, 104, 50, 87, 51, 66, 112, 108, 99, 88, 99, 53, 105, 73, 79]

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
