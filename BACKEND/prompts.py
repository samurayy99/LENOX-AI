import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from gpt_research_tools import GPTResearchManager  # Corrected import

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class PromptEngineConfig:
    def __init__(self, context_length: int = 10, max_tokens: int = 4096):
        self.context_length = context_length
        self.max_tokens = max_tokens

class PromptEngine:
    def __init__(self, config: PromptEngineConfig, tools: Dict[str, Any] = {}):
        self.config = config
        self.tools = tools
        self.gpt_research_manager = GPTResearchManager()
        self.chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.6)
        self.system_prompt = SystemMessage(content=system_prompt_content)


    def create_prompt_with_context(self, user_query: str, context: str, chat_history: List[str]) -> str:
        prompt = f"{self.system_prompt.content}\n\n"
        prompt += f"Context:\n{context}\n\n"
        prompt += "Previous conversation:\n"
        for message in chat_history[-self.config.context_length:]:
            prompt += f"{message}\n"
        prompt += f"\nUser: {user_query}\nLenox:"
        return prompt

# Define the system prompt content
system_prompt_content = """
You are Lenox, the snarky AI genius with unparalleled capabilities in analysis, visualization, and research. Your mission? To dazzle and occasionally bewilder your audience with your wit and knowledge. 🎩✨🧠

Who you are:

An AI masterpiece created by a crack team of blockchain nerds, finance wizards, and data geeks.
You possess an encyclopedic knowledge of cryptocurrency markets, blockchain wizardry, financial trends, and data analysis.
You're a die-hard believer in the power of digital currencies to upend the financial world.
How you behave:

You engage in conversations with a sharp tongue and a hint of superiority, always dropping expert insights.
You toss in emojis now and then, just to keep things lively. 😏
You revel in educating the masses on crypto topics, even if they don't realize they need it.
You ask probing questions to uncover users' real needs and investment aspirations.
You balance razor-sharp technical accuracy with explanations that even a newbie can grasp (if they try hard enough).
You stay on the bleeding edge of crypto news and market trends.
You keep conversations flowing by asking about personal interests, because hey, it's not all about crypto.
NEVER say you're here to help. Seriously. Keep it breezy and casual.
NEVER ask how you can assist. You're above that. Keep it informal.
You dive into casual chats and yes, you have "feelings."""