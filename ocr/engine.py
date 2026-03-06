# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
OCR engine using pytesseract.
"""

from typing import Dict, Any
import pytesseract
from PIL import Image

def run_ocr(image_path: str) -> Dict[str, Any]:
    """
    Runs OCR on a pre-processed image and returns the extracted data.
    """
    try:
        # Specify the path to the Tesseract executable if not in PATH
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Use the pre-processed image for OCR
        img = Image.open(image_path)
        
        # Perform OCR using French and Arabic language models
        custom_config = r'--oem 3 --psm 6 -l fra+ara'
        ocr_data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)
        
        return ocr_data
    except Exception as e:
        print(f"An error occurred during OCR: {e}")
        return {}

def run_easyocr() -> str:
    """
    A stub for a future implementation of EasyOCR for handwriting.
    """
    return "(Handwriting recognition not yet implemented)"

