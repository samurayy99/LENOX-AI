#!/usr/bin/env python3
import os, traceback, argparse, logging
from dotenv import load_dotenv

from moralis_token_tools import (
    get_token_metadata, get_token_price, get_token_holder_count,
    get_token_dex_data, get_token_marketcap, analyze_token,
    search_token, resolve_token_address
)
from moralis_wallet_tools import (
    get_sol_balance, get_spl_tokens, get_portfolio_value,
    get_wallet_overview
)

# === ENV ===
load_dotenv()
if not os.getenv("MORALIS_API_KEY"):
    print("❌ MORALIS_API_KEY fehlt")
    exit(1)

# Logging für Tests konfigurieren
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_moralis")

def run_tool(tool_func, **kwargs):
    """Ruft LangChain-Tools mit dem korrekten Muster auf."""
    try:
        # Bei LangChain StructuredTools verwenden wir das name-Attribut statt __name__
        function_name = getattr(tool_func, 'name', None)
        if not function_name and hasattr(tool_func, 'func'):
            # Alternativ: Wenn es sich um ein gewrapptes Tool handelt, prüfe den Namen der Basisfunktion
            function_name = tool_func.func.__name__
            
        # Logging für Debugging
        logger.info(f"Tool-Aufruf: {function_name} mit Parametern {kwargs}")
            
        # Direkte Verwendung der .run-Methode für LangChain Tools
        if hasattr(tool_func, 'run'):
            if function_name == "resolve_token_address":
                query = kwargs.get("query", "").strip().lower().lstrip("$")
                return tool_func.run(query)
            elif function_name in ["get_token_metadata", "get_token_price", "get_token_holder_count", 
                                "get_token_dex_data", "get_token_marketcap", "get_token_risk_score"]:
                return tool_func.run(kwargs.get("token_address", ""))
            elif function_name == "analyze_token":
                return tool_func.run(kwargs.get("token_identifier", ""))
            elif function_name == "search_token":
                return tool_func.run(kwargs.get("query", ""), kwargs.get("limit", 5))
            elif function_name in ["get_sol_balance", "get_spl_tokens", "get_portfolio_value", "get_wallet_overview"]:
                return tool_func.run(kwargs.get("wallet", ""))
            else:
                # Generischer Fallback
                logger.info(f"Verwende generischen Aufruf für {function_name}")
                return tool_func.run(**kwargs)
    except Exception as e:
        logger.warning(f"Tool-Aufruf fehlgeschlagen: {str(e)}")
        return None


def section(title): print(f"\n{'='*50}\n{title}\n{'='*50}")

