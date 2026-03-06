# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
Main controller for the application.
Connects the ribbon GUI to the OCR engine and database.
Updated to work with the new ribbon interface.
"""

from typing import List
from PyQt6.QtCore import QObject, QRunnable, QThreadPool
from ocr.preprocess import preprocess_image, deskew_image
from ocr.engine import run_ocr
from models.database import open_database, create_and_seed_database


class OcrWorker(QRunnable):
    """Runnable worker for performing OCR in a separate thread."""
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self) -> None:
        """Execute the OCR task."""
        try:
            preprocessed_image = preprocess_image(self.file_path)
            # In a real app, you would save and use the deskewed image
            # deskewed_image = deskew_image(preprocessed_image)
            print(f"OCR processing would run on {self.file_path}")
        except Exception as e:
            print(f"Error processing {self.file_path}: {e}")


class MainController(QObject):
    """
    Main application controller.
    Updated to work with the new ribbon-based MainWindow.
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.thread_pool = QThreadPool()

        # --- MOD BEGIN: Updated Signal Connections ---
        # Connect signals from the new ribbon-based window
        self.main_window.files_selected.connect(self.handle_files_selected)
        self.main_window.processing_started.connect(self.handle_processing_started)
        self.main_window.processing_finished.connect(self.handle_processing_finished)
        # --- MOD END ---

        # Initialize the database
        self.db = open_database()
        create_and_seed_database(self.db)

    def handle_files_selected(self, file_paths: List[str]) -> None:
        """Handle when files are selected in the ribbon interface."""
        # --- MOD BEGIN: File Selection Handler ---
        print(f"Files selected: {len(file_paths)} files")
        # Enable processing button in ribbon
        self.main_window.ribbon.enable_action("start_processing", True)
        # --- MOD END ---

    def handle_processing_started(self) -> None:
        """Handle when OCR processing starts."""
        # --- MOD BEGIN: Processing Start Handler ---
        print("OCR processing started")
        # Could add any additional setup here
        # --- MOD END ---

    def handle_processing_finished(self) -> None:
        """Handle when OCR processing is completed."""
        # --- MOD BEGIN: Processing Finish Handler ---
        print("OCR processing finished")
        # Enable report generation in ribbon
        self.main_window.ribbon.enable_action("generate_report", True)
        # --- MOD END ---

    def start_ocr_processing(self, file_paths: List[str]) -> None:
        """
        Starts the OCR processing in a background thread.
        Legacy method - kept for compatibility.
        """
        # --- MOD BEGIN: Legacy OCR Processing ---
        for file_path in file_paths:
            worker = OcrWorker(file_path)
            self.thread_pool.start(worker)
        
        print(f"Started OCR processing for {len(file_paths)} files")
        # --- MOD END ---