import requests
from datetime import datetime, timedelta
from langchain.tools import tool

@tool
def get_current_price(symbol):
    """
    Get the current price of a cryptocurrency from Binance.
    """
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url)
    return response.json()

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
    """
    current_price_data = get_current_price(symbol)
    historical_price_data = get_historical_prices(symbol)
    
    current_price = float(current_price_data['price'])
    historical_prices = [float(day[4]) for day in historical_price_data]  # Schlusskurse der letzten Tage
    avg_historical_price = sum(historical_prices) / len(historical_prices)
    
    if current_price > avg_historical_price * 1.2:
        return f"The price of {symbol} is quite high at {current_price} USD, compared to the average historical price of {avg_historical_price} USD. It might be a good idea to sell some assets."
    elif current_price < avg_historical_price * 0.8:
        return f"The price of {symbol} is relatively low at {current_price} USD, compared to the average historical price of {avg_historical_price} USD. This could be a buying opportunity."
    else:
        return f"The price of {symbol} is stable at {current_price} USD, compared to the average historical price of {avg_historical_price} USD. Consider holding your assets."
