"""
Optional Data Analysis Module for app_v2.py
Add OCR + Data Analysis as an optional feature to your existing app
"""

import streamlit as st
from PIL import Image
import tempfile
from pathlib import Path
import os

from tools.ocr_tool import OCRTool
from utils.data_analyzer import DataAnalyzer
from utils.data_visualizer import DataVisualizer


def render_data_analysis_page():
    """
    Render the OCR + Data Analysis page
    This can be added as an optional page in app_v2.py
    """
    
    # Initialize tools
    @st.cache_resource
    def get_analysis_tools():
        return {
            'ocr': OCRTool(),
            'analyzer': DataAnalyzer(),
            'visualizer': DataVisualizer()
        }
    
    tools = get_analysis_tools()
    
    # Session state for this page
    if 'da_extracted_text' not in st.session_state:
        st.session_state.da_extracted_text = None
    if 'da_analysis_results' not in st.session_state:
        st.session_state.da_analysis_results = None
    
    # Header
    st.markdown("""
    <div class="chat-header">
        <div class="chat-icon">📊</div>
        <div class="chat-title">Data Analysis & Visualization</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="chat-container">
        <p style="color: #6B7280;">
            Extract text from images and automatically analyze numerical data with visualizations.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📤 Upload Image")
        
        uploaded_file = st.file_uploader(
            "Choose an image with text/data",
            type=['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif'],
            key="data_analysis_uploader"
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)
            
            st.info(f"""
            **File:** {uploaded_file.name}  
            **Size:** {uploaded_file.size / 1024:.2f} KB
            """)
        
        # Settings
        st.markdown("### ⚙️ Settings")
        
        langs = tools['ocr'].get_available_languages()
        lang = st.selectbox(
            "Language",
            options=langs,
            index=langs.index('eng') if 'eng' in langs else 0,
            key="da_lang"
        )
        
        enable_viz = st.checkbox(
            "Enable Visualizations",
            value=True,
            help="Create charts and graphs from numerical data"
        )
    
    with col2:
        if uploaded_file:
            if st.button("🚀 Extract & Analyze", type="primary", use_container_width=True):
                with st.spinner("Processing..."):
                    # Save to temp
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name
                    
                    # OCR
                    result = tools['ocr'].extract_text_from_image(tmp_path, lang=lang)
                    
                    if result['success']:
                        st.session_state.da_extracted_text = result['text']
                        
                        # Analyze
                        st.session_state.da_analysis_results = tools['analyzer'].analyze_text(
                            result['text']
                        )
                        
                        st.success(f"✅ Extracted with {result['confidence']:.1f}% confidence")
                    else:
                        st.error(f"❌ {result['error']}")
                    
                    # Cleanup
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
        else:
            st.info("👆 Upload an image to start")
    
    # Results
    if st.session_state.da_extracted_text:
        st.markdown("---")
        
        # Extracted text
        with st.expander("📝 Extracted Text", expanded=True):
            st.text_area(
                "Text",
                st.session_state.da_extracted_text,
                height=150,
                label_visibility="collapsed"
            )
            
            st.download_button(
                "💾 Download Text",
                st.session_state.da_extracted_text,
                file_name="extracted_text.txt",
                use_container_width=True
            )
        
        # Analysis
        if st.session_state.da_analysis_results:
            analysis = st.session_state.da_analysis_results
            
            if analysis['has_numerical_data']:
                st.markdown("### 📊 Data Analysis")
                
                # Summary
                summary = tools['analyzer'].create_summary(analysis)
                st.info(summary)
                
                # Metrics
                if analysis['numbers']['count'] > 0:
                    stats = analysis['numbers']['statistics']
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Count", stats['count'])
                    col2.metric("Mean", f"{stats['mean']:.2f}")
                    col3.metric("Median", f"{stats['median']:.2f}")
                    col4.metric("Std Dev", f"{stats['std']:.2f}")
                
                # Visualizations
                if enable_viz:
                    st.markdown("### 📈 Visualizations")
                    
                    fig = tools['visualizer'].create_dashboard(analysis)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Detailed stats
                with st.expander("📋 Detailed Statistics"):
                    if analysis['numbers']['count'] > 0:
                        stats = analysis['numbers']['statistics']
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Basic Statistics**")
                            st.write(f"Count: {stats['count']}")
                            st.write(f"Sum: {stats['sum']:.2f}")
                            st.write(f"Mean: {stats['mean']:.2f}")
                            st.write(f"Median: {stats['median']:.2f}")
                            st.write(f"Std Dev: {stats['std']:.2f}")
                        
                        with col2:
                            st.write("**Range & Quartiles**")
                            st.write(f"Min: {stats['min']:.2f}")
                            st.write(f"Max: {stats['max']:.2f}")
                            st.write(f"Range: {stats['range']:.2f}")
                            st.write(f"Q1: {stats['q1']:.2f}")
                            st.write(f"Q3: {stats['q3']:.2f}")
            else:
                st.info("ℹ️ No numerical data detected")


# Integration instructions for app_v2.py
INTEGRATION_GUIDE = """
# How to Add Data Analysis to app_v2.py

## Step 1: Add to Navigation (around line 565)

```python
pages = [
    ("📄", "Current Paper"),
    ("🕒", "Recent Files"),
    ("👥", "Collaborations"),
    ("📊", "Data Analysis")  # Add this line
]
```

## Step 2: Add Import (at top of file)

```python
from components.data_analysis import render_data_analysis_page
```

## Step 3: Add Page Handler (around line 632)

```python
if st.session_state.current_page == 'Data Analysis':
    render_data_analysis_page()
elif not st.session_state.pdf_uploaded:
    # existing code...
```

## Step 4: Install Dependencies

```bash
pip install plotly pandas numpy pytesseract opencv-python
```

## Step 5: Install Tesseract OCR

- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- Mac: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`

That's it! The Data Analysis page will now be available as an optional feature.
"""


if __name__ == "__main__":
    # Standalone mode
    st.set_page_config(
        page_title="Data Analysis",
        page_icon="📊",
        layout="wide"
    )
    
    render_data_analysis_page()
