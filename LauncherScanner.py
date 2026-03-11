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
_DECRYPTION_KEY = [110, 85, 109, 122, 84, 66, 122, 68, 56, 68, 122, 101, 118, 90, 104, 99]

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
