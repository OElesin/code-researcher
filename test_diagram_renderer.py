#!/usr/bin/env python3
"""
Test script for the diagram renderer.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.diagram_renderer import DiagramRenderer, render_diagram

def test_simple_diagram():
    """Test rendering a simple diagram."""
    
    # Simple DOT content
    dot_content = '''
    digraph G {
        A -> B;
        B -> C;
        C -> A;
    }
    '''
    
    output_path = Path("generated-diagrams/test_simple.png")
    
    print("🧪 Testing simple diagram rendering...")
    
    success = render_diagram(dot_content, output_path)
    
    if success and output_path.exists():
        print("✅ Simple diagram test passed!")
        return True
    else:
        print("❌ Simple diagram test failed!")
        return False

def test_existing_diagrams():
    """Test rendering existing diagrams."""
    
    print("🧪 Testing existing diagram rendering...")
    
    renderer = DiagramRenderer()
    diagrams_dir = Path("generated-diagrams")
    
    if not diagrams_dir.exists():
        print("❌ No generated-diagrams directory found")
        return False
    
    results = renderer.render_directory(diagrams_dir)
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    print(f"📊 Rendered {success_count}/{total_count} diagrams successfully")
    
    return success_count > 0

def main():
    """Run all tests."""
    
    print("🎨 Testing Code Researcher Diagram Renderer")
    print("=" * 50)
    
    tests = [
        test_simple_diagram,
        test_existing_diagrams
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    exit(main())