def validate_token(symbol, expected=None):
    section(f"TOKEN: {symbol}")
    address = run_tool(resolve_token_address, query=symbol)
    if not address:
        print(f"❌ Konnte {symbol} nicht auflösen.")
        return False

    print(f"✅ Adresse: {address}")
    
    try:
        meta = run_tool(get_token_metadata, token_address=address)
        if meta:
            print(f"✅ Name: {meta.get('name')} | Symbol: {meta.get('symbol')} | Decimals: {meta.get('decimals')}")
            if expected and 'name' in expected:
                expected_name = expected['name'].lower()
                actual = meta.get('name', '').lower()
                match = expected_name in actual or actual in expected_name
                print("✅ Namensvalidierung") if match else print("❌ Namensabweichung")
        else:
            print("❌ Keine Metadaten verfügbar")
            
        price = run_tool(get_token_price, token_address=address)
        holders = run_tool(get_token_holder_count, token_address=address)
        dex = run_tool(get_token_dex_data, token_address=address)
        
        print(f"✅ Preis: ${price:.6f}" if price is not None and price > 0 else "❌ Preis: nicht verfügbar")
        print(f"✅ Holder: {holders:,}" if holders is not None and holders > 0 else "❌ Holder: nicht verfügbar")
        
        if dex and isinstance(dex, dict):
            liq = dex.get('liquidity_usd', 0)
            vol = dex.get('volume_usd', 0)
            has_data = liq > 0 or vol > 0
            status = "✅" if has_data else "⚠️"
            print(f"{status} DEX-Daten: ${liq:,.2f} Liquidität | ${vol:,.2f} 24h Volumen | DEX: {dex.get('dex', 'unknown')}")
        else:
            print("❌ DEX-Daten: nicht verfügbar")
            
        mcap = run_tool(get_token_marketcap, token_address=address)
        
        print(f"✅ Marktkapitalisierung: ${mcap:,.0f}" if mcap is not None and mcap > 0 else "❌ Marktkapitalisierung: nicht verfügbar")
        
        # Vollständige Analyse
        analysis = run_tool(analyze_token, token_identifier=symbol)
        
        if analysis and isinstance(analysis, dict):
            print(f"✅ Analyse: {analysis.get('name')} | Preis: {analysis.get('price_usd')} | Risk: {analysis.get('risk_assessment', {}).get('level')}")
            
            # Detaillierte Risikoanalyse
            issues = analysis.get('risk_assessment', {}).get('issues', [])
            if issues and issues != ["Healthy"]:
                print(f"⚠️ Risiko-Issues: {', '.join(issues)}")
        else:
            print("❌ Analyse: nicht verfügbar")
            
        return True
    except Exception as e:
        print(f"❌ Fehler bei Token-Validierung: {str(e)}")
        if logging.getLogger().level <= logging.INFO:
            traceback.print_exc()
        return False

def validate_wallet(wallet, expected=None):
    section(f"WALLET: {wallet}")
    sol = run_tool(get_sol_balance, wallet=wallet)
    tokens = run_tool(get_spl_tokens, wallet=wallet)
    value = run_tool(get_portfolio_value, wallet=wallet)
    overview = run_tool(get_wallet_overview, wallet=wallet)

    success = 0
    total_checks = 4  # Anzahl der Tests
    
    if sol is not None and sol > 0:
        print(f"✅ SOL: {sol:.2f}")
        success += 1
    else:
        print("❌ SOL: nicht verfügbar")
    
    if tokens is not None and isinstance(tokens, list):
        print(f"✅ Tokens: {len(tokens)}")
        success += 1
        
        # Liste der Top-Tokens nur anzeigen, wenn tokens vorhanden
        if tokens:
            # Sicherer Zugriff auf das amount-Attribut mit Fallback
            try:
                top = sorted(tokens, key=lambda t: float(t.get('amount', 0) if isinstance(t, dict) else 0), reverse=True)[:3]
                if top:
                    print("Top Tokens:")
                    for t in top:
                        if not isinstance(t, dict):
                            continue
                        symbol = t.get('symbol', '???')
                        decimals = int(t.get('decimals', 0))
                        amount = float(t.get('amount', 0)) / (10 ** decimals)
                        price_usd = float(t.get('usdPrice', 0))
                        value_str = f"(~${amount * price_usd:,.2f})" if price_usd > 0 else ""
                        print(f"  - {symbol}: {amount:,.2f} {value_str}")
            except Exception as e:
                print(f"  ⚠️ Fehler beim Sortieren der Tokens: {str(e)}")
    else:
        print("❌ Keine Token-Informationen verfügbar")
    
    if value is not None and value > 0:
        print(f"✅ Portfolio-Wert: ${value:,.2f}")
        success += 1
    else:
        print("❌ Portfolio: nicht verfügbar")
    
    if overview:
        print(f"✅ Übersicht: Tokens: {overview.get('token_count')} | NFTs: {overview.get('nft_count')} | Swaps: {overview.get('recent_swaps')} | Risk: {overview.get('risk', {}).get('level')}")
        success += 1
    else:
        print("❌ Übersicht: nicht verfügbar")
        
    print(f"\nZusammenfassung: {success}/{total_checks} Tests erfolgreich ({success/total_checks*100:.0f}%)")
    return success == total_checks

