# src/tools/dune/whale_movement_tools.py
from langchain.tools import tool
from dune_client.client import DuneClient
import os
import logging

# Konfiguration
logger = logging.getLogger(__name__)
DUNE_API_KEY = os.getenv('DUNE_API_KEY')
dune = DuneClient(DUNE_API_KEY or '')

# Die Query-ID, die du nach dem Speichern erhältst
WHALE_BUYS_QUERY_ID = 4902608  # Ersetze mit der tatsächlichen ID

@tool
def get_recent_whale_buys(hours: int = 24, min_purchase_usd: float = 1000):
    """
    Zeigt signifikante Token-Käufe durch Whale-Wallets auf Solana.
    
    Diese Whale-Bewegungen sind oft frühe Indikatoren für aufkommende Trends,
    da große Wallets häufig vor der breiten Masse akkumulieren.
    
    Args:
        hours: Zeitraum in Stunden für die Suche nach Käufen (Standard: 24)
        min_purchase_usd: Mindestgröße eines Kaufs in USD (Standard: 1.000)
        
    Returns:
        Liste von signifikanten Whale-Käufen mit Wallet- und Token-Details
    """
    try:
        # Note: Currently using the parameters set in the saved query
        # Parameters in the function are just for documentation
        query_result = dune.get_latest_result(WHALE_BUYS_QUERY_ID)
        return query_result.result
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Whale-Käufe: {str(e)}")
        raise Exception(f"Konnte keine Daten zu Whale-Käufen abrufen: {str(e)}")

