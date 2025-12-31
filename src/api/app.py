"""Flask application factory and routes."""
from flask import Flask, request, jsonify, Response, stream_with_context, render_template
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
)


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
