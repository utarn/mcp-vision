import time
import logging
import os
import io
import requests
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import easyocr
import fitz  # PyMuPDF
import numpy as np
from PIL import Image as PILImage

from mcp_vision.utils import load_image
from mcp_vision.cache import get_cache

# Get batch size from environment variable, default to 1 for sequential processing
# Batch size determines how many PDF pages to process simultaneously
DEFAULT_BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '1'))

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
    def read_text_from_image(image_path: str, min_confidence: float = 0.0, use_cache: bool = True) -> str:
        """Extract text from an image using EasyOCR.

        Args:
            image_path: path to the image (local file path or URL)
            min_confidence (optional): minimum confidence threshold for text recognition (default: 0.0)
                                     Use 0.0 to include all recognized text, even low confidence
            use_cache (optional): whether to use caching (default: True)
        """
        # Try to get from cache first
        if use_cache:
            cache = get_cache()
            cached_result = cache.get(image_path, min_confidence)
            if cached_result is not None:
                return cached_result
        
        try:
            # Load the image using the utility function
            pil_image = load_image(image_path)
            
            # Convert PIL Image to numpy array for EasyOCR
            image_array = np.array(pil_image)
            
            result = OCRCore.extract_text_from_image_array(image_array, min_confidence)
            
            # Cache the result
            if use_cache and not result.startswith("Error occurred while extracting text"):
                cache = get_cache()
                cache.put(image_path, result, min_confidence)
            
            return result
            
        except Exception as e:
            logger.error(f"Error while extracting text from image: {e}")
            error_msg = f"Error occurred while extracting text: {str(e)}"
            return error_msg
    
    @staticmethod
    def _process_pdf_page(page_num: int, page, min_confidence: float) -> Tuple[int, str]:
        """Process a single PDF page and return its text.
        
        Args:
            page_num: Page number (0-indexed)
            page: PyMuPDF page object
            min_confidence: Minimum confidence threshold
            
        Returns:
            Tuple of (page_num, formatted_text)
        """
        try:
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
                    formatted_text = f"\n--- Page {page_num + 1} (Low confidence text) ---\n{page_text}"
                else:
                    formatted_text = f"\n--- Page {page_num + 1} ---\n{page_text}"
            else:
                formatted_text = f"\n--- Page {page_num + 1} (No text detected) ---\n"
                
            return (page_num, formatted_text)
            
        except Exception as e:
            logger.error(f"Error processing page {page_num + 1}: {e}")
            return (page_num, f"\n--- Error processing page {page_num + 1}: {str(e)} ---\n")
    
    @staticmethod
    def read_text_from_pdf(pdf_path: str, num_pages: int = None, min_confidence: float = 0.0, use_cache: bool = True, batch_size: int = None) -> str:
        """Extract text from a PDF file by converting each page to an image and using EasyOCR.

        Args:
            pdf_path: path to the PDF file (local file path or URL)
            num_pages (optional): number of pages to process (default: all pages)
            min_confidence (optional): minimum confidence threshold for text recognition (default: 0.0)
                                     Use 0.0 to include all recognized text, even low confidence
            use_cache (optional): whether to use caching (default: True)
            batch_size (optional): number of pages to process simultaneously (default: from BATCH_SIZE env var or 1)
                                 Set to 1 for sequential processing, higher values for parallel processing
        
        Returns:
            Concatenated text from all processed pages
        """
        # Use provided batch_size or fall back to environment variable
        if batch_size is None:
            batch_size = DEFAULT_BATCH_SIZE
        
        # Try to get from cache first
        if use_cache:
            cache = get_cache()
            # Create a unique cache key that includes pdf_path, num_pages, and min_confidence
            cache_key = f"{pdf_path}_pages_{num_pages or 'all'}_conf_{min_confidence}"
            cached_result = cache.get(cache_key, min_confidence)
            if cached_result is not None:
                return cached_result
        
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
            
            logger.info(f"Processing {num_pages} pages with batch_size={batch_size}")
            
            # Process pages either sequentially or in parallel based on batch_size
            if batch_size <= 1:
                # Sequential processing
                all_text = []
                for page_num in range(num_pages):
                    page = doc[page_num]
                    _, formatted_text = OCRCore._process_pdf_page(page_num, page, min_confidence)
                    all_text.append(formatted_text)
            else:
                # Parallel processing with ThreadPoolExecutor
                page_results = {}
                with ThreadPoolExecutor(max_workers=batch_size) as executor:
                    # Submit all page processing tasks
                    future_to_page = {
                        executor.submit(OCRCore._process_pdf_page, page_num, doc[page_num], min_confidence): page_num
                        for page_num in range(num_pages)
                    }
                    
                    # Collect results as they complete
                    for future in as_completed(future_to_page):
                        page_num, formatted_text = future.result()
                        page_results[page_num] = formatted_text
                
                # Sort results by page number to maintain order
                all_text = [page_results[i] for i in range(num_pages)]
            
            doc.close()
            result = "\n".join(all_text)
            
            # Cache the result
            if use_cache and not result.startswith("Error occurred while extracting text"):
                cache = get_cache()
                # Create a unique cache key that includes pdf_path, num_pages, and min_confidence
                cache_key = f"{pdf_path}_pages_{num_pages or 'all'}_conf_{min_confidence}"
                cache.put(cache_key, result, min_confidence)
            
            return result
            
        except Exception as e:
            logger.error(f"Error while extracting text from PDF: {e}")
            error_msg = f"Error occurred while extracting text from PDF: {str(e)}"
            return error_msg


# Convenience functions for backward compatibility
def init_ocr_reader():
    """Initialize the EasyOCR reader (backward compatibility)"""
    OCRCore.init_ocr_reader()


def read_text_from_image(image_path: str, min_confidence: float = 0.0, use_cache: bool = True) -> str:
    """Extract text from an image using EasyOCR (backward compatibility)"""
    return OCRCore.read_text_from_image(image_path, min_confidence, use_cache)


def read_text_from_pdf(pdf_path: str, num_pages: int = None, min_confidence: float = 0.0, use_cache: bool = True, batch_size: int = None) -> str:
    """Extract text from a PDF file using EasyOCR (backward compatibility)"""
    return OCRCore.read_text_from_pdf(pdf_path, num_pages, min_confidence, use_cache, batch_size)