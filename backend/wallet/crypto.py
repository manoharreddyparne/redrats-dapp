# wallet/crypto.py

from mnemonic import Mnemonic
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins

import base64
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

# ------------------------
# Mnemonic & Keypair utils
# ------------------------

def generate_mnemonic():
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=128)  # 12-word mnemonic

def derive_solana_keypair(mnemonic_phrase):
    seed = Bip39SeedGenerator(mnemonic_phrase).Generate()
    bip44_ctx = Bip44.FromSeed(seed, Bip44Coins.SOLANA)
    private_key = bip44_ctx.PrivateKey().Raw().ToHex()
    public_key = bip44_ctx.PublicKey().ToAddress()
    return public_key, private_key

# ------------------------
# Encryption utils
# ------------------------

def derive_key_from_password(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_mnemonic(mnemonic: str, password: str) -> dict:
    salt = os.urandom(16)
    key = derive_key_from_password(password, salt)
    f = Fernet(key)
    encrypted = f.encrypt(mnemonic.encode())
    return {
        "ciphertext": encrypted.decode(),
        "salt": base64.b64encode(salt).decode()
    }

def decrypt_mnemonic(encrypted_data: str, password: str, salt_b64: str) -> str:
    salt = base64.b64decode(salt_b64)
    key = derive_key_from_password(password, salt)
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()
