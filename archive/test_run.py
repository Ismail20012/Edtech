#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify the ribbon interface works correctly.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported without errors."""
    try:
        from views.main_window import MainWindow
        from views.ribbon_widget import RibbonWidget
        from controllers.main_controller import MainController
        from views.worker_thread import WorkerThread
        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_app_creation():
    """Test that the application can be created."""
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication([])
        from views.main_window import MainWindow
        main_window = MainWindow()
        print("✓ Main window created successfully")
        return True
    except Exception as e:
        print(f"✗ App creation error: {e}")
        return False

if __name__ == "__main__":
    print("Testing School OCR Demo Components...")
    print("-" * 40)
    
    success = True
    success &= test_imports()
    success &= test_app_creation()
    
    print("-" * 40)
    if success:
        print("✓ All tests passed! The application should run correctly.")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    
    sys.exit(0 if success else 1)
