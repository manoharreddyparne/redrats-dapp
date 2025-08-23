# test_avalanche_wallet.py
import os
import sys
import django

# Add project root (the folder containing 'backend') to Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Correct Django settings path
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "redrats_backend.settings")
django.setup()

from wallet.crypto import (
    generate_mnemonic,
    derive_avalanche_keypair,
    encrypt_mnemonic,
    decrypt_mnemonic,
    get_web3,
)

def main():
    print("🔑 Generating Avalanche wallet...")
    mnemonic = generate_mnemonic()
    print("Mnemonic:", mnemonic)

    address, priv_key = derive_avalanche_keypair(mnemonic)
    print("Address:", address)
    print("Private Key:", priv_key)

    print("\n🔐 Encrypting mnemonic...")
    password = "test-password"
    encrypted = encrypt_mnemonic(mnemonic, password)
    print("Encrypted:", encrypted)

    decrypted = decrypt_mnemonic(encrypted["ciphertext"], password, encrypted["salt"])
    print("Decrypted:", decrypted)

    print("\n🌐 Checking Avalanche RPC...")
    w3 = get_web3()
    print("Connected?", w3.is_connected())
    print("Current Block:", w3.eth.block_number)

if __name__ == "__main__":
    main()
