# ⚠️ Diese Datei sammelt alle @tool-Funktionen aus unseren spezialisierten Modulen.
# Sie dient als zentrale Registry für die Agent-Tools, die per LangChain benutzt werden.
# Halte sie aktuell, wenn du neue Tools baust – oder nutze Autodiscovery (in Zukunft).

from reddit_tools import (
    find_trending_solana_memecoins, 
    get_memecoin_sentiment, 
    track_memecoin_mentions, 
    detect_new_memecoin_launches
)
from youtube_tools import get_token_youtube_alpha, get_influencer_youtube_alpha
from cryptopanic_tools import get_latest_news, get_last_news_title
from gmgn_tools import get_trending_wallets, get_new_token_pairs, get_trending_tokens, get_recent_pairs, diagnose_gmgn_status
from dexscreener_tools import (
    get_dex_liquidity_distribution,
    analyze_token_market_microstructure,
    get_trending_dex_pairs,
    get_newest_dex_pairs,
    get_top_gaining_dex_pairs
)

# Advanced Token Analysis Tools (combines data across sources)
from advanced_token_analysis import (
    find_new_tokens_with_smart_wallet_activity,
    find_high_volume_new_tokens
)

# Twitter Tools (X.com Datensammlung)
from twitter_tools import (
    search_tweets,
    analyze_token_sentiment,
    check_influencer_posts,
    scan_twitter_for_alpha
)

# CoinGecko Tools (neue Version)
from coingecko_tools import (
    get_current_price, get_coin_info,
    list_trending_coins
)

# Moralis Solana Tools (vereint Wallet & Token Analyse)
from moralis_tools import (
    # Token-bezogene Tools
    get_token_metadata, get_token_price, get_token_holder_count,
    get_token_dex_data, get_token_marketcap, get_token_risk_score, 
    analyze_token, resolve_token_address,
    
    # Wallet-bezogene Tools
    get_sol_balance, get_spl_tokens, get_portfolio_value,
    get_wallet_nfts, get_recent_swaps, get_wallet_risk_score, 
    get_wallet_overview, get_wallet_trading_stats, get_wallet_portfolio_allocation,
    
    # Erweiterte Analysetools
    analyze_wallet_transactions, compare_wallets, get_token_holders_analysis
)

def import_tools():
    """
    🔧 Central registry for all tool functions used across the system.

    These tools provide access to external data sources like CoinGecko, Moralis, Reddit, YouTube, etc.
    All functions are designed to be compatible with LangChain's convert_to_openai_function interface.
    """
    tools = [
        # === Advanced Token Analysis (High-Level Alpha) ===
        find_new_tokens_with_smart_wallet_activity,
        find_high_volume_new_tokens,

        # === CoinGecko Tools (neue Struktur) ===
        get_current_price,        # Aktueller Preis eines Tokens
        get_coin_info,         # Coin-Beschreibung & Metadaten
        list_trending_coins,  # Trending Coins von CoinGecko
        
        # === Reddit Solana Memecoin Tools ===
        find_trending_solana_memecoins,  # Trendende Solana Memecoins entdecken
        get_memecoin_sentiment,          # Sentiment für ein bestimmtes Memecoin
        track_memecoin_mentions,         # Entwicklung der Erwähnungen über Zeit
        detect_new_memecoin_launches,    # Neue Memecoin-Launches mit Risikobewertung

        # === YouTube Tools ===
        get_token_youtube_alpha,     # Sucht und analysiert YouTube-Videos zu einem Token
        get_influencer_youtube_alpha, # Überwacht vordefinierte Solana-Influencer für Trading-Tipps

        # === Twitter/X Tools ===
        search_tweets,               # Tweets zu einem Token/Hashtag suchen
        analyze_token_sentiment,     # Twitter-Sentiment für ein Token analysieren  
        check_influencer_posts,      # Überwacht führende Memecoin-Influencer
        scan_twitter_for_alpha,      # Erkennt neue Launches und Alpha-Signale

        # === CryptoPanic News Tools ===
        get_latest_news,       # Neueste News (inkl. Sentiment)
        get_last_news_title,   # Nur Headline der letzten News

        # === Moralis: Solana Tools (unified) ===
        # Token-Tools
        resolve_token_address, # Token-Symbol/Name zu Adresse auflösen
        get_token_metadata,    # Token-Metadaten (Name, Supply etc.)
        get_token_price,       # Preis eines Tokens
        get_token_holder_count,# Anzahl Holder
        get_token_dex_data,    # Volumen & Liquidität (DexScreener)
        get_token_marketcap,   # Market Cap (Preis × Supply)
        get_token_risk_score,  # Bewertung Risikoindikatoren
        analyze_token,         # Vollanalyse eines Tokens mit Insights
        get_token_holders_analysis, # Analyse der Top-Holder
        
        # Wallet-Tools
        get_sol_balance,       # SOL-Balance einer Wallet
        get_spl_tokens,        # Liste aller SPL-Tokens
        get_portfolio_value,   # Gesamtwert (USD)
        get_wallet_nfts,       # NFTs der Wallet
        get_recent_swaps,      # Letzte Swap-Transaktionen
        get_wallet_trading_stats, # Detaillierte Trading-Statistiken
        get_wallet_portfolio_allocation, # Portfolio-Breakdown mit Prozentanteilen
        get_wallet_risk_score, # Wallet-Risiko-Bewertung
        get_wallet_overview,   # Komplettanalyse

        # Erweiterte Analysen
        analyze_wallet_transactions, # Tiefgreifende Verhaltensanalyse
        compare_wallets,       # Mehrere Wallets vergleichen & Beziehungen finden

        # === GMGN: Smart Money & Whale Tracking ===
        get_trending_wallets,  # Top-performing Wallets tracken
        get_new_token_pairs,   # Neue Token-Pairings finden
        get_trending_tokens,   # Trending Tokens finden
        get_recent_pairs,      # Alternative Methode für neue Pairs
        diagnose_gmgn_status,  # Diagnose der GMGN-API-Endpunkte

        # === DexScreener Tools ===
        get_dex_liquidity_distribution,        # Token-Liquiditätsverteilung über DEXes
        analyze_token_market_microstructure,   # Detaillierte Marktanalyse eines Tokens
        get_trending_dex_pairs,                # Trendende Handelspaare auf DEXes
        get_newest_dex_pairs,                  # Neueste Handelspaare auf DEXes 
        get_top_gaining_dex_pairs              # Paare mit höchsten Kursgewinnen
    ]

    return tools
