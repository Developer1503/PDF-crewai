"""
PDF Research Assistant v2.0 - Production Grade
Enhanced with persistent storage, citations, query optimization, and intelligent error handling
"""

import streamlit as st
import os
import tempfile
import time
from dotenv import load_dotenv
from gtts import gTTS
from io import BytesIO
import litellm
import speech_recognition as sr
from datetime import datetime

# Core imports
from config.llm import get_llm_with_smart_fallback
from tools.pdf_reader import PDFReadTool

# Enhanced utilities
from utils.storage_manager import StorageManager
from utils.error_handler import ErrorHandler
from utils.query_optimizer import QueryOptimizer
from utils.citation_engine import CitationEngine
from utils.pdf_validator import PDFValidator, DocumentAnalyzer
from utils.export_handler import ExportHandler
from components.ui_components import (
    show_status_indicator, show_document_fingerprint,
    show_citation_display, show_storage_stats,
    show_query_quality_feedback, show_token_estimate,
    show_error_message, show_document_workspace
)

# Try to import audio recorder
try:
    from audio_recorder_streamlit import audio_recorder
    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    AUDIO_RECORDER_AVAILABLE = False

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="PDF Research Assistant v2.0 | Enterprise Edition",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (keeping the premium glassmorphism design)
def load_custom_css():
    st.markdown("""
    <style>
        /* Modern Glassmorphism Theme */
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --bg-color: #0e1117;
            --card-surface: rgba(26, 29, 36, 0.8);
            --glass-border: rgba(255, 255, 255, 0.1);
        }
        
        /* Animated Background Gradient */
        .stApp {
            background-image: radial-gradient(circle at 10% 20%, rgba(102, 126, 234, 0.1) 0%, transparent 20%),
                              radial-gradient(circle at 90% 80%, rgba(118, 75, 162, 0.1) 0%, transparent 20%);
            background-attachment: fixed;
        }

        /* Card Styling */
        .glass-card {
            background: var(--card-surface);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .glass-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
            border-color: rgba(102, 126, 234, 0.4);
        }

        /* Chat Interface */
        .chat-message {
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 0.5rem;
            animation: fadeIn 0.3s ease;
        }
        
        .user-message {
            background: rgba(102, 126, 234, 0.1);
            border: 1px solid rgba(102, 126, 234, 0.2);
            margin-left: 2rem;
            border-bottom-right-radius: 2px;
        }
        
        .ai-message {
            background: rgba(26, 29, 36, 0.6);
            border: 1px solid var(--glass-border);
            margin-right: 2rem;
            border-bottom-left-radius: 2px;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Upload Area */
        .upload-area {
            border: 2px dashed rgba(102, 126, 234, 0.4);
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            background: rgba(102, 126, 234, 0.05);
            transition: all 0.3s ease;
        }

        .upload-area:hover {
            border-color: rgba(102, 126, 234, 0.8);
            background: rgba(102, 126, 234, 0.1);
        }
    </style>
    """, unsafe_allow_html=True)

load_custom_css()

# Initialize managers
def get_managers():
    """Initialize all manager instances"""
    return {
        'storage': StorageManager(ttl_days=30),
        'error_handler': ErrorHandler(),
        'query_optimizer': QueryOptimizer(),
        'citation_engine': CitationEngine(),
        'pdf_validator': PDFValidator(),
        'doc_analyzer': DocumentAnalyzer(),
        'export_handler': ExportHandler()
    }

# Initialize storage session state BEFORE creating managers
if 'storage_documents' not in st.session_state:
    st.session_state.storage_documents = {}
if 'storage_conversations' not in st.session_state:
    st.session_state.storage_conversations = {}
if 'storage_settings' not in st.session_state:
    st.session_state.storage_settings = {}
if 'storage_analytics' not in st.session_state:
    st.session_state.storage_analytics = {}

managers = get_managers()

