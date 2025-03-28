import os
import re
import json
import time
import logging
import asyncio
from typing import Dict, List, Any
from dotenv import load_dotenv
from langchain.tools import tool
from twikit.client.client import Client
from datetime import datetime

# === ENV & CONFIG ===
load_dotenv()
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
TWITTER_EMAIL = os.getenv("TWITTER_EMAIL") 
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
TWITTER_COOKIES_FILE = os.getenv("TWITTER_COOKIES_FILE", "twitter_cookies.json")

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("twitter_tools")

# === CLIENT MANAGEMENT ===
_twitter_client = None
_last_auth_time = 0
_client_lock = asyncio.Lock()

# === CACHE SYSTEM ===
CACHE: Dict[str, tuple[Any, float]] = {}
CACHE_TTL = 600  # 10 minutes (increased from 5 minutes for better performance)

# === MEMECOIN INFLUENCER LIST ===
INFLUENCER_HANDLES = [
    "@barkmeta", "@IcedKnife", "@blknoiz06", "@LockedInLucas", "@Ashcryptoreal",
    "@lynk0x", "@shahh", "@tvbzify", "@0xSweep", "@WatcherGuru", "@HopiumPapi",
    "@Jeremyybtc", "@SolJakey", "@DegenerateNews", "@mrpunkdoteth", "@Brookcalls_",
    "@ogKOBEWAN", "@Poe_Ether", "@yuumiweb3", "@RoarWeb3", "@mythdyor", "@Doodlegenics",
    "@Block100x", "@0xRamonos", "@3orovik", "@KingAnt777", "@MustStopMurad"
]

# === KEYWORD LISTS ===
BULLISH_KEYWORDS = ['moon', 'bullish', 'buy', 'pump', 'gem', 'degen', 'gain', 'wen', 'lfg', 'alpha', 
                    'listing', 'launch', 'airdrop', 'presale', 'early', 'apeing', 'ape', 'mint']
BEARISH_KEYWORDS = ['dump', 'sell', 'scam', 'rug', 'bearish', 'crash', 'drop', 'fell', 'warning',
                    'caution', 'avoid', 'exit', 'selling', 'bearish', 'fraud']
ALPHA_KEYWORDS = [
    "just launched", "fair launch", "stealth launch", "LP locked", "next 100x",
    "ape now", "don't miss", "airdrop live", "presale", "zero tax", "no team tokens"
]

def _cache_get(key: str) -> Any:
    """Get data from cache if exists and not expired"""
    if key in CACHE:
        data, ts = CACHE[key]
        if time.time() - ts < CACHE_TTL:
            logger.debug(f"Cache hit for {key}")
            return data
    return None

def _cache_set(key: str, data: Any) -> None:
    """Store data in cache with timestamp"""
    CACHE[key] = (data, time.time())

async def _get_twitter_client() -> Client:
    """Get an authenticated Twitter client, creating one if necessary"""
    global _twitter_client, _last_auth_time
    
    async with _client_lock:
        current_time = time.time()
        
        # If client exists and was authenticated in the last hour, return it
        if _twitter_client and (current_time - _last_auth_time < 3600):
            return _twitter_client
        
        # Create new client
        client = Client(language="en-US")
        
        # Try to load cookies if they exist
        if os.path.exists(TWITTER_COOKIES_FILE):
            try:
                with open(TWITTER_COOKIES_FILE, 'r') as f:
                    cookies = json.load(f)
                client.set_cookies(cookies)
                logger.info("Loaded Twitter cookies from file")
                
                # Check if cookies are valid by getting user ID
                try:
                    user_id = await client.user_id()
                    if user_id:
                        _twitter_client = client
                        _last_auth_time = current_time
                        logger.info("Successfully authenticated with Twitter cookies")
                        return client
                except Exception:
                    logger.info("Cookies expired, logging in again")
            except Exception as e:
                logger.error(f"Error loading cookies: {e}")
        
        # If cookies don't exist or are invalid, log in
        try:
            if not TWITTER_USERNAME or not TWITTER_PASSWORD:
                raise ValueError("Twitter credentials not configured. Set TWITTER_USERNAME/EMAIL and TWITTER_PASSWORD env vars.")
                
            auth_info_1 = TWITTER_USERNAME
            auth_info_2 = TWITTER_EMAIL if TWITTER_EMAIL else None
            
            await client.login(
                auth_info_1=auth_info_1,
                auth_info_2=auth_info_2,
                password=TWITTER_PASSWORD
            )
            
            # Save cookies for future use
            cookies = client.get_cookies()
            with open(TWITTER_COOKIES_FILE, 'w') as f:
                json.dump(cookies, f)
            
            _twitter_client = client
            _last_auth_time = current_time
            logger.info("Logged in to Twitter successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to authenticate with Twitter: {e}")
            raise

