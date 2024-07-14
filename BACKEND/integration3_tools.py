from langchain.tools import tool
from whale_alert_tools import get_recent_transactions
from cryptocompare_tools import get_latest_trading_signals
from coingecko_tools import get_trending_cryptos as get_trending_cryptos_coingecko
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@tool
def combined_market_analysis(tool_input: dict) -> str:
    """
    Combines Whale Alert transactions, latest trading signals from CryptoCompare, and trending cryptocurrencies
    from CoinGecko to provide a comprehensive market analysis for a specified cryptocurrency.
    """
    try:
        logging.debug(f"Received tool_input: {tool_input}")
        symbol = tool_input.get("symbol", "")
        logging.debug(f"Symbol: {symbol}")
        
        # Whale Alert Transactions
        logging.debug("Fetching Whale Alert transactions...")
        whale_transactions = get_recent_transactions()
        logging.debug(f"Whale Alert transactions: {whale_transactions}")
        
        # Latest Trading Signals from CryptoCompare
        logging.debug("Fetching latest trading signals from CryptoCompare...")
        trading_signals = get_latest_trading_signals(symbol)
        logging.debug(f"Latest trading signals: {trading_signals}")
        
        # Trending Cryptos from CoinGecko
        logging.debug("Fetching trending cryptos from CoinGecko...")
        trending_cryptos_coingecko = get_trending_cryptos_coingecko()
        logging.debug(f"Trending cryptos on CoinGecko: {trending_cryptos_coingecko}")
        
        combined_analysis = (
            f"Whale Alert Transactions: {whale_transactions}\n"
            f"Latest Trading Signals: {trading_signals}\n"
            f"Trending Cryptos on CoinGecko: {trending_cryptos_coingecko}"
        )
        
        return combined_analysis
    except Exception as e:
        logging.error(f"Error in combined_market_analysis: {str(e)}")
        return f"Error in combined_market_analysis: {str(e)}"

@tool
def combined_analysis_recommendation(tool_input: dict) -> str:
    """
    Combines market analysis and provides recommendations based on the analysis results.

    Args:
    - tool_input (dict): Dictionary containing the symbol for the analysis.

    Returns:
    - str: A comprehensive analysis and recommendation.
    """
    try:
        analysis = combined_market_analysis(tool_input)
        logging.debug(f"Market analysis: {analysis}")
        
        # Generate a recommendation based on the analysis
        recommendation = generate_recommendation_from_analysis(analysis)
        logging.debug(f"Recommendation: {recommendation}")
        
        return f"{analysis}\n\nRecommendation: {recommendation}"
    except Exception as e:
        logging.error(f"Error in combined_analysis_recommendation: {str(e)}")
        return f"Error in combined_analysis_recommendation: {str(e)}"

def generate_recommendation_from_analysis(analysis: str) -> str:
    """
    Generates a recommendation based on the analysis results.

    Args:
    - analysis (str): The result of the market analysis.

    Returns:
    - str: A recommendation based on the analysis.
    """
    recommendation = "Based on the analysis:\n"
    
    # Interpret Whale Transactions
    if "Whale Alert Transactions" in analysis:
        recommendation += "- Recent whale transactions indicate significant market activity. Monitor the market closely for potential large movements.\n"
    
    # Interpret Trading Signals
    if "Latest Trading Signals" in analysis:
        if "bullish" in analysis:
            recommendation += "- The trading signals indicate a bullish trend. It might be a good time to consider buying.\n"
        elif "bearish" in analysis:
            recommendation += "- The trading signals indicate a bearish trend. It might be a good time to consider selling.\n"
    
    # Interpret Trending Cryptos
    if "Trending Cryptos on CoinGecko" in analysis:
        recommendation += "- The trending cryptos on CoinGecko provide insights into popular cryptocurrencies. Consider these for potential investment opportunities.\n"
    
    return recommendation