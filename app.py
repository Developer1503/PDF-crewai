import streamlit as st
import os
import tempfile
import time
import json
import base64
from io import BytesIO
from dotenv import load_dotenv
from streamlit_lottie import st_lottie
from gtts import gTTS

from config.llm import get_llm
from crew import create_crew
import litellm

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="PDF Research Crew | Intelligent Analysis",
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

        /* Step Progress Bar */
        .progress-flow {
            display: flex;
            justify-content: space-between;
            position: relative;
            margin-bottom: 3rem;
        }
        
        .progress-line {
            position: absolute;
            top: 50%;
            left: 0;
            width: 100%;
            height: 2px;
            background: #2d3139;
            z-index: 0;
            transform: translateY(-50%);
        }
        
        .progress-line-fill {
            position: absolute;
            top: 50%;
            left: 0;
            height: 2px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            z-index: 0;
            transform: translateY(-50%);
            transition: width 0.5s ease;
        }

        .step-bubble {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            z-index: 1;
            background: #1a1d24;
            border: 2px solid #444;
            color: #888;
            transition: all 0.3s ease;
        }
        
        .step-bubble.active {
            background: #667eea;
            border-color: #667eea;
            color: white;
            box-shadow: 0 0 15px rgba(102, 126, 234, 0.5);
        }
        
        .step-bubble.completed {
            background: #11998e;
            border-color: #11998e;
            color: white;
        }

        /* Agent Animations */
        @keyframes pulse-ring {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(102, 126, 234, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(102, 126, 234, 0); }
        }
        
        .agent-active-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #667eea;
            animation: pulse-ring 2s infinite;
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
    </style>
    """, unsafe_allow_html=True)

load_custom_css()

# --- Lottie Animation Loader ---
@st.cache_data
def load_lottie_url(url: str):
    import requests
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# Load animations (URLs for reliable AI/Robotics animations)
lottie_ai_scan = "https://lottie.host/5a8b7923-3803-4674-9c94-136015690dfa/qR1s5F5q2P.json"
lottie_processing = "https://lottie.host/9f66717a-514d-4444-9c94-09945c71a337/8q5s5F5q2P.json" 
lottie_success = "https://lottie.host/7e0b5030-222a-4424-8178-508544a00448/M12e3X4Y5Z.json"
# Note: Using fallback generic URLs if these precise ones fail in future, but structure is ready.
# For now, let's use reliable placeholder URLs or None handling.

# --- Session State ---
def init_session_state():
    defaults = {
        'current_step': 1,
        'pdf_uploaded': False,
        'pdf_content': None,
        'pdf_name': None,
        'pdf_path': None,
        'analysis_result': None,
        'analysis_complete': False,
        'chat_history': [],
        'agent_progress': {
            'researcher': 'waiting',
            'analyst': 'waiting',
            'writer': 'waiting',
            'reviewer': 'waiting'
        },
        'config': {
            'include_images': False,
            'analysis_depth': 'Quick',
            'output_tone': 'Professional',
            'generate_summary': True,
            'use_smaller_model': True
        }
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Components ---

def render_step_indicator():
    steps = ["Upload", "Configure", "Analyze", "Interact"]
    current = st.session_state.current_step
    
    # Use columns for a cleaner approach
    cols = st.columns(len(steps))
    
    for i, (col, step) in enumerate(zip(cols, steps)):
        step_num = i + 1
        with col:
            if step_num < current:
                # Completed
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="width: 40px; height: 40px; border-radius: 50%; background: #11998e; 
                                color: white; display: flex; align-items: center; justify-content: center; 
                                margin: 0 auto; font-weight: bold;">✓</div>
                    <div style="margin-top: 0.5rem; font-size: 0.8rem; color: #11998e;">{step}</div>
                </div>
                """, unsafe_allow_html=True)
            elif step_num == current:
                # Active
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="width: 40px; height: 40px; border-radius: 50%; background: #667eea; 
                                color: white; display: flex; align-items: center; justify-content: center; 
                                margin: 0 auto; font-weight: bold; box-shadow: 0 0 15px rgba(102, 126, 234, 0.5);">{step_num}</div>
                    <div style="margin-top: 0.5rem; font-size: 0.8rem; color: white; font-weight: 600;">{step}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Pending
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="width: 40px; height: 40px; border-radius: 50%; background: #2d3139; 
                                color: #666; display: flex; align-items: center; justify-content: center; 
                                margin: 0 auto; font-weight: bold;">{step_num}</div>
                    <div style="margin-top: 0.5rem; font-size: 0.8rem; color: #666;">{step}</div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

