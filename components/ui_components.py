"""
UI Components for Enhanced PDF-crewai
"""

import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime


def show_status_indicator(status: str, message: str, details: str = None, 
                          retry_delay: int = None, actions: List[str] = None):
    """
    Display enhanced status indicator with user-friendly messaging
    
    Args:
        status: 'optimal', 'degraded', 'throttled', 'failure', 'maintenance'
        message: Main message to display
        details: Optional detailed information
        retry_delay: Optional countdown timer
        actions: Optional list of action buttons
    """
    status_config = {
        'optimal': {'icon': '🟢', 'color': 'success'},
        'degraded': {'icon': '🟡', 'color': 'warning'},
        'throttled': {'icon': '🟠', 'color': 'warning'},
        'failure': {'icon': '🔴', 'color': 'error'},
        'maintenance': {'icon': '⚪', 'color': 'info'}
    }
    
    config = status_config.get(status, status_config['optimal'])
    
    with st.container():
        st.markdown(f"""
        <div style='
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid {'#28a745' if config['color'] == 'success' else '#ffc107' if config['color'] == 'warning' else '#dc3545' if config['color'] == 'error' else '#17a2b8'};
            background: rgba(255,255,255,0.05);
            margin: 1rem 0;
        '>
            <div style='font-size: 1.2em; font-weight: bold; margin-bottom: 0.5rem;'>
                {config['icon']} {message}
            </div>
            {f'<div style="opacity: 0.8;">{details}</div>' if details else ''}
        </div>
        """, unsafe_allow_html=True)
        
        if retry_delay:
            st.info(f"⏱️ Retrying in {retry_delay} seconds...")
        
        if actions:
            cols = st.columns(len(actions))
            for i, action in enumerate(actions):
                with cols[i]:
                    st.button(action, key=f"action_{action}_{datetime.now().timestamp()}")


