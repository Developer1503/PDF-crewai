"""
Integration Example: Adding OCR to app_v2.py

This shows how to integrate OCR functionality into your existing Streamlit app.
You can add this as a new page/tab in your app_v2.py
"""

import streamlit as st
from tools.ocr_tool import OCRTool
from PIL import Image
import tempfile
from pathlib import Path

def ocr_page():
    """OCR page for the main application"""
    
    st.markdown("## 🔍 OCR Text Extraction")
    st.markdown("Extract text from images using Optical Character Recognition")
    
    # Initialize OCR tool
    @st.cache_resource
    def get_ocr():
        return OCRTool()
    
    ocr = get_ocr()
    
    # Two columns layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Upload Image")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose an image",
            type=['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif'],
            key="ocr_uploader"
        )
        
        if uploaded_file:
            # Display image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)
            
            # Image info
            st.info(f"""
            **File**: {uploaded_file.name}  
            **Size**: {uploaded_file.size / 1024:.2f} KB  
            **Dimensions**: {image.size[0]} x {image.size[1]} px
            """)
    
    with col2:
        st.markdown("### OCR Settings")
        
        # Language selection
        langs = ocr.get_available_languages()
        lang = st.selectbox(
            "Language",
            options=langs,
            index=langs.index('eng') if 'eng' in langs else 0
        )
        
        # PSM mode
        psm_options = {
            "Automatic": "--psm 3",
            "Single Column": "--psm 4",
            "Single Block": "--psm 6",
            "Sparse Text": "--psm 11"
        }
        
        psm = st.selectbox("Page Mode", list(psm_options.keys()))
        
        # Preprocessing
        with st.expander("Image Preprocessing"):
            use_preprocess = st.checkbox("Enable", value=False)
            if use_preprocess:
                grayscale = st.checkbox("Grayscale", value=True)
                contrast = st.slider("Contrast", 0.5, 3.0, 1.5)
                brightness = st.slider("Brightness", 0.5, 2.0, 1.0)
    
    # Extract button
    if uploaded_file and st.button("🚀 Extract Text", type="primary", use_container_width=True):
        with st.spinner("Extracting text..."):
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            try:
                # Preprocess if enabled
                if use_preprocess:
                    tmp_path = ocr.preprocess_image(
                        tmp_path,
                        grayscale=grayscale,
                        contrast=contrast,
                        brightness=brightness
                    )
                
                # Extract text
                result = ocr.extract_text_from_image(
                    tmp_path,
                    lang=lang,
                    config=psm_options[psm]
                )
                
                # Display results
                if result['success']:
                    st.success("✅ Text extracted successfully!")
                    
                    # Metrics
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Confidence", f"{result['confidence']:.1f}%")
                    col2.metric("Words", result['word_count'])
                    col3.metric("Characters", result['char_count'])
                    
                    # Extracted text
                    st.markdown("### 📝 Extracted Text")
                    st.text_area(
                        "Text",
                        result['text'],
                        height=300,
                        label_visibility="collapsed"
                    )
                    
                    # Download button
                    st.download_button(
                        "💾 Download as TXT",
                        result['text'],
                        file_name=f"extracted_{Path(uploaded_file.name).stem}.txt",
                        mime="text/plain"
                    )
                else:
                    st.error(f"❌ Error: {result['error']}")
                    
                    if "Tesseract OCR not found" in result['error']:
                        st.warning("""
                        **Tesseract OCR not installed**
                        
                        Please install Tesseract:
                        - Windows: https://github.com/UB-Mannheim/tesseract/wiki
                        - Mac: `brew install tesseract`
                        - Linux: `sudo apt-get install tesseract-ocr`
                        """)
            
            except Exception as e:
                st.error(f"Error: {str(e)}")


# Example: How to add to app_v2.py
def add_to_existing_app():
    """
    To integrate OCR into app_v2.py:
    
    1. Add OCR to navigation (around line 565):
    
    pages = [
        ("📄", "Current Paper"),
        ("🕒", "Recent Files"),
        ("👥", "Collaborations"),
        ("🔍", "OCR Extract")  # Add this
    ]
    
    2. Add OCR page handler (around line 632):
    
    if st.session_state.current_page == 'OCR Extract':
        from ocr_integration import ocr_page
        ocr_page()
    elif not st.session_state.pdf_uploaded:
        # existing code...
    
    3. Import at top of app_v2.py:
    
    from tools.ocr_tool import OCRTool
    """
    pass


if __name__ == "__main__":
    # Run standalone
    st.set_page_config(
        page_title="OCR Integration",
        page_icon="🔍",
        layout="wide"
    )
    
    ocr_page()