def render_agent_status(agent_name, role, status):
    status_color = "#444"
    if status == "active": status_color = "#667eea"
    if status == "completed": status_color = "#11998e"
    
    active_dot = '<div class="agent-active-indicator"></div>' if status == "active" else ""
    
    st.markdown(f"""
    <div class="glass-card" style="border-left: 4px solid {status_color}; padding: 1rem; display: flex; align-items: center; gap: 1rem;">
        <div style="font-size: 1.5rem;">{'🤖' if agent_name == 'Researcher' else '📊' if agent_name == 'Analyst' else '✍️' if agent_name == 'Writer' else '✅'}</div>
        <div style="flex: 1;">
            <div style="font-weight: 600; color: white;">{agent_name} {active_dot}</div>
            <div style="font-size: 0.8rem; color: #888;">{role}</div>
        </div>
        <div style="font-size: 0.75rem; color: {status_color}; font-weight: 600; text-transform: uppercase;">
            {status}
        </div>
    </div>
    """, unsafe_allow_html=True)

def generate_audio_summary(text):
    try:
        # Extract the first 500 chars or introduction for TTS to keep it quick
        summary_text = text[:500] if len(text) > 500 else text
        tts = gTTS(text=summary_text, lang='en', slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except Exception as e:
        return None

def chat_interface():
    st.markdown("### 💬 Chat with your Document")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.chat_history:
            st.info("👋 Hi! I've analyzed your document. Ask me anything about it!")
        
        for msg in st.session_state.chat_history:
            div_class = "user-message" if msg["role"] == "user" else "ai-message"
            icon = "👤" if msg["role"] == "user" else "🤖"
            st.markdown(f"""
            <div class="chat-message {div_class}">
                <div style="font-size: 0.8rem; opacity: 0.7; margin-bottom: 0.25rem;">{icon} {msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)

    # Input area
    with st.form("chat_input", clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        with col1:
            user_input = st.text_input("Ask a question...", placeholder="e.g., What are the main findings?", label_visibility="collapsed")
        with col2:
            sent = st.form_submit_button("Send 🚀", use_container_width=True)
            
        if sent and user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # Simple RAG-like response using the analysis result context
            # In a real app we'd use the vector store again, but here we can use the full text context if small enough
            # or just use the generated report as context for cheaper/faster answers
            
            with st.spinner("Thinking..."):
                try:
                    # Get provider from sidebar selection if possible, else default
                    # Simple fallback logic for chat
                    api_key = os.getenv("GOOGLE_API_KEY") 
                    model = "gemini/gemini-2.0-flash-exp" # Default to fast gemini
                    
                    context = st.session_state.analysis_result
                    if not context: context = "Summary available."

                    response = litellm.completion(
                        model=model,
                        messages=[
                            {"role": "system", "content": f"You are a helpful assistant. Context from document:\n{str(context)[:10000]}"},
                            {"role": "user", "content": user_input}
                        ],
                        api_key=api_key
                    )
                    reply = response.choices[0].message.content
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.rerun()
                except Exception as e:
                    st.error(f"Chat Error: {e}")

# --- Main App Logic ---

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
        st.markdown("### ⚙️ Engine")
        provider = st.selectbox("Provider", ["gemini", "groq"], index=0, help="Gemini is recommended for fewer rate limits.")
        
        if provider == "groq":
            st.warning("⚠️ High traffic. Rate limits likely.")
            
        st.divider()
        if st.button("🗑️ Reset All", type="secondary"):
            st.session_state.current_step = 1
            st.session_state.analysis_complete = False
            st.session_state.chat_history = []
            st.rerun()

    # Main Area
    st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>🧬 PDF Research Crew</h1>", unsafe_allow_html=True)
    render_step_indicator()
    
    # Step 1: Upload
    if st.session_state.current_step == 1:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("""
            <div class="glass-card">
                <h3>📤 Upload Document</h3>
                <p>Drag and drop your PDF research paper, report, or contract here.</p>
            </div>
            """, unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")
            
            if uploaded_file:
                # Save temp
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    st.session_state.pdf_path = tmp.name
                st.session_state.pdf_name = uploaded_file.name
                
                st.success(f"Loaded: {uploaded_file.name}")
                if st.button("Continue ➡️", type="primary", use_container_width=True):
                    st.session_state.current_step = 2
                    st.rerun()
                    
        with col2:
            # Animation placeholder (using text if lottie fails to load or no internet)
            st.markdown("""
            <div style="text-align: center; color: #667eea; font-size: 5rem; margin-top: 2rem;">
                📄 ➡️ 🧠
            </div>
            <p style="text-align: center; opacity: 0.6;">Transforming documents into intelligence</p>
            """, unsafe_allow_html=True)

    # Step 2: Configure
    elif st.session_state.current_step == 2:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("### 🎯 Configure Analysis")
            with st.container(border=True):
                st.session_state.config['include_images'] = st.toggle("🖼️ Analyze Images (Charts/Graphs)", value=False, help="Uses Vision AI. Slower but more detailed.")
                st.session_state.config['use_smaller_model'] = st.toggle("⚡ Turbo Mode (Save Tokens)", value=True, help="Uses lighter models for speed.")
                st.session_state.config['analysis_depth'] = st.select_slider("🔍 Depth", options=["Summary", "Quick", "Deep"], value="Quick")
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                 if st.button("⬅️ Back"):
                    st.session_state.current_step = 1
                    st.rerun()
            with col_b2:
                if st.button("🚀 Launch Agent Crew", type="primary", use_container_width=True):
                    st.session_state.current_step = 3
                    st.rerun()
        
        with col2:
            st.markdown("### 👨‍🔬 Your Crew")
            render_agent_status("Researcher", "Data Extraction", "waiting")
            render_agent_status("Analyst", "Pattern Recognition", "waiting")
            render_agent_status("Writer", "Report Generation", "waiting")

    # Step 3: Analyze (Real-time Progress)
    elif st.session_state.current_step == 3:
        st.markdown("### 🔄 Processing Document...")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
             # Progress Bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Animation
            st.markdown('<div style="display: flex; justify-content: center; font-size: 3rem;">⚡</div>', unsafe_allow_html=True)
            
            if not st.session_state.analysis_complete:
                try:
                    # 1. Init
                    status_text.markdown("**Phase 1/4: Initializing Agents...**")
                    progress_bar.progress(10)
                    time.sleep(1)
                    
                    from tools.pdf_reader import PDFReadTool
                    pdf_tool = PDFReadTool(
                         pdf_path=st.session_state.pdf_path,
                         analyze_images=st.session_state.config['include_images']
                    )
                    
                    # 2. Researcher
                    status_text.markdown("**Phase 2/4: 🔬 Researcher is reading the document...**")
                    progress_bar.progress(30)
                    st.session_state.agent_progress['researcher'] = 'active'
                    
                    llm = get_llm(provider=provider, use_smaller_model=st.session_state.config['use_smaller_model'])
                    crew = create_crew(llm, [pdf_tool], st.session_state.pdf_path)
                    
                    # 3. Execution
                    status_text.markdown("**Phase 3/4: 📊 Analyst is connecting trends...**")
                    progress_bar.progress(60)
                    st.session_state.agent_progress['researcher'] = 'completed'
                    st.session_state.agent_progress['analyst'] = 'active'
                    
                    result = crew.kickoff()
                    
                    # 4. Finalizing
                    status_text.markdown("**Phase 4/4: ✍️ Writer is polishing the report...**")
                    progress_bar.progress(90)
                    st.session_state.agent_progress['analyst'] = 'completed'
                    st.session_state.agent_progress['writer'] = 'active'
                    
                    st.session_state.analysis_result = result
                    st.session_state.analysis_complete = True
                    progress_bar.progress(100)
                    time.sleep(1)
                    st.session_state.current_step = 4
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Analysis Failed: {e}")
                    st.markdown("💡 *Try switching to Gemini/Groq or standard mode if rate limits persist.*")
                    if st.button("Try Again"):
                        st.session_state.current_step = 2
                        st.rerun()

        with col2:
             # Live Agent Status Update
            render_agent_status("Researcher", "Data Extraction", st.session_state.agent_progress['researcher'])
            render_agent_status("Analyst", "Trend Analysis", st.session_state.agent_progress['analyst'])
            render_agent_status("Writer", "Final Polish", st.session_state.agent_progress['writer'])

    # Step 4: Interact & Results
    elif st.session_state.current_step == 4:
        st.balloons()
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📄 Final Report", "💬 Chat with Doc", "🎧 Audio Summary"])
        
        with tab1:
            st.markdown("### 📝 Research Report")
            result_text = str(st.session_state.analysis_result)
            
            # Download actions
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("📥 Download Markdown", result_text, file_name="report.md")
            with c2:
                if st.button("🔄 Analyze New Doc"):
                    st.session_state.current_step = 1
                    st.session_state.analysis_complete = False
                    st.rerun()
            
            st.markdown("---")
            st.markdown(result_text)
            
        with tab2:
            # INTEGRATED CHAT
            chat_interface()
            
        with tab3:
            st.markdown("### 🔊 Listen to Summary")
            if st.button("▶️ Generate Audio"):
                with st.spinner("Synthesizing speech..."):
                    audio_fp = generate_audio_summary(str(st.session_state.analysis_result))
                    if audio_fp:
                        st.audio(audio_fp, format='audio/mp3')
                        st.success("Audio generated!")
                    else:
                        st.error("Could not generate audio.")

if __name__ == "__main__":
    main()
