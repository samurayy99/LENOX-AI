import os
from dune_client.client import DuneClient
from langchain.tools import tool

DUNE_API_KEY = os.getenv('DUNE_API_KEY')
dune = DuneClient(DUNE_API_KEY or '') 

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
        query_result = dune.get_latest_result(3930794)  
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching DEX volume rankings: {str(e)}"

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
def get_dex_monthly_volume_trends():
    """
    Retrieves monthly DEX trading volume data grouped by project since 2019.

    This function provides a long-term view of DEX activity, allowing for
    analysis of trends and market share changes over time.

    Returns:
        dict: A dictionary containing:
            - 'project': Name of the DEX project
            - 'month': The month of the data point
            - 'usd_volume': Total trading volume for the month in USD

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3929505)
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching DEX monthly volume trends: {str(e)}"

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
    Fetches and analyzes data on Bitcoin ETFs, including TVL, market share, and fees.

    This function provides a comprehensive overview of various Bitcoin ETF products,
    their performance, and market positioning.

    Returns:
        dict: A dictionary containing:
            - 'plain_issuer': Name of the ETF issuer
            - 'issuer': Linked name of the ETF issuer
            - 'tvl': Total Value Locked in the ETF
            - 'usd_value': USD value of the TVL
            - 'percentage_of_total': Market share of the ETF
            - 'etf_ticker': Ticker symbol of the ETF
            - 'percentage_fee': Management fee of the ETF
            - 'address_source': Source of the ETF's Bitcoin address information

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
    Analyzes Ethereum staking data, including deposits, withdrawals, and net inflows for different entities.

    This function provides insights into Ethereum staking trends, highlighting the
    most active staking entities and their net positions.

    Returns:
        dict: A dictionary containing:
            - 'entity': Name of the staking entity
            - 'eth_inflow': Amount of ETH deposited for staking
            - 'eth_principal_outflow': Amount of principal ETH withdrawn
            - 'eth_rewards_outflow': Amount of reward ETH withdrawn
            - 'net_inflow': Net position (inflow - outflow)
            - 'net_inflow_excluding_rewards': Net position excluding staking rewards

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    try:
        query_result = dune.get_latest_result(3930742)
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching Ethereum staking analysis: {str(e)}"

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
        dict: A dictionary containing:
            - 'Token_symbol': Symbol of the mentioned token
            - 'count_cast_7days': Number of mentions in the last 7 days
            - 'count_cast_before_7days': Number of mentions in the 7 days before the last 7 days
            - 'rate_of_increase': Rate of increase in mentions
            - 'trend': Trend direction ('up', 'down', or 'new')

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