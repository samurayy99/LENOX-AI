# moralis_token_tools.py
import os, logging, time, requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from langchain.tools import tool

# === CONFIG ===
load_dotenv()
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", "")
SOLANA_NETWORK = "mainnet"

HEADERS = {"Accept": "application/json", "X-API-Key": MORALIS_API_KEY}
BIRDEYE_HEADERS = {"Accept": "application/json", "X-API-Key": BIRDEYE_API_KEY if BIRDEYE_API_KEY else None}

MORALIS_BASE = "https://solana-gateway.moralis.io"
DEXSCREENER = "https://api.dexscreener.com/latest/dex"
BIRDEYE = "https://public-api.birdeye.so/public"
SOLSCAN_API = "https://api.solscan.io/token"
COINGECKO_API = "https://api.coingecko.com/api/v3"

# Token address hardcoded fallbacks for important tokens (used only as last resort)
TOKEN_FALLBACKS = {
    "wif": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
    "dogwifhat": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
    "bonk": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "sol": "So11111111111111111111111111111111111111112",
    "pyth": "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3",
    "jito": "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn",
    "wen": "WeNtZqavwxHXRkc1m7CR5r3MJ1YR5QMUyJ5fGmkrvJ6"
}

CACHE: Dict[str, tuple[Any, float]] = {}
CACHE_TTL = 600

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("moralis_token_tools")

# === UTILS ===
def _cache_get(key: str) -> Optional[Any]:
    if key in CACHE:
        data, ts = CACHE[key]
        if time.time() - ts < CACHE_TTL:
            return data
    return None

def _cache_set(key: str, data: Any) -> None:
    CACHE[key] = (data, time.time())

