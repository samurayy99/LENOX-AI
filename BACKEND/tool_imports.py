from reddit_tools import get_reddit_data, count_mentions, analyze_sentiment, find_trending_topics
from cryptocompare_tools import (
    get_current_price, get_top_volume_symbols,
    get_latest_social_stats, get_historical_social_stats, list_news_feeds_and_categories,
    get_latest_trading_signals, get_top_exchanges_by_volume, get_historical_daily
)
from coingecko_tools import (
    get_market_data, get_historical_market_data, get_ohlc,
    get_trending_cryptos, calculate_macd, get_exchange_rates, calculate_rsi
)
from youtube_tools import search_youtube, process_youtube_video, query_youtube_video
from coinpaprika_tools import get_coin_details, get_coin_tags, get_market_overview, get_ticker_info
from cryptopanic_tools import get_latest_news, get_news_sources, get_last_news_title
from coinmarketcap_tools import get_latest_listings, get_crypto_metadata, get_global_metrics
from fearandgreed_tools import get_fear_and_greed_index
from whale_alert_tools import get_whale_alert_status, get_transaction_by_hash, get_recent_transactions
from binance_tools import get_binance_ticker, get_binance_order_book, get_binance_recent_trades
from integration_tools import get_current_price as binance_get_current_price, get_historical_prices, comment_on_price

# Define tools using the @tool decorator
from langchain_core.tools import tool

# Reddit Tools
@tool
def get_reddit_data(query: str) -> dict:
    """Retrieves data from Reddit for a specified cryptocurrency."""
    return get_reddit_data(query)

@tool
def count_mentions(query: str) -> dict:
    """Counts the number of mentions of a specified cryptocurrency on Reddit."""
    return count_mentions(query)

@tool
def analyze_sentiment(query: str) -> dict:
    """Analyzes sentiment of Reddit posts for a specified cryptocurrency."""
    return analyze_sentiment(query)

@tool
def find_trending_topics(query: str) -> dict:
    """Finds trending topics related to cryptocurrencies on Reddit."""
    return find_trending_topics(query)

# CryptoCompare Tools
@tool
def get_current_price(query: str) -> dict:
    """Retrieves the current price of a specified cryptocurrency."""
    return get_current_price(query)

@tool
def get_top_volume_symbols(query: str) -> dict:
    """Retrieves the top cryptocurrencies by trading volume."""
    return get_top_volume_symbols(query)

@tool
def get_latest_social_stats(query: str) -> dict:
    """Retrieves the latest social media statistics for a specified cryptocurrency."""
    return get_latest_social_stats(query)

@tool
def get_historical_social_stats(query: str) -> dict:
    """Retrieves historical social media statistics for a specified cryptocurrency."""
    return get_historical_social_stats(query)

@tool
def list_news_feeds_and_categories(query: str) -> dict:
    """Lists available news feeds and their categories from CryptoCompare."""
    return list_news_feeds_and_categories(query)

@tool
def get_latest_trading_signals(query: str) -> dict:
    """Retrieves the latest trading signals from CryptoCompare."""
    return get_latest_trading_signals(query)

@tool
def get_top_exchanges_by_volume(query: str) -> dict:
    """Retrieves the top cryptocurrency exchanges by trading volume."""
    return get_top_exchanges_by_volume(query)

@tool
def get_historical_daily(query: str) -> dict:
    """Retrieves the daily historical data for a specific cryptocurrency in a given currency."""
    return get_historical_daily(query)

# CoinGecko Tools
@tool
def get_market_data(query: str) -> dict:
    """Retrieves current market data for a specified cryptocurrency."""
    return get_market_data(query)

@tool
def get_historical_market_data(query: str) -> dict:
    """Retrieves historical market data for a specified cryptocurrency."""
    return get_historical_market_data(query)

@tool
def get_ohlc(query: str) -> dict:
    """Retrieves OHLC (Open, High, Low, Close) data for a specified cryptocurrency."""
    return get_ohlc(query)

@tool
def get_trending_cryptos(query: str) -> dict:
    """Retrieves the list of trending cryptocurrencies."""
    return get_trending_cryptos(query)

@tool
def calculate_macd(query: str) -> dict:
    """Calculates the MACD (Moving Average Convergence Divergence) for a specified cryptocurrency."""
    return calculate_macd(query)

@tool
def get_exchange_rates(query: str) -> dict:
    """Retrieves current exchange rates for a specified cryptocurrency."""
    return get_exchange_rates(query)

@tool
def calculate_rsi(query: str) -> dict:
    """Calculates the RSI (Relative Strength Index) for a specified cryptocurrency."""
    return calculate_rsi(query)

# YouTube Tools
@tool
def search_youtube(query: str) -> dict:
    """Searches YouTube for videos related to a specified cryptocurrency."""
    return search_youtube(query)

@tool
def process_youtube_video(query: str) -> dict:
    """Processes a YouTube video to extract relevant data."""
    return process_youtube_video(query)

