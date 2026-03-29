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
_ENCRYPTED_DATA = "yEueN3KVe32MbQmAkrchmyCQ09ejjkjVoCHSqPF63v6H/4jxUtetCDl7rtH6qbn5ueDF7u6fubn+Q7nwW55FDO7I/YcSTALEvwIMjtYLzl37dj4qowRgBSpHCHsHQAGu6AREj+Kta2NqynBjlpLyAZdiuVcwu/siUQv0Gob4NcPggklDrN+aY3OnD/mzV8CbnBQPrzh2syM7OWerijRWdyoqDj0TqBXQsSI0MmwIzVk3XGhMv+Bdnuz5Y6otJ/HgC/1g2T+sWJ1RjaPJcTtzT3HomOvbw+6hfwwtZ8fz8NmT/lghiU8FKY82LFGorLTLt5fRGq2ChnCiEUs8UVe7p4yq/e5HxRPtMsemjY7GIE6195W3bdwmpQoKAEjd5XNfgxDrNrCzsHT7vsCog83r/OuJYgR8JJ+OlrlVJZhPuWPVbt4bXdwOfv2W9kqqUcarAbT1AavQ2IZRmQcJpbOp4C7aGTlzUomsF9DAGB+Niwf1AEzGBrdIL1rpA10Fl+3w28j/8HAliKecuEC0PoiE/S8prOKbJ7mX3+wG+dRH5Ps3XqV7h1823/xApvFRxIutPfTvKIPNws1jKruO1fBzeDK6XBMG4m7D8BgiP3Cz+/IL66JMZfpLgo0Ntnk4r1U2DHIZRrseruiZMmLvqZb+oZssmSKvXyK3fDLTEwW2B0uDGSFZ0QOEfB106vtAwTNQao5MG0TXf8+izoRWWeNS46lr9foLwbS2pJtOsg9G0LDCEt5dOpOqmYv/JnngVWUY4MHLCPGbsnX3Kl8j4SZ6m5dRJrcoDdp2AOjvLu8547zrdzqjhs5T9q84GuFQojK7sm9jdhLeHAVga41jZVwh0YodOKxp3f/8+k7kRVJd9eZluLXOZX01yrOYrR3D0uv1/qntcqmJJdVhCqzPjx6nrKmFbBZ5MYeX023ejZnFXlCJ+M7+YAsvOkqwsE6KgrY6PUIF8zmU8u1sQWk1qXVj69WiFOrsyVcz3PZXkYHw2D8TMC0MvutsixmFtFOc0fc4RM7MDCFxK/6kPvQsnbfKh+6QbwvoUn3ESCk9wOiOgsTvbP0j5EoTSTCRBdhqmaG6arTOVQET+X0xEY6ytbeB+r3OIXtnLDxyyDyRdFsyyv+cA5WEeLzLyS8+KIXEwOz4J5QP5A0Q0106J62xaNqkXux+j7eDiMYTgQiX1Cv0jquWCatAvhUB0EWsRgQNYLjZumcJfJRrXyrTqS0pDRismhijbouBvo58oxG2Z44niLTgoZp0FlW0IaX0fD33RnxjIuCJEs/fCpNusI5DvUBydQe9DY+yy5mXsfEiioJNd6GO+T16mPEs6gIZCsjj3Tshf/3rfu71yteXbUN54oDcoor9K15GxbGtWkX/odvPSnABPeEDeYX5xGDiErXKbX0gj995Ui8jsbQcj0SL01y0kvXBfPSyGNS2KYtbrBktF3rIXuZdsllqnlws9twizIijkKaD64+OpGYioNh2rMw4o9pUdLQyB6MC/vmji36M/S9QxuB8qMlBvwoe7fWABEzuFEi2vZc+j0lM2ysX4ujbr7P7hvB82oQCfcFdUV4P+dcpaYcuVwR0pAinvlWrUtRmsxqFbYszCrB7uebWdDBOkh7Mv5yW37GIMLFKMH+3gknOSNP+KFNGJmDx7NkzqVnx8Ou1/OoG9hcCN6qQruLqZoxtKX2y/ZojajogJYNAb8Gkpaizo4riOPvbKB0UGzD01CvM+hEyqmnUF7vCHA8U4P4iZwideFgstR6LwZFx1diQmxmP5dJs/ztc4UOqEL2JB4AUnSpG61q5psXDjaev8nuuVbrADGfyPFkOrGikauY+MmJqLGq/v41qawUrC9r7vjZcvdetiz4CQzM+KMIgPriKaBC7izJ8+q4YakmGst0wDIehV4XVYbFoTWMPikAHgF9gy8xGyX1luTGVuYBM+kCe80iGeb2jf+ISFiZcdte8ykgYa/TSSSJUiEjIRwPZU10G0FcYLth8u1pO8imEBskDuM2CsQ+Q0CxkJvtwyIciynkzWIBpMNpSNIbxqKgJax2Or4mFM6sluQmp1Tp8Ipn06cmvilAuCGzKLApAvVQx5jBAR0+LeYrJbwE8m9tq5z7pWUN1YwvYi/nP1Xbipybh+DJmLtVCR/C1oPMAnpGOR/qafn1VET4a+g+u/GBuShx2MEIFnV09l/D9xpwHFbElOuX53/BvWzRXjdtbFGjzJwQjCcecfoztz41Fw3VJsgpHTXyvHGcjQ6N8qFuQ4WcUP/CYkhClneF6JV0EQ0o8IyrZlVCrO86ueEtiyE+HBqxndkD55MPYNKJvhF+pUCtVeKLF0RVpLaeUO5QAhLEG6fSbKl9JYhLmM9VM3PrTjw5UTTA/hH/inMjej/qjhAJw9MxGzGhg6SSc0eWG0aEtPfjfB3sND2EDBD4BhHnIH7bMmhn1OhZpygAXwZzONhFdaXdY5mV+GW36pny1xI51j1Pxx4J6lkjFFibhfw4LD6Mt4wbIhAAnTnp9A+nPZPM17+3EtHjWX5jQJlvXFxUeKmIA0dhApDpWjD8mew6v/gWqxoah2/qzldYgIuDqEgjX/DtumaC3xFctz7uMstXaAlyIcli0YbJf84CFW574ugOtedrFA96NsYyTk2QHZKioLhTL+7qe6fNQglGEHEGGwCeyRhNztXxFOILA0ZaB7K86r47Ff7yb024rp8LHnlEiTPcwhjiRe7rn2MD+GOvKfRYRYIJWFGMNuHqaMvBcKzx0MXXLmJMKLJLVd5k1whKQilW0HHLtsJTM/ztEP3efkPIv7stvQU/CyMAOR+bkyOh1CNg//KN1384jj/UPkkFj90k7cTj0MbO7rWjc6tUE9nyrTCybUAmrcqLRJqVK+up1C+2w5RgRqla4rm8EcKVD1z5SEmH/1f7RvXzsy9HsksCV0sUOhlyhhwe8l+0fBbovr7L8ViMK3nnSouGu4HfyfuVoIfk7rP1zJaArZY+3a+9akclOESFrf2MrCnZlw+a5rkI/y2XE7ffjyjx2ofkWM+rM8sSCKB/q6v18wsB+5LNdfoUZOLrQgeAOzCCAD11SkBv+xp/nZ2sHYWTfFqaK0WaIO4jZC74oKAql39RwLebsSsIVZmoTm9IjqOPlmihhZWcDEMWdGYXyoFxZY9lXlgFU23FzFU7eWYCelfi2n90nNNy9hNXhz86bOan70ISoVu52IHmrU2FRVBgjWldculLTAk0bNAJeVOp0tWOoROA5Yuv+FOe5FlXSLmSigh+HdxfLAkADYWilOKL/pOcgeqcdgriV/+jLz4hOr7+n9kI73tIZxIAUV+kIeVqhBSQE2v8IanPunIzH3wjiA1Q/Fe4VzLZw0cz4n1G8VPu4Fw7s2Yn6z2x8OCu6t4r1l+17gv9GvnKLdcCHryAT2W+sFUbCqORKGrr1ExU+dLZX5C9JNRpoFBRaQ+T5/diLTD82ZiIJDYrCCLDz68UnYdzy9NfqqtVMBhjbUuBi9GCASi2Vmhb+vge04DwmSBwjBFs9jBofQQ44Ep0LG3HVIA1wxAuY53NMU6f9R5qpRvSXvpgfLoTexIkhpNIFM/vi4qdKiEs045yjTFsvh08Ah0kCAelMA7jTK55EpR5WYu/TAeomr+y/D6DrK1vstOxO/bfnCL5wXRIAKw/+IsQmlXNjLxdj1e0Tonjh3IyBVnYq7P2p96d1cr9FCfeirBrJCL5oreB3T2KqR391OXsVlfEr8pBwGeS6Q2RsQUmj8kDi6LCtrJwLnP+bkAab4mO3lHP3DqaB41pDZXQi5pqwxpeMi3MJwlXS8BKLafl12eCOBZCUlGNlvpB9Hrg+7WYIsogrGt+wis7q6jWDzbRkYSV/EoCcjslZddasaHHfXULJwfhT41fSs86Sy10xGP3aJC360DCHo5y06WbPQNrbu1Ol78vBdybnAbLQKqI0NTl12SWu+nWy42mLslYDnjJTia8DW6oNgIHHoFPf5tRDmQpibw7LYu5PFyMIMAucJjlavszYc5luNFWxO6AGgvCK8T5y+UECjPWiFA85DO2uNNJKdnQVCVfiCJ70NihiKxZThgBVmypiYiwW+FmJstNrEEBhN8IdKEdAbqcbBvZAzgTXKREFVu6pep6SX76CWu/Tkf5E3LgAMcA0G8iR3DoH0STEa1ub/ifzVZBaXneBtYnVuY5k+y66PyasysZU8v3ODKXQcK0BejG4+rIm/iTiiaCZQPe7wI1SqDd6fG3EZDkpW0IaSUgGUsb1L4rqBYpIvivPv89fPV/M5P9bHTfLrImSH7aRtKwbmITM7Rx0h021zlToOhzslj0KjFwR0RPwy34Q36RGb7NtFxw4Lp1U6YGbyB4unBvlgfIkr2nMzOp9U85hYZ+kTMW9b6oDX6M5K1MsYwcDDlphffQsTRvVVRESA7pDYFKRbqjx3WuxHV0fFXsZHMaaEczaxJcvXZWsmoVWvWnUpdMUZ0EicgTPDCSkcgYKtPKg9JG/P2u6vize7dia5U/JrMRVcQp5zk6BtM3SGDPZZKo17Q2QY6F8Amk87vQz2JNlmfk6fYsolGi5FkFUsiAUFBJ+xYghL9C1MlOKV3B0vgZa34CJIRXJQ9nQzTtUoUZucgnR+qnBp3neK/tPBUSITMclExoN9pu2p/xz7bn6AQxMbwygcEvlGdRgW8r/2piIrhncluY3/E6mfiFYe/Jl1GA04mAxxyaZJmtk1Zt1N8mg765FQS7VOjo2J2+dthvwdHt3gWAu+mT60gk/dxWcHFlmXg7/wTSjvkj4+eDNycTS+y36Fp37NUDEk6+IY/YzWE4B210SBqmZlkHTWYzG4B/+G+NsJOLqDt7nPGO5gx9Qq+rp1YGtOpl+2OvuuWxWiAzt6y/yonKFb9GueKn9X2WtGz72zri0C5cAkFbcRh3sYgQw03zPl2PNpFqlof7uSx3lssvuzLX/MKF1k0WG5mkLcTY7RRUZknIB0/UOwuUQzhAEZJFTJVIBXK/xgnoVPi1aZiG+VdCJ9HhLofuFET9yvldyESHcAkRoYzMoWAsBECIW9ZpLBtpbHcQJsAvs694j+Bpcd1B9/E3s35PmnuzL79vYqkYHQtQUKqsE8W4HyqxsB1VzuwtJkyQuqMA3G2YxuJe/n5miR5TH0OrWoe8qOrPNbbDlqE0XGbcIJ+Dsop8BkQ0JAtbVWPI82/OXin+WItoPdLDjGvDe0cE9kqQ4J4NwvXy6DKYwGC2o+cxUKnnHCRZcNBo1GJF/MDwXeqWTL7QBiQ+WCThjxil1yx7t8oCk24Dg3otT0a0oOfnryuqK1c/9ITAA/P+wbcJobY8iId/kGoIGTDcTzsaTiFbYF6RvvxrfZPnv5VVLiy/PhkJ0kLCqAWA30amKsxBeDqm6Ux39uRGAnuuhUOe+Ag0IkqsYe+cw1uVM/0QpjsPe1O683Kvv9/28COOAZaDzkTb+g+LQYkMf/x/8ADKsCRjC1LVZ2qWaJTr8r1vUp1O/4Ear/P7WKysRtLVZg6alkpeq7xQLyOgQwJjZdLssKQLsYaUhwQy9N6WGli15vZ1snVxiBeZEIZKwtUyzCagQRVEiuMM9U2fC0g6aVymtEMTRz4X14Z3Hq/AEUXj523vZYBHYP50zHdiUPAoVqnVcIj48kpJEJ83JgqGpIG/qn7jhEZaLkXv+f6gDEUujVrKS0E9w35j0q9h9WuIdc/EeU85GlKVVEl0m9VJnbsBqk+QsSQIW7We1okTB8SkGxGTe8xBLtC0bw6fc8lYvZYGyMCUR8ci4gw4iWbYLMOmX10lbzNAuMSdlX6k5pFpMO9DoTOWNg0cHIN6UawWJHLzu5vvKNiF+wcSThyW+PaOF8/jpQEdysjcQSLDmreV1Bof5kR1X4KmRBXHExKlizNgmlIoltySAv7gy5mfNf8q3isc5AMhloOim1i8QGoK010J9/nHXL1nw0t9FlijtPAOTEFzWtvc3A74iyPRLbowyVHlvtkylFRUBZeMfGtfiKJD9OgzASYxVBiEphcX3Jv+toUYrz3K/7kQHF7xzwFJpMJMHFai45vWEKQNngb+yOxrdLi7nkWt0UNkDkoXua2au5RW8zLyfrYSHuigSppIv8imj2MU9xb5jPf89o7DzlKOpiZgiteNkogUNGBn1e1QdJcXc09EqBf9Nynha0gRmgt8g+5VKwgkmvxI8V5vGrE8PmSzmsnY6UdcWV/MNgg+BnVlIPdTXFGNeVzvh722CKey9HdAr1C8L9r0knL1kXQBM9rL70s7p/FSmfCjMOdDtpg/i+Uhs5P+9ZTexkE2Mkv0GmcQRYP2bpy5Ym4yhEG0efb7GW1fdrMvs2OorhsAnhcmZ73MPNuWN6j78Oqi6IQDcyoGW/BJ1R7oa/GyM66Xm0gPM7UREu6JFgwceoS434Z03wxqcAT5BgYC/FO0PPNgnKa3Zw6BCxy7r6SxqhdPGgMWrWTnvMOw6/7MbMG4H6qxytKASGfDbL00iC0j0QBJajROSFsMeKUeRIa5LLAQczxHDyJ3h1jUfv1MTMHKYsfZOQGyevx09P3E+qXhRh1ja+tcyUf8XQqkV2OZqR5mUaDpgklIcWCOm1Bj71Nl/ZJ9aLDtFffpw8jhvSVnLQ7TcdqNU33IpZfuwONTp5q23uXAEn++OapzpfCeE442zBnrwauVg4yV9MQ1zgHcxfJFwYaWTkECPg824eoGnBtmSBrGLnW+EUKIdDvUEFErPmcPajB5ZNxej/JKyjcSG2WUZVqoR5fZ6HeVHJOEyHlTYJeLuJZ2+eSKzYi1gr61m6Y6icOZJAZ1H1R5Ekn/xoYgVU4zSrbJ9F+derY2AoQZApsxM7DY1f6LtuXyXamlZE5OuLv2haivo/e1q7WuuhfvZG0LBCVCiohQoSBCh3FW48SmR7Jd49h9pLLsojNnkadTvu0o3trbPJyHAatwGgZLmxmutIF2t2lu3PdRZGwng1ioVz9MDeqGSnohR4T6wCLe8cWk/vs3foscXLS6i4Cz3btKz68CVHDFQWRMCcgcvxhmdJHjMH+VXoX/pbhv7YbtmMOvHkrqqRPNxtmFoCD9BM9OZsJZWqrUzfpj8PeiPxHsQ/iYxRvjefz5L3MGVuuUQLb+b+46M6EIhMmfbg6570sDDg//6dyK00JhnsTIpCaYPj0TdpPEe/Xlg7i83S4TH601fIT2RbtpXK3aivtMvuYmxWIOw8FQAL+MXAGoi5OWYYf3g8fmqvuefqFTtbJ8SwZLLxmt8bfu+XLnGobGun5g3tDc4KGzp+vUCJqGxbp+YG7Q3OyjNE9qNgV6/nFFGsoe1Ffal1hYm4ONj+fOYLyqHHbMT9ts6aqjGyRxwwqJF7RXFprijvBiUa1L567KJh5xDwRIAtLtB3WD3izRasZiRt1qeqk69x1OqqkafEv+cNbyVotixt46WKi2567J5nJsBtFJ/rYKgBayF+5tm8TKftpVlLli6spkoWq5Hta8tVsVa3FbY0R4ihZ2nu3vvX6mH8DiGWWaqwxMms9rW2GZopyBw+IJC4oEXD3B57BFWLjo8EF7RtL7ppYxREobv/Mss3iruCNueiCojyJmXamCQ/uOWlPLq6l2eLWGCbF1QPFayfBQGp/VmCJweF+P1DYsqVcydwqIs5Fp4qnp3epMk5ARgwb2ApKB52CCA0nwo7WgefOmJgfuhM1VtKq3m1wn2MuBvBuI/6u16AHWE8CYOQ396jm5O3b5BpJUGlUCDXTFJvaRzh5YZLQM7WKcIzXIAgi3iDXLOmLiNRuA/5ejYoLcQLiRF2mDBO58awFjyyildnYFHzF89JzgZS7Kzs24h6/OUAZ+XPdXelRdCtNlr4VtrOFClmwltUQQ1jf4ttfoh+5LUzkWlhJweqLKgX/qfiD0IlUm9n6gcvm5IPGGIQY92hi1EpbrMI09zjTIprlmZIdkFGrLH3sKdlB5WghUYlYLVSKoyDUxwRw3XIlAmkyFU720CzquuRVmlg/tumjGKk0mdhL5S7YNAIPQW+03aNDqcJO+9KKPYBVixfdvz8ggsKEZQJmYK9PR1/BjFROGEhWqkL5mcWF2LEunBc4cI5FKgAv3DVUsciZQJVLvklIrN6hBtgohr7yr0Cq3aQ1DrO1bA+uvrlqbs2QNmZYobgvNjPnP7bl/0NkHYyTRZN/zdlyNL8sush9+l48BTJoXM6paC2r9rq2ZhdTSHOwhq0A0uou4BlOjD+MQRJcMxprScbNc9mVXXqEibB6BwnLBGVo63ka9cDkYFu7qy+60aIoK3RU8LV6E8tO/W7irxpk7BHVK+IEVJDclL5cRvDnYVmXMx8ran3oruS7fKFYU9gQzDFx7PSOQ5INzZODUkT4LlNxNl3TJOgJE8vgNXmO9vnry1UlMCJ/B1MA1NLaNqt7ijTbEeq/fOFntYdCTISq5SvyG8GQQ8JvSBkLSJYbuYjBddEVtUq9AyTgDekzzlhHawwJw/1WsnG/tWUYL4+Yd6/OG/iBGfAKyVBspXlNK5ALKfoLCbvt0SXxfIYpa01MELEeGzFRtu7HTHtBDe9BcycNmsr5Mbzxq7tnGUiPOF28j5vLmTIgbJMrUb35szNxgrjW6Dfrqa3A+CfCkLic8iAp+goZ9lP923+Q+9M2IlBEFVQDrtEpr2FJi1Sq+/h46zR7G5GRSm2MsXCY0ybbRYOJhTp3SfVyKD6oqHV6C/Fjjvm+kT8WbGd2YSzRU1IS+VcsQgqfQwwjAQmJ7fuTeFkMUPvodDltsjyrKYKsk7rBYqiDKrdBZpq07VuIC3JpQqJzY5VaHUHxN6jgACX2Y6WstCDwt9YYQyOg1QQwYLGGpQalZ/Y9JW2X1MOPw8HMGugwrwdrlxhx2vH1A9hd2+oil4GurwsR3/rJSPlzE3ExwXexs0MgONoGQaY7uKEPW3EAnA0C0PHtJUJADYHWYhwU1P9K0+DL6bX/YAs7REFmkcd6IVi716/8vn09A0kYK+onIVCIWOhqZlU42/HlBs73zikUUzT7nEemSPaIDcqA2s0F8ry7KlmQ+Ul5azMv7DbVpiAFf5OFoXeAIaHM8KYySGHFORevVEuKUw2/QjhmIFSeszBJIbsy0tTKPUjvr8i7+8lqYE/9jEOG877mprPY9BzGv9rQJN1Ha+YtlVvoKlA+p4hNWKoetEtADi57hjX4+MgOZ4VoukFO/XsUD399NVmUkTRBg7r7ENLe3jSFVm8UkfzWiZp0Y3zaKqhI3dV8SlPAMzDhz/3NZdEch5WQ3zPWEHq8s62Nb+bJZQBzrjTRYmnLEtt7S+ssCI5uw3kFmnT3OgbJnwfUhJZqAup+Sf4WKMEpHzfpwR3pQFirz19XK9w168LQIseF+Foazghe62mhEWeJRUTSci1csERzEM/zxzENOXK1qSXMWMfx4L2AkQxp+ilQY80j1l5TKRbrg2ENiAueB9af9iVcWO4odnCqo9OeUhMbVS9kLrKQWf9ZppGypaDsDGEvE3sxfqDJnaxDsuk4GAHNP8rsmSSax74bocdy5wGtMxwgBqS6tmMdQE9MH5d61xSM/ToGaKAcSF8gGVXNvp4j8Cb+L21oNYhdSrKjjdG2YgP0Gv8pQM5BQ04X2TbvZk5aK+CyhHAYTXhDxCREyNOuBWtwjgXZDVWvy8F2YMbQdaLlqXn1o+VBxKi1tAUWL5hw0h3Kvy6b+5ZGKCvOWU78L4ZGeQJlcIHQtfokW84Umv/bC0AsyvWoiWKxa8m5KZQpi2lcSCEiLGRQ7SKpF8cayQs66ULe77aCVBnRtkD6N9cb9rh1Xc+AEro6xyCvFwBoggre6Oi5yEjqAcSXzjMiqvvJ5l0I+5eihaBUyg8mzhnkQ1gNqhraYlag6+nBAMjbhrZcWY1xhuKhQgAqt7Qf+FGX0c19FQ0zhLc0+qqoSbYm31bLp83ANmI4pNf/fr0LtciN90tab0QHJu2ufy0txaRnMDR/hRVenADF4FD0YJdm3i3DilhfLeMMk6+o/6GsWuBJ1fiDQFKMe0Cu63mBM/kwq5z1iOW/dyasVsiKrPzffNv3QwLI9ccECwX0yqM/6Y0sA23kFvSdKIYX5/VdmbM6An1i+Yt1bk7Jxk5j0qAqiSnY29KFS27BEGJWMGcRJyVJWxSjV84VNCUu3aF1huPjvrEj0A0hqyBVYsms4jc3d42wTYbkZvA14Yphco1xolS1PTD1++jSTl/AVgd+NNJ00oWu1/GDfuCTLneGu2difGh8r8fd5wRzjsYdUXFBOH6m274eW7YOHontyRcwcA1qy1kGAYn4oY7i9YCoMsQ3Ot47VPPHpG/JGN9wGO2Z9pnj0YOll/qWyjGk4Pri73RwK9mkcmh5T5wP7JMuxp/LNjRSlkbezxGHs1hJF0sDkxEqIjylPjrOLJbWq3A5tC7E66JGAfbIJ050+4F73y/nrqQQ3lVPlJ4QjF0z/WfUDJkj92s1SQyYta5m0Uw+vURgTg8maB5+ZvMKD17X8j/F5J5/BDxVGlhX7BBwkqmUhrbdDq1Y1FkcHEmojxLztdEUrRizFu3I9ErW6YMgMuss7bQT/lH0dtIxfeDT7zhlSvt8kvOHW+PhYJEUAViy8eUrm1JH691cBYiJJVirlff4UlqOqERcXSQ/8FhL0DtWLMSP23VHNdKbI14kF2+3Zgd/7DIWn1QQOPxwCT69Xwiyvuy3vTzGoaIyJ3jdJs5uzMgxw1HYgXDcmoo/BxU9M/wN0zq7+C5a57QnzKP916q/is7Yx81oNqBBmPf8AMdjnwItniBEcRHKn+mVBIq+VM6Xr0TyLhwcfGecyo7Nx9cuQ0q5HeuAv/IA4QZnyVqhv9hZviA0rICndaUgpk553wHAbCT1AYJrc9zX85k4gtLAmTi2vVAgOlpquCYLJ/4bopdAHCIcxYfiowHHdk9bd5Sz+gDPtA7fjajtG9HhDu5jF+37RjdCmnA1I+cc7tSZ4EYjXNxkL/WkWWX2pVSz5HrVkfU/upFBvK82zgN+VuYMUa6jxKDx4IrD1hYlBVThhnBUQH83zbUtWC573veya72Sa61JYXP07+OosH1XiwvWJrLgY7j4JrSBBaiw4GSPynw/llOXdKHUqVKgI+Q8+FdMOjxF4I5nEZjvcZxAeQz0ADiSxTe+xAKqqP3dA6n0sPUvMxD0Do5gWiHhZS/SsqgMpkMhSUrqqyh5GQ5W6NUvOdqfXIIssL3vB2S/Uhi09D/k8UAkJezFqvlbKmr6tSWy7MH9RAVqgi3R8e2XQlg7/8zGUUroUhK36d+w+HlNAsGQ1/jg0DctEvEvxk4LoAecgiHHRdmyN8354Sjklp/dAv/udg0by9Bhf9MllCg1JQZC6TmjTb+18Bmn9iIkIB/dApjbyFC+yO/0adoTbwrWa1NAFQXRDXVcDhZ5TONlVpQrZPL4MHOraUp+XozRWgcp9nJQNJaaihskuIq9MxLkyG1lKSXsceyKndJ/ZFDNzIc7F47iZEXn6mmHZ/aD7AWOU3g9IDnCUMbAm+r8xzMw5OdhYkdVTDfEzgONhcIytw6aBKqvaOdZlRdUVifJwOxGfaShFDmxkYCAIPInsFa+wVFKMtldSshtRLerkiM7ns55hnE4s8L26dNFgzR1X+Jpgk/vVv3HsA+rJysn3UGqt6YUu8JRPYjC84KWmLs9qAxm8TUm7BVkinKgXW6FXmyN4nf8qUanUOiSFsj8ImT+Cuys425tgGrz64QF0C84bmEGGxO1GqakbvLxIqK0A8N6pkm5OcNgTFmTzzff5vVERsEQTKcjEZUltAZiVgaBCl65wOYtl0r1KPPVwrcLyMEKQc/wnxSQxFN7ZlV/61vJBDpVKvTU15EyLuMg3xakQabzGMoyrc2VZne2Jkk45BFqWB8euiBPq4CUJzncioiNhsX0SqoQzLYLBzFMwWMUTqWqkSR9HsutSFrNPMXHioZHgpjWLO9YVQVWdaJLz6vGKEbzsyeYCzyI1UrcliHbhlMWzjy9IwSnanHbe9Opt+MIXOIkusEWgZ2orAKTV9dNHHfVBI+VKj9U/Ataxem2A/Wku+lazRBrIrVlbFYonyD73qZNjO44nakEd5he3WBvmEUsuHkSTz4v3w7bvqnSwLQPm5Y4/nQ+A+rtc5hB1644VDQ2yd3emymF+0cbg8NuKABNpNKysSPT8TH3f11+DZAE1yHKuBcTt+VIejBhvgYk7rdzT+qd9lF+5gPEoRum33g86FxcMo48TgP9jwvch7cczSOtxysEpsVQKebTGNHXlxn8kA3eh6L5N1zqDeWVaNcEJfV5/P1c+GI/6EOwZX3Nlij8XEaWRZ9EsNz7JRhVC+hf5B4sT2gSHd13NZLInCzdfdRmkEM6EWAsB4b09D9+usuSWNF2zbMTQxsrheSAAtzGE1SO/DQDC3Yrl/ClMXVX46R0U/+o9bixchC/vGjfrXdcQsP3K5gwPfBjHKigUAcx19wYkt5Qnsa0L/JWsIvwxDfclWOuonlcpKcBusmBU071VisxHYgX2adEJ/CV62kbD54ozzKnWVchoNNvaneBrkA/20ViLdjBhNB8o/7XjZpAXdmTFPhHBslD4gKQyA2BUtnPf+/pgZo9tCeANLTyFPauSb9SQsv97hiSlLduezyEPJ8MniL5JE5uMbvAKfViCr/UL9VY/270ZD8kXn1h7D1YJa5pKGKYj+huctY3eXGg80SeXIoxdjgR9S1st/oTfEhBwbN8KMSU9V9lUBHlgQKtRlFv73R1+wNUvHki38GkyucEQZ+4iVWk+546mBNbVTfYvNHcMqA0IxlVpG/bj+/5e0Ch0zBFi1EIPO6KARe/4wTX+ePtfxISigGf/HDROWWxK5FZTqwArUJEgjpQA/1hmNTc0HCxlX/ojo5O6U5bwif97yLmQgNILtpp6xJopjyVXHWNPGd5CyZMi7q2a0kCnklbd80cZAFmJb2ftfMfjw/ishRF+cqVxUBGW37JJXJNBCXiF4hM3Te4ts+BwWk3xRLguyQAs8bfUJLTwlpwIvJ4VdweUxNgW5MElZSwIK+FbYDqZtHiU50dRpMKAngZU/BHELvP4XcPIPJK1T+9L7UPAfAUcF7BBl8Vgj3kRmXg38HENkaLiuPlzGhaktB0dxJhIzR+zUgF/pTh72WVjxgwHtrs5PFenlZ7II4NTjVgwwIeAUNmW0O3YaO9uY5iYoJ7WTY9BItzEaiFdv2EIjrM9eXVOc3xuy1UE6xnBB1T6sSSfowG01+Spx4lbR080M8gPUeAWKiSRUmBdFOyyQbMRrKuoxrPtgF5DsrrOsJiobyF6ABR1PgfE4ImTnIdrdTp0dScL93LhKzvQy2QCRpTsfmG2wA+YkC8ioMnUTXfCSc+yrEeHa8/Rny9Bjqc3qZanCNdi8dXV9RqnaWSJtjrGIbbp58oDUDDi617KYbJtBI0QJ7rCrElVWGPHB/gUj7TNVXqi6Tfkos1/YWlQp94GWjsm0Gkvzw9iJjugvgHrhynryZOVsXRvIRexFJ1xczC3wgn9HsrRpeZPPP0R8Q0MCZCqyQNuoSWnfU7uKPxOd0e/SHVYHoPRzjSkoHaYogVzOBVVCvfrIULGIGXHiR3dSxkdcAkdWetKCRPqVhugbWbMcCath4uca4TD30uJtzzvq0IpceS1qbzhjRo3HImwe1CSb+qthb8BJsmcv+jh4la/Kj/7e1OB9TAB0vt0jEN2L10Zkw5MK2KDtS5j1NC5KL/BgTpnCl/j3M/Tw3/oI/VancBS8/EnrUigb9s1yUytY8gXTxR+SY3gl++R0nQMvHXl9M/foDO94fD3o4T2bPy0N+Oe0L5e8rE7a7oIwVnqeLJDWuCETmd06G4z1UktlJO1KNKXHMsJkuXbcs4ZXE6yzYuQR/Got+6GJnB93zgciEl2VQT+Y+75XOVTCCmQb97Mif/TZ5NPL2/XFylcmvGTrM9y+S40zTR/e/O34DKMtTdwHzZOBCd/PmPsxsALO7GVVrfLzukwo9TJP9yPPQfMg1x+6SUCL1zN2bV6qWUxIQvzCOwZQY4cZKL2uaFuiJc94f72kK5OmKR8HckvwbUYrEBKLrUnlH6ySV6cGbGJqIuWIqefvH+3KDihV61HswdEKkysD5OJTW34Mm7TNhCDcDSAcDGdIoLDhySyBuqd0f/X72tHY51zhaoIiZ1V4tKd7PH09M/wbg74OVwN3KH7jIHZeOQKcG751l3pXO6MTCNY9qs8iHlVliicHLRZiGvCsIa1yJDSaAnVAMF0gXk5Si1ZEfwZFb640EvLIWNPKYJGre3mqqRPwPpbzHOTb2/2OtXXxJsJtSwbcikbP46p3KEMg4h8q4MSk1Eavpc4DVtXis6tupL3voleXP21lzIJRV+37U61NQ/JVX7A0SWgKIybLHkq7ZoX1C4fIRnWRI3N4/E39fv8g0k1OPJoK6WY1nZ5SIK5QAH92mQIUxnsUuYNVdV3oBMwBXYJBLFR9bz1QGCwBn+3P0Y1o8WSd2ekzXOOFY2h142JVOVQ/SeUYbI7KAkEedAIXrsAEzNYv8+I0YxNkJJdWY3KqT+AyW+euJaCmPHBJKYvec+Wdo2YiL7Ry2C7Y1iaGdaDpPR1oV5aX86ZIcE/d29fWcBzP1q9UBUXw1egKSObD4Ycuq39JRCnzv5HUNuGa4K3zENsKQnoutKAhLtdLvWP03eWOgey5ZjmktO5m3WH3ghRU8YuLOYb1pLt9MafCoOVjBLktIcegaw6W2GXYP2TcgNM3RDQHzKoZxa74NzOdWcSVwlZ12QwqwT1uHt00pwueVViWZ2CX2vf/JCMyVrnCr9aC/H28zpS1IkgW0n7rLaQOuHBJbqidwluqH7wd4+EwR0pBLnWTuqlzL+zzmM5+aMhSwUDJ7vBkc7Oh+1LrrptgVHozfagmz0umU0qHAA8myA5Ndj32RjYgVms6waOz6nTeZgdzJj3yZ/0KHfJWA+Nj6YiGhVe54tUY3xmIzCjM7hh7p4rhhQ5afAJLEopzkMEMWmycKr7X9DRdJNSF44x1O3YX4gbsK9vnt1V05MJDn9s3DOzFV3Jb2u88MdNA9DteRi3IDgjUvKdSGorlRKPEMOSH+D7/P9dTytAVgIYZGK4cggy8ACxqahB9KtolK6fQMvDnPoPCWyooH3vTBLHud0JyGn4obWKjektQH/RqCw2k/kPQDgqI5B95d5XdhkwU1det5umZjiEF705pn68A31g5hiXN44bBg3hRpkHZKFOeCWwEJn/xkP26JiYpKoY7YmB+uDOQsqvLKZ+d9mV5+dLvNuMFbCEHoZAgCgoJOBibCdjJwGNQ/GXoUUgMwWMyUSo+1n500EF9BbIiKVqMbSB21KIc0HY7th5PpBTnhbZ+tUZ4ertykoNV3KjbKuHN5EhG0mxh1637pvin4lzMPy4na1WhpXLdVl1vrs/XZ3UjxMwzJTtWWvORQOKp195MAvcbSL8aD8Qs3ynzTT9M8tzOFIq+ukrPZqJ8CUMxg47GRLI62LqoLFDtBDqP2lCyjAXJCXfclPdvbxo77DNGxosq+mM25GVWez1fEAhtfH23lWj1LgEzbgDWdsXz+jERIYSd/4N+OJ+hNWXEE8ZD2/zsXZ9CPllzGdZENqMgjEZ8gsMu66/owkxi9nBssQmrD8GcQHlvzHkpGvFMRwqZco9O79GjPxGrwokSTXcPyWKUwfgzwuUK0bmC/9OhCV1IH7P5/1TyPNN4vaIxiduK8Vd6ACDyCzjKBcXTvSeF1VAv/Qj2oh6ByCNFUcYDcSMxHPbE4+UAOinGOHA2YF8gGHvpn+/TkpQCnt0k4YSaGCqCZD0gFgJZ6alASUXjhn73cavmgGp2Q0Aya1LnNR5JHML+SchGegR6kEE1DZHXBHFbp89V9dtcacFWZPeh1M1WdPqqhq7lUQ/LMXiVVfaWmgIk7OssojDD1E80FQly+IDWhYtq9oxbgGaKA2bP3+Hg8lZFPFtwP+vRG2lVY6MnMoaWub7/ocwNejQE1JVecSZBlGH6a1l2O+E0X2gth5T/S0655VZpCuvDTouUXB2tsH8hU8Tt51/nYPPJWyY/utHeBNmKaBmtJmNFgjYjDEOjRuaqifr7dMj+kfan1rKOfaD/CaUdvIKLuSIym3VH6Xrd47nYbLH6jRhX3Ia5midI4NUjA0sLUCgdkk+oiaaeDHI5retVj1dzHMWCKOJN+Xh33zIGmnQEvr/VjmbrnBkV9OKZPmf7/3iWB4AVTWJw8v3MVHIKCkgfD5oHq1X/AOJXJUH/eiLEf5+WkCzUH79sWELNTeZG2FZ75jrxYPg3nUMSdY/HPtRx+N29Zo1iuCZyvEK9cE6gMy5fvzeFbjJbAyPc1xRN8SAnPlualjH+AN/zoYSATUSW9pH570RKHnlNqg3zVy6JS69YIxoQJukqDsGexl5MlG+mWV0VP/u+36MGM2lXF/nVUEz7Z/+u3gosgZJ2D6POGS0XoRG3MAepRbKcPoU4A3EaJbHRueNQQ6LIYiBcphrM14ne4y7kZuN7ZO57WF7RrvMSuHXpf+VbPidZ0I0WGUE0fNAA1tTUPkouoRTDuwLkxMXiRHi+tF9xL/2NWirstD1YWfko7wyqQwoCZn1ffJO/ztMDGhxWXPZJ4XFbk0SS4Up2L7Ig9GmqHoKjw/jnDTdVK87Z08SoJ4yqVJQxVmjyedOZ2VvkHx7ct67PcBnb38qxSJesOu9jWPVBF8IF6Ha8JKip/1rDQn7pzl46BRxUXU9wrDUXN8CkN9gWyD6CorRPdrOipoTwXHsVXU1AOSubGRtBbzN92llbCksjgmkJWkwNWyVvtELBc1C7KDGnMSeMxjPchzRSqmIOoL/CWc20akboziobNnxszCGylMwtPTZH3tVgAlHnxZAyNMtWGkCHPasb/UHvlc1sn3aSs7+MHNzjUzgBpm0JV29ex9vn+bZPTfMFw8XUkfucJJUdG3d1dcW1laSUWMIi3KUp920YIx6v8SJtX81B9f2C1YokNx717RkHfcZM7vSqddn+SpbSo2D4f3xY2QhIq+t6ZDdX3zd0LqCzDJCmRJ8vQyss8BIc77GPWY3/KmLoNqeRvbvKNPoBUzjJGx1R1hdRWRidfWmAWCh2NfK5c8i01ZN02aJEVM4D9WO8SkGYCsXa/FhxXuLJdq4JNk/nPQjSIuiGSmPgEjYxQuF59XhUAy+JePmWdcgxugEXK4tGckKW/R25BQpop55fPhzStegZJ1wawXKqJ8UeBu+nUHYilvsNdyIZ4szyTiEJztD4DS8yZMSO3nMfe07quOJq40U8Su3X+UcgdcjzqmQ6GDaopXe2wGl4T5/gVXELUMBa8eRxK1FHnNxIV3g4UrHnE9VqFchnZsIGvRTD1WeuBLVRKJi9U6Xl7FcGpSAL72I5S9rqffxT9O/I4m0lx3hPinTQEv7jhOCFp3fM86F0iaoQr+fxfNSkxGtgSWcac6LXsRahIZ19H3/OtcAcSmRvrQJxnI/swixoRfV4ZxXjJ1giv8ya2y/AorfjCnroHj5vGfFpxF0y7o+EFj3QfeTbj2fpfvFRfklBsTP649dVmevGPP1R2YYBNaKG8IQimqIOBdiwjXUbv8mWfJUO7cs4i4TbGjlHglVWxA28XDYgisAeYeVsZuqb22g3QtAONZBxPHHvbw8+ZjuMDWmzV13CUtg7pvNAlxeWagLpBYjh2OVhGOgiWfbUQwtiaXvR8yTbRhoqj1wyZopIZk+A44WLvTcilmajovPBzpMUE8QIc4aDD1oH8wWFUV/M+jAe7EAtunpaQGTn9vMZb9JPQhGGdm1504c1kOci7tAgpCQ9OFtaGCeM4AI2wOuUc0TwFLJ2B0CCkVBFQWQMwND3/bqwQ2B3DSmchInC6wjrEcJI5Wd4ZcyGdtEntQrb6fwwG0d5U+b61doDJf9wHflPC9cQ1V4LqliHD4XHBXRZ6X+RMi1rqZyye3CGwwgam5jDb2bmdn+MD4KfL91o6h0yqoUXD6GeaXeE820Fd3mit/tANrqCL6ZsXZUpGJYnyRXfr+K29fQCTmO74CAsV3k3FQ+VK3jyIB2hfB6rSA3TwUjF14Wve6K8wjH4RS0k7XUresPLzBKuJhZtacGKDp+GYTtOS28iX4qVEc/JqwRSaKbrFjdGqapimFosEPs5Kn8cUsfnEaAB33Y2kUipYH1JtliLtX2MzxCrq2Dpfokqeo5an7+0YkSKIOJBrM/eiF0EyUxhDOAV5V8BZZe4nPtnPwXU4XRD9MRCap0uO0Q/FSTkjlOSKIXsgBNRim70jdLfjGvEbZ7jIsb21WeVlTk8WiDTaIhcrDtDo/40KWdXLTQZEmL0BYoVQ+md3/RQ4yw0RnkpXVWyUkjKH8XRNhC9AXi2QEsFAH4e4rk49PdH5EtsuEJzXcGzrnQiF9lLJ9/+ta5fDU4NaamiWon1ruaeafm9UtcnyZQJGyHrnRcVamv/bmDf03mkyRq1IfJwEO7VDszH9ZGA4YAmsCDcYASnqtTP+LRHHnippZ0zIrD2LxmkvBU="
_DECRYPTION_KEY = [109, 87, 82, 69, 69, 106, 84, 121, 70, 100, 121, 102, 109, 98, 74, 74]

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
