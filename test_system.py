#!/usr/bin/env python3
"""
Quick test script to verify the Vibe-to-Attribute Clothing Recommendation System
is working correctly without requiring all dependencies.
"""

import os
import sys
from pathlib import Path

def test_file_structure():
    """Test that all required files exist."""
    print("🔍 Testing file structure...")
    
    required_files = [
        'requirements.txt',
        'env.example',
        'streamlit_app.py',
        'create_catalog.py',
        'data/Apparels_shared.xlsx',
        'data/vibes/fit_mapping.json',
        'data/vibes/color_mapping.json',
        'data/vibes/occasion_mapping.json',
        'src/recommendation_system.py',
        'modules/nlp_analyzer.py',
        'modules/similarity_matcher.py',
        'modules/gpt_inference.py',
        'modules/catalog_filter.py',
        'modules/nlg_generator.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing_files:
        print(f"\n❌ Missing files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    print("✅ All required files present!")
    return True

def test_basic_imports():
    """Test that basic imports work."""
    print("\n🔍 Testing basic imports...")
    
    try:
        # Test data loading
        import json
        
        # Test vibe mappings
        with open('data/vibes/fit_mapping.json', 'r') as f:
            fit_data = json.load(f)
        print(f"  ✅ Fit mappings loaded: {len(fit_data)} entries")
        
        with open('data/vibes/color_mapping.json', 'r') as f:
            color_data = json.load(f)
        print(f"  ✅ Color mappings loaded: {len(color_data)} entries")
        
        with open('data/vibes/occasion_mapping.json', 'r') as f:
            occasion_data = json.load(f)
        print(f"  ✅ Occasion mappings loaded: {len(occasion_data)} entries")
        
        return True
    
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_catalog_loading():
    """Test that the catalog can be loaded."""
    print("\n🔍 Testing catalog loading...")
    
    try:
        import pandas as pd
        
        catalog_df = pd.read_excel('data/Apparels_shared.xlsx')
        print(f"  ✅ Catalog loaded: {len(catalog_df)} products")
        
        # Check required columns
        required_columns = ['Name', 'Category', 'Price', 'Available_Sizes']
        missing_columns = [col for col in required_columns if col not in catalog_df.columns]
        
        if missing_columns:
            print(f"  ⚠️ Missing columns: {missing_columns}")
        else:
            print("  ✅ All required columns present")
        
        return True
    
    except Exception as e:
        print(f"❌ Catalog test failed: {e}")
        return False

def test_system_initialization():
    """Test basic system initialization."""
    print("\n🔍 Testing system initialization...")
    
    try:
        # Add paths
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
        
        # Test basic module imports (without dependencies that might fail)
        from catalog_filter import CatalogFilter
        
        # Test catalog filter
        catalog_filter = CatalogFilter()
        print("  ✅ Catalog filter initialized")
        
        # Test basic filtering
        summary = catalog_filter.get_catalog_summary()
        print(f"  ✅ Catalog summary: {summary.get('total_products', 0)} products")
        
        return True
    
    except Exception as e:
        print(f"❌ System initialization test failed: {e}")
        print(f"    This might be due to missing dependencies - install with: pip install -r requirements.txt")
        return False

def main():
    """Run all tests."""
    print("🌟 Vibe-to-Attribute Clothing Recommendation System - Test Suite")
    print("=" * 70)
    
    tests = [
        test_file_structure,
        test_basic_imports,
        test_catalog_loading,
        test_system_initialization
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 70)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to run.")
        print("\n🚀 To start the application, run:")
        print("   python3 run.py")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        print("\n🔧 Try installing dependencies:")
        print("   pip install -r requirements.txt")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 