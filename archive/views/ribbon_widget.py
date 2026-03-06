# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
Custom ribbon widget implementation for Microsoft Office-style interface.
"""

import os
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QToolButton, QTabWidget, 
    QFrame, QLabel, QSizePolicy, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QFont


class RibbonButton(QToolButton):
    """Custom button for ribbon interface with large icon and text below."""
    
    def __init__(self, text: str, icon_path: str = "", parent=None):
        super().__init__(parent)
        self.setText(text)
        # Increased size for better visibility
        self.setFixedSize(120, 90)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Set icon with fallback and better visibility
        if icon_path:
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                self.setIcon(icon)
                self.setIconSize(QSize(48, 48))  # Larger icons
            else:
                # Create a simple text-based icon if file doesn't exist
                pixmap = QPixmap(48, 48)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                painter.setPen(Qt.GlobalColor.darkGray)
                painter.setFont(QFont("Arial", 16))
                painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "📄")
                painter.end()
                self.setIcon(QIcon(pixmap))
                self.setIconSize(QSize(48, 48))
        
        # Set text below icon
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        
        # Better font settings for text visibility
        font = self.font()
        font.setPointSize(8)  # Readable font size
        font.setFamily("Segoe UI")
        font.setBold(False)
        self.setFont(font)
        
        # Enhanced styling with better contrast and visibility
        self.setStyleSheet("""
            QToolButton {
                border: 1px solid transparent;
                border-radius: 6px;
                padding: 8px 4px;
                background-color: transparent;
                color: #2d3748;
                font-size: 8pt;
                font-weight: 500;
                text-align: center;
            }
            QToolButton:hover {
                background-color: #e2e8f0;
                border: 1px solid #cbd5e0;
                color: #1a202c;
            }
            QToolButton:pressed {
                background-color: #cbd5e0;
                border: 1px solid #a0aec0;
                color: #1a202c;
            }
            QToolButton:disabled {
                color: #a0aec0;
                background-color: transparent;
            }
        """)


class RibbonGroup(QFrame):
    """A group of related controls within a ribbon tab."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        # Increased minimum width for better layout
        self.setMinimumWidth(180)
        self.setMaximumHeight(115)
        
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                margin: 2px;
                background-color: #ffffff;
            }
            QLabel {
                border: none;
                color: #666;
                font-size: 9pt;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 4)
        layout.setSpacing(2)
        
        # Content area for buttons
        self.content_widget = QWidget()
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(4)
        
        layout.addWidget(self.content_widget, 1)  # Give it stretch
        
        # Group title at bottom
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setMaximumHeight(14)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
    
    def add_button(self, button: RibbonButton) -> None:
        """Add a button to this group."""
        self.content_layout.addWidget(button)


