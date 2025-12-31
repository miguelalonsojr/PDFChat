# Quick Start Guide

Get PDFChat running in 5 minutes!

## Prerequisites Check

```bash
# Check Python version (need 3.10+)
python3 --version

# Check UV installation
uv --version

# Check Ollama installation
ollama --version
```

If any are missing, install them first (see README.md).

## Quick Setup

```bash
# 1. Install dependencies
uv sync

# 2. Install and start Ollama with Nemotron
ollama pull nemotron
ollama serve  # Keep this running in a separate terminal

# 3. Add your PDFs to data/pdfs/
cp ~/Documents/*.pdf data/pdfs/

# 4. Build the index (one-time, takes a few minutes)
uv run python src/indexing/build_index.py

# 5. Start the server
uv run python run.py

# 6. Open browser to http://127.0.0.1:5000
```

## Even Simpler Commands

After initial setup, you only need:

```bash
# Terminal 1: Start Ollama (if not running)
ollama serve

# Terminal 2: Start PDFChat
uv run python run.py
```

## First Questions to Try

- "What topics are covered in these documents?"
- "Summarize the main points"
- "What does it say about [specific topic]?"

## Troubleshooting

**"Failed to load collection"**
→ Run: `uv run python src/indexing/build_index.py`

**"Connection refused"**
→ Make sure Ollama is running: `ollama serve`

**Slow responses**
→ Normal for first query (loading models). Subsequent queries are faster.

## Adding More PDFs

```bash
# 1. Copy new PDFs
cp new-pdfs/*.pdf data/pdfs/

# 2. Rebuild index
uv run python src/indexing/build_index.py

# 3. Restart server
# Ctrl+C to stop, then: uv run python run.py
```

That's it! See README.md for detailed documentation.
