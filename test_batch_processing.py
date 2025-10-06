#!/usr/bin/env python3
"""
Test script to verify batch processing functionality for PDF OCR.
"""
import time
from pathlib import Path
from mcp_vision.core import read_text_from_pdf

def test_batch_processing():
    """Test batch processing with different batch sizes"""
    # Use a sample PDF if it exists
    pdf_path = Path("images/sample.pdf")
    
    if not pdf_path.exists():
        print(f"Warning: Sample PDF not found at {pdf_path}")
        print("Skipping batch processing test")
        return
    
    print("Testing batch processing with different batch sizes...")
    print("=" * 60)
    
    # Test with batch_size=1 (sequential)
    print("\nTest 1: Sequential processing (batch_size=1)")
    start_time = time.time()
    result1 = read_text_from_pdf(str(pdf_path), num_pages=2, batch_size=1, use_cache=False)
    sequential_time = time.time() - start_time
    print(f"Time taken: {sequential_time:.2f} seconds")
    print(f"Text length: {len(result1)} characters")
    
    # Test with batch_size=2 (parallel)
    print("\nTest 2: Parallel processing (batch_size=2)")
    start_time = time.time()
    result2 = read_text_from_pdf(str(pdf_path), num_pages=2, batch_size=2, use_cache=False)
    parallel_time = time.time() - start_time
    print(f"Time taken: {parallel_time:.2f} seconds")
    print(f"Text length: {len(result2)} characters")
    
    # Compare results
    print("\n" + "=" * 60)
    print("Comparison:")
    print(f"Sequential time: {sequential_time:.2f}s")
    print(f"Parallel time: {parallel_time:.2f}s")
    if parallel_time < sequential_time:
        speedup = sequential_time / parallel_time
        print(f"Speedup: {speedup:.2f}x faster with batch processing")
    else:
        print("Note: Parallel processing may not show speedup for small workloads")
    
    # Verify results are consistent
    if result1 == result2:
        print("\n✓ Results are consistent between sequential and parallel processing")
    else:
        print("\n⚠ Warning: Results differ between processing modes")
        print("This may indicate an issue with parallel processing")

if __name__ == "__main__":
    test_batch_processing()