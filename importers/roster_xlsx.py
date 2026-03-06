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
Updated to support new fields: Arabic Name, NNI (ID), Date of Birth, Place of Birth.
"""

import pandas as pd
import logging
from typing import Dict, List, Optional


class RosterImporter:
    """Handles importing student rosters from Excel files."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Column mappings for the new required fields
        self.column_mappings = {
            'arabic_name': ['nom arabe', 'اسم', 'الاسم', 'nom en arabe', 'arabic name', 'nom'],
            'nni_id': ['nni', 'id', 'numéro national', 'carte nationale', 'رقم الهوية', 'رقم وطني'],
            'date_of_birth': ['date de naissance', 'naissance', 'né le', 'ddn', 'تاريخ الولادة'],
            'place_of_birth': ['lieu de naissance', 'lieu naissance', 'مكان الولادة', 'place of birth', 'lieu']
        }
    
    def import_roster(self, df: pd.DataFrame, class_id: int, column_mapping: Dict[str, str]) -> bool:
        """
        Import student roster from DataFrame with transaction support.
        
        Args:
            df: Pandas DataFrame with student data
            class_id: ID of the class to import into
            column_mapping: Mapping of field names to Excel columns
            
        Returns:
            bool: True if import successful, False otherwise
        """
        try:
            from models.database import DatabaseManager
            db = DatabaseManager()
            
            # Start transaction to ensure data integrity
            db.execute_query("BEGIN TRANSACTION")
            
            success_count = 0
            error_count = 0
            error_details = []
            
            self.logger.info(f"Starting import for class {class_id} with {len(df)} rows")
            
            for index, row in df.iterrows():
                try:
                    # Extract data based on mapping
                    arabic_name = str(row.get(column_mapping.get('arabic_name', ''), '')).strip()
                    nni_id = str(row.get(column_mapping.get('nni_id', ''), '')).strip()
                    date_of_birth = str(row.get(column_mapping.get('date_of_birth', ''), '')).strip()
                    place_of_birth = str(row.get(column_mapping.get('place_of_birth', ''), '')).strip()
                    
                    # Skip rows with empty required fields (Arabic name is required)
                    if not arabic_name or arabic_name.lower() in ['nan', 'none', '', 'null']:
                        continue
                    
                    # Clean up empty strings and NaN values
                    if nni_id.lower() in ['nan', 'none', 'null']:
                        nni_id = ''
                    if date_of_birth.lower() in ['nan', 'none', 'null']:
                        date_of_birth = ''
                    if place_of_birth.lower() in ['nan', 'none', 'null']:
                        place_of_birth = ''
                    
                    # Validate and normalize date if provided
                    if date_of_birth:
                        date_of_birth = self.validate_date(date_of_birth)
                    
                    # Insert into database using parameterized query
                    result = db.execute_query("""
                        INSERT OR REPLACE INTO ROSTERS 
                        (class_id, arabic_name, nni_id, date_of_birth, place_of_birth)
                        VALUES (?, ?, ?, ?, ?)
                    """, (class_id, arabic_name, nni_id, date_of_birth, place_of_birth))
                    
                    if result:
                        success_count += 1
                        self.logger.debug(f"Imported student: {arabic_name}")
                    else:
                        error_count += 1
                        error_msg = f"Row {index + 1}: Database insert failed"
                        error_details.append(error_msg)
                        self.logger.warning(error_msg)
                    
                except Exception as e:
                    error_count += 1
                    error_msg = f"Row {index + 1}: {str(e)}"
                    error_details.append(error_msg)
                    self.logger.error(f"Error importing row {index + 1}: {e}")
                    
                    # If too many errors (>50%), rollback and fail
                    if error_count > len(df) * 0.5:
                        self.logger.error(f"Too many errors ({error_count}/{len(df)}), rolling back")
                        db.execute_query("ROLLBACK")
                        db.close()
                        return False
                    continue
            
            # Only commit if we have successful imports
            if success_count > 0:
                db.execute_query("COMMIT")
                self.logger.info(f"Import completed: {success_count} students imported, {error_count} errors")
            else:
                db.execute_query("ROLLBACK")
                self.logger.warning("No valid students imported")
                
            db.close()
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Import failed: {e}")
            try:
                db.execute_query("ROLLBACK")
                db.close()
            except:
                pass
            return False
    
    def detect_column_mappings(self, columns: List[str]) -> Dict[str, Optional[str]]:
        """Detect column mappings based on column names."""
        mappings = {}
        
        for field, possible_names in self.column_mappings.items():
            mappings[field] = None
            
            # Look for exact matches first
            for col in columns:
                if col.lower().strip() in [name.lower() for name in possible_names]:
                    mappings[field] = col
                    break
            
            # If no exact match, look for partial matches
            if mappings[field] is None:
                for col in columns:
                    col_lower = col.lower().strip()
                    for possible_name in possible_names:
                        if possible_name.lower() in col_lower or col_lower in possible_name.lower():
                            mappings[field] = col
                            break
                    if mappings[field]:
                        break
        
        return mappings
    
    def validate_date(self, date_str: str) -> str:
        """Validate and normalize date format."""
        try:
            from datetime import datetime
            
            date_formats = [
                '%d/%m/%Y',
                '%d-%m-%Y', 
                '%Y-%m-%d',
                '%d.%m.%Y',
                '%d %m %Y'
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(str(date_str).strip(), fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # If no format matches, return as-is
            return str(date_str).strip()
            
        except Exception:
            return str(date_str).strip()
