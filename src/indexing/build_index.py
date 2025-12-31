"""Build and persist vector index from PDF documents."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
import chromadb

from src.config import (
    DATA_DIR,
    CHROMA_DIR,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_REQUEST_TIMEOUT,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    CHROMA_COLLECTION_NAME,
)


def initialize_settings():
    """Initialize global LlamaIndex settings."""
    print(f"Initializing embedding model: {EMBEDDING_MODEL}")
    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)

    print(f"Initializing Ollama LLM: {OLLAMA_MODEL} at {OLLAMA_BASE_URL}")
    Settings.llm = Ollama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        request_timeout=OLLAMA_REQUEST_TIMEOUT,
    )

    Settings.chunk_size = CHUNK_SIZE
    Settings.chunk_overlap = CHUNK_OVERLAP


def load_documents():
    """Load PDF documents from data directory."""
    print(f"\nLoading PDFs from: {DATA_DIR}")

    if not DATA_DIR.exists():
        print(f"Error: Data directory does not exist: {DATA_DIR}")
        return []

    pdf_files = list(DATA_DIR.rglob("*.pdf"))
    if not pdf_files:
        print(f"Warning: No PDF files found in {DATA_DIR}")
        return []

    print(f"Found {len(pdf_files)} PDF files")

    # Load documents recursively
    reader = SimpleDirectoryReader(
        input_dir=str(DATA_DIR),
        recursive=True,
        required_exts=[".pdf"],
    )

    documents = reader.load_data()
    print(f"Loaded {len(documents)} document chunks")

    return documents


def create_vector_store():
    """Create or get ChromaDB vector store."""
    print(f"\nInitializing ChromaDB at: {CHROMA_DIR}")

    # Initialize ChromaDB client
    db = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Get or create collection
    chroma_collection = db.get_or_create_collection(CHROMA_COLLECTION_NAME)

    # Create vector store
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    return vector_store


def build_index(documents, vector_store):
    """Build vector index from documents."""
    print("\nBuilding vector index...")
    print("This may take a while depending on the number of documents...")

    # Create storage context
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Build index
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True,
    )

    print("Index built successfully!")
    return index


def main():
    """Main indexing pipeline."""
    print("=" * 60)
    print("PDF Indexing Pipeline")
    print("=" * 60)

    # Initialize settings
    initialize_settings()

    # Load documents
    documents = load_documents()
    if not documents:
        print("\nNo documents to index. Exiting.")
        return

    # Create vector store
    vector_store = create_vector_store()

    # Build and persist index
    index = build_index(documents, vector_store)

    print("\n" + "=" * 60)
    print("Indexing complete!")
    print(f"Vector store persisted to: {CHROMA_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
