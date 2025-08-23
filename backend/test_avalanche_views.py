# test_avalanche_views.py
import os
import django
import json

# -------------------------
# Setup Django environment
# -------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "redrats_backend.settings")
django.setup()

from users.models import GoogleUser
from wallet.models import Wallet
from wallet.serializers import WalletSerializer
from rest_framework.test import APIClient

client = APIClient()

def main():
    print("🚀 Starting wallet API tests...")

    # -------------------------
    # 0️⃣ Create / fetch test user
    # -------------------------
    user_sub = "test-sub"
    user, _ = GoogleUser.objects.get_or_create(sub=user_sub, defaults={"email": "test@example.com", "name": "Test User"})
    client.force_authenticate(user=user)

    # -------------------------
    # 1️⃣ Create wallet
    # -------------------------
    print("\n1️⃣ Creating a new wallet...")
    create_resp = client.post("/api/wallets/", {"wallet_name": "TestWallet"})
    print("Status:", create_resp.status_code)
    create_data = create_resp.json()
    print("Response:", json.dumps(create_data, indent=2))

    mnemonic = create_data.get("mnemonic")
    public_key = create_data.get("wallet", {}).get("public_key")
    if not mnemonic:
        print("❌ Wallet creation failed, stopping tests.")
        return

    # -------------------------
    # 2️⃣ Import wallet using mnemonic
    # -------------------------
    print("\n2️⃣ Importing wallet using mnemonic...")
    import_resp = client.post("/api/wallets/import/", {"mnemonic": mnemonic})
    print("Status:", import_resp.status_code)
    try:
        print("Response:", json.dumps(import_resp.json(), indent=2))
    except Exception:
        print("Response content:", import_resp.content.decode())

    # -------------------------
    # 3️⃣ Set backup password
    # -------------------------
    print("\n3️⃣ Setting backup password...")
    headers = {"HTTP_X_WALLET_KEY": public_key} if public_key else {}
    backup_resp = client.post(
        "/api/wallets/set-backup-password/",
        {"password": "test1234", "password_hint": "test hint"},
        **headers
    )
    print("Status:", backup_resp.status_code)
    try:
        print("Response:", json.dumps(backup_resp.json(), indent=2))
    except Exception:
        print("Response content:", backup_resp.content.decode())

    # -------------------------
    # 4️⃣ Restore wallet from backup
    # -------------------------
    print("\n4️⃣ Restoring wallet from backup...")
    # Get the latest encrypted wallet from DB
    wallet = Wallet.objects.filter(public_key=public_key).first()
    if wallet and wallet.encrypted_mnemonic and wallet.encryption_salt:
        restore_resp = client.post(
            "/api/wallets/restore/",
            {"encrypted_wallet_data": {"ciphertext": wallet.encrypted_mnemonic, "salt": wallet.encryption_salt},
             "password": "test1234"}
        )
        print("Status:", restore_resp.status_code)
        try:
            print("Response:", json.dumps(restore_resp.json(), indent=2))
        except Exception:
            print("Response content:", restore_resp.content.decode())
    else:
        print("⚠️ No backup data available to test restore.")

if __name__ == "__main__":
    main()
