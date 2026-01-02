"""Tests for QA agent."""
import pytest
from unittest.mock import Mock, MagicMock, patch

from src.agents.qa_agent import QAAgent, get_agent


@pytest.mark.unit
class TestQAAgent:
    """Test QAAgent class."""

    @patch("src.agents.qa_agent.chromadb.PersistentClient")
    @patch("src.agents.qa_agent.VectorStoreIndex")
    @patch("src.agents.qa_agent.Settings")
    def test_init_success(self, mock_settings, mock_index, mock_chromadb):
        """Test successful initialization of QAAgent."""
        # Setup mocks
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.get_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_db

        mock_vector_index = Mock()
        mock_index.from_vector_store.return_value = mock_vector_index

        # Create agent
        agent = QAAgent()

        # Verify initialization
        assert agent is not None
        assert agent.index is not None
        assert agent.query_engine is not None
        assert agent.chat_engine is not None

    @patch("src.agents.qa_agent.chromadb.PersistentClient")
    @patch("src.agents.qa_agent.Settings")
    def test_init_collection_not_found(self, mock_settings, mock_chromadb):
        """Test initialization when collection doesn't exist."""
        # Setup mock to raise exception
        mock_db = Mock()
        mock_db.get_collection.side_effect = Exception("Collection not found")
        mock_chromadb.return_value = mock_db

        # Should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            QAAgent()

        assert "Failed to load collection" in str(exc_info.value)

    @patch("src.agents.qa_agent.chromadb.PersistentClient")
    @patch("src.agents.qa_agent.VectorStoreIndex")
    @patch("src.agents.qa_agent.Settings")
    def test_query(self, mock_settings, mock_index, mock_chromadb):
        """Test query method."""
        # Setup mocks
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.get_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_db

        mock_vector_index = Mock()
        mock_query_engine = Mock()
        mock_response = Mock()
        mock_response.__str__ = Mock(return_value="Test answer")

        mock_query_engine.query.return_value = mock_response
        mock_vector_index.as_query_engine.return_value = mock_query_engine
        mock_index.from_vector_store.return_value = mock_vector_index

        # Create agent and query
        agent = QAAgent()
        answer = agent.query("What is this?")

        assert answer == "Test answer"
        mock_query_engine.query.assert_called_once_with("What is this?")

    @patch("src.agents.qa_agent.chromadb.PersistentClient")
    @patch("src.agents.qa_agent.VectorStoreIndex")
    @patch("src.agents.qa_agent.Settings")
    def test_chat(self, mock_settings, mock_index, mock_chromadb):
        """Test chat method."""
        # Setup mocks
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.get_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_db

        mock_vector_index = Mock()
        mock_chat_engine = Mock()
        mock_stream_response = Mock()
        mock_stream_response.response_gen = iter(["Hello", " there"])

        mock_chat_engine.stream_chat.return_value = mock_stream_response
        mock_vector_index.as_chat_engine.return_value = mock_chat_engine
        mock_index.from_vector_store.return_value = mock_vector_index

        # Create agent and chat
        agent = QAAgent()
        response = agent.chat("Hi")

        assert response is not None
        mock_chat_engine.stream_chat.assert_called_once_with("Hi")

    @patch("src.agents.qa_agent.chromadb.PersistentClient")
    @patch("src.agents.qa_agent.VectorStoreIndex")
    @patch("src.agents.qa_agent.Settings")
    def test_reset_chat(self, mock_settings, mock_index, mock_chromadb):
        """Test reset_chat method."""
        # Setup mocks
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.get_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_db

        mock_vector_index = Mock()
        mock_chat_engine = Mock()
        mock_vector_index.as_chat_engine.return_value = mock_chat_engine
        mock_index.from_vector_store.return_value = mock_vector_index

        # Create agent and reset
        agent = QAAgent()
        agent.reset_chat()

        mock_chat_engine.reset.assert_called_once()

    @patch("src.agents.qa_agent.chromadb.PersistentClient")
    @patch("src.agents.qa_agent.VectorStoreIndex")
    @patch("src.agents.qa_agent.Settings")
    def test_initialize_settings(self, mock_settings, mock_index, mock_chromadb):
        """Test that settings are initialized correctly."""
        # Setup mocks
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.get_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_db

        mock_vector_index = Mock()
        mock_index.from_vector_store.return_value = mock_vector_index

        # Create agent
        agent = QAAgent()

        # Verify settings were set
        assert mock_settings.embed_model is not None
        assert mock_settings.llm is not None
        assert mock_settings.chunk_size is not None
        assert mock_settings.chunk_overlap is not None

    @patch("src.agents.qa_agent.chromadb.PersistentClient")
    @patch("src.agents.qa_agent.VectorStoreIndex")
    @patch("src.agents.qa_agent.Settings")
    def test_create_query_engine_with_config(self, mock_settings, mock_index, mock_chromadb):
        """Test that query engine is created with correct configuration."""
        # Setup mocks
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.get_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_db

        mock_vector_index = Mock()
        mock_index.from_vector_store.return_value = mock_vector_index

        # Create agent
        agent = QAAgent()

        # Verify query engine was created with correct parameters
        mock_vector_index.as_query_engine.assert_called_once()
        call_kwargs = mock_vector_index.as_query_engine.call_args[1]
        assert "similarity_top_k" in call_kwargs
        assert call_kwargs["streaming"] is False

    @patch("src.agents.qa_agent.chromadb.PersistentClient")
    @patch("src.agents.qa_agent.VectorStoreIndex")
    @patch("src.agents.qa_agent.Settings")
    def test_create_chat_engine_with_system_prompt(self, mock_settings, mock_index, mock_chromadb):
        """Test that chat engine is created with system prompt."""
        # Setup mocks
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.get_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_db

        mock_vector_index = Mock()
        mock_index.from_vector_store.return_value = mock_vector_index

        # Create agent
        agent = QAAgent()

        # Verify chat engine was created with correct parameters
        mock_vector_index.as_chat_engine.assert_called_once()
        call_kwargs = mock_vector_index.as_chat_engine.call_args[1]
        assert "similarity_top_k" in call_kwargs
        assert call_kwargs["streaming"] is True
        assert call_kwargs["chat_mode"] == "condense_plus_context"
        assert "system_prompt" in call_kwargs
        assert len(call_kwargs["system_prompt"]) > 0


