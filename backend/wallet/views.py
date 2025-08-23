import json
import io
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from users.models import GoogleUser
from drive.utils import get_user_info_from_session, refresh_credentials_if_needed
from .models import Wallet
from .serializers import WalletSerializer
from .permissions import IsAuthenticatedWalletOwner
from .crypto import generate_mnemonic, derive_solana_keypair, encrypt_mnemonic, decrypt_mnemonic
from cryptography.fernet import InvalidToken
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from django.views.decorators.csrf import csrf_exempt


class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticatedWalletOwner]

    def get_queryset(self):
        try:
            user_info = get_user_info_from_session(self.request)
            user = GoogleUser.objects.get(sub=user_info.get("sub"))
            return Wallet.objects.filter(user=user)
        except Exception:
            session_data = self.request.session.get("wallet_access")
            if session_data and session_data.get("method") == "mnemonic":
                return Wallet.objects.filter(public_key=session_data.get("public_key"))
            return Wallet.objects.none()

    def create(self, request, *args, **kwargs):
        try:
            sub = email = name = None
            try:
                user_info = get_user_info_from_session(request)
                sub = user_info.get("sub")
                email = user_info.get("email")
                name = user_info.get("name", "")
            except Exception:
               pass

            if not sub:
                sub = f"mnemonic-only-{generate_mnemonic().split()[0]}"

            user, _ = GoogleUser.objects.get_or_create(sub=sub)
            if email and not user.email:
                user.email = email
            if name and not user.name:
                user.name = name
            user.save()

            if Wallet.objects.filter(user=user, wallet_name=request.data.get("wallet_name")).exists():
                return Response({"error": "You already have a wallet with this name."}, status=400)

        # Step 1: Generate mnemonic and derive keys
            mnemonic = generate_mnemonic()
            public_key, _ = derive_solana_keypair(mnemonic)

        # Step 2: Encrypt mnemonic with a secure temporary password
            import secrets
            temporary_password = secrets.token_urlsafe(16)
            encrypted = encrypt_mnemonic(mnemonic, temporary_password)

        # Step 3: Save encrypted mnemonic in DB
            wallet = Wallet.objects.create(
                user=user,
                public_key=public_key,
                wallet_name=request.data.get("wallet_name"),
                encrypted_mnemonic=encrypted["ciphertext"],
                encryption_salt=encrypted["salt"]
            )

        # Step 4: Store access method in session (no backup password yet)
            request.session["wallet_access"] = {
                "method": "mnemonic",
                "public_key": public_key,
                "temporary_password": temporary_password  # for later re-encryption if backup is enabled
            }
            request.session.modified = True

            return Response({
                "wallet": WalletSerializer(wallet).data,
                "mnemonic": mnemonic,
                "message": "Wallet created successfully. Backup not yet configured."
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=500)



@api_view(['GET'])
def my_wallet(request):
    try:
        try:
            user_info = get_user_info_from_session(request)
            user = GoogleUser.objects.get(sub=user_info.get("sub"))
            wallets = user.wallets.all()
            return Response(WalletSerializer(wallets, many=True).data)
        except Exception:
            pass

        session_data = request.session.get("wallet_access")
        if session_data and session_data.get("method") == "mnemonic":
            wallet = Wallet.objects.get(public_key=session_data["public_key"])
            return Response(WalletSerializer(wallet).data)

        return Response({"error": "User not authenticated"}, status=401)

    except Wallet.DoesNotExist:
        return Response({"error": "Wallet not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def import_wallet(request):
    try:
        mnemonic = request.data.get("mnemonic")
        if not mnemonic:
            return Response({"error": "Mnemonic is required"}, status=400)

        public_key, _ = derive_solana_keypair(mnemonic)
        wallet = Wallet.objects.filter(public_key=public_key).first()
        if not wallet:
            return Response({"error": "No wallet found for this mnemonic"}, status=404)

        request.session["wallet_access"] = {
            "method": "mnemonic",
            "public_key": public_key
        }
        request.session.modified = True

        return Response({
            "wallet": WalletSerializer(wallet).data,
            "message": "Wallet access granted via mnemonic."
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
def logout_wallet(request):
    request.session.flush()
    return Response({"message": "Logged out"}, status=200)


@api_view(['POST'])
def restore_wallet_from_drive(request):
    try:
        encrypted_data = request.data.get("encrypted_wallet_data")
        password = request.data.get("password")

        if not encrypted_data or not password:
            return Response({"error": "Missing encrypted data or password"}, status=400)

        ciphertext = encrypted_data.get("ciphertext")
        salt = encrypted_data.get("salt")

        if not ciphertext or not salt:
            return Response({"error": "Invalid encrypted data format"}, status=400)

        try:
            mnemonic = decrypt_mnemonic(ciphertext, password, salt)
        except InvalidToken:
            return Response({"error": "Incorrect password. Decryption failed."}, status=403)

        public_key, _ = derive_solana_keypair(mnemonic)
        wallet = Wallet.objects.filter(public_key=public_key).first()
        if not wallet:
            return Response({"error": "No wallet found for decrypted mnemonic"}, status=404)

        request.session["wallet_access"] = {
            "method": "mnemonic",
            "public_key": public_key
        }
        request.session.modified = True

        return Response({
            "wallet": WalletSerializer(wallet).data,
            "mnemonic": mnemonic,
            "message": "Wallet successfully restored from backup."
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@csrf_exempt
@api_view(['POST'])
def set_backup_password(request):
    try:
        password = request.data.get("password")
        password_hint = request.data.get("password_hint", "")
        public_key = request.headers.get("X-Wallet-Key")

        if not password:
            return Response({"error": "Password is required"}, status=400)
        if not public_key:
            return Response({"error": "Missing X-Wallet-Key header"}, status=400)

        wallet = Wallet.objects.filter(public_key=public_key).first()
        if not wallet:
            return Response({"error": "Wallet not found"}, status=404)
        if not wallet.encryption_salt:
            return Response({"error": "Missing encryption salt"}, status=400)

        # ✅ Use temporary password from session instead of hardcoded "redrats_default"
        session_data = request.session.get("wallet_access", {})
        temporary_password = session_data.get("temporary_password")

        if not temporary_password:
            return Response({
                "error": "Temporary password missing from session. Please recreate wallet or reauthenticate."
            }, status=403)

        try:
            mnemonic = decrypt_mnemonic(
                wallet.encrypted_mnemonic,
                password=temporary_password,
                salt_b64=wallet.encryption_salt
            )
        except InvalidToken:
            return Response({
                "error": "Could not decrypt mnemonic with temporary password. This must be done right after wallet creation."
            }, status=403)

        # ✅ Re-encrypt with user-provided password
        encrypted = encrypt_mnemonic(mnemonic, password)
        encrypted_data = {
            "ciphertext": encrypted["ciphertext"],
            "salt": encrypted["salt"]
        }

        # ✅ Upload to Drive
        token_data = request.session.get('token')
        if not token_data:
            return Response({"error": "Google credentials not found. Please authenticate again."}, status=401)

        token_data, creds = refresh_credentials_if_needed(token_data)
        request.session['token'] = token_data

        service = build('drive', 'v3', credentials=creds)
        media_stream = io.BytesIO(json.dumps(encrypted_data).encode('utf-8'))
        media = MediaIoBaseUpload(media_stream, mimetype='text/plain')

        uploaded_file = service.files().create(
            body={'name': 'redrats_wallet_backup.txt', 'mimeType': 'text/plain'},
            media_body=media,
            fields='id'
        ).execute()

        # ✅ Save updated encryption to DB
        wallet.encrypted_mnemonic = encrypted["ciphertext"]
        wallet.encryption_salt = encrypted["salt"]
        wallet.backup_drive_file_id = uploaded_file.get("id")
        wallet.password_hint = password_hint
        wallet.save()

        return Response({
            "message": "Password set and wallet backup completed.",
            "file_id": wallet.backup_drive_file_id
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def restore_wallet_session(request):
    return Response({
        "error": "restore_wallet_session not implemented in this version"
    }, status=400)
