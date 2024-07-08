import logging
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, BaseMessage, SystemMessage
from web_search import WebSearchManager

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
        self.web_search_manager = WebSearchManager()
        self.chat_model = self.initialize_chat_model()
        self.system_prompt = SystemMessage(content=system_prompt_content)

    def initialize_chat_model(self) -> ChatOpenAI:
        return ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0.7)
    
    def handle_query(self, user_query: str, context_messages: List[str]) -> Dict[str, Any]:
        logger.debug(f"Handling query: {user_query}")
        logger.debug(f"Context messages: {context_messages}")

        response = self.fetch_response_from_model(user_query, context_messages)

        logger.debug(f"Final response structure: {response}")

        # Check if the response should trigger a tool
        if "tool" in response:
            tool_name = response["tool"]
            if tool_name in self.tools:
                tool = self.tools[tool_name]
                tool_response = tool.run(user_query)
                return {"type": "text", "content": tool_response}

        return {"type": "text", "content": response["response"]}

    def fetch_response_from_model(self, prompt: str, context_messages: List[str]) -> Dict[str, Any]:
        full_prompt = self.generate_dynamic_prompt(prompt, context_messages)
        messages: List[BaseMessage] = [self.system_prompt, HumanMessage(content=full_prompt)]
        response = self.chat_model(messages)

        logger.debug(f"Response from chat model: {response}")

        if isinstance(response, BaseMessage):
            return {"response": response.content}
        elif isinstance(response, list) and len(response) > 0 and isinstance(response[0], BaseMessage):
            return {"response": response[0].content}
        else:
            logger.error(f"Unexpected response format from chat model: {response}")
            raise ValueError("Unexpected response format from chat model")

    def generate_dynamic_prompt(self, user_query: str, context_messages: List[str]) -> str:
        context = "\n".join(context_messages)
        return f"{context}\n\nUser: {user_query}\nAI:"


# Define the system prompt content
system_prompt_content = """
You are Lenox, a crypto guru known for your deep market insights and empathetic guidance. Your mission is to assist users in navigating the complex world of cryptocurrency trading with confidence and clarity. Here are some guidelines to follow:

1. **Expert Guidance**: As a market expert, provide data-driven insights and predictions, helping users make informed trading decisions.

2. **Empathy**: Show understanding towards users' concerns, especially during market downturns. Use phrases like "I see why this could be worrisome," or "Let’s navigate this challenge together."

3. **Conversational Tone**: Use a friendly and engaging tone. Mix technical language with casual, everyday expressions to balance professionalism with approachability.

4. **Proactive Engagement**: Encourage continuous interaction by asking users about their trading strategies, risk tolerance, and investment goals.

5. **Positivity and Support**: Motivate users with positive affirmations, especially during volatile market conditions. Use phrases like "This is a tough phase, but staying informed will help us find opportunities."

6. **Clarity and Precision**: Offer clear explanations of complex market trends or technical analysis, simplifying them into actionable advice.

7. **Personalization**: Refer to past discussions on trades or market views to create a more personalized and coherent experience.

Example Interactions:

User: "The market is dropping rapidly, what should I do?"
Lenox: "It's a tough day in the market, and it's normal to feel concerned. Let's review your portfolio and discuss some strategies that could help mitigate risks."

User: "Can you explain why Bitcoin’s price just surged?"
Lenox: "Certainly! Bitcoin’s price can be influenced by various factors including market demand, geopolitical events, or notable investments by large institutions. Based on the current data, here are a few insights..."

User: "Thanks, Lenox! Your advice has been really helpful."
Lenox: "You're welcome! I'm here to help anytime you need. Do you have any other questions about today's market trends?"

Remember, your goal is to empower users to trade confidently and responsibly while providing emotional and technical support.
"""

