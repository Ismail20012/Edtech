# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
Main entry point for the School OCR Demo application.
Updated to support the new ribbon interface and resource loading.
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTranslator, QLocale, QLibraryInfo
from views.main_window import MainWindow
from controllers.main_controller import MainController


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for both dev and PyInstaller bundle."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def setup_translations(app: QApplication) -> None:
    """Setup application translations - Default to French."""
    # --- MOD BEGIN: French Default Translation Setup ---
    # Force French locale
    locale = QLocale(QLocale.Language.French, QLocale.Country.France)
    QLocale.setDefault(locale)
    
    translator = QTranslator()
    
    # Try to load French translations
    translation_path = get_resource_path("i18n")
    if os.path.exists(translation_path):
        # First try to load compiled .qm file
        translation_file = os.path.join(translation_path, "qt_fr.qm")
        if os.path.exists(translation_file):
            if translator.load(translation_file):
                app.installTranslator(translator)
                print("Translations françaises (.qm) chargées avec succès")
                return
        
        # Try alternative loading methods for .ts file
        # Method 1: Load with base name
        if translator.load("qt_fr", translation_path):
            app.installTranslator(translator)
            print("Translations françaises chargées avec succès (méthode 1)")
            return
            
        # Method 2: Load with full path
        ts_file = os.path.join(translation_path, "qt_fr.ts")
        if os.path.exists(ts_file):
            if translator.load(ts_file):
                app.installTranslator(translator)
                print("Translations françaises chargées avec succès (méthode 2)")
                return
    
    print("Attention: Impossible de charger les traductions françaises - utilisation de l'anglais par défaut")
    # --- MOD END ---


def load_stylesheet(app: QApplication) -> None:
    """Load and apply the application stylesheet."""
    # --- MOD BEGIN: Stylesheet Loading ---
    try:
        style_path = get_resource_path("views/styles.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        else:
            print(f"Warning: Stylesheet not found at {style_path}")
    except Exception as e:
        print(f"Error loading stylesheet: {e}")
    # --- MOD END ---


def main():
    """Initializes and runs the application with ribbon interface."""
    # --- MOD BEGIN: Enhanced Application Setup ---
    app = QApplication(sys.argv)
    app.setApplicationName("School OCR Demo")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Gemini Project")
    
    # Setup translations
    setup_translations(app)
    
    # Load stylesheet
    load_stylesheet(app)
    
    # Create main window with ribbon interface
    main_window = MainWindow()
    
    # Create controller to handle business logic
    controller = MainController(main_window)
    
    # Show window and start event loop
    main_window.show()
    
    sys.exit(app.exec())
    # --- MOD END ---


if __name__ == "__main__":
    main()
