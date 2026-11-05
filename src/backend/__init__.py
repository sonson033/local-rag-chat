"""Backend of Local RAG Chat.

Everything that knows about documents, embeddings, vector search and LLMs lives here.
The backend does not know Streamlit. The frontend talks to it only through `backend.api`.
"""
