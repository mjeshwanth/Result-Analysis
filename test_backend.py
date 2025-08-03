#!/usr/bin/env python3
"""
Comprehensive test script to verify all backend functionality
"""

import traceback
import sys
import os

def test_imports():
    """Test all critical imports"""
    print("🧪 Testing imports...")
    try:
        import flask
        import firebase_admin
        import magic
        import fitz  # PyMuPDF
        import pdfplumber
        from flask_cors import CORS
        print("✅ All dependencies imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_import():
    """Test main app import and configuration"""
    print("\n🧪 Testing app import...")
    try:
        import app
        from app import app as flask_app
        print("✅ Main app imported successfully")
        
        # Test route registration
        routes = [rule.rule for rule in flask_app.url_map.iter_rules()]
        expected_routes = ['/', '/upload-pdf', '/results/semesters']
        for route in expected_routes:
            if route in routes:
                print(f"✅ Route {route} registered")
            else:
                print(f"❌ Route {route} missing")
                return False
        return True
    except Exception as e:
        print(f"❌ App import error: {e}")
        traceback.print_exc()
        return False

def test_parser_imports():
    """Test parser imports"""
    print("\n🧪 Testing parser imports...")
    try:
        from parser.parser_jntuk import parse_jntuk_pdf, parse_jntuk_pdf_generator
        from parser.parser_autonomous import parse_autonomous_pdf
        print("✅ All parsers imported successfully")
        return True
    except Exception as e:
        print(f"❌ Parser import error: {e}")
        return False

def test_batch_processor():
    """Test batch processor import"""
    print("\n🧪 Testing batch processor...")
    try:
        import batch_pdf_processor
        required_functions = ['main', 'process_single_pdf', 'setup_firebase']
        for func in required_functions:
            if hasattr(batch_pdf_processor, func):
                print(f"✅ Function {func} available")
            else:
                print(f"❌ Function {func} missing")
                return False
        return True
    except Exception as e:
        print(f"❌ Batch processor error: {e}")
        return False

def test_directories():
    """Test required directories"""
    print("\n🧪 Testing directories...")
    required_dirs = ['static', 'temp', 'data', 'templates', 'parser']
    all_exist = True
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ Directory {directory} exists")
        else:
            print(f"❌ Directory {directory} missing")
            all_exist = False
    return all_exist

def test_config_files():
    """Test configuration files"""
    print("\n🧪 Testing config files...")
    config_files = ['serviceAccount.json', 'config.py', 'requirements.txt']
    all_exist = True
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ Config file {config_file} exists")
        else:
            print(f"❌ Config file {config_file} missing")
            all_exist = False
    return all_exist

def test_flask_endpoints():
    """Test Flask endpoints"""
    print("\n🧪 Testing Flask endpoints...")
    try:
        from app import app
        app.config['TESTING'] = True
        client = app.test_client()
        
        endpoints = [
            ('GET', '/', 200),
            ('GET', '/results/semesters', 200),
            ('GET', '/data-files', 200),
            ('GET', '/favicon.ico', 200)
        ]
        
        for method, endpoint, expected_status in endpoints:
            resp = client.open(endpoint, method=method)
            if resp.status_code == expected_status:
                print(f"✅ {method} {endpoint} -> {resp.status_code}")
            else:
                print(f"❌ {method} {endpoint} -> {resp.status_code} (expected {expected_status})")
                return False
        return True
    except Exception as e:
        print(f"❌ Flask endpoint test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting comprehensive backend tests...\n")
    
    tests = [
        test_imports,
        test_directories,
        test_config_files,
        test_app_import,
        test_parser_imports,
        test_batch_processor,
        test_flask_endpoints
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
