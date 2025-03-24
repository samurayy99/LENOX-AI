import random
import tls_client
from fake_useragent import UserAgent
from typing import Dict, Any, List, Union

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
        # Use a list of common browser identifiers instead of accessing ClientIdentifiers.__args__
        client_identifiers = [
            'chrome_105', 'chrome_106', 'chrome_107', 'chrome_108',
            'safari_15_3', 'safari_15_6', 'safari_16_0',
            'firefox_102', 'firefox_104', 'firefox_105'
        ]
        
        self.identifier = random.choice(client_identifiers)
        # Add type ignore to handle the ClientIdentifiers enum type mismatch
        self.sendRequest = tls_client.Session(
            random_tls_extension_order=True, 
            client_identifier=self.identifier  # type: ignore
        )

        parts = self.identifier.split('_')
        identifier = parts[0] if len(parts) > 0 else 'chrome'
        version = parts[1] if len(parts) > 1 else ''
        
        os = 'Windows'
        if identifier == 'opera':
            identifier = 'chrome'
        elif version == 'iOS':
            os = 'iOS'
        else:
            os = 'Windows'

        self.user_agent = UserAgent(browsers=[identifier.title()], os=[os]).random

        self.headers = {
            'Host': 'gmgn.ai',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'dnt': '1',
            'priority': 'u=1, i',
            'referer': 'https://gmgn.ai/?chain=sol',
            'user-agent': self.user_agent
        }

    def _process_response(self, response: Dict[str, Any]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Process API response to extract data in a consistent format.
        
        Args:
            response: The raw JSON response from API
            
        Returns:
            Processed data in a consistent format
        """
        if not response or not isinstance(response, dict):
            return {}
        
        # Extract data from response
        data = response.get('data', {})
        if not data:
            return {}
            
        # Handle different data structures
        
        # Case 1: Data contains a 'rank' array
        if isinstance(data, dict) and 'rank' in data and isinstance(data['rank'], list):
            return data['rank']
            
        # Case 2: Data contains a 'pairs' array (observed in new pairs)
        if isinstance(data, dict) and 'pairs' in data and isinstance(data['pairs'], list):
            return data['pairs']
            
        # Case 3: Data is a dict with nested items
        if isinstance(data, dict) and any(isinstance(v, list) for v in data.values()):
            # Return the first list found in the values
            for _, value in data.items():
                if isinstance(value, list) and value:
                    return value
        
        # Default: return data as is
        return data

    def getTokenInfo(self, contractAddress: str) -> Dict[str, Any]:
        """
        Gets info on a token.
        
        Args:
            contractAddress: The Solana token address
            
        Returns:
            Dictionary with token information
        """
        self.randomiseRequest()
        if not contractAddress:
            return {"error": "You must input a contract address."}
            
        url = f"{self.BASE_URL}/v1/tokens/sol/{contractAddress}"

        try:
            request = self.sendRequest.get(url, headers=self.headers)
            jsonResponse = request.json()
            
            result = self._process_response(jsonResponse)
            # Ensure we return a Dict even if we got a List
            if isinstance(result, list):
                return {"items": result} if result else {}
            return result
        except Exception:
            return {}
    
    def getNewPairs(self, limit: int = 50) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Limit - Limits how many tokens are in the response.

        Args:
            limit: Maximum number of pairs to return

        Returns:
            List or dictionary with new pairs data
        """
        self.randomiseRequest()
        if limit > 50:
            return {"error": "You cannot have more than check more than 50 pairs."}
        
        url = f"{self.BASE_URL}/v1/pairs/sol/new_pairs?limit={limit}&orderby=open_timestamp&direction=desc&filters[]=not_honeypot"

        try:
            request = self.sendRequest.get(url, headers=self.headers)
            jsonResponse = request.json()
            
            return self._process_response(jsonResponse)
        except Exception:
            return {}
    
    def getTrendingWallets(self, timeframe: str = "7d", walletTag: str = "smart_degen") -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Gets a list of trending wallets based on a timeframe and a wallet tag.

        Args:
            timeframe: "1d", "7d" or "30d"
            walletTag: "pump_smart", "smart_degen", "reowned" or "snipe_bot"

        Returns:
            List or dictionary with wallet data
        """
        self.randomiseRequest()
        
        url = f"{self.BASE_URL}/v1/rank/sol/wallets/{timeframe}?tag={walletTag}&orderby=pnl_{timeframe}&direction=desc"

        try:
            request = self.sendRequest.get(url, headers=self.headers)
            jsonResponse = request.json()
            
            return self._process_response(jsonResponse)
        except Exception:
            return {}

    def getTrendingTokens(self, timeframe: str = "1h") -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Gets a list of trending tokens based on a timeframe.

        Args:
            timeframe: "1m", "5m", "1h", "6h" or "24h"

        Returns:
            List or dictionary with token data
        """
        timeframes = ["1m", "5m", "1h", "6h", "24h"]
        self.randomiseRequest()
        
        if timeframe not in timeframes:
            return {"error": "Not a valid timeframe."}

        if timeframe == "1m":
            url = f"{self.BASE_URL}/v1/rank/sol/swaps/{timeframe}?orderby=swaps&direction=desc&limit=20"
        else:
            url = f"{self.BASE_URL}/v1/rank/sol/swaps/{timeframe}?orderby=swaps&direction=desc"
        
        try:
            request = self.sendRequest.get(url, headers=self.headers)
            jsonResponse = request.json()
            
            return self._process_response(jsonResponse)
        except Exception:
            return {}

    def getTokensByCompletion(self, limit: int = 50) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Gets tokens by their bonding curve completion progress.

        Args:
            limit: Maximum number of tokens to return
            
        Returns:
            List or dictionary with token data
        """
        self.randomiseRequest()
        if limit > 50:
            return {"error": "Limit cannot be above 50."}

        url = f"{self.BASE_URL}/v1/rank/sol/pump?limit={limit}&orderby=progress&direction=desc&pump=true"

        try:
            request = self.sendRequest.get(url, headers=self.headers)
            jsonResponse = request.json()
            
            return self._process_response(jsonResponse)
        except Exception:
            return {}
    
    def findSnipedTokens(self, size: int = 10) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Gets a list of tokens that have been sniped.

        Args:
            size: Maximum number of tokens to return
            
        Returns:
            List or dictionary with sniped token data
        """
        self.randomiseRequest()
        if size > 39:
            return {"error": "Size cannot be more than 39"}
        
        url = f"{self.BASE_URL}/v1/signals/sol/snipe_new?size={size}&is_show_alert=false&featured=false"

        try:
            request = self.sendRequest.get(url, headers=self.headers)
            jsonResponse = request.json()
            
            return self._process_response(jsonResponse)
        except Exception:
            return {}

    def getGasFee(self) -> Dict[str, Any]:
        """
        Get the current gas fee price.
        
        Returns:
            Dictionary with gas fee data
        """
        self.randomiseRequest()
        url = f"{self.BASE_URL}/v1/chains/sol/gas_price"

        try:
            request = self.sendRequest.get(url, headers=self.headers)
            jsonResponse = request.json()
            
            result = self._process_response(jsonResponse)
            # Ensure we return a Dict even if we got a List
            if isinstance(result, list):
                return {"items": result} if result else {}
            return result
        except Exception:
            return {}
    
    def getTokenUsdPrice(self, contractAddress: str) -> Dict[str, Any]:
        """
        Get the realtime USD price of the token.
        
        Args:
            contractAddress: The Solana token address
            
        Returns:
            Dictionary with token price data
        """
        self.randomiseRequest()
        if not contractAddress:
            return {"error": "You must input a contract address."}
        
        url = f"{self.BASE_URL}/v1/sol/tokens/realtime_token_price?address={contractAddress}"

        try:
            request = self.sendRequest.get(url, headers=self.headers)
            jsonResponse = request.json()
            
            result = self._process_response(jsonResponse)
            # Ensure we return a Dict even if we got a List
            if isinstance(result, list):
                return {"items": result} if result else {}
            return result
        except Exception:
            return {}

    def getTopBuyers(self, contractAddress: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Get the top buyers of a token.
        
        Args:
            contractAddress: The Solana token address
            
        Returns:
            List or dictionary with top buyers data
        """
        self.randomiseRequest()
        if not contractAddress:
            return {"error": "You must input a contract address."}
        
        url = f"{self.BASE_URL}/v1/tokens/top_buyers/sol/{contractAddress}"

        try:
            request = self.sendRequest.get(url, headers=self.headers)
            jsonResponse = request.json()
            
            return self._process_response(jsonResponse)
        except Exception:
            return {}

    def getSecurityInfo(self, contractAddress: str) -> Dict[str, Any]:
        """
        Gets security info about the token.
        
        Args:
            contractAddress: The Solana token address
            
        Returns:
            Dictionary with security data
        """
        self.randomiseRequest()
        if not contractAddress:
            return {"error": "You must input a contract address."}
        
        url = f"{self.BASE_URL}/v1/tokens/security/sol/{contractAddress}"

        try:
            request = self.sendRequest.get(url, headers=self.headers)
            jsonResponse = request.json()
            
            result = self._process_response(jsonResponse)
            # Ensure we return a Dict even if we got a List
            if isinstance(result, list):
                return {"items": result} if result else {}
            return result
        except Exception:
            return {}

    def getWalletInfo(self, walletAddress: str, period: str = "7d") -> Dict[str, Any]:
        """
        Gets various information about a wallet address.

        Args:
            walletAddress: The Solana wallet address
            period: "1d", "7d" or "30d"

        Returns:
            Dictionary with wallet information
        """
        self.randomiseRequest()
        periods = ["1d", "7d", "30d"]

        if not walletAddress:
            return {"error": "You must input a wallet address."}
        if period not in periods:
            period = "7d"
        
        url = f"{self.BASE_URL}/v1/smartmoney/sol/walletNew/{walletAddress}?period={period}"

        try:
            request = self.sendRequest.get(url, headers=self.headers)
            jsonResponse = request.json()
            
            result = self._process_response(jsonResponse)
            # Ensure we return a Dict even if we got a List
            if isinstance(result, list):
                return {"items": result} if result else {}
            return result
        except Exception:
            return {}
    
    def getWalletTokenDistribution(self, walletAddress: str, period: str = "7d") -> Dict[str, Any]:
        """
        Get the distribution of ROI on tokens traded by the wallet address
        
        Args:
            walletAddress: The Solana wallet address
            period: "1d", "7d" or "30d"
            
        Returns:
            Dictionary with wallet token distribution data
        """
        self.randomiseRequest()
        periods = ["1d", "7d", "30d"]

        if not walletAddress:
            return {"error": "You must input a wallet address."}
        if period not in periods:
            period = "7d"

        url = f"{self.BASE_URL}/v1/rank/sol/wallets/{walletAddress}/unique_token_7d?interval={period}"
        
        try:
            request = self.sendRequest.get(url, headers=self.headers)
            jsonResponse = request.json()
            
            result = self._process_response(jsonResponse)
            # Ensure we return a Dict even if we got a List
            if isinstance(result, list):
                return {"items": result} if result else {}
            return result
        except Exception:
            return {}