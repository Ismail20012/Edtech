# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
Roster import dialog for importing student lists from Excel files.
Supports Arabic and French names with proper mapping.
"""

from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QGroupBox,
    QMessageBox, QProgressDialog, QFileDialog, QSpinBox, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

import pandas as pd
from models.database import DatabaseManager
from importers.roster_xlsx import RosterImporter


class ImportWorker(QThread):
    """Worker thread for importing roster data."""
    
    progress_updated = pyqtSignal(int)
    import_completed = pyqtSignal(bool, str)
    
    def __init__(self, file_path: str, class_id: int, mapping: Dict[str, str]):
        super().__init__()
        self.file_path = file_path
        self.class_id = class_id
        self.mapping = mapping
    
    def run(self):
        """Run the import process."""
        try:
            importer = RosterImporter()
            
            # Load Excel file
            self.progress_updated.emit(10)
            df = pd.read_excel(self.file_path)
            
            # Process with mapping
            self.progress_updated.emit(30)
            success = importer.import_roster(df, self.class_id, self.mapping)
            
            self.progress_updated.emit(100)
            
            if success:
                self.import_completed.emit(True, "Import terminé avec succès")
            else:
                self.import_completed.emit(False, "Erreur lors de l'import")
                
        except Exception as e:
            self.import_completed.emit(False, f"Erreur: {str(e)}")


class RosterImportDialog(QDialog):
    """Dialog for importing student rosters from Excel files."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importer Liste d'Étudiants")
        self.setModal(True)
        self.resize(800, 600)
        
        # Data
        self.file_path: Optional[str] = None
        self.df: Optional[pd.DataFrame] = None
        self.db = DatabaseManager()
        self.worker: Optional[ImportWorker] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # File selection
        file_group = QGroupBox("Fichier Excel")
        file_layout = QHBoxLayout(file_group)
        
        self.file_label = QLabel("Aucun fichier sélectionné")
        self.browse_btn = QPushButton("Parcourir...")
        self.browse_btn.clicked.connect(self._browse_file)
        
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(self.browse_btn)
        layout.addWidget(file_group)
        
        # Class selection - Allow user to enter class name
        class_group = QGroupBox("Classe de Destination")
        class_layout = QVBoxLayout(class_group)
        
        class_layout.addWidget(QLabel("Nom de la Classe:"))
        self.class_name_input = QLineEdit()
        self.class_name_input.setPlaceholderText("Ex: 3A, 4B, 5C...")
        class_layout.addWidget(self.class_name_input)
        
        class_layout.addWidget(QLabel("Niveau:"))
        self.level_input = QLineEdit()
        self.level_input.setPlaceholderText("Ex: 3ème Année, 4ème Année...")
        class_layout.addWidget(self.level_input)
        
        layout.addWidget(class_group)
        
        # Column mapping
        mapping_group = QGroupBox("Mapping des Colonnes")
        mapping_layout = QVBoxLayout(mapping_group)
        
        # Mapping table
        self.mapping_table = QTableWidget(4, 2)
        self.mapping_table.setHorizontalHeaderLabels(["Champ", "Colonne Excel"])
        
        # Default mappings - Updated fields as requested
        fields = ["Nom (Arabe)", "NNI (ID)", "Date de Naissance", "Lieu de Naissance"]
        for i, field in enumerate(fields):
            self.mapping_table.setItem(i, 0, QTableWidgetItem(field))
            combo = QComboBox()
            combo.addItem("-- Sélectionner --")
            self.mapping_table.setCellWidget(i, 1, combo)
        
        mapping_layout.addWidget(self.mapping_table)
        layout.addWidget(mapping_group)
        
        # Preview
        preview_group = QGroupBox("Aperçu des Données")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(200)
        preview_layout.addWidget(self.preview_table)
        
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Aperçu")
        self.preview_btn.clicked.connect(self._preview_data)
        self.preview_btn.setEnabled(False)
        
        self.import_btn = QPushButton("Importer")
        self.import_btn.clicked.connect(self._start_import)
        self.import_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _browse_file(self):
        """Browse for Excel file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Sélectionner Fichier Excel",
            "",
            "Fichiers Excel (*.xlsx *.xls)"
        )
        
        if file_path:
            self.file_path = file_path
            self.file_label.setText(file_path.split('/')[-1])
            self._load_excel_columns()
    
    def _load_excel_columns(self):
        """Load columns from the Excel file."""
        try:
            self.df = pd.read_excel(self.file_path, nrows=5)  # Preview only
            columns = ["-- Sélectionner --"] + list(self.df.columns)
            
            # Update column mapping combos
            for row in range(self.mapping_table.rowCount()):
                combo = self.mapping_table.cellWidget(row, 1)
                combo.clear()
                combo.addItems(columns)
            
            self.preview_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de lire le fichier Excel: {e}")
    
    def _preview_data(self):
        """Preview the imported data."""
        if not self.df is not None:
            return
        
        # Get mapping
        mapping = self._get_column_mapping()
        if not any(mapping.values()):
            QMessageBox.warning(self, "Erreur", "Veuillez mapper au moins une colonne")
            return
        
        # Setup preview table
        self.preview_table.setRowCount(min(10, len(self.df)))
        self.preview_table.setColumnCount(len(mapping))
        self.preview_table.setHorizontalHeaderLabels(list(mapping.keys()))
        
        # Fill preview data
        for row in range(min(10, len(self.df))):
            for col, (field, excel_col) in enumerate(mapping.items()):
                if excel_col and excel_col in self.df.columns:
                    value = str(self.df.iloc[row][excel_col])
                    self.preview_table.setItem(row, col, QTableWidgetItem(value))
        
        self.import_btn.setEnabled(True)
    
    def _get_column_mapping(self) -> Dict[str, str]:
        """Get the column mapping from the UI."""
        mapping = {}
        field_names = ["arabic_name", "nni_id", "date_of_birth", "place_of_birth"]
        
        for row in range(self.mapping_table.rowCount()):
            field = field_names[row]
            combo = self.mapping_table.cellWidget(row, 1)
            excel_col = combo.currentText()
            if excel_col != "-- Sélectionner --":
                mapping[field] = excel_col
        
        return mapping
    
    def _start_import(self):
        """Start the import process."""
        if not self.class_name_input.text().strip():
            QMessageBox.warning(self, "Erreur", "Veuillez saisir le nom de la classe")
            return
        
        if not self.level_input.text().strip():
            QMessageBox.warning(self, "Erreur", "Veuillez saisir le niveau de la classe")
            return
        
        # Create or get class
        try:
            class_name = self.class_name_input.text().strip()
            level = self.level_input.text().strip()
            
            # Check if class already exists
            existing_classes = self.db.execute_query(
                "SELECT id FROM CLASSES WHERE name = ? AND level = ?", 
                (class_name, level)
            )
            
            if existing_classes:
                class_id = existing_classes[0]['id']
            else:
                # Create new class
                self.db.execute_query(
                    "INSERT INTO CLASSES (name, level, academic_year) VALUES (?, ?, ?)",
                    (class_name, level, "2024-2025")
                )
                # Get the new class ID
                new_classes = self.db.execute_query(
                    "SELECT id FROM CLASSES WHERE name = ? AND level = ? ORDER BY id DESC LIMIT 1",
                    (class_name, level)
                )
                class_id = new_classes[0]['id']
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la création de la classe: {e}")
            return
        
        mapping = self._get_column_mapping()
        
        # Create progress dialog
        self.progress_dialog = QProgressDialog("Import en cours...", "Annuler", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()
        
        # Start worker thread
        self.worker = ImportWorker(self.file_path, class_id, mapping)
        self.worker.progress_updated.connect(self.progress_dialog.setValue)
        self.worker.import_completed.connect(self._on_import_completed)
        self.worker.start()
    
    def _on_import_completed(self, success: bool, message: str):
        """Handle import completion."""
        self.progress_dialog.close()
        
        if success:
            QMessageBox.information(self, "Succès", message)
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", message)
