import sqlite3
from typing import Dict, List, Union, Optional
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents.format_scratchpad import format_to_openai_functions
from lenox_memory import SQLChatMessageHistory
import requests
from gpt_research_tools import GPTResearchManager
from intent_detection import IntentDetector
# Import system prompt content from prompts.py
from prompts import system_prompt_content, PromptEngineConfig, PromptEngine
from langchain.schema import HumanMessage, AIMessage
import logging  # Use built-in logging module
from code_interpreter import generate_visualization_response_sync  # Import the function


# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)





class Lenox:
    def __init__(self, tools, document_handler, prompt_engine=None, connection_string="sqlite:///lenox.db", openai_api_key=None):
        self.document_handler = document_handler
        self.prompt_engine = prompt_engine if prompt_engine else PromptEngine(config=PromptEngineConfig(), tools=tools)
        self.memory = SQLChatMessageHistory(session_id="my_session", connection_string=connection_string)
        self.openai_api_key = openai_api_key  # Save the API key
        self.db_path = 'lenox.db'
        self.gpt_research_manager = GPTResearchManager()
        self.intent_detector = IntentDetector(self.prompt_engine, self.gpt_research_manager)  # Corrected attribute name
        self.setup_components(tools)
        self._init_feedback_table()

    def setup_components(self, tools):
        self.functions = [convert_to_openai_function(f) for f in tools]
        self.model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0.8).bind(functions=self.functions)
        self.prompt = self.configure_prompts()
        self.chain = self.setup_chain()
        self.qa = AgentExecutor(agent=self.chain, tools=tools, verbose=False)

    def setup_chain(self):
        """Set up the agent chain."""
        return (
            RunnablePassthrough.assign(
                agent_scratchpad=lambda x: format_to_openai_functions(x.get("intermediate_steps", []))
            )
            | self.prompt
            | self.model
            | OpenAIFunctionsAgentOutputParser()
        )

    def configure_prompts(self, context_messages: Optional[List[str]] = None, user_query: str = ""):
        """Configure the prompt template with dynamic context."""
        # Filter out non-string elements from context_messages
        if context_messages:
            context_messages = [msg for msg in context_messages if isinstance(msg, str)]
        
        context = "\n".join(context_messages) if context_messages else ""
        full_prompt = f"{context}\n\nUser: {user_query}\nAI:"
        logger.debug(f"Configuring prompt with context: {context} and user query: {user_query}")
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt_content),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", full_prompt),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    def convchain(self, query: str, session_id: str = "my_session") -> dict:
        """Process a user query."""
        if not query:
            return {"type": "text", "content": "Please enter a query."}

        logger.debug(f"Received query: {query}")

        # Detect intent and handle it using the IntentDetector
        detected_intent = self.intent_detector.detect_intent(query)
        if detected_intent in self.intent_detector.intent_handlers:
            # If the detected intent has a specific handler, use it
            response = self.intent_detector.handle_intent(detected_intent, query)
            output = response.get('content', 'Error processing the request.')
            response_type = response.get('type', 'text')
        elif self.is_visualization_query(query):
            # Handle visualization queries
            response = self.handle_visualization_query(query)
            output = response.get('content', 'Error processing the request.')
            response_type = response.get('type', 'visualization')
        else:
            # General conversational handling
            self.memory.session_id = session_id
            new_message = HumanMessage(content=query)
            self.memory.add_message(new_message)
            chat_history = self.memory.messages()

            logger.debug(f"Chat history: {chat_history}")

            # Ensure chat_history is a list of strings
            chat_history_contents = [msg.content for msg in chat_history if isinstance(msg.content, str)]
            self.prompt = self.configure_prompts(context_messages=chat_history_contents, user_query=query)
            result = self.qa.invoke({"input": query, "chat_history": chat_history})
            output = result.get('output', 'Error processing the request.')
            response_type = 'text'

        logger.debug(f"Generated output: {output}")

        # Ensure output is a string
        if not isinstance(output, str):
            output = str(output)

        self.memory.add_message(AIMessage(content=output))
        return {"type": response_type, "content": output}

   
   
    def is_visualization_query(self, query: str) -> bool:
        """Identify visualization-based queries."""
        visualization_keywords = ["visualize", "graph", "chart", "plot", "show me a graph of", "display data"]
        return any(keyword in query.lower() for keyword in visualization_keywords)

    def parse_visualization_type(self, query: str) -> str:
        """Parse the type of visualization requested."""
        visualization_keywords = {
            'line': ['line', 'linear'],
            'bar': ['bar', 'column'],
            'scatter': ['scatter', 'point'],
            'pie': ['pie', 'circle']
        }
        for vis_type, keywords in visualization_keywords.items():
            if any(keyword in query.lower() for keyword in keywords):
                return vis_type
        return 'line'  # Default to line if unspecified

    def fetch_data_for_visualization(self, query: str) -> Dict[str, Union[List[int], List[str]]]:
        """Extract data for visualization."""
        numbers = [int(s) for s in query.split() if s.isdigit()]
        if numbers:
            return {'x': list(range(1, len(numbers) + 1)), 'y': numbers}
        else:
            return {'x': [1, 2, 3, 4], 'y': [10, 11, 12, 13]}

    def handle_visualization_query(self, query: str) -> dict:
        try:
            img_base64 = generate_visualization_response_sync(query)
            if img_base64:
                return {"type": "visualization", "content": img_base64}
            else:
                return {"type": "error", "content": "Failed to generate visualization."}
        except Exception as e:
            logger.error(f"Error in handle_visualization_query: {str(e)}")
            return {"type": "error", "content": "An error occurred while generating visualization."}

        
        

    def handle_document_query(self, query: str) -> str:
        """Query the document index."""
        return self.document_handler.query(query)

    def synthesize_text(self, model, input_text, voice, response_format='mp3', speed=1):
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "input": input_text,
            "voice": voice,
            "response_format": response_format,
            "speed": speed
        }

        response = requests.post('https://api.openai.com/v1/audio/speech', headers=headers, json=data)

        if response.status_code == 200:
            audio_file_path = "output.mp3"
            with open(audio_file_path, 'wb') as f:
                f.write(response.content)
            return audio_file_path
        else:
            print(f"Failed to synthesize audio: {response.status_code}, {response.text}")
            return None

    def _init_feedback_table(self):
        # Initialize the feedback table if it does not exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS feedback (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            query TEXT NOT NULL,
                            feedback TEXT NOT NULL,
                            session_id TEXT NOT NULL
                        )''')
        conn.commit()
        conn.close()

    def teach_from_feedback(self, query: str, feedback: str, session_id: str) -> None:
        """
        Update the model or system based on user feedback.

        Parameters:
        - query (str): The query for which feedback is provided.
        - feedback (str): The feedback from the user.
        - session_id (str): The session ID of the user providing the feedback.
        """
        # Store feedback in the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO feedback (query, feedback, session_id) VALUES (?, ?, ?)', 
                       (query, feedback, session_id))
        conn.commit()
        conn.close()

    def process_feedback(self, feedback: str, session_id: str) -> str:
        """
        Process feedback in real-time.

        Parameters:
        - feedback (str): The feedback provided by the user.
        - session_id (str): The session ID of the user providing the feedback.

        Returns:
        - str: Response after processing feedback.
        """
        # Here you can add logic to process the feedback in real-time
        print(f"Processing feedback '{feedback}' for session '{session_id}'")
        return "Feedback processed successfully"