# 🔍 OCR Text Extractor

Extract text from images using advanced Optical Character Recognition (OCR) powered by Tesseract.

## 📋 Features

- ✨ **Multiple Image Formats**: PNG, JPG, JPEG, TIFF, BMP, GIF
- 🌍 **Multi-Language Support**: 100+ languages supported by Tesseract
- 🎨 **Image Preprocessing**: Enhance images for better OCR accuracy
- 📊 **Confidence Scoring**: Get accuracy metrics for extracted text
- 🚀 **Batch Processing**: Process multiple images at once
- 💾 **Export Results**: Download extracted text as TXT files
- 🎯 **Multiple PSM Modes**: Different page segmentation modes for various layouts

## 🚀 Quick Start

### 1. Install Tesseract OCR

#### Windows
1. Download installer from [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer
3. Add Tesseract to your system PATH
   - Default location: `C:\Program Files\Tesseract-OCR`

#### Mac
```bash
brew install tesseract
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

The OCR dependencies include:
- `pytesseract>=0.3.10` - Python wrapper for Tesseract
- `opencv-python>=4.8.0` - Image processing
- `Pillow` - Image manipulation (already in requirements)

### 3. Verify Installation

Run the test script to verify everything is working:

```bash
python test_ocr.py
```

This will:
- Check if Tesseract is installed
- Show available languages
- Create a sample image
- Extract text from it
- Display results with confidence scores

## 📖 Usage

### Option 1: Streamlit Web Interface (Recommended)

Launch the beautiful web interface:

```bash
streamlit run ocr_demo.py
```

Features:
- 📤 Drag & drop image upload
- ⚙️ Adjustable OCR settings
- 🎨 Image preprocessing controls
- 📊 Real-time statistics
- 💾 Download extracted text

### Option 2: Python API

#### Basic Usage

```python
from tools.ocr_tool import OCRTool

# Initialize OCR tool
ocr = OCRTool()

# Extract text from image
result = ocr.extract_text_from_image('path/to/image.png')

if result['success']:
    print(f"Text: {result['text']}")
    print(f"Confidence: {result['confidence']}%")
    print(f"Words: {result['word_count']}")
else:
    print(f"Error: {result['error']}")
```

#### Quick OCR (Simple)

```python
from tools.ocr_tool import quick_ocr

# Get just the text
text = quick_ocr('image.png')
print(text)
```

#### Advanced Usage

```python
from tools.ocr_tool import OCRTool

ocr = OCRTool()

# Multi-language OCR
result = ocr.extract_text_from_image(
    'image.png',
    lang='eng+fra',  # English + French
    config='--psm 6'  # Single uniform block of text
)

# Preprocess image for better results
preprocessed_path = ocr.preprocess_image(
    'image.png',
    grayscale=True,
    contrast=1.5,
    brightness=1.2
)

result = ocr.extract_text_from_image(preprocessed_path)
```

#### Batch Processing

```python
from tools.ocr_tool import OCRTool

ocr = OCRTool()

# Process multiple images
image_paths = ['img1.png', 'img2.jpg', 'img3.png']
results = ocr.batch_extract(image_paths)

for result in results:
    print(f"File: {result['file_name']}")
    print(f"Text: {result['text'][:100]}...")  # First 100 chars
    print(f"Confidence: {result['confidence']}%")
    print("-" * 60)
```

#### Extract from Uploaded Files (Streamlit/Flask)

```python
from tools.ocr_tool import OCRTool

ocr = OCRTool()

# From file bytes (e.g., Streamlit file_uploader)
uploaded_file = st.file_uploader("Upload Image")
if uploaded_file:
    result = ocr.extract_text_from_bytes(uploaded_file.getvalue())
    st.write(result['text'])
```

#### Extract from PIL Image

```python
from PIL import Image
from tools.ocr_tool import OCRTool

ocr = OCRTool()

# From PIL Image object
img = Image.open('photo.jpg')
result = ocr.extract_text_from_pil_image(img)
print(result['text'])
```

## ⚙️ Configuration Options

### Language Codes

Common language codes:
- `eng` - English
- `fra` - French
- `deu` - German
- `spa` - Spanish
- `chi_sim` - Simplified Chinese
- `jpn` - Japanese
- `ara` - Arabic
- `hin` - Hindi

Combine multiple: `eng+fra+deu`

Check available languages:
```python
ocr = OCRTool()
print(ocr.get_available_languages())
```

### Page Segmentation Modes (PSM)

| Mode | Description | Best For |
|------|-------------|----------|
| `--psm 0` | Orientation and script detection only | Detecting text orientation |
| `--psm 3` | Fully automatic (default) | General documents |
| `--psm 4` | Single column of text | Articles, books |
| `--psm 6` | Single uniform block | Paragraphs |
| `--psm 7` | Single text line | Single lines |
| `--psm 8` | Single word | Individual words |
| `--psm 11` | Sparse text | Finding scattered text |

### Image Preprocessing

Improve OCR accuracy with preprocessing:

```python
ocr = OCRTool()

preprocessed = ocr.preprocess_image(
    'input.png',
    grayscale=True,      # Convert to grayscale
    contrast=1.5,        # Increase contrast (1.0 = no change)
    brightness=1.2       # Increase brightness (1.0 = no change)
)

result = ocr.extract_text_from_image(preprocessed)
```

## 📊 Result Structure

The OCR tool returns a dictionary with:

```python
{
    'text': str,           # Extracted text
    'confidence': float,   # Average confidence score (0-100)
    'success': bool,       # Whether extraction succeeded
    'error': str,          # Error message if failed
    'word_count': int,     # Number of words extracted
    'char_count': int      # Number of characters extracted
}
```

## 💡 Tips for Better Results

1. **Image Quality**
   - Use high-resolution images (300 DPI or higher)
   - Ensure good lighting and contrast
   - Avoid blurry or distorted images

2. **Text Orientation**
   - Keep text horizontal
   - Avoid skewed or rotated text
   - Use straight scans

3. **Preprocessing**
   - Convert to grayscale for better contrast
   - Increase contrast for faded text
   - Adjust brightness for dark images

4. **Language Selection**
   - Always specify the correct language
   - Use multiple languages if text is mixed

5. **PSM Mode**
   - Choose appropriate mode for your layout
   - Use `--psm 6` for single paragraphs
   - Use `--psm 11` for scattered text

## 🔧 Troubleshooting

### "Tesseract OCR not found"

**Solution**: Install Tesseract and ensure it's in your PATH

**Windows**: 
```powershell
# Add to PATH (replace with your installation path)
$env:Path += ";C:\Program Files\Tesseract-OCR"
```

**Or specify path in code**:
```python
ocr = OCRTool(tesseract_path=r'C:\Program Files\Tesseract-OCR\tesseract.exe')
```

### Low Confidence Scores

**Solutions**:
1. Preprocess the image
2. Try different PSM modes
3. Ensure correct language is selected
4. Improve image quality

### No Text Extracted

**Solutions**:
1. Check if image contains readable text
2. Try `--psm 11` for sparse text
3. Preprocess with higher contrast
4. Verify image format is supported

## 📚 Examples

### Example 1: Receipt OCR

```python
from tools.ocr_tool import OCRTool

ocr = OCRTool()

# Preprocess receipt image
preprocessed = ocr.preprocess_image(
    'receipt.jpg',
    grayscale=True,
    contrast=2.0,
    brightness=1.3
)

# Extract text with single column mode
result = ocr.extract_text_from_image(
    preprocessed,
    config='--psm 4'
)

print(result['text'])
```

### Example 2: Multi-Language Document

```python
from tools.ocr_tool import OCRTool

ocr = OCRTool()

# Extract English and French text
result = ocr.extract_text_from_image(
    'bilingual_doc.png',
    lang='eng+fra'
)

print(f"Confidence: {result['confidence']}%")
print(result['text'])
```

### Example 3: Batch Processing

```python
from tools.ocr_tool import OCRTool
import glob

ocr = OCRTool()

# Get all images in folder
images = glob.glob('images/*.png')

# Process all images
results = ocr.batch_extract(images)

# Save results
for result in results:
    if result['success']:
        filename = result['file_name'].replace('.png', '.txt')
        with open(f'output/{filename}', 'w') as f:
            f.write(result['text'])
```

## 🎯 Integration Examples

### Streamlit App

```python
import streamlit as st
from tools.ocr_tool import OCRTool

st.title("OCR App")

uploaded = st.file_uploader("Upload Image", type=['png', 'jpg'])

if uploaded:
    ocr = OCRTool()
    result = ocr.extract_text_from_bytes(uploaded.getvalue())
    
    if result['success']:
        st.success(f"Confidence: {result['confidence']}%")
        st.text_area("Extracted Text", result['text'], height=300)
```

### Flask API

```python
from flask import Flask, request, jsonify
from tools.ocr_tool import OCRTool

app = Flask(__name__)
ocr = OCRTool()

@app.route('/ocr', methods=['POST'])
def extract_text():
    file = request.files['image']
    result = ocr.extract_text_from_bytes(file.read())
    return jsonify(result)

if __name__ == '__main__':
    app.run()
```

## 📄 License

This OCR tool uses Tesseract OCR, which is licensed under the Apache License 2.0.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review Tesseract documentation
3. Open an issue on GitHub

---

**Made with ❤️ using Tesseract OCR**
