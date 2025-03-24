#!/usr/bin/env python3
"""
Dr. Degen Perplexity Research Test Script
-----------------------------------------
Tests the newly implemented PerplexityManager class with various scenarios:
1. Token research for Solana tokens
2. General crypto market research
3. Social media sentiment analysis

Uses the Perplexity API for real-time research and saves the results.
"""

import os
import json
import time
import argparse
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from perplexity_research import PerplexityManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_chat_response(content: str, metrics: Optional[Dict[str, Any]] = None, sources: Optional[List[str]] = None):
    """
    Print research results formatted as they would appear in a chat UI
    """
    print("\n" + "="*80)
    print("DR. DEGEN RESPONDS:")
    print("="*80)
    print(content)
    
    if sources:
        print("\n" + "-"*40)
        print("SOURCES:")
        for i, source in enumerate(sources, 1):
            print(f"{i}. {source}")
    
    if metrics:
        print("\n" + "-"*40)
        print("EXTRACTED METRICS:")
        for key, value in metrics.items():
            print(f"• {key}: {value}")
    
    print("="*80 + "\n")

def test_token_research(manager: PerplexityManager, token_symbol: str, quiet: bool = False) -> Dict[str, Any]:
    """Test token-specific research capabilities"""
    logger.info(f"🧪 Testing token research for ${token_symbol}...")
    
    query = f"What do you know about ${token_symbol} token? Is it a good investment right now?"
    
    # Simulate user input in terminal
    if not quiet:
        print(f"\nUser: {query}")
        print("⏳ Dr. Degen is researching... (this may take 20-30 seconds)")
    
    start_time = time.time()
    result = manager.run_gpt_research(query)
    duration = time.time() - start_time
    
    logger.info(f"✅ Research completed in {duration:.2f} seconds")
    
    # Log basic metrics about the result
    content_length = len(result.get("content", ""))
    logger.info(f"📊 Content length: {content_length} characters")
    logger.info(f"🔗 Sources found: {len(result.get('sources', []))}")
    
    # Check if metrics were extracted successfully
    metrics = result.get("metrics", {})
    if metrics:
        logger.info("📈 Token metrics successfully extracted:")
        important_metrics = ["blockchain", "price_usd", "market_cap", "liquidity", "degen_score", "recommendation"]
        for key in important_metrics:
            if key in metrics:
                logger.info(f"   - {key}: {metrics[key]}")
            else:
                logger.info(f"   - {key}: Not found")
    else:
        logger.warning("⚠️ No token metrics extracted")
    
    # Simulate chat UI response
    if not quiet:
        print_chat_response(
            result.get("content", ""), 
            metrics,
            result.get("sources", [])
        )
    
    return result

def test_degen_command(manager: PerplexityManager, token_identifier: str) -> Dict[str, Any]:
    """
    Test the /degen command specifically with a token symbol or contract address
    This simulates the exact usage of the new /degen command
    """
    # Normalize the token identifier - ensure it has a $ if it's a symbol and not a contract
    if not token_identifier.startswith("$") and not token_identifier.startswith("CA:") and len(token_identifier) < 20:
        token_identifier = f"${token_identifier}"
    
    command = f"/degen {token_identifier}"
    logger.info(f"🧪 Testing /degen command with: '{token_identifier}'")
    
    print(f"\nUser: {command}")
    print("⏳ Dr. Degen is researching... (this may take 30-45 seconds)")
    
    start_time = time.time()
    result = manager.degen_research(command)
    duration = time.time() - start_time
    
    logger.info(f"✅ Research completed in {duration:.2f} seconds")
    
    # Log basic metrics about the result
    content_length = len(result.get("content", ""))
    logger.info(f"📊 Content length: {content_length} characters")
    logger.info(f"🔗 Sources found: {len(result.get('sources', []))}")
    
    # Check if metrics were extracted successfully
    metrics = result.get("metrics", {})
    if metrics:
        logger.info("📈 Token metrics successfully extracted:")
        important_metrics = [
            "symbol", "blockchain", "contract", "price_usd", "market_cap", 
            "liquidity", "holders", "degen_score", "recommendation", 
            "key_risk", "key_strength", "top_wallets"
        ]
        for key in important_metrics:
            if key in metrics:
                logger.info(f"   - {key}: {metrics[key]}")
            else:
                logger.info(f"   - {key}: Not found")
    else:
        logger.warning("⚠️ No token metrics extracted")
    
    # Simulate chat UI response exactly as a user would see it
    print_chat_response(
        result.get("content", ""),
        metrics,
        result.get("sources", [])
    )
    
    # Save the result to a token-specific file
    token_name = token_identifier.replace("$", "").replace(":", "_")
    filename = f"degen_{token_name}_result.json"
    with open(filename, "w") as f:
        json.dump(result, f, indent=2)
    logger.info(f"✅ Result saved to {filename}")
    
    return result

