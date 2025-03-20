import os
import requests
import logging
import time
from typing import Dict, Optional
from dotenv import load_dotenv
from langchain.tools import tool

# Load API Keys
load_dotenv()
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
SOLANA_GATEWAY_URL = "https://solana-gateway.moralis.io"

# Rate-Limit Optimized
RATE_LIMIT_DELAY = 0.2  # Keep low to save credits

# Logger Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Headers
HEADERS = {
    "Accept": "application/json",
    "X-API-Key": MORALIS_API_KEY
}

# Cache to prevent excessive API calls
WALLET_CACHE = {}
CACHE_EXPIRY = 600  # 10 minutes

def clear_expired_cache():
    """Remove old cache entries."""
    current_time = time.time()
    expired_keys = [key for key, (_, timestamp) in WALLET_CACHE.items() if current_time - timestamp > CACHE_EXPIRY]
    for key in expired_keys:
        del WALLET_CACHE[key]

def make_request(url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None, cache_key: Optional[str] = None) -> Dict:
    """Make an API request with caching."""
    if cache_key and cache_key in WALLET_CACHE:
        data, timestamp = WALLET_CACHE[cache_key]
        if time.time() - timestamp < CACHE_EXPIRY:
            return data

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        if cache_key:
            WALLET_CACHE[cache_key] = (result, time.time())
        time.sleep(RATE_LIMIT_DELAY)
        return result
    except requests.RequestException as e:
        logger.error(f"API Error: {str(e)}")
        return {"error": str(e)}

@tool
def analyze_wallet(wallet_address: str, network: str = "mainnet") -> Dict:
    """
    🚀 Optimized Wallet Analysis (Minimal API Calls)
    
    Args:
        wallet_address (str): Solana Wallet Address.
        network (str, optional): Solana network (default: mainnet).
    
    Returns:
        Dict: Wallet analysis result.
    """
    logger.info(f"Analyzing Wallet: {wallet_address}")
    clear_expired_cache()

    # === 1. Fetch SOL Balance (1 API Call) ===
    sol_balance = make_request(
        f"{SOLANA_GATEWAY_URL}/account/{network}/{wallet_address}/balance",
        HEADERS, cache_key=f"balance_{wallet_address}"
    )
    sol_amount = float(sol_balance.get("solana", 0))

    # === 2. Fetch SPL Tokens (1 API Call) ===
    tokens_data = make_request(
        f"{SOLANA_GATEWAY_URL}/account/{network}/{wallet_address}/tokens",
        HEADERS, cache_key=f"tokens_{wallet_address}"
    )
    token_count = len(tokens_data) if isinstance(tokens_data, list) else 0

    # === 3. Fetch Portfolio (1 API Call) ===
    portfolio_data = make_request(
        f"{SOLANA_GATEWAY_URL}/account/{network}/{wallet_address}/portfolio",
        HEADERS, cache_key=f"portfolio_{wallet_address}"
    )
    token_values = portfolio_data.get("tokens", [])
    
    # === 4. Fetch NFTs (Limited API Calls) ===
    nft_data = make_request(
        f"{SOLANA_GATEWAY_URL}/account/{network}/{wallet_address}/nft",
        HEADERS, params={"limit": 10}, cache_key=f"nfts_{wallet_address}"
    )
    nft_count = len(nft_data) if isinstance(nft_data, list) else 0

    # === 5. Fetch Wallet Activity (1 API Call) ===
    swaps_data = make_request(
        f"{SOLANA_GATEWAY_URL}/account/{network}/{wallet_address}/swaps",
        HEADERS, params={"limit": 5}, cache_key=f"swaps_{wallet_address}"
    )
    swap_count = len(swaps_data.get("result", [])) if "result" in swaps_data else 0

    # === 6. Risk Assessment ===
    risk_score = 5.0
    risk_factors = []

    if sol_amount == 0:
        risk_score -= 1.5
        risk_factors.append("🚨 No SOL balance detected (Possible inactive wallet)")
    if token_count == 0:
        risk_score -= 1.0
        risk_factors.append("🚨 No SPL tokens found")
    if swap_count == 0:
        risk_score -= 1.0
        risk_factors.append("🚨 No recent trading activity")

    risk_level = "HIGH" if risk_score < 3 else "MEDIUM" if risk_score < 4 else "LOW"

    # === 7. Output Optimized for Frontend ===
    return {
        "walletInfo": {
        "address": wallet_address,
            "network": network
        },
        "solanaBalance": f"{sol_amount:.2f} SOL",
        "tokenHoldings": {
            "tokenCount": token_count,
            "portfolio": token_values
        },
        "nftHoldings": {
            "nftCount": nft_count
        },
        "activity": {
            "recentSwaps": swap_count
        },
        "riskAssessment": {
            "level": risk_level,
            "factors": "<br>".join(risk_factors) if risk_factors else "No Risk Factors Detected"
        }
    }