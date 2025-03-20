import os
from dune_client.client import DuneClient
from langchain.tools import tool



DUNE_API_KEY = os.getenv('DUNE_API_KEY')
dune = DuneClient(DUNE_API_KEY or '') 



@tool
def get_ethereum_daily_activity():
    """
    Retrieves daily active users and receiving addresses on Ethereum since 2023.

    This function provides a daily breakdown of Ethereum network activity,
    offering insights into user engagement and transaction patterns.

    Returns:
        dict: A dictionary containing:
            - 'time': The date of the activity
            - 'active_users': Number of unique addresses that initiated transactions
            - 'receiving_addresses': Number of unique addresses that received transactions

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3930800)
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching Ethereum daily activity: {str(e)}"


@tool
def get_dex_volume_rankings():
    """
    Fetches and ranks DEX (Decentralized Exchange) projects by trading volume.

    This function retrieves data on DEX trading volumes for the last 7 days and 24 hours.
    It provides insights into the most active DEX projects and their relative market share.

    Returns:
        dict: A dictionary containing:
            - 'Rank': The DEX's rank by volume
            - 'Project': Name of the DEX project
            - '7 Days Volume': Trading volume over the last 7 days in USD
            - '24 Hours Volume': Trading volume over the last 24 hours in USD

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3929505)  # Make sure this query ID is correct
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching DEX volume rankings: {str(e)}"


@tool
def get_nft_market_activity_metrics():
    """
    Fetches daily and weekly NFT market volume and activity metrics across major marketplaces.

    This function provides comprehensive data on NFT trading activity,
    including volume, unique buyers and sellers, for both daily and weekly timeframes.

    Returns:
        dict: A dictionary containing:
            - 'period': 'daily' or 'weekly'
            - 'date': The date or week of the data point
            - 'platform': Name of the NFT marketplace
            - 'volume_usd': Trading volume in USD
            - 'unique_sellers': Number of unique seller addresses
            - 'unique_buyers': Number of unique buyer addresses

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3930460)  
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching NFT market activity metrics: {str(e)}"

@tool
def get_crypto_sector_performance_analysis(period='24h'):
    """
    Analyzes the relative performance of different crypto sectors over a specified time period.

    This function calculates various metrics including price growth, relative strategy,
    and relative strength for different crypto narratives or sectors.

    Args:
        period (str): The time period for analysis. Can be '24h', '7d', or '30d'.

    Returns:
        dict: A dictionary containing:
            - 'narrative': The crypto sector or narrative
            - 'price_growth': Percentage price change over the period
            - 'relative_strategy': A metric comparing sector performance to Bitcoin
            - 'relative_strength': A metric comparing sector performance to the overall market
            - 'optimized_relative_strength': Combined metric of relative strength and strategy
            - 'signal': 'Leading' or 'Lagging' based on the optimized relative strength

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    query_ids = {'24h': 3930578, '7d': 3932113, '30d': 3932117}
    try:
        query_result = dune.get_latest_result(query_ids[period])  
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching crypto sector performance analysis: {str(e)}"

