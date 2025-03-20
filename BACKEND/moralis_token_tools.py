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
WHALE_ALERT_API_KEY = os.getenv("WHALE_ALERT_API_KEY")
SOLANA_GATEWAY_URL = "https://solana-gateway.moralis.io"
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens"
WHALE_ALERT_URL = "https://api.whale-alert.io/v1/transactions"

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
TOKEN_CACHE = {}
CACHE_EXPIRY = 600  # 10 minutes

def clear_expired_cache():
    """Remove old cache entries."""
    current_time = time.time()
    expired_keys = [key for key, (_, timestamp) in TOKEN_CACHE.items() if current_time - timestamp > CACHE_EXPIRY]
    for key in expired_keys:
        del TOKEN_CACHE[key]

def make_request(url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None, cache_key: Optional[str] = None) -> Dict:
    """Make an API request with caching."""
    if cache_key and cache_key in TOKEN_CACHE:
        data, timestamp = TOKEN_CACHE[cache_key]
        if time.time() - timestamp < CACHE_EXPIRY:
            return data

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        if cache_key:
            TOKEN_CACHE[cache_key] = (result, time.time())
        time.sleep(RATE_LIMIT_DELAY)
        return result
    except requests.RequestException as e:
        logger.error(f"API Error: {str(e)}")
        return {"error": str(e)}

def get_unique_traders(token_address: str, network: str = "mainnet", limit: int = 50) -> int:
    """
    Fetch Unique Traders from the latest swaps (max 50).
    Avoids 1000s of API calls.

    Args:
        token_address (str): Solana token address.
        network (str, optional): Solana network (default: mainnet).
        limit (int, optional): Swap history depth (default: 50).

    Returns:
        int: Approximate number of Unique Traders.
    """
    unique_wallets = set()
    
    # Fetch latest swaps (LIMITED TO 50!)
    swaps_data = make_request(
        f"{SOLANA_GATEWAY_URL}/token/{network}/{token_address}/swaps",
        HEADERS, params={"limit": limit}, cache_key=f"swaps_{token_address}"
    )
    
    if "result" in swaps_data and swaps_data["result"]:
        for swap in swaps_data["result"]:
            if "walletAddress" in swap:
                unique_wallets.add(swap["walletAddress"])
    
    return len(unique_wallets)

def get_whale_transactions(min_value: int = 100000) -> list:
    """
    Fetch recent whale transactions (default: min $100k).
    
    Returns:
        list: List of whale transactions.
    """
    params = {
        "api_key": WHALE_ALERT_API_KEY,
        "min_value": min_value,
        "start": int(time.time()) - 3600  # Last hour
    }
    whale_data = make_request(WHALE_ALERT_URL, params=params, cache_key="whale_tx")
    
    if "transactions" in whale_data:
        return whale_data["transactions"]
    return []

@tool
def analyze_memecoin(token_address: str, network: str = "mainnet") -> Dict:
    """
    🚀 Optimized Memecoin Analysis (Minimal API Calls + Whale Tracking)

    Args:
        token_address (str): Solana Token Mint Address.
        network (str, optional): Solana network (default: mainnet).

    Returns:
        Dict: Token analysis result.
    """
    logger.info(f"Analyzing Token: {token_address}")
    clear_expired_cache()

    # === 1. Fetch Metadata (1 API Call) ===
    metadata = make_request(f"{SOLANA_GATEWAY_URL}/token/{network}/{token_address}/metadata", HEADERS, cache_key=f"metadata_{token_address}")
    name = metadata.get("name", "Unknown")
    symbol = metadata.get("symbol", "???")
    decimals = int(metadata.get("decimals", 9) or 9)
    total_supply = float(metadata.get("totalSupply", 0) or 0)

    # === 2. Fetch Price (1 API Call) ===
    price_data = make_request(f"{SOLANA_GATEWAY_URL}/token/{network}/{token_address}/price", HEADERS, cache_key=f"price_{token_address}")
    price = float(price_data.get("usdPrice", 0) or 0)
    price_change = float(price_data.get("usdPrice24hrPercentChange", 0) or 0)
    market_cap = (total_supply / (10 ** decimals)) * price if total_supply and decimals else 0

    # === 3. Fetch Liquidity & Volume (1 API Call) ===
    dex_data = make_request(f"{DEXSCREENER_API}/{token_address}", cache_key=f"dexscreener_{token_address}")
    liquidity = float(dex_data.get("pairs", [{}])[0].get("liquidity", {}).get("usd", 0))
    volume_24h = float(dex_data.get("pairs", [{}])[0].get("volume", {}).get("h24", 0))

    # === 4. Fetch Unique Traders (Reduced Calls) ===
    unique_traders = get_unique_traders(token_address, network)

    # === 5. Fetch Whale Transactions ===
    whale_transactions = get_whale_transactions()

    # === 6. Risk Assessment ===
    risk_score = 5.0
    risk_factors = []

    liquidity_threshold = max(5000, market_cap * 0.01) if market_cap > 0 else 5000
    volume_threshold = max(1000, market_cap * 0.005) if market_cap > 0 else 1000

    if liquidity < liquidity_threshold:
        risk_score -= 1.5
        risk_factors.append(f"🚨 Low Liquidity (${liquidity:,.2f})")
    if volume_24h < volume_threshold:
        risk_score -= 1.0
        risk_factors.append(f"🚨 Low Trading Volume (${volume_24h:,.2f})")
    if unique_traders < 30:
        risk_score -= 1.0
        risk_factors.append(f"🚨 Few Active Traders ({unique_traders})")

    risk_level = "HIGH" if risk_score < 3 else "MEDIUM" if risk_score < 4 else "LOW"

    # === 7. Output Optimized for Frontend ===
    return {
        "basicInfo": {"name": name, "symbol": symbol, "address": token_address},
        "marketData": {"price": f"${price:.6f}", "marketCap": f"${market_cap:,.2f}"},
        "liquidityAnalysis": {"totalLiquidity": f"${liquidity:,.2f}"},
        "whaleActivity": {"whaleTransactions": whale_transactions},
        "riskAssessment": {"level": risk_level, "factors": risk_factors}
    }
