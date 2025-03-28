# dexscreener_tools.py
import time
import logging
import requests
import json
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv
from langchain.tools import tool

# === CONFIG ===
load_dotenv()
BASE_URL = "https://api.dexscreener.com/latest/dex"

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dexscreener_tools")

# === CACHE SYSTEM ===
CACHE: Dict[str, tuple[Any, float]] = {}
CACHE_TTL = 300  # 5 minutes

# Chain IDs mapping
CHAIN_IDS = {
    "solana": "solana",
    "sol": "solana",
    "ethereum": "ethereum",
    "eth": "ethereum",
    "bsc": "bsc",
    "binance": "bsc",
    "polygon": "polygon",
    "matic": "polygon",
    "arbitrum": "arbitrum",
    "avalanche": "avalanche",
    "avax": "avalanche",
    "fantom": "fantom",
    "ftm": "fantom",
    "optimism": "optimism",
    "base": "base",
    "sui": "sui"
}

# === HELPER FUNCTIONS ===
def _cache_get(key: str) -> Any:
    """Get data from cache if exists and not expired"""
    if key in CACHE:
        data, ts = CACHE[key]
        if time.time() - ts < CACHE_TTL:
            logger.debug(f"Cache hit for {key}")
            return data
    return None

def _cache_set(key: str, data: Any) -> None:
    """Store data in cache with timestamp"""
    CACHE[key] = (data, time.time())

def _parse_args(args: str, expected_args: Optional[List[str]] = None, defaults: Optional[Dict[str, Any]] = None) -> Union[List[str], Dict[str, Any]]:
    """
    Parse space-separated arguments into either a list or a dictionary.
    
    Args:
        args: Space-separated string of arguments
        expected_args: List of expected argument names
        defaults: Dictionary of default values for expected arguments
        
    Returns:
        Either a list of arguments (if expected_args is None) or a dictionary mapping
        argument names to values
    """
    args_list = args.split()
    
    # If no expected args, just return the split list
    if expected_args is None:
        return args_list
        
    # Otherwise, map the args to the expected names
    result: Dict[str, Any] = {}
    if defaults is not None:
        result.update(defaults)
        
    for i, arg_name in enumerate(expected_args):
        if i < len(args_list):
            # Try to convert to appropriate types
            arg_value = args_list[i]
            try:
                # Try as int
                if arg_value.isdigit():
                    result[arg_name] = int(arg_value)
                # Try as float
                elif arg_value.replace('.', '', 1).isdigit():
                    result[arg_name] = float(arg_value)
                else:
                    result[arg_name] = arg_value
            except (ValueError, AttributeError):
                result[arg_name] = arg_value
    
    return result

