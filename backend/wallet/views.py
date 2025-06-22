from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from users.models import GoogleUser
from drive.utils import get_user_info_from_session
from .models import Wallet
from .serializers import WalletSerializer
from .permissions import IsAuthenticatedWalletOwner
from .crypto import generate_mnemonic, derive_solana_keypair,encrypt_mnemonic,decrypt_mnemonic
from cryptography.fernet import InvalidToken


class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticatedWalletOwner]

    def get_queryset(self):
        try:
            # ✅ Google-authenticated session
            user_info = get_user_info_from_session(self.request)
            sub = user_info.get("sub")
            user = GoogleUser.objects.get(sub=sub)
            return Wallet.objects.filter(user=user)
        except Exception:
            pass

        # ✅ Mnemonic-authenticated session
        wallet_access = self.request.session.get("wallet_access")
        if wallet_access and wallet_access.get("method") == "mnemonic":
            return Wallet.objects.filter(public_key=wallet_access.get("public_key"))

        return Wallet.objects.none()

    def create(self, request, *args, **kwargs):
        try:
            user = None

            try:
                user_info = get_user_info_from_session(request)
                sub = user_info["sub"]
                email = user_info["email"]
                name = user_info.get("name", "")
                user, _ = GoogleUser.objects.get_or_create(
                    sub=sub, defaults={"email": email, "name": name}
                )
                if hasattr(user, "wallet"):
                    return Response({"error": "User already has a wallet."}, status=400)
            except Exception:
                pass  # Anonymous fallback

            mnemonic = generate_mnemonic()
            public_key, _ = derive_solana_keypair(mnemonic)

            wallet = Wallet.objects.create(
                public_key=public_key,
                wallet_name=request.data.get("wallet_name"),
                password_hint=request.data.get("password_hint"),
                user=user if user else None
            )

            request.session["wallet_access"] = {
                "method": "mnemonic",
                "public_key": public_key
            }   

            password = request.data.get("password") or "redrats_default"
            encrypted = encrypt_mnemonic(mnemonic, password)

            return Response({
                "wallet": WalletSerializer(wallet).data,
                "mnemonic": mnemonic,
                "encrypted_wallet_data": encrypted["ciphertext"],
                "encryption_salt": encrypted["salt"]
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=500)



@api_view(['GET'])
def my_wallet(request):
    try:
        try:
            user_info = get_user_info_from_session(request)
            sub = user_info.get("sub")
            user = GoogleUser.objects.get(sub=sub)
            wallet = user.wallet
            return Response(WalletSerializer(wallet).data)
        except Exception:
            pass

        wallet_access = request.session.get("wallet_access")
        if wallet_access and wallet_access.get("method") == "mnemonic":
            wallet = Wallet.objects.get(public_key=wallet_access["public_key"])
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

        try:
            wallet = Wallet.objects.get(public_key=public_key)
        except Wallet.DoesNotExist:
            return Response({"error": "No wallet found for this mnemonic"}, status=404)

        request.session["wallet_access"] = {
            "method": "mnemonic",
            "public_key": public_key
        }

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

        # 🔒 Try decrypting — catch wrong password errors
        try:
            mnemonic = decrypt_mnemonic(ciphertext, password, salt)
        except InvalidToken:
            return Response({"error": "Incorrect password. Decryption failed."}, status=403)

        public_key, _ = derive_solana_keypair(mnemonic)

        try:
            wallet = Wallet.objects.get(public_key=public_key)
        except Wallet.DoesNotExist:
            return Response({"error": "No wallet found for decrypted mnemonic"}, status=404)

        request.session["wallet_access"] = {
            "method": "mnemonic",
            "public_key": public_key
        }

        return Response({
            "wallet": WalletSerializer(wallet).data,
            "mnemonic": mnemonic,
            "message": "Wallet successfully restored from backup."
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)