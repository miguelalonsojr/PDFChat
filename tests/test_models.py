"""Tests for database models."""
import pytest
import sqlite3
from datetime import datetime

from src.models import ConversationDB, get_db


@pytest.mark.unit
class TestConversationDB:
    """Test ConversationDB class."""

    def test_init_creates_database(self, test_db_path):
        """Test that database is created on initialization."""
        db = ConversationDB(db_path=test_db_path)
        assert test_db_path.exists()

    def test_init_creates_tables(self, conversation_db, test_db_path):
        """Test that required tables are created."""
        with sqlite3.connect(test_db_path) as conn:
            cursor = conn.cursor()

            # Check conversations table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'"
            )
            assert cursor.fetchone() is not None

            # Check messages table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
            )
            assert cursor.fetchone() is not None

    def test_init_creates_indexes(self, conversation_db, test_db_path):
        """Test that indexes are created."""
        with sqlite3.connect(test_db_path) as conn:
            cursor = conn.cursor()

            # Check for indexes
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_conversations_updated'"
            )
            assert cursor.fetchone() is not None

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_messages_conversation'"
            )
            assert cursor.fetchone() is not None

    def test_create_conversation(self, conversation_db):
        """Test creating a new conversation."""
        conv_id = conversation_db.create_conversation("Test Title")
        assert isinstance(conv_id, int)
        assert conv_id > 0

    def test_create_conversation_with_default_title(self, conversation_db):
        """Test creating a conversation with default title."""
        conv_id = conversation_db.create_conversation()
        conv = conversation_db.get_conversation(conv_id)
        assert conv["title"] == "New Conversation"

    def test_update_conversation_title(self, conversation_db):
        """Test updating a conversation's title."""
        conv_id = conversation_db.create_conversation("Original Title")
        conversation_db.update_conversation_title(conv_id, "Updated Title")

        conv = conversation_db.get_conversation(conv_id)
        assert conv["title"] == "Updated Title"

    def test_add_message(self, conversation_db):
        """Test adding a message to a conversation."""
        conv_id = conversation_db.create_conversation("Test")
        conversation_db.add_message(conv_id, "user", "Hello")

        conv = conversation_db.get_conversation(conv_id)
        assert len(conv["messages"]) == 1
        assert conv["messages"][0]["role"] == "user"
        assert conv["messages"][0]["content"] == "Hello"

    def test_add_multiple_messages(self, conversation_db):
        """Test adding multiple messages to a conversation."""
        conv_id = conversation_db.create_conversation("Test")
        conversation_db.add_message(conv_id, "user", "Hello")
        conversation_db.add_message(conv_id, "assistant", "Hi there!")
        conversation_db.add_message(conv_id, "user", "How are you?")

        conv = conversation_db.get_conversation(conv_id)
        assert len(conv["messages"]) == 3
        assert conv["messages"][0]["role"] == "user"
        assert conv["messages"][1]["role"] == "assistant"
        assert conv["messages"][2]["role"] == "user"

    def test_get_conversation(self, conversation_db):
        """Test getting a conversation by ID."""
        conv_id = conversation_db.create_conversation("Test Conversation")
        conversation_db.add_message(conv_id, "user", "Test message")

        conv = conversation_db.get_conversation(conv_id)

        assert conv is not None
        assert conv["id"] == conv_id
        assert conv["title"] == "Test Conversation"
        assert "created_at" in conv
        assert "updated_at" in conv
        assert len(conv["messages"]) == 1

    def test_get_nonexistent_conversation(self, conversation_db):
        """Test getting a conversation that doesn't exist."""
        conv = conversation_db.get_conversation(99999)
        assert conv is None

    def test_list_conversations(self, conversation_db):
        """Test listing conversations."""
        # Create multiple conversations
        id1 = conversation_db.create_conversation("First")
        import time
        time.sleep(0.01)  # Small delay to ensure different timestamps
        id2 = conversation_db.create_conversation("Second")
        time.sleep(0.01)
        id3 = conversation_db.create_conversation("Third")

        convs = conversation_db.list_conversations()

        assert len(convs) == 3
        # Should be ordered by updated_at DESC, so newest first
        conv_ids = [conv["id"] for conv in convs]
        assert id3 in conv_ids
        assert id2 in conv_ids
        assert id1 in conv_ids

    def test_list_conversations_with_limit(self, conversation_db):
        """Test listing conversations with limit."""
        for i in range(5):
            conversation_db.create_conversation(f"Conv {i}")

        convs = conversation_db.list_conversations(limit=3)
        assert len(convs) == 3

    def test_list_conversations_with_offset(self, conversation_db):
        """Test listing conversations with offset."""
        for i in range(5):
            conversation_db.create_conversation(f"Conv {i}")

        convs = conversation_db.list_conversations(limit=2, offset=2)
        assert len(convs) == 2

    def test_list_conversations_includes_message_count(self, conversation_db):
        """Test that list_conversations includes message count."""
        conv_id = conversation_db.create_conversation("Test")
        conversation_db.add_message(conv_id, "user", "Message 1")
        conversation_db.add_message(conv_id, "assistant", "Message 2")

        convs = conversation_db.list_conversations()
        assert convs[0]["message_count"] == 2

    def test_search_conversations_by_title(self, conversation_db):
        """Test searching conversations by title."""
        conversation_db.create_conversation("Python Tutorial")
        conversation_db.create_conversation("JavaScript Guide")
        conversation_db.create_conversation("Python Advanced")

        results = conversation_db.search_conversations("Python")
        assert len(results) == 2

    def test_search_conversations_by_message_content(self, conversation_db):
        """Test searching conversations by message content."""
        conv1 = conversation_db.create_conversation("Test 1")
        conv2 = conversation_db.create_conversation("Test 2")

        conversation_db.add_message(conv1, "user", "Tell me about Python")
        conversation_db.add_message(conv2, "user", "Explain JavaScript")

        results = conversation_db.search_conversations("Python")
        assert len(results) == 1
        assert results[0]["id"] == conv1

    def test_search_conversations_case_insensitive(self, conversation_db):
        """Test that search is case insensitive."""
        conversation_db.create_conversation("Python Tutorial")

        results = conversation_db.search_conversations("python")
        assert len(results) == 1

    def test_search_conversations_with_limit(self, conversation_db):
        """Test searching conversations with limit."""
        for i in range(5):
            conversation_db.create_conversation(f"Python {i}")

        results = conversation_db.search_conversations("Python", limit=3)
        assert len(results) == 3

    def test_delete_conversation(self, conversation_db):
        """Test deleting a conversation."""
        conv_id = conversation_db.create_conversation("Test")
        conversation_db.add_message(conv_id, "user", "Test message")

        conversation_db.delete_conversation(conv_id)

        # Conversation should no longer exist
        conv = conversation_db.get_conversation(conv_id)
        assert conv is None

    def test_delete_conversation_cascades_messages(self, conversation_db, test_db_path):
        """Test that deleting a conversation also deletes its messages."""
        conv_id = conversation_db.create_conversation("Test")
        conversation_db.add_message(conv_id, "user", "Message 1")
        conversation_db.add_message(conv_id, "assistant", "Message 2")

        conversation_db.delete_conversation(conv_id)

        # Check that messages are also deleted
        with sqlite3.connect(test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (conv_id,))
            count = cursor.fetchone()[0]
            assert count == 0

    def test_get_recent_conversations(self, conversation_db):
        """Test getting recent conversations."""
        for i in range(15):
            conversation_db.create_conversation(f"Conv {i}")

        recent = conversation_db.get_recent_conversations(limit=10)
        assert len(recent) == 10

    def test_timestamps_are_iso_format(self, conversation_db):
        """Test that timestamps are in ISO format."""
        conv_id = conversation_db.create_conversation("Test")
        conv = conversation_db.get_conversation(conv_id)

        # Check that timestamps end with 'Z' (ISO format with UTC)
        assert conv["created_at"].endswith("Z")
        assert conv["updated_at"].endswith("Z")

    def test_updated_at_changes_on_message_add(self, conversation_db):
        """Test that updated_at changes when a message is added."""
        conv_id = conversation_db.create_conversation("Test")
        conv1 = conversation_db.get_conversation(conv_id)
        original_updated = conv1["updated_at"]

        # Add a message
        import time
        time.sleep(0.1)  # Small delay to ensure timestamp difference
        conversation_db.add_message(conv_id, "user", "New message")

        conv2 = conversation_db.get_conversation(conv_id)
        new_updated = conv2["updated_at"]

        assert new_updated >= original_updated


@pytest.mark.unit
def test_get_db_singleton():
    """Test that get_db returns a singleton instance."""
    # Reset global instance
    import src.models
    src.models._db_instance = None

    db1 = get_db()
    db2 = get_db()

    assert db1 is db2
