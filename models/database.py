# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#
# pylint: disable=invalid-name, too-few-public-methods

"""
Handles SQLite database creation, connection, and initial data seeding.
Extended schema for Moroccan school grade management system.
"""

import logging
from typing import Dict, List, Optional
from PyQt6.QtSql import QSqlDatabase, QSqlQuery

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def open_database() -> QSqlDatabase:
    """Opens and returns the SQLite database connection."""
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName("school_data.db")
    if not db.open():
        logging.error("Database connection failed: %s", db.lastError().text())
    return db

def create_and_seed_database(db: QSqlDatabase):
    """
    Creates the extended database schema for Moroccan school grade management.
    Includes terms, classes, rosters, coefficients, and OCR results.
    """
    if not db.isOpen():
        logging.error("Database is not open. Cannot create or seed tables.")
        return

    query = QSqlQuery(db)

    # Check database version for migration
    db_version = get_database_version(db)
    if db_version >= 2:
        logging.info("Database schema is up-to-date (version %d).", db_version)
        return

    # Create extended schema
    create_extended_schema(query)
    
    # Migrate existing data if needed
    if db_version == 1:
        migrate_from_v1_to_v2(query)
    else:
        # Fresh installation - seed with sample data
        seed_extended_data(query)
    
    # Update database version
    set_database_version(query, 2)
    
    logging.info("Extended database schema created and seeded successfully.")


def get_database_version(db: QSqlDatabase) -> int:
    """Get current database schema version."""
    query = QSqlQuery(db)
    
    # Check if version table exists
    if "DB_VERSION" not in db.tables():
        # Check if old schema exists
        if "STUDENTS" in db.tables():
            return 1  # Old schema
        return 0  # No schema
    
    query.exec("SELECT version FROM DB_VERSION LIMIT 1")
    if query.next():
        return query.value(0)
    return 0


def set_database_version(query: QSqlQuery, version: int):
    """Set database schema version."""
    query.exec("CREATE TABLE IF NOT EXISTS DB_VERSION (version INTEGER)")
    query.exec("DELETE FROM DB_VERSION")
    query.prepare("INSERT INTO DB_VERSION (version) VALUES (?)")
    query.addBindValue(version)
    query.exec()


