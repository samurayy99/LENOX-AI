import os
from dune_client.client import DuneClient
from langchain.tools import tool

DUNE_API_KEY = os.getenv('DUNE_API_KEY')
dune = DuneClient(DUNE_API_KEY or '')

# Query IDs for each sector and timeframe
QUERY_IDS = {
    'All Sectors': {'24H': 3955036, '7D': 3955059, '30D': 3955063, '90D': 3955072},
    'L1': {'24H': 3955080, '7D': 3955084, '30D': 3955088, '90D': 3955091},
    'L2/L3': {'24H': 3955097, '7D': 3955101, '30D': 3955103, '90D': 3955108},
    'Blockchain Service Infra': {'24H': 3955114, '7D': 3955119, '30D': 3955128, '90D': 3955134},
    'Blue Chip DeFi': {'24H': 3955181, '7D': 3955188, '30D': 3955195, '90D': 3955198},
    'DeFi 3.0': {'24H': 3955202, '7D': 3955207, '30D': 3955214, '90D': 3955222},
    'Memecoins': {'24H': 3955223, '7D': 3955227, '30D': 3955231, '90D': 3955235},
    'RWA': {'24H': 3955256, '7D': 3955257, '30D': 3955261, '90D': 3955265},
    'Web3 Gaming': {'24H': 3955271, '7D': 3955274, '30D': 3955280, '90D': 3955281},
    'Decentralised AI': {'24H': 3955293, '7D': 3955302, '30D': 3955307, '90D': 3955313},
    'DePIN': {'24H': 3955317, '7D': 3955320, '30D': 3955324, '90D': 3955326},
}

@tool
def get_all_sectors_relative_strength(timeframe='24H'):
    """
    Retrieves the relative strength analysis for all crypto sectors.

    Args:
        timeframe (str): The timeframe for analysis. Can be '24H', '7D', '30D', or '90D'.

    Returns:
        dict: A dictionary containing the relative strength analysis results for all sectors.
    """
    if timeframe not in QUERY_IDS['All Sectors']:
        raise ValueError(f"Invalid timeframe. Must be one of: {', '.join(QUERY_IDS['All Sectors'].keys())}")
    
    try:
        query_result = dune.get_latest_result(QUERY_IDS['All Sectors'][timeframe])
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching relative strength analysis for all sectors over {timeframe}: {str(e)}"

@tool
def get_l1_relative_strength(timeframe='24H'):
    """
    Retrieves the relative strength analysis for the L1 sector.

    Args:
        timeframe (str): The timeframe for analysis. Can be '24H', '7D', '30D', or '90D'.

    Returns:
        dict: A dictionary containing the relative strength analysis results for the L1 sector.
    """
    if timeframe not in QUERY_IDS['L1']:
        raise ValueError(f"Invalid timeframe for L1. Must be one of: {', '.join(QUERY_IDS['L1'].keys())}")
    
    try:
        query_result = dune.get_latest_result(QUERY_IDS['L1'][timeframe])
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching relative strength analysis for L1 sector over {timeframe}: {str(e)}"

@tool
def get_l2l3_relative_strength(timeframe='24H'):
    """
    Retrieves the relative strength analysis for the L2/L3 sector.

    Args:
        timeframe (str): The timeframe for analysis. Can be '24H', '7D', '30D', or '90D'.

    Returns:
        dict: A dictionary containing the relative strength analysis results for the L2/L3 sector.
    """
    if timeframe not in QUERY_IDS['L2/L3']:
        raise ValueError(f"Invalid timeframe for L2/L3. Must be one of: {', '.join(QUERY_IDS['L2/L3'].keys())}")
    
    try:
        query_result = dune.get_latest_result(QUERY_IDS['L2/L3'][timeframe])
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching relative strength analysis for L2/L3 sector over {timeframe}: {str(e)}"

@tool
def get_blockchain_service_infra_relative_strength(timeframe='24H'):
    """
    Retrieves the relative strength analysis for the Blockchain Service Infrastructure sector.

    Args:
        timeframe (str): The timeframe for analysis. Can be '24H', '7D', '30D', or '90D'.

    Returns:
        dict: A dictionary containing the relative strength analysis results for the Blockchain Service Infrastructure sector.
    """
    if timeframe not in QUERY_IDS['Blockchain Service Infra']:
        raise ValueError(f"Invalid timeframe for Blockchain Service Infra. Must be one of: {', '.join(QUERY_IDS['Blockchain Service Infra'].keys())}")
    
    try:
        query_result = dune.get_latest_result(QUERY_IDS['Blockchain Service Infra'][timeframe])
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching relative strength analysis for Blockchain Service Infra sector over {timeframe}: {str(e)}"

@tool
def get_blue_chip_defi_relative_strength(timeframe='24H'):
    """
    Retrieves the relative strength analysis for the Blue Chip DeFi sector.

    Args:
        timeframe (str): The timeframe for analysis. Can be '24H', '7D', '30D', or '90D'.

    Returns:
        dict: A dictionary containing the relative strength analysis results for the Blue Chip DeFi sector.
    """
    if timeframe not in QUERY_IDS['Blue Chip DeFi']:
        raise ValueError(f"Invalid timeframe for Blue Chip DeFi. Must be one of: {', '.join(QUERY_IDS['Blue Chip DeFi'].keys())}")
    
    try:
        query_result = dune.get_latest_result(QUERY_IDS['Blue Chip DeFi'][timeframe])
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching relative strength analysis for Blue Chip DeFi sector over {timeframe}: {str(e)}"