async def _execute_twitter_action(action_func):
    """Standardized method to execute Twitter API actions with proper error handling"""
    try:
        client = await _get_twitter_client()
        result = await action_func(client)
        return result
    except Exception as e:
        logger.error(f"Twitter API error: {e}")
        return {"error": str(e)}

# === CORE TWITTER TOOLS ===
@tool
def search_tweets(query: str, count: int = 10, product: str = "Latest") -> List[Dict[str, Any]]:
    """🔍 Search for tweets containing a specific token or hashtag.
    
    Args:
        query: The search query (e.g., "$WIF" or "Solana Degen")
        count: Maximum number of tweets to return (default: 10)
        product: Type of tweets to retrieve ("Top", "Latest", or "Media", default: "Latest")
    
    Returns:
        A list of tweets matching the search criteria with engagement metrics
    """
    # This function orchestrates the asynchronous search
    return asyncio.run(_search_tweets_async(query, count, product))

async def _search_tweets_async(query: str, count: int = 10, product: str = "Latest") -> List[Dict[str, Any]]:
    """Asynchronous implementation of tweet search"""
    # Handle string-based LangChain input (legacy format)
    if isinstance(query, str) and " " in query and not isinstance(count, int):
        parts = query.split()
        
        # Handle quoted query
        quoted_parts = re.findall(r'"([^"]*)"', query)
        if quoted_parts:
            query = quoted_parts[0]
            remaining_parts = [p for p in parts if p not in [f'"{query}"', f"'{query}'"]]
            
            # Check if remaining parts contain count and product
            if len(remaining_parts) >= 2 and remaining_parts[-1] in ["Top", "Latest", "Media"] and remaining_parts[-2].isdigit():
                count = int(remaining_parts[-2])
                product = remaining_parts[-1]
            elif len(remaining_parts) >= 1:
                if remaining_parts[-1].isdigit():
                    count = int(remaining_parts[-1])
                elif remaining_parts[-1] in ["Top", "Latest", "Media"]:
                    product = remaining_parts[-1]
        else:
            # Parse format like "$WIF 10 Top"
            if len(parts) >= 3 and parts[-1] in ["Top", "Latest", "Media"] and parts[-2].isdigit():
                query = " ".join(parts[:-2])
                count = int(parts[-2])
                product = parts[-1]
            elif len(parts) >= 2:
                if parts[-1].isdigit():
                    query = " ".join(parts[:-1])
                    count = int(parts[-1])
                elif parts[-1] in ["Top", "Latest", "Media"]:
                    query = " ".join(parts[:-1])
                    product = parts[-1]
    
    # Validate parameters
    count = min(max(1, count), 20)  # Between 1 and 20
    
    if product not in ["Top", "Latest", "Media"]:
        product = "Latest"
    
    logger.info(f"Searching tweets with query: '{query}', count: {count}, product: {product}")
    
    cache_key = f"search_tweets_{query}_{count}_{product}"
    cached_data = _cache_get(cache_key)
    if cached_data:
        return cached_data
    
    async def _search(client):
        try:
            results = await client.search_tweet(query, product, count=count)
            
            # Format tweets for analysis
            formatted_tweets = []
            for tweet in results:
                formatted_tweet = {
                    "id": tweet.id,
                    "text": tweet.text,
                    "created_at": tweet.created_at,
                    "likes": tweet.favorite_count,
                    "retweets": tweet.retweet_count,
                    "user": {
                        "id": tweet.user.id,
                        "name": tweet.user.name,
                        "screen_name": tweet.user.screen_name,
                        "verified": tweet.user.is_blue_verified or tweet.user.verified,
                        "followers_count": tweet.user.followers_count
                    },
                    "url": f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
                }
                
                # Add hashtags if available
                if hasattr(tweet, "hashtags") and tweet.hashtags:
                    formatted_tweet["hashtags"] = tweet.hashtags
                    
                formatted_tweets.append(formatted_tweet)
            
            return formatted_tweets
        except Exception as e:
            logger.warning(f"Error in search function: {e}")
            return []
    
    try:
        # Direkt asynchron ausführen ohne asyncio.run()
        results = await _execute_twitter_action(_search)
        
        # Sicherstellen, dass wir immer eine Liste zurückgeben
        if isinstance(results, dict) and "error" in results:
            logger.warning(f"Error in search_tweets: {results['error']}")
            return []  # Leere Liste bei Fehler zurückgeben anstatt Fehlermeldung
        
        if not isinstance(results, list):
            logger.warning(f"Unexpected response format in search_tweets: {type(results)}")
            return []
            
        # Cache results
        _cache_set(cache_key, results)
        
        return results
    except Exception as e:
        logger.error(f"Error searching tweets: {e}")
        return []  # Leere Liste zurückgeben anstatt Fehlermeldung

