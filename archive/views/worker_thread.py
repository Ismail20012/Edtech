# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
Worker thread for background operations.
"""

from typing import List
from PyQt6.QtCore import QThread, pyqtSignal


class WorkerThread(QThread):
    """
    Background worker thread for OCR processing and other long-running tasks.
    Keeps the UI responsive during intensive operations.
    """
    
    # Signals
    progress_changed = pyqtSignal(int)
    processing_finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_paths: List[str] = []
        self._is_running = False
    
    def set_files(self, file_paths: List[str]) -> None:
        """Set the files to be processed."""
        self.file_paths = file_paths
    
    def run(self) -> None:
        """
        Main thread execution method.
        Now includes real OCR processing integration.
        """
        self._is_running = True
        try:
            total_files = len(self.file_paths)
            results = []
            
            for i, file_path in enumerate(self.file_paths):
                if not self._is_running:
                    break
                
                try:
                    # Import here to avoid circular imports
                    from ocr.engine import run_ocr
                    from ocr.preprocess import preprocess_image
                    
                    # Preprocess the image
                    print(f"Preprocessing {file_path}")
                    preprocessed_image = preprocess_image(file_path)
                    
                    # Run OCR on the file
                    print(f"Running OCR on {file_path}")
                    ocr_data = run_ocr(file_path)
                    
                    # Process OCR results (simplified for now)
                    if ocr_data and 'text' in ocr_data:
                        text_count = len([text for text in ocr_data['text'] if text.strip()])
                        result = f"✓ {file_path}: Found {text_count} text elements"
                    else:
                        result = f"⚠ {file_path}: No text found"
                    
                    results.append(result)
                    print(result)
                    
                except Exception as e:
                    error_msg = f"✗ Error processing {file_path}: {str(e)}"
                    results.append(error_msg)
                    print(error_msg)
                
                # Emit progress
                progress = int((i + 1) / total_files * 100)
                self.progress_changed.emit(progress)
                
                # Small delay to show progress and prevent UI blocking
                self.msleep(200)
            
            if self._is_running:
                self.processing_finished.emit(results)
                
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self._is_running = False
    
    def stop(self) -> None:
        """Stop the worker thread gracefully."""
        self._is_running = False
        self.quit()
        self.wait()
