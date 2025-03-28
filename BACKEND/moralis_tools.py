# moralis_unified.py
import os, time, logging, requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from langchain.tools import tool

# === CONFIG ===
load_dotenv()
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", "")
SOLANA_NETWORK = "mainnet"

# API URLs
MORALIS_BASE = "https://solana-gateway.moralis.io"
DEXSCREENER = "https://api.dexscreener.com/latest/dex"
BIRDEYE = "https://public-api.birdeye.so/public"
SOLSCAN_API = "https://api.solscan.io/token"
COINGECKO_API = "https://api.coingecko.com/api/v3"
JUPAG_API = "https://price.jup.ag/v4"

# Common headers
HEADERS = {"Accept": "application/json", "X-API-Key": MORALIS_API_KEY}
BIRDEYE_HEADERS = {"Accept": "application/json", "X-API-Key": BIRDEYE_API_KEY if BIRDEYE_API_KEY else None}

# Token address fallbacks for important tokens (last resort)
TOKEN_FALLBACKS = {
    "wif": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
    "dogwifhat": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
    "bonk": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "sol": "So11111111111111111111111111111111111111112",
    "pyth": "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3",
    "jito": "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn",
    "wen": "WeNtZqavwxHXRkc1m7CR5r3MJ1YR5QMUyJ5fGmkrvJ6"
}

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("solana_tools")

# === CACHE SYSTEM ===
CACHE: Dict[str, tuple[Any, float]] = {}
CACHE_TTL = 600  # 10 minutes

def _cache_get(key: str) -> Optional[Any]:
    """Get data from cache if exists and not expired"""
    if key in CACHE:
        data, ts = CACHE[key]
        if time.time() - ts < CACHE_TTL:
            return data
    return None

def _cache_set(key: str, data: Any) -> None:
    """Store data in cache with timestamp"""
    CACHE[key] = (data, time.time())

def _clear_expired_cache():
    """Remove expired entries from cache"""
    now = time.time()
    expired = [k for k, (_, t) in CACHE.items() if now - t > CACHE_TTL]
    for k in expired:
        del CACHE[k]

def _make_request(url: str, headers=None, params=None, cache_key=None) -> Dict[str, Any]:
    """Make a request with proper error handling and caching"""
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

