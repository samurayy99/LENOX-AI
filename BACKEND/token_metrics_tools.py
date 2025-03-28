# src/tools/dune/token_metrics_tools.py
from langchain.tools import tool
from dune_client.client import DuneClient
import os
import logging

# Konfiguration
logger = logging.getLogger(__name__)
DUNE_API_KEY = os.getenv('DUNE_API_KEY')
dune = DuneClient(DUNE_API_KEY or '')

# Die Query-ID, die du nach dem Speichern erhältst
RELATIVE_STRENGTH_QUERY_ID = 4902578  # Ersetze mit der tatsächlichen ID

@tool
def get_memecoin_relative_strength(limit: int = 25, min_strength: float = 0.0):
    """
    Identifiziert Memecoins, die sowohl Bitcoin als auch den breiteren Memecoin-Markt outperformen.
    
    Diese Tokens zeigen überdurchschnittliche relative Stärke, ein Indikator, der in der 
    technischen Analyse als frühes Signal für anhaltende Aufwärtsbewegungen gilt.
    
    Args:
        limit: Anzahl der anzuzeigenden Top-Tokens (Standard: 25)
        min_strength: Minimaler Wert für optimierte relative Stärke (Standard: 0.0)
        
    Returns:
        Liste von Memecoins mit starker relativer Performance gegenüber BTC und anderen Memecoins
    """
    try:
        # Note: With get_latest_result() we're using the parameters set in the saved query
        # If you need different parameters, you'd need to use the execute_query API instead
        query_result = dune.get_latest_result(RELATIVE_STRENGTH_QUERY_ID)
        return query_result.result
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Memecoin relativen Stärke: {str(e)}")
        raise Exception(f"Konnte keine Daten zur Memecoin relativen Stärke abrufen: {str(e)}")

