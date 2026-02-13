"""
OCR + Data Analysis Demo
Extract text from images, analyze numerical data, and create visualizations
"""

import streamlit as st
from PIL import Image
import tempfile
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.ocr_tool import OCRTool
from utils.data_analyzer import DataAnalyzer
from utils.data_visualizer import DataVisualizer

# Page configuration
st.set_page_config(
    page_title="OCR + Data Analysis",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .analysis-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .success-box {
        background: #D1FAE5;
        border-left: 4px solid #10B981;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .info-box {
        background: #DBEAFE;
        border-left: 4px solid #3B82F6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize tools
@st.cache_resource
def get_tools():
    return {
        'ocr': OCRTool(),
        'analyzer': DataAnalyzer(),
        'visualizer': DataVisualizer()
    }

tools = get_tools()

# Session state
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'show_analysis' not in st.session_state:
    st.session_state.show_analysis = False

# Header
st.markdown("""
<div class="analysis-card">
    <h1 style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        📊 OCR + Data Analysis
    </h1>
    <p style="text-align: center; color: #6B7280; font-size: 1.1rem;">
        Extract text from images and automatically analyze numerical data
    </p>
</div>
""", unsafe_allow_html=True)

# Main layout
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    st.markdown("### 📤 Upload Image")
    
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif'],
        help="Upload an image containing text and numerical data"
    )
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        
        st.info(f"""
        **File:** {uploaded_file.name}  
        **Size:** {uploaded_file.size / 1024:.2f} KB  
        **Dimensions:** {image.size[0]} x {image.size[1]} px
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # OCR Settings
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    st.markdown("### ⚙️ Settings")
    
    # Language
    langs = tools['ocr'].get_available_languages()
    lang = st.selectbox(
        "Language",
        options=langs,
        index=langs.index('eng') if 'eng' in langs else 0
    )
    
    # Enable data analysis
    enable_analysis = st.checkbox(
        "📊 Enable Data Analysis & Visualization",
        value=True,
        help="Automatically analyze numerical data and create visualizations"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    
    if uploaded_file:
        if st.button("🚀 Extract & Analyze", type="primary", use_container_width=True):
            with st.spinner("🔍 Processing..."):
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                # Extract text
                ocr_result = tools['ocr'].extract_text_from_image(tmp_path, lang=lang)
                
                if ocr_result['success']:
                    st.session_state.extracted_text = ocr_result['text']
                    st.session_state.show_analysis = enable_analysis
                    
                    # Analyze data if enabled
                    if enable_analysis:
                        st.session_state.analysis_results = tools['analyzer'].analyze_text(
                            ocr_result['text']
                        )
                    
                    st.success("✅ Processing complete!")
                else:
                    st.error(f"❌ Error: {ocr_result['error']}")
                
                # Cleanup
                try:
                    os.unlink(tmp_path)
                except:
                    pass
    else:
        st.info("👆 Upload an image to get started")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Results section
if st.session_state.extracted_text:
    # OCR Results
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Extracted Text")
    
    st.text_area(
        "Text",
        st.session_state.extracted_text,
        height=200,
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "💾 Download Text",
            st.session_state.extracted_text,
            file_name="extracted_text.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Data Analysis Results
    if st.session_state.show_analysis and st.session_state.analysis_results:
        analysis = st.session_state.analysis_results
        
        if analysis['has_numerical_data']:
            st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
            st.markdown("### 📊 Data Analysis")
            
            # Summary
            summary = tools['analyzer'].create_summary(analysis)
            st.markdown(f'<div class="success-box">{summary}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Metrics
            if analysis['numbers']['count'] > 0:
                st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
                st.markdown("### 📈 Key Metrics")
                
                stats = analysis['numbers']['statistics']
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{stats['count']}</div>
                        <div class="metric-label">Numbers Found</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{stats['mean']:.2f}</div>
                        <div class="metric-label">Mean</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{stats['median']:.2f}</div>
                        <div class="metric-label">Median</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{stats['std']:.2f}</div>
                        <div class="metric-label">Std Dev</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Visualizations
            st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
            st.markdown("### 📊 Visualizations")
            
            # Create dashboard
            fig = tools['visualizer'].create_dashboard(analysis)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Detailed Statistics
            if analysis['numbers']['count'] > 0:
                with st.expander("📋 Detailed Statistics"):
                    stats = analysis['numbers']['statistics']
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Count", stats['count'])
                        st.metric("Sum", f"{stats['sum']:.2f}")
                        st.metric("Mean", f"{stats['mean']:.2f}")
                        st.metric("Median", f"{stats['median']:.2f}")
                        st.metric("Std Dev", f"{stats['std']:.2f}")
                    
                    with col2:
                        st.metric("Min", f"{stats['min']:.2f}")
                        st.metric("Max", f"{stats['max']:.2f}")
                        st.metric("Range", f"{stats['range']:.2f}")
                        st.metric("Q1", f"{stats['q1']:.2f}")
                        st.metric("Q3", f"{stats['q3']:.2f}")
            
            # Export options
            st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
            st.markdown("### 💾 Export Data")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Export as CSV", use_container_width=True):
                    csv_file = tools['analyzer'].export_to_csv(analysis, "data_export.csv")
                    if csv_file:
                        with open(csv_file, 'r') as f:
                            st.download_button(
                                "Download CSV",
                                f.read(),
                                file_name="data_export.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
            
            with col2:
                if st.button("Export as JSON", use_container_width=True):
                    json_file = tools['analyzer'].export_to_json(analysis, "data_export.json")
                    if json_file:
                        with open(json_file, 'r') as f:
                            st.download_button(
                                "Download JSON",
                                f.read(),
                                file_name="data_export.json",
                                mime="application/json",
                                use_container_width=True
                            )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
            st.info("ℹ️ No numerical data detected in the extracted text.")
            st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="analysis-card">
    <h3>💡 Tips for Best Results</h3>
    <ul>
        <li>📸 Use clear, high-resolution images</li>
        <li>📊 Ensure numerical data is clearly visible</li>
        <li>🔢 Works great with receipts, invoices, reports, and tables</li>
        <li>🌍 Select the correct language for accurate extraction</li>
        <li>📈 Enable data analysis to automatically detect and visualize numbers</li>
    </ul>
</div>
""", unsafe_allow_html=True)
