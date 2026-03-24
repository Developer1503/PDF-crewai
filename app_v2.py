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
from utils.vector_store import VectorStoreManager
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
        'citation_engine': CitationEngine(),
        'vector_store': VectorStoreManager(),
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
        'pdf_fingerprint': None,      # SHA-256 of the indexed document
        'vector_chunks_added': 0,     # chunks stored in this session
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


def get_ai_response_stream(
    user_query,
    pdf_context,
    provider="groq",
    use_turbo=True,
    doc_fingerprint: str = None,
):
    """Get AI response with streaming, using RAG context from the vector store."""
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

        # ── RAG: retrieve semantically relevant chunks ──
        rag_context = ""
        if doc_fingerprint:
            try:
                rag_context = managers['vector_store'].build_rag_context(
                    query=user_query,
                    doc_fingerprint=doc_fingerprint,
                    n_results=6,
                    min_score=0.20,
                )
            except Exception as rag_err:
                # Graceful fallback — use classic query optimizer
                rag_context = ""

        # Fall back to classic optimizer if RAG returned nothing
        if rag_context:
            final_context = rag_context
        else:
            final_context = managers['query_optimizer'].optimize_context(
                pdf_context, user_query, max_tokens=3000
            )[:10000]

        # Enhanced system prompt with citation guidance
        system_prompt = f"""You are an expert research assistant analyzing academic papers and documents.

Relevant Document Excerpts (retrieved via semantic search):
{final_context}

Instructions:
- Answer using ONLY the provided excerpts above.
- Reference specific chunks or page numbers when visible (use "Page X" or "Chunk N").
- Use academic language appropriate for research.
- If the answer is not in the excerpts, say so clearly.
- Format responses with proper structure and citations.
- When providing statistics or data, present them with clear labels.
- Include confidence indicators when making claims."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ]

        response = litellm.completion(
            model=model,
            messages=messages,
            api_key=api_key,
            temperature=0.3,
            max_tokens=2000,
            stream=True,
        )

        for chunk in response:
            if (
                hasattr(chunk.choices[0], 'delta')
                and hasattr(chunk.choices[0].delta, 'content')
                and chunk.choices[0].delta.content
            ):
                yield {
                    'chunk': chunk.choices[0].delta.content,
                    'provider': provider_used,
                }

    except Exception as e:
        yield {'error': True, 'response': f"Error: {str(e)}"}


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

                # ── Vector indexing (skips if already indexed) ──
                with st.spinner("🔢 Building vector index…"):
                    fingerprint, chunks_added = managers['vector_store'].index_document(
                        filename=uploaded_file.name,
                        text=pdf_text,
                    )
                    st.session_state.pdf_fingerprint = fingerprint
                    st.session_state.vector_chunks_added = chunks_added

                st.rerun()

    # Navigation
    st.divider()
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
    st.divider()
    if st.session_state.pdf_uploaded:
        st.markdown('<div class="doc-fingerprint">', unsafe_allow_html=True)
        st.markdown('<div class="doc-fingerprint-title">DOCUMENT FINGERPRINT</div>', unsafe_allow_html=True)

        # Calculate read time from text length
        word_count = len((st.session_state.pdf_text or "").split())
        read_time = max(1, word_count // 250)

        # Vector store status
        chunks_added = st.session_state.get('vector_chunks_added', 0)
        fp = st.session_state.get('pdf_fingerprint', '')
        fp_short = fp[:12] + '…' if fp else 'N/A'
        vector_status = '✅ Cached' if chunks_added == 0 and fp else f'🆕 {chunks_added} chunks'

        # vector backend name
        try:
            vs_backend = managers['vector_store'].backend_name
        except Exception:
            vs_backend = 'N/A'

        st.markdown(f"""
        <div class="doc-info-item">
            <span class="doc-info-label">Type</span>
            <span class="doc-info-value">Scientific Paper</span>
        </div>
        <div class="doc-info-item">
            <span class="doc-info-label">Word Count</span>
            <span class="doc-info-value">{word_count:,}</span>
        </div>
        <div class="doc-info-item">
            <span class="doc-info-label">Est. Read Time</span>
            <span class="doc-info-value">{read_time} Min</span>
        </div>
        <div class="doc-info-item">
            <span class="doc-info-label">Language</span>
            <span class="doc-info-value">English</span>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown('<div class="doc-fingerprint-title">VECTOR INDEX</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="doc-info-item">
            <span class="doc-info-label">Backend</span>
            <span class="doc-info-value">{vs_backend}</span>
        </div>
        <div class="doc-info-item">
            <span class="doc-info-label">Status</span>
            <span class="doc-info-value">{vector_status}</span>
        </div>
        <div class="doc-info-item">
            <span class="doc-info-label">SHA-256</span>
            <span class="doc-info-value" style="font-family:monospace;font-size:11px;">{fp_short}</span>
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

    # Comparison Mode
    if st.session_state.pdf_uploaded:
        st.markdown('<div class="nav-title" style="margin-top:24px;">COMPARISON MODE</div>', unsafe_allow_html=True)
        compare_file = st.file_uploader("Upload 2nd PDF to Compare", type="pdf", key="compare_upload", label_visibility="collapsed")
        
        if compare_file and (not hasattr(st.session_state, 'compare_file_name') or compare_file.name != st.session_state.compare_file_name):
            with st.spinner("📖 Analyzing second document…"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp2:
                    tmp2.write(compare_file.getvalue())
                pdf_text2 = extract_pdf_content(tmp2.name)
                
                if pdf_text2:
                    st.session_state.compare_file_name = compare_file.name
                    managers['chat'].context.add_message('user', "I have uploaded a second document for comparison. I will ask questions to compare the two papers. Here is the second document's text: \n\n" + pdf_text2[:15000])
                    # Force a rerun to process the new document message
                    st.rerun()



# ──────────────────────────────────────────────
# MAIN CONTENT AREA
# ──────────────────────────────────────────────

# 1. Header bar with title and Clear History button
col_header1, col_header2 = st.columns([5, 1])
with col_header1:
    st.markdown(f"""
    <div class="chat-header" style="border-bottom:none; margin-bottom:0px; padding-bottom:5px;">
        <div class="chat-icon">💬</div>
        <div>
            <div class="chat-title">AI Research Chat</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_header2:
    if st.button("🗑️ Clear History", key="clear_hist_top", use_container_width=True):
        managers['chat'].clear_conversation()
        st.rerun()

st.divider()

# 2. Single quick actions pill bar
st.markdown('<div class="toolbar-label" style="font-size:11px;font-weight:700;color:#9e8cca;margin-bottom:8px;">⚡ QUICK ACTIONS</div>', unsafe_allow_html=True)
qa_cols = st.columns(7)
with qa_cols[0]:
    if st.button("📝 Summarize", key="qa_sum", use_container_width=True):
        managers['chat'].context.add_message('user', "Provide a comprehensive summary of this research paper")
        st.rerun()
with qa_cols[1]:
    if st.button("🔍 Key Findings", key="qa_fin", use_container_width=True):
        managers['chat'].context.add_message('user', "What are the key findings of this research?")
        st.rerun()
with qa_cols[2]:
    if st.button("📊 Extract Stats", key="qa_stats", use_container_width=True):
        managers['chat'].context.add_message('user', "Extract the main statistics and data from this paper, presenting them in a clear format with labels and values")
        st.rerun()
with qa_cols[3]:
    if st.button("🔄 References", key="qa_refs", use_container_width=True):
        managers['chat'].context.add_message('user', "List the main references cited in this paper")
        st.rerun()
with qa_cols[4]:
    if st.button("📊 Ext Tables", key="ao_tables", use_container_width=True):
        managers['chat'].context.add_message('user', "Analyze the text and report any data or information that seems to be extracted from tables and figures. Summarize the data presented in them.")
        st.rerun()
with qa_cols[5]:
    if st.button("📚 Auto-Biblio", key="ao_biblio", use_container_width=True):
        managers['chat'].context.add_message('user', "Extract all references from this paper and format them correctly into an Auto-Bibliography with well-structured APA/MLA/Chicago formats.")
        st.rerun()
with qa_cols[6]:
    chat_content = "# AI Research Report\n\n"
    for msg in managers['chat'].context.messages:
        role_label = "User Query" if msg['role'] == 'user' else "AI Analysis"
        chat_content += f"## {role_label}\n{msg['content']}\n\n"
    st.download_button(
        label="📄 Export Report",
        data=chat_content,
        file_name=f"research_report_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown",
        key="ao_export_main",
        use_container_width=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# 3. Scrollable chat history container
chat_container = st.container(height=400)

with chat_container:
    # Inject clipboard JS
    inject_clipboard_script()

    if not st.session_state.pdf_uploaded:
        # Empty state
        st.markdown("""
        <div class="empty-state">
            <h2>📄 Upload a Research Paper</h2>
            <p>Upload a PDF document from the sidebar to start analyzing and asking questions</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Render Chat Messages
        messages = list(managers['chat'].context.messages)
        for i, msg in enumerate(messages):
            # Using custom render bubble inside st.chat_message
            with st.chat_message(msg['role']):
                citation_data = msg.get('metadata', {}).get('citation_data', None)
                render_message_bubble(
                    message=msg,
                    index=i,
                    show_actions=(msg.get('role') == 'assistant'),
                    pdf_text=st.session_state.pdf_text or "",
                    citation_data=citation_data,
                )

        # Typing Indicator
        if st.session_state.processing:
            with st.chat_message('assistant'):
                render_typing_indicator()

        # Place holder for streaming logic inside container
        response_placeholder = st.empty()

# 4 & 5. Premium Input Card and Submit
st.markdown('<br>', unsafe_allow_html=True)
st.markdown('<div class="input-card">', unsafe_allow_html=True)
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_area(
        "Ask a research question…",
        placeholder="e.g., How does this methodology compare to standard autoregressive models?",
        height=90,
        label_visibility="collapsed"
    )
    # Bottom row inside card
    ic1, ic2, ic3 = st.columns([0.5, 0.5, 5])
    with ic1:
        st.form_submit_button("🎤", use_container_width=True)
    with ic2:
        pass
    with ic3:
        submit = st.form_submit_button("✦ Analyze Query", use_container_width=True, type="primary")

    if submit and user_input:
        managers['chat'].context.add_message('user', user_input)
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ── Process Last Message (AI Response) ──
messages = list(managers['chat'].context.messages)
if messages and messages[-1]['role'] == 'user' and not st.session_state.processing:
    st.session_state.processing = True
    st.rerun()  # Rerun to show typing indicator

# Process Response Stream (outside UI rendering to avoid rerendering loops)
if st.session_state.processing and messages and messages[-1]['role'] == 'user':
    user_query = messages[-1]['content']
    
    # Put stream text safely inside the container place_holder defined above
    full_response = ""
    provider_used = st.session_state.provider
    
    stream_generator = get_ai_response_stream(
        user_query,
        st.session_state.pdf_text,
        st.session_state.provider,
        st.session_state.use_turbo,
        doc_fingerprint=st.session_state.get('pdf_fingerprint'),
    )
    
    for item in stream_generator:
        if 'error' in item:
            full_response = item['response']
            break
        full_response += item.get('chunk', '')
        provider_used = item.get('provider', provider_used)
        # Render temporary markdown while streaming
        response_placeholder.markdown(f"**AI:** {full_response}▌")
        
    # Remove placeholder and add the complete message
    response_placeholder.empty()

    if full_response:
        citation_data = managers['citation_engine'].extract_citations(full_response)
        managers['chat'].context.add_message(
            'assistant',
            full_response,
            {
                'provider': provider_used,
                'confidence': 84,
                'tokens_used': 0, # Tokens could be estimated or omitted
                'citation_data': citation_data,
            }
        )

    st.session_state.processing = False
    st.rerun()
