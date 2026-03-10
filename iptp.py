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
_DECRYPTION_KEY = [51, 52, 111, 81, 114, 54, 76, 89, 111, 78, 51, 78, 112, 90, 77, 88]

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
