import time
import logging
import os
import io
import requests
from typing import List, Tuple, Optional

import easyocr
import fitz  # PyMuPDF
import numpy as np
from PIL import Image as PILImage

from mcp_vision.utils import load_image

logger = logging.getLogger(__name__)

# Global OCR reader instance
_reader = None


class OCRCore:
    """Core OCR functionality shared between MCP server and HTTP server"""
    
    @staticmethod
    def init_ocr_reader():
        """Initialize the EasyOCR reader"""
        global _reader
        if _reader is None:
            start = time.time()
            _reader = easyocr.Reader(['en', 'th'])  # Support English and Thai
            print(f"Loaded EasyOCR reader in {time.time() - start:.2f} seconds.")
            
            # Warm up the reader with a dummy operation to ensure models are fully loaded
            try:
                dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
                _reader.readtext(dummy_image)
                print("EasyOCR reader warmed up successfully.")
            except Exception as e:
                print(f"Warning: EasyOCR reader warmup failed: {e}")
    
    @staticmethod
    def get_reader():
        """Get the OCR reader instance, initializing if necessary"""
        if _reader is None:
            OCRCore.init_ocr_reader()
        return _reader
    
    @staticmethod
    def extract_text_from_image_array(image_array: np.ndarray, min_confidence: float = 0.0) -> str:
        """Extract text from a numpy array image using EasyOCR"""
        reader = OCRCore.get_reader()
        
        # Extract text using EasyOCR with optimized parameters for Thai
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
    
    @staticmethod
    def read_text_from_image(image_path: str, min_confidence: float = 0.0) -> str:
        """Extract text from an image using EasyOCR.

        Args:
            image_path: path to the image (local file path or URL)
            min_confidence (optional): minimum confidence threshold for text recognition (default: 0.0)
                                     Use 0.0 to include all recognized text, even low confidence
        """
        try:
            # Load the image using the utility function
            pil_image = load_image(image_path)
            
            # Convert PIL Image to numpy array for EasyOCR
            image_array = np.array(pil_image)
            
            return OCRCore.extract_text_from_image_array(image_array, min_confidence)
            
        except Exception as e:
            logger.error(f"Error while extracting text from image: {e}")
            return f"Error occurred while extracting text: {str(e)}"
    
    @staticmethod
    def read_text_from_pdf(pdf_path: str, num_pages: int = None, min_confidence: float = 0.0) -> str:
        """Extract text from a PDF file by converting each page to an image and using EasyOCR.

        Args:
            pdf_path: path to the PDF file (local file path or URL)
            num_pages (optional): number of pages to process (default: all pages)
            min_confidence (optional): minimum confidence threshold for text recognition (default: 0.0)
                                     Use 0.0 to include all recognized text, even low confidence
        
        Returns:
            Concatenated text from all processed pages
        """
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
                    img_array = np.array(img)
                    
                    # Extract text using the core method
                    page_text = OCRCore.extract_text_from_image_array(img_array, min_confidence)
                    
                    if page_text:
                        if page_text.startswith("Low confidence text detected:"):
                            all_text.append(f"\n--- Page {page_num + 1} (Low confidence text) ---\n")
                            all_text.append(page_text)
                        else:
                            all_text.append(f"\n--- Page {page_num + 1} ---\n")
                            all_text.append(page_text)
                    else:
                        all_text.append(f"\n--- Page {page_num + 1} (No text detected) ---\n")
                        
                except Exception as e:
                    logger.error(f"Error processing page {page_num + 1}: {e}")
                    all_text.append(f"\n--- Error processing page {page_num + 1}: {str(e)} ---\n")
            
            doc.close()
            return "\n".join(all_text)
            
        except Exception as e:
            logger.error(f"Error while extracting text from PDF: {e}")
            return f"Error occurred while extracting text from PDF: {str(e)}"


# Convenience functions for backward compatibility
def init_ocr_reader():
    """Initialize the EasyOCR reader (backward compatibility)"""
    OCRCore.init_ocr_reader()


def read_text_from_image(image_path: str, min_confidence: float = 0.0) -> str:
    """Extract text from an image using EasyOCR (backward compatibility)"""
    return OCRCore.read_text_from_image(image_path, min_confidence)


def read_text_from_pdf(pdf_path: str, num_pages: int = None, min_confidence: float = 0.0) -> str:
    """Extract text from a PDF file using EasyOCR (backward compatibility)"""
    return OCRCore.read_text_from_pdf(pdf_path, num_pages, min_confidence)