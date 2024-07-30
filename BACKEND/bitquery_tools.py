import os
import requests
from dotenv import load_dotenv
from langchain.tools import tool
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

BITQUERY_API_KEY = os.getenv('BITQUERY_API_KEY')
BITQUERY_API_URL = "https://graphql.bitquery.io"


@tool
def get_latest_pair_created(query: str = "") -> str:
    """
    Fetch the latest pair created on the Ethereum network.

    Args:
        query (str): This parameter is not used but is required for LangChain compatibility.

    Returns:
        str: Information about the latest pair created on Ethereum.
    """
    logger.debug(f"BITQUERY_API_KEY: {'*' * len(BITQUERY_API_KEY) if BITQUERY_API_KEY else 'Not set'}")
    logger.debug(f"BITQUERY_API_URL: {BITQUERY_API_URL}")

    if not BITQUERY_API_KEY:
        return "API key for Bitquery not found. Please set it in the environment variables."

    graphql_query = """
    {
        ethereum(network: ethereum) {
            arguments(
                options: {desc: ["block.height"], limit: 1}
                smartContractAddress: {in: "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f"}
                smartContractEvent: {is: "PairCreated"}
            ) {
                block {
                    height
                    timestamp {
                        time(format: "%Y-%m-%d %H:%M:%S")
                    }
                }
            }
        }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": BITQUERY_API_KEY
    }
    
    try:
        logger.debug("Sending request to Bitquery API")
        response = requests.post(BITQUERY_API_URL, json={'query': graphql_query}, headers=headers)
        logger.debug(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"API Response Data: {data}")
            
            if 'errors' in data:
                error_message = data['errors'][0]['message']
                return f"Error in Bitquery API response: {error_message}"
            
            if 'data' in data and 'ethereum' in data['data'] and 'arguments' in data['data']['ethereum']:
                arguments = data['data']['ethereum']['arguments']
                if arguments is None or len(arguments) == 0:
                    return "No pair creation data found in the response."
                pair_data = arguments[0]
                block_height = pair_data['block']['height']
                timestamp = pair_data['block']['timestamp']['time']
                return f"Latest pair created on Ethereum at block height {block_height} on {timestamp}"
            else:
                return "Unexpected data structure in the response."
        else:
            return f"Error response from Bitquery API: {response.text}"
    except Exception as e:
        logger.exception("Exception occurred while fetching data from Bitquery API")
        return f"Error occurred while fetching data from Bitquery API: {str(e)}"
