"""
Enhanced Chat UI Components
Beautiful and functional chat interface elements
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional
import re


def render_message_bubble(message: Dict, index: int, show_actions: bool = True):
    """Render a single message bubble with enhanced styling"""
    role = message.get('role', 'user')
    content = message.get('content', '')
    timestamp = message.get('timestamp', datetime.now().isoformat())
    metadata = message.get('metadata', {})
    
    # Parse timestamp
    try:
        dt = datetime.fromisoformat(timestamp)
        time_str = dt.strftime('%I:%M %p')
    except:
        time_str = ''
    
    if role == 'user':
        st.markdown(f"""
        <div class="chat-message user-message" id="msg-{index}">
            <div class="message-header">
                <span class="message-icon">👤</span>
                <span class="message-role">You</span>
                <span class="message-time">{time_str}</span>
            </div>
            <div class="message-content">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # AI message with additional features
        provider = metadata.get('provider', '')
        tokens = metadata.get('tokens_used', 0)
        confidence = metadata.get('confidence', '')
        
        st.markdown(f"""
        <div class="chat-message ai-message" id="msg-{index}">
            <div class="message-header">
                <span class="message-icon">🤖</span>
                <span class="message-role">AI Assistant</span>
                {f'<span class="message-provider">{provider.upper()}</span>' if provider else ''}
                <span class="message-time">{time_str}</span>
            </div>
            <div class="message-content">
        """, unsafe_allow_html=True)
        
        # Render markdown content
        st.markdown(content)
        
        st.markdown("""
            </div>
        """, unsafe_allow_html=True)
        
        # Show metadata if available
        if tokens or confidence:
            col1, col2 = st.columns([3, 1])
            with col2:
                if tokens:
                    st.caption(f"🔢 {tokens} tokens")
                if confidence:
                    st.caption(f"📊 {confidence}")
        
        # Action buttons
        if show_actions:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("👍", key=f"like_{index}", help="Helpful"):
                    st.session_state[f'feedback_{index}'] = 'positive'
            with col2:
                if st.button("👎", key=f"dislike_{index}", help="Not helpful"):
                    st.session_state[f'feedback_{index}'] = 'negative'
            with col3:
                if st.button("🔄", key=f"regen_{index}", help="Regenerate"):
                    st.session_state['regenerate_index'] = index
            with col4:
                if st.button("📋", key=f"copy_{index}", help="Copy"):
                    st.session_state['copy_content'] = content


def render_chat_input(placeholder: str = "Ask a question...", 
                      show_voice: bool = False,
                      show_suggestions: bool = True) -> Optional[str]:
    """Render enhanced chat input with suggestions"""
    
    # Suggestions
    if show_suggestions and 'suggested_questions' in st.session_state:
        st.markdown("**💡 Suggested questions:**")
        suggestions = st.session_state.get('suggested_questions', [])
        
        cols = st.columns(min(len(suggestions), 3))
        for i, suggestion in enumerate(suggestions[:3]):
            with cols[i]:
                if st.button(f"💬 {suggestion[:30]}...", key=f"suggest_{i}", use_container_width=True):
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
                voice_button = st.form_submit_button("🎤 Voice", use_container_width=True)
        
        if send_button and user_input:
            return user_input
    
    return None


def render_typing_indicator():
    """Show typing indicator animation"""
    st.markdown("""
    <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    </div>
    
    <style>
    .typing-indicator {
        display: flex;
        gap: 4px;
        padding: 1rem;
        align-items: center;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #667eea;
        animation: typing 1.4s infinite;
    }
    
    .typing-dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes typing {
        0%, 60%, 100% {
            opacity: 0.3;
            transform: scale(0.8);
        }
        30% {
            opacity: 1;
            transform: scale(1.2);
        }
    }
    </style>
    """, unsafe_allow_html=True)


def render_conversation_stats(stats: Dict):
    """Display conversation statistics"""
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
    """Render quick action buttons"""
    st.markdown("**⚡ Quick Actions:**")
    
    # Group actions in rows of 4
    for i in range(0, len(actions), 4):
        cols = st.columns(4)
        for j, action in enumerate(actions[i:i+4]):
            with cols[j]:
                icon = action.get('icon', '💬')
                label = action.get('label', 'Action')
                query = action.get('query', '')
                
                if st.button(f"{icon} {label}", key=f"action_{i}_{j}", use_container_width=True):
                    return query
    
    return None


