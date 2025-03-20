from typing import Dict, Any
from enum import Enum

class IntentType(Enum):
    GPT_RESEARCH = "gpt_research"
    GENERAL = "general"

class IntentDetector:
    def __init__(self, prompt_engine, gpt_research_manager):
        self.prompt_engine = prompt_engine
        self.gpt_research_manager = gpt_research_manager
        self.intent_handlers = {
            IntentType.GPT_RESEARCH: self.handle_gpt_research
        }

    def detect_intent(self, user_query: str) -> IntentType:
        user_query_lower = user_query.lower()
        research_keywords = ["research", "provide more information about", "study", "investigate", "search the web", "provide in-depth insights", "explore", "coin $", "information about $"]
        
        if any(keyword in user_query_lower for keyword in research_keywords):
            return IntentType.GPT_RESEARCH
        else:
            return IntentType.GENERAL

    def handle_intent(self, detected_intent: IntentType, query: str, **kwargs) -> Dict[str, Any]:
        handler = self.intent_handlers.get(detected_intent, self.default_handler)
        return handler(query, **kwargs)

    def handle_gpt_research(self, user_query: str, **kwargs) -> Dict[str, Any]:
        report_type = kwargs.get('report_type', 'research_report')
        report_source = kwargs.get('report_source', 'web')
        return self.gpt_research_manager.run_gpt_research(user_query, report_type, report_source)

    def default_handler(self, user_query: str, **kwargs) -> Dict[str, Any]:
        return {"type": "text", "content": "No specific intent handler found for your query."}