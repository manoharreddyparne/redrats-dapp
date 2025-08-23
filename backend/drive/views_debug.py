# drive/views_debug.py
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.test import RequestFactory
from django.http import JsonResponse
from wallet.crypto import generate_mnemonic, derive_solana_keypair, encrypt_mnemonic, decrypt_mnemonic
from wallet.models import Wallet
from users.models import GoogleUser
from drive.views import download_wallet_backup, IsAuthenticatedWalletOwner
from drive.utils import upload_encrypted_wallet_to_drive
import base64
import os
import json

@csrf_exempt
def debug_wallet_view(request):
    context = {}

    # -------------------------
    # 1. Create Wallet
    # -------------------------
    if request.method == 'POST' and request.POST.get('action') == 'create_wallet':
        wallet_name = request.POST.get('wallet_name')
        mnemonic = generate_mnemonic()
        public_key, _ = derive_solana_keypair(mnemonic)
        temp_password = base64.urlsafe_b64encode(os.urandom(16)).decode()
        encrypted = encrypt_mnemonic(mnemonic, temp_password)

        user = GoogleUser.objects.create(sub=f"mnemonic-only-{mnemonic.split()[0]}")
        wallet = Wallet.objects.create(
            user=user,
            public_key=public_key,
            wallet_name=wallet_name,
            encrypted_mnemonic=encrypted['ciphertext'],
            encryption_salt=encrypted['salt'],
        )

        request.session['wallet_access'] = {
            "method": "mnemonic",
            "public_key": public_key,
            "temporary_password": temp_password
        }

        context["wallet"] = {
            "wallet": {
                "id": wallet.id,
                "public_key": wallet.public_key,
                "encrypted_mnemonic": wallet.encrypted_mnemonic,
                "encryption_salt": wallet.encryption_salt,
                "backup_drive_file_id": wallet.backup_drive_file_id,
                "wallet_name": wallet.wallet_name,
                "password_hint": wallet.password_hint,
                "created_at": wallet.created_at,
                "user": wallet.user.id,
            },
            "mnemonic": mnemonic,
            "message": "Wallet created successfully. Backup not yet configured."
        }

    # -------------------------
    # 2. Backup Wallet to Google Drive
    # -------------------------
    elif request.method == 'POST' and request.POST.get('action') == 'backup_wallet':
        session_data = request.session.get('wallet_access')
        password = request.POST.get('password')
        password_hint = request.POST.get('password_hint', '')

        if not session_data or not session_data.get('public_key') or not session_data.get('temporary_password'):
            context["backup_message"] = {"error": "Temporary password missing from session. Please recreate wallet."}
        else:
            wallet = Wallet.objects.filter(public_key=session_data['public_key']).first()
            if not wallet:
                context["backup_message"] = {"error": "Wallet not found"}
            else:
                try:
                    mnemonic = decrypt_mnemonic(wallet.encrypted_mnemonic, session_data['temporary_password'], wallet.encryption_salt)
                    encrypted = encrypt_mnemonic(mnemonic, password)
                    encrypted_data = {
                        "ciphertext": encrypted["ciphertext"],
                        "salt": encrypted["salt"]
                    }

                    request.META['HTTP_X_WALLET_KEY'] = session_data['public_key']
                    # Use secure upload function
                    upload_result = upload_encrypted_wallet_to_drive(request, encrypted_data, wallet_name=wallet.wallet_name, password_hint=password_hint)

                    if isinstance(upload_result, JsonResponse):
                        result_data = json.loads(upload_result.content)
                        if "error" in result_data:
                            context["backup_message"] = {"error": result_data["error"]}
                        else:
                            wallet.encrypted_mnemonic = encrypted["ciphertext"]
                            wallet.encryption_salt = encrypted["salt"]
                            wallet.backup_drive_file_id = result_data.get("file_id")
                            wallet.password_hint = password_hint
                            wallet.save()
                            context["backup_message"] = {
                                "message": "Backup completed and encrypted with your password.",
                                "file_id": wallet.backup_drive_file_id
                            }
                    else:
                        context["backup_message"] = {"error": "Unexpected upload response"}
                except Exception as e:
                    context["backup_message"] = {"error": str(e)}

    # -------------------------
    # 3. Restore Wallet from Google Drive
    # -------------------------
    elif request.method == 'POST' and request.POST.get('action') == 'restore_wallet':
        password = request.POST.get("restore_password")
        session_data = request.session.get("wallet_access")

        if not password or not session_data:
            context["restored_wallet"] = {"error": "Password or wallet session missing."}
        else:
            public_key = session_data.get("public_key")
            if not public_key:
                context["restored_wallet"] = {"error": "Public key missing in session."}
            else:
                try:
                    # Step 1: Download encrypted wallet data
                    fake_post = RequestFactory().post("/api/drive/download/", data={})
                    fake_post.session = request.session
                    fake_post.META['HTTP_X_WALLET_KEY'] = public_key

                    @IsAuthenticatedWalletOwner
                    def secure_download(request):
                        return download_wallet_backup(request)

                    download_response = secure_download(fake_post)

                    if download_response.status_code != 200:
                        context["restored_wallet"] = {"error": "Failed to download wallet backup"}
                    else:
                        encrypted_data = json.loads(download_response.content).get("encrypted_wallet_data")
                        if not encrypted_data:
                            context["restored_wallet"] = {"error": "Invalid encrypted data from Drive"}

                        # Step 2: Restore wallet locally
                        wallet = Wallet.objects.filter(public_key=public_key).first()
                        decrypted_mnemonic = decrypt_mnemonic(encrypted_data["ciphertext"], password, encrypted_data["salt"])
                        new_encrypted = encrypt_mnemonic(decrypted_mnemonic, password)

                        wallet.encrypted_mnemonic = new_encrypted["ciphertext"]
                        wallet.encryption_salt = new_encrypted["salt"]
                        wallet.save()

                        context["restored_wallet"] = {
                            "message": "Wallet restored successfully",
                            "public_key": wallet.public_key,
                            "wallet_name": wallet.wallet_name
                        }
                except Exception as e:
                    context["restored_wallet"] = {"error": str(e)}

    # -------------------------
    # 4. Session Info
    # -------------------------
    elif request.method == 'POST' and request.POST.get('action') == 'session_info':
        context["session_data"] = json.dumps(dict(request.session), indent=2, default=str)

    # -------------------------
    # 5. Logout
    # -------------------------
    elif request.method == 'POST' and request.POST.get('action') == 'logout':
        request.session.flush()
        context["logout_msg"] = "Session cleared."

    return render(request, "drive/debug_wallet.html", context)
