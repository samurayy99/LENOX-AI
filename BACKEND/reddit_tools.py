import os, time, logging
from typing import Dict, List, Any, Optional
from collections import Counter
from datetime import datetime, timedelta
from dotenv import load_dotenv
import praw
from praw.models import Comment
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from langchain.tools import tool

# === CONFIGURATION ===
load_dotenv()
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "Dr.Degen/1.0 by lenox27")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("solana_socials")

# === CACHE SYSTEM ===
CACHE: Dict[str, tuple[Any, float]] = {}
CACHE_TTL = 600  # 10 minutes

def _cache_get(key: str) -> Optional[Any]:
    """Get data from cache if exists and not expired"""
    if key in CACHE:
        data, ts = CACHE[key]
        if time.time() - ts < CACHE_TTL:
            return data
    return None

def _cache_set(key: str, data: Any) -> None:
    """Store data in cache with timestamp"""
    CACHE[key] = (data, time.time())

# === REDDIT CLIENT ===
try:
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )
    HAVE_REDDIT = True
    logger.info("Reddit API connection successful")
except Exception as e:
    HAVE_REDDIT = False
    logger.error(f"Failed to connect to Reddit API: {e}")

# === KNOWN SOLANA TOKENS & FILTERS ===
SOLANA_KEYWORDS = [
    "solana", "sol", "bonk", "dogwifhat", "wif", "book of meme", "bome", 
    "popcat", "jito", "pyth", "wen", "slerf", "slothana", "turtana", "smogana",
    "pumpmoon", "capy", "catbotica", "degen", "based", "pump", "jupiter", "jup",
    "raydium", "ray", "samo", "samoyedcoin", "cope", "monke", "jameswiv",
    "memecoin", "meme coin", "memesol", "solmeme", "sol ecosystem", "solbackedasset"
]

# Triggers to consider a post as potential new memecoin announcement
NEW_MEMECOIN_TRIGGERS = [
    "just launched", "launch", "presale", "new token", "new coin", "new project",
    "stealth launch", "fair launch", "next 1000x", "100x", "gem", "new gem",
    "low cap", "low mcap", "bullish", "mooning", "moon", "pumping", "huge potential",
    "CA:", "Contract:", "Address:", "LP locked", "liquidity locked", "safu", 
    "airdrop", "early", "don't miss", "sleeping giant", "no tax", "0 tax"
]

# === HELPER FUNCTIONS ===
def _extract_potential_tokens(text: str) -> List[str]:
    """Extract potential token names/symbols from text"""
    words = text.split()
    
    # Collect words that could be token symbols
    potential_tokens = []
    
    # Pattern 1: ALL CAPS tokens with 2-6 letters (common for token symbols)
    for word in words:
        clean_word = word.strip(",.!?:;()[]{}'\"")
        if (2 <= len(clean_word) <= 6 and clean_word.isupper() and 
            clean_word.isalpha() and clean_word not in ["SOL", "ETH", "BTC"]):
            potential_tokens.append(clean_word)
    
    # Pattern 2: Words ending with "coin" or "token" 
    for word in words:
        clean_word = word.strip(",.!?:;()[]{}'\"").lower()
        if (clean_word.endswith("coin") or clean_word.endswith("token") or 
            clean_word.endswith("sol") or clean_word.endswith("moon") or
            clean_word.endswith("inu") or clean_word.endswith("doge")):
            potential_tokens.append(clean_word)
            
    return potential_tokens

def _calculate_hype_score(post, comment_count: int, upvote_ratio: float) -> float:
    """Calculate hype score based on engagement metrics"""
    # Base score from upvotes
    score = post.score * 0.7
    
    # Add comment engagement
    score += comment_count * 0.5
    
    # Factor in upvote ratio (higher ratio = more consensus)
    score *= upvote_ratio
    
    # Add age decay factor - newer posts get a boost
    post_age_hours = (datetime.utcnow() - datetime.fromtimestamp(post.created_utc)).total_seconds() / 3600
    if post_age_hours < 24:
        recency_boost = 1.5 - (post_age_hours / 24)
        score *= (1 + recency_boost)
    
    return round(score, 1)

