import re
import json
from typing import Dict, Any
from dotenv import load_dotenv
import spacy
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage

# Load environment variables from .env file
load_dotenv()

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Import the necessary tools
from reddit_tools import get_reddit_data, count_mentions, analyze_sentiment, find_trending_topics
from cryptocompare_tools import (
    get_current_price, get_top_volume_symbols,
    get_latest_social_stats, get_historical_social_stats, list_news_feeds_and_categories,
    get_latest_trading_signals, get_top_exchanges_by_volume, get_historical_daily
)
from coingecko_tools import (
    get_market_data, get_historical_market_data, get_ohlc,
    get_trending_cryptos, calculate_macd, get_exchange_rates, calculate_rsi
)
from youtube_tools import search_youtube, process_youtube_video, query_youtube_video
from coinpaprika_tools import get_coin_details, get_coin_tags, get_market_overview, get_ticker_info
from cryptopanic_tools import get_latest_news, get_news_sources, get_last_news_title
from coinmarketcap_tools import get_latest_listings, get_crypto_metadata, get_global_metrics
from fearandgreed_tools import get_fear_and_greed_index
from whale_alert_tools import get_whale_alert_status, get_transaction_by_hash, get_recent_transactions
from binance_tools import get_binance_ticker, get_binance_order_book, get_binance_recent_trades

# Define tool wrappers
class ToolWrapper:
    def __init__(self, func):
        self.func = func

    def run(self, params):
        return self.func(**params)

