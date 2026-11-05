# 📚 Local RAG Chat

Ask questions about your own documents – PDFs, Word files, Markdown, text and CSV – in a
Streamlit chat. Everything runs **100% offline on localhost**: a local open-source LLM via
[Ollama](https://ollama.com), local embeddings and a local vector database (ChromaDB).
No cloud API, no API keys, no data leaves your computer.

## The assignment

> *"You'll make a small application where you combine RAGs, Local LLMs using Ollama, and
> Streamlit. The application runs a Streamlit frontend, a backend with any open source offline
> LLM which interacts with your personal or any kind of documents sitting inside your system.
> At the end of the day, you'll showcase your application running on localhost where you can
> interact with your documents on the Streamlit frontend."*

| Requirement | How this project does it |
|---|---|
| RAG | Own retrieval pipeline: chunking → embeddings → vector search → grounded prompt with citations |
| Local LLM with Ollama | `llama3.2` for answers, `nomic-embed-text` for embeddings, both served by Ollama |
| Streamlit frontend | `src/frontend/` – sidebar, chat tab, "How it works" tab |
| Separate backend | `src/backend/` – no Streamlit inside, only reachable through `backend/api.py` |
| Documents on your system | Scan any local folder (default `data/documents/`) **or** upload files in the browser |
| Runs on localhost | `streamlit run app.py` → http://localhost:8501 |

## Features

- 📂 **Two ways to add documents:** scan a folder on your computer (recursive) or upload files
- 📄 **Formats:** PDF (page by page), DOCX, Markdown, TXT, CSV
- ♻️ **Smart re-indexing:** files with unchanged content are skipped (MD5 hash);
  a changed file replaces its old chunks
- 🧠 **Any local model:** pick any chat model installed in Ollama, adjust *k* (chunks retrieved)
- 🔎 **Grounded answers:** the model only uses your documents and says
  *"I couldn't find that in your documents."* otherwise
- 📎 **Citations:** answers cite `[1]`, `[2]`; the Sources panel shows file, page, similarity
  and a text preview
- ⚡ **Streaming** answers, response time and model shown under each answer
- 💬 **Short chat memory** (last 6 messages) for follow-up questions
- 🗑️ **One-click reset** of the knowledge base
- 🛡️ **Robust:** errors are shown per file, the app does not crash; clear hints if Ollama is
  not running or a model is missing

## Architecture

Frontend and backend are clearly separated. The backend follows **Ports & Adapters**
(hexagonal architecture): the services depend on small interfaces (`ports.py`), and the
concrete technologies (Ollama, ChromaDB) are plugged in as adapters.

```
local-rag-chat/
├── app.py                         # entry point: streamlit run app.py
├── .streamlit/config.toml         # theme + server settings
├── .env.example                   # all settings with defaults
├── data/documents/sample/         # fictional demo documents (md, txt, pdf)
├── scripts/make_sample_pdf.py     # generates the demo PDF (no extra dependencies)
├── src/
│   ├── backend/
│   │   ├── api.py                 # ⭐ public facade – the ONLY thing the frontend imports
│   │   ├── container.py           # dependency injection: wires adapters into services
│   │   ├── config.py              # Settings from .env
│   │   ├── ports.py               # Protocols: DocumentLoader, Embedder, VectorStore, LLMClient
│   │   ├── prompts.py             # system prompt + context formatting
│   │   ├── domain/                # dataclasses (Document, Chunk, Answer, …) + errors
│   │   ├── ingestion/             # loaders, chunker, folder scanner
│   │   ├── adapters/              # OllamaEmbedder, OllamaLLM, ChromaStore
│   │   └── services/              # IngestionService, QAService (the use cases)
│   └── frontend/
│       ├── main.py                # page layout, health check, tabs
│       ├── state.py               # all session_state keys in one place
│       └── components/            # sidebar, chat, how_it_works
└── tests/                         # pytest with fakes – no Ollama needed
```

**Dependency direction** (arrows = "imports"):

```
frontend ──▶ backend.api ──▶ services ──▶ ports ◀── adapters ──▶ Ollama / ChromaDB
                  ▲                                     ▲
                  └──────────── container.py ───────────┘   (wires everything together)
```

- The **frontend** only renders UI and calls `BackendAPI` methods. No RAG logic in the UI.
- The **backend** does not know Streamlit. It could be put behind FastAPI without changing
  the services – only `api.py` would get HTTP endpoints.
- The **services** only know the ports, so tests use fake embedder / LLM / vector store.

### Data flow

```
 INDEXING (once per file)
 file / upload ─▶ Loader ─▶ Chunker ─▶ OllamaEmbedder ─▶ ChromaStore
  (bytes)        (text,     (~1000 chars,  (nomic-embed-text,  (vectors + text +
                  pages)     200 overlap)   768-dim vectors)    file, page, hash)

 ANSWERING (every question)
 question ─▶ embed ─▶ ChromaStore.query(top-k, cosine) ─▶ prompt with [1] [2] blocks
          ─▶ OllamaLLM (llama3.2, streaming) ─▶ answer with citations + Sources panel
```

## Prerequisites

- Python **3.11+**
- [Ollama](https://ollama.com/download) installed (macOS, Windows or Linux)
- ~3 GB free disk space for the models, 8 GB RAM recommended

## Setup

```bash
# 1. Install Ollama (macOS example – or download it from https://ollama.com/download)
brew install ollama
ollama serve                      # keep running (the desktop app does this automatically)

# 2. Pull the two local models
ollama pull llama3.2
ollama pull nomic-embed-text

# 3. Create a virtual environment and install dependencies
cd local-rag-chat
python3 -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 4. Start the app
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

Then in the sidebar: enter `data/documents/sample` → **Scan & index folder** → ask
*"How many vacation days do employees get?"*

## Use your own documents

- Put files into `data/documents/` (subfolders are fine) and click **Scan & index folder**, or
- enter **any folder path** on your computer (absolute, or relative to the project), or
- drag & drop files into **Upload** and click **Index uploads**.

Supported: `.pdf`, `.docx`, `.md`, `.txt`, `.csv`. Hidden files and folders are ignored.
The index is stored in `chroma_db/` and survives restarts.

## Tests and linting

```bash
pip install -r requirements-dev.txt
pytest            # unit tests, run without Ollama (fakes for embedder, LLM and vector store)
ruff check .      # linting
```

## Configuration

Copy `.env.example` to `.env` and change what you need:

| Variable | Default | Meaning |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server |
| `CHAT_MODEL` | `llama3.2` | default chat model |
| `EMBED_MODEL` | `nomic-embed-text` | embedding model |
| `CHUNK_SIZE` | `1000` | max characters per chunk |
| `CHUNK_OVERLAP` | `200` | characters repeated between chunks |
| `TOP_K` | `4` | default number of retrieved chunks |
| `DB_PATH` | `./chroma_db` | ChromaDB folder |
| `DOCS_DIR` | `./data/documents` | default folder in the sidebar |
| `COLLECTION` | `documents` | ChromaDB collection name |

If you change `EMBED_MODEL` or the chunk settings, clear the knowledge base and index again.

## Known limits

- **Scanned PDFs** (images only) have no text layer → they need OCR (not included).
- **Small local models** (3B parameters) are fast but sometimes forget a citation or miss
  details; answers take a few seconds on a laptop CPU/GPU.
- **Cross-language retrieval** is weaker: a German question about English documents finds
  fewer relevant chunks than an English one.
- **Pure vector search:** exact keywords, IDs or numbers are sometimes ranked lower
  (hybrid search would help).
- Retrieval uses only the current question; the chat memory helps the model, not the search.
- Single user, single process – fine for a local tool, not for a multi-user server.

## Possible next steps

OCR for scanned PDFs · hybrid search (BM25 + vectors) · re-ranking · evaluation set with
expected answers · FastAPI backend + Docker Compose.
