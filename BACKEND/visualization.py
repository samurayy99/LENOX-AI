import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
import yfinance as yf
import numpy as np
from typing import Dict, Any, Optional

def fetch_crypto_data(symbol: str, period: str = '1mo') -> Dict[str, Any]:
    try:
        crypto = yf.Ticker(f"{symbol}-USD")
        data = crypto.history(period=period)
        return {"dates": data.index.tolist(), "prices": data['Close'].tolist()}
    except Exception as e:
        raise ValueError(f"Error fetching data for {symbol}: {str(e)}")

def create_line_chart(symbol: str, period: str = '1mo', title: Optional[str] = None) -> str:
    data = fetch_crypto_data(symbol, period)
    
    plt.figure(figsize=(12, 6))
    plt.plot(data['dates'], data['prices'], marker='o')
    plt.title(title or f"{symbol} Price Chart ({period})")
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
    plt.grid(True)
    
    return convert_plot_to_base64()

def create_bar_chart(symbol: str, period: str = '1mo', title: Optional[str] = None) -> str:
    data = fetch_crypto_data(symbol, period)
    
    prices = np.array(data['prices'])
    daily_returns = np.diff(prices) / prices[:-1]
    
    plt.figure(figsize=(12, 6))
    plt.bar(data['dates'][1:], daily_returns)
    plt.title(title or f"{symbol} Daily Returns ({period})")
    plt.xlabel('Date')
    plt.ylabel('Daily Return')
    
    return convert_plot_to_base64()

def convert_plot_to_base64() -> str:
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    base64_img = base64.b64encode(img.getvalue()).decode('utf8')
    
    plt.close()
    
    return f"data:image/png;base64,{base64_img}"

def generate_visualization(query: str, symbol: str) -> Dict[str, Any]:
    period = '1mo'  # Default to 1 month
    
    if 'week' in query.lower():
        period = '1wk'
    elif 'year' in query.lower():
        period = '1y'
    
    if 'line chart' in query.lower() or 'price chart' in query.lower():
        image = create_line_chart(symbol, period)
        chart_type = 'line'
    elif 'bar chart' in query.lower() or 'return chart' in query.lower():
        image = create_bar_chart(symbol, period)
        chart_type = 'bar'
    else:
        raise ValueError(f"Unknown visualization type requested: {query}")

    return {
        "type": "visualization",
        "content": f"Generated {chart_type} chart for {symbol} ({period})",
        "image": image
    }