@pytest.mark.unit
class TestGetAgent:
    """Test get_agent function."""

    @patch("src.agents.qa_agent.chromadb.PersistentClient")
    @patch("src.agents.qa_agent.VectorStoreIndex")
    @patch("src.agents.qa_agent.Settings")
    def test_get_agent_singleton(self, mock_settings, mock_index, mock_chromadb):
        """Test that get_agent returns a singleton."""
        # Setup mocks
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.get_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_db

        mock_vector_index = Mock()
        mock_index.from_vector_store.return_value = mock_vector_index

        # Reset global instance
        import src.agents.qa_agent
        src.agents.qa_agent._agent_instance = None

        # Get agent twice
        agent1 = get_agent()
        agent2 = get_agent()

        # Should be the same instance
        assert agent1 is agent2

    @patch("src.agents.qa_agent.chromadb.PersistentClient")
    @patch("src.agents.qa_agent.VectorStoreIndex")
    @patch("src.agents.qa_agent.Settings")
    def test_get_agent_creates_new_instance(self, mock_settings, mock_index, mock_chromadb):
        """Test that get_agent creates a new instance if none exists."""
        # Setup mocks
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.get_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_db

        mock_vector_index = Mock()
        mock_index.from_vector_store.return_value = mock_vector_index

        # Reset global instance
        import src.agents.qa_agent
        src.agents.qa_agent._agent_instance = None

        # Get agent
        agent = get_agent()

        assert agent is not None
        assert isinstance(agent, QAAgent)


@pytest.mark.slow
@pytest.mark.integration
class TestQAAgentIntegration:
    """Integration tests for QAAgent (requires real setup)."""

    @pytest.mark.skip(reason="Requires ChromaDB and Ollama running")
    def test_real_query(self):
        """Test real query against actual index (skipped by default)."""
        agent = QAAgent()
        answer = agent.query("What is the main topic of the documents?")
        assert len(answer) > 0

    @pytest.mark.skip(reason="Requires ChromaDB and Ollama running")
    def test_real_chat(self):
        """Test real chat against actual index (skipped by default)."""
        agent = QAAgent()
        response = agent.chat("Hello, what can you tell me?")
        assert response is not None
