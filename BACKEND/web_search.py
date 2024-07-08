import os
import logging
from datetime import datetime
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI  # Updated import
from langchain.agents import initialize_agent, AgentType
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import DocumentCompressorPipeline, EmbeddingsFilter
from langchain_openai import OpenAIEmbeddings  # Updated import
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from tavily import TavilyClient






# Load environment variables from .env file
load_dotenv()

# Ensure the API key is loaded from environment variables
tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    raise ValueError("TAVILY_API_KEY environment variable is not set.")
os.environ["TAVILY_API_KEY"] = tavily_api_key


# Initialize TavilyClient
tavily_client = TavilyClient(api_key=tavily_api_key)

# Define the system prompt content for web_search
RESPONSE_TEMPLATE = """\
You are Lenox, a specialized digital assistant with expertise in the cryptocurrency market. Your role is to deliver precise and well-analyzed answers by synthesizing information from diverse web sources. Here’s how you should approach this:

- **Expert Analysis**: Draw deeply on your understanding of cryptocurrency dynamics to analyze search results. Utilize analytical tools to highlight essential data and trends.

- **Conciseness and Precision**: Ensure your answers are succinct and focused directly on the query. Avoid unnecessary details that don't serve the user's specific question.

- **Data Synthesis**: Seamlessly integrate information from multiple sources to create a coherent response. Your ability to connect disparate data points is crucial in delivering useful insights.

- **Clear Citation**: Maintain transparency by clearly citing your sources with precise notation. This practice allows users to trace information back to its origin, fostering trust and reliability.

- **Focused Tool Utilization**: Expertly navigate the Tavily search tool to retrieve the most relevant and accurate information available. Your adept use of this tool is essential in answering queries effectively.

REMEMBER: Your primary goal is to equip users with accurate, relevant, and timely information, enabling them to make well-informed decisions in the cryptocurrency space.
"""



def get_retriever():
    embeddings = OpenAIEmbeddings()
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=20)
    relevance_filter = EmbeddingsFilter(embeddings=embeddings, similarity_threshold=0.8)
    pipeline_compressor = DocumentCompressorPipeline(
        transformers=[splitter, relevance_filter]
    )
    base_tavily_retriever = TavilySearchAPIRetriever()
    tavily_retriever = ContextualCompressionRetriever(
        base_compressor=pipeline_compressor, base_retriever=base_tavily_retriever
    )
    return tavily_retriever


class WebSearchManager:
    def __init__(self):
        # Set up the agent
        self.llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0.1)
        self.retriever = get_retriever()
        self.tavily_tool = TavilySearchResults()
        
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", RESPONSE_TEMPLATE),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ]
        ).partial(current_date=datetime.now().isoformat())
        
        self.agent_chain = initialize_agent(
            tools=[self.tavily_tool],
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            prompt=self.prompt,
            verbose=True,
        )

        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)

    def run_search(self, query: str) -> dict:
        try:
            response = self.agent_chain.run({"input": query})
            self.logger.debug(f"Raw Tavily response: {response}")
            return {"type": "text", "content": response}
        except Exception as e:
            self.logger.error(f"Error using Tavily: {str(e)}")
            return {"type": "text", "content": f"Error using Tavily: {str(e)}"}