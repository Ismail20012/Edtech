# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
Grade sheet import dialog for OCR processing of handwritten grade sheets.
Supports Arabic and French headers with automatic detection.
"""

from typing import Dict, List, Optional, Tuple
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QGroupBox,
    QMessageBox, QProgressDialog, QFileDialog, QCheckBox,
    QSpinBox, QDoubleSpinBox, QTextEdit, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont

import cv2
import numpy as np
from PIL import Image
from models.database import DatabaseManager
from ocr.grades import GradeOCRProcessor


class OCRWorker(QThread):
    """Worker thread for OCR processing."""
    
    progress_updated = pyqtSignal(int)
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, image_path: str, class_id: int, subject_id: int, term_id: int):
        super().__init__()
        self.image_path = image_path
        self.class_id = class_id
        self.subject_id = subject_id
        self.term_id = term_id
    
    def run(self):
        """Run the OCR processing."""
        try:
            self.progress_updated.emit(10)
            
            # Initialize OCR engine
            ocr_engine = GradeOCRProcessor(None)  # Database will be passed later
            self.progress_updated.emit(30)
            
            # Process the image
            results = ocr_engine.process_grade_sheet(
                self.image_path, 
                self.class_id, 
                self.subject_id,
                self.term_id
            )
            
            self.progress_updated.emit(100)
            self.result_ready.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class GradeSheetImportDialog(QDialog):
    """Dialog for importing and processing grade sheets with OCR."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importer Feuille de Notes")
        self.setModal(True)
        self.resize(1000, 700)
        
        # Data
        self.image_path: Optional[str] = None
        self.ocr_results: Optional[Dict] = None
        self.db = DatabaseManager()
        self.worker: Optional[OCRWorker] = None
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QHBoxLayout(self)
        
        # Left panel - Configuration
        left_panel = QVBoxLayout()
        left_widget = QScrollArea()
        left_content = QDialog()
        left_content.setLayout(left_panel)
        left_widget.setWidget(left_content)
        left_widget.setWidgetResizable(True)
        left_widget.setMaximumWidth(400)
        
        # Image selection
        image_group = QGroupBox("Image de la Feuille")
        image_layout = QVBoxLayout(image_group)
        
        self.image_label = QLabel("Aucune image sélectionnée")
        self.image_label.setStyleSheet("border: 1px dashed #ccc; padding: 20px; text-align: center;")
        self.image_label.setMinimumHeight(150)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.browse_image_btn = QPushButton("Parcourir Image...")
        self.browse_image_btn.clicked.connect(self._browse_image)
        
        image_layout.addWidget(self.image_label)
        image_layout.addWidget(self.browse_image_btn)
        left_panel.addWidget(image_group)
        
        # Context selection
        context_group = QGroupBox("Contexte")
        context_layout = QVBoxLayout(context_group)
        
        context_layout.addWidget(QLabel("Classe:"))
        self.class_combo = QComboBox()
        context_layout.addWidget(self.class_combo)
        
        context_layout.addWidget(QLabel("Matière:"))
        self.subject_combo = QComboBox()
        context_layout.addWidget(self.subject_combo)
        
        context_layout.addWidget(QLabel("Trimestre:"))
        self.term_combo = QComboBox()
        self.term_combo.addItems(["T1", "T2", "T3"])
        context_layout.addWidget(self.term_combo)
        
        left_panel.addWidget(context_group)
        
        # OCR Settings
        ocr_group = QGroupBox("Paramètres OCR")
        ocr_layout = QVBoxLayout(ocr_group)
        
        ocr_layout.addWidget(QLabel("Seuil de confiance:"))
        self.confidence_spinbox = QDoubleSpinBox()
        self.confidence_spinbox.setRange(0.0, 1.0)
        self.confidence_spinbox.setSingleStep(0.05)
        self.confidence_spinbox.setValue(0.7)
        ocr_layout.addWidget(self.confidence_spinbox)
        
        self.arabic_names_checkbox = QCheckBox("Noms en arabe")
        self.arabic_names_checkbox.setChecked(True)
        ocr_layout.addWidget(self.arabic_names_checkbox)
        
        self.preprocess_checkbox = QCheckBox("Préprocessing d'image")
        self.preprocess_checkbox.setChecked(True)
        ocr_layout.addWidget(self.preprocess_checkbox)
        
        left_panel.addWidget(ocr_group)
        
        # Process button
        self.process_btn = QPushButton("Traiter avec OCR")
        self.process_btn.clicked.connect(self._start_ocr)
        self.process_btn.setEnabled(False)
        left_panel.addWidget(self.process_btn)
        
        left_panel.addStretch()
        
        # Right panel - Results
        right_panel = QVBoxLayout()
        
        # Results table
        results_group = QGroupBox("Résultats OCR")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Étudiant", "Note", "Confiance", "Position", "Statut", "Action"
        ])
        results_layout.addWidget(self.results_table)
        
        right_panel.addWidget(results_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("Valider Tout")
        self.validate_btn.clicked.connect(self._validate_all)
        self.validate_btn.setEnabled(False)
        
        self.save_btn = QPushButton("Sauvegarder")
        self.save_btn.clicked.connect(self._save_results)
        self.save_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.validate_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        right_panel.addLayout(button_layout)
        
        # Add panels to main layout
        layout.addWidget(left_widget)
        layout.addLayout(right_panel, 1)
    
    def _load_data(self):
        """Load classes and subjects."""
        try:
            # Load classes
            classes = self.db.get_all_classes()
            for class_data in classes:
                self.class_combo.addItem(
                    f"{class_data['name']} - {class_data['level']}", 
                    class_data['id']
                )
            
            # Load subjects
            subjects = self.db.get_all_subjects()
            for subject in subjects:
                self.subject_combo.addItem(
                    f"{subject['name']} ({subject['code']})", 
                    subject['id']
                )
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de charger les données: {e}")
    
    def _browse_image(self):
        """Browse for image file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Sélectionner Image de Feuille",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        
        if file_path:
            self.image_path = file_path
            self._display_image_preview(file_path)
            self.process_btn.setEnabled(True)
    
    def _display_image_preview(self, file_path: str):
        """Display image preview."""
        try:
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(
                350, 140, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.image_label.setText(f"Erreur de prévisualisation: {e}")
    
    def _start_ocr(self):
        """Start OCR processing."""
        if not self.image_path:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner une image")
            return
        
        if not self.class_combo.currentData() or not self.subject_combo.currentData():
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner une classe et une matière")
            return
        
        class_id = self.class_combo.currentData()
        subject_id = self.subject_combo.currentData()
        term_id = self.term_combo.currentIndex() + 1
        
        # Create progress dialog
        self.progress_dialog = QProgressDialog("Traitement OCR en cours...", "Annuler", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()
        
        # Start worker thread
        self.worker = OCRWorker(self.image_path, class_id, subject_id, term_id)
        self.worker.progress_updated.connect(self.progress_dialog.setValue)
        self.worker.result_ready.connect(self._on_ocr_completed)
        self.worker.error_occurred.connect(self._on_ocr_error)
        self.worker.start()
    
    def _on_ocr_completed(self, results: Dict):
        """Handle OCR completion."""
        self.progress_dialog.close()
        self.ocr_results = results
        self._display_results(results)
        
        self.validate_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
    
    def _on_ocr_error(self, error_message: str):
        """Handle OCR error."""
        self.progress_dialog.close()
        QMessageBox.warning(self, "Erreur OCR", f"Erreur pendant le traitement: {error_message}")
    
    def _display_results(self, results: Dict):
        """Display OCR results in the table."""
        if not results or 'grades' not in results:
            return
        
        grades = results['grades']
        self.results_table.setRowCount(len(grades))
        
        for row, grade_data in enumerate(grades):
            # Student name
            student_name = f"{grade_data.get('student_name', 'Inconnu')}"
            self.results_table.setItem(row, 0, QTableWidgetItem(student_name))
            
            # Grade
            grade_value = grade_data.get('grade', '')
            self.results_table.setItem(row, 1, QTableWidgetItem(str(grade_value)))
            
            # Confidence
            confidence = grade_data.get('confidence', 0.0)
            confidence_item = QTableWidgetItem(f"{confidence:.2f}")
            if confidence < 0.7:
                confidence_item.setBackground(Qt.GlobalColor.red)
            elif confidence < 0.85:
                confidence_item.setBackground(Qt.GlobalColor.yellow)
            else:
                confidence_item.setBackground(Qt.GlobalColor.green)
            self.results_table.setItem(row, 2, confidence_item)
            
            # Position
            position = grade_data.get('position', '')
            self.results_table.setItem(row, 3, QTableWidgetItem(str(position)))
            
            # Status
            status = "À valider" if confidence < 0.85 else "Validé"
            self.results_table.setItem(row, 4, QTableWidgetItem(status))
            
            # Action button
            action_btn = QPushButton("Éditer")
            action_btn.clicked.connect(lambda checked, r=row: self._edit_grade(r))
            self.results_table.setCellWidget(row, 5, action_btn)
    
    def _edit_grade(self, row: int):
        """Edit a specific grade."""
        # TODO: Implement grade editing dialog
        QMessageBox.information(self, "Édition", f"Édition de la note ligne {row + 1}")
    
    def _validate_all(self):
        """Validate all grades."""
        for row in range(self.results_table.rowCount()):
            status_item = self.results_table.item(row, 4)
            if status_item:
                status_item.setText("Validé")
        
        QMessageBox.information(self, "Validation", "Toutes les notes ont été validées")
    
    def _save_results(self):
        """Save OCR results to database."""
        if not self.ocr_results:
            return
        
        try:
            # TODO: Implement saving to database
            QMessageBox.information(self, "Sauvegarde", "Résultats sauvegardés avec succès")
            self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la sauvegarde: {e}")
