"""
OCR Tool - Extract text from images using Tesseract OCR
Supports multiple image formats: PNG, JPG, JPEG, TIFF, BMP, GIF
"""

import os
from typing import Optional, Dict, Any, List
from PIL import Image
import pytesseract
from pathlib import Path
import tempfile


class OCRTool:
    """
    Tool for extracting text from images using Optical Character Recognition (OCR)
    """
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize OCR Tool
        
        Args:
            tesseract_path: Path to tesseract executable (optional)
                           If not provided, assumes tesseract is in PATH
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        self.supported_formats = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif']
    
    def extract_text_from_image(
        self, 
        image_path: str,
        lang: str = 'eng',
        config: str = '--psm 3'
    ) -> Dict[str, Any]:
        """
        Extract text from a single image file
        
        Args:
            image_path: Path to the image file
            lang: Language code for OCR (default: 'eng' for English)
                  Multiple languages: 'eng+fra' for English and French
            config: Tesseract configuration string
                   --psm modes:
                   0 = Orientation and script detection (OSD) only
                   1 = Automatic page segmentation with OSD
                   3 = Fully automatic page segmentation (default)
                   4 = Assume a single column of text
                   6 = Assume a single uniform block of text
                   11 = Sparse text. Find as much text as possible
        
        Returns:
            Dictionary containing:
                - text: Extracted text
                - confidence: OCR confidence score
                - success: Boolean indicating success
                - error: Error message if failed
        """
        try:
            # Validate file exists
            if not os.path.exists(image_path):
                return {
                    'text': '',
                    'confidence': 0,
                    'success': False,
                    'error': f'File not found: {image_path}'
                }
            
            # Validate file format
            file_ext = Path(image_path).suffix.lower()
            if file_ext not in self.supported_formats:
                return {
                    'text': '',
                    'confidence': 0,
                    'success': False,
                    'error': f'Unsupported format: {file_ext}. Supported: {self.supported_formats}'
                }
            
            # Open and process image
            image = Image.open(image_path)
            
            # Extract text
            text = pytesseract.image_to_string(image, lang=lang, config=config)
            
            # Get detailed data including confidence
            data = pytesseract.image_to_data(image, lang=lang, config=config, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence (excluding -1 values which indicate no text)
            confidences = [int(conf) for conf in data['conf'] if int(conf) != -1]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'text': text.strip(),
                'confidence': round(avg_confidence, 2),
                'success': True,
                'error': None,
                'word_count': len(text.split()),
                'char_count': len(text)
            }
            
        except pytesseract.TesseractNotFoundError:
            return {
                'text': '',
                'confidence': 0,
                'success': False,
                'error': 'Tesseract OCR not found. Please install Tesseract OCR.'
            }
        except Exception as e:
            return {
                'text': '',
                'confidence': 0,
                'success': False,
                'error': f'OCR Error: {str(e)}'
            }
    
    def extract_text_from_bytes(
        self,
        image_bytes: bytes,
        lang: str = 'eng',
        config: str = '--psm 3'
    ) -> Dict[str, Any]:
        """
        Extract text from image bytes (useful for uploaded files)
        
        Args:
            image_bytes: Image data as bytes
            lang: Language code for OCR
            config: Tesseract configuration string
        
        Returns:
            Dictionary with extraction results
        """
        try:
            # Save bytes to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                tmp.write(image_bytes)
                tmp_path = tmp.name
            
            # Extract text from temporary file
            result = self.extract_text_from_image(tmp_path, lang, config)
            
            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            return result
            
        except Exception as e:
            return {
                'text': '',
                'confidence': 0,
                'success': False,
                'error': f'Error processing image bytes: {str(e)}'
            }
    
    def extract_text_from_pil_image(
        self,
        pil_image: Image.Image,
        lang: str = 'eng',
        config: str = '--psm 3'
    ) -> Dict[str, Any]:
        """
        Extract text from PIL Image object
        
        Args:
            pil_image: PIL Image object
            lang: Language code for OCR
            config: Tesseract configuration string
        
        Returns:
            Dictionary with extraction results
        """
        try:
            # Extract text
            text = pytesseract.image_to_string(pil_image, lang=lang, config=config)
            
            # Get detailed data
            data = pytesseract.image_to_data(pil_image, lang=lang, config=config, output_type=pytesseract.Output.DICT)
            
            # Calculate confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) != -1]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'text': text.strip(),
                'confidence': round(avg_confidence, 2),
                'success': True,
                'error': None,
                'word_count': len(text.split()),
                'char_count': len(text)
            }
            
        except Exception as e:
            return {
                'text': '',
                'confidence': 0,
                'success': False,
                'error': f'OCR Error: {str(e)}'
            }
    
    def batch_extract(
        self,
        image_paths: List[str],
        lang: str = 'eng',
        config: str = '--psm 3'
    ) -> List[Dict[str, Any]]:
        """
        Extract text from multiple images
        
        Args:
            image_paths: List of image file paths
            lang: Language code for OCR
            config: Tesseract configuration string
        
        Returns:
            List of dictionaries with extraction results for each image
        """
        results = []
        for image_path in image_paths:
            result = self.extract_text_from_image(image_path, lang, config)
            result['file_path'] = image_path
            result['file_name'] = os.path.basename(image_path)
            results.append(result)
        
        return results
    
    def get_available_languages(self) -> List[str]:
        """
        Get list of available Tesseract languages
        
        Returns:
            List of language codes
        """
        try:
            langs = pytesseract.get_languages()
            return langs
        except:
            return ['eng']  # Default to English if can't get languages
    
    def preprocess_image(
        self,
        image_path: str,
        output_path: Optional[str] = None,
        grayscale: bool = True,
        contrast: float = 1.5,
        brightness: float = 1.0
    ) -> str:
        """
        Preprocess image to improve OCR accuracy
        
        Args:
            image_path: Path to input image
            output_path: Path to save preprocessed image (optional)
            grayscale: Convert to grayscale
            contrast: Contrast enhancement factor
            brightness: Brightness enhancement factor
        
        Returns:
            Path to preprocessed image
        """
        from PIL import ImageEnhance
        
        try:
            image = Image.open(image_path)
            
            # Convert to grayscale
            if grayscale:
                image = image.convert('L')
            
            # Enhance contrast
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(contrast)
            
            # Enhance brightness
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(brightness)
            
            # Save preprocessed image
            if output_path is None:
                output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
            
            image.save(output_path)
            return output_path
            
        except Exception as e:
            raise Exception(f'Error preprocessing image: {str(e)}')


# Convenience function for quick OCR
def quick_ocr(image_path: str, lang: str = 'eng') -> str:
    """
    Quick OCR extraction - returns just the text
    
    Args:
        image_path: Path to image file
        lang: Language code
    
    Returns:
        Extracted text as string
    """
    ocr = OCRTool()
    result = ocr.extract_text_from_image(image_path, lang)
    return result['text'] if result['success'] else ''


if __name__ == "__main__":
    # Example usage
    ocr = OCRTool()
    
    # Test if Tesseract is available
    print("Testing OCR Tool...")
    print(f"Available languages: {ocr.get_available_languages()}")
    
    # Example: Extract text from an image
    # result = ocr.extract_text_from_image('sample_image.png')
    # print(f"Success: {result['success']}")
    # print(f"Text: {result['text']}")
    # print(f"Confidence: {result['confidence']}%")
