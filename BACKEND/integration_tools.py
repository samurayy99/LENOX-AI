import requests
from datetime import datetime, timedelta
from langchain.tools import tool
import logging

@tool
def get_current_price(symbol):
    """
    Get the current price of a cryptocurrency from Binance.

    Args:
    - symbol (str): The trading pair symbol (e.g., 'BTCUSDT').

    Returns:
    - dict: The API response containing the current price.
    """
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url)
    data = response.json()
    
    # Add debug logging
    logging.debug(f"API response for {symbol}: {data}")
    
    # Check if 'price' key exists
    if 'price' not in data:
        logging.error(f"'price' key not found in the response for {symbol}")
        raise KeyError(f"'price' key not found in the response for {symbol}")
    
    return data
     

@tool
def get_historical_prices(symbol, days=7):
    """
    Get the historical closing prices of a cryptocurrency for the last specified number of days from Binance.
    """
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&startTime={start_time}&endTime={end_time}"
    response = requests.get(url)
    return response.json()


@tool
def comment_on_price(symbol):
    """
    Analyze the current price of a cryptocurrency against its historical prices and provide a comment.

    Args:
    - symbol (str): The trading pair symbol (e.g., 'BTCUSDT').

    Returns:
    - str: A comment on the current price compared to historical prices.
    """
    try:
        current_price_data = get_current_price(symbol)
        historical_price_data = get_historical_prices(symbol)
        
        current_price = float(current_price_data['price'])
        historical_prices = [float(day[4]) for day in historical_price_data]  # Closing prices of the last days
        avg_historical_price = sum(historical_prices) / len(historical_prices)
        
        if current_price > avg_historical_price * 1.2:
            return f"The price of {symbol} is quite high at {current_price} USD, compared to the average historical price of {avg_historical_price} USD. It might be a good idea to sell some assets."
        elif current_price < avg_historical_price * 0.8:
            return f"The price of {symbol} is relatively low at {current_price} USD, compared to the average historical price of {avg_historical_price} USD. This could be a buying opportunity."
        else:
            return f"The price of {symbol} is stable at {current_price} USD, compared to the average historical price of {avg_historical_price} USD. Consider holding your assets."
    except KeyError as e:
        return f"Error: {str(e)}"