def test_market_research(manager: PerplexityManager, quiet: bool = False) -> Dict[str, Any]:
    """Test general market research capabilities"""
    logger.info("🧪 Testing general market research...")
    
    query = "What are the most important crypto market trends for Q2 2024, especially for Solana ecosystem?"
    
    # Simulate user input in terminal
    if not quiet:
        print(f"\nUser: {query}")
        print("⏳ Dr. Degen is researching... (this may take 20-30 seconds)")
    
    start_time = time.time()
    result = manager.run_gpt_research(query)
    duration = time.time() - start_time
    
    logger.info(f"✅ Research completed in {duration:.2f} seconds")
    
    # Log basic metrics about the result
    content_length = len(result.get("content", ""))
    logger.info(f"📊 Content length: {content_length} characters")
    logger.info(f"🔗 Sources found: {len(result.get('sources', []))}")
    
    # Preview content
    preview_length = min(250, content_length)
    content_preview = result.get("content", "")[:preview_length] + "..." if content_length > preview_length else result.get("content", "")
    logger.info(f"📝 Content preview:\n{content_preview}")
    
    # Simulate chat UI response
    if not quiet:
        print_chat_response(
            result.get("content", ""),
            sources=result.get("sources", [])
        )
    
    return result

def test_social_sentiment(manager: PerplexityManager, topic: str, quiet: bool = False) -> Dict[str, Any]:
    """Test social sentiment analysis capabilities"""
    logger.info(f"🧪 Testing social sentiment analysis for '{topic}'...")
    
    query = f"What's the current social sentiment on Twitter/X about {topic}? Are influencers bullish or bearish?"
    
    # Simulate user input in terminal
    if not quiet:
        print(f"\nUser: {query}")
        print("⏳ Dr. Degen is researching... (this may take 20-30 seconds)")
    
    start_time = time.time()
    result = manager.run_gpt_research(query)
    duration = time.time() - start_time
    
    logger.info(f"✅ Research completed in {duration:.2f} seconds")
    
    # Log basic metrics about the result
    content_length = len(result.get("content", ""))
    logger.info(f"📊 Content length: {content_length} characters")
    logger.info(f"🔗 Sources found: {len(result.get('sources', []))}")
    
    # Preview content
    preview_length = min(250, content_length)
    content_preview = result.get("content", "")[:preview_length] + "..." if content_length > preview_length else result.get("content", "")
    logger.info(f"📝 Content preview:\n{content_preview}")
    
    # Simulate chat UI response
    if not quiet:
        print_chat_response(
            result.get("content", ""),
            sources=result.get("sources", [])
        )
    
    return result

def test_custom_sources(manager: PerplexityManager, quiet: bool = False) -> Dict[str, Any]:
    """Test research using custom source URLs"""
    logger.info("🧪 Testing research with custom source URLs...")
    
    custom_sources = [
        "https://twitter.com/solana",
        "https://solana.com/news",
        "https://solanafm.com/",
        "https://solanabeach.io/"
    ]
    
    query = "What are the latest Solana ecosystem developments and performance metrics?"
    
    # Simulate user input in terminal
    if not quiet:
        print(f"\nUser: {query}")
        print(f"[Using custom sources]")
        print("⏳ Dr. Degen is researching... (this may take 20-30 seconds)")
    
    start_time = time.time()
    result = manager.run_gpt_research(query, source_urls=custom_sources)
    duration = time.time() - start_time
    
    logger.info(f"✅ Research completed in {duration:.2f} seconds")
    
    # Log basic metrics about the result
    content_length = len(result.get("content", ""))
    logger.info(f"📊 Content length: {content_length} characters")
    logger.info(f"🔗 Sources found: {len(result.get('sources', []))}")
    
    # Check if our custom sources were used
    sources = result.get("sources", [])
    custom_sources_used = [s for s in sources if any(cs in s for cs in custom_sources)]
    logger.info(f"🎯 Custom sources used: {len(custom_sources_used)}/{len(custom_sources)}")
    
    # Simulate chat UI response
    if not quiet:
        print_chat_response(
            result.get("content", ""),
            sources=result.get("sources", [])
        )
    
    return result

