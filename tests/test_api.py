"""Tests for Flask API endpoints."""
import pytest
import json
from unittest.mock import Mock, MagicMock

from src.api.app import create_app


@pytest.mark.unit
class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns 200 OK."""
        response = client.get("/api/health")
        assert response.status_code == 200

        data = response.get_json()
        assert data["status"] == "ok"


@pytest.mark.unit
class TestIndexRoute:
    """Test index route."""

    def test_index_returns_html(self, client):
        """Test that index route returns HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"html" in response.data.lower()


@pytest.mark.unit
class TestQueryEndpoint:
    """Test /api/query endpoint."""

    def test_query_success(self, client):
        """Test successful query."""
        response = client.post(
            "/api/query",
            json={"question": "What is this about?"},
            content_type="application/json"
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "answer" in data
        assert data["answer"] == "Test response"

    def test_query_missing_question(self, client):
        """Test query without question parameter."""
        response = client.post(
            "/api/query",
            json={},
            content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_query_no_json_body(self, client):
        """Test query without JSON body."""
        response = client.post("/api/query")
        # Flask returns 415 for unsupported media type when no content-type
        assert response.status_code in [400, 415]

    def test_query_with_agent_error(self, client, monkeypatch):
        """Test query when agent raises an error."""
        def mock_get_agent_error():
            mock = Mock()
            mock.query.side_effect = Exception("Test error")
            return mock

        monkeypatch.setattr("src.api.app.get_agent", mock_get_agent_error)

        response = client.post(
            "/api/query",
            json={"question": "Test"},
            content_type="application/json"
        )

        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data


@pytest.mark.unit
class TestChatEndpoint:
    """Test /api/chat endpoint."""

    def test_chat_success(self, client):
        """Test successful chat streaming."""
        response = client.post(
            "/api/chat",
            json={"message": "Hello"},
            content_type="application/json"
        )

        assert response.status_code == 200
        assert response.content_type == "text/plain; charset=utf-8"

        # Get streaming response data
        data = b"".join(response.response).decode("utf-8")
        assert "Test streaming response" in data

    def test_chat_missing_message(self, client):
        """Test chat without message parameter."""
        response = client.post(
            "/api/chat",
            json={},
            content_type="application/json"
        )

        assert response.status_code == 400

    def test_chat_with_sources(self, client, monkeypatch):
        """Test chat with source nodes."""
        # Create mock with source nodes
        mock_agent = Mock()
        mock_node = Mock()
        mock_node.metadata = {
            "file_name": "test.pdf",
            "page_label": "1",
            "file_path": "/test/data/pdfs/test.pdf"
        }

        mock_stream_response = MagicMock()
        mock_stream_response.response_gen = iter(["Test response"])
        mock_stream_response.source_nodes = [mock_node]
        mock_agent.chat.return_value = mock_stream_response

        def mock_get_agent():
            return mock_agent

        monkeypatch.setattr("src.api.app.get_agent", mock_get_agent)

        response = client.post(
            "/api/chat",
            json={"message": "Test"},
            content_type="application/json"
        )

        assert response.status_code == 200
        data = b"".join(response.response).decode("utf-8")
        assert "Sources:" in data


@pytest.mark.unit
class TestResetEndpoint:
    """Test /api/reset endpoint."""

    def test_reset_success(self, client):
        """Test successful reset."""
        response = client.post("/api/reset")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "Chat history reset"


@pytest.mark.unit
class TestConversationEndpoints:
    """Test conversation management endpoints."""

    def test_create_conversation(self, client):
        """Test creating a new conversation."""
        response = client.post(
            "/api/conversations",
            json={"title": "Test Conversation"},
            content_type="application/json"
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "id" in data
        assert data["title"] == "Test Conversation"

    def test_create_conversation_default_title(self, client):
        """Test creating a conversation with default title."""
        response = client.post(
            "/api/conversations",
            json={},
            content_type="application/json"
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == "New Conversation"

    def test_get_conversations(self, client):
        """Test getting list of conversations."""
        # Create a conversation first
        client.post("/api/conversations", json={"title": "Test"})

        response = client.get("/api/conversations")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_conversations_with_limit(self, client):
        """Test getting conversations with limit parameter."""
        response = client.get("/api/conversations?limit=5")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) <= 5

    def test_get_recent_conversations(self, client):
        """Test getting recent conversations."""
        response = client.get("/api/conversations/recent")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_recent_conversations_with_limit(self, client):
        """Test getting recent conversations with limit."""
        response = client.get("/api/conversations/recent?limit=3")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) <= 3

    def test_search_conversations(self, client):
        """Test searching conversations."""
        # Create a conversation first
        client.post("/api/conversations", json={"title": "Python Tutorial"})

        response = client.get("/api/conversations/search?q=Python")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_search_conversations_missing_query(self, client):
        """Test search without query parameter."""
        response = client.get("/api/conversations/search")

        assert response.status_code == 400

    def test_get_conversation(self, client):
        """Test getting a specific conversation."""
        # Create a conversation
        create_response = client.post(
            "/api/conversations",
            json={"title": "Test"},
            content_type="application/json"
        )
        conv_id = create_response.get_json()["id"]

        # Get the conversation
        response = client.get(f"/api/conversations/{conv_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == conv_id
        assert data["title"] == "Test"

    def test_get_nonexistent_conversation(self, client):
        """Test getting a conversation that doesn't exist."""
        response = client.get("/api/conversations/99999")

        assert response.status_code == 404

    def test_update_conversation(self, client):
        """Test updating a conversation."""
        # Create a conversation
        create_response = client.post(
            "/api/conversations",
            json={"title": "Original"},
            content_type="application/json"
        )
        conv_id = create_response.get_json()["id"]

        # Update it
        response = client.put(
            f"/api/conversations/{conv_id}",
            json={"title": "Updated"},
            content_type="application/json"
        )

        assert response.status_code == 200

        # Verify the update
        get_response = client.get(f"/api/conversations/{conv_id}")
        assert get_response.get_json()["title"] == "Updated"

    def test_update_conversation_missing_title(self, client):
        """Test updating conversation without title."""
        response = client.put(
            "/api/conversations/1",
            json={},
            content_type="application/json"
        )

        assert response.status_code == 400

    def test_delete_conversation(self, client):
        """Test deleting a conversation."""
        # Create a conversation
        create_response = client.post(
            "/api/conversations",
            json={"title": "To Delete"},
            content_type="application/json"
        )
        conv_id = create_response.get_json()["id"]

        # Delete it
        response = client.delete(f"/api/conversations/{conv_id}")

        assert response.status_code == 200

        # Verify it's deleted
        get_response = client.get(f"/api/conversations/{conv_id}")
        assert get_response.status_code == 404

    def test_add_message(self, client):
        """Test adding a message to a conversation."""
        # Create a conversation
        create_response = client.post(
            "/api/conversations",
            json={"title": "Test"},
            content_type="application/json"
        )
        conv_id = create_response.get_json()["id"]

        # Add a message
        response = client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"role": "user", "content": "Hello"},
            content_type="application/json"
        )

        assert response.status_code == 200

        # Verify the message was added
        get_response = client.get(f"/api/conversations/{conv_id}")
        messages = get_response.get_json()["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"

    def test_add_message_missing_fields(self, client):
        """Test adding a message without required fields."""
        response = client.post(
            "/api/conversations/1/messages",
            json={"role": "user"},
            content_type="application/json"
        )

        assert response.status_code == 400

    def test_generate_conversation_title(self, client):
        """Test generating a title for a conversation."""
        # Create a conversation with a message
        create_response = client.post(
            "/api/conversations",
            json={"title": "New Conversation"},
            content_type="application/json"
        )
        conv_id = create_response.get_json()["id"]

        # Add a user message
        client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"role": "user", "content": "Tell me about Python programming"},
            content_type="application/json"
        )

        # Generate title
        response = client.post(f"/api/conversations/{conv_id}/title")

        assert response.status_code == 200
        data = response.get_json()
        assert "title" in data
        assert len(data["title"]) > 0

    def test_generate_title_no_messages(self, client):
        """Test generating title for conversation with no messages."""
        create_response = client.post(
            "/api/conversations",
            json={"title": "Empty"},
            content_type="application/json"
        )
        conv_id = create_response.get_json()["id"]

        response = client.post(f"/api/conversations/{conv_id}/title")

        assert response.status_code == 404

    def test_generate_title_nonexistent_conversation(self, client):
        """Test generating title for nonexistent conversation."""
        response = client.post("/api/conversations/99999/title")

        assert response.status_code == 404