# Session State Initialization
def init_session_state():
    defaults = {
        'pdf_uploaded': False,
        'pdf_content': None,
        'pdf_name': None,
        'pdf_path': None,
        'pdf_text': None,
        'current_doc_id': None,
        'chat_history': [],
        'processing': False,
        'provider': 'groq',
        'use_turbo': True,
        'voice_input': None,
        'voice_text': '',
        'show_citations': True,
        'legal_mode': False,
        'session_start': datetime.now().isoformat()
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Helper Functions
def extract_pdf_content(pdf_path):
    """Extract text content from PDF"""
    try:
        pdf_tool = PDFReadTool(pdf_path=pdf_path, analyze_images=False)
        content = pdf_tool._run()
        return content
    except Exception as e:
        error_info = managers['error_handler'].get_user_message(e, {'action': 'pdf_extraction'})
        show_error_message(error_info)
        return None

def get_ai_response_with_citations(user_query, pdf_context, provider="groq", use_turbo=True):
    """Get AI response with citation enforcement"""
    try:
        # Optimize query first
        optimized_query = managers['query_optimizer'].preprocess_question(user_query)
        
        # Optimize context to save tokens
        optimized_context = managers['query_optimizer'].optimize_context(
            pdf_context, optimized_query, max_tokens=3000
        )
        
        # Use smart fallback for provider selection
        llm, provider_used = get_llm_with_smart_fallback(
            primary_provider=provider,
            use_smaller_model=use_turbo
        )
        
        # Determine model and API key
        if provider_used == "gemini":
            model = "gemini/gemini-1.5-flash"
            api_key = os.getenv("GOOGLE_API_KEY")
        else:  # groq
            model = "groq/llama-3.1-8b-instant" if use_turbo else "groq/llama-3.3-70b-versatile"
            api_key = os.getenv("GROQ_API_KEY")
        
        # Enhanced system prompt with citations
        base_prompt = f"""You are an expert PDF research assistant. You help users understand and analyze PDF documents.

Document Context:
{optimized_context[:10000]}

Instructions:
- Answer questions based on the document content
- Be concise but thorough
- If information isn't in the document, say so clearly
- Provide specific quotes or references when possible
- Format your responses clearly with markdown"""
        
        # Add citation requirements
        system_prompt = managers['citation_engine'].enhance_system_prompt(base_prompt)
        
        # Create messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": optimized_query}
        ]
        
        # Get response
        response = litellm.completion(
            model=model,
            messages=messages,
            api_key=api_key,
            temperature=0.3
        )
        
        raw_response = response.choices[0].message.content
        
        # Extract citations
        citation_info = managers['citation_engine'].extract_citations(raw_response)
        
        # Verify citations if in legal mode
        verification = None
        if st.session_state.legal_mode:
            verification = managers['citation_engine'].verify_citation(
                citation_info, pdf_context
            )
        
        return {
            'response': raw_response,
            'citation': citation_info,
            'verification': verification,
            'provider': provider_used,
            'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 0
        }
        
    except Exception as e:
        error_info = managers['error_handler'].get_user_message(
            e, {'provider': provider, 'action': 'ai_query'}
        )
        return {
            'error': error_info,
            'response': None
        }

def transcribe_audio(audio_bytes):
    """Convert audio to text using speech recognition"""
    try:
        recognizer = sr.Recognizer()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
            tmp_audio.write(audio_bytes)
            tmp_audio_path = tmp_audio.name
        
        with sr.AudioFile(tmp_audio_path) as source:
            audio_data = recognizer.record(source)
        
        text = recognizer.recognize_google(audio_data)
        os.unlink(tmp_audio_path)
        
        return text
    except sr.UnknownValueError:
        return "❌ Could not understand audio. Please try again."
    except sr.RequestError as e:
        return f"❌ Speech recognition service error: {e}"
    except Exception as e:
        return f"❌ Error processing audio: {e}"

