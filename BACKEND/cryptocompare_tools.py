import os
import requests
import json
from typing import Dict, List, TypedDict
from langchain.agents import tool
from urllib.parse import urlencode
import asyncio
import aiohttp
from functools import lru_cache
import time

class APIError(Exception):
    """Custom API Error to handle exceptions from CryptoCompare requests."""
    def __init__(self, status_code, detail):
        super().__init__(f"API Error {status_code}: {detail}")
        
        
class OHLCVData(TypedDict):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class RateLimiter:
    def __init__(self, calls: int, period: float):
        self.calls = calls
        self.period = period
        self.timestamps: List[float] = []

    async def wait(self):
        now = time.time()
        self.timestamps = [t for t in self.timestamps if now - t < self.period]
        if len(self.timestamps) >= self.calls:
            await asyncio.sleep(self.period - (now - self.timestamps[0]))
        self.timestamps.append(time.time())

rate_limiter = RateLimiter(calls=50, period=1.0)

@lru_cache(maxsize=100)
def get_cached_price(symbol: str, currencies: str) -> Dict[str, float]:
    """
    Fetches and caches the current price of a specified cryptocurrency in one or more currencies.
    
    Args:
        symbol (str): The cryptocurrency symbol (e.g., 'BTC').
        currencies (str): Comma-separated list of currency symbols (e.g., 'USD,EUR').
    
    Returns:
        Dict[str, float]: A dictionary of currency symbols to prices.
    """
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    if not api_key:
        raise ValueError("API key not found. Please set the CRYPTOCOMPARE_API_KEY environment variable.")
    
    headers = {'authorization': f'Apikey {api_key}'}
    url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol}&tsyms={currencies}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))

@tool
async def get_ohlcv_data(symbol: str, currency: str = 'USD', interval: str = 'day', limit: int = 30) -> List[OHLCVData]:
    """Fetches OHLCV data for a specified cryptocurrency."""
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    params = {
        'fsym': symbol,
        'tsym': currency,
        'limit': limit
    }
    url = f"https://min-api.cryptocompare.com/data/v2/histo{interval}?{urlencode(params)}"
    
    await rate_limiter.wait()
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                await asyncio.sleep(retry_after)
                return await get_ohlcv_data(symbol, currency, interval, limit)
            
            response.raise_for_status()
            data = await response.json()
            
            if 'Data' not in data or 'Data' not in data['Data']:
                raise KeyError("Missing 'Data' key in the response.")
            
            return [OHLCVData(**item) for item in data['Data']['Data']]


@tool
def get_cryptocompare_current_price(symbol: str, currencies: str = 'USD') -> str:
    """Fetches the current price of a specified cryptocurrency in one or more currencies."""
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    if not api_key:
        return "API key not found. Please set the CRYPTOCOMPARE_API_KEY environment variable."
    
    headers = {'authorization': f'Apikey {api_key}'}
    url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol}&tsyms={currencies}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return f"Current prices for {symbol}: {response.json()}"
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))


@tool
def get_latest_social_stats(coin_identifier: str) -> str:
    """Retrieves the latest social statistics for a given cryptocurrency symbol or ID."""
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    
    # Check if the input is a number (ID) or string (symbol)
    if coin_identifier.isdigit():
        url = f"https://min-api.cryptocompare.com/data/social/coin/latest?coinId={coin_identifier}"
    else:
        # If it's a symbol, we need to first get the coinId
        symbol_url = f"https://min-api.cryptocompare.com/data/coin/generalinfo?fsyms={coin_identifier.upper()}&tsym=USD"
        try:
            symbol_response = requests.get(symbol_url, headers=headers)
            symbol_response.raise_for_status()
            symbol_data = symbol_response.json()
            if 'Data' in symbol_data and symbol_data['Data']:
                coin_id = symbol_data['Data'][0]['CoinInfo']['Id']
                url = f"https://min-api.cryptocompare.com/data/social/coin/latest?coinId={coin_id}"
            else:
                return f"Error: Could not find coin ID for symbol {coin_identifier}"
        except requests.RequestException as e:
            raise APIError(symbol_response.status_code, str(e))
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if 'Data' in data:
            coin_symbol = data['Data'].get('General', {}).get('Name', 'Unknown')
            coin_id = data['Data'].get('General', {}).get('Id', 'Unknown')
            coin_url = f"https://www.cryptocompare.com/coins/{coin_symbol.lower()}/overview"
            return f"Latest social stats for {coin_symbol} (ID: {coin_id}): {data['Data']}. More details at: {coin_url}"
        else:
            return f"Error: No data found for coin {coin_identifier}"
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))

