# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Gemini Project. All rights reserved.
#
# This software is licensed under the MIT License.
# For the full license text, see the LICENSE file in the project root.
#

"""
Database migration script for enhanced grade management schema.
Run this to upgrade the database to the new structure.
"""

import logging
from models.database import open_database, create_and_seed_database

def main():
    """Run database migration."""
    logging.basicConfig(level=logging.INFO)
    
    print("=== Migration Base de Données ===")
    print("Ouverture de la base de données...")
    
    # Open database connection
    db = open_database()
    
    if not db.isOpen():
        print("❌ Erreur: Impossible d'ouvrir la base de données")
        return False
    
    print("✅ Base de données ouverte")
    
    # Run migration
    print("Application des migrations...")
    create_and_seed_database(db)
    
    print("✅ Migration terminée avec succès")
    print("\nLa base de données est maintenant prête avec:")
    print("- Tables TERMS (T1, T2, T3)")
    print("- Tables CLASSES (3A, 4A, 5A, 6A)")
    print("- Tables SUBJECTS avec coefficients")
    print("- Tables ROSTERS avec noms arabes/latins")
    print("- Tables COEFFICIENTS par classe")
    print("- Tables GRADES avec suivi OCR")
    print("- Données d'exemple pour la classe 3A")
    
    db.close()
    return True

if __name__ == "__main__":
    main()
