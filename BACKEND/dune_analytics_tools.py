import os
from dune_client.client import DuneClient
from langchain.tools import tool

# Get the API key from an environment variable
DUNE_API_KEY = os.getenv('DUNE_API_KEY')

# Initialize the Dune client
dune = DuneClient(DUNE_API_KEY)


@tool
def get_dex_volume_results():
    """
    Fetch the latest results from the DEX volume Dune Analytics query.
    """
    try:
        query_result = dune.get_latest_result(3930794)  
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    

@tool
def get_ethereum_daily_activity():
    """
    Fetch daily active users and receiving addresses on Ethereum since 2023.
    """
    try:
        query_result = dune.get_latest_result(3930800)
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    
    
@tool
def get_monthly_dex_volume_by_project():
    """
    Fetch monthly DEX trading volume data grouped by project since 2019.
    """
    try:
        query_result = dune.get_latest_result(3929505)
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    

@tool
def get_nft_market_volume():
    """
    Fetch daily and weekly NFT market volume across major marketplaces.
    """
    try:
        query_result = dune.get_latest_result(3930460)  
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"   
    
    
@tool
def get_sector_performance_analysis_24h():
    """
    Fetch and analyze the relative performance of different crypto narratives.
    """
    try:
        query_result = dune.get_latest_result(3930578)  
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    
    
@tool
def get_sector_performance_analysis_7d():
    """
    Fetch and analyze the 7-day relative performance of different crypto sectors.
    """
    try:
        query_result = dune.get_latest_result(3932113)  
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"

@tool
def get_sector_performance_analysis_30d():
    """
    Fetch and analyze the 30-day relative performance of different crypto sectors.
    """
    try:
        query_result = dune.get_latest_result(3932117)  
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    

@tool
def get_bitcoin_etf_analysis():
    """
    Fetch and analyze data on Bitcoin ETFs, including TVL, market share, and fees.
    """
    try:
        query_result = dune.get_latest_result(3930609)  # Replace with actual query ID
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    
    
@tool
def get_ethereum_staking_analysis():
    """
    Fetch and analyze Ethereum staking data, including deposits, withdrawals, and net inflows for different entities.
    """
    try:
        query_result = dune.get_latest_result(3930742)  # Replace with actual query ID
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    

@tool
def get_bitcoin_top_holders_analysis():
    """
    Fetch and analyze data on top Bitcoin holders, including balance and UTXO age.
    """
    try:
        query_result = dune.get_latest_result(3930766)  
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    
    
@tool
def get_polygon_gaming_analysis():
    """
    Fetch and analyze data on gaming activities on the Polygon blockchain.
    """
    try:
        query_result = dune.get_latest_result(3930816)  #
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    
    
@tool
def get_tokenization_market_analysis():
    """
    Fetch and analyze data on tokenization market categories, including market cap, market share, and growth rates.
    """
    try:
        query_result = dune.get_latest_result(3930829) 
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    
    
@tool
def get_tokenization_project_analysis():
    """
    Fetch and analyze data on individual tokenization projects, including market cap, market share, growth rates, categories, and blockchain presence.
    """
    try:
        query_result = dune.get_latest_result(3930832)  
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    
    
@tool
def get_memecoin_market_analysis():
    """
    Fetch and analyze data on memecoin performance, including price, supply, market cap, and trading volume metrics.
    """
    try:
        query_result = dune.get_latest_result(3930846)  
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    

@tool
def get_emerging_ai_tokens_analysis():
    """
    Fetch and analyze data on emerging AI-related tokens with significant trading volume.
    """
    try:
        query_result = dune.get_latest_result(3930874) 
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    
    
@tool
def get_crypto_category_performance():
    """
    Fetch and analyze performance data for various cryptocurrency categories, including market cap and price changes over different time periods.
    """
    try:
        query_result = dune.get_latest_result(3930930)  # Replace QUERY_ID with the actual query ID
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    
    
    
@tool
def get_stablecoin_market_analysis():
    """
    Fetch and analyze stablecoin market data on Ethereum, including market cap, market share, and issuing entities.
    """
    try:
        query_result = dune.get_latest_result(3932131) 
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    

@tool
def get_farcaster_token_mentions_analysis():
    """
    Fetch and analyze data on token mentions in Farcaster posts, including trending tokens, mention counts, and trends over the past 7 and 14 days.
    """
    try:
        query_result = dune.get_latest_result(3932154)  
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    

@tool
def get_top_nft_collections_ranking():
    """
    Fetch and analyze data on top NFT collections ranked by trading volume over different time periods (1 day, 7 days, 30 days).
    """
    try:
        query_result = dune.get_latest_result(3932216)  
        return query_result.result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    
    


