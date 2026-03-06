# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
Preferences dialog for application settings.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QPushButton, QLabel, QComboBox, QCheckBox, QSpinBox,
    QLineEdit, QGroupBox, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt


class PreferencesDialog(QDialog):
    """Preferences dialog for application configuration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Preferences"))
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self) -> None:
        """Setup the preferences dialog UI."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # General tab
        general_tab = self._create_general_tab()
        tab_widget.addTab(general_tab, self.tr("General"))
        
        # OCR tab
        ocr_tab = self._create_ocr_tab()
        tab_widget.addTab(ocr_tab, self.tr("OCR Settings"))
        
        # UI tab
        ui_tab = self._create_ui_tab()
        tab_widget.addTab(ui_tab, self.tr("Interface"))
        
        layout.addWidget(tab_widget)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _create_general_tab(self) -> QWidget:
        """Create the general preferences tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Language settings
        lang_group = QGroupBox(self.tr("Language"))
        lang_layout = QFormLayout(lang_group)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            self.tr("English"), 
            self.tr("Français"),
            self.tr("العربية")
        ])
        lang_layout.addRow(self.tr("Interface Language:"), self.language_combo)
        
        layout.addWidget(lang_group)
        
        # Auto-save settings
        save_group = QGroupBox(self.tr("Auto-Save"))
        save_layout = QFormLayout(save_group)
        
        self.auto_save_check = QCheckBox(self.tr("Enable auto-save"))
        self.auto_save_check.setChecked(True)
        save_layout.addRow(self.auto_save_check)
        
        self.save_interval = QSpinBox()
        self.save_interval.setRange(1, 60)
        self.save_interval.setValue(5)
        self.save_interval.setSuffix(self.tr(" minutes"))
        save_layout.addRow(self.tr("Save interval:"), self.save_interval)
        
        layout.addWidget(save_group)
        layout.addStretch()
        
        return widget
    
    def _create_ocr_tab(self) -> QWidget:
        """Create the OCR settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tesseract settings
        tesseract_group = QGroupBox(self.tr("Tesseract Configuration"))
        tesseract_layout = QFormLayout(tesseract_group)
        
        self.tesseract_path = QLineEdit()
        self.tesseract_path.setPlaceholderText("C:/Program Files/Tesseract-OCR/tesseract.exe")
        tesseract_layout.addRow(self.tr("Tesseract Path:"), self.tesseract_path)
        
        layout.addWidget(tesseract_group)
        
        # OCR languages
        lang_group = QGroupBox(self.tr("OCR Languages"))
        lang_layout = QVBoxLayout(lang_group)
        
        self.french_check = QCheckBox(self.tr("French (fra)"))
        self.french_check.setChecked(True)
        lang_layout.addWidget(self.french_check)
        
        self.arabic_check = QCheckBox(self.tr("Arabic (ara)"))
        self.arabic_check.setChecked(True)
        lang_layout.addWidget(self.arabic_check)
        
        self.english_check = QCheckBox(self.tr("English (eng)"))
        lang_layout.addWidget(self.english_check)
        
        layout.addWidget(lang_group)
        
        # Processing settings
        proc_group = QGroupBox(self.tr("Processing"))
        proc_layout = QFormLayout(proc_group)
        
        self.confidence_threshold = QSpinBox()
        self.confidence_threshold.setRange(0, 100)
        self.confidence_threshold.setValue(80)
        self.confidence_threshold.setSuffix("%")
        proc_layout.addRow(self.tr("Confidence Threshold:"), self.confidence_threshold)
        
        layout.addWidget(proc_group)
        layout.addStretch()
        
        return widget
    
    def _create_ui_tab(self) -> QWidget:
        """Create the UI preferences tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Theme settings
        theme_group = QGroupBox(self.tr("Appearance"))
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            self.tr("Light Theme"),
            self.tr("Dark Theme"),
            self.tr("Auto (System)")
        ])
        theme_layout.addRow(self.tr("Theme:"), self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # Window settings
        window_group = QGroupBox(self.tr("Window"))
        window_layout = QVBoxLayout(window_group)
        
        self.remember_size = QCheckBox(self.tr("Remember window size and position"))
        self.remember_size.setChecked(True)
        window_layout.addWidget(self.remember_size)
        
        self.start_maximized = QCheckBox(self.tr("Start maximized"))
        window_layout.addWidget(self.start_maximized)
        
        layout.addWidget(window_group)
        layout.addStretch()
        
        return widget
    
    def _load_settings(self) -> None:
        """Load current settings into the dialog."""
        # This would load from a config file in a real implementation
        pass
    
    def get_settings(self) -> dict:
        """Get the current settings from the dialog."""
        return {
            'language': self.language_combo.currentText(),
            'auto_save': self.auto_save_check.isChecked(),
            'save_interval': self.save_interval.value(),
            'tesseract_path': self.tesseract_path.text(),
            'ocr_languages': {
                'french': self.french_check.isChecked(),
                'arabic': self.arabic_check.isChecked(),
                'english': self.english_check.isChecked(),
            },
            'confidence_threshold': self.confidence_threshold.value(),
            'theme': self.theme_combo.currentText(),
            'remember_size': self.remember_size.isChecked(),
            'start_maximized': self.start_maximized.isChecked(),
        }