def create_extended_schema(query: QSqlQuery):
    """Create extended database schema for grade management."""
    
    # --- MOD BEGIN: Enhanced Schema for Business Requirements ---
    # Academic Terms (Trimesters) - T1, T2, T3
    query.exec("""
        CREATE TABLE IF NOT EXISTS TERMS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            is_active BOOLEAN DEFAULT 0
        )
    """)
    
    # School Classes/Levels
    query.exec("""
        CREATE TABLE IF NOT EXISTS CLASSES (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            level TEXT,
            section TEXT,
            academic_year TEXT DEFAULT '2024-2025'
        )
    """)
    
    # Subjects with coefficients per class
    query.exec("""
        CREATE TABLE IF NOT EXISTS SUBJECTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE,
            coefficient REAL DEFAULT 1.0,
            category TEXT,
            description TEXT
        )
    """)
    
    # Student rosters per class (many-to-many via ROSTERS)
    query.exec("""
        CREATE TABLE IF NOT EXISTS ROSTERS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            arabic_name TEXT NOT NULL,
            nni_id TEXT,
            date_of_birth TEXT,
            place_of_birth TEXT,
            enrollment_date TEXT DEFAULT CURRENT_DATE,
            FOREIGN KEY(class_id) REFERENCES CLASSES(id),
            UNIQUE(class_id, arabic_name, nni_id)
        )
    """)
    
    # Subject coefficients per class (configurable)
    query.exec("""
        CREATE TABLE IF NOT EXISTS COEFFICIENTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            coefficient REAL NOT NULL DEFAULT 1.0,
            FOREIGN KEY(class_id) REFERENCES CLASSES(id),
            FOREIGN KEY(subject_id) REFERENCES SUBJECTS(id),
            UNIQUE(class_id, subject_id)
        )
    """)
    
    # Grade entries with OCR tracking and term-based storage
    query.exec("""
        CREATE TABLE IF NOT EXISTS GRADES (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roster_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            term_id INTEGER NOT NULL,
            grade REAL NOT NULL,
            max_grade REAL DEFAULT 20.0,
            ocr_confidence REAL DEFAULT 100.0,
            manual_override BOOLEAN DEFAULT 0,
            entry_date TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY(roster_id) REFERENCES ROSTERS(id),
            FOREIGN KEY(subject_id) REFERENCES SUBJECTS(id),
            FOREIGN KEY(term_id) REFERENCES TERMS(id),
            UNIQUE(roster_id, subject_id, term_id)
        )
    """)
    
    # OCR processing results tracking
    query.exec("""
        CREATE TABLE IF NOT EXISTS OCR_RESULTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL,
            class_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            term_id INTEGER NOT NULL,
            processing_date TEXT DEFAULT CURRENT_TIMESTAMP,
            total_students INTEGER DEFAULT 0,
            matched_students INTEGER DEFAULT 0,
            confidence_score REAL DEFAULT 0.0,
            status TEXT DEFAULT 'pending',
            error_message TEXT,
            FOREIGN KEY(class_id) REFERENCES CLASSES(id),
            FOREIGN KEY(subject_id) REFERENCES SUBJECTS(id),
            FOREIGN KEY(term_id) REFERENCES TERMS(id)
        )
    """)
    # --- MOD END ---
    
    # Legacy compatibility - keep old tables structure
    query.exec("""
        CREATE TABLE IF NOT EXISTS STUDENTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date_of_birth TEXT
        )
    """)
    
    query.exec("""
        CREATE TABLE IF NOT EXISTS ATTENDANCE (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            status TEXT,
            FOREIGN KEY(student_id) REFERENCES STUDENTS(id)
        )
    """)


def migrate_from_v1_to_v2(query: QSqlQuery):
    """Migrate from old schema to new extended schema."""
    logging.info("Migrating database from v1 to v2...")
    
    # Create default term
    query.exec("INSERT INTO TERMS (name, is_active) VALUES ('Trimestre 1', 1)")
    term_id = query.lastInsertId()
    
    # Don't create default class - let users import their own classes
    class_id = 1  # Placeholder for migration purposes only
    
    # Migrate students to rosters
    query.exec("SELECT id, name, date_of_birth FROM STUDENTS")
    while query.next():
        migrate_query = QSqlQuery()
        migrate_query.prepare("INSERT INTO ROSTERS (class_id, student_name, date_of_birth) VALUES (?, ?, ?)")
        migrate_query.addBindValue(class_id)
        migrate_query.addBindValue(query.value(1))  # name
        migrate_query.addBindValue(query.value(2))  # date_of_birth
        migrate_query.exec()
    
    # Update subject codes if missing
    query.exec("SELECT id, name FROM SUBJECTS")
    subject_updates = []
    while query.next():
        subject_id = query.value(0)
        subject_name = query.value(1)
        code = subject_name.upper()[:3]  # Simple code generation
        subject_updates.append((code, subject_id))
    
    for code, subject_id in subject_updates:
        update_query = QSqlQuery()
        update_query.prepare("UPDATE SUBJECTS SET code = ? WHERE id = ?")
        update_query.addBindValue(code)
        update_query.addBindValue(subject_id)
        update_query.exec()


