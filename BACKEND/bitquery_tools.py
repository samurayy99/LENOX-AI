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
BITQUERY_EAP_URL = "https://streaming.bitquery.io/eap"
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')


headers = {
    'Content-Type': 'application/json',
    'X-API-KEY': BITQUERY_API_KEY
}


def truncate_documents(docs, max_tokens_per_doc=1000):
    truncated_docs = []
    for doc in docs:
        content = doc['content']
        if len(content.split()) > max_tokens_per_doc:
            content = ' '.join(content.split()[:max_tokens_per_doc]) + '...'
        truncated_docs.append({'name': doc['name'], 'content': content})
    return truncated_docs



@tool
def get_latest_uniswap_pairs():
    """
    Fetches the latest Uniswap pairs created on the Ethereum network.

    Returns:
        dict: The result of the GraphQL query with information about the latest Uniswap pairs.
    """
    query = """
    {
      ethereum(network: ethereum) {
        arguments(
          options: {desc: ["block.height","index"], limit: 50}
          smartContractAddress: {in: "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f"}
          smartContractEvent: {is: "PairCreated"}
        ) {
          block {
            height
            timestamp{
              time(format:"%Y-%m-%d %H:%M:%S")
            }
          }
          index
          pair: any(of: argument_value, argument: {is: "pair"})
          token0: any(of: argument_value, argument: {is: "token0"})
          token0Name: any(of: argument_value, argument: {is: "token0"}, as: token_name)
          token1: any(of: argument_value, argument: {is: "token1"})
          token1Name: any(of: argument_value, argument: {is: "token1"}, as: token_name)
        }
      }
    }
    """
    
    payload = {
        "query": query,
        "variables": {}
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": BITQUERY_API_KEY
    }
    
    try:
        response = requests.post(BITQUERY_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        logger.debug("Successfully fetched data from Bitquery.")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return {"error": str(e)}


@tool("fetch_bitfinex_bitcoin_transactions")
def fetch_bitfinex_bitcoin_transactions(limit: int = 10, from_date: str = "", till_date: str = ""):
    """
    Fetch recent inbound and outbound Bitcoin transactions for the Bitfinex cold wallet.

    Args:
        limit (int, optional): Number of transactions to fetch per depth level. Defaults to 10.
        from_date (str, optional): The start date for the query (ISO8601). Defaults to an empty string.
        till_date (str, optional): The end date for the query (ISO8601). Defaults to an empty string.

    Returns:
        dict: JSON response with transaction data.
    """
    address = "3JZq4atUahhuA9rLhXLMhhTo133J9rF97j"  # Bitfinex Cold Wallet Address

    query = """
    query ($network: BitcoinNetwork!, $address: String!, $inboundDepth: Int!, $outboundDepth: Int!, $limit: Int!, $from: ISO8601DateTime, $till: ISO8601DateTime) {
      bitcoin(network: $network) {
        inbound: coinpath(
          initialAddress: {is: $address}
          depth: {lteq: $inboundDepth}
          options: {direction: inbound, asc: "depth", desc: "amount", limitBy: {each: "depth", limit: $limit}}
          date: {since: $from, till: $till}
        ) {
          sender {
            address
            annotation
          }
          receiver {
            address
            annotation
          }
          amount
          depth
          count
        }
        outbound: coinpath(
          initialAddress: {is: $address}
          depth: {lteq: $outboundDepth}
          options: {asc: "depth", desc: "amount", limitBy: {each: "depth", limit: $limit}}
          date: {since: $from, till: $till}
        ) {
          sender {
            address
            annotation
          }
          receiver {
            address
            annotation
          }
          amount
          depth
          count
        }
      }
    }
    """
    
    # Handle empty string for dates to avoid None assignment
    variables = {
        "inboundDepth": 1,
        "outboundDepth": 1,
        "limit": limit,
        "network": "bitcoin",
        "address": address,
        "from": from_date or None,  # Keep it as None if not provided
        "till": till_date or None   # Keep it as None if not provided
    }

    headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': BITQUERY_API_KEY
    }

    try:
        response = requests.post(BITQUERY_API_URL, headers=headers, json={"query": query, "variables": variables})
        response.raise_for_status()  # Raise an error for bad HTTP status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching transactions: {e}")
        return {"error": str(e)}
    
    
@tool("compare_bsc_token_transfers")
def compare_bsc_token_transfers(from_date: str = "2024-08-01T00:00:00Z", till_date: str = "2024-12-31T23:59:59Z") -> dict:
    """
    Compare the transfer counts and unique receiver counts of Baby Doge Coin and FLOKI tokens on the BSC network.

    Args:
        from_date (str): The start date for the query (ISO8601 format).
        till_date (str): The end date for the query (ISO8601 format).

    Returns:
        dict: JSON response containing the transfer comparison data.
    """
    query = """
    query MyQuery {
      ethereum(network: bsc) {
        transfers(
          currency: {in: ["0xfb5b838b6cfeedc2873ab27866079ac55363d37e", "0xc748673057861a797275cd8a068abb95a902e8de"]}
          options: {limitBy: {each: "currency.address", limit: 10}}
          date: {since: "%s", till: "%s"}
        ) {
          currency {
            address
            name
            decimals
          }
          count(uniq: receivers)
          countBigInt(uniq: transfers)
        }
      }
    }
    """ % (from_date, till_date)

    headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': BITQUERY_API_KEY
    }

    try:
        response = requests.post(BITQUERY_API_URL, headers=headers, json={"query": query})
        response.raise_for_status()  # Raise an error for bad HTTP status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching token transfer data: {e}")
        return {"error": str(e)}

      

