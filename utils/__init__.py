"""
Utility modules for PDF-crewai v2.0
Production-grade enhancements with enhanced chatting logic
"""

__version__ = "3.1.0"

# Enhanced chatting components
from .chat_manager import (
    ChatManager,
    ConversationContext,
    ResponseFormatter,
    StreamingResponseHandler,
)

# Vector database backend (ChromaDB local | Pinecone cloud)
from .vector_store import (
    VectorStoreManager,
    compute_pdf_fingerprint,
    chunk_text,
    embed_texts,
)
