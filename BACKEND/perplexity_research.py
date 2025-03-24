import os
import logging
import re
import datetime
import json
from typing import Dict, List, Optional, Any, Tuple, cast
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerplexityManager:
    """
    Manages interactions with the Perplexity API for crypto and memecoin research
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Perplexity Manager with API key"""
        load_dotenv()
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            logger.warning("No Perplexity API key provided. Set PERPLEXITY_API_KEY environment variable.")
        
        self.cache: Dict[str, Dict[str, Any]] = {}  # Simple in-memory cache
        self.cache_ttl = 3600  # 1 hour cache TTL
        self.current_date = datetime.datetime.now().strftime("%d. %b. %Y")
        
        # OpenAI-compatible client for Perplexity API
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.perplexity.ai")
        
    def degen_research(self, query: str, source_urls: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Executes comprehensive Dr. Degen research on a token (by symbol or contract address).
        This is the main entry point for the `/degen` command.
        
        Args:
            query: The token to research (with or without /degen prefix)
            source_urls: Optional URLs to prioritize
            
        Returns:
            Dictionary with complete research results
        """
        # Strip /degen command if present
        clean_query = re.sub(r'^/degen\s+', '', query).strip()
        
        # Parse token and identify if it's a contract address or symbol
        token_info = self._parse_token_identifier(clean_query)
        if not token_info:
            return {
                "type": "text",
                "content": "Yo, Dr. Degen here! I need a token symbol (like $WIF) or a contract address (like CA:EP2i...).",
                "query": query,
                "sources": [],
                "metrics": {}
            }
            
        token_symbol, contract_address, is_contract = token_info
        
        # Generate default sources based on token info
        default_sources = self._generate_default_sources(token_symbol, contract_address)
        if source_urls:
            default_sources.extend(source_urls)
        
        # Customize the research query
        research_query = self._build_research_query(token_symbol, contract_address, is_contract)
        
        # Execute the research
        return self.run_gpt_research(
            query=research_query,
            report_type="deep_research",  # Always use deep research for /degen
            source_urls=default_sources,
            # Pass the parsed token symbol for proper formatting
            token_symbol=token_symbol
        )
    
    def run_gpt_research(self, query: str, report_type: str = "custom_report", 
                         report_source: str = "web", 
                         source_urls: Optional[List[str]] = None,
                         token_symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes research using Perplexity API.
        
        Args:
            query: The research query
            report_type: Type of report to generate
            report_source: Source of information
            source_urls: Optional URLs to prioritize
            token_symbol: Override for token detection (for direct calls from degen_research)
            
        Returns:
            Dictionary with type and content keys for the research results
        """
        try:
            # Generate cache key
            cache_key = f"{query}_{report_type}"
            current_time = datetime.datetime.now().timestamp()
            
            # Check cache
            if cache_key in self.cache and (current_time - self.cache[cache_key].get("timestamp", 0) < self.cache_ttl):
                logger.info(f"Using cached result for: {query}")
                return self.cache[cache_key]["data"]
            
            # Detect if token query (if not explicitly provided)
            is_token_query = bool(token_symbol)
            if not token_symbol and '$' in query:
                token_match = re.search(r'\$([A-Za-z0-9]+)', query)
                if token_match:
                    token_symbol = token_match.group(1)
                    is_token_query = True
            
            # Prepare messages
            system_message = self._get_system_prompt(token_symbol)
            
            # Enhanced handling for token queries - two-stage process
            if is_token_query and '$' in query and not "CA:" in query:
                # First stage: Identify the correct token with highest market cap
                token_identification_query = f"""
                Identify the HIGHEST MARKET CAP token with the symbol ${token_symbol} on SOLANA blockchain specifically.
                
                CRITICAL INSTRUCTIONS:
                1. ONLY search for tokens on SOLANA blockchain
                2. If multiple tokens with symbol ${token_symbol} exist on Solana, choose the one with HIGHEST market cap
                3. Ignore tokens on other blockchains (BSC, Ethereum, etc.)
                4. Use Solana explorers: solscan.io, birdeye.so, and dexscreener.com/solana for research
                
                Return EXACTLY this JSON format without any explanation or markdown:
                {{
                    "symbol": "The token symbol",
                    "blockchain": "Solana",
                    "contract_address": "The full Solana contract address",
                    "market_cap_usd": "Market cap value with units (e.g. $10M)",
                    "price_usd": "Current price",
                    "liquidity_usd": "Available liquidity",
                    "volume_24h": "24h trading volume"
                }}
                
                If you cannot find a ${token_symbol} token specifically on Solana, say so explicitly in your response.
                """
                
                # Only use web search for identification, not custom sources yet
                identification_messages: List[ChatCompletionMessageParam] = [
                    cast(ChatCompletionSystemMessageParam, {"role": "system", "content": "You are a crypto research tool that only provides exact JSON data about Solana tokens as requested. No explanations, just the data in JSON format."}),
                    cast(ChatCompletionUserMessageParam, {"role": "user", "content": token_identification_query})
                ]
                
                # Make identification API call
                logger.info(f"First stage: Identifying highest market cap ${token_symbol} token on Solana...")
                identification_response = self.client.chat.completions.create(
                    model="sonar-reasoning", 
                    messages=identification_messages,
                    temperature=0.1,
                    max_tokens=800,
                    extra_body={
                        "web_search_options": {"search_context_size": "high"}
                    }
                )
                
                # Process identification result
                identification_content = identification_response.choices[0].message.content
                logger.info(f"Token identification response: {identification_content[:100]}...")
                
                valid_token_data = False
                
                if identification_content:
                    # Try to extract JSON from the response
                    try:
                        # First try to find JSON block in markdown
                        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', identification_content, re.DOTALL)
                        if json_match:
                            token_data = json.loads(json_match.group(1))
                            logger.info(f"Found JSON in markdown block")
                        else:
                            # Try to find raw JSON anywhere in the response
                            json_match = re.search(r'({[\s\S]*?"symbol"[\s\S]*?})', identification_content)
                            if json_match:
                                token_data = json.loads(json_match.group(1))
                                logger.info(f"Found raw JSON in response")
                            else:
                                # Try to parse the whole response as JSON
                                token_data = json.loads(identification_content)
                                logger.info(f"Parsed whole response as JSON")
                            
                        # Validate we have a Solana token
                        if token_data and "contract_address" in token_data:
                            # Check if specifically says it's not on Solana
                            if "could not find" in identification_content.lower() or "not found" in identification_content.lower():
                                logger.warning(f"API explicitly stated no ${token_symbol} token found on Solana")
                            elif token_data.get("blockchain", "").lower() == "solana":
                                valid_token_data = True
                                contract = token_data.get("contract_address")
                                market_cap = token_data.get("market_cap_usd", "unknown")
                                price = token_data.get("price_usd", "unknown")
                                volume = token_data.get("volume_24h", "unknown")
                                
                                logger.info(f"Identified ${token_symbol} on Solana with contract {contract}")
                                logger.info(f"Market cap: ${market_cap}, Price: ${price}, Volume: ${volume}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse token identification JSON: {str(e)}")
                
                if valid_token_data:
                    # Successfully identified a Solana token with this symbol
                    # Add contract and market cap to query
                    user_message = self._format_user_query(
                        query, 
                        token_symbol,
                        source_urls=source_urls if source_urls else [
                            f"https://solscan.io/token/{contract}",
                            f"https://birdeye.so/token/{contract}?chain=solana",
                            f"https://dexscreener.com/solana/{contract}"
                        ]
                    )
                    
                    # Add the identified contract to the query for clarity
                    user_message = f"{user_message}\n\nIMPORTANT: Focus ONLY on the Solana token with contract address {contract} which has market cap ${market_cap} and price ${price}. Ignore any tokens with the same name on other blockchains. ONLY report about this specific Solana token."
                
                # If token identification failed, try one more approach: specific search with additional context
                elif "CA:" not in query:
                    logger.info(f"Token identification failed, trying direct Solana-focused search...")
                    
                    # Use the standard query but with explicit focus on Solana
                    user_message = self._format_user_query(query, token_symbol, source_urls)
                    user_message = f"{user_message}\n\nCRITICAL: Focus ONLY on tokens on the Solana blockchain. If multiple tokens with symbol ${token_symbol} exist on Solana, ONLY analyze the one with the highest market cap or volume. Completely ignore any tokens with similar names on other blockchains like Ethereum or BSC."
                else:
                    # Standard query formatting for non-token queries or contract-specific queries
                    user_message = self._format_user_query(query, token_symbol, source_urls)
            else:
                # Standard query formatting for non-token queries or contract-specific queries
                user_message = self._format_user_query(query, token_symbol, source_urls)
            
            messages: List[ChatCompletionMessageParam] = [
                cast(ChatCompletionSystemMessageParam, {"role": "system", "content": system_message}),
                cast(ChatCompletionUserMessageParam, {"role": "user", "content": user_message})
            ]
            
            # Select model based on report type
            model = "sonar-deep-research" if report_type == "deep_research" else "sonar-reasoning"
            
            # Set search context size based on report type
            search_context = "high" if report_type in ["deep_research", "comprehensive"] else "medium"
            
            # Make API call
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=3000,
                extra_body={
                    "web_search_options": {"search_context_size": search_context}
                }
            )
            
            # Process result
            content = response.choices[0].message.content
            if content is None:
                content = "No content received from API"
            
            # Extract sources or generate default sources
            sources = self._extract_sources(content, query, token_symbol)
            
            # Extract metrics (for token queries)
            metrics = self._extract_metrics(content) if is_token_query else None
            
            # Structure result
            result = {
                "type": "text",
                "content": content,
                "query": query,
                "sources": sources,
                "metrics": metrics
            }
            
            # Cache result
            self.cache[cache_key] = {
                "data": result,
                "timestamp": current_time
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Perplexity research: {str(e)}")
            return {
                "type": "text", 
                "content": f"Yo, Dr. Degen here - technical difficulties while digging for alpha! Error: {str(e)}",
                "query": query,
                "sources": [],
                "metrics": {}
            }
    
    def _parse_token_identifier(self, query: str) -> Optional[Tuple[str, Optional[str], bool]]:
        """
        Parse token identifier from query, supporting both $SYMBOL and CA:address formats.
        Returns (symbol, contract_address, is_contract) tuple, or None if no valid token found.
        """
        # Try to extract token symbol
        symbol_match = re.search(r'\$([A-Za-z0-9]+)', query)
        if symbol_match:
            return symbol_match.group(1), None, False
            
        # Try to extract contract address (CA:address or just address if it looks like one)
        ca_match = re.search(r'(?:CA:)?([A-Za-z0-9]{32,})', query)
        if ca_match:
            # For contract addresses, try to extract a possible symbol
            address = ca_match.group(1)
            symbol = None
            # Look for a potential symbol like "WIF token: CA:address"
            symbol_ca_match = re.search(r'\$?([A-Za-z0-9]{2,5})\s+(?:token|coin)', query, re.IGNORECASE)
            if symbol_ca_match:
                symbol = symbol_ca_match.group(1)
            return symbol or "UNKNOWN", address, True
            
        return None
    
    def _generate_default_sources(self, token_symbol: str, contract_address: Optional[str] = None) -> List[str]:
        """Generate comprehensive default sources for token research"""
        sources = []
        
        # Add Solana explorers and DEX sources
        sources.extend([
            f"https://solscan.io/token/{contract_address or token_symbol}",
            f"https://birdeye.so/token/{token_symbol}?chain=solana",
            f"https://dexscreener.com/solana/{token_symbol}",
            f"https://solanafloor.com/token/{token_symbol}"
        ])
        
        # Add social sources
        sources.extend([
            f"https://twitter.com/search?q=%24{token_symbol}",
            f"https://www.coingecko.com/en/coins/{token_symbol.lower()}"
        ])
        
        # Add rugpull/security check sites if we have a contract
        if contract_address:
            sources.extend([
                f"https://rugcheck.xyz/tokens/{contract_address}"
            ])
            
        return sources
    
    def _build_research_query(self, token_symbol: str, contract_address: Optional[str] = None, 
                             is_contract: bool = False) -> str:
        """Build a comprehensive research query for the token"""
        if is_contract and contract_address:
            return (f"Provide a comprehensive Dr. Degen analysis for the Solana token with contract address {contract_address}. "
                   f"Prioritize data from Solscan.io, Birdeye.so, and DexScreener for your research. "
                   f"Include current price, market cap, trading volume, liquidity, sentiment, risk factors, wallet distribution, and give it a DegenScore rating.")
        else:
            # For symbol-based search, emphasize finding the highest market cap token
            return (f"Provide a comprehensive Dr. Degen analysis for ${token_symbol} token on Solana blockchain. "
                   f"CRITICAL: If multiple tokens with ticker ${token_symbol} exist, you MUST identify and analyze ONLY the one with the "
                   f"HIGHEST market capitalization (>$1M if possible) or highest trading volume. "
                   f"Ignore low-cap clones (<$100k market cap) unless they're the only option. "
                   f"VERY IMPORTANT: Only analyze tokens ON SOLANA blockchain, not on BSC, Ethereum, or others. "
                   f"Check Birdeye.so, DexScreener and Solscan thoroughly to find the most widely traded ${token_symbol} ON SOLANA. "
                   f"Include detailed metrics: price, market cap, volume, liquidity, sentiment, risk factors, wallet distribution.")
    
    def _get_system_prompt(self, token_symbol: Optional[str] = None) -> str:
        """System prompt based on query type"""
        if token_symbol:
            # Token-specific system prompt
            return """You are Dr. Degen, an unfiltered crypto analyst specializing in brutal token analyses and rugpull detection.

                STYLE & TONE:
                • Use crypto slang, be direct and blunt
                • Write like a trading insider with alpha knowledge
                • Give unvarnished assessments - don't sugar-coat your analysis
                
                RESEARCH FOCUS:
                • Token metrics (price, market cap, liquidity)
                • Wallet distribution (top holder %, smart money movements)
                • Rugpull indicators (mint rights, blacklists, team wallets)
                • Social sentiment (Twitter/Discord activity, influencers)
                • On-chain activity (trading volume, unique buyers/sellers)
                
                FORMAT:
                • Begin with the metrics section in exactly this format
                • Use emotional emojis (🚀, 💰, ⚠️, 🔥)
                • Conclude with the DegenScore and a clear BUY/SELL/WAIT recommendation
                """
        else:
            # General crypto research prompt
            return """You are Dr. Degen, the ultimate alpha source in the crypto space.
                
                STYLE & TONE:
                • Base everything on real data and current facts
                • Use the slang of a trading veteran who has made and lost millions
                • Be brutally honest, but provide valuable insights
                
                FORMAT:
                • Structure your response in clear sections with emojis
                • Provide direct value rather than general knowledge
                • Include decentralized sources and on-chain data
                """
    
    def _format_user_query(self, query: str, token_symbol: Optional[str] = None, 
                           source_urls: Optional[List[str]] = None) -> str:
        """Format user query with specific instructions"""
        today = datetime.datetime.now().strftime("%B %d, %Y")
        
        # Sources hint
        sources_text = ""
        if source_urls:
            sources_text = "PRIORITIZE THESE SOURCES:\n" + "\n".join([f"- {url}" for url in source_urls])
        
        if token_symbol:
            # Token-specific query
            return f"""Today's date: {today}
            
            RESEARCH TASK: Analyze the ${token_symbol} token comprehensively with special focus on rugpull risks, wallet distribution, and on-chain activity.
            
            IMPORTANT: If multiple tokens with ticker ${token_symbol} exist, ALWAYS analyze the one with the highest market capitalization or trading volume!
            
            {sources_text}
            
            FORMATTING INSTRUCTIONS:
            
            1. Begin with this exact format (replace placeholders, use "Not available" for uncertainty):
            
            ---DEGEN-METRICS-START---
            Token: ${token_symbol}
            Blockchain: [Blockchain Name]
            Contract: [Full Address]
            Current Price: [$ Value]
            24h Change: [% Change]
            Market Cap: [$ Value]
            24h Volume: [$ Value]
            Liquidity: [$ Value]
            Holders: [Number]
            Creation Date: [Date]
            Top 10 Wallets: [% Share]
            ---DEGEN-METRICS-END---
            
            2. Then structure your report with these headings:
               ## 🧪 DR. DEGEN'S DIAGNOSIS
               ## 📊 TOKEN VITALS
               ## 🔬 MARKET ANALYSIS
               ## 🔥 SOCIAL SENTIMENT
               ## ⚠️ RISK FACTORS & RUGPULL CHECK
               ## 🔮 ALPHA OUTLOOK
            
            3. Conclude with this rating:
            
            ---DEGEN-SCORE-START---
            DegenScore: [1-10 Rating]
            Recommendation: [BUY/WAIT/SELL/AVOID]
            Key Risk: [Biggest Risk]
            Key Strength: [Biggest Strength]
            ---DEGEN-SCORE-END---
            
            IMPORTANT: 
            • In the first sentence under DR. DEGEN'S DIAGNOSIS, directly state which blockchain this token runs on
            • In RISK FACTORS, specifically check for rugpull indicators: minting rights, distribution, wallet activity
            • DegenScore under 3 = extremely risky, 4-6 = speculative, 7-8 = solid, 9-10 = top-tier
            
            Research ${token_symbol} thoroughly and give your unfiltered opinion.
            """
        else:
            # General crypto query
            return f"""Today's date: {today}
            
            RESEARCH TASK: {query}
            
            {sources_text}
            
            FORMATTING INSTRUCTIONS:
            
            Structure your report with these headings:
            ## 🧠 DEGEN ALPHA SUMMARY
            ## 📊 DATA & MARKET CONTEXT
            ## 🔥 SOCIAL SIGNALS 
            ## 🧩 DEEPER INSIGHTS
            ## 💰 ALPHA OPPORTUNITIES
            ## 🔮 DR. DEGEN'S VERDICT
            
            IMPORTANT:
            • Provide specific data and facts, not just general statements
            • Analyze market conditions, tweets/social and current trends
            • Offer REAL alpha - what don't most people know that you've discovered through your research?
            
            Research question: {query}
            """
    
    def _extract_sources(self, content: str, query: str, token_symbol: Optional[str] = None) -> List[str]:
        """Extract URLs from content or generate default sources"""
        # URL pattern
        url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
        
        # Extract URLs from content
        found_urls = re.findall(url_pattern, content)
        
        # If URLs found, return them
        if found_urls:
            return list(set([url.rstrip('.,;:)') for url in found_urls]))
        
        # Else generate default sources based on token or query
        if token_symbol:
            return [
                f"https://solscan.io/token/{token_symbol}",
                f"https://birdeye.so/token/{token_symbol}?chain=solana",
                f"https://dexscreener.com/solana/{token_symbol}",
                f"https://twitter.com/search?q=%24{token_symbol}"
            ]
        else:
            # For general queries
            default_sources = [
                "https://www.coindesk.com/",
                "https://cointelegraph.com/",
                "https://www.tradingview.com/markets/cryptocurrencies/prices-all/"
            ]
            
            # Extract keywords for Twitter search
            keywords = [w for w in query.lower().split() if len(w) > 3 and w not in ['what', 'when', 'where', 'which', 'how', 'about', 'with']]
            if keywords:
                default_sources.append(f"https://twitter.com/search?q={'+'.join(keywords[:2])}")
            
            return default_sources
    
    def _extract_metrics(self, content: str) -> Dict[str, Any]:
        """Extract metrics from formatted content for token research"""
        metrics: Dict[str, Any] = {}
        
        # Extract metrics block
        metrics_pattern = r"---DEGEN-METRICS-START---(.*?)---DEGEN-METRICS-END---"
        metrics_match = re.search(metrics_pattern, content, re.DOTALL)
        
        if metrics_match:
            metrics_text = metrics_match.group(1)
            
            # Extract individual metrics with flexible patterns
            patterns = {
                "symbol": r"Token:\s*(\$?[A-Za-z0-9]+)",
                "blockchain": r"Blockchain:\s*([\w\s]+)",
                "contract": r"(?:Contract|Address):\s*([\w]+)",
                "price_usd": r"(?:Current Price|Price):\s*\$?([\d,.]+)",
                "price_change_24h": r"(?:24h Change|Change):\s*([-+]?[\d,.]+)%",
                "market_cap": r"Market Cap:\s*\$?([\d,.]+[KMB]?)",
                "volume_24h": r"(?:24h Volume|Volume):\s*\$?([\d,.]+[KMB]?)",
                "liquidity": r"Liquidity:\s*\$?([\d,.]+[KMB]?)",
                "holders": r"Holders:\s*([\d,]+)",
                "creation_date": r"Creation Date:\s*(.+?)(?:\n|$)",
                "top_wallets": r"Top 10 Wallets:\s*([\d,.]+%)"
            }
            
            # Try to extract each metric
            for key, pattern in patterns.items():
                match = re.search(pattern, metrics_text, re.IGNORECASE)
                if match:
                    # Remove markdown formatting (**, __ etc.)
                    value = re.sub(r'[*_\[\]]', '', match.group(1).strip())
                    # Clean up emojis that might be in the values
                    value = re.sub(r'[^\x00-\x7F]+', '', value).strip()
                    metrics[key] = value
                    
            # Verify blockchain is Solana, if not, log a warning
            if "blockchain" in metrics and "solana" not in metrics["blockchain"].lower():
                logger.warning(f"Non-Solana token detected: {metrics.get('blockchain', 'Unknown')}. This may indicate incorrect token identification.")
        
        # Extract DegenScore and recommendation
        score_pattern = r"---DEGEN-SCORE-START---(.*?)---DEGEN-SCORE-END---"
        score_match = re.search(score_pattern, content, re.DOTALL)
        
        if score_match:
            score_text = score_match.group(1)
            
            # DegenScore
            degen_score_match = re.search(r"DegenScore:\s*(\d+(?:\.\d+)?)", score_text, re.IGNORECASE)
            if degen_score_match:
                try:
                    metrics["degen_score"] = float(degen_score_match.group(1))
                except ValueError:
                    pass
            
            # Recommendation
            recommendation_match = re.search(r"Recommendation:\s*(\w+)", score_text, re.IGNORECASE)
            if recommendation_match:
                metrics["recommendation"] = recommendation_match.group(1).upper()
            
            # Risk and strength
            risk_match = re.search(r"Key Risk:\s*(.+?)(?:\n|$)", score_text)
            if risk_match:
                metrics["key_risk"] = risk_match.group(1).strip()
                
            strength_match = re.search(r"Key Strength:\s*(.+?)(?:\n|$)", score_text)
            if strength_match:
                metrics["key_strength"] = strength_match.group(1).strip()
        
        # Fallback: Extract blockchain from first line if not in metrics
        if "blockchain" not in metrics or not metrics["blockchain"]:
            blockchain_match = re.search(r"This token runs on (\w+)", content)
            if blockchain_match:
                metrics["blockchain"] = blockchain_match.group(1)
        
        return metrics 