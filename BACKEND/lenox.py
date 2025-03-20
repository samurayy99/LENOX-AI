import os
import logging
import requests
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationSummaryBufferMemory, ConversationBufferMemory
from langchain.schema.runnable import RunnablePassthrough
from langchain.agents import AgentExecutor
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents.format_scratchpad import format_to_openai_functions
from gpt_research_tools import GPTResearchManager
from intent_detection import IntentDetector, IntentType
from prompts import system_prompt_content, PromptEngine, PromptEngineConfig
import tiktoken

# Laden der Umgebungsvariablen
load_dotenv()

# Logger Setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Lenox:
    def __init__(self, tools: List[Any], prompt_engine: Optional[PromptEngine] = None, 
                 connection_string: str = "sqlite:///lenox.db", openai_api_key: Optional[str] = None):
        """
        Initialisiert die Lenox AI mit optimierter OpenAI-Nutzung.
        """
        # Tools Dictionary für PromptEngine erstellen
        tools_dict = {tool.name: tool for tool in tools} if tools and hasattr(tools[0], 'name') else {}
        
        # Prompt Engine Setup
        self.prompt_engine = prompt_engine if prompt_engine else PromptEngine(config=PromptEngineConfig(), tools=tools_dict)
        
        # Single primary model instance - one for regular queries, will be selectively switched when needed
        self.primary_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        
        # Cheaper model for summarization to reduce costs
        self.summarization_llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
        
        # Memory Setup with token limit to reduce API calls
        self.memory = ConversationSummaryBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            llm=self.summarization_llm,
            max_token_limit=2000
        )
        
        # Save API key for potential future use
        self.openai_api_key = openai_api_key
        
        # GPT Research & Intent Detection
        self.db_path = 'lenox.db'
        self.gpt_research_manager = GPTResearchManager()
        self.intent_detector = IntentDetector(self.prompt_engine, self.gpt_research_manager)
        
        # Setup components for agent
        self.setup_components(tools)
        

    def setup_components(self, tools):
        """
        Konfiguriert Tools und Modell-Interaktionen.
        """
        self.functions = [convert_to_openai_function(f) for f in tools]
        self.model = self.primary_model.bind(functions=self.functions)
        self.prompt = self.configure_prompts()
        self.chain = self.setup_chain()
        self.qa = AgentExecutor(agent=self.chain, tools=tools, verbose=False)

    def setup_chain(self):
        """
        Erstellt die Agent-Kette für die Verarbeitung.
        """
        return (
            RunnablePassthrough.assign(
                agent_scratchpad=lambda x: format_to_openai_functions(x.get("intermediate_steps", []))
            )
            | self.prompt
            | self.model
            | OpenAIFunctionsAgentOutputParser()
        )
        
    def configure_prompts(self, context_messages: Optional[List[str]] = None, user_query: str = ""):
        """
        Konfiguriert das Prompt-Template mit dynamischem Kontext.
        """
        tokenizer = tiktoken.encoding_for_model("gpt-4o-mini")
        max_context_tokens = 1000
        max_messages = 10

        def count_tokens(text: str) -> int:
            return len(tokenizer.encode(text))

        # Filter out non-string elements and limit to max_messages
        if context_messages:
            context_messages = [msg for msg in context_messages if isinstance(msg, str)]
            context_messages = context_messages[-max_messages:]
        
        system_prompt = system_prompt_content
        query_tokens = count_tokens(user_query)
        system_tokens = count_tokens(system_prompt)
        available_tokens = max_context_tokens - query_tokens - system_tokens

        context = ""
        if context_messages:
            for message in reversed(context_messages):
                message_tokens = count_tokens(message)
                if available_tokens - message_tokens > 0:
                    context = message + "\n" + context
                    available_tokens -= message_tokens
                else:
                    break

        full_prompt = f"{context}\n\nUser: {user_query}\nAI:"

        logger.debug(f"Number of context messages: {len(context_messages) if context_messages else 0}")
        logger.debug(f"System prompt tokens: {system_tokens}")
        logger.debug(f"User query tokens: {query_tokens}")
        logger.debug(f"Available tokens for context: {available_tokens}")
        logger.debug(f"Final context tokens: {count_tokens(context)}")
        logger.debug(f"Final prompt tokens: {count_tokens(full_prompt)}")

        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", full_prompt),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
    
    def set_dynamic_temperature(self, query: str):
        """
        Passt die Temperatur dynamisch an, ohne unnötig das Modell neu zu erstellen.
        """
        if any(keyword in query.lower() for keyword in ['price', 'market data', 'regulation', 'explain']):
            return 0.2  # Lower temperature for factual queries
        elif any(keyword in query.lower() for keyword in ['predict', 'trend', 'future', 'opinion']):
            return 0.6  # Medium temperature for speculative queries
        else:
            return 0.4  # Default temperature
        
    def select_model_for_query(self, query: str):
        """
        Wählt das passende Modell je nach Komplexität der Anfrage.
        """
        use_advanced_model = any(keyword in query.lower() for keyword in [
            'analyze', 'complex', 'detailed', 'in-depth', 'comprehensive'
        ])
        
        # Nur Modell wechseln wenn nötig
        current_model = self.primary_model.model_name
        if use_advanced_model and current_model != "gpt-4o":
            return "gpt-4o"
        elif not use_advanced_model and current_model != "gpt-4o-mini":
            return "gpt-4o-mini"
        else:
            return current_model
        
    def convchain(self, query: str, session_id: str = "my_session") -> dict:
        """
        Verarbeitet Nutzeranfragen und gibt eine Antwort zurück.
        """
        if not query:
            return {"type": "text", "content": "Bitte eine Anfrage stellen."}

        logger.debug(f"Empfangene Anfrage: {query}")

        # Intent-Erkennung
        detected_intent = self.intent_detector.detect_intent(query)
        logger.debug(f"Erkannter Intent: {detected_intent}")

        # GPT Research Intent Handling
        if detected_intent == IntentType.GPT_RESEARCH:
            result = self.gpt_research_manager.run_gpt_research(query)
            research_content = result.get('content', 'Fehler beim Verarbeiten der Recherche.')

            # Chat-Historie updaten
            self.memory.chat_memory.add_user_message(query)
            self.memory.chat_memory.add_ai_message(research_content)

            return result

        # Chat-Historie aktualisieren
        self.memory.chat_memory.add_user_message(query)

        # Letzte Chat-Historie abrufen
        chat_history = self.memory.load_memory_variables({})["chat_history"]
        chat_history_contents = [str(msg) for msg in chat_history if msg is not None]

        # Prompt mit Chat-Historie konfigurieren
        prompt = self.configure_prompts(context_messages=chat_history_contents, user_query=query)

        # Dynamische Temperatur und Modellauswahl
        dynamic_temp = self.set_dynamic_temperature(query)
        model_name = self.select_model_for_query(query)
        
        # Modell nur bei Bedarf aktualisieren
        if self.primary_model.model_name != model_name:
            self.primary_model = ChatOpenAI(model=model_name, temperature=dynamic_temp)
            self.model = self.primary_model.bind(functions=self.functions)
        else:
            # Nur Temperatur anpassen wenn nötig
            self.primary_model.temperature = dynamic_temp
        
        # Prompt Engine Temperatur aktualisieren
        self.prompt_engine.set_temperature(dynamic_temp)

        # Antwort generieren
        result = self.qa.invoke(
            {"input": prompt, "chat_history": chat_history_contents},
            config={"configurable": {"session_id": session_id}}
        )

        output = result.get('output', 'Fehler bei der Anfrage.')

        # Antwort in Memory speichern
        self.memory.chat_memory.add_ai_message(output)

        # Sicherstellen, dass Output ein String ist
        if not isinstance(output, str):
            output = str(output)

        return {"type": "text", "content": output}

    def construct_prompt(self, query, summarized_history):
        # Construct a more informative prompt using the query and summarized history
        return f"Given the following conversation summary:\n{summarized_history}\n\nUser query: {query}\n\nPlease provide a relevant and context-aware response:"
