# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
Coefficient editor dialog for managing subject coefficients per class and term.
"""

from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QGroupBox,
    QMessageBox, QDoubleSpinBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from models.database import DatabaseManager


class CoefficientEditorDialog(QDialog):
    """Dialog for editing subject coefficients."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Édition des Coefficients")
        self.setModal(True)
        self.resize(800, 600)
        
        # Data
        self.db = DatabaseManager()
        self.current_class_id: Optional[int] = None
        self.current_term_id: Optional[int] = None
        self.coefficients: Dict = {}
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Context selection
        context_group = QGroupBox("Contexte")
        context_layout = QHBoxLayout(context_group)
        
        context_layout.addWidget(QLabel("Classe:"))
        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self._on_class_changed)
        context_layout.addWidget(self.class_combo)
        
        context_layout.addWidget(QLabel("Trimestre:"))
        self.term_combo = QComboBox()
        self.term_combo.addItems(["T1", "T2", "T3"])
        self.term_combo.currentIndexChanged.connect(self._on_term_changed)
        context_layout.addWidget(self.term_combo)
        
        context_layout.addStretch()
        layout.addWidget(context_group)
        
        # Coefficients table
        table_group = QGroupBox("Coefficients par Matière")
        table_layout = QVBoxLayout(table_group)
        
        self.coeff_table = QTableWidget()
        self.coeff_table.setColumnCount(4)
        self.coeff_table.setHorizontalHeaderLabels([
            "Matière", "Code", "Coefficient", "Description"
        ])
        
        # Set column widths
        header = self.coeff_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        table_layout.addWidget(self.coeff_table)
        layout.addWidget(table_group)
        
        # Actions
        action_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Réinitialiser")
        self.reset_btn.clicked.connect(self._reset_coefficients)
        
        self.apply_template_btn = QPushButton("Appliquer Modèle")
        self.apply_template_btn.clicked.connect(self._apply_template)
        
        action_layout.addWidget(self.reset_btn)
        action_layout.addWidget(self.apply_template_btn)
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Sauvegarder")
        self.save_btn.clicked.connect(self._save_coefficients)
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _load_data(self):
        """Load classes and initialize data."""
        try:
            # Load classes
            classes = self.db.get_all_classes()
            for class_data in classes:
                self.class_combo.addItem(
                    f"{class_data['name']} - {class_data['level']}", 
                    class_data['id']
                )
            
            # Set initial values
            if self.class_combo.count() > 0:
                self.current_class_id = self.class_combo.itemData(0)
                self.current_term_id = 1
                self._load_coefficients()
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de charger les données: {e}")
    
    def _on_class_changed(self):
        """Handle class selection change."""
        self.current_class_id = self.class_combo.currentData()
        if self.current_class_id:
            self._load_coefficients()
    
    def _on_term_changed(self):
        """Handle term selection change."""
        self.current_term_id = self.term_combo.currentIndex() + 1
        if self.current_class_id:
            self._load_coefficients()
    
    def _load_coefficients(self):
        """Load coefficients for current class and term."""
        if not self.current_class_id or not self.current_term_id:
            return
        
        try:
            # Load subjects and their coefficients
            subjects = self.db.get_all_subjects()
            coefficients = self.db.get_coefficients(self.current_class_id, self.current_term_id)
            
            # Create coefficient lookup
            coeff_lookup = {c['subject_id']: c['coefficient'] for c in coefficients}
            
            # Populate table
            self.coeff_table.setRowCount(len(subjects))
            
            for row, subject in enumerate(subjects):
                # Subject name
                name_item = QTableWidgetItem(subject['name'])
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.coeff_table.setItem(row, 0, name_item)
                
                # Subject code
                code_item = QTableWidgetItem(subject['code'])
                code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.coeff_table.setItem(row, 1, code_item)
                
                # Coefficient (editable)
                current_coeff = coeff_lookup.get(subject['id'], 1.0)
                coeff_spinbox = QDoubleSpinBox()
                coeff_spinbox.setRange(0.0, 10.0)
                coeff_spinbox.setSingleStep(0.5)
                coeff_spinbox.setValue(current_coeff)
                coeff_spinbox.setDecimals(1)
                self.coeff_table.setCellWidget(row, 2, coeff_spinbox)
                
                # Description
                desc_item = QTableWidgetItem(subject.get('description', ''))
                desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.coeff_table.setItem(row, 3, desc_item)
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de charger les coefficients: {e}")
    
    def _reset_coefficients(self):
        """Reset all coefficients to 1.0."""
        reply = QMessageBox.question(
            self, 
            "Confirmation", 
            "Réinitialiser tous les coefficients à 1.0 ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for row in range(self.coeff_table.rowCount()):
                spinbox = self.coeff_table.cellWidget(row, 2)
                if spinbox:
                    spinbox.setValue(1.0)
    
    def _apply_template(self):
        """Apply a predefined coefficient template."""
        # Default Moroccan coefficient template
        template_coeffs = {
            "MAT": 3.0,  # Mathematics
            "PC": 2.0,   # Physics/Chemistry
            "SN": 2.0,   # Natural Sciences
            "AR": 2.0,   # Arabic
            "FR": 2.0,   # French
            "ANG": 1.0,  # English
            "HG": 1.0,   # History/Geography
            "IR": 1.0,   # Islamic Religion
            "IC": 1.0,   # Islamic Culture
            "PH": 1.0    # Philosophy
        }
        
        reply = QMessageBox.question(
            self, 
            "Confirmation", 
            "Appliquer le modèle de coefficients marocain standard ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for row in range(self.coeff_table.rowCount()):
                code_item = self.coeff_table.item(row, 1)
                if code_item:
                    code = code_item.text()
                    if code in template_coeffs:
                        spinbox = self.coeff_table.cellWidget(row, 2)
                        if spinbox:
                            spinbox.setValue(template_coeffs[code])
    
    def _save_coefficients(self):
        """Save coefficients to database."""
        if not self.current_class_id or not self.current_term_id:
            return
        
        try:
            coefficients_data = []
            
            for row in range(self.coeff_table.rowCount()):
                # Get subject ID from database based on code
                code_item = self.coeff_table.item(row, 1)
                spinbox = self.coeff_table.cellWidget(row, 2)
                
                if code_item and spinbox:
                    subject_code = code_item.text()
                    coefficient = spinbox.value()
                    
                    # Find subject ID
                    subjects = self.db.get_all_subjects()
                    subject_id = None
                    for subject in subjects:
                        if subject['code'] == subject_code:
                            subject_id = subject['id']
                            break
                    
                    if subject_id:
                        coefficients_data.append({
                            'class_id': self.current_class_id,
                            'subject_id': subject_id,
                            'term_id': self.current_term_id,
                            'coefficient': coefficient
                        })
            
            # Save to database
            self.db.save_coefficients(coefficients_data)
            
            QMessageBox.information(self, "Succès", "Coefficients sauvegardés avec succès")
            self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la sauvegarde: {e}")