def _jupiter_lookup(query: str) -> Optional[Dict[str, Any]]:
    """Look up token via Jupiter API."""
    query = query.strip().lower().lstrip("$")
    url = f"{JUPAG_API}/price?ids={query}"
    data = _make_request(url, cache_key=f"jupiter_{query}")
    
    if data and data.get("data"):
        token_data = data["data"].get(query.upper())
        if token_data:
            # Jupiter doesn't give us token address directly
            # We can get the mint address if available
            return {
                "tokenAddress": token_data.get("id"),
                "name": query.upper(),
                "symbol": query.upper(),
                "price": token_data.get("price", 0)
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

@tool
def resolve_token_address(query: str) -> Optional[str]:
    """🔎 Resolve token symbol or name to Solana address."""
    if not query:
        return None
        
    # Clean up query
    query = query.strip().lower().lstrip("$")
    
    # If it's already an address (likely a base58 string)
    if len(query) > 30:
        return query
    
    # Try different resolution strategies in sequence
    for strategy in [_birdeye_lookup, _jupiter_lookup, _dexscreener_lookup, _coingecko_lookup, _fallback_lookup]:
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

# === TOKEN TOOLS ===
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
        
    # Fallback to Jupiter (often has best price data)
    try:
        jup_url = f"{JUPAG_API}/price?ids={token_address}"
        jup_data = _make_request(jup_url, cache_key=f"jup_price_{token_address}")
        jup_price = float(jup_data.get("data", {}).get(token_address, {}).get("price", 0))
        if jup_price > 0:
            return jup_price
    except Exception as e:
        logger.warning(f"Jupiter price lookup failed: {e}")
        
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
        "dex": pair.get("dexId", "unknown"),
        "pair_address": pair.get("pairAddress", ""),
        "price_change_24h": pair.get("priceChange", {}).get("h24", 0),
        "price_usd": pair.get("priceUsd", 0),
        "fdv": pair.get("fdv", 0)
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

def format_price(price: float) -> str:
    """Format price to readable string based on magnitude."""
    if price == 0:
        return "$0.00"
    elif price < 0.000001:
        return f"${price:.10f}"
    elif price < 0.0001:
        return f"${price:.8f}"
    elif price < 0.01:
        return f"${price:.6f}"
    elif price < 1:
        return f"${price:.4f}"
    elif price < 1000:
        return f"${price:.2f}"
    else:
        return f"${price:,.2f}"

@tool
def get_token_risk_score(token_address: str) -> Dict[str, Any]:
    """⚠️ Score token risk based on liquidity, volume, holders."""
    dex = get_token_dex_data(token_address)
    holders = get_token_holder_count(token_address)
    
    # Enhanced risk scoring with more factors
    issues = []
    risk_score = 0  # 0 = lowest risk, 100 = highest risk
    
    # Liquidity checks
    liquidity = dex["liquidity_usd"]
    if liquidity < 1000:
        issues.append("⚠️ CRITICAL: Extremely low liquidity (<$1k)")
        risk_score += 40
    elif liquidity < 10000:
        issues.append("⚠️ HIGH RISK: Very low liquidity (<$10k)")
        risk_score += 30
    elif liquidity < 50000:
        issues.append("⚠️ CAUTION: Low liquidity (<$50k)")
        risk_score += 15
    elif liquidity < 100000:
        issues.append("⚠️ NOTE: Moderate liquidity (<$100k)")
        risk_score += 5
    
    # Volume checks
    volume = dex["volume_usd"]
    if volume < 500:
        issues.append("⚠️ Very low trading volume")
        risk_score += 20
    elif volume < 5000:
        issues.append("⚠️ Low trading volume")
        risk_score += 10
    
    # Holders
    if holders < 10:
        issues.append("⚠️ CRITICAL: Few holders (<10)")
        risk_score += 25
    elif holders < 50:
        issues.append("⚠️ HIGH RISK: Low holder count (<50)")
        risk_score += 15
    elif holders < 200:
        issues.append("⚠️ Limited holder base (<200)")
        risk_score += 5
    
    # Risk level based on accumulated score
    level = "LOW"
    if risk_score > 20:
        level = "MEDIUM"
    if risk_score > 40:
        level = "HIGH" 
    if risk_score > 60:
        level = "VERY HIGH"
    if risk_score > 80:
        level = "EXTREME"
    
    # Add positive signals if not risky
    if not issues:
        issues = ["✅ Healthy liquidity", "✅ Good trading volume", "✅ Distributed holder base"]
    
    return {
        "level": level, 
        "risk_score": risk_score,
        "issues": issues,
        "details": {
            "liquidity": liquidity,
            "volume_24h": volume,
            "holders": holders
        }
    }

@tool
def analyze_token(token_identifier: str) -> Dict[str, Any]:
    """🔍 Full token analysis by symbol or address with actionable insights."""
    address = resolve_token_address(token_identifier)
    if not address:
        return {"error": f"Could not resolve token: {token_identifier}"}
        
    meta = get_token_metadata(address)
    price = get_token_price(address)
    holders = get_token_holder_count(address)
    dex = get_token_dex_data(address)
    marketcap = get_token_marketcap(address)
    risk = get_token_risk_score(address)
    
    # Calculate additional metrics
    liquidity_mcap_ratio = 0
    if marketcap > 0:
        liquidity_mcap_ratio = dex['liquidity_usd'] / marketcap
    
    # Volume to liquidity ratio as indicator of potential price movement
    vol_liq_ratio = 0
    if dex['liquidity_usd'] > 0:
        vol_liq_ratio = dex['volume_usd'] / dex['liquidity_usd']
    
    # Generate actionable insights
    insights = []
    
    # Liquidity/marketcap insights
    if liquidity_mcap_ratio < 0.03 and marketcap > 1000000:
        insights.append("⚠️ Low liquidity relative to market cap suggests vulnerability to price manipulation")
    elif liquidity_mcap_ratio > 0.3:
        insights.append("✅ High liquidity/marketcap ratio indicates strong market support")
    
    # Volume analysis
    if vol_liq_ratio > 2:
        insights.append("🔥 Very high volume/liquidity ratio suggests significant market interest and potential volatility")
    elif vol_liq_ratio > 0.5:
        insights.append("📈 Healthy trading volume relative to liquidity")
    elif vol_liq_ratio < 0.1:
        insights.append("⚠️ Low trading volume relative to liquidity may indicate limited interest")
    
    # Price change analysis
    price_change = float(dex.get("price_change_24h", 0))
    if price_change > 20:
        insights.append(f"🚀 Strong upward momentum with {price_change:.1f}% 24h price increase")
    elif price_change < -20:
        insights.append(f"📉 Significant price drop of {abs(price_change):.1f}% in 24h")
    
    # Holder analysis
    if holders > 1000:
        insights.append("👥 Well-distributed among >1000 holders, reducing concentration risk")
    
    if not insights:
        insights.append("📊 No notable patterns detected in current market metrics")

    return {
        "name": meta.get("name", "Unknown"),
        "symbol": meta.get("symbol", "???"),
        "address": address,
        "price_usd": format_price(price),
        "price_change_24h": f"{float(dex.get('price_change_24h', 0)):.1f}%",
        "market_cap": f"${marketcap:,.0f}",
        "total_supply": meta.get("totalSupply", "0"),
        "liquidity_usd": f"${dex['liquidity_usd']:,.0f}",
        "volume_24h_usd": f"${dex['volume_usd']:,.0f}",
        "vol_liq_ratio": f"{vol_liq_ratio:.2f}",
        "holders": holders,
        "dex": dex.get("dex", "unknown"),
        "risk_assessment": risk,
        "insights": insights,
        "urls": {
            "dexscreener": f"https://dexscreener.com/solana/{dex.get('pair_address', address)}",
            "birdeye": f"https://birdeye.so/token/{address}?chain=solana",
            "solscan": f"https://solscan.io/token/{address}"
        }
    }

# === WALLET TOOLS ===
@tool
def get_sol_balance(wallet: str) -> float:
    """💰 Fetch SOL balance of a wallet."""
    network = "mainnet"  # Always use mainnet for now
    url = f"{MORALIS_BASE}/account/{network}/{wallet}/balance"
    data = _make_request(url, headers=HEADERS, cache_key=f"sol_{wallet}")
    
    # Check for error response
    if isinstance(data, dict) and "error" in data:
        logger.warning(f"Error getting SOL balance for {wallet}: {data['error']}")
        return 0.0
    
    # Safe conversion to float with error handling
    try:
        return float(data.get("solana", 0))
    except (TypeError, ValueError) as e:
        logger.warning(f"Error parsing SOL balance for {wallet}: {e}")
        return 0.0

@tool
def get_spl_tokens(wallet: str) -> List[Dict[str, Any]]:
    """🪙 Fetch SPL tokens held by a wallet."""
    network = "mainnet"  # Always use mainnet for now
    url = f"{MORALIS_BASE}/account/{network}/{wallet}/tokens"
    data = _make_request(url, headers=HEADERS, cache_key=f"tokens_{wallet}")
    
    # Enhanced error handling and logging
    if isinstance(data, dict) and "error" in data:
        logger.warning(f"Error fetching SPL tokens for {wallet}: {data['error']}")
        return []
    
    # Check if API returns a list directly (older API version)
    if isinstance(data, list):
        logger.info(f"SPL tokens for {wallet}: {len(data)} found (direct list format)")
        return data
    
    # Standard case: data in dictionary with result key
    if isinstance(data, dict):
        tokens = data.get("result", [])
        if isinstance(tokens, list):
            logger.info(f"SPL tokens for {wallet}: {len(tokens)} found")
            return tokens
        else:
            logger.warning(f"Unexpected format for SPL tokens in result field: {type(tokens)}")
    else:
        logger.warning(f"Unexpected API response format for SPL tokens: {type(data)}")
    
    return []

@tool
def get_wallet_nfts(wallet: str, limit: int = 10) -> List[Dict[str, Any]]:
    """🎨 Get NFTs from wallet.
    
    Args:
        wallet: The wallet address to check
        limit: Maximum number of NFTs to return (default: 10)
    """
    network = "mainnet"  # Always use mainnet for now
    url = f"{MORALIS_BASE}/account/{network}/{wallet}/nft"
    params = {"limit": str(limit)}
    data = _make_request(url, headers=HEADERS, params=params, cache_key=f"nfts_{wallet}_{limit}")
    
    if isinstance(data, dict) and "error" in data:
        logger.warning(f"Error getting NFTs for {wallet}: {data['error']}")
        return []
    
    if isinstance(data, dict) and "result" in data:
        return data.get("result", [])
    
    return []

@tool
def get_wallet_trading_stats(wallet: str) -> Dict[str, Any]:
    """📊 Analyze wallet's trading patterns and performance."""
    # Direkt implementieren statt Tool-Aufruf mit Parametern
    network = "mainnet"  # Always use mainnet for now
    url = f"{MORALIS_BASE}/account/{network}/{wallet}/swaps"
    params = {"limit": "25"}  # Direkt im URL-Parameter setzen
    data = _make_request(url, headers=HEADERS, params=params, cache_key=f"swaps_{wallet}_25")
    
    # Swaps aus API-Antwort extrahieren
    swaps = []
    if isinstance(data, dict) and "result" in data:
        swaps = data.get("result", [])
    
    # Initialize stats
    stats = {
        "total_swaps": len(swaps),
        "buys": 0,
        "sells": 0,
        "unique_tokens_traded": set(),
        "volume_usd": 0.0,
        "largest_swap_usd": 0.0,
        "favorite_dex": {},
        "recent_activity": [],
        "most_traded_token": {"symbol": "None", "count": 0}
    }
    
    # Process swaps for insights
    token_trade_counts = {}
    dex_counts = {}
    
    for swap in swaps:
        # Count buys vs sells
        direction = swap.get("direction", "")
        if direction == "in":
            stats["buys"] += 1
        elif direction == "out":
            stats["sells"] += 1
            
        # Track unique tokens
        token_address = swap.get("tokenAddress", "")
        token_symbol = swap.get("tokenSymbol", "Unknown")
        if token_address:
            stats["unique_tokens_traded"].add(token_address)
            
            # Count trades per token
            key = token_symbol if token_symbol != "Unknown" else token_address
            token_trade_counts[key] = token_trade_counts.get(key, 0) + 1
            
        # Track volume
        usd_value = float(swap.get("usdValue", 0))
        stats["volume_usd"] += usd_value
        stats["largest_swap_usd"] = max(stats["largest_swap_usd"], usd_value)
        
        # Track DEXes used
        dex = swap.get("exchange", "Unknown")
        dex_counts[dex] = dex_counts.get(dex, 0) + 1
        
        # Recent activity for timeline
        stats["recent_activity"].append({
            "time": swap.get("blockTimestamp", ""),
            "action": "Buy" if direction == "in" else "Sell",
            "token": token_symbol,
            "amount_usd": usd_value
        })
    
    # Find most used DEX
    if dex_counts:
        favorite_dex = max(dex_counts.items(), key=lambda x: x[1])
        stats["favorite_dex"] = {"name": favorite_dex[0], "count": favorite_dex[1]}
    
    # Find most traded token
    if token_trade_counts:
        most_traded = max(token_trade_counts.items(), key=lambda x: x[1])
        stats["most_traded_token"] = {"symbol": most_traded[0], "count": most_traded[1]}
    
    # Calculate additional derived metrics
    if stats["buys"] + stats["sells"] > 0:
        stats["buy_sell_ratio"] = stats["buys"] / max(1, stats["sells"])
        stats["avg_swap_size_usd"] = stats["volume_usd"] / len(swaps) if swaps else 0
    
    return stats

@tool
def get_wallet_portfolio_allocation(wallet: str) -> Dict[str, Any]:
    """📊 Get detailed portfolio breakdown with allocation percentages."""
    # Get SOL balance and tokens
    sol_balance = get_sol_balance(wallet)
    tokens = get_spl_tokens(wallet)
    
    # Get current SOL price
    sol_price = 150.0  # Default fallback
    try:
        price_url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
        price_data = requests.get(price_url, timeout=5).json()
        if price_data and "solana" in price_data:
            sol_price = float(price_data["solana"]["usd"])
    except Exception:
        pass
    
    # Calculate SOL value and create allocation entry
    sol_value = sol_balance * sol_price
    
    # Process token holdings
    holdings = []
    total_value = sol_value
    
    for token in tokens:
        if not isinstance(token, dict):
            continue
            
        # Get token data
        symbol = token.get("symbol", "Unknown")
        name = token.get("name", symbol)
        address = token.get("tokenAddress", "")
        
        # Calculate token amount
        amount = float(token.get("amount", 0))
        decimals = int(token.get("decimals", 9))
        if decimals > 0:
            amount = amount / (10 ** decimals)
        
        # Get token price
        price = float(token.get("usdPrice", 0))
        
        # Calculate value
        value = amount * price
        total_value += value
        
        # Only include tokens with non-zero value
        if value > 0.01:
            holdings.append({
                "symbol": symbol,
                "name": name,
                "address": address,
                "amount": amount,
                "price_usd": price,
                "value_usd": value
            })
    
    # Add SOL to holdings
    holdings.append({
        "symbol": "SOL",
        "name": "Solana",
        "address": "So11111111111111111111111111111111111111112",
        "amount": sol_balance,
        "price_usd": sol_price,
        "value_usd": sol_value
    })
    
    # Sort by value (highest first)
    holdings.sort(key=lambda x: x["value_usd"], reverse=True)
    
    # Calculate percentages
    if total_value > 0:
        for h in holdings:
            h["allocation_percent"] = (h["value_usd"] / total_value) * 100
    
    # Create summary
    return {
        "total_value_usd": total_value,
        "asset_count": len(holdings),
        "holdings": holdings,
        "largest_holding": holdings[0]["symbol"] if holdings else "None",
        "largest_allocation_percent": holdings[0]["allocation_percent"] if holdings else 0
    }

@tool
def get_wallet_risk_score(wallet: str) -> Dict[str, Any]:
    """🧠 Calculate wallet risk score and provide insights."""
    # Get key wallet data
    sol = get_sol_balance(wallet)
    tokens = get_spl_tokens(wallet)
    
    # Swaps direkt abrufen
    network = "mainnet"
    url = f"{MORALIS_BASE}/account/{network}/{wallet}/swaps"
    params = {"limit": "5"}  # Geringe Anzahl für Risikobewertung
    swaps_data = _make_request(url, headers=HEADERS, params=params, cache_key=f"swaps_{wallet}_risk")
    swaps = []
    if isinstance(swaps_data, dict) and "result" in swaps_data:
        swaps = swaps_data.get("result", [])
        
    # Portfoliowert berechnen
    portfolio = get_portfolio_value(wallet)

    # Start with neutral risk level
    risk_score = 50  # 0-100 scale, higher = riskier
    signals = []  # Risk signals or insights
    
    # === SOL Balance Analysis ===
    if sol == 0:
        risk_score += 20
        signals.append("⚠️ No SOL balance (unable to pay transaction fees)")
    elif sol < 0.01:
        risk_score += 10
        signals.append("⚠️ Very low SOL balance (<0.01)")
    elif sol > 100:
        risk_score -= 10
        signals.append("✅ Large SOL position (>100)")
    
    # === Token Analysis ===
    if not tokens:
        risk_score += 10
        signals.append("⚠️ No tokens found")
    elif len(tokens) > 20:
        risk_score += 5
        signals.append("⚠️ Large number of different tokens (possibly airdrop collector)")
    
    # === Activity Analysis ===
    if not swaps:
        risk_score += 10
        signals.append("⚠️ No recent swap activity")
    else:
        # Calculate buy/sell ratio
        buys = sum(1 for s in swaps if s.get("direction") == "in")
        sells = sum(1 for s in swaps if s.get("direction") == "out")
        
        if buys > 0 and sells == 0:
            risk_score -= 5
            signals.append("✅ Only buying, no selling (accumulation pattern)")
        elif sells > buys * 2:
            risk_score += 15
            signals.append("⚠️ Heavy selling activity (distribution pattern)")
    
    # === Portfolio Value Analysis ===
    if portfolio < 10:
        risk_score += 15
        signals.append("⚠️ Very low portfolio value (<$10)")
    elif portfolio > 10000:
        risk_score -= 15
        signals.append("✅ Substantial portfolio value (>$10,000)")
    
    # === NFT Analysis ===
    # NFTs direkt abrufen
    url = f"{MORALIS_BASE}/account/{network}/{wallet}/nft"
    params = {"limit": "3"}  # Geringe Anzahl für Risikobewertung
    nfts_data = _make_request(url, headers=HEADERS, params=params, cache_key=f"nfts_{wallet}_risk")
    nfts = []
    if isinstance(nfts_data, dict) and "result" in nfts_data:
        nfts = nfts_data.get("result", [])
        
    if nfts:
        risk_score -= 5
        signals.append("✅ Holds NFTs (suggests longer-term ecosystem participant)")
    
    # === Age/History Analysis ===
    # This would require more complex on-chain analysis, simplified here
    
    # Final risk level determination
    level = "MEDIUM"  # Default
    if risk_score < 30:
        level = "LOW"
    elif risk_score < 50:
        level = "MODERATE"
    elif risk_score > 70:
        level = "HIGH"
    elif risk_score > 85:
        level = "VERY HIGH"
    
    # If no negative signals, add general positive one
    if not signals:
        signals.append("✅ No significant risk factors detected")
    
    return {
        "score": risk_score,
        "level": level,
        "signals": signals,
        "details": {
            "sol_balance": sol,
            "token_count": len(tokens),
            "recent_swaps": len(swaps),
            "portfolio_value_usd": portfolio
        }
    }

@tool
def get_recent_swaps(wallet: str, limit: int = 5) -> List[Dict[str, Any]]:
    """🔁 Get recent swaps (Raydium/Jupiter etc).
    
    Args:
        wallet: The wallet address to check
        limit: Maximum number of swaps to return (default: 5)
    """
    network = "mainnet"  # Always use mainnet for now
    url = f"{MORALIS_BASE}/account/{network}/{wallet}/swaps"
    params = {"limit": str(limit)}
    data = _make_request(url, headers=HEADERS, params=params, cache_key=f"swaps_{wallet}_{limit}")
    
    if isinstance(data, dict) and "error" in data:
        logger.warning(f"Error getting swaps for {wallet}: {data['error']}")
        return []
    
    if isinstance(data, dict) and "result" in data:
        return data.get("result", [])
    
    return []

@tool
def get_portfolio_value(wallet: str) -> float:
    """💸 Get total portfolio value in USD."""
    # First check SOL value
    sol_balance = get_sol_balance(wallet)
    
    # Get SOL price (hardcoded fallback if needed)
    sol_price = 150.0  # Default fallback price
    try:
        # Use public API to get real SOL price 
        price_url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
        price_data = requests.get(price_url, timeout=5).json()
        if price_data and "solana" in price_data:
            sol_price = float(price_data["solana"]["usd"])
    except Exception as e:
        logger.warning(f"Error getting SOL price, using fallback: {e}")
    
    # Calculate SOL value
    sol_value = sol_balance * sol_price
    
    # Try to get token values from Moralis
    tokens_value = 0.0
    tokens = get_spl_tokens(wallet)
            
    for token in tokens:
        if isinstance(token, dict):
            # Try to get price either from usdPrice or price fields
            price = token.get("usdPrice", 0)
            if not price:
                price = token.get("price", 0)
            
            # Get amount and adjust for decimals
            amount = float(token.get("amount", 0))
            decimals = int(token.get("decimals", 9))
            if decimals > 0:
                amount = amount / (10 ** decimals)
            
            # Add to total value
            token_value = amount * float(price)
            tokens_value += token_value
    
    # Return total portfolio value
    total_value = sol_value + tokens_value
    return total_value

@tool
def get_wallet_overview(wallet: str) -> Dict[str, Any]:
    """📊 Comprehensive wallet overview with risk assessment and insights."""
    try:
        # Basic data
        sol_balance = get_sol_balance(wallet)
        tokens = get_spl_tokens(wallet)
        
        # NFTs direkt abrufen, ohne parameter
        network = "mainnet"
        url = f"{MORALIS_BASE}/account/{network}/{wallet}/nft"
        params = {"limit": "3"}  # Kleine Anzahl für Übersicht
        nfts_data = _make_request(url, headers=HEADERS, params=params, cache_key=f"nfts_{wallet}_overview")
        nfts = []
        if isinstance(nfts_data, dict) and "result" in nfts_data:
            nfts = nfts_data.get("result", [])
            
        # Swaps direkt abrufen
        url = f"{MORALIS_BASE}/account/{network}/{wallet}/swaps"
        params = {"limit": "5"}  # Nur neueste für Übersicht
        swaps_data = _make_request(url, headers=HEADERS, params=params, cache_key=f"swaps_{wallet}_overview")
        swaps = []
        if isinstance(swaps_data, dict) and "result" in swaps_data:
            swaps = swaps_data.get("result", [])
        
        # Advanced data
        portfolio_value = get_portfolio_value(wallet)
        risk = get_wallet_risk_score(wallet)
        trading_stats = get_wallet_trading_stats(wallet)
        
        # Extract key insights
        insights = []
        
        # Activity pattern insights
        if trading_stats["buys"] > 0 and trading_stats["sells"] == 0:
            insights.append("🔍 Pure accumulation pattern - buying only, no selling")
        elif trading_stats.get("buy_sell_ratio", 0) > 2:
            insights.append(f"📈 Strong net buyer with {trading_stats.get('buy_sell_ratio', 0):.1f} buy/sell ratio")
        elif trading_stats["sells"] > trading_stats["buys"] * 2:
            insights.append("📉 Heavy distribution pattern - primarily selling")
        
        # Recent activity insights
        if trading_stats["total_swaps"] > 10:
            insights.append(f"🔄 Very active trader with {trading_stats['total_swaps']} recent swaps")
        elif trading_stats["total_swaps"] == 0:
            insights.append("💤 Inactive - no recent trading activity")
        
        # Volume insights
        if trading_stats["volume_usd"] > 10000:
            insights.append(f"💰 High trading volume: ${trading_stats['volume_usd']:,.2f}")
        
        # If no insights generated
        if not insights:
            insights.append("📊 Regular wallet activity, no unusual patterns detected")
        
        return {
            "sol_balance": f"{sol_balance:.4f} SOL",
            "token_count": len(tokens),
            "nft_count": len(nfts),
            "recent_swaps": len(swaps),
            "portfolio_usd": f"${portfolio_value:,.2f}",
            "risk": risk,
            "favorite_dex": trading_stats.get("favorite_dex", {}).get("name", "Unknown"),
            "buy_sell_ratio": trading_stats.get("buy_sell_ratio", 0),
            "insights": insights,
            "explorers": {
                "Solscan": f"https://solscan.io/account/{wallet}",
                "Birdeye": f"https://birdeye.so/address/{wallet}",
                "GMGN": f"https://gmgn.ai/explorer/wallet-details?address={wallet}"
            }
        }
    except Exception as e:
        logger.error(f"Error generating wallet overview: {e}")
        return {
            "error": f"Failed to generate complete overview: {str(e)}",
            "sol_balance": f"{get_sol_balance(wallet):.4f} SOL",
            "explorers": {
                "Solscan": f"https://solscan.io/account/{wallet}",
                "Birdeye": f"https://birdeye.so/address/{wallet}",
                "GMGN": f"https://gmgn.ai/explorer/wallet-details?address={wallet}"
            }
        }

# === ADVANCED ANALYTICS TOOLS ===

@tool
def analyze_wallet_transactions(wallet: str) -> Dict[str, Any]:
    """🔎 Deep analysis of wallet transaction patterns and behavior."""
    # Get trading stats - direkt implementiert statt Tool-Aufruf
    trading = get_wallet_trading_stats(wallet)
    risk = get_wallet_risk_score(wallet)
    
    # Swaps direkt abrufen
    network = "mainnet"
    url = f"{MORALIS_BASE}/account/{network}/{wallet}/swaps"
    params = {"limit": "25"}
    data = _make_request(url, headers=HEADERS, params=params, cache_key=f"swaps_{wallet}_25")
    swaps = []
    if isinstance(data, dict) and "result" in data:
        swaps = data.get("result", [])
    
    # Initialize pattern analysis
    patterns = {
        "trading_style": "Unknown",
        "token_preference": "Unknown",
        "transaction_timing": "Unknown",
        "risk_profile": "Unknown",
        "notable_behaviors": []
    }
    
    # Determine trading style
    if trading.get("buys", 0) > 0 and trading.get("sells", 0) == 0:
        patterns["trading_style"] = "Pure Accumulator"
        patterns["notable_behaviors"].append("Only purchases tokens, never sells")
    elif trading.get("buys", 0) == 0 and trading.get("sells", 0) > 0:
        patterns["trading_style"] = "Pure Distributor"
        patterns["notable_behaviors"].append("Only sells tokens, never buys")
    elif trading.get("buys", 0) > trading.get("sells", 0) * 2:
        patterns["trading_style"] = "Net Buyer"
        patterns["notable_behaviors"].append(f"Strong buying bias ({trading.get('buy_sell_ratio', 0):.1f}x more buys than sells)")
    elif trading.get("sells", 0) > trading.get("buys", 0) * 2:
        patterns["trading_style"] = "Net Seller"
        patterns["notable_behaviors"].append("Primarily selling tokens")
    elif abs(trading.get("buys", 0) - trading.get("sells", 0)) <= 2:
        patterns["trading_style"] = "Balanced Trader"
        patterns["notable_behaviors"].append("Roughly equal buys and sells")
    
    # Token preference analysis
    unique_tokens = len(trading.get("unique_tokens_traded", set()))
    if unique_tokens > 15:
        patterns["token_preference"] = "Diverse Trader"
        patterns["notable_behaviors"].append(f"Trades many different tokens ({unique_tokens})")
    elif unique_tokens < 3 and unique_tokens > 0:
        patterns["token_preference"] = "Focused Trader"
        patterns["notable_behaviors"].append(f"Focuses on just {unique_tokens} tokens")
    
    # Transaction timing and frequency
    if len(swaps) >= 10:
        # Convert timestamps and check frequency
        timestamps = []
        for swap in swaps:
            try:
                ts = swap.get("blockTimestamp", "")
                if ts:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    timestamps.append(dt)
            except Exception:
                continue
        
        if timestamps:
            timestamps.sort()
            # Check for clustering in time
            if len(timestamps) >= 3:
                clusters = []
                current_cluster = [timestamps[0]]
                
                for i in range(1, len(timestamps)):
                    time_diff = (timestamps[i] - timestamps[i-1]).total_seconds()
                    if time_diff < 300:  # 5 minutes
                        current_cluster.append(timestamps[i])
                    else:
                        if len(current_cluster) > 1:
                            clusters.append(current_cluster)
                        current_cluster = [timestamps[i]]
                
                if len(current_cluster) > 1:
                    clusters.append(current_cluster)
                
                if clusters:
                    patterns["transaction_timing"] = "Batch Trader"
                    largest_cluster = max(clusters, key=len)
                    patterns["notable_behaviors"].append(f"Makes batch transactions ({len(largest_cluster)} trades in quick succession)")
                else:
                    patterns["transaction_timing"] = "Methodical Trader"
                    patterns["notable_behaviors"].append("Spaces out transactions over time")
    
    # Risk profile determination
    risk_score = risk.get("score", 50)
    if risk_score < 30:
        patterns["risk_profile"] = "Conservative"
    elif risk_score < 50:
        patterns["risk_profile"] = "Moderate"
    elif risk_score < 75:
        patterns["risk_profile"] = "Aggressive"
    else:
        patterns["risk_profile"] = "Very Aggressive"
    
    # Check for specific behaviors
    avg_swap_size = trading.get("avg_swap_size_usd", 0)
    if avg_swap_size > 10000:
        patterns["notable_behaviors"].append(f"Large transaction size (avg ${avg_swap_size:,.2f})")
    
    # Final results
    return {
        "wallet": wallet,
        "transaction_count": len(swaps),
        "patterns": patterns,
        "insights": {
            "likely_purpose": _determine_wallet_purpose(patterns, trading, risk),
            "experience_level": _estimate_experience_level(patterns, trading, risk),
            "suggested_tags": _suggest_wallet_tags(patterns, trading, risk)
        }
    }

def _determine_wallet_purpose(patterns, trading, risk):
    """Determine the likely purpose of a wallet based on its patterns."""
    style = patterns.get("trading_style", "")
    behaviors = patterns.get("notable_behaviors", [])
    
    if "Pure Accumulator" in style:
        return "Long-term holding/investment"
    elif "Pure Distributor" in style:
        return "Distribution wallet or exit position"
    elif "Batch Trader" in patterns.get("transaction_timing", ""):
        return "Potentially automated trading or bot"
    elif trading.get("total_swaps", 0) > 15:
        return "Active trading account"
    elif any("only purchases" in b.lower() for b in behaviors):
        return "Accumulation wallet"
    else:
        return "General purpose wallet"

def _estimate_experience_level(patterns, trading, risk):
    """Estimate the experience level of the wallet owner."""
    # Various heuristics to determine experience
    
    # More experienced traders might show these patterns
    experienced_signals = 0
    
    if trading.get("total_swaps", 0) > 20:
        experienced_signals += 1
    
    if patterns.get("trading_style", "") in ["Balanced Trader", "Net Buyer"]:
        experienced_signals += 1
    
    if patterns.get("transaction_timing", "") == "Batch Trader":
        experienced_signals += 2  # Strong signal of sophistication
    
    if trading.get("avg_swap_size_usd", 0) > 5000:
        experienced_signals += 1
    
    if len(trading.get("unique_tokens_traded", set())) > 10:
        experienced_signals += 1
    
    # Determine level
    if experienced_signals >= 4:
        return "Expert"
    elif experienced_signals >= 2:
        return "Experienced"
    elif experienced_signals >= 1:
        return "Intermediate"
    else:
        return "Beginner"

def _suggest_wallet_tags(patterns, trading, risk):
    """Suggest appropriate tags for the wallet based on behavior."""
    tags = []
    
    # Trading style tags
    style = patterns.get("trading_style", "")
    if "Accumulator" in style:
        tags.append("Accumulator")
    elif "Distributor" in style:
        tags.append("Distributor")
    elif "Balanced" in style:
        tags.append("Trader")
    
    # Risk profile tags
    risk_profile = patterns.get("risk_profile", "")
    if risk_profile == "Very Aggressive":
        tags.append("Risk Taker")
    elif risk_profile == "Conservative":
        tags.append("Conservative")
    
    # Behavior-based tags
    if patterns.get("transaction_timing", "") == "Batch Trader":
        tags.append("Bot-like")
    
    if trading.get("avg_swap_size_usd", 0) > 10000:
        tags.append("Whale")
    elif trading.get("avg_swap_size_usd", 0) > 1000:
        tags.append("Large Trader")
    
    # Activity level
    if trading.get("total_swaps", 0) > 20:
        tags.append("Very Active")
    elif trading.get("total_swaps", 0) < 5:
        tags.append("Low Activity")
    
    return tags

@tool
def compare_wallets(wallets: str) -> Dict[str, Any]:
    """🔄 Compare multiple wallets to identify relationships and patterns.
    
    Args:
        wallets: Comma-separated list of wallet addresses to compare
    """
    # Parse wallet addresses
    wallet_list = [w.strip() for w in wallets.split(",")]
    
    if len(wallet_list) < 2:
        return {"error": "Please provide at least two wallet addresses to compare"}
    
    if len(wallet_list) > 5:
        return {"error": "Maximum 5 wallets can be compared at once to avoid rate limits"}
    
    # Collect data for each wallet
    wallet_data = {}
    
    for wallet in wallet_list:
        try:
            # Get basic info
            sol = get_sol_balance(wallet)
            tokens = get_spl_tokens(wallet)
            swaps = get_wallet_trading_stats(wallet)
            risk = get_wallet_risk_score(wallet)
            
            # Create wallet profile
            token_set = set()
            for t in tokens:
                if isinstance(t, dict) and "tokenAddress" in t:
                    token_set.add(t["tokenAddress"])
            
            # Store wallet data
            wallet_data[wallet] = {
                "sol_balance": sol,
                "token_count": len(tokens),
                "tokens_held": token_set,
                "swap_count": len(swaps),
                "risk_score": risk.get("score", 50),
                "risk_level": risk.get("level", "MEDIUM")
            }
        except Exception as e:
            logger.error(f"Error processing wallet {wallet}: {e}")
            wallet_data[wallet] = {"error": str(e)}
    
    # Find similarities and connections
    comparison = {
        "wallets_compared": len(wallet_data),
        "similar_risk_profiles": [],
        "similar_portfolios": [],
        "token_overlap": {},
        "sol_balance_summary": {},
        "activity_comparison": {},
        "possible_relationships": []
    }
    
    # Compare risk profiles
    risk_groups = {}
    for wallet, data in wallet_data.items():
        if "risk_level" in data:
            level = data["risk_level"]
            if level not in risk_groups:
                risk_groups[level] = []
            risk_groups[level].append(wallet)
    
    for level, wallets in risk_groups.items():
        if len(wallets) > 1:
            comparison["similar_risk_profiles"].append({
                "risk_level": level,
                "wallets": wallets
            })
    
    # Compare token portfolios
    for i, (wallet1, data1) in enumerate(wallet_data.items()):
        for wallet2, data2 in list(wallet_data.items())[i+1:]:
            if "tokens_held" in data1 and "tokens_held" in data2:
                tokens1 = data1["tokens_held"]
                tokens2 = data2["tokens_held"]
                
                # Find overlap
                common_tokens = tokens1.intersection(tokens2)
                
                if common_tokens:
                    similarity = len(common_tokens) / max(1, min(len(tokens1), len(tokens2)))
                    
                    # Only report if significant overlap
                    if similarity > 0.3 or len(common_tokens) >= 3:
                        comparison["similar_portfolios"].append({
                            "wallet_pair": [wallet1, wallet2],
                            "common_token_count": len(common_tokens),
                            "similarity_score": f"{similarity:.2f}",
                            "relationship": "Strong" if similarity > 0.7 else "Moderate" if similarity > 0.5 else "Weak"
                        })
    
    # Add SOL balance summary
    sol_balances = [(w, d["sol_balance"]) for w, d in wallet_data.items() if "sol_balance" in d]
    sol_balances.sort(key=lambda x: x[1], reverse=True)
    
    comparison["sol_balance_summary"] = {
        "highest": {"wallet": sol_balances[0][0], "balance": sol_balances[0][1]} if sol_balances else {},
        "lowest": {"wallet": sol_balances[-1][0], "balance": sol_balances[-1][1]} if sol_balances else {},
        "total_sol": sum(b for _, b in sol_balances)
    }
    
    # Activity comparison
    activity_levels = {"high": [], "medium": [], "low": []}
    for wallet, data in wallet_data.items():
        if "swap_count" in data:
            if data["swap_count"] > 10:
                activity_levels["high"].append(wallet)
            elif data["swap_count"] > 5:
                activity_levels["medium"].append(wallet)
            else:
                activity_levels["low"].append(wallet)
    
    comparison["activity_comparison"] = activity_levels
    
    # Identify possible relationships between wallets
    for level, relationship_type in [
        (0.8, "Likely same owner/Strong relationship"),
        (0.6, "Possible relationship"),
        (0.4, "Weak relationship")
    ]:
        for pair in comparison["similar_portfolios"]:
            if float(pair["similarity_score"]) >= level:
                comparison["possible_relationships"].append({
                    "wallets": pair["wallet_pair"],
                    "relationship_type": relationship_type,
                    "confidence": f"{float(pair['similarity_score'])*100:.0f}%",
                    "evidence": f"Share {pair['common_token_count']} common tokens"
                })
    
    return comparison

@tool
def get_token_holders_analysis(token_address: str, limit: int = 10) -> Dict[str, Any]:
    """👥 Analyze top holders of a token for insights on distribution.
    
    Args:
        token_address: Token address or symbol to analyze
        limit: Maximum number of top holders to analyze (default: 10)
    """
    # Resolve token address if symbol is provided
    if len(token_address) < 30:
        resolved = resolve_token_address(token_address)
        if not resolved:
            return {"error": f"Could not resolve token: {token_address}"}
        token_address = resolved
    
    # Get token metadata
    meta = get_token_metadata(token_address)
    if not meta:
        return {"error": f"Could not get metadata for token: {token_address}"}
    
    # This would require a more advanced API, which Moralis doesn't directly provide
    # For production, you would need to use a service like Solscan, Birdeye or your own RPC
    # For demo purposes, we'll create a placeholder response
    
    return {
        "token": {
            "name": meta.get("name", "Unknown"),
            "symbol": meta.get("symbol", "???"),
            "address": token_address
        },
        "holders_count": get_token_holder_count(token_address),
        "distribution_analysis": {
            "concentration_risk": "Unknown - Advanced API required",
            "top_holder_percentage": "Unknown - Advanced API required",
            "holders_chart_url": f"https://birdeye.so/token/{token_address}?chain=solana&view=holders"
        },
        "note": "For detailed holder analysis, please check the provided Birdeye URL"
    } 