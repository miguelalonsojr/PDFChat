"""Flask application factory and routes."""
from flask import Flask, request, jsonify, Response, stream_with_context, render_template, send_from_directory
from flask_cors import CORS
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents import get_agent
from src.config import (
    FLASK_HOST,
    FLASK_PORT,
    FLASK_DEBUG,
    PROJECT_ROOT,
    APP_TITLE,
    APP_SUBTITLE,
    DATA_DIR,
)
from src.models import get_db


def create_app():
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        static_folder=str(PROJECT_ROOT / "static"),
        template_folder=str(PROJECT_ROOT / "templates"),
    )
    CORS(app)

    # Initialize agent on first request
    agent = None

    def get_or_create_agent():
        nonlocal agent
        if agent is None:
            try:
                agent = get_agent()
            except RuntimeError as e:
                return None, str(e)
        return agent, None

    @app.route("/")
    def index():
        """Serve the main page."""
        return render_template("index.html", app_title=APP_TITLE, app_subtitle=APP_SUBTITLE)

    @app.route("/static/pdfs/<path:filename>")
    def serve_pdf(filename):
        """Serve PDF files from the data directory."""
        return send_from_directory(DATA_DIR, filename)

    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "ok"})

    @app.route("/api/query", methods=["POST"])
    def query():
        """
        Single question endpoint (non-streaming).

        Request body:
            {
                "question": "What is this document about?"
            }
        """
        data = request.get_json()

        if not data or "question" not in data:
            return jsonify({"error": "Missing 'question' in request body"}), 400

        question = data["question"]

        # Get agent
        agent_instance, error = get_or_create_agent()
        if error:
            return jsonify({"error": error}), 500

        try:
            answer = agent_instance.query(question)
            return jsonify({"answer": answer})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/chat", methods=["POST"])
    def chat():
        """
        Streaming chat endpoint.

        Request body:
            {
                "message": "Tell me more about..."
            }
        """
        data = request.get_json()

        if not data or "message" not in data:
            return jsonify({"error": "Missing 'message' in request body"}), 400

        message = data["message"]

        # Get agent
        agent_instance, error = get_or_create_agent()
        if error:
            return jsonify({"error": error}), 500

        def generate():
            """Stream the response."""
            try:
                response = agent_instance.chat(message)
                for token in response.response_gen:
                    yield token

                # After streaming completes, append source information
                if hasattr(response, 'source_nodes') and response.source_nodes:
                    sources = []
                    seen_sources = set()

                    for node in response.source_nodes:
                        # Extract file name and page number from metadata
                        file_name = node.metadata.get('file_name', 'Unknown')
                        page_label = node.metadata.get('page_label', '')
                        file_path = node.metadata.get('file_path', '')

                        # Create unique identifier for deduplication
                        source_id = f"{file_name}_{page_label}"
                        if source_id not in seen_sources:
                            seen_sources.add(source_id)

                            # Format source entry with link
                            if file_path:
                                # Get relative path from DATA_DIR
                                try:
                                    rel_path = Path(file_path).relative_to(DATA_DIR)
                                    # Use as_posix() to ensure forward slashes for URLs
                                    pdf_url = f"/static/pdfs/{rel_path.as_posix()}"
                                except ValueError:
                                    # If file is not in DATA_DIR, just use filename
                                    pdf_url = f"/static/pdfs/{file_name}"

                                if page_label:
                                    sources.append(f"[{file_name} (Page {page_label})]({pdf_url})")
                                else:
                                    sources.append(f"[{file_name}]({pdf_url})")
                            else:
                                if page_label:
                                    sources.append(f"{file_name} (Page {page_label})")
                                else:
                                    sources.append(file_name)

                    if sources:
                        yield "\n\n---\n\n**Sources:**\n\n"
                        for i, source in enumerate(sources, 1):
                            yield f"{i}. {source}\n"
            except Exception as e:
                yield f"\n\nError: {str(e)}"

        return Response(
            stream_with_context(generate()),
            mimetype="text/plain",
        )

    @app.route("/api/reset", methods=["POST"])
    def reset():
        """Reset chat history."""
        agent_instance, error = get_or_create_agent()
        if error:
            return jsonify({"error": error}), 500

        try:
            agent_instance.reset_chat()
            return jsonify({"status": "Chat history reset"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Conversation management endpoints
    @app.route("/api/conversations", methods=["GET"])
    def get_conversations():
        """Get list of conversations."""
        try:
            db = get_db()
            limit = request.args.get("limit", 50, type=int)
            offset = request.args.get("offset", 0, type=int)
            conversations = db.list_conversations(limit=limit, offset=offset)
            return jsonify(conversations)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/conversations/recent", methods=["GET"])
    def get_recent_conversations():
        """Get recent conversations for the flyout menu."""
        try:
            db = get_db()
            limit = request.args.get("limit", 10, type=int)
            conversations = db.get_recent_conversations(limit=limit)
            return jsonify(conversations)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/conversations/search", methods=["GET"])
    def search_conversations():
        """Search conversations."""
        try:
            query = request.args.get("q", "")
            if not query:
                return jsonify({"error": "Missing search query"}), 400

            db = get_db()
            limit = request.args.get("limit", 50, type=int)
            conversations = db.search_conversations(query, limit=limit)
            return jsonify(conversations)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/conversations", methods=["POST"])
    def create_conversation():
        """Create a new conversation."""
        try:
            data = request.get_json() or {}
            title = data.get("title", "New Conversation")

            db = get_db()
            conversation_id = db.create_conversation(title)
            return jsonify({"id": conversation_id, "title": title})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/conversations/<int:conversation_id>", methods=["GET"])
    def get_conversation(conversation_id):
        """Get a specific conversation with all messages."""
        try:
            db = get_db()
            conversation = db.get_conversation(conversation_id)
            if not conversation:
                return jsonify({"error": "Conversation not found"}), 404
            return jsonify(conversation)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/conversations/<int:conversation_id>", methods=["PUT"])
    def update_conversation(conversation_id):
        """Update a conversation (e.g., change title)."""
        try:
            data = request.get_json()
            if not data or "title" not in data:
                return jsonify({"error": "Missing 'title' in request body"}), 400

            db = get_db()
            db.update_conversation_title(conversation_id, data["title"])
            return jsonify({"status": "Conversation updated"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/conversations/<int:conversation_id>", methods=["DELETE"])
    def delete_conversation(conversation_id):
        """Delete a conversation."""
        try:
            db = get_db()
            db.delete_conversation(conversation_id)
            return jsonify({"status": "Conversation deleted"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/conversations/<int:conversation_id>/messages", methods=["POST"])
    def add_message(conversation_id):
        """Add a message to a conversation."""
        try:
            data = request.get_json()
            if not data or "role" not in data or "content" not in data:
                return jsonify({"error": "Missing 'role' or 'content' in request body"}), 400

            db = get_db()
            db.add_message(conversation_id, data["role"], data["content"])
            return jsonify({"status": "Message added"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/conversations/<int:conversation_id>/title", methods=["POST"])
    def generate_conversation_title(conversation_id):
        """Generate a title for a conversation using AI."""
        try:
            db = get_db()
            conversation = db.get_conversation(conversation_id)

            if not conversation or not conversation.get("messages"):
                return jsonify({"error": "Conversation not found or has no messages"}), 404

            # Get the first user message to generate a title
            user_messages = [msg for msg in conversation["messages"] if msg["role"] == "user"]
            if not user_messages:
                return jsonify({"error": "No user messages found"}), 400

            first_message = user_messages[0]["content"]

            # Generate a concise title (use first 50 chars or summarize)
            # For now, simple implementation - take first message and truncate
            if len(first_message) > 50:
                title = first_message[:47] + "..."
            else:
                title = first_message

            db.update_conversation_title(conversation_id, title)
            return jsonify({"title": title})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/history")
    def conversation_history():
        """Serve the conversation history page."""
        return render_template("history.html", app_title=APP_TITLE)

    return app


def main():
    """Run the Flask application."""
    app = create_app()
    print(f"\nStarting PDFChat server on http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"Make sure Ollama is running with the '{app.config.get('OLLAMA_MODEL', 'nemotron')}' model")
    print("\nPress Ctrl+C to stop\n")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)


if __name__ == "__main__":
    main()
