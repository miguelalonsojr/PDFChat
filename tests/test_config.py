"""Tests for configuration module."""
import os
import pytest
from pathlib import Path

from src import config


@pytest.mark.unit
class TestConfig:
    """Test configuration settings."""

    def test_project_root_exists(self):
        """Test that project root path exists."""
        assert config.PROJECT_ROOT.exists()
        assert config.PROJECT_ROOT.is_dir()

    def test_data_dir_created(self):
        """Test that data directory is created."""
        assert config.DATA_DIR.exists()
        assert config.DATA_DIR.is_dir()

    def test_storage_dir_created(self):
        """Test that storage directory is created."""
        assert config.STORAGE_DIR.exists()
        assert config.STORAGE_DIR.is_dir()

    def test_chroma_dir_created(self):
        """Test that ChromaDB directory is created."""
        assert config.CHROMA_DIR.exists()
        assert config.CHROMA_DIR.is_dir()

    def test_cache_dir_created(self):
        """Test that cache directory is created."""
        assert config.CACHE_DIR.exists()
        assert config.CACHE_DIR.is_dir()

    def test_ollama_base_url_default(self, monkeypatch):
        """Test Ollama base URL default value."""
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        # Need to reload config module to pick up env changes
        import importlib
        importlib.reload(config)
        assert config.OLLAMA_BASE_URL == "http://localhost:11434"

    def test_ollama_base_url_from_env(self, monkeypatch):
        """Test Ollama base URL from environment variable."""
        test_url = "http://test:11434"
        monkeypatch.setenv("OLLAMA_BASE_URL", test_url)
        import importlib
        importlib.reload(config)
        assert config.OLLAMA_BASE_URL == test_url

    def test_ollama_model_default(self):
        """Test Ollama model default value."""
        assert isinstance(config.OLLAMA_MODEL, str)
        assert len(config.OLLAMA_MODEL) > 0

    def test_ollama_request_timeout(self):
        """Test Ollama request timeout is set."""
        assert config.OLLAMA_REQUEST_TIMEOUT > 0
        assert isinstance(config.OLLAMA_REQUEST_TIMEOUT, float)

    def test_embedding_model_default(self):
        """Test embedding model default value."""
        assert isinstance(config.EMBEDDING_MODEL, str)
        assert len(config.EMBEDDING_MODEL) > 0

    def test_embed_batch_size(self):
        """Test embedding batch size is positive."""
        assert config.EMBED_BATCH_SIZE > 0
        assert isinstance(config.EMBED_BATCH_SIZE, int)

    def test_chunk_size(self):
        """Test chunk size is positive."""
        assert config.CHUNK_SIZE > 0
        assert isinstance(config.CHUNK_SIZE, int)

    def test_chunk_overlap(self):
        """Test chunk overlap is positive and less than chunk size."""
        assert config.CHUNK_OVERLAP > 0
        assert config.CHUNK_OVERLAP < config.CHUNK_SIZE
        assert isinstance(config.CHUNK_OVERLAP, int)

    def test_similarity_top_k(self):
        """Test similarity top_k is positive."""
        assert config.SIMILARITY_TOP_K > 0
        assert isinstance(config.SIMILARITY_TOP_K, int)

    def test_flask_host_default(self):
        """Test Flask host default value."""
        assert isinstance(config.FLASK_HOST, str)
        assert len(config.FLASK_HOST) > 0

    def test_flask_port_default(self):
        """Test Flask port default value."""
        assert isinstance(config.FLASK_PORT, int)
        assert 1 <= config.FLASK_PORT <= 65535

    def test_flask_port_from_env(self, monkeypatch):
        """Test Flask port from environment variable."""
        monkeypatch.setenv("FLASK_PORT", "8080")
        import importlib
        importlib.reload(config)
        assert config.FLASK_PORT == 8080

    def test_flask_debug_is_bool(self):
        """Test Flask debug is boolean."""
        assert isinstance(config.FLASK_DEBUG, bool)

    def test_chroma_collection_name(self):
        """Test ChromaDB collection name is set."""
        assert isinstance(config.CHROMA_COLLECTION_NAME, str)
        assert len(config.CHROMA_COLLECTION_NAME) > 0

    def test_app_title_default(self):
        """Test app title default value."""
        assert isinstance(config.APP_TITLE, str)
        assert len(config.APP_TITLE) > 0

    def test_app_subtitle_default(self):
        """Test app subtitle default value."""
        assert isinstance(config.APP_SUBTITLE, str)
        assert len(config.APP_SUBTITLE) > 0

    def test_database_dir_exists(self):
        """Test that database directory path is defined."""
        assert hasattr(config, "DATABASE_DIR")
        assert isinstance(config.DATABASE_DIR, Path)
