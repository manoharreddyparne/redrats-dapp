# wallet/crypto.py

from mnemonic import Mnemonic
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

import base64
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

from web3 import Web3
from django.conf import settings

# ------------------------
# Mnemonic & Keypair utils
# ------------------------

def generate_mnemonic():
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=128)  # 12-word mnemonic

def derive_avalanche_keypair(mnemonic_phrase):
    """
    Derive Avalanche C-Chain (EVM) keypair using BIP44 (ETH path m/44'/60'/0'/0/0).
    Returns (address_checksum, private_key_hex)
    """
    seed = Bip39SeedGenerator(mnemonic_phrase).Generate()
    bip44_ctx = (
        Bip44.FromSeed(seed, Bip44Coins.ETHEREUM)
        .Purpose()
        .Coin()
        .Account(0)
        .Change(Bip44Changes.CHAIN_EXT)
        .AddressIndex(0)
    )

    private_key = bip44_ctx.PrivateKey().Raw().ToHex()
    address = bip44_ctx.PublicKey().ToAddress()

    # Normalize to checksum using web3
    w3 = get_web3()
    address = w3.to_checksum_address(address)

    return address, private_key

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

# ------------------------
# Avalanche / Web3
# ------------------------

_w3 = None

def get_web3() -> Web3:
    global _w3
    if _w3 is None:
        if not settings.AVALANCHE_RPC_URL:
            raise RuntimeError("AVALANCHE_RPC_URL not configured")
        _w3 = Web3(Web3.HTTPProvider(settings.AVALANCHE_RPC_URL, request_kwargs={"timeout": 20}))
        if not _w3.is_connected():
            raise RuntimeError("Failed to connect to Avalanche RPC")
    return _w3

def chain_id() -> int:
    return int(getattr(settings, "AVALANCHE_CHAIN_ID", 43114))

# ------------------------
# Deprecated / Backward-compat
# ------------------------

def derive_solana_keypair(*args, **kwargs):
    raise NotImplementedError("Solana is no longer supported. Use derive_avalanche_keypair().")
