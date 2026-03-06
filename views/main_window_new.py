# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
Main window with Microsoft Office-style ribbon interface.
Enhanced for Moroccan school grade management system.
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QTableView, QTreeView, 
    QDockWidget, QFileDialog, QProgressBar, QLabel, QMessageBox,
    QSplitter, QFrame, QHBoxLayout, QDialog, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex
from PyQt6.QtGui import QIcon, QStandardItemModel, QStandardItem
from .ribbon_widget import RibbonWidget
from .worker_thread import WorkerThread
from .preferences_dialog import PreferencesDialog


class MainWindow(QMainWindow):
    """
    Main application window with ribbon interface.
    Provides modern Microsoft Office-style UI for grade sheet processing.
    """
    
    # Signals
    files_selected = pyqtSignal(list)
    processing_started = pyqtSignal()
    processing_finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("Démo OCR Scolaire"))
        self.setGeometry(100, 100, 1400, 900)
        
        # --- MOD BEGIN: Enhanced Window Setup ---
        # Current context tracking
        self.current_term_id = 1  # Default to T1
        self.current_class_id = None
        self.current_subject_id = None
        
        # Worker thread for background processing
        self.worker_thread: Optional[WorkerThread] = None
        self.selected_files: List[str] = []
        
        # Setup UI components
        self._setup_ribbon()
        self._setup_central_widget()
        self._setup_dock_widgets()
        self._setup_status_bar()
        self._setup_navigation_tree()
        self._connect_signals()
        # --- MOD END ---
    
    def _setup_ribbon(self) -> None:
        """Initialize the ribbon interface."""
        # --- MOD BEGIN: Ribbon Setup ---
        self.ribbon = RibbonWidget(self)
        
        # Create a container widget for the ribbon and central area
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Add ribbon to the top
        main_layout.addWidget(self.ribbon)
        
        # Create splitter for main content
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        self.setCentralWidget(main_widget)
        # --- MOD END ---
    
    def _setup_central_widget(self) -> None:
        """Setup the central widget with table and tree views."""
        # --- MOD BEGIN: Enhanced Central Widget ---
        # Left tree view for navigation
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setMaximumWidth(300)
        self.tree_view.setMinimumWidth(200)
        
        # Central table view
        self.table_view = QTableView()
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels([
            self.tr("Étudiant"), self.tr("Matière"), self.tr("Note"), 
            self.tr("Confiance"), self.tr("Statut")
        ])
        
        self.table_view.setModel(self.table_model)
        self.table_view.setSortingEnabled(True)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        
        # Add to splitter
        self.main_splitter.addWidget(self.tree_view)
        self.main_splitter.addWidget(self.table_view)
        self.main_splitter.setSizes([200, 1000])  # Initial sizes
        # --- MOD END ---
    
    def _setup_dock_widgets(self) -> None:
        """Setup the right-side preview dock widget."""
        # --- MOD BEGIN: Dock Widget Setup ---
        self.preview_dock = QDockWidget(self.tr("Aperçu OCR"), self)
        self.preview_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        
        # Preview content widget
        preview_widget = QFrame()
        preview_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        preview_widget.setMinimumWidth(300)
        
        preview_layout = QVBoxLayout(preview_widget)
        self.preview_label = QLabel(self.tr("L'aperçu OCR apparaîtra ici"))
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("color: #666; font-style: italic;")
        preview_layout.addWidget(self.preview_label)
        
        self.preview_dock.setWidget(preview_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.preview_dock)
        
        # Hide by default
        self.preview_dock.hide()
        # --- MOD END ---
    
    def _setup_navigation_tree(self) -> None:
        """Setup the navigation tree with Class > Trimester > Subject structure."""
        # --- MOD BEGIN: Navigation Tree Setup ---
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels([self.tr("Navigation")])
        
        # Sample tree structure: Class > Trimester > Subject
        class_3a = QStandardItem("3A")
        class_3a.setData("class", Qt.ItemDataRole.UserRole)
        class_3a.setData(1, Qt.ItemDataRole.UserRole + 1)  # class_id
        
        # Add trimesters
        for term_id, term_label in [(1, "T1"), (2, "T2"), (3, "T3")]:
            term_item = QStandardItem(term_label)
            term_item.setData("term", Qt.ItemDataRole.UserRole)
            term_item.setData(term_id, Qt.ItemDataRole.UserRole + 1)
            
            # Add subjects (placeholders)
            subjects = ["MAT", "PC", "SN", "AR", "FR", "ANG", "HG", "IR", "IC", "PH"]
            for i, subject_code in enumerate(subjects, 1):
                subject_item = QStandardItem(subject_code)
                subject_item.setData("subject", Qt.ItemDataRole.UserRole)
                subject_item.setData(i, Qt.ItemDataRole.UserRole + 1)  # subject_id
                term_item.appendRow(subject_item)
            
            class_3a.appendRow(term_item)
        
        self.tree_model.appendRow(class_3a)
        self.tree_view.setModel(self.tree_model)
        self.tree_view.expandAll()
        
        # Connect selection change
        self.tree_view.selectionModel().currentChanged.connect(self._on_tree_selection_changed)
        # --- MOD END ---
    
    def _setup_status_bar(self) -> None:
        """Setup the status bar with progress indicator and trimester selector."""
        # --- MOD BEGIN: Enhanced Status Bar Setup ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        
        self.status_label = QLabel(self.tr("Prêt"))
        
        # Trimester selector
        self.trimester_combo = QComboBox()
        self.trimester_combo.addItems(["T1", "T2", "T3"])
        self.trimester_combo.setCurrentText("T1")
        self.trimester_combo.currentTextChanged.connect(self._on_trimester_changed)
        
        # Add to status bar
        self.statusBar().addWidget(self.status_label, 1)
        self.statusBar().addPermanentWidget(QLabel(self.tr("Trimestre:")))
        self.statusBar().addPermanentWidget(self.trimester_combo)
        self.statusBar().addPermanentWidget(self.progress_bar)
        # --- MOD END ---
    
    def _connect_signals(self) -> None:
        """Connect all signal handlers."""
        # --- MOD BEGIN: Enhanced Signal Connections ---
        # Ribbon action signals
        self.ribbon.action_triggered.connect(self._handle_ribbon_action)
        
        # Processing signals
        self.files_selected.connect(self._on_files_selected)
        self.processing_started.connect(self._on_processing_started)
        self.processing_finished.connect(self._on_processing_finished)
        # --- MOD END ---
    
    def _handle_ribbon_action(self, action: str) -> None:
        """Handle ribbon button actions."""
        # --- MOD BEGIN: Enhanced Action Handling ---
        if action == "import_roster":
            self._import_roster()
        elif action == "view_students":
            self._view_students()
        elif action == "import_grades":
            self._import_grade_sheet()
        elif action == "validate_low_confidence":
            self._validate_low_confidence()
        elif action == "toggle_preview":
            self._toggle_preview()
        elif action == "generate_workbook":
            self._generate_workbook()
        elif action == "open_output_folder":
            self._open_output_folder()
        elif action == "preferences":
            self._show_preferences()
        elif action == "edit_coefficients":
            self._edit_coefficients()
        # --- MOD END ---
    
    def _import_roster(self) -> None:
        """Import student roster from Excel file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            self.tr("Importer liste étudiants"),
            "",
            self.tr("Fichiers Excel (*.xlsx *.xls)")
        )
        
        if file_path:
            # TODO: Implement roster import dialog
            self.status_label.setText(self.tr("Import liste: ") + file_path)
    
    def _view_students(self) -> None:
        """Show students in current class."""
        # TODO: Implement student view
        self.status_label.setText(self.tr("Affichage étudiants"))
    
    def _import_grade_sheet(self) -> None:
        """Import grade sheet for OCR processing."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Importer feuille de notes"),
            "",
            self.tr("Images (*.png *.jpg *.jpeg *.bmp *.tiff)")
        )
        
        if file_path:
            # TODO: Implement grade sheet import dialog
            self.status_label.setText(self.tr("Import feuille: ") + file_path)
    
    def _validate_low_confidence(self) -> None:
        """Show grades with low confidence for validation."""
        # TODO: Implement low confidence validation dialog
        self.status_label.setText(self.tr("Validation confiance faible"))
    
    def _toggle_preview(self) -> None:
        """Toggle OCR preview dock widget visibility."""
        if self.preview_dock.isVisible():
            self.preview_dock.hide()
        else:
            self.preview_dock.show()
    
    def _generate_workbook(self) -> None:
        """Generate Excel workbook for current trimester."""
        # TODO: Implement workbook generation
        self.status_label.setText(self.tr("Génération classeur en cours..."))
    
    def _open_output_folder(self) -> None:
        """Open output folder in file explorer."""
        import os
        import subprocess
        output_dir = "exports"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Open in file explorer
        if os.name == 'nt':  # Windows
            os.startfile(output_dir)
        else:  # macOS/Linux
            subprocess.run(['open' if os.name == 'darwin' else 'xdg-open', output_dir])
    
    def _show_preferences(self) -> None:
        """Show preferences dialog."""
        dialog = PreferencesDialog(self)
        dialog.exec()
    
    def _edit_coefficients(self) -> None:
        """Edit subject coefficients."""
        # TODO: Implement coefficient editor
        self.status_label.setText(self.tr("Édition coefficients"))
    
    def _on_tree_selection_changed(self, current: QModelIndex, previous: QModelIndex) -> None:
        """Handle tree selection changes."""
        # --- MOD BEGIN: Tree Selection Handling ---
        if not current.isValid():
            return
        
        item = self.tree_model.itemFromIndex(current)
        if not item:
            return
        
        item_type = item.data(Qt.ItemDataRole.UserRole)
        item_id = item.data(Qt.ItemDataRole.UserRole + 1)
        
        if item_type == "class":
            self.current_class_id = item_id
            self.status_label.setText(self.tr(f"Classe sélectionnée: {item.text()}"))
        elif item_type == "term":
            self.current_term_id = item_id
            self.trimester_combo.setCurrentText(item.text())
            self.status_label.setText(self.tr(f"Trimestre sélectionné: {item.text()}"))
        elif item_type == "subject":
            self.current_subject_id = item_id
            self.status_label.setText(self.tr(f"Matière sélectionnée: {item.text()}"))
        
        # TODO: Refresh table data based on selection
        # --- MOD END ---
    
    def _on_trimester_changed(self, term_label: str) -> None:
        """Handle trimester selection change in status bar."""
        term_map = {"T1": 1, "T2": 2, "T3": 3}
        self.current_term_id = term_map.get(term_label, 1)
        self.status_label.setText(self.tr(f"Trimestre changé: {term_label}"))
        
        # TODO: Refresh table data
    
    def _on_files_selected(self, files: List[str]) -> None:
        """Handle file selection."""
        self.selected_files = files
        self.ribbon.enable_action("start_processing", len(files) > 0)
    
    def _on_processing_started(self) -> None:
        """Handle processing start."""
        self.progress_bar.setVisible(True)
        self.status_label.setText(self.tr("Traitement en cours..."))
    
    def _on_processing_finished(self) -> None:
        """Handle processing completion."""
        self.progress_bar.setVisible(False)
        self.status_label.setText(self.tr("Traitement terminé"))