@pytest.mark.unit
class TestHistoryRoute:
    """Test conversation history page route."""

    def test_history_page(self, client):
        """Test that history page loads."""
        response = client.get("/history")
        assert response.status_code == 200
        assert b"html" in response.data.lower()


@pytest.mark.integration
class TestEndToEndConversation:
    """Test end-to-end conversation flow."""

    def test_full_conversation_flow(self, client):
        """Test creating a conversation, adding messages, and retrieving it."""
        # Create conversation
        create_response = client.post(
            "/api/conversations",
            json={"title": "Test Chat"},
            content_type="application/json"
        )
        conv_id = create_response.get_json()["id"]

        # Add user message
        client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"role": "user", "content": "Hello"},
            content_type="application/json"
        )

        # Add assistant message
        client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"role": "assistant", "content": "Hi there!"},
            content_type="application/json"
        )

        # Retrieve conversation
        get_response = client.get(f"/api/conversations/{conv_id}")
        data = get_response.get_json()

        assert data["title"] == "Test Chat"
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"

        # Search for it
        search_response = client.get("/api/conversations/search?q=Chat")
        search_data = search_response.get_json()
        assert len(search_data) >= 1

        # Delete it
        delete_response = client.delete(f"/api/conversations/{conv_id}")
        assert delete_response.status_code == 200

        # Verify deletion
        get_after_delete = client.get(f"/api/conversations/{conv_id}")
        assert get_after_delete.status_code == 404
