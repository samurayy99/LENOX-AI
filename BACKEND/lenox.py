import sqlite3
from typing import List, Optional
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain.schema.runnable import RunnablePassthrough
from langchain.agents.format_scratchpad import format_to_openai_functions
import requests
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from gpt_research_tools import GPTResearchManager
from intent_detection import IntentDetector, IntentType
# Import system prompt content from prompts.py
from prompts import system_prompt_content, PromptEngineConfig, PromptEngine
import logging  # Use built-in logging module
from code_interpreter import generate_visualization_response_sync
from lenox_opinion import generate_lenox_opinion


# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)





class Lenox:
    def __init__(self, tools, chart_analyzer, prompt_engine=None, connection_string="sqlite:///lenox.db", openai_api_key=None):
        self.chart_analyzer = chart_analyzer
        self.prompt_engine = prompt_engine if prompt_engine else PromptEngine(config=PromptEngineConfig(), tools=tools)
        summarization_llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        self.conversation_buffer = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.openai_api_key = openai_api_key  # Save the API key
                # Initialize ConversationSummaryBufferMemory with the llm parameter
        self.memory = ConversationSummaryBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            llm=summarization_llm  # Add this line
        )
        self.db_path = 'lenox.db'
        self.gpt_research_manager = GPTResearchManager()
        self.intent_detector = IntentDetector(self.prompt_engine, self.gpt_research_manager)  # Corrected attribute name
        self.setup_components(tools)
        self._init_feedback_table()

    def setup_components(self, tools):
        self.functions = [convert_to_openai_function(f) for f in tools]
        self.model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7).bind(functions=self.functions)
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
        
    def analyze_chart_with_recommendation(self, chart_data, additional_input=""):
        # Perform the chart analysis
        analysis_result = self.chart_analyzer.analyze(chart_data)
        
        # Generate AI opinion and recommendation
        opinion_and_recommendation = generate_lenox_opinion(analysis_result, additional_input, self)
        
        return opinion_and_recommendation
    

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
        
        
    def get_dynamic_temperature(self, query: str) -> float:
        if any(keyword in query.lower() for keyword in ['price', 'market data', 'regulation', 'explain']):
            return 0.3
        elif any(keyword in query.lower() for keyword in ['predict', 'trend', 'future', 'opinion']):
            return 0.7
        else:
            return 0.6
        
        
    def convchain(self, query: str, session_id: str = "my_session") -> dict:
        if not query:
            return {"type": "text", "content": "Please enter a query."}

        logger.debug(f"Received query: {query}")

        # Detect intent
        detected_intent = self.intent_detector.detect_intent(query)
        logger.debug(f"Detected intent: {detected_intent}")

        # Handle GPT Research intent
        if detected_intent == IntentType.GPT_RESEARCH:
            result = self.gpt_research_manager.run_gpt_research(query)
            research_content = result.get('content', 'Error processing the research request.')

            # Add research result to conversation buffer and memory
            self.conversation_buffer.chat_memory.add_user_message(query)
            self.conversation_buffer.chat_memory.add_ai_message(research_content)
            self.memory.chat_memory.add_user_message(query)
            self.memory.chat_memory.add_ai_message(research_content)

            return result

        # Handle visualization intent
        if detected_intent == IntentType.VISUALIZATION:
            try:
                result = generate_visualization_response_sync(query)
                logger.debug(f"Visualization result: {result}")
                return result
            except Exception as e:
                logger.error(f"Error generating visualization: {e}")
                return {"type": "error", "content": str(e)}

        # Update conversation buffer and memory
        self.conversation_buffer.chat_memory.add_user_message(query)
        self.memory.chat_memory.add_user_message(query)

        # Retrieve recent conversation history
        chat_history = self.memory.load_memory_variables({})["chat_history"]

        # Ensure chat_history is a list of strings
        chat_history_contents = [str(msg) for msg in chat_history if msg is not None]

        # Configure prompt with chat history
        prompt = self.configure_prompts(context_messages=chat_history_contents, user_query=query)

        # Set dynamic temperature
        dynamic_temp = self.get_dynamic_temperature(query)
        self.model = ChatOpenAI(model="gpt-4o-mini", temperature=dynamic_temp).bind(functions=self.functions)
        self.prompt_engine.set_temperature(dynamic_temp)

        # Generate response
        result = self.qa.invoke(
            {"input": prompt, "chat_history": chat_history_contents},
            config={"configurable": {"session_id": session_id}}
        )

        output = result.get('output', 'Error processing the request.')

        # Add AI response to conversation buffer and memory
        self.conversation_buffer.chat_memory.add_ai_message(output)
        self.memory.chat_memory.add_ai_message(output)

        # Ensure output is a string
        if not isinstance(output, str):
            output = str(output)

        return {"type": "text", "content": output}
    

    def construct_prompt(self, query, summarized_history):
        # Construct a more informative prompt using the query and summarized history
        return f"Given the following conversation summary:\n{summarized_history}\n\nUser query: {query}\n\nPlease provide a relevant and context-aware response:"
    

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
                    logger.info(f"Positive feedback received for query: {query} (Session: {session_id})")
                    # Example: You could update a weight or score for this response
                    # self.update_response_score(query, 1, session_id)
                elif feedback == 'negative':
                    # Logic to learn from negative feedback
                    logger.info(f"Negative feedback received for query: {query} (Session: {session_id})")
                    # Example: You could decrease a weight or score for this response
                    # self.update_response_score(query, -1, session_id)
                else:
                    logger.warning(f"Unknown feedback type received: {feedback} (Session: {session_id})")

                # Add your logic here to use this feedback for improving future responses
                # This could involve updating a machine learning model, adjusting response templates, etc.

                return "Feedback processed successfully"
            except Exception as e:
                logger.error(f"Error processing feedback: {e} (Session: {session_id})")
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