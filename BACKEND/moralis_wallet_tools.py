import os, time, logging, requests
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv
from langchain.tools import tool

# === ENV ===
load_dotenv()
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
MORALIS_BASE_URL = "https://solana-gateway.moralis.io"
HEADERS = {"Accept": "application/json", "X-API-Key": MORALIS_API_KEY}

# === Logging & Cache ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("moralis_wallet_tools")
CACHE: Dict[str, tuple[Any, float]] = {}
CACHE_EXPIRY = 600

def _clear_expired_cache():
    now = time.time()
    expired = [k for k, (_, t) in CACHE.items() if now - t > CACHE_EXPIRY]
    for k in expired:
        del CACHE[k]

def _make_request(url: str, params=None, cache_key=None) -> Dict[str, Any]:
    """Make a request with proper error handling and caching."""
    # Check cache first
    _clear_expired_cache()
    if cache_key and cache_key in CACHE:
        data, ts = CACHE[cache_key]
        if time.time() - ts < CACHE_EXPIRY:
            logger.debug(f"Cache hit for {cache_key}")
            return data
            
    # Make the request with error handling
    try:
        logger.debug(f"Making request to {url}")
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        
        # Check status code
        if response.status_code != 200:
            logger.error(f"API Error ({url}): Status {response.status_code}, {response.text}")
            return {"error": f"API returned status {response.status_code}"}
            
        # Parse JSON with error handling
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"JSON parsing error ({url}): {str(e)}")
            return {"error": f"Failed to parse JSON response: {str(e)}"}
            
        # Cache successful response
        if cache_key and data:
            CACHE[cache_key] = (data, time.time())
            logger.debug(f"Cached data for {cache_key}")
            
        return data
    except requests.RequestException as e:
        logger.error(f"Request failed ({url}): {str(e)}")
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error ({url}): {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}


# === 1. SOL BALANCE ===
@tool
def get_sol_balance(wallet: str) -> float:
    """💰 Fetch SOL balance of a wallet."""
    network = "mainnet"  # Always use mainnet for now
    url = f"{MORALIS_BASE_URL}/account/{network}/{wallet}/balance"
    data = _make_request(url, cache_key=f"sol_{wallet}")
    
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


# === 2. SPL TOKENS ===
@tool
def get_spl_tokens(wallet: str) -> List[Dict[str, Any]]:
    """🪙 Fetch SPL tokens held by a wallet."""
    network = "mainnet"  # Always use mainnet for now
    url = f"{MORALIS_BASE_URL}/account/{network}/{wallet}/tokens"
    data = _make_request(url, cache_key=f"tokens_{wallet}")
    
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
            # Debug info for empty lists
            if len(tokens) == 0:
                logger.info("No SPL tokens found. This could be normal if the wallet is new, "
                          "contains only SOL, or if the API cache hasn't been updated.")
            return tokens
        else:
            logger.warning(f"Unexpected format for SPL tokens in result field: {type(tokens)}")
    else:
        logger.warning(f"Unexpected API response format for SPL tokens: {type(data)}")
    
    return []


# === 3. PORTFOLIO USD VALUE ===
@tool
def get_portfolio_value(wallet: str) -> float:
    """💸 Get total portfolio value in USD."""
    network = "mainnet"  # Always use mainnet for now
    
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
    try:
        url = f"{MORALIS_BASE_URL}/account/{network}/{wallet}/tokens"
        data = _make_request(url, cache_key=f"tokens_{wallet}")
        
        if isinstance(data, list):
            tokens = data
        elif isinstance(data, dict) and "result" in data:
            tokens = data.get("result", [])
        else:
            tokens = []
            
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
                
    except Exception as e:
        logger.warning(f"Error calculating token values: {e}")
    
    # Return total portfolio value
    total_value = sol_value + tokens_value
    return total_value


# === 4. NFTs ===
@tool
def get_wallet_nfts(wallet: str, limit: int = 10) -> List[Dict[str, Any]]:
    """🎨 Get NFTs from wallet."""
    network = "mainnet"  # Always use mainnet for now
    url = f"{MORALIS_BASE_URL}/account/{network}/{wallet}/nft"
    params = {"limit": str(limit)}
    data = _make_request(url, params=params, cache_key=f"nfts_{wallet}")
    
    if isinstance(data, dict) and "error" in data:
        logger.warning(f"Error getting NFTs for {wallet}: {data['error']}")
        return []
    
    if isinstance(data, dict) and "result" in data:
        return data.get("result", [])
    
    return []


# === 5. Recent Swaps ===
@tool
def get_recent_swaps(wallet: str, limit: int = 5) -> List[Dict[str, Any]]:
    """🔁 Get recent swaps (Raydium/Jupiter etc)."""
    network = "mainnet"  # Always use mainnet for now
    url = f"{MORALIS_BASE_URL}/account/{network}/{wallet}/swaps"
    params = {"limit": str(limit)}
    data = _make_request(url, params=params, cache_key=f"swaps_{wallet}")
    
    if isinstance(data, dict) and "error" in data:
        logger.warning(f"Error getting swaps for {wallet}: {data['error']}")
        return []
    
    if isinstance(data, dict) and "result" in data:
        return data.get("result", [])
    
    return []


# === 6. Risk Score ===
@tool
def get_wallet_risk_score(wallet: str) -> Dict[str, Any]:
    """🧠 Calculate wallet risk based on activity."""
    # Always use mainnet for now
    sol = get_sol_balance(wallet)
    tokens = get_spl_tokens(wallet)
    swaps = get_recent_swaps(wallet)

    risk = 5.0  # Start with medium risk
    flags = []

    # Risk factors
    if sol == 0:
        risk -= 1.5
        flags.append("⚠️ No SOL balance")
    if len(tokens) == 0:
        risk -= 1.0
        flags.append("⚠️ No tokens found")
    if len(swaps) == 0:
        risk -= 1.0
        flags.append("⚠️ No recent swaps")

    # Risk level classification
    level = "LOW"
    if risk < 4.0: level = "MEDIUM" 
    if risk < 3.0: level = "HIGH"

    return {"score": risk, "level": level, "flags": flags or ["✅ Looks active"]}


# === 7. Wallet Overview ===
@tool
def get_wallet_overview(wallet: str) -> Dict[str, Any]:
    """📊 Full wallet overview (balance, tokens, NFTs, swaps, risk)."""
    try:
        sol_balance = get_sol_balance(wallet)
        tokens = get_spl_tokens(wallet)
        nfts = get_wallet_nfts(wallet)
        swaps = get_recent_swaps(wallet)
        portfolio = get_portfolio_value(wallet)
        risk = get_wallet_risk_score(wallet)
        
        return {
            "sol_balance": f"{sol_balance:.2f} SOL",
            "token_count": len(tokens),
            "nft_count": len(nfts),
            "recent_swaps": len(swaps),
            "portfolio_usd": f"${portfolio:,.2f}",
            "risk": risk,
            "explorers": {
                "Solscan": f"https://solscan.io/account/{wallet}",
                "Birdeye": f"https://birdeye.so/address/{wallet}"
            }
        }
    except Exception as e:
        logger.error(f"Error generating wallet overview: {e}")
        return {
            "error": f"Failed to generate complete overview: {str(e)}",
            "sol_balance": f"{get_sol_balance(wallet):.2f} SOL",
            "explorers": {
                "Solscan": f"https://solscan.io/account/{wallet}",
                "Birdeye": f"https://birdeye.so/address/{wallet}"
            }
        }
