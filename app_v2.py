"""
AI Research Chat v3.1 — Enhanced Chat Area
Modern research UI with reactions, copy/save, typing indicator,
structured response cards, and inline page previews.
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
from components.chat_ui import (
    apply_enhanced_chat_styles,
    render_typing_indicator,
    render_message_bubble,
    render_stats_card,
    detect_page_references,
    inject_clipboard_script,
    _detect_stats,
)

# Load environment variables
load_dotenv()

# ──────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI Research Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────
# Custom CSS (page-level: sidebar, layout, etc.)
# ──────────────────────────────────────────────
st.markdown("""
<style>
    /* ── CSS Variables ── */
    :root {
        --primary-purple: #6B46C1;
        --primary-purple-dark: #553C9A;
        --primary-purple-light: #8B5CF6;
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

    /* Main container */
    .main { background-color: #F9FAFB; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border-color);
    }
    [data-testid="stSidebar"] > div:first-child {
        background-color: var(--sidebar-bg);
    }

    /* Upload button */
    .upload-button {
        background: linear-gradient(135deg, var(--primary-purple), var(--primary-purple-light));
        color: white;
        padding: 12px 24px;
        border-radius: 10px;
        border: none;
        font-weight: 600;
        width: 100%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(107,70,193,0.3);
        transition: all 0.2s ease;
    }
    .upload-button:hover {
        background: linear-gradient(135deg, var(--primary-purple-dark), var(--primary-purple));
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(107,70,193,0.4);
    }

    /* Navigation */
    .nav-section { margin-bottom: 24px; }
    .nav-title {
        font-size: 11px; font-weight: 600;
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
        display: flex; align-items: center; gap: 10px;
        color: var(--text-primary);
        transition: all 0.2s;
    }
    .nav-item:hover { background: rgba(107, 70, 193, 0.1); }
    .nav-item.active {
        background: rgba(107, 70, 193, 0.15);
        color: var(--primary-purple);
        font-weight: 600;
    }

    /* Document fingerprint */
    .doc-fingerprint {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .doc-fingerprint-title {
        font-size: 11px; font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
    }
    .doc-info-item {
        display: flex; justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #F3F4F6;
        font-size: 14px;
    }
    .doc-info-item:last-child { border-bottom: none; }
    .doc-info-label { color: var(--text-secondary); }
    .doc-info-value { color: var(--text-primary); font-weight: 500; }

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
    .tag-llm       { background: #DBEAFE; color: #1E40AF; }
    .tag-inference { background: #FCE7F3; color: #BE185D; }
    .tag-cuda      { background: #D1FAE5; color: #065F46; }

    /* Chat header */
    .chat-header {
        display: flex; align-items: center; gap: 12px;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 24px;
    }
    .chat-icon {
        width: 36px; height: 36px;
        background: linear-gradient(135deg, var(--primary-purple), var(--primary-purple-light));
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        color: white; font-size: 18px;
        box-shadow: 0 3px 10px rgba(107,70,193,0.25);
    }
    .chat-title {
        font-size: 19px; font-weight: 700;
        color: var(--text-primary);
    }
    .chat-subtitle {
        font-size: 13px; color: var(--text-secondary);
        margin-left: 4px; font-weight: 400;
    }

    /* File info */
    .file-info {
        background: #F9FAFB;
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 16px;
        display: flex; align-items: center; gap: 12px;
    }
    .file-icon {
        width: 40px; height: 40px;
        background: #FEE2E2;
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 20px;
    }
    .file-details { flex: 1; }
    .file-name { font-weight: 600; color: var(--text-primary); font-size: 14px; }
    .file-meta { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

    /* Quick action buttons */
    .quick-actions {
        display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap;
    }
    .quick-action-btn {
        padding: 9px 18px;
        border: 1.5px solid var(--primary-purple);
        background: white;
        color: var(--primary-purple);
        border-radius: 10px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
    }
    .quick-action-btn:hover {
        background: var(--primary-purple);
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(107,70,193,0.3);
    }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 80px 24px;
        background: white;
        border-radius: 14px;
        border: 2px dashed #E5E7EB;
    }
    .empty-state h2 { color: #6B7280; margin-bottom: 12px; }
    .empty-state p  { color: #9CA3AF; font-size: 15px; }
</style>
""", unsafe_allow_html=True)

# Apply the enhanced chat component styles
apply_enhanced_chat_styles()

# ──────────────────────────────────────────────
# Managers (cached)
# ──────────────────────────────────────────────
@st.cache_resource
def get_managers():
    return {
        'chat': ChatManager(),
        'query_optimizer': QueryOptimizer(),
        'citation_engine': CitationEngine()
    }

managers = get_managers()

# ──────────────────────────────────────────────
# Session State
# ──────────────────────────────────────────────
def init_session_state():
    defaults = {
        'pdf_uploaded': False,
        'pdf_name': None,
        'pdf_text': None,
        'pdf_path': None,
        'current_page': 'Current Paper',
        'provider': 'groq',
        'use_turbo': True,
        'processing': False,
        '_clipboard_content': None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────
def extract_pdf_content(pdf_path):
    """Extract text content from PDF."""
    try:
        pdf_tool = PDFReadTool(pdf_path=pdf_path, analyze_images=False)
        return pdf_tool._run()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None


def get_ai_response(user_query, pdf_context, provider="groq", use_turbo=True):
    """Get AI response with citation-enhanced prompting."""
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

        # Enhanced system prompt with citation guidance
        system_prompt = f"""You are an expert research assistant analyzing academic papers and documents.

Document Context:
{optimized_context[:10000]}

Instructions:
- Provide clear, concise, and accurate answers based on the document
- Reference specific sections or pages when possible (use "Page X" format)
- Use academic language appropriate for research
- If information isn't in the document, state that clearly
- Format responses with proper structure and citations
- When providing statistics or data, present them clearly with labels
- Include confidence indicators when making claims"""

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

        response_text = response.choices[0].message.content

        # Extract citations from the response
        citation_data = managers['citation_engine'].extract_citations(response_text)

        return {
            'response': response_text,
            'provider': provider_used,
            'tokens': response.usage.total_tokens if hasattr(response, 'usage') else 0,
            'citation_data': citation_data,
        }

    except Exception as e:
        return {
            'error': True,
            'response': f"Error: {str(e)}",
            'provider': None,
            'citation_data': None,
        }


# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
with st.sidebar:
    # Upload button
    st.markdown("""
    <div class="upload-button">
        📄 Upload Research
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")

    if uploaded_file and uploaded_file.name != st.session_state.pdf_name:
        with st.spinner("📖 Analyzing document…"):
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
        if st.button(f"{icon} {page}", key=f"nav_{page}", use_container_width=True):
            st.session_state.current_page = page

    st.markdown('</div>', unsafe_allow_html=True)

    # Document Fingerprint
    if st.session_state.pdf_uploaded:
        st.markdown('<div class="doc-fingerprint">', unsafe_allow_html=True)
        st.markdown('<div class="doc-fingerprint-title">DOCUMENT FINGERPRINT</div>', unsafe_allow_html=True)

        # Calculate read time from text length
        word_count = len((st.session_state.pdf_text or "").split())
        read_time = max(1, word_count // 250)

        st.markdown(f"""
        <div class="doc-info-item">
            <span class="doc-info-label">Type</span>
            <span class="doc-info-value">Scientific Paper</span>
        </div>
        <div class="doc-info-item">
            <span class="doc-info-label">Est. Read Time</span>
            <span class="doc-info-value">{read_time} Minutes</span>
        </div>
        <div class="doc-info-item">
            <span class="doc-info-label">Words</span>
            <span class="doc-info-value">{word_count:,}</span>
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
        display_name = st.session_state.pdf_name
        if len(display_name) > 22:
            display_name = display_name[:20] + "…"
        st.markdown('<div class="file-info">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="file-icon">📄</div>
        <div class="file-details">
            <div class="file-name">{display_name}</div>
            <div class="file-meta">Currently loaded</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Provider selector
    st.markdown('<div class="nav-title" style="margin-top:24px;">AI PROVIDER</div>', unsafe_allow_html=True)
    provider_choice = st.selectbox(
        "Provider",
        ["groq", "gemini"],
        index=0 if st.session_state.provider == 'groq' else 1,
        label_visibility="collapsed"
    )
    st.session_state.provider = provider_choice


# ──────────────────────────────────────────────
# MAIN CONTENT AREA
# ──────────────────────────────────────────────

# Chat header
msg_count = len(list(managers['chat'].context.messages))
st.markdown(f"""
<div class="chat-header">
    <div class="chat-icon">💬</div>
    <div>
        <div class="chat-title">AI Research Chat</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Inject clipboard JS (if a copy was triggered)
inject_clipboard_script()

if not st.session_state.pdf_uploaded:
    # ── Empty state ──
    st.markdown("""
    <div class="empty-state">
        <h2>📄 Upload a Research Paper</h2>
        <p>Upload a PDF document from the sidebar to start analyzing and asking questions</p>
    </div>
    """, unsafe_allow_html=True)
else:
    # ── Chat Messages ──
    messages = list(managers['chat'].context.messages)

    for i, msg in enumerate(messages):
        citation_data = msg.get('metadata', {}).get('citation_data', None)
        render_message_bubble(
            message=msg,
            index=i,
            show_actions=(msg.get('role') == 'assistant'),
            pdf_text=st.session_state.pdf_text or "",
            citation_data=citation_data,
        )

    # ── Typing Indicator (show when processing) ──
    if st.session_state.processing:
        render_typing_indicator()

    # ── Quick Actions ──
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
            query = "Extract the main statistics and data from this paper, presenting them in a clear format with labels and values"
            managers['chat'].context.add_message('user', query)
            st.rerun()

    with col4:
        if st.button("🔄 References", use_container_width=True):
            query = "List the main references cited in this paper"
            managers['chat'].context.add_message('user', query)
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Clear history
    col_clear, _ = st.columns([1, 5])
    with col_clear:
        if st.button("🗑️ Clear History", use_container_width=True):
            managers['chat'].clear_conversation()
            st.rerun()

    # ── Input Area ──
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Ask a research question…",
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

    # ── Process Last Message (AI Response) ──
    if messages and messages[-1]['role'] == 'user' and not st.session_state.processing:
        st.session_state.processing = True
        st.rerun()  # Rerun to show typing indicator

    if st.session_state.processing and messages and messages[-1]['role'] == 'user':
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
                {
                    'provider': result['provider'],
                    'confidence': 84,
                    'tokens_used': result.get('tokens', 0),
                    'citation_data': result.get('citation_data'),
                }
            )

        st.session_state.processing = False
        st.rerun()