def seed_extended_data(query: QSqlQuery):
    """Seed database with sample data for Moroccan school system."""
    
    # --- MOD BEGIN: Enhanced Seed Data ---
    # Sample terms (T1, T2, T3)
    terms = [
        ("T1", "Premier Trimestre", "2024-09-01", "2024-12-31", True),
        ("T2", "Deuxième Trimestre", "2025-01-01", "2025-03-31", False),
        ("T3", "Troisième Trimestre", "2025-04-01", "2025-06-30", False)
    ]
    
    for label, name, start, end, active in terms:
        query.prepare("INSERT INTO TERMS (label, name, start_date, end_date, is_active) VALUES (?, ?, ?, ?, ?)")
        query.addBindValue(label)
        query.addBindValue(name)
        query.addBindValue(start)
        query.addBindValue(end)
        query.addBindValue(active)
        query.exec()
    
    # Sample classes with proper naming
    classes = [
        ("3A", "3ème Année", "A", "2024-2025"),
        ("4A", "4ème Année", "A", "2024-2025"),
        ("5A", "5ème Année", "A", "2024-2025"),
        ("6A", "6ème Année", "A", "2024-2025")
    ]
    
    for name, level, section, year in classes:
        query.prepare("INSERT INTO CLASSES (name, level, section, academic_year) VALUES (?, ?, ?, ?)")
        query.addBindValue(name)
        query.addBindValue(level)
        query.addBindValue(section)
        query.addBindValue(year)
        query.exec()
    
    # Enhanced subjects matching Moroccan curriculum
    subjects = [
        ("Mathématiques", "MAT", 7.0, "Sciences exactes"),
        ("Physique-Chimie", "PC", 6.0, "Sciences exactes"),
        ("Sciences Naturelles", "SN", 3.0, "Sciences"),
        ("Arabe", "AR", 2.0, "Langues"),
        ("Français", "FR", 2.0, "Langues"),
        ("Anglais", "ANG", 2.0, "Langues"),
        ("Histoire-Géographie", "HG", 2.0, "Sciences humaines"),
        ("Éducation Islamique", "IR", 2.0, "Religion"),
        ("Informatique", "IC", 1.0, "Technologie"),
        ("Éducation Physique", "PH", 2.0, "Sport")
    ]
    
    for name, code, coeff, category in subjects:
        query.prepare("INSERT INTO SUBJECTS (name, code, coefficient, category) VALUES (?, ?, ?, ?)")
        query.addBindValue(name)
        query.addBindValue(code)
        query.addBindValue(coeff)
        query.addBindValue(category)
        query.exec()
    
    # Sample roster for 3A class with Arabic names
    students_3a = [
        ("أحمد بن علي", "Ahmed Ben Ali", "ST2024001", "2010-03-15", "Casablanca", "M"),
        ("فاطمة المنصوري", "Fatima El Mansouri", "ST2024002", "2010-05-22", "Rabat", "F"),
        ("محمد الكريمي", "Mohammed Al Karimi", "ST2024003", "2010-01-08", "Fès", "M"),
        ("عائشة بنجلون", "Aicha Benjelloun", "ST2024004", "2010-07-12", "Marrakech", "F"),
        ("يوسف التازي", "Youssef Tazi", "ST2024005", "2010-04-03", "Meknès", "M")
    ]
    
    for arabic_name, latin_name, student_id, dob, pob, gender in students_3a:
        query.prepare("""INSERT INTO ROSTERS (class_id, student_name, arabic_name, latin_name, 
                         student_id_number, date_of_birth, place_of_birth, gender, enrollment_date) 
                         VALUES (1, ?, ?, ?, ?, ?, ?, ?, CURRENT_DATE)""")
        query.addBindValue(latin_name)  # Primary name for matching
        query.addBindValue(arabic_name)
        query.addBindValue(latin_name)
        query.addBindValue(student_id)
        query.addBindValue(dob)
        query.addBindValue(pob)
        query.addBindValue(gender)
        query.exec()
    
    # Set up coefficients for 3A class (from JSON config)
    coefficients_3a = [
        (1, 1, 7.0),  # MAT
        (1, 2, 6.0),  # PC  
        (1, 3, 3.0),  # SN
        (1, 4, 2.0),  # AR
        (1, 5, 2.0),  # FR
        (1, 6, 2.0),  # ANG
        (1, 7, 2.0),  # HG
        (1, 8, 2.0),  # IR
        (1, 9, 1.0),  # IC
        (1, 10, 2.0)  # PH
    ]
    
    for class_id, subject_id, coeff in coefficients_3a:
        query.prepare("INSERT INTO COEFFICIENTS (class_id, subject_id, coefficient) VALUES (?, ?, ?)")
        query.addBindValue(class_id)
        query.addBindValue(subject_id)
        query.addBindValue(coeff)
        query.exec()
    # --- MOD END ---



