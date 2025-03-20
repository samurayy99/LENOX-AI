from typing import List, Optional
from langchain.agents import tool
from langchain_openai import OpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain.chains.question_answering import load_qa_chain
import scrapetube
import logging
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Global embedding instance for reuse
_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings


@tool
def search_youtube(query: str, max_results: int = 5) -> str:
    """
    Searches YouTube for videos matching the query and returns a list of video titles and URLs.

    Args:
        query (str): The search query string.
        max_results (int): Maximum number of search results to return.

    Returns:
        str: A formatted string containing titles and URLs of the top search results.
    """
    try:
        videos = scrapetube.get_search(query, limit=max_results)
        results = []
        for video in videos:
            title = video.get('title', 'No title')
            video_id = video.get('videoId', 'No video ID')
            results.append(f"Title: {title}\nURL: https://www.youtube.com/watch?v={video_id}")
        
        if not results:
            return "No videos found."
            
        return "\n\n".join(results)
    except Exception as e:
        return f"Error searching YouTube: {str(e)}"


@tool
def process_youtube_video(url: str) -> List[Document]:
    """
    Processes a YouTube video URL and extracts its content for further analysis.

    Args:
        url (str): The URL of the YouTube video.

    Returns:
        List[Document]: A list of documents representing the video content.
    """
    try:
        logger.debug(f"Processing YouTube video URL: {url}")
        
        # Extract video ID from URL
        video_id = url.split("v=")[1] if "v=" in url else url.split("/")[-1]
        
        # Get video info
        yt = YouTube(url)
        title = yt.title
        description = yt.description
        
        # Get transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([entry['text'] for entry in transcript])
        
        # Create document
        document = Document(
            page_content=f"Title: {title}\n\nDescription: {description}\n\nTranscript: {transcript_text}",
            metadata={"source": url, "title": title}
        )
        
        logger.debug(f"Processed video: {title}")
        return [document]
    except Exception as e:
        logger.error(f"Error processing YouTube video: {str(e)}")
        return [Document(page_content=f"Error processing video: {str(e)}", metadata={"source": url})]



@tool
def query_youtube_video(url_or_query: str, question: Optional[str] = None) -> str:
    """
    Performs a question-answering query on the content of a YouTube video.
    If a query is provided instead of a URL, it first searches for the video.

    Args:
        url_or_query (str): The URL of the YouTube video or a search query.
        question (Optional[str]): The question to ask about the video content. If None, summarize the video.

    Returns:
        str: The answer to the question based on the video content or search results.
    """
    try:
        url: Optional[str] = None
        formatted_results: Optional[str] = None

        if not url_or_query.startswith('http'):
            # This is a search query
            search_results = search_youtube(url_or_query)
            formatted_results = search_results
            url = search_results.split('\n')[1].split(': ')[1] if search_results != "No videos found." else None
            if not url:
                return f"Search results:\n\n{formatted_results}\n\nNo videos found to analyze."
            logger.debug(f"Search results:\n{formatted_results}")
            logger.debug(f"Analyzing first video: {url}")
        else:
            url = url_or_query

        if url is None:
            return "Error: No valid URL found to analyze."

        documents = process_youtube_video(url)
        if not documents or "Error" in documents[0].page_content:
            return f"Failed to retrieve video content for URL: {url}"

        llm = OpenAI(temperature=0)
        chain = load_qa_chain(llm, chain_type="default")
        if question is None:
            question = "Summarize the main points of this video."
        output = chain.run(input_documents=documents, question=question)
        
        response = f"Video URL: {url}\n\n"
        if formatted_results:
            response += f"Search results:\n\n{formatted_results}\n\n"
        response += f"Analysis:\n{output}"
        
        return response
    except Exception as e:
        logger.error(f"Error querying YouTube video: {str(e)}")
        return f"Error querying YouTube video: {str(e)}"


class YouTubeQA:
    def __init__(self):
        """
        Initializes the YouTubeQA class for processing and querying YouTube videos.
        """
        self.llm = OpenAI(temperature=0)
        self.embeddings = get_embeddings()
        self.db = None  # Placeholder for Chroma instance
        self.chain = None  # Placeholder for QA chain
        
        

    @tool
    def ingest_video(self, url: str) -> str:
        """
        Ingests a YouTube video, processes its content, and prepares it for question-answering.

        Args:
            url (str): The URL of the YouTube video to be ingested.

        Returns:
            str: A confirmation message indicating successful ingestion.
        """
        try:
            documents = process_youtube_video(url)
            # Use persistent storage for Chroma to avoid regenerating embeddings
            persist_directory = os.path.join(os.getcwd(), "chroma_db")
            self.db = Chroma.from_documents(
                documents, 
                self.embeddings,
                persist_directory=persist_directory
            ).as_retriever()
            self.chain = load_qa_chain(self.llm, chain_type="default")
            return "Video content successfully ingested and prepared for question-answering."
        except Exception as e:
            return f"Error ingesting YouTube video: {str(e)}"

    @tool
    def answer_question(self, question: str) -> str:
        """
        Answers a question based on the ingested YouTube video content.

        Args:
            question (str): The question to be answered.

        Returns:
            str: The answer to the question, or an error message if the video has not been ingested.
        """
        if not self.chain or not self.db:
            return "Please ingest a video first using the ingest_video method."
        
        try:
            docs = self.db.get_relevant_documents(question)
            output = self.chain.run(input_documents=docs, question=question)
            return output
        except Exception as e:
            return f"Error answering question: {str(e)}"