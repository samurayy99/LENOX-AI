# dexscreener_tools.py
import time
import logging
import requests
from typing import Dict, List, Any, Optional, Union, cast
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

# === TOOLS ===
@tool
def get_dex_liquidity_distribution(token_address: str) -> List[Dict[str, Any]]:
    """📊 Analyze how a token's liquidity is distributed across different DEXes.
    
    Args:
        token_address: The token address to analyze
        
    Returns:
        List of DEX liquidity pools with details on distribution
    """
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

@tool
def get_chain_dex_volume_leaders(args: str) -> List[Dict[str, Any]]:
    """📈 Get most active DEXes on a specific chain ranked by trading volume.
    
    Args:
        args: "chain_id limit min_liquidity" - space separated arguments:
            - chain_id: Chain to analyze (e.g., solana, ethereum, bsc)
            - limit: Maximum number of DEXes to return
            - min_liquidity: Minimum liquidity in USD
        
    Returns:
        List of DEXes with highest trading volume on the chain
    """
    expected_args = ["chain_id", "limit", "min_liquidity"]
    defaults = {"chain_id": "solana", "limit": 5, "min_liquidity": 10000}
    parsed_args = cast(Dict[str, Any], _parse_args(args, expected_args, defaults))
    
    chain_id = _normalize_chain_id(parsed_args["chain_id"])
    limit = int(parsed_args["limit"])
    min_liquidity = float(parsed_args["min_liquidity"])
    
    cache_key = f"dex_volume_{chain_id}_{limit}_{min_liquidity}"
    cached_data = _cache_get(cache_key)
    if cached_data:
        return cached_data
    
    # Search for high volume pairs on the chain
    url = f"{BASE_URL}/search"
    params = {"q": chain_id}
    data = _make_request(url, params, cache_key=f"search_{chain_id}")
    
    if "error" in data:
        return [{"error": data["error"]}]
    
    pairs = _extract_pairs_data(data)
    
    # Filter by minimum liquidity
    pairs = [p for p in pairs if p.get("liquidity", {}).get("usd", 0) >= min_liquidity]
    
    # Group by DEX and calculate metrics
    dex_data = {}
    for pair in pairs:
        dex_id = pair.get("dexId", "unknown")
        
        if dex_id not in dex_data:
            dex_data[dex_id] = {
                "dex": dex_id,
                "chain": chain_id,
                "volume_24h": 0,
                "liquidity_usd": 0,
                "pairs_count": 0,
                "transactions_24h": 0
            }
        
        dex_entry = dex_data[dex_id]
        dex_entry["volume_24h"] += pair.get("volume", {}).get("h24", 0)
        dex_entry["liquidity_usd"] += pair.get("liquidity", {}).get("usd", 0)
        dex_entry["pairs_count"] += 1
        
        # Sum up transactions
        txns = pair.get("txns", {}).get("h24", {})
        if txns:
            dex_entry["transactions_24h"] += txns.get("buys", 0) + txns.get("sells", 0)
    
    # Convert to list, calculate fees estimate (0.3% is common)
    result = []
    for dex_id, data in dex_data.items():
        # Only include DEXes with reasonable volume
        if data["volume_24h"] > 0:
            fee_estimate = data["volume_24h"] * 0.003  # 0.3% fee assumption
            result.append({
                "dex": dex_id,
                "chain": chain_id,
                "volume_24h": data["volume_24h"],
                "liquidity_usd": data["liquidity_usd"],
                "pairs_count": data["pairs_count"],
                "transactions_24h": data["transactions_24h"],
                "daily_fee_estimate_usd": round(fee_estimate, 2),
                "volume_to_liquidity_ratio": round(data["volume_24h"] / data["liquidity_usd"], 2) if data["liquidity_usd"] > 0 else 0
            })
    
    # Sort by volume
    result = sorted(result, key=lambda x: x["volume_24h"], reverse=True)[:limit]
    _cache_set(cache_key, result)
    
    return result