def test_custom_query(manager: PerplexityManager, query: str) -> Dict[str, Any]:
    """Test with a custom user query - simulates exact real-world usage"""
    logger.info(f"🧪 Testing custom query: '{query}'")
    
    print(f"\nUser: {query}")
    print("⏳ Dr. Degen is researching... (this may take 20-30 seconds)")
    
    # Detect if this is a token query
    is_token_query = '$' in query
    
    start_time = time.time()
    result = manager.run_gpt_research(query)
    duration = time.time() - start_time
    
    logger.info(f"✅ Research completed in {duration:.2f} seconds")
    
    # Log basic metrics about the result
    content_length = len(result.get("content", ""))
    logger.info(f"📊 Content length: {content_length} characters")
    logger.info(f"🔗 Sources found: {len(result.get('sources', []))}")
    
    metrics = result.get("metrics", {}) if is_token_query else None
    
    # Simulate chat UI response exactly as a user would see it
    print_chat_response(
        result.get("content", ""),
        metrics,
        result.get("sources", [])
    )
    
    return result

def run_all_tests(quiet: bool = False) -> Dict[str, Any]:
    """Run all test scenarios and collect results"""
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        logger.error("❌ No PERPLEXITY_API_KEY found in environment or .env file!")
        logger.info("Please add PERPLEXITY_API_KEY=your_api_key to your .env file")
        return {}
    
    logger.info("🚀 Starting comprehensive test suite for PerplexityManager...")
    
    # Initialize PerplexityManager
    manager = PerplexityManager()
    
    results = {}
    
    # Test 1: Token Research
    results["token_research"] = test_token_research(manager, "FAT", quiet)
    time.sleep(1)  # Avoid hitting rate limits
    
    # Test 2: Market Research
    results["market_research"] = test_market_research(manager, quiet)
    time.sleep(1)
    
    # Test 3: Social Sentiment
    results["social_sentiment"] = test_social_sentiment(manager, "Solana NFTs", quiet)
    time.sleep(1)
    
    # Test 4: Custom Sources
    results["custom_sources"] = test_custom_sources(manager, quiet)
    time.sleep(1)
    
    # Test 5: Degen Command
    results["degen_command"] = test_degen_command(manager, "$FAT")
    
    # Save all results to file
    with open("perplexity_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info("✅ All tests completed. Results saved to perplexity_test_results.json")
    
    return results

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(description="Test Dr. Degen's Perplexity Research capabilities")
    parser.add_argument("--token", "-t", help="Run token research for specific symbol", default=None)
    parser.add_argument("--market", "-m", help="Run market research", action="store_true")
    parser.add_argument("--sentiment", "-s", help="Run social sentiment analysis for topic", default=None)
    parser.add_argument("--custom", "-c", help="Run research with custom query", default=None)
    parser.add_argument("--degen", "-d", help="Test /degen command with token symbol or contract", default=None)
    parser.add_argument("--all", "-a", help="Run all tests", action="store_true")
    parser.add_argument("--quiet", "-q", help="Suppress chat UI simulation", action="store_true")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        logger.error("❌ No PERPLEXITY_API_KEY found in environment or .env file!")
        logger.info("Please add PERPLEXITY_API_KEY=your_api_key to your .env file")
        return
    
    # Initialize PerplexityManager
    manager = PerplexityManager()
    
    results = {}
    
    # Determine which tests to run
    if args.all:
        results = run_all_tests(args.quiet)
    else:
        if args.token:
            results["token_research"] = test_token_research(manager, args.token, args.quiet)
        
        if args.market:
            results["market_research"] = test_market_research(manager, args.quiet)
        
        if args.sentiment:
            results["social_sentiment"] = test_social_sentiment(manager, args.sentiment, args.quiet)
            
        if args.custom:
            results["custom_query"] = test_custom_query(manager, args.custom)
        
        if args.degen:
            results["degen_command"] = test_degen_command(manager, args.degen)
        
        # Default to token research if no args provided
        if not any([args.token, args.market, args.sentiment, args.custom, args.degen, args.all]):
            logger.info("No specific test selected, running token research for FAT as default")
            results["token_research"] = test_token_research(manager, "FAT", args.quiet)
        
        # Save results
        if results:
            with open("perplexity_test_results.json", "w") as f:
                json.dump(results, f, indent=2)
            logger.info("✅ Test results saved to perplexity_test_results.json")

if __name__ == "__main__":
    main() 