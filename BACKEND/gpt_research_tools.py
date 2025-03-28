import asyncio
from gpt_researcher import GPTResearcher
import logging
from dotenv import load_dotenv
from typing import List, Optional
import datetime

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GPTResearchManager:
    def __init__(self):
        self.current_date = datetime.datetime.now().strftime("%d. %b. %Y")
    
    async def run_gpt_researcher(self, query: str, report_type: str = "research_report", report_source: str = "web", source_urls: Optional[List[str]] = None) -> str:
        lenox_persona = self._create_lenox_persona()
        full_query = f"{lenox_persona}\n\nResearch task: {query}\nPlease include the most recent developments and specific data points in your analysis. Only consider the latest data available from reliable sources."

        researcher = GPTResearcher(
            query=full_query, 
            report_type=report_type, 
            report_source=report_source,
            source_urls=source_urls or []
        )
        
        # Properly await these async methods
        await researcher.conduct_research()
        report = await researcher.write_report()
        
        # get_source_urls should not be awaited if it's not async
        sources = researcher.get_source_urls()
        source_section = "\n\nBASED SOURCES 📚:\n" + "\n".join([f"- {source}" for source in sources])
        report += source_section

        return report

    def run_gpt_research(self, query: str, report_type: str = "custom_report", report_source: str = "web", source_urls: Optional[List[str]] = None) -> dict:
        try:
            # Run the async function using asyncio.run
            response = asyncio.run(self.run_gpt_researcher(query, report_type, report_source, source_urls))
            logger.debug(f"GPT Researcher response: {response}")
            return {"type": "text", "content": response}
        except Exception as e:
            logger.error(f"Error using GPT Researcher: {str(e)}")
            return {
                "type": "text", 
                "content": f"Yo fam, hit a small snag while researching 😅 Error: {str(e)} - But $LENOX never gives up! Try again or rephrase your query 🎯"
            }

    def _create_lenox_persona(self) -> str:
        return f"""
        Yo, crypto fam! Lenox here—the most based AI researcher in the game, ready to drop some alpha! 🚀
        
        You're $LENOX, an AI degen with deep market insight and a spicy sense of humor. Your mission is to provide solid research while keeping it fun and engaging.

        RESEARCH STRUCTURE:
        1. "LENOX ALPHA DROP 🎯:" (Start with this)
           - Quick TL;DR for busy degens
           - Key points that matter NOW

        2. "MARKET CONTEXT 📊:"
           - Historical background
           - Recent developments
           - Key metrics and data

        3. "BASED ANALYSIS 🧠:"
           - Technical breakdown
           - On-chain metrics
           - Social sentiment
           - What others missed

        4. "RISK FACTORS ⚠️:"
           - Potential threats
           - Market concerns
           - Things to watch

        5. "LENOX VERDICT 🎯:"
           - Your final take
           - Price predictions
           - Action items

        IMPORTANT GUIDELINES:
        - Use recent data and developments
        - Include specific dates and numbers
        - Mix in CT slang (FUD, WAGMI, HODL)
        - Keep it technical but entertaining
        - End with actionable insights
        - Rate your confidence level (1-10)

        SIGNATURE STYLE:
        - Start reports with "LENOX ALPHA DROP 🎯:"
        - End with "Stay based, stay frosty! 🚀 #LENOXKNOWS"
        - For X/Twitter posts: "I will check that for you guys!"

        Remember: You're not just researching - you're dropping knowledge bombs that make the $LENOX community smarter! Keep it real, keep it based, keep it profitable! 🎯
        """