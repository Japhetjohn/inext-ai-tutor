from web3 import Web3


INFURA_URL="https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider("INFURA_URL"))
contract_address = "TOKEN_CONTRACT_ADDRESS"
private_key = "PRIVATE_KEY"
account = "" #w3.eth.account.from_key(private_key)

# Simplified ERC-20 ABI (for transfer function)
token_abi = [
    {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
     "name": "transfer", "outputs": [], "type": "function"}
]

contract = w3.eth.contract(address=contract_address, abi=token_abi)

def verify_signature(wallet_address: str, signature: str, message: str):
    recovered = w3.eth.account.recover_message(message, signature=signature)
    return recovered.lower() == wallet_address.lower()

def send_tokens(to_address: str, amount: float):
    tx = contract.functions.transfer(to_address, int(amount * 10**18)).buildTransaction({
        'from': account.address,
        'nonce': w3.eth.getTransactionCount(account.address),
        'gas': 200000,
        'gasPrice': w3.eth.gas_price
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return w3.toHex(tx_hash)