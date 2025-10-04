#!/usr/bin/env python3
"""
Simple test runner for MCP vision tools.
This script provides an easy way to test the vision functionality manually.
"""

import asyncio
import sys
from pathlib import Path
from fastmcp import Client
from mcp_vision.server import mcp


async def test_image_ocr(image_path: str, languages: list[str] = None):
    """Test OCR on an image file"""
    print(f"🖼️  Testing OCR on image: {image_path}")
    print(f"🌍 Languages: {languages or ['en', 'th']}")
    
    async with Client(mcp) as client:
        try:
            result = await client.call_tool("read_text_from_image", {
                "image_path": image_path,
                "languages": languages or ["en", "th"]
            })
            
            extracted_text = result.content[0].text if result.content else ""
            
            if extracted_text:
                print(f"✅ Successfully extracted text:")
                print("-" * 50)
                print(extracted_text)
                print("-" * 50)
            else:
                print("⚠️  No text extracted from image")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def test_pdf_ocr(pdf_path: str, languages: list[str] = None, num_pages: int = None):
    """Test OCR on a PDF file"""
    print(f"📄 Testing OCR on PDF: {pdf_path}")
    print(f"🌍 Languages: {languages or ['en', 'th']}")
    print(f"📖 Pages: {num_pages or 'all'}")
    
    async with Client(mcp) as client:
        try:
            result = await client.call_tool("read_text_from_pdf", {
                "pdf_path": pdf_path,
                "languages": languages or ["en", "th"],
                "num_pages": num_pages
            })
            
            extracted_text = result.content[0].text if result.content else ""
            
            if extracted_text:
                print(f"✅ Successfully extracted text:")
                print("-" * 50)
                print(extracted_text)
                print("-" * 50)
            else:
                print("⚠️  No text extracted from PDF")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def test_image_ocr_with_low_confidence(image_path: str, languages: list[str] = None):
    """Test OCR on an image file with low confidence threshold for Thai text"""
    print(f"🔍 Testing OCR with low confidence threshold: {image_path}")
    print(f"🌍 Languages: {languages or ['en', 'th']}")
    
    async with Client(mcp) as client:
        try:
            result = await client.call_tool("read_text_from_image", {
                "image_path": image_path,
                "languages": languages or ["en", "th"],
                "min_confidence": 0.0  # Include all text, even low confidence
            })
            
            extracted_text = result.content[0].text if result.content else ""
            
            if extracted_text:
                print(f"✅ Successfully extracted text (including low confidence):")
                print("-" * 50)
                print(extracted_text)
                print("-" * 50)
            else:
                print("⚠️  No text extracted from image")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Main test runner"""
    print("🚀 MCP Vision Test Runner")
    print("=" * 50)
    
    # Get sample file paths
    base_dir = Path(__file__).parent
    image_path = base_dir / "images" / "sample.png"
    pdf_path = base_dir / "images" / "sample.pdf"
    
    # Test image OCR
    if image_path.exists():
        await test_image_ocr(str(image_path), ["en"])
        print()
    else:
        print(f"⚠️  Sample image not found: {image_path}")
    
    # Test PDF OCR
    if pdf_path.exists():
        await test_pdf_ocr(str(pdf_path), ["en"], 1)  # Test first page only
        print()
    else:
        print(f"⚠️  Sample PDF not found: {pdf_path}")
    
    # Test with multiple languages
    if image_path.exists():
        print("🌍 Testing with multiple languages (English + Thai)...")
        await test_image_ocr(str(image_path), ["en", "th"])
        
        print("\n🔍 Testing Thai extraction with low confidence threshold...")
        await test_image_ocr_with_low_confidence(str(image_path), ["en", "th"])
    
    print("\n✨ Testing completed!")


if __name__ == "__main__":
    # Allow command line arguments for custom files
    if len(sys.argv) > 1:
        if sys.argv[1] == "--image" and len(sys.argv) > 2:
            asyncio.run(test_image_ocr(sys.argv[2]))
        elif sys.argv[1] == "--pdf" and len(sys.argv) > 2:
            asyncio.run(test_pdf_ocr(sys.argv[2]))
        else:
            print("Usage:")
            print("  python test_runner.py                    # Run all tests with sample files")
            print("  python test_runner.py --image <path>     # Test specific image")
            print("  python test_runner.py --pdf <path>       # Test specific PDF")
    else:
        asyncio.run(main())