def show_document_fingerprint(fingerprint: Dict):
    """
    Display comprehensive document fingerprint
    
    Args:
        fingerprint: Dict from DocumentAnalyzer.generate_document_fingerprint()
    """
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    '>
        <h3 style='margin-top: 0;'>📄 Document Fingerprint</h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Type:** {fingerprint.get('type', 'Unknown')}  
        **Length:** {fingerprint.get('length', 'Unknown')}  
        **Estimated Pages:** {fingerprint.get('pages_estimate', 'Unknown')}  
        **Read Time:** {fingerprint.get('read_time', 'Unknown')}
        """)
    
    with col2:
        st.markdown(f"""
        **Language:** {fingerprint.get('language', 'Unknown')}  
        **Confidence:** {fingerprint.get('confidence', 0) * 100:.0f}%
        """)
    
    # Key Dates
    if fingerprint.get('key_dates'):
        st.markdown("**📅 Key Dates Found:**")
        dates = fingerprint['key_dates'][:5]
        st.write(", ".join(dates))
        
        if fingerprint.get('next_important_date'):
            st.info(f"⏰ Next important: {fingerprint['next_important_date']}")
    
    # Entities
    entities = fingerprint.get('entities', {})
    if entities.get('companies') or entities.get('people'):
        st.markdown("**🏢 Entities Detected:**")
        if entities.get('companies'):
            st.write(f"Companies: {', '.join(entities['companies'][:5])}")
        if entities.get('people'):
            st.write(f"People: {', '.join(entities['people'][:5])}")
    
    # Suggested Questions
    if fingerprint.get('suggested_questions'):
        st.markdown("**💡 Suggested Questions:**")
        for i, question in enumerate(fingerprint['suggested_questions'][:4], 1):
            st.markdown(f"{i}. {question}")
    
    st.markdown("</div>", unsafe_allow_html=True)


def show_citation_display(citation: Dict, verification: Dict = None):
    """
    Display citation with verification status
    
    Args:
        citation: Dict from CitationEngine.extract_citations()
        verification: Optional verification result
    """
    # Confidence badge
    confidence_badges = {
        'High': '🟢',
        'Medium': '🟡',
        'Low': '🔴',
        'Unknown': '⚪'
    }
    
    badge = confidence_badges.get(citation.get('confidence', 'Unknown'), '⚪')
    
    # Verification status
    if verification:
        status_icons = {
            'VERIFIED': '✅',
            'LIKELY_ACCURATE': '✓',
            'NEEDS_REVIEW': '⚠️',
            'QUESTIONABLE': '❌'
        }
        status_icon = status_icons.get(verification.get('verification_status', ''), '')
    else:
        status_icon = ''
    
    st.markdown(f"""
    <div style='
        background: rgba(26, 29, 36, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    '>
        <div style='margin-bottom: 1rem;'>
            {citation.get('answer', '')}
        </div>
        
        <div style='
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding-top: 1rem;
            font-size: 0.9em;
            opacity: 0.9;
        '>
            <div><strong>📍 Source:</strong> {citation.get('source', 'Not specified')}</div>
            <div><strong>{badge} Confidence:</strong> {citation.get('confidence', 'Unknown')} {status_icon}</div>
            <div><strong>📋 Classification:</strong> {citation.get('classification', 'UNKNOWN').replace('_', ' ').title()}</div>
            {f"<div><strong>📝 Quote:</strong> \"{citation.get('quote', '')}\"</div>" if citation.get('quote') else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if verification and verification.get('issues'):
        with st.expander("⚠️ Verification Issues"):
            for issue in verification['issues']:
                st.warning(issue)


def show_storage_stats(stats: Dict):
    """
    Display storage usage statistics
    
    Args:
        stats: Dict from StorageManager.get_storage_stats()
    """
    st.markdown("### 💾 Storage Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Documents", stats.get('document_count', 0))
    
    with col2:
        st.metric("Conversations", stats.get('conversation_count', 0))
    
    with col3:
        usage_pct = stats.get('usage_percent', 0)
        st.metric("Storage Used", f"{usage_pct:.1f}%")
    
    # Progress bar
    st.progress(min(1.0, usage_pct / 100))
    
    st.caption(f"Using {stats.get('compressed_size_mb', 0):.2f} MB of {stats.get('storage_limit_mb', 50)} MB")
    
    if usage_pct > 80:
        st.warning("⚠️ Storage is running low. Consider exporting and clearing old documents.")


def show_query_quality_feedback(quality_result: Dict):
    """
    Display query quality assessment with suggestions
    
    Args:
        quality_result: Dict from QueryOptimizer.score_question_quality()
    """
    quality = quality_result.get('quality', 'good')
    score = quality_result.get('score', 0.5)
    
    if quality == 'optimal':
        st.success(f"✅ Great question! (Quality: {score*100:.0f}%)")
    elif quality == 'good':
        st.info(f"👍 Good question (Quality: {score*100:.0f}%)")
    elif quality in ['vague', 'too_broad']:
        st.warning(f"💡 This question could be improved (Quality: {score*100:.0f}%)")
        
        if quality_result.get('suggestions'):
            with st.expander("See suggestions"):
                for suggestion in quality_result['suggestions']:
                    st.write(f"• {suggestion}")


def show_token_estimate(token_info: Dict):
    """
    Display token usage estimate
    
    Args:
        token_info: Dict from QueryOptimizer.estimate_token_cost()
    """
    total_tokens = token_info.get('total_estimated_tokens', 0)
    
    # Color code based on usage
    if total_tokens > 4000:
        color = "#dc3545"  # Red
        icon = "⚠️"
    elif total_tokens > 2000:
        color = "#ffc107"  # Yellow
        icon = "⏱️"
    else:
        color = "#28a745"  # Green
        icon = "✅"
    
    st.markdown(f"""
    <div style='
        background: rgba(255,255,255,0.05);
        border-left: 4px solid {color};
        padding: 0.5rem 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
        font-size: 0.9em;
    '>
        {icon} <strong>Estimated tokens:</strong> {total_tokens:,} 
        ({token_info.get('question_tokens', 0):,} question + {token_info.get('context_tokens', 0):,} context)
    </div>
    """, unsafe_allow_html=True)


def show_error_message(error_info: Dict):
    """
    Display user-friendly error message
    
    Args:
        error_info: Dict from ErrorHandler.get_user_message()
    """
    icon = error_info.get('icon', '🔴')
    title = error_info.get('title', 'Error')
    message = error_info.get('message', '')
    severity = error_info.get('severity', 'error')
    
    if severity == 'error':
        st.error(f"{icon} **{title}**\n\n{message}")
    elif severity == 'warning':
        st.warning(f"{icon} **{title}**\n\n{message}")
    else:
        st.info(f"{icon} **{title}**\n\n{message}")
    
    # Show technical details in expander
    if error_info.get('technical_details'):
        with st.expander("🔧 Technical Details (for debugging)"):
            st.code(error_info['technical_details'])


def show_document_workspace(documents: List[Dict]):
    """
    Display multi-document workspace
    
    Args:
        documents: List of document metadata dicts
    """
    st.markdown("### 📚 Document Workspace")
    
    if not documents:
        st.info("No documents loaded. Upload a PDF to get started.")
        return
    
    st.write(f"**{len(documents)} document(s) loaded**")
    
    for doc in documents:
        with st.expander(f"📄 {doc.get('filename', 'Unknown')} ({doc.get('size_mb', 0):.2f} MB)"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Uploaded:** {doc.get('upload_date', 'Unknown')}")
                st.write(f"**Last Accessed:** {doc.get('last_accessed', 'Unknown')}")
            
            with col2:
                st.write(f"**Compression:** {doc.get('compression_ratio', 1):.1f}x")
            
            if st.button(f"Load {doc.get('filename', 'this document')}", key=f"load_{doc.get('id')}"):
                return doc.get('id')
    
    return None