@tool("fetch_latest_solana_tokens")
def fetch_latest_solana_tokens() -> dict:
    """
    Fetches the latest tokens created on the Solana network, limited to the 5 most recent.
    Provides clickable links to Solscan for detailed viewing of the addresses and transactions.

    Returns:
        dict: JSON response containing the latest 5 token creation events on Solana.
    """
    query = """
    subscription {
      Solana {
        Instructions(
          where: {Instruction: {Program: {Address: {is: "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}, Method: {in: ["initializeMint", "initializeMint2"]}}}, Transaction: {Result: {Success: true}}}
        ) {
          Instruction {
            Accounts {
              Address
              IsWritable
              Token {
                Mint
                Owner
                ProgramId
              }
            }
            Program {
              AccountNames
              Address
            }
          }
          Transaction {
            Signature
            Signer
          }
        }
      }
    }
    """

    headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': BITQUERY_API_KEY
    }

    try:
        response = requests.post(BITQUERY_EAP_URL, headers=headers, json={"query": query})
        response.raise_for_status()  # Raise an error for bad HTTP status codes
        data = response.json()
        logger.debug("Successfully fetched latest token creation data from Solana.")

        # Limit to the last 5 items
        if "data" in data and "Solana" in data["data"] and "Instructions" in data["data"]["Solana"]:
            instructions = data["data"]["Solana"]["Instructions"][:5]

            # Construct clickable links for Solscan
            for instruction in instructions:
                for account in instruction["Instruction"]["Accounts"]:
                    account_address = account["Address"]
                    account["SolscanLink"] = f"https://solscan.io/account/{account_address}"

                transaction_signature = instruction["Transaction"]["Signature"]
                instruction["Transaction"]["SolscanLink"] = f"https://solscan.io/tx/{transaction_signature}"

            data["data"]["Solana"]["Instructions"] = instructions

        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Solana token creation data: {e}")
        return {"error": str(e)}


@tool("fetch_top_10_pumpfun_tokens")
def fetch_top_10_pumpfun_tokens() -> dict:
    """
    Fetches the top 10 pump.fun tokens on the Solana network by their buy volume.
    Provides clickable links to Solscan for detailed viewing of the token mint addresses.

    Returns:
        dict: JSON response containing the top 10 pump tokens and their Solscan links, or an empty list if no data.
    """
    query = """
    query MyQuery {
      solana(network: solana) {
        dexTrades(
          options: {limit: 10, desc: "tradeAmount"}
          exchangeName: {is: "Pump"}
        ) {
          transaction {
            hash
          }
          token: baseCurrency {
            address
            name
            symbol
          }
          tradeAmount(in: USD)
          timeInterval {
            hour(count: 1)
          }
        }
      }
    }
    """

    headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': BITQUERY_API_KEY
    }

    try:
        response = requests.post(BITQUERY_API_URL, headers=headers, json={"query": query})
        response.raise_for_status()
        data = response.json()
        logger.debug("Successfully fetched top 10 pump tokens data from Solana.")
        logger.debug(f"Raw response: {data}")

        if data and "data" in data and "solana" in data["data"] and "dexTrades" in data["data"]["solana"]:
            trades = data["data"]["solana"]["dexTrades"]

            if trades:
                formatted_trades = []
                for trade in trades:
                    token_data = trade["token"]
                    if token_data and token_data.get("address"):
                        formatted_trade = {
                            "token_address": token_data["address"],
                            "token_name": token_data.get("name", "Unknown"),
                            "token_symbol": token_data.get("symbol", "Unknown"),
                            "trade_amount_usd": trade.get("tradeAmount", 0),
                            "solscan_link": f"https://solscan.io/token/{token_data['address']}"
                        }
                        formatted_trades.append(formatted_trade)

                return {"data": formatted_trades}
            else:
                logger.warning("No pump tokens data found.")
                return {"data": []}
        else:
            logger.error("The expected data structure was not found in the response.")
            return {"data": []}

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching top 10 pump tokens data: {e}")
        return {"data": [], "error": str(e)}
      

