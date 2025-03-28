# src/tools/dune/graduated_tokens_tools.py
from langchain.tools import tool
from dune_client.client import DuneClient
import os
import logging

# Konfiguration
logger = logging.getLogger(__name__)
DUNE_API_KEY = os.getenv('DUNE_API_KEY')
dune = DuneClient(DUNE_API_KEY or '')

# Query-IDs
GRADUATED_TOKENS_QUERY_ID = 4902257  # Graduated Tokens Query
# TOKEN_ANALYSIS_QUERY_ID = 7654321  # Nicht benötigt, da der Tool-Decorator entfernt wurde

@tool
def get_recent_graduated_tokens(hours_lookback: int = 24, min_trades: int = 100):
    """
    Zeigt Tokens, die kürzlich von Pump.Fun zu aktivem DEX-Handel übergegangen sind.
    
    Diese Tokens haben den kritischen Übergang von der Startplattform zum breiteren
    Markt geschafft und zeigen signifikantes Handelsvolumen.
    
    Args:
        hours_lookback: Zeitraum in Stunden für die Suche nach graduierten Tokens (Standard: 24)
        min_trades: Mindestanzahl an Trades, um als aktiv zu gelten (Standard: 100)
        
    Returns:
        Liste von kürzlich graduierten Tokens mit Marktkapitalisierung und Handelsdaten
    """
    try:
        # Note: With get_latest_result() we're using the parameters set in the saved query
        # If you need different parameters, you'd need to use the execute_query API instead
        query_result = dune.get_latest_result(GRADUATED_TOKENS_QUERY_ID)
        return query_result.result
    except Exception as e:
        logger.error(f"Fehler beim Abrufen graduierter Tokens: {str(e)}")
        raise Exception(f"Konnte keine Daten zu graduierten Tokens abrufen: {str(e)}")

