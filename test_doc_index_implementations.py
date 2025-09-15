#!/usr/bin/env python3
"""Test script to verify both document index implementations work correctly."""

import asyncio
import os
from pathlib import Path

from app.services.doc_index_factory import create_document_index, get_available_implementations


async def test_implementation(implementation: str, doc_root: str = "doc") -> bool:
    """Test a specific document index implementation."""
    print(f"\n🧪 Testing {implementation} implementation...")
    
    try:
        # Create document index
        doc_index = create_document_index(doc_root=doc_root, implementation=implementation)
        
        # Initialize
        print("  📚 Initializing document index...")
        await doc_index.initialize()
        print("  ✅ Initialization successful")
        
        # Test search
        print("  🔍 Testing search functionality...")
        results = await doc_index.search("test query", k=1)
        print(f"  ✅ Search returned {len(results)} results")
        
        # Test document content retrieval
        if results:
            print("  📄 Testing document content retrieval...")
            content = await doc_index.get_document_content(results[0].doc_id)
            print(f"  ✅ Retrieved content: {len(content) if content else 0} characters")
        
        # Test find best document
        print("  🎯 Testing find best document...")
        best_content = await doc_index.find_best_document_content("test query")
        print(f"  ✅ Found best document: {len(best_content) if best_content else 0} characters")
        
        print(f"  🎉 {implementation} implementation test passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ {implementation} implementation test failed: {e}")
        return False


async def main():
    """Test all available document index implementations."""
    print("🚀 Testing Document Index Implementations")
    print("=" * 50)
    
    # Check available implementations
    available = get_available_implementations()
    print(f"📋 Available implementations: {available}")
    
    if not available:
        print("❌ No implementations available!")
        return
    
    # Create test documents if they don't exist
    doc_root = Path("doc")
    doc_root.mkdir(exist_ok=True)
    
    test_doc = doc_root / "test_document.txt"
    if not test_doc.exists():
        test_doc.write_text("This is a test document for testing the document index implementations.")
        print("📝 Created test document")
    
    # Test each implementation
    results = {}
    for implementation in available:
        results[implementation] = await test_implementation(implementation)
    
    # Test auto-detection
    print(f"\n🤖 Testing auto-detection...")
    results["auto"] = await test_implementation("auto")
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    for impl, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{impl:20} {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