def token_search_test():
    section("TOKEN-SUCHE")
    queries = ["WIF", "dogwifhat", "SOL", "BONK"]
    success = 0
    
    for q in queries:
        print(f"🔍 Suche: {q}")
        try:
            results = run_tool(search_token, query=q, limit=3)
            if results and isinstance(results, list):
                success += 1
                print(f"  ✅ {len(results)} Ergebnisse gefunden")
                for r in results:
                    if not isinstance(r, dict):
                        continue
                    symbol = r.get('symbol', '???')
                    name = r.get('name', 'Unbekannt')
                    source = r.get('source', 'Unbekannt')
                    addr = r.get('tokenAddress') or r.get('address', 'Keine Adresse')
                    print(f"  - {symbol} ({name}) | Quelle: {source} | Adresse: {addr}")
            else:
                print("  ❌ Keine Treffer")
        except Exception as e:
            print(f"❌ Fehler bei {q}: {str(e)}")
            if logging.getLogger().level <= logging.INFO:
                traceback.print_exc()
                
    print(f"\nZusammenfassung: {success}/{len(queries)} Suchanfragen erfolgreich ({success/len(queries)*100:.0f}%)")
    return success == len(queries)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test der Solana-Tools mit realen APIs")
    parser.add_argument("--wif", action="store_true", help="Teste nur WIF")
    parser.add_argument("--wallet", action="store_true", help="Teste nur Wallet")
    parser.add_argument("--search", action="store_true", help="Teste nur Suche")
    parser.add_argument("--token", type=str, help="Teste einen benutzerdefinierten Token (Symbol oder Adresse)")
    parser.add_argument("--address", type=str, help="Teste eine benutzerdefinierte Wallet-Adresse")
    parser.add_argument("--verbose", "-v", action="store_true", help="Ausführliche Logging-Ausgabe")
    args = parser.parse_args()

    # Logging-Level anpassen, wenn verbos aktiviert ist
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    try:
        # Standard-Flags, wenn keine angegeben wurden
        run_all = not any([args.wif, args.wallet, args.search, args.token, args.address])
        
        success = []
        
        if args.wif or run_all:
            print("\n🪙 WIF Token Tests")
            expected = {
                "name": "dogwifhat",
                "symbol": "WIF",
                "price_approx": 0.55,
                "market_cap_approx": 548_600_000,
                "liquidity_approx": 9_600_000,
                "holders_approx": 206_430,
            }
            for variant in ["WIF", "$WIF", "dogwifhat"]:
                success.append(validate_token(variant, expected))

        if args.wallet or run_all:
            print("\n👛 Wallet Tests")
            expected_wallet = {"sol_balance_approx": 12.68}
            success.append(validate_wallet("8MoW9mtbEz6z3gPuAdYb1yWhjCAxQSYqpcTb1CQgN5qb", expected_wallet))
        
        if args.address:
            print(f"\n👛 Benutzerdefinierte Wallet: {args.address}")
            success.append(validate_wallet(args.address))

        if args.search or run_all:
            print("\n🔎 Suchtests")
            success.append(token_search_test())
            
        if args.token:
            print(f"\n🪙 Benutzerdefinierter Token-Test: {args.token}")
            success.append(validate_token(args.token))

        # Gesamtzusammenfassung
        success_count = sum(1 for s in success if s)
        print(f"\n{'='*50}")
        print(f"🎯 Gesamtergebnis: {success_count}/{len(success)} Tests erfolgreich ({success_count/len(success)*100:.0f}%)")
        print(f"{'='*50}")
        
        if success_count == len(success):
            print("\n🎉 Alle Tests erfolgreich abgeschlossen!")
        else:
            print(f"\n⚠️ {len(success) - success_count} Test(s) fehlgeschlagen.")

    except Exception as e:
        print(f"\n❌ Kritischer Fehler: {e}")
        traceback.print_exc()
