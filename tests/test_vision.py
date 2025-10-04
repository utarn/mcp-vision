import pytest
import pytest_asyncio
import asyncio
import os
from pathlib import Path
from fastmcp import Client
from mcp_vision.server import mcp


class TestVisionTools:
    """Test suite for MCP vision tools using FastMCP client"""

    @pytest.fixture
    def sample_files(self):
        """Get paths to sample files"""
        base_dir = Path(__file__).parent.parent
        return {
            "image": base_dir / "images" / "sample.png",
            "pdf": base_dir / "images" / "sample.pdf",
        }

    @pytest_asyncio.fixture
    async def client(self):
        """Create FastMCP client for testing"""
        async with Client(mcp) as client:
            yield client

    @pytest.mark.asyncio
    async def test_read_text_from_image(self, client, sample_files):
        """Test reading text from image file"""
        image_path = str(sample_files["image"])
        
        # Check if sample image exists
        if not os.path.exists(image_path):
            pytest.skip(f"Sample image not found at {image_path}")
        
        # Test reading text from image
        result = await client.call_tool("read_text_from_image", {
            "image_path": image_path,
            "languages": ["en"]
        })
        
        # Verify we got a result
        assert result.content is not None
        assert len(result.content) > 0
        
        # Extract text from result
        extracted_text = result.content[0].text if result.content else ""
        
        # Print the extracted text for manual verification
        print(f"\nExtracted text from image:\n{extracted_text}")
        
        # Basic validation - should not be empty for a real image
        assert isinstance(extracted_text, str)

    @pytest.mark.asyncio
    async def test_read_text_from_pdf(self, client, sample_files):
        """Test reading text from PDF file"""
        pdf_path = str(sample_files["pdf"])
        
        # Check if sample PDF exists
        if not os.path.exists(pdf_path):
            pytest.skip(f"Sample PDF not found at {pdf_path}")
        
        # Test reading text from PDF
        result = await client.call_tool("read_text_from_pdf", {
            "pdf_path": pdf_path,
            "languages": ["en"],
            "num_pages": 1  # Limit to first page for faster testing
        })
        
        # Verify we got a result
        assert result.content is not None
        assert len(result.content) > 0
        
        # Extract text from result
        extracted_text = result.content[0].text if result.content else ""
        
        # Print the extracted text for manual verification
        print(f"\nExtracted text from PDF:\n{extracted_text}")
        
        # Basic validation - should not be empty for a real PDF
        assert isinstance(extracted_text, str)

    @pytest.mark.asyncio
    async def test_read_text_with_multiple_languages(self, client, sample_files):
        """Test reading text with multiple languages"""
        image_path = str(sample_files["image"])
        
        # Check if sample image exists
        if not os.path.exists(image_path):
            pytest.skip(f"Sample image not found at {image_path}")
        
        # Test with English and Thai
        result = await client.call_tool("read_text_from_image", {
            "image_path": image_path,
            "languages": ["en", "th"]
        })
        
        # Verify we got a result
        assert result.content is not None
        assert len(result.content) > 0
        
        # Extract text from result
        extracted_text = result.content[0].text if result.content else ""
        
        print(f"\nExtracted text with multiple languages:\n{extracted_text}")
        
        # Basic validation
        assert isinstance(extracted_text, str)

    @pytest.mark.asyncio
    async def test_error_handling_nonexistent_file(self, client):
        """Test error handling for non-existent files"""
        nonexistent_path = "/path/to/nonexistent/file.png"
        
        # Test with non-existent image
        result = await client.call_tool("read_text_from_image", {
            "image_path": nonexistent_path
        })
        
        # Should return an error message
        assert result.content is not None
        assert len(result.content) > 0
        error_text = result.content[0].text if result.content else ""
        assert "Error" in error_text or "not found" in error_text.lower()
        
        print(f"\nError handling result: {error_text}")

    @pytest.mark.asyncio
    async def test_list_available_tools(self, client):
        """Test that we can list all available tools"""
        tools = await client.list_tools()
        
        # Verify our tools are available
        tool_names = [tool.name for tool in tools]
        
        expected_tools = ["read_text_from_image", "read_text_from_pdf"]
        for tool_name in expected_tools:
            assert tool_name in tool_names, f"Expected tool {tool_name} not found"
        
        print(f"\nAvailable tools: {tool_names}")


# Manual test function for quick verification
async def manual_test():
    """Manual test function for quick verification"""
    print("Running manual tests...")
    
    # Get sample file paths
    base_dir = Path(__file__).parent.parent
    image_path = base_dir / "images" / "sample.png"
    pdf_path = base_dir / "images" / "sample.pdf"
    
    async with Client(mcp) as client:
        print(f"\nTesting image: {image_path}")
        if image_path.exists():
            result = await client.call_tool("read_text_from_image", {
                "image_path": str(image_path),
                "languages": ["en"]
            })
            print(f"Image result: {result.content[0].text if result.content else 'No content'}")
        else:
            print("Sample image not found")
        
        print(f"\nTesting PDF: {pdf_path}")
        if pdf_path.exists():
            result = await client.call_tool("read_text_from_pdf", {
                "pdf_path": str(pdf_path),
                "languages": ["en"],
                "num_pages": 1
            })
            print(f"PDF result: {result.content[0].text if result.content else 'No content'}")
        else:
            print("Sample PDF not found")


if __name__ == "__main__":
    # Run manual tests
    asyncio.run(manual_test())