@tool
def get_historical_social_stats(coin_symbol: str, days: int = 30) -> str:
    """Fetches historical social data for a given cryptocurrency over a specified number of days."""
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    url = f"https://min-api.cryptocompare.com/data/social/coin/histo/day?fsym={coin_symbol}&limit={days}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        coin_url = f"https://www.cryptocompare.com/coins/{coin_symbol}/overview"
        return f"Historical social stats for {coin_symbol} over the last {days} days: {data}. More details at: {coin_url}"
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))


@tool
def list_news_feeds_and_categories() -> str:
    """Lists all news feeds and categories available from CryptoCompare."""
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    url = "https://min-api.cryptocompare.com/data/news/feedsandcategories"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return f"News feeds and categories: {response.json()}. More details at: <a href='{url}'>CryptoCompare News</a>"
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))
    
    
@tool
def get_latest_trading_signals(coin_symbol: str) -> str:
    """
    Fetches comprehensive market insights and sentiment analysis for a specified cryptocurrency symbol.

    This function retrieves advanced trading signals from CryptoCompare, including:
    - In/Out of the Money: Indicates if holders are in profit or loss
    - Address Net Growth: Shows the growth rate of new addresses
    - Concentration: Reveals changes in token distribution among holders
    - Large Transactions: Tracks significant money movements

    Each signal comes with a sentiment (bullish, bearish, or neutral) and a score,
    providing a nuanced view of the current market dynamics.

    Args:
        coin_symbol (str): The symbol of the cryptocurrency (e.g., 'BTC' for Bitcoin)

    Returns:
        str: A detailed analysis of the latest trading signals, including sentiment and potential market implications.

    Raises:
        APIError: If there's an issue with the API request or response.
    """
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    url = f"https://min-api.cryptocompare.com/data/tradingsignals/intotheblock/latest?fsym={coin_symbol}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return f"Latest trading signals for {coin_symbol}: {data}."
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))

@tool
def get_top_exchanges_by_volume(fsym: str, tsym: str, limit: int = 10) -> str:
    """Fetches top exchanges by volume for a specific trading pair."""
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    url = f"https://min-api.cryptocompare.com/data/top/exchanges?fsym={fsym}&tsym={tsym}&limit={limit}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return f"Top exchanges by volume for {fsym}/{tsym}: {response.json()}"
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))

@tool
def get_historical_daily(symbol: str, currency: str = 'USD', limit: int = 30) -> str:
    """Retrieves the daily historical data for a specific cryptocurrency in a given currency."""
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={symbol}&tsym={currency}&limit={limit}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if 'Data' not in data or 'Data' not in data['Data']:
            raise KeyError("Missing 'Data' key in the response.")
        historical_data = data['Data']['Data']
        coin_url = f"https://www.cryptocompare.com/coins/{symbol}/overview"
        return f"Historical daily data for {symbol} to {currency}: {historical_data}. More details at: {coin_url}"
    except KeyError as e:
        return f"Error: {str(e)}. Unable to retrieve historical daily data for {symbol}."
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))

@tool
def get_top_volume_symbols(currency: str = 'USD', limit: int = 10, page: int = 0) -> str:
    """
    Fetches the top cryptocurrencies by 24-hour trading volume in a specific currency.
    Args:
        currency (str): The currency symbol to consider for volume (e.g., 'USD').
        limit (int): Number of top symbols to retrieve.
        page (int): The pagination for the request.
    Returns:
        str: List of top cryptocurrencies by volume.
    """
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    url = f"https://min-api.cryptocompare.com/data/top/totalvolfull?tsym={currency}&limit={limit}&page={page}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Debug logging of the full response
        print(json.dumps(data, indent=4))

        if 'Data' not in data:
            raise KeyError("Missing 'Data' in the response")

        symbols = {item['CoinInfo']['Name']: item['RAW'][currency]['VOLUME24HOURTO'] for item in data['Data'] if 'RAW' in item and currency in item['RAW']}
        return f"Top {limit} symbols by 24-hour volume in {currency}: {symbols}"
    except KeyError as e:
        print(f"Error: Missing expected data in the response: {str(e)}")
        return f"Error: Missing expected data in the response: {str(e)}"
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))