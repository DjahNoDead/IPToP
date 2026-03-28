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
_DECRYPTION_KEY = [72, 99, 112, 103, 105, 107, 51, 89, 67, 101, 57, 109, 65, 116, 57, 90]

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