@tool
def get_bitcoin_etf_analysis():
    """
    Fetches and analyzes comprehensive data on Bitcoin ETFs, including TVL, market share, fees, and address verification.

    This function provides a detailed overview of various Bitcoin ETF products.

    Returns:
        dict: A dictionary containing for each ETF:
            - 'plain_issuer': Name of the ETF issuer
            - 'issuer': Linked name of the ETF issuer (with hyperlink)
            - 'tvl': Total Value Locked in the ETF (in BTC)
            - 'usd_value': USD value of the TVL
            - 'percentage_of_total': Market share of the ETF
            - 'etf_ticker': Ticker symbol of the ETF
            - 'percentage_fee': Management fee of the ETF
            - 'address_source': Verification status of the ETF's Bitcoin addresses
                (🟢: Proof of Reserves, 🔵: Proof of Addresses, 🟠: Unverified)

    The function uses blockchain data to calculate TVL and integrates with external sources for address verification.

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3930609)
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching Bitcoin ETF analysis: {str(e)}"


@tool
def get_ethereum_staking_analysis():
    """
    Analyzes Ethereum staking data for various entities and sub-entities.

    Returns:
        dict: For each entity:
            - 'ranking': Rank based on staked amount
            - 'entity': Name of staking entity (with hyperlink if available)
            - 'entity_just_name': Plain text name
            - 'entity_category': Category of staking entity
            - 'amount_staked': Total ETH staked
            - 'amount_staked_broken_down': Detailed staked amount (sub-entities)
            - 'validators': Number of validators
            - 'marketshare': Percentage of total staked ETH
            - 'ow_change': 1-week change in staked amount
            - 'om_change': 1-month change in staked amount
            - 'sm_change': 6-month change in staked amount
            - 'earned_rewards': Total rewards earned
            - 'last_deposit': Date of last deposit
            - 'last_withdrawal': Date of last withdrawal or 'Never'

    Raises:
        Exception: If error in fetching/processing data
    """
    try:
        query_result = dune.get_latest_result(3930742)
        return query_result.result
    except Exception as e:
        return f"Error fetching Ethereum staking analysis: {str(e)}"


@tool
def get_bitcoin_top_holders_analysis():
    """
    Fetches and analyzes data on top Bitcoin holders, including balance and UTXO age.

    This function provides insights into the distribution of Bitcoin wealth and
    the holding patterns of large Bitcoin addresses.

    Returns:
        dict: A dictionary containing:
            - 'address': Bitcoin address
            - 'balance': Current balance of the address
            - 'weighted_age_utxo_days': Average age of the UTXOs in days, weighted by amount

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3930766)  
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching Bitcoin top holders analysis: {str(e)}"


@tool
def get_polygon_gaming_metrics():
    """
    Analyzes gaming activity on Polygon blockchain. Returns metrics on transactions and users.

    Returns dict with:
    - Project name, timestamp
    - Total transactions and users
    - 7 and 30-day average transactions and users
    - Percentage changes in transactions and users

    Raises Exception on error.
    """
    try:
        query_result = dune.get_latest_result(3930816)
        return query_result.result
    except Exception as e:
        return f"Error fetching Polygon gaming metrics: {str(e)}"
 
@tool
def get_tokenization_market_analysis():
    """
    Analyzes tokenization market categories, including market cap, market share, and growth rates.

    This function provides a comprehensive overview of the tokenization market,
    breaking down performance by different categories and time periods.

    Returns:
        dict: A dictionary containing:
            - 'ranking': Rank of the category by market cap
            - 'category': Name of the tokenization category
            - 'market_cap': Total market capitalization of the category
            - 'market_share': Percentage of total tokenization market cap
            - 'change_1d': 24-hour percentage change
            - 'change_7d': 7-day percentage change
            - 'change_30d': 30-day percentage change
            - 'change_90d': 90-day percentage change
            - 'change_180d': 180-day percentage change
            - 'change_365d': 365-day percentage change

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3930829) 
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching tokenization market analysis: {str(e)}"

@tool
def get_tokenization_project_metrics():
    """
    Analyzes individual tokenization projects, including market cap, market share, growth rates, categories, and blockchain presence.

    This function provides detailed metrics for specific tokenization projects,
    allowing for comparison and analysis of different projects in the space.

    Returns:
        dict: A dictionary containing:
            - 'ranking': Rank of the project by market cap
            - 'project': Name of the tokenization project
            - 'category': List of categories the project belongs to
            - 'blockchain': List of blockchains the project is present on
            - 'number_product': Number of tokenized products offered
            - 'market_cap': Total market capitalization of the project
            - 'market_share': Percentage of total tokenization market cap
            - 'change_1d', 'change_7d', 'change_30d', 'change_90d', 'change_180d', 'change_365d': 
              Percentage changes over various time periods

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3930832)  
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching tokenization project metrics: {str(e)}"



