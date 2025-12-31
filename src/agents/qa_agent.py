"""Q&A agent using LlamaIndex query engine."""
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
import chromadb

from src.config import (
    CHROMA_DIR,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_REQUEST_TIMEOUT,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    SIMILARITY_TOP_K,
    CHROMA_COLLECTION_NAME,
)


class QAAgent:
    """Question-answering agent with RAG capabilities."""

    def __init__(self):
        """Initialize the QA agent with vector store and query engine."""
        self._initialize_settings()
        self.index = self._load_index()
        self.query_engine = self._create_query_engine()
        self.chat_engine = self._create_chat_engine()

    def _initialize_settings(self):
        """Initialize global LlamaIndex settings."""
        Settings.embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)
        Settings.llm = Ollama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            request_timeout=OLLAMA_REQUEST_TIMEOUT,
        )
        Settings.chunk_size = CHUNK_SIZE
        Settings.chunk_overlap = CHUNK_OVERLAP

    def _load_index(self):
        """Load the vector index from ChromaDB."""
        # Initialize ChromaDB client
        db = chromadb.PersistentClient(path=str(CHROMA_DIR))

        # Get collection
        try:
            chroma_collection = db.get_collection(CHROMA_COLLECTION_NAME)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load collection '{CHROMA_COLLECTION_NAME}'. "
                f"Have you run the indexing script? Error: {e}"
            )

        # Create vector store
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

        # Load index
        index = VectorStoreIndex.from_vector_store(vector_store)

        return index

    def _create_query_engine(self):
        """Create a query engine for one-off questions."""
        return self.index.as_query_engine(
            similarity_top_k=SIMILARITY_TOP_K,
            streaming=False,
        )

    def _create_chat_engine(self):
        """Create a chat engine for conversational interactions."""
        return self.index.as_chat_engine(
            similarity_top_k=SIMILARITY_TOP_K,
            streaming=True,
            chat_mode="condense_plus_context",
        )

    def query(self, question: str) -> str:
        """
        Query the knowledge base with a single question.

        Args:
            question: The question to ask

        Returns:
            The answer as a string
        """
        response = self.query_engine.query(question)
        return str(response)

    def chat(self, message: str, chat_history=None):
        """
        Chat with the agent (supports conversation context).

        Args:
            message: The user message
            chat_history: Optional chat history (not currently used)

        Returns:
            Streaming response object
        """
        return self.chat_engine.stream_chat(message)

    def reset_chat(self):
        """Reset the chat history."""
        self.chat_engine.reset()


# Global agent instance
_agent_instance = None


def get_agent():
    """Get or create the global QA agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = QAAgent()
    return _agent_instance
