import logging
import time
from datetime import datetime
from typing import Dict, List, Any
from tabulate import tabulate
from gmgn_wrapper import gmgn  # Nutzt GMGN Wrapper
from langchain.tools import tool

# Logging Setup - Reduziere Level für Produktion
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s")

# Cache-Optimierung mit unterschiedlichen Expiry-Zeiten
CACHE = {}
CACHE_EXPIRY_MAP = {
    "whale_trades": 600,    # 10 Minuten
    "trending_tokens": 120, # 2 Minuten
    "whale_buys": 300,      # 5 Minuten
    "smart_money": 600,     # 10 Minuten
}
DEFAULT_EXPIRY = 300  # 5 Minuten als Standard

def format_timestamp(ts: Any) -> str:
    """Konvertiert Unix-Timestamp in lesbares Format oder gibt 'N/A' zurück."""
    try:
        return datetime.fromtimestamp(int(float(ts or 0))).strftime('%Y-%m-%d %H:%M')
    except (ValueError, TypeError):
        return "N/A"

def clear_expired_cache() -> None:
    """Remove old cache entries."""
    current_time = time.time()
    expired_keys = []
    
    for key_to_remove, (_, timestamp, expiry) in CACHE.items():
        if current_time - timestamp > expiry:
            expired_keys.append(key_to_remove)
            
    for key_to_remove in expired_keys:
        del CACHE[key_to_remove]

def cache_result(key: str, result: Any, category: str = "default") -> Any:
    """Cache API result mit flexiblem Timeout je nach Kategorie."""
    expiry = CACHE_EXPIRY_MAP.get(category, DEFAULT_EXPIRY)
    CACHE[key] = (result, time.time(), expiry)
    return result

def get_cached_result(key: str) -> Any:
    """Get cached result if available and not expired."""
    if key in CACHE:
        result, timestamp, expiry = CACHE[key]
        if time.time() - timestamp < expiry:
            return result
    return None

