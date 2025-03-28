import time
import logging
from typing import Dict, List, Any, Optional, Union
from langchain.tools import tool

# Import core tools
from moralis_tools import (
    get_token_metadata, get_token_price
)

# Try to import the GMGN client from our wrapper
try:
    from gmgn_wrapper import gmgn
    gmgn_plugin = gmgn()
    HAVE_GMGN = True
except ImportError:
    HAVE_GMGN = False
    gmgn_plugin = None
    logging.warning("GMGN plugin not available. Some advanced features will be limited.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("advanced_token_analysis")

# Cache system for expensive computations
CACHE: Dict[str, tuple[Any, float]] = {}
CACHE_TTL = 300  # 5 minutes

def _cache_get(key: str) -> Any:
    if key in CACHE:
        data, ts = CACHE[key]
        if time.time() - ts < CACHE_TTL:
            logger.debug(f"Cache hit for {key}")
            return data
    return None

def _cache_set(key: str, data: Any) -> None:
    CACHE[key] = (data, time.time())

def _safe_get(obj: Any, key: Union[str, List[str]], default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(key, list):
        current = obj
        for k in key:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current
    if isinstance(obj, dict):
        return obj.get(key, default)
    try:
        if hasattr(obj, "__getitem__"):
            return obj[key]
    except (IndexError, TypeError, KeyError):
        pass
    return default

def _is_smart_wallet(wallet_address: str, min_win_rate: float = 40.0, min_profit: float = 25.0) -> bool:
    if not HAVE_GMGN or not wallet_address:
        return False
    try:
        wallet_data = gmgn_plugin.getWalletInfo(wallet_address, "7d")
        if not wallet_data or not isinstance(wallet_data, dict):
            return False
        win_rate = _safe_get(wallet_data, "win_rate", 0)
        realized_profit = _safe_get(wallet_data, "realized_profit", 0)
        return win_rate >= min_win_rate and realized_profit >= min_profit
    except Exception as e:
        logger.error(f"Error checking if wallet is smart: {e}")
        return False

def _get_token_age_hours(token_address: str) -> Optional[float]:
    if not HAVE_GMGN:
        return None
    try:
        token_data = gmgn_plugin.getTokenInfo(token_address)
        if not token_data:
            return None
        creation_time = token_data.get("creation_time", 0)
        if creation_time == 0:
            return None
        current_time = time.time()
        age_hours = (current_time - creation_time) / 3600
        return age_hours
    except Exception as e:
        logger.error(f"Error getting token age: {e}")
        return None

@tool
def find_new_tokens_with_smart_wallet_activity(max_age_hours: int = 48, min_smart_wallets: int = 3, min_volume_usd: int = 10000) -> List[Dict[str, Any]]:
    """Finde neue Token mit Smart Wallet Aktivität.
    
    Sucht nach kürzlich erstellten Token, die bereits Smart Money Aktivität zeigen.
    
    Args:
        max_age_hours: Maximales Alter des Tokens in Stunden
        min_smart_wallets: Mindestanzahl von Smart Wallets, die das Token gekauft haben
        min_volume_usd: Mindestvolumen in USD
    
    Returns:
        Liste von Token-Daten mit Smart Wallet Aktivität
    """
    cache_key = f"new_smart_{max_age_hours}h_{min_smart_wallets}w_{min_volume_usd}v"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    if not HAVE_GMGN:
        return [{"error": "GMGN plugin not available. This feature requires GMGN data."}]
    try:
        # Verwende kleineres Limit (20) für getNewPairs, da größere Anfragen fehlschlagen können
        new_pairs = gmgn_plugin.getNewPairs(20)
        if not new_pairs:
            logger.warning("getNewPairs returned no data")
            return []
    except Exception as e:
        logger.error(f"Error getting new pairs from GMGN: {e}")
        return [{"error": f"Failed to get new token pairs: {str(e)}"}]
    
    # Überprüfe, ob wir ein leeres Objekt bekommen haben
    if isinstance(new_pairs, dict) and len(new_pairs) == 0:
        logger.warning("getNewPairs returned empty dictionary")
        return []
        
    # Überprüfe, ob wir eine Liste bekommen haben
    if not isinstance(new_pairs, list):
        logger.warning(f"getNewPairs returned non-list type: {type(new_pairs)}")
        return []
        
    logger.info(f"Retrieved {len(new_pairs)} pairs for analysis")
    
    result_tokens = []
    for pair in new_pairs:
        try:
            token_address = _safe_get(pair, "token_address")
            # Prüfe verschiedene mögliche Felder für die Token-Adresse
            if not token_address:
                token_address = _safe_get(pair, "base_address")
            if not token_address:
                continue
            
            token_age_hours = _get_token_age_hours(token_address)
            if token_age_hours is None or token_age_hours > max_age_hours:
                continue
                
            # Prüfe verschiedene mögliche Felder für das Volumen
            volume_24h = _safe_get(pair, "volume_24h", 0)
            if volume_24h == 0:
                # Versuche alternative Felder zu finden
                quote_reserve_usd = _safe_get(pair, "quote_reserve_usd", 0)
                if quote_reserve_usd > 0:
                    volume_24h = quote_reserve_usd  # Näherungswert
                    
            if volume_24h < min_volume_usd:
                continue
                
            token_meta = get_token_metadata(token_address)
            token_name = _safe_get(token_meta, "name", "Unknown")
            token_symbol = _safe_get(token_meta, "symbol", "???")
            
            # Wenn token_name oder token_symbol nicht gefunden wurden, versuche sie aus pair-Daten zu bekommen
            if token_name == "Unknown" and _safe_get(pair, "base_token_info"):
                base_token_info = _safe_get(pair, "base_token_info", {})
                if isinstance(base_token_info, dict):
                    token_name = _safe_get(base_token_info, "name", token_name)
                    token_symbol = _safe_get(base_token_info, "symbol", token_symbol)
            
            top_buyers = gmgn_plugin.getTopBuyers(token_address)
            if not top_buyers:
                continue
                
            # Überprüfe ob top_buyers eine Liste ist
            if not isinstance(top_buyers, list):
                logger.warning(f"getTopBuyers returned non-list type: {type(top_buyers)}")
                continue
                
            smart_wallets = []
            for buyer in top_buyers:
                wallet_address = _safe_get(buyer, "wallet")
                if not wallet_address:
                    continue
                if _is_smart_wallet(wallet_address):
                    profit = _safe_get(buyer, "profit", 0)
                    bought_amount = _safe_get(buyer, "amount", 0)
                    smart_wallets.append({
                        "address": wallet_address,
                        "profit_history": profit,
                        "bought_amount": bought_amount
                    })
            if len(smart_wallets) >= min_smart_wallets:
                token_data = {
                    "address": token_address,
                    "name": token_name,
                    "symbol": token_symbol,
                    "age_hours": token_age_hours,
                    "volume_24h": volume_24h,
                    "smart_wallet_count": len(smart_wallets),
                    "smart_wallets": smart_wallets[:5] if len(smart_wallets) > 5 else smart_wallets,
                    "price": get_token_price(token_address),
                    "liquidity": _safe_get(pair, "liquidity", 0),
                    "dex": _safe_get(pair, "launchpad", _safe_get(pair, "dex", "unknown"))
                }
                result_tokens.append(token_data)
        except Exception as e:
            logger.error(f"Error processing pair: {e}")
            continue
    result_tokens.sort(key=lambda x: x["smart_wallet_count"], reverse=True)
    _cache_set(cache_key, result_tokens)
    return result_tokens

@tool
def find_high_volume_new_tokens(max_age_hours: float = 48.0, min_volume_usd: float = 10000, min_smart_wallets: int = 1, max_results: int = 5) -> List[Dict[str, Any]]:
    """Finde neue Token mit hohem Handelsvolumen.
    
    Sucht nach kürzlich erstellten Token, die bereits ein hohes Handelsvolumen aufweisen.
    
    Args:
        max_age_hours: Maximales Alter des Tokens in Stunden
        min_volume_usd: Mindestvolumen in USD (24h)
        min_smart_wallets: Mindestanzahl von Smart Wallets, die das Token gekauft haben
        max_results: Maximale Anzahl der zurückgegebenen Ergebnisse
    
    Returns:
        Liste von Token-Daten mit hohem Volumen, sortiert nach Volumen (absteigend)
    """
    if not HAVE_GMGN:
        logger.warning("GMGN plugin is required for this feature but not available")
        return []
    cache_key = f"new_tokens_{max_age_hours}_{min_volume_usd}_{min_smart_wallets}"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    try:
        # Verwende kleineres Limit (20) für getNewPairs, da größere Anfragen fehlschlagen können
        new_pairs = gmgn_plugin.getNewPairs(20)
        if not new_pairs:
            logger.warning("getNewPairs returned no data")
            return []
    except Exception as e:
        logger.error(f"Error getting new pairs: {e}")
        return []
        
    # Überprüfe, ob wir ein leeres Objekt bekommen haben
    if isinstance(new_pairs, dict) and len(new_pairs) == 0:
        logger.warning("getNewPairs returned empty dictionary")
        return []
        
    # Überprüfe, ob wir eine Liste bekommen haben
    if not isinstance(new_pairs, list):
        logger.warning(f"getNewPairs returned non-list type: {type(new_pairs)}")
        return []
        
    logger.info(f"Retrieved {len(new_pairs)} pairs for analysis")
    
    result_tokens = []
    for pair in new_pairs:
        try:
            token_address = _safe_get(pair, "token_address")
            # Prüfe verschiedene mögliche Felder für die Token-Adresse
            if not token_address:
                token_address = _safe_get(pair, "base_address")
            if not token_address:
                continue
            
            token_age_hours = _get_token_age_hours(token_address)
            if token_age_hours is None or token_age_hours > max_age_hours:
                continue
            
            # Prüfe verschiedene mögliche Felder für das Volumen
            volume_24h = _safe_get(pair, "volume_24h", 0)
            if volume_24h == 0:
                # Versuche alternative Felder zu finden
                quote_reserve_usd = _safe_get(pair, "quote_reserve_usd", 0)
                if quote_reserve_usd > 0:
                    volume_24h = quote_reserve_usd  # Näherungswert
                    
            if volume_24h < min_volume_usd:
                continue
                
            token_meta = get_token_metadata(token_address)
            token_name = _safe_get(token_meta, "name", "Unknown")
            token_symbol = _safe_get(token_meta, "symbol", "???")
            
            # Wenn token_name oder token_symbol nicht gefunden wurden, versuche sie aus pair-Daten zu bekommen
            if token_name == "Unknown" and _safe_get(pair, "base_token_info"):
                base_token_info = _safe_get(pair, "base_token_info", {})
                if isinstance(base_token_info, dict):
                    token_name = _safe_get(base_token_info, "name", token_name)
                    token_symbol = _safe_get(base_token_info, "symbol", token_symbol)
            
            top_buyers = gmgn_plugin.getTopBuyers(token_address)
            if not top_buyers:
                continue
                
            # Überprüfe ob top_buyers eine Liste ist
            if not isinstance(top_buyers, list):
                logger.warning(f"getTopBuyers returned non-list type: {type(top_buyers)}")
                continue
                
            smart_wallets = []
            for buyer in top_buyers:
                wallet_address = _safe_get(buyer, "wallet")
                if not wallet_address:
                    continue
                if _is_smart_wallet(wallet_address):
                    profit = _safe_get(buyer, "profit", 0)
                    bought_amount = _safe_get(buyer, "amount", 0)
                    smart_wallets.append({
                        "address": wallet_address,
                        "profit_history": profit,
                        "bought_amount": bought_amount
                    })
            if len(smart_wallets) >= min_smart_wallets:
                token_data = {
                    "address": token_address,
                    "name": token_name,
                    "symbol": token_symbol,
                    "age_hours": token_age_hours,
                    "volume_24h": volume_24h,
                    "smart_wallet_count": len(smart_wallets),
                    "smart_wallets": smart_wallets[:5] if len(smart_wallets) > 5 else smart_wallets,
                    "price": get_token_price(token_address),
                    "liquidity": _safe_get(pair, "liquidity", 0),
                    "dex": _safe_get(pair, "launchpad", _safe_get(pair, "dex", "unknown"))
                }
                result_tokens.append(token_data)
        except Exception as e:
            logger.error(f"Error analyzing pair: {e}")
            continue
    result_tokens.sort(key=lambda x: x["volume_24h"], reverse=True)
    _cache_set(cache_key, result_tokens[:max_results])
    return result_tokens[:max_results]