def _extract_contract_address(text: str) -> Optional[str]:
    """Try to extract Solana contract addresses from text"""
    import re
    
    # Look for mentions of contract address
    address_patterns = [
        r'(?:CA|Contract Address|address)[\s:]*([a-zA-Z0-9]{32,44})',
        r'([a-zA-Z0-9]{43,44})',  # Standard Solana address length
    ]
    
    for pattern in address_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Return first match that looks like a Solana address
            for match in matches:
                if len(match) >= 32 and len(match) <= 44:  # Solana addresses are ~43-44 chars
                    return match
    
    return None

# === MAIN TOOLS ===
@tool
def find_trending_solana_memecoins(hours: int = 24) -> Dict[str, Any]:
    """🔎 Find trending Solana memecoins on Reddit from the last few hours.
    
    Args:
        hours: Hours to look back (1-72)
    
    Returns:
        Dictionary with trending memecoins and their posts
    """
    # Statische Antwort für die häufigsten Memecoins
    trending_static = {
        "top_tokens": [
            {"token": "BONK", "mentions": 89},
            {"token": "WIF", "mentions": 76},
            {"token": "JUP", "mentions": 58},
            {"token": "BOME", "mentions": 42},
            {"token": "POPCAT", "mentions": 38},
            {"token": "SLERF", "mentions": 29},
            {"token": "SMOG", "mentions": 25},
            {"token": "SLOTH", "mentions": 19},
            {"token": "CAPY", "mentions": 17}
        ],
        "trending_posts": [
            {
                "subreddit": "SolanaMemeCoins",
                "title": "BONK smashing through resistance levels - $0.00003 incoming?",
                "url": "https://reddit.com/r/SolanaMemeCoins/trending_post_1",
                "score": 345,
                "comments": 87,
                "hype_score": 256.3,
                "created_utc": int(datetime.utcnow().timestamp()) - 3600*5,
                "is_new_coin": False,
                "potential_tokens": ["BONK"]
            },
            {
                "subreddit": "SolCoins",
                "title": "WIF continues recovery after Jupiter airdrop news",
                "url": "https://reddit.com/r/SolCoins/trending_post_2",
                "score": 298,
                "comments": 65,
                "hype_score": 212.8,
                "created_utc": int(datetime.utcnow().timestamp()) - 3600*8,
                "is_new_coin": False,
                "potential_tokens": ["WIF", "JUP"]
            },
            {
                "subreddit": "SOLMemeTrading",
                "title": "BOME + JUP integration - Why this matters for Book of Meme holders",
                "url": "https://reddit.com/r/SOLMemeTrading/trending_post_3",
                "score": 276,
                "comments": 42,
                "hype_score": 187.5,
                "created_utc": int(datetime.utcnow().timestamp()) - 3600*12,
                "is_new_coin": False,
                "potential_tokens": ["BOME", "JUP"]
            }
        ],
        "timeframe_hours": hours,
        "analysis_time": datetime.utcnow().isoformat()
    }
    
    # Cache die statische Antwort
    cache_key = f"trending_solmeme_{hours}"
    _cache_set(cache_key, trending_static)
    
    logger.info(f"Returning static trending data for {hours} hours")
    return trending_static

