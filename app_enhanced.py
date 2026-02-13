"""
Enhanced PDF Chat Application
Improved chatting logic with better UX, context management, and features
"""

import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
import litellm
from datetime import datetime

# Core imports
from config.llm import get_llm_with_smart_fallback
from tools.pdf_reader import PDFReadTool
from utils.chat_manager import ChatManager, ResponseFormatter, StreamingResponseHandler
from utils.query_optimizer import QueryOptimizer
from utils.citation_engine import CitationEngine
from components.chat_ui import (
    render_message_bubble, render_chat_input, render_typing_indicator,
    render_conversation_stats, render_quick_actions, render_context_panel,
    apply_enhanced_chat_styles, render_export_options
)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Enhanced PDF Chat Assistant",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply enhanced styles
apply_enhanced_chat_styles()

# Initialize managers
@st.cache_resource
def get_chat_managers():
    return {
        'chat': ChatManager(),
        'query_optimizer': QueryOptimizer(),
        'citation_engine': CitationEngine(),
        'formatter': ResponseFormatter(),
        'streaming': StreamingResponseHandler()
    }

managers = get_chat_managers()

# Session State Initialization
def init_session_state():
    defaults = {
        'pdf_uploaded': False,
        'pdf_content': None,
        'pdf_name': None,
        'pdf_path': None,
        'pdf_text': None,
        'chat_history': [],
        'processing': False,
        'provider': 'groq',
        'use_turbo': True,
        'show_stats': False,
        'suggested_questions': [
            "What is this document about?",
            "Summarize the key findings",
            "What are the main conclusions?"
        ],
        'regenerate_index': None,
        'copy_content': None,
        'enable_streaming': True,
        'show_context_panel': False
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
        st.error(f"Error reading PDF: {e}")
        return None

def get_ai_response_enhanced(user_query, pdf_context, provider="groq", use_turbo=True):
    """Get AI response with enhanced processing"""
    try:
        # Process user message
        processed = managers['chat'].process_user_message(user_query, pdf_context)
        
        # Check if from cache
        if processed.get('from_cache'):
            return processed
        
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
        
        # Optimize context
        optimized_context = managers['query_optimizer'].optimize_context(
            pdf_context, user_query, max_tokens=3000
        )
        
        # Enhanced system prompt with citations
        base_prompt = f"""You are an expert PDF research assistant. You help users understand and analyze PDF documents.

Document Context:
{optimized_context[:10000]}

Instructions:
- Answer questions based on the document content
- Be concise, clear, and helpful
- If information isn't in the document, say so clearly
- Use markdown formatting for better readability
- Provide specific quotes or references when possible
- Structure your responses with headers and bullet points when appropriate"""
        
        system_prompt = managers['citation_engine'].enhance_system_prompt(base_prompt)
        
        # Get context window from chat manager
        context_messages = managers['chat'].context.get_context_window()
        
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            *context_messages,
            {"role": "user", "content": processed['enhanced_prompt']}
        ]
        
        # Get response
        response = litellm.completion(
            model=model,
            messages=messages,
            api_key=api_key,
            temperature=0.3,
            max_tokens=2000
        )
        
        raw_response = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
        
        # Extract citations
        citation_info = managers['citation_engine'].extract_citations(raw_response)
        
        # Process AI response
        result = managers['chat'].process_ai_response(
            raw_response,
            user_query,
            pdf_context,
            metadata={
                'provider': provider_used,
                'tokens_used': tokens_used,
                'model': model,
                'citation': citation_info
            }
        )
        
        result['provider'] = provider_used
        result['citation'] = citation_info
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            return {
                'error': True,
                'formatted_response': "⚠️ **Rate Limit Exceeded**\n\nPlease wait a moment and try again. The system will automatically switch providers.",
                'provider': None
            }
        else:
            return {
                'error': True,
                'formatted_response': f"❌ **Error:** {error_msg}",
                'provider': None
            }

