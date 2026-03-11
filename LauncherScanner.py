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
_DECRYPTION_KEY = [74, 101, 77, 87, 102, 116, 119, 103, 69, 87, 89, 112, 70, 82, 50, 90]

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
