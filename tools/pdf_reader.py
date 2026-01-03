from crewai.tools import BaseTool
import fitz  # PyMuPDF
import os
import base64
import io
from PIL import Image
import google.generativeai as genai
from typing import Optional

class PDFReadTool(BaseTool):
    """
    Enhanced PDF Reader that extracts both text and images.
    Images are analyzed using Google Gemini Vision for comprehensive understanding.
    """
    name: str = "PDF Reader"
    description: str = "Reads the entire content of a PDF file including text and image analysis."
    pdf_path: str
    analyze_images: bool = True

    def _extract_text(self, doc) -> str:
        """Extract all text from PDF pages."""
        text = ""
        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text()
            if page_text.strip():
                text += f"\n--- Page {page_num} ---\n{page_text}"
        return text

    def _extract_images(self, doc) -> list:
        """Extract images from PDF and return as PIL Image objects with page info."""
        images = []
        for page_num, page in enumerate(doc, 1):
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Convert to PIL Image
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    
                    # Only process images that are reasonably sized (skip tiny icons)
                    if pil_image.width > 50 and pil_image.height > 50:
                        images.append({
                            "page": page_num,
                            "index": img_index + 1,
                            "image": pil_image,
                            "size": (pil_image.width, pil_image.height)
                        })
                except Exception as e:
                    continue  # Skip problematic images
        
        return images

    def _analyze_image_with_gemini(self, image: Image.Image, page_num: int, img_index: int) -> str:
        """Analyze an image using Google Gemini Vision."""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return f"[Image on page {page_num}, image {img_index}: Unable to analyze - GOOGLE_API_KEY not set]"
            
            genai.configure(api_key=api_key)
            # Try available models
            model = None
            for model_name in ['gemini-2.0-flash-exp', 'gemini-1.5-flash-latest', 'gemini-pro-vision']:
                try:
                    model = genai.GenerativeModel(model_name)
                    break
                except:
                    continue
            if not model:
                model = genai.GenerativeModel('gemini-pro-vision')
            
            prompt = """Analyze this image from a PDF document. Provide a detailed description including:
1. What type of content it shows (chart, graph, diagram, photo, table, etc.)
2. Key information, data points, or text visible in the image
3. Any important insights or conclusions that can be drawn
4. If it's a chart/graph, describe the trends or patterns shown

Be concise but comprehensive."""

            response = model.generate_content([prompt, image])
            return response.text
            
        except Exception as e:
            return f"[Image on page {page_num}, image {img_index}: Analysis failed - {str(e)}]"

    def _run(self) -> str:
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(self.pdf_path)
            
            # Extract text
            text_content = self._extract_text(doc)
            
            # Extract and analyze images if enabled
            image_analysis = ""
            if self.analyze_images:
                images = self._extract_images(doc)
                
                if images:
                    image_analysis = "\n\n=== IMAGE ANALYSIS ===\n"
                    image_analysis += f"Found {len(images)} significant images in the document.\n"
                    
                    for img_data in images:
                        image_analysis += f"\n--- Image on Page {img_data['page']}, Image #{img_data['index']} ---\n"
                        image_analysis += f"Size: {img_data['size'][0]}x{img_data['size'][1]} pixels\n"
                        
                        # Analyze with Gemini Vision
                        analysis = self._analyze_image_with_gemini(
                            img_data['image'],
                            img_data['page'],
                            img_data['index']
                        )
                        image_analysis += f"Analysis:\n{analysis}\n"
                else:
                    image_analysis = "\n\n=== IMAGE ANALYSIS ===\nNo significant images found in the document.\n"
            
            doc.close()
            
            # Combine text and image analysis
            result = "=== TEXT CONTENT ===\n"
            result += text_content if text_content.strip() else "No text content found."
            result += image_analysis
            
            return result
            
        except Exception as e:
            return f"Error reading PDF: {e}"


class PDFImageOnlyTool(BaseTool):
    """
    Tool specifically for extracting and analyzing only images from PDFs.
    Useful when you want to focus on visual content like charts, diagrams, etc.
    """
    name: str = "PDF Image Analyzer"
    description: str = "Extracts and analyzes images from a PDF file using AI vision capabilities."
    pdf_path: str

    def _run(self) -> str:
        try:
            doc = fitz.open(self.pdf_path)
            api_key = os.getenv("GOOGLE_API_KEY")
            
            if not api_key:
                return "Error: GOOGLE_API_KEY is required for image analysis."
            
            genai.configure(api_key=api_key)
            # Try available models
            model = None
            for model_name in ['gemini-2.0-flash-exp', 'gemini-1.5-flash-latest', 'gemini-pro-vision']:
                try:
                    model = genai.GenerativeModel(model_name)
                    break
                except:
                    continue
            if not model:
                model = genai.GenerativeModel('gemini-pro-vision')
            
            results = []
            total_images = 0
            
            for page_num, page in enumerate(doc, 1):
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    try:
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        pil_image = Image.open(io.BytesIO(image_bytes))
                        
                        # Skip small images (likely icons)
                        if pil_image.width < 50 or pil_image.height < 50:
                            continue
                        
                        total_images += 1
                        
                        prompt = """Describe this image in detail:
- What type of visual is it (chart, graph, diagram, photo, screenshot)?
- What are the key elements or data points?
- What insights can be drawn from it?"""
                        
                        response = model.generate_content([prompt, pil_image])
                        
                        results.append(f"\n📊 Page {page_num}, Image {img_index + 1}:\n{response.text}")
                        
                    except Exception as e:
                        continue
            
            doc.close()
            
            if results:
                return f"Found and analyzed {total_images} images:\n" + "\n".join(results)
            else:
                return "No significant images found in the PDF."
                
        except Exception as e:
            return f"Error analyzing PDF images: {e}"
