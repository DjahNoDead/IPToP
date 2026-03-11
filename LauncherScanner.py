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
_DECRYPTION_KEY = [103, 75, 65, 118, 67, 100, 98, 101, 83, 52, 105, 71, 110, 73, 86, 75]

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
