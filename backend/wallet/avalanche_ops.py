from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from web3 import Web3
from wallet.utils import decrypt_mnemonic, get_wallet_private_key  # helper functions

# Connect to Avalanche C-Chain RPC
w3 = Web3(Web3.HTTPProvider(settings.AVALANCHE_RPC_URL))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_avax(request):
    """
    Send AVAX from user's wallet to another address
    """
    user = request.user
    to_address = request.data.get("to_address")
    amount_avax = request.data.get("amount_avax")

    if not to_address or not amount_avax:
        return Response({"error": "Missing to_address or amount_avax"}, status=400)

    # Retrieve encrypted mnemonic from user's wallet
    encrypted_mnemonic = user.wallet.encrypted_mnemonic
    mnemonic = decrypt_mnemonic(encrypted_mnemonic)

    # Generate private key (helper)
    private_key = get_wallet_private_key(mnemonic)

    # Get sender address
    sender_address = w3.eth.account.from_key(private_key).address

    # Build transaction
    tx = {
        "from": sender_address,
        "to": to_address,
        "value": w3.to_wei(amount_avax, "ether"),
        "gas": 21000,
        "gasPrice": w3.to_wei("225", "gwei"),
        "nonce": w3.eth.get_transaction_count(sender_address),
        "chainId": settings.AVALANCHE_CHAIN_ID
    }

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    return Response({"tx_hash": tx_hash.hex()})