# Main App
def main():
    # Sidebar
    with st.sidebar:
        st.markdown("### 🧭 Control Center")
        
        # API Status
        col1, col2 = st.columns(2)
        with col1:
            groq_ok = "✅" if os.getenv("GROQ_API_KEY") else "❌"
            st.markdown(f"{groq_ok} **Groq**")
        with col2:
            gemini_ok = "✅" if os.getenv("GOOGLE_API_KEY") else "❌"
            st.markdown(f"{gemini_ok} **Gemini**")
        
        st.divider()
        
        # Settings
        st.markdown("### ⚙️ Settings")
        st.session_state.provider = st.selectbox(
            "AI Provider", 
            ["groq", "gemini"], 
            index=0, 
            help="Groq is recommended for better rate limits"
        )
        
        st.session_state.use_turbo = st.toggle(
            "⚡ Turbo Mode", 
            value=True, 
            help="Use smaller, faster models to save tokens"
        )
        
        st.session_state.show_citations = st.toggle(
            "📚 Show Citations",
            value=True,
            help="Display source citations with responses"
        )
        
        st.session_state.legal_mode = st.toggle(
            "⚖️ Legal-Grade Citations",
            value=False,
            help="Stricter citation verification (slower)"
        )
        
        st.divider()
        
        # Storage Stats
        st.markdown("### 💾 Storage")
        stats = managers['storage'].get_storage_stats()
        show_storage_stats(stats)
        
        if st.button("🧹 Cleanup Old Data", use_container_width=True):
            deleted = managers['storage'].cleanup_old_data()
            st.success(f"Deleted {deleted} old document(s)")
            st.rerun()
        
        st.divider()
        
        # Document Management
        if st.session_state.pdf_uploaded:
            st.markdown("### 📄 Current Document")
            st.success(f"✅ {st.session_state.pdf_name}")
            
            if st.button("🗑️ Remove Document", use_container_width=True):
                st.session_state.pdf_uploaded = False
                st.session_state.pdf_content = None
                st.session_state.pdf_name = None
                st.session_state.pdf_path = None
                st.session_state.pdf_text = None
                st.session_state.current_doc_id = None
                st.session_state.chat_history = []
                st.rerun()
        
        # Export Options
        if st.session_state.chat_history:
            st.divider()
            st.markdown("### 📥 Export")
            
            export_format = st.selectbox(
                "Format",
                ["Markdown", "JSON", "HTML", "Text", "Summary Report"]
            )
            
            if st.button("📥 Export Conversation", use_container_width=True):
                doc_info = {
                    'filename': st.session_state.pdf_name,
                    'upload_date': datetime.now().isoformat(),
                    'size_mb': 0
                }
                
                if export_format == "Markdown":
                    export_data = managers['export_handler'].export_to_markdown(
                        st.session_state.chat_history, doc_info
                    )
                    st.download_button(
                        "💾 Download MD",
                        export_data,
                        file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown"
                    )
                elif export_format == "JSON":
                    export_data = managers['export_handler'].export_to_json(
                        st.session_state.chat_history, doc_info
                    )
                    st.download_button(
                        "💾 Download JSON",
                        export_data,
                        file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                elif export_format == "HTML":
                    export_data = managers['export_handler'].export_to_html(
                        st.session_state.chat_history, doc_info
                    )
                    st.download_button(
                        "💾 Download HTML",
                        export_data,
                        file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html"
                    )
                elif export_format == "Text":
                    export_data = managers['export_handler'].export_to_text(
                        st.session_state.chat_history, doc_info
                    )
                    st.download_button(
                        "💾 Download TXT",
                        export_data,
                        file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                else:  # Summary Report
                    export_data = managers['export_handler'].create_summary_report(
                        st.session_state.chat_history, doc_info
                    )
                    st.download_button(
                        "💾 Download Report",
                        export_data,
                        file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown"
                    )
        
        st.divider()
        
        if st.button("🔄 Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; opacity: 0.6; font-size: 0.8rem;'>
            <p>🧬 PDF Research Assistant v2.0</p>
            <p>Enterprise Edition</p>
        </div>
        """, unsafe_allow_html=True)

    # Main Area
    st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>🧬 PDF Research Assistant v2.0</h1>", unsafe_allow_html=True)
    
    # Check for session recovery
    if not st.session_state.pdf_uploaded:
        stored_docs = managers['storage'].list_documents()
        
        if stored_docs:
            st.info(f"📂 Found {len(stored_docs)} previously uploaded document(s). Would you like to continue?")
            selected_doc_id = show_document_workspace(stored_docs)
            
            if selected_doc_id:
                # Load document
                doc = managers['storage'].get_document(selected_doc_id)
                if doc:
                    st.session_state.pdf_name = doc['filename']
                    st.session_state.pdf_text = managers['storage'].get_document_text(selected_doc_id)
                    st.session_state.current_doc_id = selected_doc_id
                    st.session_state.pdf_uploaded = True
                    
                    # Load conversation
                    conv = managers['storage'].get_conversation(selected_doc_id)
                    if conv:
                        st.session_state.chat_history = conv
                    
                    st.rerun()
    
    # Upload Section
    if not st.session_state.pdf_uploaded:
        st.markdown("""
        <div class='glass-card' style='text-align: center; padding: 3rem;'>
            <h2>📤 Upload Your PDF Document</h2>
            <p style='opacity: 0.8; margin-top: 1rem;'>Upload a PDF to start asking questions and getting AI-powered insights</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file", 
            type="pdf", 
            help="Upload a research paper, report, contract, or any PDF document"
        )
        
        if uploaded_file:
            with st.spinner("📖 Analyzing your document..."):
                # Save temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    st.session_state.pdf_path = tmp.name
                
                # Validate PDF
                file_size = len(uploaded_file.getvalue())
                
                # Extract sample for validation
                pdf_text = extract_pdf_content(st.session_state.pdf_path)
                
                if pdf_text:
                    # Validate
                    validation = managers['pdf_validator'].validate_pdf(
                        st.session_state.pdf_path,
                        file_size,
                        pdf_text[:1000]
                    )
                    
                    # Show warnings
                    for warning in validation['warnings']:
                        st.warning(warning)
                    
                    for error in validation['errors']:
                        st.error(error)
                    
                    if not validation['valid']:
                        st.stop()
                    
                    # Generate document fingerprint
                    fingerprint = managers['doc_analyzer'].generate_document_fingerprint(
                        pdf_text, uploaded_file.name
                    )
                    
                    # Show fingerprint
                    show_document_fingerprint(fingerprint)
                    
                    # Store document
                    doc_id = managers['storage'].store_document(
                        uploaded_file.name,
                        pdf_text,
                        metadata=fingerprint
                    )
                    
                    if doc_id.startswith("DUPLICATE:"):
                        real_id = doc_id.split(":")[1]
                        st.warning(f"⚠️ This document was already uploaded. Loading previous version...")
                        doc_id = real_id
                    
                    # Set session state
                    st.session_state.pdf_name = uploaded_file.name
                    st.session_state.pdf_text = pdf_text
                    st.session_state.current_doc_id = doc_id
                    st.session_state.pdf_uploaded = True
                    st.session_state.chat_history = [{
                        "role": "assistant",
                        "content": f"✅ **Document loaded successfully!**\n\n📄 **{uploaded_file.name}**\n\nI've analyzed your {fingerprint['type']} document. What would you like to know about it?"
                    }]
                    
                    st.rerun()
                else:
                    st.error("Failed to read PDF. Please try another file.")
    
    # Chat Interface
    else:
        st.markdown("### 💬 Chat with Your Document")
        
        # Chat History
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">👤 You</div>
                        <div>{msg['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message ai-message">
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">🤖 AI Assistant</div>
                        <div>{msg['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Quick Actions
        st.markdown("**💡 Quick Actions:**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📝 Summarize", use_container_width=True):
                user_query = "Please provide a comprehensive summary of this document, highlighting the key points, main findings, and conclusions."
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                st.rerun()
        
        with col2:
            if st.button("🔍 Key Findings", use_container_width=True):
                user_query = "What are the main findings or key takeaways from this document?"
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                st.rerun()
        
        with col3:
            if st.button("📊 Analyze", use_container_width=True):
                user_query = "Provide a detailed analysis of this document, including methodology, results, and implications."
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                st.rerun()
        
        with col4:
            if st.button("❓ Q&A", use_container_width=True):
                user_query = "What questions should I ask about this document to better understand it?"
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Voice Input
        if AUDIO_RECORDER_AVAILABLE:
            st.markdown("**🎤 Voice Input** (Click to record, click again to stop)")
            audio_bytes = audio_recorder(
                text="",
                recording_color="#667eea",
                neutral_color="#6aa36f",
                icon_name="microphone",
                icon_size="2x",
            )
            
            if audio_bytes and audio_bytes != st.session_state.voice_input:
                st.session_state.voice_input = audio_bytes
                with st.spinner("🎧 Transcribing your voice..."):
                    transcribed_text = transcribe_audio(audio_bytes)
                    if transcribed_text and not transcribed_text.startswith("❌"):
                        st.session_state.voice_text = transcribed_text
                        st.success(f"✅ Transcribed: {transcribed_text}")
                        st.session_state.chat_history.append({"role": "user", "content": transcribed_text})
                        st.session_state.voice_text = ""
                        st.rerun()
                    else:
                        st.error(transcribed_text)
        
        st.markdown("---")
        
        # Text Input
        st.markdown("**⌨️ Text Input**")
        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                user_input = st.text_input(
                    "Ask anything about your document...",
                    placeholder="e.g., What are the main conclusions? Who are the authors? What methodology was used?",
                    label_visibility="collapsed",
                    value=st.session_state.voice_text
                )
            
            with col2:
                submit = st.form_submit_button("Send 🚀", use_container_width=True)
            
            if submit and user_input:
                # Check query quality
                quality = managers['query_optimizer'].score_question_quality(user_input)
                show_query_quality_feedback(quality)
                
                # Check for duplicates
                duplicate = managers['query_optimizer'].find_duplicate_question(user_input)
                if duplicate:
                    st.info(f"💡 You asked a similar question before: \"{duplicate['previous_question']}\"")
                    if st.button("Show previous answer"):
                        st.write(duplicate['previous_answer'])
                
                # Estimate tokens
                token_info = managers['query_optimizer'].estimate_token_cost(
                    user_input, st.session_state.pdf_text
                )
                show_token_estimate(token_info)
                
                # Add to history
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                st.session_state.voice_text = ""
                st.rerun()
        
        # Process last user message
        if (len(st.session_state.chat_history) > 0 and 
            st.session_state.chat_history[-1]["role"] == "user" and
            not st.session_state.processing):
            
            st.session_state.processing = True
            
            with st.spinner("🤔 Thinking..."):
                user_query = st.session_state.chat_history[-1]["content"]
                
                # Get AI response with citations
                result = get_ai_response_with_citations(
                    user_query,
                    st.session_state.pdf_text,
                    st.session_state.provider,
                    st.session_state.use_turbo
                )
                
                if 'error' in result:
                    # Show error
                    show_error_message(result['error'])
                    st.session_state.processing = False
                else:
                    # Format response with citations
                    if st.session_state.show_citations and result['citation']['has_citation']:
                        formatted_response = managers['citation_engine'].format_citation_display(
                            result['citation'],
                            result.get('verification')
                        )
                    else:
                        formatted_response = result['response']
                    
                    # Add provider info if switched
                    if result['provider'] and result['provider'] != st.session_state.provider:
                        formatted_response = f"ℹ️ *Switched to {result['provider'].upper()}*\n\n{formatted_response}"
                    
                    # Add to history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": formatted_response
                    })
                    
                    # Add to query optimizer history
                    managers['query_optimizer'].add_to_history(user_query, formatted_response)
                    
                    # Save conversation
                    if st.session_state.current_doc_id:
                        managers['storage'].update_conversation(
                            st.session_state.current_doc_id,
                            st.session_state.chat_history
                        )
                    
                    st.session_state.processing = False
                    st.rerun()

if __name__ == "__main__":
    main()
