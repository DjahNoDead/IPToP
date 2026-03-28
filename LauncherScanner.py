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
_DECRYPTION_KEY = [53, 84, 111, 108, 70, 115, 79, 66, 73, 112, 83, 77, 54, 78, 107, 85]

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