@tool
def get_memecoin_trading_activity():
    """
    Retrieves detailed information about various memecoins, including price, supply, and market cap.

    This function provides comprehensive data on multiple memecoins across different blockchains,
    helping to identify trends and compare market performance.

    Returns:
        dict: A dictionary containing for each memecoin:
            - 'day': The date of the data point
            - 'symbol': Symbol of the memecoin
            - 'price': Current price in USD
            - 'supply': Total supply of the token
            - 'circ_supply': Circulating supply of the token
            - 'fdv': Fully Diluted Valuation (price * total supply)
            - 'market_cap': Market Capitalization (price * circulating supply)

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3930846)  # Make sure this query ID is correct for the new SQL
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching memecoin data: {str(e)}"

@tool
def get_ai_related_tokens_analysis():
    """
    Analyzes emerging AI-related tokens with significant trading volume.

    This function identifies and provides data on AI-focused tokens that have
    recently gained traction in the market, based on trading volume and other metrics.

    Returns:
        dict: A dictionary containing:
            - 'token_bought_symbol': Symbol of the AI-related token
            - 'blockchain': Blockchain on which the token is traded
            - 'volume_usd': Trading volume in USD
            - 'nb_trades': Number of trades
            - 'first_trade': Timestamp of the first recorded trade
            - 'token_address': Contract address of the token

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3930874) 
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching emerging AI tokens analysis: {str(e)}"


@tool
def get_stablecoin_market_analysis():
    """
    Analyzes stablecoin market data on Ethereum, including market cap, market share, and issuing entities.

    This function provides insights into the stablecoin ecosystem on Ethereum,
    highlighting the dominant players and their market positions.

    Returns:
        dict: A dictionary containing:
            - 'ranking': Rank of the stablecoin by market cap
            - 'symbol': Symbol of the stablecoin
            - 'total_market_cap': Total market capitalization of the stablecoin
            - 'market_share': Percentage of total stablecoin market cap
            - 'entity': Name of the issuing entity (with hyperlink)

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3932131) 
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching stablecoin market analysis: {str(e)}"


@tool
def get_farcaster_token_trends():
    """
    Analyzes token mentions in Farcaster posts, including trending tokens, mention counts, and trends over the past 7 and 14 days.

    This function provides insights into which tokens are being discussed most
    frequently on the Farcaster social platform, potentially indicating emerging trends.

    Returns:
        dict: A dictionary containing up to 101 tokens with the following information:
            - Token_symbol: Symbol of the mentioned token
            - count_cast_7days: Number of mentions in the last 7 days
            - count_cast_before_7days: Number of mentions in the 7 days before the last 7 days
            - rate_of_increase: Rate of increase in mentions (null for new tokens)
            - trend: Trend direction ('up', 'down', 'new', or null)

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3932154)  
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching Farcaster token trends: {str(e)}"
    
    

@tool
def get_nft_collection_rankings():
    """
    Ranks top NFT collections by trading volume over different time periods (1 day, 7 days, 30 days).

    This function provides a comprehensive view of the most active and valuable
    NFT collections across various timeframes, with all values denominated in Ethereum (ETH).

    Returns:
        dict: A dictionary containing:
            - 'name': Name of the NFT collection
            - 'current_floor': Current floor price in ETH
            - '1day_volume': Trading volume over the last 24 hours in ETH
            - '7day_volume': Trading volume over the last 7 days in ETH
            - '30day_volume': Trading volume over the last 30 days in ETH
            - 'all_time_volume': All-time trading volume in ETH
            - 'ranking_1d': Rank based on 1-day volume
            - 'ranking_7d': Rank based on 7-day volume
            - 'ranking_30d': Rank based on 30-day volume

    Raises:
        Exception: If there's an error in fetching or processing the data.
    """
    try:
        query_result = dune.get_latest_result(3932216)
        return query_result.result
    except Exception as e:
        raise Exception(f"An error occurred while fetching NFT collection rankings: {str(e)}")
    
    

