"""Database models for conversation history."""
from datetime import datetime
from typing import List, Optional
import json
import sqlite3
from pathlib import Path

from src.config import DATABASE_DIR


DATABASE_PATH = DATABASE_DIR / "conversations.db"


class ConversationDB:
    """Database manager for conversations."""

    def __init__(self, db_path: Path = DATABASE_PATH):
        """Initialize database connection."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
                )
            """)

            # Index for faster searches
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_updated
                ON conversations(updated_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                ON messages(conversation_id)
            """)

            conn.commit()

    def create_conversation(self, title: str = "New Conversation") -> int:
        """Create a new conversation."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (title) VALUES (?)",
                (title,)
            )
            conn.commit()
            return cursor.lastrowid

    def update_conversation_title(self, conversation_id: int, title: str):
        """Update conversation title."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (title, conversation_id)
            )
            conn.commit()

    def add_message(self, conversation_id: int, role: str, content: str):
        """Add a message to a conversation."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
                (conversation_id, role, content)
            )
            # Update conversation timestamp
            cursor.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,)
            )
            conn.commit()

    def get_conversation(self, conversation_id: int) -> Optional[dict]:
        """Get a conversation with all its messages."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get conversation
            cursor.execute(
                """
                SELECT id, title,
                       datetime(created_at) || 'Z' as created_at,
                       datetime(updated_at) || 'Z' as updated_at
                FROM conversations WHERE id = ?
                """,
                (conversation_id,)
            )
            conv_row = cursor.fetchone()

            if not conv_row:
                return None

            # Get messages
            cursor.execute(
                """
                SELECT role, content,
                       datetime(created_at) || 'Z' as created_at
                FROM messages WHERE conversation_id = ? ORDER BY id ASC
                """,
                (conversation_id,)
            )
            messages = [dict(row) for row in cursor.fetchall()]

            return {
                "id": conv_row["id"],
                "title": conv_row["title"],
                "created_at": conv_row["created_at"],
                "updated_at": conv_row["updated_at"],
                "messages": messages
            }

    def list_conversations(self, limit: int = 50, offset: int = 0) -> List[dict]:
        """List conversations ordered by most recent."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT c.id, c.title,
                       datetime(c.created_at) || 'Z' as created_at,
                       datetime(c.updated_at) || 'Z' as updated_at,
                       (SELECT COUNT(*) FROM messages WHERE conversation_id = c.id) as message_count
                FROM conversations c
                ORDER BY c.updated_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            )

            return [dict(row) for row in cursor.fetchall()]

    def search_conversations(self, query: str, limit: int = 50) -> List[dict]:
        """Search conversations by title or message content."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            search_pattern = f"%{query}%"

            cursor.execute(
                """
                SELECT DISTINCT c.id, c.title,
                       datetime(c.created_at) || 'Z' as created_at,
                       datetime(c.updated_at) || 'Z' as updated_at,
                       (SELECT COUNT(*) FROM messages WHERE conversation_id = c.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.title LIKE ? OR m.content LIKE ?
                ORDER BY c.updated_at DESC
                LIMIT ?
                """,
                (search_pattern, search_pattern, limit)
            )

            return [dict(row) for row in cursor.fetchall()]

    def delete_conversation(self, conversation_id: int):
        """Delete a conversation and all its messages."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            conn.commit()

    def get_recent_conversations(self, limit: int = 10) -> List[dict]:
        """Get the most recent conversations for the flyout menu."""
        return self.list_conversations(limit=limit, offset=0)


# Global database instance
_db_instance = None


def get_db() -> ConversationDB:
    """Get or create database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = ConversationDB()
    return _db_instance