class WhaleWatch:
    """ Klasse für Whale-Trading-Analysen auf Solana. """
    
    def __init__(self):
        """ Initialisiert die Whale Watch Klasse mit GMGN API Wrapper. """
        self.gmgn = gmgn()
        self.logger = logging.getLogger("WhaleWatch")

    def get_whale_trades(self, timeframe: str = "7d", wallet_tag: str = "smart_degen") -> List[Dict]:
        """Holt aktuelle Whale-Trades auf Solana."""
        try:
            self.logger.info(f"Fetching whale trades for {timeframe} with tag {wallet_tag}")
            cache_key = f"whale_trades_{timeframe}_{wallet_tag}"
            cached = get_cached_result(cache_key)
            if cached:
                return cached
            
            # API-Aufruf    
            response = self.gmgn.getTrendingWallets(timeframe=timeframe, walletTag=wallet_tag)
            
            # Fehlerbehandlung für Response-Format
            if not response:
                self.logger.warning("Empty response from getTrendingWallets API")
                return []
                
            # Rank-Key existiert nicht in manchen Fällen
            rank_data = response.get('rank', [])
            if not rank_data and isinstance(response, list):
                rank_data = response  # Direkte Liste verwenden
                
            if not rank_data:
                self.logger.warning("No rank data found in response")
                return []

            whale_trades = []

            for wallet in rank_data:
                if not isinstance(wallet, dict):
                    continue
                    
                # Optimiertes sicheres Extrahieren von Daten
                buy_count = int(wallet.get('buy', 0) or 0)
                sell_count = int(wallet.get('sell', 0) or 0)
                trade_count = buy_count + sell_count
                
                # Aktivitätsstufe berechnen
                activity_level = "🟢 High" if trade_count > 20 else "🟡 Medium" if trade_count > 10 else "🔴 Low"
                
                # Profit mit einfachem Fehler-Handling
                realized_profit = float(wallet.get('realized_profit', 0) or 0)
                profit_per_trade = realized_profit / max(1, trade_count) if trade_count > 0 else 0
                
                # Win-Rate vereinfacht
                win_rate = float(wallet.get('winrate_7d', 0) or 0) * 100
                
                # Timestamp mit Helper-Funktion
                last_active_str = format_timestamp(wallet.get('last_active'))
                
                whale_trades.append({
                    "wallet_address": wallet.get('wallet_address', 'N/A'),
                    "profit_sol": round(realized_profit, 2),
                    "profit_per_trade": round(profit_per_trade, 3),
                    "win_rate": round(win_rate, 1),
                    "buy_trades": buy_count,
                    "sell_trades": sell_count,
                    "trades_total": trade_count,
                    "activity": activity_level,
                    "last_active": last_active_str,
                })

            result = sorted(whale_trades, key=lambda x: x["profit_sol"], reverse=True)
            return cache_result(cache_key, result, "whale_trades")

        except Exception as e:
            self.logger.error(f"Error fetching whale trades: {str(e)}")
            return []

    def get_whale_buys(self, wallet_address: str, period: str = "7d") -> Dict:
        """Holt alle Käufe eines bestimmten Whales."""
        try:
            self.logger.info(f"Fetching trade history for {wallet_address} ({period})")
            cache_key = f"whale_buys_{wallet_address}_{period}"
            cached = get_cached_result(cache_key)
            if cached:
                return cached
            
            # API-Aufruf
            response = self.gmgn.getWalletInfo(walletAddress=wallet_address, period=period)

            if not response:
                return {}
                
            # Optimiertes Extrahieren von Daten
            realized_profit = float(response.get("realized_profit", 0) or 0)
            winrate = float(response.get("winrate", 0) or 0) * 100
            
            trades = response.get("trades", [])
            if not isinstance(trades, list):
                trades = []

            result = {
                "wallet_address": wallet_address,
                "realized_profit": round(realized_profit, 2),
                "winrate": round(winrate, 1),
                "trades": trades
            }
            
            return cache_result(cache_key, result, "whale_buys")

        except Exception as e:
            self.logger.error(f"Error fetching whale buy history: {str(e)}")
            return {}
            
    def get_trending_tokens(self, timeframe: str = "1h", limit: int = 5) -> List[Dict]:
        """Holt trending Coins mit Smart Money Volumen."""
        try:
            self.logger.info(f"Fetching trending coins for {timeframe}")
            cache_key = f"trending_coins_{timeframe}_{limit}"
            cached = get_cached_result(cache_key)
            if cached:
                return cached
            
            # Direkten API-Aufruf machen, aber mit besserer Fehlerbehandlung
            response = self.gmgn.getTrendingTokens(timeframe=timeframe)
            
            # Verbesserte Fehlerbehandlung - Log für Debugging
            if not response:
                self.logger.warning(f"Empty trending tokens response for timeframe {timeframe}")
                # Versuche andere Zeitfenster
                if timeframe != "24h":
                    self.logger.info(f"Trying fallback timeframe 24h")
                    return self.get_trending_tokens("24h", limit)
                return []
            
            trending_coins = []
            
            # Direkte Verarbeitung der Root-Elemente der API-Antwort
            # Dies funktioniert mit allen möglichen Strukturen
            if isinstance(response, dict):
                # Suche nach einer Liste in den Schlüsseln
                for key_name, value in response.items():
                    if isinstance(value, list) and value and isinstance(value[0], dict):
                        for token in value[:limit]:
                            trending_coins.append(self._process_token_data(token))
                        break
                
                # Falls keine Liste gefunden, prüfe auf direkte Token-Daten
                if not trending_coins and "token_symbol" in response:
                    trending_coins.append(self._process_token_data(response))
                
                # Spezielle Behandlung für 'swaps'-Schlüssel, der ein Dict sein könnte
                swaps_data = response.get('swaps')
                if not trending_coins and isinstance(swaps_data, dict):
                    # Hole die Werte aus dem Dict als Liste
                    swaps_list = list(swaps_data.values())
                    for token in swaps_list[:limit]:
                        if isinstance(token, dict):
                            trending_coins.append(self._process_token_data(token))
            
            elif isinstance(response, list):
                # Direkte Liste von Tokens
                for token in response[:limit]:
                    if isinstance(token, dict):
                        trending_coins.append(self._process_token_data(token))
            
            # Sortiere nach Volume
            result_tokens = sorted(trending_coins, key=lambda x: x["volume_usd"], reverse=True)
            return cache_result(cache_key, result_tokens, "trending_tokens")

        except Exception as e:
            self.logger.error(f"Error fetching trending coins: {str(e)}")
            return []
    
    def _process_token_data(self, token: Dict) -> Dict:
        """Helfer-Methode zur Verarbeitung von Token-Daten"""
        return {
            "token_symbol": token.get('token_symbol', 'UNKNOWN'),
            "token_address": token.get('token_address', 'N/A'),
            "price_usd": float(token.get('price_usd', 0) or 0),
            "volume_usd": float(token.get('volume_usd', 0) or 0),
            "buys": int(token.get('buys', 0) or 0),
            "sells": int(token.get('sells', 0) or 0),
            "price_change": float(token.get('price_change', 0) or 0) * 100
        }

    def get_smart_money_tokens(self, top_whales: int = 5) -> List[Dict]:
        """Identifiziert die beliebtesten Tokens unter Smart Money Wallets."""
        try:
            cache_key = f"smart_money_tokens_{top_whales}"
            cached = get_cached_result(cache_key)
            if cached:
                return cached
            
            # Hole aktive Whales zuerst
            all_whales = self.get_whale_trades("7d")
            active_whales = [w for w in all_whales if w["trades_total"] > 0]
            
            # Wenn wir nicht genug aktive Whales haben, ergänze mit inaktiven
            whales = active_whales[:top_whales]
            if len(whales) < top_whales:
                inactive_whales = [w for w in all_whales if w not in active_whales]
                whales.extend(inactive_whales[:top_whales - len(whales)])
            
            if not whales:
                self.logger.warning("No whale data available for token analysis")
                return []
                
            # Temporärer Cache für Wallet-Infos, um doppelte API-Calls zu vermeiden
            wallet_info_cache = {}
            
            # Hole die Trades der Top Whales
            all_tokens: Dict[str, Dict[str, Any]] = {}
            
            for idx, whale in enumerate(whales):
                wallet_address = whale.get("wallet_address")
                if not wallet_address:
                    continue
                
                # Überprüfen, ob Wallet-Info bereits abgerufen wurde
                if wallet_address in wallet_info_cache:
                    whale_buys = wallet_info_cache[wallet_address]
                else:
                    whale_buys = self.get_whale_buys(wallet_address)
                    wallet_info_cache[wallet_address] = whale_buys
                
                # Sleep nur alle 5 Calls, um API-Last zu reduzieren
                if idx > 0 and idx % 5 == 0:
                    time.sleep(0.2)
                
                if not whale_buys or "trades" not in whale_buys or not isinstance(whale_buys["trades"], list):
                    continue
                    
                for trade in whale_buys["trades"]:
                    if not isinstance(trade, dict) or trade.get("action") != "buy":
                        continue
                        
                    token_symbol = trade.get("token_symbol", "UNKNOWN")
                    token_address = trade.get("token_address", "N/A")
                    
                    if token_symbol not in all_tokens:
                        all_tokens[token_symbol] = {
                            "symbol": token_symbol,
                            "address": token_address,
                            "count": 0,
                            "unique_whales": set(),
                            "last_bought": 0
                        }
                    
                    all_tokens[token_symbol]["count"] += 1
                    all_tokens[token_symbol]["unique_whales"].add(wallet_address)
                    
                    # Update last bought time - vereinfacht
                    trade_time = int(float(trade.get("timestamp", 0) or 0))
                    if trade_time > all_tokens[token_symbol]["last_bought"]:
                        all_tokens[token_symbol]["last_bought"] = trade_time
            
            # Formatiere die Ergebnisse - optimiert mit List Comprehension
            smart_money_tokens = [
                {
                    "symbol": t["symbol"],
                    "address": t["address"],
                    "buy_count": t["count"],
                    "whale_count": len(t["unique_whales"]),
                    "last_bought": format_timestamp(t["last_bought"])
                }
                for t in all_tokens.values() if t["count"] > 0
            ]
            
            # Sortiere nach Anzahl der Whales und dann nach Anzahl der Käufe
            result = sorted(smart_money_tokens, key=lambda x: (x["whale_count"], x["buy_count"]), reverse=True)
            return cache_result(cache_key, result, "smart_money")
            
        except Exception as e:
            self.logger.error(f"Error analyzing smart money tokens: {str(e)}")
            return []

    def generate_whale_report(self, whales_limit: int = 10, trending_timeframe: str = "1h") -> str:
        """Erstellt einen Whale-Trade-Report mit allen relevanten Daten."""
        # Hole und filtre Daten
        whales = self.get_whale_trades("7d")  # 7d für bessere Daten
        trending = self.get_trending_tokens(timeframe=trending_timeframe)
        smart_money_tokens = self.get_smart_money_tokens(top_whales=min(5, whales_limit))

        if not whales:
            return "❌ **Keine Whale-Trades gefunden!** API möglicherweise nicht erreichbar."

        report = "**🐳 Whale Watch Report – Aktuelle Smart Money Bewegungen**\n\n"

        # Top Whales mit Ranking Emojis
        report += "📊 **Top Whales nach Profit (SOL):**\n"
        report += "```\n"
        report += tabulate(
            [[f"{'🥇' if idx == 0 else '🥈' if idx == 1 else '🥉' if idx == 2 else f'{idx+1}'}",
              w["wallet_address"][:10] + "...", 
              w["profit_sol"], 
              w["profit_per_trade"],
              f"{w['win_rate']}%", 
              f"{w['buy_trades']}/{w['sell_trades']}", 
              w["activity"]]
             for idx, w in enumerate(whales[:whales_limit])],
            headers=["#", "Wallet", "Profit (SOL)", "Profit/Trade", "Win Rate", "Buys/Sells", "Activity"],
            tablefmt="pretty"
        )
        report += "\n```\n"

        # Trending Coins mit Prüfung
        if trending:
            report += "\n🔥 **Trending Coins mit Smart Money-Volumen:**\n"
            report += "```\n"
            report += tabulate(
                [[t["token_symbol"], f"${t['price_usd']:.6f}", f"${t['volume_usd']:.2f}", 
                  f"{t['price_change']:.2f}%", f"{t['buys']}/{t['sells']}"]
                 for t in trending[:5]],
                headers=["Token", "Preis (USD)", "Volume (USD)", "Change", "Buys/Sells"],
                tablefmt="pretty"
            )
            report += "\n```\n"
        else:
            report += "\n⚠️ **Trending Coin-Daten nicht verfügbar**\n"
            report += "Versuche später erneut oder mit einem anderen Zeitfenster (1h, 6h, 24h).\n"
            
        # Smart Money Tokens mit Prüfung
        if smart_money_tokens:
            report += "\n🚀 **Beliebte Smart Money Tokens:**\n"
            report += "```\n"
            report += tabulate(
                [[t["symbol"], t["whale_count"], t["buy_count"], t["last_bought"]]
                 for t in smart_money_tokens[:5]],
                headers=["Token", "Whales", "Käufe", "Zuletzt gekauft"],
                tablefmt="pretty"
            )
            report += "\n```\n"
        else:
            report += "\n⚠️ **Smart Money Token-Daten nicht verfügbar**\n"
            report += "Möglicherweise keine ausreichenden Wallet-Transaktionsdaten vorhanden.\n"

        # Filtre aktive Wallets für bessere Zusammenfassung
        active_whales = [w for w in whales[:whales_limit] if w["trades_total"] > 0]
        
        # Zusammenfassung
        report += "\n📈 **Zusammenfassung:**\n"
        if active_whales:
            # Berechne Durchschnitte nur für aktive Wallets
            avg_profit = sum(w["profit_sol"] for w in active_whales) / len(active_whales)
            avg_profit_per_trade = sum(w["profit_per_trade"] for w in active_whales) / len(active_whales)
            avg_win_rate = sum(w["win_rate"] for w in active_whales) / len(active_whales)
            
            report += f"- Durchschnittlicher Profit (aktive Wallets): **{avg_profit:.2f} SOL** (pro Trade: **{avg_profit_per_trade:.3f} SOL**)\n"
            report += f"- Durchschnittliche Win Rate (aktive Wallets): **{avg_win_rate:.1f}%**\n"
        else:
            # Falls keine aktiven Wallets, zeige Gesamt-Statistik
            avg_profit = sum(w["profit_sol"] for w in whales[:whales_limit]) / min(whales_limit, len(whales))
            report += f"- Durchschnittlicher Profit (alle Whales): **{avg_profit:.2f} SOL**\n"
            report += f"- Hinweis: Die meisten Top-Wallets zeigen aktuell geringe Aktivität.\n"
        
        if smart_money_tokens:
            report += f"- Aktueller Smart Money Favorit: **{smart_money_tokens[0]['symbol']}** "
            report += f"(von **{smart_money_tokens[0]['whale_count']}** Whales gekauft)\n"
            
        report += f"- Report erstellt: **{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**\n"

        return report


@tool
def whale_watch_report(whales_limit: int = 10, trending_timeframe: str = "1h"):
    """
    🚀 **Live Whale Watch Report für Solana Smart Money Trades!**
    
    Args:
        whales_limit (int): Anzahl der Top-Whales im Report (Standard: 10).
        trending_timeframe (str): Zeitraum für Trending-Tokens ("1m", "5m", "1h", "6h", "24h").
    
    **Enthält:**
    - 🏆 **Top Whales mit Performance-Ranking** (🥇🥈🥉) und Aktivitätsstufen
    - 📊 **Profit pro Trade & Win Rate** für besseren Überblick
    - 🔥 **Trending Coins** mit Smart-Money-Volumen und Preisentwicklung
    - 🚀 **Smart Money Token-Liste** mit aktuellen Whale-Favoriten
    """
    whale_watcher = WhaleWatch()
    return whale_watcher.generate_whale_report(whales_limit=whales_limit, trending_timeframe=trending_timeframe)