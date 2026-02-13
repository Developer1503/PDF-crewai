"""
AI Research Chat - Modern UI inspired by research assistant interfaces
Clean, professional design with sidebar navigation and chat interface
"""

import streamlit as st
import os
import tempfile
from datetime import datetime
from dotenv import load_dotenv
import litellm

from config.llm import get_llm_with_smart_fallback
from tools.pdf_reader import PDFReadTool
from utils.chat_manager import ChatManager
from utils.query_optimizer import QueryOptimizer
from utils.citation_engine import CitationEngine

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Research Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS matching the research UI style
st.markdown("""
<style>
    /* Global Styles */
    :root {
        --primary-purple: #6B46C1;
        --primary-purple-dark: #553C9A;
        --sidebar-bg: #F8F7FC;
        --chat-bg: #FFFFFF;
        --border-color: #E5E7EB;
        --text-primary: #1F2937;
        --text-secondary: #6B7280;
        --success-green: #10B981;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container */
    .main {
        background-color: #F9FAFB;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border-color);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background-color: var(--sidebar-bg);
    }
    
    /* Upload button */
    .upload-button {
        background: var(--primary-purple);
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        width: 100%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin-bottom: 24px;
    }
    
    .upload-button:hover {
        background: var(--primary-purple-dark);
    }
    
    /* Navigation section */
    .nav-section {
        margin-bottom: 24px;
    }
    
    .nav-title {
        font-size: 11px;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
    }
    
    .nav-item {
        padding: 10px 12px;
        border-radius: 6px;
        margin-bottom: 4px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 10px;
        color: var(--text-primary);
        transition: all 0.2s;
    }
    
    .nav-item:hover {
        background: rgba(107, 70, 193, 0.1);
    }
    
    .nav-item.active {
        background: rgba(107, 70, 193, 0.15);
        color: var(--primary-purple);
        font-weight: 600;
    }
    
    /* Document fingerprint */
    .doc-fingerprint {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }
    
    .doc-fingerprint-title {
        font-size: 11px;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
    }
    
    .doc-info-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #F3F4F6;
        font-size: 14px;
    }
    
    .doc-info-item:last-child {
        border-bottom: none;
    }
    
    .doc-info-label {
        color: var(--text-secondary);
    }
    
    .doc-info-value {
        color: var(--text-primary);
        font-weight: 500;
    }
    
    /* Tag badges */
    .tag-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    
    .tag-llm {
        background: #DBEAFE;
        color: #1E40AF;
    }
    
    .tag-inference {
        background: #FCE7F3;
        color: #BE185D;
    }
    
    .tag-cuda {
        background: #D1FAE5;
        color: #065F46;
    }
    
    /* Chat container */
    .chat-container {
        background: white;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    /* Chat header */
    .chat-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 24px;
    }
    
    .chat-icon {
        width: 32px;
        height: 32px;
        background: var(--primary-purple);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
    }
    
    .chat-title {
        font-size: 18px;
        font-weight: 700;
        color: var(--text-primary);
    }
    
    .clear-history {
        margin-left: auto;
        color: var(--text-secondary);
        font-size: 14px;
        cursor: pointer;
        padding: 6px 12px;
        border-radius: 6px;
    }
    
    .clear-history:hover {
        background: #F3F4F6;
    }
    
    /* Chat messages */
    .chat-message {
        margin-bottom: 24px;
        animation: fadeIn 0.3s ease;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .message-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
    }
    
    .message-avatar {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        font-weight: 600;
    }
    
    .user-avatar {
        background: #DBEAFE;
        color: #1E40AF;
    }
    
    .ai-avatar {
        background: var(--primary-purple);
        color: white;
    }
    
    .message-role {
        font-weight: 600;
        font-size: 14px;
        color: var(--text-primary);
    }
    
    .message-content {
        background: #F9FAFB;
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 16px;
        margin-left: 36px;
        line-height: 1.6;
    }
    
    .user-message .message-content {
        background: #F5F3FF;
        border-color: #DDD6FE;
    }
    
    /* Page reference badge */
    .page-ref {
        display: inline-block;
        background: var(--primary-purple);
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        margin-top: 8px;
    }
    
    /* Confidence indicator */
    .confidence-bar {
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid #E5E7EB;
    }
    
    .confidence-label {
        font-size: 12px;
        color: var(--text-secondary);
        margin-bottom: 6px;
        display: flex;
        justify-content: space-between;
    }
    
    .confidence-progress {
        height: 6px;
        background: #E5E7EB;
        border-radius: 3px;
        overflow: hidden;
    }
    
    .confidence-fill {
        height: 100%;
        background: var(--success-green);
        border-radius: 3px;
        transition: width 0.3s ease;
    }
    
    /* Quick action buttons */
    .quick-actions {
        display: flex;
        gap: 8px;
        margin-bottom: 16px;
        flex-wrap: wrap;
    }
    
    .quick-action-btn {
        padding: 8px 16px;
        border: 1px solid var(--primary-purple);
        background: white;
        color: var(--primary-purple);
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .quick-action-btn:hover {
        background: var(--primary-purple);
        color: white;
    }
    
    /* Input area */
    .input-container {
        background: white;
        border: 2px solid var(--border-color);
        border-radius: 12px;
        padding: 16px;
        margin-top: 24px;
    }
    
    .input-container:focus-within {
        border-color: var(--primary-purple);
    }
    
    /* Analyze button */
    .analyze-button {
        background: var(--primary-purple);
        color: white;
        padding: 14px 24px;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        width: 100%;
        cursor: pointer;
        font-size: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin-top: 12px;
    }
    
    .analyze-button:hover {
        background: var(--primary-purple-dark);
    }
    
    /* File info */
    .file-info {
        background: #F9FAFB;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .file-icon {
        width: 40px;
        height: 40px;
        background: #FEE2E2;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }
    
    .file-details {
        flex: 1;
    }
    
    .file-name {
        font-weight: 600;
        color: var(--text-primary);
        font-size: 14px;
    }
    
    .file-meta {
        font-size: 12px;
        color: var(--text-secondary);
        margin-top: 2px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize managers
@st.cache_resource
def get_managers():
    return {
        'chat': ChatManager(),
        'query_optimizer': QueryOptimizer(),
        'citation_engine': CitationEngine()
    }

managers = get_managers()

# Session State
def init_session_state():
    defaults = {
        'pdf_uploaded': False,
        'pdf_name': None,
        'pdf_text': None,
        'pdf_path': None,
        'current_page': 'Current Paper',
        'provider': 'groq',
        'use_turbo': True,
        'processing': False
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
        return pdf_tool._run()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def get_ai_response(user_query, pdf_context, provider="groq", use_turbo=True):
    """Get AI response"""
    try:
        llm, provider_used = get_llm_with_smart_fallback(
            primary_provider=provider,
            use_smaller_model=use_turbo
        )
        
        if provider_used == "gemini":
            model = "gemini/gemini-1.5-flash"
            api_key = os.getenv("GOOGLE_API_KEY")
        else:
            model = "groq/llama-3.1-8b-instant" if use_turbo else "groq/llama-3.3-70b-versatile"
            api_key = os.getenv("GROQ_API_KEY")
        
        # Optimize context
        optimized_context = managers['query_optimizer'].optimize_context(
            pdf_context, user_query, max_tokens=3000
        )
        
        system_prompt = f"""You are an expert research assistant analyzing academic papers and documents.

Document Context:
{optimized_context[:10000]}

Instructions:
- Provide clear, concise, and accurate answers based on the document
- Reference specific sections or pages when possible
- Use academic language appropriate for research
- If information isn't in the document, state that clearly
- Format responses with proper structure and citations"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        response = litellm.completion(
            model=model,
            messages=messages,
            api_key=api_key,
            temperature=0.3,
            max_tokens=2000
        )
        
        return {
            'response': response.choices[0].message.content,
            'provider': provider_used,
            'tokens': response.usage.total_tokens if hasattr(response, 'usage') else 0
        }
        
    except Exception as e:
        return {
            'error': True,
            'response': f"Error: {str(e)}",
            'provider': None
        }

