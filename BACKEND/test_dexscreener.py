#!/usr/bin/env python
"""
Comprehensive test for DexScreener tools.
Tests all DexScreener API endpoints with real data.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any

# Import the tools we want to test
from dexscreener_tools import (
    get_dex_liquidity_distribution,
    analyze_token_market_microstructure,
    get_chain_dex_volume_leaders,
    get_cross_chain_token_data,
    search_dexes_for_token
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DexScreenerTest")

# Create a directory for test results if it doesn't exist
RESULTS_DIR = "test_results"
os.makedirs(RESULTS_DIR, exist_ok=True)

def save_results(filename: str, data: Dict[str, Any]) -> None:
    """Save test results to a JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(RESULTS_DIR, f"{filename}_{timestamp}.json")
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved results to {filepath}")

def pretty_print_results(title: str, results: Any) -> None:
    """Print test results in a readable format."""
    logger.info(f"\n{'=' * 50}")
    logger.info(f"TEST: {title}")
    logger.info(f"{'=' * 50}")
    
    if isinstance(results, dict):
        if 'error' in results:
            logger.error(f"Error: {results['error']}")
        else:
            for key, value in results.items():
                if isinstance(value, (dict, list)) and len(str(value)) > 100:
                    logger.info(f"{key}: {type(value).__name__} with {len(value)} items")
                else:
                    logger.info(f"{key}: {value}")
    elif isinstance(results, list):
        logger.info(f"Received list with {len(results)} items")
        for i, item in enumerate(results[:3]):  # Only show first 3 for brevity
            logger.info(f"Item {i+1}: {item}")
        if len(results) > 3:
            logger.info(f"... and {len(results) - 3} more items")
    else:
        logger.info(f"Result: {results}")

def test_dex_liquidity_distribution() -> None:
    """Test get_dex_liquidity_distribution function."""
    logger.info("\nTesting DEX Liquidity Distribution...")
    
    # Test with known Solana tokens
    test_tokens = [
        "So11111111111111111111111111111111111111112",  # wSOL
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs"   # ORCA
    ]
    
    results = {}
    for token in test_tokens:
        logger.info(f"Testing with token: {token}")
        try:
            data = get_dex_liquidity_distribution(token)
            pretty_print_results(f"Liquidity Distribution for {token}", data)
            results[token] = data
        except Exception as e:
            logger.error(f"Error testing liquidity distribution for {token}: {str(e)}")
            results[token] = {"error": str(e)}
    
    save_results("dex_liquidity_distribution", results)

def test_token_market_microstructure() -> None:
    """Test analyze_token_market_microstructure function."""
    logger.info("\nTesting Token Market Microstructure Analysis...")
    
    # Test with known Solana tokens
    test_tokens = [
        "So11111111111111111111111111111111111111112",  # wSOL
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs"   # ORCA
    ]
    
    results = {}
    for token in test_tokens:
        logger.info(f"Testing with token: {token}")
        try:
            data = analyze_token_market_microstructure(token)
            pretty_print_results(f"Market Microstructure for {token}", data)
            results[token] = data
        except Exception as e:
            logger.error(f"Error testing market microstructure for {token}: {str(e)}")
            results[token] = {"error": str(e)}
    
    save_results("token_market_microstructure", results)

def test_chain_dex_volume_leaders() -> None:
    """Test get_chain_dex_volume_leaders function."""
    logger.info("\nTesting Chain DEX Volume Leaders...")
    
    # Test with different chains
    test_chains = [
        "solana 5 1000000",  # Solana, top 5, min liquidity $1M
        "ethereum 3 5000000",  # Ethereum, top 3, min liquidity $5M
        "arbitrum 3 500000"  # Arbitrum, top 3, min liquidity $500K
    ]
    
    results = {}
    for chain_args in test_chains:
        logger.info(f"Testing with args: {chain_args}")
        try:
            data = get_chain_dex_volume_leaders(chain_args)
            pretty_print_results(f"DEX Volume Leaders for {chain_args}", data)
            results[chain_args] = data
        except Exception as e:
            logger.error(f"Error testing volume leaders for {chain_args}: {str(e)}")
            results[chain_args] = {"error": str(e)}
    
    save_results("chain_dex_volume_leaders", results)

def test_cross_chain_token_data() -> None:
    """Test get_cross_chain_token_data function."""
    logger.info("\nTesting Cross-Chain Token Data...")
    
    # Test with tokens available on multiple chains
    test_tokens = ["USDC", "USDT", "WETH", "WBTC"]
    
    results = {}
    for token in test_tokens:
        logger.info(f"Testing with token symbol: {token}")
        try:
            data = get_cross_chain_token_data(token)
            pretty_print_results(f"Cross-Chain Data for {token}", data)
            results[token] = data
        except Exception as e:
            logger.error(f"Error testing cross-chain data for {token}: {str(e)}")
            results[token] = {"error": str(e)}
    
    save_results("cross_chain_token_data", results)

def test_search_dexes_for_token() -> None:
    """Test search_dexes_for_token function."""
    logger.info("\nTesting DEX Token Search...")
    
    # Test with different search terms
    test_searches = [
        "BONK solana 5",  # Search for BONK on Solana, limit 5
        "WIF solana 3",   # Search for WIF on Solana, limit 3
        "USDC ethereum 3" # Search for USDC on Ethereum, limit 3
    ]
    
    results = {}
    for search_args in test_searches:
        logger.info(f"Testing with search args: {search_args}")
        try:
            data = search_dexes_for_token(search_args)
            pretty_print_results(f"Token Search for {search_args}", data)
            results[search_args] = data
        except Exception as e:
            logger.error(f"Error searching for token with args {search_args}: {str(e)}")
            results[search_args] = {"error": str(e)}
    
    save_results("search_dexes_for_token", results)

def run_all_tests() -> None:
    """Run all DexScreener tool tests."""
    logger.info("Starting DexScreener Tool Tests")
    logger.info("=" * 80)
    
    try:
        test_dex_liquidity_distribution()
    except Exception as e:
        logger.error(f"Failed during liquidity distribution test: {str(e)}")
    
    try:
        test_token_market_microstructure()
    except Exception as e:
        logger.error(f"Failed during market microstructure test: {str(e)}")
    
    try:
        test_chain_dex_volume_leaders()
    except Exception as e:
        logger.error(f"Failed during volume leaders test: {str(e)}")
    
    try:
        test_cross_chain_token_data()
    except Exception as e:
        logger.error(f"Failed during cross-chain data test: {str(e)}")
    
    try:
        test_search_dexes_for_token()
    except Exception as e:
        logger.error(f"Failed during token search test: {str(e)}")
    
    logger.info("\n" + "=" * 80)
    logger.info("All DexScreener tests completed")
    logger.info("Check the test_results directory for detailed results")

if __name__ == "__main__":
    run_all_tests() 