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

# Define tools using the @tool decorator
from langchain_core.tools import tool

# Reddit Tools
@tool
def get_reddit_data(query: str) -> dict:
    return get_reddit_data(query)

@tool
def count_mentions(query: str) -> dict:
    return count_mentions(query)

@tool
def analyze_sentiment(query: str) -> dict:
    return analyze_sentiment(query)

@tool
def find_trending_topics(query: str) -> dict:
    return find_trending_topics(query)

# CryptoCompare Tools
@tool
def get_current_price(query: str) -> dict:
    return get_current_price(query)

@tool
def get_top_volume_symbols(query: str) -> dict:
    return get_top_volume_symbols(query)

@tool
def get_latest_social_stats(query: str) -> dict:
    return get_latest_social_stats(query)

@tool
def get_historical_social_stats(query: str) -> dict:
    return get_historical_social_stats(query)

@tool
def list_news_feeds_and_categories(query: str) -> dict:
    return list_news_feeds_and_categories(query)

@tool
def get_latest_trading_signals(query: str) -> dict:
    return get_latest_trading_signals(query)

@tool
def get_top_exchanges_by_volume(query: str) -> dict:
    return get_top_exchanges_by_volume(query)

@tool
def get_historical_daily(query: str) -> dict:
    return get_historical_daily(query)

# CoinGecko Tools
@tool
def get_market_data(query: str) -> dict:
    return get_market_data(query)

@tool
def get_historical_market_data(query: str) -> dict:
    return get_historical_market_data(query)

@tool
def get_ohlc(query: str) -> dict:
    return get_ohlc(query)

@tool
def get_trending_cryptos(query: str) -> dict:
    return get_trending_cryptos(query)

@tool
def calculate_macd(query: str) -> dict:
    return calculate_macd(query)

@tool
def get_exchange_rates(query: str) -> dict:
    return get_exchange_rates(query)

@tool
def calculate_rsi(query: str) -> dict:
    return calculate_rsi(query)

# YouTube Tools
@tool
def search_youtube(query: str) -> dict:
    return search_youtube(query)

@tool
def process_youtube_video(query: str) -> dict:
    return process_youtube_video(query)

@tool
def query_youtube_video(query: str) -> dict:
    return query_youtube_video(query)

# CoinPaprika Tools
@tool
def get_coin_details(query: str) -> dict:
    return get_coin_details(query)

@tool
def get_coin_tags(query: str) -> dict:
    return get_coin_tags(query)

@tool
def get_market_overview(query: str) -> dict:
    return get_market_overview(query)

@tool
def get_ticker_info(query: str) -> dict:
    return get_ticker_info(query)

# CryptoPanic Tools
@tool
def get_latest_news(query: str) -> dict:
    return get_latest_news(query)

@tool
def get_news_sources(query: str) -> dict:
    return get_news_sources(query)

@tool
def get_last_news_title(query: str) -> dict:
    return get_last_news_title(query)

# CoinMarketCap Tools
@tool
def get_latest_listings(query: str) -> dict:
    return get_latest_listings(query)

@tool
def get_crypto_metadata(query: str) -> dict:
    return get_crypto_metadata(query)

@tool
def get_global_metrics(query: str) -> dict:
    return get_global_metrics(query)

# Fear and Greed Index Tools
@tool
def get_fear_and_greed_index(query: str) -> dict:
    return get_fear_and_greed_index(query)

# Whale Alert Tools
@tool
def get_whale_alert_status(query: str) -> dict:
    return get_whale_alert_status(query)

@tool
def get_transaction_by_hash(query: str) -> dict:
    return get_transaction_by_hash(query)

@tool
def get_recent_transactions(query: str) -> dict:
    return get_recent_transactions(query)

# Binance Tools
@tool
def get_binance_ticker(query: str) -> dict:
    return get_binance_ticker(query)

@tool
def get_binance_order_book(query: str) -> dict:
    return get_binance_order_book(query)

@tool
def get_binance_recent_trades(query: str) -> dict:
    return get_binance_recent_trades(query)

# Integration Tools
@tool
def binance_get_current_price(query: str) -> dict:
    return binance_get_current_price(query)

@tool
def get_historical_prices(query: str) -> dict:
    return get_historical_prices(query)

@tool
def comment_on_price(query: str) -> dict:
    return comment_on_price(query)

# Collect all tools into a list
tools = [
    get_reddit_data, count_mentions, analyze_sentiment, find_trending_topics,
    get_current_price, get_top_volume_symbols, get_latest_social_stats,
    get_historical_social_stats, list_news_feeds_and_categories, get_latest_trading_signals,
    get_top_exchanges_by_volume, get_historical_daily, get_market_data,
    get_historical_market_data, get_ohlc, get_trending_cryptos, calculate_macd,
    get_exchange_rates, calculate_rsi, search_youtube, process_youtube_video,
    query_youtube_video, get_coin_details, get_coin_tags, get_market_overview,
    get_ticker_info, get_latest_news, get_news_sources, get_last_news_title,
    get_latest_listings, get_crypto_metadata, get_global_metrics, get_fear_and_greed_index,
    get_whale_alert_status, get_transaction_by_hash, get_recent_transactions,
    get_binance_ticker, get_binance_order_book, get_binance_recent_trades,
    binance_get_current_price, get_historical_prices, comment_on_price
]

__all__ = ['tools']
