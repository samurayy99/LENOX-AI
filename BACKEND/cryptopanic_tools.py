import os
import requests
from dotenv import load_dotenv
from langchain.agents import tool
import time

# Load environment variables from .env file
load_dotenv()

@tool
def get_latest_news(query: str = "") -> str:
    """
    Fetches the latest news from CryptoPanic.
    
    Args:
        query: Optional token symbol to filter news (e.g., 'WIF', 'BONK')
    """
    api_key = os.getenv('CRYPTOPANIC_API_KEY')
    if not api_key:
        return "API key for CryptoPanic not found. Please set it in the environment variables."

    # Clean up query for better results (handle $ symbol)
    clean_query = query.strip()
    if clean_query.startswith('$'):
        clean_query = clean_query[1:]

    # Build URL with optional currency filter
    url = f'https://cryptopanic.com/api/v1/posts/?auth_token={api_key}&public=true'
    if clean_query:
        url += f'&currencies={clean_query}'
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            news = response.json()
            if not news.get('results'):
                return f"No news found for {query if query else 'cryptocurrency'}"
                
            # Format news items with time
            news_items = []
            current_time = time.time()
            for item in news['results']:
                try:
                    published_time = time.strptime(item['published_at'], "%Y-%m-%dT%H:%M:%SZ")
                    published_timestamp = time.mktime(published_time)
                    time_diff = current_time - published_timestamp
                    
                    if time_diff < 3600:  # Less than 1 hour
                        time_str = f"{int(time_diff/60)}m ago"
                    elif time_diff < 86400:  # Less than 24 hours
                        time_str = f"{int(time_diff/3600)}h ago"
                    else:
                        days = int(time_diff/86400)
                        time_str = f"{days}d ago"
                    
                    news_items.append(
                        f"📰 [{item['title']}]({item['url']})\n"
                        f"   Source: {item['domain']} | Time: {time_str}"
                    )
                except (ValueError, KeyError):
                    continue
            
            if not news_items:
                return f"No news found for {query}"
                
            return '\n\n'.join(news_items[:5])  # Return top 5 news items
        else:
            return f"Failed to fetch news: {response.status_code}"
    except Exception as e:
        return f"Error occurred while fetching news: {str(e)}"


@tool
def get_last_news_title() -> str:
    """
    Fetches the title of the most recent news from CryptoPanic.
    """
    api_key = os.getenv('CRYPTOPANIC_API_KEY')
    if not api_key:
        return "API key for CryptoPanic not found. Please set it in the environment variables."

    url = f'https://cryptopanic.com/api/v1/posts/?auth_token={api_key}&public=true'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            news = response.json()
            if news['results']:
                item = news['results'][0]
                return f"[{item['title']}]({item['url']})"
            else:
                return "No news available"
        else:
            return f"Failed to fetch the latest news title: {response.status_code}"
    except Exception as e:
        return f"Error occurred while fetching the latest news title: {str(e)}"