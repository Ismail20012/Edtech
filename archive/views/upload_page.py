# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
DEPRECATED: Upload page for selecting and processing images.
This component has been replaced by the ribbon interface in MainWindow.
Kept for reference only.
"""

# --- MOD BEGIN: Deprecation Notice ---
import warnings
warnings.warn(
    "UploadPage is deprecated. Upload functionality is now integrated into the ribbon interface.",
    DeprecationWarning,
    stacklevel=2
)
# --- MOD END ---

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QProgressBar, QLabel, 
    QHBoxLayout, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap

class UploadPage(QWidget):
    """
    DEPRECATED: Widget for the upload and processing page.
    Upload functionality has been moved to the ribbon interface.
    """
    files_selected = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- DEPRECATED NOTICE ---
        deprecated_label = QLabel(self.tr("⚠️ This page is deprecated. Use the ribbon interface instead."))
        deprecated_label.setStyleSheet("color: red; font-weight: bold; font-size: 12pt;")
        deprecated_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(deprecated_label)

        # Title and Info
        title_label = QLabel(self.tr("Grade Sheet OCR"))
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        info_label = QLabel(self.tr("Upload scanned grade sheets to extract student data."))
        info_label.setObjectName("infoLabel")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(info_label)

        # Upload Area
        upload_frame = QFrame()
        upload_frame.setObjectName("uploadFrame")
        upload_layout = QVBoxLayout(upload_frame)
        upload_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(upload_frame)

        # Placeholder for an icon
        # In a real app, you would use a proper icon
        icon_label = QLabel()
        # Create a dummy pixmap for the icon
        pixmap = QPixmap(128, 128)
        pixmap.fill(Qt.GlobalColor.transparent)
        icon_label.setPixmap(pixmap)
        upload_layout.addWidget(icon_label)

        self.upload_button = QPushButton(self.tr("Select Files to Upload"))
        self.upload_button.clicked.connect(self.upload_files)
        upload_layout.addWidget(self.upload_button)

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        main_layout.addWidget(self.progress_bar)

    def upload_files(self):
        """Opens a file dialog to select images and emits a signal with the file paths."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, self.tr("Select Grade Sheets"), "", self.tr("Images (*.png *.jpg)")
        )
        if file_paths:
            self.files_selected.emit(file_paths)
