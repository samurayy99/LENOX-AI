import logging
from typing import List, Dict, Union
from langchain.tools import tool
from pycoingecko import CoinGeckoAPI



# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("coingecko")

# === Init API ===
cg = CoinGeckoAPI()


@tool
def list_trending_coins() -> List[str]:
    """📈 Lists trending coins on CoinGecko."""
    try:
        data = cg.get_search_trending()
        return [coin["item"]["id"] for coin in data["coins"]]
    except Exception as e:
        logger.error(f"Trending fetch failed: {e}")
        return []


@tool
def get_current_price(query: str, vs_currency: str = "usd") -> Dict[str, Union[float, str]]:
    """
    💵 Gibt den aktuellen Preis eines Coins zurück.
    Akzeptiert entweder den CoinGecko-ID, Symbol oder Namen.
    """
    try:
        # Bereinige die Anfrage von Präfixen wie $ oder @
        original_query = query
        clean_query = query.strip()
        if clean_query.startswith('$') or clean_query.startswith('@'):
            clean_query = clean_query[1:]
        
        # Versuche verschiedene Suchstrategien
        search_attempts = [
            clean_query,                      # Basissuche mit bereinigtem Query
            clean_query.lower(),              # Lowercase-Variante
            f"{clean_query} coin",            # "coin" anhängen für bessere Ergebnisse
            f"{clean_query} token"            # "token" anhängen für bessere Ergebnisse
        ]
        
        # Führe alle Suchversuche durch, bis wir Ergebnisse haben
        coins = []
        for attempt in search_attempts:
            if not attempt:  # Leere Strings überspringen
                continue
                
            search_result = cg.search(attempt)
            coins = search_result.get("coins", [])
            if coins:
                logger.info(f"Found results using search term: '{attempt}'")
                break
                
        if not coins:
            logger.warning(f"No matches found for any variation of query: {original_query}")
            return {"error": f"Kein Coin gefunden für '{original_query}'."}

        # Nimm den ersten Match als beste Vermutung
        matched_id = coins[0]["id"]
        matched_symbol = coins[0]["symbol"].upper()
        matched_name = coins[0]["name"]
        
        # Preis abrufen
        data = cg.get_price(ids=matched_id, vs_currencies=vs_currency)
        
        if not data or matched_id not in data:
            logger.warning(f"No price data for {matched_id}")
            return {"error": f"Kein Preis gefunden für {original_query} (ID: {matched_id})."}
        
        logger.info(f"Found price for {original_query} → {matched_name} ({matched_symbol})")
        return data.get(matched_id, {"error": f"Kein Preis gefunden für ID {matched_id}."})

    except Exception as e:
        logger.error(f"Price fetch failed for {query}: {e}")
        return {"error": str(e)}




@tool
def get_coin_info(coin_id: str) -> Dict:
    """🔍 Returns full info for a specific coin ID."""
    try:
        return cg.get_coin_by_id(id=coin_id)
    except Exception as e:
        logger.error(f"Coin info fetch failed: {e}")
        return {}
