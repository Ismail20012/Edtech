import cv2
import numpy as np
import pytesseract
import logging
from typing import List, Dict, Tuple
from django.contrib.postgres.search import TrigramSimilarity
from core.models import Student, Subject

logger = logging.getLogger(__name__)

def preprocess_image(image_path: str) -> np.ndarray:
    """Preprocess image for table detection."""
    image = cv2.imread(image_path)
    if image is None:
        return None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Binary thresholding
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    return thresh

def detect_table_structure(thresh: np.ndarray) -> Tuple[List[int], List[int]]:
    """Detect horizontal and vertical lines to find table structure."""
    # Horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    detect_horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    cnts = cv2.findContours(detect_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    h_lines = sorted([cv2.boundingRect(c)[1] for c in cnts])

    # Vertical lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    detect_vertical = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    cnts = cv2.findContours(detect_vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    v_lines = sorted([cv2.boundingRect(c)[0] for c in cnts])

    # Merge nearby lines
    def merge_lines(lines, threshold=10):
        if not lines: return []
        merged = [lines[0]]
        for i in range(1, len(lines)):
            if lines[i] - merged[-1] > threshold:
                merged.append(lines[i])
        return merged

    return merge_lines(h_lines), merge_lines(v_lines)

def fuzzy_match_student(raw_name: str) -> Tuple[Student, float]:
    """Find the best matching student using Trigram similarity."""
    if not raw_name:
        return None, 0.0

    # Combine names for matching or check separately
    # Here we check first_name_fr + last_name_fr and first_name_ar + last_name_ar
    results = Student.objects.annotate(
        sim_fr=TrigramSimilarity('first_name_fr', raw_name) + TrigramSimilarity('last_name_fr', raw_name),
        sim_ar=TrigramSimilarity('first_name_ar', raw_name) + TrigramSimilarity('last_name_ar', raw_name)
    ).order_by('-sim_fr', '-sim_ar')

    best_match = results.first()
    if best_match:
        score = max(best_match.sim_fr, best_match.sim_ar) / 2.0 # Normalized-ish
        if score > 0.3: # Threshold
            return best_match, score
    
    return None, 0.0

def process_grade_sheet(image_path: str, subject_id: int) -> List[Dict]:
    """
    Core OCR utility: extracts grades and matches students.
    Returns: list of {student_id, subject_id, grade, confidence_score, student_name_raw}
    """
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Could not load image at {image_path}")
        return []

    thresh = preprocess_image(image_path)
    h_lines, v_lines = detect_table_structure(thresh)

    if len(h_lines) < 2 or len(v_lines) < 2:
        logger.warning("No table structure detected. Falling back to simple row splitting.")
        # Fallback logic if needed, but for now return empty
        return []

    results = []
    # Assume 3 columns: Name, Grade, Comments (common in Mauritania)
    # Column indices: v_lines[0], v_lines[1], v_lines[2], v_lines[3]...
    
    for i in range(len(h_lines) - 1):
        y1, y2 = h_lines[i], h_lines[i+1]
        
        # Name column (usually first)
        if len(v_lines) >= 2:
            x1_name, x2_name = v_lines[0], v_lines[1]
            name_crop = image[y1:y2, x1_name:x2_name]
            name_raw = pytesseract.image_to_string(name_crop, lang='fra+ara', config='--psm 7').strip()
            
            # Grade column (usually second)
            if len(v_lines) >= 3:
                x1_grade, x2_grade = v_lines[1], v_lines[2]
                grade_crop = image[y1:y2, x1_grade:x2_grade]
                # Filter for digits
                grade_raw = pytesseract.image_to_string(grade_crop, config='--psm 10 -c tessedit_char_whitelist=0123456789.,').strip()
                
                # Confidence (simplified)
                try:
                    data = pytesseract.image_to_data(grade_crop, output_type=pytesseract.Output.DICT)
                    conf = np.mean([float(c) for c in data['conf'] if float(c) != -1]) if data['conf'] else 0
                except:
                    conf = 50

                if name_raw:
                    student, match_conf = fuzzy_match_student(name_raw)
                    
                    results.append({
                        'student_id': student.id if student else None,
                        'student_name_raw': name_raw,
                        'subject_id': subject_id,
                        'grade': grade_raw,
                        'confidence_score': (conf / 100.0) * (match_conf if match_conf > 0 else 0.5)
                    })

    return results
