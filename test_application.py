#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify the school OCR demo application functionality.
"""

import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from models.database import DatabaseManager, open_database
        print("✓ Database module imported successfully")
        
        from views.main_window import MainWindow
        print("✓ Main window imported successfully")
        
        from views.roster_import_dialog import RosterImportDialog
        print("✓ Roster import dialog imported successfully")
        
        from views.grade_import_dialog import GradeSheetImportDialog
        print("✓ Grade import dialog imported successfully")
        
        from views.coefficient_editor_dialog import CoefficientEditorDialog
        print("✓ Coefficient editor dialog imported successfully")
        
        from reports.grade_writer import GradeReportGenerator
        print("✓ Report generator imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        traceback.print_exc()
        return False

def test_database():
    """Test database functionality."""
    print("\nTesting database...")
    
    try:
        # Need to create QApplication first for Qt SQL
        app = QApplication([])
        
        from models.database import DatabaseManager
        
        db = DatabaseManager()
        
        # Test basic queries
        classes = db.get_all_classes()
        print(f"✓ Found {len(classes)} classes")
        
        subjects = db.get_all_subjects()
        print(f"✓ Found {len(subjects)} subjects")
        
        terms = db.get_all_terms()
        print(f"✓ Found {len(terms)} terms")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        traceback.print_exc()
        return False

def test_ui():
    """Test UI creation."""
    print("\nTesting UI...")
    
    try:
        app = QApplication(sys.argv)
        
        from views.main_window import MainWindow
        
        window = MainWindow()
        print("✓ Main window created successfully")
        
        # Test dialog creation
        from views.roster_import_dialog import RosterImportDialog
        roster_dialog = RosterImportDialog(window)
        print("✓ Roster import dialog created successfully")
        
        from views.grade_import_dialog import GradeSheetImportDialog
        grade_dialog = GradeSheetImportDialog(window)
        print("✓ Grade import dialog created successfully")
        
        from views.coefficient_editor_dialog import CoefficientEditorDialog
        coeff_dialog = CoefficientEditorDialog(window)
        print("✓ Coefficient editor dialog created successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ UI test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("School OCR Demo - Test Suite")
    print("=" * 40)
    
    tests = [
        ("Import Tests", test_imports),
        ("Database Tests", test_database),
        ("UI Tests", test_ui)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 40)
    print("Test Results Summary:")
    
    all_passed = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n✓ All tests passed! The application should work correctly.")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
