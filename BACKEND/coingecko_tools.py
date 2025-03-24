import logging
from typing import List, Dict, Union
from langchain.tools import tool
from pycoingecko import CoinGeckoAPI
import pandas as pd
import numpy as np


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
def get_current_price(coin_id: str, vs_currency: str = "usd") -> Dict[str, float]:
    """💵 Current price of a coin."""
    try:
        data = cg.get_price(ids=coin_id, vs_currencies=vs_currency)
        return data.get(coin_id, {})
    except Exception as e:
        logger.error(f"Price fetch failed for {coin_id}: {e}")
        return {}


@tool
def get_ohlc_data(coin_id: str, vs_currency: str = "usd", days: int = 1) -> List[List[float]]:
    """📊 OHLC (Open, High, Low, Close) for coin (max 90 days)."""
    try:
        return cg.get_coin_ohlc_by_id(id=coin_id, vs_currency=vs_currency, days=days)
    except Exception as e:
        logger.error(f"OHLC fetch failed for {coin_id}: {e}")
        return []


@tool
def get_market_chart(coin_id: str, vs_currency: str = "usd", days: int = 30) -> List[float]:
    """📉 Returns historical closing prices."""
    try:
        data = cg.get_coin_market_chart_by_id(id=coin_id, vs_currency=vs_currency, days=days)
        return [price[1] for price in data.get("prices", [])]
    except Exception as e:
        logger.error(f"Market chart fetch failed for {coin_id}: {e}")
        return []


@tool
def calculate_macd(prices: List[float], slow: int = 26, fast: int = 12, signal: int = 9) -> Dict[str, Union[float, str]]:
    """📈 MACD Indicator calculation."""
    try:
        s = pd.Series(prices)
        macd = s.ewm(span=fast).mean() - s.ewm(span=slow).mean()
        signal_line = macd.ewm(span=signal).mean()
        return {
            "macd": round(macd.iloc[-1], 4),
            "signal": round(signal_line.iloc[-1], 4),
            "trend": "bullish" if macd.iloc[-1] > signal_line.iloc[-1] else "bearish"
        }
    except Exception as e:
        logger.error(f"MACD calc failed: {e}")
        return {}


@tool
def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """📊 Calculates the RSI (Relative Strength Index)."""
    try:
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum()/period
        down = -seed[seed < 0].sum()/period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100. / (1. + rs)

        for i in range(period, len(prices)):
            delta = deltas[i - 1]
            upval = max(delta, 0)
            downval = max(-delta, 0)
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down if down != 0 else 0
            rsi[i] = 100. - 100. / (1. + rs)

        return round(float(rsi[-1]), 2)
    except Exception as e:
        logger.error(f"RSI calc failed: {e}")
        return 0.0


@tool
def get_coin_info(coin_id: str) -> Dict:
    """🔍 Returns full info for a specific coin ID."""
    try:
        return cg.get_coin_by_id(id=coin_id)
    except Exception as e:
        logger.error(f"Coin info fetch failed: {e}")
        return {}