def _make_request(url: str, headers=None, params=None, cache_key=None) -> Dict[str, Any]:
    if cache_key:
        cached = _cache_get(cache_key)
        if cached:
            return cached
    try:
        # Only include headers that are not None
        effective_headers = {}
        if headers:
            effective_headers = {k: v for k, v in headers.items() if v is not None}
            
        res = requests.get(url, headers=effective_headers, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if cache_key:
                _cache_set(cache_key, data)
            return data
        logger.warning(f"API Error {res.status_code}: {res.text}")
    except Exception as e:
        logger.error(f"Request failed: {e}")
    return {}

# === TOKEN RESOLUTION STRATEGIES ===
def _birdeye_lookup(query: str) -> Optional[Dict[str, Any]]:
    """Look up token via Birdeye API."""
    query = query.strip().lower().lstrip("$")
    url = f"{BIRDEYE}/search/tokens"
    params = {"keyword": query}
    data = _make_request(url, headers=BIRDEYE_HEADERS, params=params, cache_key=f"birdeye_{query}")
    
    if data.get("success") and data.get("data", {}).get("tokens"):
        tokens = data["data"]["tokens"]
        if tokens:
            token = tokens[0]
            return {
                "tokenAddress": token.get("address"),
                "name": token.get("name"),
                "symbol": token.get("symbol"),
                "decimals": token.get("decimals"),
                "logo": token.get("logoURI")
            }
    return None

def _dexscreener_lookup(query: str) -> Optional[Dict[str, Any]]:
    """Look up token via DexScreener."""
    query = query.strip().lower().lstrip("$")
    url = f"{DEXSCREENER}/search"
    params = {"q": query}
    data = _make_request(url, params=params, cache_key=f"dexscreen_{query}")
    
    if data.get("pairs"):
        for pair in data["pairs"]:
            if pair.get("chainId") == "solana":
                token_data = pair.get("baseToken")
                if token_data and token_data.get("symbol", "").lower() == query:
                    return {
                        "tokenAddress": token_data.get("address"),
                        "name": token_data.get("name"),
                        "symbol": token_data.get("symbol")
                    }
    return None

def _coingecko_lookup(query: str) -> Optional[Dict[str, Any]]:
    """Look up token via CoinGecko."""
    query = query.strip().lower().lstrip("$")
    url = f"{COINGECKO_API}/coins/list"
    data = _make_request(url, cache_key="coingecko_list")
    
    if data and isinstance(data, list):
        for coin in data:
            if not isinstance(coin, dict):
                continue
                
            symbol = coin.get("symbol", "").lower()
            name = coin.get("name", "").lower()
            
            if symbol == query or query in name:
                coin_id = coin.get("id")
                if not coin_id:
                    continue
                    
                detail_url = f"{COINGECKO_API}/coins/{coin_id}"
                detail = _make_request(detail_url, cache_key=f"coingecko_{coin_id}")
                
                if not isinstance(detail, dict):
                    continue
                    
                platforms = detail.get("platforms", {})
                if not isinstance(platforms, dict):
                    continue
                    
                solana_address = platforms.get("solana")
                if solana_address:
                    return {
                        "tokenAddress": solana_address,
                        "name": coin.get("name", ""),
                        "symbol": coin.get("symbol", "").upper()
                    }
    return None

def _fallback_lookup(query: str) -> Optional[Dict[str, Any]]:
    """Last resort lookup from known hardcoded mappings."""
    query = query.strip().lower().lstrip("$")
    if query in TOKEN_FALLBACKS:
        address = TOKEN_FALLBACKS[query]
        return {
            "tokenAddress": address,
            "name": query.upper(),  # Placeholder
            "symbol": query.upper()  # Placeholder
        }
    return None

# === TOOLS ===
@tool
def get_token_metadata(token_address: str) -> Dict[str, Any]:
    """🧬 Fetch token metadata (name, symbol, decimals, total supply)."""
    url = f"{MORALIS_BASE}/token/{SOLANA_NETWORK}/{token_address}/metadata"
    data = _make_request(url, headers=HEADERS, cache_key=f"meta_{token_address}")
    if "name" in data:
        return data
        
    # Try to get metadata from birdeye
    fallback = _birdeye_lookup(token_address)
    if fallback:
        logger.info(f"Metadata via Birdeye for {token_address}")
        return {
            "name": fallback["name"],
            "symbol": fallback["symbol"],
            "decimals": str(fallback["decimals"]),
            "totalSupply": "0"
        }
        
    # Secondary fallback via DexScreener
    fallback2 = _dexscreener_lookup(token_address)
    if fallback2:
        logger.info(f"Metadata via DexScreener for {token_address}")
        return {
            "name": fallback2["name"],
            "symbol": fallback2["symbol"],
            "decimals": "9", # Default for most SPL tokens
            "totalSupply": "0"
        }
        
    return {}

@tool
def get_token_price(token_address: str) -> float:
    """💰 Fetch current token price in USD."""
    # Try Moralis first
    url = f"{MORALIS_BASE}/token/{SOLANA_NETWORK}/{token_address}/price"
    data = _make_request(url, headers=HEADERS, cache_key=f"price_{token_address}")
    price = float(data.get("usdPrice", 0))
    if price > 0:
        return price
        
    # Fallback to Birdeye
    fallback_url = f"{BIRDEYE}/token_price"
    params = {"address": token_address}
    data = _make_request(fallback_url, headers=BIRDEYE_HEADERS, params=params)
    birdeye_price = float(data.get("data", {}).get("value", 0.0))
    if birdeye_price > 0:
        return birdeye_price
        
    # Fallback to DexScreener
    dex_url = f"{DEXSCREENER}/tokens/{token_address}"
    dex_data = _make_request(dex_url, cache_key=f"dex_price_{token_address}")
    pairs = dex_data.get("pairs", [])
    if pairs:
        return float(pairs[0].get("priceUsd", 0))
        
    return 0.0

@tool
def get_token_holder_count(token_address: str) -> int:
    """👥 Get number of holders of a Solana token."""
    url = f"{MORALIS_BASE}/token/{SOLANA_NETWORK}/holders/{token_address}"
    data = _make_request(url, headers=HEADERS, cache_key=f"holders_{token_address}")
    return int(data.get("totalHolders", 0))

@tool
def get_token_dex_data(token_address: str) -> Dict[str, Any]:
    """📊 Get DEX liquidity & 24h volume."""
    url = f"{DEXSCREENER}/tokens/{token_address}"
    data = _make_request(url, cache_key=f"dex_{token_address}")
    pairs = data.get("pairs", [])
    if not pairs:
        return {
            "liquidity_usd": 0.0,
            "volume_usd": 0.0,
            "dex": "unknown"
        }
    
    pair = pairs[0]
    return {
        "liquidity_usd": float(pair.get("liquidity", {}).get("usd", 0)),
        "volume_usd": float(pair.get("volume", {}).get("h24", 0)),
        "dex": pair.get("dexId", "unknown")
    }

@tool
def get_token_marketcap(token_address: str) -> float:
    """🧮 Calculate marketcap = price × total supply."""
    meta = get_token_metadata(token_address)
    price = get_token_price(token_address)
    try:
        decimals = int(meta.get("decimals", 9))
        supply = float(meta.get("totalSupply", 0)) / (10 ** decimals)
        return price * supply
    except Exception as e:
        logger.error(f"Error calculating marketcap: {e}")
        return 0.0

@tool
def get_token_risk_score(token_address: str) -> Dict[str, Any]:
    """⚠️ Score token risk based on liquidity, volume, holders."""
    dex = get_token_dex_data(token_address)
    holders = get_token_holder_count(token_address)
    issues = []
    if dex["liquidity_usd"] < 5000:
        issues.append("Low liquidity")
    if dex["volume_usd"] < 1000:
        issues.append("Low trading volume")
    if holders < 50:
        issues.append("Low number of holders")
    level = "LOW" if not issues else "MEDIUM" if len(issues) == 1 else "HIGH"
    return {"level": level, "issues": issues or ["Healthy"]}

@tool
def analyze_token(token_identifier: str) -> Dict[str, Any]:
    """🔍 Full token analysis by symbol or address."""
    address = resolve_token_address(token_identifier)
    if not address:
        return {"error": f"Could not resolve token: {token_identifier}"}
        
    meta = get_token_metadata(address)
    price = get_token_price(address)
    holders = get_token_holder_count(address)
    dex = get_token_dex_data(address)
    marketcap = get_token_marketcap(address)
    risk = get_token_risk_score(address)

    return {
        "name": meta.get("name", "Unknown"),
        "symbol": meta.get("symbol", "???"),
        "address": address,
        "price_usd": format_price(price),
        "market_cap": f"${marketcap:,.0f}",
        "total_supply": meta.get("totalSupply", "0"),
        "liquidity_usd": f"${dex['liquidity_usd']:,.0f}",
        "volume_24h_usd": f"${dex['volume_usd']:,.0f}",
        "holders": holders,
        "dex": dex.get("dex", "unknown"),
        "risk_assessment": risk
    }

@tool
def resolve_token_address(query: str) -> Optional[str]:
    """🔎 Resolve token symbol or name to address."""
    if not query:
        return None
        
    # Clean up query
    query = query.strip().lower().lstrip("$")
    
    # If it's already an address (likely a base58 string)
    if len(query) > 30:
        return query
    
    # Try different resolution strategies in sequence
    for strategy in [_birdeye_lookup, _dexscreener_lookup, _coingecko_lookup, _fallback_lookup]:
        try:
            result = strategy(query)
            if result and result.get("tokenAddress"):
                logger.info(f"Resolved {query} to {result['tokenAddress']} via {strategy.__name__}")
                return result["tokenAddress"]
        except Exception as e:
            logger.error(f"Error in {strategy.__name__}: {e}")
    
    # If no resolution worked
    logger.warning(f"Failed to resolve token: {query}")
    return None

@tool
def search_token(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """🔎 Search for tokens using name or symbol."""
    if not query:
        return []
        
    query = query.strip().lower().lstrip("$")
    results = []
    
    # 1. Try Birdeye
    url = f"{BIRDEYE}/search/tokens"
    params = {"keyword": query}
    data = _make_request(url, headers=BIRDEYE_HEADERS, params=params, cache_key=f"birdeye_search_{query}")
    if data.get("success") and data.get("data", {}).get("tokens"):
        tokens = data["data"]["tokens"]
        for token in tokens[:limit]:
            results.append({
                "address": token.get("address"),
                "symbol": token.get("symbol"),
                "name": token.get("name"),
                "decimals": token.get("decimals"),
                "source": "Birdeye"
            })
        
    # 2. If no results, try DexScreener
    if not results:
        url = f"{DEXSCREENER}/search"
        params = {"q": query}
        data = _make_request(url, params=params, cache_key=f"dexscreen_search_{query}")
        if data.get("pairs"):
            for pair in data["pairs"][:limit]:
                if pair.get("chainId") == "solana":
                    token = pair.get("baseToken", {})
                    if token:
                        results.append({
                            "address": token.get("address"),
                            "symbol": token.get("symbol"),
                            "name": token.get("name"),
                            "source": "DexScreener"
                        })

    # 3. Last resort: check hardcoded fallbacks
    if not results:
        for symbol, address in TOKEN_FALLBACKS.items():
            if query in symbol or symbol in query:
                results.append({
                    "address": address,
                    "symbol": symbol.upper(),
                    "name": symbol.title(),
                    "source": "Fallback"
                })
                
    return results[:limit]

# Formatierung
def format_price(price: float) -> str:
    if price >= 1:
        return f"${price:.2f}"
    elif price >= 0.01:
        return f"${price:.4f}"
    elif price >= 0.00001:
        return f"${price:.6f}"
    return f"${price:.10f}".rstrip('0').rstrip('.')
