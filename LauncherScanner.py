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
_DECRYPTION_KEY = [102, 82, 108, 74, 88, 89, 99, 71, 69, 121, 85, 82, 112, 65, 117, 66]

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