# Main App
def main():
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎛️ Control Panel")
        
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
            index=0
        )
        
        st.session_state.use_turbo = st.toggle(
            "⚡ Turbo Mode", 
            value=True,
            help="Use smaller, faster models"
        )
        
        st.session_state.enable_streaming = st.toggle(
            "📡 Streaming Responses",
            value=True,
            help="Show responses as they're generated"
        )
        
        st.divider()
        
        # Document Info
        if st.session_state.pdf_uploaded:
            st.markdown("### 📄 Current Document")
            st.success(f"✅ {st.session_state.pdf_name}")
            
            if st.button("🗑️ Remove Document", use_container_width=True):
                st.session_state.pdf_uploaded = False
                st.session_state.pdf_content = None
                st.session_state.pdf_name = None
                st.session_state.pdf_path = None
                st.session_state.pdf_text = None
                managers['chat'].clear_conversation()
                st.rerun()
        
        st.divider()
        
        # Conversation Management
        st.markdown("### 💬 Conversation")
        
        if st.button("🔄 Clear Chat", use_container_width=True):
            managers['chat'].clear_conversation()
            st.session_state.chat_history = []
            st.rerun()
        
        st.session_state.show_stats = st.toggle(
            "📊 Show Statistics",
            value=st.session_state.show_stats
        )
        
        st.session_state.show_context_panel = st.toggle(
            "📚 Show Context Panel",
            value=st.session_state.show_context_panel
        )
        
        # Export
        if managers['chat'].context.messages:
            st.divider()
            export_format = render_export_options()
            
            if export_format:
                export_data = managers['chat'].export_conversation(export_format)
                file_ext = {'markdown': 'md', 'json': 'json', 'text': 'txt'}[export_format]
                
                st.download_button(
                    "💾 Download",
                    export_data,
                    file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}",
                    mime=f"text/{export_format}",
                    use_container_width=True
                )
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; opacity: 0.6; font-size: 0.8rem;'>
            <p>💬 Enhanced PDF Chat</p>
            <p>v3.0 - Powered by AI</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main Area
    st.markdown("<h1 style='text-align: center;'>💬 Enhanced PDF Chat Assistant</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; opacity: 0.8;'>Upload a PDF and have an intelligent conversation about its content</p>", unsafe_allow_html=True)
    
    # Upload Section
    if not st.session_state.pdf_uploaded:
        st.markdown("""
        <div style='text-align: center; padding: 3rem; background: rgba(102, 126, 234, 0.05); border-radius: 16px; border: 2px dashed rgba(102, 126, 234, 0.3);'>
            <h2>📤 Upload Your PDF Document</h2>
            <p style='opacity: 0.8; margin-top: 1rem;'>Upload a PDF to start an intelligent conversation</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file", 
            type="pdf",
            help="Upload any PDF document"
        )
        
        if uploaded_file:
            with st.spinner("📖 Reading your document..."):
                # Save temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    st.session_state.pdf_path = tmp.name
                
                # Extract content
                pdf_text = extract_pdf_content(st.session_state.pdf_path)
                
                if pdf_text:
                    st.session_state.pdf_name = uploaded_file.name
                    st.session_state.pdf_text = pdf_text
                    st.session_state.pdf_uploaded = True
                    
                    # Add welcome message
                    welcome_msg = {
                        'role': 'assistant',
                        'content': f"✅ **Document loaded successfully!**\n\n📄 **{uploaded_file.name}**\n\nI've analyzed your document. What would you like to know about it?",
                        'timestamp': datetime.now().isoformat(),
                        'metadata': {}
                    }
                    managers['chat'].context.add_message('assistant', welcome_msg['content'])
                    
                    # Generate suggested questions
                    st.session_state.suggested_questions = [
                        "What is this document about?",
                        "Summarize the key points",
                        "What are the main findings?",
                        "Who is the target audience?"
                    ]
                    
                    st.rerun()
                else:
                    st.error("Failed to read PDF. Please try another file.")
    
    # Chat Interface
    else:
        # Context Panel
        if st.session_state.show_context_panel:
            render_context_panel({
                'document_name': st.session_state.pdf_name,
                'context_messages': len(managers['chat'].context.messages),
                'topics': [t['topic'] for t in managers['chat'].context.topic_tracking]
            })
        
        # Statistics
        if st.session_state.show_stats:
            stats = managers['chat'].get_conversation_stats()
            render_conversation_stats(stats)
            st.divider()
        
        # Chat History
        st.markdown("### 💬 Conversation")
        
        chat_container = st.container()
        with chat_container:
            messages = list(managers['chat'].context.messages)
            for i, msg in enumerate(messages):
                render_message_bubble(msg, i, show_actions=True)
        
        # Check for regeneration request
        if st.session_state.regenerate_index is not None:
            regen_query = managers['chat'].regenerate_response(st.session_state.regenerate_index)
            if regen_query:
                st.session_state.regenerate_index = None
                # Add to processing queue
                st.session_state.processing = True
                st.rerun()
        
        st.markdown("---")
        
        # Quick Actions
        quick_actions = [
            {'icon': '📝', 'label': 'Summarize', 'query': 'Please provide a comprehensive summary of this document'},
            {'icon': '🔍', 'label': 'Key Findings', 'query': 'What are the main findings or key takeaways?'},
            {'icon': '📊', 'label': 'Analyze', 'query': 'Provide a detailed analysis of this document'},
            {'icon': '❓', 'label': 'Q&A', 'query': 'What important questions should I ask about this document?'}
        ]
        
        quick_query = render_quick_actions(quick_actions)
        if quick_query:
            managers['chat'].context.add_message('user', quick_query)
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Chat Input
        user_input = render_chat_input(
            placeholder="Ask anything about your document...",
            show_voice=False,
            show_suggestions=True
        )
        
        if user_input:
            # Quality check
            quality = managers['query_optimizer'].score_question_quality(user_input)
            if quality['quality'] in ['vague', 'too_broad'] and quality['suggestions']:
                st.warning(f"💡 **Tip:** {quality['suggestions'][0]}")
            
            # Add to chat
            managers['chat'].context.add_message('user', user_input)
            st.rerun()
        
        # Process last user message
        messages = list(managers['chat'].context.messages)
        if (messages and 
            messages[-1]['role'] == 'user' and
            not st.session_state.processing):
            
            st.session_state.processing = True
            
            # Show typing indicator
            with st.spinner(""):
                render_typing_indicator()
                
                user_query = messages[-1]['content']
                
                # Get AI response
                result = get_ai_response_enhanced(
                    user_query,
                    st.session_state.pdf_text,
                    st.session_state.provider,
                    st.session_state.use_turbo
                )
                
                # Display response
                if result.get('error'):
                    st.error(result['formatted_response'])
                else:
                    # Add provider info if switched
                    response_text = result['formatted_response']
                    if result.get('provider') and result['provider'] != st.session_state.provider:
                        response_text = f"ℹ️ *Switched to {result['provider'].upper()}*\n\n{response_text}"
                    
                    # Update chat history (already done in manager)
                    pass
                
                st.session_state.processing = False
                st.rerun()

if __name__ == "__main__":
    main()