@tool
def get_cross_chain_token_data(token_symbol: str) -> List[Dict[str, Any]]:
    """🔍 Find and compare the same token across different blockchains.
    
    Args:
        token_symbol: The token symbol or name to search for (e.g., "USDC", "ETH")
        
    Returns:
        List of matching tokens across different chains with price and liquidity data
    """
    cache_key = f"cross_chain_{token_symbol.lower()}"
    cached_data = _cache_get(cache_key)
    if cached_data:
        return cached_data
    
    url = f"{BASE_URL}/search"
    params = {"q": token_symbol}
    data = _make_request(url, params)
    
    if "error" in data:
        return [{"error": data["error"]}]
    
    pairs = _extract_pairs_data(data)
    if not pairs:
        return [{"error": f"No tokens found matching '{token_symbol}'"}]
    
    # Group by chain and find the best pair for each chain
    chain_data = {}
    for pair in pairs:
        chain_id = pair.get("chainId", "unknown")
        token_address = pair.get("baseToken", {}).get("address", "")
        token_symbol_match = pair.get("baseToken", {}).get("symbol", "").lower()
        
        # Skip pairs that don't match the token symbol
        if token_symbol.lower() not in token_symbol_match.lower():
            continue
            
        # Get or create chain entry
        if chain_id not in chain_data:
            chain_data[chain_id] = {
                "chain_id": chain_id,
                "pairs": []
            }
            
        # Add to the chain's pairs
        chain_data[chain_id]["pairs"].append({
            "dex": pair.get("dexId", "unknown"),
            "token_address": token_address,
            "token_name": pair.get("baseToken", {}).get("name", "Unknown"),
            "token_symbol": pair.get("baseToken", {}).get("symbol", "UNKNOWN"),
            "price_usd": pair.get("priceUsd", "0"),
            "liquidity_usd": pair.get("liquidity", {}).get("usd", 0),
            "volume_24h": pair.get("volume", {}).get("h24", 0),
            "price_change_24h": pair.get("priceChange", {}).get("h24", 0)
        })
    
    # For each chain, pick the pair with highest liquidity
    result = []
    for chain_id, data in chain_data.items():
        pairs = data["pairs"]
        if pairs:
            # Sort by liquidity and pick highest
            best_pair = max(pairs, key=lambda x: x["liquidity_usd"])
            best_pair["chain_id"] = chain_id
            result.append(best_pair)
    
    # Sort by liquidity across chains
    result = sorted(result, key=lambda x: x["liquidity_usd"], reverse=True)
    _cache_set(cache_key, result)
    
    return result

@tool
def search_dexes_for_token(args: str) -> List[Dict[str, Any]]:
    """
    Searches multiple DEXes for a specific token symbol or address.
    
    Args:
        args (str): Format: "{token_symbol} {chain_id} {limit}"
            - token_symbol: The symbol of the token to search for (e.g., "BONK")
            - chain_id: The blockchain to search on (e.g., "solana")
            - limit: Maximum number of results to return (e.g., "5")
    
    Returns:
        List[Dict[str, Any]]: List of found tokens with their DEX, price, and liquidity information
    """
    expected_args = ["token_symbol", "chain_id", "limit"]
    defaults = {"limit": 5}
    
    parsed_args = cast(Dict[str, Any], _parse_args(args, expected_args, defaults))
    
    if "token_symbol" not in parsed_args or not parsed_args["token_symbol"]:
        return [{"error": "Please provide a token symbol"}]
    
    if "chain_id" not in parsed_args or not parsed_args["chain_id"]:
        return [{"error": "Please provide a chain_id"}]
    
    token_symbol = str(parsed_args["token_symbol"]).upper()
    chain_id = _normalize_chain_id(parsed_args["chain_id"])
    limit = int(parsed_args["limit"])
    
    # Search for the token
    url = f"https://api.dexscreener.com/latest/dex/search?q={token_symbol}&chain={chain_id}"
    
    try:
        response_data = _make_request(url)
        if not response_data or "pairs" not in response_data:
            return [{"error": f"No data found for token {token_symbol} on {chain_id}"}]
            
        # Extract and normalize the data
        pairs = response_data.get("pairs", [])
        if not pairs:
            return [{"error": f"No pairs found for {token_symbol} on {chain_id}"}]
            
        results = []
        for pair in pairs[:limit]:  # Limit the results
            base_token = pair.get("baseToken", {})
            
            # Only include if token symbol matches what we're looking for
            if base_token.get("symbol", "").upper() == token_symbol:
                results.append({
                    "dex": pair.get("dexId", "unknown"),
                    "token_address": base_token.get("address", ""),
                    "token_name": base_token.get("name", ""),
                    "pair_address": pair.get("pairAddress", ""),
                    "price_usd": pair.get("priceUsd", "0"),
                    "price_native": pair.get("priceNative", "0"),
                    "liquidity_usd": pair.get("liquidity", {}).get("usd", 0),
                    "volume_24h": pair.get("volume", {}).get("h24", 0),
                    "chain": pair.get("chainId", "")
                })
            
        return results[:limit]  # Ensure we don't exceed the limit
        
    except Exception as e:
        logger.error(f"Error searching for token {token_symbol}: {str(e)}")
        return [{"error": f"Error searching for token: {str(e)}"}] 