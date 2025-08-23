# wallet/utils.py
from web3 import Web3
from bip_utils import Bip44, Bip44Coins, Bip44Changes, Bip39SeedGenerator
from Crypto.Cipher import AES
import base64
from django.conf import settings

# Connect to Avalanche RPC
w3 = Web3(Web3.HTTPProvider(settings.AVALANCHE_RPC_URL))

def decrypt_mnemonic(encrypted_text: str) -> str:
    """
    Decrypt mnemonic using AES key
    """
    key = settings.MNEMONIC_ENCRYPTION_KEY.encode()
    cipher = AES.new(key, AES.MODE_EAX)
    decoded = base64.b64decode(encrypted_text)
    # ⚠ production: store nonce separately!
    return cipher.decrypt(decoded).decode()

def get_wallet_private_key(mnemonic: str) -> str:
    """
    Derive private key from mnemonic using BIP44 for AVAX C-Chain
    """
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.AVALANCHE_C_CHAIN)
    bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXTERNAL).AddressIndex(0)
    return bip44_acc_ctx.PrivateKey().Raw().ToHex()

def send_transaction(private_key: str, to: str, value_ether: float, gas: int = 21000, gas_price_gwei: int = 225):
    sender_address = w3.eth.account.from_key(private_key).address
    tx = {
        "from": sender_address,
        "to": to,
        "value": w3.to_wei(value_ether, "ether"),
        "gas": gas,
        "gasPrice": w3.to_wei(gas_price_gwei, "gwei"),
        "nonce": w3.eth.get_transaction_count(sender_address),
        "chainId": settings.AVALANCHE_CHAIN_ID
    }
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash.hex()

def send_erc20(private_key: str, token_address: str, to: str, amount_tokens: float, decimals: int = 18):
    sender_address = w3.eth.account.from_key(private_key).address
    contract = w3.eth.contract(address=token_address, abi=[
        {
            "constant": False,
            "inputs": [{"name": "_to","type": "address"},{"name": "_value","type":"uint256"}],
            "name": "transfer",
            "outputs": [{"name":"","type":"bool"}],
            "type":"function"
        }
    ])
    tx = contract.functions.transfer(to, int(amount_tokens * (10 ** decimals))).buildTransaction({
        "from": sender_address,
        "gas": 100000,
        "gasPrice": w3.to_wei(225, "gwei"),
        "nonce": w3.eth.get_transaction_count(sender_address),
        "chainId": settings.AVALANCHE_CHAIN_ID
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash.hex()

def call_contract(private_key: str, contract_address: str, abi: list, function_name: str, args: list, value_ether: float = 0):
    sender_address = w3.eth.account.from_key(private_key).address
    contract = w3.eth.contract(address=contract_address, abi=abi)
    func = contract.get_function_by_name(function_name)(*args)
    tx = func.buildTransaction({
        "from": sender_address,
        "value": w3.to_wei(value_ether, "ether"),
        "gas": 300000,
        "gasPrice": w3.to_wei(225, "gwei"),
        "nonce": w3.eth.get_transaction_count(sender_address),
        "chainId": settings.AVALANCHE_CHAIN_ID
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash.hex()
