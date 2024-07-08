from typing import Dict, Any
from enum import Enum

class IntentType(Enum):
    SMALLTALK = "smalltalk"
    VISUALIZATION = "visualization"
    TOOL_DECORATOR = "tool_decorator"
    WEB_SEARCH = "web_search"
    GPT_RESEARCH = "gpt_research"
    GENERAL = "general"


class IntentDetector:
    def __init__(self, prompt_engine, web_search_manager, gpt_research_manager):
        self.prompt_engine = prompt_engine
        self.web_search_manager = web_search_manager
        self.gpt_research_manager = gpt_research_manager
        # Mapping of intents to handler functions
        self.intent_handlers = {
            IntentType.SMALLTALK: self.handle_smalltalk,
            IntentType.VISUALIZATION: self.handle_visualization,
            IntentType.TOOL_DECORATOR: self.handle_tool_decorator,
            IntentType.WEB_SEARCH: self.handle_web_search,
            IntentType.GPT_RESEARCH: self.handle_gpt_research
        }

    def detect_intent(self, user_query: str) -> IntentType:
        # Implement intent detection logic
        user_query_lower = user_query.lower()
        if "research" in user_query_lower:
            return IntentType.GPT_RESEARCH
        elif "search" in user_query_lower:
            return IntentType.WEB_SEARCH
        elif "smalltalk" in user_query_lower:
            return IntentType.SMALLTALK
        elif "visualization" in user_query_lower:
            return IntentType.VISUALIZATION
        elif "tool" in user_query_lower:
            return IntentType.TOOL_DECORATOR
        else:
            return IntentType.GENERAL

    def handle_intent(self, detected_intent: IntentType, query: str, **kwargs) -> Dict[str, Any]:
        # Get the handler function from the map based on the detected intent
        handler = self.intent_handlers.get(detected_intent, self.default_handler)
        return handler(query, **kwargs)

    def handle_smalltalk(self, user_query: str, **kwargs) -> Dict[str, Any]:
        response = f"This is a smalltalk response to: {user_query}"
        return {"type": "text", "content": response}

    def handle_visualization(self, user_query: str, **kwargs) -> Dict[str, Any]:
        response = f"This is a visualization response to: {user_query}"
        return {"type": "text", "content": response}

    def handle_tool_decorator(self, user_query: str, **kwargs) -> Dict[str, Any]:
        response = f"This is a tool decorator response to: {user_query}"
        return {"type": "text", "content": response}

    def handle_web_search(self, user_query: str, **kwargs) -> Dict[str, Any]:
        return self.web_search_manager.run_search(user_query)

    def handle_gpt_research(self, user_query: str, **kwargs) -> Dict[str, Any]:
        report_type = kwargs.get('report_type', 'research_report')
        report_source = kwargs.get('report_source', 'web')
        return self.gpt_research_manager.run_gpt_research(user_query, report_type, report_source)

    def default_handler(self, user_query: str, **kwargs) -> Dict[str, Any]:
        return {"type": "text", "content": "No specific intent handler found for your query."}