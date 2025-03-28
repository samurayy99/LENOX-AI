# src/tools/dune/smart_money_tools.py
from langchain.tools import tool
from dune_client.client import DuneClient
import os
import logging

# Konfiguration
logger = logging.getLogger(__name__)
DUNE_API_KEY = os.getenv('DUNE_API_KEY')
dune = DuneClient(DUNE_API_KEY or '')

# Die Query-ID, die du nach dem Speichern erhältst
SMART_MONEY_LEADERBOARD_QUERY_ID = 4902374
SMART_MONEY_BUYS_QUERY_ID = 4902561 

@tool
def get_top_solana_traders(limit: int = 25, min_volume_usd: float = 1000000):
    """
    Zeigt die Top-Trader auf Solana, sortiert nach Handelsvolumen und Profit.
    
    Identifiziert "Smart Money"-Wallets mit nachweislichem Erfolg, deren Aktivität
    wertvolle Signale für vielversprechende Token liefert.
    
    Args:
        limit: Anzahl der anzuzeigenden Top-Trader (Standard: 25)
        min_volume_usd: Mindest-Handelsvolumen in USD (Standard: 1.000.000)
        
    Returns:
        Liste von Top-Tradern mit Performance-Metriken, Handelsstil und aktuellen Käufen
    """
    try:
        # Note: With get_latest_result() we're using the parameters set in the saved query
        # If you need different parameters, you'd need to use the execute_query API instead
        query_result = dune.get_latest_result(SMART_MONEY_LEADERBOARD_QUERY_ID)
        return query_result.result
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Top-Trader: {str(e)}")
        raise Exception(f"Konnte keine Daten zu Top-Tradern abrufen: {str(e)}")

@tool
def get_smart_money_token_buys(hours: int = 24, min_smart_money_buyers: int = 2):
    """
    Zeigt, welche Tokens von mehreren erfolgreichen Solana-Tradern gekauft werden.
    
    Diese "Smart Money"-Signale sind oft frühe Indikatoren für vielversprechende Tokens,
    da erfolgreiche Trader oft vor der breiten Masse kaufen.
    
    Args:
        hours: Zeitraum in Stunden für die Suche nach Käufen (Standard: 24)
        min_smart_money_buyers: Mindestanzahl verschiedener Smart-Money-Wallets, die kaufen (Standard: 2)
        
    Returns:
        Liste von Tokens, die von erfolgreichen Tradern akkumuliert werden, mit Kauf-Details
    """
    try:
        # Note: With get_latest_result() we're using the parameters set in the saved query
        # If you need different parameters, you'd need to use the execute_query API instead
        query_result = dune.get_latest_result(SMART_MONEY_BUYS_QUERY_ID)
        return query_result.result
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Smart-Money-Käufe: {str(e)}")
        raise Exception(f"Konnte keine Daten zu Smart-Money-Käufen abrufen: {str(e)}")