@tool
def analyze_token_sentiment(token_symbol: str, min_likes: int = 3, verified_only: bool = False) -> Dict[str, Any]:
    """🧠 Analyze Twitter sentiment for a specific token with improved filtering.
    
    Args:
        token_symbol: The token symbol to analyze (e.g., "WIF", "BONK", "SOL")
        min_likes: Minimum number of likes for a tweet to be considered (default: 3)
        verified_only: Whether to only include tweets from verified accounts (default: False)
    
    Returns:
        A detailed sentiment analysis with engagement metrics and notable tweets
    """
    return asyncio.run(_analyze_token_sentiment_async(token_symbol, min_likes, verified_only))

async def _analyze_token_sentiment_async(token_symbol: str, min_likes: int = 3, verified_only: bool = False) -> Dict[str, Any]:
    """Asynchronous implementation of token sentiment analysis"""
    if not token_symbol:
        return {"error": "No token symbol provided"}
    
    # Clean the input - remove '$' if present
    clean_symbol = token_symbol.strip().upper()
    if clean_symbol.startswith('$'):
        clean_symbol = clean_symbol[1:]
    
    cache_key = f"sentiment_{clean_symbol}_{min_likes}_{verified_only}"
    cached_data = _cache_get(cache_key)
    if cached_data:
        return cached_data
    
    try:
        # Search for tweets with the token mention
        search_query = f"${clean_symbol}"
        tweets_data = await _search_tweets_async(query=search_query, count=20, product="Top")
        
        # Wenn keine Tweets gefunden wurden, versuche es mit anderen Produkten
        if not tweets_data or len(tweets_data) == 0:
            logger.info(f"No tweets found for {search_query} with Top product, trying Latest")
            tweets_data = await _search_tweets_async(query=search_query, count=20, product="Latest")
            
            # Wenn immer noch keine Tweets gefunden wurden, versuche ohne $-Präfix
            if not tweets_data or len(tweets_data) == 0:
                logger.info(f"No tweets found for {search_query}, trying without $ symbol")
                tweets_data = await _search_tweets_async(query=clean_symbol, count=20, product="Latest")
        
        if not tweets_data or len(tweets_data) == 0:
            return {
                "token": clean_symbol,
                "sentiment": "neutral",
                "score": 0.5,
                "engagement": {
                    "tweet_count": 0,
                    "likes": 0,
                    "retweets": 0
                },
                "summary": f"No recent tweets found for ${clean_symbol}",
                "top_tweets": []
            }
        
        # Filter tweets based on criteria
        filtered_tweets = []
        total_likes = 0
        total_retweets = 0
        
        for tweet in tweets_data:
            # Skip if minimum likes requirement not met
            if tweet.get("likes", 0) < min_likes:
                continue
                
            # Skip if verified_only is True and tweet is not from a verified user
            if verified_only and not tweet.get("user", {}).get("verified", False):
                continue
                
            # Add to filtered list
            filtered_tweets.append(tweet)
            total_likes += tweet.get("likes", 0)
            total_retweets += tweet.get("retweets", 0)
        
        # If no tweets remain after filtering
        if not filtered_tweets:
            return {
                "token": clean_symbol,
                "sentiment": "neutral",
                "score": 0.5,
                "engagement": {
                    "tweet_count": 0,
                    "likes": 0,
                    "retweets": 0
                },
                "summary": f"No tweets meeting criteria found for ${clean_symbol} (min_likes={min_likes}, verified_only={verified_only})",
                "top_tweets": []
            }
        
        # Analyze sentiment in filtered tweets
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        
        for tweet in filtered_tweets:
            text = tweet.get("text", "").lower()
            
            # Check for bullish keywords
            if any(keyword.lower() in text for keyword in BULLISH_KEYWORDS):
                bullish_count += 1
                tweet["sentiment"] = "bullish"
                continue
                
            # Check for bearish keywords
            if any(keyword.lower() in text for keyword in BEARISH_KEYWORDS):
                bearish_count += 1
                tweet["sentiment"] = "bearish"
                continue
                
            # If no clear sentiment, mark as neutral
            neutral_count += 1
            tweet["sentiment"] = "neutral"
        
        # Calculate overall sentiment
        total_count = bullish_count + bearish_count + neutral_count
        
        if total_count == 0:
            sentiment = "neutral"
            score = 0.5
        else:
            # Calculate weighted score (0-1 scale)
            # 0 = very bearish, 0.5 = neutral, 1 = very bullish
            weighted_score = (bullish_count * 1.0 + neutral_count * 0.5 + bearish_count * 0.0) / total_count
            
            # Determine sentiment label from score
            if weighted_score >= 0.8:
                sentiment = "very bullish"
            elif weighted_score >= 0.6:
                sentiment = "bullish"
            elif weighted_score >= 0.4:
                sentiment = "neutral"
            elif weighted_score >= 0.2:
                sentiment = "bearish"
            else:
                sentiment = "very bearish"
                
            score = weighted_score
        
        # Sort tweets by engagement for top tweets
        top_tweets = sorted(
            filtered_tweets, 
            key=lambda x: x.get("likes", 0) + x.get("retweets", 0), 
            reverse=True
        )[:5]  # Limit to top 5
        
        # Create summarized tweet data for output
        summarized_tweets = []
        for tweet in top_tweets:
            summarized_tweets.append({
                "text": tweet.get("text", ""),
                "user": tweet.get("user", {}).get("screen_name", "unknown"),
                "likes": tweet.get("likes", 0),
                "retweets": tweet.get("retweets", 0),
                "sentiment": tweet.get("sentiment", "neutral"),
                "url": tweet.get("url", "")
            })
        
        # Create engagement summary
        engagement_summary = {
            "tweet_count": len(filtered_tweets),
            "likes": total_likes,
            "retweets": total_retweets
        }
        
        # Generate a summary text
        summary = f"${clean_symbol} shows {sentiment} sentiment with {total_likes} likes across {len(filtered_tweets)} relevant tweets. "
        
        if bullish_count > 0:
            summary += f"{bullish_count} tweets express bullish sentiment. "
        if bearish_count > 0:
            summary += f"{bearish_count} tweets express bearish sentiment. "
        
        result = {
            "token": clean_symbol,
            "sentiment": sentiment,
            "score": score,
            "engagement": engagement_summary,
            "sentiment_breakdown": {
                "bullish": bullish_count,
                "neutral": neutral_count,
                "bearish": bearish_count
            },
            "summary": summary,
            "top_tweets": summarized_tweets
        }
        
        # Cache results
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        logger.error(f"Error analyzing token sentiment: {e}")
        return {
            "token": clean_symbol,
            "sentiment": "neutral",
            "score": 0.5,
            "engagement": {
                "tweet_count": 0,
                "likes": 0,
                "retweets": 0
            },
            "summary": f"Error analyzing sentiment for ${clean_symbol}: {str(e)}",
            "top_tweets": []
        }