class RibbonTab(QWidget):
    """A single tab in the ribbon containing groups of controls."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 8, 10, 8)
        self.layout.setSpacing(8)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        # Add stretch to push content to left
        self.layout.addStretch(1)
    
    def add_group(self, group: RibbonGroup) -> None:
        """Add a group to this tab."""
        # Insert before the stretch
        self.layout.insertWidget(self.layout.count() - 1, group)


class RibbonWidget(QFrame):
    """
    Main ribbon widget containing tabs and groups.
    Provides Microsoft Office-style interface.
    """
    
    # Signals
    action_triggered = pyqtSignal(str)  # Action name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(110)  # Proper height for ribbon
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-bottom: 1px solid #d0d0d0;
            }
        """)
        
        # --- MOD BEGIN: Ribbon Layout ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #f8f9fa;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                border: 1px solid #d0d0d0;
                border-bottom: none;
                padding: 6px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #f8f9fa;
                color: #1D6F42;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #dee2e6;
            }
        """)
        
        layout.addWidget(self.tab_widget)
        # --- MOD END ---
        
        # Store action buttons for enabling/disabling
        self.action_buttons: Dict[str, RibbonButton] = {}
        
        self._setup_tabs()
    
    def _setup_tabs(self) -> None:
        """Initialize all ribbon tabs and their groups."""
        # --- MOD BEGIN: Enhanced Ribbon for Grade Management ---
        
        # Roster Tab (Listes)
        roster_tab = RibbonTab()
        roster_group = RibbonGroup(self.tr("Listes"))
        
        import_roster_btn = RibbonButton(self.tr("Importer\nListe XLSX"), "resources/icons/upload.svg")
        import_roster_btn.clicked.connect(lambda: self.action_triggered.emit("import_roster"))
        roster_group.add_button(import_roster_btn)
        self.action_buttons["import_roster"] = import_roster_btn
        
        view_students_btn = RibbonButton(self.tr("Voir\nÉtudiants"), "resources/icons/review.svg")
        view_students_btn.clicked.connect(lambda: self.action_triggered.emit("view_students"))
        roster_group.add_button(view_students_btn)
        self.action_buttons["view_students"] = view_students_btn
        
        roster_tab.add_group(roster_group)
        self.tab_widget.addTab(roster_tab, self.tr("Listes"))
        
        # Grades Tab (Notes)
        grades_tab = RibbonTab()
        grades_group = RibbonGroup(self.tr("Notes"))
        
        import_grades_btn = RibbonButton(self.tr("Importer\nFeuille Notes"), "resources/icons/upload.svg")
        import_grades_btn.clicked.connect(lambda: self.action_triggered.emit("import_grades"))
        grades_group.add_button(import_grades_btn)
        self.action_buttons["import_grades"] = import_grades_btn
        
        validate_low_conf_btn = RibbonButton(self.tr("Valider\nConfiance Faible"), "resources/icons/review.svg")
        validate_low_conf_btn.clicked.connect(lambda: self.action_triggered.emit("validate_low_confidence"))
        grades_group.add_button(validate_low_conf_btn)
        self.action_buttons["validate_low_confidence"] = validate_low_conf_btn
        
        toggle_preview_btn = RibbonButton(self.tr("Aperçu\nOCR"), "resources/icons/review.svg")
        toggle_preview_btn.clicked.connect(lambda: self.action_triggered.emit("toggle_preview"))
        toggle_preview_btn.setEnabled(True)
        grades_group.add_button(toggle_preview_btn)
        self.action_buttons["toggle_preview"] = toggle_preview_btn
        
        grades_tab.add_group(grades_group)
        self.tab_widget.addTab(grades_tab, self.tr("Notes"))
        
        # Reports Tab (Rapports)
        reports_tab = RibbonTab()
        reports_group = RibbonGroup(self.tr("Rapports"))
        
        generate_workbook_btn = RibbonButton(self.tr("Générer\nClasseur"), "resources/icons/reports.svg")
        generate_workbook_btn.clicked.connect(lambda: self.action_triggered.emit("generate_workbook"))
        reports_group.add_button(generate_workbook_btn)
        self.action_buttons["generate_workbook"] = generate_workbook_btn
        
        open_output_btn = RibbonButton(self.tr("Ouvrir\nDossier"), "resources/icons/file.svg")
        open_output_btn.clicked.connect(lambda: self.action_triggered.emit("open_output_folder"))
        reports_group.add_button(open_output_btn)
        self.action_buttons["open_output_folder"] = open_output_btn
        
        reports_tab.add_group(reports_group)
        self.tab_widget.addTab(reports_tab, self.tr("Rapports"))
        
        # Settings Tab (Paramètres)
        settings_tab = RibbonTab()
        settings_group = RibbonGroup(self.tr("Configuration"))
        
        preferences_btn = RibbonButton(self.tr("Préférences"), "resources/icons/settings.svg")
        preferences_btn.clicked.connect(lambda: self.action_triggered.emit("preferences"))
        preferences_btn.setEnabled(True)
        settings_group.add_button(preferences_btn)
        self.action_buttons["preferences"] = preferences_btn
        
        coeff_btn = RibbonButton(self.tr("Coefficients"), "resources/icons/settings.svg")
        coeff_btn.clicked.connect(lambda: self.action_triggered.emit("edit_coefficients"))
        settings_group.add_button(coeff_btn)
        self.action_buttons["edit_coefficients"] = coeff_btn
        
        settings_tab.add_group(settings_group)
        self.tab_widget.addTab(settings_tab, self.tr("Paramètres"))
        # --- MOD END ---
    
    def enable_action(self, action_name: str, enabled: bool = True) -> None:
        """Enable or disable a specific action button."""
        if action_name in self.action_buttons:
            self.action_buttons[action_name].setEnabled(enabled)
    
    def get_action_button(self, action_name: str) -> Optional[RibbonButton]:
        """Get a specific action button by name."""
        return self.action_buttons.get(action_name)
