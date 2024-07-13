from typing import Dict, Any
from enum import Enum

class IntentType(Enum):
    WEB_SEARCH = "web_search"
    GPT_RESEARCH = "gpt_research"
    GENERAL = "general"

class IntentDetector:
    def __init__(self, prompt_engine, web_search_manager, gpt_research_manager):
        self.prompt_engine = prompt_engine
        self.web_search_manager = web_search_manager
        self.gpt_research_manager = gpt_research_manager
        self.intent_handlers = {
            IntentType.WEB_SEARCH: self.handle_web_search,
            IntentType.GPT_RESEARCH: self.handle_gpt_research
        }

    def detect_intent(self, user_query: str) -> IntentType:
        user_query_lower = user_query.lower()
        if "youtube" in user_query_lower and "search" in user_query_lower:
            return IntentType.GENERAL  # Let the tool decorator handle YouTube searches
        elif "research" in user_query_lower:
            return IntentType.GPT_RESEARCH
        elif "search" in user_query_lower:
            return IntentType.WEB_SEARCH
        else:
            return IntentType.GENERAL

    def handle_intent(self, detected_intent: IntentType, query: str, **kwargs) -> Dict[str, Any]:
        handler = self.intent_handlers.get(detected_intent, self.default_handler)
        return handler(query, **kwargs)

    def handle_web_search(self, user_query: str, **kwargs) -> Dict[str, Any]:
        return self.web_search_manager.run_search(user_query)

    def handle_gpt_research(self, user_query: str, **kwargs) -> Dict[str, Any]:
        report_type = kwargs.get('report_type', 'research_report')
        report_source = kwargs.get('report_source', 'web')
        return self.gpt_research_manager.run_gpt_research(user_query, report_type, report_source)

    def default_handler(self, user_query: str, **kwargs) -> Dict[str, Any]:
        return {"type": "text", "content": "No specific intent handler found for your query."}
