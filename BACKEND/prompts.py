import logging
from datetime import datetime
from collections import deque
from enum import Enum
from tool_imports import import_tools

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class IntentType(Enum):
    """Enumeration for identifying the user's intent more effectively."""
    GREETING = "greeting"
    EMOTIONAL_SUPPORT = "emotional_support"
    INFORMATION_QUERY = "information_query"
    SMALLTALK = "smalltalk"
    DOCUMENT_QUERY = "document_query"  # Added document query intent

class EmotionalState(Enum):
    """Enumeration to handle different levels of emotional responses."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    SUPPORTIVE = "supportive"

class PromptEngine:
    def __init__(self, tools=None, model='gpt-3.5-turbo-0125', max_tokens=4096):
        self.model = model
        self.max_tokens = max_tokens
        self.tools = tools if tools else import_tools()
        self.history = deque()  # Initialize history as a deque to manage past inputs efficiently

    def classify_intent(self, user_input: str) -> IntentType:
        """
        Simple intent classification to augment ChatGPT-4's response handling.
        """
        lower_input = user_input.lower()
        if any(greeting in lower_input for greeting in ["hello", "hi", "greetings", "hey"]):
            return IntentType.GREETING
        elif "how are you" in lower_input or "what's up" in lower_input:
            return IntentType.SMALLTALK
        elif "help" in lower_input or "sad" in lower_input:
            return IntentType.EMOTIONAL_SUPPORT
        elif "document" in lower_input or "file" in lower_input or "summarize" in lower_input:
            return IntentType.DOCUMENT_QUERY  # Added document query classification
        return IntentType.INFORMATION_QUERY

    def detect_intent(self, user_input: str) -> str:
        """
        Detect intent from user input.
        """
        intent = self.classify_intent(user_input)
        return intent.value

    def generate_emotional_response(self, state: EmotionalState) -> str:
        """
        Generates responses that are emotionally aware, enhancing the AI's empathy.
        """
        responses = {
            EmotionalState.POSITIVE: "That sounds great! How can I assist you further?",
            EmotionalState.NEUTRAL: "I understand. Please go on.",
            EmotionalState.SUPPORTIVE: "I'm here for you. Tell me more about how you're feeling."
        }
        return responses[state]

    def create_prompt(self, user_input: str) -> str:
        """
        Generates a personalized prompt based on the user's input and emotional state.
        """
        intent = self.classify_intent(user_input)
        emotional_response = self.generate_emotional_response(
            EmotionalState.SUPPORTIVE if intent == IntentType.EMOTIONAL_SUPPORT else EmotionalState.NEUTRAL
        )

        # Building a context-aware prompt
        context = " ".join(self.history)
        if intent == IntentType.DOCUMENT_QUERY:
            prompt = f"{datetime.now():%Y-%m-%d %H:%M:%S} - Context: {context}\n{emotional_response}\nPlease summarize or provide information from the specified document.\nQuery: {user_input}"
        else:
            prompt = f"{datetime.now():%Y-%m-%d %H:%M:%S} - Context: {context}\n{emotional_response}\nWhat else can I help you with today?"

        return prompt

    def handle_input(self, user_input: str) -> str:
        """
        Handles the user input, updating history and generating a suitable prompt.
        """
        prompt = self.create_prompt(user_input)
        self.history.append(user_input)
        logging.info(f"Generated Prompt: {prompt}")
        return prompt

    def process_query(self, query: str, session_id: str) -> dict:
        """
        Process the user query by identifying its intent and using the appropriate tool.
        """
        intent = self.classify_intent(query)
        if intent == IntentType.GREETING:
            return self.handle_greeting()
        elif intent == IntentType.SMALLTALK:
            return self.handle_smalltalk()
        elif intent == IntentType.DOCUMENT_QUERY:
            return self.handle_document_query(query)
        elif intent == IntentType.EMOTIONAL_SUPPORT:
            return self.handle_emotional_support()
        else:
            return self.handle_information_query(query)

    def handle_greeting(self) -> dict:
        return {"type": "text", "content": "Hello! How can I assist you today?"}

    def handle_smalltalk(self) -> dict:
        return {"type": "text", "content": "I'm here to help you with any information you need."}

    def handle_document_query(self, query: str) -> dict:
        """
        Handle document-related queries.
        """
        # Example implementation for document handling
        # Here you can integrate with your document handling logic
        return {"type": "text", "content": "Document handling is not implemented yet."}

    def handle_emotional_support(self) -> dict:
        return {"type": "text", "content": "I'm here for you. Tell me more about how you're feeling."}

    def handle_information_query(self, query: str) -> dict:
        """
        Handle general information queries using the appropriate tool.
        """
        response = None
        for tool in self.tools:
            tool_name = tool.__name__.lower()
            if tool_name in query:
                response = tool(query)
                break

        if response is None:
            response = "Sorry, I couldn't find a suitable tool to handle your query."

        return {"type": "text", "content": response}
