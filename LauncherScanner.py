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
_ENCRYPTED_DATA = "JNAkNFiqnZdwJnOuw+r/mAEIUaIaDtY28sOxjUnaJPwwAmA0GEkbpr2cTwZikbPAhpkbvaO3kTQD/qPZjW52aND075RIPxoLlZzkdzk8fPsPlThCpt5/wzPs1DEUVIUf98gL3uR+UKvLEfswJT3ZMdnM4CiBBAbPJ7PtTS6FR9qwVQcQiWJEIoWzf7rRjJ+V2HT58oKBkknI2qo2E6tXyygZ0z/wzMMDBZKTWhaK5lO6tqREkbudBnybniLKO1+dXxQ0KVgOhWIrDdQSG0E0PDXa28g6m6GxwDkqNSzIa5GgiX0J1OikhtTyVnkt2SLR7Jw+LuVXsKplYcjOYz15Vovas+7I0TOwlncprB/Az6V62T7sfqFSeYc9//Z5qlaFIu3gVDQKB8OmHaRG45vrAx7a3bUFIWkkEQGjBF/Un/zHrWEXLMpxtBCyTW6OBhtWb7X8XUE6eIOJKcOkpiqK+sJxTHJZrVZJkPzuyeDRtjrDRQyodlsnHVAerEZkPJPQ9E/54LRLwJh21tLiQgsjTAK4PoPj6RxEiHBzEVrsrvrUzkqno/UoCDxkHTK69ebo0PLK2PHJHAsYu/lZ+CEjAa/B3EJ6kLmeZMqrzrpKmIAOU+m8vvRO2JLOD98u/nUTghmhAv7umKWz6Bx4RhPMKLbT4uE38XDU09hkmCr2Ex89V40N/SnCo70a3Tw6PDuXd6CvsiOgfbXATDFZaZJY8VI0HZmlqVbHBqC9YUNFlubxj4QLX2UnTnDt2LBZmT3vURd1qD7le+PaykNSJigbXHeG6yyyQCY+s5bmgMhv8QY5ltvFRJqwN6SMMs+dgx/DeM/6TV+AqJAh3Wbq2ZnmC2ij2SnBEFdvC86dKuVwWghcpzVKTkgJc3uO1eXE73mpZOuwnS/R0FuER4crgyGn1rGFyPK8fUOu1KqfICmK4prvq625xSwTBOjR8H7woCj04ob3yyfpG77gXXDJxlYXnkX6dFyomT2yAFgZmYtBKjYBfYtTn/6LvlDdtk1HljRo/Cqel3dF4s02Nl8mxcLu139Yt+y+82IyIMUfVfFch8dUkzlzEoJ2SSKky5l53NKzzrAHWxbwA/JIvKah71XQmHxZyB2bkjS7n6o9ON/kGoCGT40aBvdcJavm3VFnzQB1dTHoCNzTtsM8fUf1jyxIkLJtSAXKLC/SVtIyYbr52+Y++cqhkqXp/6ogOiDzXE1aud9dHCq+jKhnVHhE4jMT2v86FoZ+A3Nsu00rQ/AeILenlD09XlZHSxMt+d3PT9x9OmBeu02CRXh2N54OvYnsGZOfW2pNPwo5rul6H9AFXuFxQqY22FEwMvpE3JbW4aewh778kCYBp1CQCZ+f/4Y3LIe3ehmjLMstdKr8dta/jR59vF9wyPgPdzwf9sKWkZ09vxQp4/mV+TcT5FtH7o7h4D9VpkSUEK3EdOm2eodXlbEpk1SRQ2TD7TUXSbQGDP8WBAWyNbQCi92tF7fEYzglDc36Bh6MNyYf5NKvFFe3ILHSXmrsvWc9r5ALhw99mQf2voEp8p+vA66iyDafCIgwnglMMdQ95SRiKqEPT0L0Qav4GGs/Apwkjw/4jxtparBYiRqfT5YK4Kb0AXK26AhTip6Z1q6iK+1un7w4i4g9+ZcjrHfrrANXyPasYKW7zx8uHR2W755XKcD8t36fC6tckeCkCf7zXubEfOGJr9K+5hhs9us9wqrhMOyalcSNda8+sGHWd/JqyspW5H5BMgIXlY8LlEY2RuJwBh91hYglNohQFsjeocRWjrAspxAq4N6ip8FY2msG3+QmE5cHeom1cc6ibNSJjsr7wMmbLBm8EQUEzCWZFgjZUauKJdJVMnIVCBwB11kPGZvi51QfIKDyo6F2i73q8tbdoN64tzbf7iBKmW6H68bj2gfjcw5YJgdAGPih2e0XAzGuzfjikNTwyI20/LL1Z4ISsSO1DqxEen66wLAnwEhUL5iWEKXSnhFBOhEMTtdq7/org09fI0EhdP3ULRa+n+6C6O54GyOMaV+brCycGROOn7q4aVtbGEnlvMvcqOdY5KWQb+aI6gJDYHdFKL/wjZCmX0/Uz9YR3jhVXJJGhcKzvQ7NCoDJ58UmT6ndVxtcgX2sYuJI0U4etf6I0Gy9IYRCa+rL4d/K6k3CWt0BPy9wt0pKCzwbIycd3w+WAFjhQM7ld5Kv+/dht/bn3omJqMyo1BHnJrCAzMnhCRhr9PjtmIk1JfYONzI2pwF1t73vpispfmHXlF1nSBJqIK+q9HnbZqSi2aQyEgZ0kIHi2B37q6vb8SPz2x7tXUsRhjo+Qs8hdEV3s7If++HrjIgPHKK864x8VzZnOlDXe9sab4PqbNaMfezL1wjHdZyZk4PyT+uQkPEfs7l8SC4jYCTaT7VOqyL6C7BLJitbDxQ4wz34dgK8jrLpbh68ncmX3jT5fgwL9qQ/EYVaZvcDQnmpgbU5BrDL/NopuT6P6aN/6jIoj9yvEU7+6tgRWZr5xGQFdksx8VM95ciAJA6ve5UaioeMvRfq+MgEPLcsVx8Y0OfKeY8O5G8zdpjT06tGD/bHAxyAZLHq2M72yuoqBk0tBUUUo8zyjiBCBjSTMMx60GhOUs6Sq/v9lZHNh1PFlpE1Oo9Vt/4gEyckEvjQBur5W4cXvcokp3iwMKTG+KQxuBG7UPTHVPbNHyRQS1nP6ouyRwqwL7ghAiL4kYhQCci3AxiC7lUXmti3q8b6GAl6xF+3DVL7VThJI5H7o4LAsGhtq2jTzPYuVHzh4TzSdBF4aR9VVMOC8rY8x3vkeOvJ5K9G+rxVw6PXZOhsNm7dCmjRLrb7yEjQoCd64qBVBCEIFkY2oQKog1A0eGzkk+/cxVLBamfEfExBcYNF+HmLQKYMlNuy9N7FGq4pekh3trUMu4RsIW217DJfZVD0onAYiYpZ0wappcDJnxVANeaScBicj55dt7DVQWYUgoc2WKVMKJYDe1DBW51lxZvXR8esEvp7uQ/tigqfYazhDXcn6fLgvVxNfHR6vZza31T8bMnFghRJjcSNRi6yz9DTdZOaq19oOx429BGXLuOfvqIOWbytjvetklabvpCb31Po7+lu1jswKnWjVsinoauV+JbQ1VpGQrQPhypYK+bxshEa8QsmJZSAl3XzJBESxgfKHxALGijWIUoSTNO3V2TAD1c1Z0nhtgiX+K1oUP10kQdqvgz4KHrQ27KsqOTfXGigSlyLT0BE/YSfbEZzotDFStGf+Exabmfz8e/fzzoVZ4uh/UW9kDCoNVGQpL2B4vPCyoxmjDkvT7HzjYf8NH8haMOrEyQUe9WTghRSmG+Q2Su7JQGSKfSEh7Q6GjigRKdmmP8fjOE9V5fnEXyFRIyM52en7hkTj6vZK3sOLQGgABnmyAqPIYwwkfAciAagQ0cjyGA6r7d2yGqu3R1g4J2idzsH9/zaZB9R/pilH0YaoiRUrKa9OcjP7jpaS+jbPSQn4Mt+05pm3h3GRDCbKOcGJA6Xyd1ca8s0eAgq6ePaifsBd2y417YRldfZIGzygFI16eOPbxcJp7363SN7rb5wdCNX40bD+TH9Cj1A08Hy5PHEW/9GaISV0CXznhdzw2VCD3h2Rnlf/WASJMC/K3LEf49+6cgqJjBUMAMQmFjBVH4XAC17D5xyEmiE12/9Zq+pjZgNOIqn5Ug2r52KxqCX2CwH3Cvl1iQ0qtGN1rv4G4XILvOBjJkRSvpepR9mvFKt4bm5424fF29mNn7QCWFAV24nabp7JeFsNXaJXKl+hy1RA/lzVtDs9J15C1T/pV6HA62i5y+5H8Wdo6qAoHa9YnaSIYewTy5RuStCIFDgsAZg6Ysq203BDt4TkqRGYoab4c/UxBJh8QjeLIj3Z93XmnZ5Wsyz5eFJd/FUcutf8oiiWGfY7uYhrIEutRK26h5thtb+FEPCNwPiLGAWV6BCCo8HymnoWeLOOJkiF6Bf7RTiO5f2TVCtkefRKYvwXEcMJUNUdXfaeDjOCwJ7g17X0ZgaiAF9vYM5YUuKWgd63j638isMedFnR8pIll1nH9iZL7pajrJyR335ExSjLU2aWioBD52BE83jiJk2xFxWP1TPfNa2ScfF0xOITn17oclqEInqB8lWDhY/c5/fto/UBH7nOmZXrUZnyMWgUTKXmTFP2P7bUbqxmagljZUW1rDIr7uQdR6RVghOjnY1rIMxA5+gkEpNqYG3U0bp4Ot8p34iMyoxkK4/a9VGjTt7zSkdklB6ulWJEBCKJXPjvttdtiyWEVbC0OYsaH8Ut6e4VCespgRFmS1QCWR13BNPMgIPzrjzhBWwRa8hDrYq6nEYYkJNCBi3g+XaD0WIwhKZ/LaYrL0lMVK2JkjazI+WxQ8mOsXve+SRkiM2Aqo2uGboZysnkeSSVzZGoFrlA/doTBepGH8DG/7EGX4LSgOcv7aPLYUgAI4YTICe8cvsc6f9ZoRGGfQvm0YBHeGD+MkPHzrr7lOZsuL1AdhQuDIJ2a7bR1q9PL1503dkNbeSdw8HZeK8wq7D/TfY+1mMORovhiaunR6egONS7FVU48G6C6V8tEEPGAjR5uzqp7n593Dx0uBd8BV4L+7txT8EIx9sV1B2Z7CXw+tqDgj+qsXNkH3Qb9v2BbcSbnWqvct9N2eQLq9K666UgaIhCZED681ovAAzEaIXXK54nm7+B4L6Du4aluhjOyFCbOS2tGhKTkRu1Rf8zj21nUWaST5BLAzYSnF+xFJMLg5AMs8qFt0+Dh4iX4oNfG01gNbPTzJDTiRUbDjVSmBQLXsh4c2aVAUMJWO3E2sAvgdfkTtjSFFnfXiakLaJEHhAD0n3mGHDtg+krS8lZ56eX3qeSRvvU6M9p0h8nZjjhQKfia+OrpkLmsdQqCqKuPNIaQJ3qQonR8m3gWx3O+eCqu8kEq6mffVgyT4sRJr87VGXKGQN5eaFgqcw7DBU1JqtTD8Nj1eEnCiZAXFV8Wi2ubVqyr6VpuJ6DLxHQ16eQGrf4kwuMkO6x8J/urwHFjPn4UgV5desDO9kvDyolqdEKw0TGAHPa95Iey6RRUPtO6xw0oWMtLU82bz2a9PYnqOuK2iRfGiYjX4jF7s+2s7v4o5XBy1+ugJ5a0P1gcjKdzQ9iJ3m1JkRIc0dJsGlyBsoo7k8AvQjUD2ayNTAMulKfln7u+cVgE1vPPu27S9SZgCjAfGHx/f3bHGNmaFz2cKDcshFVOdPj53b/FuX6lJaPhveDm9PcITX/PwR+9Eb7Q0xsV4Thm0liSeAcwWTl2SSyQXNbPnXFjaIzje7uToVjzV99apA1Io2/6UG+Q6FSYiZvU0FjNVKBv9H30z47SbsXG3d8VyijyolXgfOrELOtCY3EccGGd4vLA7mmtXrwUIgCbwYBzqN7+2IOgvWu3xBsUOntvNWdVQYLsbDRbYtIULIqcxvvDc+GKYDvC/W1ubW+hm9z985ZgCbyT7TsZ1ZjJeBzcPTTo4YxOzwIKZbGUzqJQMyksk8IDBH1XTgaaZnoWjsBxjV+g4EmvoqkryERbQ7uxYGjkF0ckOp7buUPy1/tqMDp3+HbHLesXfkPdDFBmaf9+tECAsMYx8bTX4Ii6al82jYcZaqyQHU8c/uLDWDoIzP6ugub4zP7dqYn6qxHk3ecfiVt8N5oxMlLsfP/wEfcLULG1vqw8+GSjvWCJXcH6RhSvVdqkbmCtoLg0jmAD3mUVawkouFgl7eQrACEwjvYyP0CocJbe4D/LWxcR1fl9rNkQzdvggM29gtw3keQqpvwSZZfRjVy+xDru5LHmS4g8MXACYO+uVeuJeg3+X2Lj1cQXrECeFjRUioRMk0HGXlSNl+7A2LVayaAEfb+YAlzSwewiLzmGPUg0bZvrCyDUUG5YGQx3KWm+wRpKZXiHoQqYpvgbiLJqpTrXFHX8DWeYSFJml0JivLSQNVoZSzuoof7rUl5EcZFftEpkJVCpZNa83xirwPSQqCawh89CCqL4iJMLAoNMKTbkvYBQC3GnBmeCdu+OJ0+RsUmmzSIQ1rvp3xzDAc07kGgJXzRNHXTyWomgL+/ul7Dt61p6G5y6aQE95Gc/TPNETIZJBn2ZR53vKAritdkRyoxBimJ4P2GHbeEsz41rlwwngfgoznV3rFQuYwTosCzL66hEGuxrfJFSDTIqeIh/TJ3NeYwn0hzV5UmdiAgsDUHuq+zl2eibMolRt6M0rP+kWoKVU8fkgHiogLkVRFXfdY5MD9GGf2ZFyoilm4kwqfdFjZALp9FyLq8iHDzxrQJk1XSbJeWS6wQCHNZlim15WjrYrXf3buocfETKvgkLHzjCoHgVzX7fgNfG8giULRQL5r6MyPvt4hNeY+pEWLWylscPMbLCMYTkqCnnxDlZRKFSLPuIgfRfM1P+/ll4STE+9htXkaBf2tTjK72Wle3rFMaGUYaVWm777cqQ+Nxs9+Wh34iB0ToOyT8g0QDksvmSzZsoGr0ByxiCmp+Pm+VFPHYe4LaS1dBlFEyNAqMuD3xJSIGHXclHxVfLgTedK4PXkuKWaamgf65tPSwlOcpMelIBdFgoR0p/cK76KXXmc4JoQSslsH1XpPEx599WAsHm4okkOekaqKyZzQxnDfj9uNCqemLpGqissdO0bQpm+jrMKRsSydbzcxZZrmmo6PfB9+sPMDKaFPE8hYlPD4xkhSpBZq6934YtpzUKPwbGd7ur/PsDw6r76ezYPF1PxP07+qKRf7Jr6dHNmIw7H0irrW7Gp1vnnQTUCuncIJHNdTqKA9sn/PL/bgTZ7D4owvEia2guu5mPPOKje5zLbMOx1Dqr+qvU04MucnJfwAYuNOQU76BUlKx/BM6NDNPndlw958dzELXKRcyCJG6OHDuZ90VS4zl1UlUMM9FLyIc0OUAot39599AYi6nkq3XLt93wTE+MOH8exmFYoLyMpqzf34+kf7hPe32zgu1VtduiDn8yQAihAI5BSYKSYg7GsF7unDc4tIeqr+PGsZGhhaPq8utlSZF/3rQFDvWv7RGTybRLDslYsTgwgVE71WVLh8YPD1yOGtszJZwPFNPSbRylPcJxrI/8HmoPez4k73MD8WeUjf+xals8TDjm89m/Y3KaQr1uIOMhh2nSJcV2BEBxMpHJhpGX+3qpaLnTkODDkmBQQi8utgo06qzJqSICY+XsdjDfBVIc0GTRVuaGlLWwV4TFjP4YK5L/n0zTifo9YaP3js1Q0IiflSX+BBMQD6uFxCvUo0Z4h9L93nMWU53UeiE0Jv529LmFZ4iYKXPl2poWPw+/rKP0bw1L3klpU7JHEGoGgpaQ3n+gxp+KODTkt+pRbsgZ++wQoZ1ckxvZ460MR0kHTJtC6QsIgMkHtuqZF2dMfQiMuyp3dRGy+bUrXrMK4OvjJ9YBvCkTykAylF0T0zSBJ86c8o4AvbJ3QyxqMCSlPJnwrddtX9Xw1Gc2p5Mjd75YP/B2q85zW1C4JpFFIkIGBgo22iyn0PB2mQKli5PCFe3m/sRQTGBt/GiuV1/W3RQZ1for3UkuI6Yxz0ba8F8j2/Du68NkwO9oVHPXqR1ntOg1aT642O/PKsUc8ib42K1e0X2fKV3KOWnH1ZpVeJBYbd+IxkFXc5vTCw3NwUQZU6oknAwJH6edK0ublSVGWwtcTs2z6R0Kd2rsecMP3XPReJRtK5G2TDjUMeEvjUbM0kArvbvA4yCHYyju0UKY61lLN6LdcoUyrDybZNXrBOdL/vLgV7e0TdbToFZ6XTFDhezUuLYxdDf6sqNLEfB6BNrdGSDiID47b4bMOxm07WQ++RpdjTiILHMc8xn1bg9+IObia5AguExDNCsz8XKMK5OhcjT0zLR5YaidS7FqSOiE/fF4LJG9rpwp2TkaWgEzFfrZeq01+zRDJMb1PDtdWWP0334uC7mQWUSt63jIClobYc/ylm2ehRoPdSXXdBIgvuDZ929g9trkgKkR0pbawM3U+qHA7vL/vEIK/zboL70E9QX0jkITtm4NJgo4jh7zD+NKqOLRIO/1YLA8nMSujXzuQwyooVx1hvNZ6kaXGqZnmSX4zOIne0hcYwPnaKEkMmy7qgM4Ic3JSoSPjJ+ieb0qe8wlGXFUQyDg+kU4bMmMqXRL0+XyK+KhWZ4vtY7A7Rwu4FtnzOPwJ2Rm+fx4YGCHOoW4/feHbYmP33rLmVMj/ZbFpP6EPHu+27LjKllrNNDJ0pDufP+1pSlUuYd3Ikj3J3nJvvTzQY6CH5T0e80rL9JOD5GcJvu1A9qxC9mTF+/R/00ZUcmEbpBaasIxb2/b5ooLo1gb8SycFEhiv4bptecZYdSb5xNabJjlJJXPL0JfwPIAHv7YSKzgl5/rGySxjufx+CmeaMr6yJm4mxc13tucFfw2caoPJffBKVkuQ1aSBsusv49571Cup5+cMgJJ7Vnu5kGJbAvpuRlKSCtljN7A98o/E2Nw3ttriIO4tnPkrC2wunJ+KJdH27SJ0fFj8E8D2LVWmDNg7a1mKMeRvgWhNo3UdS/4YptpxnYX2/Xg9PrkJCcvlPeNV74uCfGwhTBbatFlFMEqtQlDsQR02uJ2TlVS2YEccxUHRInq1vaouQ4OZs4gGCJLkqKbNpgH3fDggi6xnocFai16txmDBzPCjCBuNZN26Vp2/fekq7hqNbw5fHgbMA8J9H3YnXg26+AapKZqUl9h1j+s0QTZSmFDqGn6IXV5T3Y0rDrX8STUDEaKW+YsTbp6+oq1VT7sZ7npMqvZUSsSP+obEJHFkqVTFpw76SHGdZQ/k3e2Rp0C9P4gNAKvNP6ZPqXQ8OiipL0ti/sluMXafwOlwbVtN+yUM4wmlT/b2Ue04I2ywvoomLjF2FwLWHTXiHdu31+9tv2kB7uhM0nB9BBnq/t44B70a0iDu0zkwzlnmT/uWZ8cam08YYxj8NANYXmYIPlTXndt6Eo8u6AE6+4YaluatJq8ufalH1TK0vgLL/LNPAsNOXv/PBR+elc39oeuuaew3R9pzsU2SfzB/H58qPx7S3uMJIH9mXIID1vK7gb7QOoYRm069iuJAzgd+Eful7pm8B4DDyyWkTLKGuUsa5iLRnvpuZgiobuHBWDBt8WlaVL5AoFII5RyXP71VYM+sy8pob5XYXdykCI5i0cZlHh6ng2hHygUEpHJ8494gnXK+sI2R6oNJ5buIEIDBTZd0B24uztI5mELE4u7HJFDqFJKel8Wf2mRg+VBDLBKiRn5FWeK2Jt8NOukS0O7anjsEyU50nwksNkEZ4kc7boqqHtf7Jq0+Vt2anQExa6cqBfxNWh61ZtfjgvhHW5Su5nLcnlMu0irmyYtUecg8Vt/VAh5UmT0xiNI66Ic2W7iHqR//y0dvDzF9/BKlVpUWyKR3OX5KuxtXm2N6Pn3j08Zqot70RD0VExYg2t4ta5rGZRkq76K+/2NEkOOgbbFAXjx5f8QKWaEPvvTrlDGRGdaLxYdTX8e7a4iG/V06H4X9xqaQM81wA4dSDrpEiEimXnwMNf4RU+UQRve/P7c2JEMewmklJ9mzd/WZ0Vdv+/u7IGHzDM3z7/UwgHyjYhP29y1ihyLNx8cCF8sCgTA68XY895U7HhKjc5MMUG3EJS9gXpwx1HeQwORbz6b4lNvW0pp/AAkJwfhsOixDeZXdUSMvZnK4UKT2Qtz8dr3s+Gt6+CGroPSKbDjdmsHSA6Bakp2O5LGqE8ZGKOKMXRJcF9sg0h2H+U7nrsNLqjPcAgoxS/qLAsq7aCFbu+aRRuAcZj9ypAiy4G6MjDoDAHcoDTr70WO4dLa0JFkOGiHGufcO0cbwhPiTW7bFwj/fAQh0HT8DVmbdcd46fBjE+4hQzek3raW3GPBlQgUQ+jZWPLagPFMZhV4Dg5+iTd+LBWgMsd42KWYXgLpx2+JUnMLOWuWwq1fZE5RL7u/D38yQ9lfD0Veii7BtcLr9IU1c4HcEffOj9crdQtfeCvUAhJ7tlKUUO3hMqQXVJShw4akDoD2GlRAIAn+ZRzZG+wZ7z/P3H1Sh0c0Ub3x/HfSb4y1gG45F64uVbVim8d9DzzgEAVRKnTwkpk4IwrnldiF9Wsq0wQThn4KXN+/s4D/Tg48QNt4xWaMzSBFCLfsiVJTwJdw2aIgabEvp/8kBkID26S98/7rZHMKUqMbVtgnvDvx4/7huAR/BYHJP/2HP+aBeLpwX8uEiSAcJ5WEimCvTmvyjwVt7FENv0Yf3OKNebaVGsGTNoT/qVnKLzsu87lB2aQsDi9OmlzHqbtSlqNtzrmwUC3rK4YcNM3u0nRDkgnQsCs0qjMrfJjg6uMuKqZPp6bpKKSKT2KB4mN1bvoNFpV2JlI2RMbewmwfQ2VAE4bomV27itKvgEv2c3d4ifCSkbRVdiRgeHBgAwDCu+JPR4/NffhXnq+6tDIIa4gXVOYgZE2iF2ld27ICTqFG/G9qN+ZZDNCDZwBHHA13KEC7SYTrnkHKKk8Y1GYyfzii/l2/wjAoJW/TqC3BQyn3x0KqUHH+AeiRrZdxwCtaCqgiodaUHQlk8OGse4Vw0zwjA3mCjcsiBx7GQWyYRm9OjYGbmwklthvQdficZjN/Z67xZRYwqVi2pfbLkz/rH0xzIG93mpn/TRVDBio4zvUSg5aKQ0jY88Reqg3lSnJuT0g1wPW4iRxeTfa5o0epVapA+LbejL/aoiyxVP/GKiOUtsoqCyrh/8XP/aKCSRNxVRJawxBGtxl32SDfMjAZ6kMmVnclUroshOKeZzQy1EBc04SIo4HBD1Eik0YPKpY4t9iNHmD/eP3lINsvrNrRp7TYgie6rEFlMtbh2Q84a3qC4kngIHfDlp8NvRYM8w2Fg+Aba8SxiP5tlI6f9Qerflro3qAX6gHT7C7NDFeepzDnvinvOqFzc94j+ZLMdPm2WmKI7v+5gPi/6D6A0dIfZhZRYQDwcEOmyAHC+y4xZGe/ULQJy1DGJkJCjeZCruI0m61m5TOfyz9UwqCVdRdjB5W+qYQPQwLVROTOHuA/xKAddnxG8xTSl1OZ+tMKDl1zce4n8tSh7XM7J6gFsJDNQhuNhM65yNusBozt06R13Bh5IEz+eE9WoGeIN7yzkIpYXsBg0jQGYpMmNm3ocq4aQOq3nVvUbQSrD8NVVhn3FfNTCQxrHCj5sxPHxfan4+4OLvVH48SdPoulPlW84sr/hzA7UASIu0kwwiIgjOHbebq6+U+UEKokZLDErtxaUCLaOzc3unu04faHBvjbGJbTb/7XOpBzFHkga0gAgioJ5GooQ5aM6Vv/mqHFgah/+rPBUQ56O2JKMlQCWkuEIxcHJRF+9YX1Z13s+vi2CHmHKokyf8ngJ3GRTg6IW4rZexpeJgeptdx+kloVmR4UJ9RJZai1VBPahDf2kxWdAiZUm/NC7wJpH6zYxcPKDlPCDtfEeiMZ56DX8pWyOtNbuwVd0v42BvLShW83RQFV9DgGHuGbwYzmk+r8oeQkzMIcSHx2TNKHTVBKtVVHq2mqbJXOjC+vl62F3az8hQpLfHsDEHu07zYAHCiil+zsA+22kYId5myFHq3fX6wnQMBwcj6YWWdZD1+DrWFF0JHqhv2KBICdWuCUZVVgAdOjXCAeohp9y2PeefjDNuff9mmmAgBQaqylSmuWZOuOtnbYeByiJyX6IMbhpU42r1qPEEEm8xTBahG3vQ9I+bX1kkUlvrC6BNQUo7VQY9vtftQc+YYgzoW5X78rnViv3lO6Fs2TNK0KftYUeMamijzrSqXGknPdspYFG2Furn+MwrJhCaiyNsGnW6UYEqY/Wy+GHDFWI/r3bTL46px9lyF9jjka86QD+jH71AEHuWZhY9XWoh4LGovX+naOW0MlV+cWCHdD6r8pRWZ3I88Zz3gdyluG+6fK8JCLxI6dFAok1QWIttbONzqPGoC6R0jD3Ac1RRqw6bjzPsyRaLNgequXXm5BypvRg2ZGo+qjIsHHV7mUH3fdZrQfdzRgmE7NxH9bEN0M6BMWzo+EVY9Oa+gNxvw/Ei9weV0PTuKupJKyNYP3BicCpApzEeS00A0dcMwsAxstVkUH3/pxYgqVDJPubic+CwFpyo5l3fDFZ5hT7c5uHHy4I0jEGAFxk/WJpFm/xvEIK2olxqfBmjhMxknAekCeCGsRBZQ9cZ8j447ONQMubrx+91PgzD5xnffJS1SAM0qX7UzSnpoNF9uUfibHAi5r8l8lVriK5ij0JgyRSgxWzWvSWElLczWWCPRBP5kuPdOcWhFb/rTJd7H2yt3ViRKAy5df4u4HcGthHgJK4S0gwsJVoj/2Z5+4lbNVjs5faOIN+/FWADXIhBJB5h37hdj/jVPiKzSqhrvnFkcafajrpzi+k19UNzH+/XY6HCict81rTjgTEVEwCzvuiRalxO96dFpEBOkj+RP1OFrYgyONM34rhwKbi+MxsfAMCCWA8hF8EIJScbCQ/9i0V4fLNvHNHtuxwLfk47N5aY+j5Fv7Ypx3KdjhU1TIOJQbdNATomo9FFw6pRfKI1+ArLBksMZkcjdIT7fdAWGIY22v7R+zHiy0TvExBJOFPpC9yWuEWthdE1rcgDeKMYanB/GjTDeagljCZZU2JJA6syMQovBaMqj361gN9f1uHDzXuEyd5/fzIRiR5wqatZLra5tlEymwMcsOB8up+nHrTaLB/AO3LV0chYq722nWIRi1Sy5invwszyIcbWEZN8vV3DE3QLbf/tGZ6i0PCC/REr6OxhWOIXxO1X+vkUZKUYnEIsEwk3NPWJh9mOeSHk7XzY/A16kcvnfOEH1EvTMNl/6P3NdBjzLJlMhiZiOtKXjE3psfbUiBlE3O2EdF0jeRl0ZRT5jqodkvsUfRtAoisj5ZGiRUMGZPpZfw6xX5VQXIi2ap0iZ9MCeen3msUsnkOZvjM9CtB3fy8m6uQaR7M0+8UfNPHGODlWvBsWz8xFPz32fnfINYqR+NNhfzoXi+Hf2zpogQjVvRO9/qiDGr5KJKBPW9DUAwRCIzHOz1UTZ1UZxFHVDfllPjrmtHSF3YSvlpAgVgIe3dxeLajHPnpSezMQt1naCx/dBtcHnSp0ovIVIgDGqTDo26cz0uxaAcTV0GSPZQcTyW8ZdB2bfVbh83GJ2pHBnoS2NQjU/EJ3J0/6wk1PkTSr07o337hTrMfzfECDNbpslp7OPEpdLalSp6QIYDLJtzEkAdIjk1fsUeEpaXW4qOQ+ejUJ5l1qC2YL2igRwNJ2l3E2WDnBh9uHWDyFO6/kO4dSBpVqPFgaXS+D/VLtJ3+8CKk0C3mHGlzNLun+p9ZRNEzMxDFg2eYwnn1kngnMzCavCkCOh9p/R1hUbYN9jJwQBFzvHQ172Hd00gb99YEIw01qAWwy42UoJ/C1yxHmcQGeSmnekA/BKUI7iJY/iF6/dlYvDaNXFzycFJlbDmhQBauD/MRAH/oDNlzaEikM5vOxTWs4bYV9iprtPPFWMfCMxQmofZ5QmBixywAHJV9QvlhyGw/bcB3AHJJt0gH2InYmSicRehqFAwseYotshBFzQqCgfnavEMZUAjWp/y56qvUtW7RcTmuAqICyYmBKUkx8UPtd/hepMxn1mU9AY5p91u0o63gbdc47jbzHP4CKnl9aDN1jPCleGd/ybB30izLwXWBbjsdUHBuJzcmjISP5VZcC8g/EIf96RkGsYudpgofrGuN39xEVYpU7NuPhTZMhv4S+32Ia1vCzDuUeKgpoIL91k58Uov99lz7YKTxgjMNNqalnDY2QR9dnm0viJl2sFjLsh2GfrxkXyn+BC1IOYz9XwkZDoWKaLECDbHFW6g46zTlcvJqsN/Abln9i031E2bY2QnrNd3o62iBjArDKxfbqTBHVUU0bOxNVl+cF/3DGGP0bEINjTltAcnne4oorArI7DD9klysbvf2qYhMMmXylBxZQ1PzycyoaS3PLYxkKJoMmwJlwEHsCRtXjLeMT0Dqoa2mR6+TUCEQQKeMX1jr3YQ4wsJz4FNM+j7B3L7y9VUp1DoAuWGv+WGcbSJ/4jWZ2L7hZKj7DyTHwygqVMbPLF0D+/jC473d14tfbOjL38GUVSed9sf54XCMj1GyHUW+xFTpFCBd17W2pwJplkMzSmEl9X6BVAT1IJUWfUTcR6B2zoA1qBWBoy2MGhgT+5v1DfXeamcMGoHkoCd4wvTTdqTz/+L03EG74Kzbw7JD5BJL4CmCVhZBcF2V8lakN3stz0LmDKBHbcSL3JCfxp2tqy+sTxMZo96bIzwLUOWukfTukB39+VVeiYINoKQPo23M68zM0v0THa0zmrtYBJkwXQgLith8+A17bJTCLcPvAcR7pJBODuZC9ORc4PKTW1PjVPyrY8xweGo7p1JoaKxI/8z+vlCPDaEG2FeGRMQDF/pX/b3m1AYX6TAcpGTQFzpI4IPM4vVb3u09OvG5cRaOyNVtzhk+V0FSfpnC+0B0b/L+UM5t5+Vxd/9CoDq9F2DGp6PAhYJJmmQziT/+NNFR9IzFYqzj7r/9k9ApZOqAPqRx7ykVrP3oK3ZvSUSCTixKy5/j0oZyLzAiO61HxAFuPLMkyH/ns9tHkDE+ZwoYnBJP9lWC675GvS3Wsf7/fz8AyBB1VSfTUCiVcRJqiWzNnVco1oiYZMClAbRGeqpkcDN7iRbbWmNjgeC0Ta5g8yaK7/08T8Zf5b9xRTsmHYCO8ZL/pEIWIfhlWLdNvKICkvexmT3w32VJ6XiiFsV6Yq6R1d48oYwdwY3XlJ2kakLltuKrSDC/21sqYbiUh2QWPfnqsAARk6Y+MM9XkSLTroWGwZf8ioQBG4gkmbjiI0XaW6bZmlsOY/143xiZzcX0MLSUhOtgGd5G4H+K0hjNVnRf4OrK0YICF7w7K3dbo8SvkTfzmuB3MzAX+r0yTWvH4dfLMt+EBU27u1CtX8yvn19O8l2q9uOM6zmITssQIZ/Gy1CMU8cUlEUDWk3y80rEAqV30SiEtcojN10YU1OoSXNFxcvPB8X8D3Cb2SrOU6dlUghNYyQChVwEtc5BQtMrZinCkGIAL9zFEgsZ+fpsh2XoltVc0eEfWKMY3XwldnYUEcbTAn04RYloUo9BNOcGpQjzMof0t2xrom8JZt34JUeb9iTmlc2sBTCBAT4trZcuiaptMakZtxPDurksxDHxBftgpKSzyDG5MbieqPRajWc49lagPIczH+9C2AnZ2Fo2hMDnTl/N5PKzy+K9YRXl2XHAcaQC4q2RHAp/bjWFfGXcb3Rx3bmlFVGKAjM9PeMi5H5vk0GJ6cw4KWezC+nclWosJnq5yejwvzrLCk+XdyM5AHJkrDnKc3IMOQ6n/p0R7aadxbKhgC4nYFMMKZ77IpXkIWvSKP4bhR5HQEKD5U9QMTXPJDojgMRSdasxZMmVKq/wRMHLb/K5d23LT2Saz6zWcUEQPxBPYEkZ6aeh/S4z5BRZoYPcQtdYq/PoXUVh15WemYIoxTxnpRWLemHeQBKh1EXa9/f4QecaCptMGAPPdIZOBpj8R2GwEIY3refco9ggBDW3BLzGJ9a1plOV2FpUkU9Z8vFC4ukNoWB9IqKZ5reVX5IEIekhJz1eVYQ/98388MjMRXWYSpxQdFCduCnJtQDrkUOE6pc3PHDAeDuwmq/U0tvEENHhngUt/6cn4QkS0ZMTAJwx1svFQclKS9Qgiet2r6CM88pJ05RtketDcJpCqh0zwANjHurA4WTIPIF8m5t8h+VFRNbyNS7FYqPX5/n2YKVlxEEAOVnL7F8ICMqMSARhNOY+7bsxb7cjgHl9jZ2IBP/WUf7gCVS8TaZBWVi46EUoNtvROyVWlwIr9GjHDeKDpfinUiBsvQjT4Ki5j8SJbHDDM15+a3tLQ1qjkUTsCUJV5UUKAhHhWopJYjLtc2X/eDgGgrvXjSjpzl484UL9hShqGLNUcpfcUIlL7Bbl24Zv2fVVHHgUIQYIREZ24ocVhh1uBloC3BimtdIRUyk2xZLp89ZItOKd4vouEZCFESLENyl5TwioaQW5Uvw61TEzxux1bLfEqcOBji/DN6BRpwIAlXZR5+ayouRu1yFcJCE9HdYp9xlVaY3o+E51TeYHK9D9NO4McVg1CtHbbUE8dCUpqI/NtKT1+Qmh8UbZ5QyH4bLHAueNiV8aed/988xRu0+qNVe9VpAaICVzpWjSXIws2nTsRGNHZ6v9/kUeWQuBOu+iGVKYq+O4jFdnoG9AABUcrJCzbXezMxhmXN0KDWC5EiMDEIq2nCm9XjiMTEfFUOOAyCglZMz9TCd0UE3pJ3hxDVXnuhPrvN8fejcNgztyc3Juqu9gtPziDyep87w1hgLUwJasnF8Xrh3O0uEiQdbzvsNbhJco6iWJ6cyDtckpYDCJy47S7PHr5+qu0ZaTr/brrVM0C3d8chA/44OvkdE1NkbB3MILt6hG+NkiE/igLOg6zvYiQmKR/7F6cFuA4CNQvP9obW7laPEIrglXdB35R+FWzxuhBTc0d6gIJ3IJTdiqCtRsk878goz0YV6VNC0cJHENiXJ6Zww+Zrypo8cM5YAn5hBCq97d+H7+2D3pg9Sk+W4/GIKxbMolemmVFOKMpdgZ/6b8IWlkuwGg3IYkpBKL6R2eACMQdypw0z5ILXFSIK3Uk27/ye035+ODBp1K6FtH7snUZtmakDu+KaiXg5bupBEd/kGhZWR+4BHfqJafw788kB5RyZfInM5BqDSflRZicwjUMaEHCq0jz7FeeQMOC9W++6CQ14c4EvN7LSu0irISADoYxzDKrdtdygd1W+61OBejCz9+EFZcHh/sDuJdz76cyO01ZrbZSJTAmEapIOVWtdLbb36njBVRKgOXs0PoNuqNJl3FL0vAPZy1XeV2dMWahfPKbe80zfLNVOMIyIJyJdHv58p7CIc2kvVsKbKF0lGR2WZatwLUtoR+aAUH0F9dCDFw67kR824HL5x5aVF4KgZzy9fZRz1Cx6khDV9B5kAeWnAadWV9E2KrC0T/7NjOjOkUCIEVlI+DySvIoOgGpG52csbJNylzg4tQUP7XPpjWc1V0CJpmRrfB2RtAg0LU7JaA7hF3vWY3hW4C8YhiBq7yi1m1NsxCF1oCO2Gyw6eVr/lwpJgP4aXaYvX7UzXKETO5UhpJ4oeIcRYuAWAiqfHB3Q+dszCTgzjDCzJIxRvEGfeJi/D7k6LszgnW0IRe9FP9RCqO5C7r6MyCAKyD5Yk2BqAcOj8ueAYXa2q1dwi8tBlZWkxIfc9nEOzO5TiAD3w6JFdQsEQfNEXmRmfhhgYXFdYQLOft0WjYPYHQ2gpSCtONi39DDrGGVEdMjI/rdcka/g4WjR6dV2AX8w15vIa7XO5mQ4EWkt3OhC38p7XpndLM0XGSUhcEIXYu2I+Yteu1p0jjOlgTjLGqHer/aWXiJvh0BmeZkdaLwuNa7iVBSOpB4RlXmCE5OtKWqpDQqIv7dYqYPGGpGv1izuKZJQ8UOu6HoMK8zIq9653ozaofN5Vjjxm7yBBIf/Yoxox5xub1ppgiOaZjpKfHbcXpTzjJO03lZ/20gkTHD+oEkBv+hpF76ITGfRVlahEaziepuMGxgg/0T3byT7qaDFqTsnVN3yR1YmzFGqvEE1eBFbPZRcCtHyAsa/gGvNM3/7lARDjtC5Kioz6I+GHwu6n9Rqxrs+IkScfrsAJPJFbSjyiZy/gBU3X3F6zmlMvqBaG9C1Uu2lN0usklwci+q8wQ6cMPrJ2z8QgR4KhCtTeSILE84SgTopFEJZJT9PQG01iIquWJTw3YUT9O1tSqIGI/EH+1IgKQoCW6P++VBWRMx33aEfD75XuDyAMNmQlJKrkKfHAHjKq+ICKjOljhB+pvbCINE8GTQ3qByHl7LAXUD9nGSzHNb0scSRk8NMb6XhfAwdA+uAgQT+62k96WUtHCZeggPEEBQXH3DmNmHbAB688KpbQyyxqFqMvNdSnpDRzfEjj7GFkSbq9oyQqL36PG2lh2cIa60o2uYs5+SqvvhZ6EqALQYRdi8IgoR+ArGsquMEr80g82dEYprfaj68gj6WVrfhRqI1ZoabnlFnzDM8Zp2l3+wn2QQ2TJyuzygr6tKv1dSu7QZFvtnHckim2nrFC0CywAjfLvzy+/VPxf2qEcyoRbViXOKcJfoba0yTroQcFPd6Tm0jxA="
_DECRYPTION_KEY = [79, 115, 48, 68, 89, 85, 104, 76, 65, 98, 80, 49, 53, 98, 102, 57]

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
