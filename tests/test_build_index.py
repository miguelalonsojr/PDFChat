"""Tests for indexing module."""
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from src.indexing import build_index


@pytest.mark.unit
class TestInitializeSettings:
    """Test initialize_settings function."""

    @patch("src.indexing.build_index.Settings")
    @patch("src.indexing.build_index.HuggingFaceEmbedding")
    @patch("src.indexing.build_index.Ollama")
    def test_initialize_settings(self, mock_ollama, mock_embedding, mock_settings):
        """Test that settings are initialized correctly."""
        build_index.initialize_settings()

        # Verify embedding model was created
        mock_embedding.assert_called_once()

        # Verify LLM was created
        mock_ollama.assert_called_once()

        # Verify settings were set
        assert mock_settings.embed_model is not None
        assert mock_settings.llm is not None
        assert mock_settings.chunk_size is not None
        assert mock_settings.chunk_overlap is not None


@pytest.mark.unit
class TestLoadDocuments:
    """Test load_documents function."""

    @patch("src.indexing.build_index.SimpleDirectoryReader")
    def test_load_documents_success(self, mock_reader, temp_dir):
        """Test loading documents successfully."""
        # Create a test PDF file
        test_pdf_dir = temp_dir / "pdfs"
        test_pdf_dir.mkdir()
        test_pdf = test_pdf_dir / "test.pdf"
        test_pdf.write_text("fake pdf content")

        # Mock the reader
        mock_reader_instance = Mock()
        mock_doc = Mock()
        mock_reader_instance.load_data.return_value = [mock_doc]
        mock_reader.return_value = mock_reader_instance

        # Patch DATA_DIR
        with patch("src.indexing.build_index.DATA_DIR", test_pdf_dir):
            documents = build_index.load_documents()

        assert len(documents) == 1
        mock_reader_instance.load_data.assert_called_once()

    def test_load_documents_no_data_dir(self, temp_dir):
        """Test loading documents when data directory doesn't exist."""
        non_existent_dir = temp_dir / "nonexistent"

        with patch("src.indexing.build_index.DATA_DIR", non_existent_dir):
            documents = build_index.load_documents()

        assert documents == []

    @patch("src.indexing.build_index.SimpleDirectoryReader")
    def test_load_documents_no_pdfs(self, mock_reader, temp_dir):
        """Test loading documents when no PDFs exist."""
        # Create empty directory
        pdf_dir = temp_dir / "pdfs"
        pdf_dir.mkdir()

        with patch("src.indexing.build_index.DATA_DIR", pdf_dir):
            documents = build_index.load_documents()

        assert documents == []

    @patch("src.indexing.build_index.SimpleDirectoryReader")
    def test_load_documents_recursive(self, mock_reader, temp_dir):
        """Test that documents are loaded recursively."""
        # Create nested PDF structure
        pdf_dir = temp_dir / "pdfs"
        pdf_dir.mkdir()
        sub_dir = pdf_dir / "subdir"
        sub_dir.mkdir()

        (pdf_dir / "test1.pdf").write_text("fake pdf 1")
        (sub_dir / "test2.pdf").write_text("fake pdf 2")

        # Mock the reader
        mock_reader_instance = Mock()
        mock_reader_instance.load_data.return_value = [Mock(), Mock()]
        mock_reader.return_value = mock_reader_instance

        with patch("src.indexing.build_index.DATA_DIR", pdf_dir):
            documents = build_index.load_documents()

        # Verify recursive=True was passed
        mock_reader.assert_called_once()
        call_kwargs = mock_reader.call_args[1]
        assert call_kwargs["recursive"] is True
        assert call_kwargs["required_exts"] == [".pdf"]


@pytest.mark.unit
class TestCreateVectorStore:
    """Test create_vector_store function."""

    @patch("src.indexing.build_index.chromadb.PersistentClient")
    @patch("src.indexing.build_index.ChromaVectorStore")
    def test_create_vector_store(self, mock_vector_store, mock_chromadb, temp_dir):
        """Test creating vector store."""
        # Mock ChromaDB client
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.get_or_create_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_db

        # Mock vector store
        mock_vs = Mock()
        mock_vector_store.return_value = mock_vs

        with patch("src.indexing.build_index.CHROMA_DIR", temp_dir):
            vector_store = build_index.create_vector_store()

        assert vector_store is not None
        mock_chromadb.assert_called_once()
        mock_db.get_or_create_collection.assert_called_once()
        mock_vector_store.assert_called_once_with(chroma_collection=mock_collection)


@pytest.mark.unit
class TestBuildIndex:
    """Test build_index function."""

    @patch("src.indexing.build_index.VectorStoreIndex")
    @patch("src.indexing.build_index.StorageContext")
    def test_build_index(self, mock_storage_context, mock_index):
        """Test building index from documents."""
        # Mock documents and vector store
        mock_docs = [Mock(), Mock()]
        mock_vector_store = Mock()

        # Mock storage context
        mock_ctx = Mock()
        mock_storage_context.from_defaults.return_value = mock_ctx

        # Mock index
        mock_idx = Mock()
        mock_index.from_documents.return_value = mock_idx

        result = build_index.build_index(mock_docs, mock_vector_store)

        assert result is not None
        mock_storage_context.from_defaults.assert_called_once_with(vector_store=mock_vector_store)
        mock_index.from_documents.assert_called_once()

        # Verify arguments to from_documents
        call_args = mock_index.from_documents.call_args
        assert call_args[0][0] == mock_docs
        assert call_args[1]["storage_context"] == mock_ctx
        assert call_args[1]["show_progress"] is True


@pytest.mark.unit
class TestMain:
    """Test main function."""

    @patch("src.indexing.build_index.build_index")
    @patch("src.indexing.build_index.create_vector_store")
    @patch("src.indexing.build_index.load_documents")
    @patch("src.indexing.build_index.initialize_settings")
    def test_main_success(
        self, mock_init, mock_load_docs, mock_create_vs, mock_build_idx
    ):
        """Test successful main execution."""
        # Mock return values
        mock_docs = [Mock()]
        mock_load_docs.return_value = mock_docs
        mock_vs = Mock()
        mock_create_vs.return_value = mock_vs
        mock_idx = Mock()
        mock_build_idx.return_value = mock_idx

        build_index.main()

        # Verify all functions were called
        mock_init.assert_called_once()
        mock_load_docs.assert_called_once()
        mock_create_vs.assert_called_once()
        mock_build_idx.assert_called_once_with(mock_docs, mock_vs)

    @patch("src.indexing.build_index.build_index")
    @patch("src.indexing.build_index.create_vector_store")
    @patch("src.indexing.build_index.load_documents")
    @patch("src.indexing.build_index.initialize_settings")
    def test_main_no_documents(
        self, mock_init, mock_load_docs, mock_create_vs, mock_build_idx
    ):
        """Test main when no documents are found."""
        # Mock empty document list
        mock_load_docs.return_value = []

        build_index.main()

        # Verify initialization and load were called
        mock_init.assert_called_once()
        mock_load_docs.assert_called_once()

        # But vector store and build should not be called
        mock_create_vs.assert_not_called()
        mock_build_idx.assert_not_called()


@pytest.mark.slow
@pytest.mark.integration
class TestBuildIndexIntegration:
    """Integration tests for build_index module."""

    @pytest.mark.skip(reason="Requires actual PDFs and models")
    def test_full_indexing_pipeline(self):
        """Test full indexing pipeline (skipped by default)."""
        build_index.main()
