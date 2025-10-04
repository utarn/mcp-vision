import time
from typing import Any
from contextlib import asynccontextmanager
import logging
import os
import io
import requests

from mcp.server.fastmcp import FastMCP
from PIL import Image as PILImage
import easyocr
import fitz  # PyMuPDF

from mcp_vision.utils import to_mcp_image, MCPImage, load_image

logger = logging.getLogger(__name__)

global reader
global current_languages
reader = None
current_languages = ['en', 'th']  # Default languages


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Manage application lifecycle with type-safe context"""
    logger.info("Starting up MCP-vision server and loading EasyOCR reader...")
    try:
        # initialize global EasyOCR reader on startup
        init_ocr_reader()
    except Exception as e:
        logger.error(f"Failed to initialize OCR reader: {e}")
        raise e

    logger.info("MCP-vision server has started, listening for requests...")
    yield


mcp = FastMCP(
    "mcp-vision",
    lifespan=app_lifespan,
)


def init_ocr_reader():
    """Initialize the EasyOCR reader"""
    global reader
    global current_languages
    if reader is None:
        start = time.time()
        reader = easyocr.Reader(['en', 'th'])  # Support English and Thai
        current_languages = ['en', 'th']
        print(f"Loaded EasyOCR reader in {time.time() - start:.2f} seconds.")
        
        # Warm up the reader with a dummy operation to ensure models are fully loaded
        try:
            import numpy as np
            dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
            reader.readtext(dummy_image)
            print("EasyOCR reader warmed up successfully.")
        except Exception as e:
            print(f"Warning: EasyOCR reader warmup failed: {e}")


@mcp.tool()
def read_text_from_image(image_path: str, languages: list[str] = None, min_confidence: float = 0.0) -> str:
    """Extract text from an image using EasyOCR.

    Args:
        image_path: path to the image (local file path or URL)
        languages (optional): list of language codes to recognize (default: ['en', 'th'])
                           Common codes: 'en' (English), 'th' (Thai)
        min_confidence (optional): minimum confidence threshold for text recognition (default: 0.0)
                                 Use 0.0 to include all recognized text, even low confidence
    """
    init_ocr_reader()
    
    if languages is None:
        languages = ['en', 'th']
    
    # Reinitialize reader if different languages are requested
    global reader
    global current_languages
    if set(current_languages) != set(languages):
        start = time.time()
        reader = easyocr.Reader(languages)
        current_languages = languages
        print(f"Loaded EasyOCR reader with languages {languages} in {time.time() - start:.2f} seconds.")
        
        # Warm up the reader
        try:
            import numpy as np
            dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
            reader.readtext(dummy_image)
            print("EasyOCR reader warmed up successfully.")
        except Exception as e:
            print(f"Warning: EasyOCR reader warmup failed: {e}")
    
    try:
        # Load the image using the utility function
        pil_image = load_image(image_path)
        
        # Convert PIL Image to numpy array for EasyOCR
        import numpy as np
        image_array = np.array(pil_image)
        
        # Extract text using EasyOCR with optimized parameters for Thai
        # Use detail=0 to get just text, but we need details for confidence filtering
        results = reader.readtext(image_array, detail=1, paragraph=False)
        
        if not results or len(results) == 0:
            return ""
        
        # Extract text with confidence filtering
        extracted_texts = []
        low_confidence_texts = []
        
        for bbox, text, confidence in results:
            if text.strip():
                if confidence >= min_confidence:
                    extracted_texts.append(text)
                else:
                    low_confidence_texts.append(f"{text} (confidence: {confidence:.2f})")
        
        # If no text meets the confidence threshold, include low confidence text for debugging
        if not extracted_texts and low_confidence_texts:
            return "Low confidence text detected:\n" + "\n".join(low_confidence_texts)
        
        return "\n".join(extracted_texts)
        
    except Exception as e:
        logger.error(f"Error while extracting text from image: {e}")
        return f"Error occurred while extracting text: {str(e)}"


@mcp.tool()
def read_text_from_pdf(pdf_path: str, languages: list[str] = None, num_pages: int = None, min_confidence: float = 0.0) -> str:
    """Extract text from a PDF file by converting each page to an image and using EasyOCR.

    Args:
        pdf_path: path to the PDF file (local file path or URL)
        languages (optional): list of language codes to recognize (default: ['en', 'th'])
                           Common codes: 'en' (English), 'th' (Thai)
        num_pages (optional): number of pages to process (default: all pages)
        min_confidence (optional): minimum confidence threshold for text recognition (default: 0.0)
                                 Use 0.0 to include all recognized text, even low confidence
    
    Returns:
        Concatenated text from all processed pages
    """
    init_ocr_reader()
    
    if languages is None:
        languages = ['en', 'th']
    
    # Reinitialize reader if different languages are requested
    global reader
    global current_languages
    if set(current_languages) != set(languages):
        start = time.time()
        reader = easyocr.Reader(languages)
        current_languages = languages
        print(f"Loaded EasyOCR reader with languages {languages} in {time.time() - start:.2f} seconds.")
        
        # Warm up the reader
        try:
            import numpy as np
            dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
            reader.readtext(dummy_image)
            print("EasyOCR reader warmed up successfully.")
        except Exception as e:
            print(f"Warning: EasyOCR reader warmup failed: {e}")
    
    try:
        # Handle URL case
        if pdf_path.startswith("http://") or pdf_path.startswith("https://"):
            response = requests.get(pdf_path)
            response.raise_for_status()
            pdf_bytes = response.content
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        else:
            # Local file case
            if not os.path.isfile(pdf_path):
                return f"Error: PDF file not found at {pdf_path}"
            doc = fitz.open(pdf_path)
        
        # Get total pages and determine how many to process
        total_pages = doc.page_count
        if num_pages is None or num_pages > total_pages:
            num_pages = total_pages
        
        all_text = []
        
        # Process each page
        for page_num in range(num_pages):
            try:
                page = doc[page_num]
                
                # Convert page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))  # 2x zoom for better OCR
                img_data = pix.tobytes("png")
                img = PILImage.open(io.BytesIO(img_data))
                
                # Convert PIL Image to numpy array for EasyOCR
                import numpy as np
                img_array = np.array(img)
                
                # Extract text using EasyOCR with optimized parameters for Thai
                results = reader.readtext(img_array, detail=1, paragraph=False)
                
                # Extract text with confidence filtering
                page_texts = []
                low_confidence_texts = []
                
                for bbox, text, confidence in results:
                    if text.strip():
                        if confidence >= min_confidence:
                            page_texts.append(text)
                        else:
                            low_confidence_texts.append(f"{text} (confidence: {confidence:.2f})")
                
                if page_texts:
                    all_text.append(f"\n--- Page {page_num + 1} ---\n")
                    all_text.extend(page_texts)
                elif low_confidence_texts:
                    # If no text meets confidence threshold, include low confidence text
                    all_text.append(f"\n--- Page {page_num + 1} (Low confidence text) ---\n")
                    all_text.extend(low_confidence_texts)
                    
            except Exception as e:
                logger.error(f"Error processing page {page_num + 1}: {e}")
                all_text.append(f"\n--- Error processing page {page_num + 1}: {str(e)} ---\n")
        
        doc.close()
        return "\n".join(all_text)
        
    except Exception as e:
        logger.error(f"Error while extracting text from PDF: {e}")
        return f"Error occurred while extracting text from PDF: {str(e)}"


def main():
    """Entry point for the MCP server"""
    import sys
    
    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()