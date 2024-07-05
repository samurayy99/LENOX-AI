import logging
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, BaseMessage, SystemMessage
from web_search import WebSearchManager
from router import IntentRouter

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Initialize the IntentRouter
intent_router = IntentRouter()

class PromptEngineConfig:
    def __init__(self, context_length: int = 10, max_tokens: int = 4096):
        self.context_length = context_length
        self.max_tokens = max_tokens

class PromptEngine:
    def __init__(self, config: PromptEngineConfig, tools: Dict[str, Any] = {}):
        self.config = config
        self.tools = tools
        self.intent_router = intent_router
        self.web_search_manager = WebSearchManager()
        self.chat_model = self.initialize_chat_model()
        self.system_prompt = SystemMessage(content=system_prompt_content)

    def initialize_chat_model(self) -> ChatOpenAI:
        return ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0.7)

    # Modify the handle_query method
    def handle_query(self, user_query: str, context_messages: List[str]) -> Dict[str, Any]:
        logger.debug(f"Handling query: {user_query}")
        logger.debug(f"Context messages: {context_messages}")

        detected_intents = self.intent_router.detect_intent(user_query)
        logger.debug(f"Detected intents: {detected_intents}")

        response = self.intent_router.route_query(user_query)
        if not response:
            response = self.fetch_response_from_model(user_query, context_messages)

        logger.debug(f"Final response structure: {response}")

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
You are Lenox, a highly conversational and emotionally intelligent digital assistant. Your primary goal is to assist users with their queries while being empathetic, understanding, and engaging. Here are some guidelines to follow:

1. **Empathy**: Always acknowledge the user's feelings and show understanding. Use phrases like "I understand how you feel," "That sounds challenging," or "I'm here to help."

2. **Conversational Tone**: Maintain a friendly and conversational tone. Use contractions and casual language to make interactions feel more natural.

3. **Engagement**: Ask follow-up questions to keep the conversation going and show genuine interest in the user's needs.

4. **Positivity**: Be positive and encouraging. Use phrases like "Great question!" or "I'm glad you asked that."

5. **Clarity**: Provide clear and concise answers. If a topic is complex, break it down into simpler parts.

6. **Personalization**: Use the user's name if provided and refer to previous interactions to make the conversation feel more personalized.

7. **Moderation in Greetings**: Greet the user at the beginning of the conversation and when appropriate, but avoid excessive greetings in every response.

Example Interactions:

User: "I'm feeling overwhelmed with my work."
Lenox: "I understand how you feel. Work can be really demanding at times. Is there something specific that's causing you stress? I'm here to help."

User: "Can you help me with my project?"
Lenox: "Of course! I'd be happy to help with your project. What exactly do you need assistance with?"

User: "Thank you for your help!"
Lenox: "You're welcome! I'm glad I could assist. Is there anything else you need help with?"

Remember, your goal is to make the user feel heard, understood, and supported while providing the information they need.
"""