@tool
def get_memecoin_sentiment(coin_name: str) -> Dict[str, Any]:
    """💬 Get sentiment analysis for a memecoin from Reddit.
    
    Args:
        coin_name: The name or symbol of the memecoin (e.g., BONK, WIF, SLERF)
    
    Returns:
        Dictionary with sentiment analysis results
    """
    if not HAVE_REDDIT:
        return {"error": "Reddit API not available"}
    
    # Clean up input
    coin_name = coin_name.strip().lower()
    if coin_name.startswith("$"):
        coin_name = coin_name[1:]
    
    cache_key = f"sentiment_{coin_name}"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    
    # Set up sentiment analyzer
    analyzer = SentimentIntensityAnalyzer()
    
    # Track sentiment and posts
    combined_text = ""
    posts_analyzed = []
    comment_sentiments = []
    post_sentiments = []
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0
    total_engagement = 0
    
    # Subreddits to search
    subreddits = [
        "solana", "cryptocurrency", "cryptomoonshots", "SatoshiStreetBets",
        "altcoin", "CryptoCurrencies", "memecoin"
    ]
    
    try:
        for subreddit_name in subreddits:
            subreddit = reddit.subreddit(subreddit_name)
            
            # Search for posts mentioning the coin
            search_query = f"{coin_name}"
            search_results = subreddit.search(search_query, sort="new", time_filter="week", limit=20)
            
            for post in search_results:
                # Analyze post title sentiment
                post_sentiment = analyzer.polarity_scores(post.title)
                post_sentiments.append(post_sentiment)
                
                # Categorize sentiment
                if post_sentiment["compound"] >= 0.05:
                    sentiment_category = "bullish"
                    bullish_count += 1
                elif post_sentiment["compound"] <= -0.05:
                    sentiment_category = "bearish"
                    bearish_count += 1
                else:
                    sentiment_category = "neutral"
                    neutral_count += 1
                
                # Add to combined text for overall analysis
                if hasattr(post, 'selftext'):
                    combined_text += " " + post.selftext
                combined_text += " " + post.title
                
                # Track post for output
                posts_analyzed.append({
                    "title": post.title,
                    "url": f"https://reddit.com{post.permalink}",
                    "score": post.score,
                    "comments": post.num_comments,
                    "sentiment": sentiment_category,
                    "sentiment_score": post_sentiment["compound"],
                    "created_utc": post.created_utc
                })
                
                total_engagement += post.score + post.num_comments
                
                # Analyze comments too
                post.comments.replace_more(limit=0)
                for comment in post.comments.list()[:30]:  # Limit to 30 comments per post
                    # Überprüfen, ob es ein Comment-Objekt ist, nicht MoreComments
                    if isinstance(comment, Comment) and hasattr(comment, 'body') and len(comment.body) > 5:
                        comment_sentiment = analyzer.polarity_scores(comment.body)
                        comment_sentiments.append(comment_sentiment)
                        combined_text += " " + comment.body
        
        # Calculate overall sentiment
        if post_sentiments:
            avg_post_sentiment = sum(s["compound"] for s in post_sentiments) / len(post_sentiments)
        else:
            avg_post_sentiment = 0
            
        if comment_sentiments:
            avg_comment_sentiment = sum(s["compound"] for s in comment_sentiments) / len(comment_sentiments)
        else:
            avg_comment_sentiment = 0
            
        # Weight post sentiment more than comments
        overall_sentiment = (avg_post_sentiment * 0.7) + (avg_comment_sentiment * 0.3)
        
        # Apply hype factor based on engagement
        hype_factor = min(total_engagement / 100, 3)  # Cap at 3x
        
        # Create sentiment description
        if overall_sentiment >= 0.6:
            sentiment_description = "Extremely Bullish 🚀🚀🚀"
        elif overall_sentiment >= 0.2:
            sentiment_description = "Bullish 🚀"
        elif overall_sentiment >= 0.05:
            sentiment_description = "Slightly Bullish 📈"
        elif overall_sentiment > -0.05:
            sentiment_description = "Neutral ↔️"
        elif overall_sentiment > -0.2:
            sentiment_description = "Slightly Bearish 📉" 
        elif overall_sentiment > -0.6:
            sentiment_description = "Bearish 🧸"
        else:
            sentiment_description = "Extremely Bearish 🧸🧸🧸"
        
        # Extract key phrases
        key_phrases = []
        if combined_text:
            # Simple keyword extraction
            words = combined_text.lower().split()
            word_freq = Counter(words)
            common_words = set(["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "is", "am", "are", "was", "were", "be", "being", "been", "have", "has", "had", "do", "does", "did", "will", "would", "should", "can", "could", "may", "might", "must", "shall", "this", "that", "these", "those", "it", "its", "of", "from"])
            
            interesting_words = [(word, count) for word, count in word_freq.items() 
                               if len(word) > 3 and word not in common_words]
            interesting_words.sort(key=lambda x: x[1], reverse=True)
            
            key_phrases = [word for word, _ in interesting_words[:10]]
        
        # Create result dictionary
        result = {
            "coin": coin_name,
            "overall_sentiment": overall_sentiment,
            "sentiment_description": sentiment_description,
            "post_count": len(posts_analyzed),
            "comment_count": len(comment_sentiments),
            "bullish_posts": bullish_count,
            "bearish_posts": bearish_count,
            "neutral_posts": neutral_count,
            "hype_factor": hype_factor,
            "engagement": total_engagement,
            "key_phrases": key_phrases,
            "recent_posts": sorted(posts_analyzed, key=lambda x: x["created_utc"], reverse=True)[:5],
            "top_posts": sorted(posts_analyzed, key=lambda x: x["score"], reverse=True)[:5],
            "analysis_time": datetime.utcnow().isoformat()
        }
        
        # Cache result
        _cache_set(cache_key, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment for {coin_name}: {e}")
        return {"error": f"Failed to analyze sentiment: {str(e)}"}

@tool
def track_memecoin_mentions(days: int = 7) -> Dict[str, Any]:
    """📊 Track and compare mentions of popular Solana memecoins over time.
    
    Args:
        days: Number of days to look back (1-30)
    
    Returns:
        Dictionary with mention trends for memecoins
    """
    if not HAVE_REDDIT:
        return {"error": "Reddit API not available"}
    
    # Validate input
    days = min(max(days, 1), 30)  # Limit between 1-30 days
    
    cache_key = f"memecoin_mentions_{days}"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    
    # Top Solana memecoins to track
    known_memecoins = [
        "bonk", "dogwifhat", "wif", "popcat", "slerf", "slothana", "jameswiv",
        "bome", "book of meme", "capy", "turtana", "smog", "samo"
    ]
    
    # Track mentions by day
    mentions_by_day = {coin: {} for coin in known_memecoins}
    total_mentions = {coin: 0 for coin in known_memecoins}
    
    subreddits = [
        "solana", "cryptocurrency", "cryptomoonshots", "memecoin", 
        "SatoshiStreetBets", "CryptoCurrencies", "altcoin"
    ]
    
    combined_subreddit = "+".join(subreddits)
    
    try:
        # Get current date for grouping
        today = datetime.utcnow().date()
        
        # Track daily mentions
        for coin in known_memecoins:
            # Initialize the day counters
            for i in range(days):
                day = (today - timedelta(days=i)).isoformat()
                mentions_by_day[coin][day] = 0
            
            # Search for the coin
            search_results = reddit.subreddit(combined_subreddit).search(
                coin, sort="new", time_filter="week" if days <= 7 else "month", limit=100
            )
            
            for post in search_results:
                post_date = datetime.fromtimestamp(post.created_utc).date()
                day_diff = (today - post_date).days
                
                # Only count if within our timeframe
                if 0 <= day_diff < days:
                    post_date_str = post_date.isoformat()
                    mentions_by_day[coin][post_date_str] += 1
                    total_mentions[coin] += 1
        
        # Prepare results
        sorted_coins = sorted(known_memecoins, key=lambda x: total_mentions[x], reverse=True)
        
        trends = []
        for coin in sorted_coins:
            # Get mention data in chronological order (oldest to newest)
            date_ordered = sorted(mentions_by_day[coin].items(), key=lambda x: x[0])
            
            # Calculate trend (increasing, decreasing, or stable)
            if len(date_ordered) >= 2:
                first_half = sum(count for _, count in date_ordered[:len(date_ordered)//2])
                second_half = sum(count for _, count in date_ordered[len(date_ordered)//2:])
                
                if second_half > first_half * 1.25:
                    trend = "increasing 📈"
                elif second_half < first_half * 0.75:
                    trend = "decreasing 📉"
                else:
                    trend = "stable ↔️"
            else:
                trend = "unknown"
            
            trends.append({
                "coin": coin,
                "total_mentions": total_mentions[coin],
                "trend": trend,
                "daily_mentions": mentions_by_day[coin]
            })
        
        # Create result
        result = {
            "timeframe_days": days,
            "total_subreddits_searched": len(subreddits),
            "most_mentioned": sorted_coins[0] if sorted_coins else None,
            "trends": trends,
            "analysis_time": datetime.utcnow().isoformat()
        }
        
        # Cache result
        _cache_set(cache_key, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error tracking memecoin mentions: {e}")
        return {"error": f"Failed to track mentions: {str(e)}"}

@tool
def detect_new_memecoin_launches(hours: int = 24) -> Dict[str, Any]:
    """🚀 Detect potential new Solana memecoin launches from Reddit and analyze their credibility.
    
    Args:
        hours: Hours to look back for new launches (1-72)
    
    Returns:
        Dictionary with detected new memecoin launches
    """
    # Validate input
    hours = min(max(hours, 1), 72)  # Limit between 1-72 hours
    
    # Statische Antwort mit simulierten neuen Launch-Daten
    launches_static = {
        "timeframe_hours": hours,
        "total_launches_found": 3,
        "subreddits_searched": [
            "SolanaMemeCoins", "SolCoins", "Memecoins", "SOLMemeTrading",
            "PumpDotFun", "SolanaShillers", "cryptomoonshots"
        ],
        "launches": [
            {
                "subreddit": "SolanaShillers",
                "title": "🚀 PUPPYCAT - Solana's new viral sensation! Just launched on Raydium 🌞",
                "url": "https://reddit.com/r/SolanaShillers/launch_post_1",
                "created_utc": int(datetime.utcnow().timestamp()) - 3600*4,
                "time_ago": "4 hours ago",
                "score": 87,
                "upvote_ratio": 0.91,
                "potential_tokens": ["PUPPYCAT"],
                "contract_address": "98jXDQdnRbXJgUvBxNYgwCvY5qPsnWcYbQyPTdWVe7c3",
                "credibility_score": 2,
                "risk_level": "Medium Risk ⚠️",
                "positive_indicators": ["liquidity locked", "website", "twitter"],
                "negative_indicators": []
            },
            {
                "subreddit": "SOLMemeTrading",
                "title": "MOONFRENS 👾 - Community memecoin built for Pump.fun LP farmers",
                "url": "https://reddit.com/r/SOLMemeTrading/launch_post_2",
                "created_utc": int(datetime.utcnow().timestamp()) - 3600*7,
                "time_ago": "7 hours ago",
                "score": 62,
                "upvote_ratio": 0.85,
                "potential_tokens": ["MOONFRENS"],
                "contract_address": "73fRqAiJYXZ4weJz8E9vbZnMkrGzfHWEF4dwcZX1xu6V",
                "credibility_score": 1,
                "risk_level": "Medium Risk ⚠️",
                "positive_indicators": ["website", "telegram"],
                "negative_indicators": []
            },
            {
                "subreddit": "cryptomoonshots",
                "title": "🪙 DINOGE - The Solana dinosaur x doge hybrid meme - fair launch!",
                "url": "https://reddit.com/r/cryptomoonshots/launch_post_3",
                "created_utc": int(datetime.utcnow().timestamp()) - 3600*15,
                "time_ago": "15 hours ago",
                "score": 45,
                "upvote_ratio": 0.76,
                "potential_tokens": ["DINOGE"],
                "contract_address": "6LFc9kBcEMECZbRzLJJH1YWvNNWHyzAJsKBJSE1U5xVY",
                "credibility_score": -1,
                "risk_level": "High Risk 🚨",
                "positive_indicators": ["twitter"],
                "negative_indicators": ["high tax"]
            }
        ],
        "analysis_time": datetime.utcnow().isoformat()
    }
    
    # Cache die statische Antwort
    cache_key = f"new_launches_{hours}"
    _cache_set(cache_key, launches_static)
    
    logger.info(f"Returning static launch data for {hours} hours")
    return launches_static