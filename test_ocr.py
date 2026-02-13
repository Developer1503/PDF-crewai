"""
Simple OCR Test Script
Demonstrates basic OCR functionality
"""

import os
from tools.ocr_tool import OCRTool, quick_ocr
from PIL import Image, ImageDraw, ImageFont

def create_sample_image(text="Hello World!\nThis is OCR Test", filename="sample_ocr_test.png"):
    """Create a sample image with text for testing OCR"""
    
    # Create a white image
    img = Image.new('RGB', (800, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    # Draw text
    draw.text((50, 150), text, fill='black', font=font)
    
    # Save image
    img.save(filename)
    print(f"✅ Created sample image: {filename}")
    return filename


def test_basic_ocr():
    """Test basic OCR functionality"""
    print("\n" + "="*60)
    print("🔍 OCR TOOL TEST")
    print("="*60)
    
    # Initialize OCR tool
    ocr = OCRTool()
    
    # Check available languages
    print("\n📚 Available Languages:")
    langs = ocr.get_available_languages()
    print(f"   {', '.join(langs[:10])}")  # Show first 10
    
    # Create a sample image
    print("\n📝 Creating sample image...")
    sample_text = """Hello World!
This is a test of OCR.
Optical Character Recognition
works with Tesseract."""
    
    image_path = create_sample_image(sample_text)
    
    # Test OCR extraction
    print("\n🔍 Extracting text from image...")
    result = ocr.extract_text_from_image(image_path)
    
    # Display results
    print("\n" + "-"*60)
    print("📊 RESULTS")
    print("-"*60)
    
    if result['success']:
        print(f"✅ Success: {result['success']}")
        print(f"📈 Confidence: {result['confidence']:.2f}%")
        print(f"📝 Word Count: {result['word_count']}")
        print(f"🔤 Character Count: {result['char_count']}")
        print("\n📄 Extracted Text:")
        print("-"*60)
        print(result['text'])
        print("-"*60)
    else:
        print(f"❌ Error: {result['error']}")
        
        if "Tesseract OCR not found" in result['error']:
            print("\n" + "="*60)
            print("📦 INSTALLATION REQUIRED")
            print("="*60)
            print("\nTesseract OCR is not installed. Please install it:")
            print("\n🪟 Windows:")
            print("   1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
            print("   2. Install and add to PATH")
            print("\n🍎 Mac:")
            print("   brew install tesseract")
            print("\n🐧 Linux:")
            print("   sudo apt-get install tesseract-ocr")
            print("\n" + "="*60)
    
    # Test quick_ocr function
    print("\n🚀 Testing quick_ocr function...")
    quick_text = quick_ocr(image_path)
    if quick_text:
        print(f"✅ Quick OCR extracted {len(quick_text)} characters")
    
    # Clean up
    try:
        os.remove(image_path)
        print(f"\n🧹 Cleaned up test image")
    except:
        pass
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60 + "\n")


def test_with_user_image(image_path):
    """Test OCR with a user-provided image"""
    
    if not os.path.exists(image_path):
        print(f"❌ Error: Image not found at {image_path}")
        return
    
    print(f"\n🔍 Processing: {image_path}")
    
    ocr = OCRTool()
    result = ocr.extract_text_from_image(image_path)
    
    if result['success']:
        print(f"\n✅ Success!")
        print(f"📈 Confidence: {result['confidence']:.2f}%")
        print(f"📝 Words: {result['word_count']}")
        print(f"\n📄 Extracted Text:")
        print("-"*60)
        print(result['text'])
        print("-"*60)
    else:
        print(f"\n❌ Error: {result['error']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # User provided an image path
        test_with_user_image(sys.argv[1])
    else:
        # Run basic test
        test_basic_ocr()
    
    print("\n💡 Usage:")
    print("   Basic test:  python test_ocr.py")
    print("   Your image:  python test_ocr.py path/to/your/image.png")
