# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
Grade sheet OCR processor for Moroccan school system.
Handles digit-only recognition, grid detection, and fuzzy name matching.
"""

import cv2
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, NamedTuple
from fuzzywuzzy import fuzz
from PyQt6.QtSql import QSqlQuery, QSqlDatabase
import pytesseract
import re


class GradeEntry(NamedTuple):
    """Represents a grade entry from OCR."""
    student_name: str
    grade: float
    confidence: float
    position: Tuple[int, int, int, int]  # x, y, w, h


class GradeOCRProcessor:
    """Processes grade sheets using OpenCV and Tesseract OCR."""
    
    def __init__(self, db: QSqlDatabase):
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # --- MOD BEGIN: Enhanced OCR Configuration ---
        # OCR configuration for handwritten digits only
        self.tesseract_config = '--psm 6 -c tessedit_char_whitelist=0123456789.,'
        
        # Fuzzy matching thresholds
        self.name_match_threshold = 80  # Minimum similarity for name matching
        self.confidence_threshold = 70  # Minimum OCR confidence
        
        # Grid detection parameters
        self.min_line_length = 100
        self.max_line_gap = 10
        self.grid_tolerance = 5
        
        # Grade validation
        self.min_grade = 0.0
        self.max_grade = 20.0
        # --- MOD END ---
    
    def process_grade_sheet(self, image_path: str, class_id: int, subject_id: int, 
                          term_id: int) -> Tuple[bool, str, Dict]:
        """
        Process a grade sheet image and extract grades.
        
        Args:
            image_path: Path to the grade sheet image
            class_id: Target class ID
            subject_id: Target subject ID  
            term_id: Target term ID
            
        Returns:
            Tuple of (success, message, results)
        """
        try:
            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                return False, "Impossible de charger l'image", {}
            
            # Get student roster for the class
            students = self._get_class_roster(class_id)
            if not students:
                return False, f"Aucun étudiant trouvé pour la classe {class_id}", {}
            
            # Detect grid structure
            grid_info = self._detect_grid(image)
            
            # Extract text regions
            text_regions = self._extract_text_regions(image, grid_info)
            
            # Process each region for names and grades
            extracted_data = self._extract_grades(image, text_regions)
            
            # Match students and validate grades
            matched_grades = self._match_students_and_grades(students, extracted_data)
            
            # Save results to database
            saved_count = self._save_grades(matched_grades, class_id, subject_id, term_id)
            
            # Create OCR result record
            self._save_ocr_result(image_path, class_id, subject_id, term_id, 
                                len(students), len(matched_grades))
            
            results = {
                'total_students': len(students),
                'extracted_entries': len(extracted_data),
                'matched_grades': len(matched_grades),
                'saved_grades': saved_count,
                'confidence_avg': np.mean([g.confidence for g in matched_grades]) if matched_grades else 0
            }
            
            message = f"OCR terminé: {saved_count}/{len(students)} notes extraites"
            return True, message, results
            
        except Exception as e:
            self.logger.error(f"Erreur OCR: {e}")
            return False, f"Erreur: {str(e)}", {}
    
    def _get_class_roster(self, class_id: int) -> List[Dict]:
        """Get student roster for the class."""
        query = QSqlQuery(self.db)
        query.prepare("SELECT id, student_name FROM ROSTERS WHERE class_id = ? ORDER BY student_name")
        query.addBindValue(class_id)
        query.exec()
        
        students = []
        while query.next():
            students.append({
                'id': query.value(0),
                'name': query.value(1)
            })
        
        return students
    
    def _detect_grid(self, image: np.ndarray) -> Dict:
        """Detect table grid structure in the image."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect horizontal and vertical lines
        horizontal_lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100,
                                         minLineLength=self.min_line_length,
                                         maxLineGap=self.max_line_gap)
        
        vertical_lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100,
                                       minLineLength=self.min_line_length,
                                       maxLineGap=self.max_line_gap)
        
        # Process lines to find grid structure
        h_lines = self._process_lines(horizontal_lines, 'horizontal')
        v_lines = self._process_lines(vertical_lines, 'vertical')
        
        return {
            'horizontal_lines': h_lines,
            'vertical_lines': v_lines,
            'grid_detected': len(h_lines) > 2 and len(v_lines) > 2
        }
    
    def _process_lines(self, lines: np.ndarray, orientation: str) -> List[int]:
        """Process detected lines to extract grid coordinates."""
        if lines is None:
            return []
        
        coords = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            if orientation == 'horizontal':
                # For horizontal lines, use y coordinate
                avg_y = (y1 + y2) // 2
                coords.append(avg_y)
            else:
                # For vertical lines, use x coordinate
                avg_x = (x1 + x2) // 2
                coords.append(avg_x)
        
        # Remove duplicates and sort
        coords = sorted(list(set(coords)))
        
        # Merge nearby lines
        merged = []
        for coord in coords:
            if not merged or abs(coord - merged[-1]) > self.grid_tolerance:
                merged.append(coord)
        
        return merged
    
    def _extract_text_regions(self, image: np.ndarray, grid_info: Dict) -> List[Dict]:
        """Extract text regions based on grid structure."""
        regions = []
        
        if not grid_info['grid_detected']:
            # Fallback: divide image into regions
            h, w = image.shape[:2]
            rows = 10  # Assume 10 rows
            cols = 3   # Name, Grade, Comments
            
            for row in range(rows):
                for col in range(cols):
                    x = col * w // cols
                    y = row * h // rows
                    w_region = w // cols
                    h_region = h // rows
                    
                    regions.append({
                        'bbox': (x, y, w_region, h_region),
                        'row': row,
                        'col': col,
                        'type': 'name' if col == 0 else 'grade' if col == 1 else 'comment'
                    })
        else:
            # Use detected grid
            h_lines = grid_info['horizontal_lines']
            v_lines = grid_info['vertical_lines']
            
            for i in range(len(h_lines) - 1):
                for j in range(len(v_lines) - 1):
                    x = v_lines[j]
                    y = h_lines[i]
                    w = v_lines[j + 1] - x
                    h = h_lines[i + 1] - y
                    
                    regions.append({
                        'bbox': (x, y, w, h),
                        'row': i,
                        'col': j,
                        'type': 'name' if j == 0 else 'grade' if j == 1 else 'comment'
                    })
        
        return regions
    
    def _extract_grades(self, image: np.ndarray, regions: List[Dict]) -> List[GradeEntry]:
        """Extract text from regions and identify grades."""
        entries = []
        
        # Group regions by row
        rows = {}
        for region in regions:
            row_idx = region['row']
            if row_idx not in rows:
                rows[row_idx] = {}
            rows[row_idx][region['type']] = region
        
        for row_idx, row_regions in rows.items():
            if 'name' in row_regions and 'grade' in row_regions:
                # Extract name
                name_region = row_regions['name']
                name_bbox = name_region['bbox']
                name_crop = image[name_bbox[1]:name_bbox[1]+name_bbox[3],
                                name_bbox[0]:name_bbox[0]+name_bbox[2]]
                
                name_text = self._extract_text(name_crop, mode='name')
                
                # Extract grade
                grade_region = row_regions['grade']
                grade_bbox = grade_region['bbox']
                grade_crop = image[grade_bbox[1]:grade_bbox[1]+grade_bbox[3],
                                 grade_bbox[0]:grade_bbox[0]+grade_bbox[2]]
                
                grade_result = self._extract_text(grade_crop, mode='grade')
                
                if name_text and grade_result['text']:
                    try:
                        grade_value = float(grade_result['text'].replace(',', '.'))
                        if 0 <= grade_value <= 20:  # Valid grade range
                            entries.append(GradeEntry(
                                student_name=name_text,
                                grade=grade_value,
                                confidence=grade_result['confidence'],
                                position=grade_bbox
                            ))
                    except ValueError:
                        continue
        
        return entries
    
    def _extract_text(self, image_crop: np.ndarray, mode: str = 'name') -> str:
        """Extract text from image crop using Tesseract."""
        if image_crop.size == 0:
            return '' if mode == 'name' else {'text': '', 'confidence': 0}
        
        # Preprocess image
        gray = cv2.cvtColor(image_crop, cv2.COLOR_BGR2GRAY) if len(image_crop.shape) == 3 else image_crop
        
        # Apply threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.medianBlur(thresh, 3)
        
        if mode == 'grade':
            # Use digit-only configuration for grades
            try:
                data = pytesseract.image_to_data(denoised, config=self.tesseract_config, output_type=pytesseract.Output.DICT)
                
                # Extract text and confidence
                texts = []
                confidences = []
                for i, conf in enumerate(data['conf']):
                    if int(conf) > 30:  # Minimum confidence threshold
                        text = data['text'][i].strip()
                        if text:
                            texts.append(text)
                            confidences.append(int(conf))
                
                if texts:
                    combined_text = ''.join(texts)
                    avg_confidence = sum(confidences) / len(confidences)
                    return {'text': combined_text, 'confidence': avg_confidence}
                else:
                    return {'text': '', 'confidence': 0}
                    
            except Exception as e:
                self.logger.warning(f"Erreur OCR grade: {e}")
                return {'text': '', 'confidence': 0}
        else:
            # Use default configuration for names
            try:
                text = pytesseract.image_to_string(denoised, lang='fra+ara', config='--psm 7')
                return text.strip()
            except Exception as e:
                self.logger.warning(f"Erreur OCR nom: {e}")
                return ''
    
    def _match_students_and_grades(self, students: List[Dict], extracted_data: List[GradeEntry]) -> List[GradeEntry]:
        """Match extracted grades with student roster using fuzzy matching on Arabic names."""
        # --- MOD BEGIN: Enhanced Arabic Name Matching ---
        matched = []
        
        for entry in extracted_data:
            best_match = None
            best_score = 0
            
            for student in students:
                # Try matching with both latin and arabic names
                latin_score = fuzz.partial_ratio(entry.student_name.lower(), student['name'].lower())
                arabic_score = 0
                
                # If student has arabic_name, try matching with that too
                if 'arabic_name' in student and student['arabic_name']:
                    arabic_score = fuzz.partial_ratio(entry.student_name, student['arabic_name'])
                
                # Use the better score
                score = max(latin_score, arabic_score)
                
                if score > best_score and score >= self.name_match_threshold:
                    best_score = score
                    best_match = student
            
            if best_match:
                # Create new entry with matched student info
                matched_entry = GradeEntry(
                    student_name=best_match['name'],
                    grade=entry.grade,
                    confidence=entry.confidence * (best_score / 100),  # Adjust confidence by match score
                    position=entry.position
                )
                matched.append(matched_entry)
                
                # Add roster_id for database saving
                matched_entry.roster_id = best_match['id']
        
        return matched
        # --- MOD END ---
    
    def _save_grades(self, grades: List[GradeEntry], class_id: int, subject_id: int, term_id: int) -> int:
        """Save matched grades to database."""
        saved_count = 0
        
        for grade_entry in grades:
            query = QSqlQuery(self.db)
            
            # Check if grade already exists
            query.prepare("""
                SELECT COUNT(*) FROM GRADES 
                WHERE roster_id = ? AND subject_id = ? AND term_id = ?
            """)
            query.addBindValue(grade_entry.roster_id)
            query.addBindValue(subject_id)
            query.addBindValue(term_id)
            query.exec()
            
            if query.next() and query.value(0) > 0:
                # Update existing grade
                update_query = QSqlQuery(self.db)
                update_query.prepare("""
                    UPDATE GRADES SET grade = ?, ocr_confidence = ?, entry_date = CURRENT_TIMESTAMP
                    WHERE roster_id = ? AND subject_id = ? AND term_id = ?
                """)
                update_query.addBindValue(grade_entry.grade)
                update_query.addBindValue(grade_entry.confidence)
                update_query.addBindValue(grade_entry.roster_id)
                update_query.addBindValue(subject_id)
                update_query.addBindValue(term_id)
                
                if update_query.exec():
                    saved_count += 1
            else:
                # Insert new grade
                insert_query = QSqlQuery(self.db)
                insert_query.prepare("""
                    INSERT INTO GRADES (roster_id, subject_id, term_id, grade, ocr_confidence, manual_override)
                    VALUES (?, ?, ?, ?, ?, 0)
                """)
                insert_query.addBindValue(grade_entry.roster_id)
                insert_query.addBindValue(subject_id)
                insert_query.addBindValue(term_id)
                insert_query.addBindValue(grade_entry.grade)
                insert_query.addBindValue(grade_entry.confidence)
                
                if insert_query.exec():
                    saved_count += 1
        
        return saved_count
    
    def _save_ocr_result(self, image_path: str, class_id: int, subject_id: int, term_id: int,
                        total_students: int, matched_students: int):
        """Save OCR processing result to database."""
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO OCR_RESULTS (image_path, class_id, subject_id, term_id, 
                                   total_students, matched_students, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
        
        confidence = (matched_students / total_students * 100) if total_students > 0 else 0
        
        query.addBindValue(image_path)
        query.addBindValue(class_id)
        query.addBindValue(subject_id)
        query.addBindValue(term_id)
        query.addBindValue(total_students)
        query.addBindValue(matched_students)
        query.addBindValue(confidence)
        
        query.exec()


def preprocess_grade_image(image_path: str, output_path: str = None) -> str:
    """
    Preprocess grade sheet image for better OCR results.
    
    Args:
        image_path: Input image path
        output_path: Output path (optional)
        
    Returns:
        Path to preprocessed image
    """
    try:
        # Load image
        image = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Deskew image
        coords = np.column_stack(np.where(gray > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        if abs(angle) > 0.5:  # Only rotate if significant skew
            (h, w) = gray.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        else:
            rotated = gray
        
        # Noise reduction
        denoised = cv2.medianBlur(rotated, 3)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Save preprocessed image
        if output_path is None:
            output_path = image_path.replace('.', '_processed.')
        
        cv2.imwrite(output_path, enhanced)
        return output_path
        
    except Exception as e:
        logging.error(f"Erreur préprocessing: {e}")
        return image_path  # Return original path on error
