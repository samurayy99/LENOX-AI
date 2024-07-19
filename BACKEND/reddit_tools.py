import os
from collections import Counter
from typing import List
import string
import praw
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from praw.models import MoreComments
import spacy
from dotenv import load_dotenv
from nltk import download as nltk_download

from langchain.agents import tool  # Use the @tool decorator

# Load environment variables
load_dotenv()

# Download necessary NLTK data
nltk_download('punkt')
nltk_download('stopwords')

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# Initialize Reddit API with credentials from environment variables
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

# Known cryptocurrencies
known_cryptos = {"bitcoin", "ethereum", "litecoin", "ripple", "dogecoin", "cardano", "polkadot", "binance", "solana", "chainlink"}

@tool
def get_reddit_data(subreddit: str, category: str = 'hot') -> str:
    """
    Fetches and returns the latest posts from a specified subreddit category using PRAW.
    """
    sub = reddit.subreddit(subreddit)
    posts = getattr(sub, category)(limit=10)  # Increase the limit to fetch more data
    posts_str = "\n\n".join([f"[Title: {post.title}](https://www.reddit.com{post.permalink})" for post in posts])
    return f"Latest posts from r/{subreddit}:\n{posts_str}"

@tool
def count_mentions(subreddit: str, keyword: str, time_filter='week') -> str:
    """
    Counts how often a keyword is mentioned in a subreddit within the specified time period.
    """
    mentions = sum(1 for _ in reddit.subreddit(subreddit).search(keyword, time_filter=time_filter))
    return f"'{keyword}' was mentioned {mentions} times in r/{subreddit} over the past {time_filter}."

@tool
def analyze_sentiment(subreddit: str, keyword: str, time_filter='week') -> str:
    """
    Conducts a sentiment analysis for posts and comments containing a specific keyword, providing both the average score and a qualitative interpretation.
    """
    sentiment_analyzer = SentimentIntensityAnalyzer()
    sentiment_scores = []

    for submission in reddit.subreddit(subreddit).search(keyword, time_filter=time_filter):
        # Using TextBlob
        analysis_tb = TextBlob(submission.title)
        sentiment_scores.append(analysis_tb.sentiment.polarity)
        
        # Using VADER
        analysis_vader = sentiment_analyzer.polarity_scores(submission.title)
        sentiment_scores.append(analysis_vader['compound'])
        
        for comment in submission.comments.list():
            if isinstance(comment, MoreComments):
                continue
            analysis_tb = TextBlob(comment.body)
            sentiment_scores.append(analysis_tb.sentiment.polarity)
            
            analysis_vader = sentiment_analyzer.polarity_scores(comment.body)
            sentiment_scores.append(analysis_vader['compound'])

    if sentiment_scores:
        average_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        sentiment_description = interpret_sentiment(average_sentiment)
    else:
        average_sentiment = 0
        sentiment_description = "No sentiment data available."

    return f"Average sentiment for '{keyword}' in r/{subreddit} over the past {time_filter}: {average_sentiment:.2f}. Interpretation: {sentiment_description}"

def interpret_sentiment(score: float) -> str:
    """
    Provides a qualitative interpretation of a sentiment score.
    """
    if score > 0.05:
        return "The sentiment is mostly positive. People are generally upbeat and optimistic about this topic."
    elif score < -0.05:
        return "The sentiment is mostly negative. There seems to be a lot of concern and dissatisfaction surrounding this topic."
    else:
        return "The sentiment is neutral. There are mixed feelings about this topic, with no strong lean towards positive or negative."


@tool
def find_trending_cryptos(subreddits: List[str], time_filter='day') -> str:
    """
    Identifies trending cryptocurrencies and new coins in the given subreddits within the specified time period.
    """
    topics = Counter()
    new_coins = set()
    stopwords_set = set(stopwords.words('english'))
    
    # Add common crypto terms to avoid them being flagged as new coins
    common_crypto_terms = {"crypto", "cryptocurrency", "blockchain", "token", "coin", "defi", "nft", "mining", "wallet", "exchange"}
    known_cryptos.update(common_crypto_terms)

    for subreddit in subreddits:
        for submission in reddit.subreddit(subreddit).hot(limit=500):
            doc = nlp(submission.title.lower())
            words = [token.lemma_ for token in doc if token.text.lower() not in stopwords_set and token.is_alpha and len(token.text) > 2]
            
            # Update topics counter
            topics.update(word for word in words if word in known_cryptos or word.endswith("coin"))
            
            # Identify potential new coins
            new_coins.update(word for word in words if word not in known_cryptos and (word.endswith("coin") or word.isupper()))
    
    most_common_topics = topics.most_common(10)
    topics_str = "\n".join([f"{topic[0]}: {topic[1]} mentions" for topic in most_common_topics])
    new_coins_str = ", ".join(sorted(str(coin) for coin in new_coins)[:20])  # Convert to str before sorting

    return f"Trending topics:\n{topics_str}\n\nPotential new coins being discussed: {new_coins_str}"


def clean_reddit_text(docs: List[str]) -> List[str]:
    """
    Cleans and prepares Reddit text for sentiment analysis.
    """
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    translator = str.maketrans('', '', string.punctuation)

    clean_docs = []
    for doc in docs:
        tokens = doc.split()
        clean_tokens = [lemmatizer.lemmatize(token) for token in tokens if token not in stop_words and token.isalpha()]
        clean_doc = ' '.join(clean_tokens).translate(translator)
        clean_docs.append(clean_doc)
    return clean_docs