@tool
def get_defi_3_0_relative_strength(timeframe='24H'):
    """
    Retrieves the relative strength analysis for the DeFi 3.0 sector.

    Args:
        timeframe (str): The timeframe for analysis. Can be '24H', '7D', '30D', or '90D'.

    Returns:
        dict: A dictionary containing the relative strength analysis results for the DeFi 3.0 sector.
    """
    if timeframe not in QUERY_IDS['DeFi 3.0']:
        raise ValueError(f"Invalid timeframe for DeFi 3.0. Must be one of: {', '.join(QUERY_IDS['DeFi 3.0'].keys())}")
    
    try:
        query_result = dune.get_latest_result(QUERY_IDS['DeFi 3.0'][timeframe])
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching relative strength analysis for DeFi 3.0 sector over {timeframe}: {str(e)}"

@tool
def get_memecoins_relative_strength(timeframe='24H'):
    """
    Retrieves the relative strength analysis for the Memecoins sector.

    Args:
        timeframe (str): The timeframe for analysis. Can be '24H', '7D', '30D', or '90D'.

    Returns:
        dict: A dictionary containing the relative strength analysis results for the Memecoins sector.
    """
    if timeframe not in QUERY_IDS['Memecoins']:
        raise ValueError(f"Invalid timeframe for Memecoins. Must be one of: {', '.join(QUERY_IDS['Memecoins'].keys())}")
    
    try:
        query_result = dune.get_latest_result(QUERY_IDS['Memecoins'][timeframe])
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching relative strength analysis for Memecoins sector over {timeframe}: {str(e)}"

@tool
def get_rwa_relative_strength(timeframe='24H'):
    """
    Retrieves the relative strength analysis for the RWA (Real World Assets) sector.

    Args:
        timeframe (str): The timeframe for analysis. Can be '24H', '7D', '30D', or '90D'.

    Returns:
        dict: A dictionary containing the relative strength analysis results for the RWA sector.
    """
    if timeframe not in QUERY_IDS['RWA']:
        raise ValueError(f"Invalid timeframe for RWA. Must be one of: {', '.join(QUERY_IDS['RWA'].keys())}")
    
    try:
        query_result = dune.get_latest_result(QUERY_IDS['RWA'][timeframe])
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching relative strength analysis for RWA sector over {timeframe}: {str(e)}"

@tool
def get_web3_gaming_relative_strength(timeframe='24H'):
    """
    Retrieves the relative strength analysis for the Web3 Gaming sector.

    Args:
        timeframe (str): The timeframe for analysis. Can be '24H', '7D', '30D', or '90D'.

    Returns:
        dict: A dictionary containing the relative strength analysis results for the Web3 Gaming sector.
    """
    if timeframe not in QUERY_IDS['Web3 Gaming']:
        raise ValueError(f"Invalid timeframe for Web3 Gaming. Must be one of: {', '.join(QUERY_IDS['Web3 Gaming'].keys())}")
    
    try:
        query_result = dune.get_latest_result(QUERY_IDS['Web3 Gaming'][timeframe])
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching relative strength analysis for Web3 Gaming sector over {timeframe}: {str(e)}"

@tool
def get_decentralised_ai_relative_strength(timeframe='24H'):
    """
    Retrieves the relative strength analysis for the Decentralised AI sector.

    Args:
        timeframe (str): The timeframe for analysis. Can be '24H', '7D', '30D', or '90D'.

    Returns:
        dict: A dictionary containing the relative strength analysis results for the Decentralised AI sector.
    """
    if timeframe not in QUERY_IDS['Decentralised AI']:
        raise ValueError(f"Invalid timeframe for Decentralised AI. Must be one of: {', '.join(QUERY_IDS['Decentralised AI'].keys())}")
    
    try:
        query_result = dune.get_latest_result(QUERY_IDS['Decentralised AI'][timeframe])
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching relative strength analysis for Decentralised AI sector over {timeframe}: {str(e)}"

@tool
def get_depin_relative_strength(timeframe='24H'):
    """
    Retrieves the relative strength analysis for the DePIN sector.

    Args:
        timeframe (str): The timeframe for analysis. Can be '24H', '7D', '30D', or '90D'.

    Returns:
        dict: A dictionary containing the relative strength analysis results for the DePIN sector.
    """
    if timeframe not in QUERY_IDS['DePIN']:
        raise ValueError(f"Invalid timeframe for DePIN. Must be one of: {', '.join(QUERY_IDS['DePIN'].keys())}")
    
    try:
        query_result = dune.get_latest_result(QUERY_IDS['DePIN'][timeframe])
        return query_result.result
    except Exception as e:
        return f"An error occurred while fetching relative strength analysis for DePIN sector over {timeframe}: {str(e)}"