# Define tool metadata
tool_metadata = {
    # Reddit Tools
    "get_reddit_data": {
        "patterns": [r"\b(reddit mentions|reddit data|reddit)\b"],
        "params": {
            "subreddit": {"default": "Bitcoin", "type": "entity", "entity_type": "ORG"},
            "category": {"default": "hot", "type": "entity", "entity_type": "CATEGORY"}
        }
    },
    "count_mentions": {
        "patterns": [r"\b(count mentions|mentions count|mention count)\b"],
        "params": {
            "subreddit": {"default": "Bitcoin", "type": "entity", "entity_type": "ORG"},
            "keyword": {"default": "", "type": "text"}
        }
    },
    "analyze_sentiment": {
        "patterns": [r"\b(sentiment analysis|analyze sentiment|sentiment)\b"],
        "params": {
            "subreddit": {"default": "Bitcoin", "type": "entity", "entity_type": "ORG"},
            "keyword": {"default": "", "type": "text"}
        }
    },
    "find_trending_topics": {
        "patterns": [r"\b(trending topics|trending)\b"],
        "params": {
            "subreddits": {"default": ["Bitcoin"], "type": "list", "entity_type": "ORG"}
        }
    },
    # CryptoCompare Tools
    "get_current_price": {
        "patterns": [r"\b(current price|price of bitcoin|btc price|bitcoin price)\b"],
        "params": {"symbol": {"default": "BTC", "type": "constant"}}
    },
    "get_top_volume_symbols": {
        "patterns": [r"\b(top volume symbols|top symbols|volume symbols)\b"],
        "params": {}
    },
    "get_latest_social_stats": {
        "patterns": [r"\b(latest social stats|social stats)\b"],
        "params": {}
    },
    "get_historical_social_stats": {
        "patterns": [r"\b(historical social stats|social stats history)\b"],
        "params": {}
    },
    "list_news_feeds_and_categories": {
        "patterns": [r"\b(news feeds and categories|news categories|news feeds)\b"],
        "params": {}
    },
    "get_latest_trading_signals": {
        "patterns": [r"\b(latest trading signals|trading signals)\b"],
        "params": {}
    },
    "get_top_exchanges_by_volume": {
        "patterns": [r"\b(top exchanges by volume|top exchanges|exchanges volume)\b"],
        "params": {}
    },
    "get_historical_daily": {
        "patterns": [r"\b(historical daily|daily history)\b"],
        "params": {}
    },
    # CoinGecko Tools
    "get_market_data": {
        "patterns": [r"\b(market data|crypto market data)\b"],
        "params": {}
    },
    "get_historical_market_data": {
        "patterns": [r"\b(historical market data|market data history)\b"],
        "params": {}
    },
    "get_ohlc": {
        "patterns": [r"\b(ohlc|open high low close)\b"],
        "params": {}
    },
    "get_trending_cryptos": {
        "patterns": [r"\b(trending cryptos|trending cryptocurrencies)\b"],
        "params": {}
    },
    "calculate_macd": {
        "patterns": [r"\b(calculate macd|macd)\b"],
        "params": {}
    },
    "get_exchange_rates": {
        "patterns": [r"\b(exchange rates|crypto exchange rates)\b"],
        "params": {}
    },
    "calculate_rsi": {
        "patterns": [r"\b(calculate rsi|rsi)\b"],
        "params": {}
    },
    # YouTube Tools
    "search_youtube": {
        "patterns": [r"\b(search youtube|youtube search)\b"],
        "params": {}
    },
    "process_youtube_video": {
        "patterns": [r"\b(process youtube video|youtube video process)\b"],
        "params": {}
    },
    "query_youtube_video": {
        "patterns": [r"\b(query youtube video|youtube video query)\b"],
        "params": {}
    },
    # CoinPaprika Tools
    "get_coin_details": {
        "patterns": [r"\b(coin details|details of coin)\b"],
        "params": {}
    },
    "get_coin_tags": {
        "patterns": [r"\b(coin tags|tags of coin)\b"],
        "params": {}
    },
    "get_market_overview": {
        "patterns": [r"\b(market overview|overview of market)\b"],
        "params": {}
    },
    "get_ticker_info": {
        "patterns": [r"\b(ticker info|info of ticker)\b"],
        "params": {}
    },
    # CryptoPanic Tools
    "get_latest_news": {
        "patterns": [r"\b(latest news|news)\b"],
        "params": {}
    },
    "get_news_sources": {
        "patterns": [r"\b(news sources|sources of news)\b"],
        "params": {}
    },
    "get_last_news_title": {
        "patterns": [r"\b(last news title|news title)\b"],
        "params": {}
    },
    # CoinMarketCap Tools
    "get_latest_listings": {
        "patterns": [r"\b(latest listings|listings)\b"],
        "params": {}
    },
    "get_crypto_metadata": {
        "patterns": [r"\b(crypto metadata|metadata)\b"],
        "params": {}
    },
    "get_global_metrics": {
        "patterns": [r"\b(global metrics|metrics)\b"],
        "params": {}
    },
    # Fear and Greed Index Tools
    "get_fear_and_greed_index": {
        "patterns": [r"\b(fear and greed index|fear and greed)\b"],
        "params": {}
    },
    # Whale Alert Tools
    "get_whale_alert_status": {
        "patterns": [r"\b(whale alert status|whale alert)\b"],
        "params": {}
    },
    "get_transaction_by_hash": {
        "patterns": [r"\b(transaction by hash|hash transaction)\b"],
        "params": {}
    },
    "get_recent_transactions": {
        "patterns": [r"\b(recent transactions|transactions)\b"],
        "params": {}
    },
    # Binance Tools
    "get_binance_ticker": {
        "patterns": [r"\b(binance ticker|ticker)\b"],
        "params": {}
    },
    "get_binance_order_book": {
        "patterns": [r"\b(binance order book|order book)\b"],
        "params": {}
    },
    "get_binance_recent_trades": {
        "patterns": [r"\b(binance recent trades|recent trades)\b"],
        "params": {}
    }
    # Add other tools' metadata here
}