@tool
def query_youtube_video(query: str) -> dict:
    """Queries detailed information about a specific YouTube video."""
    return query_youtube_video(query)

# CoinPaprika Tools
@tool
def get_coin_details(query: str) -> dict:
    """Retrieves detailed information about a specified cryptocurrency."""
    return get_coin_details(query)

@tool
def get_coin_tags(query: str) -> dict:
    """Retrieves tags associated with a specified cryptocurrency."""
    return get_coin_tags(query)

@tool
def get_market_overview(query: str) -> dict:
    """Retrieves an overview of the cryptocurrency market."""
    return get_market_overview(query)

@tool
def get_ticker_info(query: str) -> dict:
    """Retrieves ticker information for a specified cryptocurrency."""
    return get_ticker_info(query)

# CryptoPanic Tools
@tool
def get_latest_news(query: str) -> dict:
    """Retrieves the latest news from CryptoPanic."""
    return get_latest_news(query)

@tool
def get_news_sources(query: str) -> dict:
    """Retrieves a list of news sources from CryptoPanic."""
    return get_news_sources(query)

@tool
def get_last_news_title(query: str) -> dict:
    """Retrieves the title of the most recent news article from CryptoPanic."""
    return get_last_news_title(query)

# CoinMarketCap Tools
@tool
def get_latest_listings(query: str) -> dict:
    """Retrieves the latest listings of cryptocurrencies from CoinMarketCap."""
    return get_latest_listings(query)

@tool
def get_crypto_metadata(query: str) -> dict:
    """Retrieves metadata for a specified cryptocurrency."""
    return get_crypto_metadata(query)

@tool
def get_global_metrics(query: str) -> dict:
    """Retrieves global metrics for the cryptocurrency market."""
    return get_global_metrics(query)

# Fear and Greed Index Tools
@tool
def get_fear_and_greed_index(query: str) -> dict:
    """Retrieves the Fear and Greed Index for the cryptocurrency market."""
    return get_fear_and_greed_index(query)

# Whale Alert Tools
@tool
def get_whale_alert_status(query: str) -> dict:
    """Retrieves the current status of Whale Alert."""
    return get_whale_alert_status(query)

@tool
def get_transaction_by_hash(query: str) -> dict:
    """Retrieves details of a specific transaction by its hash."""
    return get_transaction_by_hash(query)

@tool
def get_recent_transactions(query: str) -> dict:
    """Retrieves recent large transactions in the cryptocurrency market."""
    return get_recent_transactions(query)

# Binance Tools
@tool
def get_binance_ticker(query: str) -> dict:
    """Retrieves the current ticker price from Binance."""
    return get_binance_ticker(query)

@tool
def get_binance_order_book(query: str) -> dict:
    """Retrieves the order book for a specified cryptocurrency on Binance."""
    return get_binance_order_book(query)

@tool
def get_binance_recent_trades(query: str) -> dict:
    """Retrieves recent trades for a specified cryptocurrency on Binance."""
    return get_binance_recent_trades(query)

# Integration Tools
@tool
def binance_get_current_price(query: str) -> dict:
    """Retrieves the current price of a specified cryptocurrency from Binance."""
    return binance_get_current_price(query)

@tool
def get_historical_prices(query: str) -> dict:
    """Retrieves historical prices for a specified cryptocurrency."""
    return get_historical_prices(query)

@tool
def comment_on_price(query: str) -> dict:
    """Generates a comment on the current price of a specified cryptocurrency."""
    return comment_on_price(query)

# Collect all tools into a list
tools = [
    # Reddit Tools
    get_reddit_data, count_mentions, analyze_sentiment, find_trending_topics,

    # CryptoCompare Tools
    get_current_price, get_top_volume_symbols, get_latest_social_stats,
    get_historical_social_stats, list_news_feeds_and_categories, get_latest_trading_signals,
    get_top_exchanges_by_volume, get_historical_daily,

    # CoinGecko Tools
    get_market_data, get_historical_market_data, get_ohlc,
    get_trending_cryptos, calculate_macd, get_exchange_rates, calculate_rsi,

    # YouTube Tools
    search_youtube, process_youtube_video, query_youtube_video,

    # CoinPaprika Tools
    get_coin_details, get_coin_tags, get_market_overview, get_ticker_info,

    # CryptoPanic Tools
    get_latest_news, get_news_sources, get_last_news_title,

    # CoinMarketCap Tools
    get_latest_listings, get_crypto_metadata, get_global_metrics,

    # Fear and Greed Index Tools
    get_fear_and_greed_index,

    # Whale Alert Tools
    get_whale_alert_status, get_transaction_by_hash, get_recent_transactions,

    # Binance Tools
    get_binance_ticker, get_binance_order_book, get_binance_recent_trades,

    # Integration Tools
    binance_get_current_price, get_historical_prices, comment_on_price,
]

__all__ = ['tools']
