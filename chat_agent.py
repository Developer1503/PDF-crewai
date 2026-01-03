import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
import litellm
from tools.pdf_reader import PDFReadTool

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="AI Chat Agent - PDF Assistant",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for chat interface
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 20%;
    }
    .assistant-message {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        margin-right: 20%;
    }
    .stTextInput > div > div > input {
        background-color: #1e1e1e;
        color: white;
        border: 1px solid #444;
    }
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #333;
        border-radius: 10px;
        background-color: #0e1117;
    }
</style>
""", unsafe_allow_html=True)

def get_llm_response(messages, provider="groq"):
    """Get response from LLM using LiteLLM."""
    try:
        if provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                return "Error: GROQ_API_KEY not found in .env file"
            
            response = litellm.completion(
                model="groq/llama-3.3-70b-versatile",
                messages=messages,
                api_key=api_key,
                temperature=0.7,
                max_tokens=4000
            )
            return response.choices[0].message.content
        
        elif provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return "Error: GOOGLE_API_KEY not found in .env file"
            
            response = litellm.completion(
                model="gemini/gemini-2.0-flash",
                messages=messages,
                api_key=api_key,
                temperature=0.7,
                max_tokens=4000
            )
            return response.choices[0].message.content
            
    except Exception as e:
        return f"Error: {str(e)}"

def extract_pdf_content(pdf_path):
    """Extract content from PDF including text and image analysis."""
    try:
        pdf_tool = PDFReadTool(pdf_path=pdf_path, analyze_images=False)  # Disable image analysis to save quota
        return pdf_tool._run()
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

def get_ai_response(chat_history, pdf_content, user_question, provider):
    """Get AI response based on PDF content and chat history."""
    
    # Build messages for the LLM
    system_message = f"""You are a helpful AI assistant that answers questions about a PDF document.
You have access to the following document content:

=== DOCUMENT CONTENT ===
{pdf_content[:30000]}
=== END OF DOCUMENT ===

Instructions:
- Answer questions based on the document content
- Be helpful, accurate, and conversational
- If the information is not in the document, say so honestly
- Format your responses with markdown for readability"""

    messages = [{"role": "system", "content": system_message}]
    
    # Add chat history (last 6 messages for context)
    for msg in chat_history[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add current question
    messages.append({"role": "user", "content": user_question})
    
    return get_llm_response(messages, provider)

def main():
    st.title("🤖 Interactive AI Chat Agent")
    st.markdown("""
    Upload a PDF and have a conversation with an AI agent about its content!
    Ask questions, get explanations, and explore your document interactively.
    """)
    
    # Initialize session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "pdf_content" not in st.session_state:
        st.session_state.pdf_content = None
    if "pdf_name" not in st.session_state:
        st.session_state.pdf_name = None
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # LLM Provider selection
        provider = st.selectbox(
            "Select AI Provider",
            ["groq", "gemini"],
            index=0,
            help="Groq is faster. Gemini may have quota limits."
        )
        
        # Show API key status
        groq_key = os.getenv("GROQ_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")
        
        if provider == "groq":
            if groq_key:
                st.success("✅ Groq API Key loaded")
            else:
                st.error("❌ Groq API Key missing")
        else:
            if google_key:
                st.success("✅ Google API Key loaded")
            else:
                st.error("❌ Google API Key missing")
        
        st.divider()
        st.header("📄 Document Upload")
        
        uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
        
        if uploaded_file is not None and uploaded_file.name != st.session_state.pdf_name:
            with st.spinner("📖 Reading PDF..."):
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    pdf_path = tmp_file.name
                
                # Extract content
                try:
                    content = extract_pdf_content(pdf_path)
                    st.session_state.pdf_content = content
                    st.session_state.pdf_name = uploaded_file.name
                    st.session_state.chat_history = []  # Clear chat for new document
                    st.success(f"✅ Loaded: {uploaded_file.name}")
                    
                    # Show preview
                    with st.expander("📋 Document Preview"):
                        st.text(content[:2000] + "..." if len(content) > 2000 else content)
                        
                except Exception as e:
                    st.error(f"Error reading PDF: {e}")
                finally:
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
        
        if st.session_state.pdf_content:
            st.info(f"📄 Active: {st.session_state.pdf_name}")
            
            if st.button("🗑️ Clear Chat History"):
                st.session_state.chat_history = []
                st.rerun()
        
        st.divider()
        st.markdown("### 💡 Example Questions")
        st.markdown("""
        - What is this document about?
        - Summarize the main points
        - What are the key findings?
        - Explain [specific topic]
        """)
    
    # Main chat area
    if st.session_state.pdf_content is None:
        st.info("👆 Please upload a PDF document from the sidebar to start chatting!")
        
        # Demo mode without PDF
        st.markdown("---")
        st.subheader("💬 Or chat without a document")
        demo_input = st.text_input("Ask me anything:", key="demo_input", placeholder="Type your question here...")
        
        if demo_input:
            with st.spinner("🤔 Thinking..."):
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant. Answer questions helpfully and concisely."},
                    {"role": "user", "content": demo_input}
                ]
                response = get_llm_response(messages, provider)
                st.markdown(f"**🤖 Assistant:** {response}")
    else:
        # Display chat history
        st.markdown("### 💬 Chat")
        
        # Chat messages container
        chat_container = st.container()
        
        with chat_container:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>👤 You</strong>
                        <p>{msg['content']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <strong>🤖 AI Assistant</strong>
                        <p>{msg['content']}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Chat input
        st.markdown("---")
        col1, col2 = st.columns([6, 1])
        
        with col1:
            user_input = st.text_input(
                "Your message:",
                key="user_input",
                placeholder="Ask a question about your document...",
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.button("Send 📤", use_container_width=True)
        
        # Process input
        if (send_button or user_input) and user_input:
            # Add user message to history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Get AI response
            with st.spinner("🤔 Thinking..."):
                response = get_ai_response(
                    st.session_state.chat_history,
                    st.session_state.pdf_content,
                    user_input,
                    provider
                )
            
            # Add assistant response to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })
            
            # Rerun to update chat display
            st.rerun()
        
        # Quick action buttons
        st.markdown("### ⚡ Quick Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📋 Summarize", use_container_width=True):
                question = "Please summarize this document in a clear and concise way."
                st.session_state.chat_history.append({"role": "user", "content": question})
                with st.spinner("Summarizing..."):
                    response = get_ai_response(st.session_state.chat_history, st.session_state.pdf_content, question, provider)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
        
        with col2:
            if st.button("🔑 Key Points", use_container_width=True):
                question = "What are the key points in this document? List them as bullet points."
                st.session_state.chat_history.append({"role": "user", "content": question})
                with st.spinner("Extracting key points..."):
                    response = get_ai_response(st.session_state.chat_history, st.session_state.pdf_content, question, provider)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
        
        with col3:
            if st.button("📊 Data Insights", use_container_width=True):
                question = "What data, statistics, or numbers are mentioned in this document?"
                st.session_state.chat_history.append({"role": "user", "content": question})
                with st.spinner("Analyzing data..."):
                    response = get_ai_response(st.session_state.chat_history, st.session_state.pdf_content, question, provider)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
        
        with col4:
            if st.button("❓ Q&A Format", use_container_width=True):
                question = "Generate 5 important Q&A pairs from this document that would help someone understand it."
                st.session_state.chat_history.append({"role": "user", "content": question})
                with st.spinner("Generating Q&A..."):
                    response = get_ai_response(st.session_state.chat_history, st.session_state.pdf_content, question, provider)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()


if __name__ == "__main__":
    main()