@tool
def get_bitcoin_yearly_returns():
    """
    Retrieves Bitcoin's yearly returns from 2011 to the current year.

    This function queries the Dune Analytics database to fetch the annual returns of Bitcoin
    for each year from 2011 to the present. It calculates the return based on the price
    at the beginning and end of each year.

    Returns:
        dict: A dictionary containing:
            - 'year': The year for which the return is calculated
            - 'return': The annual return for Bitcoin in that year, expressed as a decimal
              (e.g., 0.5 represents a 50% return)

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(2111396) 
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching Bitcoin yearly returns: {str(e)}"
    
    
@tool
def get_opensea_daily_active_users():
    """
    Retrieves the daily count of active users on OpenSea over the last 3 months.

    This function queries the Dune Analytics database to fetch the number of unique
    users (buyers and sellers) who have made at least one transaction on OpenSea
    each day for the past 3 months.

    Returns:
        dict: A dictionary containing:
            - 'day': The date of the activity
            - 'count': The number of unique active users for that day

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3952388)  
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching OpenSea daily active users: {str(e)}"
    
    
@tool
def get_opensea_monthly_active_users():
    """
    Retrieves the monthly count of active users on OpenSea for all available data.

    This function queries the Dune Analytics database to fetch the number of unique
    users (buyers and sellers) who have made at least one transaction on OpenSea
    for each month since the platform's inception.

    Returns:
        dict: A dictionary containing:
            - 'month': The month of the activity (format: YYYY-MM-01)
            - 'count': The number of unique active users for that month

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3952429)  
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching OpenSea monthly active users: {str(e)}"
    
    
@tool
def get_opensea_monthly_nfts_sold():
    """
    Retrieves the monthly count of NFTs sold on OpenSea for all available data.

    This function queries the Dune Analytics database to fetch the number of NFTs
    sold on OpenSea for each month since the platform's inception. It excludes
    self-trades where the buyer and seller are the same.

    Returns:
        dict: A dictionary containing:
            - 'month': The month of the sales (format: YYYY-MM-01)
            - 'count': The number of NFTs sold in that month

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3952447)  
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching OpenSea monthly NFTs sold: {str(e)}"


