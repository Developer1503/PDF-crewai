"""
Persistent Storage Manager using Browser-Compatible Methods
Handles IndexedDB-like persistence through Streamlit session state
"""

import json
import hashlib
import gzip
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import streamlit as st


class StorageManager:
    """
    Manages persistent storage for documents, conversations, and settings
    Uses Streamlit session state with serialization for persistence
    """
    
    def __init__(self, ttl_days: int = 30):
        self.ttl_days = ttl_days
        self._init_storage()
    
    def _init_storage(self):
        """Initialize storage structures in session state"""
        if 'storage_documents' not in st.session_state:
            st.session_state.storage_documents = {}
        
        if 'storage_conversations' not in st.session_state:
            st.session_state.storage_conversations = {}
        
        if 'storage_settings' not in st.session_state:
            st.session_state.storage_settings = {
                'user_id': self._generate_device_id(),
                'preferences': {},
                'quota_usage': {}
            }
        
        if 'storage_analytics' not in st.session_state:
            st.session_state.storage_analytics = []
    
    def _generate_device_id(self) -> str:
        """Generate a unique device identifier"""
        # Use a combination of timestamp and random data for uniqueness
        import uuid
        return str(uuid.uuid4())
    
    def generate_document_id(self, content: str) -> str:
        """Generate unique document ID from content hash"""
        # Hash first 1KB for quick fingerprinting
        sample = content[:1024] if len(content) > 1024 else content
        return hashlib.sha256(sample.encode()).hexdigest()[:16]
    
    def compress_text(self, text: str) -> str:
        """Compress text using gzip and base64 encode"""
        compressed = gzip.compress(text.encode('utf-8'))
        return base64.b64encode(compressed).decode('ascii')
    
    def decompress_text(self, compressed: str) -> str:
        """Decompress base64 encoded gzipped text"""
        decoded = base64.b64decode(compressed.encode('ascii'))
        return gzip.decompress(decoded).decode('utf-8')
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        return chunks
    
    def store_document(self, filename: str, text: str, metadata: Dict = None) -> str:
        """
        Store document with compression and chunking
        Returns document ID
        """
        doc_id = self.generate_document_id(text)
        self._init_storage()
        
        # Check if document already exists
        if doc_id in st.session_state.storage_documents:
            existing = st.session_state.storage_documents[doc_id]
            if existing['filename'] != filename:
                # Same content, different name - warn user
                return f"DUPLICATE:{doc_id}"
        
        # Chunk and compress text
        chunks = self.chunk_text(text)
        compressed_chunks = [self.compress_text(chunk) for chunk in chunks]
        
        # Store document
        st.session_state.storage_documents[doc_id] = {
            'id': doc_id,
            'filename': filename,
            'upload_date': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'text_chunks': compressed_chunks,
            'chunk_count': len(chunks),
            'original_size': len(text),
            'compressed_size': sum(len(c) for c in compressed_chunks),
            'metadata': metadata or {}
        }
        
        return doc_id
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Retrieve document by ID"""
        if doc_id not in st.session_state.storage_documents:
            return None
        
        doc = st.session_state.storage_documents[doc_id]
        
        # Update last accessed
        doc['last_accessed'] = datetime.now().isoformat()
        
        return doc
    
    def get_document_text(self, doc_id: str) -> Optional[str]:
        """Get full decompressed document text"""
        doc = self.get_document(doc_id)
        if not doc:
            return None
        
        # Decompress all chunks and join
        chunks = [self.decompress_text(c) for c in doc['text_chunks']]
        return ' '.join(chunks)
    
    def list_documents(self) -> List[Dict]:
        """List all stored documents with metadata"""
        self._init_storage()
        docs = []
        for doc_id, doc in st.session_state.storage_documents.items():
            docs.append({
                'id': doc_id,
                'filename': doc['filename'],
                'upload_date': doc['upload_date'],
                'last_accessed': doc['last_accessed'],
                'size_mb': doc['original_size'] / (1024 * 1024),
                'compression_ratio': doc['original_size'] / doc['compressed_size'] if doc['compressed_size'] > 0 else 1
            })
        
        # Sort by last accessed (most recent first)
        docs.sort(key=lambda x: x['last_accessed'], reverse=True)
        return docs
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete document and associated conversations"""
        if doc_id not in st.session_state.storage_documents:
            return False
        
        # Delete document
        del st.session_state.storage_documents[doc_id]
        
        # Delete associated conversations
        conv_to_delete = [
            conv_id for conv_id, conv in st.session_state.storage_conversations.items()
            if conv.get('document_id') == doc_id
        ]
        
        for conv_id in conv_to_delete:
            del st.session_state.storage_conversations[conv_id]
        
        return True
    
    def store_conversation(self, doc_id: str, messages: List[Dict]) -> str:
        """Store conversation for a document"""
        import uuid
        conv_id = str(uuid.uuid4())
        
        st.session_state.storage_conversations[conv_id] = {
            'id': conv_id,
            'document_id': doc_id,
            'messages': messages,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        return conv_id
    
    def get_conversation(self, doc_id: str) -> Optional[List[Dict]]:
        """Get most recent conversation for a document"""
        conversations = [
            conv for conv in st.session_state.storage_conversations.values()
            if conv.get('document_id') == doc_id
        ]
        
        if not conversations:
            return None
        
        # Return most recent
        conversations.sort(key=lambda x: x['updated_at'], reverse=True)
        return conversations[0]['messages']
    
    def update_conversation(self, doc_id: str, messages: List[Dict]):
        """Update existing conversation or create new one"""
        # Find existing conversation
        for conv_id, conv in st.session_state.storage_conversations.items():
            if conv.get('document_id') == doc_id:
                conv['messages'] = messages
                conv['updated_at'] = datetime.now().isoformat()
                return
        
        # Create new if not found
        self.store_conversation(doc_id, messages)
    
    def cleanup_old_data(self):
        """Remove data older than TTL"""
        cutoff = datetime.now() - timedelta(days=self.ttl_days)
        cutoff_iso = cutoff.isoformat()
        
        # Clean documents
        docs_to_delete = [
            doc_id for doc_id, doc in st.session_state.storage_documents.items()
            if doc['last_accessed'] < cutoff_iso
        ]
        
        for doc_id in docs_to_delete:
            self.delete_document(doc_id)
        
        return len(docs_to_delete)
    
    def get_storage_stats(self) -> Dict:
        """Get storage usage statistics"""
        # Force initialization before accessing session state
        self._init_storage()
        total_docs = len(st.session_state.storage_documents)
        total_convs = len(st.session_state.storage_conversations)
        
        total_size = sum(
            doc['original_size'] 
            for doc in st.session_state.storage_documents.values()
        )
        
        compressed_size = sum(
            doc['compressed_size']
            for doc in st.session_state.storage_documents.values()
        )
        
        return {
            'document_count': total_docs,
            'conversation_count': total_convs,
            'total_size_mb': total_size / (1024 * 1024),
            'compressed_size_mb': compressed_size / (1024 * 1024),
            'compression_ratio': total_size / compressed_size if compressed_size > 0 else 1,
            'storage_limit_mb': 50,  # Browser typical limit
            'usage_percent': (compressed_size / (50 * 1024 * 1024)) * 100
        }
    
    def export_to_json(self) -> str:
        """Export all data to JSON string"""
        export_data = {
            'documents': st.session_state.storage_documents,
            'conversations': st.session_state.storage_conversations,
            'settings': st.session_state.storage_settings,
            'export_date': datetime.now().isoformat(),
            'version': '2.0.0'
        }
        
        return json.dumps(export_data, indent=2)
    
    def import_from_json(self, json_str: str) -> bool:
        """Import data from JSON string"""
        try:
            data = json.loads(json_str)
            
            st.session_state.storage_documents = data.get('documents', {})
            st.session_state.storage_conversations = data.get('conversations', {})
            st.session_state.storage_settings = data.get('settings', {})
            
            return True
        except Exception as e:
            print(f"Import failed: {e}")
            return False