# Legacy seed functions for compatibility
def seed_students(query: QSqlQuery):
    """Seeds the STUDENTS table with dummy data (legacy)."""
    students = [
        ("Ahmed Yassine", "2008-05-12"),
        ("Fatima Zahra", "2009-01-20"),
        ("Youssef El-Amrani", "2008-11-30"),
        ("Salma Bennani", "2009-03-15"),
        ("Karim Bouazza", "2008-07-22"),
    ]
    query.prepare("INSERT INTO STUDENTS (name, date_of_birth) VALUES (?, ?)")
    for name, dob in students:
        query.addBindValue(name)
        query.addBindValue(dob)
        if not query.exec():
            logging.warning("Failed to insert student %s: %s", name, query.lastError().text())


def seed_subjects(query: QSqlQuery):
    """Seeds the SUBJECTS table with dummy data (legacy)."""
    subjects = ["Mathématiques", "Français", "Arabe", "Physique-Chimie", "Histoire-Géographie"]
    query.prepare("INSERT INTO SUBJECTS (name) VALUES (?)")
    for name in subjects:
        query.addBindValue(name)
        if not query.exec():
            logging.warning("Failed to insert subject %s: %s", name, query.lastError().text())


def seed_grades(query: QSqlQuery):
    """Seeds the GRADES table with dummy data (legacy)."""
    grades = [
        (1, 1, 15.5), (1, 2, 12.0), (1, 3, 18.0),
        (2, 1, 19.0), (2, 2, 17.5), (2, 3, 16.0),
        (3, 1, 11.0), (3, 2, 9.5), (3, 3, 13.0),
        (4, 1, 16.5), (4, 2, 18.0), (4, 3, 17.0),
        (5, 1, 14.0), (5, 2, 13.5), (5, 3, 15.0),
    ]
    query.prepare("INSERT INTO GRADES (student_id, subject_id, grade) VALUES (?, ?, ?)")
    for student_id, subject_id, grade in grades:
        query.addBindValue(student_id)
        query.addBindValue(subject_id)
        query.addBindValue(grade)
        if not query.exec():
            logging.warning("Failed to insert grade: %s", query.lastError().text())


def seed_attendance(query: QSqlQuery):
    """Seeds the ATTENDANCE table with dummy data (legacy)."""
    attendance = [
        (1, "2025-05-10", "Présent"),
        (2, "2025-05-10", "Présent"),
        (3, "2025-05-10", "Absent"),
        (4, "2025-05-10", "Présent"),
        (5, "2025-05-10", "Présent"),
    ]
    query.prepare("INSERT INTO ATTENDANCE (student_id, date, status) VALUES (?, ?, ?)")
    for student_id, date, status in attendance:
        query.addBindValue(student_id)
        query.addBindValue(date)
        query.addBindValue(status)
        if not query.exec():
            logging.warning("Failed to insert attendance: %s", query.lastError().text())