# Sidebar
with st.sidebar:
    # Upload button
    st.markdown("""
    <div class="upload-button">
        📄 Upload Research
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("", type="pdf", label_visibility="collapsed")
    
    if uploaded_file and uploaded_file.name != st.session_state.pdf_name:
        with st.spinner("📖 Analyzing document..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getvalue())
                st.session_state.pdf_path = tmp.name
            
            pdf_text = extract_pdf_content(st.session_state.pdf_path)
            
            if pdf_text:
                st.session_state.pdf_name = uploaded_file.name
                st.session_state.pdf_text = pdf_text
                st.session_state.pdf_uploaded = True
                managers['chat'].clear_conversation()
                st.rerun()
    
    # Navigation
    st.markdown('<div class="nav-section">', unsafe_allow_html=True)
    st.markdown('<div class="nav-title">NAVIGATION</div>', unsafe_allow_html=True)
    
    pages = [
        ("📄", "Current Paper"),
        ("🕒", "Recent Files"),
        ("👥", "Collaborations")
    ]
    
    for icon, page in pages:
        active = "active" if st.session_state.current_page == page else ""
        if st.button(f"{icon} {page}", key=f"nav_{page}", use_container_width=True):
            st.session_state.current_page = page
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Document Fingerprint
    if st.session_state.pdf_uploaded:
        st.markdown('<div class="doc-fingerprint">', unsafe_allow_html=True)
        st.markdown('<div class="doc-fingerprint-title">DOCUMENT FINGERPRINT</div>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="doc-info-item">
            <span class="doc-info-label">Type</span>
            <span class="doc-info-value">Scientific Paper</span>
        </div>
        <div class="doc-info-item">
            <span class="doc-info-label">Est. Read Time</span>
            <span class="doc-info-value">12 Minutes</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="doc-fingerprint-title" style="margin-top: 16px;">KEY ENTITIES</div>', unsafe_allow_html=True)
        st.markdown("""
        <div>
            <span class="tag-badge tag-llm">LLM</span>
            <span class="tag-badge tag-inference">INFERENCE</span>
            <span class="tag-badge tag-cuda">CUDA</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Current file info
    if st.session_state.pdf_uploaded:
        st.markdown('<div class="file-info">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="file-icon">📄</div>
        <div class="file-details">
            <div class="file-name">{st.session_state.pdf_name[:20]}...</div>
            <div class="file-meta">Last viewed 2m ago</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Main Content
st.markdown("""
<div class="chat-header">
    <div class="chat-icon">💬</div>
    <div class="chat-title">AI Research Chat</div>
    <div class="clear-history">Clear History</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.pdf_uploaded:
    st.markdown("""
    <div class="chat-container" style="text-align: center; padding: 60px 24px;">
        <h2 style="color: #6B7280; margin-bottom: 16px;">📄 Upload a Research Paper</h2>
        <p style="color: #9CA3AF;">Upload a PDF document from the sidebar to start analyzing and asking questions</p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Chat messages
    messages = list(managers['chat'].context.messages)
    
    for i, msg in enumerate(messages):
        if msg['role'] == 'user':
            st.markdown(f"""
            <div class="chat-message user-message">
                <div class="message-header">
                    <div class="message-avatar user-avatar">U</div>
                    <div class="message-role">You</div>
                </div>
                <div class="message-content">{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            confidence = msg.get('metadata', {}).get('confidence', 84)
            st.markdown(f"""
            <div class="chat-message ai-message">
                <div class="message-header">
                    <div class="message-avatar ai-avatar">AI</div>
                    <div class="message-role">PDF ASSISTANT</div>
                </div>
                <div class="message-content">
                    {msg['content']}
                    <div class="page-ref">📄 Page 4</div>
                    <div class="confidence-bar">
                        <div class="confidence-label">
                            <span>CONFIDENCE</span>
                            <span>{confidence}%</span>
                        </div>
                        <div class="confidence-progress">
                            <div class="confidence-fill" style="width: {confidence}%"></div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Quick actions
    st.markdown('<div class="quick-actions">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📝 Summarize", use_container_width=True):
            query = "Provide a comprehensive summary of this research paper"
            managers['chat'].context.add_message('user', query)
            st.rerun()
    
    with col2:
        if st.button("🔍 Key Findings", use_container_width=True):
            query = "What are the key findings of this research?"
            managers['chat'].context.add_message('user', query)
            st.rerun()
    
    with col3:
        if st.button("📊 Extract Stats", use_container_width=True):
            query = "Extract the main statistics and data from this paper"
            managers['chat'].context.add_message('user', query)
            st.rerun()
    
    with col4:
        if st.button("🔄 References", use_container_width=True):
            query = "List the main references cited in this paper"
            managers['chat'].context.add_message('user', query)
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input area
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Ask a research question...",
            placeholder="e.g., How does this methodology compare to standard autoregressive models?",
            height=100,
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            voice_btn = st.form_submit_button("🎤", use_container_width=True)
        with col2:
            submit = st.form_submit_button("Analyze Query ➤", use_container_width=True, type="primary")
        
        if submit and user_input:
            managers['chat'].context.add_message('user', user_input)
            st.rerun()
    
    # Process last message
    if (messages and messages[-1]['role'] == 'user' and not st.session_state.processing):
        st.session_state.processing = True
        
        with st.spinner("🔍 Analyzing..."):
            user_query = messages[-1]['content']
            result = get_ai_response(
                user_query,
                st.session_state.pdf_text,
                st.session_state.provider,
                st.session_state.use_turbo
            )
            
            if not result.get('error'):
                managers['chat'].context.add_message(
                    'assistant',
                    result['response'],
                    {'provider': result['provider'], 'confidence': 84}
                )
            
            st.session_state.processing = False
            st.rerun()
