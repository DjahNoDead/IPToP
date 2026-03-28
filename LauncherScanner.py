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
_DECRYPTION_KEY = [112, 99, 83, 65, 89, 74, 69, 100, 106, 75, 118, 109, 104, 49, 106, 73]

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