@tool
def check_influencer_posts() -> Dict[str, Any]:
    """🔍 Check what top memecoin influencers are posting on Twitter right now.
    
    Returns:
        A summary of the most relevant tweets from key memecoin influencers
    """
    return asyncio.run(_check_influencer_posts_async())

async def _check_influencer_posts_async() -> Dict[str, Any]:
    """Asynchronous implementation of influencer posts checking"""
    cache_key = "influencer_posts"
    cached_data = _cache_get(cache_key)
    if cached_data:
        return cached_data
    
    try:
        # Verwenden Sie ein einziges get_twitter_client für alle API-Calls
        client = await _get_twitter_client()
        all_data = []
        
        for handle in INFLUENCER_HANDLES:
            try:
                # Get user by handle first
                user = await client.get_user_by_screen_name(handle.replace("@", ""))
                if not user:
                    logger.warning(f"User {handle} not found")
                    continue
                    
                # Get user timeline
                tweets = await client.get_user_tweets(user.id, count=5, tweet_type="Tweets")
                
                # Filter tweets - max 48h old
                now = time.time()
                processed_tweets = []
                
                for tweet in tweets:
                    # Skip if tweet has no text
                    if not hasattr(tweet, 'text') or not tweet.text:
                        continue
                    
                    # Weniger strenge Zeitfilterung - 48h statt 24h
                    if hasattr(tweet, 'created_at'):
                        # Skip if older than 48h
                        tweet_time = tweet.created_at
                        if isinstance(tweet_time, str):
                            try:
                                # Parse different time formats
                                if 'T' in tweet_time:
                                    tweet_time = datetime.fromisoformat(tweet_time.replace('Z', '+00:00'))
                                else:
                                    tweet_time = datetime.strptime(tweet_time, '%a %b %d %H:%M:%S %z %Y')
                                
                                tweet_timestamp = tweet_time.timestamp()
                                age_hours = (now - tweet_timestamp) / 3600
                                
                                if age_hours > 48:  # 48h statt 24h
                                    continue
                            except Exception as e:
                                logger.warning(f"Error parsing tweet time: {e}")
                    
                    # Berücksichtige auch kurze Tweets
                    processed_tweet = {
                        "id": tweet.id,
                        "text": tweet.text,
                        "created_at": getattr(tweet, 'created_at', None),
                        "likes": getattr(tweet, 'favorite_count', 0),
                        "retweets": getattr(tweet, 'retweet_count', 0),
                        "url": f"https://twitter.com/{handle.replace('@', '')}/status/{tweet.id}"
                    }
                    
                    # Extract coin mentions using regex for $SYMBOL pattern
                    coin_mentions = re.findall(r'\$([A-Za-z0-9_]+)', tweet.text)
                    if coin_mentions:
                        # Filtere ungültige Token-Namen (nur numerisch oder zu kurz)
                        valid_tokens = [token for token in coin_mentions if not token.isdigit() and len(token) > 1]
                        if valid_tokens:
                            processed_tweet["coin_mentions"] = valid_tokens
                    
                    # Check for alpha signals
                    alpha_signals = []
                    for keyword in ALPHA_KEYWORDS:
                        if keyword.lower() in tweet.text.lower():
                            alpha_signals.append(keyword)
                    if alpha_signals:
                        processed_tweet["alpha_signals"] = alpha_signals
                        
                    # Determine sentiment based on keyword presence
                    bullish_count = 0
                    bearish_count = 0
                    
                    for keyword in BULLISH_KEYWORDS:
                        if keyword.lower() in tweet.text.lower():
                            bullish_count += 1
                            
                    for keyword in BEARISH_KEYWORDS:
                        if keyword.lower() in tweet.text.lower():
                            bearish_count += 1
                    
                    if bullish_count > 0 or bearish_count > 0:
                        sentiment = "bullish" if bullish_count > bearish_count else "bearish" if bearish_count > bullish_count else "neutral"
                        processed_tweet["sentiment"] = sentiment
                    
                    processed_tweets.append(processed_tweet)
                
                all_data.append({
                    "handle": handle,
                    "tweets": processed_tweets
                })
                
            except Exception as e:
                logger.error(f"Error getting tweets for {handle}: {e}")
                continue
                
        # Process results into a readable summary
        summary = {"influencers_checked": len(INFLUENCER_HANDLES), "relevant_updates": []}
        
        # Track mentioned tokens for the summary
        all_mentioned_tokens = {}
        alpha_signals_found = []
        bullish_tokens = {}
        bearish_tokens = {}
        
        # Count how many influencers had data
        processed_count = 0
        
        for influencer in all_data:
            handle = influencer.get("handle", "Unknown")
            tweets = influencer.get("tweets", [])
            
            # Skip if no tweets found
            if not tweets:
                continue
                
            processed_count += 1
                
            # Find the most relevant tweet from this influencer
            most_relevant = None
            highest_score = -1
            
            for tweet in tweets:
                relevance_score = 0
                
                # Tweets with alpha signals are most important
                if "alpha_signals" in tweet:
                    relevance_score += 20 * len(tweet.get("alpha_signals", []))
                    
                # Tweets mentioning coins are important
                if "coin_mentions" in tweet:
                    relevance_score += 10 * len(tweet.get("coin_mentions", []))
                    
                # Engagement adds relevance
                relevance_score += tweet.get("likes", 0) * 0.1
                relevance_score += tweet.get("retweets", 0) * 0.2
                
                # Sentiment matters
                if "sentiment" in tweet:
                    relevance_score += 5
                
                if relevance_score > highest_score:
                    highest_score = relevance_score
                    most_relevant = tweet
            
            # Skip if no relevant tweet found
            if not most_relevant:
                continue
            
            # Add this tweet to the summary
            entry = {
                "influencer": handle,
                "tweet": most_relevant.get("text", ""),
                "url": most_relevant.get("url", ""),
                "engagement": {
                    "likes": most_relevant.get("likes", 0),
                    "retweets": most_relevant.get("retweets", 0)
                }
            }
            
            # Add tokens mentioned
            if "coin_mentions" in most_relevant:
                entry["tokens"] = most_relevant["coin_mentions"]
                
                # Track globally mentioned tokens
                for token in most_relevant["coin_mentions"]:
                    all_mentioned_tokens[token] = all_mentioned_tokens.get(token, 0) + 1
                    
                    # Track sentiment for tokens
                    if most_relevant.get("sentiment") == "bullish":
                        bullish_tokens[token] = bullish_tokens.get(token, 0) + 1
                    elif most_relevant.get("sentiment") == "bearish":
                        bearish_tokens[token] = bearish_tokens.get(token, 0) + 1
            
            # Add sentiment if available
            if "sentiment" in most_relevant:
                entry["sentiment"] = most_relevant["sentiment"]
            
            # Add alpha signals if available
            if "alpha_signals" in most_relevant:
                entry["alpha_signals"] = most_relevant["alpha_signals"]
                alpha_signals_found.extend(most_relevant["alpha_signals"])
            
            summary["relevant_updates"].append(entry)
        
        # Add summary data
        summary["processed_count"] = processed_count
        
        # Sort tokens by mention count
        if all_mentioned_tokens:
            sorted_tokens = sorted(all_mentioned_tokens.items(), key=lambda x: x[1], reverse=True)
            summary["mentioned_tokens"] = [
                {"token": token, "mentions": count} for token, count in sorted_tokens
            ]
        
        # Generate insight based on data
        insights = []
        
        # Token insights
        if all_mentioned_tokens:
            most_mentioned = sorted(all_mentioned_tokens.items(), key=lambda x: x[1], reverse=True)[:3]
            insights.append(f"Most mentioned tokens: {', '.join(['$' + token for token, _ in most_mentioned])}")
        
        # Sentiment insights
        if bullish_tokens:
            most_bullish = sorted(bullish_tokens.items(), key=lambda x: x[1], reverse=True)[:2]
            if most_bullish:
                insights.append(f"Bullish sentiment for: {', '.join(['$' + token for token, _ in most_bullish])}")
                
        if bearish_tokens:
            most_bearish = sorted(bearish_tokens.items(), key=lambda x: x[1], reverse=True)[:2]
            if most_bearish:
                insights.append(f"Bearish sentiment for: {', '.join(['$' + token for token, _ in most_bearish])}")
        
        # Alpha signals
        if alpha_signals_found:
            # Count frequency of each signal
            signal_counts = {}
            for signal in alpha_signals_found:
                signal_counts[signal] = signal_counts.get(signal, 0) + 1
                
            # Get most common signals
            common_signals = sorted(signal_counts.items(), key=lambda x: x[1], reverse=True)[:2]
            if common_signals:
                insights.append(f"Common signals: {', '.join([signal for signal, _ in common_signals])}")
        
        # Keine relevanten Daten aber erfolgreich verbunden
        if len(summary["relevant_updates"]) == 0 and processed_count > 0:
            insights.append("No relevant crypto content from influencers in the last 48 hours.")
        
        summary["insights"] = insights
        
        # Cache results
        _cache_set(cache_key, summary)
        
        return summary
    except Exception as e:
        logger.error(f"Error in check_influencer_posts: {e}")
        return {
            "influencers_checked": len(INFLUENCER_HANDLES),
            "error": str(e),
            "relevant_updates": [],
            "insights": ["Could not retrieve influencer posts at this time."]
        }