@tool
def fetch_latest_pancakeswap_tokens():
    """
    Fetches the 10 most recently created tokens on PancakeSwap on the Binance Smart Chain (BSC).

    This function queries the Bitquery API to retrieve information about the latest token pair creations
    on PancakeSwap, filters out known tokens, and identifies the newest token launches.

    Returns:
        dict: A dictionary containing data about the 10 most recent tokens created on PancakeSwap:
            - 'token_address': The address of the new token
            - 'token_name': The name of the token
            - 'token_symbol': The symbol of the token
            - 'creation_time': The timestamp of the token's first appearance in a pair

    Raises:
        Exception: If there's an error in fetching or processing the data
    """
    BITQUERY_API_URL = "https://graphql.bitquery.io"
    BITQUERY_API_KEY = os.getenv("BITQUERY_API_KEY")

    if not BITQUERY_API_KEY:
        return {"error": "API key not found", "data": []}

    query = """
    {
      ethereum(network: bsc) {
        dexTrades(
          options: {desc: "block.timestamp.time", limit: 1000}
          exchangeName: {is: "Pancake v2"}
          baseCurrency: {notIn: ["0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"]}
        ) {
          block {
            timestamp {
              time(format: "%Y-%m-%d %H:%M:%S")
            }
          }
          baseCurrency {
            address
            name
            symbol
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
        response = requests.post(BITQUERY_API_URL, json={"query": query}, headers=headers)
        response.raise_for_status()
        data = response.json()

        if "data" in data and "ethereum" in data["data"] and "dexTrades" in data["data"]["ethereum"]:
            trades = data["data"]["ethereum"]["dexTrades"]
            
            # Process to find new tokens
            known_tokens = set()
            new_tokens = []
            for trade in trades:
                token = trade["baseCurrency"]
                token_address = token["address"]
                creation_time = trade["block"]["timestamp"]["time"]
                
                if token_address not in known_tokens:
                    known_tokens.add(token_address)
                    new_tokens.append({
                        "token_address": token_address,
                        "token_name": token["name"],
                        "token_symbol": token["symbol"],
                        "creation_time": creation_time
                    })
                
                if len(new_tokens) >= 10:
                    break

            return {"data": new_tokens[:10]}
        else:
            return {"error": "Unexpected response structure", "data": []}

    except requests.exceptions.RequestException as e:
        return {"error": str(e), "data": []}
    except Exception as e:
        return {"error": f"Unexpected error occurred: {str(e)}", "data": []}
      
      
@tool
def get_multichain_portfolio(address: str, max_tokens_per_chain: int = 5, min_usd_value: float = 0.01) -> dict:
    """
    Retrieves a summarized multi-chain portfolio for a given wallet address across various EVM-compatible blockchains.

    Args:
        address (str): The wallet address to query.
        max_tokens_per_chain (int): Maximum number of tokens to return per chain. Default is 5.
        min_usd_value (float): Minimum USD value for a token to be included. Default is 0.01.

    Returns:
        dict: A summarized portfolio data for each supported blockchain.
    """
    query = """
    query ($address: String!) {
      ethereum: ethereum {
        address(address: {is: $address}) {
          balances {
            value
            usdValue: value(in: USD)
            currency {
              address
              symbol
              tokenType
            }
          }
        }
      }
      bsc: ethereum(network: bsc) {
        address(address: {is: $address}) {
          balances {
            value
            usdValue: value(in: USD)
            currency {
              address
              symbol
              tokenType
            }
          }
        }
      }
      matic: ethereum(network: matic) {
        address(address: {is: $address}) {
          balances {
            value
            usdValue: value(in: USD)
            currency {
              address
              symbol
              tokenType
            }
          }
        }
      }
      # Add more chains as needed
    }
    """
    variables = {
        "address": address,
    }

    try:
        response = requests.post(BITQUERY_API_URL, json={"query": query, "variables": variables}, headers=headers)
        response.raise_for_status()
        data = response.json()

        if 'data' not in data:
            raise Exception("Unexpected response structure")

        portfolio = {}
        total_value = 0

        for chain in data['data']:
            chain_data = data['data'][chain].get('address', [])
            if chain_data and isinstance(chain_data, list) and len(chain_data) > 0:
                balances = chain_data[0].get('balances', [])
                if balances:
                    valid_tokens = [
                        {
                            'Symbol': token['currency'].get('symbol', 'Unknown'),
                            'Address': token['currency'].get('address', 'N/A'),
                            'USD Value': float(token.get('usdValue', 0)),
                            'Token Type': token['currency'].get('tokenType', 'Unknown')
                        }
                        for token in balances
                        if isinstance(token, dict) and 'currency' in token
                        and float(token.get('usdValue', 0)) >= min_usd_value
                    ]
                    valid_tokens.sort(key=lambda x: x['USD Value'], reverse=True)
                    portfolio[chain] = valid_tokens[:max_tokens_per_chain]
                    total_value += sum(token['USD Value'] for token in portfolio[chain])

        # Sort chains by total value
        sorted_portfolio = dict(sorted(portfolio.items(), key=lambda x: sum(token['USD Value'] for token in x[1]), reverse=True))

        return {
            "total_value_usd": total_value,
            "portfolio": sorted_portfolio
        }

    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching data from Bitquery: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing portfolio data: {str(e)}")

        