class IntentRouter:
    def __init__(self):
        self.tools = {
            # Reddit Tools
            "get_reddit_data": ToolWrapper(get_reddit_data),
            "count_mentions": ToolWrapper(count_mentions),
            "analyze_sentiment": ToolWrapper(analyze_sentiment),
            "find_trending_topics": ToolWrapper(find_trending_topics),
            # CryptoCompare Tools
            "get_current_price": ToolWrapper(get_current_price),
            "get_top_volume_symbols": ToolWrapper(get_top_volume_symbols),
            "get_latest_social_stats": ToolWrapper(get_latest_social_stats),
            "get_historical_social_stats": ToolWrapper(get_historical_social_stats),
            "list_news_feeds_and_categories": ToolWrapper(list_news_feeds_and_categories),
            "get_latest_trading_signals": ToolWrapper(get_latest_trading_signals),
            "get_top_exchanges_by_volume": ToolWrapper(get_top_exchanges_by_volume),
            "get_historical_daily": ToolWrapper(get_historical_daily),
            # CoinGecko Tools
            "get_market_data": ToolWrapper(get_market_data),
            "get_historical_market_data": ToolWrapper(get_historical_market_data),
            "get_ohlc": ToolWrapper(get_ohlc),
            "get_trending_cryptos": ToolWrapper(get_trending_cryptos),
            "calculate_macd": ToolWrapper(calculate_macd),
            "get_exchange_rates": ToolWrapper(get_exchange_rates),
            "calculate_rsi": ToolWrapper(calculate_rsi),
            # YouTube Tools
            "search_youtube": ToolWrapper(search_youtube),
            "process_youtube_video": ToolWrapper(process_youtube_video),
            "query_youtube_video": ToolWrapper(query_youtube_video),
            # CoinPaprika Tools
            "get_coin_details": ToolWrapper(get_coin_details),
            "get_coin_tags": ToolWrapper(get_coin_tags),
            "get_market_overview": ToolWrapper(get_market_overview),
            "get_ticker_info": ToolWrapper(get_ticker_info),
            # CryptoPanic Tools
            "get_latest_news": ToolWrapper(get_latest_news),
            "get_news_sources": ToolWrapper(get_news_sources),
            "get_last_news_title": ToolWrapper(get_last_news_title),
            # CoinMarketCap Tools
            "get_latest_listings": ToolWrapper(get_latest_listings),
            "get_crypto_metadata": ToolWrapper(get_crypto_metadata),
            "get_global_metrics": ToolWrapper(get_global_metrics),
            # Fear and Greed Index Tools
            "get_fear_and_greed_index": ToolWrapper(get_fear_and_greed_index),
            # Whale Alert Tools
            "get_whale_alert_status": ToolWrapper(get_whale_alert_status),
            "get_transaction_by_hash": ToolWrapper(get_transaction_by_hash),
            "get_recent_transactions": ToolWrapper(get_recent_transactions),
            # Binance Tools
            "get_binance_ticker": ToolWrapper(get_binance_ticker),
            "get_binance_order_book": ToolWrapper(get_binance_order_book),
            "get_binance_recent_trades": ToolWrapper(get_binance_recent_trades)
        }
        self.tool_metadata = tool_metadata
        self.chat_model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
        self.system_prompt = SystemMessage(content=self.system_prompt_content())

    def system_prompt_content(self):
        return """
        You are Lenox, a highly conversational and emotionally intelligent digital assistant. Your primary goal is to assist users with their queries while being empathetic, understanding, and engaging. Here are some guidelines to follow:
        ...
        """

    def detect_intent(self, query: str) -> Dict[str, Any]:
        detected_intents = {}
        for tool_name, metadata in self.tool_metadata.items():
            for pattern in metadata["patterns"]:
                if re.search(pattern, query, re.IGNORECASE):
                    detected_intents[tool_name] = True
        print(f"Detected intents: {detected_intents}")  # Debug print
        return detected_intents

    def parse_query(self, query: str, intents: Dict[str, Any]) -> Dict[str, Any]:
        parsed_data = {}
        doc = nlp(query)
        for tool_name, _ in intents.items():
            params = {}
            for param_name, param_info in self.tool_metadata[tool_name]["params"].items():
                if param_info["type"] == "constant":
                    params[param_name] = param_info["default"]
                elif param_info["type"] == "entity":
                    entity_value = self.extract_entity(doc, param_info["entity_type"])
                    params[param_name] = entity_value if entity_value else param_info["default"]
                elif param_info["type"] == "text":
                    params[param_name] = param_info["default"]  # Default to empty text for now
                elif param_info["type"] == "list":
                    params[param_name] = [param_info["default"]]  # Default to list containing default value
            parsed_data[tool_name] = params
        print(f"Parsed query data: {parsed_data}")  # Debug print
        return parsed_data

    def extract_entity(self, doc, entity_type: str) -> str:
        for ent in doc.ents:
            if ent.label_ == entity_type:
                return ent.text
        return ""

    def route_query(self, query: str) -> Dict[str, Any]:
        detected_intents = self.detect_intent(query)
        parsed_data = self.parse_query(query, detected_intents)
        responses = {}

        for tool_name in detected_intents.keys():
            tool = self.tools.get(tool_name)
            if tool:
                try:
                    params = parsed_data.get(tool_name, {})
                    print(f"Invoking tool: {tool_name} with params: {params}")  # Debug print
                    response = tool.run(params)  # Ensure the method call is correct
                    if isinstance(response, dict):
                        response = json.dumps(response)
                    responses[tool_name] = response
                except Exception as e:
                    responses[tool_name] = {"error": str(e)}

        print(f"Responses: {responses}")  # Debug print
        return responses

# Example of initializing and using the IntentRouter
if __name__ == "__main__":
    router = IntentRouter()
    query = "What is the price of bitcoin now?"
    response = router.route_query(query)
    print(response)
