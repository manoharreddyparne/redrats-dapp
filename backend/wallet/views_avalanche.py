# wallet/views_avalanche.py
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from wallet.models import Wallet
from wallet.crypto import decrypt_mnemonic, derive_avalanche_keypair
from wallet.utils import get_wallet_private_key, send_transaction, send_erc20, call_contract
from drive.utils import get_user_info_from_session

logger = logging.getLogger(__name__)


def get_wallet_from_request(request):
    """
    Helper to fetch Wallet object based on session or GoogleUser.
    """
    try:
        # 1️⃣ Try Google session
        user_info = get_user_info_from_session(request)
        sub = user_info.get("sub")
        wallet = Wallet.objects.filter(user__sub=sub).first()
        if wallet:
            return wallet
    except Exception as e:
        logger.debug(f"Google session wallet fetch failed: {str(e)}")

    # 2️⃣ Try mnemonic session
    wallet_access = request.session.get("wallet_access")
    if wallet_access and wallet_access.get("method") == "mnemonic":
        wallet = Wallet.objects.filter(public_key=wallet_access.get("public_key")).first()
        if wallet:
            return wallet

    return None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_avax(request):
    wallet = get_wallet_from_request(request)
    if not wallet:
        return Response({"error": "Wallet not found or access denied"}, status=403)

    to_address = request.data.get("to_address")
    amount_avax = float(request.data.get("amount_avax", 0))
    if not to_address or amount_avax <= 0:
        return Response({"error": "Missing or invalid to_address or amount_avax"}, status=400)

    mnemonic = decrypt_mnemonic(wallet.encrypted_mnemonic, request.session.get("wallet_access", {}).get("temporary_password") or "dummy", wallet.encryption_salt)
    private_key = get_wallet_private_key(mnemonic)
    tx_hash = send_transaction(private_key, to_address, amount_avax)

    return Response({"tx_hash": tx_hash})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_token(request):
    wallet = get_wallet_from_request(request)
    if not wallet:
        return Response({"error": "Wallet not found or access denied"}, status=403)

    token_address = request.data.get("token_address")
    to_address = request.data.get("to_address")
    amount = float(request.data.get("amount", 0))

    if not token_address or not to_address or amount <= 0:
        return Response({"error": "Missing or invalid parameters"}, status=400)

    mnemonic = decrypt_mnemonic(wallet.encrypted_mnemonic, request.session.get("wallet_access", {}).get("temporary_password") or "dummy", wallet.encryption_salt)
    private_key = get_wallet_private_key(mnemonic)
    tx_hash = send_erc20(private_key, token_address, to_address, amount)

    return Response({"tx_hash": tx_hash})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def contract_call(request):
    wallet = get_wallet_from_request(request)
    if not wallet:
        return Response({"error": "Wallet not found or access denied"}, status=403)

    contract_address = request.data.get("contract_address")
    abi = request.data.get("abi")
    function_name = request.data.get("function_name")
    args = request.data.get("args", [])
    value_ether = float(request.data.get("value_ether", 0))

    if not contract_address or not abi or not function_name:
        return Response({"error": "Missing parameters"}, status=400)

    mnemonic = decrypt_mnemonic(wallet.encrypted_mnemonic, request.session.get("wallet_access", {}).get("temporary_password") or "dummy", wallet.encryption_salt)
    private_key = get_wallet_private_key(mnemonic)
    tx_hash = call_contract(private_key, contract_address, abi, function_name, args, value_ether)

    return Response({"tx_hash": tx_hash})
