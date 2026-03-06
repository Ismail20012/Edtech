#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create a sample Excel file for testing the new roster import functionality.
Contains the new required fields: Arabic Name, NNI, Date of Birth, Place of Birth.
"""

import pandas as pd
import os

def create_sample_roster():
    """Create a sample Excel file with student roster data."""
    
    # Sample data with the new fields
    sample_data = {
        'الاسم الكامل': [
            'أحمد محمد العلوي',
            'فاطمة أحمد الزهراء', 
            'محمد عبد الله الصدقي',
            'عائشة يوسف الفهري',
            'عمر الحسن التازي'
        ],
        'رقم الهوية الوطنية': [
            'AB123456',
            'CD789012', 
            'EF345678',
            'GH901234',
            'IJ567890'
        ],
        'تاريخ الميلاد': [
            '15/03/2010',
            '22/07/2009',
            '08/11/2010', 
            '14/02/2009',
            '30/09/2010'
        ],
        'مكان الميلاد': [
            'الرباط',
            'الدار البيضاء',
            'فاس',
            'مراكش',
            'طنجة'
        ]
    }
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Create output directory if it doesn't exist
    os.makedirs('samples', exist_ok=True)
    
    # Save to Excel file
    output_path = 'samples/liste_etudiants_exemple.xlsx'
    df.to_excel(output_path, index=False, engine='openpyxl')
    
    print(f"Sample roster file created: {output_path}")
    print("Columns:")
    for col in df.columns:
        print(f"  - {col}")
    print(f"Number of students: {len(df)}")
    
    return output_path

def create_french_sample_roster():
    """Create a French version of the sample roster."""
    
    # Sample data in French
    sample_data = {
        'Nom (Arabe)': [
            'أحمد محمد العلوي',
            'فاطمة أحمد الزهراء', 
            'محمد عبد الله الصدقي',
            'عائشة يوسف الفهري',
            'عمر الحسن التازي'
        ],
        'NNI': [
            'AB123456',
            'CD789012', 
            'EF345678',
            'GH901234',
            'IJ567890'
        ],
        'Date de naissance': [
            '15/03/2010',
            '22/07/2009',
            '08/11/2010', 
            '14/02/2009',
            '30/09/2010'
        ],
        'Lieu de naissance': [
            'Rabat',
            'Casablanca',
            'Fès',
            'Marrakech',
            'Tanger'
        ]
    }
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Save to Excel file
    output_path = 'samples/liste_etudiants_francais.xlsx'
    df.to_excel(output_path, index=False, engine='openpyxl')
    
    print(f"French sample roster file created: {output_path}")
    return output_path

if __name__ == "__main__":
    print("Creating sample roster files...")
    create_sample_roster()
    create_french_sample_roster()
    print("Sample files created successfully!")
