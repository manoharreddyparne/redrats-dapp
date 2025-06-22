# from cryptography.fernet import Fernet
# import base64
# import os

# # Load from environment or generate and store securely
# SECRET_KEY = os.getenv("MNEMONIC_ENCRYPTION_KEY")
# if not SECRET_KEY:
#     raise Exception("MNEMONIC_ENCRYPTION_KEY not set in environment")

# fernet = Fernet(SECRET_KEY)

# def encrypt_mnemonic(plaintext: str) -> str:
#     return fernet.encrypt(plaintext.encode()).decode()

# def decrypt_mnemonic(ciphertext: str) -> str:
#     return fernet.decrypt(ciphertext.encode()).decode()
