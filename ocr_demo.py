"""
OCR Demo Application - Extract text from images
Streamlit interface for the OCR Tool
"""

import streamlit as st
import os
from PIL import Image
import tempfile
from pathlib import Path
import sys

# Add parent directory to path to import tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.ocr_tool import OCRTool

# Page configuration
st.set_page_config(
    page_title="OCR Text Extractor",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    /* Main styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    
    .stApp {
        background: transparent;
    }
    
    /* Card styling */
    .ocr-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    
    /* Header */
    .ocr-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .ocr-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .ocr-subtitle {
        color: #6B7280;
        font-size: 1.2rem;
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Result box */
    .result-box {
        background: #F9FAFB;
        border: 2px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
        font-family: 'Courier New', monospace;
        white-space: pre-wrap;
        max-height: 400px;
        overflow-y: auto;
    }
    
    /* Success message */
    .success-badge {
        background: #10B981;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        font-weight: 600;
        margin: 1rem 0;
    }
    
    /* Error message */
    .error-badge {
        background: #EF4444;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        font-weight: 600;
        margin: 1rem 0;
    }
    
    /* Image preview */
    .image-preview {
        border: 3px solid #667eea;
        border-radius: 12px;
        padding: 1rem;
        background: white;
        margin: 1rem 0;
    }
    
    /* Confidence bar */
    .confidence-container {
        margin: 1rem 0;
    }
    
    .confidence-bar {
        background: #E5E7EB;
        height: 30px;
        border-radius: 15px;
        overflow: hidden;
        position: relative;
    }
    
    .confidence-fill {
        background: linear-gradient(90deg, #10B981 0%, #059669 100%);
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 700;
        transition: width 0.5s ease;
    }
</style>
""", unsafe_allow_html=True)

# Initialize OCR Tool
@st.cache_resource
def get_ocr_tool():
    return OCRTool()

ocr_tool = get_ocr_tool()

# Initialize session state
if 'ocr_results' not in st.session_state:
    st.session_state.ocr_results = None

# Header
st.markdown("""
<div class="ocr-card">
    <div class="ocr-header">
        <div class="ocr-title">🔍 OCR Text Extractor</div>
        <div class="ocr-subtitle">Extract text from images using advanced Optical Character Recognition</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<div class="ocr-card">', unsafe_allow_html=True)
    st.markdown("### 📤 Upload Image")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif'],
        help="Supported formats: PNG, JPG, JPEG, TIFF, BMP, GIF"
    )
    
    # OCR Settings
    st.markdown("### ⚙️ OCR Settings")
    
    # Language selection
    available_langs = ocr_tool.get_available_languages()
    lang = st.selectbox(
        "Language",
        options=available_langs,
        index=available_langs.index('eng') if 'eng' in available_langs else 0,
        help="Select the language of the text in the image"
    )
    
    # PSM mode
    psm_options = {
        "Automatic (Default)": "--psm 3",
        "Single Column": "--psm 4",
        "Single Block": "--psm 6",
        "Sparse Text": "--psm 11",
        "Single Line": "--psm 7",
        "Single Word": "--psm 8"
    }
    
    psm_mode = st.selectbox(
        "Page Segmentation Mode",
        options=list(psm_options.keys()),
        help="Choose how Tesseract should interpret the image layout"
    )
    
    # Image preprocessing
    st.markdown("### 🎨 Image Preprocessing")
    
    use_preprocessing = st.checkbox("Enable preprocessing", value=False)
    
    if use_preprocessing:
        grayscale = st.checkbox("Convert to Grayscale", value=True)
        contrast = st.slider("Contrast", 0.5, 3.0, 1.5, 0.1)
        brightness = st.slider("Brightness", 0.5, 2.0, 1.0, 0.1)
    
    # Extract button
    if st.button("🚀 Extract Text", type="primary", use_container_width=True):
        if uploaded_file is not None:
            with st.spinner("🔍 Extracting text..."):
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                try:
                    # Preprocess if enabled
                    if use_preprocessing:
                        tmp_path = ocr_tool.preprocess_image(
                            tmp_path,
                            grayscale=grayscale,
                            contrast=contrast,
                            brightness=brightness
                        )
                    
                    # Extract text
                    result = ocr_tool.extract_text_from_image(
                        tmp_path,
                        lang=lang,
                        config=psm_options[psm_mode]
                    )
                    
                    # Store result in session state
                    st.session_state.ocr_results = result
                    st.session_state.uploaded_image = uploaded_file
                    
                    # Clean up
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("⚠️ Please upload an image first!")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="ocr-card">', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        st.markdown("### 🖼️ Image Preview")
        st.markdown('<div class="image-preview">', unsafe_allow_html=True)
        
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)
        
        # Image info
        st.markdown(f"""
        **Filename:** {uploaded_file.name}  
        **Size:** {uploaded_file.size / 1024:.2f} KB  
        **Dimensions:** {image.size[0]} x {image.size[1]} px
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("👆 Upload an image to get started")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Results section
if st.session_state.ocr_results is not None:
    result = st.session_state.ocr_results
    
    st.markdown('<div class="ocr-card">', unsafe_allow_html=True)
    
    if result['success']:
        st.markdown('<div class="success-badge">✅ Text Extracted Successfully</div>', unsafe_allow_html=True)
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{result['confidence']:.1f}%</div>
                <div class="stat-label">Confidence</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{result['word_count']}</div>
                <div class="stat-label">Words</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{result['char_count']}</div>
                <div class="stat-label">Characters</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{len(result['text'].split(chr(10)))}</div>
                <div class="stat-label">Lines</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Confidence bar
        st.markdown(f"""
        <div class="confidence-container">
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: {result['confidence']}%">
                    {result['confidence']:.1f}% Confidence
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Extracted text
        st.markdown("### 📝 Extracted Text")
        st.markdown(f'<div class="result-box">{result["text"]}</div>', unsafe_allow_html=True)
        
        # Download button
        st.download_button(
            label="💾 Download as TXT",
            data=result['text'],
            file_name=f"extracted_text_{Path(st.session_state.uploaded_image.name).stem}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
    else:
        st.markdown(f'<div class="error-badge">❌ {result["error"]}</div>', unsafe_allow_html=True)
        
        # Installation instructions if Tesseract not found
        if "Tesseract OCR not found" in result['error']:
            st.markdown("""
            ### 📦 Installation Instructions
            
            **Windows:**
            1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
            2. Install and add to PATH
            
            **Mac:**
            ```bash
            brew install tesseract
            ```
            
            **Linux:**
            ```bash
            sudo apt-get install tesseract-ocr
            ```
            """)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer with tips
st.markdown("""
<div class="ocr-card">
    <h3>💡 Tips for Better OCR Results</h3>
    <ul>
        <li>✨ Use high-resolution images (300 DPI or higher)</li>
        <li>📐 Ensure text is horizontal and not skewed</li>
        <li>🔆 Good lighting and contrast improve accuracy</li>
        <li>🎯 Avoid blurry or distorted images</li>
        <li>🔤 Select the correct language for best results</li>
        <li>🎨 Try preprocessing options if initial results are poor</li>
    </ul>
</div>
""", unsafe_allow_html=True)
