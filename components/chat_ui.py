"""
Enhanced Chat UI Components v2.0
Premium chat interface with reactions, copy/save, typing indicator,
structured response cards, and inline page previews.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional
import re
import json
import html


# ─────────────────────────────────────────────────────────────
# 1. ENHANCED STYLES — injected once per page load
# ─────────────────────────────────────────────────────────────
def apply_enhanced_chat_styles():
    """Apply all premium CSS for the upgraded chat area."""
    st.markdown("""
    <style>
    /* ========== MESSAGE BUBBLES ========== */
    .chat-message {
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        animation: slideIn 0.35s cubic-bezier(.25,.46,.45,.94);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        position: relative;
    }

    @keyframes slideIn {
        from { opacity: 0; transform: translateY(18px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    .message-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
        font-size: 0.9rem;
        opacity: 0.85;
    }
    .message-icon  { font-size: 1.2rem; }
    .message-role  { font-weight: 600; }
    .message-provider {
        background: rgba(107, 70, 193, 0.2);
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .message-time {
        margin-left: auto;
        font-size: 0.72rem;
        opacity: 0.55;
    }
    .message-content { line-height: 1.65; }

    .user-message {
        background: linear-gradient(135deg, rgba(107, 70, 193, 0.12) 0%, rgba(139, 92, 246, 0.12) 100%);
        border: 1px solid rgba(107, 70, 193, 0.25);
        margin-left: 2rem;
        border-bottom-right-radius: 4px;
    }
    .ai-message {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        margin-right: 2rem;
        border-bottom-left-radius: 4px;
    }

    /* ========== ACTION BAR (reactions + copy/save) ========== */
    .msg-action-bar {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: 12px;
        padding-top: 10px;
        border-top: 1px solid rgba(0,0,0,0.06);
        flex-wrap: wrap;
    }
    .msg-action-btn {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 5px 12px;
        border-radius: 20px;
        border: 1px solid #E5E7EB;
        background: #F9FAFB;
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s ease;
        color: #6B7280;
        user-select: none;
    }
    .msg-action-btn:hover {
        background: #F3F0FF;
        border-color: #C4B5FD;
        color: #6B46C1;
        transform: translateY(-1px);
        box-shadow: 0 2px 6px rgba(107,70,193,0.15);
    }
    .msg-action-btn.active-like {
        background: #ECFDF5;
        border-color: #6EE7B7;
        color: #059669;
    }
    .msg-action-btn.active-dislike {
        background: #FEF2F2;
        border-color: #FCA5A5;
        color: #DC2626;
    }
    .msg-action-btn .action-label {
        font-size: 12px;
        font-weight: 500;
    }
    .msg-action-spacer {
        flex: 1;
    }

    /* Copy-success flash */
    .copy-flash {
        animation: flashGreen 1.2s ease forwards;
    }
    @keyframes flashGreen {
        0%   { background: #D1FAE5; border-color: #34D399; color: #059669; }
        100% { background: #F9FAFB; border-color: #E5E7EB; color: #6B7280; }
    }

    /* ========== TYPING INDICATOR ========== */
    .typing-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 20px;
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        animation: slideIn 0.35s ease;
    }
    .typing-avatar {
        width: 32px; height: 32px;
        background: linear-gradient(135deg, #6B46C1, #8B5CF6);
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: white; font-size: 14px; font-weight: 700;
        box-shadow: 0 0 12px rgba(107,70,193,0.35);
        animation: pulseGlow 2s ease-in-out infinite;
    }
    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 8px rgba(107,70,193,0.3); }
        50%      { box-shadow: 0 0 18px rgba(107,70,193,0.6); }
    }
    .typing-dots {
        display: flex; gap: 5px; align-items: center;
    }
    .typing-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6B46C1, #8B5CF6);
        animation: dotBounce 1.4s ease-in-out infinite;
    }
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes dotBounce {
        0%, 60%, 100% { transform: translateY(0);    opacity: 0.4; }
        30%           { transform: translateY(-8px);  opacity: 1; }
    }
    .typing-label {
        font-size: 13px; color: #9CA3AF; font-style: italic;
    }

    /* ========== RESPONSE CARDS ========== */
    .response-card {
        background: #FAFBFC;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        margin: 12px 0;
        overflow: hidden;
        transition: box-shadow 0.2s ease;
    }
    .response-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .response-card-header {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        background: linear-gradient(135deg, #F3F0FF, #EDE9FE);
        border-bottom: 1px solid #E5E7EB;
        font-weight: 600;
        font-size: 13px;
        color: #6B46C1;
        letter-spacing: 0.3px;
    }
    .response-card-body {
        padding: 14px;
        font-size: 14px;
        line-height: 1.6;
        color: #374151;
    }

    /* Stats card table */
    .stats-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 8px;
        overflow: hidden;
    }
    .stats-table th {
        background: #F3F0FF;
        color: #6B46C1;
        padding: 10px 14px;
        text-align: left;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 700;
    }
    .stats-table td {
        padding: 10px 14px;
        border-bottom: 1px solid #F3F4F6;
        font-size: 13.5px;
    }
    .stats-table tr:last-child td { border-bottom: none; }
    .stats-table tr:hover td { background: #F9FAFB; }

    /* Citation card */
    .citation-inline {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 10px;
        background: linear-gradient(135deg, #EDE9FE, #DDD6FE);
        color: #6B46C1;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        position: relative;
        transition: all 0.2s ease;
        text-decoration: none;
    }
    .citation-inline:hover {
        background: linear-gradient(135deg, #DDD6FE, #C4B5FD);
        transform: translateY(-1px);
        box-shadow: 0 3px 8px rgba(107,70,193,0.2);
    }

    /* ========== INLINE PAGE PREVIEW (tooltip) ========== */
    .page-preview-wrapper {
        position: relative;
        display: inline-block;
    }
    .page-preview-tooltip {
        display: none;
        position: absolute;
        bottom: calc(100% + 10px);
        left: 50%;
        transform: translateX(-50%);
        width: 340px;
        max-height: 220px;
        overflow-y: auto;
        background: #FFFFFF;
        border: 1px solid #DDD6FE;
        border-radius: 10px;
        padding: 14px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        z-index: 9999;
        animation: tooltipFade 0.2s ease;
    }
    .page-preview-tooltip::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border: 8px solid transparent;
        border-top-color: #FFFFFF;
    }
    .page-preview-wrapper:hover .page-preview-tooltip {
        display: block;
    }
    @keyframes tooltipFade {
        from { opacity: 0; transform: translateX(-50%) translateY(5px); }
        to   { opacity: 1; transform: translateX(-50%) translateY(0); }
    }
    .page-preview-title {
        font-size: 11px;
        font-weight: 700;
        color: #6B46C1;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        padding-bottom: 6px;
        border-bottom: 2px solid #EDE9FE;
    }
    .page-preview-text {
        font-size: 12.5px;
        line-height: 1.55;
        color: #4B5563;
        white-space: pre-wrap;
    }

    /* ========== CONFIDENCE BAR (improved) ========== */
    .confidence-bar-v2 {
        margin-top: 12px;
        padding-top: 10px;
        border-top: 1px solid #F3F4F6;
    }
    .confidence-bar-v2 .cb-label {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        font-weight: 600;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-bottom: 5px;
    }
    .confidence-bar-v2 .cb-track {
        height: 5px;
        background: #E5E7EB;
        border-radius: 3px;
        overflow: hidden;
    }
    .confidence-bar-v2 .cb-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.6s ease;
    }
    .cb-fill-high   { background: linear-gradient(90deg, #34D399, #10B981); }
    .cb-fill-medium { background: linear-gradient(90deg, #FBBF24, #F59E0B); }
    .cb-fill-low    { background: linear-gradient(90deg, #F87171, #EF4444); }

    /* ========== SCROLLBAR ========== */
    .chat-scroll::-webkit-scrollbar { width: 6px; }
    .chat-scroll::-webkit-scrollbar-track { background: transparent; }
    .chat-scroll::-webkit-scrollbar-thumb {
        background: rgba(107,70,193,0.3); border-radius: 3px;
    }
    .chat-scroll::-webkit-scrollbar-thumb:hover { background: rgba(107,70,193,0.5); }

    /* ========== INPUT AREA ========== */
    .stTextArea textarea {
        border-radius: 8px !important;
        border: 1.5px solid #E5E7EB !important;
        background: #FFFFFF !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    .stTextArea textarea:focus {
        border-color: #8B5CF6 !important;
        box-shadow: 0 0 0 3px rgba(139,92,246,0.12) !important;
    }
    .stButton button {
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(107,70,193,0.2);
    }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# 2. TYPING INDICATOR
# ─────────────────────────────────────────────────────────────
def render_typing_indicator():
    """Premium animated typing indicator while AI is processing."""
    st.markdown("""
    <div class="typing-container">
        <div class="typing-avatar">AI</div>
        <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
        <span class="typing-label">Analyzing your document…</span>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# 3. RESPONSE CARD PARSER
# ─────────────────────────────────────────────────────────────
def _detect_stats(text: str) -> List[Dict]:
    """Detect stat-like patterns (key: value or key — value) in text."""
    stats = []
    patterns = [
        # "Accuracy: 94.2%" or "Accuracy — 94.2%"
        re.compile(r'[-•*]?\s*\*?\*?(.+?)\*?\*?\s*[:—–]\s*(.+)', re.MULTILINE),
    ]
    for pat in patterns:
        for m in pat.finditer(text):
            key = m.group(1).strip().strip('*').strip()
            val = m.group(2).strip().strip('*').strip()
            if 3 < len(key) < 60 and len(val) < 100:
                stats.append({'key': key, 'value': val})
    return stats


def _detect_table(text: str) -> Optional[Dict]:
    """Detect markdown tables in text and return header + rows."""
    lines = text.strip().split('\n')
    table_lines = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if '|' in stripped and stripped.startswith('|'):
            in_table = True
            table_lines.append(stripped)
        elif in_table:
            break

    if len(table_lines) >= 3:  # header + separator + at least 1 row
        header = [c.strip() for c in table_lines[0].split('|')[1:-1]]
        rows = []
        for row_line in table_lines[2:]:
            cells = [c.strip() for c in row_line.split('|')[1:-1]]
            if cells:
                rows.append(cells)
        if header and rows:
            return {'headers': header, 'rows': rows}
    return None


def render_stats_card(stats: List[Dict]):
    """Render a beautiful stats card."""
    rows_html = ""
    for s in stats[:10]:
        rows_html += f"""
        <tr>
            <td style="font-weight:600;color:#374151;">{html.escape(s['key'])}</td>
            <td style="color:#6B46C1;font-weight:500;">{html.escape(s['value'])}</td>
        </tr>"""

    st.markdown(f"""
    <div class="response-card">
        <div class="response-card-header">📊 Extracted Statistics</div>
        <div class="response-card-body">
            <table class="stats-table">
                <thead><tr><th>Metric</th><th>Value</th></tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_table_card(table: Dict):
    """Render a detected markdown table as a premium card."""
    header_html = "".join(f"<th>{html.escape(h)}</th>" for h in table['headers'])
    rows_html = ""
    for row in table['rows'][:20]:
        cells = "".join(f"<td>{html.escape(c)}</td>" for c in row)
        rows_html += f"<tr>{cells}</tr>"

    st.markdown(f"""
    <div class="response-card">
        <div class="response-card-header">📋 Data Table</div>
        <div class="response-card-body">
            <table class="stats-table">
                <thead><tr>{header_html}</tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_citation_card_v2(citation: Dict):
    """Render a premium citation card."""
    confidence = citation.get('confidence', 'Unknown')
    badge_map = {'High': ('🟢', 'cb-fill-high'), 'Medium': ('🟡', 'cb-fill-medium'),
                 'Low': ('🔴', 'cb-fill-low')}
    badge, fill_cls = badge_map.get(confidence, ('⚪', 'cb-fill-medium'))

    pages = citation.get('page_numbers', [])
    pages_str = ', '.join(str(p) for p in pages) if pages else 'N/A'

    quote_html = ""
    if citation.get('quote'):
        quote_html = f"""
        <div style="margin-top:8px;padding:10px 12px;background:#F5F3FF;border-left:3px solid #8B5CF6;
                     border-radius:0 6px 6px 0;font-style:italic;font-size:13px;color:#4B5563;">
            "{html.escape(citation['quote'])}"
        </div>"""

    st.markdown(f"""
    <div class="response-card">
        <div class="response-card-header">📚 Citation</div>
        <div class="response-card-body">
            <div style="display:flex;gap:20px;flex-wrap:wrap;">
                <div><span style="font-size:11px;color:#9CA3AF;text-transform:uppercase;font-weight:700;">Source</span>
                     <div style="font-weight:600;margin-top:2px;">{html.escape(citation.get('source', 'N/A'))}</div></div>
                <div><span style="font-size:11px;color:#9CA3AF;text-transform:uppercase;font-weight:700;">Pages</span>
                     <div style="font-weight:600;margin-top:2px;">{pages_str}</div></div>
                <div><span style="font-size:11px;color:#9CA3AF;text-transform:uppercase;font-weight:700;">Confidence</span>
                     <div style="font-weight:600;margin-top:2px;">{badge} {confidence}</div></div>
            </div>
            {quote_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# 4. INLINE PAGE PREVIEW
# ─────────────────────────────────────────────────────────────
def _get_page_text(pdf_text: str, page_num: int) -> str:
    """Extract text for a given page number from extracted PDF text."""
    # The pdf_reader separates pages with "--- Page N ---"
    pattern = rf'--- Page {page_num} ---\n(.*?)(?=--- Page \d+ ---|=== IMAGE ANALYSIS ===|$)'
    match = re.search(pattern, pdf_text, re.DOTALL)
    if match:
        text = match.group(1).strip()
        # Truncate for preview
        return text[:500] + ("…" if len(text) > 500 else "")
    return f"Page {page_num} content not available for preview."


def render_page_citation_with_preview(page_num: int, pdf_text: str = ""):
    """Render a page citation badge with hover preview."""
    preview_text = html.escape(_get_page_text(pdf_text, page_num)) if pdf_text else f"Page {page_num} preview"
    return f"""
    <div class="page-preview-wrapper">
        <span class="citation-inline">📄 Page {page_num}</span>
        <div class="page-preview-tooltip">
            <div class="page-preview-title">📖 Page {page_num} Preview</div>
            <div class="page-preview-text">{preview_text}</div>
        </div>
    </div>"""


def detect_page_references(text: str) -> List[int]:
    """Find all page references in AI response text."""
    pages = set()
    patterns = [
        r'[Pp]age\s+(\d+)',
        r'p\.\s*(\d+)',
        r'pp\.\s*([\d,\s]+)'
    ]
    for pat in patterns:
        for m in re.finditer(pat, text):
            val = m.group(1)
            if ',' in val:
                for v in val.split(','):
                    v = v.strip()
                    if v.isdigit():
                        pages.add(int(v))
            elif val.isdigit():
                pages.add(int(val))
    return sorted(pages)


# ─────────────────────────────────────────────────────────────
# 5. RENDER MESSAGE BUBBLE (fully upgraded)
# ─────────────────────────────────────────────────────────────
def render_message_bubble(message: Dict, index: int, show_actions: bool = True,
                          pdf_text: str = "", citation_data: Dict = None):
    """Render a message bubble with reactions, copy/save, cards, and page previews."""
    role = message.get('role', 'user')
    content = message.get('content', '')
    timestamp = message.get('timestamp', datetime.now().isoformat())
    metadata = message.get('metadata', {})

    # Parse timestamp
    try:
        dt = datetime.fromisoformat(timestamp)
        time_str = dt.strftime('%I:%M %p')
    except Exception:
        time_str = ''

    if role == 'user':
        st.markdown(f"""
        <div class="chat-message user-message" id="msg-{index}">
            <div class="message-header">
                <span class="message-icon">👤</span>
                <span class="message-role">You</span>
                <span class="message-time">{time_str}</span>
            </div>
            <div class="message-content">{html.escape(content)}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # ── AI message ──
        provider = metadata.get('provider', '')
        tokens = metadata.get('tokens_used', 0)
        confidence = metadata.get('confidence', 84)

        provider_html = f'<span class="message-provider">{html.escape(provider.upper())}</span>' if provider else ''

        st.markdown(f"""
        <div class="chat-message ai-message" id="msg-{index}">
            <div class="message-header">
                <span class="message-icon">🤖</span>
                <span class="message-role">PDF Assistant</span>
                {provider_html}
                <span class="message-time">{time_str}</span>
            </div>
            <div class="message-content">
        """, unsafe_allow_html=True)

        # Render main content as markdown
        st.markdown(content)

        # ── Structured Response Cards ──
        # Detect & render table
        table = _detect_table(content)
        if table:
            render_table_card(table)

        # Detect & render citation card
        if citation_data and citation_data.get('has_citation'):
            render_citation_card_v2(citation_data)

        # ── Inline Page Previews ──
        page_refs = detect_page_references(content)
        if page_refs and pdf_text:
            badges_html = "".join(
                render_page_citation_with_preview(p, pdf_text) for p in page_refs[:5]
            )
            st.markdown(f"""
            <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;">
                {badges_html}
            </div>
            """, unsafe_allow_html=True)

        # ── Confidence bar ──
        conf_val = confidence if isinstance(confidence, (int, float)) else 84
        if conf_val >= 75:
            fill_cls = 'cb-fill-high'
        elif conf_val >= 50:
            fill_cls = 'cb-fill-medium'
        else:
            fill_cls = 'cb-fill-low'

        st.markdown(f"""
            <div class="confidence-bar-v2">
                <div class="cb-label">
                    <span>Confidence</span>
                    <span>{conf_val}%</span>
                </div>
                <div class="cb-track">
                    <div class="cb-fill {fill_cls}" style="width:{conf_val}%"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Close message-content and chat-message divs
        st.markdown("</div></div>", unsafe_allow_html=True)

        # ── Action bar: Reactions + Copy + Save ──
        if show_actions:
            _render_action_bar(index, content)


def _render_action_bar(index: int, content: str):
    """Render reaction buttons + copy + save for a single AI message."""
    # Initialize feedback state
    fb_key = f'feedback_{index}'
    if fb_key not in st.session_state:
        st.session_state[fb_key] = None

    cols = st.columns([1, 1, 1, 1, 4])

    with cols[0]:
        current = st.session_state[fb_key]
        like_label = "👍 Helpful" if current != 'positive' else "👍 Liked!"
        if st.button(like_label, key=f"like_{index}", use_container_width=True):
            st.session_state[fb_key] = 'positive' if current != 'positive' else None
            st.rerun()

    with cols[1]:
        dislike_label = "👎 Not helpful" if current != 'negative' else "👎 Noted"
        if st.button(dislike_label, key=f"dislike_{index}", use_container_width=True):
            st.session_state[fb_key] = 'negative' if current != 'negative' else None
            st.rerun()

    with cols[2]:
        if st.button("📋 Copy", key=f"copy_{index}", use_container_width=True):
            # Use Streamlit's clipboard approach via session state
            st.session_state['_clipboard_content'] = content
            st.toast("📋 Copied to clipboard!", icon="✅")

    with cols[3]:
        st.download_button(
            label="💾 Save",
            data=content,
            file_name=f"response_{index + 1}.md",
            mime="text/markdown",
            key=f"save_{index}",
            use_container_width=True
        )


# ─────────────────────────────────────────────────────────────
# 6. CLIPBOARD JAVASCRIPT INJECTION
# ─────────────────────────────────────────────────────────────
def inject_clipboard_script():
    """Inject JS to copy content to system clipboard."""
    if '_clipboard_content' in st.session_state and st.session_state['_clipboard_content']:
        escaped = json.dumps(st.session_state['_clipboard_content'])
        st.markdown(f"""
        <script>
        (function() {{
            try {{
                navigator.clipboard.writeText({escaped});
            }} catch(e) {{
                // Fallback for non-secure contexts
                var ta = document.createElement('textarea');
                ta.value = {escaped};
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                document.body.removeChild(ta);
            }}
        }})();
        </script>
        """, unsafe_allow_html=True)
        st.session_state['_clipboard_content'] = None


# ─────────────────────────────────────────────────────────────
# 7. CHAT INPUT
# ─────────────────────────────────────────────────────────────
def render_chat_input(placeholder: str = "Ask a question…",
                      show_voice: bool = False,
                      show_suggestions: bool = True) -> Optional[str]:
    """Render enhanced chat input with suggestions."""

    # Suggestions
    if show_suggestions and 'suggested_questions' in st.session_state:
        st.markdown("**💡 Suggested questions:**")
        suggestions = st.session_state.get('suggested_questions', [])
        cols = st.columns(min(len(suggestions), 3))
        for i, suggestion in enumerate(suggestions[:3]):
            with cols[i]:
                if st.button(f"💬 {suggestion[:30]}…", key=f"suggest_{i}", use_container_width=True):
                    return suggestion

    # Main input
    with st.form("chat_input_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_area(
                "Message",
                placeholder=placeholder,
                label_visibility="collapsed",
                height=100,
                key="chat_input_area"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            send_button = st.form_submit_button("Send 🚀", use_container_width=True)
            if show_voice:
                st.form_submit_button("🎤 Voice", use_container_width=True)

        if send_button and user_input:
            return user_input

    return None


# ─────────────────────────────────────────────────────────────
# 8. UTILITIES — kept from v1
# ─────────────────────────────────────────────────────────────
def render_conversation_stats(stats: Dict):
    """Display conversation statistics."""
    st.markdown("### 📊 Conversation Stats")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Messages", stats.get('total_messages', 0))
    with col2:
        st.metric("Your Questions", stats.get('user_messages', 0))
    with col3:
        st.metric("AI Responses", stats.get('ai_messages', 0))
    with col4:
        st.metric("Cache Hits", stats.get('cache_hits', 0),
                   help="Responses served from cache for faster performance")


def render_quick_actions(actions: List[Dict]):
    """Render quick action buttons."""
    st.markdown("**⚡ Quick Actions:**")
    for i in range(0, len(actions), 4):
        cols = st.columns(4)
        for j, action in enumerate(actions[i:i + 4]):
            with cols[j]:
                icon = action.get('icon', '💬')
                label = action.get('label', 'Action')
                query = action.get('query', '')
                if st.button(f"{icon} {label}", key=f"action_{i}_{j}", use_container_width=True):
                    return query
    return None


def render_message_search(messages: List[Dict]) -> Optional[List[int]]:
    """Search through conversation messages."""
    search_query = st.text_input("🔍 Search conversation", placeholder="Search messages…")
    if search_query:
        matching = [i for i, msg in enumerate(messages) if search_query.lower() in msg.get('content', '').lower()]
        if matching:
            st.success(f"Found {len(matching)} matching message(s)")
            return matching
        else:
            st.info("No matching messages found")
    return None


def render_context_panel(context_info: Dict):
    """Display context information panel."""
    with st.expander("📚 Context Information", expanded=False):
        st.markdown(f"""
        **Document:** {context_info.get('document_name', 'N/A')}

        **Context Window:** {context_info.get('context_messages', 0)} messages

        **Topics Discussed:**
        """)
        topics = context_info.get('topics', [])
        if topics:
            for topic in topics[-5:]:
                st.markdown(f"- {topic}")
        else:
            st.markdown("_No topics tracked yet_")


def render_response_quality_indicator(quality_score: float):
    """Show response quality indicator."""
    if quality_score >= 0.8:
        color, label, icon = "#10B981", "Excellent", "🟢"
    elif quality_score >= 0.6:
        color, label, icon = "#F59E0B", "Good", "🟡"
    else:
        color, label, icon = "#EF4444", "Needs Improvement", "🔴"

    st.markdown(f"""
    <div style="padding:0.5rem;border-left:4px solid {color};background:rgba(255,255,255,0.05);margin:0.5rem 0;">
        {icon} <strong>Response Quality:</strong> {label} ({quality_score:.0%})
    </div>
    """, unsafe_allow_html=True)


def render_export_options():
    """Render conversation export options."""
    st.markdown("### 📥 Export Conversation")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📄 Markdown", use_container_width=True):
            return 'markdown'
    with col2:
        if st.button("📋 JSON", use_container_width=True):
            return 'json'
    with col3:
        if st.button("📝 Text", use_container_width=True):
            return 'text'
    return None
