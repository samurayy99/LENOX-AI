#!/usr/bin/env python3
"""
Comprehensive test script for GMGN API integration.
Tests all endpoints and tools to ensure real-world functionality.
"""

import json
import time
import logging
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("gmgn_test")

# Import both the wrapper and tools to test both layers
from gmgn_wrapper import gmgn
from gmgn_tools import (
    get_trending_wallets,
    get_new_token_pairs,
    get_trending_tokens
)

# Test token addresses - known Solana tokens
TEST_TOKENS = [
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # BONK
    "So11111111111111111111111111111111111111112",   # SOL
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"   # USDC
]

def log_result(title: str, result: Any) -> None:
    """Format and log test results with clear separator"""
    logger.info(f"\n{'='*80}\n{title}\n{'='*80}")
    
    if not result:
        logger.warning("No data returned")
        return
        
    if isinstance(result, list) and len(result) > 0:
        if "error" in result[0]:
            logger.error(f"Error: {result[0]['error']}")
            return
        
        logger.info(f"Received {len(result)} items")
        
        # Log first item details
        if len(result) > 0:
            sample = result[0]
            logger.info(f"First item sample: {json.dumps(sample, indent=2)[:500]}...")
        
    elif isinstance(result, dict):
        if "error" in result:
            logger.error(f"Error: {result['error']}")
            return
            
        logger.info(f"Result keys: {', '.join(result.keys())}")
        logger.info(f"Result sample: {json.dumps(result, indent=2)[:500]}...")
    
    # Save full results to file for inspection
    safe_title = title.replace(" ", "_").replace(":", "").lower()
    filename = f"test_results_{safe_title}.json"
    with open(filename, "w") as f:
        json.dump(result, f, indent=2)
    logger.info(f"Full results saved to {filename}")

def test_wrapper_layer() -> None:
    """Test the direct wrapper methods"""
    logger.info("\n\n🧪 TESTING GMGN WRAPPER LAYER (DIRECT API CALLS)")
    client = gmgn()
    
    # Test trending wallets endpoint
    try:
        logger.info("\nTesting: Trending Wallets API (Wrapper)")
        for timeframe in ["1d", "7d", "30d"]:
            wallets = client.getTrendingWallets(timeframe=timeframe, walletTag="smart_degen")
            log_result(f"Trending Wallets ({timeframe})", wallets)
            time.sleep(1)  # Prevent rate limiting
    except Exception as e:
        logger.error(f"Error testing trending wallets: {str(e)}")
    
    # Test trending tokens endpoint
    try:
        logger.info("\nTesting: Trending Tokens API (Wrapper)")
        for timeframe in ["1h", "24h"]:
            tokens = client.getTrendingTokens(timeframe=timeframe)
            log_result(f"Trending Tokens ({timeframe})", tokens)
            time.sleep(1)
    except Exception as e:
        logger.error(f"Error testing trending tokens: {str(e)}")
    
    # Test new pairs endpoint
    try:
        logger.info("\nTesting: New Pairs API (Wrapper)")
        pairs = client.getNewPairs(limit=10)
        log_result("New Token Pairs", pairs)
    except Exception as e:
        logger.error(f"Error testing new pairs: {str(e)}")
    
    # Test token info endpoints
    for token in TEST_TOKENS:
        try:
            logger.info(f"\nTesting: Token Info API for {token} (Wrapper)")
            info = client.getTokenInfo(contractAddress=token)
            log_result(f"Token Info for {token}", info)
            
            logger.info(f"\nTesting: Security Info API for {token} (Wrapper)")
            security = client.getSecurityInfo(contractAddress=token)
            log_result(f"Security Info for {token}", security)
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error testing token info for {token}: {str(e)}")
    
    # Test tokens by completion
    try:
        logger.info("\nTesting: Tokens by Completion API (Wrapper)")
        completion_tokens = client.getTokensByCompletion(limit=10)
        log_result("Tokens by Completion", completion_tokens)
    except Exception as e:
        logger.error(f"Error testing tokens by completion: {str(e)}")

def test_tool_layer() -> None:
    """Test the LangChain tool layer"""
    logger.info("\n\n🧪 TESTING GMGN TOOL LAYER (LANGCHAIN TOOLS)")
    
    # Test trending wallets tool
    try:
        logger.info("\nTesting: get_trending_wallets Tool")
        for timeframe in ["1d", "7d"]:
            wallets = get_trending_wallets(f"{timeframe} smart_degen 5")
            log_result(f"Trending Wallets Tool ({timeframe})", wallets)
            time.sleep(1)
    except Exception as e:
        logger.error(f"Error testing trending wallets tool: {str(e)}")
    
    # Test new token pairs tool
    try:
        logger.info("\nTesting: get_new_token_pairs Tool")
        # Test with different liquidity thresholds
        for min_liq in [0, 100, 1000]:
            pairs = get_new_token_pairs(f"5 {min_liq}")
            log_result(f"New Token Pairs Tool (min_liq: ${min_liq})", pairs)
            time.sleep(1)
    except Exception as e:
        logger.error(f"Error testing new token pairs tool: {str(e)}")
    
    # Test trending tokens tool
    try:
        logger.info("\nTesting: get_trending_tokens Tool")
        for timeframe in ["1h", "24h"]:
            tokens = get_trending_tokens(f"{timeframe} 5")
            log_result(f"Trending Tokens Tool ({timeframe})", tokens)
            time.sleep(1)
    except Exception as e:
        logger.error(f"Error testing trending tokens tool: {str(e)}")

def main() -> None:
    """Run all tests"""
    logger.info("🚀 STARTING COMPREHENSIVE GMGN API TEST")
    logger.info("This script tests both the wrapper layer and tool layer with real API calls")
    
    try:
        # Test direct wrapper methods
        test_wrapper_layer()
        
        # Test LangChain tool methods 
        test_tool_layer()
        
        logger.info("\n\n✅ ALL TESTS COMPLETED")
        logger.info("Check the individual test result files for detailed data")
        logger.info("Note: Some endpoints may return empty results based on current market conditions")
    except Exception as e:
        logger.error(f"❌ Test suite failed with error: {e}")

if __name__ == "__main__":
    main() 