def render_message_search(messages: List[Dict]) -> Optional[List[int]]:
    """Search through conversation messages"""
    search_query = st.text_input("🔍 Search conversation", placeholder="Search messages...")
    
    if search_query:
        matching_indices = []
        for i, msg in enumerate(messages):
            if search_query.lower() in msg.get('content', '').lower():
                matching_indices.append(i)
        
        if matching_indices:
            st.success(f"Found {len(matching_indices)} matching message(s)")
            return matching_indices
        else:
            st.info("No matching messages found")
    
    return None


def render_context_panel(context_info: Dict):
    """Display context information panel"""
    with st.expander("📚 Context Information", expanded=False):
        st.markdown(f"""
        **Document:** {context_info.get('document_name', 'N/A')}
        
        **Context Window:** {context_info.get('context_messages', 0)} messages
        
        **Topics Discussed:**
        """)
        
        topics = context_info.get('topics', [])
        if topics:
            for topic in topics[-5:]:  # Show last 5 topics
                st.markdown(f"- {topic}")
        else:
            st.markdown("_No topics tracked yet_")


def render_response_quality_indicator(quality_score: float):
    """Show response quality indicator"""
    if quality_score >= 0.8:
        color = "#4CAF50"
        label = "Excellent"
        icon = "🟢"
    elif quality_score >= 0.6:
        color = "#FFC107"
        label = "Good"
        icon = "🟡"
    else:
        color = "#F44336"
        label = "Needs Improvement"
        icon = "🔴"
    
    st.markdown(f"""
    <div style="padding: 0.5rem; border-left: 4px solid {color}; background: rgba(255,255,255,0.05); margin: 0.5rem 0;">
        {icon} <strong>Response Quality:</strong> {label} ({quality_score:.0%})
    </div>
    """, unsafe_allow_html=True)


def render_citation_card(citation: Dict):
    """Render a citation card"""
    st.markdown(f"""
    <div class="citation-card">
        <div class="citation-header">
            📚 <strong>Citation</strong>
        </div>
        <div class="citation-body">
            <p><strong>Source:</strong> {citation.get('source', 'N/A')}</p>
            <p><strong>Confidence:</strong> {citation.get('confidence', 'Unknown')}</p>
            {f'<p><strong>Quote:</strong> "{citation.get("quote", "")}"</p>' if citation.get('quote') else ''}
            <p><strong>Pages:</strong> {', '.join(map(str, citation.get('page_numbers', []))) or 'N/A'}</p>
        </div>
    </div>
    
    <style>
    .citation-card {
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: rgba(102, 126, 234, 0.05);
    }
    
    .citation-header {
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #667eea;
    }
    
    .citation-body p {
        margin: 0.25rem 0;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)


def render_export_options():
    """Render conversation export options"""
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


def apply_enhanced_chat_styles():
    """Apply enhanced CSS styles for chat interface"""
    st.markdown("""
    <style>
    /* Enhanced Chat Styles */
    .chat-message {
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        animation: slideIn 0.3s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .message-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
        font-size: 0.9rem;
        opacity: 0.8;
    }
    
    .message-icon {
        font-size: 1.2rem;
    }
    
    .message-role {
        font-weight: 600;
    }
    
    .message-provider {
        background: rgba(102, 126, 234, 0.2);
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .message-time {
        margin-left: auto;
        font-size: 0.75rem;
        opacity: 0.6;
    }
    
    .message-content {
        line-height: 1.6;
    }
    
    .user-message {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        margin-left: 2rem;
        border-bottom-right-radius: 4px;
    }
    
    .ai-message {
        background: rgba(26, 29, 36, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-right: 2rem;
        border-bottom-left-radius: 4px;
    }
    
    /* Code blocks */
    .ai-message code {
        background: rgba(0, 0, 0, 0.3);
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
    }
    
    .ai-message pre {
        background: rgba(0, 0, 0, 0.3);
        padding: 1rem;
        border-radius: 8px;
        overflow-x: auto;
        border-left: 3px solid #667eea;
    }
    
    /* Scrollbar styling */
    .chat-container::-webkit-scrollbar {
        width: 8px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: rgba(102, 126, 234, 0.5);
        border-radius: 4px;
    }
    
    .chat-container::-webkit-scrollbar-thumb:hover {
        background: rgba(102, 126, 234, 0.7);
    }
    
    /* Input area */
    .stTextArea textarea {
        border-radius: 8px !important;
        border: 1px solid rgba(102, 126, 234, 0.3) !important;
        background: rgba(26, 29, 36, 0.8) !important;
    }
    
    .stTextArea textarea:focus {
        border-color: rgba(102, 126, 234, 0.6) !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
    }
    
    /* Buttons */
    .stButton button {
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)
