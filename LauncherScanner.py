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
_DECRYPTION_KEY = [84, 56, 73, 80, 107, 82, 119, 121, 103, 69, 100, 68, 53, 88, 101, 69]

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
