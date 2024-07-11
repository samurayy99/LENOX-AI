from reddit_tools import get_reddit_data, count_mentions, analyze_sentiment, find_trending_cryptos
from cryptocompare_tools import (
    get_cryptocompare_current_price, get_top_volume_symbols,
    get_latest_social_stats, get_historical_social_stats, list_news_feeds_and_categories,
    get_latest_trading_signals as get_crypto_compare_latest_trading_signals, get_top_exchanges_by_volume, get_historical_daily
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
from integration_tools import get_current_price, get_historical_prices, comment_on_price






def import_tools():
    """
    Collects and returns a list of functions for various external data retrieval and processing tasks.
    Each tool function is designed to be compatible with LangChain's convert_to_openai_function, which expects
    callable objects.
    """
    tools = [
        # CryptoCompare Tools
        get_cryptocompare_current_price,  # Retrieves the current price of a specified cryptocurrency.
        get_top_volume_symbols,  # Retrieves the top cryptocurrencies by trading volume.
        get_latest_social_stats,  # Retrieves the latest social media statistics for a specified cryptocurrency.
        get_historical_social_stats,  # Retrieves historical social media statistics for a specified cryptocurrency.
        list_news_feeds_and_categories,  # Lists available news feeds and their categories from CryptoCompare.
        get_crypto_compare_latest_trading_signals,  # Retrieves the latest trading signals from CryptoCompare.
        get_top_exchanges_by_volume,  # Retrieves the top cryptocurrency exchanges by trading volume.
        get_historical_daily,  # Retrieves the daily historical data for a specific cryptocurrency in a given currency.

        # CoinGecko Tools
        get_market_data,  # Retrieves current market data for a specified cryptocurrency.
        get_historical_market_data,  # Retrieves historical market data for a specified cryptocurrency.
        get_ohlc,  # Retrieves OHLC (Open, High, Low, Close) data for a specified cryptocurrency.
        get_trending_cryptos,  # Retrieves the list of trending cryptocurrencies.
        calculate_macd,  # Calculates the MACD (Moving Average Convergence Divergence) for a specified cryptocurrency.
        get_exchange_rates,  # Retrieves current exchange rates for a specified cryptocurrency.
        calculate_rsi,  # Calculates the RSI (Relative Strength Index) for a specified cryptocurrency.

        # Reddit Tools
        get_reddit_data,  # Retrieves data from Reddit for a specified cryptocurrency.
        count_mentions,  # Counts the number of mentions of a specified cryptocurrency on Reddit.
        analyze_sentiment,  # Analyzes sentiment of Reddit posts for a specified cryptocurrency.
        find_trending_cryptos,  # Finds trending cryptocurrencies and new coins being discussed on Reddit.

        # YouTube Tools
        search_youtube,  # Searches YouTube for videos related to a specified cryptocurrency.
        process_youtube_video,  # Processes a YouTube video to extract relevant data.
        query_youtube_video,  # Queries detailed information about a specific YouTube video.

        # CoinPaprika Tools
        get_coin_details,  # Retrieves detailed information about a specified cryptocurrency.
        get_coin_tags,  # Retrieves tags associated with a specified cryptocurrency.
        get_market_overview,  # Retrieves an overview of the cryptocurrency market.
        get_ticker_info,  # Retrieves ticker information for a specified cryptocurrency.

        # CryptoPanic Tools
        get_latest_news,  # Retrieves the latest news from CryptoPanic.
        get_news_sources,  # Retrieves a list of news sources from CryptoPanic.
        get_last_news_title,  # Retrieves the title of the most recent news article from CryptoPanic.

        # CoinMarketCap Tools
        get_latest_listings,  # Retrieves the latest listings of cryptocurrencies from CoinMarketCap.
        get_crypto_metadata,  # Retrieves metadata for a specified cryptocurrency.
        get_global_metrics,  # Retrieves global metrics for the cryptocurrency market.

        # Fear and Greed Index Tools
        get_fear_and_greed_index,  # Retrieves the Fear and Greed Index for the cryptocurrency market.

        # Whale Alert Tools
        get_whale_alert_status,  # Retrieves the current status of Whale Alert.
        get_transaction_by_hash,  # Retrieves details of a specific transaction by its hash.
        get_recent_transactions,  # Retrieves recent large transactions in the cryptocurrency market.

        # Binance Tools
        get_binance_ticker,  # Retrieves the current ticker price from Binance.
        get_binance_order_book,  # Retrieves the order book for a specified cryptocurrency on Binance.
        get_binance_recent_trades,  # Retrieves recent trades for a specified cryptocurrency on Binance.

        # Integration Tools
        get_current_price,
        get_historical_prices,
        comment_on_price,
        
    
        
    ]
    return tools