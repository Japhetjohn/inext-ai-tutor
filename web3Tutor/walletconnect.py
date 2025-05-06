import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pywalletconnect import WCClient, WCClientInvalidOption
from web3 import Web3
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Sonic config
SONIC_RPC_URL = os.getenv("SONIC_RPC_URL", "https://rpc.soniclabs.com")
SONIC_CHAIN_ID = "146"
WALLETCONNECT_PROJECT_ID = os.getenv("WALLETCONNECT_PROJECT_ID")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
TOKEN_CONTRACT_ADDRESS = os.getenv("TOKEN_CONTRACT_ADDRESS")

# Web3 setup
w3 = Web3(Web3.HTTPProvider(SONIC_RPC_URL))
if not w3.is_connected():
    raise Exception("Cannot connect to Sonic RPC")
account = w3.eth.account.from_key(PRIVATE_KEY)

# ERC-20 ABI (your simplified version)
token_abi = [
    {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
     "name": "transfer", "outputs": [], "type": "function"}
]
contract = w3.eth.contract(address=TOKEN_CONTRACT_ADDRESS, abi=token_abi)

# WalletConnect metadata
WALLET_METADATA = {
    "name": "Aquacoinx",
    "description": "Aquacoinx backend on Sonic",
    "url": "https://aquacoinx.com",
    "icons": ["https://aquacoinx.com/icon.png"]
}

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AquacoinxBackend")

# FastAPI app
app = FastAPI(title="Aquacoinx WalletConnect Backend")

# Models
class ConnectResponse(BaseModel):
    uri: str

class TokenRequest(BaseModel):
    to_address: str
    amount: float
    wallet_address: str
    signature: str
    message: str

# Session store (use Redis in production)
sessions = {}

def verify_signature(wallet_address: str, signature: str, message: str) -> bool:
    """Verify a signature matches the wallet address."""
    try:
        recovered = w3.eth.account.recover_message(message, signature=signature)
        return recovered.lower() == wallet_address.lower()
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False

def send_tokens(to_address: str, amount: float) -> str:
    """Send tokens using the backend account."""
    try:
        tx = contract.functions.transfer(to_address, int(amount * 10**18)).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 200000,
            'gasPrice': w3.eth.gas_price
        })
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return w3.to_hex(tx_hash)
    except Exception as e:
        logger.error(f"Token send failed: {e}")
        raise

async def handle_wallet_session(wc_client: WCClient):
    """Handle WalletConnect session asynchronously."""
    try:
        req_id, chain_ids, request_info = wc_client.open_session()
        if SONIC_CHAIN_ID not in chain_ids:
            wc_client.close()
            raise ValueError("Sonic chain ID not supported")
        
        # Approve session with backend account (for demo; adjust for user wallet in prod)
        wc_client.reply_session_request(req_id, SONIC_CHAIN_ID, account.address)
        logger.info(f"Session established with {request_info['name']}")
        sessions[wc_client.wc_uri] = wc_client

        while True:
            message = wc_client.get_message()
            if message:
                logger.info(f"Received: {message}")
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Session error: {e}")
        wc_client.close()
        raise

@app.get("/connect", response_model=ConnectResponse)
async def connect_wallet():
    """Generate WalletConnect URI."""
    try:
        WCClient.set_wallet_metadata(WALLET_METADATA)
        WCClient.set_project_id(WALLETCONNECT_PROJECT_ID)

        uri = f"wc:{os.urandom(16).hex()}@2?projectId={WALLETCONNECT_PROJECT_ID}&relay-url=wss://relay.walletconnect.com"
        wc_client = WCClient.from_wc_uri(uri)

        asyncio.create_task(handle_wallet_session(wc_client))
        logger.info(f"Generated URI: {uri}")
        return {"uri": uri}
    except Exception as e:
        logger.error(f"Connect error: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate connection")

@app.post("/send-tokens")
async def send_tokens_endpoint(request: TokenRequest):
    """Send tokens after verifying signature."""
    if request.wallet_address not in [account.address]:  # Replace with real session check
        if not verify_signature(request.wallet_address, request.signature, request.message):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        tx_hash = send_tokens(request.to_address, request.amount)
        logger.info(f"Tokens sent: {tx_hash}")
        return {"tx_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token transfer failed: {str(e)}")

@app.on_event("shutdown")
async def cleanup():
    for wc_client in sessions.values():
        wc_client.close()
    logger.info("Sessions closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)