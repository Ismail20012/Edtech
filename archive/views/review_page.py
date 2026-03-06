# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
Review page for viewing and editing OCR results.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QPushButton
from PyQt6.QtCore import pyqtSignal

class ReviewPage(QWidget):
    """Widget for the data review page."""
    navigate_to_student_view = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.table = QTableWidget(10, 5)  # Example size
        self.table.setHorizontalHeaderLabels([self.tr("Student"), self.tr("Subject"), self.tr("Grade"), self.tr("Confidence"), self.tr("Actions")])
        layout.addWidget(self.table)

        self.save_button = QPushButton(self.tr("Save and View Students"))
        self.save_button.clicked.connect(self.navigate_to_student_view.emit)
        layout.addWidget(self.save_button)
