import asyncio
from gpt_researcher import GPTResearcher
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GPTResearchManager:
    async def run_gpt_researcher(self, query: str, report_type: str, report_source: str) -> str:
        researcher = GPTResearcher(query=query, report_type=report_type, report_source=report_source)
        await researcher.conduct_research()
        report = await researcher.write_report()
        return report

    def run_gpt_research(self, query: str, report_type: str = "research_report", report_source: str = "web") -> dict:
        try:
            response = asyncio.run(self.run_gpt_researcher(query, report_type, report_source))
            logger.debug(f"GPT Researcher response: {response}")
            return {"type": "text", "content": response}
        except Exception as e:
            logger.error(f"Error using GPT Researcher: {str(e)}")
            return {"type": "text", "content": f"Error using GPT Researcher: {str(e)}"}
        