"""
Quick OCR Example - Create and process a sample image
"""

from PIL import Image, ImageDraw, ImageFont
from tools.ocr_tool import OCRTool
import os

def main():
    print("\n" + "="*70)
    print("🔍 OCR QUICK EXAMPLE")
    print("="*70)
    
    # Create a sample image with text
    print("\n📝 Step 1: Creating sample image...")
    
    # Create image
    img = Image.new('RGB', (800, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # Sample text
    text = """OCR Text Extraction Demo
    
This is a test of Optical Character Recognition.
The tool can extract text from images accurately!"""
    
    # Draw text (using default font since custom fonts may not be available)
    try:
        # Try to use a nicer font
        font = ImageFont.truetype("arial.ttf", 32)
    except:
        # Fallback to default
        font = ImageFont.load_default()
    
    draw.text((50, 50), text, fill='black', font=font)
    
    # Save image
    image_path = 'sample_ocr_image.png'
    img.save(image_path)
    print(f"   ✅ Created: {image_path}")
    
    # Initialize OCR
    print("\n🔍 Step 2: Initializing OCR Tool...")
    ocr = OCRTool()
    
    # Check available languages
    langs = ocr.get_available_languages()
    print(f"   📚 Available languages: {len(langs)}")
    print(f"   🌍 Examples: {', '.join(langs[:5])}")
    
    # Extract text
    print("\n📖 Step 3: Extracting text from image...")
    result = ocr.extract_text_from_image(image_path)
    
    # Display results
    print("\n" + "="*70)
    print("📊 RESULTS")
    print("="*70)
    
    if result['success']:
        print(f"\n✅ Status: SUCCESS")
        print(f"📈 Confidence: {result['confidence']:.2f}%")
        print(f"📝 Words: {result['word_count']}")
        print(f"🔤 Characters: {result['char_count']}")
        print(f"\n📄 Extracted Text:")
        print("-"*70)
        print(result['text'])
        print("-"*70)
        
        # Save extracted text
        txt_path = 'extracted_text.txt'
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(result['text'])
        print(f"\n💾 Saved to: {txt_path}")
        
    else:
        print(f"\n❌ Status: FAILED")
        print(f"⚠️ Error: {result['error']}")
        
        if "Tesseract OCR not found" in result['error']:
            print("\n" + "="*70)
            print("📦 TESSERACT INSTALLATION REQUIRED")
            print("="*70)
            print("\nPlease install Tesseract OCR:")
            print("\n🪟 Windows:")
            print("   Download: https://github.com/UB-Mannheim/tesseract/wiki")
            print("\n🍎 Mac:")
            print("   brew install tesseract")
            print("\n🐧 Linux:")
            print("   sudo apt-get install tesseract-ocr")
    
    print("\n" + "="*70)
    print("✨ NEXT STEPS")
    print("="*70)
    print("\n1. Run the beautiful web interface:")
    print("   streamlit run ocr_demo.py")
    print("\n2. Test with your own image:")
    print("   python test_ocr.py path/to/your/image.png")
    print("\n3. Read the full documentation:")
    print("   See OCR_README.md")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