@tool
def get_opensea_daily_volume_usd():
    """
    Retrieves the daily trading volume in USD on OpenSea for the last 3 months.

    This function queries the Dune Analytics database to fetch the total USD value
    of NFTs traded on OpenSea each day for the past 3 months. It excludes
    self-trades where the buyer and seller are the same.

    Returns:
        dict: A dictionary containing:
            - 'day': The date of the trading activity (format: YYYY-MM-DD)
            - 'volume_usd': The total trading volume in USD for that day

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3952481)  
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching OpenSea daily volume in USD: {str(e)}"
    
    
    
@tool
def get_opensea_monthly_volume_usd():
    """
    Retrieves the monthly trading volume in USD on OpenSea for all available data.

    This function queries the Dune Analytics database to fetch the total USD value
    of NFTs traded on OpenSea each month since the platform's inception. It excludes
    self-trades where the buyer and seller are the same.

    Returns:
        dict: A dictionary containing:
            - 'month': The month of the trading activity (format: YYYY-MM-01)
            - 'volume_usd': The total trading volume in USD for that month

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3952504)  
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching OpenSea monthly volume in USD: {str(e)}"
    
    
@tool
def get_nft_wash_trading_analysis():
    """
    Analyzes NFT wash trading across different Ethereum marketplaces.

    Fetches data on NFT trading volume, identifying wash trades vs. organic trades.
    Provides insights into market integrity and trading behavior.

    Returns:
        dict: Contains for each marketplace:
            - Name and type
            - Total volume and trade count
            - Wash trade percentages (volume and count)
            - Organic volume and trade count
            - Operating blockchains

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3958323)
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching NFT wash trading analysis: {str(e)}"
    
    
@tool
def get_solana_dex_volume_analysis():
    """
    Retrieves and analyzes the trading volume data for decentralized exchanges (DEXs) on the Solana blockchain.

    This function queries Dune Analytics to fetch trading volume statistics for various DEX projects on Solana,
    including daily, weekly, monthly, and all-time volumes.

    Returns:
        dict: A dictionary containing:
            - 'project': Name of the DEX project (with 'whirlpool' renamed to 'orca')
            - 'one_day_volume': Trading volume over the last 24 hours in USD
            - 'seven_day_volume': Trading volume over the last 7 days in USD
            - 'thirty_day_volume': Trading volume over the last 30 days in USD
            - 'all_time_volume': All-time trading volume in USD

    The results are ordered by the 24-hour trading volume in descending order.

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3935128)
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching Solana DEX volume analysis: {str(e)}"
    
    
@tool
def get_sunpump_recent_buys():
    """
    Retrieves recent SunPump token buy transactions.

    This function queries the Dune Analytics database to fetch recent buy transactions
    for SunPump tokens on the Tron blockchain. It provides details such as the transaction
    hash, buyer's wallet address, amount of TRX paid, and the token address.

    Returns:
        dict: A dictionary containing:
            - 'Transaction': Link to view the transaction on Tronscan
            - 'Wallet': The buyer's wallet address
            - 'Type': Always "Buy" for this query
            - 'TRX Paid': Amount of TRX paid for the transaction
            - 'Token address': Link to view the token on SunPump website
            - 'Times bought': Number of times this token has been bought in the period

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(4002974)
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching SunPump recent buys data: {str(e)}"
    
    
    
@tool
def get_daily_fees_comparison():
    """
    Fetches and compares daily fees for FourMeme, SunPump, and Pumpdotfun platforms.

    This function retrieves daily fee data for three different platforms (FourMeme on BNB chain,
    SunPump on TRON, and Pumpdotfun on Solana) from August 11, 2024 onwards. It calculates
    daily revenue in USD and cumulative revenue for each platform.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'date': The date of the fee collection
            - 'platform': The name of the platform (FourMeme, SunPump, or Pumpdotfun)
            - 'daily_revenue': Daily revenue in the platform's native token
            - 'daily_revenue_usd': Daily revenue converted to USD
            - 'cumulative_revenue_usd': Cumulative revenue in USD since August 11, 2024

    Raises:
        Exception: If there's an error in fetching or processing the data.
    """
    try:
        query_result = dune.get_latest_result(4017952)
        return query_result.result
    except Exception as e:
        raise Exception(f"An error occurred while fetching daily fees comparison: {str(e)}")
    
    
@tool
def get_top_solana_memecoins():
    """
    Retrieves the top 10 Solana memecoins created in the last month, ranked by trading volume.

    Returns:
        dict: Contains for each memecoin:
            - 'birdeye': Link to Birdeye info
            - 'dexscreener': Link to Dexscreener info
            - 'rugcheck': Link to Rugcheck analysis
            - 'created_at': Token creation date
            - 'symbol': Token symbol
            - 'name': Token name
            - 'token': Token address
            - 'first_trade': First trade timestamp
            - 'traders_count': Number of unique traders
            - 'trades_count': Total number of trades
            - 'trade_volume': Total trading volume in USD
            - 'isMintable': If token supply can be increased ('❗' or '❎')
            - 'isFreezable': If token transfers can be frozen ('❗' or '❎')
            - 'isMutable': If token metadata can be changed ('❗' or '❎')
            - 'status': Trading activity status ('Active' or 'Inactive')

    Raises:
        Exception: If there's an error in fetching or processing the data.
    """
    try:
        query_result = dune.get_latest_result(4034915)
        return query_result.result
    except Exception as e:
        raise Exception(f"An error occurred while fetching daily fees comparison: {str(e)}")
    
    
@tool
def get_memecoin_project_rankings():
    """
    Fetches ranking data for MemeSeason2024 memecoin projects.

    Returns:
        Dict[str, Any]: Contains:
            'Project': Name with hyperlink
            'Symbol': With explorer link
            'Points': For ranking
            '🔰': Overall rank
            'Qualify': ✔️ or ❌
            '🏆': 🥇, 🥈, 🥉, or 🏅
            'Deployer 💰': USD reward
            'Holders 💰': USD reward
            'Liquidity 💧': Avg
            'Volume 💱': Trading
            'Market Cap (💲)'
            'Total Supply (🤡)'
            'Current 💧': Liquidity
            '24h ΔLiquidity': Change
            '24h ΔVolume': Change
            '24h ΔPrice': % Change
            'Current Price'
            'Avg. 3d Price'

    Raises:
        Exception: On fetch/process error
    """
    try:
        query_result = dune.get_latest_result(4037624)
        return query_result.result
    except Exception as e:
        raise Exception(f"Error fetching memecoin rankings: {str(e)}")
    
    

@tool
def get_bitcoin_activity_metrics():
    """
    Fetches Bitcoin activity metrics including active addresses and transaction volume.

    Returns:
        dict: A dictionary containing:
            - 'time': The timestamp for the data point
            - 'volume': The transaction volume in USD
            - 'active_address': The number of active addresses

    Raises:
        Exception: If there's an error in fetching or processing the data.
    """
    try:
        query_result = dune.get_latest_result(4040951)
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching Bitcoin activity metrics: {str(e)}"
    
    
@tool
def get_tether_tron_daily_volume():
    """
    Retrieves the daily transaction volume of Tether (USDT) on the Tron blockchain.

    This function queries Dune Analytics to fetch the total daily transaction volume of USDT on Tron,
    providing insights into the network's liquidity and activity level.

    Returns:
        dict: A dictionary containing:
            - 'day': The date of the transactions (truncated to day)
            - 'label': Always 'USDT' for this query
            - 'Volume': The total transaction volume of USDT for that day

    The results are ordered by date in descending order, with the most recent day first.

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(4053687)
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching Tether Tron daily volume: {str(e)}"
    

