#!/usr/bin/env python3
"""
Database initialization script
"""

import os
import sys
from models.database import Database

def main():
    """Initialize the database"""
    try:
        # Set the database path
        db_path = os.path.join('instance', 'database.db')
        
        # Create database instance
        db = Database(db_path)
        
        # Initialize database (this will create all tables)
        db.init_database()
        
        print(f"Database initialized successfully at: {db_path}")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()