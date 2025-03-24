# ⚠️ Diese Datei sammelt alle @tool-Funktionen aus unseren spezialisierten Modulen.
# Sie dient als zentrale Registry für die Agent-Tools, die per LangChain benutzt werden.
# Halte sie aktuell, wenn du neue Tools baust – oder nutze Autodiscovery (in Zukunft).

from reddit_tools import get_reddit_data, count_mentions, analyze_sentiment, find_trending_cryptos
from youtube_tools import search_youtube, process_youtube_video, query_youtube_video
from cryptopanic_tools import get_latest_news, get_news_sources, get_last_news_title
from fearandgreed_tools import get_fear_and_greed_index
from gmgn_tools import get_trending_wallets, get_new_token_pairs, get_trending_tokens
from dexscreener_tools import (
    get_dex_liquidity_distribution,
    analyze_token_market_microstructure,
    get_chain_dex_volume_leaders,
    get_cross_chain_token_data,
    search_dexes_for_token
)

# CoinGecko Tools (neue Version)
from coingecko_tools import (
    get_current_price, get_market_chart, get_ohlc_data, get_coin_info,
    list_trending_coins, list_trending_coins
)

# Moralis Wallet & Token Tools (Solana)
from moralis_wallet_tools import (
    get_sol_balance, get_spl_tokens, get_portfolio_value,
    get_wallet_nfts, get_recent_swaps, get_wallet_risk_score, get_wallet_overview
)
from moralis_token_tools import (
    get_token_metadata, get_token_price, get_token_holder_count,
    get_token_dex_data, get_token_marketcap, get_token_risk_score, analyze_token,
    search_token, resolve_token_address
)





def import_tools():
    """
    🔧 Central registry for all tool functions used across the system.

    These tools provide access to external data sources like CoinGecko, Moralis, Reddit, YouTube, etc.
    All functions are designed to be compatible with LangChain's convert_to_openai_function interface.
    """
    tools = [

        # === CoinGecko Tools (neue Struktur) ===
        get_current_price,        # Aktueller Preis eines Tokens
        get_market_chart,      # Preis, Volumen und MarketCap über Zeit
        get_ohlc_data,         # OHLC-Daten (candlestick-style)
        get_coin_info,         # Coin-Beschreibung & Metadaten
        list_trending_coins,  # Trending Coins von CoinGecko
        list_trending_coins,   # Liste mit detaillierten Trendinfos

        # === Reddit Tools ===
        get_reddit_data,       # Gesamtdaten aus Reddit
        count_mentions,        # Erwähnungen eines Coins zählen
        analyze_sentiment,     # Sentiment zu einem Coin analysieren
        find_trending_cryptos, # Neue/trendende Coins auf Reddit finden

        # === YouTube Tools ===
        search_youtube,        # YouTube-Suche zu einem Coin
        process_youtube_video, # Transkription & Analyse eines Videos
        query_youtube_video,   # Metadaten & Analyse zu einem Video

        # === CryptoPanic News Tools ===
        get_latest_news,       # Neueste News (inkl. Sentiment)
        get_news_sources,      # Liste von Newsquellen
        get_last_news_title,   # Nur Headline der letzten News

        # === Fear and Greed Index ===
        get_fear_and_greed_index,  # Aktueller Marktstimmungsindex

        # === Moralis: Solana Wallet Tools ===
        get_sol_balance,       # SOL-Balance einer Wallet
        get_spl_tokens,        # Liste aller SPL-Tokens
        get_portfolio_value,   # Gesamtwert (USD)
        get_wallet_nfts,       # NFTs der Wallet
        get_recent_swaps,      # Letzte Swap-Transaktionen
        get_wallet_risk_score, # Wallet-Risiko-Bewertung
        get_wallet_overview,   # Komplettanalyse

        # === Moralis: Token Tools ===
        get_token_metadata,    # Token-Metadaten (Name, Supply etc.)
        get_token_price,       # Preis eines Tokens
        get_token_holder_count,# Anzahl Holder
        get_token_dex_data,    # Volumen & Liquidität (DexScreener)
        get_token_marketcap,   # Market Cap (Preis × Supply)
        get_token_risk_score,  # Bewertung Risikoindikatoren
        analyze_token,         # Vollanalyse
        search_token,          # Verbesserte Token-Suche (Name/Symbol/Adresse)
        resolve_token_address, # Token-Symbol/Name zu Adresse auflösen

        # === GMGN: Smart Money & Whale Tracking ===
        get_trending_wallets,  # Top-performing Wallets tracken
        get_new_token_pairs,   # Neue Token-Pairings finden
        get_trending_tokens,   # Trending Tokens finden

        # === DexScreener Tools ===
        get_dex_liquidity_distribution,
        analyze_token_market_microstructure,
        get_chain_dex_volume_leaders,
        get_cross_chain_token_data,
        search_dexes_for_token,
    ]

    return tools