@tool
def get_trading_bot_leaderboard():
    """
    Fetches and ranks trading bot performance data.

    Returns a leaderboard of trading bots with key metrics including volume, revenue, user base, and cross-chain activity. Provides insights into the most active and successful trading bots.

    Returns:
        dict: Contains for each bot:
            'volumeRank': Rank by volume (with medal emojis for top 3)
            'bot': Bot name
            'dashboard': Dashboard link
            'volumeUSD': Total volume in USD
            'volume7dUSD': 7-day volume in USD
            'numberOfUsers': Unique users count
            'botRevenueUSD': Bot revenue in USD
            'numberOfTrades': Total trades
            'platforms': Supported platforms
            'blockchains': Supported blockchains
            'numberOfSupportedBlockchains': Count of supported chains
            'activityDays': Active days
            'averageVolumePerDayUSD': Avg daily volume
            'averageVolumePerUserUSD': Avg volume per user
            'averageVolumePerTradeUSD': Avg volume per trade

    Raises:
        Exception: On fetch/process error
    """
    try:
        query_result = dune.get_latest_result(4077873)
        return query_result.result
    except Exception as e:
        return f"Error fetching trading bot leaderboard: {str(e)}"
    
    
    
@tool
def get_base_token_pair_metrics():
    """
    Analyzes trading activity for token pairs on Base blockchain with volume and user metrics.

    Returns:
        dict: Contains for each token pair:
            - 'Token Pair': Trading pair name
            - '1/7/30 Day USD Volume': Trading volumes for each period
            - '1/7/30 Day DAU': Daily Active Users for each period
            - 'Previous Period Volumes': For 1d/7d/30d comparisons
            - Volume Change (%): Percentage changes across timeframes

    Results ordered by 7-day volume (desc), top 250 pairs shown.

    Raises:
        Exception: If error in fetching/processing data
    """
    try:
        query_result = dune.get_latest_result(4350809)
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching Base token pair metrics: {str(e)}"
    
    
   
   
@tool
def get_virtuals_launch_metrics():
    """
    Analyzes daily metrics for Virtuals.io AI token launches on Base blockchain.

    Returns:
        dict: Contains daily metrics:
            - 'day': Date of metrics
            - 'num_tokens': New tokens launched that day
            - 'unique_addresses': Unique deployers
            - 'virtual_spent': Amount of VIRTUAL tokens spent
            - 'cumulative_spent': Total VIRTUAL spent to date
            - 'total_tokens_launched': Cumulative tokens launched
            - 'num_grad_tokens': Graduated tokens that day
            - 'cumulative_grad_tokens': Total graduated tokens
            - 'avg_ownership': Average ownership percentage

    Results ordered by date descending, starting from 2024-11-01.

    Raises:
        Exception: If error in fetching data
    """
    try:
        query_result = dune.get_latest_result(4354271)  # Replace with actual query ID
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching Virtuals.io launch metrics: {str(e)}" 
    
    
    
    
@tool
def get_token_holder_distribution():
    """
    Analyzes token holder distribution across different balance ranges.

    Returns:
        dict: Contains for each balance range:
            - 'lvl': Tier level (1-6)
            - 'label': Balance range (e.g., '0-100', '100-1,000', etc.)
            - 'wallets': Number of wallets in this range
            - 'total_tokens': Total tokens held in this range
            - 'percentage': Percentage of total supply in this range

    The analysis covers these ranges:
    - 0-100 tokens
    - 100-1,000 tokens
    - 1,000-10,000 tokens
    - 10,000-100,000 tokens
    - 100,000-600,000 tokens
    - over 600,000 tokens

    Raises:
        Exception: If error in fetching data
    """
    try:
        query_result = dune.get_latest_result(4359001)
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching token holder distribution: {str(e)}"