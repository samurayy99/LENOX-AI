from typing import Dict, List, Any
from dotenv import load_dotenv
import json
import re

# Load environment variables from .env file
load_dotenv()

from reddit_tools import get_reddit_data, count_mentions, analyze_sentiment, find_trending_topics
from cryptocompare_tools import get_current_price as cryptocompare_get_current_price, get_top_volume_symbols, get_latest_social_stats, get_historical_social_stats, list_news_feeds_and_categories, get_latest_trading_signals, get_top_exchanges_by_volume, get_historical_daily
from coingecko_tools import get_market_data, get_historical_market_data, get_ohlc, get_trending_cryptos, calculate_macd, get_exchange_rates, calculate_rsi
from youtube_tools import search_youtube, process_youtube_video, query_youtube_video
from coinpaprika_tools import get_coin_details, get_coin_tags, get_market_overview, get_ticker_info
from cryptopanic_tools import get_latest_news

class IntentRouter:
    def __init__(self):
        self.tools = {
            "get_reddit_data": get_reddit_data,
            "count_mentions": count_mentions,
            "analyze_sentiment": analyze_sentiment,
            "find_trending_topics": find_trending_topics,
            "get_current_price": cryptocompare_get_current_price,
            "get_top_volume_symbols": get_top_volume_symbols,
            "get_latest_social_stats": get_latest_social_stats,
            "get_historical_social_stats": get_historical_social_stats,
            "list_news_feeds_and_categories": list_news_feeds_and_categories,
            "get_latest_trading_signals": get_latest_trading_signals,
            "get_top_exchanges_by_volume": get_top_exchanges_by_volume,
            "get_historical_daily": get_historical_daily,
            "get_market_data": get_market_data,
            "get_historical_market_data": get_historical_market_data,
            "get_ohlc": get_ohlc,
            "get_trending_cryptos": get_trending_cryptos,
            "calculate_macd": calculate_macd,
            "get_exchange_rates": get_exchange_rates,
            "calculate_rsi": calculate_rsi,
            "search_youtube": search_youtube,
            "process_youtube_video": process_youtube_video,
            "query_youtube_video": query_youtube_video,
            "get_coin_details": get_coin_details,
            "get_coin_tags": get_coin_tags,
            "get_market_overview": get_market_overview,
            "get_ticker_info": get_ticker_info,
            "get_latest_news": get_latest_news
        }

        # Define patterns for different tools
        self.tool_patterns = {
            "fetch_bitcoin_price": re.compile(r"\b(bitcoin price|btc price|current bitcoin value)\b", re.IGNORECASE),
            "get_reddit_data": re.compile(r"\b(reddit data|reddit mentions|reddit sentiment)\b", re.IGNORECASE),
            "get_current_price": re.compile(r"\b(current price|price of)\b", re.IGNORECASE),
            "get_market_data": re.compile(r"\b(market data|market overview)\b", re.IGNORECASE),
            # Add more patterns for other tools as needed
        }

    def detect_intent(self, query: str) -> List[str]:
        relevant_tools = [tool_name for tool_name, pattern in self.tool_patterns.items() if pattern.search(query)]
        return relevant_tools

    def identify_relevant_tools(self, user_query: str) -> List[str]:
        return self.detect_intent(user_query)

    def parse_query(self, query: str) -> Dict[str, Any]:
        # Extract relevant parts of the query for each tool
        parsed_data = {}
        if "current price" in query or "price of" in query:
            parsed_data["get_current_price"] = {"symbol": "BTC"}  # Example: Extract symbol from query
        if "market data" in query or "market overview" in query:
            parsed_data["get_market_data"] = {"coin_ids": ["bitcoin"], "vs_currency": "usd"}  # Example: Extract coin_ids and vs_currency from query
        return parsed_data

    def route_query(self, query: str) -> Dict[str, Any]:
        relevant_tools = self.detect_intent(query)
        parsed_data = self.parse_query(query)
        responses = {}

        for tool_name in relevant_tools:
            tool = self.tools.get(tool_name)
            if tool:
                try:
                    params = parsed_data.get(tool_name, {})
                    response = tool.invoke(params)  # Use invoke method
                    if isinstance(response, dict):
                        response = json.dumps(response)  # Convert dict to string
                    responses[tool_name] = response
                except Exception as e:
                    responses[tool_name] = {"error": str(e)}

        return responses