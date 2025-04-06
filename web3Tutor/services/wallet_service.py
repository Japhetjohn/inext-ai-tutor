
from web3 import Web3
from eth_account.messages import encode_defunct
from typing import Optional

class WalletService:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR-PROJECT-ID'))
    
    def verify_signature(self, message: str, signature: str, address: str) -> bool:
        message_hash = encode_defunct(text=message)
        recovered_address = self.w3.eth.account.recover_message(message_hash, signature=signature)
        return recovered_address.lower() == address.lower()

    async def get_balance(self, address: str) -> Optional[float]:
        try:
            balance = self.w3.eth.get_balance(address)
            return float(self.w3.from_wei(balance, 'ether'))
        except Exception as e:
            print(f"Error getting balance: {e}")
            return None
