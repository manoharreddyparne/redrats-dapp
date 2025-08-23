# wallet/views.py
import json
import io
import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from cryptography.fernet import InvalidToken
from users.models import GoogleUser
from drive.utils import get_user_info_from_session, refresh_credentials_if_needed
from .models import Wallet
from .serializers import WalletSerializer
from .permissions import IsAuthenticatedWalletOwner
from .crypto import generate_mnemonic, derive_avalanche_keypair, encrypt_mnemonic, decrypt_mnemonic
from web3 import Web3
from django.conf import settings
import secrets
logger = logging.getLogger(__name__)
derive_evm_keypair = derive_avalanche_keypair

# -------------------------
# Wallet ViewSet
# -------------------------
logger = logging.getLogger(__name__)
derive_evm_keypair = derive_avalanche_keypair
class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer

    # ---------------------------
    # Permissions
    # ---------------------------
    def get_permissions(self):
        if self.request.method == "POST" and self.request.path.endswith("/wallets/"):
            # Allow wallet creation without JWT
            return [AllowAny()]
        return [IsAuthenticated()]

    # ---------------------------
    # Queryset
    # ---------------------------
    def get_queryset(self):
        try:
            # Try Google-authenticated user first
            user_info = self.request.session.get("google_user_info")
            user = GoogleUser.objects.get(sub=user_info.get("sub"))
            return Wallet.objects.filter(user=user)
        except Exception:
            # Fallback to mnemonic session
            session_data = self.request.session.get("wallet_access")
            if session_data and session_data.get("method") == "mnemonic":
                return Wallet.objects.filter(public_key=session_data.get("public_key"))
            return Wallet.objects.none()

    # ---------------------------
    # Create wallet
    # ---------------------------
    def create(self, request, *args, **kwargs):
        try:
            # Attempt to get Google session info
            user_info = request.session.get("google_user_info", {})
            sub = user_info.get("sub") or f"mnemonic-only-{generate_mnemonic().split()[0]}"
            email = user_info.get("email")
            name = user_info.get("name", "")

            # Get or create user
            user, _ = GoogleUser.objects.get_or_create(sub=sub)
            if email and not user.email:
                user.email = email
            if name and not user.name:
                user.name = name
            user.save()

            # Wallet name check
            wallet_name = request.data.get("wallet_name")
            if not wallet_name:
                return Response({"error": "Wallet name is required"}, status=400)

            if Wallet.objects.filter(user=user, wallet_name=wallet_name).exists():
                return Response({"error": "You already have a wallet with this name."}, status=400)

            # Generate mnemonic & keypair
            mnemonic = generate_mnemonic()
            public_key, _ = derive_evm_keypair(mnemonic)

            # Encrypt mnemonic with temporary password
            temporary_password = secrets.token_urlsafe(16)
            encrypted = encrypt_mnemonic(mnemonic, temporary_password)

            # Create wallet record
            wallet = Wallet.objects.create(
                user=user,
                public_key=public_key,
                wallet_name=wallet_name,
                encrypted_mnemonic=encrypted["ciphertext"],
                encryption_salt=encrypted["salt"]
            )

            # Store wallet session
            request.session["wallet_access"] = {
                "method": "mnemonic",
                "public_key": public_key,
                "temporary_password": temporary_password
            }
            request.session.modified = True

            # Return wallet + mnemonic
            return Response({
                "wallet": WalletSerializer(wallet).data,
                "mnemonic": mnemonic,
                "message": "Wallet created successfully. Backup not yet configured."
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Create wallet error: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=500)
# Utility: fetch AVAX balance & placeholder txs
# -------------------------
def fetch_avalanche_wallet_data(public_key: str):
    w3 = Web3(Web3.HTTPProvider(settings.AVALANCHE_RPC_URL))
    if not w3.isConnected():
        return {"error": "Cannot connect to Avalanche RPC"}

    balance_wei = w3.eth.get_balance(public_key)
    balance_avax = w3.fromWei(balance_wei, "ether")

    recent_txs = []  # Placeholder for future transaction history

    return {
        "avax_balance": float(balance_avax),
        "recent_transactions": recent_txs,
    }


# -------------------------
# Wallet endpoints
# -------------------------
@api_view(['GET'])
def my_wallet(request):
    try:
        # Try Google-authenticated user first
        user_info = get_user_info_from_session(request)
        user = GoogleUser.objects.get(sub=user_info.get("sub"))
        wallets = user.wallets.all()
    except Exception:
        # Fall back to mnemonic-only session
        session_data = request.session.get("wallet_access")
        if session_data and session_data.get("method") == "mnemonic":
            wallets = Wallet.objects.filter(public_key=session_data.get("public_key"))
        else:
            return Response({"error": "User not authenticated"}, status=401)

    wallet_data = []
    for wallet in wallets:
        w_data = WalletSerializer(wallet).data
        avax_data = fetch_avalanche_wallet_data(wallet.public_key)
        w_data.update(avax_data)
        wallet_data.append(w_data)

    return Response(wallet_data)


@api_view(['POST'])
def import_wallet(request):
    try:
        mnemonic = request.data.get("mnemonic")
        if not mnemonic:
            return Response({"error": "Mnemonic is required"}, status=400)

        public_key, _ = derive_evm_keypair(mnemonic)
        wallet = Wallet.objects.filter(public_key=public_key).first()
        if not wallet:
            return Response({"error": "No wallet found for this mnemonic"}, status=404)

        request.session["wallet_access"] = {"method": "mnemonic", "public_key": public_key}
        request.session.modified = True

        return Response({"wallet": WalletSerializer(wallet).data, "message": "Wallet access granted via mnemonic."})

    except Exception as e:
        logger.error(f"Import wallet error: {str(e)}", exc_info=True)
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

        try:
            mnemonic = decrypt_mnemonic(encrypted_data["ciphertext"], password, encrypted_data["salt"])
        except InvalidToken:
            return Response({"error": "Incorrect password. Decryption failed."}, status=403)

        public_key, _ = derive_evm_keypair(mnemonic)
        wallet = Wallet.objects.filter(public_key=public_key).first()
        if not wallet:
            return Response({"error": "No wallet found for decrypted mnemonic"}, status=404)

        request.session["wallet_access"] = {"method": "mnemonic", "public_key": public_key}
        request.session.modified = True

        return Response({"wallet": WalletSerializer(wallet).data, "mnemonic": mnemonic, "message": "Wallet restored from backup."})
    except Exception as e:
        logger.error(f"Restore wallet error: {str(e)}", exc_info=True)
        return Response({"error": str(e)}, status=500)


@csrf_exempt
@api_view(['POST'])
def set_backup_password(request):
    try:
        password = request.data.get("password")
        password_hint = request.data.get("password_hint", "")
        public_key = request.headers.get("X-Wallet-Key")

        if not password or not public_key:
            return Response({"error": "Missing password or wallet key"}, status=400)

        wallet = Wallet.objects.filter(public_key=public_key).first()
        if not wallet or not wallet.encryption_salt:
            return Response({"error": "Wallet not found or invalid"}, status=404)

        temporary_password = request.session.get("wallet_access", {}).get("temporary_password")
        if not temporary_password:
            return Response({"error": "Temporary password missing. Recreate wallet or reauthenticate."}, status=403)

        mnemonic = decrypt_mnemonic(wallet.encrypted_mnemonic, temporary_password, wallet.encryption_salt)
        encrypted = encrypt_mnemonic(mnemonic, password)
        encrypted_data = {"ciphertext": encrypted["ciphertext"], "salt": encrypted["salt"]}

        token_data = request.session.get('token')
        if not token_data:
            return Response({"error": "Google credentials missing"}, status=401)

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

        wallet.encrypted_mnemonic = encrypted["ciphertext"]
        wallet.encryption_salt = encrypted["salt"]
        wallet.backup_drive_file_id = uploaded_file.get("id")
        wallet.password_hint = password_hint
        wallet.save()

        return Response({"message": "Password set and wallet backup completed.", "file_id": wallet.backup_drive_file_id})
    except Exception as e:
        logger.error(f"Set backup password error: {str(e)}", exc_info=True)
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
def restore_wallet_session(request):
    return Response({"message": "restore_wallet_session endpoint placeholder"}, status=200)
