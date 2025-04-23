import base64
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

# === CHIFFREMENT / DÉCHIFFREMENT ===

def derive_key(salt):
    return sum(hashlib.sha256(salt.encode()).digest()) % 256

def encrypt(data, salt):
    key = derive_key(salt)
    encoded = ''.join(chr((ord(c) ^ key) + 3) for c in data)
    return base64.b64encode(encoded.encode()).decode()

def decrypt(encoded_data, salt):
    key = derive_key(salt)
    encrypted = base64.b64decode(encoded_data.encode()).decode()
    return ''.join(chr((ord(c) - 3) ^ key) for c in encrypted)

# === SIGNATURE NUMÉRIQUE ===

def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key

def generate_signature(message):
    private_key, public_key = generate_rsa_keys()

    signature = private_key.sign(
        message.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    signature_b64 = base64.b64encode(signature).decode()
    return signature_b64, public_key

def verify_signature(message, signature_b64, pub_key_path="public_key.pem"):
    try:
        with open(pub_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())

        signature = base64.b64decode(signature_b64)

        public_key.verify(
            signature,
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except (InvalidSignature, FileNotFoundError):
        return False

def save_public_key(public_key):
    with open("public_key.pem", "wb") as f:
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        f.write(pem)

# === VÉRIFICATION D'INTÉGRITÉ ===

def compute_file_hash(message):
    return hashlib.sha256(message.encode()).hexdigest()

def verify_file_hash(message, expected_hash):
    return compute_file_hash(message) == expected_hash