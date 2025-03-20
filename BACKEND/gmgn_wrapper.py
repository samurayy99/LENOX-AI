import random
import tls_client
from fake_useragent import UserAgent
from typing import Dict, Any, Optional, List, Union

class gmgn:
    """GMGN API Wrapper für Solana Smart Money Tracking."""
    BASE_URL = "https://gmgn.ai/defi/quotation"

    def __init__(self):
        """Initialisiert den GMGN Wrapper."""
        self.sendRequest = None
        self.headers = None
        self.randomiseRequest()

    def randomiseRequest(self) -> None:
        """Erstellt einen randomisierten Request-Header für API-Zugriffe."""
        # Identifier für Client - Nutze die korrekten String-Werte
        client_identifiers = [
            'chrome_105', 'chrome_106', 'chrome_107', 'chrome_108',
            'safari_15_3', 'safari_15_6', 'safari_16_0',
            'firefox_102', 'firefox_104', 'firefox_105'
        ]
        
        # Direkte Verwendung des String-Identifiers
        self.identifier = random.choice(client_identifiers)
        
        # Session erstellen mit Type-Ignore für den client_identifier Parameter
        self.sendRequest = tls_client.Session(
            random_tls_extension_order=True, 
            client_identifier=self.identifier  # type: ignore
        )

        # Browser und OS bestimmen
        browser = 'Chrome'
        os_type = 'Windows'
        if 'safari' in self.identifier:
            browser = 'Safari'
            os_type = 'iOS' if 'iOS' in self.identifier else 'Mac OS X'
        elif 'firefox' in self.identifier:
            browser = 'Firefox'

        # User-Agent generieren
        self.user_agent = UserAgent(browsers=[browser], os=[os_type]).random

        # Headers setzen
        self.headers = {
            'Host': 'gmgn.ai',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'dnt': '1',
            'priority': 'u=1, i',
            'referer': 'https://gmgn.ai/?chain=sol',
            'user-agent': self.user_agent
        }

    def getTrendingWallets(self, timeframe: str = "7d", walletTag: str = "smart_degen") -> Dict[str, Any]:
        """
        Holt eine Liste von Trending-Wallets basierend auf Zeitraum und Wallet-Tag.

        Args:
            timeframe: "1d", "7d" oder "30d"
            walletTag: "pump_smart", "smart_degen", "reowned" oder "snipe_bot"

        Returns:
            Dictionary mit Wallet-Daten
        """
        self.randomiseRequest()
        
        # URL für Trending Wallets
        url = f"{self.BASE_URL}/v1/rank/sol/wallets/{timeframe}?tag={walletTag}&orderby=pnl_{timeframe}&direction=desc"

        try:
            # API-Aufruf
            request = self.sendRequest.get(url, headers=self.headers)
            response = request.json()
            
            if 'data' in response:
                return response['data']
            return {}
        except Exception:
            return {}

    def getTrendingTokens(self, timeframe: str = "1h") -> Dict[str, Any]:
        """
        Holt eine Liste von Trending-Tokens basierend auf einem Zeitraum.

        Args:
            timeframe: "1m", "5m", "1h", "6h" oder "24h"

        Returns:
            Dictionary mit Token-Daten
        """
        self.randomiseRequest()
        
        # Prüfe auf gültigen Zeitraum
        valid_timeframes = ["1m", "5m", "1h", "6h", "24h"]
        if timeframe not in valid_timeframes:
            timeframe = "1h"

        # URL basierend auf Zeitraum
        if timeframe == "1m":
            url = f"{self.BASE_URL}/v1/rank/sol/swaps/{timeframe}?orderby=swaps&direction=desc&limit=20"
        else:
            url = f"{self.BASE_URL}/v1/rank/sol/swaps/{timeframe}?orderby=swaps&direction=desc"
        
        try:
            # API-Aufruf
            request = self.sendRequest.get(url, headers=self.headers)
            response = request.json()
            
            if 'data' in response:
                return response['data']
            return {}
        except Exception:
            return {}

    def getWalletInfo(self, walletAddress: str, period: str = "7d") -> Dict[str, Any]:
        """
        Holt verschiedene Informationen über eine Wallet-Adresse.

        Args:
            walletAddress: Die Solana-Wallet-Adresse
            period: "1d", "7d" oder "30d"

        Returns:
            Dictionary mit Wallet-Informationen
        """
        self.randomiseRequest()
        
        # Prüfe auf gültigen Zeitraum
        valid_periods = ["1d", "7d", "30d"]
        if period not in valid_periods:
            period = "7d"
        
        # URL für Wallet-Info
        url = f"{self.BASE_URL}/v1/smartmoney/sol/walletNew/{walletAddress}?period={period}"

        try:
            # API-Aufruf
            request = self.sendRequest.get(url, headers=self.headers)
            response = request.json()
            
            if 'data' in response:
                return response['data']
            return {}
        except Exception:
            return {}