"""
Vector Database Backend
Supports ChromaDB (local, persistent) and Pinecone (cloud).
Prevents re-processing the same PDF twice via SHA-256 content fingerprinting.
"""

import os
import hashlib
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# Embedding helper (sentence-transformers, no extra key needed)
# ─────────────────────────────────────────────────────────
_embedding_model = None


def _get_embedding_model():
    """Lazy-load the local sentence-transformer model (cached after first load)."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Embedding model loaded: all-MiniLM-L6-v2")
        except ImportError:
            raise ImportError(
                "sentence-transformers is required.  "
                "Run: pip install sentence-transformers>=2.2.0"
            )
    return _embedding_model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Return a list of embedding vectors for the given list of texts."""
    model = _get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


# ─────────────────────────────────────────────────────────
# Document fingerprinting
# ─────────────────────────────────────────────────────────

def compute_pdf_fingerprint(content: str) -> str:
    """Compute a stable SHA-256 fingerprint from the PDF text content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────────────────
# Text chunking
# ─────────────────────────────────────────────────────────

def chunk_text(
    text: str,
    chunk_size: int = 400,
    overlap: int = 60,
) -> List[str]:
    """
    Split *text* into overlapping word-based chunks.

    Args:
        text:       Full document text.
        chunk_size: Target number of words per chunk.
        overlap:    Number of words to overlap between consecutive chunks.

    Returns:
        List of text chunks.
    """
    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks


# ─────────────────────────────────────────────────────────
# ChromaDB backend
# ─────────────────────────────────────────────────────────

CHROMA_PERSIST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "chroma_db"
)


class ChromaVectorStore:
    """
    Persistent ChromaDB vector store.

    One Chroma collection per application; each document gets its own
    namespace via metadata filters.  Chunks are tagged with the document
    SHA-256 fingerprint so we can check for duplicates without re-embedding.
    """

    COLLECTION_NAME = "pdf_research_docs"

    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR):
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            raise ImportError(
                "chromadb is required.  Run: pip install chromadb>=0.4.0"
            )

        self.persist_dir = persist_dir
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB initialised at '%s' (collection: %s)",
            persist_dir,
            self.COLLECTION_NAME,
        )

    # ── Public API ─────────────────────────────────────────

    def document_exists(self, fingerprint: str) -> bool:
        """Return True if any chunk with this fingerprint is already stored."""
        results = self._collection.get(
            where={"doc_fingerprint": fingerprint},
            limit=1,
        )
        return len(results["ids"]) > 0

    def add_document(
        self,
        filename: str,
        text: str,
        fingerprint: str,
        extra_metadata: Optional[Dict] = None,
    ) -> int:
        """
        Chunk, embed, and store a document.

        Args:
            filename:       Original filename (for metadata).
            text:           Full document text.
            fingerprint:    SHA-256 of the text content.
            extra_metadata: Any additional key/value pairs to persist.

        Returns:
            Number of chunks added.
        """
        if self.document_exists(fingerprint):
            logger.info("Document '%s' already indexed — skipping.", filename)
            return 0

        chunks = chunk_text(text)
        if not chunks:
            logger.warning("No chunks produced for '%s'.", filename)
            return 0

        embeddings = embed_texts(chunks)

        base_meta = {
            "doc_fingerprint": fingerprint,
            "filename": filename,
            "upload_date": datetime.now().isoformat(),
        }
        if extra_metadata:
            base_meta.update(extra_metadata)

        ids = [f"{fingerprint}_{i}" for i in range(len(chunks))]
        metadatas = [{**base_meta, "chunk_index": i} for i in range(len(chunks))]

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

        logger.info(
            "Indexed '%s': %d chunks stored in ChromaDB.", filename, len(chunks)
        )
        return len(chunks)

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        fingerprint_filter: Optional[str] = None,
    ) -> List[Dict]:
        """
        Semantic search in the vector store.

        Args:
            query_text:        Natural-language query.
            n_results:         Number of top results to return.
            fingerprint_filter: If given, restrict search to one document.

        Returns:
            List of result dicts with keys: text, score, metadata.
        """
        query_embedding = embed_texts([query_text])[0]

        where = {"doc_fingerprint": fingerprint_filter} if fingerprint_filter else None

        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "distances", "metadatas"],
            )
        except Exception as exc:
            logger.error("ChromaDB query error: %s", exc)
            return []

        hits = []
        for doc, dist, meta in zip(
            results["documents"][0],
            results["distances"][0],
            results["metadatas"][0],
        ):
            hits.append(
                {
                    "text": doc,
                    "score": round(1.0 - dist, 4),   # cosine similarity
                    "metadata": meta,
                }
            )

        return hits

    def delete_document(self, fingerprint: str) -> int:
        """Remove all chunks for a document. Returns number of chunks deleted."""
        existing = self._collection.get(where={"doc_fingerprint": fingerprint})
        ids = existing["ids"]
        if ids:
            self._collection.delete(ids=ids)
        return len(ids)

    def list_documents(self) -> List[Dict]:
        """Return one summary entry per stored document."""
        all_meta = self._collection.get(include=["metadatas"])["metadatas"]
        seen: Dict[str, Dict] = {}
        for m in all_meta:
            fp = m.get("doc_fingerprint", "")
            if fp not in seen:
                seen[fp] = {
                    "fingerprint": fp,
                    "filename": m.get("filename", "unknown"),
                    "upload_date": m.get("upload_date", ""),
                    "chunk_count": 1,
                }
            else:
                seen[fp]["chunk_count"] += 1
        return list(seen.values())

    def get_stats(self) -> Dict:
        """Return basic collection stats."""
        count = self._collection.count()
        docs = self.list_documents()
        return {
            "backend": "ChromaDB",
            "persist_dir": self.persist_dir,
            "total_chunks": count,
            "total_documents": len(docs),
        }


# ─────────────────────────────────────────────────────────
# Pinecone backend
# ─────────────────────────────────────────────────────────

class PineconeVectorStore:
    """
    Cloud-based Pinecone vector store.

    Requires environment variables:
        PINECONE_API_KEY   – your Pinecone API key
        PINECONE_INDEX     – the name of an existing index
        PINECONE_ENV       – (optional) Pinecone environment / region
    """

    EMBEDDING_DIM = 384   # all-MiniLM-L6-v2 output dimension

    def __init__(self):
        api_key = os.getenv("PINECONE_API_KEY", "")
        index_name = os.getenv("PINECONE_INDEX", "pdf-research")
        environment = os.getenv("PINECONE_ENV", "us-east-1-aws")

        if not api_key:
            raise EnvironmentError(
                "PINECONE_API_KEY is not set. "
                "Add it to your .env file to use Pinecone."
            )

        try:
            from pinecone import Pinecone, ServerlessSpec
        except ImportError:
            raise ImportError(
                "pinecone-client is required.  "
                "Run: pip install pinecone-client>=3.0.0"
            )

        pc = Pinecone(api_key=api_key)

        # Create index if it doesn't exist yet
        existing = [idx.name for idx in pc.list_indexes()]
        if index_name not in existing:
            pc.create_index(
                name=index_name,
                dimension=self.EMBEDDING_DIM,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=environment.split("-aws")[0]),
            )
            logger.info("Created Pinecone index '%s'.", index_name)

        self._index = pc.Index(index_name)
        self._index_name = index_name
        logger.info("Pinecone index '%s' connected.", index_name)

    # ── Public API ─────────────────────────────────────────

    def document_exists(self, fingerprint: str) -> bool:
        """Check if any vector with this fingerprint namespace exists."""
        # We use fingerprint as Pinecone namespace
        stats = self._index.describe_index_stats()
        namespaces = stats.get("namespaces", {})
        return fingerprint in namespaces and namespaces[fingerprint].get("vector_count", 0) > 0

    def add_document(
        self,
        filename: str,
        text: str,
        fingerprint: str,
        extra_metadata: Optional[Dict] = None,
    ) -> int:
        if self.document_exists(fingerprint):
            logger.info("Document '%s' already in Pinecone — skipping.", filename)
            return 0

        chunks = chunk_text(text)
        if not chunks:
            return 0
        embeddings = embed_texts(chunks)

        base_meta = {
            "doc_fingerprint": fingerprint,
            "filename": filename,
            "upload_date": datetime.now().isoformat(),
        }
        if extra_metadata:
            base_meta.update(extra_metadata)

        vectors = []
        for i, (emb, chunk) in enumerate(zip(embeddings, chunks)):
            meta = {**base_meta, "chunk_index": i, "text": chunk}
            vectors.append((f"{fingerprint}_{i}", emb, meta))

        # Upsert in batches of 100
        batch_size = 100
        for start in range(0, len(vectors), batch_size):
            batch = vectors[start : start + batch_size]
            self._index.upsert(
                vectors=batch,
                namespace=fingerprint,
            )

        logger.info(
            "Indexed '%s': %d chunks stored in Pinecone (ns=%s).",
            filename,
            len(chunks),
            fingerprint,
        )
        return len(chunks)

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        fingerprint_filter: Optional[str] = None,
    ) -> List[Dict]:
        query_embedding = embed_texts([query_text])[0]
        namespace = fingerprint_filter or ""

        try:
            resp = self._index.query(
                vector=query_embedding,
                top_k=n_results,
                namespace=namespace,
                include_metadata=True,
            )
        except Exception as exc:
            logger.error("Pinecone query error: %s", exc)
            return []

        hits = []
        for match in resp.get("matches", []):
            meta = match.get("metadata", {})
            hits.append(
                {
                    "text": meta.pop("text", ""),
                    "score": round(float(match.get("score", 0.0)), 4),
                    "metadata": meta,
                }
            )
        return hits

    def delete_document(self, fingerprint: str) -> int:
        stats = self._index.describe_index_stats()
        count = (
            stats.get("namespaces", {}).get(fingerprint, {}).get("vector_count", 0)
        )
        if count:
            self._index.delete(delete_all=True, namespace=fingerprint)
        return count

    def list_documents(self) -> List[Dict]:
        stats = self._index.describe_index_stats()
        docs = []
        for ns, info in stats.get("namespaces", {}).items():
            docs.append(
                {
                    "fingerprint": ns,
                    "filename": "unknown",   # Pinecone stats don't return metadata
                    "chunk_count": info.get("vector_count", 0),
                }
            )
        return docs

    def get_stats(self) -> Dict:
        stats = self._index.describe_index_stats()
        return {
            "backend": "Pinecone",
            "index": self._index_name,
            "total_chunks": stats.get("total_vector_count", 0),
            "total_documents": len(stats.get("namespaces", {})),
        }


# ─────────────────────────────────────────────────────────
# Unified VectorStoreManager  (auto-selects backend)
# ─────────────────────────────────────────────────────────

class VectorStoreManager:
    """
    Unified interface that wraps either ChromaDB or Pinecone.

    Backend selection logic:
      1. If VECTOR_BACKEND=pinecone in environment AND PINECONE_API_KEY is set
         → uses Pinecone.
      2. Otherwise → uses local ChromaDB (persistent, zero-config).

    Usage example
    -------------
    >>> vsm = VectorStoreManager()
    >>> doc_id, chunks = vsm.index_document("report.pdf", full_text)
    >>> results = vsm.search("What is the methodology?", doc_fingerprint=doc_id)
    """

    def __init__(self):
        backend_env = os.getenv("VECTOR_BACKEND", "chroma").lower()
        pinecone_key = os.getenv("PINECONE_API_KEY", "")

        if backend_env == "pinecone" and pinecone_key:
            try:
                self._store = PineconeVectorStore()
                self.backend_name = "Pinecone"
            except Exception as exc:
                logger.warning(
                    "Pinecone init failed (%s). Falling back to ChromaDB.", exc
                )
                self._store = ChromaVectorStore()
                self.backend_name = "ChromaDB (fallback)"
        else:
            self._store = ChromaVectorStore()
            self.backend_name = "ChromaDB"

        logger.info("VectorStoreManager using backend: %s", self.backend_name)

    # ── High-level helpers ─────────────────────────────────

    def index_document(
        self,
        filename: str,
        text: str,
        extra_metadata: Optional[Dict] = None,
    ) -> Tuple[str, int]:
        """
        Index a document, skipping work if it's already in the store.

        Returns:
            (fingerprint, chunks_added)
            chunks_added == 0 means the document was already indexed.
        """
        fingerprint = compute_pdf_fingerprint(text)
        chunks_added = self._store.add_document(
            filename=filename,
            text=text,
            fingerprint=fingerprint,
            extra_metadata=extra_metadata,
        )
        return fingerprint, chunks_added

    def is_already_indexed(self, text: str) -> Tuple[bool, str]:
        """
        Check whether a document (identified by its text) is already in the store.

        Returns:
            (already_indexed: bool, fingerprint: str)
        """
        fingerprint = compute_pdf_fingerprint(text)
        exists = self._store.document_exists(fingerprint)
        return exists, fingerprint

    def search(
        self,
        query: str,
        n_results: int = 5,
        doc_fingerprint: Optional[str] = None,
    ) -> List[Dict]:
        """
        Semantic search across indexed documents (or within a single document).

        Args:
            query:          Natural-language query string.
            n_results:      Max number of chunks to return.
            doc_fingerprint: If provided, limit search to that document only.

        Returns:
            List of {text, score, metadata} dicts, sorted by score desc.
        """
        return self._store.query(
            query_text=query,
            n_results=n_results,
            fingerprint_filter=doc_fingerprint,
        )

    def build_rag_context(
        self,
        query: str,
        doc_fingerprint: Optional[str] = None,
        n_results: int = 6,
        min_score: float = 0.25,
    ) -> str:
        """
        Build a RAG (Retrieval-Augmented Generation) context string
        from the top-k most relevant chunks.

        Args:
            query:          The user's question.
            doc_fingerprint: Restrict to one document (recommended).
            n_results:      Number of chunks to retrieve.
            min_score:      Minimum cosine similarity to include.

        Returns:
            A single string suitable for injecting into the LLM prompt.
        """
        hits = self.search(query, n_results=n_results, doc_fingerprint=doc_fingerprint)
        relevant = [h for h in hits if h["score"] >= min_score]

        if not relevant:
            return ""

        parts = []
        for rank, hit in enumerate(relevant, 1):
            chunk_idx = hit["metadata"].get("chunk_index", "?")
            score = hit["score"]
            parts.append(
                f"[Chunk {rank} | chunk_index={chunk_idx} | relevance={score:.2f}]\n"
                + hit["text"]
            )

        return "\n\n---\n\n".join(parts)

    def delete_document(self, fingerprint: str) -> int:
        """Remove a document from the vector store. Returns chunks deleted."""
        return self._store.delete_document(fingerprint)

    def list_documents(self) -> List[Dict]:
        """List all indexed documents with metadata."""
        return self._store.list_documents()

    def get_stats(self) -> Dict:
        """Return backend statistics."""
        return self._store.get_stats()
