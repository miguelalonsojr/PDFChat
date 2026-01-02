"""Shared pytest fixtures for PDFChat tests."""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
import sqlite3

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.app import create_app
from src.models import ConversationDB


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_db_path(temp_dir):
    """Create a temporary database path."""
    return temp_dir / "test_conversations.db"


@pytest.fixture
def conversation_db(test_db_path):
    """Create a test database instance."""
    db = ConversationDB(db_path=test_db_path)
    yield db
    # Cleanup is handled by temp_dir fixture


@pytest.fixture
def app(monkeypatch, temp_dir):
    """Create a Flask test application."""
    # Set test environment variables
    test_storage = temp_dir / "storage"
    test_storage.mkdir(exist_ok=True)

    monkeypatch.setenv("FLASK_DEBUG", "False")

    # Mock the agent to avoid needing Ollama running
    mock_agent = Mock()
    mock_agent.query.return_value = "Test response"
    mock_agent.reset_chat.return_value = None

    # Create mock streaming response
    mock_stream_response = MagicMock()
    mock_stream_response.response_gen = iter(["Test", " streaming", " response"])
    mock_stream_response.source_nodes = []
    mock_agent.chat.return_value = mock_stream_response

    # Patch get_agent to return our mock
    def mock_get_agent():
        return mock_agent

    monkeypatch.setattr("src.api.app.get_agent", mock_get_agent)

    # Create test database for conversations
    test_db = test_storage / "conversations" / "conversations.db"
    test_db.parent.mkdir(parents=True, exist_ok=True)

    # Patch get_db to use test database
    def mock_get_db():
        return ConversationDB(db_path=test_db)

    monkeypatch.setattr("src.api.app.get_db", mock_get_db)

    app = create_app()
    app.config["TESTING"] = True

    yield app


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    return app.test_client()


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    mock = Mock()
    mock.complete.return_value = Mock(text="Test completion")
    mock.chat.return_value = Mock(message=Mock(content="Test chat response"))
    return mock


@pytest.fixture
def mock_embed_model():
    """Create a mock embedding model for testing."""
    mock = Mock()
    mock.get_text_embedding.return_value = [0.1] * 384  # Standard embedding size
    return mock


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store for testing."""
    mock = Mock()
    mock.query.return_value = Mock(
        nodes=[
            Mock(
                text="Test document content",
                metadata={"file_name": "test.pdf", "page_label": "1", "file_path": "/test/test.pdf"}
            )
        ]
    )
    return mock


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing."""
    return {
        "title": "Test Conversation",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
    }
