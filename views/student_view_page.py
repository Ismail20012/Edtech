# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
Student view page for browsing student data and generating reports.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton
from PyQt6.QtCore import pyqtSignal

class StudentViewPage(QWidget):
    """Widget for the student data browsing page."""
    back_to_upload = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.student_list = QListWidget()
        layout.addWidget(self.student_list)

        self.generate_report_button = QPushButton(self.tr("Generate PDF Report"))
        layout.addWidget(self.generate_report_button)

        self.back_button = QPushButton(self.tr("Back to Upload"))
        self.back_button.clicked.connect(self.back_to_upload.emit)
        layout.addWidget(self.back_button)
