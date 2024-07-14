import logging
from datetime import datetime, timedelta
from langchain.tools import tool
from coingecko_tools import calculate_rsi, calculate_macd
from fearandgreed_tools import get_fear_and_greed_index
from whale_alert_tools import get_recent_transactions

@tool
def combined_technical_analysis(symbol: str, prices: list, period: int = 14) -> str:
    """
    Combines RSI, MACD, Fear and Greed Index, and Whale Alert data to provide a comprehensive analysis and recommendation.

    Args:
    - symbol (str): The trading pair symbol (e.g., 'BTCUSDT').
    - prices (list): List of historical prices for the symbol.
    - period (int): The period for RSI calculation. Default is 14.

    Returns:
    - str: A comprehensive analysis and recommendation.
    """
    try:
        # Calculate RSI
        rsi_result = calculate_rsi(prices, period)
        
        # Calculate MACD
        macd_result = calculate_macd(prices)
        
        # Get Fear and Greed Index
        fng_result = get_fear_and_greed_index()
        
        # Get recent whale transactions
        start_time = int((datetime.now() - timedelta(days=1)).timestamp())
        whale_transactions = get_recent_transactions(start=start_time)
        
        # Combine the results into a comprehensive analysis
        analysis = f"RSI Analysis: {rsi_result}\n\n"
        analysis += f"MACD Analysis: {macd_result}\n\n"
        analysis += f"Fear and Greed Index: {fng_result}\n\n"
        analysis += f"Recent Whale Transactions: {whale_transactions}\n\n"
        
        # Generate a recommendation based on the analysis
        recommendation = generate_recommendation(rsi_result, macd_result, fng_result, whale_transactions)
        
        return f"{analysis}\nRecommendation: {recommendation}"
    except Exception as e:
        logging.error(f"Error in combined technical analysis: {str(e)}")
        return f"Error in combined technical analysis: {str(e)}"

@tool
def generate_recommendation(rsi_result: str, macd_result: str, fng_result: str, whale_transactions: str) -> str:
    """
    Generates a recommendation based on the analysis results.

    Args:
    - rsi_result (str): The result of the RSI analysis.
    - macd_result (str): The result of the MACD analysis.
    - fng_result (str): The result of the Fear and Greed Index analysis.
    - whale_transactions (str): The result of the Whale Alert analysis.

    Returns:
    - str: A recommendation based on the analysis.
    """
    recommendation = "Based on the analysis:\n"
    
    # Interpret RSI
    if "RSI: " in rsi_result:
        rsi_value = float(rsi_result.split("RSI: ")[1])
        if rsi_value > 70:
            recommendation += "- The RSI indicates that the market is overbought. It might be a good time to consider selling.\n"
        elif rsi_value < 30:
            recommendation += "- The RSI indicates that the market is oversold. It might be a good time to consider buying.\n"
        else:
            recommendation += "- The RSI indicates that the market is neutral. Consider holding your assets.\n"
    
    # Interpret MACD
    if "bullish" in macd_result:
        recommendation += "- The MACD indicates a bullish trend. It might be a good time to consider buying.\n"
    elif "bearish" in macd_result:
        recommendation += "- The MACD indicates a bearish trend. It might be a good time to consider selling.\n"
    
    # Interpret Fear and Greed Index
    if "Fear and Greed Index" in fng_result:
        fng_value = int(fng_result.split("value: ")[1].split(",")[0])
        if fng_value > 60:
            recommendation += "- The Fear and Greed Index indicates greed in the market. Be cautious of potential overvaluation.\n"
        elif fng_value < 40:
            recommendation += "- The Fear and Greed Index indicates fear in the market. There might be buying opportunities.\n"
        else:
            recommendation += "- The Fear and Greed Index indicates a neutral market sentiment.\n"
    
    # Interpret Whale Transactions
    if "transactions" in whale_transactions:
        recommendation += "- Recent whale transactions indicate significant market activity. Monitor the market closely for potential large movements.\n"
    
    return recommendation