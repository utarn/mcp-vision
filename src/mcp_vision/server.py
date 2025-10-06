from contextlib import asynccontextmanager
import logging

from fastmcp import FastMCP

from mcp_vision.core import init_ocr_reader, read_text_from_image, read_text_from_pdf

logger = logging.getLogger(__name__)

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


@mcp.tool()
def read_text_from_image(image_path: str, min_confidence: float = 0.0) -> str:
    """Extract text from an image using EasyOCR.

    Args:
        image_path: path to the image (local file path or URL)
        min_confidence (optional): minimum confidence threshold for text recognition (default: 0.0)
                                 Use 0.0 to include all recognized text, even low confidence
    """
    from mcp_vision.core import read_text_from_image as core_read_text_from_image
    return core_read_text_from_image(image_path, min_confidence)


@mcp.tool()
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
    from mcp_vision.core import read_text_from_pdf as core_read_text_from_pdf
    return core_read_text_from_pdf(pdf_path, num_pages, min_confidence)


def main():
    """Entry point for the MCP server"""
    # Run the MCP server with stdio transport
    mcp.run()


if __name__ == "__main__":
    main()