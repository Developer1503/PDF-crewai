import streamlit as st
import os
import tempfile
import time
from dotenv import load_dotenv
from gtts import gTTS
from io import BytesIO
import litellm
import speech_recognition as sr

from config.llm import get_llm_with_smart_fallback
from tools.pdf_reader import PDFReadTool

# Try to import audio recorder, fallback if not available
try:
    from audio_recorder_streamlit import audio_recorder
    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    AUDIO_RECORDER_AVAILABLE = False

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="PDF Research Assistant | AI-Powered Analysis",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
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

# --- Session State ---
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
        'voice_input': None,
        'voice_text': ''
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Helper Functions ---

def extract_pdf_content(pdf_path):
    """Extract text content from PDF"""
    try:
        pdf_tool = PDFReadTool(pdf_path=pdf_path, analyze_images=False)
        # Read the PDF content
        content = pdf_tool._run()
        return content
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def get_ai_response(user_query, pdf_context, provider="groq", use_turbo=True):
    """Get AI response using smart fallback"""
    try:
        # Use smart fallback for provider selection
        llm, provider_used = get_llm_with_smart_fallback(
            primary_provider=provider,
            use_smaller_model=use_turbo
        )
        
        # Determine model and API key based on provider
        if provider_used == "gemini":
            model = "gemini/gemini-1.5-flash"
            api_key = os.getenv("GOOGLE_API_KEY")
        else:  # groq
            model = "groq/llama-3.1-8b-instant" if use_turbo else "groq/llama-3.3-70b-versatile"
            api_key = os.getenv("GROQ_API_KEY")
        
        # Prepare context (limit to avoid token overflow)
        context_text = str(pdf_context)[:15000] if pdf_context else "No document loaded."
        
        # Create messages
        messages = [
            {
                "role": "system", 
                "content": f"""You are an expert PDF research assistant. You help users understand and analyze PDF documents.

Document Context:
{context_text}

Instructions:
- Answer questions based on the document content
- Be concise but thorough
- If information isn't in the document, say so
- Provide specific quotes or references when possible
- Format your responses clearly with markdown"""
            },
            {"role": "user", "content": user_query}
        ]
        
        # Get response
        response = litellm.completion(
            model=model,
            messages=messages,
            api_key=api_key,
            temperature=0.3
        )
        
        return response.choices[0].message.content, provider_used
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            return "⚠️ **Rate Limit Exceeded**\n\nPlease wait a moment and try again. The system will automatically switch providers.", None
        else:
            return f"❌ Error: {error_msg}", None

def generate_audio(text):
    """Generate audio from text"""
    try:
        summary_text = text[:500] if len(text) > 500 else text
        tts = gTTS(text=summary_text, lang='en', slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except Exception as e:
        return None

def transcribe_audio(audio_bytes):
    """Convert audio to text using speech recognition"""
    try:
        recognizer = sr.Recognizer()
        
        # Save audio bytes to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
            tmp_audio.write(audio_bytes)
            tmp_audio_path = tmp_audio.name
        
        # Load audio file
        with sr.AudioFile(tmp_audio_path) as source:
            audio_data = recognizer.record(source)
        
        # Recognize speech using Google Speech Recognition
        text = recognizer.recognize_google(audio_data)
        
        # Clean up temp file
        os.unlink(tmp_audio_path)
        
        return text
    except sr.UnknownValueError:
        return "❌ Could not understand audio. Please try again."
    except sr.RequestError as e:
        return f"❌ Speech recognition service error: {e}"
    except Exception as e:
        return f"❌ Error processing audio: {e}"


# --- Main App ---

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
                st.session_state.chat_history = []
                st.rerun()
        
        st.divider()
        
        if st.button("🔄 Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; opacity: 0.6; font-size: 0.8rem;'>
            <p>🧬 PDF Research Assistant</p>
            <p>Powered by AI</p>
        </div>
        """, unsafe_allow_html=True)

    # Main Area
    st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>🧬 PDF Research Assistant</h1>", unsafe_allow_html=True)
    
    # Upload Section (if no PDF uploaded)
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
                    st.session_state.chat_history = [{
                        "role": "assistant",
                        "content": f"✅ **Document loaded successfully!**\n\n📄 **{uploaded_file.name}**\n\nI've analyzed your document. What would you like to know about it?"
                    }]
                    st.rerun()
                else:
                    st.error("Failed to read PDF. Please try another file.")
    
    # Chat Interface (if PDF uploaded)
    else:
        # Chat History
        st.markdown("### 💬 Chat with Your Document")
        
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
        
        # Input Area
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
        
        # Voice Input Section (outside form)
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
                        # Automatically add to chat
                        st.session_state.chat_history.append({"role": "user", "content": transcribed_text})
                        st.session_state.voice_text = ""
                        st.rerun()
                    else:
                        st.error(transcribed_text)
        else:
            st.info("💡 **Tip**: Install `audio-recorder-streamlit` and `SpeechRecognition` for voice input support")
        
        st.markdown("---")
        
        # Text Input Section
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
                # Add user message
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                st.session_state.voice_text = ""
                st.rerun()
        
        # Process last user message if exists and no AI response yet
        if (len(st.session_state.chat_history) > 0 and 
            st.session_state.chat_history[-1]["role"] == "user" and
            not st.session_state.processing):
            
            st.session_state.processing = True
            
            with st.spinner("🤔 Thinking..."):
                user_query = st.session_state.chat_history[-1]["content"]
                
                # Get AI response
                ai_response, provider_used = get_ai_response(
                    user_query,
                    st.session_state.pdf_text,
                    st.session_state.provider,
                    st.session_state.use_turbo
                )
                
                # Add provider info if switched
                if provider_used and provider_used != st.session_state.provider:
                    ai_response = f"ℹ️ *Switched to {provider_used.upper()}*\n\n{ai_response}"
                
                # Add AI response
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                st.session_state.processing = False
                st.rerun()

if __name__ == "__main__":
    main()