class DatabaseManager:
    """Database manager class with utility methods for the application."""
    
    def __init__(self):
        self.db = open_database()
    
    def execute_query(self, query_text: str, params: tuple = None) -> List[Dict]:
        """Execute a query and return results as list of dictionaries."""
        query = QSqlQuery(self.db)
        query.prepare(query_text)
        
        if params:
            for param in params:
                query.addBindValue(param)
        
        if not query.exec():
            raise Exception(f"Database query failed: {query.lastError().text()}")
        
        results = []
        while query.next():
            record = {}
            for i in range(query.record().count()):
                field_name = query.record().fieldName(i)
                record[field_name] = query.value(i)
            results.append(record)
        
        return results
    
    def get_all_classes(self) -> List[Dict]:
        """Get all classes."""
        return self.execute_query("SELECT id, name, level, section, academic_year FROM CLASSES ORDER BY name")
    
    def get_class_by_id(self, class_id: int) -> Dict:
        """Get class by ID."""
        results = self.execute_query("SELECT id, name, level, section, academic_year FROM CLASSES WHERE id = ?", (class_id,))
        return results[0] if results else None
    
    def get_all_subjects(self) -> List[Dict]:
        """Get all subjects."""
        return self.execute_query("SELECT id, name, '' as code, 1.0 as coefficient, '' as category, '' as description FROM SUBJECTS ORDER BY name")
    
    def get_all_terms(self) -> List[Dict]:
        """Get all terms."""
        return self.execute_query("SELECT id, label, name, start_date, end_date, is_active FROM TERMS ORDER BY id")
    
    def get_coefficients(self, class_id: int, term_id: int) -> List[Dict]:
        """Get coefficients for a class and term."""
        return self.execute_query("""
            SELECT c.subject_id, c.coefficient 
            FROM COEFFICIENTS c 
            WHERE c.class_id = ?
        """, (class_id,))
    
    def save_coefficients(self, coefficients_data: List[Dict]):
        """Save coefficients to database."""
        query = QSqlQuery(self.db)
        
        # First, delete existing coefficients for this class/term
        if coefficients_data:
            class_id = coefficients_data[0]['class_id']
            term_id = coefficients_data[0]['term_id']
            
            query.prepare("DELETE FROM COEFFICIENTS WHERE class_id = ? AND term_id = ?")
            query.addBindValue(class_id)
            query.addBindValue(term_id)
            
            if not query.exec():
                raise Exception(f"Failed to delete existing coefficients: {query.lastError().text()}")
        
        # Insert new coefficients
        query.prepare("""
            INSERT INTO COEFFICIENTS (class_id, subject_id, term_id, coefficient) 
            VALUES (?, ?, ?, ?)
        """)
        
        for coeff_data in coefficients_data:
            query.addBindValue(coeff_data['class_id'])
            query.addBindValue(coeff_data['subject_id'])
            query.addBindValue(coeff_data['term_id'])
            query.addBindValue(coeff_data['coefficient'])
            
            if not query.exec():
                raise Exception(f"Failed to insert coefficient: {query.lastError().text()}")
    
    def get_students_by_class(self, class_id: int) -> List[Dict]:
        """Get all students in a class."""
        return self.execute_query("""
            SELECT id, student_name, arabic_name, latin_name, student_id_number, 
                   date_of_birth, place_of_birth, gender, enrollment_date
            FROM ROSTERS 
            WHERE class_id = ? 
            ORDER BY student_name
        """, (class_id,))
    
    def get_grades_by_class_term(self, class_id: int, term_id: int, subject_id: int = None) -> List[Dict]:
        """Get grades for a class and term, optionally filtered by subject."""
        if subject_id:
            return self.execute_query("""
                SELECT g.id, r.student_name, s.name as subject_name, g.grade, 
                       g.ocr_confidence, g.manual_override, g.entry_date
                FROM GRADES g
                JOIN ROSTERS r ON g.roster_id = r.id
                JOIN SUBJECTS s ON g.subject_id = s.id
                WHERE r.class_id = ? AND g.term_id = ? AND g.subject_id = ?
                ORDER BY r.student_name, s.name
            """, (class_id, term_id, subject_id))
        else:
            return self.execute_query("""
                SELECT g.id, r.student_name, s.name as subject_name, g.grade, 
                       g.ocr_confidence, g.manual_override, g.entry_date
                FROM GRADES g
                JOIN ROSTERS r ON g.roster_id = r.id
                JOIN SUBJECTS s ON g.subject_id = s.id
                WHERE r.class_id = ? AND g.term_id = ?
                ORDER BY r.student_name, s.name
            """, (class_id, term_id))
    
    def close(self):
        """Close database connection."""
        if self.db.isOpen():
            self.db.close()


if __name__ == '__main__':
    # This allows direct execution for database setup.
    db_conn = open_database()
    create_and_seed_database(db_conn)
    db_conn.close()