def _make_request(url: str, params: Optional[Dict[str, Any]] = None, cache_key: Optional[str] = None) -> Dict[str, Any]:
    """Make API request with caching and error handling"""
    if cache_key:
        cached = _cache_get(cache_key)
        if cached:
            return cached
    
    try:
        logger.debug(f"Making request to {url} with params {params}")
        # Include user agent to be a good citizen
        headers = {
            "User-Agent": "Dr-Degen-Assistant/1.0.0",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 429:
            logger.warning("Hit rate limit from DexScreener API")
            return {"error": "Rate limit exceeded. Please try again in a minute."}
        
        response.raise_for_status()
        data = response.json()
        
        if cache_key:
            _cache_set(cache_key, data)
            
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return {"error": f"Request failed: {str(e)}"}
    except ValueError as e:
        logger.error(f"JSON parsing error: {e}")
        return {"error": f"Failed to parse response: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": f"Unexpected error: {str(e)}"}

def _normalize_chain_id(chain: str) -> str:
    """Normalize chain ID input to DexScreener format"""
    chain = chain.lower().strip()
    return CHAIN_IDS.get(chain, chain)

def _extract_pairs_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract and normalize pairs data from API response"""
    if not data or "pairs" not in data:
        return []
    
    pairs = data.get("pairs", [])
    if not isinstance(pairs, list):
        return []
    
    return pairs

def _calculate_buy_sell_ratio(txns: Dict[str, Any], timeframe: str = "h24") -> float:
    """Calculate buy/sell ratio from transaction data"""
    if not txns or timeframe not in txns:
        return 1.0
    
    tf_data = txns.get(timeframe, {})
    buys = tf_data.get("buys", 0)
    sells = tf_data.get("sells", 0)
    
    if sells == 0:
        return float(buys) if buys > 0 else 1.0
    
    return buys / sells

def _get_volume_liquidity_ratio(pair: Dict[str, Any]) -> float:
    """Calculate volume to liquidity ratio (useful for detecting wash trading)"""
    volume = pair.get("volume", {}).get("h24", 0)
    liquidity = pair.get("liquidity", {}).get("usd", 0)
    
    if liquidity == 0:
        return 0
    
    return volume / liquidity

def _clean_token_address(address: str) -> str:
    """Clean token address by removing $ prefix and trimming"""
    address = address.strip()
    if address.startswith('$'):
        address = address[1:]
    return address

def _find_token_by_search(query: str) -> Dict[str, Any]:
    """Use search API to find token by name, symbol, or partial address"""
    # Strip spaces first to handle whitespace properly
    clean_query = query.strip()
    
    # Remove any '$' prefix from token symbols
    if clean_query.startswith('$'):
        clean_query = clean_query[1:]
    
    if not clean_query:
        clean_query = "token"  # Default to generic token search
    
    logger.info(f"Searching for token using '{clean_query}' as search term")
    
    # Use a generic approach without hardcoding specific tokens
    # Try multiple search patterns to increase chances of finding the correct token
    search_terms = [
        clean_query,                    # Direct search
        f"{clean_query} token",         # Add "token" suffix
        clean_query.replace(" ", "")    # No spaces version
    ]
    
    all_pairs = []
    for term in search_terms:
        search_data = _make_request(f"{BASE_URL}/search", {"q": term})
        
        if "error" in search_data:
            continue
        
        pairs = _extract_pairs_data(search_data)
        if pairs:
            all_pairs.extend(pairs)
    
    if not all_pairs:
        return {"error": f"No token found for query: {query}"}
    
    # Find exact symbol matches first
    exact_matches = []
    for pair in all_pairs:
        base_token = pair.get("baseToken", {})
        symbol = base_token.get("symbol", "").lower()
        name = base_token.get("name", "").lower() 
        
        # Try to match against symbol or name (exact match, case insensitive)
        query_lower = clean_query.lower()
        if query_lower == symbol.lower() or query_lower == name.lower():
            exact_matches.append(pair)
    
    # If we have exact matches, use those. Otherwise use all pairs.
    pairs_to_use = exact_matches if exact_matches else all_pairs
    
    # Sort by liquidity for most reliable result
    pairs_to_use.sort(key=lambda p: p.get("liquidity", {}).get("usd", 0), reverse=True)
    selected_pair = pairs_to_use[0]
    base_token = selected_pair.get("baseToken", {})
    
    match_type = "exact match" if exact_matches else "related match"
    logger.info(f"Found {match_type} for {clean_query}: {base_token.get('name', 'Unknown')} ({base_token.get('symbol', 'Unknown')})")
    
    return {
        "pairs": [selected_pair],
        "token_address": base_token.get("address", ""),
        "token_name": base_token.get("name", ""),
        "token_symbol": base_token.get("symbol", "")
    }

# === TOOLS ===
@tool
def get_dex_liquidity_distribution(token_address: str) -> List[Dict[str, Any]]:
    """📊 Analyze how a token's liquidity is distributed across different DEXes.
    
    Args:
        token_address: The token address to analyze
        
    Returns:
        List of DEX liquidity pools with details on distribution
    """
    # Clean and normalize the token address
    token_address = _clean_token_address(token_address)
    
    # Try to find the token by search if it isn't a standard address format
    if not (token_address.startswith("0x") or len(token_address) >= 32):
        search_result = _find_token_by_search(token_address)
        if "error" in search_result:
            return [{"error": search_result["error"]}]
        token_address = search_result.get("token_address", token_address)
    
    cache_key = f"dex_liquidity_{token_address}"
    cached_data = _cache_get(cache_key)
    if cached_data:
        return cached_data
    
    url = f"{BASE_URL}/tokens/{token_address}"
    data = _make_request(url)
    
    if "error" in data:
        return [{"error": data["error"]}]
    
    pairs = _extract_pairs_data(data)
    if not pairs:
        # Try a different approach - search by token name/symbol
        search_result = _find_token_by_search(token_address)
        if "error" in search_result:
            return [{"error": f"No liquidity pools found for token {token_address}"}]
        
        # Extract pairs directly from search result
        if "pairs" in search_result and search_result["pairs"]:
            pairs = search_result["pairs"]
        else:
            return [{"error": f"No liquidity pools found for token {token_address}"}]
    
    # Group and analyze by DEX
    dex_data = {}
    total_liquidity = 0
    
    for pair in pairs:
        dex_id = pair.get("dexId", "unknown")
        liquidity = pair.get("liquidity", {}).get("usd", 0)
        total_liquidity += liquidity
        
        if dex_id not in dex_data:
            dex_data[dex_id] = {
                "dex": dex_id,
                "liquidity_usd": 0,
                "pools": 0,
                "volume_24h": 0
            }
        
        dex_entry = dex_data[dex_id]
        dex_entry["liquidity_usd"] += liquidity
        dex_entry["pools"] += 1
        dex_entry["volume_24h"] += pair.get("volume", {}).get("h24", 0)
    
    # Convert to list and calculate percentages
    result = []
    for dex_id, data in dex_data.items():
        percentage = (data["liquidity_usd"] / total_liquidity * 100) if total_liquidity > 0 else 0
        result.append({
            "dex": dex_id,
            "liquidity_usd": data["liquidity_usd"],
            "percentage": round(percentage, 2),
            "pools": data["pools"],
            "volume_24h": data["volume_24h"]
        })
    
    # Sort by liquidity (highest first)
    result = sorted(result, key=lambda x: x["liquidity_usd"], reverse=True)
    _cache_set(cache_key, result)
    
    return result

@tool
def analyze_token_market_microstructure(token_address: str) -> Dict[str, Any]:
    """🔬 Analyze trading patterns and market microstructure for a token.
    
    Args:
        token_address: The token address to analyze
        
    Returns:
        Detailed analysis of trading patterns and market structure
    """
    # Clean and normalize the token address
    token_address = _clean_token_address(token_address)
    
    # Try to find the token by search if it isn't a standard address format
    if not (token_address.startswith("0x") or len(token_address) >= 32):
        search_result = _find_token_by_search(token_address)
        if "error" in search_result:
            return {"error": search_result["error"]}
        token_address = search_result.get("token_address", token_address)
    
    cache_key = f"microstructure_{token_address}"
    cached_data = _cache_get(cache_key)
    if cached_data:
        return cached_data
    
    url = f"{BASE_URL}/tokens/{token_address}"
    data = _make_request(url)
    
    if "error" in data:
        return {"error": data["error"]}
    
    pairs = _extract_pairs_data(data)
    if not pairs:
        # Try a different approach - search by token name/symbol
        search_result = _find_token_by_search(token_address)
        if "error" in search_result:
            return {"error": f"No trading pairs found for token {token_address}"}
        
        # Extract pairs directly from search result
        if "pairs" in search_result and search_result["pairs"]:
            pairs = search_result["pairs"]
        else:
            return {"error": f"No trading pairs found for token {token_address}"}
    
    # Find the primary trading pair (highest liquidity)
    primary_pair = max(pairs, key=lambda p: p.get("liquidity", {}).get("usd", 0))
    
    # Calculate key metrics
    buy_sell_ratio_24h = _calculate_buy_sell_ratio(primary_pair.get("txns", {}), "h24")
    buy_sell_ratio_6h = _calculate_buy_sell_ratio(primary_pair.get("txns", {}), "h6")
    vol_liq_ratio = _get_volume_liquidity_ratio(primary_pair)
    
    # Analyze price impact
    price_change_24h = primary_pair.get("priceChange", {}).get("h24", 0)
    price_change_6h = primary_pair.get("priceChange", {}).get("h6", 0)
    price_change_1h = primary_pair.get("priceChange", {}).get("h1", 0)
    
    # Analyze token information
    token_name = primary_pair.get("baseToken", {}).get("name", "Unknown")
    token_symbol = primary_pair.get("baseToken", {}).get("symbol", "UNKNOWN")
    
    # Trading pattern analysis
    trading_pattern = "neutral"
    pattern_reasons = []
    
    if buy_sell_ratio_24h > 1.5:
        trading_pattern = "accumulation"
        pattern_reasons.append(f"Buy/sell ratio is high ({buy_sell_ratio_24h:.2f})")
    elif buy_sell_ratio_24h < 0.7:
        trading_pattern = "distribution"
        pattern_reasons.append(f"Buy/sell ratio is low ({buy_sell_ratio_24h:.2f})")
    
    if vol_liq_ratio > 3:
        if vol_liq_ratio > 10:
            pattern_reasons.append(f"Very high volume/liquidity ratio ({vol_liq_ratio:.2f}) suggests potential wash trading")
        else:
            pattern_reasons.append(f"High volume/liquidity ratio ({vol_liq_ratio:.2f})")
    
    if abs(price_change_1h) > 5 and abs(price_change_6h) < 2:
        pattern_reasons.append("Recent price volatility with little 6h change suggests manipulation")
    
    # Liquidity analysis
    liquidity_usd = primary_pair.get("liquidity", {}).get("usd", 0)
    fdv = primary_pair.get("fdv", 0)
    liquidity_to_mcap_ratio = (liquidity_usd / fdv * 100) if fdv > 0 else 0
    
    liquidity_quality = "low"
    if liquidity_to_mcap_ratio > 15:
        liquidity_quality = "high"
    elif liquidity_to_mcap_ratio > 5:
        liquidity_quality = "medium"
    
    # Prepare result
    result = {
        "token_name": token_name,
        "token_symbol": token_symbol,
        "token_address": token_address,
        "primary_dex": primary_pair.get("dexId", "unknown"),
        "liquidity_usd": liquidity_usd,
        "volume_24h": primary_pair.get("volume", {}).get("h24", 0),
        "price_usd": primary_pair.get("priceUsd", "0"),
        "price_changes": {
            "1h": price_change_1h,
            "6h": price_change_6h,
            "24h": price_change_24h
        },
        "market_metrics": {
            "buy_sell_ratio_24h": round(buy_sell_ratio_24h, 2),
            "buy_sell_ratio_6h": round(buy_sell_ratio_6h, 2),
            "volume_liquidity_ratio": round(vol_liq_ratio, 2),
            "liquidity_to_mcap_percentage": round(liquidity_to_mcap_ratio, 2),
            "liquidity_quality": liquidity_quality
        },
        "trading_pattern": {
            "pattern": trading_pattern,
            "reasons": pattern_reasons
        },
        "transaction_stats": {
            "buys_24h": primary_pair.get("txns", {}).get("h24", {}).get("buys", 0),
            "sells_24h": primary_pair.get("txns", {}).get("h24", {}).get("sells", 0),
            "buys_6h": primary_pair.get("txns", {}).get("h6", {}).get("buys", 0),
            "sells_6h": primary_pair.get("txns", {}).get("h6", {}).get("sells", 0),
        }
    }
    
    _cache_set(cache_key, result)
    return result

def get_trending_pairs(chain_id: str = "", limit: int = 10) -> List[Dict[str, Any]]:
    """📈 Get the most trending pairs on DEXes right now.
    
    Args:
        chain_id: Optional chain ID to filter pairs (e.g., "solana", "ethereum", "bsc")
        limit: Maximum number of pairs to return (default: 10, max: 100)
        
    Returns:
        List of trending pairs with market data
    """
    # Validate limit
    limit = max(1, min(100, limit))
    
    # Normalize chain ID
    if chain_id:
        chain_id = _normalize_chain_id(chain_id)
    
    # Build cache key
    cache_key = f"trending_pairs_{chain_id}_{limit}" if chain_id else f"trending_pairs_{limit}"
    cached_data = _cache_get(cache_key)
    if cached_data:
        return cached_data
    
    # Use the most effective search strategies that don't hardcode specific coin names
    # 1. Use common DEX quote currencies to find active pairs
    # 2. Use generic category terms for crypto assets
    search_strategies = [
        # Quote currencies and base currencies
        "usdc", "usdt", "sol", "eth", "btc", "weth",
        # Generic crypto categories instead of specific coins
        "meme", "token", "coin", "dao", "ai", "defi"
    ]
    
    all_pairs = []
    for term in search_strategies:
        url = f"{BASE_URL}/search"
        params = {"q": term}
        
        data = _make_request(url, params=params)
        
        if "error" not in data:
            pairs = _extract_pairs_data(data)
            all_pairs.extend(pairs)
    
    if not all_pairs:
        return [{"error": "No trending pairs found"}]
    
    # Remove duplicates based on pairAddress
    unique_pairs = {}
    for pair in all_pairs:
        addr = pair.get("pairAddress", "")
        if addr and addr not in unique_pairs:
            unique_pairs[addr] = pair
    
    pairs = list(unique_pairs.values())
    
    # Filter by chain if specified
    if chain_id:
        pairs = [p for p in pairs if p.get("chainId", "").lower() == chain_id.lower()]
        if not pairs:
            return [{"error": f"No trending pairs found for chain: {chain_id}"}]
    
    # Calculate trendiness score: prioritize volume-to-liquidity ratio, high transaction count,
    # and price movement, which are better indicators of trending tokens
    for pair in pairs:
        liquidity = pair.get("liquidity", {}).get("usd", 0)
        volume = pair.get("volume", {}).get("h24", 0)
        price_change = abs(pair.get("priceChange", {}).get("h24", 0))
        txns_24h = sum(pair.get("txns", {}).get("h24", {}).get(x, 0) for x in ["buys", "sells"])
        
        # Avoid division by zero
        if liquidity <= 1:
            vol_liq_ratio = 0
        else:
            vol_liq_ratio = volume / liquidity
        
        # Calculate trending score
        trending_score = (vol_liq_ratio * 100) + (txns_24h * 0.5) + (price_change * 5)
        pair["trending_score"] = trending_score
    
    # Sort by trending score for truly trending pairs
    pairs.sort(key=lambda p: p.get("trending_score", 0), reverse=True)
    
    # Limit results
    pairs = pairs[:limit]
    
    # Format response
    result = []
    for pair in pairs:
        base_token = pair.get("baseToken", {})
        quote_token = pair.get("quoteToken", {})
        
        result.append({
            "chain_id": pair.get("chainId", ""),
            "dex_id": pair.get("dexId", ""),
            "pair_address": pair.get("pairAddress", ""),
            "base_token": {
                "address": base_token.get("address", ""),
                "name": base_token.get("name", ""),
                "symbol": base_token.get("symbol", "")
            },
            "quote_token": {
                "address": quote_token.get("address", ""),
                "name": quote_token.get("name", ""),
                "symbol": quote_token.get("symbol", "")
            },
            "price_usd": pair.get("priceUsd", "0"),
            "price_native": pair.get("priceNative", "0"),
            "liquidity_usd": pair.get("liquidity", {}).get("usd", 0),
            "volume_24h": pair.get("volume", {}).get("h24", 0),
            "price_change_24h": pair.get("priceChange", {}).get("h24", 0),
            "created_at": pair.get("pairCreatedAt", 0),
            "url": pair.get("url", "")
        })
    
    _cache_set(cache_key, result)
    return result

def get_newest_pairs(chain_id: str = "", limit: int = 10) -> List[Dict[str, Any]]:
    """🆕 Get the most recently created pairs on DEXes.
    
    Args:
        chain_id: Optional chain ID to filter pairs (e.g., "solana", "ethereum", "bsc")
        limit: Maximum number of pairs to return (default: 10, max: 100)
        
    Returns:
        List of newest pairs with market data
    """
    # Validate limit
    limit = max(1, min(100, limit))
    
    # Normalize chain ID
    if chain_id:
        chain_id = _normalize_chain_id(chain_id)
    
    # Build cache key with a short TTL for newest pairs
    cache_key = f"newest_pairs_{chain_id}_{limit}" if chain_id else f"newest_pairs_{limit}"
    cached_data = _cache_get(cache_key)
    if cached_data:
        return cached_data
    
    # Search strategies that maximize the chance of finding recent pairs
    # without hardcoding specific token names
    search_strategies = [
        # Quote currencies (most new tokens pair with these)
        "usdc", "usdt", "sol", "eth", "weth",
        # Generic terms for finding new tokens
        "token", "coin", "new", "launch", "meme",
        # Common categories for crypto projects
        "dao", "finance", "swap", "ai", "game"
    ]
    
    all_pairs = []
    for term in search_strategies:
        url = f"{BASE_URL}/search"
        params = {"q": term}
        
        data = _make_request(url, params=params)
        
        if "error" not in data:
            pairs = _extract_pairs_data(data)
            all_pairs.extend(pairs)
    
    if not all_pairs:
        return [{"error": "No pairs found"}]
    
    # Remove duplicates based on pairAddress
    unique_pairs = {}
    for pair in all_pairs:
        addr = pair.get("pairAddress", "")
        if addr and addr not in unique_pairs:
            unique_pairs[addr] = pair
    
    pairs = list(unique_pairs.values())
    
    # Filter by chain if specified
    if chain_id:
        pairs = [p for p in pairs if p.get("chainId", "").lower() == chain_id.lower()]
        if not pairs:
            return [{"error": f"No pairs found for chain: {chain_id}"}]
    
    # Filter to only include pairs with creation timestamp
    pairs = [p for p in pairs if p.get("pairCreatedAt", 0) > 0]
    
    # Sort by creation time (newest first)
    pairs.sort(key=lambda p: p.get("pairCreatedAt", 0), reverse=True)
    
    # Use current timestamp to filter only recently created pairs (last 7 days)
    current_time = time.time() * 1000  # Convert to milliseconds
    week_ago = current_time - (7 * 24 * 60 * 60 * 1000)
    recent_pairs = [p for p in pairs if p.get("pairCreatedAt", 0) >= week_ago]
    
    # Use recent pairs if we have enough, otherwise fallback to sorted pairs
    if len(recent_pairs) >= limit:
        pairs = recent_pairs
    
    # Limit results
    pairs = pairs[:limit]
    
    # Format response
    result = []
    for pair in pairs:
        base_token = pair.get("baseToken", {})
        quote_token = pair.get("quoteToken", {})
        
        # Calculate how many hours ago the pair was created
        created_at = pair.get("pairCreatedAt", 0)
        hours_ago = "N/A"
        if created_at:
            try:
                # Convert milliseconds to hours
                hours_ago = round((time.time() * 1000 - created_at) / (1000 * 60 * 60), 1)
                hours_ago = f"{hours_ago} hours ago"
            except (ValueError, TypeError):
                hours_ago = "N/A"
        
        result.append({
            "chain_id": pair.get("chainId", ""),
            "dex_id": pair.get("dexId", ""),
            "pair_address": pair.get("pairAddress", ""),
            "base_token": {
                "address": base_token.get("address", ""),
                "name": base_token.get("name", ""),
                "symbol": base_token.get("symbol", "")
            },
            "quote_token": {
                "address": quote_token.get("address", ""),
                "name": quote_token.get("name", ""),
                "symbol": quote_token.get("symbol", "")
            },
            "price_usd": pair.get("priceUsd", "0"),
            "liquidity_usd": pair.get("liquidity", {}).get("usd", 0),
            "volume_24h": pair.get("volume", {}).get("h24", 0),
            "created_at": created_at,
            "created_ago": hours_ago,
            "url": pair.get("url", "")
        })
    
    # Very short TTL for newest pairs cache
    _cache_set(cache_key, result)
    return result

def get_top_gaining_pairs(chain_id: str = "", timeframe: str = "h24", limit: int = 10) -> List[Dict[str, Any]]:
    """📊 Get pairs with the highest price gains in the selected timeframe.
    
    Args:
        chain_id: Optional chain ID to filter pairs (e.g., "solana", "ethereum", "bsc")
        timeframe: Time period for price change - "m5", "h1", "h6", or "h24" (default: "h24")
        limit: Maximum number of pairs to return (default: 10, max: 100)
        
    Returns:
        List of top gaining pairs with market data
    """
    # Validate limit
    limit = max(1, min(100, limit))
    
    # Validate timeframe
    valid_timeframes = ["m5", "h1", "h6", "h24"]
    if timeframe not in valid_timeframes:
        timeframe = "h24"
    
    # Normalize chain ID
    if chain_id:
        chain_id = _normalize_chain_id(chain_id)
    
    # Build cache key
    cache_key = f"top_gaining_{chain_id}_{timeframe}_{limit}" if chain_id else f"top_gaining_{timeframe}_{limit}"
    cached_data = _cache_get(cache_key)
    if cached_data:
        return cached_data
    
    # Use general search strategies to cast a wide net for trading pairs
    # without hardcoding specific token names
    search_strategies = [
        # Quote currencies (most tokens pair with these)
        "usdc", "usdt", "sol", "eth", "btc", "weth", 
        # Generic asset categories and concepts
        "token", "coin", "meme", "dao", "ai", "defi", "game", 
        # Terms related to volatility/gains
        "pump", "moon", "1000x", "gem", "farm"
    ]
    
    all_pairs = []
    for term in search_strategies:
        url = f"{BASE_URL}/search"
        params = {"q": term}
        
        data = _make_request(url, params=params)
        
        if "error" not in data:
            pairs = _extract_pairs_data(data)
            all_pairs.extend(pairs)
    
    if not all_pairs:
        return [{"error": "No pairs found"}]
    
    # Remove duplicates based on pairAddress
    unique_pairs = {}
    for pair in all_pairs:
        addr = pair.get("pairAddress", "")
        if addr and addr not in unique_pairs:
            unique_pairs[addr] = pair
    
    pairs = list(unique_pairs.values())
    
    # Filter by chain if specified
    if chain_id:
        pairs = [p for p in pairs if p.get("chainId", "").lower() == chain_id.lower()]
        if not pairs:
            return [{"error": f"No pairs found for chain: {chain_id}"}]
    
    # Filter out pairs without price change data for the requested timeframe
    pairs = [p for p in pairs if timeframe in p.get("priceChange", {})]
    
    if not pairs:
        return [{"error": f"No pairs with price change data for timeframe: {timeframe}"}]
    
    # Filter for minimum liquidity to avoid scams ($1000 minimum)
    pairs = [p for p in pairs if p.get("liquidity", {}).get("usd", 0) >= 1000]
    
    # Sort by price change (highest first)
    pairs.sort(key=lambda p: p.get("priceChange", {}).get(timeframe, 0), reverse=True)
    
    # Limit results
    pairs = pairs[:limit]
    
    # Format response
    result = []
    for pair in pairs:
        base_token = pair.get("baseToken", {})
        quote_token = pair.get("quoteToken", {})
        price_change = pair.get("priceChange", {}).get(timeframe, 0)
        
        result.append({
            "chain_id": pair.get("chainId", ""),
            "dex_id": pair.get("dexId", ""),
            "pair_address": pair.get("pairAddress", ""),
            "base_token": {
                "address": base_token.get("address", ""),
                "name": base_token.get("name", ""),
                "symbol": base_token.get("symbol", "")
            },
            "quote_token": {
                "address": quote_token.get("address", ""),
                "name": quote_token.get("name", ""),
                "symbol": quote_token.get("symbol", "")
            },
            "price_usd": pair.get("priceUsd", "0"),
            "price_change": f"+{price_change}%" if price_change > 0 else f"{price_change}%",
            "price_change_value": price_change,
            "timeframe": timeframe,
            "liquidity_usd": pair.get("liquidity", {}).get("usd", 0),
            "volume_24h": pair.get("volume", {}).get("h24", 0),
            "url": pair.get("url", "")
        })
    
    _cache_set(cache_key, result)
    return result

# Create LangChain tool wrappers for the dexscreener functions
@tool
def get_trending_dex_pairs(query: str) -> str:
    """📈 Get the most trending trading pairs on DEXes.
    
    Args:
        query: Format as "chain_id limit" (e.g., "solana 5" or just "5" for all chains)
        
    Returns:
        JSON string of trending pairs with market data
    """
    args = query.strip().split()
    
    if len(args) == 0:
        chain_id = ""
        limit = 10
    elif len(args) == 1:
        # Check if the argument is a number (limit) or a string (chain_id)
        if args[0].isdigit():
            chain_id = ""
            limit = int(args[0])
        else:
            chain_id = args[0]
            limit = 10
    else:
        chain_id = args[0]
        try:
            limit = int(args[1])
        except ValueError:
            limit = 10
    
    result = get_trending_pairs(chain_id, limit)
    return json.dumps(result, indent=2)

@tool
def get_newest_dex_pairs(query: str) -> str:
    """🆕 Get the most recently created pairs on DEXes.
    
    Args:
        query: Format as "chain_id limit" (e.g., "solana 5" or just "5" for all chains)
        
    Returns:
        JSON string of newest pairs with market data
    """
    args = query.strip().split()
    
    if len(args) == 0:
        chain_id = ""
        limit = 10
    elif len(args) == 1:
        # Check if the argument is a number (limit) or a string (chain_id)
        if args[0].isdigit():
            chain_id = ""
            limit = int(args[0])
        else:
            chain_id = args[0]
            limit = 10
    else:
        chain_id = args[0]
        try:
            limit = int(args[1])
        except ValueError:
            limit = 10
    
    result = get_newest_pairs(chain_id, limit)
    return json.dumps(result, indent=2)

@tool
def get_top_gaining_dex_pairs(query: str) -> str:
    """📊 Get pairs with the highest price gains in the selected timeframe.
    
    Args:
        query: Format as "chain_id timeframe limit" (e.g., "solana h24 5")
            chain_id: Optional chain ID (e.g., "solana", "ethereum", "bsc")
            timeframe: Time period - "m5", "h1", "h6", or "h24" (default: "h24")
            limit: Maximum number of pairs (default: 10)
        
    Returns:
        JSON string of top gaining pairs with market data
    """
    args = query.strip().split()
    
    chain_id = ""
    timeframe = "h24"
    limit = 10
    
    if len(args) >= 1:
        chain_id = args[0]
    
    if len(args) >= 2:
        if args[1] in ["m5", "h1", "h6", "h24"]:
            timeframe = args[1]
        elif args[1].isdigit():
            limit = int(args[1])
    
    if len(args) >= 3 and args[2].isdigit():
        limit = int(args[2])
    
    result = get_top_gaining_pairs(chain_id, timeframe, limit)
    return json.dumps(result, indent=2)
