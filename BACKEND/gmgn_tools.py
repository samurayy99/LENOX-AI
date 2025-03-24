# gmgn_tools.py
import time, logging
from typing import Dict, List, Any, Union
from dotenv import load_dotenv
from langchain.tools import tool
from gmgn_wrapper import gmgn

# === ENV & CONFIG ===
load_dotenv()
# GMGN Client
gmgn_client = gmgn()

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gmgn_tools")

# === CACHE SYSTEM ===
CACHE: Dict[str, tuple[Any, float]] = {}
CACHE_TTL = 300  # 5 minutes

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

def _parse_args(arg_str: str, expected_args: List[str], defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Parse space-separated string arguments for LangChain tool invocation
    
    Args:
        arg_str: The space-separated string of arguments
        expected_args: List of argument names in order
        defaults: Default values for each argument
        
    Returns:
        Dictionary of parsed arguments
    """
    args = arg_str.split() if arg_str else []
    result = defaults.copy()
    
    # Apply provided arguments
    for i, value in enumerate(args):
        if i < len(expected_args):
            arg_name = expected_args[i]
            # Convert to appropriate type based on default
            if arg_name in defaults:
                default_type = type(defaults[arg_name])
                try:
                    if default_type == bool:
                        result[arg_name] = value.lower() in ("yes", "true", "t", "1")
                    else:
                        result[arg_name] = default_type(value)
                except ValueError:
                    # If conversion fails, keep as string
                    result[arg_name] = value
            else:
                # No default, just use as string
                result[arg_name] = value
    
    return result

def _process_response_data(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Process API response data into a consistent format
    
    Args:
        data: Response data from API (either dict or list)
        
    Returns:
        List of items from the response
    """
    if not data:
        return []
        
    # Convert dictionary items to list
    if isinstance(data, dict):
        # Check if we have an "items" key (for wrapper-normalized list responses)
        if "items" in data and isinstance(data["items"], list):
            return data["items"]
        
        # Check for "error" key
        if "error" in data:
            return [data]
            
        # Check for nested data structures common in GMGN API
        if "rank" in data and isinstance(data["rank"], list):
            return data["rank"]
            
        if "pairs" in data and isinstance(data["pairs"], list):
            return data["pairs"]
            
        # Try to extract values or convert to list of items
        items = []
        for key, value in data.items():
            if isinstance(value, dict):
                # Include the key as an ID if it might be useful
                value_with_id = value.copy()
                if "id" not in value and key not in value:
                    value_with_id["id"] = key
                items.append(value_with_id)
            else:
                # For non-dict values, create a simple key-value item
                items.append({"key": key, "value": value})
        return items
    
    # Data is already a list
    return data

# === TOOLS ===
@tool
def get_trending_wallets(args: str) -> List[Dict[str, Any]]:
    """🔍 Get top-performing wallets based on profitability for a specific timeframe.
    
    Args:
        args: "timeframe wallet_tag limit" - space separated arguments:
            - timeframe: Time period to analyze wallets (1d, 7d, 30d)
            - wallet_tag: Type of wallets (smart_degen, pump_smart, reowned, snipe_bot)
            - limit: Maximum number of wallets to return
        
    Returns:
        List of top wallets with performance metrics
    """
    # Parse arguments
    expected_args = ["timeframe", "wallet_tag", "limit"]
    defaults = {"timeframe": "7d", "wallet_tag": "smart_degen", "limit": 10}
    parsed_args = _parse_args(args, expected_args, defaults)
    
    timeframe = parsed_args["timeframe"]
    wallet_tag = parsed_args["wallet_tag"]
    limit = parsed_args["limit"]
    
    valid_timeframes = ["1d", "7d", "30d"]
    if timeframe not in valid_timeframes:
        return [{"error": f"Invalid timeframe. Choose from: {', '.join(valid_timeframes)}"}]
        
    valid_tags = ["smart_degen", "pump_smart", "reowned", "snipe_bot", "all"]
    if wallet_tag not in valid_tags:
        return [{"error": f"Invalid wallet tag. Choose from: {', '.join(valid_tags)}"}]
    
    # Use cache if available
    cache_key = f"trending_wallets_{timeframe}_{wallet_tag}_{limit}"
    cached_data = _cache_get(cache_key)
    if cached_data:
        return cached_data
    
    # Get data from GMGN API
    wallets_data = gmgn_client.getTrendingWallets(timeframe=timeframe, walletTag=wallet_tag)
    
    if not wallets_data:
        return [{"error": "Failed to fetch trending wallets"}]
    
    # Process wallets data
    wallets_list = _process_response_data(wallets_data)
    
    result: List[Dict[str, Any]] = []
    for wallet in wallets_list[:limit]:
        if not isinstance(wallet, dict):
            continue
            
        # Try both wallet_address and address fields
        wallet_address = wallet.get("wallet_address") or wallet.get("address") or "Unknown"
        
        # Extract profit metrics from different possible structures
        pnl_key = f"pnl_{timeframe}"
        profit_usd = 0
        profit_sol = 0
        
        # Try different field structures
        if "pnl" in wallet and isinstance(wallet["pnl"], dict):
            profit_usd = wallet["pnl"].get("usd", 0)
            profit_sol = wallet["pnl"].get("sol", 0)
        elif pnl_key in wallet:
            profit_usd = wallet[pnl_key]
        elif "realized_profit" in wallet:
            profit_usd = wallet["realized_profit"]
        
        # Extract win rate and trade stats
        win_rate = wallet.get("winRate", 0) or wallet.get("winrate_7d", 0) or 0
        trade_count = wallet.get("tradeCount", 0) or wallet.get("txs_30d", 0) or 0
        
        # Get tag information
        tags = wallet.get("tags", [])
        if not tags and wallet.get("tag") and isinstance(wallet.get("tag"), str):
            tags = [wallet.get("tag")]
        
        # Advanced metrics available in the API
        buys = wallet.get("buy", 0) or wallet.get("buy_30d", 0) or 0
        sells = wallet.get("sell", 0) or wallet.get("sell_30d", 0) or 0
        last_active = wallet.get("last_active", 0)
        balance = wallet.get("balance", 0) or wallet.get("sol_balance", 0) or 0
        
        result.append({
            "address": wallet_address,
            "profit_usd": profit_usd,
            "profit_sol": profit_sol,
            "profit_percent": wallet.get("profitPercent", 0),
            "win_rate": win_rate,
            "trade_count": trade_count,
            "tags": tags,
            "buys": buys,
            "sells": sells,
            "last_active": last_active,
            "balance": balance
        })
    
    # Cache results
    _cache_set(cache_key, result)
    return result

@tool
def get_new_token_pairs(args: str) -> List[Dict[str, Any]]:
    """🔎 Discover newly created token pairs on DEXes with filtering options.
    
    Args:
        args: "limit min_liquidity" - space separated arguments:
            - limit: Maximum number of new pairs to return
            - min_liquidity: Minimum liquidity in USD
        
    Returns:
        List of new token pairs with metadata
    """
    # Parse arguments
    expected_args = ["limit", "min_liquidity"]
    defaults = {"limit": 10, "min_liquidity": 0}  # Default to no minimum
    parsed_args = _parse_args(args, expected_args, defaults)
    
    limit = parsed_args["limit"]
    min_liquidity = parsed_args["min_liquidity"]
    
    cache_key = f"new_pairs_{limit}_{min_liquidity}"
    cached_data = _cache_get(cache_key)
    if cached_data:
        return cached_data
    
    # Get new pairs from GMGN API - request more pairs than needed to account for filtering
    requested_limit = max(limit * 2, 20)  # Request at least 20 pairs or double the needed amount
    pairs_data = gmgn_client.getNewPairs(limit=requested_limit)
    
    if not pairs_data:
        return [{"error": "Failed to fetch new token pairs"}]
    
    # Process pairs data
    pairs_list = _process_response_data(pairs_data)
    
    result: List[Dict[str, Any]] = []
    for pair in pairs_list:
        if not isinstance(pair, dict):
            continue
            
        # Extract token data from various formats
        # Format 1: Token info in a 'token' object
        token = pair.get("token", {})
        
        # Format 2: Token info in a 'base_token_info' object
        if not token and "base_token_info" in pair:
            token = pair.get("base_token_info", {})
        
        # Get token name and symbol
        token_name = token.get("name") or pair.get("name", "Unknown")
        token_symbol = token.get("symbol") or pair.get("symbol", "???")
            
        # Extract liquidity from different possible fields
        liquidity = 0
        
        # Check token liquidity field first
        if "liquidity" in token:
            if isinstance(token["liquidity"], dict):
                liquidity = token["liquidity"].get("usd", 0)
            elif isinstance(token["liquidity"], (int, float, str)):
                try:
                    liquidity = float(token["liquidity"])
                except (ValueError, TypeError):
                    liquidity = 0
        
        # Check pair liquidity fields if token liquidity is zero
        if liquidity == 0:
            # Try different liquidity fields in the pair object
            for liq_field in ["liquidity", "initial_liquidity", "quote_reserve_usd"]:
                if liq_field in pair:
                    try:
                        if isinstance(pair[liq_field], dict):
                            liquidity = pair[liq_field].get("usd", 0)
                        else:
                            liquidity = float(pair[liq_field]) if pair[liq_field] else 0
                        if liquidity > 0:
                            break
                    except (ValueError, TypeError):
                        continue
        
        # Extract DEX info
        dex = pair.get("dexName") or pair.get("pool_type_str") or pair.get("launchpad", "unknown").lower()
        
        # Get token address from different possible fields
        token_address = (token.get("address") or 
                        pair.get("base_address") or 
                        pair.get("token_address", ""))
        
        # Creation timestamp data
        created_at = pair.get("openTimestamp") or pair.get("pool_creation_timestamp") or pair.get("creation_timestamp", "")
        
        # Only include pairs that meet the minimum liquidity requirement
        if liquidity >= min_liquidity:
            result.append({
                "token_name": token_name,
                "token_symbol": token_symbol,
                "token_address": token_address,
                "liquidity_usd": float(liquidity) if isinstance(liquidity, (int, float)) else 0,
                "pool_address": pair.get("address", ""),
                "created_at": created_at,
                "dex": dex,
                "quote_symbol": pair.get("quote_symbol", "SOL")
            })
    
    # Filter by limit and cache results
    filtered_result = result[:limit]
    _cache_set(cache_key, filtered_result)
    return filtered_result

@tool
def get_trending_tokens(args: str) -> List[Dict[str, Any]]:
    """📈 Get trending tokens by trading volume and activity.
    
    Args:
        args: "timeframe limit" - space separated arguments:
            - timeframe: Time period to analyze (1h, 6h, 24h)
            - limit: Maximum number of tokens to return
        
    Returns:
        List of trending tokens with market data
    """
    # Parse arguments
    expected_args = ["timeframe", "limit"]
    defaults = {"timeframe": "1h", "limit": 10}
    parsed_args = _parse_args(args, expected_args, defaults)
    
    timeframe = parsed_args["timeframe"]
    limit = parsed_args["limit"]
    
    valid_timeframes = ["1h", "6h", "24h"]
    if timeframe not in valid_timeframes:
        return [{"error": f"Invalid timeframe. Choose from: {', '.join(valid_timeframes)}"}]
    
    # Use cache if available
    cache_key = f"trending_tokens_{timeframe}_{limit}"
    cached_data = _cache_get(cache_key)
    if cached_data:
        return cached_data
    
    # Get data from GMGN API
    tokens_data = gmgn_client.getTrendingTokens(timeframe=timeframe)
    
    if not tokens_data:
        return [{"error": "Failed to fetch trending tokens"}]
    
    # Process tokens data
    tokens_list = _process_response_data(tokens_data)
    
    result: List[Dict[str, Any]] = []
    for token in tokens_list[:limit]:
        if not isinstance(token, dict):
            continue
            
        # Extract price data
        price_usd = token.get("price", 0)
        
        # Handle price change data
        price_change_key = f"price_change_percent{timeframe}"
        price_change = token.get("price_change_percent", 0)
        if price_change_key in token:
            price_change = token[price_change_key]
        
        # Volume data
        volume = token.get("volume", 0)
        
        # Liquidity data
        liquidity = token.get("liquidity", 0)
        
        # Market cap data
        market_cap = token.get("market_cap", 0) or token.get("marketCap", 0) or token.get("fdv", 0)
        
        # Social data
        twitter = token.get("twitter_username", "")
        website = token.get("website", "")
        
        result.append({
            "name": token.get("name", "Unknown"),
            "symbol": token.get("symbol", "???"),
            "address": token.get("address", ""),
            "price_usd": price_usd,
            "price_change_percent": price_change,
            "volume": volume,
            "liquidity": liquidity,
            "market_cap": market_cap,
            "swaps": token.get("swaps", 0),
            "holder_count": token.get("holder_count", 0),
            "creation_date": token.get("pool_creation_timestamp", 0) or token.get("open_timestamp", 0),
            "twitter": twitter,
            "website": website
        })
    
    # Cache results
    _cache_set(cache_key, result)
    return result