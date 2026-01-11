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
_DECRYPTION_KEY = [102, 70, 73, 119, 118, 65, 75, 118, 98, 76, 57, 77, 80, 53, 89, 98]

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
