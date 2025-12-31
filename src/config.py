"""Configuration settings for PDFChat application."""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "pdfs"
STORAGE_DIR = PROJECT_ROOT / "storage"
CHROMA_DIR = STORAGE_DIR / "chroma_db"
CACHE_DIR = STORAGE_DIR / "index_cache"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi4-reasoning")
OLLAMA_REQUEST_TIMEOUT = 120.0

# Embedding settings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
EMBED_BATCH_SIZE = 10

# LlamaIndex settings
CHUNK_SIZE = 1024
CHUNK_OVERLAP = 200
SIMILARITY_TOP_K = 5

# Flask settings
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

# ChromaDB collection name
CHROMA_COLLECTION_NAME = "pdf_documents"

# UI settings
APP_TITLE = os.getenv("APP_TITLE", "PDFChat")
APP_SUBTITLE = os.getenv("APP_SUBTITLE", "Ask questions about your PDF documents")