@tool
def scan_twitter_for_alpha() -> Dict[str, Any]:
    """🚀 Scan Twitter for new memecoin launch signals and alpha from accounts with 1k+ followers.
    
    Returns:
        A list of recent memecoin launches and alpha signals from influential accounts
    """
    return asyncio.run(_scan_twitter_for_alpha_async())

async def _scan_twitter_for_alpha_async() -> Dict[str, Any]:
    """Asynchronous implementation of Twitter alpha scanning"""
    cache_key = "twitter_alpha_scan"
    cached_data = _cache_get(cache_key)
    if cached_data:
        return cached_data
    
    # Define search terms for different types of alpha signals
    LAUNCH_SEARCH_TERMS = [
        "just launched $", "launching $", "fair launch $", "stealth launch $", 
        "new memecoin $", "new token $", "low mcap $", "LP locked $", 
        "Birdeye listing $", "new solana", "memecoin solana", "solana token",
        "solana launch", "airdrop solana", "solana presale", "new coin solana"
    ]
    
    # Additional alpha keywords specifically for search
    ALPHA_SEARCH_TERMS = [
        "next 100x", "solana gem", "potential 100x", "hidden gem solana",
        "accumulating $", "ape now $", "don't miss $", "airdrop live",
        "presale $", "mint live $", "zero tax $", "new listing $",
        "early gem", "solana alpha", "ape opportunity", "bullish solana"
    ]
    
    MIN_FOLLOWERS = 1000  # Reduziert von 5000 auf 1000
    
    try:
        # Track all potential opportunities found
        all_opportunities = []
        
        # Search using launch terms first
        for search_term in LAUNCH_SEARCH_TERMS:
            try:
                tweets = await _search_tweets_async(search_term, count=10, product="Latest")
                
                # Skip if error or no results
                if not tweets or len(tweets) == 0:
                    continue
                
                # Process each tweet
                for tweet in tweets:
                    # Skip if user doesn't have enough followers
                    user_followers = tweet.get("user", {}).get("followers_count", 0)
                    if user_followers < MIN_FOLLOWERS:
                        continue
                    
                    # Extract token symbols mentioned (typically in $XXX format)
                    tweet_text = tweet.get("text", "")
                    token_mentions = re.findall(r'\$([A-Za-z0-9_]+)', tweet_text)
                    # Filtere ungültige Token-Namen (nur numerisch oder zu kurz)
                    token_mentions = [token for token in token_mentions if not token.isdigit() and len(token) > 1]
                    
                    # Skip if no token mentioned, AUSSER bei expliziten Launch-Signalen
                    has_launch_signal = any(launch.lower() in tweet_text.lower() for launch in ["launch", "launching", "just launched"])
                    if not token_mentions and not has_launch_signal:
                        continue
                    
                    # Bei fehlenden Token-Erwähnungen aber Launch-Signal, füge "UNKNOWN" hinzu
                    if not token_mentions and has_launch_signal:
                        matches = re.findall(r'(?:launched|launching|launch) ([A-Za-z0-9_]+)', tweet_text)
                        if matches:
                            token_mentions = [matches[0].upper()]
                        else:
                            token_mentions = ["UNKNOWN"]
                    
                    # Check for alpha signals in text
                    alpha_signals = []
                    for keyword in ALPHA_KEYWORDS:
                        if keyword.lower() in tweet_text.lower():
                            alpha_signals.append(keyword)
                    
                    # Calculate a relevance score
                    relevance_score = 0
                    
                    # Tokens mentioned add to relevance
                    relevance_score += len(token_mentions) * 10
                    
                    # Alpha signals add to relevance
                    relevance_score += len(alpha_signals) * 15
                    
                    # More followers = more relevant
                    relevance_score += min(user_followers / 1000, 100)  # Cap at 100 points
                    
                    # More engagement = more relevant
                    relevance_score += tweet.get("likes", 0) * 0.5
                    relevance_score += tweet.get("retweets", 0) * 1.5
                    
                    # Determine type of opportunity
                    opportunity_type = "launch" if any(term.lower() in tweet_text.lower() for term in ["launch", "launching", "just launched"]) else "alpha"
                    
                    # Create opportunity entry
                    opportunity = {
                        "type": opportunity_type,
                        "tokens": token_mentions,
                        "tweet_text": tweet_text,
                        "user": {
                            "name": tweet.get("user", {}).get("name", "Unknown"),
                            "screen_name": tweet.get("user", {}).get("screen_name", "Unknown"),
                            "followers": user_followers,
                            "verified": tweet.get("user", {}).get("verified", False)
                        },
                        "signals": alpha_signals,
                        "relevance_score": relevance_score,
                        "engagement": {
                            "likes": tweet.get("likes", 0),
                            "retweets": tweet.get("retweets", 0)
                        },
                        "url": tweet.get("url", ""),
                        "timestamp": tweet.get("created_at", None)
                    }
                    
                    # Check if this opportunity is already in our list (by URL)
                    if not any(o.get("url") == opportunity["url"] for o in all_opportunities):
                        all_opportunities.append(opportunity)
            except Exception as e:
                logger.error(f"Error processing search term '{search_term}': {e}")
                continue
                
            # Sleep briefly between searches to avoid rate limits
            await asyncio.sleep(0.5)  # Reduziert von 1s auf 0.5s
        
        # Also search using alpha terms
        for search_term in ALPHA_SEARCH_TERMS:
            try:
                tweets = await _search_tweets_async(search_term, count=5, product="Latest")
                
                # Skip if error or no results
                if not tweets or len(tweets) == 0:
                    continue
                
                # Process each tweet
                for tweet in tweets:
                    # Skip if user doesn't have enough followers
                    user_followers = tweet.get("user", {}).get("followers_count", 0)
                    if user_followers < MIN_FOLLOWERS:
                        continue
                    
                    # Extract token symbols mentioned 
                    tweet_text = tweet.get("text", "")
                    token_mentions = re.findall(r'\$([A-Za-z0-9_]+)', tweet_text)
                    # Filtere ungültige Token-Namen (nur numerisch oder zu kurz)
                    token_mentions = [token for token in token_mentions if not token.isdigit() and len(token) > 1]
                    
                    # Skip if no token mentioned and kein Alpha-Keyword
                    has_alpha_signal = any(alpha.lower() in tweet_text.lower() for alpha in ["100x", "gem", "alpha", "opportunity"])
                    if not token_mentions and not has_alpha_signal:
                        continue
                        
                    # Bei fehlenden Token-Erwähnungen aber Alpha-Signal, füge "UNKNOWN" hinzu
                    if not token_mentions and has_alpha_signal:
                        token_mentions = ["ALPHA_SIGNAL"]
                    
                    # Calculate a relevance score
                    relevance_score = 0
                    
                    # Tokens mentioned add to relevance
                    relevance_score += len(token_mentions) * 10
                    
                    # Check for alpha signals in text
                    alpha_signals = []
                    for keyword in ALPHA_KEYWORDS:
                        if keyword.lower() in tweet_text.lower():
                            alpha_signals.append(keyword)
                            relevance_score += 15  # Each alpha keyword adds points
                    
                    # More followers = more relevant
                    relevance_score += min(user_followers / 1000, 100)  # Cap at 100 points
                    
                    # More engagement = more relevant
                    relevance_score += tweet.get("likes", 0) * 0.5
                    relevance_score += tweet.get("retweets", 0) * 1.5
                    
                    # Create opportunity entry
                    opportunity = {
                        "type": "alpha",
                        "tokens": token_mentions,
                        "tweet_text": tweet_text,
                        "user": {
                            "name": tweet.get("user", {}).get("name", "Unknown"),
                            "screen_name": tweet.get("user", {}).get("screen_name", "Unknown"),
                            "followers": user_followers,
                            "verified": tweet.get("user", {}).get("verified", False)
                        },
                        "signals": alpha_signals,
                        "relevance_score": relevance_score,
                        "engagement": {
                            "likes": tweet.get("likes", 0),
                            "retweets": tweet.get("retweets", 0)
                        },
                        "url": tweet.get("url", ""),
                        "timestamp": tweet.get("created_at", None)
                    }
                    
                    # Check if this opportunity is already in our list (by URL)
                    if not any(o.get("url") == opportunity["url"] for o in all_opportunities):
                        all_opportunities.append(opportunity)
            except Exception as e:
                logger.error(f"Error processing alpha search term '{search_term}': {e}")
                continue
                
            # Sleep briefly between searches to avoid rate limits
            await asyncio.sleep(0.5)  # Reduziert von 1s auf 0.5s
        
        # If no opportunities found
        if not all_opportunities:
            result = {
                "status": "success",
                "opportunities_found": 0,
                "message": "No recent alpha or launch signals found from accounts with 1000+ followers",
                "opportunities": []
            }
            # Cache and return results
            _cache_set(cache_key, result)
            return result
        
        # Sort opportunities by relevance score
        sorted_opportunities = sorted(all_opportunities, key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        # Group by token to see which ones appear most
        token_counts = {}
        for opp in all_opportunities:
            for token in opp.get("tokens", []):
                if token not in ["UNKNOWN", "ALPHA_SIGNAL"]:  # Ignoriere Platzhalter
                    token_counts[token] = token_counts.get(token, 0) + 1
        
        # Get trending tokens (mentioned in multiple tweets)
        trending_tokens = []
        if token_counts:
            trending_tokens = sorted(token_counts.items(), key=lambda x: x[1], reverse=True)
            trending_tokens = [{"token": token, "mentions": count} for token, count in trending_tokens]
        
        # Generate insights
        insights = []
        
        # Most mentioned tokens
        if trending_tokens:
            tokens_str = ", ".join([f"${item['token']}" for item in trending_tokens[:3]])
            insights.append(f"Most mentioned tokens: {tokens_str}")
        
        # Launch signals
        launch_opps = [opp for opp in sorted_opportunities if opp.get("type") == "launch"]
        if launch_opps:
            # Filtere UNKNOWN aus den Launch-Meldungen heraus
            launch_tokens = []
            for opp in launch_opps[:3]:
                tokens = [t for t in opp.get("tokens", []) if t not in ["UNKNOWN", "ALPHA_SIGNAL"]]
                if tokens:
                    launch_tokens.extend(tokens)
            
            if launch_tokens:
                recent_launches = ", ".join([f"${token}" for token in launch_tokens[:3]])
                insights.append(f"Recent launches detected: {recent_launches}")
            else:
                insights.append("Recent launches detected, but token symbols not identified.")
        
        # Top influencers sharing alpha
        influencers = {}
        for opp in sorted_opportunities:
            screen_name = opp.get("user", {}).get("screen_name")
            if screen_name:
                followers = opp.get("user", {}).get("followers", 0)
                if screen_name not in influencers or followers > influencers[screen_name]:
                    influencers[screen_name] = followers
        
        if influencers:
            top_influencers = sorted(influencers.items(), key=lambda x: x[1], reverse=True)[:3]
            influencers_str = ", ".join([f"@{name}" for name, _ in top_influencers])
            insights.append(f"Top influencers sharing alpha: {influencers_str}")
        
        # Format final response
        result = {
            "status": "success",
            "opportunities_found": len(sorted_opportunities),
            "trending_tokens": trending_tokens,
            "insights": insights,
            "opportunities": sorted_opportunities[:10]  # Limit to top 10
        }
        
        # Cache results (use shorter TTL for this dynamic data)
        _cache_set(cache_key, result)
        return result
        
    except Exception as e:
        logger.error(f"Error in scan_twitter_for_alpha: {e}")
        return {
            "status": "partial_success",
            "message": f"Some results may be incomplete: {str(e)}",
            "opportunities_found": 0,
            "insights": ["Scanning for alpha signals hit an error."],
            "opportunities": []
        }

# Provide backwards compatibility with old function name
analyze_twitter_sentiment = analyze_token_sentiment 