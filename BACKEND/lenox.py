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
    def __init__(self, tools, chart_analyzer, prompt_engine=None, connection_string="sqlite:///lenox.db", openai_api_key=None):
        self.chart_analyzer = chart_analyzer
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

        
        

    # Update any methods that were using document_handler to use chart_analyzer instead
    def handle_document_query(self, query, filename):
        return self.chart_analyzer.query(query, filename)

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
        """Initialize the feedback table if it does not exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''CREATE TABLE IF NOT EXISTS feedback (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    query TEXT NOT NULL,
                                    feedback TEXT NOT NULL,
                                    session_id TEXT NOT NULL,
                                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                                )''')
            logger.info("Feedback table initialized successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error initializing feedback table: {e}")

    def teach_from_feedback(self, query: str, feedback: str, session_id: str) -> None:
        """
        Store user feedback and update the model or system based on it.

        Parameters:
        - query (str): The query for which feedback is provided.
        - feedback (str): The feedback from the user ('positive' or 'negative').
        - session_id (str): The session ID of the user providing the feedback.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO feedback (query, feedback, session_id) VALUES (?, ?, ?)', 
                               (query, feedback, session_id))
            logger.info(f"Feedback stored for query: {query}")
            
            # Process feedback in real-time
            self.process_feedback(feedback, query, session_id)
        except sqlite3.Error as e:
            logger.error(f"Error storing feedback: {e}")

    def process_feedback(self, feedback: str, query: str, session_id: str) -> str:
        """
        Process feedback in real-time to improve the model.

        Parameters:
        - feedback (str): The feedback provided by the user ('positive' or 'negative').
        - query (str): The original query associated with the feedback.
        - session_id (str): The session ID of the user providing the feedback.

        Returns:
        - str: Response after processing feedback.
        """
        try:
            if feedback == 'positive':
                # Logic to reinforce good responses
                logger.info(f"Positive feedback received for query: {query}")
                # Example: You could update a weight or score for this response
                # self.update_response_score(query, 1)
            elif feedback == 'negative':
                # Logic to learn from negative feedback
                logger.info(f"Negative feedback received for query: {query}")
                # Example: You could decrease a weight or score for this response
                # self.update_response_score(query, -1)
            else:
                logger.warning(f"Unknown feedback type received: {feedback}")

            # Add your logic here to use this feedback for improving future responses
            # This could involve updating a machine learning model, adjusting response templates, etc.

            return "Feedback processed successfully"
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            return "Error processing feedback"

    def apply_feedback(self):
        """Periodically apply accumulated feedback to improve the model."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT query, feedback FROM feedback WHERE timestamp > date('now', '-7 days')")
                recent_feedback = cursor.fetchall()

            # Process recent feedback to improve your model
            positive_queries = []
            negative_queries = []
            for query, feedback in recent_feedback:
                if feedback == 'positive':
                    positive_queries.append(query)
                elif feedback == 'negative':
                    negative_queries.append(query)

            # Example: Update the model based on feedback
            if positive_queries:
                logger.info(f"Reinforcing model for {len(positive_queries)} positive queries")
                self.reinforce_positive_responses(positive_queries)

            if negative_queries:
                logger.info(f"Adjusting model for {len(negative_queries)} negative queries")
                self.adjust_negative_responses(negative_queries)

            logger.info("Applied recent feedback to improve the model")
        except sqlite3.Error as e:
            logger.error(f"Error applying feedback: {e}")

    def reinforce_positive_responses(self, queries):
        """
        Method to reinforce the model for queries that received positive feedback.
        Implement your logic here to improve the model for these queries.
        """
        # Example implementation:
        for query in queries:
            # You might update weights, adjust response templates, or fine-tune your model
            logger.info(f"Reinforcing model for query: {query}")
        # Add your specific implementation here

    def adjust_negative_responses(self, queries):
        """
        Method to adjust the model for queries that received negative feedback.
        Implement your logic here to improve responses for these queries in the future.
        """
        # Example implementation:
        for query in queries:
            # You might update weights, adjust response templates, or fine-tune your model
            logger.info(f"Adjusting model for query: {query}")
        # Add your specific implementation here
