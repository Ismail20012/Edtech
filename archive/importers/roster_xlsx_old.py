# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
Excel roster importer for Moroccan school grade management system.
Handles importing student rosters from Excel files with flexible column mapping.
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from PyQt6.QtSql import QSqlQuery, QSqlDatabase
from pathlib import Path


class RosterImporter:
    """Handles importing student rosters from Excel files."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # --- MOD BEGIN: Updated Column Mappings for New Fields ---
        # Column mappings for the new required fields
        self.column_mappings = {
            'arabic_name': ['nom arabe', 'اسم', 'الاسم', 'nom en arabe', 'arabic name', 'nom'],
            'nni_id': ['nni', 'id', 'numéro national', 'carte nationale', 'رقم الهوية', 'رقم وطني'],
            'date_of_birth': ['date de naissance', 'naissance', 'né le', 'ddn', 'تاريخ الولادة'],
            'place_of_birth': ['lieu de naissance', 'lieu naissance', 'مكان الولادة', 'place of birth', 'lieu']
        }
        # --- MOD END ---
    
    def import_roster(self, df: pd.DataFrame, class_id: int, column_mapping: Dict[str, str]) -> bool:
        """
        Import student roster from DataFrame.
        
        Args:
            df: Pandas DataFrame with student data
            class_id: ID of the class to import into
            column_mapping: Mapping of field names to Excel columns
            
        Returns:
            bool: True if import successful, False otherwise
        """
            Tuple of (success, message, stats)
        """
        try:
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path)
            
            # Detect column mappings
            column_map = self._detect_columns(df.columns.tolist())
            
            if not column_map.get('student_name'):
                return False, "Aucune colonne 'nom' détectée", {}
            
            # Validate class exists
            if not self._validate_class(class_id):
                return False, f"Classe avec ID {class_id} introuvable", {}
            
            # Import students
            stats = self._import_students(df, class_id, column_map)
            
            message = f"Import terminé: {stats['imported']} étudiants importés, {stats['skipped']} ignorés"
            return True, message, stats
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'import: {e}")
            return False, f"Erreur: {str(e)}", {}
    
    def _detect_columns(self, columns: List[str]) -> Dict[str, str]:
        """Detect column mappings based on column names."""
        column_map = {}
        columns_lower = [col.lower().strip() for col in columns]
        
        for field, possible_names in self.column_mappings.items():
            for col_idx, col_name in enumerate(columns_lower):
                for possible in possible_names:
                    if possible in col_name:
                        column_map[field] = columns[col_idx]  # Use original case
                        break
                if field in column_map:
                    break
        
        return column_map
    
    def _validate_class(self, class_id: int) -> bool:
        """Validate that class exists."""
        query = QSqlQuery(self.db)
        query.prepare("SELECT COUNT(*) FROM CLASSES WHERE id = ?")
        query.addBindValue(class_id)
        query.exec()
        
        if query.next():
            return query.value(0) > 0
        return False
    
    def _import_students(self, df: pd.DataFrame, class_id: int, column_map: Dict[str, str]) -> Dict:
        """Import students from DataFrame."""
        stats = {'imported': 0, 'skipped': 0, 'errors': []}
        
        for index, row in df.iterrows():
            try:
                # Extract student data
                student_data = self._extract_student_data(row, column_map)
                
                if not student_data['student_name']:
                    stats['skipped'] += 1
                    continue
                
                # Check for duplicates
                if self._student_exists(class_id, student_data['student_name']):
                    stats['skipped'] += 1
                    self.logger.warning(f"Étudiant {student_data['student_name']} existe déjà")
                    continue
                
                # Insert student
                if self._insert_student(class_id, student_data):
                    stats['imported'] += 1
                else:
                    stats['skipped'] += 1
                    
            except Exception as e:
                stats['errors'].append(f"Ligne {index + 2}: {str(e)}")
                stats['skipped'] += 1
        
        return stats
    
    def _extract_student_data(self, row: pd.Series, column_map: Dict[str, str]) -> Dict:
        """Extract student data from row."""
        data = {
            'student_name': '',
            'student_id_number': '',
            'date_of_birth': '',
            'gender': '',
            'enrollment_date': ''
        }
        
        for field, column in column_map.items():
            if column in row.index:
                value = row[column]
                if pd.notna(value):
                    if field == 'date_of_birth' and hasattr(value, 'strftime'):
                        data[field] = value.strftime('%Y-%m-%d')
                    elif field == 'enrollment_date' and hasattr(value, 'strftime'):
                        data[field] = value.strftime('%Y-%m-%d')
                    elif field == 'gender':
                        # Normalize gender values
                        gender_str = str(value).lower().strip()
                        if gender_str in ['m', 'masculin', 'male', 'garçon']:
                            data[field] = 'M'
                        elif gender_str in ['f', 'féminin', 'female', 'fille']:
                            data[field] = 'F'
                        else:
                            data[field] = str(value).strip()
                    else:
                        data[field] = str(value).strip()
        
        return data
    
    def _student_exists(self, class_id: int, student_name: str) -> bool:
        """Check if student already exists in the class."""
        query = QSqlQuery(self.db)
        query.prepare("SELECT COUNT(*) FROM ROSTERS WHERE class_id = ? AND student_name = ?")
        query.addBindValue(class_id)
        query.addBindValue(student_name)
        query.exec()
        
        if query.next():
            return query.value(0) > 0
        return False
    
    def _insert_student(self, class_id: int, student_data: Dict) -> bool:
        """Insert student into database."""
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO ROSTERS (class_id, student_name, student_id_number, 
                               date_of_birth, gender, enrollment_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """)
        
        query.addBindValue(class_id)
        query.addBindValue(student_data['student_name'])
        query.addBindValue(student_data['student_id_number'] or None)
        query.addBindValue(student_data['date_of_birth'] or None)
        query.addBindValue(student_data['gender'] or None)
        query.addBindValue(student_data['enrollment_date'] or 'CURRENT_DATE')
        
        success = query.exec()
        if not success:
            self.logger.error(f"Erreur insertion: {query.lastError().text()}")
        
        return success
    
    def get_available_sheets(self, file_path: str) -> List[str]:
        """Get list of available sheets in Excel file."""
        try:
            excel_file = pd.ExcelFile(file_path)
            return excel_file.sheet_names
        except Exception as e:
            self.logger.error(f"Erreur lecture fichier Excel: {e}")
            return []
    
    def preview_import(self, file_path: str, sheet_name: str = None, max_rows: int = 10) -> Tuple[bool, Dict]:
        """
        Preview import to show detected columns and sample data.
        
        Returns:
            Tuple of (success, preview_data)
        """
        try:
            # Read sample data
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=max_rows)
            else:
                df = pd.read_excel(file_path, nrows=max_rows)
            
            # Detect columns
            column_map = self._detect_columns(df.columns.tolist())
            
            # Prepare preview data
            preview_data = {
                'total_columns': len(df.columns),
                'detected_mappings': column_map,
                'unmapped_columns': [col for col in df.columns if col not in column_map.values()],
                'sample_data': df.head(5).to_dict('records'),
                'estimated_rows': len(df)
            }
            
            return True, preview_data
            
        except Exception as e:
            self.logger.error(f"Erreur aperçu: {e}")
            return False, {'error': str(e)}


def create_sample_roster_template(output_path: str) -> bool:
    """Create a sample Excel template for roster import."""
    try:
        sample_data = {
            'Nom et Prénom': [
                'Ahmed Ben Ali',
                'Fatima El Mansouri',
                'Mohammed Karimi',
                'Aicha Benjelloun',
                'Youssef Tazi'
            ],
            'Numéro': ['ST001', 'ST002', 'ST003', 'ST004', 'ST005'],
            'Date de Naissance': [
                '2010-03-15',
                '2010-05-22',
                '2010-01-08',
                '2010-07-12',
                '2010-04-03'
            ],
            'Sexe': ['M', 'F', 'M', 'F', 'M'],
            'Date Inscription': [
                '2024-09-01',
                '2024-09-01',
                '2024-09-01',
                '2024-09-01',
                '2024-09-01'
            ]
        }
        
        df = pd.DataFrame(sample_data)
        df.to_excel(output_path, index=False, sheet_name='Liste Étudiants')
        
        return True
        
    except Exception as e:
        logging.error(f"Erreur création template: {e}")
        return False
